/**
 * Build the two Max-loadable artifacts.
 *
 * `v8` supports CommonJS `require()` but not ESM `import`, so this core -- which
 * is written as ES modules -- has to be flattened before Max can load it. Two
 * shapes, for two ways of using it:
 *
 *   max/js2max.v8.js   IIFE, self-contained. `[v8 js2max.v8.js]` and send it
 *                      messages. Nothing to require, nothing to resolve.
 *   max/js2max.js      CommonJS. `var js2max = require("js2max.js")` from your
 *                      own script, and drive the model and bridge yourself.
 *
 * `--check` rebuilds into memory and compares, so a committed artifact cannot
 * drift from its source unnoticed -- the same guard the Python single-file
 * edition uses.
 */

import { existsSync } from "node:fs";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";

const ROOT = dirname(Bun.fileURLToPath(import.meta.url));

/**
 * Where Max loads the bundles from: beside the harness patches, because Max
 * resolves a bare filename through its search path and a patch expects the
 * script next to it.
 */
const OUT = join(ROOT, "max");

/**
 * The second home: inside the Python package, so `pip install py2max` ships the
 * runtime and `py2max.js2max_runtime` can write it beside a generated patch.
 *
 * A mirror rather than a move. `js2max/max/` has to stay where it is for Max,
 * and the alternatives to copying are worse -- a symlink is not portable to
 * Windows, and making the package directory the only home breaks how the
 * harness finds its bundle. The cost is 160 KB duplicated in the tree; the
 * `--check` pass below is what stops the two drifting apart.
 *
 * Shipping them together is also a correctness guarantee, not only a
 * convenience: `src/objects.ts` is generated from py2max's maxref bundle, so a
 * bundle built against one version of py2max and used with another declares
 * wrong port counts -- and a box that declares a port it does not have loses
 * the cord attached to it when Max opens the file.
 */
const PKG = join(ROOT, "..", "py2max", "data", "js2max");

interface Artifact {
  entry: string;
  outfile: string;
  format: "iife" | "cjs";
}

const ARTIFACTS: Artifact[] = [
  { entry: "src/entry.v8.ts", outfile: "js2max.v8.js", format: "iife" },
  { entry: "src/lib.v8.ts", outfile: "js2max.js", format: "cjs" },
];

async function bundle(artifact: Artifact): Promise<string> {
  const result = await Bun.build({
    entrypoints: [join(ROOT, artifact.entry)],
    target: "browser",
    format: artifact.format,
  });
  if (!result.success) {
    for (const log of result.logs) console.error(log);
    throw new Error(`bundling ${artifact.entry} failed`);
  }
  const [output] = result.outputs;
  if (output === undefined) throw new Error(`no output for ${artifact.entry}`);
  return await output.text();
}

const check = process.argv.includes("--check");
let stale = false;

await mkdir(OUT, { recursive: true });
await mkdir(PKG, { recursive: true });

/** Both homes for one artifact, labelled as they appear in messages. */
function destinations(outfile: string): { label: string; path: string }[] {
  return [
    { label: `max/${outfile}`, path: join(OUT, outfile) },
    { label: `py2max/data/js2max/${outfile}`, path: join(PKG, outfile) },
  ];
}

for (const artifact of ARTIFACTS) {
  const fresh = await bundle(artifact);

  for (const { label, path } of destinations(artifact.outfile)) {
    if (check) {
      const current = existsSync(path) ? await readFile(path, "utf8") : null;
      if (current !== fresh) {
        console.error(`${label} is stale; run: bun run build`);
        stale = true;
      } else {
        console.log(`${label} is up to date`);
      }
      continue;
    }

    await writeFile(path, fresh);
    console.log(
      `wrote ${label} (${artifact.format}, ${(fresh.length / 1024).toFixed(1)} KB)`,
    );
  }
}

if (stale) process.exit(1);
