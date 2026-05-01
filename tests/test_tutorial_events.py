"""EventBus — pub/sub correctness, isolation, unsubscribe."""
from __future__ import annotations

from commonsense.tutorial.events import EventBus


def test_emit_calls_handler():
    bus = EventBus()
    seen = []
    bus.on("paint", lambda **kw: seen.append(kw))
    bus.emit("paint", x=1, y=2)
    assert seen == [{"x": 1, "y": 2}]


def test_unsubscribe_stops_delivery():
    bus = EventBus()
    seen = []
    off = bus.on("save_done", lambda **_: seen.append(1))
    bus.emit("save_done")
    off()
    bus.emit("save_done")
    assert seen == [1]


def test_handler_exception_does_not_break_other_handlers():
    """A buggy listener must not block other listeners or crash the editor."""
    bus = EventBus()
    seen = []

    def boom(**_):
        raise RuntimeError("listener went bad")

    bus.on("frame_added", boom)
    bus.on("frame_added", lambda **_: seen.append("ok"))
    bus.emit("frame_added")
    assert seen == ["ok"]


def test_emit_on_unknown_event_is_noop():
    bus = EventBus()
    bus.emit("never_subscribed", foo="bar")  # must not raise


def test_listener_count():
    bus = EventBus()
    assert bus.listener_count("paint") == 0
    off = bus.on("paint", lambda **_: None)
    assert bus.listener_count("paint") == 1
    off()
    assert bus.listener_count("paint") == 0


def test_clear_drops_all_handlers():
    bus = EventBus()
    seen = []
    bus.on("a", lambda **_: seen.append("a"))
    bus.on("b", lambda **_: seen.append("b"))
    bus.clear()
    bus.emit("a")
    bus.emit("b")
    assert seen == []
