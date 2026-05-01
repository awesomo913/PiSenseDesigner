import pytest

from commonsense.sense_paint.model import CELLS, AnimationModel, Frame


def test_model_round_trip():
    m = AnimationModel(palette=[(0, 0, 0), (255, 0, 0)], frames=[Frame(), Frame()])
    m.frames[0].pixels[0] = 1
    d = m.to_dict()
    m2 = AnimationModel.from_dict(d)
    assert m2.palette == m.palette
    assert m2.frames[0].pixels == m.frames[0].pixels


def test_invalid_pixel_index():
    m = AnimationModel(palette=[(0, 0, 0)], frames=[Frame()])
    m.frames[0].pixels[0] = 1
    with pytest.raises(ValueError):
        m.validate()


def test_from_dict_bad_frame_length():
    data = {
        "palette": [[0, 0, 0]],
        "frames": [[0] * (CELLS - 1)],
        "frame_delay_ms": 100,
        "loop": True,
    }
    with pytest.raises(ValueError):
        AnimationModel.from_dict(data)
