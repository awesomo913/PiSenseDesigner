"""Gate predicates — verify each gate fires only on the right signal."""
from __future__ import annotations

from commonsense.tutorial.events import EventBus
from commonsense.tutorial.gates import gate_for
from commonsense.tutorial.model import GateName


def _gate_with(name: GateName, bus: EventBus):
    """Bind a gate, return (gate, list-that-gets-1-when-satisfied)."""
    fired = []
    gate = gate_for(name)
    gate.bind(bus, lambda: fired.append(1))
    return gate, fired


def test_immediate_fires_on_bind():
    bus = EventBus()
    _g, fired = _gate_with(GateName.IMMEDIATE, bus)
    assert fired == [1]


def test_pick_color_fires_only_on_color_picked():
    bus = EventBus()
    _g, fired = _gate_with(GateName.PICK_COLOR, bus)
    bus.emit("paint", x=0, y=0)
    assert fired == []
    bus.emit("color_picked", index=3)
    assert fired == [1]


def test_paint_once_fires_on_first_paint():
    bus = EventBus()
    _g, fired = _gate_with(GateName.PAINT_ONCE, bus)
    bus.emit("paint", x=2, y=2, idx=4)
    assert fired == [1]


def test_paint_three_dedupes_same_cell():
    bus = EventBus()
    _g, fired = _gate_with(GateName.PAINT_THREE, bus)
    # Same cell hit five times → only counts once.
    for _ in range(5):
        bus.emit("paint", x=1, y=1)
    assert fired == []
    bus.emit("paint", x=2, y=1)
    assert fired == []
    bus.emit("paint", x=3, y=1)
    assert fired == [1]


def test_paint_three_does_not_double_fire():
    bus = EventBus()
    _g, fired = _gate_with(GateName.PAINT_THREE, bus)
    for x in range(5):
        bus.emit("paint", x=x, y=0)
    assert fired == [1]  # exactly one fire even with extra paints


def test_frame_added_fires_on_event():
    bus = EventBus()
    _g, fired = _gate_with(GateName.FRAME_ADDED, bus)
    bus.emit("frame_added")
    assert fired == [1]


def test_play_started_fires_on_event():
    bus = EventBus()
    _g, fired = _gate_with(GateName.PLAY_STARTED, bus)
    bus.emit("play_started")
    assert fired == [1]


def test_save_done_fires_on_event():
    bus = EventBus()
    _g, fired = _gate_with(GateName.SAVE_DONE, bus)
    bus.emit("save_done", path="/tmp/x.json")
    assert fired == [1]


def test_unbind_stops_listening():
    bus = EventBus()
    g, fired = _gate_with(GateName.PAINT_ONCE, bus)
    g.unbind()
    bus.emit("paint", x=0, y=0)
    assert fired == []


def test_wait_gate_fires_via_scheduler():
    """If the bus exposes `schedule(seconds, fn)`, the wait gate uses it."""
    bus = EventBus()
    pending = []
    bus.schedule = lambda seconds, fn: pending.append((seconds, fn))  # type: ignore[attr-defined]
    _g, fired = _gate_with(GateName.WAIT, bus)
    assert fired == []
    assert len(pending) == 1
    pending[0][1]()  # simulate the timer firing
    assert fired == [1]


def test_wait_gate_falls_back_to_immediate_without_scheduler():
    """No scheduler → don't hang the tutorial; fire right away."""
    bus = EventBus()
    _g, fired = _gate_with(GateName.WAIT, bus)
    assert fired == [1]
