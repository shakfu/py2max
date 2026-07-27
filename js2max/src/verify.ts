/**
 * The assumptions the bridge rests on, turned into checks that run in Max.
 *
 * Everything in `scripting.ts` is tested against `MockPatcher`, which proves
 * the *mapping* is right and proves nothing about whether Max accepts the
 * calls. These are the assumptions the rest of the bridge rests on. Two of the
 * first four were false when this was written, and each cost a real bug:
 *
 *   1. A message box built from a description ends up holding its text.
 *      It did not: `newdefault` cannot fill one by any route, and every message
 *      box js2max built was empty while the patch looked right.
 *   2. `newdefault` reports a class Max does not have. It does not -- it
 *      returns a `jbogus` placeholder and logs to the console, so unknown
 *      classes went undetected entirely.
 *   3. A box carrying a nested patcher exposes it through `subpatcher()`, so
 *      recursion reaches the contents. True.
 *   4. A comment ends up holding its text. Added after the message box was
 *      fixed, since the fix was extended to comments by inference.
 *   5. `snapshot` reads a live patcher's boxes and cords. True.
 *
 * Each check builds what it needs, observes, and takes it away again. The
 * observations are returned rather than posted, so the same code runs under
 * `bun test` against the mock -- a verification harness that has never been run
 * is worth about as much as the assumption it was meant to settle.
 */

import type { PatcherDict } from "./format.ts";
import { Patcher } from "./model.ts";
import {
  attrNamesOf,
  instantiate,
  objectsOf,
  remove as removeObjects,
  snapshot,
} from "./scripting.ts";

/**
 * Where a check builds, and why there.
 *
 * A column below a typical patcher window rather than far off in the canvas:
 * these boxes exist for a few microseconds and are removed in a `finally`, so
 * nobody should ever see them -- but if cleanup ever fails, the debris wants to
 * be one scroll away and in an obvious line, not somewhere the user has to hunt
 * for it.
 */
const AWAY = [24, 560] as const;

/** Vertical step between the boxes a check builds. */
const STEP = 32;

export interface Check {
  /** Short name, for the log. */
  name: string;
  /** The assumption, phrased so that "held" is unambiguous. */
  assumption: string;
  /** What was actually observed, in enough detail to act on. */
  observed: string;
  /**
   * Whether the assumption held.
   *
   * `undefined` for a check that could not run at all -- which is itself worth
   * seeing, and is not the same as a failure.
   */
  held: boolean | undefined;
}

export interface VerifyResult {
  checks: Check[];
  /** Objects the checks created and then removed again. */
  removed: number;
}

/** A description holding one message box with known content. */
function messageBoxPatch(): PatcherDict {
  const p = new Patcher();
  p.add("1 2 3", {
    maxclass: "message",
    patching_rect: [AWAY[0], AWAY[1], 60, 22],
  });
  return p.toPatcherDict();
}

/** A description holding one comment with known content. */
function commentPatch(): PatcherDict {
  const p = new Patcher();
  p.add("js2max check 440 Hz", {
    maxclass: "comment",
    patching_rect: [AWAY[0], AWAY[1] + STEP * 6, 140, 22],
  });
  return p.toPatcherDict();
}

/** A description naming a class Max cannot possibly have. */
function unknownClassPatch(): PatcherDict {
  const p = new Patcher();
  p.add("js2max.nosuchobject~ 1", {
    patching_rect: [AWAY[0], AWAY[1] + STEP, 160, 22],
  });
  return p.toPatcherDict();
}

/** A description with a subpatcher holding two boxes. */
function subpatcherPatch(): PatcherDict {
  const p = new Patcher();
  const { sub } = p.addSubpatcher("p js2max_check", {
    patching_rect: [AWAY[0], AWAY[1] + STEP * 2, 110, 22],
  });
  sub.add("cycle~ 220", { patching_rect: [40, 40, 70, 22] });
  sub.add("gain~", { patching_rect: [40, 80, 22, 140] });
  return p.toPatcherDict();
}

/**
 * Run every check against a live patcher, leaving it as it was found.
 *
 * `self` is the box running the script, which cleanup must never remove --
 * doing so frees the object out from under the running code.
 */
export function verifyBridge(
  target: MaxPatcher,
  self?: Maxobj,
): VerifyResult {
  const checks: Check[] = [];
  const built: Maxobj[] = [];
  let removed = 0;

  try {
    // 1. Does `set` fill a message box?
    //
    // Read back through `boxtext`, which the probe established is the only
    // accessor for a box's text -- and which `serialize` already depends on, so
    // a failure here is a failure in both directions at once.
    const message = instantiate(target, messageBoxPatch());
    built.push(...message.objects.values());
    const box = [...message.objects.values()][0];
    const text = box?.boxtext;
    checks.push({
      name: "message content",
      assumption: 'a message box built from a description holds "1 2 3"',
      observed:
        box === undefined
          ? "no message box was created at all"
          : `boxtext = ${JSON.stringify(text ?? null)}`,
      held: box === undefined ? undefined : (text ?? "").trim() === "1 2 3",
    });

    // 2. Null or throw for an unknown class?
    //
    // Both are handled, but the reason `instantiate` reports is only accurate
    // for one of them, and a throw would mean every skipped box in every log
    // has been described wrongly.
    const unknown = instantiate(target, unknownClassPatch());
    built.push(...unknown.objects.values());
    const reason = unknown.skipped[0]?.reason ?? "";
    checks.push({
      name: "unknown class",
      assumption: "an object class Max does not have is detected and reported",
      observed:
        unknown.created > 0
          ? `Max created an object for "js2max.nosuchobject~" -- neither`
          : reason === ""
            ? "nothing was created and nothing was reported"
            : reason,
      held:
        unknown.created > 0
          ? false
          : reason.indexOf("unknown object class") >= 0,
    });

    // 3. Does a subpatcher box expose its patcher?
    const sub = instantiate(target, subpatcherPatch());
    built.push(...sub.objects.values());
    const subSkips = sub.skipped.filter(
      (s) => s.reason.indexOf("subpatcher()") >= 0,
    );
    checks.push({
      name: "subpatcher",
      assumption: "a box with a nested patcher builds its contents too",
      observed:
        `created ${sub.created} object(s) ` +
        `(1 box + 2 inside expected)` +
        (subSkips.length > 0 ? `; ${subSkips[0]?.reason}` : ""),
      held: sub.created === 3 && subSkips.length === 0,
    });

    // 4. Does a comment get its content?
    //
    // Added after the message box was fixed. A comment goes by the same
    // `newobject` signature, on the reasoning that both are content-carrying
    // boxes -- which is an inference, not an observation, and this is what
    // keeps it from staying one.
    const comment = instantiate(target, commentPatch());
    built.push(...comment.objects.values());
    const commentBox = [...comment.objects.values()][0];
    const commentText = commentBox?.boxtext;
    checks.push({
      name: "comment content",
      assumption: "newobject gives a comment its text, as it does a message box",
      observed:
        commentBox === undefined
          ? "no comment was created at all"
          : `boxtext = ${JSON.stringify(commentText ?? null)}`,
      held:
        commentBox === undefined
          ? undefined
          : (commentText ?? "").trim() === "js2max check 440 Hz",
    });

    // 5. Can a live patcher be read back?
    //
    // Runs last, so it sees everything the checks above built -- which makes
    // its counts non-trivial rather than a reading of an empty patcher.
    const shot = snapshot(target);
    checks.push({
      name: "snapshot",
      assumption: "snapshot reads boxes and cords from a live patcher",
      observed:
        `${shot.boxes.length} box(es), ${shot.lines.length} cord(s), ` +
        `${shot.unresolved} unresolved`,
      held: shot.boxes.length > 0 && shot.unresolved === 0,
    });
  } finally {
    // Whatever happened above, the patcher goes back to how it was found. A
    // check that throws half way still cleans up after itself, or a failed run
    // leaves debris in someone's patch.
    removed = removeObjects(target, built, {
      keep: self === undefined ? [] : [self],
    });
  }

  return { checks, removed };
}

/** One thing looked at, and what it said. */
export interface Observation {
  label: string;
  detail: string;
}

/** Everything readable about one live object, for comparing against another. */
function describeObject(object: Maxobj | undefined): string {
  if (object === undefined) return "<not created>";
  const read = (name: string, fn: () => unknown): string => {
    try {
      return `${name}=${JSON.stringify(fn()) ?? "undefined"}`;
    } catch (err) {
      return `${name}=<threw ${String(err)}>`;
    }
  };
  return [
    read("maxclass", () => object.maxclass),
    read("boxtext", () => object.boxtext),
    read("valid", () => object.valid),
    read("understands(bang)", () => object.understands("bang")),
    read("boxattrs", () => object.getboxattrnames().length),
    // `?.` rather than a bare `.length`: this is the exact call that reported
    // `<threw TypeError>` for `trigger` and `jbogus` in Max, which is how the
    // null came to light. Now that it is known, report it as the answer it is.
    read("objattrs", () => object.getattrnames()?.length ?? null),
  ].join(" ");
}

/**
 * The two questions `verify` left open, put to Max as experiments.
 *
 * A check reports whether an assumption held. When one does not, the next thing
 * needed is not another verdict but the shape of the thing that broke it -- so
 * this builds several variants side by side and prints what each reports, and
 * the reading is done afterwards by a person.
 *
 * **A. How does a message box get its content?** `verify` showed that creating
 * one and sending it `set` leaves `boxtext` empty. Three routes are tried:
 * `set` afterwards, arguments at creation, and `set` with the content as a
 * single symbol rather than separate atoms.
 *
 * **B. What does a failed `newdefault` return?** Not null, which is what the
 * bridge assumed -- Max logs `No such object` and hands back a box anyway, so
 * `instantiate` has never detected an unknown class and the patch silently
 * gets a dead box. Detecting it needs a field that tells a broken box from a
 * working one, and the obvious candidate (`maxclass` equals the class asked
 * for) is unsafe, because Max resolves aliases: `t` becomes `trigger`. So a
 * known-good box, an aliased box and a bogus one are built together and every
 * readable field printed for all three. Whatever distinguishes the third is
 * the detector.
 *
 * Creating the bogus box logs `No such object` to the Max console. That is this
 * function doing its job, not a fault.
 */
export function diagnoseBridge(
  target: MaxPatcher,
  self?: Maxobj,
): { observations: Observation[]; removed: number } {
  const observations: Observation[] = [];
  const built: Maxobj[] = [];
  let removed = 0;

  const make = (
    x: number,
    y: number,
    className: string,
    ...args: (string | number)[]
  ): Maxobj | undefined => {
    try {
      const object = target.newdefault(x, y, className, ...args);
      if (object === null || object === undefined) return undefined;
      built.push(object);
      return object;
    } catch (err) {
      observations.push({
        label: `newdefault("${className}")`,
        detail: `threw: ${String(err)}`,
      });
      return undefined;
    }
  };

  try {
    // A0. The control, and the question the first round left open.
    //
    // All three routes below reported `boxtext = ""`, which has two readings:
    // the box is genuinely empty, or `boxtext` does not report a *scripted*
    // message box's contents. The original probe showed `boxtext` reading a
    // message box correctly -- but that box came from a file. So: read one that
    // came from a file, here, in the same run. If this reports its text and the
    // built ones do not, the difference is how the box was made, not `boxtext`.
    const fromFile = objectsOf(target).find(
      (object) => object.maxclass === "message",
    );
    observations.push({
      label: "control: a message box loaded from the patch file",
      detail:
        fromFile === undefined
          ? "<none in this patcher -- open the harness, which has several>"
          : `boxtext=${JSON.stringify(fromFile.boxtext ?? null)}`,
    });

    // A. Which route fills a message box?
    const viaSet = make(AWAY[0], AWAY[1], "message");
    viaSet?.message("set", 1, 2, 3);
    observations.push({
      label: "message via set(1, 2, 3)",
      detail: `boxtext=${JSON.stringify(viaSet?.boxtext ?? null)}`,
    });

    const viaArgs = make(AWAY[0], AWAY[1] + STEP, "message", 1, 2, 3);
    observations.push({
      label: "message via creation args",
      detail: `boxtext=${JSON.stringify(viaArgs?.boxtext ?? null)}`,
    });

    const viaSymbol = make(AWAY[0], AWAY[1] + STEP * 2, "message");
    viaSymbol?.message("set", "1 2 3");
    observations.push({
      label: 'message via set("1 2 3")',
      detail: `boxtext=${JSON.stringify(viaSymbol?.boxtext ?? null)}`,
    });

    // A fourth route: the box attribute directly. `getboxattr("text")` reads
    // back null, established by the original probe -- but a write is a
    // different operation, and Max's own `thispatcher` scripting sets a message
    // box's contents with `@text`, so the attribute plainly exists somewhere.
    const viaAttr = make(AWAY[0], AWAY[1] + STEP * 3, "message");
    try {
      viaAttr?.setboxattr("text", "1 2 3");
    } catch (err) {
      observations.push({
        label: 'message via setboxattr("text")',
        detail: `threw: ${String(err)}`,
      });
    }
    observations.push({
      label: 'message via setboxattr("text")',
      detail:
        `boxtext=${JSON.stringify(viaAttr?.boxtext ?? null)} ` +
        `getboxattr(text)=${JSON.stringify(viaAttr?.getboxattr("text") ?? null)}`,
    });

    // Does the box react to `set` at all?
    //
    // A message box sizes itself to its contents. If `set` reaches it and only
    // `boxtext` is stale, the width should change; if the box is the same size
    // before and after, nothing arrived. Cheap, and independent of every
    // accessor that has already answered.
    const sized = make(AWAY[0], AWAY[1] + STEP * 4, "message");
    const before = JSON.stringify(sized?.getboxattr("patching_rect") ?? null);
    sized?.message("set", "wwwwwwwwwwwwwwwwwwww");
    const after = JSON.stringify(sized?.getboxattr("patching_rect") ?? null);
    observations.push({
      label: "does the box resize when set",
      detail: `before=${before} after=${after} (a message box fits its content)`,
    });

    // `newobject`, which is a different call, not a different argument.
    //
    // Every route so far has been `newdefault` plus something. `newobject`
    // takes the box's parameters explicitly rather than defaulting them, which
    // is how a `.maxpat` box is described -- so if content can be given at
    // creation at all, this is where. The signature is not documented in a form
    // that says what a message box wants, so two plausible shapes are tried and
    // both reported; a throw is an answer too.
    for (const [label, args] of [
      ["newobject(message, x, y, 1, 2, 3)", [AWAY[0], AWAY[1] + STEP * 5, 1, 2, 3]],
      [
        'newobject(message, x, y, w, 0, "1 2 3")',
        [AWAY[0], AWAY[1] + STEP * 6, 100, 0, "1 2 3"],
      ],
    ] as const) {
      try {
        const object = target.newobject("message", ...args);
        if (object !== null && object !== undefined) built.push(object);
        observations.push({
          label,
          detail: `boxtext=${JSON.stringify(object?.boxtext ?? null)} maxclass=${JSON.stringify(object?.maxclass ?? null)}`,
        });
      } catch (err) {
        observations.push({ label, detail: `threw: ${String(err)}` });
      }
    }

    // Where does the content live, if not in `boxtext`?
    //
    // The control settled that `boxtext` works -- a message box from the file
    // reports its text -- so a built one reading `""` means either the content
    // is genuinely absent, or it is set and `boxtext` reports the box's
    // *stored* text, which a scripted box only acquires when the patch is
    // saved. Those need different fixes and nothing so far separates them.
    //
    // So: every attribute of a built message box and a file-loaded one, with
    // values, side by side. If the content is in there under some name, this
    // finds it and the fix is to read that. If neither box has it anywhere, the
    // content really is missing and the fix is a different way of creating it.
    const fileBox = objectsOf(target).find(
      (object) => object.maxclass === "message" && !built.includes(object),
    );
    for (const [label, object] of [
      ["built message box", viaSet],
      ["file message box", fileBox],
    ] as const) {
      if (object === undefined) {
        observations.push({ label: `${label} attrs`, detail: "<none>" });
        continue;
      }
      const dump = (kind: string, names: string[]): string =>
        names.length === 0
          ? `${kind}=<none>`
          : `${kind}: ` +
            names
              .map((name) => {
                try {
                  const value =
                    kind === "box"
                      ? object.getboxattr(name)
                      : object.getattr(name);
                  return `${name}=${JSON.stringify(value) ?? "undefined"}`;
                } catch {
                  return `${name}=<threw>`;
                }
              })
              .join(" ");
      observations.push({
        label: `${label} attrs`,
        detail: dump("box", attrNamesOf(() => object.getboxattrnames())),
      });
      observations.push({
        label: `${label} objattrs`,
        detail: dump("obj", attrNamesOf(() => object.getattrnames())),
      });
    }

    // B. What distinguishes a box Max could not build?
    observations.push({
      label: "-- the next line is expected in the console --",
      detail: "Max logs `No such object` for the bogus class below",
    });
    const good = make(AWAY[0], AWAY[1] + STEP * 3, "cycle~", 440);
    observations.push({ label: "good box (cycle~ 440)", detail: describeObject(good) });

    const alias = make(AWAY[0], AWAY[1] + STEP * 4, "t", "b", "i");
    observations.push({
      label: "aliased box (t b i)",
      detail: describeObject(alias),
    });

    const broken = make(
      AWAY[0],
      AWAY[1] + STEP * 5,
      "js2max.nosuchobject~",
      1,
    );
    observations.push({
      label: "bogus box (js2max.nosuchobject~ 1)",
      detail: describeObject(broken),
    });
  } finally {
    removed = removeObjects(target, built, {
      keep: self === undefined ? [] : [self],
    });
  }

  return { observations, removed };
}

/** The observations as lines for the Max console. */
export function formatDiagnosis(result: {
  observations: Observation[];
  removed: number;
}): string[] {
  const lines = result.observations.map(
    (o) => `js2max diagnose: ${o.label} -- ${o.detail}`,
  );
  lines.push(`js2max diagnose: removed ${result.removed} object(s)`);
  return lines;
}

/** The checks as lines for the Max console. */
export function formatChecks(result: VerifyResult): string[] {
  const lines = result.checks.map((check, index) => {
    const verdict =
      check.held === undefined ? "???" : check.held ? "yes" : "NO ";
    return (
      `js2max verify ${index + 1}/${result.checks.length} [${verdict}] ` +
      `${check.name}: ${check.observed}`
    );
  });
  lines.push(
    `js2max verify: removed ${result.removed} object(s); ` +
      `patcher left as found`,
  );
  return lines;
}
