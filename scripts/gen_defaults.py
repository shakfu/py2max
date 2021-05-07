#!/usr/bin/env python3

import os
import json
import sys
import shutil
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from py2max import Patcher
from py2max.registry import objects

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def dump_registry(to_folder='out', size=20):
    xs = list(objects.keys())
    
    for i, ys in enumerate(chunks(xs, size)):
        p = Patcher(f'{to_folder}/{i}.maxpat')
        for j in ys:
            p.add_textbox(j)
        p.save()

# def convert_patcher_to_dict(maxpat):
#     with open(maxpat) as f:
#         d = json.load(f)

#     boxes = d['patcher']['boxes']
#     _boxes = [box['box'] for box in boxes]

#     db = {}
#     for b in _boxes:
#         entry = b.copy()
#         del entry['id']
#         _, _, w, h = entry['patching_rect']
#         entry['patching_rect'] = 0.0, 0.0, w, h
#         try:
#             db[entry['text']] = entry
#         except KeyError:
#             db[entry['maxclass']] = entry
#     return db


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
    if os.path.exists(path):
        print(f'reseting {path}')
        shutil.rmtree(path)
        os.mkdir(path)
    dump_registry(to_folder=path, size=20)
    gen_defaults(from_folder=path)

if __name__ == '__main__':
    main()
