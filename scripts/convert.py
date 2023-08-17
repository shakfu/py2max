#!/usr/bin/env python3

import argparse
import json
import pathlib


import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper



def convert_maxfile_to_yaml(max_file):
    path = pathlib.Path(max_file)
    name = path.stem
    with open(path) as f:
        d = json.load(f)

    yml_file = path.parent / f'{name}.yml'
    with open(yml_file, 'w') as f:
        yml = yaml.dump(d, Dumper=Dumper)
        f.write(yml)

def convert_yaml_to_maxfile(yml_file, to_suffix='.maxpat'):
    path = pathlib.Path(yml_file)
    name  = path.stem
    with open(path) as f:
        d = yaml.load(f, Loader=Loader)

    max_file = path.parent / f'{name}{to_suffix}'
    with open(max_file, 'w') as f:
        _json = json.dumps(d, indent='\t')
        f.write(_json)

def main(target, to_suffix='.maxpat'):
    path = pathlib.Path(target)
    if path.suffix in ['.yml', '.yaml']:
        print(f"converting {path} to max file:")
        convert_yaml_to_maxfile(path, to_suffix)
    elif path.suffix in ['.maxpat', '.maxhelp', '.rnbopat']:
        print(f"converting {path} to .yml file")
        convert_maxfile_to_yaml(path)
    else:
        print(f"cannot process: {path}")



if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                    prog='maxfile-converter',
                    description='converts max file to and from yml')
    arg = option = parser.add_argument
    arg("target", help="target max file or yml file to convert")
    option('--to-rnbopat', help="convert yaml to .rnbopat max file type", action="store_true")
    option('--to-maxhelp', help="convert yaml to .maxhelp max file type", action="store_true")
    args = parser.parse_args()
    if args.to_rnbopat:
        main(args.target, to_suffix='.rnbopat')
    elif args.to_maxhelp:
        main(args.target, to_suffix='.maxhelp')
    else:
        main(args.target)
