/**
 * Reading and writing `.maxpat` files from inside Max.
 *
 * Max's `File` class is the only file I/O available to a `v8` script -- there is
 * no `fs`. It is reached through the global `File` constructor, which exists
 * only inside Max, so everything here funnels through {@link FileFactory}: the
 * default resolves the global, and tests pass a double. That keeps the chunked
 * read loop and the truncate-before-write dance testable outside Max, which is
 * where their bugs would otherwise hide.
 *
 * API surface used, from the Cycling '74 reference:
 * `new File(name, access)` (auto-opens), `isopen`, `position`, `eof`,
 * `readstring(count)`, `writestring(text)`, `close()`.
 */

import type { MaxPatchFile } from "./format.ts";
import { LoadedPatcher, Patcher } from "./model.ts";

/** The subset of Max's `File` this uses. */
export interface MaxFile {
  readonly isopen: boolean;
  /** Current read/write offset in bytes. */
  position: number;
  /** File length in bytes. Assigning shrinks or extends the file. */
  eof: number;
  readstring(count: number): string;
  writestring(text: string): void;
  close(): void;
}

export type FileAccess = "read" | "write" | "readwrite";
export type FileFactory = (path: string, access: FileAccess) => MaxFile;

/** How much `readstring` is asked for at a time. */
const CHUNK = 16384;

interface MaxFileConstructor {
  new (path: string, access: FileAccess): MaxFile;
}

/**
 * The Max `File` global, or a clear failure.
 *
 * Resolved through `globalThis` rather than declared as an ambient `File`,
 * which would collide with the DOM `File` that TypeScript's lib and Bun's types
 * both define. The dynamic lookup also gives an honest error outside Max
 * instead of a `ReferenceError`.
 */
export const maxFileFactory: FileFactory = (path, access) => {
  const ctor = (globalThis as unknown as { File?: MaxFileConstructor }).File;
  if (ctor === undefined) {
    throw new Error(
      "js2max: no Max File class -- file I/O is only available inside Max",
    );
  }
  return new ctor(path, access);
};

export interface FileOptions {
  /** Override the `File` constructor. Tests pass a double; Max needs no override. */
  factory?: FileFactory;
}

/**
 * Read a whole file as text.
 *
 * `readstring` returns *up to* the requested count, so this loops to the end.
 * It also watches `position`: if a read fails to advance it, the loop stops
 * rather than spinning forever on a file that reports a length it will not
 * yield -- an infinite loop inside Max locks the whole application.
 */
export function readText(path: string, options: FileOptions = {}): string {
  const factory = options.factory ?? maxFileFactory;
  const file = factory(path, "read");
  if (!file.isopen) {
    throw new Error(`js2max: could not open ${path} for reading`);
  }
  try {
    const chunks: string[] = [];
    while (file.position < file.eof) {
      const before = file.position;
      const chunk = file.readstring(CHUNK);
      if (chunk === "" || file.position <= before) break;
      chunks.push(chunk);
    }
    return chunks.join("");
  } finally {
    file.close();
  }
}

/**
 * Write text to a file, replacing what was there.
 *
 * `eof = 0` first, because opening for write does not itself truncate: without
 * it, writing a shorter document over a longer one leaves the tail of the old
 * one behind, which for a `.maxpat` means trailing bytes after the closing
 * brace. Setting `eof` is the documented way to change a file's length; the
 * assignment is tolerated if it fails, so a host that disallows it still writes
 * rather than throwing.
 */
export function writeText(
  path: string,
  text: string,
  options: FileOptions = {},
): void {
  const factory = options.factory ?? maxFileFactory;
  const file = factory(path, "write");
  if (!file.isopen) {
    throw new Error(`js2max: could not open ${path} for writing`);
  }
  try {
    try {
      file.eof = 0;
    } catch {
      // Some hosts may refuse; the write below is still correct for any
      // document at least as long as the previous one.
    }
    file.position = 0;
    file.writestring(text);
  } finally {
    file.close();
  }
}

/** Read and parse a `.maxpat`, keeping every key the file contains. */
export function readPatch(
  path: string,
  options: FileOptions = {},
): LoadedPatcher {
  const text = readText(path, options);
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch (err) {
    throw new Error(`js2max: ${path} is not valid JSON -- ${String(err)}`);
  }
  const file = parsed as MaxPatchFile;
  if (file?.patcher?.boxes === undefined) {
    throw new Error(`js2max: ${path} has no patcher.boxes -- not a .maxpat?`);
  }
  return Patcher.fromFile(file);
}

/** Serialize a patcher and write it as a `.maxpat`. */
export function writePatch(
  path: string,
  patcher: Patcher | LoadedPatcher,
  options: FileOptions & { indent?: number } = {},
): void {
  writeText(path, patcher.toJSON(options.indent ?? 4), options);
}
