/**
 * serialize -- read the live patcher back into a description, from your script.
 *
 * The library route for the lossy direction. Use it when the objects in the
 * patcher are the source of truth, because someone placed or edited them by
 * hand; if you are exporting something you just described in code, use
 * writePatch instead -- see save-example.js.
 *
 * What it cannot recover, and why: every field has to be rebuilt from whatever
 * the JS API exposes. A font equal to the patcher default is indistinguishable
 * from an unset one; port counts maxref does not state are omitted for Max to
 * derive; `linecount`, `filename` and `textfile` have no accessor at all. This
 * script reports anything it could not describe rather than writing it out
 * half-formed.
 *
 * Load it with [v8 serialize-example.js] and send it a bang.
 */

"use strict";

var js2max = require("js2max.js");

inlets = 1;
outlets = 1;
autowatch = 0;

var OUTPUT = "js2max-serialize-out.maxpat";

function bang() {
    var result = js2max.serialize(this.patcher);

    for (var i = 0; i < result.incomplete.length; i++) {
        var box = result.incomplete[i];
        error("serialize: cannot describe " + box.id + " (" + box.maxclass +
              ") -- missing " + box.missing.join(", ") + "\n");
    }
    if (result.incomplete.length > 0) {
        error("serialize: refusing to write a patch Max may not open\n");
        outlet(0, "error", result.incomplete.length);
        return;
    }

    js2max.writePatch(OUTPUT, new js2max.LoadedPatcher(result.patcher));

    post("serialize: wrote " + OUTPUT + " -- " +
         result.patcher.boxes.length + " boxes, " +
         result.patcher.lines.length + " cords\n");
    outlet(0, "done", result.patcher.boxes.length, result.patcher.lines.length);
}

/** Report what is in the patcher without writing anything. */
function inspect() {
    var result = js2max.serialize(this.patcher);
    var classes = {};
    for (var i = 0; i < result.patcher.boxes.length; i++) {
        var maxclass = result.patcher.boxes[i].box.maxclass;
        classes[maxclass] = (classes[maxclass] || 0) + 1;
    }
    for (var name in classes) {
        post("serialize: " + classes[name] + " x " + name + "\n");
    }
    post("serialize: " + result.patcher.lines.length + " cord(s), " +
         result.incomplete.length + " box(es) not describable\n");
    outlet(0, "inspected", result.patcher.boxes.length);
}
