/**
 * Tests for live patcher -> `.maxpat`.
 *
 * The mock defines what `getboxattr` / `boxtext` return, so these check the
 * *logic* -- which accessor wins, what counts as complete, what happens when a
 * box cannot be described -- not that Max behaves this way. The harness settles
 * that.
 */

import { describe, expect, test } from "bun:test";

import { serialize } from "../src/serialize.ts";
import { Patcher } from "../src/model.ts";
import { instantiate } from "../src/scripting.ts";
import { synthPatch } from "../src/demo.ts";
import { MockPatcher, asHost } from "./mockhost.ts";

function built(patch: (p: Patcher) => void): MockPatcher {
  const p = new Patcher();
  patch(p);
  const host = new MockPatcher();
  instantiate(asHost(host), p.toPatcherDict());
  return host;
}

describe("serialize produces boxes Max can load", () => {
  test("an object box is maxclass newobj carrying its text", () => {
    // The defect that withdrew the first attempt: it wrote maxclass "cycle~"
    // with no text. The box class comes from getboxattr, the text from boxtext.
    const host = built((p) => {
      p.add("cycle~ 440");
    });
    const { patcher, incomplete } = serialize(asHost(host));

    expect(incomplete).toEqual([]);
    const box = patcher.boxes[0]?.box;
    expect(box?.maxclass).toBe("newobj");
    expect(box?.text).toBe("cycle~ 440");
    expect(box?.id).toBe("obj-1");
  });

  test("a class in OWN_MAXCLASS keeps it", () => {
    const host = built((p) => {
      p.add("", { maxclass: "toggle" });
    });
    const box = serialize(asHost(host)).patcher.boxes[0]?.box;

    expect(box?.maxclass).toBe("toggle");
    expect(box?.numinlets).toBe(1);
    expect(box?.numoutlets).toBe(1);
  });

  test("a comment keeps its class, and its text is the content", () => {
    // Straight from the probe: a comment reports maxclass "comment" and its
    // boxtext is the comment's words, not "comment ...".
    const host = new MockPatcher();
    const object = host.newdefault(10, 10, "comment");
    object!.boxtext = "some prose here";

    const box = serialize(asHost(host)).patcher.boxes[0]?.box;
    expect(box?.maxclass).toBe("comment");
    expect(box?.text).toBe("some prose here");
  });

  test("port counts come from the class table, since Max will not report them", () => {
    // getboxattr("numinlets") returns null in Max; the counts are static per
    // class and come from py2max via objects.ts.
    const host = built((p) => {
      p.add("cycle~ 440", { patching_rect: [10, 20, 66, 22] });
    });
    const box = serialize(asHost(host)).patcher.boxes[0]?.box;

    expect(box?.numinlets).toBe(2);
    expect(box?.numoutlets).toBe(1);
    expect(box?.outlettype).toEqual(["signal"]);
    expect(box?.patching_rect).toEqual([10, 20, 66, 22]);
  });

  test("an unknown class omits port counts rather than guessing", () => {
    // A third-party external has no table entry. Max derives ports from the
    // instantiated object, so omitting beats inventing a count that would
    // silently drop patchcords on load.
    const host = built((p) => {
      p.add("some.external~ 1");
    });
    const box = serialize(asHost(host)).patcher.boxes[0]?.box;

    expect(box?.maxclass).toBe("newobj");
    expect(box?.text).toBe("some.external~ 1");
    expect(box).not.toHaveProperty("numinlets");
    expect(box).not.toHaveProperty("numoutlets");
  });

  test("connections are emitted against the assigned ids", () => {
    const host = built((p) => {
      const osc = p.add("cycle~ 440");
      const dac = p.add("ezdac~", { maxclass: "ezdac~" });
      p.connect(osc, dac, 0, 1);
    });
    const { patcher } = serialize(asHost(host));

    expect(patcher.lines).toEqual([
      { patchline: { source: ["obj-1", 0], destination: ["obj-2", 1] } },
    ]);
  });

  test("the result round-trips through the model unchanged", () => {
    const host = built((p) => {
      const osc = p.add("cycle~ 440");
      const gain = p.add("gain~", { maxclass: "gain~" });
      p.connect(osc, gain);
    });
    const { patcher } = serialize(asHost(host));

    const reparsed = Patcher.fromFile({ patcher });
    expect(reparsed.boxes).toHaveLength(2);
    expect(reparsed.lines).toHaveLength(1);
  });
});

describe("serialize refuses to emit a box it cannot describe", () => {
  test("a box missing its text is reported, not written", () => {
    // An object box without text reopens empty: silent data loss rather than a
    // load failure, which is why it counts as incomplete.
    const host = built((p) => {
      p.add("cycle~ 440");
      p.add("saw~ 220");
    });
    const broken = host.objects[0];
    broken!.boxtext = undefined;

    const { patcher, incomplete } = serialize(asHost(host));

    expect(patcher.boxes).toHaveLength(1);
    expect(incomplete).toHaveLength(1);
    expect(incomplete[0]?.missing).toEqual(["text"]);
  });

  test("a box with no readable rect is reported", () => {
    const host = built((p) => {
      p.add("cycle~ 440");
    });
    host.objects[0]?.boxAttrs.delete("patching_rect");
    (host.objects[0] as unknown as { rect: unknown }).rect = null;

    const { incomplete } = serialize(asHost(host));
    expect(incomplete[0]?.missing).toEqual(["patching_rect"]);
  });

  test("a cord to a dropped box is dropped too, never left dangling", () => {
    const host = built((p) => {
      const osc = p.add("cycle~ 440");
      const dac = p.add("ezdac~", { maxclass: "ezdac~" });
      p.connect(osc, dac);
    });
    host.objects[0]!.boxtext = undefined;

    const { patcher, incomplete } = serialize(asHost(host));

    expect(incomplete).toHaveLength(1);
    expect(patcher.lines).toEqual([]); // would have referenced a missing id
  });

  test("emitIncomplete opts into the broken box anyway", () => {
    const host = built((p) => {
      p.add("cycle~ 440");
    });
    host.objects[0]!.boxtext = undefined;

    const { patcher, incomplete } = serialize(asHost(host), {
      emitIncomplete: true,
    });
    expect(incomplete).toHaveLength(1);
    expect(patcher.boxes).toHaveLength(0); // still not emitted, but id is kept
  });
});

describe("attribute selection", () => {
  test("optional attributes are carried when set", () => {
    const host = built((p) => {
      p.add("cycle~ 440", { varname: "osc" });
    });
    host.objects[0]?.boxAttrs.set("varname", "osc");
    host.objects[0]?.boxAttrs.set("hidden", 1);

    const box = serialize(asHost(host)).patcher.boxes[0]?.box;
    expect(box?.varname).toBe("osc");
    expect(box?.hidden).toBe(1);
  });

  test("defaults are not written back", () => {
    // Max omits an attribute left at its default and gives no way to ask which
    // those are. A wider list wrote nine keys onto every box and took a 7 KB
    // patch to 18 KB. Falsy flags are dropped; colours are out of the default
    // set entirely; fonts are kept but filtered against the patcher's own
    // defaults, which is the one case Max gives us a reference for.
    const host = built((p) => {
      p.add("cycle~ 440");
    });
    host.attrs.set("default_fontsize", 12);
    host.objects[0]?.boxAttrs.set("hidden", 0);
    host.objects[0]?.boxAttrs.set("presentation", 0);
    host.objects[0]?.boxAttrs.set("fontsize", 12);
    host.objects[0]?.boxAttrs.set("bgcolor", [0, 0, 0, 1]);

    const box = serialize(asHost(host)).patcher.boxes[0]?.box;
    expect(box).not.toHaveProperty("hidden");
    expect(box).not.toHaveProperty("presentation");
    expect(box).not.toHaveProperty("fontsize");
    expect(box).not.toHaveProperty("bgcolor");
  });

  test("allAttributes picks up anything getboxattrnames reports", () => {
    const host = built((p) => {
      p.add("cycle~ 440");
    });
    host.objects[0]?.boxAttrs.set("some_exotic_attr", 7);

    const curated = serialize(asHost(host)).patcher.boxes[0]
      ?.box as unknown as Record<string, unknown>;
    expect(curated["some_exotic_attr"]).toBeUndefined();

    const all = serialize(asHost(host), { allAttributes: true }).patcher
      .boxes[0]?.box as unknown as Record<string, unknown>;
    expect(all["some_exotic_attr"]).toBe(7);
  });

  test("id and patcher are never copied from box attributes", () => {
    const host = built((p) => {
      p.add("cycle~ 440");
    });
    host.objects[0]?.boxAttrs.set("id", "obj-999");
    host.objects[0]?.boxAttrs.set("patcher", { boxes: [] });

    const box = serialize(asHost(host), { allAttributes: true }).patcher
      .boxes[0]?.box;
    expect(box?.id).toBe("obj-1");
    expect(box?.patcher).toBeUndefined();
  });
});

describe("boxtext is the only source of a box's text", () => {
  test("without boxtext, an object box is incomplete -- there is no fallback", () => {
    // The probe showed `text` is not among the names getboxattrnames() reports,
    // so nothing else can supply it. `boxtext` is v8-only, which means the
    // legacy `js` engine cannot serialize a patcher at all.
    const host = built((p) => {
      p.add("cycle~ 440");
    });
    host.objects[0]!.boxtext = undefined;

    const { patcher, incomplete } = serialize(asHost(host));
    expect(patcher.boxes).toHaveLength(0);
    expect(incomplete[0]?.missing).toEqual(["text"]);
  });

  test("a class that keeps its own maxclass survives without text", () => {
    // Only an object box needs text: `maxclass: "toggle"` is self-describing.
    const host = new MockPatcher();
    host.newdefault(10, 10, "toggle");

    const { patcher, incomplete } = serialize(asHost(host));
    expect(incomplete).toEqual([]);
    expect(patcher.boxes[0]?.box.maxclass).toBe("toggle");
  });
});

describe("object-level attributes", () => {
  test("are absent by default", () => {
    const host = built((p) => {
      p.add("v8 script.js");
    });
    host.objects[0]?.objectAttrs.set("embed", 1);

    const box = serialize(asHost(host)).patcher.boxes[0]?.box;
    expect(box).not.toHaveProperty("saved_object_attributes");
  });

  test("records only what the object has beyond its box", () => {
    // Measured in Max: a [v8] box reports these four via getattrnames() and
    // nothing else -- notably not `filename` or `textfile`.
    const host = built((p) => {
      p.add("v8 script.js");
    });
    const object = host.objects[0];
    object?.objectAttrs.set("embed", 1);
    object?.objectAttrs.set("parameter_enable", 0); // a default, dropped
    object?.objectAttrs.set("annotation_name", "osc");

    const box = serialize(asHost(host), { objectAttributes: true }).patcher
      .boxes[0]?.box;

    expect(box?.saved_object_attributes).toEqual({
      embed: 1,
      annotation_name: "osc",
    });
  });

  test("a UI box records nothing, because its two lists are identical", () => {
    // Confirmed in Max: for a comment, getattrnames() and getboxattrnames()
    // return the same 33 names. Reading both would write every box attribute a
    // second time under saved_object_attributes.
    const host = new MockPatcher();
    const object = host.newdefault(10, 10, "comment");
    object!.boxtext = "prose";
    for (const name of object!.boxAttrs.keys()) {
      object!.objectAttrs.set(name, "duplicate");
    }

    const box = serialize(asHost(host), { objectAttributes: true }).patcher
      .boxes[0]?.box;
    expect(box).not.toHaveProperty("saved_object_attributes");
  });

  test("a value the JS bridge cannot represent is skipped", () => {
    // Reading `textfile` on a [v8] box returns a Max object, and logs
    // `v8_wrapobject: couldn't wrap instance of class textfile`.
    const host = built((p) => {
      p.add("v8 script.js");
    });
    host.objects[0]?.objectAttrs.set("embed", 1);
    host.objects[0]?.objectAttrs.set("weird", { some: "object" });

    const box = serialize(asHost(host), { objectAttributes: true }).patcher
      .boxes[0]?.box;
    expect(box?.saved_object_attributes).toEqual({ embed: 1 });
  });

  test("keys already written as box keys are not duplicated", () => {
    const host = built((p) => {
      p.add("cycle~ 440", { varname: "osc" });
    });
    host.objects[0]?.boxAttrs.set("varname", "osc");
    host.objects[0]?.objectAttrs.set("varname", "something-else");
    host.objects[0]?.boxAttrs.delete("varname");
    host.objects[0]?.boxAttrs.set("varname", "osc");

    const box = serialize(asHost(host), { objectAttributes: true }).patcher
      .boxes[0]?.box;

    expect(box?.varname).toBe("osc");
    expect(box?.saved_object_attributes).toBeUndefined();
  });

  test("defaults are dropped here too", () => {
    const host = built((p) => {
      p.add("v8 script.js");
    });
    host.objects[0]?.objectAttrs.set("parameter_enable", 0);
    host.objects[0]?.objectAttrs.set("annotation_name", "");

    const box = serialize(asHost(host), { objectAttributes: true }).patcher
      .boxes[0]?.box;
    expect(box).not.toHaveProperty("saved_object_attributes");
  });

  test("a host without getattrnames degrades rather than throwing", () => {
    const host = built((p) => {
      p.add("v8 script.js");
    });
    (host.objects[0] as unknown as { getattrnames: () => string[] }).getattrnames =
      () => {
        throw new Error("not supported");
      };

    const result = serialize(asHost(host), { objectAttributes: true });
    expect(result.incomplete).toEqual([]);
    expect(result.patcher.boxes).toHaveLength(1);
  });
});

describe("the synth demo, as a serialize exercise", () => {
  test("round-trips through build and serialize with nothing incomplete", () => {
    const host = new MockPatcher();
    instantiate(asHost(host), synthPatch());

    const { patcher, incomplete } = serialize(asHost(host));

    expect(incomplete).toEqual([]);
    expect(patcher.boxes).toHaveLength(9);
    expect(patcher.lines).toHaveLength(9);
  });

  test("covers both box kinds, which the harness alone does not", () => {
    const host = new MockPatcher();
    instantiate(asHost(host), synthPatch());
    const classes = serialize(asHost(host)).patcher.boxes.map(
      (e) => e.box.maxclass,
    );

    // classes that keep their own maxclass, and plain object boxes
    expect(classes).toContain("toggle");
    expect(classes).toContain("flonum");
    expect(classes).toContain("ezdac~");
    expect(classes).toContain("newobj");
  });

  test("a fan-out to two inlets survives", () => {
    const host = new MockPatcher();
    instantiate(asHost(host), synthPatch());
    const { patcher } = serialize(asHost(host));

    const toDac = patcher.lines.filter(
      (l) => l.patchline.destination[0] === "obj-9",
    );
    expect(toDac.map((l) => l.patchline.destination[1]).sort()).toEqual([0, 1]);
  });
});

describe("fonts are judged against the patcher's defaults", () => {
  test("a font matching the patcher default is omitted", () => {
    const host = new MockPatcher();
    host.attrs.set("default_fontsize", 12);
    const object = host.newdefault(10, 10, "comment");
    object!.boxtext = "prose";
    object!.boxAttrs.set("fontsize", 12);

    const box = serialize(asHost(host)).patcher.boxes[0]?.box;
    expect(box).not.toHaveProperty("fontsize");
  });

  test("a font differing from it survives", () => {
    // Regression: dropping fonts wholesale lost a comment deliberately set to
    // 14pt; including them wrote Max's default onto every box.
    const host = new MockPatcher();
    host.attrs.set("default_fontsize", 12);
    const object = host.newdefault(10, 10, "comment");
    object!.boxtext = "prose";
    object!.boxAttrs.set("fontsize", 14);

    const box = serialize(asHost(host)).patcher.boxes[0]?.box;
    expect(box?.fontsize).toBe(14);
  });

  test("a host with no patcher defaults keeps whatever it finds", () => {
    const host = new MockPatcher();
    const object = host.newdefault(10, 10, "comment");
    object!.boxtext = "prose";
    object!.boxAttrs.set("fontsize", 12);

    const box = serialize(asHost(host)).patcher.boxes[0]?.box;
    expect(box?.fontsize).toBe(12);
  });
});

describe("exporting only what was built", () => {
  test("only the given objects appear, not the whole patcher", () => {
    // "save this patcher" and "export what I built" are different requests.
    // A script that builds an instrument into a host patch wants the
    // instrument, not the [v8] box and messages that built it.
    const host = new MockPatcher();
    host.newdefault(0, 0, "v8 script.js"); // the host patch's own furniture
    host.newdefault(0, 40, "comment");

    const result = instantiate(asHost(host), synthPatch());
    const { patcher, incomplete } = serialize(asHost(host), {
      only: [...result.objects.values()],
    });

    expect(incomplete).toEqual([]);
    expect(patcher.boxes).toHaveLength(9);
    expect(host.count).toBe(11); // the patcher still holds everything
    const texts = patcher.boxes.map((b) => b.box.text ?? "");
    expect(texts.some((t) => t.includes("script.js"))).toBe(false);
  });

  test("cords are kept only where both ends are in the set", () => {
    const host = new MockPatcher();
    const result = instantiate(asHost(host), synthPatch());
    const objects = [...result.objects.values()];

    // drop the oscillator: its cords in and out must go with it
    const withoutOsc = objects.filter((o) => o.maxclass !== "cycle~");
    const { patcher } = serialize(asHost(host), { only: withoutOsc });

    expect(patcher.boxes).toHaveLength(8);
    expect(patcher.lines).toHaveLength(7); // 9 minus mtof->cycle~ and cycle~->*~
  });

  test("ids are renumbered for the exported subset", () => {
    const host = new MockPatcher();
    host.newdefault(0, 0, "comment");
    const result = instantiate(asHost(host), synthPatch());

    const { patcher } = serialize(asHost(host), {
      only: [...result.objects.values()],
    });
    expect(patcher.boxes[0]?.box.id).toBe("obj-1");
    expect(patcher.lines[0]?.patchline.source[0]).toBe("obj-1");
  });

  test("a removed object is skipped rather than read after free", () => {
    const host = new MockPatcher();
    const result = instantiate(asHost(host), synthPatch());
    const objects = [...result.objects.values()];
    host.remove(objects[0] as unknown as import("./mockhost.ts").MockMaxobj);

    const { patcher } = serialize(asHost(host), { only: objects });
    expect(patcher.boxes).toHaveLength(8);
  });
});

describe("a description written directly beats one round-tripped", () => {
  test("the description survives verbatim; nothing has to be read back", () => {
    // The reason `save` exists. A description is already the shape of a
    // .maxpat, so writing it is exact by construction -- no accessor, no
    // default to guess at, no live patcher.
    const source = synthPatch();
    const written = JSON.parse(JSON.stringify({ patcher: source }));

    expect(written.patcher).toEqual(source);
  });

  test("the round trip is bounded by what the JS API exposes", () => {
    // Serializing has to rebuild every field from an accessor, and some fields
    // have none: `print` has no maxref numoutlets, so it is omitted for Max to
    // derive. Fine for a patch Max will open, lossy as an export format.
    const host = new MockPatcher();
    instantiate(asHost(host), synthPatch());
    const roundTripped = serialize(asHost(host)).patcher;

    expect(roundTripped.boxes).toHaveLength(synthPatch().boxes.length);
    for (const entry of roundTripped.boxes) {
      expect(entry.box).toHaveProperty("maxclass");
      expect(entry.box).toHaveProperty("patching_rect");
    }
  });
});
