/**
 * The decisions behind the `v8` messages.
 *
 * These used to live in `entry.v8.ts`, which no test can import -- it assigns
 * to `inlets` / `outlets` / `autowatch` at load time, and those exist only
 * inside Max. So this was the code with the edge cases and no coverage: a typo
 * in a mode word, a path that is the patcher's own file under another spelling,
 * the substring an `extract` matches on.
 */

import { describe, expect, test } from "bun:test";

import {
  WRITE_MODES,
  basename,
  isOwnFile,
  parseWriteModes,
  selectMatching,
} from "../src/commands.ts";
import { instantiate } from "../src/scripting.ts";
import { synthPatch } from "../src/demo.ts";
import { MockPatcher, asHost } from "./mockhost.ts";

describe("write modes", () => {
  test("the modes the documentation lists are the modes accepted", () => {
    // The README table and this list are the same promise.
    expect([...WRITE_MODES].sort()).toEqual(["built", "full", "partial"]);
  });

  test("several modes combine", () => {
    const { modes, unknown } = parseWriteModes(["built", "full"]);

    expect(modes.has("built")).toBe(true);
    expect(modes.has("full")).toBe(true);
    expect(modes.has("partial")).toBe(false);
    expect(unknown).toEqual([]);
  });

  test("no modes at all is not an error", () => {
    const { modes, unknown } = parseWriteModes([]);

    expect(modes.size).toBe(0);
    expect(unknown).toEqual([]);
  });

  test("a typo is reported rather than ignored", () => {
    // The bug: unknown words were dropped, so `write out.maxpat buit`
    // serialized the whole patcher -- [v8] box and message boxes included --
    // and said it had succeeded, when the request was for the last build.
    const { modes, unknown } = parseWriteModes(["buit"]);

    expect(modes.size).toBe(0);
    expect(unknown).toEqual(["buit"]);
  });

  test("a typo alongside a real mode is still reported", () => {
    const { modes, unknown } = parseWriteModes(["built", "ful"]);

    expect(modes.has("built")).toBe(true);
    expect(unknown).toEqual(["ful"]);
  });

  test("an empty argument is not a typo", () => {
    // Max can deliver a trailing empty symbol; it is not something to refuse.
    expect(parseWriteModes([""]).unknown).toEqual([]);
  });
});

describe("refusing to overwrite the patcher's own file", () => {
  test("the same file under a bare name is caught", () => {
    // The case worth catching: Max resolves a bare name through the search
    // path, so this *is* the patcher's own file, spelled differently. A
    // full-path comparison would miss it and quietly replace the patch with a
    // lossy round-trip of itself.
    expect(
      isOwnFile("/Users/x/patches/v8-harness.maxpat", "v8-harness.maxpat"),
    ).toBe(true);
  });

  test("a windows path is compared the same way", () => {
    expect(isOwnFile("C:\\patches\\harness.maxpat", "harness.maxpat")).toBe(
      true,
    );
  });

  test("another name in the same folder is fine", () => {
    expect(isOwnFile("/Users/x/harness.maxpat", "/Users/x/out.maxpat")).toBe(
      false,
    );
  });

  test("an unsaved patcher has no own file to protect", () => {
    // `filepath` is empty until the patch is saved; every write is fine then.
    expect(isOwnFile("", "out.maxpat")).toBe(false);
  });

  test("basename handles a path with no separator at all", () => {
    expect(basename("out.maxpat")).toBe("out.maxpat");
  });
});

describe("selecting what an extract writes", () => {
  /** The synth patch, built into a host that also holds its own furniture. */
  function host(): MockPatcher {
    const patcher = new MockPatcher();
    patcher.newdefault(0, 0, "v8", "js2max.v8.js");
    patcher.newdefault(0, 40, "comment");
    instantiate(asHost(patcher), synthPatch());
    return patcher;
  }

  test("the default needle picks the signal chain", () => {
    const patcher = host();
    const chosen = selectMatching(
      patcher.objects as unknown as Maxobj[],
      "~",
    );

    const texts = chosen.map((o) => o.boxtext ?? "");
    expect(texts).toContain("cycle~");
    expect(texts).toContain("*~ 0.2");
    expect(texts.some((t) => t.includes("js2max.v8.js"))).toBe(false);
  });

  test("a needle matches the object class as well as the text", () => {
    const patcher = host();
    const chosen = selectMatching(
      patcher.objects as unknown as Maxobj[],
      "comment",
    );

    expect(chosen).toHaveLength(1);
    expect(chosen[0]?.maxclass).toBe("comment");
  });

  test("a needle that matches nothing selects nothing", () => {
    const patcher = host();

    expect(
      selectMatching(patcher.objects as unknown as Maxobj[], "nosuchthing"),
    ).toEqual([]);
  });

  test("a needle is a substring, not a pattern", () => {
    // It arrives as a Max message argument, where a regex would need escaping a
    // message box cannot express. `.` is a literal dot.
    const patcher = new MockPatcher();
    patcher.newdefault(0, 0, "zl.reg");
    patcher.newdefault(0, 40, "zlXreg");

    const chosen = selectMatching(
      patcher.objects as unknown as Maxobj[],
      "zl.",
    );
    expect(chosen).toHaveLength(1);
    expect(chosen[0]?.maxclass).toBe("zl.reg");
  });
});
