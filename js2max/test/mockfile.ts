/**
 * An in-memory stand-in for Max's `File` class.
 *
 * Models the behaviours the reader and writer actually depend on: `readstring`
 * returning *up to* the requested count, `position` advancing, `eof` reporting
 * the length, and assignment to `eof` truncating. A `MockFileSystem` holds the
 * contents so a test can write then read back.
 */

import type { FileAccess, MaxFile } from "../src/fileio.ts";

export class MockFileSystem {
  readonly files = new Map<string, string>();
  /** Paths that cannot be opened, whatever the access mode. */
  readonly unopenable = new Set<string>();
  /** When true, assigning to `eof` throws, as a stricter host might. */
  refuseTruncate = false;
  /** Cap on what one `readstring` returns, to force the chunking loop. */
  chunkLimit = Number.POSITIVE_INFINITY;

  open(path: string, access: FileAccess): MockFile {
    return new MockFile(this, path, access);
  }

  /** Use as a `FileFactory`. */
  get factory(): (path: string, access: FileAccess) => MaxFile {
    return (path, access) => this.open(path, access) as unknown as MaxFile;
  }
}

export class MockFile {
  position = 0;
  closed = false;

  constructor(
    private readonly fs: MockFileSystem,
    readonly path: string,
    readonly access: FileAccess,
  ) {
    if (access === "write" && !fs.files.has(path)) fs.files.set(path, "");
  }

  get isopen(): boolean {
    if (this.fs.unopenable.has(this.path)) return false;
    return this.fs.files.has(this.path);
  }

  private get contents(): string {
    return this.fs.files.get(this.path) ?? "";
  }

  get eof(): number {
    return this.contents.length;
  }

  set eof(length: number) {
    if (this.fs.refuseTruncate) throw new Error("eof is not settable here");
    this.fs.files.set(this.path, this.contents.slice(0, length));
  }

  readstring(count: number): string {
    const limit = Math.min(count, this.fs.chunkLimit);
    const chunk = this.contents.slice(this.position, this.position + limit);
    this.position += chunk.length;
    return chunk;
  }

  writestring(text: string): void {
    const current = this.contents;
    const next =
      current.slice(0, this.position) +
      text +
      current.slice(this.position + text.length);
    this.fs.files.set(this.path, next);
    this.position += text.length;
  }

  close(): void {
    this.closed = true;
  }
}
