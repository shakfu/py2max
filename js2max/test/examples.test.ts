/**
 * The shipped example scripts must keep working.
 *
 * `max/save-example.js` and `max/serialize-example.js` are plain JavaScript,
 * loaded by Max rather than by the build, so nothing else here would notice if
 * a rename made them reference a symbol that no longer exists. These tests
 * check every `js2max.<name>` they use against the actual CommonJS bundle --
 * the same file Max would `require`.
 */

import { describe, expect, test } from "bun:test";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const MAX_DIR = join(import.meta.dir, "..", "max");
const EXAMPLES = ["save-example.js", "serialize-example.js"];

/** Every `js2max.<name>` and `new js2max.<name>` referenced by a script. */
function symbolsUsed(source: string): string[] {
  // Comments and string literals first: a doc comment mentioning
  // `js2max.v8.js`, or `require("js2max.js")`, would otherwise register
  // symbols named `v8` and `js`.
  const code = source
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/\/\/[^\n]*/g, "")
    .replace(/"[^"]*"|'[^']*'/g, '""');
  const found = new Set<string>();
  for (const match of code.matchAll(/\bjs2max\.([A-Za-z_$][\w$]*)/g)) {
    if (match[1] !== undefined) found.add(match[1]);
  }
  return [...found].sort();
}

/** The bundle Max would load, required as Max would require it. */
function bundle(): Record<string, unknown> {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  return require(join(MAX_DIR, "js2max.js")) as Record<string, unknown>;
}

describe.each(EXAMPLES)("%s", (name) => {
  const source = readFileSync(join(MAX_DIR, name), "utf8");

  test("requires the shipped bundle by the name Max resolves", () => {
    expect(source).toContain('require("js2max.js")');
  });

  test("uses only symbols the bundle exports", () => {
    const exported = bundle();
    const missing = symbolsUsed(source).filter((s) => !(s in exported));
    expect(missing).toEqual([]);
  });

  test("references at least one symbol, so the check is not vacuous", () => {
    expect(symbolsUsed(source).length).toBeGreaterThan(0);
  });

  test("declares its inlets and outlets, as a v8 script must", () => {
    expect(source).toMatch(/^inlets\s*=/m);
    expect(source).toMatch(/^outlets\s*=/m);
  });

  test("sets autowatch = 0, matching the shipped entry point", () => {
    // A reload resets any state the script holds; these are shipped files, not
    // ones being edited in place.
    expect(source).toMatch(/^autowatch\s*=\s*0/m);
  });

  test("is plain ES5-compatible JavaScript, not TypeScript", () => {
    // v8 runs JavaScript. The examples are read by users as well as by Max, so
    // they stay in the dialect the docs use.
    expect(source).not.toMatch(/\bconst\b|\blet\b|=>/);
  });
});

describe("the two examples demonstrate different directions", () => {
  test("save-example writes a description, never reading the patcher", () => {
    const source = readFileSync(join(MAX_DIR, "save-example.js"), "utf8");
    expect(source).toContain("writePatch");
    expect(source).not.toContain("serialize");
    expect(source).not.toContain("instantiate");
  });

  test("serialize-example reads the patcher", () => {
    const source = readFileSync(join(MAX_DIR, "serialize-example.js"), "utf8");
    expect(source).toContain("serialize(this.patcher)");
  });
});
