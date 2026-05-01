"""8x8 Sense HAT frame model with validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Tuple

GRID = 8
CELLS = GRID * GRID

RGB = Tuple[int, int, int]

DEFAULT_PALETTE: List[RGB] = [
    (0, 0, 0),
    (255, 255, 255),
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
    (255, 255, 0),
    (255, 0, 255),
    (0, 255, 255),
    (128, 128, 128),
    (64, 64, 64),
]


def _validate_rgb(c: Any) -> RGB:
    if not (isinstance(c, (list, tuple)) and len(c) == 3):
        raise ValueError(f"palette color must be length-3 tuple, got {c!r}")
    r, g, b = (int(c[0]), int(c[1]), int(c[2]))
    for v in (r, g, b):
        if v < 0 or v > 255:
            raise ValueError(f"RGB values must be 0..255, got {c!r}")
    return (r, g, b)


@dataclass
class Frame:
    """One 8x8 frame: 64 palette indices (row-major)."""

    pixels: List[int] = field(default_factory=lambda: [0] * CELLS)

    def __post_init__(self) -> None:
        if len(self.pixels) != CELLS:
            raise ValueError(f"frame must have {CELLS} pixels, got {len(self.pixels)}")

    def copy(self) -> "Frame":
        return Frame(pixels=list(self.pixels))

    def set_idx(self, x: int, y: int, idx: int) -> None:
        if not (0 <= x < GRID and 0 <= y < GRID):
            raise ValueError("x,y out of range")
        self.pixels[y * GRID + x] = idx

    def get_idx(self, x: int, y: int) -> int:
        return self.pixels[y * GRID + x]


@dataclass
class AnimationModel:
    palette: List[RGB]
    frames: List[Frame]
    frame_delay_ms: int = 250
    loop: bool = True
    current_frame: int = 0

    def __post_init__(self) -> None:
        self.palette = [_validate_rgb(c) for c in self.palette]
        if not self.frames:
            raise ValueError("at least one frame required")
        raw_frames = self.frames
        self.frames = []
        for f in raw_frames:
            if isinstance(f, Frame):
                self.frames.append(f)
            else:
                self.frames.append(Frame(pixels=list(f.pixels)))
        for i, fr in enumerate(self.frames):
            if len(fr.pixels) != CELLS:
                raise ValueError(f"frame {i} must have {CELLS} pixels")
        for fr in self.frames:
            for p in fr.pixels:
                if p < 0 or p >= len(self.palette):
                    raise ValueError("pixel index out of palette range")
        if self.frame_delay_ms < 1:
            raise ValueError("frame_delay_ms must be >= 1")
        if self.current_frame < 0 or self.current_frame >= len(self.frames):
            self.current_frame = 0

    def validate(self) -> None:
        AnimationModel(
            palette=list(self.palette),
            frames=[f.copy() for f in self.frames],
            frame_delay_ms=self.frame_delay_ms,
            loop=bool(self.loop),
            current_frame=self.current_frame,
        )

    def to_dict(self) -> dict:
        self.validate()
        return {
            "version": 1,
            "palette": [list(c) for c in self.palette],
            "frames": [list(f.pixels) for f in self.frames],
            "frame_delay_ms": int(self.frame_delay_ms),
            "loop": bool(self.loop),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AnimationModel":
        pal = [_validate_rgb(tuple(c)) for c in data["palette"]]
        frames = [Frame(pixels=[int(x) for x in row]) for row in data["frames"]]
        delay = int(data.get("frame_delay_ms", 250))
        loop = bool(data.get("loop", True))
        m = cls(palette=pal, frames=frames, frame_delay_ms=delay, loop=loop, current_frame=0)
        for fr in m.frames:
            for p in fr.pixels:
                if p < 0 or p >= len(m.palette):
                    raise ValueError("loaded frame references invalid palette index")
        return m

    def next_frame(self) -> None:
        if not self.frames:
            return
        if self.current_frame + 1 < len(self.frames):
            self.current_frame += 1
        elif self.loop:
            self.current_frame = 0

    def prev_frame(self) -> None:
        if not self.frames:
            return
        if self.current_frame > 0:
            self.current_frame -= 1
        elif self.loop:
            self.current_frame = len(self.frames) - 1
