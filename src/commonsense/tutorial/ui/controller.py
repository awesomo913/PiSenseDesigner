"""TutorialController — glue layer that turns runner callbacks into UI actions.

This is the single integration point the editor uses:

    controller = TutorialController(root, registry, runner, profile)
    controller.start()

Internally it owns the spotlight, bubble, pulse, and confetti widgets and
subscribes to runner.on_step_enter / on_step_complete / on_reward / on_finished
/ on_skip.

Lifecycle:
    start()      runner.start() — drives the first uncompleted step
    skip()       runner.skip()
    replay()     runner.replay()
    destroy()    tear down all UI, unsubscribe everything
"""
from __future__ import annotations

import tkinter as tk
from typing import Optional

from ..model import Profile, Step
from ..runner import TutorialRunner
from .bubble import SpeechBubble
from .confetti import Confetti
from .highlight import TargetPulse
from .registry import WidgetRegistry
from .spotlight import Spotlight


class TutorialController:
    def __init__(
        self,
        root: tk.Tk,
        registry: WidgetRegistry,
        runner: TutorialRunner,
        profile: Profile,
    ) -> None:
        self.root = root
        self.registry = registry
        self.runner = runner
        self.profile = profile

        self.spotlight = Spotlight(root)
        self.bubble = SpeechBubble(root)
        self.pulse = TargetPulse(root)
        self.confetti = Confetti(root)

        # Hook runner events.
        self.runner.on_step_enter(self._on_step_enter)
        self.runner.on_step_complete(self._on_step_complete)
        self.runner.on_reward(self._on_reward)
        self.runner.on_finished(self._on_finished)
        self.runner.on_skip(self._on_skip)

        # Make the bus aware of Tk's after-loop so WAIT gates can schedule.
        # The bus must support a `schedule(seconds, fn)` callable; runner.bus
        # is the same EventBus, so monkey-patch the method onto it.
        try:
            self.runner.bus.schedule = self._bus_schedule  # type: ignore[attr-defined]
        except Exception:
            pass

    # ── public ──────────────────────────────────────────────────────────────
    def start(self) -> None:
        self.runner.start()

    def skip(self) -> None:
        self.runner.skip()

    def replay(self) -> None:
        # Tear UI down first so a re-enter shows the first step cleanly.
        self._teardown_widgets()
        self.runner.replay()

    def destroy(self) -> None:
        self._teardown_widgets()
        self.confetti._teardown()  # noqa: SLF001 — internal cleanup is fine

    # ── runner callbacks ────────────────────────────────────────────────────
    def _on_step_enter(self, step: Step) -> None:
        bbox = self.registry.bbox(step.target)
        # Spotlight first (background), then pulse (above target), then bubble
        # (next to it). Order matters — Tk's topmost discipline is per-window.
        self.spotlight.show(bbox)
        self.pulse.show(bbox)

        title = self._personalize(step.title)
        body = self._personalize(step.body)
        helper = step.helper_text
        progress = self._progress_label()

        self.bubble.show(
            title=title,
            body=body,
            helper=helper,
            button_text=self._button_text(step),
            on_button=self._on_bubble_button,
            on_skip=self.skip,
            progress=progress,
            mascot_pose=step.reward.mascot_pose or "idle",
            target_bbox=bbox,
        )

    def _on_step_complete(self, _step: Step) -> None:
        # Tear down per-step UI; the next _on_step_enter will rebuild it.
        self._teardown_widgets()

    def _on_reward(self, step: Step) -> None:
        if step.reward.confetti:
            self.confetti.burst()
        # Audio + Sense HAT reactions land in Phase 3 — hook points are here.

    def _on_finished(self) -> None:
        self._teardown_widgets()

    def _on_skip(self) -> None:
        self._teardown_widgets()

    # ── ui helpers ──────────────────────────────────────────────────────────
    def _on_bubble_button(self) -> None:
        """The big green button on the bubble.

        For step types that have no real action gate (IMMEDIATE, WAIT, or any
        step the kid finished off-bubble), pressing the button advances. For
        action-gated steps the button is a "I did it" override — kid claims
        completion. We use force_next which marks the step complete.
        """
        self.runner.force_next()

    def _bus_schedule(self, seconds: float, fn) -> None:
        """Tk-driven scheduler so WAIT gates work in real time."""
        ms = max(0, int(seconds * 1000))
        self.root.after(ms, fn)

    def _teardown_widgets(self) -> None:
        self.bubble.hide()
        self.spotlight.hide()
        self.pulse.hide()

    def _progress_label(self) -> str:
        total = len(self.runner.steps)
        done = len(self.runner.state.completed_step_ids)
        return f"⭐ {done} / {total}"

    def _button_text(self, step: Step) -> str:
        # Last step gets a celebratory verb. Action-gated steps get a softer
        # nudge ("I did it!"). Wait/immediate get "Let's go!".
        from ..model import GateName
        if step.gate == GateName.IMMEDIATE or step.gate == GateName.WAIT:
            return "Let's go! ✨"
        return "I did it! ✨"

    def _personalize(self, text: str) -> str:
        name = self.profile.name
        if not name:
            return text
        # Prefix the welcome step with the kid's name. Cheap, effective.
        if text.lower().startswith("hi"):
            return f"Hi, {name}!"
        return text
