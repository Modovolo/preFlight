"""Checks the preFlight config the slicer service writes from client settings."""
from app import generate_preflight_config


def parse(text):
    return dict(line.split(" = ", 1) for line in text.strip().splitlines())


PROFILE = {"buildVolume": {"x": 220, "y": 220, "z": 250}, "extruderCount": 2}


def test_cooling_retraction_and_filament_type_repeat_per_extruder():
    config = parse(generate_preflight_config({
        "filament_type": "petg", "min_fan_speed": 30, "max_fan_speed": 50, "bridge_fan_speed": 100,
        "disable_fan_first_layers": 3, "retract_length": 1.0, "retract_speed": 30, "retract_lift": 0.2,
    }, PROFILE))
    assert config["filament_type"] == "PETG;PETG"
    assert config["cooling"] == "1,1"
    assert config["fan_always_on"] == "1,1"
    assert config["min_fan_speed"] == "30,30"
    assert config["max_fan_speed"] == "50,50"
    assert config["bridge_fan_speed"] == "100,100"
    assert config["disable_fan_first_layers"] == "3,3"
    assert config["retract_length"] == "1,1"
    assert config["retract_speed"] == config["deretract_speed"] == "30,30"
    assert config["retract_lift"] == "0.2,0.2"


def test_fan_off_unknown_types_and_out_of_range_values_are_made_safe():
    config = parse(generate_preflight_config({
        "filament_type": "unobtainium", "min_fan_speed": 40, "max_fan_speed": 10,
        "bridge_fan_speed": 250, "disable_fan_first_layers": -2, "retract_length": -1, "retract_lift": -0.5,
    }, {"extruderCount": 1}))
    assert "filament_type" not in config
    assert config["max_fan_speed"] == "40", "max is never below min"
    assert config["bridge_fan_speed"] == "100"
    assert config["disable_fan_first_layers"] == "0"
    assert config["retract_length"] == "0"
    assert config["retract_lift"] == "0"
    off = parse(generate_preflight_config({"min_fan_speed": 0, "max_fan_speed": 15}, {}))
    assert off["fan_always_on"] == "0"


def test_older_clients_without_these_settings_keep_preflight_defaults():
    config = parse(generate_preflight_config({"layer_height": 0.2}, PROFILE))
    for key in ("filament_type", "cooling", "min_fan_speed", "retract_length", "retract_speed", "retract_lift"):
        assert key not in config


def unescape_cstyle(text):
    """Python port of preFlight's unescape_string_cstyle (src/libslic3r/Config.cpp)."""
    out, i = [], 0
    while i < len(text):
        c = text[i]
        if c == "\\":
            i += 1
            c = {"r": "\r", "n": "\n"}.get(text[i], text[i])
        out.append(c)
        i += 1
    return "".join(out)


def test_start_and_end_gcode_survive_the_ini_round_trip():
    start = 'G28\nSTART_PRINT EXTRUDER_TEMP=[first_layer_temperature] BED_TEMP=[first_layer_bed_temperature]\n; path C:\\temp\\x\n{if layer_height > 0.2}M117 coarse{endif}\n'
    text = generate_preflight_config({}, {**PROFILE, "startGcode": start, "endGcode": "END_PRINT\r\n"})
    config = parse(text)
    assert unescape_cstyle(config["start_gcode"]) == start
    assert unescape_cstyle(config["end_gcode"]) == "END_PRINT\n", "Windows line endings are normalized"


def test_a_macro_cannot_inject_other_settings():
    text = generate_preflight_config({}, {**PROFILE, "startGcode": "G28\nperimeters = 99\npost_process = /bin/sh"})
    keys = [line.split(" = ", 1)[0] for line in text.strip().splitlines()]
    assert "post_process" not in keys and keys.count("perimeters") == 1
    assert parse(text)["perimeters"] != "99"


def test_blank_macros_keep_preflight_defaults_and_bad_ones_are_rejected():
    config = parse(generate_preflight_config({}, {**PROFILE, "startGcode": "  \n", "endGcode": ""}))
    assert "start_gcode" not in config and "end_gcode" not in config
    for bad in ({"startGcode": 5}, {"endGcode": "x" * 20001}, {"startGcode": "G28\0"}):
        try:
            generate_preflight_config({}, {**PROFILE, **bad})
        except ValueError:
            continue
        raise AssertionError(f"accepted {bad}")
