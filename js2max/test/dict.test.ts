/**
 * Building a patch from a Max dictionary.
 *
 * The route exists because the message route cannot be made to work: a Max
 * message box ends its message at the first `,`, so a `.maxpat` handed to
 * `[v8]` as a message is truncated a few characters in. A `dict` is passed by
 * name, so the message carries one symbol and the document never goes through
 * Max's message parser at all.
 */

import { describe, expect, test } from "bun:test";

import { readDictPatch, patcherOf } from "../src/dict.ts";
import { instantiate } from "../src/scripting.ts";
import { Patcher } from "../src/model.ts";
import { synthPatch } from "../src/demo.ts";
import { dictFactory } from "./mockdict.ts";
import { MockPatcher, asHost } from "./mockhost.ts";

/** A whole `.maxpat` document, as `import_json` would leave in a dictionary. */
const DOCUMENT = JSON.stringify({ patcher: synthPatch() });

/** A bare patcher, as a dictionary assembled in the patch might hold. */
const BARE = JSON.stringify(synthPatch());

describe("reading a description out of a dictionary", () => {
  test("a whole .maxpat document is unwrapped", () => {
    const patcher = readDictPatch("my_patch", {
      factory: dictFactory({ my_patch: DOCUMENT }),
    });

    expect(patcher.boxes).toHaveLength(9);
    expect(patcher.lines).toHaveLength(9);
  });

  test("a bare patcher object is taken as it is", () => {
    // Both shapes turn up: the first from `import_json` on a file py2max
    // wrote, the second from a dictionary built by other objects in the patch.
    const patcher = readDictPatch("my_patch", {
      factory: dictFactory({ my_patch: BARE }),
    });

    expect(patcher.boxes).toHaveLength(9);
  });

  test("what comes out builds, which is the whole point", () => {
    const patcher = readDictPatch("my_patch", {
      factory: dictFactory({ my_patch: DOCUMENT }),
    });
    const host = new MockPatcher();
    const result = instantiate(asHost(host), patcher);

    expect(result.created).toBe(9);
    expect(result.skipped).toEqual([]);
  });

  test("a description round-trips through a dictionary unchanged", () => {
    const p = new Patcher();
    const osc = p.add("cycle~ 440");
    const dac = p.add("ezdac~");
    p.connect(osc, dac);

    const patcher = readDictPatch("built", {
      factory: dictFactory({ built: p.toJSON() }),
    });
    expect(patcher).toEqual(p.toPatcherDict());
  });
});

describe("a dictionary that cannot be built from says why", () => {
  test("an unbound name reads as empty, and says how to fill it", () => {
    // Max hands back an empty dictionary for a name nothing has bound, rather
    // than failing -- so "empty" is the common mistake, not an exotic one, and
    // a typo in the name looks exactly like a load that did not happen.
    expect(() =>
      readDictPatch("nothing_here", { factory: dictFactory({}) }),
    ).toThrow(/is empty/);
    expect(() =>
      readDictPatch("nothing_here", { factory: dictFactory({}) }),
    ).toThrow(/import my-patch\.json/);
  });

  test("an empty dictionary stringifies to {} and is caught as empty", () => {
    // Observed in Max the first time this ran: the load had failed, so the
    // dictionary was empty -- and it does not stringify to an empty *string*,
    // it comes back as `{}`. That parses cleanly and then failed much further
    // on as "no patcher.boxes", blaming the description for an unloaded dict.
    for (const text of ["{}", "{\n\n}", "  { }  "]) {
      expect(() =>
        readDictPatch("blank", { factory: dictFactory({ blank: text }) }),
      ).toThrow(/is empty/);
    }
  });

  test("a dictionary with content but no patcher is not called empty", () => {
    // The two failures are different and need different fixes: nothing loaded,
    // versus the wrong thing loaded.
    expect(() =>
      readDictPatch("wrong", {
        factory: dictFactory({ wrong: '{"hello": "world"}' }),
      }),
    ).toThrow(/has no patcher\.boxes/);
  });

  test("text that is not JSON is quoted back, not merely refused", () => {
    // Max's dictionary text format is close to JSON but not confirmed to be it
    // in every case. A near-miss and a wholly different format need different
    // responses, and only the text distinguishes them.
    expect(() =>
      readDictPatch("odd", { factory: dictFactory({ odd: "boxes : [ ]" }) }),
    ).toThrow(/did not parse as JSON/);
    expect(() =>
      readDictPatch("odd", { factory: dictFactory({ odd: "boxes : [ ]" }) }),
    ).toThrow(/it begins "boxes/);
  });

  test("valid JSON that is not a patch is reported as such", () => {
    expect(() =>
      readDictPatch("wrong", {
        factory: dictFactory({ wrong: '{"hello": "world"}' }),
      }),
    ).toThrow(/dictionary "wrong" has no patcher\.boxes/);
  });

  test("a dictionary that refuses to stringify is reported, not swallowed", () => {
    const factory = dictFactory({
      broken: () => {
        throw new Error("dict is busy");
      },
    });

    expect(() => readDictPatch("broken", { factory })).toThrow(
      /could not read dictionary "broken"/,
    );
  });
});

describe("the description shape is understood in one place", () => {
  test("build and builddict accept exactly the same two shapes", () => {
    // `patcherOf` is shared by both handlers, so a document that one accepts
    // cannot be one the other rejects.
    const document = patcherOf(JSON.parse(DOCUMENT), "test");
    const bare = patcherOf(JSON.parse(BARE), "test");

    expect(document).toEqual(bare);
  });

  test("the source is named in the error, so the user knows which failed", () => {
    expect(() => patcherOf({ nope: 1 }, "dictionary \"foo\"")).toThrow(
      /dictionary "foo" has no patcher\.boxes/,
    );
    expect(() => patcherOf(null, "the patch description")).toThrow(
      /the patch description does not hold/,
    );
  });
});
