/**
 * Tests for the model -> live-patcher bridge.
 *
 * Driven against `MockPatcher`, which records the Patcher-API calls the bridge
 * makes. What this proves: the mapping from a patch description to
 * `newdefault`/`connect` calls is correct. What it cannot prove: that Max
 * accepts those calls. See `patchers/v8-harness.maxpat`.
 */

import { describe, expect, test } from "bun:test";

import { Patcher } from "../src/model.ts";
import {
  clear,
  fromMaxobjRect,
  instantiate,
  remove,
  snapshot,
  toMaxobjRect,
} from "../src/scripting.ts";
import { demoPatch } from "../src/demo.ts";
import { MockPatcher, asHost, asObject } from "./mockhost.ts";

describe("rect conventions", () => {
  test("patching_rect [x,y,w,h] converts to Maxobj rect [l,t,r,b]", () => {
    expect(toMaxobjRect([10, 20, 100, 50])).toEqual([10, 20, 110, 70]);
  });

  test("the conversion round-trips", () => {
    expect(fromMaxobjRect(toMaxobjRect([10, 20, 100, 50]))).toEqual([
      10, 20, 100, 50,
    ]);
  });
});

describe("instantiate", () => {
  test("a newobj box becomes newdefault(x, y, class, ...typed args)", () => {
    const p = new Patcher();
    p.add("cycle~ 440", { patching_rect: [10, 20, 66, 22] });

    const host = new MockPatcher();
    const result = instantiate(asHost(host), p.toPatcherDict());

    expect(result.created).toBe(1);
    expect(result.skipped).toEqual([]);
    expect(host.objects[0]?.created).toEqual({
      left: 10,
      top: 20,
      className: "cycle~",
      args: [440],
    });
  });

  test("numeric arguments are numbers, not symbols", () => {
    const p = new Patcher();
    p.add("scale 0 127 0. 1.");
    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict());

    expect(host.objects[0]?.created.args).toEqual([0, 127, 0, 1]);
  });

  test("non-numeric arguments stay symbols", () => {
    const p = new Patcher();
    p.add("route bang stop 1");
    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict());

    expect(host.objects[0]?.created.args).toEqual(["bang", "stop", 1]);
  });

  test("a UI box uses its maxclass and takes no typed arguments", () => {
    const p = new Patcher();
    p.add("", { maxclass: "toggle", numinlets: 1, numoutlets: 1 });
    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict());

    expect(host.objects[0]?.created.className).toBe("toggle");
    expect(host.objects[0]?.created.args).toEqual([]);
  });

  test("a message box gets its content via a set message, not arguments", () => {
    const p = new Patcher();
    p.add("1 2 3", { maxclass: "message", numinlets: 2, numoutlets: 1 });
    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict());

    expect(host.objects[0]?.created.args).toEqual([]);
    expect(host.objects[0]?.messages).toEqual([
      { name: "set", args: ["1", "2", "3"] },
    ]);
  });

  test("objects are named after their model id so getnamed can find them", () => {
    const p = new Patcher();
    const osc = p.add("cycle~ 440");
    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict());

    expect(host.getnamed(osc.id)).not.toBeNull();
  });

  test("an explicit varname wins over the model id", () => {
    const p = new Patcher();
    p.add("cycle~ 440", { varname: "osc" });
    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict());

    expect(host.objects[0]?.varname).toBe("osc");
  });

  test("connections carry the right port indices", () => {
    const p = new Patcher();
    const osc = p.add("cycle~ 440");
    const dac = p.add("ezdac~", { maxclass: "ezdac~" });
    p.connect(osc, dac, 0, 1);

    const host = new MockPatcher();
    const result = instantiate(asHost(host), p.toPatcherDict());

    expect(result.connected).toBe(1);
    expect(host.connections).toEqual([
      { from: osc.id, outlet: 0, to: dac.id, inlet: 1 },
    ]);
  });

  test("offset shifts every position", () => {
    const p = new Patcher();
    p.add("cycle~ 440", { patching_rect: [10, 20, 66, 22] });
    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict(), { offset: [100, 200] });

    expect(host.objects[0]?.created.left).toBe(110);
    expect(host.objects[0]?.created.top).toBe(220);
    expect(host.objects[0]?.rect).toEqual([110, 220, 176, 242]);
  });

  test("subpatchers are built recursively", () => {
    const p = new Patcher();
    const { sub } = p.addSubpatcher("p voice");
    sub.add("cycle~ 220");
    sub.add("gain~", { maxclass: "gain~" });

    const host = new MockPatcher({ subpatcherClasses: ["p"] });
    const result = instantiate(asHost(host), p.toPatcherDict());

    expect(result.created).toBe(3); // the p box, plus two inside it
    expect(host.objects[0]?.nested?.count).toBe(2);
  });
});

describe("instantiate collects failures rather than throwing", () => {
  test("an unknown object class is skipped, and the rest still build", () => {
    const p = new Patcher();
    p.add("nosuchobject~ 1");
    const good = p.add("cycle~ 440");

    const host = new MockPatcher({ unknownClasses: ["nosuchobject~"] });
    const result = instantiate(asHost(host), p.toPatcherDict());

    expect(result.created).toBe(1);
    expect(result.skipped).toHaveLength(1);
    expect(result.skipped[0]?.reason).toContain("unknown object class");
    expect(host.getnamed(good.id)).not.toBeNull();
  });

  test("a patchline to a box that failed is skipped, not fatal", () => {
    const p = new Patcher();
    const missing = p.add("nosuchobject~ 1");
    const dac = p.add("ezdac~", { maxclass: "ezdac~" });
    p.connect(missing, dac);

    const host = new MockPatcher({ unknownClasses: ["nosuchobject~"] });
    const result = instantiate(asHost(host), p.toPatcherDict());

    expect(result.connected).toBe(0);
    expect(host.connections).toEqual([]);
    expect(result.skipped.map((s) => s.reason)).toEqual([
      expect.stringContaining("unknown object class"),
      expect.stringContaining("references a box that was not created"),
    ]);
  });
});

describe("clear", () => {
  test("removes every object", () => {
    const p = new Patcher();
    p.add("cycle~ 440");
    p.add("gain~", { maxclass: "gain~" });
    p.add("ezdac~", { maxclass: "ezdac~" });

    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict());
    expect(host.count).toBe(3);

    const removed = clear(asHost(host));
    expect(removed).toBe(3);
    expect(host.count).toBe(0);
  });
});

describe("snapshot", () => {
  test("reads live objects back, converting rects", () => {
    const p = new Patcher();
    p.add("cycle~ 440", { patching_rect: [10, 20, 66, 22], varname: "osc" });

    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict());

    expect(snapshot(asHost(host)).boxes).toEqual([
      {
        id: "osc",
        maxclass: "cycle~",
        patching_rect: [10, 20, 66, 22],
        varname: "osc",
      },
    ]);
  });

  test("reads connections back from patchcords", () => {
    // Regression for a wrong claim: this used to return boxes only, on the
    // basis that the JS API could not enumerate patchlines. `Maxobj.patchcords`
    // does exactly that.
    const p = new Patcher();
    const osc = p.add("cycle~ 440", { varname: "osc" });
    const dac = p.add("ezdac~", { maxclass: "ezdac~", varname: "dac" });
    p.connect(osc, dac, 0, 1);

    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict());

    const shot = snapshot(asHost(host));
    expect(shot.unresolved).toBe(0);
    expect(shot.lines).toEqual([
      { source: ["osc", 0], destination: ["dac", 1] },
    ]);
  });

  test("each cord is reported once, not once per endpoint", () => {
    const p = new Patcher();
    const a = p.add("cycle~ 440");
    const b = p.add("gain~", { maxclass: "gain~" });
    p.connect(a, b, 0, 0);

    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict());

    expect(snapshot(asHost(host)).lines).toHaveLength(1);
  });

  test("unnamed objects get positional ids", () => {
    const p = new Patcher();
    p.add("cycle~ 440");

    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict(), { nameById: false });

    expect(snapshot(asHost(host)).boxes[0]?.id).toBe("obj-1");
  });
});

describe("the demo patch", () => {
  test("builds a three-object signal chain with a stereo pair", () => {
    const host = new MockPatcher();
    const result = instantiate(asHost(host), demoPatch());

    expect(result.created).toBe(3);
    expect(result.connected).toBe(3);
    expect(result.skipped).toEqual([]);
    expect(host.objects.map((o) => o.created.className)).toEqual([
      "cycle~",
      "gain~",
      "ezdac~",
    ]);
  });
});

describe("clear never deletes the script's own box", () => {
  // Regression test for a failure observed in Max: `clear` removed every
  // object, the `[v8]` box included, so the script carried on against a freed
  // pointer and the next post() reported `bad object` / `corrupt object`.

  test("clear skips objects in keep", () => {
    const p = new Patcher();
    p.add("cycle~ 440");
    p.add("gain~", { maxclass: "gain~" });

    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict());
    const self = host.objects[0];
    if (self === undefined) throw new Error("nothing built");

    const removed = clear(asHost(host), { keep: [asObject(self)] });

    expect(removed).toBe(1);
    expect(host.count).toBe(1);
    expect(host.firstobject).toBe(self);
    expect(host.removed).not.toContain(self);
  });

  test("remove takes only the objects it is given", () => {
    const p = new Patcher();
    const osc = p.add("cycle~ 440");
    p.add("gain~", { maxclass: "gain~" });

    const host = new MockPatcher();
    const result = instantiate(asHost(host), p.toPatcherDict());
    const oscObject = result.objects.get(osc.id);
    if (oscObject === undefined) throw new Error("nothing built");

    expect(remove(asHost(host), [oscObject])).toBe(1);
    expect(host.count).toBe(1);
    expect(host.objects[0]?.maxclass).toBe("gain~");
  });

  test("remove honours keep, so a caller cannot delete itself by accident", () => {
    const p = new Patcher();
    p.add("cycle~ 440");

    const host = new MockPatcher();
    const result = instantiate(asHost(host), p.toPatcherDict());
    const everything = [...result.objects.values()];
    const self = everything[0];
    if (self === undefined) throw new Error("nothing built");

    expect(remove(asHost(host), everything, { keep: [self] })).toBe(0);
    expect(host.count).toBe(1);
  });
});

describe("hidden patchcords", () => {
  test("a hidden line uses hiddenconnect, not connect", () => {
    // `patchline.hidden` used to be dropped silently: instantiate always called
    // connect, so a hidden cord came back visible.
    const p = new Patcher();
    const osc = p.add("cycle~ 440");
    const dac = p.add("ezdac~", { maxclass: "ezdac~" });
    const line = p.connect(osc, dac, 0, 0);
    (line as { hidden?: number }).hidden = 1;

    const host = new MockPatcher();
    const result = instantiate(asHost(host), p.toPatcherDict());

    expect(result.connected).toBe(1);
    expect(host.connections[0]?.hidden).toBe(true);
  });

  test("an ordinary line stays visible", () => {
    const p = new Patcher();
    const osc = p.add("cycle~ 440");
    const dac = p.add("ezdac~", { maxclass: "ezdac~" });
    p.connect(osc, dac, 0, 0);

    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict());

    expect(host.connections[0]?.hidden).toBeUndefined();
  });
});

describe("removed objects report themselves invalid", () => {
  test("valid goes false after remove, as Maxobj.valid does", () => {
    const p = new Patcher();
    p.add("cycle~ 440");

    const host = new MockPatcher();
    const result = instantiate(asHost(host), p.toPatcherDict());
    const object = [...result.objects.values()][0];
    if (object === undefined) throw new Error("nothing built");

    expect((object as unknown as { valid: boolean }).valid).toBe(true);
    remove(asHost(host), [object]);
    expect((object as unknown as { valid: boolean }).valid).toBe(false);
  });
});
