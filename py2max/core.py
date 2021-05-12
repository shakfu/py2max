"""py2max: a pure python library to generate .maxpat patcher files.

basic usage:

    >>> p = Patcher('out.maxpat')
    >>> osc1 = p.add_textbox('cycle~ 440')
    >>> gain = p.add_textbox('gain~')
    >>> dac = p.add_textbox('ezdac~')
    >>> p.add_line(osc1, gain)
    >>> p.add_line(gain, dac)
    >>> p.save()

"""
import json
import os
from typing import Dict, Any, Optional, Type

from .maxclassdb import MAXCLASS_DEFAULTS

LAYOUT_DEFAULT_PAD = 32.0
LAYOUT_DEFAULT_BOX_WIDTH = 66.0
LAYOUT_DEFAULT_BOX_HEIGHT = 22.0


class LayoutManager:
    """Utility class to help with object position calculations."""

    def __init__(self, parent):
        self.parent = parent
        self.pad = LAYOUT_DEFAULT_PAD
        self.box_width = LAYOUT_DEFAULT_BOX_WIDTH
        self.box_height = LAYOUT_DEFAULT_BOX_HEIGHT

        self.x_layout_counter = 0
        self.y_layout_counter = 0

    def get_pos(self):
        """helper func providing very rough auto-layout of objects"""
        pad = LAYOUT_DEFAULT_PAD  # 32.0
        x_pad = pad
        y_pad = pad
        x_shift = 3 * pad * self.x_layout_counter
        y_shift = 1.5 * pad * self.y_layout_counter
        x = x_pad + x_shift
        w = LAYOUT_DEFAULT_BOX_WIDTH   # 66.0
        h = LAYOUT_DEFAULT_BOX_HEIGHT  # 22.0
        self.x_layout_counter += 1
        if x + w + 2 * x_pad > self.parent.width:
            self.x_layout_counter = 0
            self.y_layout_counter += 1
        y = y_pad + y_shift
        return [x, y, w, h]

    @property
    def patcher_rect(self):
        """return rect coordinates of the parent patcher"""
        return self.parent.rect

    def above(self, rect):
        """Return a position above the object"""
        x, y, w, h = rect
        return [x, y - self.box_height, w, h]

    def below(self, rect):
        """Return a position below the object"""
        x, y, w, h = rect
        return [x, y + (self.box_height + h), w, h]

    def left(self, rect):
        """Return a position left of the object"""
        x, y, w, h = rect
        return [x - self.box_width, y, w, h]

    def right(self, rect):
        """Return a position right of the object"""
        x, y, w, h = rect
        return [x + (self.box_width + w), y, w, h]


class Patcher:
    """Core Patcher class describing a Max patchers from the ground up.

    Any Patcher can be converted to a .maxpat file.
    """

    def __init__(self, path: str = None, parent: 'Patcher' = None, 
                 classnamespace: str = None, reset_on_render: bool = True, 
                 layout_mgr_class: Type[LayoutManager] = None, auto_hints: bool = False):
        self._path = path
        self._parent = parent
        self._node_ids = []     # ids by order of creation
        self._objects = {}      # dict of objects by id
        self._boxes = []        # store child objects (boxes, etc.)
        self._lines = []        # store patchline objects
        self._edge_ids = []     # store edge-ids by order of creation 
        self._id_counter = 0
        self._link_counter = 0
        self._last_link = None
        self._reset_on_render = reset_on_render
        self._layout_mgr = layout_mgr_class(self) if layout_mgr_class else LayoutManager(self)
        self._auto_hints = auto_hints

        # begin max attributes
        self.fileversion = 1
        self.appversion = {
            'major': 8,
            'minor': 1,
            'revision': 11,
            'architecture': "x64",
            'modernui': 1
        }
        self.classnamespace = classnamespace or "box"
        self.rect = [85.0, 104.0, 640.0, 480.0]
        self.bglocked = 0
        self.openinpresentation = 0
        self.default_fontsize = 12.0
        self.default_fontface = 0
        self.default_fontname = "Arial"
        self.gridonopen = 1
        self.gridsize = [15.0, 15.0]
        self.gridsnaponopen = 1
        self.objectsnaponopen = 1
        self.statusbarvisible = 2
        self.toolbarvisible = 1
        self.lefttoolbarpinned = 0
        self.toptoolbarpinned = 0
        self.righttoolbarpinned = 0
        self.bottomtoolbarpinned = 0
        self.toolbars_unpinned_last_save = 0
        self.tallnewobj = 0
        self.boxanimatetime = 200
        self.enablehscroll = 1
        self.enablevscroll = 1
        self.devicewidth = 0.0
        self.description = ""
        self.digest = ""
        self.tags = ""
        self.style = ""
        self.subpatcher_template = ""
        self.assistshowspatchername = 0
        self.boxes = []
        self.lines = []
        self.parameters = {}
        self.dependency_cache = []
        self.autosave = 0

    def __repr__(self):
        return f"{self.__class__.__name__}(path='{self._path}')"

    def __iter__(self):
        yield self
        for box in self._boxes:
            yield from iter(box)

    @property
    def width(self):
        """width of patcher window."""
        return self.rect[2]

    @property
    def height(self):
        """height of patcher windows."""
        return self.rect[3]

    # @staticmethod
    # def box_from_dict(d):
    #     if 'maxclass' in d:
    #         try:
    #             box_class = MAXCLASS_DEFAULTS[d['maxclass']]
    #         except KeyError:
    #             box_class = Box
    #         return box_class.from_dict(d)

    @classmethod
    def from_dict(cls, patcher_dict):
        """create a patcher instance from a dict"""

        patcher = cls()
        patcher.__dict__.update(patcher_dict)

        for box_dict in patcher.boxes:
            box = box_dict['box']
            b = Box.from_dict(box)
            # b = patcher.box_from_dict(box)
            patcher._boxes.append(b)

        for line_dict in patcher.lines:
            line = line_dict['patchline']
            pl = Patchline.from_dict(line)
            patcher._lines.append(pl)

        return patcher

    @classmethod
    def from_file(cls, path, save_to: str = None):
        """create a patcher instance from a .maxpat json file"""

        with open(path) as f:
            maxpat = json.load(f)
        return Patcher.from_dict(maxpat['patcher'])        

    def to_dict(self):
        """create dict from object with extra kwds included"""
        d = vars(self).copy()
        to_del = [k for k in d if k.startswith('_')]
        for k in to_del:
            del d[k]
        if not self._parent:
            return dict(patcher=d)
        else:
            return d

    def to_json(self):
        """cascade convert to json"""
        self.render()
        return json.dumps(self.to_dict(), indent=4)

    def render(self, reset=False):
        """cascade convert py2max objects to dicts."""
        if reset or self._reset_on_render:
            self.boxes = []
            self.lines = []
        for box in self._boxes:
            box.render()
            self.boxes.append(box.to_dict())
        self.lines = [line.to_dict() for line in self._lines]

    def saveas(self, path):
        """save as .maxpat json file"""
        parent_dir = os.path.dirname(path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        self.render()
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)

    def save(self):
        """save as json .maxpat file"""
        self.saveas(self._path)

    def get_id(self):
        """helper func to increment object ids"""
        self._id_counter += 1
        return f'obj-{self._id_counter}'

    def get_pos(self):
        return self._layout_mgr.get_pos()

    def get_link_order(self, src_id, dst_id):
        """get order of lines between the same pair of objects"""

        if ((src_id, dst_id) == self._last_link):
            self._link_counter += 1
        else:
            self._link_counter = 0
            self._last_link = (src_id, dst_id)
        return self._link_counter

    def add_box(self, box, comment=None, comment_pos=None):
        """registers the box and adds it to the patcher"""

        self._node_ids.append(box.id)
        self._objects[box.id] = box
        self._boxes.append(box)
        if comment:
            rect = box.patching_rect.copy()
            self.add_associated_comment(rect, comment, comment_pos)
        return box

    def add_associated_comment(self, rect, comment, comment_pos=None):
        """add a comment associated with the object"""

        if comment_pos:
            assert comment_pos in ['above', 'below', 'right', 'left']
            patching_rect = getattr(self._layout_mgr, comment_pos)(rect)
        else:
            patching_rect = self._layout_mgr.above(rect)
        self.add_comment(comment, patching_rect)

    def add_patchline_by_index(self, src_i, src_outlet, dst_i, dst_inlet):
        """Patchline creation between two objects using stored indexes"""

        src_id = self._node_ids[src_i]
        dst_id = self._node_ids[dst_i]
        self.add_patchline(src_id, src_outlet, dst_id, dst_inlet)

    def add_patchline(self, src_id, src_outlet, dst_id, dst_inlet):
        """primary patchline creation method"""

        order = self.get_link_order(src_id, dst_id)
        src, dst = [src_id, src_outlet], [dst_id, dst_inlet]
        patchline = Patchline(source=src, destination=dst, order=order)
        self._lines.append(patchline)
        self._edge_ids.append((src_id, dst_id))
        return patchline

    def add_line(self, src_obj, dst_obj, inlet=0, outlet=0):
        """convenience line adding taking objects with default outlet to inlet"""

        return self.add_patchline(src_obj.id, outlet, dst_obj.id, inlet)
    
    # alias for add_line
    link = add_line

    def add_textbox(self, text: str, maxclass: str = None,
                    numinlets: int = None, numoutlets: int = None, outlettype: list[str] = None,
                    patching_rect: list[float] = None, id: str = None,
                    comment: str = None, comment_pos: str = None, **kwds):
        """Add a generic textbox object to the patcher.

        Looks up default attributes from a dictionary.
        """

        return self.add_box(
            Box(
                id=id or self.get_id(),
                text=text,
                maxclass=maxclass or 'newobj',
                numinlets=numinlets or 1,
                numoutlets=numoutlets or 0,
                outlettype=outlettype or [""],
                patching_rect=patching_rect or self.get_pos(),
                **kwds
            ),
            comment,
            comment_pos
        )
    
    # alias for add_textbox
    add = add_textbox

    def add_coll(self, name: str = None, dictionary: dict = None, embed: int = 1,
                 patching_rect: list[float] = None, text: str = None, id: str = None,
                 comment: str = None, comment_pos: str = None, **kwds):
        """Add a coll object with option to pre-populate from a py dictionary."""
        extra = {
            'saved_object_attributes': {
                'embed': embed,
                'precision': 6
            }
        }
        if dictionary:
            extra['coll_data'] = {
                'count': len(dictionary.keys()),
                'data': [{'key': k, 'value': v} for k, v in dictionary.items()]
            }
        kwds.update(extra)
        return self.add_box(
            Box(
                id=id or self.get_id(),
                text=text or f"coll {name} @embed {embed}" if name else "coll @embed {embed}",
                maxclass='newobj',
                numinlets=1,
                numoutlets=4,
                outlettype=["", "", "", ""],
                patching_rect=patching_rect or self.get_pos(),
                **kwds
            ),
            comment,
            comment_pos
        )

    def add_dict(self, name: str = None, dictionary: dict = None, embed: int = 1,
                 patching_rect: list[float] = None, text: str = None, id: str = None,
                 comment: str = None, comment_pos: str = None, **kwds):
        """Add a dict object with option to pre-populate from a py dictionary."""
        extra = {
            'saved_object_attributes': {
                'embed': embed,
          		'parameter_enable': kwds.get('parameter_enable', 0),
          		'parameter_mappable': kwds.get('parameter_mappable', 0)
            },
            'data': dictionary or {}
        }
        kwds.update(extra)
        return self.add_box(
            Box(
                id=id or self.get_id(),
                text=text or f"dict {name} @embed {embed}" if name else "dict @embed {embed}",
                maxclass='newobj',
                numinlets=2,
                numoutlets=4,
                outlettype=["dictionary", "", "", ""],
                patching_rect=patching_rect or self.get_pos(),
                **kwds
            ),
            comment,
            comment_pos
        )

    def add_table(self, name: str = None, array: list[int] = None, embed: int = 1,
                 patching_rect: list[float] = None, text: str = None, id: str = None,
                 comment: str = None, comment_pos: str = None, **kwds):
        """Add a table object with option to pre-populate from a py list."""
        
        extra = {
            'embed': embed,
            'saved_object_attributes': {
                'name': name,
          		'parameter_enable': kwds.get('parameter_enable', 0),
          		'parameter_mappable': kwds.get('parameter_mappable', 0),
                'range': kwds.get('range', 128),
                'showeditor': 0,
                'size': len(array) if array else 128,
            },
            # "showeditor": 0,
            # 'size': kwds.get('size', 128),
            'table_data': array or [],
            'editor_rect': [100.0, 100.0, 300.0, 300.0],
        }
        kwds.update(extra)
        return self.add_box(
            Box(
                id=id or self.get_id(),
                text=text or f"table {name} @embed {embed}" if name else "table @embed {embed}",
                maxclass='newobj',
                numinlets=2,
                numoutlets=2,
                outlettype=["int", "bang"],
                patching_rect=patching_rect or self.get_pos(),
                **kwds
            ),
            comment,
            comment_pos
        )

    def add_itable(self, name: str = None, array: list[int] = None,
                  patching_rect: list[float] = None, text: str = None, id: str = None,
                  comment: str = None, comment_pos: str = None, **kwds):
        """Add a itable object with option to pre-populate from a py list."""

        extra = {
            'range': kwds.get('range', 128),
            'size': len(array) if array else 128,
            'table_data': array or [],
        }
        kwds.update(extra)
        return self.add_box(
            Box(
                id=id or self.get_id(),
                text=text or f"itable {name}",
                maxclass='itable',
                numinlets=2,
                numoutlets=2,
                outlettype=["int", "bang"],
                patching_rect=patching_rect or self.get_pos(),
                **kwds
            ),
            comment,
            comment_pos
        )

    def add_comment(self, text: str, patching_rect: list[float] = None,
                    id: str = None, **kwds):
        """Add a basic comment object."""
        return self.add_box(
            Box(
                id=id or self.get_id(),
                text=text,
                maxclass='comment',
                patching_rect=patching_rect or self.get_pos(),
                **kwds
            )
        )

    def add_subpatcher(self, text: str, maxclass: str = None,
                       numinlets: int = None, numoutlets: int = None,
                       outlettype: list[str] = None, patching_rect: list[float] = None,
                       id: str = None, patcher: 'Patcher' = None, **kwds):
        """Add a subpatcher object."""

        return self.add_box(
            Box(
                id=id or self.get_id(),
                text=text,
                maxclass=maxclass or 'newobj',
                numinlets=numinlets or 1,
                numoutlets=numoutlets or 0,
                outlettype=outlettype or [""],
                patching_rect=patching_rect or self.get_pos(),
                patcher=patcher or Patcher(parent=self),
                **kwds
            )
        )

    def add_gen(self, text: str = 'gen~',  **kwds):
        """Add a gen~ object."""

        return self.add_subpatcher(text,
            patcher=Patcher(parent=self, classnamespace='gen.dsp'), **kwds)


    def add_intbox(self, numinlets: int = None, numoutlets: int = None,
                   outlettype: list[str] = None, patching_rect: list[float] = None,
                   id: str = None,
                   comment: str = None, comment_pos: str = None, **kwds):
        """Add an int box object."""

        return self.add_box(
            Box(
                id=id or self.get_id(),
                maxclass='number',
                numinlets=numinlets or 1,
                numoutlets=numoutlets or 2,
                outlettype=outlettype or ["", "bang"],
                patching_rect=patching_rect or self.get_pos(),
                **kwds
            ),
            comment,
            comment_pos
        )


    def add_floatbox(self, numinlets: int = None, numoutlets: int = None,
                     outlettype: list[str] = None, patching_rect: list[float] = None,
                     id: str = None,
                     comment: str = None, comment_pos: str = None, **kwds):
        """Add an float box object."""

        return self.self.add_box(
            Box(
                id=id or self.get_id(),
                maxclass='flonum',
                numinlets=numinlets or 1,
                numoutlets=numoutlets or 2,
                outlettype=outlettype or ["", "bang"],
                patching_rect=patching_rect or self.get_pos(),
                **kwds
            ),
            comment,
            comment_pos
        )

    def add_floatparam(self, longname: str, initial: float = None,
                       minimum: float = None, maximum: float = None, shortname: str = None,
                       numinlets: int = None, numoutlets: int = None, outlettype: list[str] = None,
                       id: str = None, rect: list[float] = None, hint: str = None,
                       comment: str = None, comment_pos: str = None, **kwds):
        """Add a float parameter object."""

        return self.add_box(
            Box(
                id=id or self.get_id(),
                maxclass='flonum',
                numinlets=numinlets or 1,
                numoutlets=numoutlets or 2,
                outlettype=outlettype or ["", "bang"],
                parameter_enable=1,
                saved_attribute_attributes=dict(
                    valueof=dict(
                        parameter_initial=[initial or 0.5],
                        parameter_initial_enable=1,
                        parameter_longname=longname,
                        parameter_mmax=maximum,
                        parameter_shortname=shortname or "",
                        parameter_type=0,
                    )
                ),
                maximum=maximum or 1.0,
                minimum=minimum or 0.0,
                patching_rect=rect or self.get_pos(),
                hint=hint or (longname if self._auto_hints else ""),
                **kwds
            ),
            comment or longname,  # units can also be added here
            comment_pos
        )

    def add_intparam(self, longname: str, initial: int = None,
                     minimum: int = None, maximum: int = None, shortname: str = None,
                     numinlets: int = None, numoutlets: int = None, outlettype: list[str] = None,
                     id: str = None, rect: list[float] = None, hint: str = None,
                     comment: str = None, comment_pos: str = None, **kwds):
        """Add an int parameter object."""

        return self.add_box(
            Box(
                id=id or self.get_id(),
                maxclass='number',
                numinlets=numinlets or 1,
                numoutlets=numoutlets or 2,
                outlettype=outlettype or ["", "bang"],
                parameter_enable=1,
                saved_attribute_attributes=dict(
                    valueof=dict(
                        parameter_initial=[initial or 5],
                        parameter_initial_enable=1,
                        parameter_longname=longname,
                        parameter_mmax=maximum,
                        parameter_shortname=shortname or "",
                        parameter_type=1,
                    )
                ),
                maximum=maximum or 10,
                minimum=minimum or 0,
                patching_rect=rect or self.get_pos(),
                hint=hint or (longname if self._auto_hints else ""),
                **kwds
            ),
            comment or longname,  # units can also be added here
            comment_pos
        )



class Box:
    """Max Box object"""

    def __init__(self, maxclass: str = None,
                 numinlets: int = None, numoutlets: int = None,
                 id: str = None, patching_rect: list[float] = None, **kwds):

        self.id = id
        self.maxclass = maxclass or 'newobj'
        self.numinlets = numinlets or 0
        self.numoutlets = numoutlets or 1
        self.patching_rect = patching_rect or [0, 0, 62, 22]
        # self.outlettype = outlettype

        self._kwds = kwds
        self._patcher = self._kwds.pop('patcher', None)
        # self._parse(self.text)

    def __iter__(self):
        yield self
        if self._patcher:
            yield from iter(self._patcher)

    def __repr__(self):
        return f"{self.__class__.__name__}(id='{self.id}', maxclass='{self.maxclass}')"

    # def _parse(self, text):
    #     """Extracts maxclass from text and updates fields from defaults.

    #     NOTE: defaults dictionary should not have a `text field or it will
    #     overwrite `text` at object creation making this pretty pointless.
    #     """
    #     maxclass = text.split()[0]
    #     try:
    #         props = MAXCLASS_DEFAULTS[maxclass]
    #         assert 'text' not in props, "'text' field cannot be in default properties"
    #         x1, y1, _, _ = self.__dict__['patching_rect']
    #         _, _, w2, h2 = props['patching_rect']
    #         props['patching_rect'] = [x1, y1, w2, h2]
    #         props.update(self._kwds)
    #         self.__dict__.update(props)
    #     except KeyError:
    #         pass

    def render(self):
        """convert self and children to dictionary."""
        if self._patcher:
            self._patcher.render()

            self.patcher = self._patcher.to_dict()

    def to_dict(self):
        """create dict from object with extra kwds included"""
        d = vars(self).copy()
        to_del = [k for k in d if k.startswith('_')]
        for k in to_del:
            del d[k]
        d.update(self._kwds)
        return dict(box=d)

    @classmethod
    def from_dict(cls, obj_dict):
        box = cls()
        box.__dict__.update(obj_dict)
        if hasattr(box, 'patcher'):
            box._patcher = Patcher.from_dict(getattr(box, 'patcher'))
        return box

    @property
    def oid(self) -> int:
        return int(self.id[4:])

    @property
    def subpatcher(self):
        return self._patcher


class Patchline:
    """A class for Max patchlines."""

    def __init__(self, source: list = None, destination: list = None, **kwds):
        self.source = source or []
        self.destination = destination or []
        self._kwds = kwds

    def __repr__(self):
        return f"Patchline({self.source} -> {self.destination})"

    @property
    def src(self):
        return self.source[0]

    @property
    def dst(self):
        return self.destination[0]

    def to_tuple(self):
        """Return a tuple describing the patchline."""
        return (self.source[0], self.source[1],
                self.destination[0], self.destination[1],
                self._kwds.get('order', 0))

    def to_dict(self):
        """create dict from object with extra kwds included"""
        d = vars(self).copy()
        to_del = [k for k in d if k.startswith('_')]
        for k in to_del:
            del d[k]
        d.update(self._kwds)
        return dict(patchline=d)

    @classmethod
    def from_dict(cls, obj_dict):
        patchline = cls()
        patchline.__dict__.update(obj_dict)
        return patchline