#!/usr/bin/env python3

import os
import sys
from pathlib import Path

# sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from py2max import Patcher
from tests.registry import objects


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def dump_registry(to_folder, size=20):
    os.makedirs(to_folder, exist_ok=True)
    xs = list(objects.keys())

    for i, ys in enumerate(chunks(xs, size)):
        p = Patcher(f"{to_folder}/{i}.maxpat")
        for j in ys:
            p.add_textbox(j)
        p.save()


if __name__ == "__main__":
    dump_registry(to_folder="outputs/registry", size=20)
