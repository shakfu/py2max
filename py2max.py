"""py2max: a pure python script to generate .maxpat patcher files.

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

    def __init__(self, id: str, maxclass: str,
                 numinlets: int, numoutlets: int, outlettype: list[str],
                 patching_rect: list[float], text: str, varname: str = None, **kwds):
        super().__init__(id, maxclass, numinlets, numoutlets, outlettype,
                         patching_rect, varname, **kwds)
        self.text = text


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
                 varname: str = None, **kwds):
        super().__init__(id, 'flonum', numinlets, numoutlets, outlettype,
                         patching_rect, varname, **kwds)
        self.parameter_enable = 1
        self.parameter_initial = parameter_initial
        self.maximum = maximum
        self.minimum = minimum
        self.parameter_longname = parameter_longname
        self.parameter_shortname = parameter_shortname


class IntParam(NumberBox):
    """Int NumberBox as parameter"""

    def __init__(self, id: str,
                 numinlets: int, numoutlets: int, outlettype: list[str],
                 patching_rect: list[float],
                 parameter_longname: str, parameter_shortname: str,
                 parameter_initial: int = 0, maximum: int = 0, minimum: int = 0,
                 varname: str = None, **kwds):
        super().__init__(id, 'number', numinlets, numoutlets, outlettype,
                         patching_rect, varname, **kwds)
        self.parameter_enable = 1
        self.parameter_initial = parameter_initial
        self.maximum = maximum
        self.minimum = minimum
        self.parameter_longname = parameter_longname
        self.parameter_shortname = parameter_shortname


class Patchline:
    def __init__(self, src: str, src_outlet: int, dst: str, dst_inlet: int, order: int = 0):
        self.source = [src, src_outlet]
        self.destination = [dst, dst_inlet]
        self.order = order

    def to_tuple(self):
        """return a tuple describing the patchline"""
        return (self.source[0], self.source[1], 
                self.destination[0], self.destination[1], 
                self.order)

    def to_dict(self):
        """create dict from object"""
        return dict(patchline=vars(self))


class Patcher:
    """Build Max patchers from the ground up
    
    Top level Patcher can be converted to .maxpat file
    """

    def __init__(self, path=None, parent=None, classnamespace=None, reset_on_render=True):
        self._path = path
        self._parent = parent
        self._ids = []          # ids by order of creation
        self._objects = {}      # dict of objects by id
        self._boxes = []        # store objects
        self._lines = []        # store patchline objects
        self._id_counter = 0
        self._x_layout_counter = 0
        self._y_layout_counter = 0
        self._link_counter = 0
        self._last_link = None
        self._reset_on_render = reset_on_render

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

    def to_dict(self):
        """create dict from object with extra kwds included"""
        d = vars(self).copy()
        to_del = [k for k in d if k.startswith('_')]
        for k in to_del:
            del d[k]
        return dict(patcher=d)

    def to_json(self):
        self.render()
        return json.dumps(self.to_dict(), indent=4)

    @property
    def width(self):
        return self.rect[2]

    @property
    def height(self):
        return self.rect[3]

    def render(self, reset=False):
        if reset or self._reset_on_render:
            self.boxes = []
            self.lines = []
        for box in self._boxes:
            box.render()
            self.boxes.append(box.to_dict())
        self.lines = [line.to_dict() for line in self._lines]

    def saveas(self, path):
        self.render()
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)

    def save(self):
        self.saveas(self._path)

    def get_id(self):
        self._id_counter += 1
        return f'obj-{self._id_counter}'
 
    def get_pos(self):
        """rough auto-layout of objects"""
        pad = LAYOUT_DEFAULT_PAD  # 32.0
        x_pad = pad
        y_pad = pad
        x_shift =   3 * pad * self._x_layout_counter
        y_shift = 1.5 * pad * self._y_layout_counter
        x = x_pad + x_shift
        w = LAYOUT_DEFAULT_BOX_WIDTH  # 66.0
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

    def add_box(self, box):
        """registers the box and adds it to the patcher"""
        self._ids.append(box.id)
        self._objects[box.id] = box
        self._boxes.append(box)
        return box

    def add_patchline_by_index(self, src_i: int, src_outlet, dst_i, dst_inlet):
        src_id = self._ids[src_i]
        dst_id = self._ids[dst_i]
        self.add_patchline(src_id, src_outlet, dst_id, dst_inlet)

    def add_patchline(self, src_id, src_outlet, dst_id, dst_inlet):
        order = self.get_link_order(src_id, dst_id)
        patchline = Patchline(src_id, src_outlet, dst_id, dst_inlet, order)
        self._lines.append(patchline)
        return patchline

    def add_line(self, src_obj, dst_obj):
        """convenience line adding taking objects with default outlet to inlet"""
        return self.add_patchline(src_obj.id, 0, dst_obj.id, 0)

    def add_textbox(self, text: str, maxclass: str = None, numinlets: int = None, numoutlets: int = None, 
                    outlettype: list[str] = None, patching_rect: list[float] = None,
                    id: str = None, varname: str = None, **kwds):

        return self.add_box(
            TextBox(
                id=id or self.get_id(),
                text=text,
                maxclass=maxclass or 'newobj',
                numinlets=numinlets or 1,
                numoutlets=numoutlets or 0,
                outlettype=outlettype or [""],
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
                       id: str = None, varname: str = None, **kwds):
        
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
            )
        )

    def add_intbox(self, numinlets: int = None, numoutlets: int = None,
                   outlettype: list[str] = None, patching_rect: list[float] = None,
                   id: str = None, varname: str = None, **kwds):
        
        return self._add_numberbox(
            maxclass='number',
            numinlets=numinlets,
            numoutlets=numoutlets,
            outlettype=outlettype,
            patching_rect=patching_rect,
            varname=varname,
            **kwds
        )

    def add_floatbox(self, numinlets: int = None, numoutlets: int = None,
                     outlettype: list[str] = None, patching_rect: list[float] = None,
                     varname: str = None, **kwds):

        return self._add_numberbox(
            maxclass='flonum',
            numinlets=numinlets,
            numoutlets=numoutlets,
            outlettype=outlettype,
            patching_rect=patching_rect,
            varname=varname,
            **kwds
        )
    
    def add_floatparam(self, parameter_longname: str, parameter_shortname: str = None,
                       numinlets: int = None, numoutlets: int = None, outlettype: list[str] = None,
                       parameter_initial: float = None, maximum: float = None, minimum: float = None,
                       id: str = None, patching_rect: list[float] = None, varname: str = None, **kwds):
        
        return self.add_box(
            FloatParam(
                id=id or self.get_id(),
                numinlets=numinlets or 1,
                numoutlets=numoutlets or 2,
                outlettype=outlettype or ["", "bang"],
                parameter_longname=parameter_longname,
                parameter_shortname=parameter_shortname or "",
                parameter_initial=parameter_initial or 0.5,
                maximum=maximum or 1.0,
                minimum=minimum or 0.0,
                patching_rect=patching_rect or self.get_pos(),
                varname=varname or parameter_longname,
                **kwds
            )
        )

    def add_intparam(self,  parameter_longname: str, parameter_shortname: str = None,
                     numinlets: int = None, numoutlets: int = None, outlettype: list[str] = None,
                     parameter_initial: int = None, maximum: int = None, minimum: int = None,
                     patching_rect: list[float] = None, varname: str = None, **kwds):

        return self.add_box(
            IntParam(
                id=self.get_id(),
                numinlets=numinlets or 1,
                numoutlets=numoutlets or 2,
                outlettype=outlettype or ["", "bang"],
                parameter_longname=parameter_longname,
                parameter_shortname=parameter_shortname or "",
                parameter_initial=parameter_initial or 5,
                maximum=maximum or 10,
                minimum=minimum or 0,
                patching_rect=patching_rect or self.get_pos(),
                varname=varname or parameter_longname,
                **kwds
            )
        )


class SubPatcher(TextBox):
    """Subpatcher textbox subclass"""

    def __init__(self, id: str, maxclass: str,
                 numinlets: int, numoutlets: int, outlettype: list[str],
                 patching_rect: list[float], text: str, patcher: Patcher = None,
                 varname: str = None, **kwds):
        super().__init__(id, maxclass, numinlets, numoutlets, outlettype,
                         patching_rect, text, varname, **kwds)
        self._patcher = patcher

    def render(self):
        self._patcher.render()
        self.patcher = self._patcher.to_dict()
    
    @property
    def subpatcher(self):
        return self._patcher


def test_colors():
    p = Patcher('out.maxpat')
    for i in range(54):
        m = i/54.
        p.add_textbox('cycle~ 400', bgcolor=[1.0-m, 0.32, 0.0+m, 0.5])
    p.save()

def test_basic():
    p = Patcher('out.maxpat')
    osc1 = p.add_textbox('cycle~ 440')
    gain = p.add_textbox('gain~')
    dac = p.add_textbox('ezdac~')
    p.add_line(osc1, gain)
    p.add_line(gain, dac)
    p.save()

def test_subpatch():
    p = Patcher('out.maxpat')
    sbox = p.add_subpatcher('p mysub')
    sp = sbox.subpatcher
    i = sp.add_textbox('inlet')
    g = sp.add_textbox('gain~')
    o = sp.add_textbox('outlet')
    osc = p.add_textbox('cycle~ 440')
    dac = p.add_textbox('ezdac~')
    sp.add_line(i, g)
    sp.add_line(g, o)
    p.add_line(osc, sbox)
    p.add_line(sbox, dac)
    p.save()


if __name__ == '__main__':
    # test_colors()
    # test_basic()
    test_subpatch()
