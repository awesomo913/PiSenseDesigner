"""Content sanity — every step respects its age preset's word budget,
every target/gate is valid, every reward audio name is sane."""
from __future__ import annotations

from commonsense.tutorial import content
from commonsense.tutorial.model import AGE_PRESETS, GateName


# Targets the editor exposes. Phase 2's spotlight will resolve these names
# against winfo_children. Keep this list in sync with editor.py widget refs.
KNOWN_TARGETS = {
    None,
    "palette", "canvas", "add_btn", "play_btn", "save_btn",
    "tools", "anim_btn",
}

KNOWN_AUDIO = {None, "chime", "yay", "whoosh", "oops", "click"}
KNOWN_HAT = {None, "rainbow_fade", "green_flash", "play_demo", "pulse"}


def test_all_age_presets_have_steps():
    for age in AGE_PRESETS:
        assert content.steps_for(age), f"no steps for age preset {age}"


def test_unknown_age_preset_falls_back_to_seven():
    fallback = content.steps_for("99")
    seven = content.steps_for("7")
    assert [s.id for s in fallback] == [s.id for s in seven]


def test_step_ids_unique_within_each_preset():
    for age in AGE_PRESETS:
        ids = [s.id for s in content.steps_for(age)]
        assert len(ids) == len(set(ids)), f"duplicate step ids in preset {age}"


def test_body_word_count_respects_preset_budget():
    for age, preset in AGE_PRESETS.items():
        for s in content.steps_for(age):
            words = len(s.body.split())
            assert words <= preset.max_words, (
                f"preset {age} step {s.id!r}: {words} words "
                f"(max {preset.max_words}) — '{s.body}'"
            )


def test_every_target_is_known():
    for age in AGE_PRESETS:
        for s in content.steps_for(age):
            assert s.target in KNOWN_TARGETS, (
                f"step {s.id!r} targets unknown widget {s.target!r}"
            )


def test_every_gate_is_a_valid_gate_name():
    for age in AGE_PRESETS:
        for s in content.steps_for(age):
            assert isinstance(s.gate, GateName), (
                f"step {s.id!r} has bad gate {s.gate!r}"
            )


def test_every_audio_is_known():
    for age in AGE_PRESETS:
        for s in content.steps_for(age):
            assert s.reward.audio in KNOWN_AUDIO, (
                f"step {s.id!r} uses unknown audio {s.reward.audio!r}"
            )


def test_every_hat_pattern_is_known():
    for age in AGE_PRESETS:
        for s in content.steps_for(age):
            assert s.reward.hat_pattern in KNOWN_HAT, (
                f"step {s.id!r} uses unknown hat pattern "
                f"{s.reward.hat_pattern!r}"
            )


def test_first_step_is_a_friendly_greeting():
    """Sanity — every preset opens with a low-stakes greeting step.
    Locks the gate to IMMEDIATE or WAIT so the kid isn't gated out by
    needing to take an action before they understand the app."""
    for age in AGE_PRESETS:
        first = content.steps_for(age)[0]
        assert first.gate in (GateName.IMMEDIATE, GateName.WAIT), (
            f"preset {age} opens with hard gate {first.gate!r}"
        )
