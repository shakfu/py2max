/**
 * A recording stand-in for the Max `v8` host.
 *
 * The bridge cannot be tested against Max from a terminal, so it is tested
 * against a double that implements the documented Patcher/Maxobj surface and
 * records every call. That checks the mapping -- class names, typed-in
 * arguments, rect conversion, connection indices, subpatcher recursion -- which
 * is where the bugs actually live. It does not check that Max accepts the
 * calls; only running it inside Max does that, and `patchers/v8-harness.maxpat`
 * exists for exactly that step.
 */

export interface CreatedObject {
  left: number;
  top: number;
  className: string;
  args: (string | number)[];
}

/**
 * A `connect` call as it was made.
 *
 * Endpoints are the objects, as Max receives them. They were recorded by
 * `varname`, which quietly made this log depend on the naming policy: it read
 * correctly only because `instantiate` happened to name every box after its
 * model id, and said nothing at all once it stopped.
 */
export interface Connection {
  from: MockMaxobj;
  outlet: number;
  to: MockMaxobj;
  inlet: number;
  hidden?: boolean;
}

export interface MockConnection {
  srcobject: MockMaxobj;
  srcoutlet: number;
  dstobject: MockMaxobj;
  dstinlet: number;
  hidden: boolean;
}

export class MockMaxobj {
  /**
   * The scripting name.
   *
   * Backed by the box attribute rather than held beside it, because in Max they
   * are one piece of state: assigning `Maxobj.varname` is what a later
   * `getboxattr("varname")` reads back, and it is how the name reaches a saved
   * file at all. Kept separate here, a box named by `instantiate` reported no
   * name to `serialize`, and the two directions agreed only by accident.
   */
  get varname(): string {
    return (this.boxAttrs.get("varname") as string | undefined) ?? "";
  }

  set varname(value: string) {
    this.boxAttrs.set("varname", value);
  }

  rect: [number, number, number, number] = [0, 0, 0, 0];
  readonly messages: Array<{ name: string; args: unknown[] }> = [];
  nested: MockPatcher | null = null;
  /** False once removed, mirroring `Maxobj.valid`. */
  valid = true;
  /** Box attributes -- the keys a `.maxpat` stores, read via `getboxattr`. */
  readonly boxAttrs = new Map<string, unknown>();
  /** `Maxobj.boxtext`; undefined models the legacy `js` engine, which lacks it. */
  boxtext: string | undefined;

  constructor(
    readonly maxclass: string,
    readonly created: CreatedObject,
    readonly patcher: MockPatcher,
  ) {}

  /**
   * As `Maxobj.patchcords`: every cord touching this object, split by
   * direction. Derived from the patcher's connection list so that a cord shows
   * up on both of its endpoints, exactly as it does in Max -- which is what
   * makes the "reported once, not once per endpoint" test meaningful.
   */
  get patchcords(): {
    inputs: MockConnection[];
    outputs: MockConnection[];
  } {
    return {
      inputs: this.patcher.cords.filter((c) => c.dstobject === this),
      outputs: this.patcher.cords.filter((c) => c.srcobject === this),
    };
  }

  understands(): boolean {
    return true;
  }

  /** Object attributes, reached by `getattr` -- distinct from box attributes. */
  readonly objectAttrs = new Map<string, unknown>();

  getattr(name: string): unknown {
    return this.objectAttrs.get(name);
  }

  /** Null for some classes, exactly as Max does. See `nullAttrNames`. */
  nullAttrNames = false;

  getattrnames(): string[] | null {
    return this.nullAttrNames ? null : [...this.objectAttrs.keys()];
  }

  setattr(name: string, value: unknown): void {
    this.objectAttrs.set(name, value);
  }

  getboxattr(name: string): unknown {
    return this.boxAttrs.get(name);
  }

  getboxattrnames(): string[] {
    return [...this.boxAttrs.keys()];
  }

  /** Names this box will refuse to set, so the failure path can be exercised. */
  readonly refuses = new Set<string>();

  /**
   * As Max: an attribute takes an atom *list*, so a rect arrives as four
   * arguments rather than one array. Stored the way `getboxattr` gives it back
   * -- a single atom as itself, several as an array.
   */
  setboxattr(name: string, ...value: unknown[]): void {
    if (this.refuses.has(name)) throw new Error(`${name} refused`);
    this.boxAttrs.set(name, value.length === 1 ? value[0] : value);
  }

  get nextobject(): MockMaxobj | null {
    const list = this.patcher.objects;
    const index = list.indexOf(this);
    return index >= 0 && index + 1 < list.length ? (list[index + 1] ?? null) : null;
  }

  subpatcher(): MockPatcher | null {
    return this.nested;
  }

  /** Whether `set` rewrites this box's text, as it does for a message box. */
  setFillsText = false;

  message(name: string, ...args: unknown[]): void {
    this.messages.push({ name, args });
    // A real message box's contents *are* its text: `set 1 2 3` is what a later
    // `boxtext` reads back, and what a save writes to the file.
    if (name === "set" && this.setFillsText) {
      this.boxtext = args.join(" ");
    }
  }
}

/**
 * Box attributes every created box reports, declared but unset.
 *
 * `getboxattrnames()` answers for the attributes a box *has*, at whatever value
 * -- which is what `instantiate` consults before setting anything, and what
 * `serialize` walks under `allAttributes`. A mock whose boxes claimed no
 * attributes would let either side pass while doing nothing. Unset, so they are
 * reported without being written back out (`isSet` drops them).
 */
const DECLARED_BOX_ATTRS = [
  "annotation",
  "bgcolor",
  "border",
  "color",
  "fontface",
  "fontname",
  "fontsize",
  "hidden",
  "hint",
  "ignoreclick",
  "presentation",
  "presentation_rect",
  "textcolor",
  "varname",
];

export interface MockPatcherOptions {
  /** Class names to reject, as Max does for an object it cannot instantiate. */
  unknownClasses?: readonly string[];
  /** Class names whose boxes expose a nested patcher. */
  subpatcherClasses?: readonly string[];
  /**
   * Classes that are their own box class (`toggle`, `message`, ...). Anything
   * else gets `maxclass: "newobj"`, as Max does for an object box.
   */
  uiClasses?: readonly string[];
  /** Attribute names every box refuses to set, for the failure path. */
  refusedBoxAttrs?: readonly string[];
  /**
   * Whether a `set` message fills a message box's text.
   *
   * The assumption `verify`'s first check exists to settle, and therefore one
   * the mock must be able to *break*: a check that cannot fail proves nothing.
   * Left undefined, a message box behaves like any other object and ignores it.
   */
  setFillsMessageBox?: boolean;
  /**
   * Class names for which `newdefault` throws instead of returning null.
   *
   * Max was assumed to return null for a class it does not know. Both are
   * handled, but only one keeps the reported reason accurate, so the check has
   * to be able to see the difference.
   */
  throwingClasses?: readonly string[];
  /**
   * Class names Max cannot build, modelled the way it actually behaves.
   *
   * Observed by running `diagnose`: `newdefault` returns neither null nor a
   * throw for an unknown class. It logs `No such object` and hands back a real
   * box whose `maxclass` is `jbogus`, with `valid` true and `boxtext` set to
   * the text asked for -- so only the class name gives it away.
   */
  bogusClasses?: readonly string[];
  /**
   * Class names whose `getattrnames()` returns null rather than an array.
   *
   * `trigger` and `jbogus` both do, in Max. Not an empty array and not a throw,
   * which is why a `try` around the call did not save the caller from a
   * `TypeError` several frames later.
   */
  nullAttrNames?: readonly string[];
  /**
   * Whether `newobject` leaves a message box empty despite being given text.
   *
   * The route that finally worked in Max, so the mock must be able to break it:
   * a check that cannot fail reports "yes" either way.
   */
  newobjectIgnoresText?: boolean;
}

export class MockPatcher {
  readonly objects: MockMaxobj[] = [];
  readonly connections: Connection[] = [];
  /** Cords as objects, so `patchcords` can be derived the way Max derives it. */
  readonly cords: MockConnection[] = [];
  readonly removed: MockMaxobj[] = [];

  constructor(private readonly options: MockPatcherOptions = {}) {}

  /** Patcher attributes, e.g. default_fontsize. */
  readonly attrs = new Map<string, unknown>();

  getattr(name: string): unknown {
    return this.attrs.get(name);
  }

  getattrnames(): string[] {
    return [...this.attrs.keys()];
  }

  get count(): number {
    return this.objects.length;
  }

  get firstobject(): MockMaxobj | null {
    return this.objects[0] ?? null;
  }

  get box(): MockMaxobj | null {
    return null;
  }

  filepath = "";

  get name(): string {
    return "mock";
  }

  newdefault(
    left: number,
    top: number,
    className: string,
    ...args: (string | number)[]
  ): MockMaxobj | null {
    if (this.options.throwingClasses?.includes(className)) {
      throw new Error(`mock: newdefault refuses "${className}"`);
    }
    if (this.options.unknownClasses?.includes(className)) return null;
    // What Max really does: a placeholder box, reported only to the console.
    const bogus = this.options.bogusClasses?.includes(className) === true;
    const object = new MockMaxobj(
      bogus ? "jbogus" : className,
      { left, top, className, args },
      this,
    );
    if (this.options.nullAttrNames?.includes(className) === true || bogus) {
      object.nullAttrNames = true;
    }
    const ui = this.options.uiClasses ?? [];
    const boxclass = ui.includes(className) ? className : "newobj";
    const text = [className, ...args].join(" ");
    object.boxtext = text;
    // Confirmed by probing Max: maxclass, numinlets and numoutlets are NOT box
    // attributes -- getboxattr returns null for all three. Only what Max really
    // offers is modelled here, or the tests would validate a fiction.
    void boxclass;
    object.boxAttrs.set("patching_rect", [left, top, 66, 22]);
    for (const name of DECLARED_BOX_ATTRS) {
      if (!object.boxAttrs.has(name)) object.boxAttrs.set(name, undefined);
    }
    for (const name of this.options.refusedBoxAttrs ?? []) {
      object.refuses.add(name);
    }
    if (boxclass === "message" && this.options.setFillsMessageBox === true) {
      object.setFillsText = true;
    }
    if (this.options.subpatcherClasses?.includes(className)) {
      object.nested = new MockPatcher(this.options);
    }
    this.objects.push(object);
    return object;
  }

  /**
   * As Max: `(class, left, top, width, fontsize, ...text atoms)`.
   *
   * The signature was decoded from two calls run in Max, which is also how the
   * bridge learned to give a message box its content at all:
   *
   *     newobject("message", 24, 720, 1, 2, 3)          boxtext "3"
   *     newobject("message", 24, 752, 100, 0, "1 2 3")  boxtext "\"1 2 3\""
   *
   * The first consumed `1` and `2` as width and font size; the second took the
   * content as one symbol and Max quoted it, which is why the atoms have to be
   * passed separately rather than joined.
   */
  newobject(className: string, ...params: (string | number)[]): MockMaxobj {
    const [left = 0, top = 0, width = 66, , ...text] = params;
    const object = this.newdefault(Number(left), Number(top), className);
    if (object === null) {
      throw new Error(`mock: newobject cannot build "${className}"`);
    }
    object.created.args = text;
    object.boxAttrs.set("patching_rect", [left, top, width, 22]);
    // The content, which is the whole reason this call exists.
    object.boxtext =
      this.options.newobjectIgnoresText === true ? "" : text.join(" ");
    return object;
  }

  connect(
    from: MockMaxobj,
    outlet: number,
    to: MockMaxobj,
    inlet: number,
  ): void {
    this.wire(from, outlet, to, inlet, false);
  }

  hiddenconnect(
    from: MockMaxobj,
    outlet: number,
    to: MockMaxobj,
    inlet: number,
  ): void {
    this.wire(from, outlet, to, inlet, true);
  }

  private wire(
    from: MockMaxobj,
    outlet: number,
    to: MockMaxobj,
    inlet: number,
    hidden: boolean,
  ): void {
    this.connections.push({
      from,
      outlet,
      to,
      inlet,
      ...(hidden ? { hidden: true } : {}),
    });
    this.cords.push({
      srcobject: from,
      srcoutlet: outlet,
      dstobject: to,
      dstinlet: inlet,
      hidden,
    });
  }

  disconnect(): void {
    /* not exercised */
  }

  remove(object: MockMaxobj): void {
    const index = this.objects.indexOf(object);
    if (index >= 0) this.objects.splice(index, 1);
    // Max frees the object; the handle stays but stops being valid.
    object.valid = false;
    for (let i = this.cords.length - 1; i >= 0; i -= 1) {
      const cord = this.cords[i];
      if (cord !== undefined && (cord.srcobject === object || cord.dstobject === object)) {
        this.cords.splice(i, 1);
      }
    }
    this.removed.push(object);
  }

  getnamed(name: string): MockMaxobj | null {
    return this.objects.find((o) => o.varname === name) ?? null;
  }

  apply(fn: (object: MockMaxobj) => void): void {
    for (const object of [...this.objects]) fn(object);
  }
}

/** The mock satisfies the ambient host types, so the bridge takes it directly. */
export function asHost(patcher: MockPatcher): MaxPatcher {
  return patcher as unknown as MaxPatcher;
}

/** As {@link asHost}, for a single object -- `keep` lists want `Maxobj`. */
export function asObject(object: MockMaxobj): Maxobj {
  return object as unknown as Maxobj;
}
