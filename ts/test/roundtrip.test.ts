/**
 * Round-trip the repository's real `.maxpat` fixtures through the typed model.
 *
 * The bar is semantic identity, not byte identity: Max writes its JSON with an
 * idiosyncratic mix of tabs and newlines that neither this spike nor the Python
 * package reproduces (Python emits `json.dump(indent=4)`). What must hold is
 * that no key, value or ordering-independent structure is lost or invented --
 * which is the same guarantee the Python side's round-trip tests assert.
 */

import { describe, expect, test } from "bun:test";
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { Patcher } from "../src/index.ts";
import type { MaxPatchFile } from "../src/index.ts";

const REPO = join(import.meta.dir, "..", "..");
const DATA = join(REPO, "tests", "data");
const PREVIEW = join(REPO, "tests", "examples", "preview");

function fixtures(): { name: string; path: string }[] {
  const found: { name: string; path: string }[] = [];
  for (const dir of [DATA, PREVIEW]) {
    for (const name of readdirSync(dir)) {
      if (name.endsWith(".maxpat")) found.push({ name, path: join(dir, name) });
    }
  }
  return found.sort((a, b) => a.name.localeCompare(b.name));
}

const ALL = fixtures();

test("the fixture corpus was found", () => {
  expect(ALL.length).toBeGreaterThanOrEqual(14);
});

describe("round-trip preserves the document", () => {
  for (const { name, path } of ALL) {
    test(name, () => {
      const source = readFileSync(path, "utf8");
      const original = JSON.parse(source) as MaxPatchFile;

      const loaded = Patcher.parse(source);
      const emitted = JSON.parse(loaded.toJSON()) as MaxPatchFile;

      // Nothing lost, nothing invented, at any depth.
      expect(emitted).toEqual(original);
    });
  }
});

describe("the typed model reads real files correctly", () => {
  test("simple.maxpat: boxes, ports and connections", () => {
    const loaded = Patcher.parse(readFileSync(join(DATA, "simple.maxpat"), "utf8"));

    expect(loaded.boxes).toHaveLength(2);
    expect(loaded.lines).toHaveLength(2);

    const osc = loaded.findById("obj-1");
    expect(osc?.text).toBe("cycle~ 440");
    expect(osc?.maxclass).toBe("newobj");
    expect(osc?.varname).toBe("osc1");
    expect(osc?.numoutlets).toBe(1);

    const dac = loaded.findById("obj-2");
    expect(dac?.maxclass).toBe("ezdac~");
    expect(dac?.numoutlets).toBe(0);

    // Both patchlines leave obj-1 outlet 0; they differ by destination inlet.
    const inlets = loaded.lines.map((l) => l.patchline.destination[1]).sort();
    expect(inlets).toEqual([0, 1]);
  });

  test("nested.maxpat: subpatchers are walked", () => {
    const loaded = Patcher.parse(readFileSync(join(DATA, "nested.maxpat"), "utf8"));
    const all = [...loaded.walk()];
    expect(all.length).toBeGreaterThan(loaded.boxes.length);
    expect(all.some((b) => b.patcher !== undefined)).toBe(true);
  });

  test("empty.maxpat: an empty patcher is still valid", () => {
    const loaded = Patcher.parse(readFileSync(join(DATA, "empty.maxpat"), "utf8"));
    expect(loaded.boxes).toHaveLength(0);
    expect(loaded.lines).toHaveLength(0);
  });

  test("unknown keys survive a round-trip", () => {
    // tabular.maxpat carries `parameters`, which the model does not interpret.
    const source = readFileSync(join(DATA, "tabular.maxpat"), "utf8");
    const emitted = JSON.parse(Patcher.parse(source).toJSON()) as MaxPatchFile;
    expect(emitted.patcher.parameters).toEqual(
      (JSON.parse(source) as MaxPatchFile).patcher.parameters,
    );
  });

  test("editing after a load does not reuse ids", () => {
    const loaded = Patcher.parse(readFileSync(join(DATA, "complex.maxpat"), "utf8"));
    const existing = new Set([...loaded.walk()].map((b) => b.id));
    expect(loaded.maxNumericId()).toBeGreaterThan(0);
    const nextId = `obj-${loaded.maxNumericId() + 1}`;
    expect(existing.has(nextId)).toBe(false);
  });
});

describe("construction", () => {
  test("a built patch has the expected shape", () => {
    const p = new Patcher();
    const osc = p.add("cycle~ 440", { outlettype: ["signal"] });
    const dac = p.add("ezdac~", { maxclass: "ezdac~", numinlets: 2, numoutlets: 0 });
    p.connect(osc, dac, 0, 0);
    p.connect(osc, dac, 0, 1);

    const file = JSON.parse(p.toJSON()) as MaxPatchFile;
    expect(file.patcher.boxes).toHaveLength(2);
    expect(file.patcher.lines).toHaveLength(2);
    expect(file.patcher.boxes[0]?.box.id).toBe("obj-1");
    expect(file.patcher.lines[1]?.patchline.order).toBe(1);
  });

  test("absent optionals are absent, not null", () => {
    // The behaviour `_remove_none_entries` exists to produce in Python is the
    // default here: an unset optional never reaches the output.
    const p = new Patcher();
    p.add("cycle~ 440");
    const emitted = p.toJSON();
    expect(emitted).not.toContain("null");
    expect(emitted).not.toContain("bgcolor");

    const box = (JSON.parse(emitted) as MaxPatchFile).patcher.boxes[0]?.box;
    expect(box).toBeDefined();
    expect("bgcolor" in box!).toBe(false);
  });

  test("a subpatcher nests a whole patcher", () => {
    const p = new Patcher();
    const { box, sub } = p.addSubpatcher("p filter");
    sub.add("inlet", { maxclass: "inlet", numinlets: 0, numoutlets: 1 });
    sub.add("outlet", { maxclass: "outlet", numinlets: 1, numoutlets: 0 });
    // The nested dict is live, so boxes added afterwards are included.
    box.patcher = sub.toPatcherDict();

    const file = JSON.parse(p.toJSON()) as MaxPatchFile;
    expect(file.patcher.boxes[0]?.box.patcher?.boxes).toHaveLength(2);
  });
});
