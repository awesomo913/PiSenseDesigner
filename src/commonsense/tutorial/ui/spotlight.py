"""Spotlight overlay — dims the screen, leaves a hole around the target.

Approach: 4 borderless `Toplevel`s (top/bottom/left/right strips) wrapping
the target rectangle. Together they cover the whole root window minus the
target hole. Target widget remains fully interactive.

Why 4 toplevels instead of one transparent window with a clipped region:
the X11 SHAPE extension is not portable across LXDE/Openbox + Tk. The
4-strip approach renders identically on every WM with no extension calls.

If `target_bbox` is None (step has no target — e.g. welcome step), the whole
root is dimmed uniformly.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

import tkinter as tk

from .theme import THEME

BBox = Tuple[int, int, int, int]


class Spotlight:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self._strips: List[tk.Toplevel] = []
        self._visible = False

    # ── public API ──────────────────────────────────────────────────────────
    def show(self, target_bbox: Optional[BBox]) -> None:
        """Dim everything except `target_bbox`. None → dim everything."""
        self.hide()
        root_bbox = self._root_bbox()
        if target_bbox is None:
            # Single full-screen dim — no hole.
            self._strips = [self._make_strip(*root_bbox)]
            self._visible = True
            return

        rx, ry, rw, rh = root_bbox
        tx, ty, tw, th = self._clip(target_bbox, root_bbox)

        # Build 4 strips: top, bottom, left, right. Skip zero-area strips.
        candidates = [
            (rx, ry, rw, ty - ry),                       # top
            (rx, ty + th, rw, (ry + rh) - (ty + th)),    # bottom
            (rx, ty, tx - rx, th),                       # left
            (tx + tw, ty, (rx + rw) - (tx + tw), th),    # right
        ]
        for x, y, w, h in candidates:
            if w > 0 and h > 0:
                self._strips.append(self._make_strip(x, y, w, h))
        self._visible = True

    def hide(self) -> None:
        for s in self._strips:
            try:
                s.destroy()
            except tk.TclError:
                pass
        self._strips.clear()
        self._visible = False

    @property
    def visible(self) -> bool:
        return self._visible

    # ── internals ───────────────────────────────────────────────────────────
    def _root_bbox(self) -> BBox:
        try:
            self.root.update_idletasks()
        except tk.TclError:
            pass
        return (
            self.root.winfo_rootx(),
            self.root.winfo_rooty(),
            self.root.winfo_width(),
            self.root.winfo_height(),
        )

    @staticmethod
    def _clip(target: BBox, root: BBox) -> BBox:
        """Clip target to root bounds — defensive against off-screen widgets."""
        tx, ty, tw, th = target
        rx, ry, rw, rh = root
        x0 = max(tx, rx)
        y0 = max(ty, ry)
        x1 = min(tx + tw, rx + rw)
        y1 = min(ty + th, ry + rh)
        return (x0, y0, max(0, x1 - x0), max(0, y1 - y0))

    def _make_strip(self, x: int, y: int, w: int, h: int) -> tk.Toplevel:
        s = tk.Toplevel(self.root)
        s.overrideredirect(True)             # no decorations, no taskbar entry
        try:
            s.attributes("-topmost", True)
        except tk.TclError:
            pass
        try:
            s.attributes("-alpha", THEME["dim_alpha"])
        except tk.TclError:
            pass
        s.configure(bg=THEME["dim_bg"])
        s.geometry(f"{w}x{h}+{x}+{y}")
        # Click-through is OS-dependent and unreliable on Linux X11. Keep the
        # strips opaque to clicks — that's actually a feature: it prevents
        # the kid from clicking the wrong thing while the tutorial guides
        # them. Target hole stays interactive.
        return s
