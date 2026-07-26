/**
 * Ambient declarations for the Max `v8` host environment.
 *
 * The `v8` object exposes ECMAScript 6+ plus a set of Max-specific globals that
 * exist only inside Max. Nothing here is implemented by this package -- these
 * are the shapes the host provides, written down so that code targeting v8
 * type-checks under the same `strict` settings as the rest of the core.
 *
 * Provenance matters for a file like this, so it is marked per declaration:
 *
 *   VERIFIED  -- signature taken from the Cycling '74 Patcher-object and v8
 *                reference pages (docs.cycling74.com/reference/v8/ and
 *                /max8/vignettes/jspatcherobject).
 *   NARROWED  -- the host is more permissive than this; the declaration is
 *                deliberately tighter to catch mistakes in *our* code. Widen it
 *                if a legitimate call is rejected.
 *
 * Anything not needed by `scripting.ts` or `entry.v8.ts` is left out on purpose:
 * an incomplete-but-correct subset is more useful than a complete guess.
 */

declare global {
  /** VERIFIED -- print to the Max console. */
  function post(...args: unknown[]): void;

  /** VERIFIED -- print to the Max console as an error. */
  function error(...args: unknown[]): void;

  /** VERIFIED -- send a value out of the object's nth outlet (0-indexed). */
  function outlet(index: number, ...args: unknown[]): void;

  /** VERIFIED -- arguments typed into the `v8` box, `jsarguments[0]` being the filename. */
  const jsarguments: readonly (string | number)[];

  /** VERIFIED -- number of inlets/outlets the script declares. Assign at top level. */
  let inlets: number;
  let outlets: number;

  /** VERIFIED -- reload the script when the file changes on disk. */
  let autowatch: number;

  /**
   * A Max object inside a patcher.
   *
   * NARROWED -- the host object carries far more than this (per-class getters,
   * `message()`, listeners). Only what the bridge touches is declared.
   */
  /** VERIFIED -- a patchcord, as the JS API exposes it. All four are read-only. */
  interface MaxobjConnection {
    readonly srcobject: Maxobj;
    readonly srcoutlet: number;
    readonly dstobject: Maxobj;
    readonly dstinlet: number;
  }

  interface Maxobj {
    /** VERIFIED -- the object's scripting name, settable. */
    varname: string;
    /** VERIFIED -- the box class, e.g. "newobj", "toggle", "flonum". */
    readonly maxclass: string;
    /** VERIFIED -- `[left, top, right, bottom]`, note: NOT Max's `[x, y, w, h]`. */
    rect: [number, number, number, number];
    /** VERIFIED -- next object in the patcher's list, or nil at the end. */
    readonly nextobject: Maxobj | null | undefined;
    /** VERIFIED -- the patcher containing this object. */
    readonly patcher: MaxPatcher;
    /**
     * VERIFIED -- the object's patchcords, as two arrays of connections.
     *
     * This is how connections are enumerated. An earlier version of this file
     * claimed the JS API had no such facility and `snapshot` was cut down to
     * boxes only as a result; it does, and it does not.
     */
    readonly patchcords: {
      readonly inputs: readonly MaxobjConnection[];
      readonly outputs: readonly MaxobjConnection[];
    };
    /**
     * VERIFIED -- whether this reference still designates a live Max object.
     *
     * False after the object is removed. Worth checking before touching a
     * handle you have held across a `remove`.
     */
    readonly valid: boolean;
    /** VERIFIED -- for a subpatcher box, the patcher inside it; otherwise nil. */
    subpatcher(index?: number): MaxPatcher | null | undefined;
    /** VERIFIED -- send the object a message with any additional arguments. */
    message(name: string, ...args: unknown[]): void;
    /** VERIFIED -- whether the object accepts a given message. */
    understands(message: string): boolean;

    /**
     * VERIFIED -- the *object's* attributes. Not the box's.
     *
     * The distinction matters and cost a feature: a `.maxpat` box records *box*
     * attributes (`maxclass`, `text`, `numinlets`, `patching_rect`), which is
     * what `getboxattr` reads. `getattr` reaches the object inside the box.
     */
    getattr(name: string): unknown;
    /** Every attribute the object exposes. Presence on `v8` is unconfirmed. */
    getattrnames(): string[];
    setattr(name: string, ...value: unknown[]): void;

    /** VERIFIED -- the *box's* attributes: exactly the keys a `.maxpat` stores. */
    getboxattr(name: string): unknown;
    getboxattrnames(): string[];
    setboxattr(name: string, ...value: unknown[]): void;

    /**
     * VERIFIED -- "The text contained in the object box (if present)".
     *
     * Read-only, and documented as **v8 only** -- absent on the legacy `js`
     * engine. This is the accessor whose supposed absence made serializing a
     * live patcher look impossible.
     */
    readonly boxtext?: string;
  }

  /**
   * A patcher, as reachable from a script via `this.patcher`.
   *
   * VERIFIED signatures. Note the argument order of `newdefault`: position
   * comes *first*, unlike `newobject`, where the class name leads.
   */
  interface MaxPatcher {
    /** Create an object with default appearance at (left, top). */
    newdefault(
      left: number,
      top: number,
      classname: string,
      ...args: (string | number)[]
    ): Maxobj;
    /** Create an object, giving its box parameters explicitly. */
    newobject(classname: string, ...params: (string | number)[]): Maxobj;
    /** Connect an outlet to an inlet. Indices are 0-based. */
    connect(from: Maxobj, outlet: number, to: Maxobj, inlet: number): void;
    /** As `connect`, but the cord is hidden in a locked patcher. */
    hiddenconnect(from: Maxobj, outlet: number, to: Maxobj, inlet: number): void;
    disconnect(from: Maxobj, outlet: number, to: Maxobj, inlet: number): void;
    /** Remove an object, and with it any patchlines attached to it. */
    remove(object: Maxobj): void;
    /** First object whose scripting name matches, or nil. */
    getnamed(name: string): Maxobj | null | undefined;
    /** Call `fn` once per object in the patcher. */
    apply(fn: (object: Maxobj) => void): void;
    /** As `apply`, recursing into subpatchers. */
    applydeep(fn: (object: Maxobj) => void): void;
    /** Every object for which `test` returns true. */
    getlogical(test: (object: Maxobj) => boolean): Maxobj[];
    /** Send an arbitrary message to the patcher. */
    message(name: string, ...args: unknown[]): void;
    /** Patcher attributes -- `default_fontsize`, `default_fontname`, ... */
    getattr(name: string): unknown;
    getattrnames(): string[];

    readonly filepath: string;
    readonly name: string;
    readonly count: number;
    readonly firstobject: Maxobj | null | undefined;
    /** For a subpatcher, the box containing it; otherwise nil. */
    readonly box: Maxobj | null | undefined;
    /** For a subpatcher, its containing patcher; otherwise nil. */
    readonly parentpatcher: MaxPatcher | null | undefined;
  }

  /**
   * The `this` of a v8 script.
   *
   * NARROWED -- `this` in a v8 script also carries `autowatch` and the message
   * plumbing; only what the bridge needs is declared.
   */
  interface MaxThis {
    /** VERIFIED in Max -- `demo` and `count` both reach the patcher this way. */
    readonly patcher: MaxPatcher;
    /**
     * The box hosting this script.
     *
     * Documented for the `js` object and assumed to hold for `v8`; treated as
     * possibly absent because deleting your own box corrupts the running script
     * (see `ClearOptions.keep`), so the code refuses to bulk-remove rather than
     * guess when this is missing.
     */
    readonly box?: Maxobj;
  }
}

export {};
