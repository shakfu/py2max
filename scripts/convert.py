#!/usr/bin/env python3

import argparse
import json
import pathlib


import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper



def convert_maxpat_to_yaml(maxpat_file):
    path = pathlib.Path(maxpat_file)
    name = path.stem
    with open(path) as f:
        d = json.load(f)

    yml_file = path.parent / f'{name}.yml'
    with open(yml_file, 'w') as f:
        yml = yaml.dump(d, Dumper=Dumper)
        f.write(yml)

def convert_yaml_to_maxpat(yml_file):
    path = pathlib.Path(yml_file)
    name  = path.stem
    with open(path) as f:
        d = yaml.load(f, Loader=Loader)

    maxpat_file = path.parent / f'{name}.maxpat'
    with open(maxpat_file, 'w') as f:
        _json = json.dumps(d, indent='\t')
        f.write(_json)

def main(target):
    path = pathlib.Path(target)
    if path.suffix in ['.yml', '.yaml']:
        print(f"converting {path} to .maxpat file:")
        convert_yaml_to_maxpat(path)
    elif path.suffix in ['.maxpat', '.maxhelp']:
        print(f"converting {path} to .yml file")
        convert_maxpat_to_yaml(path)
    else:
        print(f"cannot process: {path}")



if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                    prog='maxpat-converter',
                    description='converts maxpat to and from yml')
    arg = option = parser.add_argument
    arg("target", help="target maxpat or yml file to convert")
    args = parser.parse_args()
    # print(args.target)
    main(args.target)
