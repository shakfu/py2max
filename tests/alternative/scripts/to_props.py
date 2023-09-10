tmp = """\
    @property
    def {name}(self):
        return self.model["{name}"]

    @{name}.setter
    def {name}(self, value: {type}):
        self.model["{name}"] = value
"""

d = {
    "fileversion" : 1,
    "appversion" :      {
        "major" : 8,
        "minor" : 5,
        "revision" : 5,
        "architecture" : "x64",
        "modernui" : 1
    }
    ,
    "classnamespace" : "box",
    "rect" : [ 91.0, 106.0, 640.0, 480.0 ],
    "bglocked" : 0,
    "openinpresentation" : 0,
    "default_fontsize" : 12.0,
    "default_fontface" : 0,
    "default_fontname" : "Arial",
    "gridonopen" : 1,
    "gridsize" : [ 15.0, 15.0 ],
    "gridsnaponopen" : 1,
    "objectsnaponopen" : 1,
    "statusbarvisible" : 2,
    "toolbarvisible" : 1,
    "lefttoolbarpinned" : 0,
    "toptoolbarpinned" : 0,
    "righttoolbarpinned" : 0,
    "bottomtoolbarpinned" : 0,
    "toolbars_unpinned_last_save" : 0,
    "tallnewobj" : 0,
    "boxanimatetime" : 200,
    "enablehscroll" : 1,
    "enablevscroll" : 1,
    "devicewidth" : 0.0,
    "description" : "",
    "digest" : "",
    "tags" : "",
    "style" : "",
    "subpatcher_template" : "",
    "assistshowspatchername" : 0,
    "dependency_cache" : [  ],
    "autosave" : 0
}

for key, value in d.items():
    if isinstance(value, str):
        out = tmp.format(name=key, type="str")
    elif isinstance(value, int):
        out = tmp.format(name=key, type="int")
    elif isinstance(value, float):
        out = tmp.format(name=key, type="float")
    elif isinstance(value, list):
        if len(value) == 4:
            out = tmp.format(name=key, type="Rect")
        else:
            out = tmp.format(name=key, type="list")
    elif isinstance(value, dict):
        out = tmp.format(name=key, type="dict")
    print(out)



