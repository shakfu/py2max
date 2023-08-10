import random

from py2max import Patcher

POSITIONS = ["above", "right", "below", "left"]


def test_number_tilde():
    p = Patcher('outputs/test_number_tilde.maxpat')
    for pos in POSITIONS:
        p.add_textbox("number~", mode=1, comment=f"mode1-{pos}", comment_pos=pos)
    for pos in POSITIONS:
        p.add_textbox("number~", mode=2, comment=f"mode2-{pos}", comment_pos=pos)
    p.save()

def test_number_tilde_resized():
    choices = list(range(len(POSITIONS)))
    rw1 = random.randint(30, 200)
    rw2 = random.randint(30, 200)
    rw3 = random.randint(30, 200)
    rw4 = random.randint(30, 200)
    p = Patcher('outputs/test_number_tilde_resized.maxpat')
    p.add_textbox("number~", patching_rect = [150.0, 60.0, rw1, 50.0],
        mode=1, comment=f"mode1-above", comment_pos="above")
    p.add_textbox("number~", patching_rect = [200.0, 120.0, rw2, 50.0],
        mode=2, comment=f"mode2-right", comment_pos="right")
    p.add_textbox("number~", patching_rect = [250.0, 180.0, rw3, 50.0],
        mode=2, comment=f"mode2-below", comment_pos="below")
    p.add_textbox("number~", patching_rect = [300.0, 260.0, rw4, 50.0],
        mode=2, comment=f"mode2-left", comment_pos="left")
    p.save()



if __name__ == '__main__':
    test_number_tilde()
    test_number_tilde_resized()
