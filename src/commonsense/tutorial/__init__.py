"""Tutorial subsystem — pluggable, event-driven, age-presetable.

Phase 1 ships the backend only:
    EventBus       editor → tutorial action signal
    Step           one teaching step
    TutorialState  persistence-friendly progress record
    Gate           predicate that decides "did the kid do the thing?"
    TutorialRunner state machine — listens to bus, advances on gate hit
    Profile        kid's name + chosen age preset

Phase 2+ replaces the legacy modal Toplevel with a non-modal spotlight + mascot
+ Sense HAT reactions; the backend doesn't change.
"""
from .events import EventBus
from .model import (
    AGE_PRESETS,
    GateName,
    Profile,
    RewardSpec,
    Step,
    TutorialState,
)
from .gates import gate_for
from .persistence import (
    load_profile,
    load_state,
    profile_path,
    save_profile,
    save_state,
    state_path,
)
from .runner import TutorialRunner

__all__ = [
    "AGE_PRESETS",
    "EventBus",
    "GateName",
    "Profile",
    "RewardSpec",
    "Step",
    "TutorialRunner",
    "TutorialState",
    "gate_for",
    "load_profile",
    "load_state",
    "profile_path",
    "save_profile",
    "save_state",
    "state_path",
]
