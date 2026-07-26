/**
 * The object model: Box, Patchline, Patcher.
 *
 * Deliberately thin. The Python package's equivalent is ~2,400 lines across
 * `core/`, most of it the `add_*` factory family; this spike keeps only what a
 * round-trip needs, because the question under test is whether *typing the
 * format* pays off, not whether the API can be reproduced.
 *
 * Note what is absent compared to the Python version: no `to_dict` walking
 * `vars(self)`, no `_remove_none_entries`, no `render()` pass to convert objects
 * into dicts. A `Box` here already *is* the wire shape, so serialization is
 * `JSON.stringify`.
 */

import type {
  BoxDict,
  BoxEntry,
  BoxProps,
  MaxPatchFile,
  PatcherDict,
  PatchlineDict,
  PatchlineEntry,
  Rect4,
} from "./format.ts";
import { APP_VERSION, PORTS, boxClassOf } from "./objects.ts";

/**
 * The Max version a written file declares.
 *
 * Generated from py2max's `MAX_VER_*` rather than restated here, where it was a
 * literal that would have gone stale the first time the Python side bumped.
 */
export const MAX_VERSION = APP_VERSION;

/** Default box geometry, matching the Python package's fallback. */
const DEFAULT_BOX: Rect4 = [0, 0, 66, 22];

/**
 * Port counts for a class the table does not know -- a third-party external.
 *
 * A `.maxpat` box must state both counts, so unlike {@link serialize} (which
 * omits them and lets Max derive them from the instantiated object) this has to
 * put something down. The commonest shape is the guess.
 */
const FALLBACK_PORTS: readonly [number, number] = [2, 1];

/**
 * The object class a box is keyed on, for the tables in `objects.ts`.
 *
 * The first word of the typed-in text -- `cycle~ 440` is a `cycle~` -- falling
 * back to an explicit `maxclass` for a UI box added with no text at all.
 */
function classNameOf(text: string, maxclass: string | undefined): string {
  const head = text.trim().split(/\s+/)[0];
  return head === undefined || head === "" ? (maxclass ?? "") : head;
}

export interface PatcherOptions {
  title?: string;
  classnamespace?: string;
  rect?: Rect4;
  /** Layout step between successive boxes; the spike has no layout manager. */
  spacing?: number;
}

export interface AddBoxOptions extends BoxProps {
  id?: string;
  maxclass?: string;
  numinlets?: number;
  numoutlets?: number;
  patching_rect?: Rect4;
}

/**
 * A patcher under construction, and the round-trip entry points.
 *
 * `fromJSON`/`toJSON` are the interesting pair: parsing keeps every key the
 * source file had (including ones this model does not know about, via the index
 * signature on the parsed value), and emitting writes back exactly what is
 * present. Nothing is seeded and then deleted again.
 */
export class Patcher {
  readonly boxes: BoxEntry[] = [];
  readonly lines: PatchlineEntry[] = [];

  private idCounter = 0;
  private readonly spacing: number;
  private readonly settings: Omit<PatcherDict, "boxes" | "lines">;

  constructor(options: PatcherOptions = {}) {
    this.spacing = options.spacing ?? 72;
    this.settings = {
      fileversion: 1,
      appversion: { ...MAX_VERSION },
      classnamespace: options.classnamespace ?? "box",
      rect: options.rect ?? [85, 104, 640, 480],
      ...(options.title === undefined ? {} : { title: options.title }),
    };
  }

  /** `obj-1`, `obj-2`, ... matching the Python package's numbering. */
  nextId(): string {
    this.idCounter += 1;
    return `obj-${this.idCounter}`;
  }

  /** Position for the next box, in a simple left-to-right run. */
  private nextRect(): Rect4 {
    const index = this.boxes.length;
    return [
      48 + (index % 8) * this.spacing,
      48 + Math.floor(index / 8) * this.spacing,
      DEFAULT_BOX[2],
      DEFAULT_BOX[3],
    ];
  }

  /**
   * Add a box.
   *
   * Every property in `options` is checked against {@link BoxProps}: a
   * misspelling such as `bgcolour` is a compile error here, where the Python
   * equivalent accepts it through `**kwds: Any` and writes it to the file.
   *
   * The box class and port counts are looked up from the object class, so
   * `p.add("ezdac~")` is a `maxclass: "ezdac~"` box with 2 inlets and no
   * outlets, and `p.add("mtof")` a `newobj` with one of each. That knowledge is
   * py2max's, exported into `objects.ts` for 1098 classes, and it was being
   * ignored here: every box got 2 inlets and 1 outlet regardless, so a caller
   * had to spell out what the table already knew and a caller who did not got a
   * box whose declared ports contradicted the object inside it.
   *
   * Anything given explicitly wins, including for a class the table does not
   * know -- there is no way to be right about a third-party external.
   */
  add(text: string, options: AddBoxOptions = {}): BoxDict {
    const { id, maxclass, numinlets, numoutlets, patching_rect, ...props } =
      options;
    const className = classNameOf(text, maxclass);
    const ports = PORTS[className];
    // Only alongside a derived `numoutlets`: an explicit count the table
    // disagrees with would leave the two describing different objects.
    const outlettype =
      numoutlets === undefined && ports !== undefined && ports.length === 3
        ? ports[2]
        : undefined;
    const box: BoxDict = {
      id: id ?? this.nextId(),
      maxclass: maxclass ?? boxClassOf(className),
      numinlets: numinlets ?? ports?.[0] ?? FALLBACK_PORTS[0],
      numoutlets: numoutlets ?? ports?.[1] ?? FALLBACK_PORTS[1],
      patching_rect: patching_rect ?? this.nextRect(),
      ...(text === "" ? {} : { text }),
      ...(outlettype === undefined ? {} : { outlettype: [...outlettype] }),
      ...props,
    };
    this.boxes.push({ box });
    return box;
  }

  /** Add a subpatcher box, returning the box and its nested patcher. */
  addSubpatcher(
    text: string,
    options: AddBoxOptions = {},
  ): { box: BoxDict; sub: Patcher } {
    const sub = new Patcher({ classnamespace: "box" });
    const box = this.add(text, { numinlets: 1, numoutlets: 1, ...options });
    box.patcher = sub.toPatcherDict();
    return { box, sub };
  }

  /** Connect `from`'s outlet to `to`'s inlet. */
  connect(from: BoxDict, to: BoxDict, outlet = 0, inlet = 0): PatchlineDict {
    const order = this.lines.filter(
      (l) => l.patchline.source[0] === from.id && l.patchline.destination[0] === to.id,
    ).length;
    const patchline: PatchlineDict = {
      source: [from.id, outlet],
      destination: [to.id, inlet],
      ...(order === 0 ? {} : { order }),
    };
    this.lines.push({ patchline });
    return patchline;
  }

  /** The patcher as it will be written. */
  toPatcherDict(): PatcherDict {
    return { ...this.settings, boxes: this.boxes, lines: this.lines };
  }

  toFile(): MaxPatchFile {
    return { patcher: this.toPatcherDict() };
  }

  /**
   * Serialize.
   *
   * No pre-pass: absent optionals are simply not present, so `JSON.stringify`
   * emits exactly the keys that were set.
   */
  toJSON(indent = 4): string {
    return JSON.stringify(this.toFile(), null, indent);
  }

  /**
   * Parse a `.maxpat` document, preserving every key it contains.
   *
   * Unknown keys survive because the parsed value keeps them: the types describe
   * what this model *understands*, not an allowlist of what may exist. That is
   * what makes a faithful round-trip possible without an escape hatch.
   */
  static fromFile(file: MaxPatchFile): LoadedPatcher {
    return new LoadedPatcher(file.patcher);
  }

  static parse(text: string): LoadedPatcher {
    return Patcher.fromFile(JSON.parse(text) as MaxPatchFile);
  }
}

/**
 * A patcher loaded from a file.
 *
 * Kept separate from {@link Patcher} because the two have genuinely different
 * contracts: a constructed patcher owns its settings and may seed defaults, a
 * loaded one must not invent keys the source did not have. Conflating them is
 * what produced the Python package's "delete the seeded defaults again" step.
 */
export class LoadedPatcher {
  constructor(readonly patcher: PatcherDict) {}

  get boxes(): BoxEntry[] {
    return this.patcher.boxes;
  }

  get lines(): PatchlineEntry[] {
    return this.patcher.lines;
  }

  /** Highest `obj-N` in the file, so edits after a load do not collide. */
  maxNumericId(): number {
    let max = 0;
    for (const entry of this.patcher.boxes) {
      const match = /^obj-(\d+)$/.exec(entry.box.id);
      if (match?.[1] !== undefined) {
        max = Math.max(max, Number.parseInt(match[1], 10));
      }
    }
    return max;
  }

  findById(id: string): BoxDict | undefined {
    return this.patcher.boxes.find((entry) => entry.box.id === id)?.box;
  }

  /** Every box in the tree, subpatchers included. */
  *walk(): Generator<BoxDict> {
    const visit = function* (p: PatcherDict): Generator<BoxDict> {
      for (const entry of p.boxes) {
        yield entry.box;
        if (entry.box.patcher) yield* visit(entry.box.patcher);
      }
    };
    yield* visit(this.patcher);
  }

  toFile(): MaxPatchFile {
    return { patcher: this.patcher };
  }

  toJSON(indent = 4): string {
    return JSON.stringify(this.toFile(), null, indent);
  }
}
