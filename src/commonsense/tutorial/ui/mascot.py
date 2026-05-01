"""Sparky — the tutorial mascot.

Pixel-art bot rendered in a tk.Canvas. 8x8 grid scaled up. Each pose is a
list of "row strings" where each character maps to a color key in `THEME`.
Animation = loop through `pose_frames`, redraw on after().

Poses:
    idle   — neutral, occasional blink
    wave   — arm up/down (welcome step)
    cheer  — arms up, sparkle eyes (gate-hit reward)
    point  — arm extended right (steps that point at a target)
"""
from __future__ import annotations

from typing import Dict, List

import tkinter as tk

from .theme import MASCOT_PX, THEME

# Color key → THEME entry
_PALETTE = {
    ".": None,                      # transparent
    "Y": "sparky_yellow",
    "E": "sparky_eye",
    "C": "sparky_cheek",
    "O": "sparky_outline",
}

# 8x8 frames. "." = transparent.
# Idle Sparky — round yellow body, two black eyes, pink cheek dot.
_IDLE_OPEN = [
    "..OOOO..",
    ".OYYYYO.",
    "OYYYYYYO",
    "OYEYYEY O".replace(" ", "Y"),
    "OYYYYYYO",
    "OYCYYCY O".replace(" ", "Y"),
    ".OYYYYO.",
    "..OOOO..",
]
_IDLE_BLINK = [
    "..OOOO..",
    ".OYYYYO.",
    "OYYYYYYO",
    "OYOYYOY O".replace(" ", "Y"),  # eyes closed → outline line
    "OYYYYYYO",
    "OYCYYCY O".replace(" ", "Y"),
    ".OYYYYO.",
    "..OOOO..",
]

_WAVE_DOWN = list(_IDLE_OPEN)
_WAVE_UP = [
    "..OOOO.Y",
    ".OYYYYOY",
    "OYYYYYYO",
    "OYEYYEY O".replace(" ", "Y"),
    "OYYYYYYO",
    "OYCYYCY O".replace(" ", "Y"),
    ".OYYYYO.",
    "..OOOO..",
]

_CHEER_LEFT = [
    "Y.OOOO.Y",
    "YOYYYYO Y".replace(" ", "Y"),
    "OYYYYYYO",
    "OY*YY*Y O".replace(" ", "Y").replace("*", "E"),
    "OYYYYYYO",
    "OYCYYCY O".replace(" ", "Y"),
    ".OYYYYO.",
    "..OOOO..",
]
_CHEER_RIGHT = list(_CHEER_LEFT)  # symmetric — same frame, simulates bounce

_POINT_RIGHT = [
    "..OOOO..",
    ".OYYYYO.",
    "OYYYYYYO",
    "OYEYYEY O".replace(" ", "Y") + "OYYO",
    "OYYYYYYOYYYY",
    "OYCYYCY O".replace(" ", "Y"),
    ".OYYYYO.",
    "..OOOO..",
]


def _pad(rows: List[str], width: int = 8) -> List[str]:
    """Truncate or pad rows to a fixed width, swapping spaces for transparency."""
    out: List[str] = []
    for r in rows:
        r = r.replace(" ", ".")
        if len(r) < width:
            r = r.ljust(width, ".")
        out.append(r[:width])
    return out


_POSES: Dict[str, List[List[str]]] = {
    "idle":  [_pad(_IDLE_OPEN), _pad(_IDLE_OPEN), _pad(_IDLE_OPEN), _pad(_IDLE_BLINK)],
    "wave":  [_pad(_WAVE_DOWN), _pad(_WAVE_UP)],
    "cheer": [_pad(_CHEER_LEFT), _pad(_CHEER_RIGHT)],
    "point": [_pad(_POINT_RIGHT)],
}

_FRAME_MS = 350


class SparkyMascot:
    def __init__(self, parent: tk.Misc, size: int = MASCOT_PX) -> None:
        self.size = size
        self.cell = size // 8
        self.canvas = tk.Canvas(
            parent, width=size, height=size,
            bg=THEME["bubble_bg"], highlightthickness=0, bd=0,
        )
        self._pose: str = "idle"
        self._frame_idx: int = 0
        self._after_id = None  # type: ignore[assignment]
        self._cells: List[List[int]] = [[0] * 8 for _ in range(8)]
        self._build_cells()
        self.set_pose("idle")

    # ── public API ──────────────────────────────────────────────────────────
    def set_pose(self, pose: str) -> None:
        if pose not in _POSES:
            pose = "idle"
        self._pose = pose
        self._frame_idx = 0
        self._draw_current_frame()
        self._restart_loop()

    def stop(self) -> None:
        if self._after_id is not None:
            try:
                self.canvas.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

    def destroy(self) -> None:
        self.stop()
        try:
            self.canvas.destroy()
        except tk.TclError:
            pass

    # ── internals ───────────────────────────────────────────────────────────
    def _build_cells(self) -> None:
        c = self.cell
        for y in range(8):
            for x in range(8):
                self._cells[y][x] = self.canvas.create_rectangle(
                    x * c, y * c, (x + 1) * c, (y + 1) * c,
                    fill=THEME["bubble_bg"], outline="",
                )

    def _draw_current_frame(self) -> None:
        frames = _POSES[self._pose]
        rows = frames[self._frame_idx % len(frames)]
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                key = _PALETTE.get(ch)
                color = THEME[key] if key else THEME["bubble_bg"]
                self.canvas.itemconfigure(self._cells[y][x], fill=color)

    def _restart_loop(self) -> None:
        self.stop()
        if len(_POSES[self._pose]) <= 1:
            return  # static pose — no animation needed
        self._after_id = self.canvas.after(_FRAME_MS, self._tick)

    def _tick(self) -> None:
        self._frame_idx += 1
        self._draw_current_frame()
        self._after_id = self.canvas.after(_FRAME_MS, self._tick)
