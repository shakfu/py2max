from .. import Patcher

POSITIONS = ["above", "right", "below", "left"]


def test_number_tilde():
    p = Patcher('outputs/test_number_tilde.maxpat')
    for pos in POSITIONS:
        p.add_textbox("number~", mode=1, comment=f"mode1-{pos}", comment_pos=pos)
    for pos in POSITIONS:
        p.add_textbox("number~", mode=2, comment=f"mode2-{pos}", comment_pos=pos)
    p.save()


if __name__ == '__main__':
    test_number_tilde()
