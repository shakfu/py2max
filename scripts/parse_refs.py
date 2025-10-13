#!/usr/bin/env python3

import os
import xml.etree.ElementTree as ET
from pathlib import Path

max_refpages_dir = Path(
    "/Applications/Studio/Max.app/Contents/Resources/C74/docs/refpages"
)

for entry in max_refpages_dir.iterdir():
    if entry.is_file():
        continue
    for f in entry.iterdir():
        if not f.is_file():
            continue
        # print(f)
        tree = ET.parse(f)
        root = tree.getroot()
        print(root.tag, root.attrib["name"])
