#!/usr/bin/env python3

import os
import json
from pathlib import Path

#sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from py2max import Patcher

def convert_patcher_to_dict(maxpat):
    with open(maxpat) as f:
        d = json.load(f)

    boxes = d['patcher']['boxes']
    _boxes = [box['box'] for box in boxes]

    db = {}
    for b in _boxes:
        entry = b.copy()
        del entry['id']
        _, _, w, h = entry['patching_rect']
        entry['patching_rect'] = 0.0, 0.0, w, h
        try:
            db[entry['maxclass']] = entry
        except KeyError:
            continue
    return db


def gen_defaults(from_folder, outfile='defaults.py'):
    object_defaults = {}
    path = Path(from_folder)
    db = {}
    for f in path.iterdir():
        d = convert_patcher_to_dict(f)
        db.update(d)
    db.update(object_defaults)
    sorted_db = {k: db[k] for k in sorted(db)}
    with open('defaults.py', 'w') as f:
        f.write('OBJECT_DEFAULTS={}'.format(sorted_db))
    os.system(f'black {outfile}')


def main(path='outputs'):
    if not os.path.exists(path):
        os.mkdir(path)
    gen_defaults(from_folder=path)

if __name__ == '__main__':
    main()
