import re
import xml.etree.ElementTree as ET
from pathlib import Path

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


def parse_maxref(path) -> dict:
    d = {}
    with open(path) as f:
        text = f.read()
        text = clean(text)
    root = ET.fromstring(text)
    d.update(root.attrib)
    for elem in root:
        if elem.tag == "digest":
            d["digest"] = strip(elem.text)
        elif elem.tag == "description":
            d["description"] = dstrip(elem.text)
        elif elem.tag == "inletlist":
            d["inletlist"] = inletlist = []
            for inlet in elem:
                _d = {}
                _d.update(inlet.attrib)
                _d["digest"] = strip(inlet[0].text)
                _d["description"] = dstrip(inlet[1].text)
                inletlist.append(_d)
        elif elem.tag == "outletlist":
            d["outletlist"] = outletlist = []
            for outlet in elem:
                _d = {}
                _d.update(outlet.attrib)
                _d["digest"] = strip(outlet[0].text)
                _d["description"] = dstrip(outlet[1].text)
                outletlist.append(_d)
        elif elem.tag == "objarglist":
            d["objarglist"] = objarglist = []
            for objarg in elem:
                _d = {}
                _d.update(objarg.attrib)
                for subelem in objarg:
                    if subelem.tag == "digest":
                        _d["digest"] = strip(subelem.text)
                    if subelem.tag == "description":
                        _d["description"] = dstrip(subelem.text)
                objarglist.append(_d)
        elif elem.tag == "methodlist":
            d["methodlist"] = methodlist = []
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
                methodlist.append(_d)
        elif elem.tag == "attributelist":
            d["attributelist"] = attributelist = []
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
                attributelist.append(_d)
    return d

modules = {}
for name in ["m4l", "max", "msp"]:
    modules[name] = {}
    for f in Path(f"{name}-ref").iterdir():
        d = parse_maxref(f)
        modules[name][d['name']] = d
d = modules['msp']['adsr~']



