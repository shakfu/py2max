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

from .defaults import OBJECT_DEFAULTS

LAYOUT_DEFAULT_PAD = 32.0
LAYOUT_DEFAULT_BOX_WIDTH = 66.0
LAYOUT_DEFAULT_BOX_HEIGHT = 22.0


class Box:
    """Generic Max Box object"""

    def __init__(self, id: str, maxclass: str,
                 numinlets: int, numoutlets: int, outlettype: list[str],
                 patching_rect: list[float], varname: str = None, **kwds):
        self.id = id
        self.maxclass = maxclass
        self.numinlets = numinlets
        self.numoutlets = numoutlets
        self.outlettype = outlettype
        self.patching_rect = patching_rect
        self.varname = varname
        self._kwds = kwds

    @property
    def label(self):
        if hasattr(self, 'text'):
            return self.text
        elif hasattr(self, 'parameter_longname'):
            return getattr(self, 'parameter_longname')
        elif hasattr(self, 'maxclass'):
            return self.maxclass
        else:
            return self.id


    def render(self):
        """convert python subobjects to dicts"""

    def to_dict(self):
        """create dict from object with extra kwds included"""
        d = vars(self).copy()
        to_del = [k for k in d if k.startswith('_')]
        for k in to_del:
            del d[k]
        d.update(self._kwds)
        return dict(box=d)


class TextBox(Box):
    """Box with text"""

    def __init__(self, id: str, maxclass: str, text: str,
                 numinlets: int, numoutlets: int, outlettype: list[str],
                 patching_rect: list[float], varname: str = None, **kwds):
        super().__init__(id, maxclass, numinlets, numoutlets, outlettype,
                         patching_rect, varname, **kwds)
        self.text = text
        self._kwds = kwds
        self._parse(text)

    def _parse(self, text):
        """Extracts maxclass from text and updates fields from defaults.
        """
        maxclass = text.split()[0]
        try:
            props = OBJECT_DEFAULTS[maxclass]
            x1, y1, _, _ = self.__dict__['patching_rect']
            _, _, w2, h2 = props['patching_rect']
            props['patching_rect'] = [x1, y1, w2, h2]
            props.update(self._kwds)
            self.__dict__.update(props)
        except:
            # print(f"warning: no default for {maxclass}")
            pass


class CommentBox(TextBox):
    """Comment object"""

    def __init__(self, id: str,  maxclass: str, text: str,
                 numinlets: int, numoutlets: int, outlettype: list[str],
                 patching_rect: list[float], varname: str = None, **kwds):
        super().__init__(id, maxclass, text, numinlets, numoutlets, outlettype,
                         patching_rect, varname, **kwds)


class NumberBox(Box):       
    """Box with numbers"""

    def __init__(self, id: str,  maxclass: str,
                 numinlets: int, numoutlets: int, outlettype: list[str],
                 patching_rect: list[float], varname: str = None, **kwds):
        super().__init__(id, maxclass, numinlets, numoutlets, outlettype,
                         patching_rect, varname, **kwds)
        self.parameter_enable = 0


class FloatParam(NumberBox):
    """Float NumberBox as parameter"""

    def __init__(self, id: str,
                 numinlets: int, numoutlets: int, outlettype: list[str],
                 patching_rect: list[float], 
                 parameter_longname: str, parameter_shortname: str,
                 parameter_initial: float = 0, maximum: float = 0, minimum: float = 0,
                 varname: str = None, hint: str = None, **kwds):
        super().__init__(id, 'flonum', numinlets, numoutlets, outlettype,
                         patching_rect, varname, **kwds)
        self.parameter_enable = 1
        self.saved_attribute_attributes = dict(
            valueof=dict(
                parameter_initial=[parameter_initial],
                parameter_initial_enable=1,
                parameter_longname=parameter_longname,
                parameter_mmax=maximum,
                parameter_shortname=parameter_shortname,
                parameter_type=0,
            )
        )
        self.maximum = maximum
        self.minimum = minimum
        self.hint = hint



class IntParam(NumberBox):
    """Int NumberBox as parameter"""

    def __init__(self, id: str,
                 numinlets: int, numoutlets: int, outlettype: list[str],
                 patching_rect: list[float],
                 parameter_longname: str, parameter_shortname: str,
                 parameter_initial: int = 0, maximum: int = 0, minimum: int = 0,
                 varname: str = None, hint: str = None, **kwds):
        super().__init__(id, 'number', numinlets, numoutlets, outlettype,
                         patching_rect, varname, **kwds)
        self.parameter_enable = 1
        self.saved_attribute_attributes = dict(
            valueof=dict(
                parameter_initial=[parameter_initial],
                parameter_initial_enable=1,
                parameter_longname=parameter_longname,
                parameter_mmax=maximum,
                parameter_shortname=parameter_shortname,
                parameter_type=0,
            )
        )
        self.maximum = maximum
        self.minimum = minimum
        self.hint = hint



class Patchline:
    """A class for Max patchlines."""

    def __init__(self, src: str, src_outlet: int, dst: str, dst_inlet: int, order: int = 0):
        self.src = src
        self.source = [src, src_outlet]
        self.dst = dst
        self.destination = [dst, dst_inlet]
        self.order = order

    def to_tuple(self):
        """Return a tuple describing the patchline."""
        return (self.source[0], self.source[1], 
                self.destination[0], self.destination[1], 
                self.order)

    def to_dict(self):
        """create dict from object."""
        return dict(patchline=vars(self))


class PositionManager:
    """Utiltiy class to help with object position calculations."""

    def __init__(self, parent):
        self.parent = parent
        self.pad = LAYOUT_DEFAULT_PAD
        self.box_width = LAYOUT_DEFAULT_BOX_WIDTH
        self.box_height = LAYOUT_DEFAULT_BOX_HEIGHT
    
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

    def __init__(self, path=None, parent=None, classnamespace=None, 
                 reset_on_render=True, auto_hints=False):
        self._path = path
        self._parent = parent
        self._node_ids = []     # ids by order of creation
        self._objects = {}      # dict of objects by id
        self._boxes = []        # store child objects (boxes, etc.)
        self._lines = []        # store patchline objects
        self._edge_ids = []     # store edge (src_id, dst_id) by order of creation
        self._id_counter = 0
        self._x_layout_counter = 0
        self._y_layout_counter = 0
        self._link_counter = 0
        self._last_link = None
        self._reset_on_render = reset_on_render
        self._pos_mgr = PositionManager(self)
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
        self.rect = [85.0, 104.0, 400.0, 400.0]
        # self.rect = [85.0, 104.0, 640.0, 480.0]
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

    def to_dict(self):
        """create dict from object with extra kwds included"""
        d = vars(self).copy()
        to_del = [k for k in d if k.startswith('_')]
        for k in to_del:
            del d[k]
        return dict(patcher=d)

    def to_json(self):
        """cascade convert to json"""
        self.render()
        return json.dumps(self.to_dict(), indent=4)

    @property
    def width(self):
        """width of patcher window."""
        return self.rect[2]

    @property
    def height(self):
        """height of patcher windows."""
        return self.rect[3]

    def render(self, reset=False):
        """cascade convert py2max objects to dicts."""
        if reset or self._reset_on_render:
            self.boxes = []
            self.lines = []
        for box in self._boxes:
            box.render()
            self.boxes.append(box.to_dict())
        self.lines = [line.to_dict() for line in self._lines]

    def reposition(self):
        import networkx as nx

        G = nx.DiGraph()

        # add nodes
        for box in self._boxes:
            if box.maxclass == 'comment':
                continue
            G.add_node(box.id)

        # edd edges
        for line in self._lines:
            G.add_edge(line.src, line.dst)

        # layout
        scale = self.rect[2]
        # pos = nx.circular_layout(G, scale=scale)
        # pos = nx.kamada_kawai_layout(G, scale=scale)
        # pos = nx.planar_layout(G, scale=scale)
        # pos = nx.shell_layout(G, scale=scale)
        # pos = nx.spectral_layout(G, scale=scale)
        # pos = nx.spiral_layout(G. scale=scale)
        pos = nx.spring_layout(G, scale=scale)
 
        repos = []
        for p in pos.items():
            _, coord = p
            x, y = coord
            repos.append((x+scale, y+scale))

        _boxes = []
        for box, xy in zip(self._boxes, repos):
            x, y, h, w = box.patching_rect
            newx, newy = xy
            box.patching_rect = newx, newy, h, w
            _boxes.append(box)
        self.boxes = _boxes

    def graph(self):
        import networkx as nx
        import matplotlib.pyplot as plt

        G = nx.DiGraph()

        # make labels
        # labels = {b.id: b.label for b in self._boxes}
        
        # add nodes
        for box in self._boxes:
            if box.maxclass == 'comment':
                continue
            G.add_node(box.id)
        
        # edd edges
        for line in self._lines:
            G.add_edge(line.src, line.dst)

        # layout
        pos = nx.spring_layout(G)
        # pos = nx.circular_layout(G)
        # pos = nx.kamada_kawai_layout(G)
        # pos = nx.planar_layout(G)
        # pos = nx.shell_layout(G)
        # pos = nx.spectral_layout(G)
        # pos = nx.spiral_layout(G)
        # pos = nx.kamada_kawai_layout(G)

        # G = nx.convert_node_labels_to_integers(G)
        # G = nx.relabel_nodes(G, labels)
        # nx.draw(G, with_labels=True)
        nx.draw(G, pos=pos, with_labels=True)
        # nx.draw(G, pos=pos, with_labels=False)
        plt.show()



    def saveas(self, path):
        """save as .maxpat json file"""
        parent_dir = os.path.dirname(path)
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
        """helper func providing very rough auto-layout of objects"""
        pad = LAYOUT_DEFAULT_PAD  # 32.0
        x_pad = pad
        y_pad = pad
        x_shift =   3 * pad * self._x_layout_counter
        y_shift = 1.5 * pad * self._y_layout_counter
        x = x_pad + x_shift
        w = LAYOUT_DEFAULT_BOX_WIDTH   # 66.0
        h = LAYOUT_DEFAULT_BOX_HEIGHT  # 22.0
        self._x_layout_counter += 1
        if x + w + 2 * x_pad > self.width:
            self._x_layout_counter = 0
            self._y_layout_counter += 1
        y = y_pad + y_shift
        return [x, y, w, h]

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
            patching_rect = getattr(self._pos_mgr, comment_pos)(rect)
        else:
            patching_rect = self._pos_mgr.above(rect)
        self.add_comment(comment, patching_rect)

    def add_patchline_by_index(self, src_i, src_outlet, dst_i, dst_inlet):
        """Patchline creation between two objects using stored indexes"""

        src_id = self._node_ids[src_i]
        dst_id = self._node_ids[dst_i]
        self.add_patchline(src_id, src_outlet, dst_id, dst_inlet)

    def add_patchline(self, src_id, src_outlet, dst_id, dst_inlet):
        """primary patchline creation method"""

        order = self.get_link_order(src_id, dst_id)
        patchline = Patchline(src_id, src_outlet, dst_id, dst_inlet, order)
        self._lines.append(patchline)
        self._edge_ids.append((src_id, dst_id))
        return patchline

    def add_line(self, src_obj, dst_obj, outlet=0, inlet=0):
        """convenience line adding taking objects with default outlet to inlet"""

        return self.add_patchline(src_obj.id, outlet, dst_obj.id, inlet)

    def add_textbox(self, text: str, maxclass: str = None, 
                    numinlets: int = None, numoutlets: int = None, outlettype: list[str] = None, 
                    patching_rect: list[float] = None, id: str = None, varname: str = None, 
                    comment: str = None, comment_pos: str = None, **kwds):
        """Add a generic textbox object to the patcher.

        Looks up default attributes from a dictionary.
        """

        return self.add_box(
            TextBox(
                id=id or self.get_id(),
                text=text,
                maxclass=maxclass or 'newobj',
                numinlets=numinlets or 1,
                numoutlets=numoutlets or 0,
                outlettype=outlettype or [""],
                patching_rect=patching_rect or self.get_pos(),
                varname=varname or '',
                **kwds
            ),
            comment,
            comment_pos
        )

    def add_comment(self, text: str, patching_rect: list[float] = None,
                    id: str = None, varname: str = None, **kwds):

        return self.add_box(
            CommentBox(
                id=id or self.get_id(),
                text=text,
                maxclass="comment",
                numinlets=1,
                numoutlets=0,
                outlettype=[""],
                patching_rect=patching_rect or self.get_pos(),
                varname=varname,
                **kwds
            )
        )

    def add_subpatcher(self, text: str, maxclass: str = None,
                       numinlets: int = None, numoutlets: int = None,
                       outlettype: list[str] = None, patching_rect: list[float] = None,
                       id: str = None, varname: str = None, **kwds):

        return self.add_box(
            SubPatcher(
                id=id or self.get_id(),
                text=text,
                maxclass=maxclass or 'newobj',
                numinlets=numinlets or 1,
                numoutlets=numoutlets or 0,
                outlettype=outlettype or [""],
                patching_rect=patching_rect or self.get_pos(),
                varname=varname,
                patcher=Patcher(parent=self),
                **kwds
            )
        )

    def _add_numberbox(self, maxclass: str, numinlets: int = None, numoutlets: int = None,
                       outlettype: list[str] = None, patching_rect: list[float] = None,
                       id: str = None, varname: str = None, 
                       comment: str = None, comment_pos: str = None, **kwds):
        
        return self.add_box(
            NumberBox(
                id=id or self.get_id(),
                maxclass=maxclass,
                numinlets=numinlets or 1,
                numoutlets=numoutlets or 2,
                outlettype=outlettype or ["", "bang"],
                patching_rect=patching_rect or self.get_pos(),
                varname=varname,
                **kwds
            ),
            comment,
            comment_pos
        )

    def add_intbox(self, numinlets: int = None, numoutlets: int = None,
                   outlettype: list[str] = None, patching_rect: list[float] = None,
                   id: str = None, varname: str = None, 
                   comment: str = None, comment_pos: str = None, **kwds):
        
        return self._add_numberbox(
            maxclass='number',
            numinlets=numinlets,
            numoutlets=numoutlets,
            outlettype=outlettype,
            patching_rect=patching_rect,
            varname=varname,
            comment=comment,
            comment_pos=comment_pos,
            **kwds
        )

    def add_floatbox(self, numinlets: int = None, numoutlets: int = None,
                     outlettype: list[str] = None, patching_rect: list[float] = None,
                     varname: str = None, comment: str = None, comment_pos: str = None, **kwds):

        return self._add_numberbox(
            maxclass='flonum',
            numinlets=numinlets,
            numoutlets=numoutlets,
            outlettype=outlettype,
            patching_rect=patching_rect,
            varname=varname,
            comment=comment,
            comment_pos=comment_pos,
            **kwds
        )
    
    def add_floatparam(self, longname: str, initial: float = None, 
                       minimum: float = None, maximum: float = None, shortname: str = None,                       
                       numinlets: int = None, numoutlets: int = None, outlettype: list[str] = None,
                       id: str = None, rect: list[float] = None, varname: str = None, hint: str = None,
                       comment: str = None, comment_pos: str = None, **kwds):
        
        return self.add_box(
            FloatParam(
                id=id or self.get_id(),
                numinlets=numinlets or 1,
                numoutlets=numoutlets or 2,
                outlettype=outlettype or ["", "bang"],
                parameter_longname=longname,
                parameter_shortname=shortname or "",
                parameter_initial=initial or 0.5,
                maximum=maximum or 1.0,
                minimum=minimum or 0.0,
                patching_rect=rect or self.get_pos(),
                varname=varname or longname,
                hint=hint or (longname if self._auto_hints else ""),
                **kwds
            ),
            comment or longname,  # units can also be added here
            comment_pos
        )

    def add_intparam(self, longname: str, initial: int = None,
                     minimum: int = None, maximum: int = None, shortname: str = None,
                     numinlets: int = None, numoutlets: int = None, outlettype: list[str] = None,
                     id: str = None, rect: list[float] = None, varname: str = None, hint: str = None,
                     comment: str = None, comment_pos: str = None, **kwds):

        return self.add_box(
            IntParam(
                id=id or self.get_id(),
                numinlets=numinlets or 1,
                numoutlets=numoutlets or 2,
                outlettype=outlettype or ["", "bang"],
                parameter_longname=longname,
                parameter_shortname=shortname or "",
                parameter_initial=initial or 5,
                maximum=maximum or 10,
                minimum=minimum or 0,
                patching_rect=rect or self.get_pos(),
                varname=varname or longname,
                hint=hint or (longname if self._auto_hints else ""),
                **kwds
            ),
            comment or longname,
            comment_pos
        )


class SubPatcher(TextBox):
    """Subpatcher textbox subclass"""

    def __init__(self, id: str, maxclass: str,
                 numinlets: int, numoutlets: int, outlettype: list[str],
                 patching_rect: list[float], text: str, patcher: Patcher = None,
                 varname: str = None, **kwds):
        super().__init__(id, maxclass, text, numinlets, numoutlets, outlettype,
                         patching_rect, varname, **kwds)
        self._patcher = patcher

    def render(self):
        self._patcher.render()
        self.patcher = self._patcher.to_dict()
    
    @property
    def subpatcher(self):
        return self._patcher
