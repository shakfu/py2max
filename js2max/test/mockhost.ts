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

export interface Connection {
  from: string;
  outlet: number;
  to: string;
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
  varname = "";
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

  getattrnames(): string[] {
    return [...this.objectAttrs.keys()];
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

  setboxattr(name: string, value: unknown): void {
    this.boxAttrs.set(name, value);
  }

  get nextobject(): MockMaxobj | null {
    const list = this.patcher.objects;
    const index = list.indexOf(this);
    return index >= 0 && index + 1 < list.length ? (list[index + 1] ?? null) : null;
  }

  subpatcher(): MockPatcher | null {
    return this.nested;
  }

  message(name: string, ...args: unknown[]): void {
    this.messages.push({ name, args });
  }
}

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
    if (this.options.unknownClasses?.includes(className)) return null;
    const object = new MockMaxobj(
      className,
      { left, top, className, args },
      this,
    );
    const ui = this.options.uiClasses ?? [];
    const boxclass = ui.includes(className) ? className : "newobj";
    const text = [className, ...args].join(" ");
    object.boxtext = text;
    // Confirmed by probing Max: maxclass, numinlets and numoutlets are NOT box
    // attributes -- getboxattr returns null for all three. Only what Max really
    // offers is modelled here, or the tests would validate a fiction.
    void boxclass;
    object.boxAttrs.set("patching_rect", [left, top, 66, 22]);
    if (this.options.subpatcherClasses?.includes(className)) {
      object.nested = new MockPatcher(this.options);
    }
    this.objects.push(object);
    return object;
  }

  newobject(className: string, ...params: (string | number)[]): MockMaxobj {
    const object = new MockMaxobj(
      className,
      { left: 0, top: 0, className, args: params },
      this,
    );
    this.objects.push(object);
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
      from: from.varname,
      outlet,
      to: to.varname,
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
