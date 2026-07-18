import random

from py2max import Patcher

POSITIONS = ["above", "right", "below", "left"]


def test_number_tilde():
    p = Patcher("outputs/test_number_tilde.maxpat")
    boxes = []
    for pos in POSITIONS:
        boxes.append(
            p.add_textbox("number~", mode=1, comment=f"mode1-{pos}", comment_pos=pos)
        )
    for pos in POSITIONS:
        boxes.append(
            p.add_textbox("number~", mode=2, comment=f"mode2-{pos}", comment_pos=pos)
        )
    p.save()

    # each add_textbox with a comment also emits a separate comment box on save
    number_boxes = [b for b in p._boxes if b.maxclass == "number~"]
    comment_boxes = [b for b in p._boxes if b.maxclass == "comment"]
    assert len(number_boxes) == 8
    assert len(comment_boxes) == 8
    for b in boxes:
        assert b.maxclass == "number~"
        assert b.text == "number~"

    for b in boxes[:4]:
        assert b.to_dict()["box"]["mode"] == 1
    for b in boxes[4:]:
        assert b.to_dict()["box"]["mode"] == 2


def test_number_tilde_resized():
    list(range(len(POSITIONS)))
    rw1 = random.randint(30, 200)
    rw2 = random.randint(30, 200)
    rw3 = random.randint(30, 200)
    rw4 = random.randint(30, 200)
    p = Patcher("outputs/test_number_tilde_resized.maxpat")
    b1 = p.add_textbox(
        "number~",
        patching_rect=[150.0, 60.0, rw1, 50.0],
        mode=1,
        comment="mode1-above",
        comment_pos="above",
    )
    b2 = p.add_textbox(
        "number~",
        patching_rect=[200.0, 120.0, rw2, 50.0],
        mode=2,
        comment="mode2-right",
        comment_pos="right",
    )
    b3 = p.add_textbox(
        "number~",
        patching_rect=[250.0, 180.0, rw3, 50.0],
        mode=2,
        comment="mode2-below",
        comment_pos="below",
    )
    b4 = p.add_textbox(
        "number~",
        patching_rect=[300.0, 260.0, rw4, 50.0],
        mode=2,
        comment="mode2-left",
        comment_pos="left",
    )
    p.save()

    number_boxes = [b for b in p._boxes if b.maxclass == "number~"]
    comment_boxes = [b for b in p._boxes if b.maxclass == "comment"]
    assert len(number_boxes) == 4
    assert len(comment_boxes) == 4
    for b in (b1, b2, b3, b4):
        assert b.maxclass == "number~"

    assert b1.to_dict()["box"]["mode"] == 1
    for b in (b2, b3, b4):
        assert b.to_dict()["box"]["mode"] == 2

    assert b1.patching_rect[2] == rw1
    assert b2.patching_rect[2] == rw2
    assert b3.patching_rect[2] == rw3
    assert b4.patching_rect[2] == rw4
