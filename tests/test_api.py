from commonsense.sense_paint.api import deserialize_model, draw_text_on_frame, paint_diagonal, serialize_model
from commonsense.sense_paint.model import AnimationModel, Frame, DEFAULT_PALETTE


def test_serialize_round_trip():
    m = AnimationModel(palette=list(DEFAULT_PALETTE[:4]), frames=[Frame(), Frame()])
    d = serialize_model(m)
    m2 = deserialize_model(d)
    assert len(m2.frames) == 2


def test_paint_diagonal():
    m = AnimationModel(palette=[(0, 0, 0), (255, 0, 0)], frames=[Frame()])
    paint_diagonal(m, 0, 1)
    for i in range(8):
        assert m.frames[0].get_idx(i, i) == 1


def test_draw_text_marks_pixels():
    m = AnimationModel(palette=[(0, 0, 0), (255, 255, 255)], frames=[Frame()])
    draw_text_on_frame(m, 0, "A", 1, start_x=2, start_y=1)
    assert sum(1 for p in m.frames[0].pixels if p == 1) > 0
