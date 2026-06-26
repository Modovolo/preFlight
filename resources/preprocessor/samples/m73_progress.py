"""M73 progress code insertion - as a pre-processor script.

This is functionally equivalent to what preFlight does natively
during processing, but implemented as a Python script to
demonstrate that even core G-code processing can live here.

NOT intended for production use - preFlight's built-in M73 handling
is faster and more accurate since it runs inside the time estimator.
This exists purely as a proof of concept.
"""

import preFlight
from preFlight import MoveType


def process(gcode: preFlight.GCode):
    total_time = gcode.time_estimate_normal
    if total_time <= 0:
        return

    last_pct = -1
    last_remaining = -1
    insertions = 0

    for move in gcode.moves:
        elapsed = move.time
        remaining = total_time - elapsed
        pct = int(elapsed / total_time * 100)
        remaining_min = int(remaining / 60)

        # Only insert when percentage or remaining minutes change
        if pct != last_pct or remaining_min != last_remaining:
            gcode.insert(
                move.gcode_line_id - 1,
                f"M73 P{pct} R{remaining_min}"
            )
            last_pct = pct
            last_remaining = remaining_min
            insertions += 1

    print(f"[m73_progress] Inserted {insertions} progress markers "
          f"for {total_time / 60:.0f} minute print")
