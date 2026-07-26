/// <reference path="./max.d.ts" />
/**
 * js2max -- the JavaScript counterpart to py2max.
 *
 * The `.maxpat` format as types, an object model with a JSON round-trip, a
 * bridge that builds a description into a live patcher, and the reverse. Out of
 * scope by design: layout managers, maxref, the SQLite database, the CLI and
 * SVG export -- those stay in Python, where the users and the graph-layout
 * libraries are. See README.md.
 *
 * This is the entry point for TypeScript consumers; `lib.v8.ts` is the same
 * surface bundled as CommonJS for `require()` inside Max. The two had drifted,
 * with this one missing the bridge, the file I/O and `serialize` -- so a reader
 * who started here would conclude js2max could not do the thing it exists for.
 *
 * The reference above is load-bearing, not tidiness. Everything reachable from
 * here now touches `Maxobj` and `MaxPatcher`, which `max.d.ts` declares as
 * ambient globals -- so a program that imports this module and does not compile
 * that file fails with 28 "Cannot find name" errors that are nothing to do with
 * the consumer's code. The directive pulls it in.
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

export { APP_VERSION, OWN_MAXCLASS, PORTS, boxClassOf } from "./objects.ts";
export type { PortEntry } from "./objects.ts";

export {
  clear,
  fromMaxobjRect,
  instantiate,
  objectsOf,
  remove,
  snapshot,
  toMaxobjRect,
} from "./scripting.ts";
export type {
  ClearOptions,
  InstantiateOptions,
  InstantiateResult,
  SkippedBox,
} from "./scripting.ts";

export {
  maxFileFactory,
  readPatch,
  readText,
  writePatch,
  writeText,
} from "./fileio.ts";
export type { FileAccess, FileFactory, FileOptions, MaxFile } from "./fileio.ts";

export { serialize } from "./serialize.ts";
export type {
  IncompleteBox,
  SerializeOptions,
  SerializeResult,
} from "./serialize.ts";

export { demoPatch, synthPatch } from "./demo.ts";
