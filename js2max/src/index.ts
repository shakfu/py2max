/**
 * js2max -- the TypeScript counterpart to py2max.
 *
 * Scope: the `.maxpat` format as types, plus a minimal Box/Patcher/Patchline
 * model and JSON round-trip. Out of scope by design: layout managers, maxref,
 * the SQLite database, the CLI and SVG export.
 *
 * See README.md for what the spike showed and the verdict against its decision
 * gate.
 */

export type {
  AppVersion,
  BoxDict,
  BoxEntry,
  BoxProps,
  Color,
  Endpoint,
  MaxPatchFile,
  PatcherDict,
  PatchlineDict,
  PatchlineEntry,
  Rect4,
} from "./format.ts";

export type {
  CommentBox,
  EzdacBox,
  MessageBox,
  NewobjBox,
  NumberBox,
  ToggleBox,
  TypedBox,
} from "./maxclass.ts";

export { describeBox } from "./maxclass.ts";
export { LoadedPatcher, MAX_VERSION, Patcher } from "./model.ts";
export type { AddBoxOptions, PatcherOptions } from "./model.ts";
