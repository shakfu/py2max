#!/usr/bin/env python3

import argparse
import json
import pathlib
import pprint

import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper



from deepdiff import DeepDiff

def from_json(maxpat) -> dict:
    path = pathlib.Path(maxpat)
    name = path.stem
    with open(path) as f:
        d = json.load(f)
    return d

def compare(maxpat1, maxpat2, options=None):
    p1 = pathlib.Path(maxpat1)
    p2 = pathlib.Path(maxpat2)
    d1 = from_json(p1)
    d2 = from_json(p2)
    delta = dict(DeepDiff(d1, d2))
    if options:
        if options.yml:
            yml_diff = p1.parent / f'{p1.stem}-{p2.stem}-delta.yml'
            with open(yml_diff, 'w') as f:
                yml = yaml.dump(delta, Dumper=Dumper)
                f.write(yml)
    else:
        pprint.pprint(delta, indent=2)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                    prog='maxpat-comparer',
                    description='compares two maxpat files recursively')
    arg = option = parser.add_argument
    option('-y', '--yml', help='convert output to yaml', action='store_true')
    arg("maxpat1", help="maxpat file 1")
    arg("maxpat2", help="maxpat file 2")
    args = parser.parse_args()
    compare(args.maxpat1, args.maxpat2, options=args)
