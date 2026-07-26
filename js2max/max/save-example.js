/**
 * writePatch -- build a patch description and write it, from your own script.
 *
 * The library route. `js2max.v8.js` exposes a fixed message set; this is what
 * you write when you want your own. Nothing here touches the patcher: a
 * description is already the shape of a `.maxpat`, so writing it is exact and
 * creates no objects.
 *
 * Load it with [v8 save-example.js] and send it a bang.
 */

"use strict";

var js2max = require("js2max.js");

inlets = 1;
outlets = 1;
autowatch = 0;

var OUTPUT = "js2max-writepatch-out.maxpat";

function bang() {
    var p = new js2max.Patcher();

    var osc = p.add("cycle~ 220", { patching_rect: [40, 40, 70, 22] });
    var amp = p.add("*~ 0.1", { patching_rect: [40, 80, 60, 22] });
    var out = p.add("", {
        maxclass: "ezdac~",
        patching_rect: [40, 120, 45, 45]
    });

    p.connect(osc, amp);
    p.connect(amp, out, 0, 0);
    p.connect(amp, out, 0, 1);

    js2max.writePatch(OUTPUT, p);

    post("writePatch: wrote " + OUTPUT + " -- 3 boxes, 3 cords, 0 objects created\n");
    outlet(0, "done", 3, 3);
}

/** Show that the description and the file agree, without opening Max. */
function verify() {
    var p = new js2max.Patcher();
    p.add("cycle~ 220");
    js2max.writePatch(OUTPUT, p);

    var reloaded = js2max.readPatch(OUTPUT);
    var same = reloaded.toJSON() === p.toJSON();
    post("writePatch: round trip through the file is " +
         (same ? "exact" : "NOT exact") + "\n");
    outlet(0, "verified", same ? 1 : 0);
}
