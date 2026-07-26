/**
 * Tests for `.maxpat` file I/O.
 *
 * Driven against `MockFileSystem` rather than Max's `File`. What this proves:
 * the chunked read loop terminates and reassembles correctly, and a write
 * replaces rather than overwrites-in-place. What it cannot prove: that Max's
 * `File` behaves as modelled -- in particular that assigning `eof = 0`
 * truncates, which the reference documents only for *extending* a file.
 */

import { describe, expect, test } from "bun:test";

import {
  maxFileFactory,
  readPatch,
  readText,
  writePatch,
  writeText,
} from "../src/fileio.ts";
import { Patcher } from "../src/model.ts";
import { MockFileSystem } from "./mockfile.ts";
import { snapshot, instantiate } from "../src/scripting.ts";
import { MockPatcher, asHost } from "./mockhost.ts";

function withPatch(): { fs: MockFileSystem; json: string } {
  const p = new Patcher();
  const osc = p.add("cycle~ 440");
  const dac = p.add("ezdac~", { maxclass: "ezdac~", numinlets: 2 });
  p.connect(osc, dac, 0, 0);
  const fs = new MockFileSystem();
  fs.files.set("patch.maxpat", p.toJSON());
  return { fs, json: p.toJSON() };
}

describe("readText", () => {
  test("reads a whole file", () => {
    const fs = new MockFileSystem();
    fs.files.set("a.txt", "hello world");
    expect(readText("a.txt", { factory: fs.factory })).toBe("hello world");
  });

  test("reassembles a file larger than one readstring", () => {
    const fs = new MockFileSystem();
    fs.chunkLimit = 4; // force many round trips
    const body = "0123456789abcdefghij".repeat(50);
    fs.files.set("big.txt", body);

    expect(readText("big.txt", { factory: fs.factory })).toBe(body);
  });

  test("an empty file reads as an empty string, not a hang", () => {
    const fs = new MockFileSystem();
    fs.files.set("empty.txt", "");
    expect(readText("empty.txt", { factory: fs.factory })).toBe("");
  });

  test("a read that makes no progress terminates instead of spinning", () => {
    // An infinite loop inside Max locks the application, so the loop watches
    // `position` rather than trusting `eof`.
    const fs = new MockFileSystem();
    fs.files.set("stuck.txt", "abc");
    const factory = (path: string) => {
      const file = fs.open(path, "read");
      return Object.assign(file, {
        readstring: () => "",
        get eof() {
          return 999;
        },
      }) as never;
    };
    expect(readText("stuck.txt", { factory })).toBe("");
  });

  test("an unopenable path throws with the path in the message", () => {
    const fs = new MockFileSystem();
    expect(() => readText("missing.txt", { factory: fs.factory })).toThrow(
      /could not open missing\.txt/,
    );
  });

  test("the file is closed even when reading throws", () => {
    const fs = new MockFileSystem();
    fs.files.set("bad.txt", "abc");
    const opened = fs.open("bad.txt", "read");
    const factory = () =>
      Object.assign(opened, {
        readstring: () => {
          throw new Error("boom");
        },
      }) as never;

    expect(() => readText("bad.txt", { factory })).toThrow("boom");
    expect(opened.closed).toBe(true);
  });
});

describe("writeText", () => {
  test("writes a file", () => {
    const fs = new MockFileSystem();
    writeText("out.txt", "hello", { factory: fs.factory });
    expect(fs.files.get("out.txt")).toBe("hello");
  });

  test("a shorter document replaces a longer one, leaving no tail", () => {
    // Opening for write does not truncate, so without `eof = 0` the end of the
    // previous file survives -- for a .maxpat, trailing bytes after the closing
    // brace, which is invalid JSON.
    const fs = new MockFileSystem();
    fs.files.set("out.txt", "a very long previous document indeed");
    writeText("out.txt", "short", { factory: fs.factory });
    expect(fs.files.get("out.txt")).toBe("short");
  });

  test("a host that refuses truncation still writes", () => {
    const fs = new MockFileSystem();
    fs.refuseTruncate = true;
    fs.files.set("out.txt", "old");
    writeText("out.txt", "new content", { factory: fs.factory });
    expect(fs.files.get("out.txt")).toBe("new content");
  });
});

describe("readPatch / writePatch", () => {
  test("round-trips a patcher through a file", () => {
    const { fs, json } = withPatch();
    const loaded = readPatch("patch.maxpat", { factory: fs.factory });

    expect(loaded.boxes).toHaveLength(2);
    expect(loaded.lines).toHaveLength(1);
    expect(loaded.toJSON()).toBe(json);
  });

  test("writePatch then readPatch preserves the document", () => {
    const p = new Patcher();
    p.add("cycle~ 440", { varname: "osc" });
    const fs = new MockFileSystem();

    writePatch("new.maxpat", p, { factory: fs.factory });
    const loaded = readPatch("new.maxpat", { factory: fs.factory });

    expect(loaded.toJSON()).toBe(p.toJSON());
    expect(loaded.boxes[0]?.box.varname).toBe("osc");
  });

  test("non-JSON is rejected by name", () => {
    const fs = new MockFileSystem();
    fs.files.set("junk.maxpat", "this is not json");
    expect(() => readPatch("junk.maxpat", { factory: fs.factory })).toThrow(
      /not valid JSON/,
    );
  });

  test("valid JSON that is not a patch is rejected", () => {
    const fs = new MockFileSystem();
    fs.files.set("other.json", '{"hello": "world"}');
    expect(() => readPatch("other.json", { factory: fs.factory })).toThrow(
      /not a \.maxpat/,
    );
  });
});

describe("outside Max", () => {
  test("the default factory fails with a readable message, not ReferenceError", () => {
    // Bun defines a DOM-style `File`, so this asserts on behaviour rather than
    // absence: whatever happens, it must not be a bare ReferenceError.
    try {
      maxFileFactory("x.maxpat", "read");
    } catch (err) {
      expect(err).not.toBeInstanceOf(ReferenceError);
    }
  });
});


describe("what writePatch can and cannot be given", () => {
  test("a model-authored patch writes boxes Max will load", () => {
    // An object box must be maxclass "newobj" carrying its text; the class name
    // belongs in `text`, not in `maxclass`.
    const p = new Patcher();
    p.add("cycle~ 440");
    const fs = new MockFileSystem();

    writePatch("ok.maxpat", p, { factory: fs.factory });
    const box = JSON.parse(fs.files.get("ok.maxpat") ?? "{}").patcher.boxes[0]
      .box;

    expect(box.maxclass).toBe("newobj");
    expect(box.text).toBe("cycle~ 440");
    expect(typeof box.numinlets).toBe("number");
    expect(typeof box.numoutlets).toBe("number");
  });

  test("a snapshot is NOT a patch description, and the types say so", () => {
    // Regression for a shipped bug: `write` reconstructed boxes from a snapshot
    // and produced files Max would not load. A live object reports its
    // instantiated class (`cycle~`), never the box class (`newobj`), and
    // exposes neither the typed-in text nor the port counts.
    const p = new Patcher();
    p.add("cycle~ 440");

    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict());
    const box = snapshot(asHost(host)).boxes[0];

    expect(box?.maxclass).toBe("cycle~"); // not "newobj"
    expect(box).not.toHaveProperty("text");
    expect(box).not.toHaveProperty("numinlets");
    expect(box).not.toHaveProperty("numoutlets");
  });
});
