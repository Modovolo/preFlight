"""Detailed print analysis and statistics.

Generates a breakdown of time, filament, and move counts by feature type.
Identifies potential problem areas like excessive travel, high retraction
counts, or layers that take disproportionately long.

This script is read-only - it analyzes but doesn't modify the G-code.
"""

import preFlight
from preFlight import MoveType, ExtrusionRole
from collections import defaultdict
import math


def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h}h {m:02d}m"
    return f"{m}m {s:02d}s"


def distance(m1, m2):
    dx = m2.x - m1.x
    dy = m2.y - m1.y
    return math.sqrt(dx * dx + dy * dy)


def process(gcode: preFlight.GCode):
    # Time by extrusion role
    time_by_role = defaultdict(float)
    moves_by_role = defaultdict(int)
    flow_by_role = defaultdict(float)

    # Travel stats
    total_travel_dist = 0.0
    total_extrude_dist = 0.0
    retraction_count = 0
    wipe_count = 0
    tool_changes = 0

    # Layer timing for outlier detection
    layer_times = []

    prev_move = None
    for move in gcode.moves:
        if move.type == MoveType.Extrude:
            time_by_role[move.role] += move.time
            moves_by_role[move.role] += 1
            flow_by_role[move.role] += move.delta_e
            if prev_move:
                total_extrude_dist += distance(prev_move, move)
        elif move.type == MoveType.Travel and prev_move:
            total_travel_dist += distance(prev_move, move)
        elif move.type == MoveType.Retract:
            retraction_count += 1
        elif move.type == MoveType.Wipe:
            wipe_count += 1
        elif move.type == MoveType.ToolChange:
            tool_changes += 1
        prev_move = move

    for layer in gcode.layers:
        layer_times.append((layer.id, layer.z, layer.time))

    # Print summary
    total_time = gcode.time_estimate_normal
    print("=" * 60)
    print("PRINT ANALYSIS")
    print("=" * 60)
    print(f"Total time:  {format_time(total_time)}")
    print(f"Layers:      {len(gcode.layers)}")
    print(f"Max height:  {gcode.max_print_height:.1f}mm")
    print(f"Extruders:   {gcode.extruder_count}")
    print(f"Total moves: {len(gcode.moves)}")
    print()

    # Time breakdown by role
    print("TIME BY FEATURE:")
    print("-" * 60)
    for role in sorted(time_by_role, key=lambda r: -time_by_role[r]):
        t = time_by_role[role]
        pct = t / total_time * 100 if total_time > 0 else 0
        count = moves_by_role[role]
        filament = flow_by_role[role]
        print(f"  {role.name:28s} {format_time(t):>8s} ({pct:5.1f}%)  "
              f"{count:6d} moves  {filament:8.1f}mm filament")
    print()

    # Travel analysis
    print("TRAVEL ANALYSIS:")
    print("-" * 60)
    total_dist = total_travel_dist + total_extrude_dist
    travel_pct = total_travel_dist / total_dist * 100 if total_dist > 0 else 0
    print(f"  Extrusion distance: {total_extrude_dist / 1000:.1f}m")
    print(f"  Travel distance:    {total_travel_dist / 1000:.1f}m ({travel_pct:.1f}% of total)")
    print(f"  Retractions:        {retraction_count}")
    print(f"  Wipes:              {wipe_count}")
    print(f"  Tool changes:       {tool_changes}")
    print()

    # Filament usage
    print("FILAMENT USAGE:")
    print("-" * 60)
    for role, usage in gcode.filament_by_role.items():
        print(f"  {role.name:28s} {usage.meters:6.1f}m  {usage.grams:6.1f}g")
    print()

    for ext_id, usage in gcode.filament_by_extruder.items():
        print(f"  Extruder T{ext_id}: {usage.meters:.1f}m, "
              f"{usage.grams:.1f}g, ${usage.cost:.2f}")
    print()

    # Slowest layers
    print("SLOWEST LAYERS (top 10):")
    print("-" * 60)
    layer_times.sort(key=lambda x: -x[2])
    for layer_id, z, t in layer_times[:10]:
        print(f"  Layer {layer_id:4d}  Z={z:7.2f}mm  {format_time(t)}")
    print()

    # Flow rate warnings
    print("FLOW RATE WARNINGS:")
    print("-" * 60)
    high_flow_count = 0
    for move in gcode.moves:
        if move.type == MoveType.Extrude and move.volumetric_rate > 15.0:
            if high_flow_count < 5:
                print(f"  Layer {move.layer_id:4d}: {move.role.name} at "
                      f"{move.volumetric_rate:.1f} mm3/s "
                      f"(F{move.feedrate:.0f})")
            high_flow_count += 1
    if high_flow_count > 5:
        print(f"  ... and {high_flow_count - 5} more")
    if high_flow_count == 0:
        print("  None - all moves within safe flow rates")

    print("=" * 60)
