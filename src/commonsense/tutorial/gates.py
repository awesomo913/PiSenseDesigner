"""Action gates — predicates that decide when a step is satisfied.

A gate is a small object with two methods:
    bind(bus, on_satisfied)    install bus subscriptions
    unbind()                   tear them down

When the gate's condition is met it calls `on_satisfied()` exactly once.
The TutorialRunner is responsible for binding the gate when a step starts
and unbinding it on advance.

Gates are intentionally tiny — a misbehaving gate must not corrupt the
editor. Keep them as pure as possible.
"""
from __future__ import annotations

from typing import Any, Callable, List, Optional

from .events import EventBus
from .model import GateName


class _Gate:
    def __init__(self) -> None:
        self._unsubs: List[Callable[[], None]] = []
        self._fired = False
        self._on_satisfied: Optional[Callable[[], None]] = None

    def bind(self, bus: EventBus, on_satisfied: Callable[[], None]) -> None:
        self._on_satisfied = on_satisfied
        self._fired = False
        self._install(bus)

    def unbind(self) -> None:
        for off in self._unsubs:
            off()
        self._unsubs.clear()
        self._on_satisfied = None

    def _fire(self) -> None:
        if self._fired:
            return
        self._fired = True
        cb = self._on_satisfied
        if cb is not None:
            cb()

    # --- subclasses override -------------------------------------------------
    def _install(self, bus: EventBus) -> None:  # pragma: no cover - abstract
        raise NotImplementedError


class _Immediate(_Gate):
    """Fires the moment it's bound. Used for "click Next" steps."""

    def _install(self, bus: EventBus) -> None:
        # No subscriptions; ready immediately.
        self._fire()


class _Wait(_Gate):
    """Fires after `seconds` of wall-clock time.

    Schedules via the bus's scheduler (so headless tests can fake the clock).
    The bus injects `_schedule(seconds, fn)` if available; otherwise the gate
    fires immediately so the tutorial doesn't get stuck without a scheduler.
    """

    def __init__(self, seconds: float = 2.0) -> None:
        super().__init__()
        self.seconds = seconds

    def _install(self, bus: EventBus) -> None:
        scheduler = getattr(bus, "schedule", None)
        if callable(scheduler):
            scheduler(self.seconds, self._fire)
        else:
            self._fire()


class _OnEvent(_Gate):
    """Fires on the first emission of `event_name`."""

    def __init__(self, event_name: str) -> None:
        super().__init__()
        self.event_name = event_name

    def _install(self, bus: EventBus) -> None:
        self._unsubs.append(bus.on(self.event_name, lambda **_: self._fire()))


class _PaintN(_Gate):
    """Fires after `n` distinct cells have been painted in the current step.

    Drag-painting a single cell repeatedly only counts once. Painting the
    same cell again with the same color is filtered upstream by the editor's
    `_last_paint_cell` short-circuit, but we de-dupe here too as a defense.
    """

    def __init__(self, n: int) -> None:
        super().__init__()
        self.n = n
        self._cells: set = set()

    def _install(self, bus: EventBus) -> None:
        self._cells.clear()
        self._unsubs.append(bus.on("paint", self._on_paint))

    def _on_paint(self, **payload: Any) -> None:
        x = payload.get("x")
        y = payload.get("y")
        if x is None or y is None:
            return
        self._cells.add((x, y))
        if len(self._cells) >= self.n:
            self._fire()


def gate_for(name: GateName) -> _Gate:
    """Construct a fresh gate instance for the given gate name."""
    if name == GateName.IMMEDIATE:
        return _Immediate()
    if name == GateName.WAIT:
        return _Wait(seconds=2.0)
    if name == GateName.PICK_COLOR:
        return _OnEvent("color_picked")
    if name == GateName.PAINT_ONCE:
        return _PaintN(1)
    if name == GateName.PAINT_THREE:
        return _PaintN(3)
    if name == GateName.FRAME_ADDED:
        return _OnEvent("frame_added")
    if name == GateName.PLAY_STARTED:
        return _OnEvent("play_started")
    if name == GateName.SAVE_DONE:
        return _OnEvent("save_done")
    raise ValueError(f"unknown gate: {name!r}")
