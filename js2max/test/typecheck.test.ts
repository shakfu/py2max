/**
 * The spike's central claim, tested rather than asserted.
 *
 * Each case below is a code snippet compiled with `tsc` in a subprocess. The
 * "rejected" cases are the failure modes that reach the emitted `.maxpat`
 * silently in the Python package, where the entire property vocabulary arrives
 * through `**kwds: Any`. `ts/README.md` records the corresponding Python
 * behaviour for the same inputs.
 *
 * These are slow (a `tsc` process each), which is the honest cost of the claim.
 */

import { describe, expect, test } from "bun:test";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const TS_ROOT = join(import.meta.dir, "..");
const TMP = join(TS_ROOT, ".tmp-typecheck");

function typecheck(code: string, name: string): { ok: boolean; output: string } {
  mkdirSync(TMP, { recursive: true });
  const file = join(TMP, `${name}.ts`);
  writeFileSync(file, code);
  const result = Bun.spawnSync({
    cmd: [
      "bunx",
      "tsc",
      "--noEmit",
      "--strict",
      "--exactOptionalPropertyTypes",
      "--allowImportingTsExtensions",
      "--target",
      "esnext",
      "--module",
      "esnext",
      "--moduleResolution",
      "bundler",
      "--skipLibCheck",
      file,
    ],
    cwd: TS_ROOT,
    stdout: "pipe",
    stderr: "pipe",
  });
  const output = `${result.stdout.toString()}${result.stderr.toString()}`;
  rmSync(file, { force: true });
  return { ok: result.exitCode === 0, output };
}

const PRELUDE = `import { Patcher } from "../src/index.ts";
import type { BoxDict, Rect4 } from "../src/index.ts";
const p = new Patcher();
`;

interface Case {
  name: string;
  code: string;
  /** Substring the compiler error must mention, proving it failed for the right reason. */
  because: string;
}

const REJECTED: Case[] = [
  {
    name: "misspelled-property",
    // The headline case. In Python this key lands in the .maxpat verbatim.
    code: `${PRELUDE}p.add("cycle~ 440", { bgcolour: [0, 0, 0, 1] });`,
    because: "bgcolour",
  },
  {
    name: "wrong-property-type",
    code: `${PRELUDE}p.add("cycle~ 440", { fontsize: "12" });`,
    because: "Type 'string' is not assignable to type 'number'",
  },
  {
    name: "wrong-rect-arity",
    code: `${PRELUDE}const r: Rect4 = [0, 0, 66];`,
    because: "Rect4",
  },
  {
    name: "missing-required-key",
    code: `${PRELUDE}const b: BoxDict = { maxclass: "newobj", numinlets: 2, numoutlets: 1, patching_rect: [0, 0, 66, 22] };`,
    because: "id",
  },
  {
    name: "explicit-undefined-for-optional",
    // exactOptionalPropertyTypes: "absent" and "present but undefined" differ,
    // which is precisely the distinction Max's format cares about.
    code: `${PRELUDE}p.add("cycle~ 440", { varname: undefined });`,
    because: "undefined",
  },
  {
    name: "non-exhaustive-switch",
    code: `import type { TypedBox } from "../src/index.ts";
function label(box: TypedBox): string {
  switch (box.maxclass) {
    case "newobj": return box.text;
    default: {
      const unreachable: never = box;
      return unreachable;
    }
  }
}
export { label };`,
    because: "never",
  },
  {
    name: "wrong-variant-property",
    // A comment box has no outlets; the variant pins numoutlets to 0.
    code: `import type { CommentBox } from "../src/index.ts";
const c: CommentBox = { maxclass: "comment", id: "obj-1", numinlets: 1, numoutlets: 1, patching_rect: [0, 0, 66, 22] };
export { c };`,
    because: "Type '1' is not assignable to type '0'",
  },
];

describe("tsc rejects what Python's **kwds: Any accepts", () => {
  for (const c of REJECTED) {
    test(c.name, () => {
      const { ok, output } = typecheck(c.code, c.name);
      expect(ok).toBe(false);
      expect(output).toContain(c.because);
    });
  }
});

describe("tsc accepts correct usage", () => {
  test("well-formed patch construction compiles", () => {
    const { ok, output } = typecheck(
      `${PRELUDE}const osc = p.add("cycle~ 440", {
  outlettype: ["signal"],
  bgcolor: [0.1, 0.2, 0.3, 1],
  varname: "osc1",
  fontsize: 12,
});
const dac = p.add("ezdac~", { maxclass: "ezdac~", numinlets: 2, numoutlets: 0 });
p.connect(osc, dac);
export { osc, dac };`,
      "valid-usage",
    );
    expect(output).toBe("");
    expect(ok).toBe(true);
  });

  test("the project itself typechecks under the full config", () => {
    const result = Bun.spawnSync({
      cmd: ["bunx", "tsc", "--noEmit"],
      cwd: TS_ROOT,
      stdout: "pipe",
      stderr: "pipe",
    });
    const output = `${result.stdout.toString()}${result.stderr.toString()}`;
    expect(output).toBe("");
    expect(result.exitCode).toBe(0);
  });
});
