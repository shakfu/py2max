/**
 * serialize -- read a live patcher into a data structure, from your script.
 *
 * The point is not to write the patcher back out. Serializing a whole patcher
 * and saving it is a worse `cp`: a file copy is exact, and this is not -- a
 * font equal to the patcher default cannot be told from an unset one, port
 * counts maxref does not state are omitted, and `linecount` / `filename` /
 * `textfile` have no accessor at all.
 *
 * What a copy cannot do is give you the patch as *data*. Once you have that you
 * can filter it, measure it, or rewrite it -- and get a patch that did not
 * exist before. This script does all three:
 *
 *     bang      extract the signal objects into their own patch
 *     report    what is in here, and what is not connected to anything
 *     spread    rewrite every position, tidying the layout in place
 *
 * Load it with [v8 serialize-example.js].
 */

"use strict";

var js2max = require("js2max.js");

inlets = 1;
outlets = 1;
autowatch = 0;

var OUTPUT = "js2max-signal-chain.maxpat";

/** Every object in the patcher, as an array. */
function objects() {
    var found = [];
    for (var o = this.patcher.firstobject; o; o = o.nextobject) {
        found.push(o);
    }
    return found;
}

/**
 * `bang` -- extract the signal chain into a standalone patch.
 *
 * The output is a different patch from this one: fewer boxes, only the cords
 * between the survivors. No file copy produces it.
 */
function bang() {
    var signal = [];
    var all = objects.call(this);
    for (var i = 0; i < all.length; i++) {
        var text = all[i].boxtext || "";
        if (all[i].maxclass.indexOf("~") >= 0 || text.indexOf("~") >= 0) {
            signal.push(all[i]);
        }
    }

    if (signal.length === 0) {
        error("serialize: no signal objects here\n");
        outlet(0, "error", "no-match");
        return;
    }

    var result = js2max.serialize(this.patcher, { only: signal });
    js2max.writePatch(OUTPUT, new js2max.LoadedPatcher(result.patcher));

    post("serialize: extracted " + result.patcher.boxes.length + " of " +
         all.length + " objects to " + OUTPUT + " (" +
         result.patcher.lines.length + " cords)\n");
    outlet(0, "extracted", result.patcher.boxes.length);
}

/** `report` -- what is here, and what is wired to nothing. */
function report() {
    var result = js2max.serialize(this.patcher);
    var counts = {};
    var connected = {};

    for (var i = 0; i < result.patcher.lines.length; i++) {
        var line = result.patcher.lines[i].patchline;
        connected[line.source[0]] = true;
        connected[line.destination[0]] = true;
    }

    var orphans = 0;
    for (var j = 0; j < result.patcher.boxes.length; j++) {
        var box = result.patcher.boxes[j].box;
        counts[box.maxclass] = (counts[box.maxclass] || 0) + 1;
        if (!connected[box.id]) {
            orphans += 1;
        }
    }

    for (var name in counts) {
        post("serialize: " + counts[name] + " x " + name + "\n");
    }
    post("serialize: " + result.patcher.lines.length + " cord(s), " +
         orphans + " box(es) connected to nothing\n");
    outlet(0, "reported", result.patcher.boxes.length, orphans);
}

/**
 * `spread` -- rewrite the patcher's layout from its own description.
 *
 * Read the positions, compute new ones, push them back. A round trip through
 * data that ends by *changing* the patcher, which is the other thing a copy
 * cannot do.
 */
function spread() {
    var all = objects.call(this);
    var top = 40;
    for (var i = 0; i < all.length; i++) {
        var rect = all[i].rect;
        var height = rect[3] - rect[1];
        var width = rect[2] - rect[0];
        all[i].rect = [40, top, 40 + width, top + height];
        top += height + 14;
    }
    post("serialize: repositioned " + all.length + " object(s)\n");
    outlet(0, "spread", all.length);
}
