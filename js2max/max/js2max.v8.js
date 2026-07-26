(() => {
  var __defProp = Object.defineProperty;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  function __accessProp(key) {
    return this[key];
  }
  var __toCommonJS = (from) => {
    var entry = (__moduleCache ??= new WeakMap).get(from), desc;
    if (entry)
      return entry;
    entry = __defProp({}, "__esModule", { value: true });
    if (from && typeof from === "object" || typeof from === "function") {
      for (var key of __getOwnPropNames(from))
        if (!__hasOwnProp.call(entry, key))
          __defProp(entry, key, {
            get: __accessProp.bind(from, key),
            enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable
          });
    }
    __moduleCache.set(from, entry);
    return entry;
  };
  var __moduleCache;
  var __returnValue = (v) => v;
  function __exportSetter(name, newValue) {
    this[name] = __returnValue.bind(null, newValue);
  }
  var __export = (target, all) => {
    for (var name in all)
      __defProp(target, name, {
        get: all[name],
        enumerable: true,
        configurable: true,
        set: __exportSetter.bind(all, name)
      });
  };

  // src/entry.v8.ts
  var exports_entry_v8 = {};
  __export(exports_entry_v8, {
    write: () => write,
    synth: () => synth,
    save: () => save,
    read: () => read,
    probe: () => probe,
    extract: () => extract,
    demo: () => demo,
    count: () => count,
    clearall: () => clearall,
    clear: () => clear2,
    build: () => build
  });

  // src/scripting.ts
  var SET_CONTENT_CLASSES = new Set(["message", "comment"]);
  function classNameOf(box) {
    if (box.maxclass !== "newobj")
      return box.maxclass;
    const text = box.text ?? "";
    const head = text.trim().split(/\s+/)[0];
    return head === undefined || head === "" ? "newobj" : head;
  }
  function typedArgsOf(box) {
    if (box.maxclass !== "newobj")
      return [];
    const tokens = (box.text ?? "").trim().split(/\s+/).slice(1);
    return tokens.filter((token) => token !== "").map((token) => {
      const asNumber = Number(token);
      return Number.isFinite(asNumber) && token !== "" ? asNumber : token;
    });
  }
  function toMaxobjRect(rect) {
    const [x, y, w, h] = rect;
    return [x, y, x + w, y + h];
  }
  function fromMaxobjRect(rect) {
    const [left, top, right, bottom] = rect;
    return [left, top, right - left, bottom - top];
  }
  function instantiate(target, source, options = {}) {
    const {
      nameById = true,
      applyRects = true,
      buildSubpatchers = true,
      offset = [0, 0]
    } = options;
    const [dx, dy] = offset;
    const objects = new Map;
    const skipped = [];
    let created = 0;
    let connected = 0;
    for (const entry of source.boxes) {
      const box = entry.box;
      const [x, y, w, h] = box.patching_rect;
      const className = classNameOf(box);
      let object = null;
      try {
        object = target.newdefault(x + dx, y + dy, className, ...typedArgsOf(box));
      } catch (err) {
        skipped.push({ id: box.id, reason: `newdefault threw: ${String(err)}` });
        continue;
      }
      if (object === null || object === undefined) {
        skipped.push({ id: box.id, reason: `unknown object class "${className}"` });
        continue;
      }
      objects.set(box.id, object);
      created += 1;
      if (SET_CONTENT_CLASSES.has(box.maxclass) && box.text !== undefined) {
        object.message("set", ...box.text.trim().split(/\s+/));
      }
      if (nameById) {
        object.varname = box.varname ?? box.id;
      } else if (box.varname !== undefined) {
        object.varname = box.varname;
      }
      if (applyRects) {
        object.rect = toMaxobjRect([x + dx, y + dy, w, h]);
      }
      if (buildSubpatchers && box.patcher !== undefined) {
        const nested = object.subpatcher();
        if (nested === null || nested === undefined) {
          skipped.push({
            id: box.id,
            reason: "box carries a nested patcher but exposes no subpatcher()"
          });
        } else {
          const inner = instantiate(nested, box.patcher, options);
          created += inner.created;
          connected += inner.connected;
          skipped.push(...inner.skipped);
        }
      }
    }
    for (const entry of source.lines) {
      const { source: from, destination: to, hidden } = entry.patchline;
      const fromObject = objects.get(from[0]);
      const toObject = objects.get(to[0]);
      if (fromObject === undefined || toObject === undefined) {
        skipped.push({
          id: `${from[0]}->${to[0]}`,
          reason: "patchline references a box that was not created"
        });
        continue;
      }
      try {
        const wire = hidden ? target.hiddenconnect : target.connect;
        wire.call(target, fromObject, from[1], toObject, to[1]);
        connected += 1;
      } catch (err) {
        skipped.push({
          id: `${from[0]}->${to[0]}`,
          reason: `connect threw: ${String(err)}`
        });
      }
    }
    return { objects, created, connected, skipped };
  }
  function clear(target, options = {}) {
    const keep = options.keep ?? [];
    const doomed = [];
    for (let object = target.firstobject;object !== null && object !== undefined; object = object.nextobject) {
      if (!keep.includes(object))
        doomed.push(object);
    }
    for (const object of doomed)
      target.remove(object);
    return doomed.length;
  }
  function remove(target, objects, options = {}) {
    const keep = options.keep ?? [];
    let removed = 0;
    for (const object of [...objects]) {
      if (keep.includes(object))
        continue;
      target.remove(object);
      removed += 1;
    }
    return removed;
  }

  // src/model.ts
  var MAX_VERSION = {
    major: 8,
    minor: 5,
    revision: 5,
    architecture: "x64",
    modernui: 1
  };
  var DEFAULT_BOX = [0, 0, 66, 22];

  class Patcher {
    boxes = [];
    lines = [];
    idCounter = 0;
    spacing;
    settings;
    constructor(options = {}) {
      this.spacing = options.spacing ?? 72;
      this.settings = {
        fileversion: 1,
        appversion: { ...MAX_VERSION },
        classnamespace: options.classnamespace ?? "box",
        rect: options.rect ?? [85, 104, 640, 480],
        ...options.title === undefined ? {} : { title: options.title }
      };
    }
    nextId() {
      this.idCounter += 1;
      return `obj-${this.idCounter}`;
    }
    nextRect() {
      const index = this.boxes.length;
      return [
        48 + index % 8 * this.spacing,
        48 + Math.floor(index / 8) * this.spacing,
        DEFAULT_BOX[2],
        DEFAULT_BOX[3]
      ];
    }
    add(text, options = {}) {
      const { id, maxclass, numinlets, numoutlets, patching_rect, ...props } = options;
      const box = {
        id: id ?? this.nextId(),
        maxclass: maxclass ?? "newobj",
        numinlets: numinlets ?? 2,
        numoutlets: numoutlets ?? 1,
        patching_rect: patching_rect ?? this.nextRect(),
        ...text === "" ? {} : { text },
        ...props
      };
      this.boxes.push({ box });
      return box;
    }
    addSubpatcher(text, options = {}) {
      const sub = new Patcher({ classnamespace: "box" });
      const box = this.add(text, { numinlets: 1, numoutlets: 1, ...options });
      box.patcher = sub.toPatcherDict();
      return { box, sub };
    }
    connect(from, to, outlet2 = 0, inlet = 0) {
      const order = this.lines.filter((l) => l.patchline.source[0] === from.id && l.patchline.destination[0] === to.id).length;
      const patchline = {
        source: [from.id, outlet2],
        destination: [to.id, inlet],
        ...order === 0 ? {} : { order }
      };
      this.lines.push({ patchline });
      return patchline;
    }
    toPatcherDict() {
      return { ...this.settings, boxes: this.boxes, lines: this.lines };
    }
    toFile() {
      return { patcher: this.toPatcherDict() };
    }
    toJSON(indent = 4) {
      return JSON.stringify(this.toFile(), null, indent);
    }
    static fromFile(file) {
      return new LoadedPatcher(file.patcher);
    }
    static parse(text) {
      return Patcher.fromFile(JSON.parse(text));
    }
  }

  class LoadedPatcher {
    patcher;
    constructor(patcher) {
      this.patcher = patcher;
    }
    get boxes() {
      return this.patcher.boxes;
    }
    get lines() {
      return this.patcher.lines;
    }
    maxNumericId() {
      let max = 0;
      for (const entry of this.patcher.boxes) {
        const match = /^obj-(\d+)$/.exec(entry.box.id);
        if (match?.[1] !== undefined) {
          max = Math.max(max, Number.parseInt(match[1], 10));
        }
      }
      return max;
    }
    findById(id) {
      return this.patcher.boxes.find((entry) => entry.box.id === id)?.box;
    }
    *walk() {
      const visit = function* (p) {
        for (const entry of p.boxes) {
          yield entry.box;
          if (entry.box.patcher)
            yield* visit(entry.box.patcher);
        }
      };
      yield* visit(this.patcher);
    }
    toFile() {
      return { patcher: this.patcher };
    }
    toJSON(indent = 4) {
      return JSON.stringify(this.toFile(), null, indent);
    }
  }

  // src/demo.ts
  function demoPatch() {
    const p = new Patcher;
    const osc = p.add("cycle~ 440");
    const gain = p.add("gain~", {
      maxclass: "gain~",
      numinlets: 2,
      numoutlets: 2
    });
    const dac = p.add("ezdac~", {
      maxclass: "ezdac~",
      numinlets: 2,
      numoutlets: 0
    });
    p.connect(osc, gain);
    p.connect(gain, dac, 0, 0);
    p.connect(gain, dac, 0, 1);
    return p.toPatcherDict();
  }
  function synthPatch() {
    const p = new Patcher;
    const ui = (maxclass, rect, extra = {}) => p.add("", { maxclass, patching_rect: rect, ...extra });
    const obj = (text, rect) => p.add(text, { patching_rect: rect });
    const onoff = ui("toggle", [40, 40, 24, 24]);
    const metro = obj("metro 250", [40, 80, 70, 22]);
    const pick = obj("random 12", [40, 120, 70, 22]);
    const transpose = obj("+ 60", [40, 160, 45, 22]);
    const tofreq = obj("mtof", [40, 200, 45, 22]);
    const osc = obj("cycle~", [40, 240, 60, 22]);
    const amp = ui("flonum", [160, 240, 50, 22]);
    const gain = obj("*~ 0.2", [40, 280, 60, 22]);
    const out = ui("ezdac~", [40, 330, 45, 45]);
    p.connect(onoff, metro);
    p.connect(metro, pick);
    p.connect(pick, transpose);
    p.connect(transpose, tofreq);
    p.connect(tofreq, osc);
    p.connect(osc, gain);
    p.connect(amp, gain, 0, 1);
    p.connect(gain, out, 0, 0);
    p.connect(gain, out, 0, 1);
    return p.toPatcherDict();
  }

  // src/fileio.ts
  var CHUNK = 16384;
  var maxFileFactory = (path, access) => {
    const ctor = globalThis.File;
    if (ctor === undefined) {
      throw new Error("js2max: no Max File class -- file I/O is only available inside Max");
    }
    return new ctor(path, access);
  };
  function readText(path, options = {}) {
    const factory = options.factory ?? maxFileFactory;
    const file = factory(path, "read");
    if (!file.isopen) {
      throw new Error(`js2max: could not open ${path} for reading`);
    }
    try {
      const chunks = [];
      while (file.position < file.eof) {
        const before = file.position;
        const chunk = file.readstring(CHUNK);
        if (chunk === "" || file.position <= before)
          break;
        chunks.push(chunk);
      }
      return chunks.join("");
    } finally {
      file.close();
    }
  }
  function writeText(path, text, options = {}) {
    const factory = options.factory ?? maxFileFactory;
    const file = factory(path, "write");
    if (!file.isopen) {
      throw new Error(`js2max: could not open ${path} for writing`);
    }
    try {
      try {
        file.eof = 0;
      } catch {}
      file.position = 0;
      file.writestring(text);
    } finally {
      file.close();
    }
  }
  function readPatch(path, options = {}) {
    const text = readText(path, options);
    let parsed;
    try {
      parsed = JSON.parse(text);
    } catch (err) {
      throw new Error(`js2max: ${path} is not valid JSON -- ${String(err)}`);
    }
    const file = parsed;
    if (file?.patcher?.boxes === undefined) {
      throw new Error(`js2max: ${path} has no patcher.boxes -- not a .maxpat?`);
    }
    return Patcher.fromFile(file);
  }
  function writePatch(path, patcher, options = {}) {
    writeText(path, patcher.toJSON(options.indent ?? 4), options);
  }

  // src/objects.ts
  var OWN_MAXCLASS = new Set([
    "attrui",
    "bpatcher",
    "button",
    "comment",
    "dial",
    "ezadc~",
    "ezdac~",
    "filtergraph~",
    "flonum",
    "function",
    "gain~",
    "gen.codebox~",
    "gswitch",
    "gswitch2",
    "incdec",
    "itable",
    "kslider",
    "led",
    "levelmeter~",
    "matrixctrl",
    "message",
    "meter~",
    "multislider",
    "nodes",
    "nslider",
    "number",
    "number~",
    "pictctrl",
    "pictslider",
    "playbar",
    "playlist~",
    "radiogroup",
    "rslider",
    "scope~",
    "slider",
    "spectroscope~",
    "tab",
    "textbutton",
    "toggle",
    "ubutton",
    "umenu",
    "waveform~",
    "zplane~"
  ]);
  var PORTS = {
    "2d.wave~": [4, 1, ["signal"]],
    abs: [1, 1, [""]],
    absolutepath: [1, 1, ["symbol"]],
    "abs~": [1, 1, ["signal"]],
    accum: [3, 1, [""]],
    acos: [1, 1, [""]],
    acosh: [1, 1, [""]],
    "acosh~": [1, 1, ["signal"]],
    "acos~": [1, 1, ["signal"]],
    "adc~": [1, 2, ["signal", "signal"]],
    "adoutput~": [1, 2, ["signal", "signal"]],
    "adsr~": [5, 4, ["signal", "signal", "message", "message"]],
    "allpass~": [3, 1, ["signal"]],
    "amxd~": [3, 4, ["signal", "signal", "signal", "signal"]],
    anal: [1, 1, [""]],
    append: [1, 1, [""]],
    array: [2, 3, ["", "", ""]],
    "array.change": [2, 2, ["", ""]],
    "array.compare": [2, 1, [""]],
    "array.concat": [2, 1, [""]],
    "array.deserialize": [1, 1, [""]],
    "array.every": [2, 3, ["", "", ""]],
    "array.expr": [2, 1, [""]],
    "array.fill": [2, 1, [""]],
    "array.filter": [2, 3, ["", "", ""]],
    "array.flatten": [2, 1, [""]],
    "array.foreach": [2, 3, ["", "", ""]],
    "array.frombuffer": [2, 2, ["", ""]],
    "array.group": [2, 1, [""]],
    "array.index": [2, 2, ["", ""]],
    "array.indexmap": [2, 1, [""]],
    "array.indexof": [2, 1, [""]],
    "array.insert": [3, 1, [""]],
    "array.iter": [2, 1, [""]],
    "array.join": [2, 1, [""]],
    "array.length": [1, 1, [""]],
    "array.map": [2, 3, ["", "", ""]],
    "array.max": [2, 1, [""]],
    "array.mean": [2, 1, [""]],
    "array.median": [2, 1, [""]],
    "array.min": [2, 1, [""]],
    "array.mode": [2, 1, [""]],
    "array.pop": [2, 3, ["", "", ""]],
    "array.push": [2, 1, [""]],
    "array.random": [2, 1, [""]],
    "array.reduce": [2, 4, ["", "", "", ""]],
    "array.regexp": [3, 5, ["", "", "", "", ""]],
    "array.remove": [3, 1, [""]],
    "array.replace": [3, 1, [""]],
    "array.reverse": [2, 1, [""]],
    "array.rotate": [2, 1, [""]],
    "array.routepass": [1, 1, [""]],
    "array.scramble": [2, 2, ["", ""]],
    "array.sect": [2, 1, [""]],
    "array.shift": [2, 3, ["", "", ""]],
    "array.slice": [2, 1, [""]],
    "array.some": [2, 3, ["", "", ""]],
    "array.sort": [2, 3, ["", "", ""]],
    "array.split": [2, 2, ["", ""]],
    "array.stddev": [2, 1, [""]],
    "array.stream": [2, 2, ["", ""]],
    "array.subarray": [2, 1, [""]],
    "array.thin": [1, 1, [""]],
    "array.tobuffer": [2, 1, [""]],
    "array.tolist": [1, 1, [""]],
    "array.tostring": [1, 1, [""]],
    "array.tosymbol": [1, 1, [""]],
    "array.tuplewise": [2, 2, ["", ""]],
    "array.union": [2, 1, [""]],
    "array.unique": [2, 1, [""]],
    "array.unshift": [2, 1, [""]],
    "array.wrap": [2, 1, [""]],
    asin: [1, 1, [""]],
    asinh: [1, 1, [""]],
    "asinh~": [1, 1, ["signal"]],
    "asin~": [1, 1, ["signal"]],
    atan: [1, 1, [""]],
    atan2: [2, 1, [""]],
    "atan2~": [2, 1, ["signal"]],
    atanh: [1, 1, [""]],
    "atanh~": [1, 1, ["signal"]],
    "atan~": [1, 1, ["signal"]],
    atodb: [1, 1, ["float"]],
    "atodb~": [1, 1, ["signal"]],
    atoi: [3, 1, ["list"]],
    attrui: [1, 1, [""]],
    autopattr: [1, 4, ["", "", "", ""]],
    "average~": [1, 1, ["signal"]],
    "avg~": [1, 1, ["float"]],
    bag: [2, 1, [""]],
    bangbang: [1, 2, ["", ""]],
    bendin: [1, 2, ["", ""]],
    "biquad~": [6, 1, ["signal"]],
    bitand: [2, 1, [""]],
    "bitand~": [2, 1, ["signal"]],
    "bitnot~": [1, 1, ["signal"]],
    bitor: [2, 1, [""]],
    "bitor~": [2, 1, ["signal"]],
    "bitsafe~": [1, 1, ["signal"]],
    "bitshift~": [1, 1, ["signal"]],
    "bitxor~": [2, 1, ["signal"]],
    bline: [1, 2, ["", ""]],
    bondo: [2, 2, ["", ""]],
    borax: [3, 9, ["", "", "", "", "", "", "", "", ""]],
    bpatcher: [1, 1, ["float", "", ""]],
    bucket: [1, 1, [""]],
    buddy: [2, 2, ["", ""]],
    "buffer~": [1, 2, ["", ""]],
    "buffir~": [3, 1, ["signal"]],
    button: [1, 1, ["bang"]],
    capture: [1, 2, ["", ""]],
    cartopol: [2, 2, ["", ""]],
    "cartopol~": [2, 2, ["signal", "signal"]],
    "cascade~": [2, 1, ["signal"]],
    change: [1, 3, ["", "", ""]],
    "change~": [1, 1, ["signal"]],
    chooser: [1, 6, ["", "", "", "", "", ""]],
    "chucker~": [3, 3, ["", "", ""]],
    "click~": [1, 1, ["signal"]],
    clip: [3, 1, [""]],
    "clip~": [3, 1, ["signal"]],
    clocker: [2, 1, [""]],
    closebang: [1, 1, [""]],
    coll: [1, 4, ["", "", "", ""]],
    "coll.codebox": [1, 4, ["", "", "", ""]],
    colorpicker: [1, 2, ["", ""]],
    combine: [1, 2, ["", ""]],
    "comb~": [5, 1, ["signal"]],
    comment: [1, 0],
    conformpath: [1, 2, ["symbol", "int"]],
    console: [1, 3, ["", "", "int"]],
    cos: [1, 1, [""]],
    cosh: [1, 1, [""]],
    "cosh~": [1, 1, [""]],
    "cosx~": [1, 1, [""]],
    "cos~": [1, 1, ["signal"]],
    counter: [5, 4, ["", "", "", ""]],
    "count~": [2, 1, ["signal"]],
    cpuclock: [1, 1, [""]],
    crosspatch: [1, 2, ["", "dictionary"]],
    "cross~": [2, 2, ["signal", "signal"]],
    ctlin: [1, 3, ["", "", ""]],
    "curve~": [3, 2, ["signal", "signal"]],
    "cverb~": [2, 1, ["signal"]],
    cycle: [1, 1, [""]],
    "cycle~": [2, 1, ["signal"]],
    date: [1, 3, ["", "", ""]],
    dbtoa: [1, 1, ["float"]],
    "dbtoa~": [1, 1, ["signal"]],
    "ddg.mono": [2, 2, ["int", "int"]],
    decide: [2, 1, [""]],
    decode: [3, 1, [""]],
    defer: [1, 1, [""]],
    deferlow: [1, 1, [""]],
    "degrade~": [3, 1, ["signal"]],
    delay: [2, 1, [""]],
    "delay~": [2, 1, ["signal"]],
    "deltaclip~": [3, 1, ["signal"]],
    "delta~": [1, 1, ["signal"]],
    detonate: [8, 8, ["", "", "", "", "", "", "", ""]],
    dial: [1, 1, ["float"]],
    dialog: [2, 3, ["", "", ""]],
    dict: [2, 5, ["", "", "", "", ""]],
    "dict.codebox": [2, 5, ["", "", "", "", ""]],
    "dict.compare": [2, 1, [""]],
    "dict.deserialize": [1, 1, [""]],
    "dict.group": [1, 1, [""]],
    "dict.iter": [1, 1, [""]],
    "dict.join": [2, 1, [""]],
    "dict.pack": [1, 1, [""]],
    "dict.route": [2, 2, ["", ""]],
    "dict.serialize": [1, 1, [""]],
    "dict.slice": [1, 2, ["", ""]],
    "dict.strip": [1, 2, ["", ""]],
    "dict.unpack": [1, 2, ["", ""]],
    div: [2, 1, [""]],
    "div~": [2, 1, ["signal"]],
    "downsamp~": [2, 1, ["signal"]],
    dropfile: [1, 2, ["", ""]],
    drunk: [3, 1, [""]],
    "dspstate~": [1, 4, ["", "", "", ""]],
    "dsptime~": [1, 1, [""]],
    "edge~": [1, 2, ["bang", "bang"]],
    equals: [2, 1, [""]],
    "equals~": [2, 1, ["signal"]],
    error: [1, 1, [""]],
    expr: [1, 1, [""]],
    "ezadc~": [1, 2, ["signal", "signal"]],
    "ezdac~": [2, 0],
    "fbinshift~": [3, 2, ["signal", "signal"]],
    "fffb~": [1, 4, ["signal", "signal", "signal", "signal"]],
    "fftinfo~": [1, 4, ["int", "int", "int", "int"]],
    "fftin~": [1, 3, ["signal", "signal", "signal"]],
    "fft~": [2, 3, ["signal", "signal", "signal"]],
    filedate: [1, 1, [""]],
    filein: [3, 3, ["", "", ""]],
    filepath: [1, 1, [""]],
    filewatch: [1, 1, [""]],
    "filtercoeff~": [3, 5, ["signal", "signal", "signal", "signal", "signal"]],
    filterdesign: [1, 1, [""]],
    filterdetail: [1, 6, ["", "", "", "", "", ""]],
    "filtergraph~": [8, 7, ["list", "float", "float", "float", "float", "list", "int"]],
    float: [2, 1, [""]],
    flonum: [1, 2, ["", "bang"]],
    flush: [2, 2, ["", ""]],
    folder: [1, 2, ["", ""]],
    follow: [1, 2, ["", ""]],
    fontlist: [1, 1, [""]],
    fpic: [1, 1, ["matrix"]],
    "frameaccum~": [1, 1, ["signal"]],
    "frameaverage~": [1, 1, ["signal"]],
    "framedelta~": [1, 1, ["signal"]],
    "framesmooth~": [1, 1, ["signal"]],
    "framesnap~": [2, 1, ["list"]],
    "frame~": [1, 1, ["signal"]],
    freebang: [1, 1, [""]],
    "freqshift~": [2, 2, ["signal", "signal"]],
    fromsymbol: [1, 1, [""]],
    fswap: [2, 2, ["", ""]],
    ftom: [1, 1, [""]],
    "ftom~": [1, 1, ["signal"]],
    funbuff: [2, 3, ["", "", ""]],
    function: [1, 4, ["float", "", "", "bang"]],
    "fzero~": [1, 3, ["float", "float", "bang"]],
    "gain~": [1, 2, ["signal", ""]],
    gamepad: [1, 3, ["list", "list", "message"]],
    gate: [2, 1, [""]],
    "gate~": [2, 1, ["signal"]],
    gen: [2, 1, [""]],
    "gen.codebox": [2, 1, [""]],
    "gen.codebox~": [1, 1, ["signal"]],
    "gen~": [2, 1, [""]],
    gestalt: [1, 2, ["", ""]],
    getattr: [1, 3, ["", "", ""]],
    "gizmo~": [3, 2, ["signal", "signal"]],
    grab: [1, 2, ["", ""]],
    greaterthan: [2, 1, [""]],
    greaterthaneq: [2, 1, [""]],
    "greaterthaneq~": [2, 1, ["signal"]],
    "greaterthan~": [2, 1, ["signal"]],
    "gridmeter~": [1, 1, ["multi-channel signal"]],
    "groove~": [3, 2, ["signal", "signal"]],
    gswitch: [3, 1, [""]],
    gswitch2: [2, 2, ["", ""]],
    hi: [1, 2, ["list", "message"]],
    hid: [1, 3, ["list", "message", "message"]],
    "hilbert~": [1, 2, ["signal", "signal"]],
    histo: [2, 2, ["", ""]],
    hover: [1, 4, ["", "", "", ""]],
    "ifft~": [2, 3, ["signal", "signal", "signal"]],
    imovie: [1, 3, ["", "", ""]],
    in: [1, 1, [""]],
    incdec: [1, 1, ["float"]],
    "index~": [2, 2, ["signal", "signal"]],
    "info~": [1, 10, ["", "", "", "", "", "", "", "", "", ""]],
    inlet: [1, 1, [""]],
    int: [2, 1, [""]],
    "in~": [1, 1, ["signal"]],
    "ioscbank~": [4, 1, ["signal"]],
    itable: [2, 2, ["int", "bang"]],
    iter: [1, 1, [""]],
    itoa: [3, 1, [""]],
    "jit.3m": [1, 4, ["list", "list", "list", "list"]],
    "jit.alphablend": [2, 2, ["matrix", "matrix"]],
    "jit.altern": [1, 2, ["matrix", "matrix"]],
    "jit.ameba": [1, 2, ["matrix", "matrix"]],
    "jit.anim.drive": [1, 2, ["", ""]],
    "jit.anim.node": [1, 2, ["", ""]],
    "jit.anim.path": [1, 2, ["", ""]],
    "jit.argb2ayuv": [1, 2, ["matrix", "matrix"]],
    "jit.argb2grgb": [1, 2, ["matrix", "matrix"]],
    "jit.argb2uyvy": [1, 2, ["matrix", "matrix"]],
    "jit.avc": [2, 1, [""]],
    "jit.avg4": [1, 2, ["matrix", "matrix"]],
    "jit.axis2quat": [1, 2, ["", ""]],
    "jit.ayuv2argb": [1, 2, ["matrix", "matrix"]],
    "jit.ayuv2luma": [1, 2, ["matrix", "matrix"]],
    "jit.ayuv2uyvy": [1, 2, ["matrix", "matrix"]],
    "jit.bfg": [1, 2, ["matrix", "matrix"]],
    "jit.brass": [1, 2, ["matrix", "matrix"]],
    "jit.brcosa": [1, 2, ["matrix", "matrix"]],
    "jit.bsort": [1, 2, ["matrix", "matrix"]],
    "jit.buffer~": [1, 3, ["matrix", "matrix", "matrix"]],
    "jit.catch~": [1, 2, ["matrix", "matrix"]],
    "jit.cellblock": [2, 4, ["list", "list", "list", "list"]],
    "jit.change": [1, 2, ["matrix", "matrix"]],
    "jit.charmap": [2, 2, ["matrix", "matrix"]],
    "jit.chromakey": [2, 2, ["matrix", "matrix"]],
    "jit.clip": [1, 2, ["matrix", "matrix"]],
    "jit.coerce": [1, 2, ["matrix", "matrix"]],
    "jit.colorspace": [1, 2, ["matrix", "matrix"]],
    "jit.concat": [2, 2, ["matrix", "matrix"]],
    "jit.convolve": [2, 2, ["matrix", "matrix"]],
    "jit.conway": [1, 2, ["matrix", "matrix"]],
    "jit.cycle": [1, 2, ["", ""]],
    "jit.demultiplex": [1, 3, ["matrix", "matrix", "matrix"]],
    "jit.desktop": [1, 2, ["matrix", "matrix"]],
    "jit.dimmap": [1, 2, ["matrix", "matrix"]],
    "jit.dimop": [1, 2, ["matrix", "matrix"]],
    "jit.displays": [1, 1, [""]],
    "jit.dx.grab": [2, 2, ["matrix", "matrix"]],
    "jit.dx.videoout": [2, 2, ["matrix", "matrix"]],
    "jit.eclipse": [2, 2, ["matrix", "matrix"]],
    "jit.euler2quat": [1, 2, ["", ""]],
    "jit.expr": [2, 2, ["matrix", "matrix"]],
    "jit.fastblur": [1, 2, ["matrix", "matrix"]],
    "jit.fft": [1, 2, ["matrix", "matrix"]],
    "jit.fill": [1, 2, ["", ""]],
    "jit.findbounds": [1, 3, ["list", "list", "list"]],
    "jit.fluoride": [1, 2, ["matrix", "matrix"]],
    "jit.fprint": [1, 2, ["matrix", "matrix"]],
    "jit.fpsgui": [1, 2, ["", ""]],
    "jit.freeframe": [2, 2, ["matrix", "matrix"]],
    "jit.gen": [1, 2, ["", ""]],
    "jit.gen.codebox": [1, 2, ["", ""]],
    "jit.gencoord": [1, 2, ["matrix", "matrix"]],
    "jit.gl.asyncread": [1, 2, ["", ""]],
    "jit.gl.bfg": [1, 2, ["", ""]],
    "jit.gl.camera": [1, 2, ["", ""]],
    "jit.gl.cornerpin": [1, 2, ["", ""]],
    "jit.gl.cubemap": [6, 2, ["", ""]],
    "jit.gl.graph": [1, 2, ["disabled", "disabled"]],
    "jit.gl.gridshape": [1, 2, ["disabled", "disabled"]],
    "jit.gl.handle": [1, 2, ["", ""]],
    "jit.gl.isosurf": [1, 2, ["disabled", "disabled"]],
    "jit.gl.light": [1, 1, [""]],
    "jit.gl.lua": [1, 2, ["", ""]],
    "jit.gl.material": [8, 2, ["", ""]],
    "jit.gl.mesh": [9, 2, ["", ""]],
    "jit.gl.model": [1, 2, ["disabled", "disabled"]],
    "jit.gl.multiple": [2, 2, ["", ""]],
    "jit.gl.node": [1, 3, ["", "", ""]],
    "jit.gl.nurbs": [1, 2, ["disabled", "disabled"]],
    "jit.gl.pass": [1, 3, ["", "", ""]],
    "jit.gl.path": [1, 2, ["", ""]],
    "jit.gl.physdraw": [1, 1, [""]],
    "jit.gl.picker": [1, 2, ["", ""]],
    "jit.gl.pix": [2, 2, ["", ""]],
    "jit.gl.pix.codebox": [2, 2, ["", ""]],
    "jit.gl.plato": [1, 2, ["disabled", "disabled"]],
    "jit.gl.render": [1, 2, ["", ""]],
    "jit.gl.shader": [1, 2, ["", ""]],
    "jit.gl.sketch": [1, 2, ["", ""]],
    "jit.gl.skybox": [1, 2, ["", ""]],
    "jit.gl.slab": [2, 2, ["", ""]],
    "jit.gl.text": [1, 2, ["disabled", "disabled"]],
    "jit.gl.texture": [1, 2, ["", ""]],
    "jit.gl.videoplane": [1, 2, ["disabled", "disabled"]],
    "jit.gl.volume": [1, 2, ["disabled", "disabled"]],
    "jit.glop": [1, 2, ["matrix", "matrix"]],
    "jit.glue": [1, 2, ["matrix", "matrix"]],
    "jit.grab": [1, 2, ["matrix / texture", "matrix / texture"]],
    "jit.gradient": [1, 2, ["matrix", "matrix"]],
    "jit.grgb2argb": [1, 2, ["matrix", "matrix"]],
    "jit.hatch": [1, 2, ["matrix", "matrix"]],
    "jit.hello": [1, 1, [""]],
    "jit.histogram": [1, 2, ["matrix", "matrix"]],
    "jit.hsl2rgb": [1, 2, ["matrix", "matrix"]],
    "jit.hue": [1, 2, ["matrix", "matrix"]],
    "jit.iter": [1, 3, ["list", "list", "list"]],
    "jit.keyscreen": [3, 2, ["matrix", "matrix"]],
    "jit.la.determinant": [1, 2, ["float/list", "float/list"]],
    "jit.la.diagproduct": [1, 2, ["float/list", "float/list"]],
    "jit.la.inverse": [1, 2, ["matrix", "matrix"]],
    "jit.la.mult": [2, 2, ["matrix", "matrix"]],
    "jit.la.trace": [1, 2, ["float/list", "float/list"]],
    "jit.la.uppertri": [1, 2, ["matrix", "matrix"]],
    "jit.lcd": [1, 2, ["matrix", "matrix"]],
    "jit.linden": [1, 2, ["matrix", "matrix"]],
    "jit.luma2ayuv": [1, 2, ["matrix", "matrix"]],
    "jit.luma2uyvy": [1, 2, ["matrix", "matrix"]],
    "jit.lumakey": [2, 2, ["matrix", "matrix"]],
    "jit.map": [1, 2, ["matrix", "matrix"]],
    "jit.matrix": [1, 2, ["matrix", "matrix"]],
    "jit.matrixinfo": [1, 1, ["matrix"]],
    "jit.matrixset": [1, 2, ["matrix", "matrix"]],
    "jit.mgraphics": [1, 2, ["matrix", "matrix"]],
    "jit.movie": [1, 2, ["matrix / texture", "matrix / texture"]],
    "jit.multiplex": [2, 2, ["matrix", "matrix"]],
    "jit.mxform2d": [1, 2, ["matrix", "matrix"]],
    "jit.net.recv": [1, 3, ["", "", ""]],
    "jit.net.send": [2, 1, [""]],
    "jit.noise": [1, 2, ["matrix", "matrix"]],
    "jit.normalize": [1, 2, ["matrix", "matrix"]],
    "jit.op": [2, 2, ["matrix", "matrix"]],
    "jit.openexr": [1, 2, ["matrix", "matrix"]],
    "jit.p.bounds": [1, 2, ["matrix", "matrix"]],
    "jit.p.shiva": [1, 2, ["matrix", "matrix"]],
    "jit.p.vishnu": [1, 2, ["matrix", "matrix"]],
    "jit.pack": [4, 2, ["matrix", "matrix"]],
    "jit.path": [1, 4, ["", "", "", ""]],
    "jit.peek~": [2, 2, ["signal", "signal"]],
    "jit.phys.6dof": [1, 3, ["", "", ""]],
    "jit.phys.barslide": [1, 3, ["", "", ""]],
    "jit.phys.body": [1, 2, ["", ""]],
    "jit.phys.conetwist": [1, 3, ["", "", ""]],
    "jit.phys.ghost": [1, 2, ["", ""]],
    "jit.phys.hinge": [1, 3, ["", "", ""]],
    "jit.phys.multiple": [2, 3, ["", "", ""]],
    "jit.phys.picker": [1, 2, ["", ""]],
    "jit.phys.point2point": [1, 3, ["", "", ""]],
    "jit.phys.world": [1, 2, ["", ""]],
    "jit.pix": [1, 2, ["", ""]],
    "jit.pix.codebox": [1, 2, ["", ""]],
    "jit.planeop": [1, 2, ["matrix", "matrix"]],
    "jit.playlist": [1, 3, ["matrix/texture", "matrix/texture", "dict"]],
    "jit.plume": [2, 2, ["matrix", "matrix"]],
    "jit.plur": [1, 2, ["matrix", "matrix"]],
    "jit.poke~": [3, 1, [""]],
    "jit.print": [1, 2, ["matrix", "matrix"]],
    "jit.proxy": [1, 2, ["", ""]],
    "jit.pwindow": [1, 2, ["", ""]],
    "jit.pworld": [1, 2, ["", ""]],
    "jit.qball": [1, 2, ["", ""]],
    "jit.qfaker": [1, 2, ["", ""]],
    "jit.qt.grab": [2, 2, ["matrix", "matrix"]],
    "jit.qt.movie": [2, 2, ["matrix", "matrix"]],
    "jit.qt.record": [2, 2, ["matrix", "matrix"]],
    "jit.qt.videoout": [2, 2, ["matrix", "matrix"]],
    "jit.quat": [2, 2, ["", ""]],
    "jit.quat2axis": [1, 2, ["", ""]],
    "jit.quat2euler": [1, 2, ["", ""]],
    "jit.record": [1, 2, ["matrix", "matrix"]],
    "jit.release~": [1, 2, ["signal", "signal"]],
    "jit.repos": [2, 2, ["matrix", "matrix"]],
    "jit.resamp": [1, 2, ["matrix", "matrix"]],
    "jit.reverse": [2, 2, ["", ""]],
    "jit.rgb2hsl": [1, 2, ["matrix", "matrix"]],
    "jit.rgb2luma": [1, 2, ["matrix", "matrix"]],
    "jit.robcross": [1, 2, ["matrix", "matrix"]],
    "jit.rota": [1, 2, ["matrix", "matrix"]],
    "jit.roy": [2, 2, ["matrix", "matrix"]],
    "jit.rubix": [1, 2, ["matrix", "matrix"]],
    "jit.scalebias": [1, 2, ["matrix", "matrix"]],
    "jit.scanoffset": [2, 2, ["matrix", "matrix"]],
    "jit.scanslide": [1, 2, ["matrix", "matrix"]],
    "jit.scanwrap": [1, 2, ["matrix", "matrix"]],
    "jit.scissors": [1, 2, ["matrix", "matrix"]],
    "jit.scope": [1, 2, ["", ""]],
    "jit.shade": [3, 2, ["matrix", "matrix"]],
    "jit.slide": [1, 2, ["matrix", "matrix"]],
    "jit.sobel": [1, 2, ["matrix", "matrix"]],
    "jit.spill": [1, 2, ["list", "list"]],
    "jit.split": [1, 3, ["matrix", "matrix", "matrix"]],
    "jit.sprinkle": [1, 2, ["matrix", "matrix"]],
    "jit.str.fromsymbol": [1, 2, ["matrix", "matrix"]],
    "jit.str.op": [2, 2, ["matrix", "matrix"]],
    "jit.str.regexp": [1, 5, ["matrix", "matrix", "matrix", "matrix", "matrix"]],
    "jit.str.tosymbol": [1, 2, ["symbol", "symbol"]],
    "jit.streak": [1, 2, ["matrix", "matrix"]],
    "jit.submatrix": [1, 2, ["matrix", "matrix"]],
    "jit.textfile": [1, 3, ["matrix", "matrix", "matrix"]],
    "jit.thin": [1, 2, ["matrix", "matrix"]],
    "jit.tiffany": [1, 2, ["matrix", "matrix"]],
    "jit.traffic": [2, 2, ["matrix", "matrix"]],
    "jit.transpose": [1, 2, ["matrix", "matrix"]],
    "jit.turtle": [1, 2, ["matrix", "matrix"]],
    "jit.uldl": [1, 2, ["matrix", "matrix"]],
    "jit.unpack": [1, 5, ["matrix", "matrix", "matrix", "matrix", "matrix"]],
    "jit.uyvy2argb": [1, 2, ["matrix", "matrix"]],
    "jit.uyvy2ayuv": [1, 2, ["matrix", "matrix"]],
    "jit.uyvy2luma": [1, 2, ["matrix", "matrix"]],
    "jit.vcr": [3, 2, ["matrix", "matrix"]],
    "jit.wake": [1, 2, ["matrix", "matrix"]],
    "jit.window": [1, 2, ["", ""]],
    "jit.world": [1, 3, ["", "", ""]],
    "jit.xfade": [2, 2, ["matrix", "matrix"]],
    join: [2, 1, [""]],
    js: [1, 1, [""]],
    jsui: [1, 1, [""]],
    jweb: [1, 1, [""]],
    "jweb~": [1, 3, ["signal", "signal", "signal"]],
    "kink~": [2, 1, ["signal"]],
    kslider: [2, 2, ["int", "int"]],
    lcd: [1, 4, ["", "", "", ""]],
    led: [1, 1, ["int"]],
    lessthan: [2, 1, [""]],
    lessthaneq: [2, 1, [""]],
    "lessthaneq~": [2, 1, ["signal"]],
    "lessthan~": [2, 1, ["signal"]],
    "levelmeter~": [1, 1, [""]],
    "limi~": [1, 1, ["signal"]],
    line: [3, 2, ["", ""]],
    "line~": [2, 2, ["signal", "signal"]],
    listbox: [1, 2, ["", ""]],
    listfunnel: [1, 1, [""]],
    "live.arrows": [1, 1, [""]],
    "live.banks": [1, 1, [""]],
    "live.button": [1, 1, [""]],
    "live.colors": [1, 2, ["", ""]],
    "live.dial": [1, 2, ["int/float", "int/float"]],
    "live.drop": [1, 2, ["", ""]],
    "live.gain~": [2, 5, ["signal", "signal", "int/float", "int/float", "float/list"]],
    "live.grid": [2, 6, ["list", "list", "list", "list", "list", "anything"]],
    "live.map": [1, 5, ["", "", "", "", ""]],
    "live.menu": [1, 3, ["", "", ""]],
    "live.meter~": [1, 2, ["float", "int"]],
    "live.miditool.in": [1, 3, ["", "", ""]],
    "live.modulate~": [2, 1, [""]],
    "live.numbox": [1, 2, ["int/float", "int/float"]],
    "live.routing": [1, 5, ["", "", "", "", ""]],
    "live.slider": [1, 2, ["int/float", "int/float"]],
    "live.step": [1, 5, ["list", "list", "list", "list", "int"]],
    "live.tab": [1, 3, ["", "", ""]],
    "live.text": [1, 2, ["", ""]],
    "live.thisdevice": [1, 3, ["", "", ""]],
    "live.toggle": [1, 1, ["int"]],
    loadbang: [1, 1, [""]],
    loadmess: [1, 1, [""]],
    logand: [2, 1, [""]],
    logor: [2, 1, [""]],
    "log~": [2, 1, ["signal"]],
    "lookup~": [3, 1, ["signal"]],
    "lores~": [3, 1, ["signal"]],
    "loudness~": [1, 6, ["float", "float", "float", "float", "float", "float"]],
    makenote: [3, 2, ["", ""]],
    match: [1, 1, [""]],
    matrix: [3, 3, ["dictionary", "dictionary", "dictionary"]],
    matrixctrl: [1, 2, ["list", "list"]],
    "matrix~": [2, 3, ["signal", "signal", "list"]],
    maximum: [2, 2, ["", ""]],
    "maximum~": [2, 1, ["Signal"]],
    maxurl: [2, 2, ["", ""]],
    "mc.2d.wave~": [4, 1, ["signal"]],
    "mc.abs~": [1, 1, ["signal"]],
    "mc.acosh~": [1, 1, ["signal"]],
    "mc.acos~": [1, 1, ["signal"]],
    "mc.adc~": [1, 1, ["multi-channel signal"]],
    "mc.adsr~": [5, 4, ["signal", "signal", "message", "message"]],
    "mc.allpass~": [3, 1, ["signal"]],
    "mc.amxd~": [3, 4, ["signal", "signal", "signal", "signal"]],
    "mc.apply~": [3, 1, ["multi-channel signal"]],
    "mc.asinh~": [1, 1, ["signal"]],
    "mc.asin~": [1, 1, ["signal"]],
    "mc.assign": [1, 1, [""]],
    "mc.atan2~": [2, 1, ["signal"]],
    "mc.atanh~": [1, 1, ["signal"]],
    "mc.atan~": [1, 1, ["signal"]],
    "mc.atodb~": [1, 1, ["signal"]],
    "mc.average~": [1, 1, ["signal"]],
    "mc.avg~": [1, 1, ["float"]],
    "mc.biquad~": [6, 1, ["signal"]],
    "mc.bitand~": [2, 1, ["signal"]],
    "mc.bitnot~": [1, 1, ["signal"]],
    "mc.bitor~": [2, 1, ["signal"]],
    "mc.bitsafe~": [1, 1, ["signal"]],
    "mc.bitshift~": [1, 1, ["signal"]],
    "mc.bitxor~": [2, 1, ["signal"]],
    "mc.buffir~": [3, 1, ["signal"]],
    "mc.cartopol~": [2, 2, ["signal", "signal"]],
    "mc.cascade~": [2, 1, ["signal"]],
    "mc.cell": [1, 1, [""]],
    "mc.change~": [1, 1, ["signal"]],
    "mc.channelcount~": [1, 2, ["int", "signal"]],
    "mc.chord~": [1, 4, ["multi-channel signal", "multi-channel signal", "list", "int"]],
    "mc.click~": [1, 1, ["signal"]],
    "mc.clip~": [3, 1, ["signal"]],
    "mc.combine~": [2, 1, ["multi-channel signal"]],
    "mc.comb~": [5, 1, ["signal"]],
    "mc.cosh~": [1, 1, [""]],
    "mc.cosx~": [1, 1, [""]],
    "mc.cos~": [1, 1, ["signal"]],
    "mc.count~": [2, 1, ["signal"]],
    "mc.cross~": [2, 2, ["signal", "signal"]],
    "mc.curve~": [3, 2, ["signal", "signal"]],
    "mc.cycle~": [2, 1, ["signal"]],
    "mc.dbtoa~": [1, 1, ["signal"]],
    "mc.degrade~": [3, 1, ["signal"]],
    "mc.deinterleave~": [1, 2, ["multi-channel signal", "multi-channel signal"]],
    "mc.delay~": [2, 1, ["signal"]],
    "mc.deltaclip~": [3, 1, ["signal"]],
    "mc.delta~": [1, 1, ["signal"]],
    "mc.div~": [2, 1, ["signal"]],
    "mc.downsamp~": [2, 1, ["signal"]],
    "mc.dup~": [1, 1, ["multi-channel signal"]],
    "mc.edge~": [1, 2, ["bang", "bang"]],
    "mc.equals~": [2, 1, ["signal"]],
    "mc.evolve~": [1, 3, ["multi-channel signal", "float", "list"]],
    "mc.ezadc~": [1, 1, ["multi-channel signal"]],
    "mc.fffb~": [1, 4, ["signal", "signal", "signal", "signal"]],
    "mc.fft~": [2, 3, ["signal", "signal", "signal"]],
    "mc.filtercoeff~": [3, 5, ["signal", "signal", "signal", "signal", "signal"]],
    "mc.frameaccum~": [1, 1, ["signal"]],
    "mc.frameaverage~": [1, 1, ["signal"]],
    "mc.framedelta~": [1, 1, ["signal"]],
    "mc.framesmooth~": [1, 1, ["signal"]],
    "mc.freqshift~": [2, 2, ["signal", "signal"]],
    "mc.ftom~": [1, 1, ["signal"]],
    "mc.function": [1, 5, ["", "", "", "", ""]],
    "mc.fzero~": [1, 3, ["float", "float", "bang"]],
    "mc.gain~": [1, 2, ["signal", "signal"]],
    "mc.gate~": [2, 1, ["signal"]],
    "mc.gen": [2, 1, [""]],
    "mc.generate~": [4, 1, ["multi-channel signal"]],
    "mc.gen~": [2, 1, [""]],
    "mc.getattr": [1, 3, ["", "", ""]],
    "mc.gradient~": [1, 3, ["multi-channel signal", "float", "list"]],
    "mc.greaterthaneq~": [2, 1, ["signal"]],
    "mc.greaterthan~": [2, 1, ["signal"]],
    "mc.groove~": [3, 2, ["signal", "signal"]],
    "mc.hilbert~": [1, 2, ["signal", "signal"]],
    "mc.ifft~": [2, 3, ["signal", "signal", "signal"]],
    "mc.index~": [2, 2, ["signal", "signal"]],
    "mc.interleave~": [2, 1, ["multi-channel signal"]],
    "mc.in~": [1, 1, ["multi-channel signal"]],
    "mc.jit.peek~": [2, 2, ["signal", "signal"]],
    "mc.kink~": [2, 1, ["signal"]],
    "mc.lessthaneq~": [2, 1, ["signal"]],
    "mc.lessthan~": [2, 1, ["signal"]],
    "mc.limi~": [1, 1, ["signal"]],
    "mc.line": [3, 2, ["", ""]],
    "mc.line~": [2, 2, ["signal", "signal"]],
    "mc.list~": [1, 1, ["multi-channel signal"]],
    "mc.live.gain~": [1, 4, ["multi-channel signal", "int/float", "int/float", "float/list"]],
    "mc.log~": [2, 1, ["signal"]],
    "mc.lookup~": [3, 1, ["signal"]],
    "mc.lores~": [3, 1, ["signal"]],
    "mc.loudness~": [1, 6, ["float", "float", "float", "float", "float", "float"]],
    "mc.makelist": [3, 1, [""]],
    "mc.matrix~": [2, 3, ["signal", "signal", "list"]],
    "mc.maximum~": [2, 1, ["Signal"]],
    "mc.midiplayer~": [3, 2, ["signal", "midievent"]],
    "mc.miditarget": [1, 1, [""]],
    "mc.minimum~": [2, 1, ["Signal"]],
    "mc.minmax~": [2, 4, ["signal", "signal", "double", "double"]],
    "mc.minus~": [2, 1, ["signal"]],
    "mc.mixdown~": [2, 1, ["multi-channel signal"]],
    "mc.modulo~": [2, 1, ["signal"]],
    "mc.mstosamps~": [1, 2, ["signal", "double"]],
    "mc.mtof~": [1, 1, ["signal"]],
    "mc.noise~": [1, 1, ["signal"]],
    "mc.normalize~": [2, 1, ["signal"]],
    "mc.noteallocator~": [1, 6, ["", "", "", "", "", ""]],
    "mc.notequals~": [2, 1, ["signal"]],
    "mc.number~": [2, 3, ["multi-channel signal", "float", "float"]],
    "mc.omx.4band~": [2, 4, ["signal", "signal", "list", "list"]],
    "mc.omx.5band~": [2, 4, ["signal", "signal", "list", "list"]],
    "mc.omx.comp~": [2, 4, ["signal", "signal", "list", "list"]],
    "mc.omx.peaklim~": [2, 4, ["signal", "signal", "list", "list"]],
    "mc.onepole~": [2, 1, ["signal"]],
    "mc.op~": [1, 1, ["signal"]],
    "mc.overdrive~": [2, 1, [""]],
    "mc.pack~": [2, 1, ["multi-channel signal"]],
    "mc.pattern~": [1, 3, ["multi-channel signal", "multi-channel signal", "dictionary"]],
    "mc.peakamp~": [2, 1, ["float"]],
    "mc.peek~": [3, 1, [""]],
    "mc.phasegroove~": [1, 1, ["signal"]],
    "mc.phaseshift~": [3, 1, ["signal"]],
    "mc.phasewrap~": [1, 1, [""]],
    "mc.phasor~": [2, 1, ["signal"]],
    "mc.pink~": [1, 1, ["signal"]],
    "mc.pitchshift~": [2, 2, ["Signal", "Signal"]],
    "mc.playlist~": [1, 4, ["multi-channel signal", "signal", "signal", "dict"]],
    "mc.play~": [1, 2, ["signal", "signal"]],
    "mc.plusequals~": [2, 1, ["signal"]],
    "mc.plus~": [2, 1, ["signal"]],
    "mc.poltocar~": [2, 2, ["", ""]],
    "mc.pong~": [3, 1, ["signal"]],
    "mc.pow~": [2, 1, ["signal"]],
    "mc.rampsmooth~": [3, 1, ["signal"]],
    "mc.ramp~": [4, 2, ["signal", "signal"]],
    "mc.rand~": [1, 1, ["signal"]],
    "mc.range~": [1, 3, ["multi-channel signal", "list", "setvalue"]],
    "mc.rate~": [2, 1, ["signal"]],
    "mc.rdiv~": [2, 1, ["signal"]],
    "mc.receive~": [1, 1, ["multi-channel signal"]],
    "mc.record~": [3, 1, ["signal"]],
    "mc.rect~": [3, 1, ["signal"]],
    "mc.resize~": [1, 1, ["multi-channel signal"]],
    "mc.reson~": [4, 1, ["signal"]],
    "mc.retune~": [3, 5, ["Signal", "Signal", "Signal", "Signal", "List"]],
    "mc.rminus~": [2, 1, ["signal"]],
    "mc.round~": [2, 1, ["signal"]],
    "mc.route": [2, 2, ["int", "int"]],
    "mc.sah~": [2, 1, ["signal"]],
    "mc.sampstoms~": [1, 2, ["signal", "double"]],
    "mc.sash~": [3, 1, ["signal"]],
    "mc.saw~": [2, 1, ["signal"]],
    "mc.scale~": [6, 1, ["signal"]],
    "mc.selector~": [2, 1, ["signal"]],
    "mc.separate~": [1, 2, ["multi-channel signal", "multi-channel signal"]],
    "mc.seq~": [1, 3, ["anything", "list", "symbol"]],
    "mc.sfizz~": [2, 2, ["", ""]],
    "mc.sfplay~": [2, 2, ["signal", "signal"]],
    "mc.sfrecord~": [1, 1, ["signal"]],
    "mc.shape~": [1, 1, ["signal"]],
    "mc.sig~": [1, 1, ["signal"]],
    "mc.sinh~": [1, 1, [""]],
    "mc.sinx~": [1, 1, [""]],
    "mc.slide~": [3, 1, ["signal"]],
    "mc.snapshot~": [2, 1, ["float"]],
    "mc.snowfall~": [1, 1, ["signal"]],
    "mc.snowphasor~": [2, 1, ["multi-channel signal"]],
    "mc.spike~": [2, 1, ["double"]],
    "mc.sqrt~": [1, 1, ["signal"]],
    "mc.stash~": [4, 2, ["signal", "signal"]],
    "mc.stepdiv~": [1, 2, ["signal", "signal"]],
    "mc.stepfun~": [2, 2, ["signal", "signal"]],
    "mc.stereo~": [2, 1, ["multi-channel signal"]],
    "mc.stutter~": [3, 1, ["signal"]],
    "mc.subdiv~": [1, 3, ["signal", "signal", "int"]],
    "mc.svf~": [3, 4, ["signal", "signal", "signal", "signal"]],
    "mc.swing~": [1, 3, ["signal", "signal", "int"]],
    "mc.sync~": [1, 3, ["", "", ""]],
    "mc.table~": [1, 1, ["signal"]],
    "mc.tanh~": [1, 1, [""]],
    "mc.tanx~": [1, 1, [""]],
    "mc.tapin~": [1, 1, [""]],
    "mc.tapout~": [1, 1, ["signal"]],
    "mc.target": [2, 2, ["", "int, voice"]],
    "mc.targetlist": [2, 2, ["", "int"]],
    "mc.teeth~": [6, 1, ["signal"]],
    "mc.thresh~": [3, 1, ["signal"]],
    "mc.times~": [2, 1, ["Signal"]],
    "mc.train~": [3, 2, ["signal", "signal"]],
    "mc.transpose~": [2, 2, ["multi-channel signal", "multi-channel signal"]],
    "mc.trapezoid~": [3, 1, ["signal"]],
    "mc.triangle~": [2, 1, ["signal"]],
    "mc.tri~": [3, 1, ["signal"]],
    "mc.trunc~": [1, 1, ["signal"]],
    "mc.twist~": [2, 1, ["signal"]],
    "mc.unpack~": [1, 2, ["signal", "signal"]],
    "mc.updown~": [1, 1, ["signal"]],
    "mc.vectral~": [3, 1, ["signal"]],
    "mc.voiceallocator~": [1, 2, ["", ""]],
    "mc.vst~": [2, 8, ["signal", "signal", "signal", "signal", "signal", "signal", "signal", "signal"]],
    "mc.wave~": [3, 1, ["signal"]],
    "mc.what~": [1, 2, ["signal", "int"]],
    "mc.where~": [1, 2, ["signal", "signal"]],
    "mc.zerox~": [1, 2, ["signal", "signal"]],
    "mc.zigzag~": [2, 4, ["signal", "signal", "signal", "signal"]],
    "mcs.2d.wave~": [4, 1, ["multi-channel signal"]],
    "mcs.amxd~": [2, 3, ["multi-channel signal", "multi-channel signal", "multi-channel signal"]],
    "mcs.fffb~": [1, 1, ["multi-channel signal"]],
    "mcs.gate~": [2, 1, ["multi-channel signal"]],
    "mcs.gen~": [1, 1, [""]],
    "mcs.groove~": [3, 2, ["multi-channel signal", "signal"]],
    "mcs.limi~": [1, 1, ["multi-channel signal"]],
    "mcs.matrix~": [1, 2, ["multi-channel signal", "list"]],
    "mcs.play~": [1, 2, ["multi-channel signal", "multi-channel signal"]],
    "mcs.selector~": [2, 1, ["signal"]],
    "mcs.sig~": [1, 1, ["multi-channel signal"]],
    "mcs.tapout~": [1, 1, ["signal"]],
    "mcs.vst~": [1, 7, ["multi-channel signal", "multi-channel signal", "multi-channel signal", "multi-channel signal", "multi-channel signal", "multi-channel signal", "multi-channel signal"]],
    "mcs.wave~": [3, 1, ["multi-channel signal"]],
    mean: [1, 2, ["float", "int"]],
    menubar: [1, 4, ["", "", "", ""]],
    message: [2, 1, [""]],
    messageview: [1, 1, [""]],
    "meter~": [1, 1, ["float"]],
    metro: [2, 1, [""]],
    midiflush: [1, 1, [""]],
    midiin: [1, 1, [""]],
    midiinfo: [2, 1, [""]],
    midiparse: [1, 8, ["", "", "", "", "", "", "", ""]],
    midiselect: [1, 8, ["", "", "", "", "", "", "", ""]],
    minimum: [2, 2, ["", ""]],
    "minimum~": [2, 1, ["Signal"]],
    "minmax~": [2, 4, ["signal", "signal", "double", "double"]],
    minus: [2, 1, [""]],
    "minus~": [2, 1, ["signal"]],
    modifiers: [1, 5, ["", "", "", "", ""]],
    modulo: [2, 1, [""]],
    "modulo~": [2, 1, ["signal"]],
    mousefilter: [1, 1, [""]],
    mousestate: [1, 10, ["", "", "", "", "", "", "", "", "", ""]],
    movie: [1, 3, ["", "", ""]],
    mpeconfig: [1, 2, ["", ""]],
    mpeformat: [16, 2, ["", ""]],
    mpeparse: [1, 10, ["", "", "", "", "", "", "", "", "", ""]],
    "mstosamps~": [1, 2, ["signal", "double"]],
    mtof: [1, 1, [""]],
    "mtof~": [1, 1, ["signal"]],
    mtr: [2, 2, ["", ""]],
    multirange: [1, 4, ["", "", "", ""]],
    multislider: [1, 2, ["", ""]],
    "mute~": [1, 1, [""]],
    next: [1, 2, ["", ""]],
    nodes: [1, 3, ["", "", ""]],
    "noise~": [1, 1, ["signal"]],
    "normalize~": [2, 1, ["signal"]],
    notein: [1, 3, ["", "", ""]],
    notequals: [2, 1, [""]],
    "notequals~": [2, 1, ["signal"]],
    nrpnin: [1, 4, ["", "", "", ""]],
    nrpnout: [4, 1, [""]],
    nslider: [2, 2, ["int", "int"]],
    number: [1, 2, ["", "bang"]],
    "number~": [2, 2, ["signal", "float"]],
    numkey: [1, 2, ["", ""]],
    offer: [2, 1, [""]],
    "omx.4band~": [2, 4, ["signal", "signal", "list", "list"]],
    "omx.5band~": [2, 4, ["signal", "signal", "list", "list"]],
    "omx.comp~": [2, 4, ["signal", "signal", "list", "list"]],
    "omx.peaklim~": [2, 4, ["signal", "signal", "list", "list"]],
    onebang: [2, 2, ["bang", "bang"]],
    "onepole~": [2, 1, ["signal"]],
    opendialog: [1, 2, ["", ""]],
    "osc.packet": [2, 1, [""]],
    "oscbank~": [4, 1, ["signal"]],
    "overdrive~": [2, 1, [""]],
    pack: [2, 1, [""]],
    pak: [2, 1, [""]],
    param: [1, 2, ["", ""]],
    "param.osc": [1, 1, [""]],
    paraminspector: [1, 2, ["", ""]],
    "pass~": [1, 1, ["signal"]],
    past: [1, 1, [""]],
    patcherargs: [1, 2, ["list", "list"]],
    pattr: [1, 3, ["", "", ""]],
    pattrforward: [1, 1, [""]],
    pattrhub: [1, 2, ["", ""]],
    pattrmarker: [1, 1, [""]],
    pattrstorage: [1, 1, [""]],
    pcontrol: [1, 1, [""]],
    peak: [2, 3, ["", "", ""]],
    "peakamp~": [2, 1, ["float"]],
    "peek~": [3, 1, [""]],
    pgmin: [1, 2, ["", ""]],
    "phasegroove~": [1, 1, ["signal"]],
    "phaseshift~": [3, 1, ["signal"]],
    "phasewrap~": [1, 1, [""]],
    "phasor~": [2, 1, ["signal"]],
    pictctrl: [1, 1, ["int"]],
    pictslider: [2, 2, ["int", "int"]],
    "pink~": [1, 1, ["signal"]],
    pipe: [2, 1, [""]],
    "pitchshift~": [2, 2, ["Signal", "Signal"]],
    playbar: [1, 2, ["", "int"]],
    "playlist~": [1, 5, ["signal", "signal", "signal", "", "dictionary"]],
    "play~": [1, 2, ["signal", "signal"]],
    "plot~": [1, 1, [""]],
    "plugin~": [2, 2, ["signal", "signal"]],
    "plugout~": [2, 2, ["signal", "signal"]],
    "plugphasor~": [1, 2, ["signal", "list"]],
    "plugreceive~": [1, 1, ["signal"]],
    "plugsync~": [1, 9, ["int", "int", "int", "double", "list", "double", "double", "int", "long"]],
    plus: [2, 1, [""]],
    "plusequals~": [2, 1, ["signal"]],
    "plus~": [2, 1, ["signal"]],
    "poke~": [3, 1, ["signal"]],
    poltocar: [2, 2, ["", ""]],
    "poltocar~": [2, 2, ["", ""]],
    poly: [2, 4, ["", "", "", ""]],
    "polybuffer~": [1, 2, ["", ""]],
    polyin: [1, 3, ["", "", ""]],
    pong: [3, 1, ["signal"]],
    "pong~": [3, 1, ["signal"]],
    pow: [2, 1, [""]],
    "pow~": [2, 1, ["signal"]],
    prepend: [1, 1, [""]],
    preset: [1, 5, ["", "", "", "", ""]],
    prob: [1, 2, ["", ""]],
    pv: [1, 1, [""]],
    pvar: [1, 1, [""]],
    qlim: [2, 1, [""]],
    qlist: [1, 3, ["", "", ""]],
    qmetro: [2, 1, [""]],
    quickthresh: [4, 1, [""]],
    radiogroup: [1, 1, [""]],
    "rampsmooth~": [3, 1, ["signal"]],
    "ramp~": [4, 2, ["signal", "signal"]],
    random: [2, 1, [""]],
    "rand~": [1, 1, ["signal"]],
    "rate~": [2, 1, ["signal"]],
    rdiv: [2, 1, [""]],
    "rdiv~": [2, 1, ["signal"]],
    receive: [1, 1, [""]],
    "receive~": [1, 1, ["signal"]],
    "record~": [3, 1, ["signal"]],
    "rect~": [3, 1, ["signal"]],
    regexp: [1, 5, ["", "", "", "", ""]],
    relativepath: [1, 1, [""]],
    repl: [2, 3, ["", "", ""]],
    "reson~": [4, 1, ["signal"]],
    "retune~": [3, 5, ["Signal", "Signal", "Signal", "Signal", "List"]],
    rminus: [2, 1, [""]],
    "rminus~": [2, 1, ["signal"]],
    round: [2, 1, [""]],
    "round~": [2, 1, ["signal"]],
    route: [2, 2, ["", ""]],
    routepass: [2, 2, ["", ""]],
    router: [2, 2, ["", ""]],
    rpnin: [1, 4, ["", "", "", ""]],
    rpnout: [4, 1, [""]],
    rslider: [2, 2, ["", ""]],
    rtin: [1, 1, [""]],
    "sah~": [2, 1, ["signal"]],
    "sampstoms~": [1, 2, ["signal", "double"]],
    "sash~": [3, 1, ["signal"]],
    savebang: [1, 1, [""]],
    savedialog: [1, 3, ["", "", ""]],
    "saw~": [2, 1, ["signal"]],
    scale: [6, 1, [""]],
    "scale~": [6, 1, ["signal"]],
    schedule: [1, 1, [""]],
    "scope~": [2, 0],
    screensize: [1, 2, ["list", "list"]],
    select: [2, 2, ["", ""]],
    "selector~": [2, 1, ["signal"]],
    seq: [1, 3, ["", "", ""]],
    "seq~": [1, 3, ["anything", "list", "symbol"]],
    serial: [1, 2, ["", ""]],
    setclock: [2, 1, [""]],
    "sfinfo~": [1, 6, ["", "", "", "", "", ""]],
    "sfizz~": [2, 2, ["", ""]],
    "sflist~": [1, 1, [""]],
    "sfplay~": [2, 2, ["signal", "signal"]],
    "sfrecord~": [1, 1, ["signal"]],
    "shape~": [1, 1, ["signal"]],
    shiftleft: [2, 1, [""]],
    shiftright: [2, 1, [""]],
    "sig~": [1, 1, ["signal"]],
    sin: [1, 1, [""]],
    sinh: [1, 1, [""]],
    "sinh~": [1, 1, [""]],
    "sinx~": [1, 1, [""]],
    slide: [3, 1, ["float"]],
    slider: [1, 1, [""]],
    "slide~": [3, 1, ["signal"]],
    "snapshot~": [2, 1, ["float"]],
    "snowfall~": [1, 1, ["signal"]],
    "spectroscope~": [2, 1, [""]],
    speedlim: [2, 1, [""]],
    spell: [1, 1, [""]],
    "spike~": [2, 1, ["double"]],
    split: [3, 2, ["", ""]],
    spray: [1, 2, ["", ""]],
    sprintf: [1, 1, [""]],
    sqrt: [1, 1, [""]],
    "sqrt~": [1, 1, ["signal"]],
    "stash~": [4, 2, ["signal", "signal"]],
    stepcounter: [1, 4, ["", "", "", ""]],
    "stepcounter~": [1, 4, ["signal", "signal", "signal", "signal"]],
    "stepdiv~": [1, 2, ["signal", "signal"]],
    "stepfun~": [2, 2, ["signal", "signal"]],
    "stretch~": [1, 2, ["", ""]],
    string: [2, 3, ["", "", ""]],
    "string.append": [3, 1, [""]],
    "string.bytes": [2, 1, [""]],
    "string.change": [2, 2, ["", ""]],
    "string.compare": [2, 1, [""]],
    "string.concat": [2, 1, [""]],
    "string.contains": [2, 1, [""]],
    "string.endswith": [2, 1, [""]],
    "string.frombytes": [2, 1, [""]],
    "string.fromsymlist": [1, 1, [""]],
    "string.fromutf8": [2, 1, [""]],
    "string.index": [2, 2, ["", ""]],
    "string.indexof": [2, 1, [""]],
    "string.iter": [1, 1, [""]],
    "string.length": [2, 1, [""]],
    "string.prepend": [3, 1, [""]],
    "string.regexp": [3, 5, ["", "", "", "", ""]],
    "string.remove": [3, 1, [""]],
    "string.replace": [3, 1, [""]],
    "string.replaceall": [3, 1, [""]],
    "string.reverse": [2, 1, [""]],
    "string.rotate": [2, 1, [""]],
    "string.slice": [2, 1, [""]],
    "string.split": [2, 2, ["", ""]],
    "string.sprintf": [2, 1, [""]],
    "string.startswith": [2, 1, [""]],
    "string.substring": [2, 1, [""]],
    "string.toarray": [2, 1, [""]],
    "string.tolist": [2, 1, [""]],
    "string.tolower": [1, 1, [""]],
    "string.tosymbol": [2, 1, [""]],
    "string.toupper": [1, 1, [""]],
    "string.trim": [2, 1, [""]],
    "string.trimend": [2, 1, [""]],
    "string.trimstart": [1, 1, [""]],
    "string.utf8": [1, 1, [""]],
    "string.withpass": [1, 1, [""]],
    stripnote: [2, 2, ["", ""]],
    strippath: [1, 2, ["", ""]],
    "stutter~": [3, 1, ["signal"]],
    "subdiv~": [1, 3, ["signal", "signal", "int"]],
    substitute: [2, 2, ["", ""]],
    suckah: [1, 1, [""]],
    suspend: [1, 1, [""]],
    sustain: [3, 2, ["", ""]],
    "svf~": [3, 4, ["signal", "signal", "signal", "signal"]],
    swap: [2, 2, ["", ""]],
    swatch: [3, 2, ["", ""]],
    "swing~": [1, 3, ["signal", "signal", "int"]],
    switch: [3, 1, [""]],
    sxformat: [1, 1, [""]],
    "sync~": [1, 3, ["", "", ""]],
    sysexin: [1, 1, [""]],
    tab: [1, 3, ["int", "", ""]],
    table: [2, 2, ["", ""]],
    "table~": [1, 1, ["signal"]],
    tan: [1, 1, [""]],
    tanh: [1, 1, [""]],
    "tanh~": [1, 1, [""]],
    "tanx~": [1, 1, [""]],
    "tapin~": [1, 1, [""]],
    "tapout~": [1, 1, ["signal"]],
    "techno~": [1, 3, ["signal", "signal", "signal"]],
    "teeth~": [6, 1, ["signal"]],
    tempo: [4, 1, [""]],
    text: [1, 3, ["", "", ""]],
    "text.codebox": [2, 3, ["", "", ""]],
    textbox: [1, 2, ["", ""]],
    textbutton: [1, 3, ["", "", "int"]],
    textedit: [1, 4, ["", "", "", ""]],
    themecolor: [1, 2, ["list", "list"]],
    thisobject: [1, 2, ["", "dictionary"]],
    thispatcher: [1, 2, ["", ""]],
    "thispoly~": [1, 3, ["", "", ""]],
    threadcheck: [1, 4, ["bang", "bang", "bang", "bang"]],
    thresh: [2, 1, [""]],
    "thresh~": [3, 1, ["signal"]],
    timepoint: [1, 1, [""]],
    timer: [2, 2, ["", ""]],
    times: [2, 1, [""]],
    "times~": [2, 1, ["Signal"]],
    togedge: [1, 2, ["", ""]],
    toggle: [1, 1, ["int"]],
    tosymbol: [1, 1, [""]],
    touchin: [1, 2, ["", ""]],
    "train~": [3, 2, ["signal", "signal"]],
    translate: [1, 1, [""]],
    transport: [2, 9, ["", "", "", "", "", "", "", "", ""]],
    "trapezoid~": [3, 1, ["signal"]],
    "triangle~": [2, 1, ["signal"]],
    trigger: [1, 2, ["", ""]],
    "tri~": [3, 1, ["signal"]],
    trough: [2, 3, ["", "", ""]],
    "trunc~": [1, 1, ["signal"]],
    "twist~": [2, 1, ["signal"]],
    "typeroute~": [1, 6, ["signal", "bang", "int", "float", "symbol", "list"]],
    ubutton: [1, 4, ["bang", "bang", "", "int"]],
    udpreceive: [1, 1, [""]],
    umenu: [1, 3, ["int", "", ""]],
    unjoin: [1, 3, ["", "", ""]],
    unpack: [1, 2, ["", ""]],
    "updown~": [1, 1, ["signal"]],
    urn: [2, 2, ["", ""]],
    uzi: [2, 3, ["", "", ""]],
    v8: [1, 1, [""]],
    "v8.codebox": [2, 1, [""]],
    v8ui: [1, 1, [""]],
    value: [1, 1, [""]],
    vdp: [3, 4, ["", "", "", ""]],
    "vectral~": [3, 1, ["signal"]],
    vexpr: [1, 1, [""]],
    vstscan: [1, 2, ["list", "list"]],
    "vst~": [2, 8, ["signal", "signal", "signal", "signal", "signal", "signal", "signal", "signal"]],
    "waveform~": [5, 6, ["float", "float", "float", "float", "list", ""]],
    "wave~": [3, 1, ["signal"]],
    "what~": [1, 2, ["signal", "int"]],
    when: [1, 2, ["", ""]],
    "where~": [1, 2, ["signal", "signal"]],
    xbendin: [1, 2, ["", ""]],
    xbendout: [2, 1, [""]],
    xctlin: [1, 3, ["", "", ""]],
    xctlout: [3, 1, [""]],
    xmidiin: [2, 1, [""]],
    xnotein: [1, 4, ["", "", "", ""]],
    xnoteout: [4, 1, [""]],
    "zerox~": [1, 2, ["signal", "signal"]],
    "zigzag~": [2, 4, ["signal", "signal", "signal", "signal"]],
    zl: [2, 2, ["inactive", "inactive"]],
    "zl.change": [2, 2, ["anything", "int"]],
    "zl.compare": [2, 2, ["int", "int/list"]],
    "zl.delace": [2, 2, ["anything", "anything"]],
    "zl.ecils": [2, 2, ["list", "list"]],
    "zl.filter": [2, 2, ["anything", "list"]],
    "zl.group": [2, 2, ["list", "inactive"]],
    "zl.indexmap": [2, 2, ["anything", "inactive"]],
    "zl.iter": [2, 2, ["list", "inactive"]],
    "zl.join": [2, 2, ["list", "inactive"]],
    "zl.lace": [2, 2, ["anything", "inactive"]],
    "zl.len": [2, 2, ["int", "inactive"]],
    "zl.lookup": [2, 2, ["anything", "inactive"]],
    "zl.median": [2, 2, ["int/float", "inactive"]],
    "zl.mth": [2, 2, ["anything", "list"]],
    "zl.nth": [2, 2, ["anything", "list"]],
    "zl.queue": [2, 2, ["anything", "int"]],
    "zl.reg": [2, 2, ["list", "inactive"]],
    "zl.rev": [2, 2, ["list", "inactive"]],
    "zl.rot": [2, 2, ["list", "inactive"]],
    "zl.scramble": [2, 2, ["anything", "list"]],
    "zl.sect": [2, 2, ["list", "bang"]],
    "zl.slice": [2, 2, ["list", "list"]],
    "zl.sort": [2, 2, ["anything", "list"]],
    "zl.stack": [2, 2, ["anything", "int"]],
    "zl.stream": [2, 2, ["anything", "int"]],
    "zl.sub": [2, 2, ["int", "int"]],
    "zl.sum": [2, 2, ["int/float", "inactive"]],
    "zl.swap": [2, 2, ["anything", "list"]],
    "zl.thin": [2, 2, ["anything", "inactive"]],
    "zl.union": [2, 2, ["list", "inactive"]],
    "zl.unique": [2, 2, ["anything", "inactive"]],
    zmap: [5, 1, [""]],
    "zplane~": [5, 4, ["list", "list", "list", "list"]]
  };
  function boxClassOf(objectClass) {
    return OWN_MAXCLASS.has(objectClass) ? objectClass : "newobj";
  }

  // src/serialize.ts
  var DERIVED = new Set([
    "id",
    "maxclass",
    "numinlets",
    "numoutlets",
    "patcher",
    "rect",
    "text"
  ]);
  var OPTIONAL = [
    "varname",
    "fontname",
    "fontsize",
    "fontface",
    "presentation",
    "presentation_rect",
    "hidden",
    "ignoreclick",
    "annotation",
    "hint",
    "linecount",
    "parameter_enable",
    "saved_attribute_attributes",
    "saved_object_attributes"
  ];
  function first(value) {
    return Array.isArray(value) && value.length === 1 ? value[0] : value;
  }
  function isSet(value) {
    if (value === undefined || value === null)
      return false;
    if (value === "" || value === 0)
      return false;
    if (Array.isArray(value) && value.length === 0)
      return false;
    return true;
  }
  function readBoxAttr(object, name) {
    try {
      const value = object.getboxattr(name);
      return value === null ? undefined : value;
    } catch {
      return;
    }
  }
  function asNumber(value) {
    const scalar = first(value);
    if (typeof scalar === "number" && Number.isFinite(scalar))
      return scalar;
    if (typeof scalar === "string" && scalar.trim() !== "") {
      const parsed = Number(scalar);
      if (Number.isFinite(parsed))
        return parsed;
    }
    return;
  }
  function asRect(value) {
    if (!Array.isArray(value) || value.length < 4)
      return;
    const numbers = value.slice(0, 4).map((v) => asNumber(v));
    if (numbers.some((n) => n === undefined))
      return;
    return numbers;
  }
  function isPlain(value) {
    const kind = typeof value;
    if (kind === "number" || kind === "string" || kind === "boolean")
      return true;
    if (Array.isArray(value)) {
      return value.every((item) => {
        const k = typeof item;
        return k === "number" || k === "string" || k === "boolean";
      });
    }
    return false;
  }
  function readObjectAttrs(object, box) {
    let names;
    let boxNames;
    try {
      names = object.getattrnames();
      boxNames = object.getboxattrnames();
    } catch {
      return {};
    }
    const isBoxAttr = new Set(boxNames);
    const saved = {};
    const already = box;
    for (const name of names) {
      if (isBoxAttr.has(name) || DERIVED.has(name) || name in already)
        continue;
      let value;
      try {
        value = first(object.getattr(name));
      } catch {
        continue;
      }
      if (!isSet(value) || !isPlain(value))
        continue;
      saved[name] = value;
    }
    return saved;
  }
  function patcherFontDefaults(target) {
    const defaults = {};
    for (const name of ["fontname", "fontsize", "fontface"]) {
      try {
        const value = first(target.getattr(`default_${name}`));
        if (value !== undefined && value !== null)
          defaults[name] = value;
      } catch {}
    }
    return defaults;
  }
  function describe(object, id, options, fontDefaults = {}) {
    const objectClass = object.maxclass ?? "";
    const maxclass = boxClassOf(objectClass);
    const text = object.boxtext;
    const ports = PORTS[objectClass];
    const numinlets = ports?.[0] ?? asNumber(readBoxAttr(object, "numinlets"));
    const numoutlets = ports?.[1] ?? asNumber(readBoxAttr(object, "numoutlets"));
    const patching_rect = asRect(readBoxAttr(object, "patching_rect")) ?? (Array.isArray(object.rect) ? fromMaxobjRect(object.rect) : undefined);
    const missing = [];
    if (objectClass === "")
      missing.push("maxclass");
    if (patching_rect === undefined)
      missing.push("patching_rect");
    if (maxclass === "newobj" && (text === undefined || text === "")) {
      missing.push("text");
    }
    if (missing.length > 0)
      return { missing, maxclass };
    const box = {
      id,
      maxclass,
      ...numinlets === undefined ? {} : { numinlets },
      ...numoutlets === undefined ? {} : { numoutlets },
      patching_rect
    };
    const outlettype = ports !== undefined && ports.length === 3 ? ports[2] : undefined;
    if (outlettype !== undefined)
      box.outlettype = [...outlettype];
    const names = options.allAttributes ? (() => {
      try {
        return object.getboxattrnames();
      } catch {
        return OPTIONAL;
      }
    })() : OPTIONAL;
    for (const name of names) {
      if (DERIVED.has(name))
        continue;
      const value = first(readBoxAttr(object, name));
      if (!isSet(value))
        continue;
      if (name in fontDefaults && value === fontDefaults[name])
        continue;
      box[name] = value;
    }
    if (text !== undefined && text !== "")
      box.text = text;
    if (options.objectAttributes === true) {
      const saved = readObjectAttrs(object, box);
      if (Object.keys(saved).length > 0)
        box.saved_object_attributes = saved;
    }
    return { box, missing, maxclass };
  }
  function serialize(target, options = {}) {
    let objects;
    if (options.only !== undefined) {
      objects = [...options.only].filter((o) => o.valid !== false);
    } else {
      objects = [];
      for (let object = target.firstobject;object !== null && object !== undefined; object = object.nextobject) {
        objects.push(object);
      }
    }
    const boxes = [];
    const incomplete = [];
    const ids = new Map;
    const fontDefaults = patcherFontDefaults(target);
    objects.forEach((object, index) => {
      const id = `obj-${index + 1}`;
      const { box, missing, maxclass } = describe(object, id, options, fontDefaults);
      if (box === undefined) {
        incomplete.push({ id, maxclass, missing });
        if (options.emitIncomplete !== true)
          return;
      }
      ids.set(object, id);
      if (box !== undefined)
        boxes.push({ box });
    });
    const lines = [];
    for (const object of objects) {
      for (const cord of object.patchcords.outputs) {
        const from = ids.get(cord.srcobject);
        const to = ids.get(cord.dstobject);
        if (from === undefined || to === undefined)
          continue;
        lines.push({
          patchline: {
            source: [from, cord.srcoutlet],
            destination: [to, cord.dstinlet]
          }
        });
      }
    }
    return {
      patcher: {
        fileversion: 1,
        appversion: { ...MAX_VERSION },
        classnamespace: "box",
        rect: options.rect ?? [85, 104, 640, 480],
        boxes,
        lines
      },
      incomplete
    };
  }

  // src/entry.v8.ts
  inlets = 1;
  outlets = 1;
  autowatch = 0;
  function contextOf(context) {
    const bound = context;
    if (bound?.patcher !== undefined)
      return bound;
    const global = globalThis;
    if (global.this?.patcher !== undefined)
      return global.this;
    throw new Error("js2max: no patcher handle -- this script must be loaded by a [v8] object");
  }
  function patcherOf(context) {
    return contextOf(context).patcher;
  }
  function selfBox(context) {
    return contextOf(context).box;
  }
  var DEMO_OFFSET = [0, 280];
  var built = [];
  var described = null;
  function basename(path) {
    const cut = Math.max(path.lastIndexOf("/"), path.lastIndexOf("\\"));
    return cut < 0 ? path : path.slice(cut + 1);
  }
  function report(result) {
    built = [...result.objects.values()];
    post(`js2max: created ${result.created} object(s), ` + `${result.connected} connection(s)
`);
    for (const skip of result.skipped) {
      error(`js2max: skipped ${skip.id} -- ${skip.reason}
`);
    }
    outlet(0, "done", result.created, result.connected, result.skipped.length);
  }
  function guard(action) {
    try {
      action();
    } catch (err) {
      error(`${String(err)}
`);
    }
  }
  function build(json) {
    const target = this;
    guard(() => {
      let parsed;
      try {
        parsed = JSON.parse(json);
      } catch (err) {
        error(`js2max: could not parse patch description -- ${String(err)}
`);
        return;
      }
      const patcher = parsed !== null && typeof parsed === "object" && "patcher" in parsed ? parsed.patcher : parsed;
      if (patcher === null || patcher === undefined || !Array.isArray(patcher.boxes)) {
        error(`js2max: patch description has no boxes
`);
        return;
      }
      described = patcher;
      report(instantiate(patcherOf(target), patcher));
    });
  }
  function demo() {
    const target = this;
    guard(() => {
      report(instantiate(patcherOf(target), demoPatch(), { offset: DEMO_OFFSET }));
    });
  }
  function synth() {
    const target = this;
    guard(() => {
      const description = synthPatch();
      described = description;
      report(instantiate(patcherOf(target), description, { offset: [0, 40] }));
    });
  }
  function save(path) {
    guard(() => {
      const description = described ?? synthPatch();
      writePatch(path, new LoadedPatcher(description));
      post(`js2max: wrote ${path} -- ${description.boxes.length} box(es), ` + `${description.lines.length} line(s), exact (no objects created)
`);
      outlet(0, "saved", description.boxes.length, description.lines.length);
    });
  }
  function clear2() {
    const target = this;
    guard(() => {
      const self = selfBox(target);
      const removed = remove(patcherOf(target), built, {
        keep: self === undefined ? [] : [self]
      });
      built = [];
      post(`js2max: removed ${removed} object(s)
`);
      outlet(0, "cleared", removed);
    });
  }
  function clearall() {
    const target = this;
    guard(() => {
      const self = selfBox(target);
      if (self === undefined) {
        error("js2max: clearall needs this.box to avoid deleting the [v8] object " + `itself; use clear to undo the last build instead
`);
        return;
      }
      const removed = clear(patcherOf(target), { keep: [self] });
      built = [];
      post(`js2max: removed ${removed} object(s)
`);
      outlet(0, "cleared", removed);
    });
  }
  function read(path) {
    const target = this;
    guard(() => {
      const loaded = readPatch(path);
      post(`js2max: read ${path}
`);
      report(instantiate(patcherOf(target), loaded.patcher, { offset: DEMO_OFFSET }));
    });
  }
  function write(path, ...modes) {
    const mode = new Set(modes);
    const target = this;
    guard(() => {
      const patcher = patcherOf(target);
      const own = basename(patcher.filepath ?? "");
      if (own !== "" && basename(path) === own && !mode.has("built")) {
        error(`js2max: refusing to write ${path} -- that is this patcher's own file. ` + `serialize() describes the whole patcher, so this would overwrite it ` + `with a copy of itself. Choose another name.
`);
        outlet(0, "error", "self");
        return;
      }
      if (mode.has("built") && built.length === 0) {
        error(`js2max: nothing built to write. Click "synth" (or "demo", or send ` + `"build <json>") before "write ${path} built", or drop the word ` + `"built" to serialize the whole patcher instead.
`);
        outlet(0, "error", "nothing-built");
        return;
      }
      const result = serialize(patcher, {
        objectAttributes: mode.has("full"),
        ...mode.has("built") ? { only: built } : {}
      });
      if (result.incomplete.length > 0) {
        for (const box of result.incomplete) {
          error(`js2max: cannot describe ${box.id} (${box.maxclass}) -- ` + `missing ${box.missing.join(", ")}
`);
        }
        if (!mode.has("partial")) {
          error(`js2max: refusing to write ${path}; ` + `send "write ${path} partial" to write the rest anyway
`);
          outlet(0, "error", "incomplete", result.incomplete.length);
          return;
        }
      }
      writeText(path, JSON.stringify({ patcher: result.patcher }, null, 4));
      post(`js2max: wrote ${path} -- ${result.patcher.boxes.length} box(es), ` + `${result.patcher.lines.length} line(s)` + `${mode.has("built") ? " (built objects only)" : ""}
`);
      outlet(0, "wrote", result.patcher.boxes.length, result.patcher.lines.length, result.incomplete.length);
    });
  }
  function probe() {
    const target = this;
    guard(() => {
      const patcher = patcherOf(target);
      let index = 0;
      for (let object = patcher.firstobject;object !== null && object !== undefined; object = object.nextobject) {
        index += 1;
        const names = (() => {
          try {
            return object.getboxattrnames();
          } catch (err) {
            return [`<getboxattrnames failed: ${String(err)}>`];
          }
        })();
        post(`js2max probe ${index}: maxclass=${object.maxclass} ` + `boxclass=${String(object.getboxattr("maxclass"))} ` + `boxtext=${JSON.stringify(object.boxtext)} ` + `numinlets=${String(object.getboxattr("numinlets"))} ` + `numoutlets=${String(object.getboxattr("numoutlets"))}
`);
        const objectAttrs = (() => {
          try {
            return object.getattrnames();
          } catch (err) {
            return [`<getattrnames failed: ${String(err)}>`];
          }
        })();
        const boxOnly = new Set(names);
        const objectOnly = objectAttrs.filter((n) => !boxOnly.has(n));
        post(`js2max probe ${index} boxattrs: ${names.join(" ")}
`);
        post(`js2max probe ${index} objattrs (beyond the box): ` + `${objectOnly.length === 0 ? "<none>" : objectOnly.join(" ")}
`);
        for (const name of objectOnly) {
          let value;
          try {
            value = object.getattr(name);
          } catch (err) {
            value = `<threw: ${String(err)}>`;
          }
          post(`js2max probe ${index}   ${name} = ${JSON.stringify(value) ?? String(value)}
`);
        }
      }
      outlet(0, "probed", index);
    });
  }
  function extract(path, match) {
    const target = this;
    const needle = match ?? "~";
    guard(() => {
      const patcher = patcherOf(target);
      const chosen = [];
      for (let object = patcher.firstobject;object !== null && object !== undefined; object = object.nextobject) {
        const text = object.boxtext ?? "";
        if (object.maxclass.indexOf(needle) >= 0 || text.indexOf(needle) >= 0) {
          chosen.push(object);
        }
      }
      if (chosen.length === 0) {
        error(`js2max: nothing in this patcher matches "${needle}"
`);
        outlet(0, "error", "no-match");
        return;
      }
      const result = serialize(patcher, { only: chosen });
      for (const box of result.incomplete) {
        error(`js2max: cannot describe ${box.id} (${box.maxclass}) -- ` + `missing ${box.missing.join(", ")}
`);
      }
      writeText(path, JSON.stringify({ patcher: result.patcher }, null, 4));
      post(`js2max: extracted ${result.patcher.boxes.length} of ${patcher.count} ` + `object(s) matching "${needle}" to ${path} -- ` + `${result.patcher.lines.length} cord(s)
`);
      outlet(0, "extracted", result.patcher.boxes.length, result.patcher.lines.length);
    });
  }
  function count() {
    const target = this;
    guard(() => {
      outlet(0, "count", patcherOf(target).count);
    });
  }
  Object.assign(globalThis, {
    build,
    clear: clear2,
    clearall,
    count,
    demo,
    extract,
    probe,
    read,
    save,
    synth,
    write
  });
})();
