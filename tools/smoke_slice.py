"""Run inside the release image: real CLI/config compatibility, without a display."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
sys.path.insert(0, "/app")
from app import generate_preflight_config

with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    vertices = [(x,y,z) for z in (0,10) for y in (100,110) for x in (100,110)]
    mesh = root / "cube.stl"
    with mesh.open("w") as out:
        out.write("solid cube\n")
        for a,b,c,d in ((0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)):
            for tri in ((a,b,c),(a,c,d)):
                out.write("facet normal 0 0 0\nouter loop\n")
                for index in tri: out.write("vertex %g %g %g\n" % vertices[index])
                out.write("endloop\nendfacet\n")
        out.write("endsolid cube\n")
    for name, params in (("pla", {"filament_type":"pla", "nozzle_temp":210, "bed_temp":60}),
                         ("petg", {"filament_type":"petg", "nozzle_temp":240, "bed_temp":80, "min_fan_speed":30, "max_fan_speed":50, "retract_length":1, "retract_speed":30, "retract_lift":.2})):
        config = root / (name+".ini"); output = root / (name+".gcode")
        config.write_text(generate_preflight_config({"layer_height":.2, "infill_density":15, **params}, {"buildVolume":{"x":220,"y":220,"z":250}}))
        run = subprocess.run([os.environ["PREFLIGHT_BIN"], "--export-gcode", "--dont-arrange", "--load", str(config), "--output", str(output), str(mesh)], capture_output=True, text=True, timeout=180)
        if run.returncode or not output.exists(): raise RuntimeError(run.stdout + run.stderr)
        assert "G1 X" in output.read_text(), "No extrusion paths"
        print(name, "real slice passed", output.stat().st_size, "bytes")
