"""Programmatic helpers for building animations."""

from __future__ import annotations

from typing import Dict, List, Tuple

from commonsense.sense_paint.model import GRID, AnimationModel, Frame

# 3 columns × 5 rows per glyph (bits 2..0 = left→right)
_FONT: Dict[str, Tuple[int, ...]] = {
    "A": (0b010, 0b101, 0b111, 0b101, 0b101),
    "B": (0b110, 0b101, 0b110, 0b101, 0b110),
    "C": (0b011, 0b100, 0b100, 0b100, 0b011),
    "D": (0b110, 0b101, 0b101, 0b101, 0b110),
    "E": (0b111, 0b100, 0b110, 0b100, 0b111),
    "F": (0b111, 0b100, 0b110, 0b100, 0b100),
    "G": (0b011, 0b100, 0b101, 0b101, 0b011),
    "H": (0b101, 0b101, 0b111, 0b101, 0b101),
    "I": (0b111, 0b010, 0b010, 0b010, 0b111),
    "L": (0b100, 0b100, 0b100, 0b100, 0b111),
    "O": (0b010, 0b101, 0b101, 0b101, 0b010),
    "P": (0b110, 0b101, 0b110, 0b100, 0b100),
    "R": (0b110, 0b101, 0b110, 0b101, 0b101),
    "S": (0b011, 0b100, 0b010, 0b001, 0b110),
    "T": (0b111, 0b010, 0b010, 0b010, 0b010),
    "U": (0b101, 0b101, 0b101, 0b101, 0b011),
    "0": (0b010, 0b101, 0b101, 0b101, 0b010),
    "1": (0b010, 0b110, 0b010, 0b010, 0b111),
    "2": (0b111, 0b001, 0b010, 0b100, 0b111),
}


def serialize_model(model: AnimationModel) -> dict:
    return model.to_dict()


def deserialize_model(data: dict) -> AnimationModel:
    return AnimationModel.from_dict(data)


def paint_diagonal(model: AnimationModel, frame_index: int, color_index: int) -> None:
    if frame_index < 0 or frame_index >= len(model.frames):
        raise ValueError("frame_index out of range")
    if color_index < 0 or color_index >= len(model.palette):
        raise ValueError("color_index out of range")
    fr = model.frames[frame_index]
    for i in range(GRID):
        fr.set_idx(i, i, color_index)


def draw_text_on_frame(
    model: AnimationModel,
    frame_index: int,
    text: str,
    color_index: int,
    start_x: int = 0,
    start_y: int = 0,
) -> None:
    if frame_index < 0 or frame_index >= len(model.frames):
        raise ValueError("frame_index out of range")
    if color_index < 0 or color_index >= len(model.palette):
        raise ValueError("color_index out of range")
    fr = model.frames[frame_index]
    x = start_x
    for ch in text.upper():
        if ch == " ":
            x += 4
            continue
        rows = _FONT.get(ch)
        if not rows:
            continue
        if x + 2 >= GRID or start_y + 4 >= GRID:
            break
        for r, rowbits in enumerate(rows):
            for c in range(3):
                if rowbits & (1 << (2 - c)):
                    px, py = x + c, start_y + r
                    if 0 <= px < GRID and 0 <= py < GRID:
                        fr.set_idx(px, py, color_index)
        x += 4
