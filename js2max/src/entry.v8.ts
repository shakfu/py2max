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
  clear as clearPatcher,
  instantiate,
  remove as removeObjects,
} from "./scripting.ts";
import { demoPatch, synthPatch } from "./demo.ts";
import { readPatch, writePatch, writeText } from "./fileio.ts";
import { LoadedPatcher } from "./model.ts";
import { serialize } from "./serialize.ts";

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

function patcherOf(context: unknown): MaxPatcher {
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

function basename(path: string): string {
  const cut = Math.max(path.lastIndexOf("/"), path.lastIndexOf("\\"));
  return cut < 0 ? path : path.slice(cut + 1);
}

function report(result: InstantiateResult): void {
  built = [...result.objects.values()];
  post(
    `js2max: created ${result.created} object(s), ` +
      `${result.connected} connection(s)\n`,
  );
  for (const skip of result.skipped) {
    error(`js2max: skipped ${skip.id} -- ${skip.reason}\n`);
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
export function build(this: unknown, json: string): void {
  const target = this;
  guard(() => {
    let parsed: unknown;
    try {
      parsed = JSON.parse(json);
    } catch (err) {
      error(`js2max: could not parse patch description -- ${String(err)}\n`);
      return;
    }
    const patcher =
      parsed !== null && typeof parsed === "object" && "patcher" in parsed
        ? (parsed as { patcher: PatcherDict }).patcher
        : (parsed as PatcherDict);

    if (patcher === null || patcher === undefined || !Array.isArray(patcher.boxes)) {
      error("js2max: patch description has no boxes\n");
      return;
    }
    described = patcher;
    report(instantiate(patcherOf(target), patcher));
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
      instantiate(patcherOf(target), demoPatch(), { offset: DEMO_OFFSET }),
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
    report(instantiate(patcherOf(target), description, { offset: [0, 40] }));
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
    const removed = removeObjects(patcherOf(target), built, {
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
    const removed = clearPatcher(patcherOf(target), { keep: [self] });
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
    report(instantiate(patcherOf(target), loaded.patcher, { offset: DEMO_OFFSET }));
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
  const mode = new Set(modes);
  const target = this;
  guard(() => {
    const patcher = patcherOf(target);

    // Refuse to write over the patch being serialized. `serialize` describes the
    // whole patcher, so the output of writing to your own filename is a copy of
    // yourself -- and for a generated patch (the harness is one) that silently
    // replaces a build artifact.
    const own = basename(patcher.filepath ?? "");
    if (own !== "" && basename(path) === own && !mode.has("built")) {
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
    const patcher = patcherOf(target);
    let index = 0;
    for (
      let object = patcher.firstobject;
      object !== null && object !== undefined;
      object = object.nextobject
    ) {
      index += 1;
      const names = (() => {
        try {
          return object.getboxattrnames();
        } catch (err) {
          return [`<getboxattrnames failed: ${String(err)}>`];
        }
      })();
      post(
        `js2max probe ${index}: maxclass=${object.maxclass} ` +
          `boxclass=${String(object.getboxattr("maxclass"))} ` +
          `boxtext=${JSON.stringify(object.boxtext)} ` +
          `numinlets=${String(object.getboxattr("numinlets"))} ` +
          `numoutlets=${String(object.getboxattr("numoutlets"))}\n`,
      );
      const objectAttrs = (() => {
        try {
          return object.getattrnames();
        } catch (err) {
          return [`<getattrnames failed: ${String(err)}>`];
        }
      })();
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

export function count(this: unknown): void {
  const target = this;
  guard(() => {
    outlet(0, "count", patcherOf(target).count);
  });
}

// The v8 object dispatches an incoming message to the same-named global
// function, so these assignments *are* the public interface. Without them the
// bundler's module scope would hide every handler.
Object.assign(globalThis, {
  build,
  clear,
  clearall,
  count,
  demo,
  probe,
  read,
  save,
  synth,
  write,
});
