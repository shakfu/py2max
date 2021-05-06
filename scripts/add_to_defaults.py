#!/usr/bin/env python3

import argparse
import os
import json
import sys
from pathlib import Path
from pprint import pprint

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from py2max.defaults import OBJECT_DEFAULTS
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
            db[entry['text']] = entry
        except KeyError:
            db[entry['maxclass']] = entry
    return db



def gen_defaults(from_folder, outfile='defaults.py'):
    path = Path(from_folder)
    db = {}
    for f in path.iterdir():
        d = convert_patcher_to_dict(f)
        db.update(d)
    db.update(OBJECT_DEFAULTS)
    sorted_db = {k: db[k] for k in sorted(db)}
    with open('defaults.py', 'w') as f:
        f.write('OBJECT_DEFAULTS={}'.format(sorted_db))
    os.system(f'black {outfile}')


if __name__ == '__main__': 
    parser = argparse.ArgumentParser(description='add to OBJECT_DEFAULTS')
    subparsers = parser.add_subparsers(help='sub-command help', dest='command')

    parser_dump = subparsers.add_parser('dump',
                            help='dump objects as .maxpat files from registry to a folder.')
    arg = option = parser_dump.add_argument
    arg('path', help="path to output folder")
    arg('--size', '-s', type=int, help="number of objects per file", default=20)
 
    parser_gen = subparsers.add_parser('gen', 
                            help='generate defaults.py from a folder of .maxpat files.')
    arg = option = parser_gen.add_argument
    arg('from_folder', help='folder of .maxpat files to parse for object defaults')
    option('--output', '-o', help="output path to defaults.py", default='defaults.py')

    args = parser.parse_args()
    if args.command == 'dump':
        dump_registry(args.path, args.size)

    if args.commend == 'gen':
        gen_defaults(args.from_folder, args.output)

