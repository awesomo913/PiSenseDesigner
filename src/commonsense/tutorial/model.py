"""Dataclasses for the tutorial backend.

Everything here is pure data — no Tk, no I/O. Lets the state machine and
gates be unit-tested headless.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set


class GateName(str, Enum):
    """Predicate that decides when a step is satisfied.

    String-valued so it round-trips cleanly through JSON without a custom
    encoder.
    """

    IMMEDIATE = "immediate"          # advance as soon as the user hits Next
    WAIT = "wait"                    # advance after a fixed delay (welcome step)
    PICK_COLOR = "pick_color"        # any palette click
    PAINT_ONCE = "paint_once"        # first paint cell on the canvas
    PAINT_THREE = "paint_three"      # 3 distinct cells painted this step
    FRAME_ADDED = "frame_added"      # ➕ Add fired
    PLAY_STARTED = "play_started"    # PLAY pressed and tick loop running
    SAVE_DONE = "save_done"          # save_done event fired with valid path


@dataclass(frozen=True)
class RewardSpec:
    """What happens visually + audibly + on the Sense HAT after a gate hits.

    All fields optional — Phase 1 ignores everything except `audio` (no UI yet).
    """
    audio: Optional[str] = None          # "chime" | "yay" | "whoosh" | path
    voice: Optional[str] = None          # text to speak via espeak
    hat_pattern: Optional[str] = None    # "rainbow_fade" | "green_flash" | …
    confetti: bool = False
    mascot_pose: Optional[str] = None    # "wave" | "cheer" | "point"


@dataclass(frozen=True)
class Step:
    """One tutorial step.

    Body must respect the active age preset's `max_words`. `target` names the
    UI widget the spotlight should highlight (resolved at render time, not
    here — keeps this module Tk-free).
    """
    id: str
    title: str
    body: str
    target: Optional[str]
    gate: GateName
    reward: RewardSpec = RewardSpec()
    helper_text: Optional[str] = None    # shown if kid stalls > 30s on this step


@dataclass
class AgePreset:
    name: str
    max_words: int
    narration: bool
    auto_helper: bool          # auto-do the action after stall
    helper_delay_s: int


AGE_PRESETS: Dict[str, AgePreset] = {
    "5": AgePreset(name="5",  max_words=8,  narration=True,  auto_helper=True,  helper_delay_s=20),
    "7": AgePreset(name="7",  max_words=14, narration=True,  auto_helper=False, helper_delay_s=40),
    "9": AgePreset(name="9",  max_words=22, narration=False, auto_helper=False, helper_delay_s=60),
}


@dataclass
class Profile:
    """Per-kid settings. Survives reinstalls (lives in ~/.commonsense)."""
    name: Optional[str] = None
    age_preset: str = "7"
    # ISO-8601 string — easier than juggling tz-aware datetimes through JSON.
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "age_preset": self.age_preset,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Profile":
        return cls(
            name=d.get("name"),
            age_preset=d.get("age_preset", "7"),
            created_at=d.get("created_at", ""),
        )

    @classmethod
    def fresh(cls, name: Optional[str] = None, age_preset: str = "7") -> "Profile":
        return cls(
            name=name,
            age_preset=age_preset,
            created_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
        )


@dataclass
class TutorialState:
    """Persistence-friendly progress record.

    Stores by step **id**, not index, so step reordering doesn't lose progress.
    """
    current_step_id: Optional[str] = None
    completed_step_ids: Set[str] = field(default_factory=set)
    started_at: str = ""
    completed_at: Optional[str] = None
    skip_count: int = 0
    replay_count: int = 0
    paint_progress: int = 0   # for PAINT_THREE — counts distinct cells this step

    def to_dict(self) -> dict:
        return {
            "current_step_id": self.current_step_id,
            "completed_step_ids": sorted(self.completed_step_ids),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "skip_count": self.skip_count,
            "replay_count": self.replay_count,
            "paint_progress": self.paint_progress,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TutorialState":
        return cls(
            current_step_id=d.get("current_step_id"),
            completed_step_ids=set(d.get("completed_step_ids", [])),
            started_at=d.get("started_at", ""),
            completed_at=d.get("completed_at"),
            skip_count=int(d.get("skip_count", 0)),
            replay_count=int(d.get("replay_count", 0)),
            paint_progress=int(d.get("paint_progress", 0)),
        )

    @classmethod
    def fresh(cls) -> "TutorialState":
        return cls(
            started_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
        )

    def mark_completed(self, step_id: str) -> None:
        self.completed_step_ids.add(step_id)

    def is_done_with_all(self, step_ids: List[str]) -> bool:
        return all(sid in self.completed_step_ids for sid in step_ids)
