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
import {
  STRUCTURAL,
  fromMaxobjRect,
  isPlain,
  objectsOf,
} from "./scripting.ts";

/**
 * Box attributes never copied verbatim: supplied from the class table, derived,
 * or the patcher's business rather than the box's.
 *
 * Almost exactly the set `instantiate` refuses to push back, and for the same
 * reason -- these are the box's structure, reached through their own accessors
 * -- so it is shared rather than restated, and the two directions cannot drift
 * apart on what counts as a box attribute.
 *
 * `varname` is the one genuine difference, and it is not an oversight in either
 * direction: building a box assigns it (`object.varname = ...`, no attribute
 * involved), while a `.maxpat` records it as an ordinary box key that this must
 * read back. Same name, two mechanisms.
 */
const DERIVED = new Set([...STRUCTURAL].filter((name) => name !== "varname"));

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
  /**
   * Cords not written, because an endpoint is not among the boxes written.
   *
   * Expected under `only`, where dropping the cords that leave the set is what
   * makes the extract self-contained, and after an `incomplete` box is left
   * out. Serializing a whole patcher, it is neither: every cord's endpoints are
   * in the set by construction, so a non-zero count means cords were lost.
   * Counted rather than assumed away -- endpoints are matched by object
   * identity, and the JS API does not promise that two reads of the same object
   * give the same wrapper (`snapshot` carries a `varname` fallback for exactly
   * this). If that assumption is ever wrong, this is what says so instead of a
   * patch quietly arriving with no connections in it.
   */
  unresolved: number;
}

/**
 * Describe one live object as a `.maxpat` box.
 *
 * Text comes from `boxtext` alone. There is no fallback because there is
 * nothing to fall back to: `text` is not a box attribute, so the legacy `js`
 * engine -- which lacks `boxtext` -- cannot serialize a patcher at all.
 */
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
 *
 * These are read to filter *and* written into the emitted patcher, and the two
 * are not separable. Filtering alone was a silent bug: a patcher defaulting to
 * 14pt had `fontsize: 14` dropped from every box as "unstyled" and no default
 * recorded to restore it, so the file reopened at Max's own 12pt -- every box
 * changed size, and nothing said so.
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

/**
 * Whether a box attribute matches the patcher default it is judged against.
 *
 * Compared as text, because the two come from different reads and Max is not
 * consistent about which returns `12` and which `"12"`. A box left at the
 * default that came back as a string would otherwise be written out as a
 * deliberate override.
 */
function matchesDefault(value: unknown, fallback: unknown): boolean {
  return value === fallback || String(value) === String(fallback);
}

/** The patcher-level font defaults, as the keys a `.maxpat` records them under. */
function defaultFontEntries(
  defaults: Record<string, unknown>,
): Partial<Pick<
  PatcherDict,
  "default_fontname" | "default_fontsize" | "default_fontface"
>> {
  const name = defaults["fontname"];
  const size = asNumber(defaults["fontsize"]);
  const face = asNumber(defaults["fontface"]);
  return {
    ...(size === undefined ? {} : { default_fontsize: size }),
    ...(face === undefined ? {} : { default_fontface: face }),
    ...(typeof name === "string" && name !== ""
      ? { default_fontname: name }
      : {}),
  };
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
    // Equal to the patcher default means unstyled: Max omits it, so do we --
    // and `serialize` records that default in the file, or this would drop the
    // font without preserving what it was equal to.
    if (name in fontDefaults && matchesDefault(value, fontDefaults[name])) {
      continue;
    }
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
    objects = objectsOf(target);
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
  let unresolved = 0;
  const inScope = new Set(objects);
  for (const object of objects) {
    // Cords arriving from outside the set are never seen by the pass below,
    // which walks outputs only -- correct for emitting each cord once, and a
    // blind spot for counting the ones that do not make it. Under `only` that
    // was half the boundary: dropping the oscillator counted the cord out of it
    // and not the cord into it.
    for (const cord of object.patchcords.inputs) {
      // Already accounted for by the outputs pass, whichever way it went.
      if (inScope.has(cord.srcobject)) continue;
      unresolved += 1;
    }
    for (const cord of object.patchcords.outputs) {
      const from = ids.get(cord.srcobject);
      const to = ids.get(cord.dstobject);
      // A cord to a box that was dropped would reference a missing id.
      if (from === undefined || to === undefined) {
        unresolved += 1;
        continue;
      }
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
      // The window geometry is deliberately not read back from the patcher.
      // `.maxpat` stores `rect` as `[x, y, w, h]` and the JS API's rects are
      // `[left, top, right, bottom]`; which convention a patcher attribute
      // answers in is not settled outside Max, and a wrong window rect is a
      // patch that opens the wrong size. `probe` now reports it, so the harness
      // can settle it. Until then, pass `rect` if you know it.
      rect: options.rect ?? [85, 104, 640, 480],
      // Written because they are what the box fonts above were filtered
      // against: a box equal to the default is omitted, so the default has to
      // be in the file for it to mean anything.
      ...defaultFontEntries(fontDefaults),
      boxes,
      lines,
    },
    incomplete,
    unresolved,
  };
}
