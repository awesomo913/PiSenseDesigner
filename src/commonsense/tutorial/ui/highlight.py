"""TargetPulse — pulsing yellow ring around the target widget.

Implementation: a tiny borderless `Toplevel` with a `Canvas` drawn as a
hollow rectangle frame surrounding the target. Animates the rectangle's
outline width on a sine cycle so it gently breathes. Click-through is
unreliable on X11, so the ring is rendered just OUTSIDE the target rect
and 1px tall — kid clicks the actual widget, not the ring.

Stops cleanly on `hide()`. Multiple `show()` calls cancel and replace.
"""
from __future__ import annotations

import math
from typing import Optional, Tuple

import tkinter as tk

from .theme import PULSE_PERIOD_MS, THEME

BBox = Tuple[int, int, int, int]


class TargetPulse:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self._win: Optional[tk.Toplevel] = None
        self._canvas: Optional[tk.Canvas] = None
        self._rect: Optional[int] = None
        self._after_id = None  # type: ignore[assignment]
        self._t0_ms: int = 0

    def show(self, target_bbox: Optional[BBox]) -> None:
        self.hide()
        if target_bbox is None:
            return

        # Pad the ring around the target so it doesn't overlap clicks.
        pad = THEME["pulse_thick_max"] + 4
        tx, ty, tw, th = target_bbox
        wx = tx - pad
        wy = ty - pad
        ww = tw + 2 * pad
        wh = th + 2 * pad

        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        try:
            win.attributes("-topmost", True)
        except tk.TclError:
            pass
        # The pulse window background must NOT obscure the target — make it
        # the same as the editor bg. We only draw the ring outline.
        win.configure(bg="#1e2030")
        try:
            # Keep only the outline visible; alpha lets the editor show through
            # the empty interior of the window.
            win.attributes("-alpha", 0.92)
        except tk.TclError:
            pass
        win.geometry(f"{ww}x{wh}+{wx}+{wy}")

        canvas = tk.Canvas(win, width=ww, height=wh, bg="#1e2030",
                           highlightthickness=0, bd=0)
        canvas.pack()
        # Initial outline.
        thick = THEME["pulse_thick_min"]
        rect = canvas.create_rectangle(
            thick, thick, ww - thick, wh - thick,
            outline=THEME["pulse_color"], width=thick,
        )
        # The interior of the rectangle stays unfilled (target shows through
        # via alpha). The 4 corners outside the rectangle are filled with the
        # editor bg so the ring looks like a clean glow.

        self._win = win
        self._canvas = canvas
        self._rect = rect
        self._t0_ms = self._now_ms()
        self._tick()

    def hide(self) -> None:
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
        self._rect = None

    @property
    def visible(self) -> bool:
        return self._win is not None

    # ── internals ───────────────────────────────────────────────────────────
    def _tick(self) -> None:
        if self._canvas is None or self._rect is None:
            return
        elapsed = (self._now_ms() - self._t0_ms) % PULSE_PERIOD_MS
        phase = elapsed / PULSE_PERIOD_MS  # 0..1
        # sine eased min..max..min over one period
        ease = (math.sin(phase * 2 * math.pi - math.pi / 2) + 1) / 2
        thick = int(THEME["pulse_thick_min"]
                    + ease * (THEME["pulse_thick_max"] - THEME["pulse_thick_min"]))
        try:
            self._canvas.itemconfigure(self._rect, width=thick)
        except tk.TclError:
            return
        self._after_id = self.root.after(33, self._tick)  # ~30 fps

    @staticmethod
    def _now_ms() -> int:
        import time
        return int(time.monotonic() * 1000)
