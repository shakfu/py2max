/**
 * The core, packaged for `require()` inside Max.
 *
 * `v8` supports CommonJS modules, so a user script can pull the model and the
 * bridge in and drive them itself rather than being limited to the message set
 * `entry.v8.ts` happens to expose:
 *
 *     var js2max = require("js2max.js");
 *
 *     function bang() {
 *         var p = new js2max.Patcher();
 *         var osc = p.add("cycle~ 440");
 *         var dac = p.add("ezdac~", { maxclass: "ezdac~", numinlets: 2 });
 *         p.connect(osc, dac, 0, 0);
 *         p.connect(osc, dac, 0, 1);
 *         var result = js2max.instantiate(this.patcher, p.toPatcherDict());
 *
 *         // to undo it later, remove what you built -- and never the box
 *         // running the script, which frees it mid-execution:
 *         // js2max.remove(this.patcher, result.objects.values(),
 *         //               { keep: [this.box] });
 *     }
 *
 * The same description can equally be written to disk by the Python package and
 * read here -- `instantiate` takes the parsed patcher either way, which is the
 * whole reason the format lives in types rather than in each implementation.
 *
 * ESM `import` is not supported by `v8`, so this is bundled to CommonJS. The
 * TypeScript source stays ES modules; only the artifact differs.
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

export { LoadedPatcher, MAX_VERSION, Patcher } from "./model.ts";
export type { AddBoxOptions, PatcherOptions } from "./model.ts";

export {
  clear,
  fromMaxobjRect,
  instantiate,
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

export { demoPatch } from "./demo.ts";
export { describeBox } from "./maxclass.ts";
