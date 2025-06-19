#!/usr/bin/env python3


import json
import platform
import re
import sys
from keyword import iskeyword
from pathlib import Path
from pprint import pprint
from tempfile import TemporaryDirectory
from textwrap import fill

from typing import Optional, Any

import xmltodict
import yaml
try:
    from yaml import CLoader as yaml_Loader, CDumper as yaml_Dumper
except ImportError:
    from yaml import Loader as yaml_Loader, Dumper as yaml_Dumper

# -----------------------------------------------------------------------------
# constants

PLATFORM = platform.system()


# -----------------------------------------------------------------------------
# helper functions

def replace_tags(text, sub, *tags):
    for tag in tags:
        text = text.replace(f'<{tag}>', sub).replace(f'</{tag}>', sub)
    return text

def to_pascal_case(s):
    return ''.join(x for x in s.title() if not x in ['_','-',' ', '.'])

# -----------------------------------------------------------------------------
# main class


class MaxRefDB:

    def __init__(self):
        self.suffix = '.maxref.xml'
        self.db = self.get_db()

    def __len__(self) -> int:
        return len(self.db.keys())

    def _get_refpages(self) -> Path:
        if PLATFORM == 'Darwin':
            for p in Path('/Applications').glob('**/Max.app'):
                if not 'Ableton' in str(p):
                    return p / 'Contents/Resources/C74/docs/refpages'

    def get_db(self) -> dict[str, dict[str, str]]:
        _db = {}
        refpages = self._get_refpages()
        for prefix in ['jit', 'max', 'msp', 'm4l']:
            ref_dir = refpages / f'{prefix}-ref'
            for f in ref_dir.iterdir():
                name = f.name.replace(self.suffix, '')
                _db[name] = str(f)
        return _db

    def parse(self, name: str) -> 'MaxRefObject':
        assert name in self.db, f"{name} does not exist in db"
        return MaxRefObject(path=self.db[name])



class MaxRefObject:
    OBJECT_SUPER_CLASS = 'Box'
    TRIPLE_QUOTE = '\"\"\"'

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.suffix = '.maxref.xml'
        self.d = self.load()

    def _get_prop(self, key: str, parent: dict) -> Optional[str]:
        if key in parent and parent.get(key):
            return parent.get(key)

    @property
    def name(self) -> str:
        return self.d['c74object']['@name']

    @property
    def identifier(self) -> str:
        if self.name.endswith('~'):
            return self.name[:-1] + '_tilde'
        return self.name

    @property
    def module(self) -> str:
        return self.d['c74object']['@module']

    @property
    def category(self) -> str:
        return self.d['c74object']['@category']

    @property
    def classname(self) -> str:
        return to_pascal_case(self.identifier)

    @property
    def superclass(self) -> str:
        return self.OBJECT_SUPER_CLASS

    @property
    def digest(self) -> Optional[str]:
        return self._get_prop('digest', self.d['c74object'])

    @property
    def description(self) -> Optional[str]:
        return self._get_prop('description', self.d['c74object'])

    @property
    def discussion(self) -> Optional[str]:
        return self._get_prop('discussion', self.d['c74object'])
    
    def get_attributes(self, attrs: list[dict]) -> list[dict[str, Any]]:
        _attrs = []
        for attr in attrs:
            _attr = {
                'name': attr['@name'],
                'get': bool(int(attr['@get'])),
                'set': bool(int(attr['@set'])),
                'size': int(attr['@size']),
                'type': attr['@type'],
            }
            if '@value' in attr:
                _attr['value'] = attr['@value']
            if 'description' in attr and attr['description'] and attr['description'] != 'TEXT_HERE':
                _attr['description'] = attr['description']
            if 'digest' in attr and attr['digest'] and attr['digest'] != 'TEXT_HERE':
                _attr['digest'] = attr['digest']
            if 'attributelist' in attr and attr['attributelist'] and attr['attributelist']['attribute']:                
                _attr['attributes'] = []
                if isinstance(attr['attributelist']['attribute'], dict):
                    attr['attributelist']['attribute'] = [attr['attributelist']['attribute']]
                _attr['attributes'] = self.get_attributes(attr['attributelist']['attribute'])
            _attrs.append(_attr)
        return _attrs

    @property
    def attributes(self) -> list[dict[str, Any]]:
        if self.d['c74object']['attributelist']['attribute']:
            return self.get_attributes(self.d['c74object']['attributelist']['attribute'])
        return []

    @property
    def inlets(self) -> list[dict[str, Any]]:
        _inlets = []
        for inlet in self.d['c74object']['inletlist']['inlet']:
            _inlet = {
                'id': int(inlet['@id']),
                'type': inlet['@type'],
            }
            if 'description' in inlet and inlet['description'] and inlet['description'] != 'TEXT_HERE':
                _inlet['description'] = inlet['description']
            if 'digest' in inlet and inlet['digest'] and inlet['digest'] != 'TEXT_HERE':
                _inlet['digest'] = inlet['digest']
            _inlets.append(_inlet)
        return _inlets
    
    @property
    def outlets(self) -> list[dict[str, Any]]:
        _outlets = []
        if isinstance(self.d['c74object']['outletlist']['outlet'], dict):
            self.d['c74object']['outletlist']['outlet'] = [self.d['c74object']['outletlist']['outlet']]
        for outlet in self.d['c74object']['outletlist']['outlet']:
            _outlet = {
                'id': int(outlet['@id']),
                'type': outlet['@type'],
            }
            if 'description' in outlet and outlet['description'] and outlet['description'] != 'TEXT_HERE':
                _outlet['description'] = outlet['description']
            if 'digest' in outlet and outlet['digest'] and outlet['digest'] != 'TEXT_HERE':
                _outlet['digest'] = outlet['digest']
            _outlets.append(_outlet)
        return _outlets
    
    @property
    def args(self) -> list[dict[str, Any]]:
        _args = []
        for arg in self.d['c74object']['objarglist']['objarg']:
            _arg = {
                'name': arg['@name'],
                'optional': bool(int(arg['@optional'])),
                'type': arg['@type'],
                }
            if '@units' in arg:
                _arg['units'] = arg['@units']
            if 'description' in arg and arg['description'] and arg['description'] != 'TEXT_HERE':
                _arg['description'] = arg['description']
            if 'digest' in arg and arg['digest'] and arg['digest'] != 'TEXT_HERE':
                _arg['digest'] = arg['digest']
            _args.append(_arg)
        return _args

    @property
    def methods(self) -> list[dict[str, Any]]:
        _methods = []
        for method in self.d['c74object']['methodlist']['method']:
            _method = {
                'name': method['@name'],
            }
            if 'description' in method and method['description'] and method['description'] != 'TEXT_HERE':
                _method['description'] = method['description']
            if 'digest' in method and method['digest'] and method['digest'] != 'TEXT_HERE':
                _method['digest'] = method['digest']
            if 'arglist' in method and method['arglist'] and method['arglist']['arg']:
                _args = []
                if isinstance(method['arglist']['arg'], dict):
                    method['arglist']['arg'] = [method['arglist']['arg']]
                for arg in method['arglist']['arg']:
                    _args.append({
                        'name': arg['@name'],
                        'optional': bool(int(arg['@optional'])),
                        'type': arg['@type'],
                    })
                _method['args'] = _args
            _methods.append(_method)
        return _methods

    @property
    def seelso(self) -> list[str]:
        _entries = []
        if 'seealsolist' in self.d['c74object'] and self.d['c74object']['seealsolist']['seealso']:
            for entry in self.d['c74object']['seealsolist']['seealso']:
                _entries.append(entry['@name'])
        return _entries

    def _clean_text(self, text: str) -> str:
        backtick = '`'
        return (
            replace_tags(text, backtick, 'm', 'i', 'g', 'o', 'at')
            .replace('&quot;', backtick)
        )

    def _clean_linebreaks(self, text: str) -> str:
        linebreak = '\n'
        variations = ['<br>', '<br/>', '<br />']
        for variation in variations:
            text = text.replace(variation, linebreak)
        return text

    def _clean_whitespace(self, text: str) -> str:
        text = text.replace('\t', '')
        text = re.sub(r'\n+', '\n', text)
        return text

    def preprocess(self, content: str) -> str:
        content = self._clean_text(content)
        content = self._clean_linebreaks(content)
        content = self._clean_whitespace(content)
        return content

    def load(self) -> None:
        with open(self.path) as f:
            content = f.read()
            preprocessed = self.preprocess(content)
        return xmltodict.parse(preprocessed)

    def parse(self):
        self.check_exists()
        self.load()

    def as_objdict(self) -> dict:
        return {
            'name': self.name,
            'module': self.module,
            'category': self.category,
            'classname': self.classname,
            'superclass': self.superclass,
            'digest': self.digest,
            'description': self.description,
            'discussion': self.discussion,
            'attributes': self.attributes,
            'inlets': self.inlets,
            'outlets': self.outlets,
            'args': self.args,
            'methods': self.methods,
            'seelso': self.seelso,
        }
    
    def as_objdict_json(self) -> str:
        return json.dumps(self.as_objdict(), indent=2)
    
    def as_objdict_yaml(self, indent: int = 2, to_file: Optional[str] = None):
        _yml = yaml.dump(self.as_objdict(), Dumper=yaml_Dumper, indent=indent)
        if to_file:
            with open(to_file, 'w') as f:
                print(_yml, file=f)
        else:
            print(_yml)

    def as_json_schema(self):
        return {
            '$id': 'https://example.com/person.schema.json',
            '$schema': 'https://json-schema.org/draft/2020-12/schema',
            'title': self.classname,
            'description': self.description,
            'type': 'object',
            'properties': self.properties,
        }

    def as_class(self):
        tq = self.TRIPLE_QUOTE
        spacer = ' '*4
        print(f'class {self.classname}({self.superclass}):')
        print(f"{spacer}{tq}{self.digest}")
        print()
        description =fill(self.description, subsequent_indent=spacer)
        print(f"{spacer}{description}")
        print(f"{spacer}{tq}")
        print()
        for m in self.methods:
            name = m['name']
            if '(' in name and ')' in name:
                continue
            if name == 'signal':
                m['args'] = [{'name': 'value', 'type': 'float'}]
            sig = None
            if 'args' in m:
                args = []
                for arg in m['args']:
                    if 'optional' in arg:
                        args.append('{type} {name}?'.format(**arg))
                    else:
                        args.append('{type} {name}'.format(**arg))

                method_args = self.__get_method_args(args)
                sig = "{name}({self}{args}):".format(
                    name=self.__check_iskeyword(name),
                    self='self, ' if args else 'self',
                    args=", ".join(method_args))
                sig_selfless = "{name}({args})".format(
                    name=name,
                    args=", ".join(args))
            else:
                sig = "{name}(self):".format(name=self.__check_iskeyword(name))
            print(f'{spacer}def {sig}')

            if 'digest' in m:
                print('{spacer}{tq}{digest}'.format(
                    spacer=spacer*2,
                    tq=tq,
                    digest=m['digest']))
            if args:
                print()
                print("{spacer}{sig}".format(spacer=spacer*2, sig=sig_selfless))
            if 'description' in m:
                if m['description'] and 'TEXT_HERE' not in m['description']:
                    print()
                    print('{spacer}{desc}'.format(
                        spacer=spacer*2,
                        desc=fill(m['description'], subsequent_indent=spacer*2)))
            print('{spacer}{tq}'.format(spacer=spacer*2, tq=tq))
            print('{spacer}{call}'.format(
                spacer=spacer*2, call=self.__get_call(name, method_args)))
            print()

    def dump_json_schema(self):
        pprint(self.as_json_schema())

    def as_dict(self) -> dict:
        return self.d

    def dump_dict(self):
        pprint(self.d)

    def dump_json(self):
        json.dump(self.d, fp=sys.stdout)

    def dump_yaml(self, indent: int = 2, to_file: Optional[str] = None):
        _yml = yaml.dump(self.d, Dumper=yaml_Dumper, indent=indent)
        if to_file:
            with open(to_file, 'w') as f:
                print(_yml, file=f)
        else:
            print(_yml)

    def __get_method_args(self, args: list[str]) -> list[str]:
        _args = []
        for i, arg in enumerate(args):
            if '?' in arg:
                arg = arg.replace('?', '')
            if 'symbol' in arg:
                arg = arg.replace('symbol', 'str')
            if 'any' in arg:
                arg = arg.replace('any', 'object')
            if '-' in arg:
                arg = arg.replace('-', '_')
            parts = arg.split()
            if len(parts) > 2:
                _type, *name_parts = parts
                name = '_'.join(name_parts)
                arg = f"{_type} {name}"
            if 'list' in arg:
                arg = arg.replace('list ', '*')
            _args.append(arg)
        return _args

    def __check_iskeyword(self, name: str) -> str:
        if iskeyword(name):
            name = name+'_'
        return name

    def __get_call(self, method_name: str, method_args: list[str]) -> str:
        _args = []
        for arg in method_args:
            if '*' in arg:
                arg = arg.replace('*', '')
            else:
                _type, name = arg.split()
                arg = name
            _args.append(arg)
        if len(_args) == 0:
            return f'self.call("{method_name}")'
        else:
            params = ", ".join(_args)
            return f'self.call("{method_name}", {params})'



db = MaxRefDB()
p = db.parse('filepath')



