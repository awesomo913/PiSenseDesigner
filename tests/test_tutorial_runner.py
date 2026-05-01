"""TutorialRunner — state machine drives steps from gate hits."""
from __future__ import annotations

from typing import List

from commonsense.tutorial.events import EventBus
from commonsense.tutorial.model import GateName, RewardSpec, Step, TutorialState
from commonsense.tutorial.runner import TutorialRunner


def _three_step_program():
    return [
        Step(id="hi",     title="Hi",        body="b", target=None,
             gate=GateName.IMMEDIATE, reward=RewardSpec()),
        Step(id="paint",  title="Paint",     body="b", target="canvas",
             gate=GateName.PAINT_ONCE, reward=RewardSpec()),
        Step(id="save",   title="Save",      body="b", target="save_btn",
             gate=GateName.SAVE_DONE, reward=RewardSpec()),
    ]


def _instrumented_runner(steps=None):
    bus = EventBus()
    state = TutorialState.fresh()
    saved: List[TutorialState] = []
    runner = TutorialRunner(
        bus, steps or _three_step_program(), state,
        save_callback=lambda s: saved.append(_clone(s)),
    )
    log: dict = {"enter": [], "complete": [], "reward": [], "done": 0, "skip": 0}
    runner.on_step_enter(lambda s: log["enter"].append(s.id))
    runner.on_step_complete(lambda s: log["complete"].append(s.id))
    runner.on_reward(lambda s: log["reward"].append(s.id))
    runner.on_finished(lambda: log.__setitem__("done", log["done"] + 1))
    runner.on_skip(lambda: log.__setitem__("skip", log["skip"] + 1))
    return runner, bus, state, saved, log


def _clone(s: TutorialState) -> TutorialState:
    return TutorialState.from_dict(s.to_dict())


def test_start_enters_first_step():
    r, _bus, _st, _saved, log = _instrumented_runner()
    r.start()
    # IMMEDIATE step "hi" auto-completes, then paint becomes current.
    assert log["enter"][0] == "hi"
    assert log["complete"][0] == "hi"
    assert log["enter"][-1] == "paint"


def test_advance_only_on_matching_gate():
    r, bus, _st, _saved, log = _instrumented_runner()
    r.start()
    # Currently on "paint" step. Wrong event must not advance.
    bus.emit("frame_added")
    assert log["complete"] == ["hi"]
    bus.emit("paint", x=0, y=0)
    assert log["complete"] == ["hi", "paint"]


def test_full_run_to_finish():
    r, bus, _st, _saved, log = _instrumented_runner()
    r.start()
    bus.emit("paint", x=0, y=0)
    bus.emit("save_done", path="/tmp/x.json")
    assert log["complete"] == ["hi", "paint", "save"]
    assert log["done"] == 1


def test_skip_marks_skip_and_calls_on_skip():
    r, _bus, state, _saved, log = _instrumented_runner()
    r.start()
    r.skip()
    assert log["skip"] == 1
    assert state.skip_count == 1
    # After skip, gate events for the abandoned step must NOT advance.
    assert log["complete"] == ["hi"]


def test_persistence_saves_after_each_transition():
    r, bus, _st, saved, _log = _instrumented_runner()
    r.start()
    saves_before = len(saved)
    bus.emit("paint", x=0, y=0)
    saves_after = len(saved)
    assert saves_after > saves_before


def test_resume_skips_completed_steps():
    """Run partway, simulate restart by handing the state back into a fresh runner."""
    r, bus, state, _saved, _log = _instrumented_runner()
    r.start()
    bus.emit("paint", x=0, y=0)
    # State should now have hi + paint marked complete.
    assert {"hi", "paint"} <= state.completed_step_ids

    # New session — same state dict, fresh bus, fresh runner.
    bus2 = EventBus()
    state2 = TutorialState.from_dict(state.to_dict())
    log2: List[str] = []
    runner2 = TutorialRunner(bus2, _three_step_program(), state2)
    runner2.on_step_enter(lambda s: log2.append(s.id))
    runner2.start()
    # Should jump straight to "save" — the only uncompleted step.
    assert log2 == ["save"]


def test_replay_clears_progress_and_restarts():
    r, bus, state, _saved, log = _instrumented_runner()
    r.start()
    bus.emit("paint", x=0, y=0)
    bus.emit("save_done", path="/tmp/x.json")
    assert state.replay_count == 0
    log["enter"].clear()
    log["complete"].clear()

    r.replay()
    assert state.replay_count == 1
    assert state.completed_step_ids == {"hi"}  # IMMEDIATE re-fired during replay
    assert log["enter"][0] == "hi"


def test_back_unmarks_step_so_gate_runs_again():
    r, bus, state, _saved, _log = _instrumented_runner()
    r.start()
    bus.emit("paint", x=0, y=0)
    # Now on "save". Go back to "paint".
    r.back()
    assert "paint" not in state.completed_step_ids
    # Paint gate should run again.
    bus.emit("paint", x=5, y=5)
    assert "paint" in state.completed_step_ids


def test_runner_rejects_empty_step_list():
    import pytest
    with pytest.raises(ValueError):
        TutorialRunner(EventBus(), [], TutorialState.fresh())


def test_finished_callback_fires_exactly_once():
    r, bus, _st, _saved, log = _instrumented_runner()
    r.start()
    bus.emit("paint", x=0, y=0)
    bus.emit("save_done", path="/tmp/x.json")
    assert log["done"] == 1
    # Stray events after finish must not refire.
    bus.emit("save_done", path="/tmp/y.json")
    assert log["done"] == 1
