"""Extruder selection: config keys, per-layer tool changes and the 3MF they travel in."""
import struct
import xml.etree.ElementTree as ET
import zipfile

import pytest

import extruders
from app import generate_preflight_config


def parse(text):
    return dict(line.split(" = ", 1) for line in text.strip().splitlines())


PROFILE = {"buildVolume": {"x": 220, "y": 220, "z": 250}, "extruderCount": 3}
LAYERS = {"first_layer_height": 0.3, "layer_height": 0.2}


def test_print_extruder_sets_every_region_and_leaves_support_on_the_active_tool():
    config = parse(generate_preflight_config({"print_extruder": 2}, PROFILE))
    assert (config["perimeter_extruder"], config["infill_extruder"], config["solid_infill_extruder"]) == ("2", "2", "2")
    assert "support_material_extruder" not in config


def test_older_clients_without_an_extruder_keep_preflight_defaults():
    config = parse(generate_preflight_config({}, PROFILE))
    assert not set(extruders.REGION_EXTRUDER_KEYS) & set(config)


@pytest.mark.parametrize("value", [0, 4, 1.5, True, "2", None])
def test_invalid_print_extruders_are_rejected(value):
    with pytest.raises(ValueError):
        generate_preflight_config({"print_extruder": value}, PROFILE)


def test_no_ranges_means_no_tool_changes():
    assert extruders.tool_changes({"print_extruder": 2, **LAYERS}, 3) == []


def test_a_range_switches_in_and_back_half_a_layer_below_each_boundary():
    params = {"print_extruder": 1, "extruder_layer_ranges": [{"from_layer": 5, "to_layer": 10, "extruder": 2}], **LAYERS}
    # Layer n tops out at 0.3 + (n-1) * 0.2: layer 5 at 1.1, layer 11 at 2.3.
    assert extruders.tool_changes(params, 3) == [(1.0, 2), (2.2, 1)]


def test_a_range_from_the_first_layer_switches_inside_that_layer():
    params = {"print_extruder": 1, "extruder_layer_ranges": [{"from_layer": 1, "to_layer": 2, "extruder": 3}], **LAYERS}
    assert extruders.tool_changes(params, 3) == [(0.15, 3), (0.6, 1)]


def test_adjacent_ranges_switch_directly_and_ranges_on_the_default_add_nothing():
    params = {"print_extruder": 1, **LAYERS, "extruder_layer_ranges": [
        {"from_layer": 8, "to_layer": 9, "extruder": 3},
        {"from_layer": 3, "to_layer": 7, "extruder": 2},
        {"from_layer": 20, "to_layer": 25, "extruder": 1},
    ]}
    assert extruders.tool_changes(params, 3) == [(0.6, 2), (1.6, 3), (2.0, 1)]


@pytest.mark.parametrize("ranges, count", [
    ([{"from_layer": 1, "to_layer": 5, "extruder": 2}, {"from_layer": 5, "to_layer": 6, "extruder": 3}], 3),
    ([{"from_layer": 4, "to_layer": 3, "extruder": 2}], 3),
    ([{"from_layer": 0, "to_layer": 3, "extruder": 2}], 3),
    ([{"from_layer": 1, "to_layer": 3, "extruder": 4}], 3),
    ([{"from_layer": 1, "to_layer": 3}], 3),
    ([{"from_layer": 1, "to_layer": 3, "extruder": 1}], 1),
    ("1-3", 3),
    ([{"from_layer": n, "to_layer": n, "extruder": 2} for n in range(1, 40)], 3),
])
def test_invalid_ranges_are_rejected(ranges, count):
    with pytest.raises(ValueError):
        extruders.tool_changes({"extruder_layer_ranges": ranges, **LAYERS}, count)


def binary_stl(path, *triangles):
    data = bytearray(80) + struct.pack("<I", len(triangles))
    for triangle in triangles:
        data += struct.pack("<12fH", 0, 0, 1, *[v for corner in triangle for v in corner], 0)
    path.write_bytes(bytes(data))
    return path


def test_project_keeps_mesh_positions_and_carries_the_tool_changes(tmp_path):
    left = binary_stl(tmp_path / "model_0.stl", ((10, 10, 0), (20, 10, 0), (10, 20, 5)), ((20, 10, 0), (20, 20, 0), (10, 20, 5)))
    right = tmp_path / "model_1.stl"
    right.write_text("solid r\nfacet normal 0 0 1\nouter loop\nvertex 100 100 0\nvertex 110 100 0\nvertex 100 110 2.5\nendloop\nendfacet\nendsolid r\n")
    output = extruders.write_project([left, right], [(1.0, 2), (2.2, 1)], tmp_path / "plate.3mf")
    ns = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
    with zipfile.ZipFile(output) as archive:
        model = ET.fromstring(archive.read("3D/3dmodel.model"))
        custom = ET.fromstring(archive.read(extruders.CUSTOM_GCODE_FILE))
        assert "_rels/.rels" in archive.namelist() and "[Content_Types].xml" in archive.namelist()
    objects = model.findall("m:resources/m:object", ns)
    assert [o.get("name") for o in objects] == ["model_0", "model_1"]
    assert len(objects[0].findall(".//m:vertex", ns)) == 4, "shared corners are stored once"
    assert len(objects[0].findall(".//m:triangle", ns)) == 2
    assert [(v.get("x"), v.get("y"), v.get("z")) for v in objects[1].findall(".//m:vertex", ns)] == [("100", "100", "0"), ("110", "100", "0"), ("100", "110", "2.5")]
    assert [i.get("objectid") for i in model.findall("m:build/m:item", ns)] == ["1", "2"]
    assert all(i.get("transform") is None for i in model.findall("m:build/m:item", ns))
    assert custom.tag == "custom_gcodes_per_print_z" and custom.get("bed_idx") == "0"
    assert [(c.get("print_z"), c.get("type"), c.get("extruder"), c.get("extra")) for c in custom.findall("code")] == [("1", "2", "2", ""), ("2.2", "2", "1", "")]
    assert custom.find("mode").get("value") == "MultiAsSingle"


def test_project_rejects_non_stl_meshes(tmp_path):
    mesh = tmp_path / "model_0.obj"
    mesh.write_text("v 0 0 0\n")
    with pytest.raises(ValueError, match="STL"):
        extruders.write_project([mesh], [(1.0, 2)], tmp_path / "plate.3mf")
