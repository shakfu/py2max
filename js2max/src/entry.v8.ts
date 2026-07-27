/**
 * The `v8` entry point: what a Max patcher actually loads.
 *
 * Bundled to a single self-contained `max/js2max.v8.js`. The bundling is not
 * incidental: **`v8` supports CommonJS `require()` but not ESM `import`**
 * (confirmed by Cycling '74 on the forum -- `include()` also exists, sharing
 * scope with the caller). This core is written as ES modules, so it must be
 * flattened before Max can load it.
 *
 * Two artifacts come out of that, for two different users:
 *
 *   `max/js2max.v8.js`  this file, bundled as an IIFE -- drop it into a patch
 *                       as `[v8 js2max.v8.js]` and send it messages.
 *   `max/js2max.js`     the same core bundled as CommonJS, for writing your
 *                       own script: `var js2max = require("js2max.js")`.
 *
 * Usage in a patch:
 *
 *     [v8 js2max.v8.js]
 *
 * Messages it accepts:
 *
 *     demo            build a small built-in patch, to prove the path works
 *     synth           build a richer one, for demonstrating `write`
 *     build <json>    build a patch description into this patcher
 *     read <path>     load a .maxpat from disk and build it here
 *     save <path>             write a description straight to a .maxpat,
 *                             creating no objects at all -- the exact route
 *     write <path>            serialize the whole patcher, [v8] box included
 *     extract <path> [match]  serialize only the objects matching `match`
 *                             (default "~"), and the cords among them
 *     write <path> built      serialize only what the last build created
 *     write <path> partial    write even if some boxes are incomplete
 *     write <path> full       also record each object box's own attributes
 *     probe           log the box attributes of each object
 *     clear           remove what the last build created
 *     clearall        remove everything except this [v8] object
 *     count           report how many objects the patcher holds
 *
 * Everything here is glue. The logic lives in `scripting.ts`, which takes its
 * patcher as an argument and is therefore testable without Max.
 */

import type { PatcherDict } from "./format.ts";
import type { InstantiateResult } from "./scripting.ts";
import {
  attrNamesOf,
  clear as clearPatcher,
  instantiate,
  objectsOf,
  remove as removeObjects,
} from "./scripting.ts";
import {
  WRITE_MODES,
  isOwnFile,
  parseWriteModes,
  selectMatching,
} from "./commands.ts";
import { patcherOf as patcherIn, readDictPatch } from "./dict.ts";
import { demoPatch, synthPatch } from "./demo.ts";
import { readPatch, writePatch, writeText } from "./fileio.ts";
import { LoadedPatcher } from "./model.ts";
import { serialize } from "./serialize.ts";
import {
  diagnoseBridge,
  formatChecks,
  formatDiagnosis,
  verifyBridge,
} from "./verify.ts";

inlets = 1;
outlets = 1;
// 0, not 1. Reloading the script resets `built`, so with autowatch on, a
// `make js2max` in another window silently discards what `synth` created and
// the next `write ... built` reports nothing to write. This is a built
// artifact, not a file anyone edits in place.
autowatch = 0;

/**
 * Find the patcher this script is running inside.
 *
 * Max binds `this` to the script's object when it dispatches a message, but the
 * reference pages do not state how that interacts with a bundled module scope,
 * and it is not verifiable outside Max. So: try the call's own `this`, fall
 * back to a global `this` handle, and fail with a sentence a user can act on
 * rather than a `TypeError` on `undefined.patcher`.
 */
function contextOf(context: unknown): MaxThis {
  const bound = context as MaxThis | null | undefined;
  if (bound?.patcher !== undefined) return bound;

  const global = globalThis as unknown as { this?: MaxThis };
  if (global.this?.patcher !== undefined) return global.this;

  throw new Error(
    "js2max: no patcher handle -- this script must be loaded by a [v8] object",
  );
}

function patcherOfContext(context: unknown): MaxPatcher {
  return contextOf(context).patcher;
}

/**
 * This script's own box, so it can avoid deleting itself.
 *
 * Not deleting yourself is not a nicety. Removing the box that hosts a running
 * script leaves execution on a freed object, and the next `post()` fails with
 * `bad object` / `typedmess: post: corrupt object`. Observed in Max.
 */
function selfBox(context: unknown): Maxobj | undefined {
  return contextOf(context).box;
}

/** Where `demo` builds, clear of a host patcher's own top-left controls. */
const DEMO_OFFSET = [0, 280] as const;

/** Objects built by the most recent `demo` / `build`, so `clear` can undo it. */
let built: Maxobj[] = [];

/**
 * The description behind that build, kept so it can be written *exactly*.
 *
 * This is the point of {@link save}. A description is already a `.maxpat`;
 * instantiating it and reading the objects back only loses things -- fonts that
 * match a patcher default, port counts maxref does not state, `linecount`,
 * anything Max writes at save time. Going through live objects is for capturing
 * a patcher someone edited, not for exporting what you just described.
 */
let described: PatcherDict | null = null;

function report(result: InstantiateResult): void {
  built = [...result.objects.values()];
  post(
    `js2max: created ${result.created} object(s), ` +
      `${result.connected} connection(s)\n`,
  );
  for (const skip of result.skipped) {
    error(`js2max: skipped ${skip.id} -- ${skip.reason}\n`);
  }
  // Built, but not as described -- worth saying, and not an error: the object
  // is there and the rest of the patch is unaffected.
  for (const warning of result.warnings) {
    post(`js2max: warning, ${warning.id} -- ${warning.reason}\n`);
  }
  outlet(0, "done", result.created, result.connected, result.skipped.length);
}

function guard(action: () => void): void {
  try {
    action();
  } catch (err) {
    error(`${String(err)}\n`);
  }
}

/**
 * `build <json>` -- instantiate a patch description.
 *
 * Accepts either a whole `.maxpat` document (`{"patcher": {...}}`) or a bare
 * patcher object, because both turn up: the first from a file py2max wrote, the
 * second from a `dict` or a message assembled in the patch.
 */
export function build(this: unknown, ...atoms: (string | number)[]): void {
  const target = this;
  guard(() => {
    // Max splits a message into atoms at whitespace, so a JSON document never
    // arrives as one symbol -- it arrives as however many pieces the tokenizer
    // made of it. Taking only the first argument, as this used to, meant `build`
    // could not work from a message box at all. Rejoining is the most that can
    // be done here; whether Max delivers the braces, quotes and colons intact
    // is what the harness is for.
    const json = atoms.join(" ");
    let parsed: unknown;
    try {
      parsed = JSON.parse(json);
    } catch (err) {
      error(`js2max: could not parse patch description -- ${String(err)}\n`);
      // The failure as data rather than as a verdict: a message box cannot
      // carry `,` or `;` (Max ends the message there), so a JSON document with
      // either is truncated before this code ever sees it. Printing what did
      // arrive is what distinguishes "Max mangled it" from "the JSON is wrong".
      error(
        `js2max: received ${atoms.length} atom(s), ${json.length} chars: ` +
          `${JSON.stringify(json.slice(0, 200))}\n`,
      );
      outlet(0, "error", "parse", atoms.length);
      return;
    }
    let patcher: PatcherDict;
    try {
      // Shared with `builddict`, so the two cannot disagree about what counts
      // as a description -- both accept a whole document or a bare patcher.
      patcher = patcherIn(parsed, "the patch description");
    } catch (err) {
      error(`${String(err)}\n`);
      return;
    }
    described = patcher;
    report(instantiate(patcherOfContext(target), patcher));
  });
}

/**
 * `builddict <name>` -- build the patch description held in a Max dictionary.
 *
 * The usable form of `build`. A message box ends its message at the first `,`,
 * so a `.maxpat` handed over as a message arrives truncated a few characters
 * in; a `dict` is passed by *name*, holds nested structure natively, and can
 * load a file from disk itself:
 *
 *     [import_json my-patch.maxpat(  ->  [dict my_patch]
 *     [builddict my_patch(           ->  [v8 js2max.v8.js]
 *
 * Where `read <path>` opens a file this script chooses, this builds whatever
 * the patch has already assembled -- from a file, from a `[dict]` built by
 * other objects, or from JSON that arrived over the network.
 */
export function builddict(this: unknown, name: string): void {
  const target = this;
  guard(() => {
    if (name === undefined || String(name) === "") {
      error(
        'js2max: builddict needs a dictionary name, e.g. "builddict my_patch"\n',
      );
      outlet(0, "error", "no-name");
      return;
    }
    const patcher = readDictPatch(String(name));
    described = patcher;
    post(`js2max: read dictionary ${String(name)}\n`);
    // Offset like `read`, and for the same reason: a description that came
    // from somewhere else carries its own coordinates, which land on top of
    // whatever the host patch keeps at its top left.
    report(
      instantiate(patcherOfContext(target), patcher, { offset: DEMO_OFFSET }),
    );
  });
}

/**
 * `demo` -- build a small patch, so the whole path can be checked at a glance.
 *
 * Offset downward because a host patcher's own controls are usually at the top
 * left, and the demo's boxes start at (48, 48): without this they land on top
 * of whatever sent the message.
 */
export function demo(this: unknown): void {
  const target = this;
  guard(() => {
    report(
      instantiate(patcherOfContext(target), demoPatch(), { offset: DEMO_OFFSET }),
    );
  });
}

/**
 * `clear` -- undo the last build, leaving the rest of the patcher alone.
 *
 * This used to remove *every* object, which included the `[v8]` box running
 * this code: Max freed it, execution carried on against the freed pointer, and
 * the next `post()` reported `bad object` / `corrupt object`. Undoing only what
 * was built is both safer and what anyone actually wants after `demo`.
 */
/**
 * `synth` -- build a patch worth writing out.
 *
 * `demo` proves the path works; this gives `write` something to serialize that
 * is plainly unlike the patch it was built into. Uses classes that keep their
 * own `maxclass` (`toggle`, `flonum`, `ezdac~`) alongside object boxes, so a
 * written file exercises both halves of `serialize`.
 */
export function synth(this: unknown): void {
  const target = this;
  guard(() => {
    const description = synthPatch();
    described = description;
    report(instantiate(patcherOfContext(target), description, { offset: [0, 40] }));
  });
}

/**
 * `save <path>` -- write a patch description straight to disk.
 *
 * **No objects are created.** A description is already the shape of a
 * `.maxpat`, so this is exact: every attribute survives, because nothing has to
 * be read back out of Max. Compare `write`, which serializes the live patcher
 * and can only recover what the JS API exposes.
 *
 * Writes the description behind the last `demo` / `synth` / `build`, or the
 * built-in instrument if nothing has been described yet -- so the demo patch is
 * one click, with nothing to clean up afterwards.
 */
export function save(this: unknown, path: string): void {
  guard(() => {
    const description = described ?? synthPatch();
    writePatch(path, new LoadedPatcher(description));
    post(
      `js2max: wrote ${path} -- ${description.boxes.length} box(es), ` +
        `${description.lines.length} line(s), exact (no objects created)\n`,
    );
    outlet(0, "saved", description.boxes.length, description.lines.length);
  });
}

export function clear(this: unknown): void {
  const target = this;
  guard(() => {
    const self = selfBox(target);
    const removed = removeObjects(patcherOfContext(target), built, {
      keep: self === undefined ? [] : [self],
    });
    built = [];
    post(`js2max: removed ${removed} object(s)\n`);
    outlet(0, "cleared", removed);
  });
}

/**
 * `clearall` -- remove everything in the patcher except this script's own box.
 *
 * Named separately from `clear` because it is destructive in a way `clear` is
 * not: it takes the patcher's original contents with it. Refuses to run when
 * the script cannot identify its own box, since bulk-removing without that
 * knowledge is exactly the case that corrupts the running script.
 */
export function clearall(this: unknown): void {
  const target = this;
  guard(() => {
    const self = selfBox(target);
    if (self === undefined) {
      error(
        "js2max: clearall needs this.box to avoid deleting the [v8] object " +
          "itself; use clear to undo the last build instead\n",
      );
      return;
    }
    const removed = clearPatcher(patcherOfContext(target), { keep: [self] });
    built = [];
    post(`js2max: removed ${removed} object(s)\n`);
    outlet(0, "cleared", removed);
  });
}

/**
 * `read <path>` -- load a `.maxpat` and build it into this patcher.
 *
 * The other half of the loop: py2max writes the file, this opens it. Paths
 * resolve the way Max resolves them, so a name alone finds a patch on the
 * search path.
 */
export function read(this: unknown, path: string): void {
  const target = this;
  guard(() => {
    const loaded = readPatch(path);
    post(`js2max: read ${path}\n`);
    report(instantiate(patcherOfContext(target), loaded.patcher, { offset: DEMO_OFFSET }));
  });
}

/**
 * `write <path>` -- serialize this patcher to a `.maxpat`.
 *
 * Refuses to write a file Max would not load: any box that cannot be fully
 * described is named in the console and the write is abandoned, rather than
 * emitting a patch with holes in it. `write <path> partial` overrides that,
 * writing what could be described.
 */
export function write(this: unknown, path: string, ...modes: string[]): void {
  // modes, in any combination:
  //   built    export only what the last build created, not the whole patcher
  //   partial  write even if some boxes could not be described
  //   full     also record each object box's own attributes
  const { modes: mode, unknown } = parseWriteModes(modes);
  const target = this;
  guard(() => {
    const patcher = patcherOfContext(target);

    // A typo is not a mode. Ignoring one used to mean `write out.maxpat buit`
    // serialized the whole patcher -- [v8] box included -- while reporting
    // success, when what was asked for was the last build.
    if (unknown.length > 0) {
      error(
        `js2max: "${unknown.join('", "')}" is not a write mode. ` +
          `Use any of: ${WRITE_MODES.join(", ")}.\n`,
      );
      outlet(0, "error", "bad-mode");
      return;
    }

    // Refuse to write over the patch being serialized. `serialize` describes the
    // whole patcher, so the output of writing to your own filename is a copy of
    // yourself -- and for a generated patch (the harness is one) that silently
    // replaces a build artifact.
    if (isOwnFile(patcher.filepath ?? "", path) && !mode.has("built")) {
      error(
        `js2max: refusing to write ${path} -- that is this patcher's own file. ` +
          `serialize() describes the whole patcher, so this would overwrite it ` +
          `with a copy of itself. Choose another name.\n`,
      );
      outlet(0, "error", "self");
      return;
    }

    if (mode.has("built") && built.length === 0) {
      error(
        `js2max: nothing built to write. Click "synth" (or "demo", or send ` +
          `"build <json>") before "write ${path} built", or drop the word ` +
          `"built" to serialize the whole patcher instead.\n`,
      );
      outlet(0, "error", "nothing-built");
      return;
    }

    const result = serialize(patcher, {
      objectAttributes: mode.has("full"),
      ...(mode.has("built") ? { only: built } : {}),
    });
    if (result.incomplete.length > 0) {
      for (const box of result.incomplete) {
        error(
          `js2max: cannot describe ${box.id} (${box.maxclass}) -- ` +
            `missing ${box.missing.join(", ")}\n`,
        );
      }
      if (!mode.has("partial")) {
        error(
          `js2max: refusing to write ${path}; ` +
            `send "write ${path} partial" to write the rest anyway\n`,
        );
        outlet(0, "error", "incomplete", result.incomplete.length);
        return;
      }
    }
    // Serializing the whole patcher, every cord has both ends in the set by
    // construction -- so a drop here is loss, not filtering, and is worth
    // saying before the file is called faithful.
    if (result.unresolved > 0) {
      const why = mode.has("built")
        ? "an endpoint is outside the built set"
        : "an endpoint was not written";
      post(
        `js2max: ${result.unresolved} cord(s) not written -- ${why}\n`,
      );
    }
    writeText(path, JSON.stringify({ patcher: result.patcher }, null, 4));
    post(
      `js2max: wrote ${path} -- ${result.patcher.boxes.length} box(es), ` +
        `${result.patcher.lines.length} line(s)` +
        `${mode.has("built") ? " (built objects only)" : ""}\n`,
    );
    outlet(
      0,
      "wrote",
      result.patcher.boxes.length,
      result.patcher.lines.length,
      result.incomplete.length,
    );
  });
}

/**
 * `probe` -- log what each box will tell us about itself.
 *
 * A diagnostic, not a feature. Every assumption here about `getboxattr` and
 * `boxtext` is from the reference rather than from a Max run; this prints what
 * Max actually returns, so a discrepancy shows up as data instead of as a file
 * that will not open.
 */
export function probe(this: unknown): void {
  const target = this;
  guard(() => {
    const patcher = patcherOfContext(target);
    // The patcher's own attributes, which decide what the emitted file records
    // above the boxes. `rect` is the open question: `.maxpat` stores
    // `[x, y, w, h]` and the JS API's rects are `[left, top, right, bottom]`,
    // so until this line is read in Max, `serialize` will not guess at it.
    for (const name of [
      "rect",
      "default_fontname",
      "default_fontsize",
      "default_fontface",
    ]) {
      let value: unknown;
      try {
        value = patcher.getattr(name);
      } catch (err) {
        value = `<threw: ${String(err)}>`;
      }
      post(`js2max probe patcher: ${name} = ${JSON.stringify(value)}\n`);
    }
    let index = 0;
    for (const object of objectsOf(patcher)) {
      index += 1;
      const names = attrNamesOf(() => object.getboxattrnames());
      post(
        `js2max probe ${index}: maxclass=${object.maxclass} ` +
          `boxclass=${String(object.getboxattr("maxclass"))} ` +
          `boxtext=${JSON.stringify(object.boxtext)} ` +
          `numinlets=${String(object.getboxattr("numinlets"))} ` +
          `numoutlets=${String(object.getboxattr("numoutlets"))}\n`,
      );
      // Null for a `trigger`, and for the `jbogus` placeholder -- not an empty
      // array, and not a throw. `probe` used to die on the `.filter` below.
      const objectAttrs = attrNamesOf(() => object.getattrnames());
      // Only what the object has beyond its box is interesting: for a UI box
      // the two lists are identical. Reading a name the object does not report
      // is what logged `v8_wrapobject: couldn't wrap instance of class
      // textfile`, so nothing outside this set is touched.
      const boxOnly = new Set(names);
      const objectOnly = objectAttrs.filter((n) => !boxOnly.has(n));

      post(`js2max probe ${index} boxattrs: ${names.join(" ")}\n`);
      post(
        `js2max probe ${index} objattrs (beyond the box): ` +
          `${objectOnly.length === 0 ? "<none>" : objectOnly.join(" ")}\n`,
      );
      for (const name of objectOnly) {
        let value: unknown;
        try {
          value = object.getattr(name);
        } catch (err) {
          value = `<threw: ${String(err)}>`;
        }
        post(
          `js2max probe ${index}   ${name} = ${JSON.stringify(value) ?? String(value)}\n`,
        );
      }
    }
    outlet(0, "probed", index);
  });
}

/**
 * `extract <path> [match]` -- write out part of a patcher as its own patch.
 *
 * This is what reading a live patcher is *for*. Serializing a whole patcher is
 * a worse `cp`: lossy where a file copy is exact. The value appears only when
 * the result is not a copy -- when you filter, and get a patch that did not
 * exist before.
 *
 * `match` is tested against each object's class and text, and defaults to `~`,
 * which selects the signal objects. Cords are kept only where both ends
 * survive, so the extracted patch is self-contained.
 */
export function extract(this: unknown, path: string, match?: string): void {
  const target = this;
  const needle = match ?? "~";
  guard(() => {
    const patcher = patcherOfContext(target);
    const chosen = selectMatching(objectsOf(patcher), needle);

    if (chosen.length === 0) {
      error(`js2max: nothing in this patcher matches "${needle}"\n`);
      outlet(0, "error", "no-match");
      return;
    }

    const result = serialize(patcher, { only: chosen });
    for (const box of result.incomplete) {
      error(
        `js2max: cannot describe ${box.id} (${box.maxclass}) -- ` +
          `missing ${box.missing.join(", ")}\n`,
      );
    }
    writeText(path, JSON.stringify({ patcher: result.patcher }, null, 4));
    post(
      `js2max: extracted ${result.patcher.boxes.length} of ${patcher.count} ` +
        `object(s) matching "${needle}" to ${path} -- ` +
        `${result.patcher.lines.length} cord(s)` +
        // Expected here rather than alarming: cutting the cords that leave the
        // set is what makes the extract a patch on its own.
        (result.unresolved > 0
          ? `, ${result.unresolved} cut at the boundary`
          : "") +
        `\n`,
    );
    outlet(
      0,
      "extracted",
      result.patcher.boxes.length,
      result.patcher.lines.length,
    );
  });
}

/**
 * `verify` -- run the bridge's own assumptions against this Max, and report.
 *
 * Everything in `scripting.ts` is checked against a mock, which proves the
 * mapping and proves nothing about whether Max accepts the calls. This settles
 * the four assumptions the rest of the bridge rests on: whether `set` fills a
 * message box, whether `newdefault` returns null or throws for an unknown
 * class, whether a subpatcher box exposes its patcher, and whether `snapshot`
 * reads a live one.
 *
 * Builds what each check needs and takes it away again, so the patcher is left
 * as it was found. Read the console; `[NO ]` on any line is a real finding.
 */
export function verify(this: unknown): void {
  const target = this;
  guard(() => {
    const result = verifyBridge(patcherOfContext(target), selfBox(target));
    for (const line of formatChecks(result)) post(`${line}\n`);
    const failed = result.checks.filter((c) => c.held !== true).length;
    if (failed > 0) {
      error(
        `js2max verify: ${failed} assumption(s) did not hold -- ` +
          `js2max/README.md records what each one costs\n`,
      );
    }
    outlet(0, "verified", result.checks.length - failed, failed);
  });
}

/**
 * `diagnose` -- the questions `verify` left open, put to Max as experiments.
 *
 * Where `verify` reports whether an assumption held, this reports what the
 * thing that broke it actually looks like: several variants built side by side
 * with every readable field printed, so a detector can be written from evidence
 * instead of from a guess. Cleans up after itself, as `verify` does.
 *
 * Expect `js2max.nosuchobject~: No such object` in the console. That is the
 * experiment running, not a fault.
 */
export function diagnose(this: unknown): void {
  const target = this;
  guard(() => {
    const result = diagnoseBridge(patcherOfContext(target), selfBox(target));
    for (const line of formatDiagnosis(result)) post(`${line}\n`);
    outlet(0, "diagnosed", result.observations.length);
  });
}

export function count(this: unknown): void {
  const target = this;
  guard(() => {
    outlet(0, "count", patcherOfContext(target).count);
  });
}

// The v8 object dispatches an incoming message to the same-named global
// function, so these assignments *are* the public interface. Without them the
// bundler's module scope would hide every handler.
Object.assign(globalThis, {
  build,
  builddict,
  clear,
  clearall,
  count,
  demo,
  diagnose,
  extract,
  probe,
  read,
  save,
  synth,
  verify,
  write,
});
