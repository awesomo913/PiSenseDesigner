"""TutorialRunner — the state machine that drives the tutorial.

Phase 1: backend only. The runner emits abstract callbacks (`on_step_enter`,
`on_step_complete`, `on_finished`, `on_skip`, `on_reward`) which Phase 2's UI
layer subscribes to. Headless code (and tests) can subscribe to the same
callbacks with no Tk involved.

Lifecycle
─────────
    runner = TutorialRunner(bus, steps, state)
    runner.on_step_enter(handle_show_bubble)
    runner.on_reward(handle_play_audio)
    runner.start()                   # enters the first not-yet-completed step
    # ... editor emits events on the bus, gates fire, runner advances ...
    runner.skip()                    # marks remaining steps unfinished, calls on_finished
    runner.replay()                  # clears completed_step_ids and restarts

Concurrency
───────────
Single-threaded — every method assumed to run on the Tk main loop. Don't
call across threads.
"""
from __future__ import annotations

from datetime import datetime
from typing import Callable, List, Optional

from .events import EventBus
from .gates import gate_for
from .model import Step, TutorialState

StepHandler = Callable[[Step], None]
RewardHandler = Callable[[Step], None]
DoneHandler = Callable[[], None]


class TutorialRunner:
    def __init__(
        self,
        bus: EventBus,
        steps: List[Step],
        state: TutorialState,
        save_callback: Optional[Callable[[TutorialState], None]] = None,
    ) -> None:
        if not steps:
            raise ValueError("TutorialRunner needs at least one step")
        self.bus = bus
        self.steps = steps
        self.state = state
        self._save = save_callback or (lambda _s: None)

        self._idx: int = 0
        self._current_gate = None  # type: ignore[assignment]
        self._active = False

        # Listener slots — Phase 2 UI layer fills these in.
        self._enter_handlers: List[StepHandler] = []
        self._complete_handlers: List[StepHandler] = []
        self._reward_handlers: List[RewardHandler] = []
        self._done_handlers: List[DoneHandler] = []
        self._skip_handlers: List[DoneHandler] = []

    # ── public registration API ──────────────────────────────────────────────
    def on_step_enter(self, fn: StepHandler) -> None:
        self._enter_handlers.append(fn)

    def on_step_complete(self, fn: StepHandler) -> None:
        self._complete_handlers.append(fn)

    def on_reward(self, fn: RewardHandler) -> None:
        self._reward_handlers.append(fn)

    def on_finished(self, fn: DoneHandler) -> None:
        self._done_handlers.append(fn)

    def on_skip(self, fn: DoneHandler) -> None:
        self._skip_handlers.append(fn)

    # ── lifecycle ────────────────────────────────────────────────────────────
    def start(self) -> None:
        """Enter the first uncompleted step. If everything's done, finish."""
        if self._active:
            return
        self._active = True
        if not self.state.started_at:
            self.state.started_at = _utcnow()
        self._idx = self._first_uncompleted_index()
        if self._idx >= len(self.steps):
            self._finish()
            return
        self._enter_current()

    def replay(self) -> None:
        """Rewind to step 0 and run again. Bumps replay_count, persists."""
        self._teardown_gate()
        self.state.completed_step_ids.clear()
        self.state.completed_at = None
        self.state.paint_progress = 0
        self.state.replay_count += 1
        self.state.started_at = _utcnow()
        self._save(self.state)
        self._idx = 0
        self._active = True
        self._enter_current()

    def skip(self) -> None:
        """User aborted. Mark skipped, persist, fire skip handlers."""
        self._teardown_gate()
        self.state.skip_count += 1
        self._save(self.state)
        self._active = False
        for fn in self._skip_handlers:
            _safe(fn)

    def back(self) -> None:
        """Go to previous step. Bound by 0."""
        if self._idx <= 0:
            return
        self._teardown_gate()
        # Un-complete the step we're going back to so its gate runs again.
        prev = self.steps[self._idx - 1]
        self.state.completed_step_ids.discard(prev.id)
        self._idx -= 1
        self._enter_current()

    def force_next(self) -> None:
        """Advance regardless of gate (e.g. for "Skip step" UI). Marks complete."""
        if not self._active:
            return
        self._satisfy_current()

    # ── internals ────────────────────────────────────────────────────────────
    def _first_uncompleted_index(self) -> int:
        for i, s in enumerate(self.steps):
            if s.id not in self.state.completed_step_ids:
                return i
        return len(self.steps)

    def _enter_current(self) -> None:
        step = self.steps[self._idx]
        self.state.current_step_id = step.id
        self._save(self.state)

        for fn in self._enter_handlers:
            _safe(fn, step)

        # Build + bind a fresh gate. Gates auto-fire for IMMEDIATE.
        self._current_gate = gate_for(step.gate)
        self._current_gate.bind(self.bus, self._satisfy_current)

    def _satisfy_current(self) -> None:
        if not self._active:
            return
        step = self.steps[self._idx]
        self._teardown_gate()
        self.state.mark_completed(step.id)
        self._save(self.state)

        for fn in self._complete_handlers:
            _safe(fn, step)
        for fn in self._reward_handlers:
            _safe(fn, step)

        # Advance.
        self._idx += 1
        if self._idx >= len(self.steps):
            self._finish()
        else:
            self._enter_current()

    def _finish(self) -> None:
        self.state.completed_at = _utcnow()
        self.state.current_step_id = None
        self._save(self.state)
        self._active = False
        for fn in self._done_handlers:
            _safe(fn)

    def _teardown_gate(self) -> None:
        g = self._current_gate
        if g is not None:
            g.unbind()
        self._current_gate = None


# ── module helpers ───────────────────────────────────────────────────────────
def _utcnow() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _safe(fn, *args) -> None:
    """Call `fn(*args)` swallowing any exception so one buggy listener can't
    derail the whole tutorial."""
    try:
        fn(*args)
    except Exception:
        import sys
        import traceback
        traceback.print_exc(file=sys.stderr)
