"""WidgetRegistry — naming, lookup, bbox handling."""
from __future__ import annotations

import os

import pytest

# Most CI hosts and Windows test runners don't have a display. Skip Tk tests
# unless DISPLAY is set or we're on Windows (where Tk works without it).
_HAS_DISPLAY = bool(os.environ.get("DISPLAY")) or os.name == "nt"


@pytest.mark.skipif(not _HAS_DISPLAY, reason="needs Tk display")
def test_register_and_get_resolves_widget():
    import tkinter as tk

    from commonsense.tutorial.ui.registry import WidgetRegistry

    root = tk.Tk()
    try:
        f = tk.Frame(root)
        reg = WidgetRegistry()
        reg.register("palette", f)
        assert reg.get("palette") is f
        assert reg.get("nope") is None
        assert reg.get(None) is None
        assert "palette" in reg.names()
    finally:
        root.destroy()


def test_register_rejects_empty_name():
    from commonsense.tutorial.ui.registry import WidgetRegistry

    reg = WidgetRegistry()
    with pytest.raises(ValueError):
        reg.register("", "anything")  # type: ignore[arg-type]


@pytest.mark.skipif(not _HAS_DISPLAY, reason="needs Tk display")
def test_bbox_returns_none_for_unmapped_widget():
    """Widget exists but isn't laid out yet → bbox returns None, not (0,0,1,1).
    The spotlight relies on this to avoid drawing at the screen origin."""
    import tkinter as tk

    from commonsense.tutorial.ui.registry import WidgetRegistry

    root = tk.Tk()
    try:
        f = tk.Frame(root, width=100, height=50)
        # Don't pack — widget never gets a real geometry.
        reg = WidgetRegistry()
        reg.register("orphan", f)
        assert reg.bbox("orphan") is None
    finally:
        root.destroy()


@pytest.mark.skipif(not _HAS_DISPLAY, reason="needs Tk display")
def test_bbox_returns_real_geometry_after_pack():
    import tkinter as tk

    from commonsense.tutorial.ui.registry import WidgetRegistry

    root = tk.Tk()
    root.geometry("400x300+0+0")
    try:
        f = tk.Frame(root, width=120, height=80, bg="red")
        f.pack(padx=10, pady=10)
        root.update_idletasks()
        reg = WidgetRegistry()
        reg.register("box", f)
        bbox = reg.bbox("box")
        assert bbox is not None
        x, y, w, h = bbox
        # Width/height should be roughly 120x80; allow some Tk geometry slack.
        assert w >= 100
        assert h >= 60
    finally:
        root.destroy()
