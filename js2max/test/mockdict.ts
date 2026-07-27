/**
 * An in-memory stand-in for Max's `Dict`.
 *
 * The `Dict` constructor exists only inside Max, so `readDictPatch` reaches it
 * through an injectable factory -- the same seam `fileio.ts` uses for `File`.
 * This is what goes in instead, so the parsing and its failure paths are
 * exercised without Max.
 */

import type { DictFactory, MaxDict } from "../src/dict.ts";

export class MockDict implements MaxDict {
  constructor(
    readonly name: string,
    /** What `stringify()` returns; a thrower models a dictionary that refuses. */
    private readonly text: string | (() => string),
  ) {}

  stringify(): string {
    return typeof this.text === "function" ? this.text() : this.text;
  }
}

/** A factory serving the named dictionaries, as Max serves them by name. */
export function dictFactory(
  dicts: Record<string, string | (() => string)>,
): DictFactory {
  return (name) => {
    const text = dicts[name];
    // Max creates an empty dictionary for a name nothing has bound, rather
    // than failing -- which is why "empty" needs its own error message.
    return new MockDict(name, text ?? "");
  };
}
