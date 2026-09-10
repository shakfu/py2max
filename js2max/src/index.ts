/// <reference path="./max.d.ts" />
/**
 * js2max -- the JavaScript counterpart to py2max.
 * 
 * It models the .maxpat format as types in typescript, provides an object model 
 * with JSON round-tripping, and includes bridges that turn a description into
 * a live patcher — and back again. Out of scope by design are layout managers,
 * maxref, the SQLite database, the CLI, and SVG export; those remain in Python
 * alongside its users and graph-layout libraries. See README.md.
 *
 * This is the entry point for TypeScript consumers. lib.v8.ts exposes the same
 * API bundled as CommonJS so it can be consumed with require() inside Max. The
 * two have drifted apart — this module lacks the bridge, file I/O, and serialize.
 * A reader who starts here may wrongly conclude that js2max can't do what it's 
 * meant to do.
 *
 * Everything reachable from here depends on Maxobj and MaxPatcher, which max.d.ts
 * declares as globals. Importing this module without also compiling max.d.ts will
 * fail.
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

export { maxDictFactory, readDictPatch } from "./dict.ts";
export type { DictFactory, DictOptions, MaxDict } from "./dict.ts";

export { serialize } from "./serialize.ts";
export type {
  IncompleteBox,
  SerializeOptions,
  SerializeResult,
} from "./serialize.ts";

export { demoPatch, synthPatch } from "./demo.ts";
