"""Confetti — 50 little colored rectangles fall over the editor for 1.5s.

Pure tk.Canvas, no images, no extensions. Spawns a borderless transparent
Toplevel covering the root, draws particles, animates them downward + sideways
with a tiny rotation flicker (toggle aspect ratio).

`burst()` is fire-and-forget. Multiple bursts overlap fine.
"""
from __future__ import annotations

import random
from typing import List, Optional, Tuple

import tkinter as tk

from .theme import THEME

_DURATION_MS = 1500
_FRAME_MS = 33
_NUM_PARTICLES = 60


class _Particle:
    __slots__ = ("rect_id", "x", "y", "vx", "vy", "size", "color", "tilt")

    def __init__(self, x: float, y: float, color: str) -> None:
        self.x = x
        self.y = y
        self.vx = random.uniform(-2.5, 2.5)
        self.vy = random.uniform(2.0, 5.0)
        self.size = random.randint(6, 12)
        self.color = color
        self.tilt = 0
        self.rect_id: int = 0


class Confetti:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self._win: Optional[tk.Toplevel] = None
        self._canvas: Optional[tk.Canvas] = None
        self._particles: List[_Particle] = []
        self._after_id = None  # type: ignore[assignment]
        self._elapsed_ms = 0

    def burst(self) -> None:
        self._teardown()  # if a previous burst is still running, replace it

        try:
            self.root.update_idletasks()
        except tk.TclError:
            return
        rx = self.root.winfo_rootx()
        ry = self.root.winfo_rooty()
        rw = self.root.winfo_width()
        rh = self.root.winfo_height()
        if rw <= 1 or rh <= 1:
            return

        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        try:
            win.attributes("-topmost", True)
        except tk.TclError:
            pass
        try:
            # The background color is the "transparent" one — alpha works on
            # most Linux WMs even if -transparentcolor doesn't.
            win.attributes("-alpha", 0.92)
        except tk.TclError:
            pass
        win.configure(bg=THEME["bubble_bg"])
        win.geometry(f"{rw}x{rh}+{rx}+{ry}")

        canvas = tk.Canvas(win, width=rw, height=rh, bg=THEME["bubble_bg"],
                           highlightthickness=0, bd=0)
        canvas.pack()

        palette = THEME["confetti_palette"]
        spawn_y = rh * 0.15
        for _ in range(_NUM_PARTICLES):
            p = _Particle(
                x=random.uniform(rw * 0.2, rw * 0.8),
                y=spawn_y + random.uniform(-30, 30),
                color=random.choice(palette),
            )
            p.rect_id = canvas.create_rectangle(
                p.x, p.y, p.x + p.size, p.y + p.size,
                fill=p.color, outline="",
            )
            self._particles.append(p)

        self._win = win
        self._canvas = canvas
        self._elapsed_ms = 0
        self._tick()

    # ── internals ───────────────────────────────────────────────────────────
    def _tick(self) -> None:
        if self._canvas is None:
            return
        self._elapsed_ms += _FRAME_MS
        if self._elapsed_ms >= _DURATION_MS:
            self._teardown()
            return

        for p in self._particles:
            p.x += p.vx
            p.y += p.vy
            p.vy += 0.18  # gravity
            p.tilt = (p.tilt + 1) % 2
            w = p.size if p.tilt == 0 else max(2, p.size // 3)
            try:
                self._canvas.coords(p.rect_id, p.x, p.y, p.x + w, p.y + p.size)
            except tk.TclError:
                return
        self._after_id = self.root.after(_FRAME_MS, self._tick)

    def _teardown(self) -> None:
        if self._after_id is not None:
            try:
                self.root.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None
        if self._win is not None:
            try:
                self._win.destroy()
            except tk.TclError:
                pass
        self._win = None
        self._canvas = None
        self._particles.clear()
        self._elapsed_ms = 0
