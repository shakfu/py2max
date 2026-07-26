/**
 * Serializing a live patcher back into a `.maxpat`.
 *
 * Two wrong theories preceded this, both settled by running `probe` in Max:
 *
 *   1. "read the object" -- `Maxobj.maxclass` for a `cycle~ 440` box, written
 *      straight into the file. Wrong: the file needs `maxclass: "newobj"` with
 *      the text alongside.
 *   2. "read the box attributes" -- `getboxattr("maxclass")`, `("numinlets")`,
 *      `("numoutlets")`. Also wrong: **all three return null.** They are not box
 *      attributes. `getboxattrnames()` lists colours, fonts, rects and `varname`
 *      -- never the class or the port counts.
 *
 * What Max does give, confirmed: `Maxobj.maxclass` (the *object* class, e.g.
 * `print`, `v8`, `comment`) and `Maxobj.boxtext` (the box's text). Those two are
 * enough, because the rest is static per class -- and py2max already knows it
 * from the maxref bundle, exported into `objects.ts`.
 *
 * So: the object class is the lookup key, `OWN_MAXCLASS` decides whether the box
 * keeps that class or is an object box, and `PORTS` supplies the counts.
 *
 * The rule this module keeps: **produce a valid patch or say precisely what is
 * missing.** Every box is validated before it is emitted, and one that cannot be
 * described lands in `incomplete` rather than being written out half-formed.
 * A `.maxpat` that Max silently refuses to open is worse than an error.
 */

import type {
  BoxDict,
  BoxEntry,
  PatcherDict,
  PatchlineEntry,
  Rect4,
} from "./format.ts";
import { MAX_VERSION } from "./model.ts";
import { PORTS, boxClassOf } from "./objects.ts";
import { fromMaxobjRect } from "./scripting.ts";

/**
 * Box attributes never copied verbatim: supplied from the class table, derived,
 * or the patcher's business rather than the box's.
 */
const DERIVED = new Set([
  "id",
  "maxclass",
  "numinlets",
  "numoutlets",
  "patcher",
  "rect",
  "text",
]);

/**
 * Box attributes carried over when set.
 *
 * Deliberately short. `getboxattr` answers for *every* attribute a box has,
 * including ones sitting at their defaults, and there is no way to ask which
 * those are -- so a wider list writes Max's own defaults back into the file.
 * Measured: including colours and fonts here added nine keys to every box and
 * took a 7 KB patch to 18 KB, none of which Max writes itself.
 *
 * `allAttributes` opts into everything `getboxattrnames()` reports, for when
 * verbosity is preferable to loss.
 */
const OPTIONAL = [
  "varname",
  // Fonts are included but filtered against the patcher's own defaults below:
  // writing them unconditionally puts Max's default on every box, while
  // dropping them loses a deliberate override.
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
  "saved_object_attributes",
];

function first(value: unknown): unknown {
  // Max attribute reads often come back wrapped in an array, even for scalars.
  return Array.isArray(value) && value.length === 1 ? value[0] : value;
}

/**
 * Whether an attribute value is worth writing.
 *
 * Max omits an attribute left at its default, and `0` / `""` / `[]` is the
 * default for most of the flags here (`hidden`, `presentation`, `ignoreclick`).
 * Writing them back is harmless but unfaithful, and it is what made a
 * round-tripped patch two and a half times the size of its source.
 */
function isSet(value: unknown): boolean {
  if (value === undefined || value === null) return false;
  if (value === "" || value === 0) return false;
  if (Array.isArray(value) && value.length === 0) return false;
  return true;
}

function readBoxAttr(object: Maxobj, name: string): unknown {
  try {
    const value = object.getboxattr(name);
    return value === null ? undefined : value;
  } catch {
    return undefined;
  }
}

function asNumber(value: unknown): number | undefined {
  const scalar = first(value);
  if (typeof scalar === "number" && Number.isFinite(scalar)) return scalar;
  if (typeof scalar === "string" && scalar.trim() !== "") {
    const parsed = Number(scalar);
    if (Number.isFinite(parsed)) return parsed;
  }
  return undefined;
}

function asRect(value: unknown): Rect4 | undefined {
  if (!Array.isArray(value) || value.length < 4) return undefined;
  const numbers = value.slice(0, 4).map((v) => asNumber(v));
  if (numbers.some((n) => n === undefined)) return undefined;
  return numbers as unknown as Rect4;
}

export interface IncompleteBox {
  /** The id this box would have had. */
  id: string;
  maxclass: string;
  /** Which required pieces could not be read. */
  missing: string[];
}

export interface SerializeOptions {
  /**
   * Copy every attribute `getboxattrnames()` reports, not just the curated set.
   *
   * More faithful and much more verbose: Max omits attributes sitting at their
   * defaults, and this cannot tell which those are.
   */
  allAttributes?: boolean;
  /** Patcher window rect for the emitted file. */
  rect?: Rect4;
  /** Emit boxes that failed validation anyway. Off, deliberately. */
  emitIncomplete?: boolean;
  /**
   * Serialize only these objects, rather than everything in the patcher.
   *
   * The difference between "save this patcher" and "export what I built". A
   * script that builds an instrument into a host patch wants the instrument on
   * its own -- not wrapped in the `[v8]` box and message boxes that built it.
   * Cords are kept only where both ends are in the set, so the result is
   * self-contained.
   */
  only?: readonly Maxobj[];
  /**
   * Also read the *object's* attributes and record them under
   * `saved_object_attributes`.
   *
   * Off by default, and not merely for size. `getattrnames()` reports every
   * attribute the object has, at whatever value it holds, with no way to ask
   * which are defaults -- so this writes a great many keys Max would omit. It
   * captures what an object box holds beyond its box -- `print`'s `level` and
   * `popup`, a `[v8]` box's `embed`. It does **not** recover `filename` or
   * `textfile`: those are absent from `getattrnames()` entirely, so they are
   * bookkeeping Max writes on save rather than state anything can read back.
   */
  objectAttributes?: boolean;
}

export interface SerializeResult {
  patcher: PatcherDict;
  /** Boxes left out because they could not be described. Empty means faithful. */
  incomplete: IncompleteBox[];
}

/**
 * Describe one live object as a `.maxpat` box.
 *
 * Text comes from `boxtext` alone. There is no fallback because there is
 * nothing to fall back to: `text` is not a box attribute, so the legacy `js`
 * engine -- which lacks `boxtext` -- cannot serialize a patcher at all.
 */
/**
 * Whether a value is plain data a `.maxpat` can hold.
 *
 * Attributes do not all return data. Reading `textfile` on a `[v8]` box hands
 * back a Max object the JS bridge cannot wrap, and logs
 * `v8_wrapobject: couldn't wrap instance of class textfile` to the console for
 * the attempt. Anything that is not a number, string, boolean or a flat array
 * of those is skipped.
 */
function isPlain(value: unknown): boolean {
  const kind = typeof value;
  if (kind === "number" || kind === "string" || kind === "boolean") return true;
  if (Array.isArray(value)) {
    return value.every((item) => {
      const k = typeof item;
      return k === "number" || k === "string" || k === "boolean";
    });
  }
  return false;
}

/**
 * The object's own attributes, as distinct from the box's.
 *
 * Only attributes `getattrnames()` reports that `getboxattrnames()` does *not*
 * -- which is the whole point, and was measured. For a UI box the two lists are
 * identical, because there the box and the object are one thing: a comment
 * reports the same 33 names either way, so reading both would write every box
 * attribute a second time under `saved_object_attributes`. Only object boxes
 * have anything of their own, and it is exactly what you would want:
 *
 *     print   bettersymquotes deltatime floatprecision level popup time
 *     v8      annotation_name embed parameter_enable parameter_mappable
 */
function readObjectAttrs(
  object: Maxobj,
  box: BoxDict,
): Record<string, unknown> {
  let names: string[];
  let boxNames: string[];
  try {
    names = object.getattrnames();
    boxNames = object.getboxattrnames();
  } catch {
    return {};
  }

  const isBoxAttr = new Set(boxNames);
  const saved: Record<string, unknown> = {};
  const already = box as unknown as Record<string, unknown>;
  for (const name of names) {
    if (isBoxAttr.has(name) || DERIVED.has(name) || name in already) continue;
    let value: unknown;
    try {
      value = first(object.getattr(name));
    } catch {
      continue;
    }
    if (!isSet(value) || !isPlain(value)) continue;
    saved[name] = value;
  }
  return saved;
}

/**
 * The patcher's own font defaults, against which a box's fonts are judged.
 *
 * A `.maxpat` records `default_fontsize` / `default_fontname` / `default_fontface`,
 * and Max omits a box attribute equal to the patcher default. That is the only
 * principled way to tell "this box was styled" from "this box is normal" --
 * without it, including fonts writes Max's defaults onto every box, and
 * excluding them loses a comment someone deliberately set to 14pt.
 */
function patcherFontDefaults(target: MaxPatcher): Record<string, unknown> {
  const defaults: Record<string, unknown> = {};
  for (const name of ["fontname", "fontsize", "fontface"]) {
    try {
      const value = first(target.getattr(`default_${name}`));
      if (value !== undefined && value !== null) defaults[name] = value;
    } catch {
      // A host without patcher attributes just gets no filtering.
    }
  }
  return defaults;
}

function describe(
  object: Maxobj,
  id: string,
  options: SerializeOptions,
  fontDefaults: Record<string, unknown> = {},
): { box?: BoxDict; missing: string[]; maxclass: string } {
  // `Maxobj.maxclass` is the *object* class -- "print", "v8", "cycle~",
  // "comment". It is the key into the class table, and decides whether the box
  // keeps that class or is written as a `newobj` carrying its text.
  const objectClass = object.maxclass ?? "";
  const maxclass = boxClassOf(objectClass);
  // `boxtext` is the only source: the probe showed `text` is not among the
  // names `getboxattrnames()` reports, so there is no attribute to fall back
  // to. `boxtext` is documented v8-only, which is what js2max targets.
  const text = object.boxtext;

  const ports = PORTS[objectClass];
  const numinlets =
    ports?.[0] ?? asNumber(readBoxAttr(object, "numinlets"));
  const numoutlets =
    ports?.[1] ?? asNumber(readBoxAttr(object, "numoutlets"));

  const patching_rect =
    asRect(readBoxAttr(object, "patching_rect")) ??
    (Array.isArray(object.rect) ? fromMaxobjRect(object.rect) : undefined);

  const missing: string[] = [];
  if (objectClass === "") missing.push("maxclass");
  if (patching_rect === undefined) missing.push("patching_rect");
  // An object box without its text reopens empty -- silent data loss rather
  // than a load failure, so it counts as missing.
  if (maxclass === "newobj" && (text === undefined || text === "")) {
    missing.push("text");
  }

  if (missing.length > 0) return { missing, maxclass };

  const box: BoxDict = {
    id,
    maxclass,
    // An unknown class (a third-party external) has no table entry. Max derives
    // ports from the instantiated object anyway, so omitting is better than
    // guessing a count that would silently drop patchcords on load.
    ...(numinlets === undefined ? {} : { numinlets }),
    ...(numoutlets === undefined ? {} : { numoutlets }),
    patching_rect: patching_rect as Rect4,
  } as BoxDict;

  const outlettype = ports !== undefined && ports.length === 3 ? ports[2] : undefined;
  if (outlettype !== undefined) box.outlettype = [...outlettype];

  const names = options.allAttributes
    ? (() => {
        try {
          return object.getboxattrnames();
        } catch {
          return OPTIONAL;
        }
      })()
    : OPTIONAL;

  for (const name of names) {
    if (DERIVED.has(name)) continue;
    const value = first(readBoxAttr(object, name));
    if (!isSet(value)) continue;
    // Equal to the patcher default means unstyled: Max omits it, so do we.
    if (name in fontDefaults && value === fontDefaults[name]) continue;
    (box as unknown as Record<string, unknown>)[name] = value;
  }

  if (text !== undefined && text !== "") box.text = text;

  if (options.objectAttributes === true) {
    const saved = readObjectAttrs(object, box);
    if (Object.keys(saved).length > 0) box.saved_object_attributes = saved;
  }

  return { box, missing, maxclass };
}

/**
 * Serialize a live patcher.
 *
 * Ids are assigned positionally (`obj-1`, `obj-2`, ...) rather than taken from
 * `varname`, so the emitted file matches Max's own convention and a box keeps
 * its `varname` as a separate attribute.
 */
export function serialize(
  target: MaxPatcher,
  options: SerializeOptions = {},
): SerializeResult {
  let objects: Maxobj[];
  if (options.only !== undefined) {
    // Skip handles whose object has since been removed: `valid` goes false and
    // reading attributes off a freed object is how the console fills with
    // `bad object`.
    objects = [...options.only].filter((o) => o.valid !== false);
  } else {
    objects = [];
    for (
      let object = target.firstobject;
      object !== null && object !== undefined;
      object = object.nextobject
    ) {
      objects.push(object);
    }
  }

  const boxes: BoxEntry[] = [];
  const incomplete: IncompleteBox[] = [];
  const ids = new Map<Maxobj, string>();
  const fontDefaults = patcherFontDefaults(target);

  objects.forEach((object, index) => {
    const id = `obj-${index + 1}`;
    const { box, missing, maxclass } = describe(object, id, options, fontDefaults);
    if (box === undefined) {
      incomplete.push({ id, maxclass, missing });
      if (options.emitIncomplete !== true) return;
    }
    ids.set(object, id);
    if (box !== undefined) boxes.push({ box });
  });

  const lines: PatchlineEntry[] = [];
  for (const object of objects) {
    for (const cord of object.patchcords.outputs) {
      const from = ids.get(cord.srcobject);
      const to = ids.get(cord.dstobject);
      // A cord to a box that was dropped would reference a missing id.
      if (from === undefined || to === undefined) continue;
      lines.push({
        patchline: {
          source: [from, cord.srcoutlet],
          destination: [to, cord.dstinlet],
        },
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
      lines,
    },
    incomplete,
  };
}
