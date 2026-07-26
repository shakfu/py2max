/**
 * The decisions the `v8` message handlers make, separated from the handlers.
 *
 * `entry.v8.ts` cannot be imported outside Max: it assigns to `inlets`,
 * `outlets` and `autowatch` at load time, and those exist only in the host. So
 * anything that lives there is untestable by construction -- which was fine
 * while it was glue, and stopped being fine once it held mode parsing, a
 * refusal to overwrite the patcher's own file, and the whole of `extract`'s
 * matching. Those are decisions with edge cases; they belong where `bun test`
 * can reach them.
 *
 * The handlers stay in `entry.v8.ts` and stay glue: read arguments, call one of
 * these, post the result.
 */

/** Words `write` accepts after the path. Anything else is a typo, not a mode. */
export const WRITE_MODES = ["built", "partial", "full"] as const;

export type WriteMode = (typeof WRITE_MODES)[number];

export interface ParsedModes {
  modes: ReadonlySet<WriteMode>;
  /** Words that are not modes. A non-empty list should stop the write. */
  unknown: readonly string[];
}

/**
 * Split `write`'s trailing words into modes and typos.
 *
 * Unknown words used to be ignored, which is the worst reading of a typo: `write
 * out.maxpat buit` silently serialized the *whole patcher* -- `[v8]` box,
 * message boxes and all -- when what was asked for was the handful of objects
 * the last build created. A wrong file with a success message is worse than no
 * file.
 */
export function parseWriteModes(words: readonly string[]): ParsedModes {
  const known = new Set<WriteMode>();
  const unknown: string[] = [];
  for (const word of words) {
    if ((WRITE_MODES as readonly string[]).includes(word)) {
      known.add(word as WriteMode);
    } else if (word !== "") {
      unknown.push(word);
    }
  }
  return { modes: known, unknown };
}

/** The last path component, for either separator. */
export function basename(path: string): string {
  const cut = Math.max(path.lastIndexOf("/"), path.lastIndexOf("\\"));
  return cut < 0 ? path : path.slice(cut + 1);
}

/**
 * Whether writing to `target` would overwrite the patcher doing the writing.
 *
 * `serialize` describes the whole patcher, so writing to your own filename
 * produces a copy of yourself -- and for a generated patch (the harness is one)
 * that silently replaces a build artifact with a lossy round-trip of itself.
 *
 * Compared by filename rather than by full path, deliberately: Max resolves a
 * bare name through the search path, so `write v8-harness.maxpat` and the
 * patcher's own absolute path are the same file with different spellings, and
 * the strict comparison would miss exactly the case worth catching.
 */
export function isOwnFile(patcherPath: string, target: string): boolean {
  const own = basename(patcherPath);
  return own !== "" && basename(target) === own;
}

/**
 * The objects an `extract` should write out.
 *
 * `needle` is tested against each object's class and its box text, so `~` picks
 * the signal chain, `metro` picks the metros, and a varname picks one box. A
 * substring rather than a pattern: this arrives as a Max message argument,
 * where a regex would need escaping that a message box cannot express.
 */
export function selectMatching(
  objects: readonly Maxobj[],
  needle: string,
): Maxobj[] {
  return objects.filter((object) => {
    const text = object.boxtext ?? "";
    return object.maxclass.indexOf(needle) >= 0 || text.indexOf(needle) >= 0;
  });
}
