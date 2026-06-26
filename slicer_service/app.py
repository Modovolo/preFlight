#!/usr/bin/env python3
"""HTTP wrapper for running preFlight as a headless slicing service."""

from __future__ import annotations

import asyncio
import json
import math
import os
import re
import shutil
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aiohttp import WSMsgType, web


API_PREFIX = os.environ.get("PREFLIGHT_API_PREFIX", "/api/slicer").rstrip("/")
PREFLIGHT_BIN = Path(os.environ.get("PREFLIGHT_BIN", "/opt/preflight/bin/preflight"))
WORK_DIR = Path(os.environ.get("PREFLIGHT_WORK_DIR", "/work"))
JOB_TTL_SECONDS = int(os.environ.get("PREFLIGHT_JOB_TTL_SECONDS", "3600"))
SLICE_TIMEOUT_SECONDS = int(os.environ.get("PREFLIGHT_SLICE_TIMEOUT_SECONDS", "1800"))


@dataclass
class SliceJob:
    id: str
    dir: Path
    status: str = "queued"
    progress: int = 0
    stage: str = "preparing"
    message: str = "Queued"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    result: dict[str, Any] | None = None
    error: str | None = None
    details: str | None = None
    gcode_path: Path | None = None
    process: asyncio.subprocess.Process | None = None
    websockets: set[web.WebSocketResponse] = field(default_factory=set)


jobs: dict[str, SliceJob] = {}


def now_ms() -> int:
    return int(time.time() * 1000)


def as_bool(value: Any) -> str:
    return "1" if bool(value) else "0"


def percent(value: Any) -> str:
    try:
        return f"{float(value):g}%"
    except (TypeError, ValueError):
        return "0%"


def number(value: Any, default: float = 0) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = default

    if numeric.is_integer():
        return str(int(numeric))
    return f"{numeric:g}"


def join_numbers(values: list[Any], default: Any) -> str:
    source = values if values else [default]
    return ",".join(number(value, default) for value in source)


def repeated_number(value: Any, count: Any, default: float) -> str:
    try:
        repeat_count = max(1, int(count))
    except (TypeError, ValueError):
        repeat_count = 1
    return ",".join(number(value, default) for _ in range(repeat_count))


def bed_shape(profile: dict[str, Any]) -> str:
    build_volume = profile.get("buildVolume") or {}
    bed_type = profile.get("bedShape")
    width = float(build_volume.get("x") or profile.get("bed_size_x") or 220)
    depth = float(build_volume.get("y") or profile.get("bed_size_y") or 220)

    if bed_type == "circular":
        radius = min(width, depth) / 2
        center_x = width / 2
        center_y = depth / 2
        points = []
        for index in range(32):
            angle = 2 * 3.141592653589793 * index / 32
            points.append(f"{center_x + radius * math.cos(angle):.3f}x{center_y + radius * math.sin(angle):.3f}")
        return ",".join(points)

    return f"0x0,{width:g}x0,{width:g}x{depth:g},0x{depth:g}"


def map_gcode_flavor(value: Any) -> str | None:
    if not value:
        return None

    normalized = str(value).strip().lower().replace(" ", "_").replace("-", "_")
    if normalized in {"klipper", "marlin", "reprap", "repetier", "machinekit", "smoothie"}:
        return normalized
    if normalized in {"marlin_legacy", "marlin2", "marlin_2"}:
        return "marlin"
    return None


def generate_preflight_config(params: dict[str, Any], profile: dict[str, Any]) -> str:
    build_volume = profile.get("buildVolume") or {}
    nozzle_diameter = profile.get("nozzleDiameter") or profile.get("nozzle_diameter") or 0.4
    filament_diameter = profile.get("filamentDiameter") or profile.get("filament_diameter") or 1.75
    extruder_count = profile.get("extruderCount") or 1
    max_print_height = build_volume.get("z") or profile.get("bed_size_z") or 250
    nozzle_temps = params.get("nozzle_temps") or []
    bed_temps = params.get("bed_controller_temps") or []
    nozzle_temp = params.get("nozzle_temp") or 200
    bed_temp = params.get("bed_temp") or 0

    config: dict[str, str] = {
        "printer_technology": "FFF",
        "bed_shape": bed_shape(profile),
        "max_print_height": number(max_print_height, 250),
        "nozzle_diameter": repeated_number(nozzle_diameter, extruder_count, 0.4),
        "filament_diameter": repeated_number(filament_diameter, extruder_count, 1.75),
        "layer_height": number(params.get("layer_height"), 0.2),
        "first_layer_height": number(params.get("first_layer_height"), 0.2),
        "extrusion_width": number(params.get("line_width"), 0),
        "fill_density": percent(params.get("infill_density")),
        "fill_pattern": str(params.get("infill_pattern") or "grid"),
        "perimeters": number(params.get("wall_count"), 2),
        "top_solid_layers": number(params.get("top_layers"), 4),
        "bottom_solid_layers": number(params.get("bottom_layers"), 4),
        "perimeter_speed": number(params.get("print_speed"), 60),
        "infill_speed": number(params.get("print_speed"), 60),
        "solid_infill_speed": number(params.get("print_speed"), 60),
        "travel_speed": number(params.get("travel_speed"), 120),
        "first_layer_speed": number(params.get("first_layer_speed"), 30),
        "temperature": join_numbers(nozzle_temps, nozzle_temp),
        "first_layer_temperature": join_numbers(nozzle_temps, nozzle_temp),
        "bed_temperature": number(bed_temps[0] if bed_temps else bed_temp, 0),
        "first_layer_bed_temperature": number(bed_temps[0] if bed_temps else bed_temp, 0),
        "support_material": as_bool(params.get("enable_support")),
        "support_material_threshold": number(params.get("support_angle"), 45),
        "support_material_pattern": str(params.get("support_pattern") or "rectilinear"),
        "dont_support_bridges": "1",
    }

    if params.get("adhesion_type") == "brim":
        config["brim_width"] = number(params.get("brim_width"), 5)
    else:
        config["brim_width"] = "0"

    gcode_flavor = map_gcode_flavor(profile.get("gcodeFlavor") or profile.get("gcode_flavor"))
    if gcode_flavor:
        config["gcode_flavor"] = gcode_flavor

    return "\n".join(f"{key} = {value}" for key, value in config.items()) + "\n"


def make_job_response(job: SliceJob) -> dict[str, Any]:
    response: dict[str, Any] = {
        "job_id": job.id,
        "status": job.status,
        "progress": job.progress,
        "stage": job.stage,
        "message": job.message,
    }

    if job.result:
        response["result"] = job.result
        response["gcode_url"] = f"{API_PREFIX}/gcode/{job.id}.gcode"
    if job.error:
        response["error"] = job.error
    if job.details:
        response["details"] = job.details
    return response


async def notify_job(job: SliceJob, event: dict[str, Any] | None = None) -> None:
    payload = event or {
        "type": "progress",
        "job_id": job.id,
        "progress": job.progress,
        "stage": job.stage,
        "message": job.message,
    }

    stale: list[web.WebSocketResponse] = []
    for ws in job.websockets:
        try:
            await ws.send_json(payload)
        except Exception:
            stale.append(ws)

    for ws in stale:
        job.websockets.discard(ws)


async def update_job(job: SliceJob, *, status: str | None = None, progress: int | None = None, stage: str | None = None, message: str | None = None) -> None:
    if status is not None:
        job.status = status
    if progress is not None:
        job.progress = progress
    if stage is not None:
        job.stage = stage
    if message is not None:
        job.message = message
    job.updated_at = time.time()
    await notify_job(job)


def find_gcode(job_dir: Path, preferred: Path) -> Path | None:
    if preferred.exists():
        return preferred


    candidates = sorted(
        list(job_dir.glob("*.gcode")) + list(job_dir.glob("*.g")) + list(job_dir.glob("*.bgcode")),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def parse_gcode_result(gcode_path: Path) -> dict[str, Any]:
    text = gcode_path.read_text(errors="ignore")
    layer_count = len(re.findall(r"^;\s*(?:LAYER_CHANGE|LAYER:)\b", text, re.MULTILINE))

    filament_weight_g = 0.0
    filament_used_m = 0.0
    estimated_time = "Unknown"

    weight_match = re.search(r"filament used \[g\]\s*=\s*([0-9.]+)", text, re.IGNORECASE)
    if weight_match:
        filament_weight_g = float(weight_match.group(1))

    length_match = re.search(r"filament used \[(?:mm|m)\]\s*=\s*([0-9.]+)", text, re.IGNORECASE)
    if length_match:
        value = float(length_match.group(1))
        filament_used_m = value / 1000 if "[mm]" in length_match.group(0).lower() else value

    time_match = re.search(r"estimated printing time[^=]*=\s*(.+)", text, re.IGNORECASE)
    if time_match:
        estimated_time = time_match.group(1).strip()

    if layer_count == 0:
        layer_markers = re.findall(r"^;\s*Z:([0-9.]+)", text, re.MULTILINE)
        layer_count = len(set(layer_markers))

    return {
        "layer_count": layer_count,
        "filament_used_m": round(filament_used_m, 3),
        "filament_weight_g": round(filament_weight_g, 3),
        "estimated_time_formatted": estimated_time,
        "gcode_size": gcode_path.stat().st_size,
    }


async def run_preflight(job: SliceJob, mesh_paths: list[Path], config_path: Path, output_path: Path) -> None:
    await update_job(job, status="processing", progress=10, stage="preparing", message="Preparing preFlight job...")

    command = [
        str(PREFLIGHT_BIN),
        "--export-gcode",
        "--dont-arrange",
        "--load",
        str(config_path),
        "--output",
        str(output_path),
        *[str(path) for path in mesh_paths],
    ]

    await update_job(job, progress=25, stage="slicing", message="Running preFlight slicer...")
    stdout = b""
    stderr = b""

    returncode: int | None = None

    try:
        job.process = await asyncio.create_subprocess_exec(
            *command,
            cwd=str(job.dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(job.process.communicate(), timeout=SLICE_TIMEOUT_SECONDS)
        returncode = job.process.returncode
    except asyncio.TimeoutError:
        if job.process and job.process.returncode is None:
            job.process.kill()
            await job.process.wait()
        raise RuntimeError(f"preFlight slicing timed out after {SLICE_TIMEOUT_SECONDS} seconds")
    finally:
        job.process = None

    stdout_text = stdout.decode(errors="replace")
    stderr_text = stderr.decode(errors="replace")
    combined_output = "\n".join(part for part in [stdout_text, stderr_text] if part).strip()

    if job.status == "cancelled":
        return

    if returncode not in (0, None):
        raise RuntimeError(combined_output or f"preFlight exited with {returncode}")

    actual_gcode_path = find_gcode(job.dir, output_path)
    if not actual_gcode_path:
        raise RuntimeError(combined_output or "preFlight did not produce a G-code file")

    job.gcode_path = actual_gcode_path
    await update_job(job, progress=95, stage="generating", message="Finalizing G-code...")
    job.result = parse_gcode_result(actual_gcode_path)
    job.status = "complete"
    job.progress = 100
    job.stage = "complete"
    job.message = "Slicing complete"
    job.updated_at = time.time()
    await notify_job(
        job,
        {
            "type": "complete",
            "job_id": job.id,
            "result": job.result,
            "gcode_url": f"{API_PREFIX}/gcode/{job.id}.gcode",
        },
    )


async def run_job_task(job: SliceJob, mesh_paths: list[Path], config_path: Path, output_path: Path) -> None:
    try:
        await run_preflight(job, mesh_paths, config_path, output_path)
    except Exception as error:
        if job.status == "cancelled":
            return
        job.status = "error"
        job.progress = 100
        job.stage = "complete"
        job.error = "Remote slicing failed"
        job.details = str(error)
        job.message = str(error)
        job.updated_at = time.time()
        await notify_job(
            job,
            {
                "type": "error",
                "job_id": job.id,
                "error": job.error,
                "details": job.details,
            },
        )


async def health(_request: web.Request) -> web.Response:
    binary_ready = PREFLIGHT_BIN.exists() and os.access(PREFLIGHT_BIN, os.X_OK)
    payload = {
        "status": "healthy" if binary_ready else "unavailable",
        "engine": "preflight",
        "binary": str(PREFLIGHT_BIN),
    }
    return web.json_response(payload, status=200 if binary_ready else 503)


async def engines(_request: web.Request) -> web.Response:
    return web.json_response({"engines": ["preflight"]})


async def create_slice(request: web.Request) -> web.Response:
    if not (PREFLIGHT_BIN.exists() and os.access(PREFLIGHT_BIN, os.X_OK)):
        return web.json_response({"error": f"preFlight binary is not executable at {PREFLIGHT_BIN}"}, status=503)

    reader = await request.multipart()
    job_id = f"pf-{now_ms()}-{uuid.uuid4().hex[:8]}"
    job_dir = WORK_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=False)

    params: dict[str, Any] = {}
    profile: dict[str, Any] = {}
    mesh_paths: list[Path] = []
    mesh_index = 0

    async for field in reader:
        if field.name == "meshes":
            filename = Path(field.filename or f"model_{mesh_index}.stl").name
            suffix = Path(filename).suffix or ".stl"
            mesh_path = job_dir / f"model_{mesh_index}{suffix}"
            mesh_path.write_bytes(await field.read())
            mesh_paths.append(mesh_path)
            mesh_index += 1
        elif field.name == "params":
            params = json.loads((await field.read()).decode("utf-8") or "{}")
        elif field.name == "printer_profile_config":
            profile = json.loads((await field.read()).decode("utf-8") or "{}")

    if not mesh_paths:
        shutil.rmtree(job_dir, ignore_errors=True)
        return web.json_response({"error": "At least one mesh is required"}, status=400)

    config_path = job_dir / "preflight.ini"
    output_path = job_dir / "output.gcode"
    config_path.write_text(generate_preflight_config(params, profile), encoding="utf-8")

    job = SliceJob(id=job_id, dir=job_dir)
    jobs[job_id] = job
    asyncio.create_task(run_job_task(job, mesh_paths, config_path, output_path))
    return web.json_response({"job_id": job_id, "status": "queued", "message": "Slice job queued"})


async def get_job(request: web.Request) -> web.Response:
    job = jobs.get(request.match_info["job_id"])
    if not job:
        return web.json_response({"error": "Job not found"}, status=404)
    return web.json_response(make_job_response(job))


async def cancel_job(request: web.Request) -> web.Response:
    job = jobs.get(request.match_info["job_id"])
    if not job:
        return web.json_response({"error": "Job not found"}, status=404)

    if job.process and job.process.returncode is None:
        job.process.terminate()
        try:
            await asyncio.wait_for(job.process.wait(), timeout=5)
        except asyncio.TimeoutError:
            job.process.kill()
            await job.process.wait()

    job.status = "cancelled"
    job.progress = 100
    job.stage = "complete"
    job.message = "Slicing cancelled"
    job.updated_at = time.time()
    await notify_job(job, {"type": "error", "job_id": job.id, "error": "Slicing cancelled"})
    return web.json_response({"message": "Job cancelled"})


async def get_gcode(request: web.Request) -> web.StreamResponse:
    job_id = request.match_info["job_id"]
    if job_id.endswith(".gcode"):
        job_id = job_id[:-6]

    job = jobs.get(job_id)
    if not job or not job.gcode_path or not job.gcode_path.exists():
        return web.json_response({"error": "G-code not found"}, status=404)

    return web.FileResponse(job.gcode_path, headers={"Content-Disposition": f'attachment; filename="{job.id}.gcode"'})


async def websocket_job(request: web.Request) -> web.WebSocketResponse:
    job = jobs.get(request.match_info["job_id"])
    ws = web.WebSocketResponse(heartbeat=30)
    await ws.prepare(request)

    if not job:
        await ws.send_json({"type": "error", "error": "Job not found"})
        await ws.close()
        return ws

    job.websockets.add(ws)
    await notify_job(job)
    if job.status == "complete" and job.result:
        await ws.send_json({"type": "complete", "job_id": job.id, "result": job.result, "gcode_url": f"{API_PREFIX}/gcode/{job.id}.gcode"})
    elif job.status == "error":
        await ws.send_json({"type": "error", "job_id": job.id, "error": job.error, "details": job.details})

    async for message in ws:
        if message.type == WSMsgType.ERROR:
            break

    job.websockets.discard(ws)
    return ws


async def cleanup_jobs(_app: web.Application) -> None:
    while True:
        await asyncio.sleep(300)
        cutoff = time.time() - JOB_TTL_SECONDS
        expired = [job_id for job_id, job in jobs.items() if job.updated_at < cutoff and job.status in {"complete", "error", "cancelled"}]
        for job_id in expired:
            job = jobs.pop(job_id, None)
            if job:
                shutil.rmtree(job.dir, ignore_errors=True)


def add_prefixed_routes(app: web.Application, prefix: str) -> None:
    app.router.add_get(f"{prefix}/health", health)
    app.router.add_get(f"{prefix}/engines", engines)
    app.router.add_post(f"{prefix}/slice", create_slice)
    app.router.add_get(f"{prefix}/job/{{job_id}}", get_job)
    app.router.add_post(f"{prefix}/job/{{job_id}}/cancel", cancel_job)
    app.router.add_get(f"{prefix}/gcode/{{job_id}}", get_gcode)
    app.router.add_get(f"{prefix}/ws/job/{{job_id}}", websocket_job)


async def on_startup(app: web.Application) -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    app["cleanup_task"] = asyncio.create_task(cleanup_jobs(app))


async def on_cleanup(app: web.Application) -> None:
    task = app.get("cleanup_task")
    if task:
        task.cancel()


def create_app() -> web.Application:
    app = web.Application(client_max_size=1024**3)
    add_prefixed_routes(app, "")
    if API_PREFIX:
        add_prefixed_routes(app, API_PREFIX)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8090"))
    web.run_app(create_app(), host="0.0.0.0", port=port)