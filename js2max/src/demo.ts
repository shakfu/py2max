/**
 * A small patch description used to prove the v8 path end to end.
 *
 * Kept out of `entry.v8.ts` on purpose: that module assigns to `inlets` /
 * `outlets` / `autowatch` at load time, which only exist inside Max, so
 * importing it anywhere else throws. Everything worth testing therefore lives
 * outside the entry point, and the entry point stays pure glue.
 */

import type { PatcherDict, Rect4 } from "./format.ts";
import type { AddBoxOptions } from "./model.ts";
import { Patcher } from "./model.ts";

/** `cycle~ 440 -> gain~ -> ezdac~`, with the gain fanned to both dac inlets. */
export function demoPatch(): PatcherDict {
  const p = new Patcher();
  const osc = p.add("cycle~ 440");
  const gain = p.add("gain~", {
    maxclass: "gain~",
    numinlets: 2,
    numoutlets: 2,
  });
  const dac = p.add("ezdac~", {
    maxclass: "ezdac~",
    numinlets: 2,
    numoutlets: 0,
  });
  p.connect(osc, gain);
  p.connect(gain, dac, 0, 0);
  p.connect(gain, dac, 0, 1);
  return p.toPatcherDict();
}

/**
 * A richer patch than {@link demoPatch}, for exercising `write`.
 *
 * Serializing the harness produces something that resembles the harness, which
 * is a fair round-trip check but a poor demonstration -- you cannot tell a real
 * serialization from a file copy by looking. Building *this* into a nearly
 * empty patch and then writing it gives an output plainly unlike its input.
 *
 * Chosen to exercise the parts of `serialize` the harness does not: classes
 * that keep their own `maxclass` (`toggle`, `flonum`, `ezdac~`) alongside plain
 * object boxes, a signal chain, a control chain, and a fan-out to two inlets.
 */
export function synthPatch(): PatcherDict {
  const p = new Patcher();

  const ui = (maxclass: string, rect: Rect4, extra: AddBoxOptions = {}) =>
    p.add("", { maxclass, patching_rect: rect, ...extra });
  const obj = (text: string, rect: Rect4) =>
    p.add(text, { patching_rect: rect });

  const onoff = ui("toggle", [40, 40, 24, 24]);
  const metro = obj("metro 250", [40, 80, 70, 22]);
  const pick = obj("random 12", [40, 120, 70, 22]);
  const transpose = obj("+ 60", [40, 160, 45, 22]);
  const tofreq = obj("mtof", [40, 200, 45, 22]);
  const osc = obj("cycle~", [40, 240, 60, 22]);
  const amp = ui("flonum", [160, 240, 50, 22]);
  const gain = obj("*~ 0.2", [40, 280, 60, 22]);
  const out = ui("ezdac~", [40, 330, 45, 45]);

  p.connect(onoff, metro);
  p.connect(metro, pick);
  p.connect(pick, transpose);
  p.connect(transpose, tofreq);
  p.connect(tofreq, osc);
  p.connect(osc, gain);
  p.connect(amp, gain, 0, 1);
  p.connect(gain, out, 0, 0);
  p.connect(gain, out, 0, 1);

  return p.toPatcherDict();
}
