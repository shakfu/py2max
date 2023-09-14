import re
import xml.etree.ElementTree as ET
from pathlib import Path

MAX_APP = Path("/Applications/Studio/Max.app")
MAX_APP_REFPAGES = MAX_APP / "Contents/Resources/C74/docs/refpages"


strip = lambda s: s.lstrip().strip() if s else None
dstrip = lambda s: strip(s).replace("\n"," ").replace("  ", " ") if s else None
clean = lambda s: strip(s.replace("<o>", "`")
                         .replace("</o>", "`")
                         .replace("<at>", "`")
                         .replace("</at>", "`")
                         .replace("<m>", "`")
                         .replace("</m>", "`")
                         .replace("<br />", "")
                         .replace("\t", "")
)


class MaxRefParser:
    def __init__(self, path):
        self.path = path
        self.d = {}
        self.root = None

    def parse_inletlist(self, elem: ET.Element):
        self.d["inletlist"] = []
        for inlet in elem:
            _d = {}
            _d.update(inlet.attrib)
            _d["digest"] = strip(inlet[0].text)
            _d["description"] = dstrip(inlet[1].text)
            self.d["inletlist"].append(_d)

    def parse_outletlist(self, elem: ET.Element):
        self.d["outletlist"] = []
        for outlet in elem:
            _d = {}
            _d.update(outlet.attrib)
            _d["digest"] = strip(outlet[0].text)
            _d["description"] = dstrip(outlet[1].text)
            self.d["outletlist"].append(_d)

    def parse_objarglist(self, elem: ET.Element):
        self.d["objarglist"] = []
        for objarg in elem:
            _d = {}
            _d.update(objarg.attrib)
            for subelem in objarg:
                if subelem.tag == "digest":
                    _d["digest"] = strip(subelem.text)
                if subelem.tag == "description":
                    _d["description"] = dstrip(subelem.text)
            self.d["objarglist"].append(_d)

    def parse_methodlist(self, elem: ET.Element):
        self.d["methodlist"] = []
        for method in elem:
            _d = {}
            _d.update(method.attrib)
            for subelem in method:
                if subelem.tag == "arglist":
                    _d['arglist'] = arglist = []
                    for arg in subelem:
                        arglist.append(dict(arg.attrib))
                elif subelem.tag == "digest":
                    _d["digest"] = strip(subelem.text)
                elif subelem.tag == "description":
                    _d["description"] = dstrip(subelem.text)
            self.d["methodlist"].append(_d)

    def parse_attributelist(self, elem: ET.Element):
        self.d["attributelist"] = []
        for attribute in elem:
            _d = {}
            _d.update(attribute.attrib)
            for subelem in attribute:
                if subelem.tag == "attributelist":
                    _d['attributelist'] = sub_attributelist = []
                    for attr in subelem:
                        _a = {}
                        _a.update(attr.attrib)
                        for subsubelem in attr:
                            if subsubelem == "enumlist":
                                _a["enumlist"] = enumlist = []
                                for enum in subsubelem:
                                    _e = {}
                                    _e.update(enum.attrib)
                                    for sub in enum:
                                        if sub.tag == "digest":
                                            _e["digest"] = strip(subelem.text)
                                        if sub.tag == "description":
                                            _e["description"] = dstrip(subelem.text)
                                    enumlist.append(_e)
                        sub_attributelist.append(_a)
                elif subelem.tag == "digest":
                    _d["digest"] = strip(subelem.text)
                elif subelem.tag == "description":
                    _d["description"] = dstrip(subelem.text)
            self.d["attributelist"].append(_d)

    def parse(self) -> ET.Element:
        with open(self.path) as f:
            text = f.read()
            text = clean(text)
        self.root = ET.fromstring(text)

        self.d.update(self.root.attrib)

        for elem in self.root:
            if elem.tag == "digest":
                self.d["digest"] = strip(elem.text)
            elif elem.tag == "description":
                self.d["description"] = dstrip(elem.text)
            elif elem.tag == "inletlist":
                self.parse_inletlist(elem)
            elif elem.tag == "outletlist":
                self.parse_outletlist(elem)
            elif elem.tag == "objarglist":
                self.parse_objarglist(elem)
            elif elem.tag == "methodlist":
                self.parse_methodlist(elem)
            elif elem.tag == "attributelist":
                self.parse_attributelist(elem)

        return self.d

def get_modules():
    modules = {}
    for name in ["m4l", "max", "msp"]:
        modules[name] = {}
        directory = MAX_APP_REFPAGES / f"{name}-ref"
        for f in directory.glob("*.xml"):
            p = MaxRefParser(f)
            d = p.parse()
            modules[name][d['name']] = d
    return modules


if __name__ == '__main__':
    ms = get_modules()



