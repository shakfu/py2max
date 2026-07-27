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

/**
 * The class Max instantiates in place of one it cannot find.
 *
 * Established by running `diagnose` in Max, and it is the reason unknown object
 * classes went undetected for as long as they did. `newdefault` does **not**
 * return null for a class Max does not have: it logs `<name>: No such object`
 * to the console and hands back a real box whose `maxclass` is `jbogus` -- the
 * dashed-border placeholder you get by typing a bad name into a patcher. Every
 * other field looks healthy (`valid` is 1, `boxtext` is the text asked for), so
 * nothing short of the class name gives it away.
 *
 * The obvious alternative test -- does `maxclass` equal the class we asked for
 * -- is wrong, and the same run proved it: Max resolves aliases, so `t b i`
 * comes back as `trigger` and would read as broken.
 */
const BOGUS_CLASS = "jbogus";

/**
 * Names of the attributes an object or its box has, or none.
 *
 * `getattrnames()` **returns null** for some objects -- `trigger` and `jbogus`
 * both do, observed in Max -- rather than an empty array or an error. Calling it
 * inside a `try` is not enough, because there is nothing to catch: the null
 * comes back cleanly and the `TypeError` happens later, wherever the result is
 * first treated as an array. That is a crash in the caller, several frames from
 * the cause.
 */
export function attrNamesOf(read: () => string[] | null | undefined): string[] {
  let names: string[] | null | undefined;
  try {
    names = read();
  } catch {
    return [];
  }
  return Array.isArray(names) ? names : [];
}

/**
 * Max's message separators, which a `set` message cannot carry.
 *
 * In a `.maxpat` a message box's `text` may hold several messages -- `1, 2` is
 * two of them, `bang; foo bar` sends to a receive. Those are `A_COMMA` and
 * `A_SEMI` atoms in Max, and nothing the JS API offers produces one: an
 * argument to `message()` is a number or a symbol, so a `,` arrives as the
 * *symbol* `,`. The box is still created; what it holds is reported instead of
 * being passed off as faithful.
 */
const SEPARATORS = /[,;]/;

/** Box classes that are their own class name, with no `text` to parse. */
function classNameOf(box: BoxDict): string {
  if (box.maxclass !== "newobj") return box.maxclass;
  const text = box.text ?? "";
  const head = text.trim().split(/\s+/)[0];
  return head === undefined || head === "" ? "newobj" : head;
}

/**
 * A number, if the token is one Max would read as a number, else the symbol.
 *
 * The distinction is real: Max treats the symbol `440` and the int `440` as
 * different atoms, and an object's argument list is parsed accordingly.
 *
 * The pattern is deliberately narrower than `Number()`, which also accepts
 * forms Max does not read as numbers and would silently rewrite: `0x10` would
 * become 16, `1e3` 1000, `Infinity` a float. Those stay symbols, which is what
 * a box typed with them contains.
 */
function atomOf(token: string): string | number {
  if (!/^[+-]?(?:\d+\.?\d*|\.\d+)$/.test(token)) return token;
  const value = Number(token);
  return Number.isFinite(value) ? value : token;
}

/**
 * Box text as the atoms Max would parse from it.
 *
 * One tokenizer for both directions -- typed-in arguments and message/comment
 * content. They were separate, and had drifted: arguments were coerced while
 * `set` content was passed through as symbols, so a message box `1 2 3` was
 * built holding three symbols where the file said three ints.
 */
function atomsOf(text: string): (string | number)[] {
  return text
    .trim()
    .split(/\s+/)
    .filter((token) => token !== "")
    .map(atomOf);
}

/**
 * The arguments to hand `newdefault` for this box: everything after the class
 * name. `cycle~ 440` is the class `cycle~` with the argument `440`.
 */
function creationArgsOf(box: BoxDict): (string | number)[] {
  if (box.maxclass === "newobj") return atomsOf(box.text ?? "").slice(1);
  return [];
}

/**
 * Create a box, by whichever call actually gives it its content.
 *
 * `newdefault` builds every kind of box, and cannot give a message box its
 * text. Four routes were tried in Max and all four failed: `set` with separate
 * atoms, `set` with one symbol, the content as `newdefault` arguments, and
 * `setboxattr("text", ...)`. The box came out real -- its attribute list
 * matches a file-loaded message box exactly -- and empty, and the box did not
 * even resize, which a message box does to fit its contents.
 *
 * `newobject` is a different call rather than a different argument: it takes
 * the box's parameters explicitly, the way a `.maxpat` describes one. Two
 * shapes were tried and together they decode the signature:
 *
 *     newobject("message", 24, 720, 1, 2, 3)          boxtext "3"
 *     newobject("message", 24, 752, 100, 0, "1 2 3")  boxtext "\"1 2 3\""
 *
 * The first consumed `1` and `2` as width and font size and left `3` as the
 * text; the second took the content as one symbol, which Max quoted because it
 * contains spaces. So the signature is
 * `(class, left, top, width, fontsize, ...text atoms)`, and the atoms must be
 * passed separately -- handing it `"1 2 3"` produces a box containing the
 * literal string with quotes, not three atoms.
 *
 * A font size of `0` means the patcher default; an explicit `fontsize` in the
 * description is applied afterwards with the rest of the box attributes.
 */
function createBox(
  target: MaxPatcher,
  box: BoxDict,
  className: string,
  left: number,
  top: number,
): Maxobj | null | undefined {
  // Both content-carrying box classes go this way. Message boxes were fixed
  // first and confirmed in Max (`verify` check 1 reads back `"1 2 3"`);
  // comments followed, on the same signature, and `verify` check 5 is there to
  // hold that to the same standard rather than assuming it.
  if (SET_CONTENT_CLASSES.has(box.maxclass)) {
    return target.newobject(
      className,
      left,
      top,
      box.patching_rect[2],
      0,
      ...atomsOf(box.text ?? ""),
    );
  }
  return target.newdefault(left, top, className, ...creationArgsOf(box));
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

/**
 * Box keys that are the box's *structure*, not attributes to be pushed back.
 *
 * Every one of these is either established when the object is created
 * (`maxclass` and `text` decide what it is, the port counts follow from that),
 * applied through its own accessor (`patching_rect` via `rect`, `varname`
 * directly), a nested document (`patcher`), or Max's own save bookkeeping
 * (`saved_*`). A probe in Max settled the first group for good: `getboxattr`
 * returns null for `maxclass`, `numinlets`, `numoutlets` and `text`, because
 * they are not box attributes at all -- so setting them is not merely redundant,
 * there is nothing to set.
 *
 * Shared with `serialize.ts`, which must not read back out what this does not
 * write in. The two lists were separate and the same knowledge.
 */
export const STRUCTURAL: ReadonlySet<string> = new Set([
  "id",
  "maxclass",
  "numinlets",
  "numoutlets",
  "outlettype",
  "patcher",
  "patching_rect",
  "rect",
  "text",
  "varname",
  "saved_attribute_attributes",
  "saved_object_attributes",
]);

/**
 * Whether a value is plain data a `.maxpat` can hold, and Max can be handed.
 *
 * Attributes do not all carry data. Reading `textfile` on a `[v8]` box hands
 * back a Max object the JS bridge cannot wrap, and logs `v8_wrapobject:
 * couldn't wrap instance of class textfile` for the attempt. Anything that is
 * not a number, string, boolean or a flat array of those is left alone, in both
 * directions.
 */
export function isPlain(value: unknown): boolean {
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
 * Push a description's box attributes onto the object just created for it.
 *
 * The asymmetry this closes: `serialize` works to preserve `bgcolor`,
 * `fontsize`, `presentation` and the rest, and `instantiate` used to apply the
 * rect and the varname and drop everything else -- so a patch that went file ->
 * live -> file arrived stripped of its appearance, for reasons that have
 * nothing to do with what the JS API can reach.
 *
 * Only attributes the box itself reports are set. Asking a box to set an
 * attribute it does not have is how the Max console fills with complaints about
 * a file that is otherwise fine, and `getboxattrnames()` is the box's own answer
 * to what it accepts. A box that will not answer gets nothing rather than a
 * guess.
 */
function applyBoxAttrs(object: Maxobj, box: BoxDict): string[] {
  const known = new Set(attrNamesOf(() => object.getboxattrnames()));
  if (known.size === 0) return [];

  const failed: string[] = [];
  for (const [name, value] of Object.entries(box)) {
    if (STRUCTURAL.has(name) || !known.has(name)) continue;
    if (!isPlain(value)) continue;
    try {
      // A Max attribute takes an atom list, so a rect or a colour goes as four
      // arguments and not as one array.
      if (Array.isArray(value)) object.setboxattr(name, ...value);
      else object.setboxattr(name, value);
    } catch {
      failed.push(name);
    }
  }
  return failed;
}

/**
 * A scripting name not already in use in this patcher.
 *
 * `getnamed` answers with the *first* object of a given name, so two builds
 * that both named a box `obj-1` would leave the second unreachable and the
 * first answering for it. Suffixed rather than refused: the point of the name
 * is to be found by, and a caller who wanted a specific one would have put it
 * in the description.
 */
function freeName(target: MaxPatcher, wanted: string): string {
  let candidate = wanted;
  // Bounded because this runs inside Max, where a runaway loop takes the whole
  // application with it. A patcher with a thousand `obj-1`s is not a patcher.
  for (let n = 2; n <= 1000; n += 1) {
    let taken: boolean;
    try {
      const found = target.getnamed(candidate);
      taken = found !== null && found !== undefined;
    } catch {
      // A host that will not answer gets the name as asked.
      return candidate;
    }
    if (!taken) return candidate;
    candidate = `${wanted}-${n}`;
  }
  return candidate;
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
  /**
   * Boxes that were built, but not faithfully.
   *
   * Distinct from {@link skipped}, which is about what does not exist in the
   * patcher. These do exist and hold something other than what the description
   * said -- a message box whose commas could not survive a `set`. An empty
   * `skipped` means the patch was built; an empty `warnings` too means it was
   * built as written.
   */
  readonly warnings: readonly SkippedBox[];
}

export interface InstantiateOptions {
  /**
   * Name every created object after its model id when it has no `varname`, so
   * `patcher.getnamed("obj-3")` finds it afterwards.
   *
   * **Off by default**, and it used to be on. The justification for on was that
   * a script could not otherwise address what it had just built -- which is not
   * true: {@link InstantiateResult.objects} maps every model id to its live
   * object, in process, without touching the patch. What it cost was paid by
   * every box: a description with no `varname` produced an object with one, so
   * serializing the result wrote `varname: "obj-1"` onto boxes that had never
   * asked for a name and that py2max would never write one for. Two builds into
   * the same patcher then collided on those names, and `getnamed` answers with
   * whichever it finds first.
   *
   * Turn it on when the name has to outlive the call -- a later message, a
   * `[js]` in the patch, another script. Names are then made unique against the
   * patcher, so a second build does not shadow the first.
   *
   * A `varname` the description actually carries is applied either way.
   */
  nameById?: boolean;
  /** Resize each object to its `patching_rect`. On by default. */
  applyRects?: boolean;
  /**
   * Apply the box attributes the description carries -- colours, fonts,
   * presentation, `hidden`. On by default: a description that says a box is
   * blue should produce a blue box, and the alternative is a patch that comes
   * back from a file looking nothing like it went in.
   */
  applyAttributes?: boolean;
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
    nameById = false,
    applyRects = true,
    applyAttributes = true,
    buildSubpatchers = true,
    offset = [0, 0],
  } = options;
  const [dx, dy] = offset;

  const objects = new Map<string, Maxobj>();
  const skipped: SkippedBox[] = [];
  const warnings: SkippedBox[] = [];
  let created = 0;
  let connected = 0;

  for (const entry of source.boxes) {
    const box = entry.box;
    const [x, y, w, h] = box.patching_rect;
    const className = classNameOf(box);

    let object: Maxobj | null | undefined = null;
    try {
      object = createBox(target, box, className, x + dx, y + dy);
    } catch (err) {
      skipped.push({ id: box.id, reason: `creating the box threw: ${String(err)}` });
      continue;
    }
    if (object === null || object === undefined) {
      skipped.push({ id: box.id, reason: `unknown object class "${className}"` });
      continue;
    }

    // What Max actually does for a class it does not have: a `jbogus`
    // placeholder box, reported only to the console. Removed rather than left
    // behind, because `skipped` means "not built" and a caller that trusts it
    // would otherwise be handed a patcher containing a dead box it was told
    // nothing about.
    if (object.maxclass === BOGUS_CLASS) {
      skipped.push({
        id: box.id,
        reason:
          `unknown object class "${className}" -- Max built a placeholder ` +
          `(${BOGUS_CLASS}) and logged "No such object"`,
      });
      try {
        target.remove(object);
      } catch {
        // Left in place, but still reported: the caller knows either way.
      }
      continue;
    }

    objects.set(box.id, object);
    created += 1;

    if (SET_CONTENT_CLASSES.has(box.maxclass) && box.text !== undefined) {
      // No `set` any more, for either class: four `set`-based routes were
      // tried in Max and every one left the box empty. The content arrives at
      // creation, from `newobject`.
      //
      // Only for a message box: there `,` and `;` separate messages and their
      // loss changes what the box does. In a comment they are prose.
      if (box.maxclass === "message" && SEPARATORS.test(box.text)) {
        warnings.push({
          id: box.id,
          reason:
            `message text "${box.text}" contains a message separator ` +
            `(, or ;), which cannot be passed as an atom -- the box holds it ` +
            `as an ordinary symbol. Write the patch to a file instead if the ` +
            `separator matters.`,
        });
      }
    }

    // A name the description carries is the caller's, and goes on verbatim --
    // uniquifying it would break the reference it exists to be. A name invented
    // from the model id is ours, and is made unique so a second build does not
    // shadow the first.
    if (box.varname !== undefined) {
      object.varname = box.varname;
    } else if (nameById) {
      object.varname = freeName(target, box.id);
    }

    if (applyRects) {
      object.rect = toMaxobjRect([x + dx, y + dy, w, h]);
    }

    if (applyAttributes) {
      const failed = applyBoxAttrs(object, box);
      if (failed.length > 0) {
        warnings.push({
          id: box.id,
          reason: `box attribute(s) refused by the object: ${failed.join(", ")}`,
        });
      }
    }

    if (buildSubpatchers && box.patcher !== undefined) {
      const nested = object.subpatcher();
      if (nested === null || nested === undefined) {
        skipped.push({
          id: box.id,
          reason: "box carries a nested patcher but exposes no subpatcher()",
        });
      } else {
        // `offset` must not travel into the subpatcher. A nested box's
        // coordinates are its own window's, so shifting the parent's boxes by
        // (dx, dy) says nothing about where the subpatcher's contents belong --
        // forwarding it moved them by the parent's offset a second time, in a
        // window that never saw the first.
        const inner = instantiate(nested, box.patcher, {
          ...options,
          offset: [0, 0],
        });
        created += inner.created;
        connected += inner.connected;
        skipped.push(...inner.skipped);
        warnings.push(...inner.warnings);
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

  return { objects, created, connected, skipped, warnings };
}

/**
 * Whether two handles designate the same box, without relying on identity.
 *
 * `snapshot` already assumes they might not: the JS API does not promise that
 * two reads of the same object give the same JavaScript wrapper, which is why
 * it carries a `varname` fallback. The same doubt is far more serious here.
 * `keep` exists so a script does not delete the box it is running in, and
 * `Array.includes` answers that question by identity alone -- so if the
 * assumption ever fails, the one call whose failure frees the running script
 * fails open.
 *
 * So: identity, then a scripting name if both have one, then class and position
 * -- two different boxes of the same class stacked at exactly the same
 * coordinates is not a patch anyone has. The asymmetry is deliberate. A false
 * match leaves an object in the patcher; a missed match leaves Max executing
 * against freed memory, which reports as `bad object` / `typedmess: post:
 * corrupt object` and takes the script with it.
 */
function sameObject(a: Maxobj, b: Maxobj): boolean {
  if (a === b) return true;
  try {
    if (a.varname !== "" && a.varname === b.varname) return true;
    if (a.maxclass !== b.maxclass) return false;
    const [al, at, ar, ab] = a.rect;
    const [bl, bt, br, bb] = b.rect;
    return al === bl && at === bt && ar === br && ab === bb;
  } catch {
    // A handle that will not answer is not one to match against.
    return false;
  }
}

function isKept(keep: readonly Maxobj[], object: Maxobj): boolean {
  return keep.some((kept) => sameObject(kept, object));
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
  const doomed = objectsOf(target).filter((object) => !isKept(keep, object));
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
    if (isKept(keep, object)) continue;
    target.remove(object);
    removed += 1;
  }
  return removed;
}

/** Every object in a patcher, in list order. */
export function objectsOf(target: MaxPatcher): Maxobj[] {
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
