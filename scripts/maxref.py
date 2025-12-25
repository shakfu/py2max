#!/usr/bin/env python3

"""maxref.py -- handle maxref files.

usage: maxref-parser [-h] [-d] [-c] name

Handle <name>.maxref.xml files

positional arguments:
  name        enter <name>.maxref.xml name

options:
  -h, --help  show this help message and exit
  -d, --dict  dump parsed maxref a dict
  -c, --code  dump parsed maxref as code

"""

import platform
import sys
from pathlib import Path
from textwrap import fill
from pprint import pprint
from xml.etree import ElementTree
from keyword import iskeyword
import json
from typing import Any

try:
    HAVE_YAML = True
    import yaml  # type: ignore[import-untyped]
except ImportError:
    HAVE_YAML = False

# -----------------------------------------------------------------------------
# constants

PLATFORM = platform.system()


# -----------------------------------------------------------------------------
# helper functions


def replace_tags(text: str, sub: str, *tags: str) -> str:
    for tag in tags:
        text = text.replace(f"<{tag}>", sub).replace(f"</{tag}>", sub)
    return text


def to_pascal_case(s: str) -> str:
    return "".join(x for x in s.title() if x not in ["_", "-", " ", "."])


# -----------------------------------------------------------------------------
# main class


class MaxRefDatabase:
    def __init__(self) -> None:
        self.suffix = ".maxref.xml"
        self.db: dict[str, "MaxRefParser"] = {}

    def _get_refpages(self) -> Path | None:
        if PLATFORM == "Darwin":
            for p in Path("/Applications").glob("**/Max.app"):
                if "Ableton" not in str(p):
                    return p / "Contents/Resources/C74/docs/refpages"
        return None

    def collect(self) -> None:
        refpages = self._get_refpages()
        if refpages is None:
            return
        # for prefix in ['jit', 'max', 'msp', 'm4l']:
        for prefix in ["msp"]:
            ref_dir = refpages / f"{prefix}-ref"
            for f in ref_dir.iterdir():
                name = f.name.replace(self.suffix, "")
                self.db[name] = MaxRefParser(name)

    def names(self) -> list[str]:
        return list(self.db.keys())


class MaxRefParser:
    OBJECT_SUPER_CLASS = "Object"
    TRIPLE_QUOTE = '"""'

    def __init__(self, name: str) -> None:
        self.name = name
        self.suffix = ".maxref.xml"
        self.refdict = self.get_refdict()
        self.root: ElementTree.Element | None = None
        self.d: dict[str, Any] = {
            "methods": {},
            "attributes": {},
            "metadata": {},
            "objargs": [],
            "palette": {},
            "parameter": {},
            "examples": [],
            "seealso": [],
            "misc": {},
        }

    def check_exists(self) -> None:
        if self.name not in self.refdict:
            raise KeyError(f"cannot find '{self.name}' maxref")

    def _get_refpages(self) -> Path | None:
        if PLATFORM == "Darwin":
            for p in Path("/Applications").glob("**/Max.app"):
                if "Ableton" not in str(p):
                    return p / "Contents/Resources/C74/docs/refpages"
        return None

    def get_refdict(self) -> dict[str, Path]:
        refdict: dict[str, Path] = {}
        refpages = self._get_refpages()
        if refpages is None:
            return refdict
        for prefix in ["jit", "max", "msp", "m4l"]:
            ref_dir = refpages / f"{prefix}-ref"
            for f in ref_dir.iterdir():
                name = f.name.replace(self.suffix, "")
                refdict[name] = f
        return refdict

    def _clean_text(self, text: str) -> str:
        backtick = "`"
        return replace_tags(text, backtick, "m", "i", "g", "o", "at").replace(
            "&quot;", backtick
        )

    def load(self) -> None:
        filename = self.refdict[self.name]
        cleaned = self._clean_text(filename.read_text())
        self.root = ElementTree.fromstring(cleaned)

    def parse(self) -> None:
        self.check_exists()
        self.load()
        self.extract_basic_info()
        self.extract_metadata()
        self.extract_inlets_outlets()
        self.extract_palette()
        self.extract_objargs()
        self.extract_parameter()
        self.extract_methods()
        self.extract_attributes()
        self.extract_examples()
        self.extract_seealso()
        self.extract_misc()

    def extract_basic_info(self) -> None:
        """Extract basic object information"""
        if self.root is None:
            return
        root = self.root
        self.d.update(root.attrib)

        digest_elem = root.find("digest")
        if digest_elem is not None and digest_elem.text:
            self.d["digest"] = digest_elem.text.strip()

        desc_elem = root.find("description")
        if desc_elem is not None and desc_elem.text:
            self.d["description"] = desc_elem.text.strip()

    def extract_metadata(self) -> None:
        """Extract metadata information"""
        if self.root is None:
            return
        metadatalist = self.root.find("metadatalist")
        if metadatalist is not None:
            for metadata in metadatalist.findall("metadata"):
                name = metadata.get("name")
                if name and metadata.text:
                    if name in self.d["metadata"]:
                        # Handle multiple entries (like multiple tags)
                        if not isinstance(self.d["metadata"][name], list):
                            self.d["metadata"][name] = [self.d["metadata"][name]]
                        self.d["metadata"][name].append(metadata.text.strip())
                    else:
                        self.d["metadata"][name] = metadata.text.strip()

    def extract_inlets_outlets(self) -> None:
        """Extract inlet and outlet information"""
        if self.root is None:
            return
        self.d["inlets"] = []
        inletlist = self.root.find("inletlist")
        if inletlist is not None:
            for inlet in inletlist.findall("inlet"):
                inlet_data: dict[str, Any] = dict(inlet.attrib)
                digest_elem = inlet.find("digest")
                if digest_elem is not None and digest_elem.text:
                    inlet_data["digest"] = digest_elem.text.strip()
                desc_elem = inlet.find("description")
                if desc_elem is not None and desc_elem.text:
                    inlet_data["description"] = desc_elem.text.strip()
                self.d["inlets"].append(inlet_data)

        self.d["outlets"] = []
        outletlist = self.root.find("outletlist")
        if outletlist is not None:
            for outlet in outletlist.findall("outlet"):
                outlet_data: dict[str, Any] = dict(outlet.attrib)
                digest_elem = outlet.find("digest")
                if digest_elem is not None and digest_elem.text:
                    outlet_data["digest"] = digest_elem.text.strip()
                desc_elem = outlet.find("description")
                if desc_elem is not None and desc_elem.text:
                    outlet_data["description"] = desc_elem.text.strip()
                self.d["outlets"].append(outlet_data)

    def extract_palette(self) -> None:
        """Extract palette information"""
        if self.root is None:
            return
        palette = self.root.find("palette")
        if palette is not None:
            self.d["palette"] = dict(palette.attrib)

    def extract_objargs(self) -> None:
        """Extract object arguments"""
        if self.root is None:
            return
        objarglist = self.root.find("objarglist")
        if objarglist is not None:
            for objarg in objarglist.findall("objarg"):
                arg_data: dict[str, Any] = dict(objarg.attrib)
                digest_elem = objarg.find("digest")
                if digest_elem is not None and digest_elem.text:
                    arg_data["digest"] = digest_elem.text.strip()
                desc_elem = objarg.find("description")
                if desc_elem is not None and desc_elem.text:
                    arg_data["description"] = desc_elem.text.strip()
                self.d["objargs"].append(arg_data)

    def extract_parameter(self) -> None:
        """Extract parameter information"""
        if self.root is None:
            return
        parameter = self.root.find("parameter")
        if parameter is not None:
            self.d["parameter"] = dict(parameter.attrib)

    def extract_examples(self) -> None:
        """Extract example information"""
        if self.root is None:
            return
        examplelist = self.root.find("examplelist")
        if examplelist is not None:
            for example in examplelist.findall("example"):
                self.d["examples"].append(dict(example.attrib))

    def extract_seealso(self) -> None:
        """Extract see also references"""
        if self.root is None:
            return
        seealsolist = self.root.find("seealsolist")
        if seealsolist is not None:
            for seealso in seealsolist.findall("seealso"):
                name = seealso.get("name")
                if name:
                    self.d["seealso"].append(name)

    def extract_misc(self) -> None:
        """Extract misc information like Output and Connections"""
        if self.root is None:
            return
        for misc in self.root.findall("misc"):
            misc_name = misc.get("name")
            if misc_name:
                self.d["misc"][misc_name] = {}
                for entry in misc.findall("entry"):
                    entry_name = entry.get("name")
                    if entry_name:
                        desc_elem = entry.find("description")
                        if desc_elem is not None and desc_elem.text:
                            self.d["misc"][misc_name][entry_name] = (
                                desc_elem.text.strip()
                            )

    def extract_attributes(self) -> None:
        """Extract attribute information with full nested structure"""
        if self.root is None:
            return
        self.d["attributes"] = {}
        attributelist = self.root.find("attributelist")
        if attributelist is not None:
            for attr in attributelist.findall("attribute"):
                name = attr.get("name")
                if name:
                    attr_data: dict[str, Any] = dict(attr.attrib)

                    # Extract digest
                    digest_elem = attr.find("digest")
                    if digest_elem is not None and digest_elem.text:
                        attr_data["digest"] = digest_elem.text.strip()

                    # Extract description
                    desc_elem = attr.find("description")
                    if desc_elem is not None and desc_elem.text:
                        attr_data["description"] = desc_elem.text.strip()

                    # Extract nested attributelist (meta-attributes)
                    nested_attrs = attr.find("attributelist")
                    if nested_attrs is not None:
                        attr_data["attributes"] = {}
                        for nested_attr in nested_attrs.findall("attribute"):
                            nested_name = nested_attr.get("name")
                            if nested_name:
                                nested_data = dict(nested_attr.attrib)
                                attr_data["attributes"][nested_name] = nested_data

                    # Extract enumlist if present
                    enumlist = attr.find(".//enumlist")
                    if enumlist is not None:
                        attr_data["enumlist"] = []
                        for enum in enumlist.findall("enum"):
                            enum_data: dict[str, Any] = dict(enum.attrib)
                            digest_elem = enum.find("digest")
                            if digest_elem is not None and digest_elem.text:
                                enum_data["digest"] = digest_elem.text.strip()
                            desc_elem = enum.find("description")
                            if desc_elem is not None and desc_elem.text:
                                enum_data["description"] = desc_elem.text.strip()
                            attr_data["enumlist"].append(enum_data)

                    self.d["attributes"][name] = attr_data

    def extract_methods(self) -> None:
        """Extract method information with full argument and attribute support"""
        if self.root is None:
            return
        self.d["methods"] = {}
        methodlist = self.root.find("methodlist")
        if methodlist is not None:
            for method in methodlist.findall("method"):
                name = method.get("name")
                if name:
                    method_data: dict[str, Any] = dict(method.attrib)

                    # Extract arguments
                    arglist = method.find("arglist")
                    if arglist is not None:
                        method_data["args"] = []
                        for arg in arglist.findall("arg"):
                            method_data["args"].append(dict(arg.attrib))

                        # Handle argument groups
                        for arggroup in arglist.findall("arggroup"):
                            group_attrs = dict(arggroup.attrib)
                            for arg in arggroup.findall("arg"):
                                arg_data = dict(arg.attrib)
                                arg_data.update(group_attrs)  # Add group attributes
                                method_data["args"].append(arg_data)

                    # Extract digest
                    digest_elem = method.find("digest")
                    if digest_elem is not None and digest_elem.text:
                        method_data["digest"] = digest_elem.text.strip()

                    # Extract description
                    desc_elem = method.find("description")
                    if desc_elem is not None and desc_elem.text:
                        method_data["description"] = desc_elem.text.strip()

                    # Extract nested attributelist (method attributes like 'introduced')
                    nested_attrs = method.find("attributelist")
                    if nested_attrs is not None:
                        method_data["attributes"] = {}
                        for nested_attr in nested_attrs.findall("attribute"):
                            nested_name = nested_attr.get("name")
                            if nested_name:
                                nested_data = dict(nested_attr.attrib)
                                method_data["attributes"][nested_name] = nested_data

                    self.d["methods"][name] = method_data

    def dump_dict(self) -> None:
        pprint(self.d)

    def dump_json(self) -> None:
        json.dump(self.d, fp=sys.stdout)

    def __get_method_args(self, args: list[str]) -> list[str]:
        _args: list[str] = []
        for arg in args:
            if "?" in arg:
                arg = arg.replace("?", "")
            if "symbol" in arg:
                arg = arg.replace("symbol", "str")
            if "any" in arg:
                arg = arg.replace("any", "object")
            if "-" in arg:
                arg = arg.replace("-", "_")
            parts = arg.split()
            if len(parts) > 2:
                _type, *name_parts = parts
                name = "_".join(name_parts)
                arg = f"{_type} {name}"
            if "list" in arg:
                arg = arg.replace("list ", "*")
            _args.append(arg)
        return _args

    def __check_iskeyword(self, name: str) -> str:
        if iskeyword(name):
            name = name + "_"
        return name

    def __get_call(self, method_name: str, method_args: list[str]) -> str:
        _args: list[str] = []
        for arg in method_args:
            if "*" in arg:
                arg = arg.replace("*", "")
            else:
                _type, name = arg.split()
                arg = name
            _args.append(arg)
        if len(_args) == 0:
            return f'self.call("{method_name}")'
        else:
            params = ", ".join(_args)
            return f'self.call("{method_name}", {params})'

    def dump_code(self) -> None:
        tq = self.TRIPLE_QUOTE
        superclass = self.OBJECT_SUPER_CLASS
        spacer = " " * 4
        classname = to_pascal_case(self.name)
        print(f"cdef class {classname}({superclass}):")
        digest = self.d.get("digest", "")
        print(f"{spacer}{tq}{digest}")
        print()
        description = self.d.get("description", "")
        print(f"{spacer}{fill(str(description), subsequent_indent=spacer)}")
        print(f"{spacer}{tq}")
        print()
        method_args: list[str] = []
        methods: dict[str, Any] = self.d.get("methods", {})
        for name in methods:
            m = methods[name]
            if "(" in str(name) and ")" in str(name):
                continue

            sig: str | None = None
            args: list[str] = []
            sig_selfless = ""
            if "args" in m:
                args = []
                for arg in m["args"]:
                    if "optional" in arg:
                        args.append("{type} {name}?".format(**arg))
                    else:
                        args.append("{type} {name}".format(**arg))

                method_args = self.__get_method_args(args)
                sig = "{name}({self}{args}):".format(
                    name=self.__check_iskeyword(str(name)),
                    self="self, " if args else "self",
                    args=", ".join(method_args),
                )
                sig_selfless = "{name}({args})".format(
                    name=name, args=", ".join(args)
                )
            else:
                sig = "{name}(self):".format(name=self.__check_iskeyword(str(name)))
            print(f"{spacer}def {sig}")

            if "digest" in m:
                print(f"{spacer * 2}{tq}{m['digest']}")
            if args:
                print()
                print(f"{spacer * 2}{sig_selfless}")
            if "description" in m:
                if m["description"] and "TEXT_HERE" not in m["description"]:
                    print()
                    print(
                        f"{spacer * 2}{fill(m['description'], subsequent_indent=spacer * 2)}"
                    )
            print(f"{spacer * 2}{tq}")
            print(f"{spacer * 2}{self.__get_call(str(name), method_args)}")
            print()

    def dump_tests(self) -> None:
        spacer = " " * 4
        classname = self.d.get("name", "unknown")
        tq = self.TRIPLE_QUOTE

        methods: dict[str, Any] = self.d.get("methods", {})
        for name in methods:
            m = methods[name]
            print(f"def test_{classname}_{name}():")
            print(f"{spacer}{tq}{m.get('digest', '')}{tq}")
            print()

    if HAVE_YAML:

        def dump_yaml(self) -> None:
            print(yaml.dump(self.d, Dumper=yaml.Dumper))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        prog="maxref-parser",
        description="Parse and generate code from *.maxref.xml files.",
    )
    parser.add_argument("name", nargs="?", help="enter <name>.maxref.xml name")
    parser.add_argument(
        "-d", "--dict", action="store_true", help="dump parsed maxref as dict"
    )
    parser.add_argument(
        "-j", "--json", action="store_true", help="dump parsed maxref as json"
    )
    parser.add_argument(
        "-c", "--code", action="store_true", help="generate class outline"
    )
    parser.add_argument("-t", "--test", action="store_true", help="generate tests")
    if HAVE_YAML:
        parser.add_argument(
            "-y", "--yaml", action="store_true", help="dump parsed maxref as yaml"
        )
    parser.add_argument("-l", "--list", action="store_true", help="list all objects")
    parser.add_argument(
        "-i", "--info", action="store_true", help="list all objects with info"
    )

    args = parser.parse_args()
    p = MaxRefParser(args.name)

    # pre-parsing actions -------
    if args.list:
        for name in sorted(p.refdict.keys()):
            print(name)
        sys.exit(0)
    elif args.info:
        _db = MaxRefDatabase()
        _db.collect()
        res: dict[str, Any] = {}
        for name, refobj in _db.db.items():
            try:
                refobj.parse()
                res[name] = refobj.d["digest"]
            except Exception:
                pass
        with open("objects-msp.py", "w") as f:
            pprint(res, stream=f)
        sys.exit(0)

    # post-parsing actions -------
    p.parse()
    assert args.name, "name in `maxref [options] <name>` must be provided"
    if args.dict:
        p.dump_dict()

    elif args.code:
        p.dump_code()

    elif args.json:
        p.dump_json()

    elif args.test:
        p.dump_tests()

    elif HAVE_YAML and args.yaml:
        p.dump_yaml()
