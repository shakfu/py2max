/**
 * Per-maxclass box variants as a discriminated union.
 *
 * The second half of the spike's type-system claim: a union discriminated on
 * `maxclass` lets the checker prove a `switch` covers every case, and lets each
 * variant carry only the properties that make sense for it. Python's closest
 * equivalent is a `Literal` type plus `assert_never`, which works but does not
 * constrain the *properties* per variant -- `**kwds: Any` accepts anything
 * regardless of maxclass.
 *
 * This is a representative slice, not the full ~1175-object vocabulary; the real
 * version would be generated from the maxref bundle.
 */

import type { BoxProps, Rect4 } from "./format.ts";

interface Common extends BoxProps {
  id: string;
  numinlets: number;
  numoutlets: number;
  patching_rect: Rect4;
}

/** `newobj` -- a typed-in object box. `text` is what makes it meaningful. */
export interface NewobjBox extends Common {
  maxclass: "newobj";
  text: string;
}

/** `message` -- a clickable message box. */
export interface MessageBox extends Common {
  maxclass: "message";
  text?: string;
}

/** `comment` -- inert text. Cannot be a connection source. */
export interface CommentBox extends Common {
  maxclass: "comment";
  text?: string;
  numoutlets: 0;
}

/** `toggle` -- 0/1 switch. */
export interface ToggleBox extends Common {
  maxclass: "toggle";
}

/** `flonum` / `number` -- number boxes. */
export interface NumberBox extends Common {
  maxclass: "flonum" | "number";
  minimum?: number;
  maximum?: number;
}

/** `ezdac~` -- stereo output. Two inlets, no outlets. */
export interface EzdacBox extends Common {
  maxclass: "ezdac~";
  numinlets: 2;
  numoutlets: 0;
}

export type TypedBox =
  | NewobjBox
  | MessageBox
  | CommentBox
  | ToggleBox
  | NumberBox
  | EzdacBox;

/**
 * Where a box's label comes from, per class.
 *
 * The `never` in the default branch is the exhaustiveness proof: add a variant
 * to {@link TypedBox} without handling it here and `tsc` fails this function.
 * Delete a `case` and it fails too. Python cannot make the compiler do this for
 * a dict-shaped model.
 */
export function describeBox(box: TypedBox): string {
  switch (box.maxclass) {
    case "newobj":
      return box.text;
    case "message":
      return `message: ${box.text ?? "(empty)"}`;
    case "comment":
      return `comment: ${box.text ?? "(empty)"}`;
    case "toggle":
      return "toggle";
    case "flonum":
    case "number":
      return `number box (${box.minimum ?? "-inf"}..${box.maximum ?? "inf"})`;
    case "ezdac~":
      return "ezdac~";
    default: {
      const unreachable: never = box;
      return unreachable;
    }
  }
}
