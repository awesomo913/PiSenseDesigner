"""Standalone animation player — loops a JSON animation on the Sense HAT.

Used by the editor to keep an animation playing after the window closes.
Detached subprocess (Popen with start_new_session=True) survives parent exit.

Usage:  python -m commonsense.sense_paint.play_anim <path-to-json>
"""
from __future__ import annotations

import json
import sys
import time
from typing import List, Tuple

try:
    from sense_hat import SenseHat  # type: ignore
except Exception:  # pragma: no cover
    SenseHat = None  # type: ignore


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: play_anim <json>", file=sys.stderr)
        return 2
    path = sys.argv[1]
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"can't open {path}: {e}", file=sys.stderr)
        return 1

    palette: List[Tuple[int, int, int]] = [tuple(c) for c in data.get("palette", [])]
    frames: List[List[int]] = data.get("frames", [])
    delay_ms = max(50, int(data.get("frame_delay_ms", 250)))
    loop = bool(data.get("loop", True))

    if not palette or not frames:
        return 1

    if SenseHat is None:
        return 0  # no hardware, silent exit
    try:
        hat = SenseHat()
    except Exception:
        return 0

    delay = delay_ms / 1000.0
    idx = 0
    try:
        while True:
            pixels = [palette[i] for i in frames[idx]]
            try:
                hat.set_pixels(pixels)  # type: ignore[attr-defined]
            except Exception:
                pass
            time.sleep(delay)
            idx += 1
            if idx >= len(frames):
                if not loop:
                    break
                idx = 0
    except KeyboardInterrupt:
        pass
    finally:
        try:
            hat.clear()  # type: ignore[attr-defined]
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
