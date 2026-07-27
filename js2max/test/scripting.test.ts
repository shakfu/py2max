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
import { MockMaxobj, MockPatcher, asHost, asObject } from "./mockhost.ts";

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

  test("a message box is built with newobject, which is what fills it", () => {
    // Four routes through `newdefault` were tried in Max and every one left the
    // box empty: `set` with separate atoms, `set` with one symbol, the content
    // as creation arguments, and setboxattr("text"). The box was real -- its
    // attribute list matched a file-loaded message box exactly -- and it did
    // not even resize, which a message box does to fit its contents.
    //
    // `newobject` takes the box's parameters explicitly and does fill it. The
    // signature `(class, left, top, width, fontsize, ...atoms)` was decoded from
    // two calls whose results differed in exactly the way that identifies it.
    const p = new Patcher();
    p.add("1 2 3", {
      maxclass: "message",
      patching_rect: [10, 20, 60, 22],
      numinlets: 2,
      numoutlets: 1,
    });
    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict());

    // Ints, not the symbols `"1" "2" "3"`: content and typed-in arguments share
    // one tokenizer, and Max distinguishes the symbol `440` from the int `440`.
    expect(host.objects[0]?.created.args).toEqual([1, 2, 3]);
    expect(host.objects[0]?.boxtext).toBe("1 2 3");
    // No `set` any more: it demonstrably does nothing to a message box.
    expect(host.objects[0]?.messages).toEqual([]);
  });

  test("the atoms go separately, not joined into one symbol", () => {
    // The second probe call passed "1 2 3" whole and Max quoted it, producing a
    // box holding the literal string rather than three atoms.
    const p = new Patcher();
    p.add("1 2 3", { maxclass: "message", patching_rect: [10, 20, 60, 22] });
    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict());

    expect(host.objects[0]?.created.args).toHaveLength(3);
  });

  test("no box class is sent a set message any more", () => {
    // Four `set`-based routes were tried in Max and every one left the box
    // empty. Keeping the call would be cargo cult.
    const p = new Patcher();
    p.add("1 2", { maxclass: "message" });
    p.add("prose", { maxclass: "comment" });
    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict());

    for (const object of host.objects) expect(object.messages).toEqual([]);
  });

  test("a UI box that is not a message still takes no arguments", () => {
    // The creation-argument route is for message and comment boxes only: a
    // toggle has no content, and handing it arguments would be inventing some.
    const p = new Patcher();
    p.add("", { maxclass: "toggle" });
    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict());

    expect(host.objects[0]?.created.args).toEqual([]);
    expect(host.objects[0]?.messages).toEqual([]);
  });

  test("a comment is built the same way as a message box", () => {
    // Both content-carrying classes go through `newobject` now. Message boxes
    // were confirmed in Max first; comments followed on the same signature,
    // and `verify` check 5 holds them to the same standard rather than
    // assuming it.
    const p = new Patcher();
    p.add("440 Hz", {
      maxclass: "comment",
      patching_rect: [10, 20, 100, 22],
      numinlets: 1,
      numoutlets: 0,
    });
    const host = new MockPatcher();
    const result = instantiate(asHost(host), p.toPatcherDict());

    expect(host.objects[0]?.created.args).toEqual([440, "Hz"]);
    expect(host.objects[0]?.boxtext).toBe("440 Hz");
    expect(host.objects[0]?.messages).toEqual([]);
    // A comma in a comment is prose, not a separator, so nothing is warned.
    expect(result.warnings).toEqual([]);
  });

  test("only Max's own number syntax becomes a number", () => {
    // `Number()` would take all four. Max reads none of the first three as
    // numbers, so coercing them would rewrite an object's arguments: `gate
    // 0x10` is not `gate 16`.
    const p = new Patcher();
    p.add("obj 0x10 1e3 Infinity -2.5");
    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict());

    expect(host.objects[0]?.created.args).toEqual([
      "0x10",
      "1e3",
      "Infinity",
      -2.5,
    ]);
  });

  test("a box with no varname is left unnamed", () => {
    // The default, and it used to be the opposite. Naming every box after its
    // model id put a `varname` on boxes that never asked for one, which
    // serialize then wrote into the file -- a key py2max would not have
    // written, on a box that has no use for it.
    const p = new Patcher();
    p.add("cycle~ 440");
    const host = new MockPatcher();
    const result = instantiate(asHost(host), p.toPatcherDict());

    expect(host.objects[0]?.varname).toBe("");
    // Addressing what you built does not need a name: this is the mapping.
    expect(result.objects.size).toBe(1);
  });

  test("nameById opts back into scripting names", () => {
    // For when the name has to outlive the call -- a later message, another
    // object in the patch reaching in with getnamed.
    const p = new Patcher();
    const osc = p.add("cycle~ 440");
    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict(), { nameById: true });

    expect(host.getnamed(osc.id)).not.toBeNull();
  });

  test("a second build does not shadow the first's names", () => {
    // `getnamed` answers with the first match, so two builds both naming a box
    // `obj-1` would leave the second unreachable and the first answering for
    // it. Ids restart at obj-1 with every description.
    const p = new Patcher();
    p.add("cycle~ 440");
    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict(), { nameById: true });
    instantiate(asHost(host), p.toPatcherDict(), { nameById: true });

    expect(host.objects[0]?.varname).toBe("obj-1");
    expect(host.objects[1]?.varname).toBe("obj-1-2");
    expect(host.getnamed("obj-1")).toBe(host.objects[0] ?? null);
    expect(host.getnamed("obj-1-2")).toBe(host.objects[1] ?? null);
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
    expect(host.connections).toHaveLength(1);
    expect(host.connections[0]?.from).toBe(host.objects[0]);
    expect(host.connections[0]?.outlet).toBe(0);
    expect(host.connections[0]?.to).toBe(host.objects[1]);
    expect(host.connections[0]?.inlet).toBe(1);
    // The endpoints are the objects built for those two boxes.
    expect(result.objects.get(osc.id)).toBe(asObject(host.objects[0]!));
    expect(result.objects.get(dac.id)).toBe(asObject(host.objects[1]!));
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

  test("the offset stops at the subpatcher boundary", () => {
    // Regression: `offset` was forwarded into the recursion, so a nested box
    // was placed at the parent's offset plus its own position -- in a window
    // the offset means nothing in. A subpatcher's coordinates are its own.
    const p = new Patcher();
    const { sub } = p.addSubpatcher("p voice", {
      patching_rect: [10, 20, 66, 22],
    });
    sub.add("cycle~ 220", { patching_rect: [30, 40, 66, 22] });

    const host = new MockPatcher({ subpatcherClasses: ["p"] });
    instantiate(asHost(host), p.toPatcherDict(), { offset: [100, 200] });

    const box = host.objects[0];
    expect(box?.created.left).toBe(110); // the parent box does move
    expect(box?.created.top).toBe(220);

    const inner = box?.nested?.objects[0];
    expect(inner?.created.left).toBe(30); // its contents do not
    expect(inner?.created.top).toBe(40);
    expect(inner?.rect).toEqual([30, 40, 96, 62]);
  });
});

describe("a built box carries the description's appearance", () => {
  test("attributes the box reports are set on it", () => {
    // The asymmetry this closes: serialize preserves these, and instantiate
    // used to apply the rect and the varname and drop the rest, so file ->
    // live -> file came back stripped of everything the box looked like.
    const p = new Patcher();
    p.add("cycle~ 440", { hidden: 1, fontsize: 14 });
    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict());

    expect(host.objects[0]?.boxAttrs.get("hidden")).toBe(1);
    expect(host.objects[0]?.boxAttrs.get("fontsize")).toBe(14);
  });

  test("an array attribute goes as an atom list, not as one array", () => {
    // A Max attribute takes atoms: a colour is four arguments. Passing the
    // array whole would set one atom that happens to be a list.
    const p = new Patcher();
    p.add("cycle~ 440", { bgcolor: [0.1, 0.2, 0.3, 1] });
    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict());

    expect(host.objects[0]?.boxAttrs.get("bgcolor")).toEqual([0.1, 0.2, 0.3, 1]);
  });

  test("structure is never pushed back as an attribute", () => {
    // maxclass, the port counts and text are not box attributes at all --
    // getboxattr returns null for every one of them, confirmed in Max. They are
    // established by newdefault, and setting them is setting nothing.
    const p = new Patcher();
    p.add("cycle~ 440");
    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict());

    const written = host.objects[0]?.messages ?? [];
    expect(written).toEqual([]); // no message traffic either
    for (const name of ["maxclass", "numinlets", "numoutlets", "text", "id"]) {
      expect(host.objects[0]?.boxAttrs.get(name)).toBeUndefined();
    }
  });

  test("an attribute the box does not report is not attempted", () => {
    // Asking a box for an attribute it does not have is how the Max console
    // fills up over a file that is otherwise fine. `getboxattrnames()` is the
    // box's own answer to what it accepts.
    const p = new Patcher();
    p.add("cycle~ 440", { prototypename: "not-a-real-box-attr" });
    const host = new MockPatcher();
    const result = instantiate(asHost(host), p.toPatcherDict());

    expect(host.objects[0]?.boxAttrs.get("prototypename")).toBeUndefined();
    expect(result.warnings).toEqual([]); // not attempted is not a failure
  });

  test("applyAttributes: false leaves the box alone", () => {
    const p = new Patcher();
    p.add("cycle~ 440", { hidden: 1 });
    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict(), { applyAttributes: false });

    expect(host.objects[0]?.boxAttrs.get("hidden")).toBeUndefined();
  });

  test("an attribute the object refuses is reported, and the build goes on", () => {
    const p = new Patcher();
    p.add("cycle~ 440", { hidden: 1, fontsize: 14 });
    p.add("saw~ 220");

    const host = new MockPatcher({ refusedBoxAttrs: ["hidden"] });
    const result = instantiate(asHost(host), p.toPatcherDict());

    expect(result.created).toBe(2); // both boxes still built
    expect(result.skipped).toEqual([]);
    expect(result.warnings).toHaveLength(1);
    expect(result.warnings[0]?.reason).toContain("hidden");
    // One refusal does not abandon the rest of the box.
    expect(host.objects[0]?.boxAttrs.get("fontsize")).toBe(14);
  });

  test("a subpatcher's boxes get their attributes too", () => {
    const p = new Patcher();
    const { sub } = p.addSubpatcher("p voice");
    sub.add("cycle~ 220", { hidden: 1 });

    const host = new MockPatcher({ subpatcherClasses: ["p"] });
    instantiate(asHost(host), p.toPatcherDict());

    expect(host.objects[0]?.nested?.objects[0]?.boxAttrs.get("hidden")).toBe(1);
  });
});

describe("instantiate reports what it built unfaithfully", () => {
  test("a message box's separators cannot survive a set message", () => {
    // `1, 2` is two messages in Max -- an A_COMMA atom between them. Nothing
    // the JS API offers produces one, so the box gets an ordinary symbol and
    // the caller is told rather than left to discover it by clicking.
    const p = new Patcher();
    const box = p.add("1, 2", { maxclass: "message" });
    const host = new MockPatcher();
    const result = instantiate(asHost(host), p.toPatcherDict());

    expect(result.created).toBe(1); // built, not skipped
    expect(result.skipped).toEqual([]);
    expect(result.warnings).toHaveLength(1);
    expect(result.warnings[0]?.id).toBe(box.id);
    expect(result.warnings[0]?.reason).toContain("separator");
  });

  test("a semicolon counts too", () => {
    const p = new Patcher();
    p.add("; foo bang", { maxclass: "message" });
    const host = new MockPatcher();

    expect(instantiate(asHost(host), p.toPatcherDict()).warnings).toHaveLength(
      1,
    );
  });

  test("an ordinary message box warns about nothing", () => {
    const p = new Patcher();
    p.add("start", { maxclass: "message" });
    const host = new MockPatcher();

    expect(instantiate(asHost(host), p.toPatcherDict()).warnings).toEqual([]);
  });

  test("a warning from inside a subpatcher reaches the caller", () => {
    const p = new Patcher();
    const { sub } = p.addSubpatcher("p voice");
    sub.add("1, 2", { maxclass: "message" });

    const host = new MockPatcher({ subpatcherClasses: ["p"] });
    const result = instantiate(asHost(host), p.toPatcherDict());

    expect(result.warnings).toHaveLength(1);
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
    expect(result.objects.get(good.id)).toBeDefined();
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

  test("a second handle on the same box is still kept", () => {
    // The API does not promise two reads of an object give the same wrapper --
    // `snapshot` already assumes they may not. Matching `keep` by identity
    // alone means that assumption fails open on the one call whose failure
    // frees the running script, so class and position are matched as well.
    const p = new Patcher();
    p.add("v8 js2max.v8.js");
    p.add("cycle~ 440");

    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict());
    const self = host.objects[0];
    if (self === undefined) throw new Error("nothing built");

    // A distinct wrapper designating the same box: same class, same rect.
    const otherHandle = new MockMaxobj(self.maxclass, self.created, host);
    otherHandle.rect = [...self.rect];
    expect(otherHandle).not.toBe(self);

    const removed = clear(asHost(host), { keep: [asObject(otherHandle)] });

    expect(removed).toBe(1);
    expect(host.removed).not.toContain(self);
  });

  test("a scripting name is enough on its own", () => {
    const p = new Patcher();
    p.add("v8 js2max.v8.js", { varname: "the-script" });
    p.add("cycle~ 440");

    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict());
    const self = host.objects[0];
    if (self === undefined) throw new Error("nothing built");

    // Same name, different class and position: still the same box.
    const otherHandle = new MockMaxobj("something-else", self.created, host);
    otherHandle.varname = "the-script";
    otherHandle.rect = [999, 999, 999, 999];

    expect(clear(asHost(host), { keep: [asObject(otherHandle)] })).toBe(1);
    expect(host.removed).not.toContain(self);
  });

  test("a different box at a different place is not kept by mistake", () => {
    const p = new Patcher();
    p.add("cycle~ 440", { patching_rect: [10, 10, 66, 22] });
    p.add("cycle~ 880", { patching_rect: [10, 90, 66, 22] });

    const host = new MockPatcher();
    instantiate(asHost(host), p.toPatcherDict());
    const first = host.objects[0];
    if (first === undefined) throw new Error("nothing built");

    // Same class as the second box, but nowhere near it.
    expect(clear(asHost(host), { keep: [asObject(first)] })).toBe(1);
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

describe("a class Max cannot build is detected, not counted as built", () => {
  // Settled by running `diagnose` in Max. `newdefault` returns neither null nor
  // a throw for an unknown class: Max logs `No such object` and hands back a
  // real box whose maxclass is `jbogus`. Everything else about it looks healthy
  // -- `valid` is 1 and `boxtext` is the text asked for -- so before this,
  // `instantiate` reported it as successfully created and the patch quietly
  // gained a dead box.
  const bogus = () =>
    new MockPatcher({ bogusClasses: ["js2max.nosuchobject~"] });

  test("the placeholder is reported as an unknown class", () => {
    const p = new Patcher();
    const dead = p.add("js2max.nosuchobject~ 1");
    const host = bogus();
    const result = instantiate(asHost(host), p.toPatcherDict());

    expect(result.created).toBe(0);
    expect(result.skipped).toHaveLength(1);
    expect(result.skipped[0]?.id).toBe(dead.id);
    expect(result.skipped[0]?.reason).toContain("unknown object class");
    expect(result.skipped[0]?.reason).toContain("jbogus");
  });

  test("the placeholder box is removed rather than left in the patcher", () => {
    // `skipped` means "not built". A caller that trusts it would otherwise be
    // handed a patcher containing a box it was told nothing about.
    const p = new Patcher();
    p.add("js2max.nosuchobject~ 1");
    const host = bogus();
    instantiate(asHost(host), p.toPatcherDict());

    expect(host.count).toBe(0);
  });

  test("the rest of the patch still builds, and cords to it are skipped", () => {
    const p = new Patcher();
    const dead = p.add("js2max.nosuchobject~ 1");
    const good = p.add("cycle~ 440");
    p.connect(dead, good);
    const host = bogus();
    const result = instantiate(asHost(host), p.toPatcherDict());

    expect(result.created).toBe(1);
    expect(result.connected).toBe(0);
    expect(result.objects.get(good.id)).toBeDefined();
    expect(result.skipped).toHaveLength(2); // the box, and the cord to it
  });

  test("an alias is not mistaken for a placeholder", () => {
    // The reason the detector is the class name `jbogus` and not "maxclass
    // differs from what was asked for": Max resolves aliases, and `t b i` comes
    // back as `trigger`. The naive test would call every alias broken.
    const p = new Patcher();
    p.add("t b i");
    const host = new MockPatcher({ bogusClasses: ["js2max.nosuchobject~"] });
    const object = host.newdefault(0, 0, "trigger", "b", "i");
    expect(object?.maxclass).toBe("trigger");

    const result = instantiate(asHost(host), p.toPatcherDict());
    expect(result.skipped).toEqual([]);
    expect(result.created).toBe(1);
  });
});

describe("an object that will not enumerate its attributes", () => {
  test("getattrnames returning null does not crash the build", () => {
    // `trigger` and `jbogus` both return null rather than an array or an error,
    // observed in Max. A `try` around the call does not help: the null arrives
    // cleanly and the TypeError lands wherever the result is first used.
    const p = new Patcher();
    p.add("t b i", { hidden: 1 });
    const host = new MockPatcher({ nullAttrNames: ["t"] });

    const result = instantiate(asHost(host), p.toPatcherDict());
    expect(result.created).toBe(1);
    expect(host.objects[0]?.boxAttrs.get("hidden")).toBe(1);
  });
});
