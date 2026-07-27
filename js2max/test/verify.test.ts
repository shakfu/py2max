/**
 * The in-Max checks, checked.
 *
 * `verifyBridge` exists to settle assumptions by running them inside Max, which
 * makes it the one piece of code whose own failure is hardest to notice: a
 * check that always reports "yes" is indistinguishable from an assumption that
 * holds, and a verification harness nobody verified is worth about as much as
 * the assumption it was meant to settle.
 *
 * So each check is driven both ways against the mock -- once with a host that
 * behaves as assumed, once with one that does not -- and must report the
 * difference. `MockPatcher` can be configured to fail in exactly the ways Max
 * might.
 */

import { describe, expect, test } from "bun:test";

import {
  diagnoseBridge,
  formatChecks,
  verifyBridge,
} from "../src/verify.ts";
import { MockPatcher, asHost, asObject } from "./mockhost.ts";

/** A host that behaves the way the bridge assumes Max does. */
function goodHost(): MockPatcher {
  return new MockPatcher({
    subpatcherClasses: ["p"],
    uiClasses: ["message"],
    // The class the unknown-class check names must actually be unknown.
    unknownClasses: ["js2max.nosuchobject~"],
    setFillsMessageBox: true,
  });
}

describe("every assumption holds against a host that behaves", () => {
  const result = verifyBridge(asHost(goodHost()));

  test("all four checks report that they held", () => {
    expect(result.checks).toHaveLength(5);
    for (const check of result.checks) {
      expect({ name: check.name, held: check.held }).toEqual({
        name: check.name,
        held: true,
      });
    }
  });

  test("each check says what it observed, not just whether it passed", () => {
    // The point of running in Max is the observation. A bare pass/fail would
    // not tell anyone what to change.
    for (const check of result.checks) {
      expect(check.observed.length).toBeGreaterThan(0);
      expect(check.assumption.length).toBeGreaterThan(0);
    }
  });

  test("the patcher is left as it was found", () => {
    const host = goodHost();
    const before = host.count;
    const run = verifyBridge(asHost(host));

    expect(run.removed).toBeGreaterThan(0);
    expect(host.count).toBe(before);
  });

  test("the script's own box is never removed by the cleanup", () => {
    const host = goodHost();
    const self = host.newdefault(0, 0, "v8", "js2max.v8.js");
    if (self === null) throw new Error("no self box");

    verifyBridge(asHost(host), asObject(self));

    expect(host.removed).not.toContain(self);
    expect(host.count).toBe(1); // just the [v8] box
  });
});

describe("a host that misbehaves is reported, not passed", () => {
  test("a message box that comes out empty is caught", () => {
    // The failure that matters most, and the one that actually happened: every
    // message box js2max built was empty, and the patch looked right while
    // doing nothing.
    const host = new MockPatcher({
      subpatcherClasses: ["p"],
      uiClasses: ["message"],
      unknownClasses: ["js2max.nosuchobject~"],
      newobjectIgnoresText: true,
    });

    const check = verifyBridge(asHost(host)).checks[0];
    expect(check?.name).toBe("message content");
    expect(check?.held).toBe(false);
    expect(check?.observed).toContain("boxtext");
  });

  test("newdefault throwing instead of returning null is caught", () => {
    // Both are handled by `instantiate`, but the reason it reports is only
    // accurate for one -- so a throw means every skipped-box log ever written
    // has described the cause wrongly.
    const host = new MockPatcher({
      subpatcherClasses: ["p"],
      uiClasses: ["message"],
      setFillsMessageBox: true,
      throwingClasses: ["js2max.nosuchobject~"],
    });

    const check = verifyBridge(asHost(host)).checks[1];
    expect(check?.name).toBe("unknown class");
    expect(check?.held).toBe(false);
    expect(check?.observed).toContain("threw");
  });

  test("a Max that quietly creates the unknown class is caught too", () => {
    // Neither null nor a throw: the check must not read "created something" as
    // success just because nothing was skipped.
    const host = new MockPatcher({
      subpatcherClasses: ["p"],
      uiClasses: ["message"],
      setFillsMessageBox: true,
    });

    const check = verifyBridge(asHost(host)).checks[1];
    expect(check?.held).toBe(false);
    expect(check?.observed).toContain("neither");
  });

  test("a subpatcher box that exposes no patcher is caught", () => {
    const host = new MockPatcher({
      uiClasses: ["message"],
      unknownClasses: ["js2max.nosuchobject~"],
      setFillsMessageBox: true,
      // no subpatcherClasses: `p` builds, but subpatcher() returns null
    });

    const check = verifyBridge(asHost(host)).checks[2];
    expect(check?.name).toBe("subpatcher");
    expect(check?.held).toBe(false);
    expect(check?.observed).toContain("subpatcher()");
  });
});

describe("the console report", () => {
  test("names the verdict, the check and the observation on each line", () => {
    const lines = formatChecks(verifyBridge(asHost(goodHost())));

    expect(lines).toHaveLength(6); // five checks plus the cleanup line
    expect(lines[0]).toContain("[yes]");
    expect(lines[0]).toContain("message content");
    expect(lines[5]).toContain("removed");
  });

  test("a failure is visually distinct in a wall of console output", () => {
    const host = new MockPatcher({
      subpatcherClasses: ["p"],
      uiClasses: ["message"],
      unknownClasses: ["js2max.nosuchobject~"],
      newobjectIgnoresText: true,
    });

    expect(formatChecks(verifyBridge(asHost(host)))[0]).toContain("[NO ]");
  });
});

describe("diagnose reports what the failed assumptions actually look like", () => {
  test("it tries every route a message box's content might arrive by", () => {
    // Three routes, because `verify` showed the assumed one does not work and
    // did not say which does. Each is reported whether or not it worked -- the
    // reading is done by a person looking at the console.
    const result = diagnoseBridge(asHost(goodHost()));
    const labels = result.observations.map((o) => o.label);

    expect(labels).toContain("message via set(1, 2, 3)");
    expect(labels).toContain("message via creation args");
    expect(labels).toContain('message via set("1 2 3")');
    for (const o of result.observations) {
      expect(o.detail.length).toBeGreaterThan(0);
    }
  });

  test("it builds a good box, an aliased box and a bogus one to compare", () => {
    // `maxclass === the class asked for` is the obvious detector for a box Max
    // could not build, and it is unsafe: Max resolves `t` to `trigger`, so an
    // alias would read as broken. All three are printed side by side for that
    // reason.
    const labels = diagnoseBridge(asHost(goodHost())).observations.map(
      (o) => o.label,
    );

    expect(labels.some((l) => l.indexOf("good box") >= 0)).toBe(true);
    expect(labels.some((l) => l.indexOf("aliased box") >= 0)).toBe(true);
    expect(labels.some((l) => l.indexOf("bogus box") >= 0)).toBe(true);
  });

  test("every readable field is reported for each box", () => {
    const good = diagnoseBridge(asHost(goodHost())).observations.find(
      (o) => o.label.indexOf("good box") >= 0,
    );

    for (const field of ["maxclass", "boxtext", "valid", "understands(bang)"]) {
      expect(good?.detail).toContain(field);
    }
  });

  test("a field that throws is reported rather than aborting the run", () => {
    // Reading an attribute off a box Max could not build is exactly the case
    // where a getter might refuse, and losing the whole diagnosis to it would
    // waste the run.
    const host = new MockPatcher({ unknownClasses: ["js2max.nosuchobject~"] });
    const result = diagnoseBridge(asHost(host));

    const bogus = result.observations.find((o) => o.label.indexOf("bogus") >= 0);
    expect(bogus?.detail).toBe("<not created>");
    expect(result.observations.length).toBeGreaterThan(5);
  });

  test("the patcher is left as it was found", () => {
    const host = goodHost();
    const before = host.count;
    const result = diagnoseBridge(asHost(host));

    expect(result.removed).toBeGreaterThan(0);
    expect(host.count).toBe(before);
  });
});

describe("against a host that behaves the way Max actually does", () => {
  /** Max's real answer for an unknown class: a `jbogus` placeholder box. */
  function realHost(): MockPatcher {
    return new MockPatcher({
      subpatcherClasses: ["p"],
      uiClasses: ["message"],
      bogusClasses: ["js2max.nosuchobject~"],
      setFillsMessageBox: true,
    });
  }

  test("the unknown-class check passes now that the placeholder is detected", () => {
    // It failed in Max before `jbogus` was known: `newdefault` returned a box,
    // so nothing was skipped and the check reported the assumption broken.
    const check = verifyBridge(asHost(realHost())).checks[1];

    expect(check?.name).toBe("unknown class");
    expect(check?.held).toBe(true);
    expect(check?.observed).toContain("unknown object class");
  });

  test("the placeholder does not survive as debris", () => {
    const host = realHost();
    const before = host.count;
    verifyBridge(asHost(host));

    expect(host.count).toBe(before);
  });
});

describe("the control that separates an empty box from an unreadable one", () => {
  test("a message box already in the patcher is read alongside the built ones", () => {
    // All three build routes reported boxtext="" in Max, which has two
    // readings: the box is empty, or boxtext does not report a *scripted*
    // message box's contents. A box that came from the file answers that --
    // if it reports its text and the built ones do not, the difference is how
    // the box was made.
    const host = new MockPatcher({ uiClasses: ["message"] });
    const existing = host.newdefault(0, 0, "message");
    existing!.boxtext = "already here";

    const control = diagnoseBridge(asHost(host)).observations[0];
    expect(control?.label).toContain("control");
    expect(control?.detail).toContain("already here");
  });

  test("it says so plainly when the patcher has none to compare against", () => {
    const control = diagnoseBridge(asHost(new MockPatcher())).observations[0];
    expect(control?.detail).toContain("none in this patcher");
  });
});

describe("locating where a message box keeps its content", () => {
  /** A patcher holding a file-loaded message box, as the harness does. */
  function withFileBox(): MockPatcher {
    const host = new MockPatcher({
      uiClasses: ["message"],
      setFillsMessageBox: true,
    });
    const existing = host.newdefault(0, 0, "message");
    existing!.boxtext = "diagnose";
    existing!.boxAttrs.set("textcolor", [0, 0, 0, 1]);
    return host;
  }

  test("the box attribute route is tried as well as the message routes", () => {
    // `getboxattr("text")` reads back null, but a write is a different
    // operation -- and Max's own `thispatcher` scripting sets a message box's
    // contents with `@text`, so the attribute exists somewhere.
    const labels = diagnoseBridge(asHost(withFileBox())).observations.map(
      (o) => o.label,
    );
    expect(labels).toContain('message via setboxattr("text")');
  });

  test("both message boxes are dumped attribute by attribute", () => {
    // The comparison that locates the content: if it is stored under some name,
    // the file-loaded box has it and the built one does not, and that name is
    // what serialize should be reading.
    const labels = diagnoseBridge(asHost(withFileBox())).observations.map(
      (o) => o.label,
    );

    expect(labels).toContain("built message box attrs");
    expect(labels).toContain("built message box objattrs");
    expect(labels).toContain("file message box attrs");
    expect(labels).toContain("file message box objattrs");
  });

  test("the dump reports values, not just names", () => {
    const dump = diagnoseBridge(asHost(withFileBox())).observations.find(
      (o) => o.label === "file message box attrs",
    );
    expect(dump?.detail).toContain("textcolor=");
  });

  test("the box the checks built is never mistaken for the file's", () => {
    // They are both `message` boxes in the same patcher; picking the wrong one
    // would compare a built box against itself and show no difference at all.
    const host = withFileBox();
    const dumps = diagnoseBridge(asHost(host)).observations.filter((o) =>
      o.label.startsWith("file message box"),
    );
    expect(dumps).toHaveLength(2);
    expect(dumps[0]?.detail).not.toBe("<none>");
  });
});

describe("the routes that do not go through newdefault", () => {
  test("newobject is tried in two shapes, and a throw is an answer", () => {
    // Every earlier route was `newdefault` plus something. `newobject` takes
    // the box's parameters explicitly, which is how a `.maxpat` describes a
    // box -- so if content can be given at creation at all, it is there. The
    // signature is not documented in a form that says what a message box
    // wants, so both plausible shapes are reported rather than picked between.
    const labels = diagnoseBridge(asHost(new MockPatcher())).observations.map(
      (o) => o.label,
    );

    expect(labels).toContain("newobject(message, x, y, 1, 2, 3)");
    expect(labels).toContain('newobject(message, x, y, w, 0, "1 2 3")');
  });

  test("the resize check reads the box before and after set", () => {
    // Independent of every accessor that has already answered: a message box
    // fits itself to its contents, so a width that does not move means nothing
    // reached the box, whatever `boxtext` says.
    const detail = diagnoseBridge(asHost(new MockPatcher())).observations.find(
      (o) => o.label === "does the box resize when set",
    )?.detail;

    expect(detail).toContain("before=");
    expect(detail).toContain("after=");
  });

  test("boxes made by newobject are cleaned up like the rest", () => {
    const host = new MockPatcher();
    const before = host.count;
    const result = diagnoseBridge(asHost(host));

    expect(result.removed).toBeGreaterThan(0);
    expect(host.count).toBe(before);
  });
});
