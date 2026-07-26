/**
 * The `.maxpat` wire format, as types.
 *
 * This file is the spike's central claim in concrete form. In the Python package
 * the same knowledge is implicit: `Box.__init__` declares five parameters and
 * takes the rest through `**kwds: Any`, and `to_dict` is `vars(self)` minus
 * underscore keys. Nothing describes the file's shape, so nothing can check it.
 *
 * Here the shape *is* the type. Three properties fall out for free:
 *
 *   1. Optional properties model Max's absent-vs-present distinction directly.
 *      `JSON.stringify` omits `undefined`, so there is no null-stripping pass --
 *      `_remove_none_entries` (and its "TODO: make recursive") has no analogue.
 *   2. `exactOptionalPropertyTypes` makes `{bgcolor?: Color}` reject an explicit
 *      `bgcolor: undefined`, so "I did not set this" and "I set this to nothing"
 *      cannot be confused.
 *   3. A misspelled property is a compile error rather than a key that ships
 *      silently into the emitted patch.
 */

/** `[x, y, width, height]` -- Max writes rects as a 4-element array. */
export type Rect4 = readonly [number, number, number, number];

/** `[r, g, b, a]`, each 0..1. */
export type Color = readonly [number, number, number, number];

/** `[objectId, portIndex]` -- one end of a patchline. */
export type Endpoint = readonly [string, number];

export interface AppVersion {
  major: number;
  minor: number;
  revision: number;
  architecture: string;
  modernui: number;
}

/**
 * Box properties that are not structural.
 *
 * Every key here was observed in the `.maxpat` fixtures under `tests/` or is
 * listed in the Python package's `UNIVERSAL_BOX_ATTRS`. In a real
 * implementation the per-class half of this vocabulary would be generated from
 * the maxref bundle (attributes whose nested `save` meta-attribute is 1 are
 * exactly the ones Max persists into the file); this hand-written subset is
 * enough to show the checking working.
 */
export interface BoxProps {
  // text and font
  text?: string;
  fontname?: string;
  fontsize?: number;
  fontface?: number;
  linecount?: number;
  format?: number;
  comment?: string;

  // identity and presentation
  varname?: string;
  prototypename?: string;
  presentation?: number;
  presentation_rect?: Rect4;
  hidden?: number;
  ignoreclick?: number;
  background?: number;
  rounded?: number;
  hint?: string;
  annotation?: string;

  // color
  bgcolor?: Color;
  color?: Color;
  textcolor?: Color;
  bordercolor?: Color;

  // ranges and values
  size?: number;
  range?: readonly number[];
  domain?: number;
  minimum?: number;
  maximum?: number;
  outputmode?: number;
  orientation?: number;
  index?: number;

  // parameters / pattr
  parameter_enable?: number;
  saved_attribute_attributes?: Readonly<Record<string, unknown>>;
  saved_object_attributes?: Readonly<Record<string, unknown>>;

  // container payloads
  data?: unknown;
  table_data?: readonly number[];
  preset_data?: readonly unknown[];
  addpoints?: readonly unknown[];
  embed?: number;
  name?: string;
  editor_rect?: Rect4;
  showeditor?: number;
  code?: string;

  // misc observed in fixtures
  bubble?: number;
  tabs?: readonly string[];
  lastchannelcount?: number;
  outlettype?: readonly string[];
}

/**
 * A box as it appears in the file.
 *
 * The five structural keys are required -- Max rejects a box without them --
 * and everything else arrives through {@link BoxProps} as an optional property.
 * A nested `patcher` makes this box a subpatcher.
 */
export interface BoxDict extends BoxProps {
  id: string;
  maxclass: string;
  numinlets: number;
  numoutlets: number;
  patching_rect: Rect4;
  patcher?: PatcherDict;
}

/** Boxes are wrapped one level deep in the file: `{"box": {...}}`. */
export interface BoxEntry {
  box: BoxDict;
}

export interface PatchlineDict {
  source: Endpoint;
  destination: Endpoint;
  order?: number;
  midpoints?: readonly number[];
  hidden?: number;
  disabled?: number;
}

export interface PatchlineEntry {
  patchline: PatchlineDict;
}

/**
 * A patcher: the window's own settings plus its boxes and lines.
 *
 * Only the keys py2max always writes are required. `autosave` and
 * `dependency_cache` are deliberately optional because real Max subpatchers omit
 * them -- the Python package had to add code to delete those keys again after
 * seeding defaults, to keep load/save faithful for patches with subpatchers.
 * Optionality expresses that directly instead.
 */
export interface PatcherDict {
  fileversion: number;
  appversion: AppVersion;
  classnamespace?: string;
  rect: Rect4;
  bglocked?: number;
  bgcolor?: Color;
  openinpresentation?: number;
  default_fontsize?: number;
  default_fontface?: number;
  default_fontname?: string;
  gridonopen?: number;
  gridsize?: readonly [number, number];
  gridsnaponopen?: number;
  objectsnaponopen?: number;
  statusbarvisible?: number;
  toolbarvisible?: number;
  lefttoolbarpinned?: number;
  toptoolbarpinned?: number;
  righttoolbarpinned?: number;
  bottomtoolbarpinned?: number;
  toolbars_unpinned_last_save?: number;
  tallnewobj?: number;
  boxanimatetime?: number;
  enablehscroll?: number;
  enablevscroll?: number;
  devicewidth?: number;
  description?: string;
  digest?: string;
  tags?: string;
  style?: string;
  styles?: readonly unknown[];
  subpatcher_template?: string;
  assistshowspatchername?: number;
  title?: string;
  globalpatchername?: string;
  parameters?: Readonly<Record<string, unknown>>;
  boxes: BoxEntry[];
  lines: PatchlineEntry[];
  dependency_cache?: readonly unknown[];
  autosave?: number;
}

/** A whole `.maxpat` file. */
export interface MaxPatchFile {
  patcher: PatcherDict;
}
