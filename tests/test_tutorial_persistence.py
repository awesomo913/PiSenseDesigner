"""Persistence — JSON roundtrip, atomic writes, corruption recovery."""
from __future__ import annotations

import json

import pytest

from commonsense.tutorial import persistence
from commonsense.tutorial.model import Profile, TutorialState


@pytest.fixture
def tmp_state_dir(tmp_path, monkeypatch):
    """Redirect ~/.commonsense/ → a tmp dir for the test."""
    monkeypatch.setattr(persistence, "_state_dir", lambda: tmp_path)
    return tmp_path


def test_state_load_returns_fresh_when_missing(tmp_state_dir):
    s = persistence.load_state()
    assert s.completed_step_ids == set()
    assert s.current_step_id is None
    assert s.skip_count == 0


def test_state_roundtrip(tmp_state_dir):
    s = TutorialState.fresh()
    s.current_step_id = "paint_three"
    s.completed_step_ids.update({"hi", "pick_color"})
    s.skip_count = 1
    s.replay_count = 2

    persistence.save_state(s)
    loaded = persistence.load_state()
    assert loaded.current_step_id == "paint_three"
    assert loaded.completed_step_ids == {"hi", "pick_color"}
    assert loaded.skip_count == 1
    assert loaded.replay_count == 2


def test_state_load_recovers_from_corrupt_json(tmp_state_dir):
    # Write garbage to the state file — load() should fall back to fresh
    # rather than raise into the editor.
    path = persistence.state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{this is not json", encoding="utf-8")
    s = persistence.load_state()
    assert s.completed_step_ids == set()
    assert s.skip_count == 0


def test_profile_roundtrip(tmp_state_dir):
    p = Profile.fresh(name="Asher", age_preset="7")
    persistence.save_profile(p)
    loaded = persistence.load_profile()
    assert loaded.name == "Asher"
    assert loaded.age_preset == "7"
    assert loaded.created_at  # non-empty timestamp


def test_profile_load_returns_fresh_when_missing(tmp_state_dir):
    p = persistence.load_profile()
    assert p.name is None
    assert p.age_preset == "7"


def test_atomic_write_does_not_leave_temp_files(tmp_state_dir):
    """The mkstemp temp file must be renamed — never leaked into ~/.commonsense.
    A leaked temp would confuse load() and bloat the state dir."""
    s = TutorialState.fresh()
    persistence.save_state(s)
    # Only the canonical file should exist.
    files = sorted(p.name for p in tmp_state_dir.iterdir())
    assert files == ["tutorial_state.json"]


def test_save_then_corrupt_then_save_recovers(tmp_state_dir):
    """A power-cut scenario: corrupt mid-life, then save again — last write wins."""
    s1 = TutorialState.fresh()
    s1.completed_step_ids.add("hi")
    persistence.save_state(s1)

    persistence.state_path().write_text("garbage", encoding="utf-8")
    # Save survives even after the on-disk file went bad.
    s2 = TutorialState.fresh()
    s2.completed_step_ids.add("pick_color")
    persistence.save_state(s2)

    loaded = persistence.load_state()
    assert loaded.completed_step_ids == {"pick_color"}


def test_state_json_is_indented_and_parseable(tmp_state_dir):
    """File must be human-readable for parents who want to inspect progress."""
    s = TutorialState.fresh()
    s.completed_step_ids = {"hi", "play"}
    persistence.save_state(s)
    txt = persistence.state_path().read_text(encoding="utf-8")
    assert "\n" in txt  # indented, not single-line
    parsed = json.loads(txt)
    assert "completed_step_ids" in parsed
