import json

OBJECT_DEFAULTS = {
    "button": {
        "maxclass": "button",
        "numinlets": 1,
        "numoutlets": 1,
        "outlettype": ["bang"],
        "parameter_enable": 0,
        "patching_rect": [0.0, 0.0, 24.0, 24.0],
    },
    "dial": {
        "maxclass": "dial",
        "numinlets": 1,
        "numoutlets": 1,
        "outlettype": ["float"],
        "parameter_enable": 0,
        "patching_rect": [0.0, 0.0, 40.0, 40.0],
    },
    "ezadc~": {
        "maxclass": "ezadc~",
        "numinlets": 1,
        "numoutlets": 2,
        "outlettype": ["signal", "signal"],
        "patching_rect": [0.0, 0.0, 45.0, 45.0],
    },
    "ezdac~": {
        "maxclass": "ezdac~",
        "numinlets": 2,
        "numoutlets": 0,
        "patching_rect": [0.0, 0.0, 45.0, 45.0],
    },
    "filtergraph~": {
        "fontface": 0,
        "linmarkers": [0.0, 11025.0, 16537.5],
        "logmarkers": [0.0, 100.0, 1000.0, 10000.0],
        "maxclass": "filtergraph~",
        "nfilters": 1,
        "numinlets": 8,
        "numoutlets": 7,
        "outlettype": ["list", "float", "float", "float", "float", "list", "int"],
        "parameter_enable": 0,
        "patching_rect": [0.0, 0.0, 256.0, 128.0],
        "setfilter": [0, 5, 1, 0, 0, 40.0, 1.0, 2.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    },
    "function": {
        "maxclass": "function",
        "numinlets": 1,
        "numoutlets": 4,
        "outlettype": ["float", "", "", "bang"],
        "parameter_enable": 0,
        "patching_rect": [0.0, 0.0, 200.0, 100.0],
    },
    "gain~": {
        "maxclass": "gain~",
        "multichannelvariant": 0,
        "numinlets": 1,
        "numoutlets": 2,
        "outlettype": ["signal", ""],
        "parameter_enable": 0,
        "patching_rect": [0.0, 0.0, 22.0, 140.0],
    },
    "gswitch": {
        "maxclass": "gswitch",
        "numinlets": 3,
        "numoutlets": 1,
        "outlettype": [""],
        "parameter_enable": 0,
        "patching_rect": [0.0, 0.0, 41.0, 32.0],
    },
    "gswitch2": {
        "maxclass": "gswitch2",
        "numinlets": 2,
        "numoutlets": 2,
        "outlettype": ["", ""],
        "parameter_enable": 0,
        "patching_rect": [0.0, 0.0, 39.0, 32.0],
    },
    "incdec": {
        "maxclass": "incdec",
        "numinlets": 1,
        "numoutlets": 1,
        "outlettype": ["float"],
        "parameter_enable": 0,
        "patching_rect": [0.0, 0.0, 20.0, 24.0],
    },
    "kslider": {
        "maxclass": "kslider",
        "numinlets": 2,
        "numoutlets": 2,
        "outlettype": ["int", "int"],
        "parameter_enable": 0,
        "patching_rect": [0.0, 0.0, 336.0, 53.0],
    },
    "led": {
        "maxclass": "led",
        "numinlets": 1,
        "numoutlets": 1,
        "outlettype": ["int"],
        "parameter_enable": 0,
        "patching_rect": [0.0, 0.0, 24.0, 24.0],
    },
    "levelmeter~": {
        "markers": [-60, -48, -36, -24, -12, -6, 0, 6],
        "markersused": 8,
        "maxclass": "levelmeter~",
        "numinlets": 1,
        "numoutlets": 1,
        "outlettype": [""],
        "patching_rect": [0.0, 0.0, 128.0, 64.0],
    },
    "matrixctrl": {
        "maxclass": "matrixctrl",
        "numinlets": 1,
        "numoutlets": 2,
        "outlettype": ["list", "list"],
        "parameter_enable": 0,
        "patching_rect": [0.0, 0.0, 130.0, 66.0],
    },
    "meter~": {
        "maxclass": "meter~",
        "numinlets": 1,
        "numoutlets": 1,
        "outlettype": ["float"],
        "patching_rect": [0.0, 0.0, 80.0, 13.0],
    },
    "multislider": {
        "maxclass": "multislider",
        "numinlets": 1,
        "numoutlets": 2,
        "outlettype": ["", ""],
        "parameter_enable": 0,
        "patching_rect": [0.0, 0.0, 20.0, 140.0],
    },
    "nodes": {
        "maxclass": "nodes",
        "nodesnames": ["1"],
        "nsize": [0.2],
        "numinlets": 1,
        "numoutlets": 3,
        "outlettype": ["", "", ""],
        "parameter_enable": 0,
        "patching_rect": [231.0, 478.0, 100.0, 100.0],
        "xplace": [0.083333333333333],
        "yplace": [0.083333333333333],
    },
    "nslider": {
        "maxclass": "nslider",
        "numinlets": 2,
        "numoutlets": 2,
        "outlettype": ["int", "int"],
        "parameter_enable": 0,
        "patching_rect": [0.0, 0.0, 75.0, 198.0],
    },
    "number~": {
        "fontface": 0,
        "fontname": "Arial",
        "fontsize": 12.0,
        "maxclass": "number~",
        "mode": 2,
        "numinlets": 2,
        "numoutlets": 2,
        "outlettype": ["signal", "float"],
        "patching_rect": [0.0, 0.0, 56.0, 22.0],
        "sig": 0.0,
    },
    "pictctrl": {
        "maxclass": "pictctrl",
        "numinlets": 1,
        "numoutlets": 1,
        "outlettype": ["int"],
        "parameter_enable": 0,
        "patching_rect": [0.0, 0.0, 20.0, 20.0],
    },
    "pictslider": {
        "maxclass": "pictslider",
        "numinlets": 2,
        "numoutlets": 2,
        "outlettype": ["int", "int"],
        "parameter_enable": 0,
        "patching_rect": [0.0, 0.0, 100.0, 100.0],
    },
    "playbar": {
        "maxclass": "playbar",
        "numinlets": 1,
        "numoutlets": 2,
        "outlettype": ["", "int"],
        "patching_rect": [0.0, 0.0, 320.0, 16.0],
    },
    "playlist~": {
        "basictuning": 0,
        "data": {"clips": []},
        "followglobaltempo": 0,
        "formantcorrection": 0,
        "maxclass": "playlist~",
        "mode": 0,
        "numinlets": 1,
        "numoutlets": 5,
        "originallength": [0],
        "originaltempo": 0,
        "outlettype": ["signal", "signal", "signal", "", "dictionary"],
        "parameter_enable": 0,
        "patching_rect": [0.0, 0.0, 150.0, 92.0],
        "pitchcorrection": 0,
        "quality": 0,
        "timestretch": [0],
    },
    "radiogroup": {
        "disabled": [0, 0],
        "itemtype": 0,
        "maxclass": "radiogroup",
        "numinlets": 1,
        "numoutlets": 1,
        "outlettype": [""],
        "parameter_enable": 0,
        "patching_rect": [0.0, 0.0, 18.0, 34.0],
        "size": 2,
        "value": 0,
    },
    "rslider": {
        "maxclass": "rslider",
        "numinlets": 2,
        "numoutlets": 2,
        "outlettype": ["", ""],
        "parameter_enable": 0,
        "patching_rect": [0.0, 0.0, 20.0, 140.0],
    },
    "scope~": {
        "maxclass": "scope~",
        "numinlets": 2,
        "numoutlets": 0,
        "patching_rect": [0.0, 0.0, 130.0, 130.0],
    },
    "slider": {
        "maxclass": "slider",
        "numinlets": 1,
        "numoutlets": 1,
        "outlettype": [""],
        "parameter_enable": 0,
        "patching_rect": [0.0, 0.0, 20.0, 140.0],
    },
    "spectroscope~": {
        "maxclass": "spectroscope~",
        "numinlets": 2,
        "numoutlets": 1,
        "outlettype": [""],
        "patching_rect": [0.0, 0.0, 300.0, 100.0],
    },
    "tab": {
        "maxclass": "tab",
        "numinlets": 1,
        "numoutlets": 3,
        "outlettype": ["int", "", ""],
        "parameter_enable": 0,
        "patching_rect": [0.0, 0.0, 200.0, 24.0],
    },
    "textbutton": {
        "maxclass": "textbutton",
        "numinlets": 1,
        "numoutlets": 3,
        "outlettype": ["", "", "int"],
        "parameter_enable": 0,
        "patching_rect": [0.0, 0.0, 100.0, 20.0],
    },
    "toggle": {
        "maxclass": "toggle",
        "numinlets": 1,
        "numoutlets": 1,
        "outlettype": ["int"],
        "parameter_enable": 0,
        "patching_rect": [0.0, 0.0, 24.0, 24.0],
    },
    "ubutton": {
        "handoff": "",
        "maxclass": "ubutton",
        "numinlets": 1,
        "numoutlets": 4,
        "outlettype": ["bang", "bang", "", "int"],
        "parameter_enable": 0,
        "patching_rect": [0.0, 0.0, 33.0, 42.0],
    },
    "waveform~": {
        "buffername": "",
        "maxclass": "waveform~",
        "numinlets": 5,
        "numoutlets": 6,
        "outlettype": ["float", "float", "float", "float", "list", ""],
        "patching_rect": [0.0, 0.0, 256.0, 64.0],
    },
    "zplane~": {
        "maxclass": "zplane~",
        "numinlets": 5,
        "numoutlets": 4,
        "outlettype": ["list", "list", "list", "list"],
        "patching_rect": [0.0, 0.0, 256.0, 256.0],
    },
}


def convert_patcher_to_dict(maxpat):
    with open(maxpat) as f:
        d = json.load(f)

    boxes = d['patcher']['boxes']
    _boxes = [box['box'] for box in boxes]

    db = {}
    for b in _boxes:
        entry = b.copy()
        del entry['id']
        db[entry['maxclass']] = entry

    return db


# class SmartBox:
#     """prototype minimal textbox"""
#     def __init__(self, text: str, **kwds):
#         self.text = text
#         self._kwds = kwds
#         self._parse(text)

#     def _parse(self, text):
#         maxclass = text.split()[0]
#         props = OBJECT_DEFAULTS[maxclass]
#         props.update(self._kwds)
#         self.__dict__.update(props)

#     def to_dict(self):
#         """create dict from object with extra kwds included"""
#         d = vars(self).copy()
#         to_del = [k for k in d if k.startswith("_")]
#         for k in to_del:
#             del d[k]
#         d.update(self._kwds)
#         return dict(box=d)