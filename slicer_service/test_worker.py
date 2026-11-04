import asyncio
import json
from pathlib import Path
from aiohttp import FormData
from aiohttp.test_utils import TestClient, TestServer
import pytest
import app

def payload():
    data = FormData()
    data.add_field("meshes", b"synthetic", filename="part.stl")
    data.add_field("params", json.dumps({"layer_height": .2}))
    return data

def setup(monkeypatch, tmp_path):
    binary = tmp_path / "engine"
    binary.write_text("#!/usr/bin/env python3\nimport time,sys\nfrom pathlib import Path\ntime.sleep(.3)\nPath(sys.argv[sys.argv.index('--output')+1]).write_text(';LAYER_CHANGE\\nG1 X10 Y10 E1\\n')\n")
    binary.chmod(0o755)
    monkeypatch.setattr(app, "PREFLIGHT_BIN", binary)
    monkeypatch.setattr(app, "WORK_DIR", tmp_path / "work")
    monkeypatch.setattr(app, "WORKER_TOKEN", "fixture-token")
    monkeypatch.setattr(app, "MAX_QUEUED", 2)
    app.jobs.clear()

@pytest.mark.asyncio
async def test_private_auth_bounded_queue_and_queued_cancellation(monkeypatch, tmp_path):
    setup(monkeypatch, tmp_path)
    async with TestClient(TestServer(app.create_app())) as client:
        assert (await client.post("/api/slicer/slice", data=payload())).status == 401
        headers = {"X-Service-Token":"fixture-token"}
        first = await (await client.post("/api/slicer/slice", data=payload(), headers=headers)).json()
        second = await (await client.post("/api/slicer/slice", data=payload(), headers=headers)).json()
        assert (await client.post("/api/slicer/slice", data=payload(), headers=headers)).status == 429
        assert (await client.post("/api/slicer/job/"+second["job_id"]+"/cancel", headers=headers)).status == 200
        for _ in range(40):
            result = await (await client.get("/api/slicer/job/"+first["job_id"], headers=headers)).json()
            if result["status"] == "complete": break
            await asyncio.sleep(.025)
        assert result["status"] == "complete"
        result = await (await client.get("/api/slicer/job/"+second["job_id"], headers=headers)).json()
        assert result["status"] == "cancelled"
        assert app.jobs[second["job_id"]].process is None

@pytest.mark.asyncio
async def test_timeout_is_terminal_and_invalid_input_leaves_no_orphan_directory(monkeypatch, tmp_path):
    setup(monkeypatch, tmp_path)
    monkeypatch.setattr(app, "SLICE_TIMEOUT_SECONDS", .01)
    async with TestClient(TestServer(app.create_app())) as client:
        headers = {"X-Service-Token":"fixture-token"}
        data = FormData(); data.add_field("meshes", b"mesh", filename="part.stl"); data.add_field("params", "not-json")
        assert (await client.post("/api/slicer/slice", data=data, headers=headers)).status == 422
        assert list(app.WORK_DIR.iterdir()) == []
        job = await (await client.post("/api/slicer/slice", data=payload(), headers=headers)).json()
        for _ in range(40):
            result = await (await client.get("/api/slicer/job/"+job["job_id"], headers=headers)).json()
            if result["status"] == "error": break
            await asyncio.sleep(.025)
        assert result["status"] == "error" and "timed out" in result["details"]

@pytest.mark.asyncio
async def test_extruder_layer_ranges_slice_a_3mf_and_bad_ranges_are_rejected(monkeypatch, tmp_path):
    setup(monkeypatch, tmp_path)
    binary = tmp_path / "engine"
    binary.write_text("#!/usr/bin/env python3\nimport sys\nfrom pathlib import Path\nargs=sys.argv[1:]\nout=args[args.index('--output')+1]\nPath(out).with_name('args.txt').write_text('\\n'.join(args))\nPath(out).write_text(';LAYER_CHANGE\\nG1 X10 Y10 E1\\n')\n")
    stl = "solid t\nfacet normal 0 0 1\nouter loop\nvertex 0 0 0\nvertex 10 0 0\nvertex 0 10 1\nendloop\nendfacet\nendsolid t\n"
    def request(params):
        data = FormData()
        data.add_field("meshes", stl.encode(), filename="a.stl"); data.add_field("meshes", stl.encode(), filename="b.stl")
        data.add_field("params", json.dumps(params)); data.add_field("printer_profile_config", json.dumps({"extruderCount": 2}))
        return data
    async with TestClient(TestServer(app.create_app())) as client:
        headers = {"X-Service-Token": "fixture-token"}
        assert "extruder_selection" in (await (await client.get("/health")).json())["features"]
        bad = await client.post("/api/slicer/slice", data=request({"extruder_layer_ranges": [{"from_layer": 1, "to_layer": 2, "extruder": 3}]}), headers=headers)
        assert bad.status == 422 and "extruder" in (await bad.json())["error"]
        assert list(app.WORK_DIR.iterdir()) == []
        ranges = {"print_extruder": 1, "layer_height": .2, "first_layer_height": .2, "extruder_layer_ranges": [{"from_layer": 3, "to_layer": 4, "extruder": 2}]}
        job = await (await client.post("/api/slicer/slice", data=request(ranges), headers=headers)).json()
        for _ in range(40):
            result = await (await client.get("/api/slicer/job/" + job["job_id"], headers=headers)).json()
            if result["status"] == "complete": break
            await asyncio.sleep(.025)
        assert result["status"] == "complete"
        args = (app.WORK_DIR / job["job_id"] / "args.txt").read_text().splitlines()
        assert [Path(a).name for a in args if a.endswith((".stl", ".3mf"))] == ["plate.3mf"], "both meshes travel in one project"
        config = (app.WORK_DIR / job["job_id"] / "preflight.ini").read_text()
        assert "perimeter_extruder = 1" in config
