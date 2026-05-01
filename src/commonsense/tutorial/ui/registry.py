"""Named-widget lookup.

Editor registers important widgets by short name (`palette`, `canvas`,
`play_btn`…). Tutorial steps reference widgets by the same name. Registry
resolves at render time — bind order doesn't matter.

Names are intentionally short and stable; treat the keyset as an API.
"""
from __future__ import annotations

from typing import Dict, Optional

import tkinter as tk


class WidgetRegistry:
    def __init__(self) -> None:
        self._by_name: Dict[str, tk.Misc] = {}

    def register(self, name: str, widget: tk.Misc) -> None:
        if not name or not isinstance(name, str):
            raise ValueError(f"bad widget name: {name!r}")
        self._by_name[name] = widget

    def get(self, name: Optional[str]) -> Optional[tk.Misc]:
        if name is None:
            return None
        return self._by_name.get(name)

    def names(self) -> list:
        return sorted(self._by_name.keys())

    def bbox(self, name: Optional[str]) -> Optional[tuple]:
        """(root_x, root_y, width, height) for a registered widget, or None.

        Returns None if the widget is unknown or not yet mapped to the screen
        (winfo_rootx returns 0 before the widget is laid out — guard against
        rendering the spotlight at the screen origin during init).
        """
        w = self.get(name)
        if w is None:
            return None
        try:
            w.update_idletasks()
            x = w.winfo_rootx()
            y = w.winfo_rooty()
            ww = w.winfo_width()
            hh = w.winfo_height()
        except tk.TclError:
            return None
        if ww <= 1 or hh <= 1:
            return None
        return (x, y, ww, hh)
