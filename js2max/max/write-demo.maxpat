{
    "patcher": {
        "fileversion": 1,
        "appversion": {
            "major": 9,
            "minor": 1,
            "revision": 4,
            "architecture": "x64",
            "modernui": 1
        },
        "classnamespace": "box",
        "rect": [ 85.0, 104.0, 560.0, 520.0 ],
        "boxes": [
            {
                "box": {
                    "fontsize": 14.0,
                    "id": "obj-1",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 24.0, 20.0, 460.0, 22.0 ],
                    "text": "js2max -- writing a patch from code"
                }
            },
            {
                "box": {
                    "id": "obj-2",
                    "linecount": 4,
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 24.0, 44.0, 460.0, 60.0 ],
                    "text": "'save' writes a nine-object instrument straight to disk. No objects are created here, nothing to tidy up afterwards, and the file is exact -- a description already IS a .maxpat, so nothing has to be read back out of Max. Open js2max-demo-out.maxpat, toggle it on, raise the float."
                }
            },
            {
                "box": {
                    "id": "obj-3",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 24.0, 132.0, 200.0, 22.0 ],
                    "text": "save js2max-demo-out.maxpat"
                }
            },
            {
                "box": {
                    "id": "obj-4",
                    "linecount": 4,
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 46.0, 180.0, 438.0, 60.0 ],
                    "text": "The other direction, for capturing a patcher someone edited by hand: 'synth' builds the same instrument into THIS patch, and 'write ... built' serializes those live objects back out. Use it when the objects are the source of truth; otherwise prefer 'save', which cannot lose anything."
                }
            },
            {
                "box": {
                    "id": "obj-5",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 24.0, 268.0, 50.0, 22.0 ],
                    "text": "synth"
                }
            },
            {
                "box": {
                    "id": "obj-6",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 84.0, 268.0, 220.0, 22.0 ],
                    "text": "write js2max-live-out.maxpat built"
                }
            },
            {
                "box": {
                    "id": "obj-7",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 314.0, 268.0, 48.0, 22.0 ],
                    "text": "clear"
                }
            },
            {
                "box": {
                    "filename": "js2max.v8.js",
                    "id": "obj-8",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 24.0, 312.0, 200.0, 22.0 ],
                    "saved_object_attributes": {
                        "parameter_enable": 0
                    },
                    "text": "v8 js2max.v8.js",
                    "textfile": {
                        "filename": "js2max.v8.js",
                        "flags": 0,
                        "embed": 0,
                        "autowatch": 0
                    }
                }
            },
            {
                "box": {
                    "id": "obj-9",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 24.0, 352.0, 90.0, 22.0 ],
                    "text": "print js2max"
                }
            }
        ],
        "lines": [
            {
                "patchline": {
                    "destination": [ "obj-8", 0 ],
                    "source": [ "obj-3", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-8", 0 ],
                    "source": [ "obj-5", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-8", 0 ],
                    "source": [ "obj-6", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-8", 0 ],
                    "source": [ "obj-7", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-9", 0 ],
                    "source": [ "obj-8", 0 ]
                }
            }
        ],
        "autosave": 0
    }
}