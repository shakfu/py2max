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
const OUT = join(ROOT, "max");

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

for (const artifact of ARTIFACTS) {
  const path = join(OUT, artifact.outfile);
  const fresh = await bundle(artifact);

  if (check) {
    const current = existsSync(path) ? await readFile(path, "utf8") : null;
    if (current !== fresh) {
      console.error(`max/${artifact.outfile} is stale; run: bun run build`);
      stale = true;
    } else {
      console.log(`max/${artifact.outfile} is up to date`);
    }
    continue;
  }

  await writeFile(path, fresh);
  console.log(
    `wrote max/${artifact.outfile} (${artifact.format}, ${(fresh.length / 1024).toFixed(1)} KB)`,
  );
}

if (stale) process.exit(1);
