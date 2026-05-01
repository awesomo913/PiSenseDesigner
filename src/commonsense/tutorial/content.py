"""Step content — three age presets, all UI-free.

Word counts respect each preset's `max_words` (see model.py). Phase 1 only
exercises the data; the spotlight/mascot/narration UI lands in Phase 2+.
"""
from __future__ import annotations

from typing import Dict, List

from .model import GateName, RewardSpec, Step


# ── helpers ──────────────────────────────────────────────────────────────────
def _r(audio: str = "", hat: str = "", confetti: bool = False,
       pose: str = "", voice: str = "") -> RewardSpec:
    return RewardSpec(
        audio=audio or None,
        voice=voice or None,
        hat_pattern=hat or None,
        confetti=confetti,
        mascot_pose=pose or None,
    )


# ── AGE 7 — primary target ────────────────────────────────────────────────
# Body ≤ 14 words per step. Verified by tests.
_AGE_7: List[Step] = [
    Step(
        id="hi",
        title="Hi, friend!",
        body="I'm Sparky! Let's make a tiny moving picture together.",
        target=None,
        gate=GateName.WAIT,
        reward=_r(audio="chime", hat="rainbow_fade", pose="wave", voice="Hi friend!"),
    ),
    Step(
        id="pick_color",
        title="Pick a color!",
        body="Tap any color square on the left.",
        target="palette",
        gate=GateName.PICK_COLOR,
        reward=_r(audio="yay", pose="cheer", voice="Nice color!"),
        helper_text="Try a bright one — yellow or pink!",
    ),
    Step(
        id="paint_three",
        title="Paint 3 squares!",
        body="Tap 3 squares in the big grid. Any 3!",
        target="canvas",
        gate=GateName.PAINT_THREE,
        reward=_r(audio="yay", confetti=True, pose="cheer",
                  voice="Wow, look at that!"),
        helper_text="Drag your finger to paint many at once.",
    ),
    Step(
        id="add_frame",
        title="Add a new picture!",
        body="Press the purple ➕ Add button.",
        target="add_btn",
        gate=GateName.FRAME_ADDED,
        reward=_r(audio="whoosh", hat="green_flash", pose="point",
                  voice="Now we have two pictures!"),
        helper_text="It's right under the big PLAY button.",
    ),
    Step(
        id="play",
        title="Press PLAY!",
        body="Hit the big green PLAY button. Watch it move!",
        target="play_btn",
        gate=GateName.PLAY_STARTED,
        reward=_r(audio="yay", hat="play_demo", confetti=True, pose="cheer",
                  voice="Look at that go!"),
    ),
    Step(
        id="save",
        title="Save your art!",
        body="Press SAVE. Pick any name. Hit OK.",
        target="save_btn",
        gate=GateName.SAVE_DONE,
        reward=_r(audio="chime", hat="green_flash", pose="cheer",
                  voice="Saved forever!"),
        helper_text="It goes to a folder called MyAnimations.",
    ),
    Step(
        id="done",
        title="You did it!",
        body="You're an animator now! Try the tools next.",
        target=None,
        gate=GateName.IMMEDIATE,
        reward=_r(audio="yay", confetti=True, pose="cheer",
                  voice="You did it!"),
    ),
]


# ── AGE 5 — fewer steps, shorter words ──────────────────────────────────────
_AGE_5: List[Step] = [
    Step(
        id="hi",
        title="Hi!",
        body="I'm Sparky. Let's make art!",
        target=None,
        gate=GateName.WAIT,
        reward=_r(audio="chime", hat="rainbow_fade", pose="wave"),
    ),
    Step(
        id="pick_color",
        title="Pick a color!",
        body="Tap a color box.",
        target="palette",
        gate=GateName.PICK_COLOR,
        reward=_r(audio="yay", pose="cheer"),
    ),
    Step(
        id="paint_once",
        title="Paint!",
        body="Tap the big grid.",
        target="canvas",
        gate=GateName.PAINT_ONCE,
        reward=_r(audio="yay", confetti=True, pose="cheer"),
    ),
    Step(
        id="play",
        title="Press play!",
        body="Tap green PLAY!",
        target="play_btn",
        gate=GateName.PLAY_STARTED,
        reward=_r(audio="yay", hat="play_demo", confetti=True, pose="cheer"),
    ),
]


# ── AGE 9 — full feature tour, more words allowed ──────────────────────────
_AGE_9: List[Step] = [
    Step(
        id="hi",
        title="Welcome to CommonSense.",
        body="You'll build pixel animations that play on your Sense HAT.",
        target=None,
        gate=GateName.WAIT,
        reward=_r(audio="chime", hat="rainbow_fade"),
    ),
    Step(
        id="pick_color",
        title="Step 1 — choose a color",
        body="Click any color in the PAINT BOX, or press a number key 1–9.",
        target="palette",
        gate=GateName.PICK_COLOR,
        reward=_r(audio="yay"),
    ),
    Step(
        id="paint_three",
        title="Step 2 — draw on the canvas",
        body="Click cells to paint, or drag to paint a streak.",
        target="canvas",
        gate=GateName.PAINT_THREE,
        reward=_r(audio="yay", confetti=True),
    ),
    Step(
        id="add_frame",
        title="Step 3 — add another frame",
        body="Press ➕ Add. Each frame is one picture in the movie.",
        target="add_btn",
        gate=GateName.FRAME_ADDED,
        reward=_r(audio="whoosh", hat="green_flash"),
    ),
    Step(
        id="play",
        title="Step 4 — play it back",
        body="Press the green PLAY button. Press it again to pause.",
        target="play_btn",
        gate=GateName.PLAY_STARTED,
        reward=_r(audio="yay", hat="play_demo"),
    ),
    Step(
        id="save",
        title="Step 5 — save your work",
        body="SAVE writes a JSON file you can re-open or play standalone.",
        target="save_btn",
        gate=GateName.SAVE_DONE,
        reward=_r(audio="chime", hat="green_flash"),
    ),
    Step(
        id="tools",
        title="Step 6 — explore the tools",
        body="Try Eraser, Bucket, Mirror, Rotate, Random, and the stamp library.",
        target="tools",
        gate=GateName.IMMEDIATE,
        reward=_r(),
    ),
    Step(
        id="library",
        title="Step 7 — try the Animations Library",
        body="Click ANIMATIONS to load any of 400+ pre-made animations.",
        target="anim_btn",
        gate=GateName.IMMEDIATE,
        reward=_r(),
    ),
    Step(
        id="done",
        title="You're ready.",
        body="Make something cool. Press F11 for fullscreen, Ctrl+S to save.",
        target=None,
        gate=GateName.IMMEDIATE,
        reward=_r(audio="yay", confetti=True),
    ),
]


_BUNDLES: Dict[str, List[Step]] = {
    "5": _AGE_5,
    "7": _AGE_7,
    "9": _AGE_9,
}


def steps_for(age_preset: str) -> List[Step]:
    """Return the step list for `age_preset`. Falls back to "7" if unknown."""
    return list(_BUNDLES.get(age_preset, _AGE_7))


def all_age_presets() -> List[str]:
    return list(_BUNDLES.keys())
