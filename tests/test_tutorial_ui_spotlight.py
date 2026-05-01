"""Spotlight geometry — clip math is pure, testable headless.

The 4-strip layout is the trickiest part of the spotlight. Verify that:
- A target inside root produces 4 strips covering everything except the hole
- A target on root's edge produces 3 strips (one is zero-area)
- A target outside root is clipped to nothing visible
- A None target dims the whole root
"""
from __future__ import annotations

import os

import pytest

_HAS_DISPLAY = bool(os.environ.get("DISPLAY")) or os.name == "nt"


@pytest.mark.skipif(not _HAS_DISPLAY, reason="needs Tk display")
def test_clip_keeps_target_inside_root():
    from commonsense.tutorial.ui.spotlight import Spotlight

    root_bbox = (0, 0, 1000, 800)
    target = (300, 200, 200, 100)
    out = Spotlight._clip(target, root_bbox)
    assert out == (300, 200, 200, 100)


@pytest.mark.skipif(not _HAS_DISPLAY, reason="needs Tk display")
def test_clip_handles_target_off_left_edge():
    from commonsense.tutorial.ui.spotlight import Spotlight

    root_bbox = (100, 100, 800, 600)
    target = (50, 200, 200, 100)  # left edge starts before root
    x, y, w, h = Spotlight._clip(target, root_bbox)
    # Should clip to root's left edge (100, 200) and reduce width by 50.
    assert x == 100
    assert y == 200
    assert w == 150
    assert h == 100


@pytest.mark.skipif(not _HAS_DISPLAY, reason="needs Tk display")
def test_clip_handles_target_fully_outside():
    from commonsense.tutorial.ui.spotlight import Spotlight

    root_bbox = (0, 0, 1000, 800)
    target = (-200, -200, 50, 50)
    x, y, w, h = Spotlight._clip(target, root_bbox)
    assert w == 0 and h == 0


@pytest.mark.skipif(not _HAS_DISPLAY, reason="needs Tk display")
def test_show_with_no_target_creates_one_full_dim():
    """target=None → single full-screen dim, no hole."""
    import tkinter as tk

    from commonsense.tutorial.ui.spotlight import Spotlight

    root = tk.Tk()
    root.geometry("400x300+0+0")
    try:
        root.update_idletasks()
        s = Spotlight(root)
        s.show(None)
        assert s.visible
        # 4-strip layout collapses to 1 full strip when no hole is requested.
        assert len(s._strips) == 1
        s.hide()
        assert not s.visible
        assert len(s._strips) == 0
    finally:
        root.destroy()


@pytest.mark.skipif(not _HAS_DISPLAY, reason="needs Tk display")
def test_show_with_inset_target_creates_four_strips():
    import tkinter as tk

    from commonsense.tutorial.ui.spotlight import Spotlight

    root = tk.Tk()
    root.geometry("400x300+0+0")
    try:
        root.update_idletasks()
        rx = root.winfo_rootx()
        ry = root.winfo_rooty()
        # A target firmly inside root → all 4 strips have non-zero area.
        target = (rx + 100, ry + 80, 80, 60)
        s = Spotlight(root)
        s.show(target)
        assert s.visible
        assert len(s._strips) == 4
        s.hide()
    finally:
        root.destroy()


@pytest.mark.skipif(not _HAS_DISPLAY, reason="needs Tk display")
def test_show_then_hide_destroys_all_strips():
    """No leaked toplevels after hide — important for repeated tutorial runs."""
    import tkinter as tk

    from commonsense.tutorial.ui.spotlight import Spotlight

    root = tk.Tk()
    root.geometry("400x300+0+0")
    try:
        root.update_idletasks()
        rx = root.winfo_rootx()
        ry = root.winfo_rooty()
        s = Spotlight(root)
        s.show((rx + 50, ry + 50, 100, 100))
        s.show((rx + 60, ry + 60, 80, 80))  # second show should replace first
        # Pump events so destroy() takes effect.
        root.update_idletasks()
        # No way to assert "no Toplevels" cheaply; assert handle list is clean.
        assert len(s._strips) == 4
        s.hide()
        assert len(s._strips) == 0
    finally:
        root.destroy()
