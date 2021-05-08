#!/usr/bin/env python3
import sys

template = """
from .. import Patcher


def test_{name}():
    p = Patcher('outputs/test_{name}.maxpat')
    obj = p.add_textbox('{obj}')
    p.save()


if __name__ == '__main__':
    test_{name}()
"""

if __name__ == '__main__':
    length = len(sys.argv)
    if length in [2, 3]:
        name = sys.argv[1]
        obj = name if length == 2 else sys.argv[2]
        with open(f'py2max/tests/test_{name}.py', 'w') as f:
            rendered = template.format(name=name, obj=obj)
            f.write(rendered)
    else:
        print("At least one arg must be given: gen_test.py <name> [<obj>]")

