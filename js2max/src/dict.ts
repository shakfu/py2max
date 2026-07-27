/**
 * Reading a patch description out of a Max `dict`.
 *
 * This exists because `build <json>` cannot work. A Max message box ends the
 * message at the first `,`, and splits it at every space, so a `.maxpat`
 * document handed to `[v8]` as a message arrives truncated at its first comma
 * -- which for a real patch is a few characters in. `build` still takes every
 * atom it is given and rejoins them, and that is as far as the message path can
 * be pushed.
 *
 * A `dict` has none of those limits. It is Max's own structured-data object, it
 * holds nested dictionaries and arrays natively, it can load a document
 * straight off disk with `import`, and it is passed around by *name*, so
 * the message that triggers a build carries one symbol instead of a document:
 *
 *     [import my-patch.json(
 *              |
 *     [dict my_patch]        [builddict my_patch(
 *                                     |
 *                            [v8 js2max.v8.js]
 *
 * The `Dict` constructor exists only inside Max, so it is reached through
 * {@link maxDictFactory} rather than referenced directly -- the same seam
 * `fileio.ts` uses for `File`, and for the same two reasons: the parsing stays
 * testable outside Max, and a script run outside it gets a sentence rather than
 * a `ReferenceError`.
 */

import type { MaxPatchFile, PatcherDict } from "./format.ts";

/** The subset of Max's `Dict` this uses. */
export interface MaxDict {
  /** The dictionary's name, by which the rest of the patch refers to it. */
  readonly name: string;
  /** The whole dictionary as text. */
  stringify(): string;
}

export type DictFactory = (name: string) => MaxDict;

interface MaxDictConstructor {
  new (name: string): MaxDict;
}

/**
 * The Max `Dict` global, or a clear failure.
 *
 * Resolved through `globalThis` rather than declared as an ambient `Dict`,
 * which keeps the name out of the global type space and gives an honest error
 * outside Max instead of a `ReferenceError`.
 */
export const maxDictFactory: DictFactory = (name) => {
  const ctor = (globalThis as unknown as { Dict?: MaxDictConstructor }).Dict;
  if (ctor === undefined) {
    throw new Error(
      "js2max: no Max Dict class -- dictionaries are only available inside Max",
    );
  }
  return new ctor(name);
};

export interface DictOptions {
  /** Override the `Dict` constructor. Tests pass a double; Max needs none. */
  factory?: DictFactory;
}

/**
 * The patcher description held in the named dictionary.
 *
 * Accepts either a whole `.maxpat` document (`{"patcher": {...}}`) or a bare
 * patcher object, because both turn up: the first from `import` on a file
 * py2max wrote, the second from a dictionary assembled in the patch.
 *
 * `stringify()` is the only accessor used. Walking the dictionary key by key
 * would mean rebuilding the nested `boxes` / `lines` / `patcher` structure by
 * hand, in a second vocabulary, when the text is already the shape `JSON.parse`
 * wants -- and the format types exist precisely so that shape is described
 * once.
 */
export function readDictPatch(
  name: string,
  options: DictOptions = {},
): PatcherDict {
  const factory = options.factory ?? maxDictFactory;
  const dict = factory(name);

  let text: string;
  try {
    text = dict.stringify();
  } catch (err) {
    throw new Error(
      `js2max: could not read dictionary "${name}" -- ${String(err)}`,
    );
  }
  if (typeof text !== "string" || text.trim() === "") {
    throw new Error(emptyMessage(name));
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch (err) {
    // Max's dictionary text format is close to JSON but has not been confirmed
    // to *be* JSON in every case, so the failure names what came back rather
    // than only that it failed. A leading fragment is enough to tell a
    // near-miss from something else entirely.
    throw new Error(
      `js2max: dictionary "${name}" did not parse as JSON -- ${String(err)}; ` +
        `it begins ${JSON.stringify(text.slice(0, 120))}`,
    );
  }

  // An empty dictionary does not stringify to an empty *string* -- it comes
  // back as `{}`, which parses cleanly and then fails much further on as "no
  // patcher.boxes", blaming the description for what is really an unloaded
  // dictionary. Observed the first time this was run in Max, where the load had
  // failed and this was the error that came out.
  if (
    parsed !== null &&
    typeof parsed === "object" &&
    Object.keys(parsed).length === 0
  ) {
    throw new Error(emptyMessage(name));
  }

  return patcherOf(parsed, `dictionary "${name}"`);
}

/**
 * What to say about a dictionary with nothing in it.
 *
 * The commonest failure by far, because Max creates an empty dictionary for any
 * name nothing has bound rather than reporting an unknown one -- so a typo in
 * the name and a load that did not happen look identical. Naming the fix is
 * worth more than naming the fault.
 */
function emptyMessage(name: string): string {
  return (
    `js2max: dictionary "${name}" is empty -- load it first, e.g. send ` +
    `[dict ${name}] the message "import my-patch.json", and check the name ` +
    `matches`
  );
}

/** The patcher inside a parsed document, whichever of the two shapes it is. */
export function patcherOf(parsed: unknown, source: string): PatcherDict {
  if (parsed === null || typeof parsed !== "object") {
    throw new Error(`js2max: ${source} does not hold a patch description`);
  }
  const patcher =
    "patcher" in parsed
      ? (parsed as MaxPatchFile).patcher
      : (parsed as PatcherDict);
  if (patcher === null || patcher === undefined || !Array.isArray(patcher.boxes)) {
    throw new Error(`js2max: ${source} has no patcher.boxes -- not a .maxpat?`);
  }
  return patcher;
}
