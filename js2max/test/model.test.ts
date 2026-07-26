/**
 * What a box knows about itself before Max ever sees it.
 *
 * `Patcher.add` used to declare 2 inlets and 1 outlet for everything, which is
 * right for a `cycle~` and wrong for most of the vocabulary -- a `gain~` has
 * one inlet, an `ezdac~` no outlets, and neither is a `newobj` box at all. The
 * facts were already in `objects.ts`, exported from py2max for 1098 classes;
 * these check that they are used, and that a caller who knows better still
 * wins.
 */

import { describe, expect, test } from "bun:test";

import { Patcher } from "../src/model.ts";
import { demoPatch } from "../src/demo.ts";

describe("a box takes its class and ports from the object class", () => {
  test("an object box is a newobj with the class table's counts", () => {
    const box = new Patcher().add("cycle~ 440");

    expect(box.maxclass).toBe("newobj");
    expect(box.numinlets).toBe(2);
    expect(box.numoutlets).toBe(1);
    expect(box.outlettype).toEqual(["signal"]);
    expect(box.text).toBe("cycle~ 440");
  });

  test("a class that keeps its own maxclass gets it without being told", () => {
    // The README's own example had to spell this out as
    // `{ maxclass: "ezdac~", numinlets: 2, numoutlets: 0 }`.
    const box = new Patcher().add("ezdac~");

    expect(box.maxclass).toBe("ezdac~");
    expect(box.numinlets).toBe(2);
    expect(box.numoutlets).toBe(0);
  });

  test("port counts are per class, not the same guess for everything", () => {
    const p = new Patcher();

    // 1 in / 1 out, where the old default said 2 / 1.
    const mtof = p.add("mtof");
    expect([mtof.numinlets, mtof.numoutlets]).toEqual([1, 1]);

    // 1 in / 2 out, and its own box class.
    const gain = p.add("gain~");
    expect(gain.maxclass).toBe("gain~");
    expect([gain.numinlets, gain.numoutlets]).toEqual([1, 2]);
    expect(gain.outlettype).toEqual(["signal", ""]);
  });

  test("a UI box added with no text is keyed on its maxclass", () => {
    const box = new Patcher().add("", { maxclass: "toggle" });

    expect(box.numinlets).toBe(1);
    expect(box.numoutlets).toBe(1);
    expect(box).not.toHaveProperty("text");
  });

  test("an unknown class falls back rather than inventing a count", () => {
    // A third-party external has no table entry, and a `.maxpat` box must
    // state both counts -- so unlike `serialize`, which omits them and lets Max
    // derive them, this has to guess. The guess is the commonest shape.
    const box = new Patcher().add("some.external~ 1");

    expect(box.maxclass).toBe("newobj");
    expect(box.numinlets).toBe(2);
    expect(box.numoutlets).toBe(1);
    expect(box).not.toHaveProperty("outlettype");
  });
});

describe("what the caller states wins over the table", () => {
  test("an explicit count is kept, and the other is still derived", () => {
    const box = new Patcher().add("mtof", { numinlets: 3 });

    expect(box.numinlets).toBe(3);
    expect(box.numoutlets).toBe(1);
  });

  test("an explicit numoutlets suppresses the table's outlettype", () => {
    // Otherwise the two would describe different objects: three outlets and a
    // list of one type.
    const box = new Patcher().add("cycle~ 440", { numoutlets: 3 });

    expect(box.numoutlets).toBe(3);
    expect(box).not.toHaveProperty("outlettype");
  });

  test("an explicit maxclass is kept", () => {
    const box = new Patcher().add("ezdac~", { maxclass: "newobj" });

    expect(box.maxclass).toBe("newobj");
  });

  test("an explicit outlettype survives the derived one", () => {
    const box = new Patcher().add("cycle~ 440", { outlettype: ["bang"] });

    expect(box.outlettype).toEqual(["bang"]);
  });
});

describe("the shipped demo patch describes real objects", () => {
  test("gain~ is declared as the object it is", () => {
    // It was written by hand as 2 inlets / 2 outlets, and a gain~ has 1 inlet.
    const boxes = demoPatch().boxes.map((entry) => entry.box);
    const gain = boxes.find((box) => box.text === "gain~");

    expect(gain?.maxclass).toBe("gain~");
    expect(gain?.numinlets).toBe(1);
    expect(gain?.numoutlets).toBe(2);
  });

  test("every cord lands on a port its box declares", () => {
    // The point of getting the counts right: Max drops a patchline to a port
    // the box does not declare, silently, when the file opens.
    const patch = demoPatch();
    const byId = new Map(patch.boxes.map((entry) => [entry.box.id, entry.box]));

    for (const { patchline } of patch.lines) {
      const [fromId, outlet] = patchline.source;
      const [toId, inlet] = patchline.destination;
      expect(outlet).toBeLessThan(byId.get(fromId)?.numoutlets ?? 0);
      expect(inlet).toBeLessThan(byId.get(toId)?.numinlets ?? 0);
    }
  });
});
