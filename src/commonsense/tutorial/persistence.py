"""On-disk persistence for tutorial state and kid profile.

Lives in ~/.commonsense/ — out of the repo, out of the project tree, so it
survives `update.sh` (fresh git clone) and `pip install -e .` reinstalls.

All writes are atomic: write to a temp file in the same directory, fsync,
rename. Prevents truncated JSON if the Pi loses power mid-write — a real
concern for a 7yo who unplugs the USB.

Read paths are tolerant: missing file → fresh state. Corrupt JSON → log a
warning and fall back to fresh.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

from .model import Profile, TutorialState


def _state_dir() -> Path:
    """~/.commonsense/ — created lazily on first write."""
    return Path.home() / ".commonsense"


def state_path() -> Path:
    return _state_dir() / "tutorial_state.json"


def profile_path() -> Path:
    return _state_dir() / "profile.json"


def _atomic_write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # mkstemp in the same directory so the rename is on the same filesystem
    # (rename across mounts is not atomic on POSIX).
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def load_state() -> TutorialState:
    p = state_path()
    if not p.exists():
        return TutorialState.fresh()
    try:
        with p.open("r", encoding="utf-8") as f:
            return TutorialState.from_dict(json.load(f))
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"[tutorial] state load failed ({e!r}), starting fresh",
              file=sys.stderr)
        return TutorialState.fresh()


def save_state(state: TutorialState) -> None:
    _atomic_write_json(state_path(), state.to_dict())


def load_profile() -> Profile:
    p = profile_path()
    if not p.exists():
        return Profile.fresh()
    try:
        with p.open("r", encoding="utf-8") as f:
            return Profile.from_dict(json.load(f))
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"[tutorial] profile load failed ({e!r}), starting fresh",
              file=sys.stderr)
        return Profile.fresh()


def save_profile(profile: Profile) -> None:
    _atomic_write_json(profile_path(), profile.to_dict())
