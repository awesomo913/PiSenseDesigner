"""EventBus — decoupled editor→tutorial signaling.

Editor calls `bus.emit("paint", x=x, y=y, idx=idx)`.
Tutorial calls `bus.on("paint", handler)` to subscribe.

Sync, in-process, no thread safety needed (Tk single-threaded GUI).
Handler exceptions are swallowed and logged so a buggy listener can't
break the editor.
"""
from __future__ import annotations

import sys
import traceback
from typing import Any, Callable, Dict, List

Handler = Callable[..., None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: Dict[str, List[Handler]] = {}

    def on(self, event: str, handler: Handler) -> Callable[[], None]:
        """Subscribe `handler` to `event`. Returns an unsubscribe callable."""
        self._handlers.setdefault(event, []).append(handler)

        def _off() -> None:
            try:
                self._handlers.get(event, []).remove(handler)
            except ValueError:
                pass

        return _off

    def emit(self, event: str, **payload: Any) -> None:
        """Call every handler registered for `event`. Errors are isolated."""
        for h in list(self._handlers.get(event, [])):
            try:
                h(**payload)
            except Exception:
                # Log but never raise — a misbehaving tutorial listener must
                # not be able to crash the editor's paint/save path.
                traceback.print_exc(file=sys.stderr)

    def clear(self) -> None:
        self._handlers.clear()

    def listener_count(self, event: str) -> int:
        return len(self._handlers.get(event, []))
