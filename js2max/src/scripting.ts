/**
 * The bridge: turn a patch *description* into live Max objects.
 *
 * This is the one thing the Python package cannot do. py2max writes `.maxpat`
 * files that Max later opens; a `v8` script runs *inside* an open patcher and
 * can build it in place. Both directions share the format types in
 * `format.ts`, so the same description round-trips through a file or through
 * `this.patcher` without a second vocabulary.
 *
 * The target patcher is passed in rather than read from `this.patcher`, which
 * is what makes any of this testable: the tests drive it with a mock host that
 * records calls, so the mapping logic is checked without Max present.
 *
 * Both directions work. Model -> live is `newdefault` / `connect`; live ->
 * model is {@link snapshot}, which reads objects from the patcher's list and
 * connections from `Maxobj.patchcords`. An earlier version of this file claimed
 * connections could not be enumerated and cut the reverse direction down to
 * boxes only -- that was simply wrong, and the correction is why `snapshot`
 * returns lines.
 *
 * What live -> model still cannot recover is the *file's* content rather than
 * the patcher's structure: a live object exposes its class, name, position and
 * cords, but not the typed-in text or the per-class attributes a `.maxpat`
 * records. Use the file when you need those.
 */

import type { BoxDict, PatcherDict, PatchlineDict, Rect4 } from "./format.ts";

/** Box classes whose content is set with a `set` message, not typed-in args. */
const SET_CONTENT_CLASSES = new Set(["message", "comment"]);

/** Box classes that are their own class name, with no `text` to parse. */
function classNameOf(box: BoxDict): string {
  if (box.maxclass !== "newobj") return box.maxclass;
  const text = box.text ?? "";
  const head = text.trim().split(/\s+/)[0];
  return head === undefined || head === "" ? "newobj" : head;
}

/**
 * Typed-in arguments for a `newobj` box: everything after the class name.
 *
 * Numeric-looking tokens become numbers because Max distinguishes the symbol
 * `440` from the int `440` when it reaches an object's argument list.
 */
function typedArgsOf(box: BoxDict): (string | number)[] {
  if (box.maxclass !== "newobj") return [];
  const tokens = (box.text ?? "").trim().split(/\s+/).slice(1);
  return tokens
    .filter((token) => token !== "")
    .map((token) => {
      const asNumber = Number(token);
      return Number.isFinite(asNumber) && token !== "" ? asNumber : token;
    });
}

/**
 * Max's two rectangle conventions, which are not the same and are easy to
 * confuse: a box's `patching_rect` in the file is `[x, y, width, height]`,
 * while `Maxobj.rect` is `[left, top, right, bottom]`.
 */
export function toMaxobjRect(
  rect: Rect4,
): [number, number, number, number] {
  const [x, y, w, h] = rect;
  return [x, y, x + w, y + h];
}

export function fromMaxobjRect(
  rect: readonly [number, number, number, number],
): Rect4 {
  const [left, top, right, bottom] = rect;
  return [left, top, right - left, bottom - top];
}

export interface SkippedBox {
  id: string;
  reason: string;
}

export interface InstantiateResult {
  /** Model box id -> the live object created for it. */
  readonly objects: ReadonlyMap<string, Maxobj>;
  readonly created: number;
  readonly connected: number;
  /** Boxes and lines that could not be built, with why. Never throws for these. */
  readonly skipped: readonly SkippedBox[];
}

export interface InstantiateOptions {
  /**
   * Name every created object after its model id when it has no `varname`, so
   * `patcher.getnamed("obj-3")` finds it afterwards. On by default: without it
   * a script cannot address what it just built.
   */
  nameById?: boolean;
  /** Resize each object to its `patching_rect`. On by default. */
  applyRects?: boolean;
  /** Recurse into subpatcher boxes that carry a nested `patcher`. On by default. */
  buildSubpatchers?: boolean;
  /** Offset every position, for building into a region of an existing patcher. */
  offset?: readonly [number, number];
}

/**
 * Build `source` inside `target`.
 *
 * Failures are collected rather than thrown: a patch description is data, often
 * from a file, and one unknown object class should not abandon a half-built
 * patcher. Callers decide what an empty `skipped` list is worth.
 */
export function instantiate(
  target: MaxPatcher,
  source: PatcherDict,
  options: InstantiateOptions = {},
): InstantiateResult {
  const {
    nameById = true,
    applyRects = true,
    buildSubpatchers = true,
    offset = [0, 0],
  } = options;
  const [dx, dy] = offset;

  const objects = new Map<string, Maxobj>();
  const skipped: SkippedBox[] = [];
  let created = 0;
  let connected = 0;

  for (const entry of source.boxes) {
    const box = entry.box;
    const [x, y, w, h] = box.patching_rect;
    const className = classNameOf(box);

    let object: Maxobj | null = null;
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
      // A message or comment carries its content as text rather than as
      // typed-in arguments; `set` fills it without triggering output.
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
          reason: "box carries a nested patcher but exposes no subpatcher()",
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
        reason: "patchline references a box that was not created",
      });
      continue;
    }
    try {
      // A hidden cord is a different call, not a property set afterwards.
      const wire = hidden ? target.hiddenconnect : target.connect;
      wire.call(target, fromObject, from[1], toObject, to[1]);
      connected += 1;
    } catch (err) {
      skipped.push({
        id: `${from[0]}->${to[0]}`,
        reason: `connect threw: ${String(err)}`,
      });
    }
  }

  return { objects, created, connected, skipped };
}

export interface ClearOptions {
  /**
   * Objects to leave alone. **A script must pass its own box here.**
   *
   * Removing the object that hosts the running script does not fail cleanly:
   * Max frees it, execution continues against the freed pointer, and the next
   * `post()` or `outlet()` reports `bad object` / `typedmess: post: corrupt
   * object` / `doesn't understand "post"`. Verified in Max, which is how this
   * option came to exist.
   */
  keep?: readonly Maxobj[];
}

/**
 * Remove every object in a patcher, except those in `keep`.
 *
 * Collects first, then removes: mutating the object list while walking it with
 * `nextobject` is how you lose half of them.
 */
export function clear(target: MaxPatcher, options: ClearOptions = {}): number {
  const keep = options.keep ?? [];
  const doomed: Maxobj[] = [];
  for (
    let object = target.firstobject;
    object !== null && object !== undefined;
    object = object.nextobject
  ) {
    if (!keep.includes(object)) doomed.push(object);
  }
  for (const object of doomed) target.remove(object);
  return doomed.length;
}

/**
 * Remove a specific set of objects -- what `instantiate` just created, say.
 *
 * Safer and usually more useful than {@link clear}: it undoes a build without
 * touching what was in the patcher beforehand, including the script's own box.
 * Objects in `keep` are skipped, so a caller that has accidentally included its
 * own box still cannot delete itself.
 */
export function remove(
  target: MaxPatcher,
  objects: Iterable<Maxobj>,
  options: ClearOptions = {},
): number {
  const keep = options.keep ?? [];
  let removed = 0;
  for (const object of [...objects]) {
    if (keep.includes(object)) continue;
    target.remove(object);
    removed += 1;
  }
  return removed;
}

/** Every object in a patcher, in list order. */
function objectsOf(target: MaxPatcher): Maxobj[] {
  const objects: Maxobj[] = [];
  for (
    let object = target.firstobject;
    object !== null && object !== undefined;
    object = object.nextobject
  ) {
    objects.push(object);
  }
  return objects;
}

/**
 * What a live object can tell you about itself.
 *
 * Deliberately **not** a `BoxDict`. Converting one to a `.maxpat` box was tried
 * and produced files Max would not load, because three things a box needs are
 * not reachable from a live object:
 *
 *   - **the box class.** `Maxobj.maxclass` is the *instantiated* class, so a
 *     `cycle~ 440` object box reports `cycle~`, where the file needs
 *     `maxclass: "newobj"` with `text: "cycle~ 440"`.
 *   - **the typed-in text**, which has no accessor at all.
 *   - **`numinlets` / `numoutlets`**, likewise -- and a patchline referencing a
 *     port the box does not declare is dropped on load.
 *
 * So this type describes the patcher, and cannot be serialized as one. Build a
 * {@link Patcher} and use `writePatch` when you want a file.
 */
export interface SnapshotBox {
  id: string;
  /** The *instantiated* class, not the file's `maxclass`. See above. */
  maxclass: string;
  patching_rect: Rect4;
  varname?: string;
}

/**
 * Read a live patcher back into boxes *and* connections.
 *
 * Connections come from `Maxobj.patchcords`, which exposes `inputs` and
 * `outputs` arrays of `MaxobjConnection`. Only `outputs` is walked: every cord
 * appears in both its source's outputs and its destination's inputs, so reading
 * one side visits each exactly once.
 *
 * Endpoints are matched by object identity first, falling back to `varname`
 * when a handle does not compare equal -- the API does not promise that two
 * reads of the same object yield the same JavaScript wrapper. A cord whose ends
 * cannot be resolved is dropped rather than emitted with a wrong id.
 *
 * The result describes the patcher; it is **not** convertible to a `.maxpat`.
 * See {@link SnapshotBox} for exactly which three pieces are missing and why.
 */
export function snapshot(target: MaxPatcher): {
  boxes: SnapshotBox[];
  lines: PatchlineDict[];
  /** Cords whose endpoints could not be resolved to a box. */
  unresolved: number;
} {
  const objects = objectsOf(target);

  const ids = new Map<Maxobj, string>();
  const byVarname = new Map<string, string>();
  const boxes = objects.map((object, index) => {
    const id = object.varname === "" ? `obj-${index + 1}` : object.varname;
    ids.set(object, id);
    if (object.varname !== "") byVarname.set(object.varname, id);
    return {
      id,
      maxclass: object.maxclass,
      patching_rect: fromMaxobjRect(object.rect),
      ...(object.varname === "" ? {} : { varname: object.varname }),
    };
  });

  const identify = (object: Maxobj): string | undefined =>
    ids.get(object) ??
    (object.varname === "" ? undefined : byVarname.get(object.varname));

  const lines: PatchlineDict[] = [];
  let unresolved = 0;
  for (const object of objects) {
    for (const cord of object.patchcords.outputs) {
      const from = identify(cord.srcobject);
      const to = identify(cord.dstobject);
      if (from === undefined || to === undefined) {
        unresolved += 1;
        continue;
      }
      lines.push({
        source: [from, cord.srcoutlet],
        destination: [to, cord.dstinlet],
      });
    }
  }

  return { boxes, lines, unresolved };
}
