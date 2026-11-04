"""Extruder selection for preFlight jobs.

`print_extruder` picks the extruder that prints every layer. `extruder_layer_ranges`
optionally prints inclusive, 1-based layer ranges with other extruders; layers outside
every range return to `print_extruder`.

preFlight reads per-layer tool changes only from a 3MF project (its "MultiAsSingle"
custom G-code mode), so when ranges are present the meshes are packed into one 3MF
that carries the tool changes. The changes are placed half a layer below the first
layer that uses the new extruder, so float rounding can't move them to a neighbour.
"""
from __future__ import annotations

import math
import struct
import zipfile
from pathlib import Path
from typing import Any
from xml.sax.saxutils import quoteattr

MAX_RANGES = 32
MAX_LAYER = 100_000
REGION_EXTRUDER_KEYS = ("perimeter_extruder", "infill_extruder", "solid_infill_extruder")
CUSTOM_GCODE_FILE = "Metadata/preFlight_custom_gcode_per_print_z.xml"
TOOL_CHANGE = 2  # CustomGCode::Type::ToolChange


def _whole(value: Any, low: int, high: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or int(value) != value or not low <= value <= high:
        raise ValueError(f"{name} must be a whole number from {low} to {high}")
    return int(value)


def print_extruder(params: dict[str, Any], extruder_count: int) -> int:
    if "print_extruder" not in params:
        return 1
    return _whole(params["print_extruder"], 1, extruder_count, "Print extruder")


def layer_ranges(params: dict[str, Any], extruder_count: int) -> list[dict[str, int]]:
    ranges = params.get("extruder_layer_ranges") or []
    if not isinstance(ranges, list) or len(ranges) > MAX_RANGES:
        raise ValueError(f"Extruder layer ranges must be a list of at most {MAX_RANGES}")
    if ranges and extruder_count < 2:
        raise ValueError("Extruder layer ranges need a printer with more than one extruder")
    result = []
    for item in ranges:
        if not isinstance(item, dict):
            raise ValueError("Each extruder layer range needs from_layer, to_layer and extruder")
        start = _whole(item.get("from_layer"), 1, MAX_LAYER, "From layer")
        end = _whole(item.get("to_layer"), start, MAX_LAYER, "To layer")
        result.append({"from_layer": start, "to_layer": end, "extruder": _whole(item.get("extruder"), 1, extruder_count, "Range extruder")})
    result.sort(key=lambda r: r["from_layer"])
    for before, after in zip(result, result[1:]):
        if after["from_layer"] <= before["to_layer"]:
            raise ValueError(f"Extruder layer ranges overlap at layer {after['from_layer']}")
    return result


def region_settings(params: dict[str, Any], extruder_count: int) -> dict[str, str]:
    """Config keys that make every region print with the chosen extruder. Support keeps
    preFlight's default of the active extruder, so it follows layer-range tool changes."""
    tool = print_extruder(params, extruder_count)
    return {key: str(tool) for key in REGION_EXTRUDER_KEYS}


def tool_changes(params: dict[str, Any], extruder_count: int) -> list[tuple[float, int]]:
    """(print_z, extruder) switches for the layer ranges, in print order."""
    default = print_extruder(params, extruder_count)
    ranges = layer_ranges(params, extruder_count)
    first = float(params.get("first_layer_height") or 0.2)
    height = float(params.get("layer_height") or 0.2)

    def below(layer: int) -> float:
        top = first + (layer - 1) * height
        return round(top - (first if layer == 1 else height) / 2, 6)

    changes, current = [], default
    for index, item in enumerate(ranges):
        if item["extruder"] != current:
            changes.append((below(item["from_layer"]), item["extruder"]))
            current = item["extruder"]
        following = ranges[index + 1] if index + 1 < len(ranges) else None
        if current != default and not (following and following["from_layer"] == item["to_layer"] + 1):
            changes.append((below(item["to_layer"] + 1), default))
            current = default
    return changes


def _read_stl(path: Path) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    data = path.read_bytes()
    triangles: list[tuple[tuple[float, ...], ...]] = []
    if len(data) >= 84 and 84 + 50 * struct.unpack_from("<I", data, 80)[0] == len(data):
        for index in range(struct.unpack_from("<I", data, 80)[0]):
            values = struct.unpack_from("<12f", data, 84 + 50 * index)
            triangles.append((values[3:6], values[6:9], values[9:12]))
    else:
        corners = []
        for line in data.decode("utf-8", errors="replace").splitlines():
            parts = line.split()
            if parts[:1] == ["vertex"] and len(parts) == 4:
                corners.append(tuple(float(v) for v in parts[1:]))
        if len(corners) % 3:
            raise ValueError(f"{path.name} is not a valid STL")
        triangles = [tuple(corners[i:i + 3]) for i in range(0, len(corners), 3)]
    if not triangles:
        raise ValueError(f"{path.name} has no triangles")
    vertices: list[tuple[float, float, float]] = []
    index_of: dict[tuple[float, float, float], int] = {}
    faces = []
    for triangle in triangles:
        ids = []
        for corner in triangle:
            if not all(math.isfinite(v) for v in corner):
                raise ValueError(f"{path.name} has non-finite coordinates")
            key = tuple(float(v) for v in corner)
            if key not in index_of:
                index_of[key] = len(vertices)
                vertices.append(key)
            ids.append(index_of[key])
        if len(set(ids)) == 3:
            faces.append(tuple(ids))
    return vertices, faces


def write_project(mesh_paths: list[Path], changes: list[tuple[float, int]], output: Path) -> Path:
    """Pack STL meshes, in place, into a 3MF whose per-height tool changes preFlight applies."""
    if any(path.suffix.lower() != ".stl" for path in mesh_paths):
        raise ValueError("Extruder layer ranges need STL meshes")
    objects, items = [], []
    for number, path in enumerate(mesh_paths, start=1):
        vertices, faces = _read_stl(path)
        vertex_xml = "".join(f'<vertex x="{x:.9g}" y="{y:.9g}" z="{z:.9g}"/>' for x, y, z in vertices)
        face_xml = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in faces)
        objects.append(f'<object id="{number}" name={quoteattr(path.stem)} type="model"><mesh><vertices>{vertex_xml}</vertices><triangles>{face_xml}</triangles></mesh></object>')
        items.append(f'<item objectid="{number}"/>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<resources>{"".join(objects)}</resources><build>{"".join(items)}</build></model>')
    codes = "".join(f'<code print_z="{z:g}" type="{TOOL_CHANGE}" extruder="{tool}" color="" extra="" gcode="tool_change"/>' for z, tool in changes)
    custom = ('<?xml version="1.0" encoding="utf-8"?>\n'
              f'<custom_gcodes_per_print_z bed_idx="0">{codes}<mode value="MultiAsSingle"/></custom_gcodes_per_print_z>')
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                         '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                         '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        archive.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                         '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        archive.writestr("3D/3dmodel.model", model)
        archive.writestr(CUSTOM_GCODE_FILE, custom)
    return output
