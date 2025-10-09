(function(f){if(typeof exports==="object"&&typeof module!=="undefined"){module.exports=f()}else if(typeof define==="function"&&define.amd){define([],f)}else{var g;if(typeof window!=="undefined"){g=window}else if(typeof global!=="undefined"){g=global}else if(typeof self!=="undefined"){g=self}else{g=this}g.cola = f()}})(function(){var define,module,exports;return (function(){function r(e,n,t){function o(i,f){if(!n[i]){if(!e[i]){var c="function"==typeof require&&require;if(!f&&c)return c(i,!0);if(u)return u(i,!0);var a=new Error("Cannot find module '"+i+"'");throw a.code="MODULE_NOT_FOUND",a}var p=n[i]={exports:{}};e[i][0].call(p.exports,function(r){var n=e[i][1][r];return o(n||r)},p,p.exports,r,e,n,t)}return n[i].exports}for(var u="function"==typeof require&&require,i=0;i<t.length;i++)o(t[i]);return o}return r})()({1:[function(require,module,exports){
"use strict";
function __export(m) {
    for (var p in m) if (!exports.hasOwnProperty(p)) exports[p] = m[p];
}
Object.defineProperty(exports, "__esModule", { value: true });
__export(require("./src/adaptor"));
__export(require("./src/d3adaptor"));
__export(require("./src/descent"));
__export(require("./src/geom"));
__export(require("./src/gridrouter"));
__export(require("./src/handledisconnected"));
__export(require("./src/layout"));
__export(require("./src/layout3d"));
__export(require("./src/linklengths"));
__export(require("./src/powergraph"));
__export(require("./src/pqueue"));
__export(require("./src/rbtree"));
__export(require("./src/rectangle"));
__export(require("./src/shortestpaths"));
__export(require("./src/vpsc"));
__export(require("./src/batch"));
},{"./src/adaptor":2,"./src/batch":3,"./src/d3adaptor":4,"./src/descent":7,"./src/geom":8,"./src/gridrouter":9,"./src/handledisconnected":10,"./src/layout":11,"./src/layout3d":12,"./src/linklengths":13,"./src/powergraph":14,"./src/pqueue":15,"./src/rbtree":16,"./src/rectangle":17,"./src/shortestpaths":18,"./src/vpsc":19}],2:[function(require,module,exports){
"use strict";
var __extends = (this && this.__extends) || (function () {
    var extendStatics = function (d, b) {
        extendStatics = Object.setPrototypeOf ||
            ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
            function (d, b) { for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p]; };
        return extendStatics(d, b);
    };
    return function (d, b) {
        extendStatics(d, b);
        function __() { this.constructor = d; }
        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
var layout_1 = require("./layout");
var LayoutAdaptor = (function (_super) {
    __extends(LayoutAdaptor, _super);
    function LayoutAdaptor(options) {
        var _this = _super.call(this) || this;
        var self = _this;
        var o = options;
        if (o.trigger) {
            _this.trigger = o.trigger;
        }
        if (o.kick) {
            _this.kick = o.kick;
        }
        if (o.drag) {
            _this.drag = o.drag;
        }
        if (o.on) {
            _this.on = o.on;
        }
        _this.dragstart = _this.dragStart = layout_1.Layout.dragStart;
        _this.dragend = _this.dragEnd = layout_1.Layout.dragEnd;
        return _this;
    }
    LayoutAdaptor.prototype.trigger = function (e) { };
    ;
    LayoutAdaptor.prototype.kick = function () { };
    ;
    LayoutAdaptor.prototype.drag = function () { };
    ;
    LayoutAdaptor.prototype.on = function (eventType, listener) { return this; };
    ;
    return LayoutAdaptor;
}(layout_1.Layout));
exports.LayoutAdaptor = LayoutAdaptor;
function adaptor(options) {
    return new LayoutAdaptor(options);
}
exports.adaptor = adaptor;
},{"./layout":11}],3:[function(require,module,exports){
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var layout_1 = require("./layout");
var gridrouter_1 = require("./gridrouter");
function gridify(pgLayout, nudgeGap, margin, groupMargin) {
    pgLayout.cola.start(0, 0, 0, 10, false);
    var gridrouter = route(pgLayout.cola.nodes(), pgLayout.cola.groups(), margin, groupMargin);
    return gridrouter.routeEdges(pgLayout.powerGraph.powerEdges, nudgeGap, function (e) { return e.source.routerNode.id; }, function (e) { return e.target.routerNode.id; });
}
exports.gridify = gridify;
function route(nodes, groups, margin, groupMargin) {
    nodes.forEach(function (d) {
        d.routerNode = {
            name: d.name,
            bounds: d.bounds.inflate(-margin)
        };
    });
    groups.forEach(function (d) {
        d.routerNode = {
            bounds: d.bounds.inflate(-groupMargin),
            children: (typeof d.groups !== 'undefined' ? d.groups.map(function (c) { return nodes.length + c.id; }) : [])
                .concat(typeof d.leaves !== 'undefined' ? d.leaves.map(function (c) { return c.index; }) : [])
        };
    });
    var gridRouterNodes = nodes.concat(groups).map(function (d, i) {
        d.routerNode.id = i;
        return d.routerNode;
    });
    return new gridrouter_1.GridRouter(gridRouterNodes, {
        getChildren: function (v) { return v.children; },
        getBounds: function (v) { return v.bounds; }
    }, margin - groupMargin);
}
function powerGraphGridLayout(graph, size, grouppadding) {
    var powerGraph;
    graph.nodes.forEach(function (v, i) { return v.index = i; });
    new layout_1.Layout()
        .avoidOverlaps(false)
        .nodes(graph.nodes)
        .links(graph.links)
        .powerGraphGroups(function (d) {
        powerGraph = d;
        powerGraph.groups.forEach(function (v) { return v.padding = grouppadding; });
    });
    var n = graph.nodes.length;
    var edges = [];
    var vs = graph.nodes.slice(0);
    vs.forEach(function (v, i) { return v.index = i; });
    powerGraph.groups.forEach(function (g) {
        var sourceInd = g.index = g.id + n;
        vs.push(g);
        if (typeof g.leaves !== 'undefined')
            g.leaves.forEach(function (v) { return edges.push({ source: sourceInd, target: v.index }); });
        if (typeof g.groups !== 'undefined')
            g.groups.forEach(function (gg) { return edges.push({ source: sourceInd, target: gg.id + n }); });
    });
    powerGraph.powerEdges.forEach(function (e) {
        edges.push({ source: e.source.index, target: e.target.index });
    });
    new layout_1.Layout()
        .size(size)
        .nodes(vs)
        .links(edges)
        .avoidOverlaps(false)
        .linkDistance(30)
        .symmetricDiffLinkLengths(5)
        .convergenceThreshold(1e-4)
        .start(100, 0, 0, 0, false);
    return {
        cola: new layout_1.Layout()
            .convergenceThreshold(1e-3)
            .size(size)
            .avoidOverlaps(true)
            .nodes(graph.nodes)
            .links(graph.links)
            .groupCompactness(1e-4)
            .linkDistance(30)
            .symmetricDiffLinkLengths(5)
            .powerGraphGroups(function (d) {
            powerGraph = d;
            powerGraph.groups.forEach(function (v) {
                v.padding = grouppadding;
            });
        }).start(50, 0, 100, 0, false),
        powerGraph: powerGraph
    };
}
exports.powerGraphGridLayout = powerGraphGridLayout;
},{"./gridrouter":9,"./layout":11}],4:[function(require,module,exports){
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var d3v3 = require("./d3v3adaptor");
var d3v4 = require("./d3v4adaptor");
;
function d3adaptor(d3Context) {
    if (!d3Context || isD3V3(d3Context)) {
        return new d3v3.D3StyleLayoutAdaptor();
    }
    return new d3v4.D3StyleLayoutAdaptor(d3Context);
}
exports.d3adaptor = d3adaptor;
function isD3V3(d3Context) {
    var v3exp = /^3\./;
    return d3Context.version && d3Context.version.match(v3exp) !== null;
}
},{"./d3v3adaptor":5,"./d3v4adaptor":6}],5:[function(require,module,exports){
"use strict";
var __extends = (this && this.__extends) || (function () {
    var extendStatics = function (d, b) {
        extendStatics = Object.setPrototypeOf ||
            ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
            function (d, b) { for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p]; };
        return extendStatics(d, b);
    };
    return function (d, b) {
        extendStatics(d, b);
        function __() { this.constructor = d; }
        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
var layout_1 = require("./layout");
var D3StyleLayoutAdaptor = (function (_super) {
    __extends(D3StyleLayoutAdaptor, _super);
    function D3StyleLayoutAdaptor() {
        var _this = _super.call(this) || this;
        _this.event = d3.dispatch(layout_1.EventType[layout_1.EventType.start], layout_1.EventType[layout_1.EventType.tick], layout_1.EventType[layout_1.EventType.end]);
        var d3layout = _this;
        var drag;
        _this.drag = function () {
            if (!drag) {
                var drag = d3.behavior.drag()
                    .origin(layout_1.Layout.dragOrigin)
                    .on("dragstart.d3adaptor", layout_1.Layout.dragStart)
                    .on("drag.d3adaptor", function (d) {
                    layout_1.Layout.drag(d, d3.event);
                    d3layout.resume();
                })
                    .on("dragend.d3adaptor", layout_1.Layout.dragEnd);
            }
            if (!arguments.length)
                return drag;
            this
                .call(drag);
        };
        return _this;
    }
    D3StyleLayoutAdaptor.prototype.trigger = function (e) {
        var d3event = { type: layout_1.EventType[e.type], alpha: e.alpha, stress: e.stress };
        this.event[d3event.type](d3event);
    };
    D3StyleLayoutAdaptor.prototype.kick = function () {
        var _this = this;
        d3.timer(function () { return _super.prototype.tick.call(_this); });
    };
    D3StyleLayoutAdaptor.prototype.on = function (eventType, listener) {
        if (typeof eventType === 'string') {
            this.event.on(eventType, listener);
        }
        else {
            this.event.on(layout_1.EventType[eventType], listener);
        }
        return this;
    };
    return D3StyleLayoutAdaptor;
}(layout_1.Layout));
exports.D3StyleLayoutAdaptor = D3StyleLayoutAdaptor;
function d3adaptor() {
    return new D3StyleLayoutAdaptor();
}
exports.d3adaptor = d3adaptor;
},{"./layout":11}],6:[function(require,module,exports){
"use strict";
var __extends = (this && this.__extends) || (function () {
    var extendStatics = function (d, b) {
        extendStatics = Object.setPrototypeOf ||
            ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
            function (d, b) { for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p]; };
        return extendStatics(d, b);
    };
    return function (d, b) {
        extendStatics(d, b);
        function __() { this.constructor = d; }
        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
var layout_1 = require("./layout");
var D3StyleLayoutAdaptor = (function (_super) {
    __extends(D3StyleLayoutAdaptor, _super);
    function D3StyleLayoutAdaptor(d3Context) {
        var _this = _super.call(this) || this;
        _this.d3Context = d3Context;
        _this.event = d3Context.dispatch(layout_1.EventType[layout_1.EventType.start], layout_1.EventType[layout_1.EventType.tick], layout_1.EventType[layout_1.EventType.end]);
        var d3layout = _this;
        var drag;
        _this.drag = function () {
            if (!drag) {
                var drag = d3Context.drag()
                    .subject(layout_1.Layout.dragOrigin)
                    .on("start.d3adaptor", layout_1.Layout.dragStart)
                    .on("drag.d3adaptor", function (d) {
                    layout_1.Layout.drag(d, d3Context.event);
                    d3layout.resume();
                })
                    .on("end.d3adaptor", layout_1.Layout.dragEnd);
            }
            if (!arguments.length)
                return drag;
            arguments[0].call(drag);
        };
        return _this;
    }
    D3StyleLayoutAdaptor.prototype.trigger = function (e) {
        var d3event = { type: layout_1.EventType[e.type], alpha: e.alpha, stress: e.stress };
        this.event.call(d3event.type, d3event);
    };
    D3StyleLayoutAdaptor.prototype.kick = function () {
        var _this = this;
        var t = this.d3Context.timer(function () { return _super.prototype.tick.call(_this) && t.stop(); });
    };
    D3StyleLayoutAdaptor.prototype.on = function (eventType, listener) {
        if (typeof eventType === 'string') {
            this.event.on(eventType, listener);
        }
        else {
            this.event.on(layout_1.EventType[eventType], listener);
        }
        return this;
    };
    return D3StyleLayoutAdaptor;
}(layout_1.Layout));
exports.D3StyleLayoutAdaptor = D3StyleLayoutAdaptor;
},{"./layout":11}],7:[function(require,module,exports){
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var Locks = (function () {
    function Locks() {
        this.locks = {};
    }
    Locks.prototype.add = function (id, x) {
        this.locks[id] = x;
    };
    Locks.prototype.clear = function () {
        this.locks = {};
    };
    Locks.prototype.isEmpty = function () {
        for (var l in this.locks)
            return false;
        return true;
    };
    Locks.prototype.apply = function (f) {
        for (var l in this.locks) {
            f(Number(l), this.locks[l]);
        }
    };
    return Locks;
}());
exports.Locks = Locks;
var Descent = (function () {
    function Descent(x, D, G) {
        if (G === void 0) { G = null; }
        this.D = D;
        this.G = G;
        this.threshold = 0.0001;
        this.numGridSnapNodes = 0;
        this.snapGridSize = 100;
        this.snapStrength = 1000;
        this.scaleSnapByMaxH = false;
        this.random = new PseudoRandom();
        this.project = null;
        this.x = x;
        this.k = x.length;
        var n = this.n = x[0].length;
        this.H = new Array(this.k);
        this.g = new Array(this.k);
        this.Hd = new Array(this.k);
        this.a = new Array(this.k);
        this.b = new Array(this.k);
        this.c = new Array(this.k);
        this.d = new Array(this.k);
        this.e = new Array(this.k);
        this.ia = new Array(this.k);
        this.ib = new Array(this.k);
        this.xtmp = new Array(this.k);
        this.locks = new Locks();
        this.minD = Number.MAX_VALUE;
        var i = n, j;
        while (i--) {
            j = n;
            while (--j > i) {
                var d = D[i][j];
                if (d > 0 && d < this.minD) {
                    this.minD = d;
                }
            }
        }
        if (this.minD === Number.MAX_VALUE)
            this.minD = 1;
        i = this.k;
        while (i--) {
            this.g[i] = new Array(n);
            this.H[i] = new Array(n);
            j = n;
            while (j--) {
                this.H[i][j] = new Array(n);
            }
            this.Hd[i] = new Array(n);
            this.a[i] = new Array(n);
            this.b[i] = new Array(n);
            this.c[i] = new Array(n);
            this.d[i] = new Array(n);
            this.e[i] = new Array(n);
            this.ia[i] = new Array(n);
            this.ib[i] = new Array(n);
            this.xtmp[i] = new Array(n);
        }
    }
    Descent.createSquareMatrix = function (n, f) {
        var M = new Array(n);
        for (var i = 0; i < n; ++i) {
            M[i] = new Array(n);
            for (var j = 0; j < n; ++j) {
                M[i][j] = f(i, j);
            }
        }
        return M;
    };
    Descent.prototype.offsetDir = function () {
        var _this = this;
        var u = new Array(this.k);
        var l = 0;
        for (var i = 0; i < this.k; ++i) {
            var x = u[i] = this.random.getNextBetween(0.01, 1) - 0.5;
            l += x * x;
        }
        l = Math.sqrt(l);
        return u.map(function (x) { return x *= _this.minD / l; });
    };
    Descent.prototype.computeDerivatives = function (x) {
        var _this = this;
        var n = this.n;
        if (n < 1)
            return;
        var i;
        var d = new Array(this.k);
        var d2 = new Array(this.k);
        var Huu = new Array(this.k);
        var maxH = 0;
        for (var u_1 = 0; u_1 < n; ++u_1) {
            for (i = 0; i < this.k; ++i)
                Huu[i] = this.g[i][u_1] = 0;
            for (var v = 0; v < n; ++v) {
                if (u_1 === v)
                    continue;
                var maxDisplaces = n;
                var distanceSquared = 0;
                while (maxDisplaces--) {
                    distanceSquared = 0;
                    for (i = 0; i < this.k; ++i) {
                        var dx_1 = d[i] = x[i][u_1] - x[i][v];
                        distanceSquared += d2[i] = dx_1 * dx_1;
                    }
                    if (distanceSquared > 1e-9)
                        break;
                    var rd = this.offsetDir();
                    for (i = 0; i < this.k; ++i)
                        x[i][v] += rd[i];
                }
                var distance = Math.sqrt(distanceSquared);
                var idealDistance = this.D[u_1][v];
                var weight = this.G != null ? this.G[u_1][v] : 1;
                if (weight > 1 && distance > idealDistance || !isFinite(idealDistance)) {
                    for (i = 0; i < this.k; ++i)
                        this.H[i][u_1][v] = 0;
                    continue;
                }
                if (weight > 1) {
                    weight = 1;
                }
                var idealDistSquared = idealDistance * idealDistance, gs = 2 * weight * (distance - idealDistance) / (idealDistSquared * distance), distanceCubed = distanceSquared * distance, hs = 2 * -weight / (idealDistSquared * distanceCubed);
                if (!isFinite(gs))
                    console.log(gs);
                for (i = 0; i < this.k; ++i) {
                    this.g[i][u_1] += d[i] * gs;
                    Huu[i] -= this.H[i][u_1][v] = hs * (2 * distanceCubed + idealDistance * (d2[i] - distanceSquared));
                }
            }
            for (i = 0; i < this.k; ++i)
                maxH = Math.max(maxH, this.H[i][u_1][u_1] = Huu[i]);
        }
        var r = this.snapGridSize / 2;
        var g = this.snapGridSize;
        var w = this.snapStrength;
        var k = w / (r * r);
        var numNodes = this.numGridSnapNodes;
        for (var u = 0; u < numNodes; ++u) {
            for (i = 0; i < this.k; ++i) {
                var xiu = this.x[i][u];
                var m = xiu / g;
                var f = m % 1;
                var q = m - f;
                var a = Math.abs(f);
                var dx = (a <= 0.5) ? xiu - q * g :
                    (xiu > 0) ? xiu - (q + 1) * g : xiu - (q - 1) * g;
                if (-r < dx && dx <= r) {
                    if (this.scaleSnapByMaxH) {
                        this.g[i][u] += maxH * k * dx;
                        this.H[i][u][u] += maxH * k;
                    }
                    else {
                        this.g[i][u] += k * dx;
                        this.H[i][u][u] += k;
                    }
                }
            }
        }
        if (!this.locks.isEmpty()) {
            this.locks.apply(function (u, p) {
                for (i = 0; i < _this.k; ++i) {
                    _this.H[i][u][u] += maxH;
                    _this.g[i][u] -= maxH * (p[i] - x[i][u]);
                }
            });
        }
    };
    Descent.dotProd = function (a, b) {
        var x = 0, i = a.length;
        while (i--)
            x += a[i] * b[i];
        return x;
    };
    Descent.rightMultiply = function (m, v, r) {
        var i = m.length;
        while (i--)
            r[i] = Descent.dotProd(m[i], v);
    };
    Descent.prototype.computeStepSize = function (d) {
        var numerator = 0, denominator = 0;
        for (var i = 0; i < this.k; ++i) {
            numerator += Descent.dotProd(this.g[i], d[i]);
            Descent.rightMultiply(this.H[i], d[i], this.Hd[i]);
            denominator += Descent.dotProd(d[i], this.Hd[i]);
        }
        if (denominator === 0 || !isFinite(denominator))
            return 0;
        return 1 * numerator / denominator;
    };
    Descent.prototype.reduceStress = function () {
        this.computeDerivatives(this.x);
        var alpha = this.computeStepSize(this.g);
        for (var i = 0; i < this.k; ++i) {
            this.takeDescentStep(this.x[i], this.g[i], alpha);
        }
        return this.computeStress();
    };
    Descent.copy = function (a, b) {
        var m = a.length, n = b[0].length;
        for (var i = 0; i < m; ++i) {
            for (var j = 0; j < n; ++j) {
                b[i][j] = a[i][j];
            }
        }
    };
    Descent.prototype.stepAndProject = function (x0, r, d, stepSize) {
        Descent.copy(x0, r);
        this.takeDescentStep(r[0], d[0], stepSize);
        if (this.project)
            this.project[0](x0[0], x0[1], r[0]);
        this.takeDescentStep(r[1], d[1], stepSize);
        if (this.project)
            this.project[1](r[0], x0[1], r[1]);
        for (var i = 2; i < this.k; i++)
            this.takeDescentStep(r[i], d[i], stepSize);
    };
    Descent.mApply = function (m, n, f) {
        var i = m;
        while (i-- > 0) {
            var j = n;
            while (j-- > 0)
                f(i, j);
        }
    };
    Descent.prototype.matrixApply = function (f) {
        Descent.mApply(this.k, this.n, f);
    };
    Descent.prototype.computeNextPosition = function (x0, r) {
        var _this = this;
        this.computeDerivatives(x0);
        var alpha = this.computeStepSize(this.g);
        this.stepAndProject(x0, r, this.g, alpha);
        if (this.project) {
            this.matrixApply(function (i, j) { return _this.e[i][j] = x0[i][j] - r[i][j]; });
            var beta = this.computeStepSize(this.e);
            beta = Math.max(0.2, Math.min(beta, 1));
            this.stepAndProject(x0, r, this.e, beta);
        }
    };
    Descent.prototype.run = function (iterations) {
        var stress = Number.MAX_VALUE, converged = false;
        while (!converged && iterations-- > 0) {
            var s = this.rungeKutta();
            converged = Math.abs(stress / s - 1) < this.threshold;
            stress = s;
        }
        return stress;
    };
    Descent.prototype.rungeKutta = function () {
        var _this = this;
        this.computeNextPosition(this.x, this.a);
        Descent.mid(this.x, this.a, this.ia);
        this.computeNextPosition(this.ia, this.b);
        Descent.mid(this.x, this.b, this.ib);
        this.computeNextPosition(this.ib, this.c);
        this.computeNextPosition(this.c, this.d);
        var disp = 0;
        this.matrixApply(function (i, j) {
            var x = (_this.a[i][j] + 2.0 * _this.b[i][j] + 2.0 * _this.c[i][j] + _this.d[i][j]) / 6.0, d = _this.x[i][j] - x;
            disp += d * d;
            _this.x[i][j] = x;
        });
        return disp;
    };
    Descent.mid = function (a, b, m) {
        Descent.mApply(a.length, a[0].length, function (i, j) {
            return m[i][j] = a[i][j] + (b[i][j] - a[i][j]) / 2.0;
        });
    };
    Descent.prototype.takeDescentStep = function (x, d, stepSize) {
        for (var i = 0; i < this.n; ++i) {
            x[i] = x[i] - stepSize * d[i];
        }
    };
    Descent.prototype.computeStress = function () {
        var stress = 0;
        for (var u = 0, nMinus1 = this.n - 1; u < nMinus1; ++u) {
            for (var v = u + 1, n = this.n; v < n; ++v) {
                var l = 0;
                for (var i = 0; i < this.k; ++i) {
                    var dx = this.x[i][u] - this.x[i][v];
                    l += dx * dx;
                }
                l = Math.sqrt(l);
                var d = this.D[u][v];
                if (!isFinite(d))
                    continue;
                var rl = d - l;
                var d2 = d * d;
                stress += rl * rl / d2;
            }
        }
        return stress;
    };
    Descent.zeroDistance = 1e-10;
    return Descent;
}());
exports.Descent = Descent;
var PseudoRandom = (function () {
    function PseudoRandom(seed) {
        if (seed === void 0) { seed = 1; }
        this.seed = seed;
        this.a = 214013;
        this.c = 2531011;
        this.m = 2147483648;
        this.range = 32767;
    }
    PseudoRandom.prototype.getNext = function () {
        this.seed = (this.seed * this.a + this.c) % this.m;
        return (this.seed >> 16) / this.range;
    };
    PseudoRandom.prototype.getNextBetween = function (min, max) {
        return min + this.getNext() * (max - min);
    };
    return PseudoRandom;
}());
exports.PseudoRandom = PseudoRandom;
},{}],8:[function(require,module,exports){
"use strict";
var __extends = (this && this.__extends) || (function () {
    var extendStatics = function (d, b) {
        extendStatics = Object.setPrototypeOf ||
            ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
            function (d, b) { for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p]; };
        return extendStatics(d, b);
    };
    return function (d, b) {
        extendStatics(d, b);
        function __() { this.constructor = d; }
        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
var rectangle_1 = require("./rectangle");
var Point = (function () {
    function Point() {
    }
    return Point;
}());
exports.Point = Point;
var LineSegment = (function () {
    function LineSegment(x1, y1, x2, y2) {
        this.x1 = x1;
        this.y1 = y1;
        this.x2 = x2;
        this.y2 = y2;
    }
    return LineSegment;
}());
exports.LineSegment = LineSegment;
var PolyPoint = (function (_super) {
    __extends(PolyPoint, _super);
    function PolyPoint() {
        return _super !== null && _super.apply(this, arguments) || this;
    }
    return PolyPoint;
}(Point));
exports.PolyPoint = PolyPoint;
function isLeft(P0, P1, P2) {
    return (P1.x - P0.x) * (P2.y - P0.y) - (P2.x - P0.x) * (P1.y - P0.y);
}
exports.isLeft = isLeft;
function above(p, vi, vj) {
    return isLeft(p, vi, vj) > 0;
}
function below(p, vi, vj) {
    return isLeft(p, vi, vj) < 0;
}
function ConvexHull(S) {
    var P = S.slice(0).sort(function (a, b) { return a.x !== b.x ? b.x - a.x : b.y - a.y; });
    var n = S.length, i;
    var minmin = 0;
    var xmin = P[0].x;
    for (i = 1; i < n; ++i) {
        if (P[i].x !== xmin)
            break;
    }
    var minmax = i - 1;
    var H = [];
    H.push(P[minmin]);
    if (minmax === n - 1) {
        if (P[minmax].y !== P[minmin].y)
            H.push(P[minmax]);
    }
    else {
        var maxmin, maxmax = n - 1;
        var xmax = P[n - 1].x;
        for (i = n - 2; i >= 0; i--)
            if (P[i].x !== xmax)
                break;
        maxmin = i + 1;
        i = minmax;
        while (++i <= maxmin) {
            if (isLeft(P[minmin], P[maxmin], P[i]) >= 0 && i < maxmin)
                continue;
            while (H.length > 1) {
                if (isLeft(H[H.length - 2], H[H.length - 1], P[i]) > 0)
                    break;
                else
                    H.length -= 1;
            }
            if (i != minmin)
                H.push(P[i]);
        }
        if (maxmax != maxmin)
            H.push(P[maxmax]);
        var bot = H.length;
        i = maxmin;
        while (--i >= minmax) {
            if (isLeft(P[maxmax], P[minmax], P[i]) >= 0 && i > minmax)
                continue;
            while (H.length > bot) {
                if (isLeft(H[H.length - 2], H[H.length - 1], P[i]) > 0)
                    break;
                else
                    H.length -= 1;
            }
            if (i != minmin)
                H.push(P[i]);
        }
    }
    return H;
}
exports.ConvexHull = ConvexHull;
function clockwiseRadialSweep(p, P, f) {
    P.slice(0).sort(function (a, b) { return Math.atan2(a.y - p.y, a.x - p.x) - Math.atan2(b.y - p.y, b.x - p.x); }).forEach(f);
}
exports.clockwiseRadialSweep = clockwiseRadialSweep;
function nextPolyPoint(p, ps) {
    if (p.polyIndex === ps.length - 1)
        return ps[0];
    return ps[p.polyIndex + 1];
}
function prevPolyPoint(p, ps) {
    if (p.polyIndex === 0)
        return ps[ps.length - 1];
    return ps[p.polyIndex - 1];
}
function tangent_PointPolyC(P, V) {
    var Vclosed = V.slice(0);
    Vclosed.push(V[0]);
    return { rtan: Rtangent_PointPolyC(P, Vclosed), ltan: Ltangent_PointPolyC(P, Vclosed) };
}
function Rtangent_PointPolyC(P, V) {
    var n = V.length - 1;
    var a, b, c;
    var upA, dnC;
    if (below(P, V[1], V[0]) && !above(P, V[n - 1], V[0]))
        return 0;
    for (a = 0, b = n;;) {
        if (b - a === 1)
            if (above(P, V[a], V[b]))
                return a;
            else
                return b;
        c = Math.floor((a + b) / 2);
        dnC = below(P, V[c + 1], V[c]);
        if (dnC && !above(P, V[c - 1], V[c]))
            return c;
        upA = above(P, V[a + 1], V[a]);
        if (upA) {
            if (dnC)
                b = c;
            else {
                if (above(P, V[a], V[c]))
                    b = c;
                else
                    a = c;
            }
        }
        else {
            if (!dnC)
                a = c;
            else {
                if (below(P, V[a], V[c]))
                    b = c;
                else
                    a = c;
            }
        }
    }
}
function Ltangent_PointPolyC(P, V) {
    var n = V.length - 1;
    var a, b, c;
    var dnA, dnC;
    if (above(P, V[n - 1], V[0]) && !below(P, V[1], V[0]))
        return 0;
    for (a = 0, b = n;;) {
        if (b - a === 1)
            if (below(P, V[a], V[b]))
                return a;
            else
                return b;
        c = Math.floor((a + b) / 2);
        dnC = below(P, V[c + 1], V[c]);
        if (above(P, V[c - 1], V[c]) && !dnC)
            return c;
        dnA = below(P, V[a + 1], V[a]);
        if (dnA) {
            if (!dnC)
                b = c;
            else {
                if (below(P, V[a], V[c]))
                    b = c;
                else
                    a = c;
            }
        }
        else {
            if (dnC)
                a = c;
            else {
                if (above(P, V[a], V[c]))
                    b = c;
                else
                    a = c;
            }
        }
    }
}
function tangent_PolyPolyC(V, W, t1, t2, cmp1, cmp2) {
    var ix1, ix2;
    ix1 = t1(W[0], V);
    ix2 = t2(V[ix1], W);
    var done = false;
    while (!done) {
        done = true;
        while (true) {
            if (ix1 === V.length - 1)
                ix1 = 0;
            if (cmp1(W[ix2], V[ix1], V[ix1 + 1]))
                break;
            ++ix1;
        }
        while (true) {
            if (ix2 === 0)
                ix2 = W.length - 1;
            if (cmp2(V[ix1], W[ix2], W[ix2 - 1]))
                break;
            --ix2;
            done = false;
        }
    }
    return { t1: ix1, t2: ix2 };
}
exports.tangent_PolyPolyC = tangent_PolyPolyC;
function LRtangent_PolyPolyC(V, W) {
    var rl = RLtangent_PolyPolyC(W, V);
    return { t1: rl.t2, t2: rl.t1 };
}
exports.LRtangent_PolyPolyC = LRtangent_PolyPolyC;
function RLtangent_PolyPolyC(V, W) {
    return tangent_PolyPolyC(V, W, Rtangent_PointPolyC, Ltangent_PointPolyC, above, below);
}
exports.RLtangent_PolyPolyC = RLtangent_PolyPolyC;
function LLtangent_PolyPolyC(V, W) {
    return tangent_PolyPolyC(V, W, Ltangent_PointPolyC, Ltangent_PointPolyC, below, below);
}
exports.LLtangent_PolyPolyC = LLtangent_PolyPolyC;
function RRtangent_PolyPolyC(V, W) {
    return tangent_PolyPolyC(V, W, Rtangent_PointPolyC, Rtangent_PointPolyC, above, above);
}
exports.RRtangent_PolyPolyC = RRtangent_PolyPolyC;
var BiTangent = (function () {
    function BiTangent(t1, t2) {
        this.t1 = t1;
        this.t2 = t2;
    }
    return BiTangent;
}());
exports.BiTangent = BiTangent;
var BiTangents = (function () {
    function BiTangents() {
    }
    return BiTangents;
}());
exports.BiTangents = BiTangents;
var TVGPoint = (function (_super) {
    __extends(TVGPoint, _super);
    function TVGPoint() {
        return _super !== null && _super.apply(this, arguments) || this;
    }
    return TVGPoint;
}(Point));
exports.TVGPoint = TVGPoint;
var VisibilityVertex = (function () {
    function VisibilityVertex(id, polyid, polyvertid, p) {
        this.id = id;
        this.polyid = polyid;
        this.polyvertid = polyvertid;
        this.p = p;
        p.vv = this;
    }
    return VisibilityVertex;
}());
exports.VisibilityVertex = VisibilityVertex;
var VisibilityEdge = (function () {
    function VisibilityEdge(source, target) {
        this.source = source;
        this.target = target;
    }
    VisibilityEdge.prototype.length = function () {
        var dx = this.source.p.x - this.target.p.x;
        var dy = this.source.p.y - this.target.p.y;
        return Math.sqrt(dx * dx + dy * dy);
    };
    return VisibilityEdge;
}());
exports.VisibilityEdge = VisibilityEdge;
var TangentVisibilityGraph = (function () {
    function TangentVisibilityGraph(P, g0) {
        this.P = P;
        this.V = [];
        this.E = [];
        if (!g0) {
            var n = P.length;
            for (var i = 0; i < n; i++) {
                var p = P[i];
                for (var j = 0; j < p.length; ++j) {
                    var pj = p[j], vv = new VisibilityVertex(this.V.length, i, j, pj);
                    this.V.push(vv);
                    if (j > 0)
                        this.E.push(new VisibilityEdge(p[j - 1].vv, vv));
                }
                if (p.length > 1)
                    this.E.push(new VisibilityEdge(p[0].vv, p[p.length - 1].vv));
            }
            for (var i = 0; i < n - 1; i++) {
                var Pi = P[i];
                for (var j = i + 1; j < n; j++) {
                    var Pj = P[j], t = tangents(Pi, Pj);
                    for (var q in t) {
                        var c = t[q], source = Pi[c.t1], target = Pj[c.t2];
                        this.addEdgeIfVisible(source, target, i, j);
                    }
                }
            }
        }
        else {
            this.V = g0.V.slice(0);
            this.E = g0.E.slice(0);
        }
    }
    TangentVisibilityGraph.prototype.addEdgeIfVisible = function (u, v, i1, i2) {
        if (!this.intersectsPolys(new LineSegment(u.x, u.y, v.x, v.y), i1, i2)) {
            this.E.push(new VisibilityEdge(u.vv, v.vv));
        }
    };
    TangentVisibilityGraph.prototype.addPoint = function (p, i1) {
        var n = this.P.length;
        this.V.push(new VisibilityVertex(this.V.length, n, 0, p));
        for (var i = 0; i < n; ++i) {
            if (i === i1)
                continue;
            var poly = this.P[i], t = tangent_PointPolyC(p, poly);
            this.addEdgeIfVisible(p, poly[t.ltan], i1, i);
            this.addEdgeIfVisible(p, poly[t.rtan], i1, i);
        }
        return p.vv;
    };
    TangentVisibilityGraph.prototype.intersectsPolys = function (l, i1, i2) {
        for (var i = 0, n = this.P.length; i < n; ++i) {
            if (i != i1 && i != i2 && intersects(l, this.P[i]).length > 0) {
                return true;
            }
        }
        return false;
    };
    return TangentVisibilityGraph;
}());
exports.TangentVisibilityGraph = TangentVisibilityGraph;
function intersects(l, P) {
    var ints = [];
    for (var i = 1, n = P.length; i < n; ++i) {
        var int = rectangle_1.Rectangle.lineIntersection(l.x1, l.y1, l.x2, l.y2, P[i - 1].x, P[i - 1].y, P[i].x, P[i].y);
        if (int)
            ints.push(int);
    }
    return ints;
}
function tangents(V, W) {
    var m = V.length - 1, n = W.length - 1;
    var bt = new BiTangents();
    for (var i = 0; i <= m; ++i) {
        for (var j = 0; j <= n; ++j) {
            var v1 = V[i == 0 ? m : i - 1];
            var v2 = V[i];
            var v3 = V[i == m ? 0 : i + 1];
            var w1 = W[j == 0 ? n : j - 1];
            var w2 = W[j];
            var w3 = W[j == n ? 0 : j + 1];
            var v1v2w2 = isLeft(v1, v2, w2);
            var v2w1w2 = isLeft(v2, w1, w2);
            var v2w2w3 = isLeft(v2, w2, w3);
            var w1w2v2 = isLeft(w1, w2, v2);
            var w2v1v2 = isLeft(w2, v1, v2);
            var w2v2v3 = isLeft(w2, v2, v3);
            if (v1v2w2 >= 0 && v2w1w2 >= 0 && v2w2w3 < 0
                && w1w2v2 >= 0 && w2v1v2 >= 0 && w2v2v3 < 0) {
                bt.ll = new BiTangent(i, j);
            }
            else if (v1v2w2 <= 0 && v2w1w2 <= 0 && v2w2w3 > 0
                && w1w2v2 <= 0 && w2v1v2 <= 0 && w2v2v3 > 0) {
                bt.rr = new BiTangent(i, j);
            }
            else if (v1v2w2 <= 0 && v2w1w2 > 0 && v2w2w3 <= 0
                && w1w2v2 >= 0 && w2v1v2 < 0 && w2v2v3 >= 0) {
                bt.rl = new BiTangent(i, j);
            }
            else if (v1v2w2 >= 0 && v2w1w2 < 0 && v2w2w3 >= 0
                && w1w2v2 <= 0 && w2v1v2 > 0 && w2v2v3 <= 0) {
                bt.lr = new BiTangent(i, j);
            }
        }
    }
    return bt;
}
exports.tangents = tangents;
function isPointInsidePoly(p, poly) {
    for (var i = 1, n = poly.length; i < n; ++i)
        if (below(poly[i - 1], poly[i], p))
            return false;
    return true;
}
function isAnyPInQ(p, q) {
    return !p.every(function (v) { return !isPointInsidePoly(v, q); });
}
function polysOverlap(p, q) {
    if (isAnyPInQ(p, q))
        return true;
    if (isAnyPInQ(q, p))
        return true;
    for (var i = 1, n = p.length; i < n; ++i) {
        var v = p[i], u = p[i - 1];
        if (intersects(new LineSegment(u.x, u.y, v.x, v.y), q).length > 0)
            return true;
    }
    return false;
}
exports.polysOverlap = polysOverlap;
},{"./rectangle":17}],9:[function(require,module,exports){
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var rectangle_1 = require("./rectangle");
var vpsc_1 = require("./vpsc");
var shortestpaths_1 = require("./shortestpaths");
var NodeWrapper = (function () {
    function NodeWrapper(id, rect, children) {
        this.id = id;
        this.rect = rect;
        this.children = children;
        this.leaf = typeof children === 'undefined' || children.length === 0;
    }
    return NodeWrapper;
}());
exports.NodeWrapper = NodeWrapper;
var Vert = (function () {
    function Vert(id, x, y, node, line) {
        if (node === void 0) { node = null; }
        if (line === void 0) { line = null; }
        this.id = id;
        this.x = x;
        this.y = y;
        this.node = node;
        this.line = line;
    }
    return Vert;
}());
exports.Vert = Vert;
var LongestCommonSubsequence = (function () {
    function LongestCommonSubsequence(s, t) {
        this.s = s;
        this.t = t;
        var mf = LongestCommonSubsequence.findMatch(s, t);
        var tr = t.slice(0).reverse();
        var mr = LongestCommonSubsequence.findMatch(s, tr);
        if (mf.length >= mr.length) {
            this.length = mf.length;
            this.si = mf.si;
            this.ti = mf.ti;
            this.reversed = false;
        }
        else {
            this.length = mr.length;
            this.si = mr.si;
            this.ti = t.length - mr.ti - mr.length;
            this.reversed = true;
        }
    }
    LongestCommonSubsequence.findMatch = function (s, t) {
        var m = s.length;
        var n = t.length;
        var match = { length: 0, si: -1, ti: -1 };
        var l = new Array(m);
        for (var i = 0; i < m; i++) {
            l[i] = new Array(n);
            for (var j = 0; j < n; j++)
                if (s[i] === t[j]) {
                    var v = l[i][j] = (i === 0 || j === 0) ? 1 : l[i - 1][j - 1] + 1;
                    if (v > match.length) {
                        match.length = v;
                        match.si = i - v + 1;
                        match.ti = j - v + 1;
                    }
                    ;
                }
                else
                    l[i][j] = 0;
        }
        return match;
    };
    LongestCommonSubsequence.prototype.getSequence = function () {
        return this.length >= 0 ? this.s.slice(this.si, this.si + this.length) : [];
    };
    return LongestCommonSubsequence;
}());
exports.LongestCommonSubsequence = LongestCommonSubsequence;
var GridRouter = (function () {
    function GridRouter(originalnodes, accessor, groupPadding) {
        var _this = this;
        if (groupPadding === void 0) { groupPadding = 12; }
        this.originalnodes = originalnodes;
        this.groupPadding = groupPadding;
        this.leaves = null;
        this.nodes = originalnodes.map(function (v, i) { return new NodeWrapper(i, accessor.getBounds(v), accessor.getChildren(v)); });
        this.leaves = this.nodes.filter(function (v) { return v.leaf; });
        this.groups = this.nodes.filter(function (g) { return !g.leaf; });
        this.cols = this.getGridLines('x');
        this.rows = this.getGridLines('y');
        this.groups.forEach(function (v) {
            return v.children.forEach(function (c) { return _this.nodes[c].parent = v; });
        });
        this.root = { children: [] };
        this.nodes.forEach(function (v) {
            if (typeof v.parent === 'undefined') {
                v.parent = _this.root;
                _this.root.children.push(v.id);
            }
            v.ports = [];
        });
        this.backToFront = this.nodes.slice(0);
        this.backToFront.sort(function (x, y) { return _this.getDepth(x) - _this.getDepth(y); });
        var frontToBackGroups = this.backToFront.slice(0).reverse().filter(function (g) { return !g.leaf; });
        frontToBackGroups.forEach(function (v) {
            var r = rectangle_1.Rectangle.empty();
            v.children.forEach(function (c) { return r = r.union(_this.nodes[c].rect); });
            v.rect = r.inflate(_this.groupPadding);
        });
        var colMids = this.midPoints(this.cols.map(function (r) { return r.pos; }));
        var rowMids = this.midPoints(this.rows.map(function (r) { return r.pos; }));
        var rowx = colMids[0], rowX = colMids[colMids.length - 1];
        var coly = rowMids[0], colY = rowMids[rowMids.length - 1];
        var hlines = this.rows.map(function (r) { return ({ x1: rowx, x2: rowX, y1: r.pos, y2: r.pos }); })
            .concat(rowMids.map(function (m) { return ({ x1: rowx, x2: rowX, y1: m, y2: m }); }));
        var vlines = this.cols.map(function (c) { return ({ x1: c.pos, x2: c.pos, y1: coly, y2: colY }); })
            .concat(colMids.map(function (m) { return ({ x1: m, x2: m, y1: coly, y2: colY }); }));
        var lines = hlines.concat(vlines);
        lines.forEach(function (l) { return l.verts = []; });
        this.verts = [];
        this.edges = [];
        hlines.forEach(function (h) {
            return vlines.forEach(function (v) {
                var p = new Vert(_this.verts.length, v.x1, h.y1);
                h.verts.push(p);
                v.verts.push(p);
                _this.verts.push(p);
                var i = _this.backToFront.length;
                while (i-- > 0) {
                    var node = _this.backToFront[i], r = node.rect;
                    var dx = Math.abs(p.x - r.cx()), dy = Math.abs(p.y - r.cy());
                    if (dx < r.width() / 2 && dy < r.height() / 2) {
                        p.node = node;
                        break;
                    }
                }
            });
        });
        lines.forEach(function (l, li) {
            _this.nodes.forEach(function (v, i) {
                v.rect.lineIntersections(l.x1, l.y1, l.x2, l.y2).forEach(function (intersect, j) {
                    var p = new Vert(_this.verts.length, intersect.x, intersect.y, v, l);
                    _this.verts.push(p);
                    l.verts.push(p);
                    v.ports.push(p);
                });
            });
            var isHoriz = Math.abs(l.y1 - l.y2) < 0.1;
            var delta = function (a, b) { return isHoriz ? b.x - a.x : b.y - a.y; };
            l.verts.sort(delta);
            for (var i = 1; i < l.verts.length; i++) {
                var u = l.verts[i - 1], v = l.verts[i];
                if (u.node && u.node === v.node && u.node.leaf)
                    continue;
                _this.edges.push({ source: u.id, target: v.id, length: Math.abs(delta(u, v)) });
            }
        });
    }
    GridRouter.prototype.avg = function (a) { return a.reduce(function (x, y) { return x + y; }) / a.length; };
    GridRouter.prototype.getGridLines = function (axis) {
        var columns = [];
        var ls = this.leaves.slice(0, this.leaves.length);
        while (ls.length > 0) {
            var overlapping = ls.filter(function (v) { return v.rect['overlap' + axis.toUpperCase()](ls[0].rect); });
            var col = {
                nodes: overlapping,
                pos: this.avg(overlapping.map(function (v) { return v.rect['c' + axis](); }))
            };
            columns.push(col);
            col.nodes.forEach(function (v) { return ls.splice(ls.indexOf(v), 1); });
        }
        columns.sort(function (a, b) { return a.pos - b.pos; });
        return columns;
    };
    GridRouter.prototype.getDepth = function (v) {
        var depth = 0;
        while (v.parent !== this.root) {
            depth++;
            v = v.parent;
        }
        return depth;
    };
    GridRouter.prototype.midPoints = function (a) {
        var gap = a[1] - a[0];
        var mids = [a[0] - gap / 2];
        for (var i = 1; i < a.length; i++) {
            mids.push((a[i] + a[i - 1]) / 2);
        }
        mids.push(a[a.length - 1] + gap / 2);
        return mids;
    };
    GridRouter.prototype.findLineage = function (v) {
        var lineage = [v];
        do {
            v = v.parent;
            lineage.push(v);
        } while (v !== this.root);
        return lineage.reverse();
    };
    GridRouter.prototype.findAncestorPathBetween = function (a, b) {
        var aa = this.findLineage(a), ba = this.findLineage(b), i = 0;
        while (aa[i] === ba[i])
            i++;
        return { commonAncestor: aa[i - 1], lineages: aa.slice(i).concat(ba.slice(i)) };
    };
    GridRouter.prototype.siblingObstacles = function (a, b) {
        var _this = this;
        var path = this.findAncestorPathBetween(a, b);
        var lineageLookup = {};
        path.lineages.forEach(function (v) { return lineageLookup[v.id] = {}; });
        var obstacles = path.commonAncestor.children.filter(function (v) { return !(v in lineageLookup); });
        path.lineages
            .filter(function (v) { return v.parent !== path.commonAncestor; })
            .forEach(function (v) { return obstacles = obstacles.concat(v.parent.children.filter(function (c) { return c !== v.id; })); });
        return obstacles.map(function (v) { return _this.nodes[v]; });
    };
    GridRouter.getSegmentSets = function (routes, x, y) {
        var vsegments = [];
        for (var ei = 0; ei < routes.length; ei++) {
            var route = routes[ei];
            for (var si = 0; si < route.length; si++) {
                var s = route[si];
                s.edgeid = ei;
                s.i = si;
                var sdx = s[1][x] - s[0][x];
                if (Math.abs(sdx) < 0.1) {
                    vsegments.push(s);
                }
            }
        }
        vsegments.sort(function (a, b) { return a[0][x] - b[0][x]; });
        var vsegmentsets = [];
        var segmentset = null;
        for (var i = 0; i < vsegments.length; i++) {
            var s = vsegments[i];
            if (!segmentset || Math.abs(s[0][x] - segmentset.pos) > 0.1) {
                segmentset = { pos: s[0][x], segments: [] };
                vsegmentsets.push(segmentset);
            }
            segmentset.segments.push(s);
        }
        return vsegmentsets;
    };
    GridRouter.nudgeSegs = function (x, y, routes, segments, leftOf, gap) {
        var n = segments.length;
        if (n <= 1)
            return;
        var vs = segments.map(function (s) { return new vpsc_1.Variable(s[0][x]); });
        var cs = [];
        for (var i = 0; i < n; i++) {
            for (var j = 0; j < n; j++) {
                if (i === j)
                    continue;
                var s1 = segments[i], s2 = segments[j], e1 = s1.edgeid, e2 = s2.edgeid, lind = -1, rind = -1;
                if (x == 'x') {
                    if (leftOf(e1, e2)) {
                        if (s1[0][y] < s1[1][y]) {
                            lind = j, rind = i;
                        }
                        else {
                            lind = i, rind = j;
                        }
                    }
                }
                else {
                    if (leftOf(e1, e2)) {
                        if (s1[0][y] < s1[1][y]) {
                            lind = i, rind = j;
                        }
                        else {
                            lind = j, rind = i;
                        }
                    }
                }
                if (lind >= 0) {
                    cs.push(new vpsc_1.Constraint(vs[lind], vs[rind], gap));
                }
            }
        }
        var solver = new vpsc_1.Solver(vs, cs);
        solver.solve();
        vs.forEach(function (v, i) {
            var s = segments[i];
            var pos = v.position();
            s[0][x] = s[1][x] = pos;
            var route = routes[s.edgeid];
            if (s.i > 0)
                route[s.i - 1][1][x] = pos;
            if (s.i < route.length - 1)
                route[s.i + 1][0][x] = pos;
        });
    };
    GridRouter.nudgeSegments = function (routes, x, y, leftOf, gap) {
        var vsegmentsets = GridRouter.getSegmentSets(routes, x, y);
        for (var i = 0; i < vsegmentsets.length; i++) {
            var ss = vsegmentsets[i];
            var events = [];
            for (var j = 0; j < ss.segments.length; j++) {
                var s = ss.segments[j];
                events.push({ type: 0, s: s, pos: Math.min(s[0][y], s[1][y]) });
                events.push({ type: 1, s: s, pos: Math.max(s[0][y], s[1][y]) });
            }
            events.sort(function (a, b) { return a.pos - b.pos + a.type - b.type; });
            var open = [];
            var openCount = 0;
            events.forEach(function (e) {
                if (e.type === 0) {
                    open.push(e.s);
                    openCount++;
                }
                else {
                    openCount--;
                }
                if (openCount == 0) {
                    GridRouter.nudgeSegs(x, y, routes, open, leftOf, gap);
                    open = [];
                }
            });
        }
    };
    GridRouter.prototype.routeEdges = function (edges, nudgeGap, source, target) {
        var _this = this;
        var routePaths = edges.map(function (e) { return _this.route(source(e), target(e)); });
        var order = GridRouter.orderEdges(routePaths);
        var routes = routePaths.map(function (e) { return GridRouter.makeSegments(e); });
        GridRouter.nudgeSegments(routes, 'x', 'y', order, nudgeGap);
        GridRouter.nudgeSegments(routes, 'y', 'x', order, nudgeGap);
        GridRouter.unreverseEdges(routes, routePaths);
        return routes;
    };
    GridRouter.unreverseEdges = function (routes, routePaths) {
        routes.forEach(function (segments, i) {
            var path = routePaths[i];
            if (path.reversed) {
                segments.reverse();
                segments.forEach(function (segment) {
                    segment.reverse();
                });
            }
        });
    };
    GridRouter.angleBetween2Lines = function (line1, line2) {
        var angle1 = Math.atan2(line1[0].y - line1[1].y, line1[0].x - line1[1].x);
        var angle2 = Math.atan2(line2[0].y - line2[1].y, line2[0].x - line2[1].x);
        var diff = angle1 - angle2;
        if (diff > Math.PI || diff < -Math.PI) {
            diff = angle2 - angle1;
        }
        return diff;
    };
    GridRouter.isLeft = function (a, b, c) {
        return ((b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)) <= 0;
    };
    GridRouter.getOrder = function (pairs) {
        var outgoing = {};
        for (var i = 0; i < pairs.length; i++) {
            var p = pairs[i];
            if (typeof outgoing[p.l] === 'undefined')
                outgoing[p.l] = {};
            outgoing[p.l][p.r] = true;
        }
        return function (l, r) { return typeof outgoing[l] !== 'undefined' && outgoing[l][r]; };
    };
    GridRouter.orderEdges = function (edges) {
        var edgeOrder = [];
        for (var i = 0; i < edges.length - 1; i++) {
            for (var j = i + 1; j < edges.length; j++) {
                var e = edges[i], f = edges[j], lcs = new LongestCommonSubsequence(e, f);
                var u, vi, vj;
                if (lcs.length === 0)
                    continue;
                if (lcs.reversed) {
                    f.reverse();
                    f.reversed = true;
                    lcs = new LongestCommonSubsequence(e, f);
                }
                if ((lcs.si <= 0 || lcs.ti <= 0) &&
                    (lcs.si + lcs.length >= e.length || lcs.ti + lcs.length >= f.length)) {
                    edgeOrder.push({ l: i, r: j });
                    continue;
                }
                if (lcs.si + lcs.length >= e.length || lcs.ti + lcs.length >= f.length) {
                    u = e[lcs.si + 1];
                    vj = e[lcs.si - 1];
                    vi = f[lcs.ti - 1];
                }
                else {
                    u = e[lcs.si + lcs.length - 2];
                    vi = e[lcs.si + lcs.length];
                    vj = f[lcs.ti + lcs.length];
                }
                if (GridRouter.isLeft(u, vi, vj)) {
                    edgeOrder.push({ l: j, r: i });
                }
                else {
                    edgeOrder.push({ l: i, r: j });
                }
            }
        }
        return GridRouter.getOrder(edgeOrder);
    };
    GridRouter.makeSegments = function (path) {
        function copyPoint(p) {
            return { x: p.x, y: p.y };
        }
        var isStraight = function (a, b, c) { return Math.abs((b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)) < 0.001; };
        var segments = [];
        var a = copyPoint(path[0]);
        for (var i = 1; i < path.length; i++) {
            var b = copyPoint(path[i]), c = i < path.length - 1 ? path[i + 1] : null;
            if (!c || !isStraight(a, b, c)) {
                segments.push([a, b]);
                a = b;
            }
        }
        return segments;
    };
    GridRouter.prototype.route = function (s, t) {
        var _this = this;
        var source = this.nodes[s], target = this.nodes[t];
        this.obstacles = this.siblingObstacles(source, target);
        var obstacleLookup = {};
        this.obstacles.forEach(function (o) { return obstacleLookup[o.id] = o; });
        this.passableEdges = this.edges.filter(function (e) {
            var u = _this.verts[e.source], v = _this.verts[e.target];
            return !(u.node && u.node.id in obstacleLookup
                || v.node && v.node.id in obstacleLookup);
        });
        for (var i = 1; i < source.ports.length; i++) {
            var u = source.ports[0].id;
            var v = source.ports[i].id;
            this.passableEdges.push({
                source: u,
                target: v,
                length: 0
            });
        }
        for (var i = 1; i < target.ports.length; i++) {
            var u = target.ports[0].id;
            var v = target.ports[i].id;
            this.passableEdges.push({
                source: u,
                target: v,
                length: 0
            });
        }
        var getSource = function (e) { return e.source; }, getTarget = function (e) { return e.target; }, getLength = function (e) { return e.length; };
        var shortestPathCalculator = new shortestpaths_1.Calculator(this.verts.length, this.passableEdges, getSource, getTarget, getLength);
        var bendPenalty = function (u, v, w) {
            var a = _this.verts[u], b = _this.verts[v], c = _this.verts[w];
            var dx = Math.abs(c.x - a.x), dy = Math.abs(c.y - a.y);
            if (a.node === source && a.node === b.node || b.node === target && b.node === c.node)
                return 0;
            return dx > 1 && dy > 1 ? 1000 : 0;
        };
        var shortestPath = shortestPathCalculator.PathFromNodeToNodeWithPrevCost(source.ports[0].id, target.ports[0].id, bendPenalty);
        var pathPoints = shortestPath.reverse().map(function (vi) { return _this.verts[vi]; });
        pathPoints.push(this.nodes[target.id].ports[0]);
        return pathPoints.filter(function (v, i) {
            return !(i < pathPoints.length - 1 && pathPoints[i + 1].node === source && v.node === source
                || i > 0 && v.node === target && pathPoints[i - 1].node === target);
        });
    };
    GridRouter.getRoutePath = function (route, cornerradius, arrowwidth, arrowheight) {
        var result = {
            routepath: 'M ' + route[0][0].x + ' ' + route[0][0].y + ' ',
            arrowpath: ''
        };
        if (route.length > 1) {
            for (var i = 0; i < route.length; i++) {
                var li = route[i];
                var x = li[1].x, y = li[1].y;
                var dx = x - li[0].x;
                var dy = y - li[0].y;
                if (i < route.length - 1) {
                    if (Math.abs(dx) > 0) {
                        x -= dx / Math.abs(dx) * cornerradius;
                    }
                    else {
                        y -= dy / Math.abs(dy) * cornerradius;
                    }
                    result.routepath += 'L ' + x + ' ' + y + ' ';
                    var l = route[i + 1];
                    var x0 = l[0].x, y0 = l[0].y;
                    var x1 = l[1].x;
                    var y1 = l[1].y;
                    dx = x1 - x0;
                    dy = y1 - y0;
                    var angle = GridRouter.angleBetween2Lines(li, l) < 0 ? 1 : 0;
                    var x2, y2;
                    if (Math.abs(dx) > 0) {
                        x2 = x0 + dx / Math.abs(dx) * cornerradius;
                        y2 = y0;
                    }
                    else {
                        x2 = x0;
                        y2 = y0 + dy / Math.abs(dy) * cornerradius;
                    }
                    var cx = Math.abs(x2 - x);
                    var cy = Math.abs(y2 - y);
                    result.routepath += 'A ' + cx + ' ' + cy + ' 0 0 ' + angle + ' ' + x2 + ' ' + y2 + ' ';
                }
                else {
                    var arrowtip = [x, y];
                    var arrowcorner1, arrowcorner2;
                    if (Math.abs(dx) > 0) {
                        x -= dx / Math.abs(dx) * arrowheight;
                        arrowcorner1 = [x, y + arrowwidth];
                        arrowcorner2 = [x, y - arrowwidth];
                    }
                    else {
                        y -= dy / Math.abs(dy) * arrowheight;
                        arrowcorner1 = [x + arrowwidth, y];
                        arrowcorner2 = [x - arrowwidth, y];
                    }
                    result.routepath += 'L ' + x + ' ' + y + ' ';
                    if (arrowheight > 0) {
                        result.arrowpath = 'M ' + arrowtip[0] + ' ' + arrowtip[1] + ' L ' + arrowcorner1[0] + ' ' + arrowcorner1[1]
                            + ' L ' + arrowcorner2[0] + ' ' + arrowcorner2[1];
                    }
                }
            }
        }
        else {
            var li = route[0];
            var x = li[1].x, y = li[1].y;
            var dx = x - li[0].x;
            var dy = y - li[0].y;
            var arrowtip = [x, y];
            var arrowcorner1, arrowcorner2;
            if (Math.abs(dx) > 0) {
                x -= dx / Math.abs(dx) * arrowheight;
                arrowcorner1 = [x, y + arrowwidth];
                arrowcorner2 = [x, y - arrowwidth];
            }
            else {
                y -= dy / Math.abs(dy) * arrowheight;
                arrowcorner1 = [x + arrowwidth, y];
                arrowcorner2 = [x - arrowwidth, y];
            }
            result.routepath += 'L ' + x + ' ' + y + ' ';
            if (arrowheight > 0) {
                result.arrowpath = 'M ' + arrowtip[0] + ' ' + arrowtip[1] + ' L ' + arrowcorner1[0] + ' ' + arrowcorner1[1]
                    + ' L ' + arrowcorner2[0] + ' ' + arrowcorner2[1];
            }
        }
        return result;
    };
    return GridRouter;
}());
exports.GridRouter = GridRouter;
},{"./rectangle":17,"./shortestpaths":18,"./vpsc":19}],10:[function(require,module,exports){
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var packingOptions = {
    PADDING: 10,
    GOLDEN_SECTION: (1 + Math.sqrt(5)) / 2,
    FLOAT_EPSILON: 0.0001,
    MAX_INERATIONS: 100
};
function applyPacking(graphs, w, h, node_size, desired_ratio, centerGraph) {
    if (desired_ratio === void 0) { desired_ratio = 1; }
    if (centerGraph === void 0) { centerGraph = true; }
    var init_x = 0, init_y = 0, svg_width = w, svg_height = h, desired_ratio = typeof desired_ratio !== 'undefined' ? desired_ratio : 1, node_size = typeof node_size !== 'undefined' ? node_size : 0, real_width = 0, real_height = 0, min_width = 0, global_bottom = 0, line = [];
    if (graphs.length == 0)
        return;
    calculate_bb(graphs);
    apply(graphs, desired_ratio);
    if (centerGraph) {
        put_nodes_to_right_positions(graphs);
    }
    function calculate_bb(graphs) {
        graphs.forEach(function (g) {
            calculate_single_bb(g);
        });
        function calculate_single_bb(graph) {
            var min_x = Number.MAX_VALUE, min_y = Number.MAX_VALUE, max_x = 0, max_y = 0;
            graph.array.forEach(function (v) {
                var w = typeof v.width !== 'undefined' ? v.width : node_size;
                var h = typeof v.height !== 'undefined' ? v.height : node_size;
                w /= 2;
                h /= 2;
                max_x = Math.max(v.x + w, max_x);
                min_x = Math.min(v.x - w, min_x);
                max_y = Math.max(v.y + h, max_y);
                min_y = Math.min(v.y - h, min_y);
            });
            graph.width = max_x - min_x;
            graph.height = max_y - min_y;
        }
    }
    function put_nodes_to_right_positions(graphs) {
        graphs.forEach(function (g) {
            var center = { x: 0, y: 0 };
            g.array.forEach(function (node) {
                center.x += node.x;
                center.y += node.y;
            });
            center.x /= g.array.length;
            center.y /= g.array.length;
            var corner = { x: center.x - g.width / 2, y: center.y - g.height / 2 };
            var offset = { x: g.x - corner.x + svg_width / 2 - real_width / 2, y: g.y - corner.y + svg_height / 2 - real_height / 2 };
            g.array.forEach(function (node) {
                node.x += offset.x;
                node.y += offset.y;
            });
        });
    }
    function apply(data, desired_ratio) {
        var curr_best_f = Number.POSITIVE_INFINITY;
        var curr_best = 0;
        data.sort(function (a, b) { return b.height - a.height; });
        min_width = data.reduce(function (a, b) {
            return a.width < b.width ? a.width : b.width;
        });
        var left = x1 = min_width;
        var right = x2 = get_entire_width(data);
        var iterationCounter = 0;
        var f_x1 = Number.MAX_VALUE;
        var f_x2 = Number.MAX_VALUE;
        var flag = -1;
        var dx = Number.MAX_VALUE;
        var df = Number.MAX_VALUE;
        while ((dx > min_width) || df > packingOptions.FLOAT_EPSILON) {
            if (flag != 1) {
                var x1 = right - (right - left) / packingOptions.GOLDEN_SECTION;
                var f_x1 = step(data, x1);
            }
            if (flag != 0) {
                var x2 = left + (right - left) / packingOptions.GOLDEN_SECTION;
                var f_x2 = step(data, x2);
            }
            dx = Math.abs(x1 - x2);
            df = Math.abs(f_x1 - f_x2);
            if (f_x1 < curr_best_f) {
                curr_best_f = f_x1;
                curr_best = x1;
            }
            if (f_x2 < curr_best_f) {
                curr_best_f = f_x2;
                curr_best = x2;
            }
            if (f_x1 > f_x2) {
                left = x1;
                x1 = x2;
                f_x1 = f_x2;
                flag = 1;
            }
            else {
                right = x2;
                x2 = x1;
                f_x2 = f_x1;
                flag = 0;
            }
            if (iterationCounter++ > 100) {
                break;
            }
        }
        step(data, curr_best);
    }
    function step(data, max_width) {
        line = [];
        real_width = 0;
        real_height = 0;
        global_bottom = init_y;
        for (var i = 0; i < data.length; i++) {
            var o = data[i];
            put_rect(o, max_width);
        }
        return Math.abs(get_real_ratio() - desired_ratio);
    }
    function put_rect(rect, max_width) {
        var parent = undefined;
        for (var i = 0; i < line.length; i++) {
            if ((line[i].space_left >= rect.height) && (line[i].x + line[i].width + rect.width + packingOptions.PADDING - max_width) <= packingOptions.FLOAT_EPSILON) {
                parent = line[i];
                break;
            }
        }
        line.push(rect);
        if (parent !== undefined) {
            rect.x = parent.x + parent.width + packingOptions.PADDING;
            rect.y = parent.bottom;
            rect.space_left = rect.height;
            rect.bottom = rect.y;
            parent.space_left -= rect.height + packingOptions.PADDING;
            parent.bottom += rect.height + packingOptions.PADDING;
        }
        else {
            rect.y = global_bottom;
            global_bottom += rect.height + packingOptions.PADDING;
            rect.x = init_x;
            rect.bottom = rect.y;
            rect.space_left = rect.height;
        }
        if (rect.y + rect.height - real_height > -packingOptions.FLOAT_EPSILON)
            real_height = rect.y + rect.height - init_y;
        if (rect.x + rect.width - real_width > -packingOptions.FLOAT_EPSILON)
            real_width = rect.x + rect.width - init_x;
    }
    ;
    function get_entire_width(data) {
        var width = 0;
        data.forEach(function (d) { return width += d.width + packingOptions.PADDING; });
        return width;
    }
    function get_real_ratio() {
        return (real_width / real_height);
    }
}
exports.applyPacking = applyPacking;
function separateGraphs(nodes, links) {
    var marks = {};
    var ways = {};
    var graphs = [];
    var clusters = 0;
    for (var i = 0; i < links.length; i++) {
        var link = links[i];
        var n1 = link.source;
        var n2 = link.target;
        if (ways[n1.index])
            ways[n1.index].push(n2);
        else
            ways[n1.index] = [n2];
        if (ways[n2.index])
            ways[n2.index].push(n1);
        else
            ways[n2.index] = [n1];
    }
    for (var i = 0; i < nodes.length; i++) {
        var node = nodes[i];
        if (marks[node.index])
            continue;
        explore_node(node, true);
    }
    function explore_node(n, is_new) {
        if (marks[n.index] !== undefined)
            return;
        if (is_new) {
            clusters++;
            graphs.push({ array: [] });
        }
        marks[n.index] = clusters;
        graphs[clusters - 1].array.push(n);
        var adjacent = ways[n.index];
        if (!adjacent)
            return;
        for (var j = 0; j < adjacent.length; j++) {
            explore_node(adjacent[j], false);
        }
    }
    return graphs;
}
exports.separateGraphs = separateGraphs;
},{}],11:[function(require,module,exports){
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var powergraph = require("./powergraph");
var linklengths_1 = require("./linklengths");
var descent_1 = require("./descent");
var rectangle_1 = require("./rectangle");
var shortestpaths_1 = require("./shortestpaths");
var geom_1 = require("./geom");
var handledisconnected_1 = require("./handledisconnected");
var EventType;
(function (EventType) {
    EventType[EventType["start"] = 0] = "start";
    EventType[EventType["tick"] = 1] = "tick";
    EventType[EventType["end"] = 2] = "end";
})(EventType = exports.EventType || (exports.EventType = {}));
;
function isGroup(g) {
    return typeof g.leaves !== 'undefined' || typeof g.groups !== 'undefined';
}
var Layout = (function () {
    function Layout() {
        var _this = this;
        this._canvasSize = [1, 1];
        this._linkDistance = 20;
        this._defaultNodeSize = 10;
        this._linkLengthCalculator = null;
        this._linkType = null;
        this._avoidOverlaps = false;
        this._handleDisconnected = true;
        this._running = false;
        this._nodes = [];
        this._groups = [];
        this._rootGroup = null;
        this._links = [];
        this._constraints = [];
        this._distanceMatrix = null;
        this._descent = null;
        this._directedLinkConstraints = null;
        this._threshold = 0.01;
        this._visibilityGraph = null;
        this._groupCompactness = 1e-6;
        this.event = null;
        this.linkAccessor = {
            getSourceIndex: Layout.getSourceIndex,
            getTargetIndex: Layout.getTargetIndex,
            setLength: Layout.setLinkLength,
            getType: function (l) { return typeof _this._linkType === "function" ? _this._linkType(l) : 0; }
        };
    }
    Layout.prototype.on = function (e, listener) {
        if (!this.event)
            this.event = {};
        if (typeof e === 'string') {
            this.event[EventType[e]] = listener;
        }
        else {
            this.event[e] = listener;
        }
        return this;
    };
    Layout.prototype.trigger = function (e) {
        if (this.event && typeof this.event[e.type] !== 'undefined') {
            this.event[e.type](e);
        }
    };
    Layout.prototype.kick = function () {
        while (!this.tick())
            ;
    };
    Layout.prototype.tick = function () {
        if (this._alpha < this._threshold) {
            this._running = false;
            this.trigger({ type: EventType.end, alpha: this._alpha = 0, stress: this._lastStress });
            return true;
        }
        var n = this._nodes.length, m = this._links.length;
        var o, i;
        this._descent.locks.clear();
        for (i = 0; i < n; ++i) {
            o = this._nodes[i];
            if (o.fixed) {
                if (typeof o.px === 'undefined' || typeof o.py === 'undefined') {
                    o.px = o.x;
                    o.py = o.y;
                }
                var p = [o.px, o.py];
                this._descent.locks.add(i, p);
            }
        }
        var s1 = this._descent.rungeKutta();
        if (s1 === 0) {
            this._alpha = 0;
        }
        else if (typeof this._lastStress !== 'undefined') {
            this._alpha = s1;
        }
        this._lastStress = s1;
        this.updateNodePositions();
        this.trigger({ type: EventType.tick, alpha: this._alpha, stress: this._lastStress });
        return false;
    };
    Layout.prototype.updateNodePositions = function () {
        var x = this._descent.x[0], y = this._descent.x[1];
        var o, i = this._nodes.length;
        while (i--) {
            o = this._nodes[i];
            o.x = x[i];
            o.y = y[i];
        }
    };
    Layout.prototype.nodes = function (v) {
        if (!v) {
            if (this._nodes.length === 0 && this._links.length > 0) {
                var n = 0;
                this._links.forEach(function (l) {
                    n = Math.max(n, l.source, l.target);
                });
                this._nodes = new Array(++n);
                for (var i = 0; i < n; ++i) {
                    this._nodes[i] = {};
                }
            }
            return this._nodes;
        }
        this._nodes = v;
        return this;
    };
    Layout.prototype.groups = function (x) {
        var _this = this;
        if (!x)
            return this._groups;
        this._groups = x;
        this._rootGroup = {};
        this._groups.forEach(function (g) {
            if (typeof g.padding === "undefined")
                g.padding = 1;
            if (typeof g.leaves !== "undefined") {
                g.leaves.forEach(function (v, i) {
                    if (typeof v === 'number')
                        (g.leaves[i] = _this._nodes[v]).parent = g;
                });
            }
            if (typeof g.groups !== "undefined") {
                g.groups.forEach(function (gi, i) {
                    if (typeof gi === 'number')
                        (g.groups[i] = _this._groups[gi]).parent = g;
                });
            }
        });
        this._rootGroup.leaves = this._nodes.filter(function (v) { return typeof v.parent === 'undefined'; });
        this._rootGroup.groups = this._groups.filter(function (g) { return typeof g.parent === 'undefined'; });
        return this;
    };
    Layout.prototype.powerGraphGroups = function (f) {
        var g = powergraph.getGroups(this._nodes, this._links, this.linkAccessor, this._rootGroup);
        this.groups(g.groups);
        f(g);
        return this;
    };
    Layout.prototype.avoidOverlaps = function (v) {
        if (!arguments.length)
            return this._avoidOverlaps;
        this._avoidOverlaps = v;
        return this;
    };
    Layout.prototype.handleDisconnected = function (v) {
        if (!arguments.length)
            return this._handleDisconnected;
        this._handleDisconnected = v;
        return this;
    };
    Layout.prototype.flowLayout = function (axis, minSeparation) {
        if (!arguments.length)
            axis = 'y';
        this._directedLinkConstraints = {
            axis: axis,
            getMinSeparation: typeof minSeparation === 'number' ? function () { return minSeparation; } : minSeparation
        };
        return this;
    };
    Layout.prototype.links = function (x) {
        if (!arguments.length)
            return this._links;
        this._links = x;
        return this;
    };
    Layout.prototype.constraints = function (c) {
        if (!arguments.length)
            return this._constraints;
        this._constraints = c;
        return this;
    };
    Layout.prototype.distanceMatrix = function (d) {
        if (!arguments.length)
            return this._distanceMatrix;
        this._distanceMatrix = d;
        return this;
    };
    Layout.prototype.size = function (x) {
        if (!x)
            return this._canvasSize;
        this._canvasSize = x;
        return this;
    };
    Layout.prototype.defaultNodeSize = function (x) {
        if (!x)
            return this._defaultNodeSize;
        this._defaultNodeSize = x;
        return this;
    };
    Layout.prototype.groupCompactness = function (x) {
        if (!x)
            return this._groupCompactness;
        this._groupCompactness = x;
        return this;
    };
    Layout.prototype.linkDistance = function (x) {
        if (!x) {
            return this._linkDistance;
        }
        this._linkDistance = typeof x === "function" ? x : +x;
        this._linkLengthCalculator = null;
        return this;
    };
    Layout.prototype.linkType = function (f) {
        this._linkType = f;
        return this;
    };
    Layout.prototype.convergenceThreshold = function (x) {
        if (!x)
            return this._threshold;
        this._threshold = typeof x === "function" ? x : +x;
        return this;
    };
    Layout.prototype.alpha = function (x) {
        if (!arguments.length)
            return this._alpha;
        else {
            x = +x;
            if (this._alpha) {
                if (x > 0)
                    this._alpha = x;
                else
                    this._alpha = 0;
            }
            else if (x > 0) {
                if (!this._running) {
                    this._running = true;
                    this.trigger({ type: EventType.start, alpha: this._alpha = x });
                    this.kick();
                }
            }
            return this;
        }
    };
    Layout.prototype.getLinkLength = function (link) {
        return typeof this._linkDistance === "function" ? +(this._linkDistance(link)) : this._linkDistance;
    };
    Layout.setLinkLength = function (link, length) {
        link.length = length;
    };
    Layout.prototype.getLinkType = function (link) {
        return typeof this._linkType === "function" ? this._linkType(link) : 0;
    };
    Layout.prototype.symmetricDiffLinkLengths = function (idealLength, w) {
        var _this = this;
        if (w === void 0) { w = 1; }
        this.linkDistance(function (l) { return idealLength * l.length; });
        this._linkLengthCalculator = function () { return linklengths_1.symmetricDiffLinkLengths(_this._links, _this.linkAccessor, w); };
        return this;
    };
    Layout.prototype.jaccardLinkLengths = function (idealLength, w) {
        var _this = this;
        if (w === void 0) { w = 1; }
        this.linkDistance(function (l) { return idealLength * l.length; });
        this._linkLengthCalculator = function () { return linklengths_1.jaccardLinkLengths(_this._links, _this.linkAccessor, w); };
        return this;
    };
    Layout.prototype.start = function (initialUnconstrainedIterations, initialUserConstraintIterations, initialAllConstraintsIterations, gridSnapIterations, keepRunning, centerGraph) {
        var _this = this;
        if (initialUnconstrainedIterations === void 0) { initialUnconstrainedIterations = 0; }
        if (initialUserConstraintIterations === void 0) { initialUserConstraintIterations = 0; }
        if (initialAllConstraintsIterations === void 0) { initialAllConstraintsIterations = 0; }
        if (gridSnapIterations === void 0) { gridSnapIterations = 0; }
        if (keepRunning === void 0) { keepRunning = true; }
        if (centerGraph === void 0) { centerGraph = true; }
        var i, j, n = this.nodes().length, N = n + 2 * this._groups.length, m = this._links.length, w = this._canvasSize[0], h = this._canvasSize[1];
        var x = new Array(N), y = new Array(N);
        var G = null;
        var ao = this._avoidOverlaps;
        this._nodes.forEach(function (v, i) {
            v.index = i;
            if (typeof v.x === 'undefined') {
                v.x = w / 2, v.y = h / 2;
            }
            x[i] = v.x, y[i] = v.y;
        });
        if (this._linkLengthCalculator)
            this._linkLengthCalculator();
        var distances;
        if (this._distanceMatrix) {
            distances = this._distanceMatrix;
        }
        else {
            distances = (new shortestpaths_1.Calculator(N, this._links, Layout.getSourceIndex, Layout.getTargetIndex, function (l) { return _this.getLinkLength(l); })).DistanceMatrix();
            G = descent_1.Descent.createSquareMatrix(N, function () { return 2; });
            this._links.forEach(function (l) {
                if (typeof l.source == "number")
                    l.source = _this._nodes[l.source];
                if (typeof l.target == "number")
                    l.target = _this._nodes[l.target];
            });
            this._links.forEach(function (e) {
                var u = Layout.getSourceIndex(e), v = Layout.getTargetIndex(e);
                G[u][v] = G[v][u] = e.weight || 1;
            });
        }
        var D = descent_1.Descent.createSquareMatrix(N, function (i, j) {
            return distances[i][j];
        });
        if (this._rootGroup && typeof this._rootGroup.groups !== 'undefined') {
            var i = n;
            var addAttraction = function (i, j, strength, idealDistance) {
                G[i][j] = G[j][i] = strength;
                D[i][j] = D[j][i] = idealDistance;
            };
            this._groups.forEach(function (g) {
                addAttraction(i, i + 1, _this._groupCompactness, 0.1);
                if (typeof g.bounds === 'undefined') {
                    x[i] = w / 2, y[i++] = h / 2;
                    x[i] = w / 2, y[i++] = h / 2;
                }
                else {
                    x[i] = g.bounds.x, y[i++] = g.bounds.y;
                    x[i] = g.bounds.X, y[i++] = g.bounds.Y;
                }
            });
        }
        else
            this._rootGroup = { leaves: this._nodes, groups: [] };
        var curConstraints = this._constraints || [];
        if (this._directedLinkConstraints) {
            this.linkAccessor.getMinSeparation = this._directedLinkConstraints.getMinSeparation;
            curConstraints = curConstraints.concat(linklengths_1.generateDirectedEdgeConstraints(n, this._links, this._directedLinkConstraints.axis, (this.linkAccessor)));
        }
        this.avoidOverlaps(false);
        this._descent = new descent_1.Descent([x, y], D);
        this._descent.locks.clear();
        for (var i = 0; i < n; ++i) {
            var o = this._nodes[i];
            if (o.fixed) {
                o.px = o.x;
                o.py = o.y;
                var p = [o.x, o.y];
                this._descent.locks.add(i, p);
            }
        }
        this._descent.threshold = this._threshold;
        this.initialLayout(initialUnconstrainedIterations, x, y);
        if (curConstraints.length > 0)
            this._descent.project = new rectangle_1.Projection(this._nodes, this._groups, this._rootGroup, curConstraints).projectFunctions();
        this._descent.run(initialUserConstraintIterations);
        this.separateOverlappingComponents(w, h, centerGraph);
        this.avoidOverlaps(ao);
        if (ao) {
            this._nodes.forEach(function (v, i) { v.x = x[i], v.y = y[i]; });
            this._descent.project = new rectangle_1.Projection(this._nodes, this._groups, this._rootGroup, curConstraints, true).projectFunctions();
            this._nodes.forEach(function (v, i) { x[i] = v.x, y[i] = v.y; });
        }
        this._descent.G = G;
        this._descent.run(initialAllConstraintsIterations);
        if (gridSnapIterations) {
            this._descent.snapStrength = 1000;
            this._descent.snapGridSize = this._nodes[0].width;
            this._descent.numGridSnapNodes = n;
            this._descent.scaleSnapByMaxH = n != N;
            var G0 = descent_1.Descent.createSquareMatrix(N, function (i, j) {
                if (i >= n || j >= n)
                    return G[i][j];
                return 0;
            });
            this._descent.G = G0;
            this._descent.run(gridSnapIterations);
        }
        this.updateNodePositions();
        this.separateOverlappingComponents(w, h, centerGraph);
        return keepRunning ? this.resume() : this;
    };
    Layout.prototype.initialLayout = function (iterations, x, y) {
        if (this._groups.length > 0 && iterations > 0) {
            var n = this._nodes.length;
            var edges = this._links.map(function (e) { return ({ source: e.source.index, target: e.target.index }); });
            var vs = this._nodes.map(function (v) { return ({ index: v.index }); });
            this._groups.forEach(function (g, i) {
                vs.push({ index: g.index = n + i });
            });
            this._groups.forEach(function (g, i) {
                if (typeof g.leaves !== 'undefined')
                    g.leaves.forEach(function (v) { return edges.push({ source: g.index, target: v.index }); });
                if (typeof g.groups !== 'undefined')
                    g.groups.forEach(function (gg) { return edges.push({ source: g.index, target: gg.index }); });
            });
            new Layout()
                .size(this.size())
                .nodes(vs)
                .links(edges)
                .avoidOverlaps(false)
                .linkDistance(this.linkDistance())
                .symmetricDiffLinkLengths(5)
                .convergenceThreshold(1e-4)
                .start(iterations, 0, 0, 0, false);
            this._nodes.forEach(function (v) {
                x[v.index] = vs[v.index].x;
                y[v.index] = vs[v.index].y;
            });
        }
        else {
            this._descent.run(iterations);
        }
    };
    Layout.prototype.separateOverlappingComponents = function (width, height, centerGraph) {
        var _this = this;
        if (centerGraph === void 0) { centerGraph = true; }
        if (!this._distanceMatrix && this._handleDisconnected) {
            var x_1 = this._descent.x[0], y_1 = this._descent.x[1];
            this._nodes.forEach(function (v, i) { v.x = x_1[i], v.y = y_1[i]; });
            var graphs = handledisconnected_1.separateGraphs(this._nodes, this._links);
            handledisconnected_1.applyPacking(graphs, width, height, this._defaultNodeSize, 1, centerGraph);
            this._nodes.forEach(function (v, i) {
                _this._descent.x[0][i] = v.x, _this._descent.x[1][i] = v.y;
                if (v.bounds) {
                    v.bounds.setXCentre(v.x);
                    v.bounds.setYCentre(v.y);
                }
            });
        }
    };
    Layout.prototype.resume = function () {
        return this.alpha(0.1);
    };
    Layout.prototype.stop = function () {
        return this.alpha(0);
    };
    Layout.prototype.prepareEdgeRouting = function (nodeMargin) {
        if (nodeMargin === void 0) { nodeMargin = 0; }
        this._visibilityGraph = new geom_1.TangentVisibilityGraph(this._nodes.map(function (v) {
            return v.bounds.inflate(-nodeMargin).vertices();
        }));
    };
    Layout.prototype.routeEdge = function (edge, ah, draw) {
        if (ah === void 0) { ah = 5; }
        var lineData = [];
        var vg2 = new geom_1.TangentVisibilityGraph(this._visibilityGraph.P, { V: this._visibilityGraph.V, E: this._visibilityGraph.E }), port1 = { x: edge.source.x, y: edge.source.y }, port2 = { x: edge.target.x, y: edge.target.y }, start = vg2.addPoint(port1, edge.source.index), end = vg2.addPoint(port2, edge.target.index);
        vg2.addEdgeIfVisible(port1, port2, edge.source.index, edge.target.index);
        if (typeof draw !== 'undefined') {
            draw(vg2);
        }
        var sourceInd = function (e) { return e.source.id; }, targetInd = function (e) { return e.target.id; }, length = function (e) { return e.length(); }, spCalc = new shortestpaths_1.Calculator(vg2.V.length, vg2.E, sourceInd, targetInd, length), shortestPath = spCalc.PathFromNodeToNode(start.id, end.id);
        if (shortestPath.length === 1 || shortestPath.length === vg2.V.length) {
            var route = rectangle_1.makeEdgeBetween(edge.source.innerBounds, edge.target.innerBounds, ah);
            lineData = [route.sourceIntersection, route.arrowStart];
        }
        else {
            var n = shortestPath.length - 2, p = vg2.V[shortestPath[n]].p, q = vg2.V[shortestPath[0]].p, lineData = [edge.source.innerBounds.rayIntersection(p.x, p.y)];
            for (var i = n; i >= 0; --i)
                lineData.push(vg2.V[shortestPath[i]].p);
            lineData.push(rectangle_1.makeEdgeTo(q, edge.target.innerBounds, ah));
        }
        return lineData;
    };
    Layout.getSourceIndex = function (e) {
        return typeof e.source === 'number' ? e.source : e.source.index;
    };
    Layout.getTargetIndex = function (e) {
        return typeof e.target === 'number' ? e.target : e.target.index;
    };
    Layout.linkId = function (e) {
        return Layout.getSourceIndex(e) + "-" + Layout.getTargetIndex(e);
    };
    Layout.dragStart = function (d) {
        if (isGroup(d)) {
            Layout.storeOffset(d, Layout.dragOrigin(d));
        }
        else {
            Layout.stopNode(d);
            d.fixed |= 2;
        }
    };
    Layout.stopNode = function (v) {
        v.px = v.x;
        v.py = v.y;
    };
    Layout.storeOffset = function (d, origin) {
        if (typeof d.leaves !== 'undefined') {
            d.leaves.forEach(function (v) {
                v.fixed |= 2;
                Layout.stopNode(v);
                v._dragGroupOffsetX = v.x - origin.x;
                v._dragGroupOffsetY = v.y - origin.y;
            });
        }
        if (typeof d.groups !== 'undefined') {
            d.groups.forEach(function (g) { return Layout.storeOffset(g, origin); });
        }
    };
    Layout.dragOrigin = function (d) {
        if (isGroup(d)) {
            return {
                x: d.bounds.cx(),
                y: d.bounds.cy()
            };
        }
        else {
            return d;
        }
    };
    Layout.drag = function (d, position) {
        if (isGroup(d)) {
            if (typeof d.leaves !== 'undefined') {
                d.leaves.forEach(function (v) {
                    d.bounds.setXCentre(position.x);
                    d.bounds.setYCentre(position.y);
                    v.px = v._dragGroupOffsetX + position.x;
                    v.py = v._dragGroupOffsetY + position.y;
                });
            }
            if (typeof d.groups !== 'undefined') {
                d.groups.forEach(function (g) { return Layout.drag(g, position); });
            }
        }
        else {
            d.px = position.x;
            d.py = position.y;
        }
    };
    Layout.dragEnd = function (d) {
        if (isGroup(d)) {
            if (typeof d.leaves !== 'undefined') {
                d.leaves.forEach(function (v) {
                    Layout.dragEnd(v);
                    delete v._dragGroupOffsetX;
                    delete v._dragGroupOffsetY;
                });
            }
            if (typeof d.groups !== 'undefined') {
                d.groups.forEach(Layout.dragEnd);
            }
        }
        else {
            d.fixed &= ~6;
        }
    };
    Layout.mouseOver = function (d) {
        d.fixed |= 4;
        d.px = d.x, d.py = d.y;
    };
    Layout.mouseOut = function (d) {
        d.fixed &= ~4;
    };
    return Layout;
}());
exports.Layout = Layout;
},{"./descent":7,"./geom":8,"./handledisconnected":10,"./linklengths":13,"./powergraph":14,"./rectangle":17,"./shortestpaths":18}],12:[function(require,module,exports){
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var shortestpaths_1 = require("./shortestpaths");
var descent_1 = require("./descent");
var rectangle_1 = require("./rectangle");
var linklengths_1 = require("./linklengths");
var Link3D = (function () {
    function Link3D(source, target) {
        this.source = source;
        this.target = target;
    }
    Link3D.prototype.actualLength = function (x) {
        var _this = this;
        return Math.sqrt(x.reduce(function (c, v) {
            var dx = v[_this.target] - v[_this.source];
            return c + dx * dx;
        }, 0));
    };
    return Link3D;
}());
exports.Link3D = Link3D;
var Node3D = (function () {
    function Node3D(x, y, z) {
        if (x === void 0) { x = 0; }
        if (y === void 0) { y = 0; }
        if (z === void 0) { z = 0; }
        this.x = x;
        this.y = y;
        this.z = z;
    }
    return Node3D;
}());
exports.Node3D = Node3D;
var Layout3D = (function () {
    function Layout3D(nodes, links, idealLinkLength) {
        var _this = this;
        if (idealLinkLength === void 0) { idealLinkLength = 1; }
        this.nodes = nodes;
        this.links = links;
        this.idealLinkLength = idealLinkLength;
        this.constraints = null;
        this.useJaccardLinkLengths = true;
        this.result = new Array(Layout3D.k);
        for (var i = 0; i < Layout3D.k; ++i) {
            this.result[i] = new Array(nodes.length);
        }
        nodes.forEach(function (v, i) {
            for (var _i = 0, _a = Layout3D.dims; _i < _a.length; _i++) {
                var dim = _a[_i];
                if (typeof v[dim] == 'undefined')
                    v[dim] = Math.random();
            }
            _this.result[0][i] = v.x;
            _this.result[1][i] = v.y;
            _this.result[2][i] = v.z;
        });
    }
    ;
    Layout3D.prototype.linkLength = function (l) {
        return l.actualLength(this.result);
    };
    Layout3D.prototype.start = function (iterations) {
        var _this = this;
        if (iterations === void 0) { iterations = 100; }
        var n = this.nodes.length;
        var linkAccessor = new LinkAccessor();
        if (this.useJaccardLinkLengths)
            linklengths_1.jaccardLinkLengths(this.links, linkAccessor, 1.5);
        this.links.forEach(function (e) { return e.length *= _this.idealLinkLength; });
        var distanceMatrix = (new shortestpaths_1.Calculator(n, this.links, function (e) { return e.source; }, function (e) { return e.target; }, function (e) { return e.length; })).DistanceMatrix();
        var D = descent_1.Descent.createSquareMatrix(n, function (i, j) { return distanceMatrix[i][j]; });
        var G = descent_1.Descent.createSquareMatrix(n, function () { return 2; });
        this.links.forEach(function (_a) {
            var source = _a.source, target = _a.target;
            return G[source][target] = G[target][source] = 1;
        });
        this.descent = new descent_1.Descent(this.result, D);
        this.descent.threshold = 1e-3;
        this.descent.G = G;
        if (this.constraints)
            this.descent.project = new rectangle_1.Projection(this.nodes, null, null, this.constraints).projectFunctions();
        for (var i = 0; i < this.nodes.length; i++) {
            var v = this.nodes[i];
            if (v.fixed) {
                this.descent.locks.add(i, [v.x, v.y, v.z]);
            }
        }
        this.descent.run(iterations);
        return this;
    };
    Layout3D.prototype.tick = function () {
        this.descent.locks.clear();
        for (var i = 0; i < this.nodes.length; i++) {
            var v = this.nodes[i];
            if (v.fixed) {
                this.descent.locks.add(i, [v.x, v.y, v.z]);
            }
        }
        return this.descent.rungeKutta();
    };
    Layout3D.dims = ['x', 'y', 'z'];
    Layout3D.k = Layout3D.dims.length;
    return Layout3D;
}());
exports.Layout3D = Layout3D;
var LinkAccessor = (function () {
    function LinkAccessor() {
    }
    LinkAccessor.prototype.getSourceIndex = function (e) { return e.source; };
    LinkAccessor.prototype.getTargetIndex = function (e) { return e.target; };
    LinkAccessor.prototype.getLength = function (e) { return e.length; };
    LinkAccessor.prototype.setLength = function (e, l) { e.length = l; };
    return LinkAccessor;
}());
},{"./descent":7,"./linklengths":13,"./rectangle":17,"./shortestpaths":18}],13:[function(require,module,exports){
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
function unionCount(a, b) {
    var u = {};
    for (var i in a)
        u[i] = {};
    for (var i in b)
        u[i] = {};
    return Object.keys(u).length;
}
function intersectionCount(a, b) {
    var n = 0;
    for (var i in a)
        if (typeof b[i] !== 'undefined')
            ++n;
    return n;
}
function getNeighbours(links, la) {
    var neighbours = {};
    var addNeighbours = function (u, v) {
        if (typeof neighbours[u] === 'undefined')
            neighbours[u] = {};
        neighbours[u][v] = {};
    };
    links.forEach(function (e) {
        var u = la.getSourceIndex(e), v = la.getTargetIndex(e);
        addNeighbours(u, v);
        addNeighbours(v, u);
    });
    return neighbours;
}
function computeLinkLengths(links, w, f, la) {
    var neighbours = getNeighbours(links, la);
    links.forEach(function (l) {
        var a = neighbours[la.getSourceIndex(l)];
        var b = neighbours[la.getTargetIndex(l)];
        la.setLength(l, 1 + w * f(a, b));
    });
}
function symmetricDiffLinkLengths(links, la, w) {
    if (w === void 0) { w = 1; }
    computeLinkLengths(links, w, function (a, b) { return Math.sqrt(unionCount(a, b) - intersectionCount(a, b)); }, la);
}
exports.symmetricDiffLinkLengths = symmetricDiffLinkLengths;
function jaccardLinkLengths(links, la, w) {
    if (w === void 0) { w = 1; }
    computeLinkLengths(links, w, function (a, b) {
        return Math.min(Object.keys(a).length, Object.keys(b).length) < 1.1 ? 0 : intersectionCount(a, b) / unionCount(a, b);
    }, la);
}
exports.jaccardLinkLengths = jaccardLinkLengths;
function generateDirectedEdgeConstraints(n, links, axis, la) {
    var components = stronglyConnectedComponents(n, links, la);
    var nodes = {};
    components.forEach(function (c, i) {
        return c.forEach(function (v) { return nodes[v] = i; });
    });
    var constraints = [];
    links.forEach(function (l) {
        var ui = la.getSourceIndex(l), vi = la.getTargetIndex(l), u = nodes[ui], v = nodes[vi];
        if (u !== v) {
            constraints.push({
                axis: axis,
                left: ui,
                right: vi,
                gap: la.getMinSeparation(l)
            });
        }
    });
    return constraints;
}
exports.generateDirectedEdgeConstraints = generateDirectedEdgeConstraints;
function stronglyConnectedComponents(numVertices, edges, la) {
    var nodes = [];
    var index = 0;
    var stack = [];
    var components = [];
    function strongConnect(v) {
        v.index = v.lowlink = index++;
        stack.push(v);
        v.onStack = true;
        for (var _i = 0, _a = v.out; _i < _a.length; _i++) {
            var w = _a[_i];
            if (typeof w.index === 'undefined') {
                strongConnect(w);
                v.lowlink = Math.min(v.lowlink, w.lowlink);
            }
            else if (w.onStack) {
                v.lowlink = Math.min(v.lowlink, w.index);
            }
        }
        if (v.lowlink === v.index) {
            var component = [];
            while (stack.length) {
                w = stack.pop();
                w.onStack = false;
                component.push(w);
                if (w === v)
                    break;
            }
            components.push(component.map(function (v) { return v.id; }));
        }
    }
    for (var i = 0; i < numVertices; i++) {
        nodes.push({ id: i, out: [] });
    }
    for (var _i = 0, edges_1 = edges; _i < edges_1.length; _i++) {
        var e = edges_1[_i];
        var v_1 = nodes[la.getSourceIndex(e)], w = nodes[la.getTargetIndex(e)];
        v_1.out.push(w);
    }
    for (var _a = 0, nodes_1 = nodes; _a < nodes_1.length; _a++) {
        var v = nodes_1[_a];
        if (typeof v.index === 'undefined')
            strongConnect(v);
    }
    return components;
}
exports.stronglyConnectedComponents = stronglyConnectedComponents;
},{}],14:[function(require,module,exports){
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var PowerEdge = (function () {
    function PowerEdge(source, target, type) {
        this.source = source;
        this.target = target;
        this.type = type;
    }
    return PowerEdge;
}());
exports.PowerEdge = PowerEdge;
var Configuration = (function () {
    function Configuration(n, edges, linkAccessor, rootGroup) {
        var _this = this;
        this.linkAccessor = linkAccessor;
        this.modules = new Array(n);
        this.roots = [];
        if (rootGroup) {
            this.initModulesFromGroup(rootGroup);
        }
        else {
            this.roots.push(new ModuleSet());
            for (var i = 0; i < n; ++i)
                this.roots[0].add(this.modules[i] = new Module(i));
        }
        this.R = edges.length;
        edges.forEach(function (e) {
            var s = _this.modules[linkAccessor.getSourceIndex(e)], t = _this.modules[linkAccessor.getTargetIndex(e)], type = linkAccessor.getType(e);
            s.outgoing.add(type, t);
            t.incoming.add(type, s);
        });
    }
    Configuration.prototype.initModulesFromGroup = function (group) {
        var moduleSet = new ModuleSet();
        this.roots.push(moduleSet);
        for (var i = 0; i < group.leaves.length; ++i) {
            var node = group.leaves[i];
            var module = new Module(node.id);
            this.modules[node.id] = module;
            moduleSet.add(module);
        }
        if (group.groups) {
            for (var j = 0; j < group.groups.length; ++j) {
                var child = group.groups[j];
                var definition = {};
                for (var prop in child)
                    if (prop !== "leaves" && prop !== "groups" && child.hasOwnProperty(prop))
                        definition[prop] = child[prop];
                moduleSet.add(new Module(-1 - j, new LinkSets(), new LinkSets(), this.initModulesFromGroup(child), definition));
            }
        }
        return moduleSet;
    };
    Configuration.prototype.merge = function (a, b, k) {
        if (k === void 0) { k = 0; }
        var inInt = a.incoming.intersection(b.incoming), outInt = a.outgoing.intersection(b.outgoing);
        var children = new ModuleSet();
        children.add(a);
        children.add(b);
        var m = new Module(this.modules.length, outInt, inInt, children);
        this.modules.push(m);
        var update = function (s, i, o) {
            s.forAll(function (ms, linktype) {
                ms.forAll(function (n) {
                    var nls = n[i];
                    nls.add(linktype, m);
                    nls.remove(linktype, a);
                    nls.remove(linktype, b);
                    a[o].remove(linktype, n);
                    b[o].remove(linktype, n);
                });
            });
        };
        update(outInt, "incoming", "outgoing");
        update(inInt, "outgoing", "incoming");
        this.R -= inInt.count() + outInt.count();
        this.roots[k].remove(a);
        this.roots[k].remove(b);
        this.roots[k].add(m);
        return m;
    };
    Configuration.prototype.rootMerges = function (k) {
        if (k === void 0) { k = 0; }
        var rs = this.roots[k].modules();
        var n = rs.length;
        var merges = new Array(n * (n - 1));
        var ctr = 0;
        for (var i = 0, i_ = n - 1; i < i_; ++i) {
            for (var j = i + 1; j < n; ++j) {
                var a = rs[i], b = rs[j];
                merges[ctr] = { id: ctr, nEdges: this.nEdges(a, b), a: a, b: b };
                ctr++;
            }
        }
        return merges;
    };
    Configuration.prototype.greedyMerge = function () {
        for (var i = 0; i < this.roots.length; ++i) {
            if (this.roots[i].modules().length < 2)
                continue;
            var ms = this.rootMerges(i).sort(function (a, b) { return a.nEdges == b.nEdges ? a.id - b.id : a.nEdges - b.nEdges; });
            var m = ms[0];
            if (m.nEdges >= this.R)
                continue;
            this.merge(m.a, m.b, i);
            return true;
        }
    };
    Configuration.prototype.nEdges = function (a, b) {
        var inInt = a.incoming.intersection(b.incoming), outInt = a.outgoing.intersection(b.outgoing);
        return this.R - inInt.count() - outInt.count();
    };
    Configuration.prototype.getGroupHierarchy = function (retargetedEdges) {
        var _this = this;
        var groups = [];
        var root = {};
        toGroups(this.roots[0], root, groups);
        var es = this.allEdges();
        es.forEach(function (e) {
            var a = _this.modules[e.source];
            var b = _this.modules[e.target];
            retargetedEdges.push(new PowerEdge(typeof a.gid === "undefined" ? e.source : groups[a.gid], typeof b.gid === "undefined" ? e.target : groups[b.gid], e.type));
        });
        return groups;
    };
    Configuration.prototype.allEdges = function () {
        var es = [];
        Configuration.getEdges(this.roots[0], es);
        return es;
    };
    Configuration.getEdges = function (modules, es) {
        modules.forAll(function (m) {
            m.getEdges(es);
            Configuration.getEdges(m.children, es);
        });
    };
    return Configuration;
}());
exports.Configuration = Configuration;
function toGroups(modules, group, groups) {
    modules.forAll(function (m) {
        if (m.isLeaf()) {
            if (!group.leaves)
                group.leaves = [];
            group.leaves.push(m.id);
        }
        else {
            var g = group;
            m.gid = groups.length;
            if (!m.isIsland() || m.isPredefined()) {
                g = { id: m.gid };
                if (m.isPredefined())
                    for (var prop in m.definition)
                        g[prop] = m.definition[prop];
                if (!group.groups)
                    group.groups = [];
                group.groups.push(m.gid);
                groups.push(g);
            }
            toGroups(m.children, g, groups);
        }
    });
}
var Module = (function () {
    function Module(id, outgoing, incoming, children, definition) {
        if (outgoing === void 0) { outgoing = new LinkSets(); }
        if (incoming === void 0) { incoming = new LinkSets(); }
        if (children === void 0) { children = new ModuleSet(); }
        this.id = id;
        this.outgoing = outgoing;
        this.incoming = incoming;
        this.children = children;
        this.definition = definition;
    }
    Module.prototype.getEdges = function (es) {
        var _this = this;
        this.outgoing.forAll(function (ms, edgetype) {
            ms.forAll(function (target) {
                es.push(new PowerEdge(_this.id, target.id, edgetype));
            });
        });
    };
    Module.prototype.isLeaf = function () {
        return this.children.count() === 0;
    };
    Module.prototype.isIsland = function () {
        return this.outgoing.count() === 0 && this.incoming.count() === 0;
    };
    Module.prototype.isPredefined = function () {
        return typeof this.definition !== "undefined";
    };
    return Module;
}());
exports.Module = Module;
function intersection(m, n) {
    var i = {};
    for (var v in m)
        if (v in n)
            i[v] = m[v];
    return i;
}
var ModuleSet = (function () {
    function ModuleSet() {
        this.table = {};
    }
    ModuleSet.prototype.count = function () {
        return Object.keys(this.table).length;
    };
    ModuleSet.prototype.intersection = function (other) {
        var result = new ModuleSet();
        result.table = intersection(this.table, other.table);
        return result;
    };
    ModuleSet.prototype.intersectionCount = function (other) {
        return this.intersection(other).count();
    };
    ModuleSet.prototype.contains = function (id) {
        return id in this.table;
    };
    ModuleSet.prototype.add = function (m) {
        this.table[m.id] = m;
    };
    ModuleSet.prototype.remove = function (m) {
        delete this.table[m.id];
    };
    ModuleSet.prototype.forAll = function (f) {
        for (var mid in this.table) {
            f(this.table[mid]);
        }
    };
    ModuleSet.prototype.modules = function () {
        var vs = [];
        this.forAll(function (m) {
            if (!m.isPredefined())
                vs.push(m);
        });
        return vs;
    };
    return ModuleSet;
}());
exports.ModuleSet = ModuleSet;
var LinkSets = (function () {
    function LinkSets() {
        this.sets = {};
        this.n = 0;
    }
    LinkSets.prototype.count = function () {
        return this.n;
    };
    LinkSets.prototype.contains = function (id) {
        var result = false;
        this.forAllModules(function (m) {
            if (!result && m.id == id) {
                result = true;
            }
        });
        return result;
    };
    LinkSets.prototype.add = function (linktype, m) {
        var s = linktype in this.sets ? this.sets[linktype] : this.sets[linktype] = new ModuleSet();
        s.add(m);
        ++this.n;
    };
    LinkSets.prototype.remove = function (linktype, m) {
        var ms = this.sets[linktype];
        ms.remove(m);
        if (ms.count() === 0) {
            delete this.sets[linktype];
        }
        --this.n;
    };
    LinkSets.prototype.forAll = function (f) {
        for (var linktype in this.sets) {
            f(this.sets[linktype], Number(linktype));
        }
    };
    LinkSets.prototype.forAllModules = function (f) {
        this.forAll(function (ms, lt) { return ms.forAll(f); });
    };
    LinkSets.prototype.intersection = function (other) {
        var result = new LinkSets();
        this.forAll(function (ms, lt) {
            if (lt in other.sets) {
                var i = ms.intersection(other.sets[lt]), n = i.count();
                if (n > 0) {
                    result.sets[lt] = i;
                    result.n += n;
                }
            }
        });
        return result;
    };
    return LinkSets;
}());
exports.LinkSets = LinkSets;
function intersectionCount(m, n) {
    return Object.keys(intersection(m, n)).length;
}
function getGroups(nodes, links, la, rootGroup) {
    var n = nodes.length, c = new Configuration(n, links, la, rootGroup);
    while (c.greedyMerge())
        ;
    var powerEdges = [];
    var g = c.getGroupHierarchy(powerEdges);
    powerEdges.forEach(function (e) {
        var f = function (end) {
            var g = e[end];
            if (typeof g == "number")
                e[end] = nodes[g];
        };
        f("source");
        f("target");
    });
    return { groups: g, powerEdges: powerEdges };
}
exports.getGroups = getGroups;
},{}],15:[function(require,module,exports){
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var PairingHeap = (function () {
    function PairingHeap(elem) {
        this.elem = elem;
        this.subheaps = [];
    }
    PairingHeap.prototype.toString = function (selector) {
        var str = "", needComma = false;
        for (var i = 0; i < this.subheaps.length; ++i) {
            var subheap = this.subheaps[i];
            if (!subheap.elem) {
                needComma = false;
                continue;
            }
            if (needComma) {
                str = str + ",";
            }
            str = str + subheap.toString(selector);
            needComma = true;
        }
        if (str !== "") {
            str = "(" + str + ")";
        }
        return (this.elem ? selector(this.elem) : "") + str;
    };
    PairingHeap.prototype.forEach = function (f) {
        if (!this.empty()) {
            f(this.elem, this);
            this.subheaps.forEach(function (s) { return s.forEach(f); });
        }
    };
    PairingHeap.prototype.count = function () {
        return this.empty() ? 0 : 1 + this.subheaps.reduce(function (n, h) {
            return n + h.count();
        }, 0);
    };
    PairingHeap.prototype.min = function () {
        return this.elem;
    };
    PairingHeap.prototype.empty = function () {
        return this.elem == null;
    };
    PairingHeap.prototype.contains = function (h) {
        if (this === h)
            return true;
        for (var i = 0; i < this.subheaps.length; i++) {
            if (this.subheaps[i].contains(h))
                return true;
        }
        return false;
    };
    PairingHeap.prototype.isHeap = function (lessThan) {
        var _this = this;
        return this.subheaps.every(function (h) { return lessThan(_this.elem, h.elem) && h.isHeap(lessThan); });
    };
    PairingHeap.prototype.insert = function (obj, lessThan) {
        return this.merge(new PairingHeap(obj), lessThan);
    };
    PairingHeap.prototype.merge = function (heap2, lessThan) {
        if (this.empty())
            return heap2;
        else if (heap2.empty())
            return this;
        else if (lessThan(this.elem, heap2.elem)) {
            this.subheaps.push(heap2);
            return this;
        }
        else {
            heap2.subheaps.push(this);
            return heap2;
        }
    };
    PairingHeap.prototype.removeMin = function (lessThan) {
        if (this.empty())
            return null;
        else
            return this.mergePairs(lessThan);
    };
    PairingHeap.prototype.mergePairs = function (lessThan) {
        if (this.subheaps.length == 0)
            return new PairingHeap(null);
        else if (this.subheaps.length == 1) {
            return this.subheaps[0];
        }
        else {
            var firstPair = this.subheaps.pop().merge(this.subheaps.pop(), lessThan);
            var remaining = this.mergePairs(lessThan);
            return firstPair.merge(remaining, lessThan);
        }
    };
    PairingHeap.prototype.decreaseKey = function (subheap, newValue, setHeapNode, lessThan) {
        var newHeap = subheap.removeMin(lessThan);
        subheap.elem = newHeap.elem;
        subheap.subheaps = newHeap.subheaps;
        if (setHeapNode !== null && newHeap.elem !== null) {
            setHeapNode(subheap.elem, subheap);
        }
        var pairingNode = new PairingHeap(newValue);
        if (setHeapNode !== null) {
            setHeapNode(newValue, pairingNode);
        }
        return this.merge(pairingNode, lessThan);
    };
    return PairingHeap;
}());
exports.PairingHeap = PairingHeap;
var PriorityQueue = (function () {
    function PriorityQueue(lessThan) {
        this.lessThan = lessThan;
    }
    PriorityQueue.prototype.top = function () {
        if (this.empty()) {
            return null;
        }
        return this.root.elem;
    };
    PriorityQueue.prototype.push = function () {
        var args = [];
        for (var _i = 0; _i < arguments.length; _i++) {
            args[_i] = arguments[_i];
        }
        var pairingNode;
        for (var i = 0, arg; arg = args[i]; ++i) {
            pairingNode = new PairingHeap(arg);
            this.root = this.empty() ?
                pairingNode : this.root.merge(pairingNode, this.lessThan);
        }
        return pairingNode;
    };
    PriorityQueue.prototype.empty = function () {
        return !this.root || !this.root.elem;
    };
    PriorityQueue.prototype.isHeap = function () {
        return this.root.isHeap(this.lessThan);
    };
    PriorityQueue.prototype.forEach = function (f) {
        this.root.forEach(f);
    };
    PriorityQueue.prototype.pop = function () {
        if (this.empty()) {
            return null;
        }
        var obj = this.root.min();
        this.root = this.root.removeMin(this.lessThan);
        return obj;
    };
    PriorityQueue.prototype.reduceKey = function (heapNode, newKey, setHeapNode) {
        if (setHeapNode === void 0) { setHeapNode = null; }
        this.root = this.root.decreaseKey(heapNode, newKey, setHeapNode, this.lessThan);
    };
    PriorityQueue.prototype.toString = function (selector) {
        return this.root.toString(selector);
    };
    PriorityQueue.prototype.count = function () {
        return this.root.count();
    };
    return PriorityQueue;
}());
exports.PriorityQueue = PriorityQueue;
},{}],16:[function(require,module,exports){
"use strict";
var __extends = (this && this.__extends) || (function () {
    var extendStatics = function (d, b) {
        extendStatics = Object.setPrototypeOf ||
            ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
            function (d, b) { for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p]; };
        return extendStatics(d, b);
    };
    return function (d, b) {
        extendStatics(d, b);
        function __() { this.constructor = d; }
        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
var TreeBase = (function () {
    function TreeBase() {
        this.findIter = function (data) {
            var res = this._root;
            var iter = this.iterator();
            while (res !== null) {
                var c = this._comparator(data, res.data);
                if (c === 0) {
                    iter._cursor = res;
                    return iter;
                }
                else {
                    iter._ancestors.push(res);
                    res = res.get_child(c > 0);
                }
            }
            return null;
        };
    }
    TreeBase.prototype.clear = function () {
        this._root = null;
        this.size = 0;
    };
    ;
    TreeBase.prototype.find = function (data) {
        var res = this._root;
        while (res !== null) {
            var c = this._comparator(data, res.data);
            if (c === 0) {
                return res.data;
            }
            else {
                res = res.get_child(c > 0);
            }
        }
        return null;
    };
    ;
    TreeBase.prototype.lowerBound = function (data) {
        return this._bound(data, this._comparator);
    };
    ;
    TreeBase.prototype.upperBound = function (data) {
        var cmp = this._comparator;
        function reverse_cmp(a, b) {
            return cmp(b, a);
        }
        return this._bound(data, reverse_cmp);
    };
    ;
    TreeBase.prototype.min = function () {
        var res = this._root;
        if (res === null) {
            return null;
        }
        while (res.left !== null) {
            res = res.left;
        }
        return res.data;
    };
    ;
    TreeBase.prototype.max = function () {
        var res = this._root;
        if (res === null) {
            return null;
        }
        while (res.right !== null) {
            res = res.right;
        }
        return res.data;
    };
    ;
    TreeBase.prototype.iterator = function () {
        return new Iterator(this);
    };
    ;
    TreeBase.prototype.each = function (cb) {
        var it = this.iterator(), data;
        while ((data = it.next()) !== null) {
            cb(data);
        }
    };
    ;
    TreeBase.prototype.reach = function (cb) {
        var it = this.iterator(), data;
        while ((data = it.prev()) !== null) {
            cb(data);
        }
    };
    ;
    TreeBase.prototype._bound = function (data, cmp) {
        var cur = this._root;
        var iter = this.iterator();
        while (cur !== null) {
            var c = this._comparator(data, cur.data);
            if (c === 0) {
                iter._cursor = cur;
                return iter;
            }
            iter._ancestors.push(cur);
            cur = cur.get_child(c > 0);
        }
        for (var i = iter._ancestors.length - 1; i >= 0; --i) {
            cur = iter._ancestors[i];
            if (cmp(data, cur.data) > 0) {
                iter._cursor = cur;
                iter._ancestors.length = i;
                return iter;
            }
        }
        iter._ancestors.length = 0;
        return iter;
    };
    ;
    return TreeBase;
}());
exports.TreeBase = TreeBase;
var Iterator = (function () {
    function Iterator(tree) {
        this._tree = tree;
        this._ancestors = [];
        this._cursor = null;
    }
    Iterator.prototype.data = function () {
        return this._cursor !== null ? this._cursor.data : null;
    };
    ;
    Iterator.prototype.next = function () {
        if (this._cursor === null) {
            var root = this._tree._root;
            if (root !== null) {
                this._minNode(root);
            }
        }
        else {
            if (this._cursor.right === null) {
                var save;
                do {
                    save = this._cursor;
                    if (this._ancestors.length) {
                        this._cursor = this._ancestors.pop();
                    }
                    else {
                        this._cursor = null;
                        break;
                    }
                } while (this._cursor.right === save);
            }
            else {
                this._ancestors.push(this._cursor);
                this._minNode(this._cursor.right);
            }
        }
        return this._cursor !== null ? this._cursor.data : null;
    };
    ;
    Iterator.prototype.prev = function () {
        if (this._cursor === null) {
            var root = this._tree._root;
            if (root !== null) {
                this._maxNode(root);
            }
        }
        else {
            if (this._cursor.left === null) {
                var save;
                do {
                    save = this._cursor;
                    if (this._ancestors.length) {
                        this._cursor = this._ancestors.pop();
                    }
                    else {
                        this._cursor = null;
                        break;
                    }
                } while (this._cursor.left === save);
            }
            else {
                this._ancestors.push(this._cursor);
                this._maxNode(this._cursor.left);
            }
        }
        return this._cursor !== null ? this._cursor.data : null;
    };
    ;
    Iterator.prototype._minNode = function (start) {
        while (start.left !== null) {
            this._ancestors.push(start);
            start = start.left;
        }
        this._cursor = start;
    };
    ;
    Iterator.prototype._maxNode = function (start) {
        while (start.right !== null) {
            this._ancestors.push(start);
            start = start.right;
        }
        this._cursor = start;
    };
    ;
    return Iterator;
}());
exports.Iterator = Iterator;
var Node = (function () {
    function Node(data) {
        this.data = data;
        this.left = null;
        this.right = null;
        this.red = true;
    }
    Node.prototype.get_child = function (dir) {
        return dir ? this.right : this.left;
    };
    ;
    Node.prototype.set_child = function (dir, val) {
        if (dir) {
            this.right = val;
        }
        else {
            this.left = val;
        }
    };
    ;
    return Node;
}());
var RBTree = (function (_super) {
    __extends(RBTree, _super);
    function RBTree(comparator) {
        var _this = _super.call(this) || this;
        _this._root = null;
        _this._comparator = comparator;
        _this.size = 0;
        return _this;
    }
    RBTree.prototype.insert = function (data) {
        var ret = false;
        if (this._root === null) {
            this._root = new Node(data);
            ret = true;
            this.size++;
        }
        else {
            var head = new Node(undefined);
            var dir = false;
            var last = false;
            var gp = null;
            var ggp = head;
            var p = null;
            var node = this._root;
            ggp.right = this._root;
            while (true) {
                if (node === null) {
                    node = new Node(data);
                    p.set_child(dir, node);
                    ret = true;
                    this.size++;
                }
                else if (RBTree.is_red(node.left) && RBTree.is_red(node.right)) {
                    node.red = true;
                    node.left.red = false;
                    node.right.red = false;
                }
                if (RBTree.is_red(node) && RBTree.is_red(p)) {
                    var dir2 = ggp.right === gp;
                    if (node === p.get_child(last)) {
                        ggp.set_child(dir2, RBTree.single_rotate(gp, !last));
                    }
                    else {
                        ggp.set_child(dir2, RBTree.double_rotate(gp, !last));
                    }
                }
                var cmp = this._comparator(node.data, data);
                if (cmp === 0) {
                    break;
                }
                last = dir;
                dir = cmp < 0;
                if (gp !== null) {
                    ggp = gp;
                }
                gp = p;
                p = node;
                node = node.get_child(dir);
            }
            this._root = head.right;
        }
        this._root.red = false;
        return ret;
    };
    ;
    RBTree.prototype.remove = function (data) {
        if (this._root === null) {
            return false;
        }
        var head = new Node(undefined);
        var node = head;
        node.right = this._root;
        var p = null;
        var gp = null;
        var found = null;
        var dir = true;
        while (node.get_child(dir) !== null) {
            var last = dir;
            gp = p;
            p = node;
            node = node.get_child(dir);
            var cmp = this._comparator(data, node.data);
            dir = cmp > 0;
            if (cmp === 0) {
                found = node;
            }
            if (!RBTree.is_red(node) && !RBTree.is_red(node.get_child(dir))) {
                if (RBTree.is_red(node.get_child(!dir))) {
                    var sr = RBTree.single_rotate(node, dir);
                    p.set_child(last, sr);
                    p = sr;
                }
                else if (!RBTree.is_red(node.get_child(!dir))) {
                    var sibling = p.get_child(!last);
                    if (sibling !== null) {
                        if (!RBTree.is_red(sibling.get_child(!last)) && !RBTree.is_red(sibling.get_child(last))) {
                            p.red = false;
                            sibling.red = true;
                            node.red = true;
                        }
                        else {
                            var dir2 = gp.right === p;
                            if (RBTree.is_red(sibling.get_child(last))) {
                                gp.set_child(dir2, RBTree.double_rotate(p, last));
                            }
                            else if (RBTree.is_red(sibling.get_child(!last))) {
                                gp.set_child(dir2, RBTree.single_rotate(p, last));
                            }
                            var gpc = gp.get_child(dir2);
                            gpc.red = true;
                            node.red = true;
                            gpc.left.red = false;
                            gpc.right.red = false;
                        }
                    }
                }
            }
        }
        if (found !== null) {
            found.data = node.data;
            p.set_child(p.right === node, node.get_child(node.left === null));
            this.size--;
        }
        this._root = head.right;
        if (this._root !== null) {
            this._root.red = false;
        }
        return found !== null;
    };
    ;
    RBTree.is_red = function (node) {
        return node !== null && node.red;
    };
    RBTree.single_rotate = function (root, dir) {
        var save = root.get_child(!dir);
        root.set_child(!dir, save.get_child(dir));
        save.set_child(dir, root);
        root.red = true;
        save.red = false;
        return save;
    };
    RBTree.double_rotate = function (root, dir) {
        root.set_child(!dir, RBTree.single_rotate(root.get_child(!dir), !dir));
        return RBTree.single_rotate(root, dir);
    };
    return RBTree;
}(TreeBase));
exports.RBTree = RBTree;
},{}],17:[function(require,module,exports){
"use strict";
var __extends = (this && this.__extends) || (function () {
    var extendStatics = function (d, b) {
        extendStatics = Object.setPrototypeOf ||
            ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
            function (d, b) { for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p]; };
        return extendStatics(d, b);
    };
    return function (d, b) {
        extendStatics(d, b);
        function __() { this.constructor = d; }
        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
var vpsc_1 = require("./vpsc");
var rbtree_1 = require("./rbtree");
function computeGroupBounds(g) {
    g.bounds = typeof g.leaves !== "undefined" ?
        g.leaves.reduce(function (r, c) { return c.bounds.union(r); }, Rectangle.empty()) :
        Rectangle.empty();
    if (typeof g.groups !== "undefined")
        g.bounds = g.groups.reduce(function (r, c) { return computeGroupBounds(c).union(r); }, g.bounds);
    g.bounds = g.bounds.inflate(g.padding);
    return g.bounds;
}
exports.computeGroupBounds = computeGroupBounds;
var Rectangle = (function () {
    function Rectangle(x, X, y, Y) {
        this.x = x;
        this.X = X;
        this.y = y;
        this.Y = Y;
    }
    Rectangle.empty = function () { return new Rectangle(Number.POSITIVE_INFINITY, Number.NEGATIVE_INFINITY, Number.POSITIVE_INFINITY, Number.NEGATIVE_INFINITY); };
    Rectangle.prototype.cx = function () { return (this.x + this.X) / 2; };
    Rectangle.prototype.cy = function () { return (this.y + this.Y) / 2; };
    Rectangle.prototype.overlapX = function (r) {
        var ux = this.cx(), vx = r.cx();
        if (ux <= vx && r.x < this.X)
            return this.X - r.x;
        if (vx <= ux && this.x < r.X)
            return r.X - this.x;
        return 0;
    };
    Rectangle.prototype.overlapY = function (r) {
        var uy = this.cy(), vy = r.cy();
        if (uy <= vy && r.y < this.Y)
            return this.Y - r.y;
        if (vy <= uy && this.y < r.Y)
            return r.Y - this.y;
        return 0;
    };
    Rectangle.prototype.setXCentre = function (cx) {
        var dx = cx - this.cx();
        this.x += dx;
        this.X += dx;
    };
    Rectangle.prototype.setYCentre = function (cy) {
        var dy = cy - this.cy();
        this.y += dy;
        this.Y += dy;
    };
    Rectangle.prototype.width = function () {
        return this.X - this.x;
    };
    Rectangle.prototype.height = function () {
        return this.Y - this.y;
    };
    Rectangle.prototype.union = function (r) {
        return new Rectangle(Math.min(this.x, r.x), Math.max(this.X, r.X), Math.min(this.y, r.y), Math.max(this.Y, r.Y));
    };
    Rectangle.prototype.lineIntersections = function (x1, y1, x2, y2) {
        var sides = [[this.x, this.y, this.X, this.y],
            [this.X, this.y, this.X, this.Y],
            [this.X, this.Y, this.x, this.Y],
            [this.x, this.Y, this.x, this.y]];
        var intersections = [];
        for (var i = 0; i < 4; ++i) {
            var r = Rectangle.lineIntersection(x1, y1, x2, y2, sides[i][0], sides[i][1], sides[i][2], sides[i][3]);
            if (r !== null)
                intersections.push({ x: r.x, y: r.y });
        }
        return intersections;
    };
    Rectangle.prototype.rayIntersection = function (x2, y2) {
        var ints = this.lineIntersections(this.cx(), this.cy(), x2, y2);
        return ints.length > 0 ? ints[0] : null;
    };
    Rectangle.prototype.vertices = function () {
        return [
            { x: this.x, y: this.y },
            { x: this.X, y: this.y },
            { x: this.X, y: this.Y },
            { x: this.x, y: this.Y }
        ];
    };
    Rectangle.lineIntersection = function (x1, y1, x2, y2, x3, y3, x4, y4) {
        var dx12 = x2 - x1, dx34 = x4 - x3, dy12 = y2 - y1, dy34 = y4 - y3, denominator = dy34 * dx12 - dx34 * dy12;
        if (denominator == 0)
            return null;
        var dx31 = x1 - x3, dy31 = y1 - y3, numa = dx34 * dy31 - dy34 * dx31, a = numa / denominator, numb = dx12 * dy31 - dy12 * dx31, b = numb / denominator;
        if (a >= 0 && a <= 1 && b >= 0 && b <= 1) {
            return {
                x: x1 + a * dx12,
                y: y1 + a * dy12
            };
        }
        return null;
    };
    Rectangle.prototype.inflate = function (pad) {
        return new Rectangle(this.x - pad, this.X + pad, this.y - pad, this.Y + pad);
    };
    return Rectangle;
}());
exports.Rectangle = Rectangle;
function makeEdgeBetween(source, target, ah) {
    var si = source.rayIntersection(target.cx(), target.cy()) || { x: source.cx(), y: source.cy() }, ti = target.rayIntersection(source.cx(), source.cy()) || { x: target.cx(), y: target.cy() }, dx = ti.x - si.x, dy = ti.y - si.y, l = Math.sqrt(dx * dx + dy * dy), al = l - ah;
    return {
        sourceIntersection: si,
        targetIntersection: ti,
        arrowStart: { x: si.x + al * dx / l, y: si.y + al * dy / l }
    };
}
exports.makeEdgeBetween = makeEdgeBetween;
function makeEdgeTo(s, target, ah) {
    var ti = target.rayIntersection(s.x, s.y);
    if (!ti)
        ti = { x: target.cx(), y: target.cy() };
    var dx = ti.x - s.x, dy = ti.y - s.y, l = Math.sqrt(dx * dx + dy * dy);
    return { x: ti.x - ah * dx / l, y: ti.y - ah * dy / l };
}
exports.makeEdgeTo = makeEdgeTo;
var Node = (function () {
    function Node(v, r, pos) {
        this.v = v;
        this.r = r;
        this.pos = pos;
        this.prev = makeRBTree();
        this.next = makeRBTree();
    }
    return Node;
}());
var Event = (function () {
    function Event(isOpen, v, pos) {
        this.isOpen = isOpen;
        this.v = v;
        this.pos = pos;
    }
    return Event;
}());
function compareEvents(a, b) {
    if (a.pos > b.pos) {
        return 1;
    }
    if (a.pos < b.pos) {
        return -1;
    }
    if (a.isOpen) {
        return -1;
    }
    if (b.isOpen) {
        return 1;
    }
    return 0;
}
function makeRBTree() {
    return new rbtree_1.RBTree(function (a, b) { return a.pos - b.pos; });
}
var xRect = {
    getCentre: function (r) { return r.cx(); },
    getOpen: function (r) { return r.y; },
    getClose: function (r) { return r.Y; },
    getSize: function (r) { return r.width(); },
    makeRect: function (open, close, center, size) { return new Rectangle(center - size / 2, center + size / 2, open, close); },
    findNeighbours: findXNeighbours
};
var yRect = {
    getCentre: function (r) { return r.cy(); },
    getOpen: function (r) { return r.x; },
    getClose: function (r) { return r.X; },
    getSize: function (r) { return r.height(); },
    makeRect: function (open, close, center, size) { return new Rectangle(open, close, center - size / 2, center + size / 2); },
    findNeighbours: findYNeighbours
};
function generateGroupConstraints(root, f, minSep, isContained) {
    if (isContained === void 0) { isContained = false; }
    var padding = root.padding, gn = typeof root.groups !== 'undefined' ? root.groups.length : 0, ln = typeof root.leaves !== 'undefined' ? root.leaves.length : 0, childConstraints = !gn ? []
        : root.groups.reduce(function (ccs, g) { return ccs.concat(generateGroupConstraints(g, f, minSep, true)); }, []), n = (isContained ? 2 : 0) + ln + gn, vs = new Array(n), rs = new Array(n), i = 0, add = function (r, v) { rs[i] = r; vs[i++] = v; };
    if (isContained) {
        var b = root.bounds, c = f.getCentre(b), s = f.getSize(b) / 2, open = f.getOpen(b), close = f.getClose(b), min = c - s + padding / 2, max = c + s - padding / 2;
        root.minVar.desiredPosition = min;
        add(f.makeRect(open, close, min, padding), root.minVar);
        root.maxVar.desiredPosition = max;
        add(f.makeRect(open, close, max, padding), root.maxVar);
    }
    if (ln)
        root.leaves.forEach(function (l) { return add(l.bounds, l.variable); });
    if (gn)
        root.groups.forEach(function (g) {
            var b = g.bounds;
            add(f.makeRect(f.getOpen(b), f.getClose(b), f.getCentre(b), f.getSize(b)), g.minVar);
        });
    var cs = generateConstraints(rs, vs, f, minSep);
    if (gn) {
        vs.forEach(function (v) { v.cOut = [], v.cIn = []; });
        cs.forEach(function (c) { c.left.cOut.push(c), c.right.cIn.push(c); });
        root.groups.forEach(function (g) {
            var gapAdjustment = (g.padding - f.getSize(g.bounds)) / 2;
            g.minVar.cIn.forEach(function (c) { return c.gap += gapAdjustment; });
            g.minVar.cOut.forEach(function (c) { c.left = g.maxVar; c.gap += gapAdjustment; });
        });
    }
    return childConstraints.concat(cs);
}
function generateConstraints(rs, vars, rect, minSep) {
    var i, n = rs.length;
    var N = 2 * n;
    console.assert(vars.length >= n);
    var events = new Array(N);
    for (i = 0; i < n; ++i) {
        var r = rs[i];
        var v = new Node(vars[i], r, rect.getCentre(r));
        events[i] = new Event(true, v, rect.getOpen(r));
        events[i + n] = new Event(false, v, rect.getClose(r));
    }
    events.sort(compareEvents);
    var cs = new Array();
    var scanline = makeRBTree();
    for (i = 0; i < N; ++i) {
        var e = events[i];
        var v = e.v;
        if (e.isOpen) {
            scanline.insert(v);
            rect.findNeighbours(v, scanline);
        }
        else {
            scanline.remove(v);
            var makeConstraint = function (l, r) {
                var sep = (rect.getSize(l.r) + rect.getSize(r.r)) / 2 + minSep;
                cs.push(new vpsc_1.Constraint(l.v, r.v, sep));
            };
            var visitNeighbours = function (forward, reverse, mkcon) {
                var u, it = v[forward].iterator();
                while ((u = it[forward]()) !== null) {
                    mkcon(u, v);
                    u[reverse].remove(v);
                }
            };
            visitNeighbours("prev", "next", function (u, v) { return makeConstraint(u, v); });
            visitNeighbours("next", "prev", function (u, v) { return makeConstraint(v, u); });
        }
    }
    console.assert(scanline.size === 0);
    return cs;
}
function findXNeighbours(v, scanline) {
    var f = function (forward, reverse) {
        var it = scanline.findIter(v);
        var u;
        while ((u = it[forward]()) !== null) {
            var uovervX = u.r.overlapX(v.r);
            if (uovervX <= 0 || uovervX <= u.r.overlapY(v.r)) {
                v[forward].insert(u);
                u[reverse].insert(v);
            }
            if (uovervX <= 0) {
                break;
            }
        }
    };
    f("next", "prev");
    f("prev", "next");
}
function findYNeighbours(v, scanline) {
    var f = function (forward, reverse) {
        var u = scanline.findIter(v)[forward]();
        if (u !== null && u.r.overlapX(v.r) > 0) {
            v[forward].insert(u);
            u[reverse].insert(v);
        }
    };
    f("next", "prev");
    f("prev", "next");
}
function generateXConstraints(rs, vars) {
    return generateConstraints(rs, vars, xRect, 1e-6);
}
exports.generateXConstraints = generateXConstraints;
function generateYConstraints(rs, vars) {
    return generateConstraints(rs, vars, yRect, 1e-6);
}
exports.generateYConstraints = generateYConstraints;
function generateXGroupConstraints(root) {
    return generateGroupConstraints(root, xRect, 1e-6);
}
exports.generateXGroupConstraints = generateXGroupConstraints;
function generateYGroupConstraints(root) {
    return generateGroupConstraints(root, yRect, 1e-6);
}
exports.generateYGroupConstraints = generateYGroupConstraints;
function removeOverlaps(rs) {
    var vs = rs.map(function (r) { return new vpsc_1.Variable(r.cx()); });
    var cs = generateXConstraints(rs, vs);
    var solver = new vpsc_1.Solver(vs, cs);
    solver.solve();
    vs.forEach(function (v, i) { return rs[i].setXCentre(v.position()); });
    vs = rs.map(function (r) { return new vpsc_1.Variable(r.cy()); });
    cs = generateYConstraints(rs, vs);
    solver = new vpsc_1.Solver(vs, cs);
    solver.solve();
    vs.forEach(function (v, i) { return rs[i].setYCentre(v.position()); });
}
exports.removeOverlaps = removeOverlaps;
var IndexedVariable = (function (_super) {
    __extends(IndexedVariable, _super);
    function IndexedVariable(index, w) {
        var _this = _super.call(this, 0, w) || this;
        _this.index = index;
        return _this;
    }
    return IndexedVariable;
}(vpsc_1.Variable));
exports.IndexedVariable = IndexedVariable;
var Projection = (function () {
    function Projection(nodes, groups, rootGroup, constraints, avoidOverlaps) {
        var _this = this;
        if (rootGroup === void 0) { rootGroup = null; }
        if (constraints === void 0) { constraints = null; }
        if (avoidOverlaps === void 0) { avoidOverlaps = false; }
        this.nodes = nodes;
        this.groups = groups;
        this.rootGroup = rootGroup;
        this.avoidOverlaps = avoidOverlaps;
        this.variables = nodes.map(function (v, i) {
            return v.variable = new IndexedVariable(i, 1);
        });
        if (constraints)
            this.createConstraints(constraints);
        if (avoidOverlaps && rootGroup && typeof rootGroup.groups !== 'undefined') {
            nodes.forEach(function (v) {
                if (!v.width || !v.height) {
                    v.bounds = new Rectangle(v.x, v.x, v.y, v.y);
                    return;
                }
                var w2 = v.width / 2, h2 = v.height / 2;
                v.bounds = new Rectangle(v.x - w2, v.x + w2, v.y - h2, v.y + h2);
            });
            computeGroupBounds(rootGroup);
            var i = nodes.length;
            groups.forEach(function (g) {
                _this.variables[i] = g.minVar = new IndexedVariable(i++, typeof g.stiffness !== "undefined" ? g.stiffness : 0.01);
                _this.variables[i] = g.maxVar = new IndexedVariable(i++, typeof g.stiffness !== "undefined" ? g.stiffness : 0.01);
            });
        }
    }
    Projection.prototype.createSeparation = function (c) {
        return new vpsc_1.Constraint(this.nodes[c.left].variable, this.nodes[c.right].variable, c.gap, typeof c.equality !== "undefined" ? c.equality : false);
    };
    Projection.prototype.makeFeasible = function (c) {
        var _this = this;
        if (!this.avoidOverlaps)
            return;
        var axis = 'x', dim = 'width';
        if (c.axis === 'x')
            axis = 'y', dim = 'height';
        var vs = c.offsets.map(function (o) { return _this.nodes[o.node]; }).sort(function (a, b) { return a[axis] - b[axis]; });
        var p = null;
        vs.forEach(function (v) {
            if (p) {
                var nextPos = p[axis] + p[dim];
                if (nextPos > v[axis]) {
                    v[axis] = nextPos;
                }
            }
            p = v;
        });
    };
    Projection.prototype.createAlignment = function (c) {
        var _this = this;
        var u = this.nodes[c.offsets[0].node].variable;
        this.makeFeasible(c);
        var cs = c.axis === 'x' ? this.xConstraints : this.yConstraints;
        c.offsets.slice(1).forEach(function (o) {
            var v = _this.nodes[o.node].variable;
            cs.push(new vpsc_1.Constraint(u, v, o.offset, true));
        });
    };
    Projection.prototype.createConstraints = function (constraints) {
        var _this = this;
        var isSep = function (c) { return typeof c.type === 'undefined' || c.type === 'separation'; };
        this.xConstraints = constraints
            .filter(function (c) { return c.axis === "x" && isSep(c); })
            .map(function (c) { return _this.createSeparation(c); });
        this.yConstraints = constraints
            .filter(function (c) { return c.axis === "y" && isSep(c); })
            .map(function (c) { return _this.createSeparation(c); });
        constraints
            .filter(function (c) { return c.type === 'alignment'; })
            .forEach(function (c) { return _this.createAlignment(c); });
    };
    Projection.prototype.setupVariablesAndBounds = function (x0, y0, desired, getDesired) {
        this.nodes.forEach(function (v, i) {
            if (v.fixed) {
                v.variable.weight = v.fixedWeight ? v.fixedWeight : 1000;
                desired[i] = getDesired(v);
            }
            else {
                v.variable.weight = 1;
            }
            var w = (v.width || 0) / 2, h = (v.height || 0) / 2;
            var ix = x0[i], iy = y0[i];
            v.bounds = new Rectangle(ix - w, ix + w, iy - h, iy + h);
        });
    };
    Projection.prototype.xProject = function (x0, y0, x) {
        if (!this.rootGroup && !(this.avoidOverlaps || this.xConstraints))
            return;
        this.project(x0, y0, x0, x, function (v) { return v.px; }, this.xConstraints, generateXGroupConstraints, function (v) { return v.bounds.setXCentre(x[v.variable.index] = v.variable.position()); }, function (g) {
            var xmin = x[g.minVar.index] = g.minVar.position();
            var xmax = x[g.maxVar.index] = g.maxVar.position();
            var p2 = g.padding / 2;
            g.bounds.x = xmin - p2;
            g.bounds.X = xmax + p2;
        });
    };
    Projection.prototype.yProject = function (x0, y0, y) {
        if (!this.rootGroup && !this.yConstraints)
            return;
        this.project(x0, y0, y0, y, function (v) { return v.py; }, this.yConstraints, generateYGroupConstraints, function (v) { return v.bounds.setYCentre(y[v.variable.index] = v.variable.position()); }, function (g) {
            var ymin = y[g.minVar.index] = g.minVar.position();
            var ymax = y[g.maxVar.index] = g.maxVar.position();
            var p2 = g.padding / 2;
            g.bounds.y = ymin - p2;
            ;
            g.bounds.Y = ymax + p2;
        });
    };
    Projection.prototype.projectFunctions = function () {
        var _this = this;
        return [
            function (x0, y0, x) { return _this.xProject(x0, y0, x); },
            function (x0, y0, y) { return _this.yProject(x0, y0, y); }
        ];
    };
    Projection.prototype.project = function (x0, y0, start, desired, getDesired, cs, generateConstraints, updateNodeBounds, updateGroupBounds) {
        this.setupVariablesAndBounds(x0, y0, desired, getDesired);
        if (this.rootGroup && this.avoidOverlaps) {
            computeGroupBounds(this.rootGroup);
            cs = cs.concat(generateConstraints(this.rootGroup));
        }
        this.solve(this.variables, cs, start, desired);
        this.nodes.forEach(updateNodeBounds);
        if (this.rootGroup && this.avoidOverlaps) {
            this.groups.forEach(updateGroupBounds);
            computeGroupBounds(this.rootGroup);
        }
    };
    Projection.prototype.solve = function (vs, cs, starting, desired) {
        var solver = new vpsc_1.Solver(vs, cs);
        solver.setStartingPositions(starting);
        solver.setDesiredPositions(desired);
        solver.solve();
    };
    return Projection;
}());
exports.Projection = Projection;
},{"./rbtree":16,"./vpsc":19}],18:[function(require,module,exports){
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var pqueue_1 = require("./pqueue");
var Neighbour = (function () {
    function Neighbour(id, distance) {
        this.id = id;
        this.distance = distance;
    }
    return Neighbour;
}());
var Node = (function () {
    function Node(id) {
        this.id = id;
        this.neighbours = [];
    }
    return Node;
}());
var QueueEntry = (function () {
    function QueueEntry(node, prev, d) {
        this.node = node;
        this.prev = prev;
        this.d = d;
    }
    return QueueEntry;
}());
var Calculator = (function () {
    function Calculator(n, es, getSourceIndex, getTargetIndex, getLength) {
        this.n = n;
        this.es = es;
        this.neighbours = new Array(this.n);
        var i = this.n;
        while (i--)
            this.neighbours[i] = new Node(i);
        i = this.es.length;
        while (i--) {
            var e = this.es[i];
            var u = getSourceIndex(e), v = getTargetIndex(e);
            var d = getLength(e);
            this.neighbours[u].neighbours.push(new Neighbour(v, d));
            this.neighbours[v].neighbours.push(new Neighbour(u, d));
        }
    }
    Calculator.prototype.DistanceMatrix = function () {
        var D = new Array(this.n);
        for (var i = 0; i < this.n; ++i) {
            D[i] = this.dijkstraNeighbours(i);
        }
        return D;
    };
    Calculator.prototype.DistancesFromNode = function (start) {
        return this.dijkstraNeighbours(start);
    };
    Calculator.prototype.PathFromNodeToNode = function (start, end) {
        return this.dijkstraNeighbours(start, end);
    };
    Calculator.prototype.PathFromNodeToNodeWithPrevCost = function (start, end, prevCost) {
        var q = new pqueue_1.PriorityQueue(function (a, b) { return a.d <= b.d; }), u = this.neighbours[start], qu = new QueueEntry(u, null, 0), visitedFrom = {};
        q.push(qu);
        while (!q.empty()) {
            qu = q.pop();
            u = qu.node;
            if (u.id === end) {
                break;
            }
            var i = u.neighbours.length;
            while (i--) {
                var neighbour = u.neighbours[i], v = this.neighbours[neighbour.id];
                if (qu.prev && v.id === qu.prev.node.id)
                    continue;
                var viduid = v.id + ',' + u.id;
                if (viduid in visitedFrom && visitedFrom[viduid] <= qu.d)
                    continue;
                var cc = qu.prev ? prevCost(qu.prev.node.id, u.id, v.id) : 0, t = qu.d + neighbour.distance + cc;
                visitedFrom[viduid] = t;
                q.push(new QueueEntry(v, qu, t));
            }
        }
        var path = [];
        while (qu.prev) {
            qu = qu.prev;
            path.push(qu.node.id);
        }
        return path;
    };
    Calculator.prototype.dijkstraNeighbours = function (start, dest) {
        if (dest === void 0) { dest = -1; }
        var q = new pqueue_1.PriorityQueue(function (a, b) { return a.d <= b.d; }), i = this.neighbours.length, d = new Array(i);
        while (i--) {
            var node = this.neighbours[i];
            node.d = i === start ? 0 : Number.POSITIVE_INFINITY;
            node.q = q.push(node);
        }
        while (!q.empty()) {
            var u = q.pop();
            d[u.id] = u.d;
            if (u.id === dest) {
                var path = [];
                var v = u;
                while (typeof v.prev !== 'undefined') {
                    path.push(v.prev.id);
                    v = v.prev;
                }
                return path;
            }
            i = u.neighbours.length;
            while (i--) {
                var neighbour = u.neighbours[i];
                var v = this.neighbours[neighbour.id];
                var t = u.d + neighbour.distance;
                if (u.d !== Number.MAX_VALUE && v.d > t) {
                    v.d = t;
                    v.prev = u;
                    q.reduceKey(v.q, v, function (e, q) { return e.q = q; });
                }
            }
        }
        return d;
    };
    return Calculator;
}());
exports.Calculator = Calculator;
},{"./pqueue":15}],19:[function(require,module,exports){
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var PositionStats = (function () {
    function PositionStats(scale) {
        this.scale = scale;
        this.AB = 0;
        this.AD = 0;
        this.A2 = 0;
    }
    PositionStats.prototype.addVariable = function (v) {
        var ai = this.scale / v.scale;
        var bi = v.offset / v.scale;
        var wi = v.weight;
        this.AB += wi * ai * bi;
        this.AD += wi * ai * v.desiredPosition;
        this.A2 += wi * ai * ai;
    };
    PositionStats.prototype.getPosn = function () {
        return (this.AD - this.AB) / this.A2;
    };
    return PositionStats;
}());
exports.PositionStats = PositionStats;
var Constraint = (function () {
    function Constraint(left, right, gap, equality) {
        if (equality === void 0) { equality = false; }
        this.left = left;
        this.right = right;
        this.gap = gap;
        this.equality = equality;
        this.active = false;
        this.unsatisfiable = false;
        this.left = left;
        this.right = right;
        this.gap = gap;
        this.equality = equality;
    }
    Constraint.prototype.slack = function () {
        return this.unsatisfiable ? Number.MAX_VALUE
            : this.right.scale * this.right.position() - this.gap
                - this.left.scale * this.left.position();
    };
    return Constraint;
}());
exports.Constraint = Constraint;
var Variable = (function () {
    function Variable(desiredPosition, weight, scale) {
        if (weight === void 0) { weight = 1; }
        if (scale === void 0) { scale = 1; }
        this.desiredPosition = desiredPosition;
        this.weight = weight;
        this.scale = scale;
        this.offset = 0;
    }
    Variable.prototype.dfdv = function () {
        return 2.0 * this.weight * (this.position() - this.desiredPosition);
    };
    Variable.prototype.position = function () {
        return (this.block.ps.scale * this.block.posn + this.offset) / this.scale;
    };
    Variable.prototype.visitNeighbours = function (prev, f) {
        var ff = function (c, next) { return c.active && prev !== next && f(c, next); };
        this.cOut.forEach(function (c) { return ff(c, c.right); });
        this.cIn.forEach(function (c) { return ff(c, c.left); });
    };
    return Variable;
}());
exports.Variable = Variable;
var Block = (function () {
    function Block(v) {
        this.vars = [];
        v.offset = 0;
        this.ps = new PositionStats(v.scale);
        this.addVariable(v);
    }
    Block.prototype.addVariable = function (v) {
        v.block = this;
        this.vars.push(v);
        this.ps.addVariable(v);
        this.posn = this.ps.getPosn();
    };
    Block.prototype.updateWeightedPosition = function () {
        this.ps.AB = this.ps.AD = this.ps.A2 = 0;
        for (var i = 0, n = this.vars.length; i < n; ++i)
            this.ps.addVariable(this.vars[i]);
        this.posn = this.ps.getPosn();
    };
    Block.prototype.compute_lm = function (v, u, postAction) {
        var _this = this;
        var dfdv = v.dfdv();
        v.visitNeighbours(u, function (c, next) {
            var _dfdv = _this.compute_lm(next, v, postAction);
            if (next === c.right) {
                dfdv += _dfdv * c.left.scale;
                c.lm = _dfdv;
            }
            else {
                dfdv += _dfdv * c.right.scale;
                c.lm = -_dfdv;
            }
            postAction(c);
        });
        return dfdv / v.scale;
    };
    Block.prototype.populateSplitBlock = function (v, prev) {
        var _this = this;
        v.visitNeighbours(prev, function (c, next) {
            next.offset = v.offset + (next === c.right ? c.gap : -c.gap);
            _this.addVariable(next);
            _this.populateSplitBlock(next, v);
        });
    };
    Block.prototype.traverse = function (visit, acc, v, prev) {
        var _this = this;
        if (v === void 0) { v = this.vars[0]; }
        if (prev === void 0) { prev = null; }
        v.visitNeighbours(prev, function (c, next) {
            acc.push(visit(c));
            _this.traverse(visit, acc, next, v);
        });
    };
    Block.prototype.findMinLM = function () {
        var m = null;
        this.compute_lm(this.vars[0], null, function (c) {
            if (!c.equality && (m === null || c.lm < m.lm))
                m = c;
        });
        return m;
    };
    Block.prototype.findMinLMBetween = function (lv, rv) {
        this.compute_lm(lv, null, function () { });
        var m = null;
        this.findPath(lv, null, rv, function (c, next) {
            if (!c.equality && c.right === next && (m === null || c.lm < m.lm))
                m = c;
        });
        return m;
    };
    Block.prototype.findPath = function (v, prev, to, visit) {
        var _this = this;
        var endFound = false;
        v.visitNeighbours(prev, function (c, next) {
            if (!endFound && (next === to || _this.findPath(next, v, to, visit))) {
                endFound = true;
                visit(c, next);
            }
        });
        return endFound;
    };
    Block.prototype.isActiveDirectedPathBetween = function (u, v) {
        if (u === v)
            return true;
        var i = u.cOut.length;
        while (i--) {
            var c = u.cOut[i];
            if (c.active && this.isActiveDirectedPathBetween(c.right, v))
                return true;
        }
        return false;
    };
    Block.split = function (c) {
        c.active = false;
        return [Block.createSplitBlock(c.left), Block.createSplitBlock(c.right)];
    };
    Block.createSplitBlock = function (startVar) {
        var b = new Block(startVar);
        b.populateSplitBlock(startVar, null);
        return b;
    };
    Block.prototype.splitBetween = function (vl, vr) {
        var c = this.findMinLMBetween(vl, vr);
        if (c !== null) {
            var bs = Block.split(c);
            return { constraint: c, lb: bs[0], rb: bs[1] };
        }
        return null;
    };
    Block.prototype.mergeAcross = function (b, c, dist) {
        c.active = true;
        for (var i = 0, n = b.vars.length; i < n; ++i) {
            var v = b.vars[i];
            v.offset += dist;
            this.addVariable(v);
        }
        this.posn = this.ps.getPosn();
    };
    Block.prototype.cost = function () {
        var sum = 0, i = this.vars.length;
        while (i--) {
            var v = this.vars[i], d = v.position() - v.desiredPosition;
            sum += d * d * v.weight;
        }
        return sum;
    };
    return Block;
}());
exports.Block = Block;
var Blocks = (function () {
    function Blocks(vs) {
        this.vs = vs;
        var n = vs.length;
        this.list = new Array(n);
        while (n--) {
            var b = new Block(vs[n]);
            this.list[n] = b;
            b.blockInd = n;
        }
    }
    Blocks.prototype.cost = function () {
        var sum = 0, i = this.list.length;
        while (i--)
            sum += this.list[i].cost();
        return sum;
    };
    Blocks.prototype.insert = function (b) {
        b.blockInd = this.list.length;
        this.list.push(b);
    };
    Blocks.prototype.remove = function (b) {
        var last = this.list.length - 1;
        var swapBlock = this.list[last];
        this.list.length = last;
        if (b !== swapBlock) {
            this.list[b.blockInd] = swapBlock;
            swapBlock.blockInd = b.blockInd;
        }
    };
    Blocks.prototype.merge = function (c) {
        var l = c.left.block, r = c.right.block;
        var dist = c.right.offset - c.left.offset - c.gap;
        if (l.vars.length < r.vars.length) {
            r.mergeAcross(l, c, dist);
            this.remove(l);
        }
        else {
            l.mergeAcross(r, c, -dist);
            this.remove(r);
        }
    };
    Blocks.prototype.forEach = function (f) {
        this.list.forEach(f);
    };
    Blocks.prototype.updateBlockPositions = function () {
        this.list.forEach(function (b) { return b.updateWeightedPosition(); });
    };
    Blocks.prototype.split = function (inactive) {
        var _this = this;
        this.updateBlockPositions();
        this.list.forEach(function (b) {
            var v = b.findMinLM();
            if (v !== null && v.lm < Solver.LAGRANGIAN_TOLERANCE) {
                b = v.left.block;
                Block.split(v).forEach(function (nb) { return _this.insert(nb); });
                _this.remove(b);
                inactive.push(v);
            }
        });
    };
    return Blocks;
}());
exports.Blocks = Blocks;
var Solver = (function () {
    function Solver(vs, cs) {
        this.vs = vs;
        this.cs = cs;
        this.vs = vs;
        vs.forEach(function (v) {
            v.cIn = [], v.cOut = [];
        });
        this.cs = cs;
        cs.forEach(function (c) {
            c.left.cOut.push(c);
            c.right.cIn.push(c);
        });
        this.inactive = cs.map(function (c) { c.active = false; return c; });
        this.bs = null;
    }
    Solver.prototype.cost = function () {
        return this.bs.cost();
    };
    Solver.prototype.setStartingPositions = function (ps) {
        this.inactive = this.cs.map(function (c) { c.active = false; return c; });
        this.bs = new Blocks(this.vs);
        this.bs.forEach(function (b, i) { return b.posn = ps[i]; });
    };
    Solver.prototype.setDesiredPositions = function (ps) {
        this.vs.forEach(function (v, i) { return v.desiredPosition = ps[i]; });
    };
    Solver.prototype.mostViolated = function () {
        var minSlack = Number.MAX_VALUE, v = null, l = this.inactive, n = l.length, deletePoint = n;
        for (var i = 0; i < n; ++i) {
            var c = l[i];
            if (c.unsatisfiable)
                continue;
            var slack = c.slack();
            if (c.equality || slack < minSlack) {
                minSlack = slack;
                v = c;
                deletePoint = i;
                if (c.equality)
                    break;
            }
        }
        if (deletePoint !== n &&
            (minSlack < Solver.ZERO_UPPERBOUND && !v.active || v.equality)) {
            l[deletePoint] = l[n - 1];
            l.length = n - 1;
        }
        return v;
    };
    Solver.prototype.satisfy = function () {
        if (this.bs == null) {
            this.bs = new Blocks(this.vs);
        }
        this.bs.split(this.inactive);
        var v = null;
        while ((v = this.mostViolated()) && (v.equality || v.slack() < Solver.ZERO_UPPERBOUND && !v.active)) {
            var lb = v.left.block, rb = v.right.block;
            if (lb !== rb) {
                this.bs.merge(v);
            }
            else {
                if (lb.isActiveDirectedPathBetween(v.right, v.left)) {
                    v.unsatisfiable = true;
                    continue;
                }
                var split = lb.splitBetween(v.left, v.right);
                if (split !== null) {
                    this.bs.insert(split.lb);
                    this.bs.insert(split.rb);
                    this.bs.remove(lb);
                    this.inactive.push(split.constraint);
                }
                else {
                    v.unsatisfiable = true;
                    continue;
                }
                if (v.slack() >= 0) {
                    this.inactive.push(v);
                }
                else {
                    this.bs.merge(v);
                }
            }
        }
    };
    Solver.prototype.solve = function () {
        this.satisfy();
        var lastcost = Number.MAX_VALUE, cost = this.bs.cost();
        while (Math.abs(lastcost - cost) > 0.0001) {
            this.satisfy();
            lastcost = cost;
            cost = this.bs.cost();
        }
        return cost;
    };
    Solver.LAGRANGIAN_TOLERANCE = -1e-4;
    Solver.ZERO_UPPERBOUND = -1e-10;
    return Solver;
}());
exports.Solver = Solver;
function removeOverlapInOneDimension(spans, lowerBound, upperBound) {
    var vs = spans.map(function (s) { return new Variable(s.desiredCenter); });
    var cs = [];
    var n = spans.length;
    for (var i = 0; i < n - 1; i++) {
        var left = spans[i], right = spans[i + 1];
        cs.push(new Constraint(vs[i], vs[i + 1], (left.size + right.size) / 2));
    }
    var leftMost = vs[0], rightMost = vs[n - 1], leftMostSize = spans[0].size / 2, rightMostSize = spans[n - 1].size / 2;
    var vLower = null, vUpper = null;
    if (lowerBound) {
        vLower = new Variable(lowerBound, leftMost.weight * 1000);
        vs.push(vLower);
        cs.push(new Constraint(vLower, leftMost, leftMostSize));
    }
    if (upperBound) {
        vUpper = new Variable(upperBound, rightMost.weight * 1000);
        vs.push(vUpper);
        cs.push(new Constraint(rightMost, vUpper, rightMostSize));
    }
    var solver = new Solver(vs, cs);
    solver.solve();
    return {
        newCenters: vs.slice(0, spans.length).map(function (v) { return v.position(); }),
        lowerBound: vLower ? vLower.position() : leftMost.position() - leftMostSize,
        upperBound: vUpper ? vUpper.position() : rightMost.position() + rightMostSize
    };
}
exports.removeOverlapInOneDimension = removeOverlapInOneDimension;
},{}]},{},[1])(1)
});

//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIm5vZGVfbW9kdWxlcy9icm93c2VyLXBhY2svX3ByZWx1ZGUuanMiLCJkaXN0L2luZGV4LmpzIiwiZGlzdC9zcmMvYWRhcHRvci5qcyIsImRpc3Qvc3JjL2JhdGNoLmpzIiwiZGlzdC9zcmMvZDNhZGFwdG9yLmpzIiwiZGlzdC9zcmMvZDN2M2FkYXB0b3IuanMiLCJkaXN0L3NyYy9kM3Y0YWRhcHRvci5qcyIsImRpc3Qvc3JjL2Rlc2NlbnQuanMiLCJkaXN0L3NyYy9nZW9tLmpzIiwiZGlzdC9zcmMvZ3JpZHJvdXRlci5qcyIsImRpc3Qvc3JjL2hhbmRsZWRpc2Nvbm5lY3RlZC5qcyIsImRpc3Qvc3JjL2xheW91dC5qcyIsImRpc3Qvc3JjL2xheW91dDNkLmpzIiwiZGlzdC9zcmMvbGlua2xlbmd0aHMuanMiLCJkaXN0L3NyYy9wb3dlcmdyYXBoLmpzIiwiZGlzdC9zcmMvcHF1ZXVlLmpzIiwiZGlzdC9zcmMvcmJ0cmVlLmpzIiwiZGlzdC9zcmMvcmVjdGFuZ2xlLmpzIiwiZGlzdC9zcmMvc2hvcnRlc3RwYXRocy5qcyIsImRpc3Qvc3JjL3Zwc2MuanMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IkFBQUE7QUNBQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQ3JCQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUNyREE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQ3hGQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FDaEJBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQ2pFQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FDN0RBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FDdFZBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FDdmFBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FDcmlCQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FDMU1BO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUNsakJBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FDbEhBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQ3ZIQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FDNVRBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUNoS0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FDcllBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQ25kQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FDekhBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBIiwiZmlsZSI6ImdlbmVyYXRlZC5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzQ29udGVudCI6WyIoZnVuY3Rpb24oKXtmdW5jdGlvbiByKGUsbix0KXtmdW5jdGlvbiBvKGksZil7aWYoIW5baV0pe2lmKCFlW2ldKXt2YXIgYz1cImZ1bmN0aW9uXCI9PXR5cGVvZiByZXF1aXJlJiZyZXF1aXJlO2lmKCFmJiZjKXJldHVybiBjKGksITApO2lmKHUpcmV0dXJuIHUoaSwhMCk7dmFyIGE9bmV3IEVycm9yKFwiQ2Fubm90IGZpbmQgbW9kdWxlICdcIitpK1wiJ1wiKTt0aHJvdyBhLmNvZGU9XCJNT0RVTEVfTk9UX0ZPVU5EXCIsYX12YXIgcD1uW2ldPXtleHBvcnRzOnt9fTtlW2ldWzBdLmNhbGwocC5leHBvcnRzLGZ1bmN0aW9uKHIpe3ZhciBuPWVbaV1bMV1bcl07cmV0dXJuIG8obnx8cil9LHAscC5leHBvcnRzLHIsZSxuLHQpfXJldHVybiBuW2ldLmV4cG9ydHN9Zm9yKHZhciB1PVwiZnVuY3Rpb25cIj09dHlwZW9mIHJlcXVpcmUmJnJlcXVpcmUsaT0wO2k8dC5sZW5ndGg7aSsrKW8odFtpXSk7cmV0dXJuIG99cmV0dXJuIHJ9KSgpIiwiXCJ1c2Ugc3RyaWN0XCI7XHJcbmZ1bmN0aW9uIF9fZXhwb3J0KG0pIHtcclxuICAgIGZvciAodmFyIHAgaW4gbSkgaWYgKCFleHBvcnRzLmhhc093blByb3BlcnR5KHApKSBleHBvcnRzW3BdID0gbVtwXTtcclxufVxyXG5PYmplY3QuZGVmaW5lUHJvcGVydHkoZXhwb3J0cywgXCJfX2VzTW9kdWxlXCIsIHsgdmFsdWU6IHRydWUgfSk7XHJcbl9fZXhwb3J0KHJlcXVpcmUoXCIuL3NyYy9hZGFwdG9yXCIpKTtcclxuX19leHBvcnQocmVxdWlyZShcIi4vc3JjL2QzYWRhcHRvclwiKSk7XHJcbl9fZXhwb3J0KHJlcXVpcmUoXCIuL3NyYy9kZXNjZW50XCIpKTtcclxuX19leHBvcnQocmVxdWlyZShcIi4vc3JjL2dlb21cIikpO1xyXG5fX2V4cG9ydChyZXF1aXJlKFwiLi9zcmMvZ3JpZHJvdXRlclwiKSk7XHJcbl9fZXhwb3J0KHJlcXVpcmUoXCIuL3NyYy9oYW5kbGVkaXNjb25uZWN0ZWRcIikpO1xyXG5fX2V4cG9ydChyZXF1aXJlKFwiLi9zcmMvbGF5b3V0XCIpKTtcclxuX19leHBvcnQocmVxdWlyZShcIi4vc3JjL2xheW91dDNkXCIpKTtcclxuX19leHBvcnQocmVxdWlyZShcIi4vc3JjL2xpbmtsZW5ndGhzXCIpKTtcclxuX19leHBvcnQocmVxdWlyZShcIi4vc3JjL3Bvd2VyZ3JhcGhcIikpO1xyXG5fX2V4cG9ydChyZXF1aXJlKFwiLi9zcmMvcHF1ZXVlXCIpKTtcclxuX19leHBvcnQocmVxdWlyZShcIi4vc3JjL3JidHJlZVwiKSk7XHJcbl9fZXhwb3J0KHJlcXVpcmUoXCIuL3NyYy9yZWN0YW5nbGVcIikpO1xyXG5fX2V4cG9ydChyZXF1aXJlKFwiLi9zcmMvc2hvcnRlc3RwYXRoc1wiKSk7XHJcbl9fZXhwb3J0KHJlcXVpcmUoXCIuL3NyYy92cHNjXCIpKTtcclxuX19leHBvcnQocmVxdWlyZShcIi4vc3JjL2JhdGNoXCIpKTtcclxuLy8jIHNvdXJjZU1hcHBpbmdVUkw9ZGF0YTphcHBsaWNhdGlvbi9qc29uO2Jhc2U2NCxleUoyWlhKemFXOXVJam96TENKbWFXeGxJam9pYVc1a1pYZ3Vhbk1pTENKemIzVnlZMlZTYjI5MElqb2lJaXdpYzI5MWNtTmxjeUk2V3lJdUxpOVhaV0pEYjJ4aEwybHVaR1Y0TG5SeklsMHNJbTVoYldWeklqcGJYU3dpYldGd2NHbHVaM01pT2lJN096czdPMEZCUVVFc2JVTkJRVFpDTzBGQlF6ZENMSEZEUVVFclFqdEJRVU12UWl4dFEwRkJOa0k3UVVGRE4wSXNaME5CUVRCQ08wRkJRekZDTEhORFFVRm5RenRCUVVOb1F5dzRRMEZCZDBNN1FVRkRlRU1zYTBOQlFUUkNPMEZCUXpWQ0xHOURRVUU0UWp0QlFVTTVRaXgxUTBGQmFVTTdRVUZEYWtNc2MwTkJRV2RETzBGQlEyaERMR3REUVVFMFFqdEJRVU0xUWl4clEwRkJORUk3UVVGRE5VSXNjVU5CUVN0Q08wRkJReTlDTEhsRFFVRnRRenRCUVVOdVF5eG5RMEZCTUVJN1FVRkRNVUlzYVVOQlFUSkNJbjA9IiwiXCJ1c2Ugc3RyaWN0XCI7XHJcbnZhciBfX2V4dGVuZHMgPSAodGhpcyAmJiB0aGlzLl9fZXh0ZW5kcykgfHwgKGZ1bmN0aW9uICgpIHtcclxuICAgIHZhciBleHRlbmRTdGF0aWNzID0gZnVuY3Rpb24gKGQsIGIpIHtcclxuICAgICAgICBleHRlbmRTdGF0aWNzID0gT2JqZWN0LnNldFByb3RvdHlwZU9mIHx8XHJcbiAgICAgICAgICAgICh7IF9fcHJvdG9fXzogW10gfSBpbnN0YW5jZW9mIEFycmF5ICYmIGZ1bmN0aW9uIChkLCBiKSB7IGQuX19wcm90b19fID0gYjsgfSkgfHxcclxuICAgICAgICAgICAgZnVuY3Rpb24gKGQsIGIpIHsgZm9yICh2YXIgcCBpbiBiKSBpZiAoYi5oYXNPd25Qcm9wZXJ0eShwKSkgZFtwXSA9IGJbcF07IH07XHJcbiAgICAgICAgcmV0dXJuIGV4dGVuZFN0YXRpY3MoZCwgYik7XHJcbiAgICB9O1xyXG4gICAgcmV0dXJuIGZ1bmN0aW9uIChkLCBiKSB7XHJcbiAgICAgICAgZXh0ZW5kU3RhdGljcyhkLCBiKTtcclxuICAgICAgICBmdW5jdGlvbiBfXygpIHsgdGhpcy5jb25zdHJ1Y3RvciA9IGQ7IH1cclxuICAgICAgICBkLnByb3RvdHlwZSA9IGIgPT09IG51bGwgPyBPYmplY3QuY3JlYXRlKGIpIDogKF9fLnByb3RvdHlwZSA9IGIucHJvdG90eXBlLCBuZXcgX18oKSk7XHJcbiAgICB9O1xyXG59KSgpO1xyXG5PYmplY3QuZGVmaW5lUHJvcGVydHkoZXhwb3J0cywgXCJfX2VzTW9kdWxlXCIsIHsgdmFsdWU6IHRydWUgfSk7XHJcbnZhciBsYXlvdXRfMSA9IHJlcXVpcmUoXCIuL2xheW91dFwiKTtcclxudmFyIExheW91dEFkYXB0b3IgPSAoZnVuY3Rpb24gKF9zdXBlcikge1xyXG4gICAgX19leHRlbmRzKExheW91dEFkYXB0b3IsIF9zdXBlcik7XHJcbiAgICBmdW5jdGlvbiBMYXlvdXRBZGFwdG9yKG9wdGlvbnMpIHtcclxuICAgICAgICB2YXIgX3RoaXMgPSBfc3VwZXIuY2FsbCh0aGlzKSB8fCB0aGlzO1xyXG4gICAgICAgIHZhciBzZWxmID0gX3RoaXM7XHJcbiAgICAgICAgdmFyIG8gPSBvcHRpb25zO1xyXG4gICAgICAgIGlmIChvLnRyaWdnZXIpIHtcclxuICAgICAgICAgICAgX3RoaXMudHJpZ2dlciA9IG8udHJpZ2dlcjtcclxuICAgICAgICB9XHJcbiAgICAgICAgaWYgKG8ua2ljaykge1xyXG4gICAgICAgICAgICBfdGhpcy5raWNrID0gby5raWNrO1xyXG4gICAgICAgIH1cclxuICAgICAgICBpZiAoby5kcmFnKSB7XHJcbiAgICAgICAgICAgIF90aGlzLmRyYWcgPSBvLmRyYWc7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIGlmIChvLm9uKSB7XHJcbiAgICAgICAgICAgIF90aGlzLm9uID0gby5vbjtcclxuICAgICAgICB9XHJcbiAgICAgICAgX3RoaXMuZHJhZ3N0YXJ0ID0gX3RoaXMuZHJhZ1N0YXJ0ID0gbGF5b3V0XzEuTGF5b3V0LmRyYWdTdGFydDtcclxuICAgICAgICBfdGhpcy5kcmFnZW5kID0gX3RoaXMuZHJhZ0VuZCA9IGxheW91dF8xLkxheW91dC5kcmFnRW5kO1xyXG4gICAgICAgIHJldHVybiBfdGhpcztcclxuICAgIH1cclxuICAgIExheW91dEFkYXB0b3IucHJvdG90eXBlLnRyaWdnZXIgPSBmdW5jdGlvbiAoZSkgeyB9O1xyXG4gICAgO1xyXG4gICAgTGF5b3V0QWRhcHRvci5wcm90b3R5cGUua2ljayA9IGZ1bmN0aW9uICgpIHsgfTtcclxuICAgIDtcclxuICAgIExheW91dEFkYXB0b3IucHJvdG90eXBlLmRyYWcgPSBmdW5jdGlvbiAoKSB7IH07XHJcbiAgICA7XHJcbiAgICBMYXlvdXRBZGFwdG9yLnByb3RvdHlwZS5vbiA9IGZ1bmN0aW9uIChldmVudFR5cGUsIGxpc3RlbmVyKSB7IHJldHVybiB0aGlzOyB9O1xyXG4gICAgO1xyXG4gICAgcmV0dXJuIExheW91dEFkYXB0b3I7XHJcbn0obGF5b3V0XzEuTGF5b3V0KSk7XHJcbmV4cG9ydHMuTGF5b3V0QWRhcHRvciA9IExheW91dEFkYXB0b3I7XHJcbmZ1bmN0aW9uIGFkYXB0b3Iob3B0aW9ucykge1xyXG4gICAgcmV0dXJuIG5ldyBMYXlvdXRBZGFwdG9yKG9wdGlvbnMpO1xyXG59XHJcbmV4cG9ydHMuYWRhcHRvciA9IGFkYXB0b3I7XHJcbi8vIyBzb3VyY2VNYXBwaW5nVVJMPWRhdGE6YXBwbGljYXRpb24vanNvbjtiYXNlNjQsZXlKMlpYSnphVzl1SWpvekxDSm1hV3hsSWpvaVlXUmhjSFJ2Y2k1cWN5SXNJbk52ZFhKalpWSnZiM1FpT2lJaUxDSnpiM1Z5WTJWeklqcGJJaTR1THk0dUwxZGxZa052YkdFdmMzSmpMMkZrWVhCMGIzSXVkSE1pWFN3aWJtRnRaWE1pT2x0ZExDSnRZWEJ3YVc1bmN5STZJanM3T3pzN096czdPenM3T3pzN08wRkJRVUVzYlVOQlFXbEVPMEZCUlRkRE8wbEJRVzFETEdsRFFVRk5PMGxCWVhKRExIVkNRVUZoTEU5QlFVODdVVUZCY0VJc1dVRkRTU3hwUWtGQlR5eFRRWGxDVmp0UlFYSkNSeXhKUVVGSkxFbEJRVWtzUjBGQlJ5eExRVUZKTEVOQlFVTTdVVUZEYUVJc1NVRkJTU3hEUVVGRExFZEJRVWNzVDBGQlR5eERRVUZETzFGQlJXaENMRWxCUVVzc1EwRkJReXhEUVVGRExFOUJRVThzUlVGQlJ6dFpRVU5pTEV0QlFVa3NRMEZCUXl4UFFVRlBMRWRCUVVjc1EwRkJReXhEUVVGRExFOUJRVThzUTBGQlF6dFRRVU0xUWp0UlFVVkVMRWxCUVVzc1EwRkJReXhEUVVGRExFbEJRVWtzUlVGQlJUdFpRVU5VTEV0QlFVa3NRMEZCUXl4SlFVRkpMRWRCUVVjc1EwRkJReXhEUVVGRExFbEJRVWtzUTBGQlF6dFRRVU4wUWp0UlFVVkVMRWxCUVVzc1EwRkJReXhEUVVGRExFbEJRVWtzUlVGQlJUdFpRVU5VTEV0QlFVa3NRMEZCUXl4SlFVRkpMRWRCUVVjc1EwRkJReXhEUVVGRExFbEJRVWtzUTBGQlF6dFRRVU4wUWp0UlFVVkVMRWxCUVVzc1EwRkJReXhEUVVGRExFVkJRVVVzUlVGQlJUdFpRVU5RTEV0QlFVa3NRMEZCUXl4RlFVRkZMRWRCUVVjc1EwRkJReXhEUVVGRExFVkJRVVVzUTBGQlF6dFRRVU5zUWp0UlFVVkVMRXRCUVVrc1EwRkJReXhUUVVGVExFZEJRVWNzUzBGQlNTeERRVUZETEZOQlFWTXNSMEZCUnl4bFFVRk5MRU5CUVVNc1UwRkJVeXhEUVVGRE8xRkJRMjVFTEV0QlFVa3NRMEZCUXl4UFFVRlBMRWRCUVVjc1MwRkJTU3hEUVVGRExFOUJRVThzUjBGQlJ5eGxRVUZOTEVOQlFVTXNUMEZCVHl4RFFVRkRPenRKUVVOcVJDeERRVUZETzBsQmNFTkVMQ3RDUVVGUExFZEJRVkFzVlVGQlVTeERRVUZSTEVsQlFVY3NRMEZCUXp0SlFVRkJMRU5CUVVNN1NVRkRja0lzTkVKQlFVa3NSMEZCU2l4alFVRlJMRU5CUVVNN1NVRkJRU3hEUVVGRE8wbEJRMVlzTkVKQlFVa3NSMEZCU2l4alFVRlJMRU5CUVVNN1NVRkJRU3hEUVVGRE8wbEJRMVlzTUVKQlFVVXNSMEZCUml4VlFVRkhMRk5CUVRaQ0xFVkJRVVVzVVVGQmIwSXNTVUZCVnl4UFFVRlBMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU03U1VGQlFTeERRVUZETzBsQmEwTndSaXh2UWtGQlF6dEJRVUZFTEVOQlFVTXNRVUY0UTBRc1EwRkJiVU1zWlVGQlRTeEhRWGREZUVNN1FVRjRRMWtzYzBOQlFXRTdRVUUyUXpGQ0xGTkJRV2RDTEU5QlFVOHNRMEZCUlN4UFFVRlBPMGxCUXpWQ0xFOUJRVThzU1VGQlNTeGhRVUZoTEVOQlFVVXNUMEZCVHl4RFFVRkZMRU5CUVVNN1FVRkRlRU1zUTBGQlF6dEJRVVpFTERCQ1FVVkRJbjA9IiwiXCJ1c2Ugc3RyaWN0XCI7XHJcbk9iamVjdC5kZWZpbmVQcm9wZXJ0eShleHBvcnRzLCBcIl9fZXNNb2R1bGVcIiwgeyB2YWx1ZTogdHJ1ZSB9KTtcclxudmFyIGxheW91dF8xID0gcmVxdWlyZShcIi4vbGF5b3V0XCIpO1xyXG52YXIgZ3JpZHJvdXRlcl8xID0gcmVxdWlyZShcIi4vZ3JpZHJvdXRlclwiKTtcclxuZnVuY3Rpb24gZ3JpZGlmeShwZ0xheW91dCwgbnVkZ2VHYXAsIG1hcmdpbiwgZ3JvdXBNYXJnaW4pIHtcclxuICAgIHBnTGF5b3V0LmNvbGEuc3RhcnQoMCwgMCwgMCwgMTAsIGZhbHNlKTtcclxuICAgIHZhciBncmlkcm91dGVyID0gcm91dGUocGdMYXlvdXQuY29sYS5ub2RlcygpLCBwZ0xheW91dC5jb2xhLmdyb3VwcygpLCBtYXJnaW4sIGdyb3VwTWFyZ2luKTtcclxuICAgIHJldHVybiBncmlkcm91dGVyLnJvdXRlRWRnZXMocGdMYXlvdXQucG93ZXJHcmFwaC5wb3dlckVkZ2VzLCBudWRnZUdhcCwgZnVuY3Rpb24gKGUpIHsgcmV0dXJuIGUuc291cmNlLnJvdXRlck5vZGUuaWQ7IH0sIGZ1bmN0aW9uIChlKSB7IHJldHVybiBlLnRhcmdldC5yb3V0ZXJOb2RlLmlkOyB9KTtcclxufVxyXG5leHBvcnRzLmdyaWRpZnkgPSBncmlkaWZ5O1xyXG5mdW5jdGlvbiByb3V0ZShub2RlcywgZ3JvdXBzLCBtYXJnaW4sIGdyb3VwTWFyZ2luKSB7XHJcbiAgICBub2Rlcy5mb3JFYWNoKGZ1bmN0aW9uIChkKSB7XHJcbiAgICAgICAgZC5yb3V0ZXJOb2RlID0ge1xyXG4gICAgICAgICAgICBuYW1lOiBkLm5hbWUsXHJcbiAgICAgICAgICAgIGJvdW5kczogZC5ib3VuZHMuaW5mbGF0ZSgtbWFyZ2luKVxyXG4gICAgICAgIH07XHJcbiAgICB9KTtcclxuICAgIGdyb3Vwcy5mb3JFYWNoKGZ1bmN0aW9uIChkKSB7XHJcbiAgICAgICAgZC5yb3V0ZXJOb2RlID0ge1xyXG4gICAgICAgICAgICBib3VuZHM6IGQuYm91bmRzLmluZmxhdGUoLWdyb3VwTWFyZ2luKSxcclxuICAgICAgICAgICAgY2hpbGRyZW46ICh0eXBlb2YgZC5ncm91cHMgIT09ICd1bmRlZmluZWQnID8gZC5ncm91cHMubWFwKGZ1bmN0aW9uIChjKSB7IHJldHVybiBub2Rlcy5sZW5ndGggKyBjLmlkOyB9KSA6IFtdKVxyXG4gICAgICAgICAgICAgICAgLmNvbmNhdCh0eXBlb2YgZC5sZWF2ZXMgIT09ICd1bmRlZmluZWQnID8gZC5sZWF2ZXMubWFwKGZ1bmN0aW9uIChjKSB7IHJldHVybiBjLmluZGV4OyB9KSA6IFtdKVxyXG4gICAgICAgIH07XHJcbiAgICB9KTtcclxuICAgIHZhciBncmlkUm91dGVyTm9kZXMgPSBub2Rlcy5jb25jYXQoZ3JvdXBzKS5tYXAoZnVuY3Rpb24gKGQsIGkpIHtcclxuICAgICAgICBkLnJvdXRlck5vZGUuaWQgPSBpO1xyXG4gICAgICAgIHJldHVybiBkLnJvdXRlck5vZGU7XHJcbiAgICB9KTtcclxuICAgIHJldHVybiBuZXcgZ3JpZHJvdXRlcl8xLkdyaWRSb3V0ZXIoZ3JpZFJvdXRlck5vZGVzLCB7XHJcbiAgICAgICAgZ2V0Q2hpbGRyZW46IGZ1bmN0aW9uICh2KSB7IHJldHVybiB2LmNoaWxkcmVuOyB9LFxyXG4gICAgICAgIGdldEJvdW5kczogZnVuY3Rpb24gKHYpIHsgcmV0dXJuIHYuYm91bmRzOyB9XHJcbiAgICB9LCBtYXJnaW4gLSBncm91cE1hcmdpbik7XHJcbn1cclxuZnVuY3Rpb24gcG93ZXJHcmFwaEdyaWRMYXlvdXQoZ3JhcGgsIHNpemUsIGdyb3VwcGFkZGluZykge1xyXG4gICAgdmFyIHBvd2VyR3JhcGg7XHJcbiAgICBncmFwaC5ub2Rlcy5mb3JFYWNoKGZ1bmN0aW9uICh2LCBpKSB7IHJldHVybiB2LmluZGV4ID0gaTsgfSk7XHJcbiAgICBuZXcgbGF5b3V0XzEuTGF5b3V0KClcclxuICAgICAgICAuYXZvaWRPdmVybGFwcyhmYWxzZSlcclxuICAgICAgICAubm9kZXMoZ3JhcGgubm9kZXMpXHJcbiAgICAgICAgLmxpbmtzKGdyYXBoLmxpbmtzKVxyXG4gICAgICAgIC5wb3dlckdyYXBoR3JvdXBzKGZ1bmN0aW9uIChkKSB7XHJcbiAgICAgICAgcG93ZXJHcmFwaCA9IGQ7XHJcbiAgICAgICAgcG93ZXJHcmFwaC5ncm91cHMuZm9yRWFjaChmdW5jdGlvbiAodikgeyByZXR1cm4gdi5wYWRkaW5nID0gZ3JvdXBwYWRkaW5nOyB9KTtcclxuICAgIH0pO1xyXG4gICAgdmFyIG4gPSBncmFwaC5ub2Rlcy5sZW5ndGg7XHJcbiAgICB2YXIgZWRnZXMgPSBbXTtcclxuICAgIHZhciB2cyA9IGdyYXBoLm5vZGVzLnNsaWNlKDApO1xyXG4gICAgdnMuZm9yRWFjaChmdW5jdGlvbiAodiwgaSkgeyByZXR1cm4gdi5pbmRleCA9IGk7IH0pO1xyXG4gICAgcG93ZXJHcmFwaC5ncm91cHMuZm9yRWFjaChmdW5jdGlvbiAoZykge1xyXG4gICAgICAgIHZhciBzb3VyY2VJbmQgPSBnLmluZGV4ID0gZy5pZCArIG47XHJcbiAgICAgICAgdnMucHVzaChnKTtcclxuICAgICAgICBpZiAodHlwZW9mIGcubGVhdmVzICE9PSAndW5kZWZpbmVkJylcclxuICAgICAgICAgICAgZy5sZWF2ZXMuZm9yRWFjaChmdW5jdGlvbiAodikgeyByZXR1cm4gZWRnZXMucHVzaCh7IHNvdXJjZTogc291cmNlSW5kLCB0YXJnZXQ6IHYuaW5kZXggfSk7IH0pO1xyXG4gICAgICAgIGlmICh0eXBlb2YgZy5ncm91cHMgIT09ICd1bmRlZmluZWQnKVxyXG4gICAgICAgICAgICBnLmdyb3Vwcy5mb3JFYWNoKGZ1bmN0aW9uIChnZykgeyByZXR1cm4gZWRnZXMucHVzaCh7IHNvdXJjZTogc291cmNlSW5kLCB0YXJnZXQ6IGdnLmlkICsgbiB9KTsgfSk7XHJcbiAgICB9KTtcclxuICAgIHBvd2VyR3JhcGgucG93ZXJFZGdlcy5mb3JFYWNoKGZ1bmN0aW9uIChlKSB7XHJcbiAgICAgICAgZWRnZXMucHVzaCh7IHNvdXJjZTogZS5zb3VyY2UuaW5kZXgsIHRhcmdldDogZS50YXJnZXQuaW5kZXggfSk7XHJcbiAgICB9KTtcclxuICAgIG5ldyBsYXlvdXRfMS5MYXlvdXQoKVxyXG4gICAgICAgIC5zaXplKHNpemUpXHJcbiAgICAgICAgLm5vZGVzKHZzKVxyXG4gICAgICAgIC5saW5rcyhlZGdlcylcclxuICAgICAgICAuYXZvaWRPdmVybGFwcyhmYWxzZSlcclxuICAgICAgICAubGlua0Rpc3RhbmNlKDMwKVxyXG4gICAgICAgIC5zeW1tZXRyaWNEaWZmTGlua0xlbmd0aHMoNSlcclxuICAgICAgICAuY29udmVyZ2VuY2VUaHJlc2hvbGQoMWUtNClcclxuICAgICAgICAuc3RhcnQoMTAwLCAwLCAwLCAwLCBmYWxzZSk7XHJcbiAgICByZXR1cm4ge1xyXG4gICAgICAgIGNvbGE6IG5ldyBsYXlvdXRfMS5MYXlvdXQoKVxyXG4gICAgICAgICAgICAuY29udmVyZ2VuY2VUaHJlc2hvbGQoMWUtMylcclxuICAgICAgICAgICAgLnNpemUoc2l6ZSlcclxuICAgICAgICAgICAgLmF2b2lkT3ZlcmxhcHModHJ1ZSlcclxuICAgICAgICAgICAgLm5vZGVzKGdyYXBoLm5vZGVzKVxyXG4gICAgICAgICAgICAubGlua3MoZ3JhcGgubGlua3MpXHJcbiAgICAgICAgICAgIC5ncm91cENvbXBhY3RuZXNzKDFlLTQpXHJcbiAgICAgICAgICAgIC5saW5rRGlzdGFuY2UoMzApXHJcbiAgICAgICAgICAgIC5zeW1tZXRyaWNEaWZmTGlua0xlbmd0aHMoNSlcclxuICAgICAgICAgICAgLnBvd2VyR3JhcGhHcm91cHMoZnVuY3Rpb24gKGQpIHtcclxuICAgICAgICAgICAgcG93ZXJHcmFwaCA9IGQ7XHJcbiAgICAgICAgICAgIHBvd2VyR3JhcGguZ3JvdXBzLmZvckVhY2goZnVuY3Rpb24gKHYpIHtcclxuICAgICAgICAgICAgICAgIHYucGFkZGluZyA9IGdyb3VwcGFkZGluZztcclxuICAgICAgICAgICAgfSk7XHJcbiAgICAgICAgfSkuc3RhcnQoNTAsIDAsIDEwMCwgMCwgZmFsc2UpLFxyXG4gICAgICAgIHBvd2VyR3JhcGg6IHBvd2VyR3JhcGhcclxuICAgIH07XHJcbn1cclxuZXhwb3J0cy5wb3dlckdyYXBoR3JpZExheW91dCA9IHBvd2VyR3JhcGhHcmlkTGF5b3V0O1xyXG4vLyMgc291cmNlTWFwcGluZ1VSTD1kYXRhOmFwcGxpY2F0aW9uL2pzb247YmFzZTY0LGV5SjJaWEp6YVc5dUlqb3pMQ0ptYVd4bElqb2lZbUYwWTJndWFuTWlMQ0p6YjNWeVkyVlNiMjkwSWpvaUlpd2ljMjkxY21ObGN5STZXeUl1TGk4dUxpOVhaV0pEYjJ4aEwzTnlZeTlpWVhSamFDNTBjeUpkTENKdVlXMWxjeUk2VzEwc0ltMWhjSEJwYm1keklqb2lPenRCUVVGQkxHMURRVUV5UXp0QlFVTXpReXd5UTBGQmRVTTdRVUZSZGtNc1UwRkJaMElzVDBGQlR5eERRVUZETEZGQlFWRXNSVUZCUlN4UlFVRm5RaXhGUVVGRkxFMUJRV01zUlVGQlJTeFhRVUZ0UWp0SlFVTnVSaXhSUVVGUkxFTkJRVU1zU1VGQlNTeERRVUZETEV0QlFVc3NRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhGUVVGRkxFTkJRVU1zUlVGQlJTeEZRVUZGTEVWQlFVVXNTMEZCU3l4RFFVRkRMRU5CUVVNN1NVRkRlRU1zU1VGQlNTeFZRVUZWTEVkQlFVY3NTMEZCU3l4RFFVRkRMRkZCUVZFc1EwRkJReXhKUVVGSkxFTkJRVU1zUzBGQlN5eEZRVUZGTEVWQlFVVXNVVUZCVVN4RFFVRkRMRWxCUVVrc1EwRkJReXhOUVVGTkxFVkJRVVVzUlVGQlJTeE5RVUZOTEVWQlFVVXNWMEZCVnl4RFFVRkRMRU5CUVVNN1NVRkRNMFlzVDBGQlR5eFZRVUZWTEVOQlFVTXNWVUZCVlN4RFFVRk5MRkZCUVZFc1EwRkJReXhWUVVGVkxFTkJRVU1zVlVGQlZTeEZRVUZGTEZGQlFWRXNSVUZCUlN4VlFVRkJMRU5CUVVNc1NVRkJSeXhQUVVGQkxFTkJRVU1zUTBGQlF5eE5RVUZOTEVOQlFVTXNWVUZCVlN4RFFVRkRMRVZCUVVVc1JVRkJkRUlzUTBGQmMwSXNSVUZCUlN4VlFVRkJMRU5CUVVNc1NVRkJSeXhQUVVGQkxFTkJRVU1zUTBGQlF5eE5RVUZOTEVOQlFVTXNWVUZCVlN4RFFVRkRMRVZCUVVVc1JVRkJkRUlzUTBGQmMwSXNRMEZCUXl4RFFVRkRPMEZCUTNoSkxFTkJRVU03UVVGS1JDd3dRa0ZKUXp0QlFVVkVMRk5CUVZNc1MwRkJTeXhEUVVGRExFdEJRVXNzUlVGQlJTeE5RVUZOTEVWQlFVVXNUVUZCWXl4RlFVRkZMRmRCUVcxQ08wbEJRemRFTEV0QlFVc3NRMEZCUXl4UFFVRlBMRU5CUVVNc1ZVRkJRU3hEUVVGRE8xRkJRMWdzUTBGQlF5eERRVUZETEZWQlFWVXNSMEZCVVR0WlFVTm9RaXhKUVVGSkxFVkJRVVVzUTBGQlF5eERRVUZETEVsQlFVazdXVUZEV2l4TlFVRk5MRVZCUVVVc1EwRkJReXhEUVVGRExFMUJRVTBzUTBGQlF5eFBRVUZQTEVOQlFVTXNRMEZCUXl4TlFVRk5MRU5CUVVNN1UwRkRjRU1zUTBGQlF6dEpRVU5PTEVOQlFVTXNRMEZCUXl4RFFVRkRPMGxCUTBnc1RVRkJUU3hEUVVGRExFOUJRVThzUTBGQlF5eFZRVUZCTEVOQlFVTTdVVUZEV2l4RFFVRkRMRU5CUVVNc1ZVRkJWU3hIUVVGUk8xbEJRMmhDTEUxQlFVMHNSVUZCUlN4RFFVRkRMRU5CUVVNc1RVRkJUU3hEUVVGRExFOUJRVThzUTBGQlF5eERRVUZETEZkQlFWY3NRMEZCUXp0WlFVTjBReXhSUVVGUkxFVkJRVVVzUTBGQlF5eFBRVUZQTEVOQlFVTXNRMEZCUXl4TlFVRk5MRXRCUVVzc1YwRkJWeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNUVUZCVFN4RFFVRkRMRWRCUVVjc1EwRkJReXhWUVVGQkxFTkJRVU1zU1VGQlJ5eFBRVUZCTEV0QlFVc3NRMEZCUXl4TlFVRk5MRWRCUVVjc1EwRkJReXhEUVVGRExFVkJRVVVzUlVGQmJrSXNRMEZCYlVJc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTTdhVUpCUTI1R0xFMUJRVTBzUTBGQlF5eFBRVUZQTEVOQlFVTXNRMEZCUXl4TlFVRk5MRXRCUVVzc1YwRkJWeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNUVUZCVFN4RFFVRkRMRWRCUVVjc1EwRkJReXhWUVVGQkxFTkJRVU1zU1VGQlJ5eFBRVUZCTEVOQlFVTXNRMEZCUXl4TFFVRkxMRVZCUVZBc1EwRkJUeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXp0VFFVTm9SaXhEUVVGRE8wbEJRMDRzUTBGQlF5eERRVUZETEVOQlFVTTdTVUZEU0N4SlFVRkpMR1ZCUVdVc1IwRkJSeXhMUVVGTExFTkJRVU1zVFVGQlRTeERRVUZETEUxQlFVMHNRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhWUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETzFGQlEyaEVMRU5CUVVNc1EwRkJReXhWUVVGVkxFTkJRVU1zUlVGQlJTeEhRVUZITEVOQlFVTXNRMEZCUXp0UlFVTndRaXhQUVVGUExFTkJRVU1zUTBGQlF5eFZRVUZWTEVOQlFVTTdTVUZEZUVJc1EwRkJReXhEUVVGRExFTkJRVU03U1VGRFNDeFBRVUZQTEVsQlFVa3NkVUpCUVZVc1EwRkJReXhsUVVGbExFVkJRVVU3VVVGRGJrTXNWMEZCVnl4RlFVRkZMRlZCUVVNc1EwRkJUU3hKUVVGTExFOUJRVUVzUTBGQlF5eERRVUZETEZGQlFWRXNSVUZCVml4RFFVRlZPMUZCUTI1RExGTkJRVk1zUlVGQlJTeFZRVUZCTEVOQlFVTXNTVUZCU1N4UFFVRkJMRU5CUVVNc1EwRkJReXhOUVVGTkxFVkJRVklzUTBGQlVUdExRVU16UWl4RlFVRkZMRTFCUVUwc1IwRkJSeXhYUVVGWExFTkJRVU1zUTBGQlF6dEJRVU0zUWl4RFFVRkRPMEZCUlVRc1UwRkJaMElzYjBKQlFXOUNMRU5CUTJoRExFdEJRVFpETEVWQlF6ZERMRWxCUVdNc1JVRkRaQ3haUVVGdlFqdEpRVWR3UWl4SlFVRkpMRlZCUVZVc1EwRkJRenRKUVVObUxFdEJRVXNzUTBGQlF5eExRVUZMTEVOQlFVTXNUMEZCVHl4RFFVRkRMRlZCUVVNc1EwRkJReXhGUVVGRExFTkJRVU1zU1VGQlN5eFBRVUZOTEVOQlFVVXNRMEZCUXl4TFFVRkxMRWRCUVVjc1EwRkJReXhGUVVGc1FpeERRVUZyUWl4RFFVRkRMRU5CUVVNN1NVRkRha1FzU1VGQlNTeGxRVUZOTEVWQlFVVTdVMEZEVUN4aFFVRmhMRU5CUVVNc1MwRkJTeXhEUVVGRE8xTkJRM0JDTEV0QlFVc3NRMEZCUXl4TFFVRkxMRU5CUVVNc1MwRkJTeXhEUVVGRE8xTkJRMnhDTEV0QlFVc3NRMEZCUXl4TFFVRkxMRU5CUVVNc1MwRkJTeXhEUVVGRE8xTkJRMnhDTEdkQ1FVRm5RaXhEUVVGRExGVkJRVlVzUTBGQlF6dFJRVU42UWl4VlFVRlZMRWRCUVVjc1EwRkJReXhEUVVGRE8xRkJRMllzVlVGQlZTeERRVUZETEUxQlFVMHNRMEZCUXl4UFFVRlBMRU5CUVVNc1ZVRkJRU3hEUVVGRExFbEJRVWNzVDBGQlFTeERRVUZETEVOQlFVTXNUMEZCVHl4SFFVRkhMRmxCUVZrc1JVRkJlRUlzUTBGQmQwSXNRMEZCUXl4RFFVRkRPMGxCUXpWRUxFTkJRVU1zUTBGQlF5eERRVUZETzBsQlNWQXNTVUZCU1N4RFFVRkRMRWRCUVVjc1MwRkJTeXhEUVVGRExFdEJRVXNzUTBGQlF5eE5RVUZOTEVOQlFVTTdTVUZETTBJc1NVRkJTU3hMUVVGTExFZEJRVWNzUlVGQlJTeERRVUZETzBsQlEyWXNTVUZCU1N4RlFVRkZMRWRCUVVjc1MwRkJTeXhEUVVGRExFdEJRVXNzUTBGQlF5eExRVUZMTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1NVRkRPVUlzUlVGQlJTeERRVUZETEU5QlFVOHNRMEZCUXl4VlFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFbEJRVXNzVDBGQlRTeERRVUZGTEVOQlFVTXNTMEZCU3l4SFFVRkhMRU5CUVVNc1JVRkJiRUlzUTBGQmEwSXNRMEZCUXl4RFFVRkRPMGxCUTNwRExGVkJRVlVzUTBGQlF5eE5RVUZOTEVOQlFVTXNUMEZCVHl4RFFVRkRMRlZCUVVFc1EwRkJRenRSUVVOMlFpeEpRVUZKTEZOQlFWTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1MwRkJTeXhIUVVGSExFTkJRVU1zUTBGQlF5eEZRVUZGTEVkQlFVY3NRMEZCUXl4RFFVRkRPMUZCUTI1RExFVkJRVVVzUTBGQlF5eEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1VVRkRXQ3hKUVVGSkxFOUJRVThzUTBGQlF5eERRVUZETEUxQlFVMHNTMEZCU3l4WFFVRlhPMWxCUXk5Q0xFTkJRVU1zUTBGQlF5eE5RVUZOTEVOQlFVTXNUMEZCVHl4RFFVRkRMRlZCUVVFc1EwRkJReXhKUVVGSkxFOUJRVUVzUzBGQlN5eERRVUZETEVsQlFVa3NRMEZCUXl4RlFVRkZMRTFCUVUwc1JVRkJSU3hUUVVGVExFVkJRVVVzVFVGQlRTeEZRVUZGTEVOQlFVTXNRMEZCUXl4TFFVRkxMRVZCUVVVc1EwRkJReXhGUVVGc1JDeERRVUZyUkN4RFFVRkRMRU5CUVVNN1VVRkRPVVVzU1VGQlNTeFBRVUZQTEVOQlFVTXNRMEZCUXl4TlFVRk5MRXRCUVVzc1YwRkJWenRaUVVNdlFpeERRVUZETEVOQlFVTXNUVUZCVFN4RFFVRkRMRTlCUVU4c1EwRkJReXhWUVVGQkxFVkJRVVVzU1VGQlNTeFBRVUZCTEV0QlFVc3NRMEZCUXl4SlFVRkpMRU5CUVVNc1JVRkJSU3hOUVVGTkxFVkJRVVVzVTBGQlV5eEZRVUZGTEUxQlFVMHNSVUZCUlN4RlFVRkZMRU5CUVVNc1JVRkJSU3hIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETEVWQlFYQkVMRU5CUVc5RUxFTkJRVU1zUTBGQlF6dEpRVU55Uml4RFFVRkRMRU5CUVVNc1EwRkJRenRKUVVOSUxGVkJRVlVzUTBGQlF5eFZRVUZWTEVOQlFVTXNUMEZCVHl4RFFVRkRMRlZCUVVFc1EwRkJRenRSUVVNelFpeExRVUZMTEVOQlFVTXNTVUZCU1N4RFFVRkRMRVZCUVVVc1RVRkJUU3hGUVVGRkxFTkJRVU1zUTBGQlF5eE5RVUZOTEVOQlFVTXNTMEZCU3l4RlFVRkZMRTFCUVUwc1JVRkJSU3hEUVVGRExFTkJRVU1zVFVGQlRTeERRVUZETEV0QlFVc3NSVUZCUlN4RFFVRkRMRU5CUVVNN1NVRkRia1VzUTBGQlF5eERRVUZETEVOQlFVTTdTVUZIU0N4SlFVRkpMR1ZCUVUwc1JVRkJSVHRUUVVOUUxFbEJRVWtzUTBGQlF5eEpRVUZKTEVOQlFVTTdVMEZEVml4TFFVRkxMRU5CUVVNc1JVRkJSU3hEUVVGRE8xTkJRMVFzUzBGQlN5eERRVUZETEV0QlFVc3NRMEZCUXp0VFFVTmFMR0ZCUVdFc1EwRkJReXhMUVVGTExFTkJRVU03VTBGRGNFSXNXVUZCV1N4RFFVRkRMRVZCUVVVc1EwRkJRenRUUVVOb1FpeDNRa0ZCZDBJc1EwRkJReXhEUVVGRExFTkJRVU03VTBGRE0wSXNiMEpCUVc5Q0xFTkJRVU1zU1VGQlNTeERRVUZETzFOQlF6RkNMRXRCUVVzc1EwRkJReXhIUVVGSExFVkJRVVVzUTBGQlF5eEZRVUZGTEVOQlFVTXNSVUZCUlN4RFFVRkRMRVZCUVVVc1MwRkJTeXhEUVVGRExFTkJRVU03U1VGTGFFTXNUMEZCVHp0UlFVTklMRWxCUVVrc1JVRkRRU3hKUVVGSkxHVkJRVTBzUlVGQlJUdGhRVU5ZTEc5Q1FVRnZRaXhEUVVGRExFbEJRVWtzUTBGQlF6dGhRVU14UWl4SlFVRkpMRU5CUVVNc1NVRkJTU3hEUVVGRE8yRkJRMVlzWVVGQllTeERRVUZETEVsQlFVa3NRMEZCUXp0aFFVTnVRaXhMUVVGTExFTkJRVU1zUzBGQlN5eERRVUZETEV0QlFVc3NRMEZCUXp0aFFVTnNRaXhMUVVGTExFTkJRVU1zUzBGQlN5eERRVUZETEV0QlFVc3NRMEZCUXp0aFFVVnNRaXhuUWtGQlowSXNRMEZCUXl4SlFVRkpMRU5CUVVNN1lVRkRkRUlzV1VGQldTeERRVUZETEVWQlFVVXNRMEZCUXp0aFFVTm9RaXgzUWtGQmQwSXNRMEZCUXl4RFFVRkRMRU5CUVVNN1lVRkRNMElzWjBKQlFXZENMRU5CUVVNc1ZVRkJWU3hEUVVGRE8xbEJRM3BDTEZWQlFWVXNSMEZCUnl4RFFVRkRMRU5CUVVNN1dVRkRaaXhWUVVGVkxFTkJRVU1zVFVGQlRTeERRVUZETEU5QlFVOHNRMEZCUXl4VlFVRlZMRU5CUVVNN1owSkJRMnBETEVOQlFVTXNRMEZCUXl4UFFVRlBMRWRCUVVjc1dVRkJXU3hEUVVGQk8xbEJRelZDTEVOQlFVTXNRMEZCUXl4RFFVRkRPMUZCUTFBc1EwRkJReXhEUVVGRExFTkJRVU1zUzBGQlN5eERRVUZETEVWQlFVVXNSVUZCUlN4RFFVRkRMRVZCUVVVc1IwRkJSeXhGUVVGRkxFTkJRVU1zUlVGQlJTeExRVUZMTEVOQlFVTTdVVUZEYkVNc1ZVRkJWU3hGUVVGRkxGVkJRVlU3UzBGRGVrSXNRMEZCUXp0QlFVTk9MRU5CUVVNN1FVRnlSVVFzYjBSQmNVVkRJbjA9IiwiXCJ1c2Ugc3RyaWN0XCI7XHJcbk9iamVjdC5kZWZpbmVQcm9wZXJ0eShleHBvcnRzLCBcIl9fZXNNb2R1bGVcIiwgeyB2YWx1ZTogdHJ1ZSB9KTtcclxudmFyIGQzdjMgPSByZXF1aXJlKFwiLi9kM3YzYWRhcHRvclwiKTtcclxudmFyIGQzdjQgPSByZXF1aXJlKFwiLi9kM3Y0YWRhcHRvclwiKTtcclxuO1xyXG5mdW5jdGlvbiBkM2FkYXB0b3IoZDNDb250ZXh0KSB7XHJcbiAgICBpZiAoIWQzQ29udGV4dCB8fCBpc0QzVjMoZDNDb250ZXh0KSkge1xyXG4gICAgICAgIHJldHVybiBuZXcgZDN2My5EM1N0eWxlTGF5b3V0QWRhcHRvcigpO1xyXG4gICAgfVxyXG4gICAgcmV0dXJuIG5ldyBkM3Y0LkQzU3R5bGVMYXlvdXRBZGFwdG9yKGQzQ29udGV4dCk7XHJcbn1cclxuZXhwb3J0cy5kM2FkYXB0b3IgPSBkM2FkYXB0b3I7XHJcbmZ1bmN0aW9uIGlzRDNWMyhkM0NvbnRleHQpIHtcclxuICAgIHZhciB2M2V4cCA9IC9eM1xcLi87XHJcbiAgICByZXR1cm4gZDNDb250ZXh0LnZlcnNpb24gJiYgZDNDb250ZXh0LnZlcnNpb24ubWF0Y2godjNleHApICE9PSBudWxsO1xyXG59XHJcbi8vIyBzb3VyY2VNYXBwaW5nVVJMPWRhdGE6YXBwbGljYXRpb24vanNvbjtiYXNlNjQsZXlKMlpYSnphVzl1SWpvekxDSm1hV3hsSWpvaVpETmhaR0Z3ZEc5eUxtcHpJaXdpYzI5MWNtTmxVbTl2ZENJNklpSXNJbk52ZFhKalpYTWlPbHNpTGk0dkxpNHZWMlZpUTI5c1lTOXpjbU12WkROaFpHRndkRzl5TG5SeklsMHNJbTVoYldWeklqcGJYU3dpYldGd2NHbHVaM01pT2lJN08wRkJRVUVzYjBOQlFYRkRPMEZCUTNKRExHOURRVUZ4UXp0QlFVZFZMRU5CUVVNN1FVRTBRbWhFTEZOQlFXZENMRk5CUVZNc1EwRkJReXhUUVVGM1F6dEpRVU01UkN4SlFVRkpMRU5CUVVNc1UwRkJVeXhKUVVGSkxFMUJRVTBzUTBGQlF5eFRRVUZUTEVOQlFVTXNSVUZCUlR0UlFVTnFReXhQUVVGUExFbEJRVWtzU1VGQlNTeERRVUZETEc5Q1FVRnZRaXhGUVVGRkxFTkJRVU03UzBGRE1VTTdTVUZEUkN4UFFVRlBMRWxCUVVrc1NVRkJTU3hEUVVGRExHOUNRVUZ2UWl4RFFVRkRMRk5CUVZNc1EwRkJReXhEUVVGRE8wRkJRM0JFTEVOQlFVTTdRVUZNUkN3NFFrRkxRenRCUVVWRUxGTkJRVk1zVFVGQlRTeERRVUZETEZOQlFYVkRPMGxCUTI1RUxFbEJRVTBzUzBGQlN5eEhRVUZITEUxQlFVMHNRMEZCUXp0SlFVTnlRaXhQUVVGaExGTkJRVlVzUTBGQlF5eFBRVUZQTEVsQlFWVXNVMEZCVlN4RFFVRkRMRTlCUVU4c1EwRkJReXhMUVVGTExFTkJRVU1zUzBGQlN5eERRVUZETEV0QlFVc3NTVUZCU1N4RFFVRkRPMEZCUTNSR0xFTkJRVU1pZlE9PSIsIlwidXNlIHN0cmljdFwiO1xyXG52YXIgX19leHRlbmRzID0gKHRoaXMgJiYgdGhpcy5fX2V4dGVuZHMpIHx8IChmdW5jdGlvbiAoKSB7XHJcbiAgICB2YXIgZXh0ZW5kU3RhdGljcyA9IGZ1bmN0aW9uIChkLCBiKSB7XHJcbiAgICAgICAgZXh0ZW5kU3RhdGljcyA9IE9iamVjdC5zZXRQcm90b3R5cGVPZiB8fFxyXG4gICAgICAgICAgICAoeyBfX3Byb3RvX186IFtdIH0gaW5zdGFuY2VvZiBBcnJheSAmJiBmdW5jdGlvbiAoZCwgYikgeyBkLl9fcHJvdG9fXyA9IGI7IH0pIHx8XHJcbiAgICAgICAgICAgIGZ1bmN0aW9uIChkLCBiKSB7IGZvciAodmFyIHAgaW4gYikgaWYgKGIuaGFzT3duUHJvcGVydHkocCkpIGRbcF0gPSBiW3BdOyB9O1xyXG4gICAgICAgIHJldHVybiBleHRlbmRTdGF0aWNzKGQsIGIpO1xyXG4gICAgfTtcclxuICAgIHJldHVybiBmdW5jdGlvbiAoZCwgYikge1xyXG4gICAgICAgIGV4dGVuZFN0YXRpY3MoZCwgYik7XHJcbiAgICAgICAgZnVuY3Rpb24gX18oKSB7IHRoaXMuY29uc3RydWN0b3IgPSBkOyB9XHJcbiAgICAgICAgZC5wcm90b3R5cGUgPSBiID09PSBudWxsID8gT2JqZWN0LmNyZWF0ZShiKSA6IChfXy5wcm90b3R5cGUgPSBiLnByb3RvdHlwZSwgbmV3IF9fKCkpO1xyXG4gICAgfTtcclxufSkoKTtcclxuT2JqZWN0LmRlZmluZVByb3BlcnR5KGV4cG9ydHMsIFwiX19lc01vZHVsZVwiLCB7IHZhbHVlOiB0cnVlIH0pO1xyXG52YXIgbGF5b3V0XzEgPSByZXF1aXJlKFwiLi9sYXlvdXRcIik7XHJcbnZhciBEM1N0eWxlTGF5b3V0QWRhcHRvciA9IChmdW5jdGlvbiAoX3N1cGVyKSB7XHJcbiAgICBfX2V4dGVuZHMoRDNTdHlsZUxheW91dEFkYXB0b3IsIF9zdXBlcik7XHJcbiAgICBmdW5jdGlvbiBEM1N0eWxlTGF5b3V0QWRhcHRvcigpIHtcclxuICAgICAgICB2YXIgX3RoaXMgPSBfc3VwZXIuY2FsbCh0aGlzKSB8fCB0aGlzO1xyXG4gICAgICAgIF90aGlzLmV2ZW50ID0gZDMuZGlzcGF0Y2gobGF5b3V0XzEuRXZlbnRUeXBlW2xheW91dF8xLkV2ZW50VHlwZS5zdGFydF0sIGxheW91dF8xLkV2ZW50VHlwZVtsYXlvdXRfMS5FdmVudFR5cGUudGlja10sIGxheW91dF8xLkV2ZW50VHlwZVtsYXlvdXRfMS5FdmVudFR5cGUuZW5kXSk7XHJcbiAgICAgICAgdmFyIGQzbGF5b3V0ID0gX3RoaXM7XHJcbiAgICAgICAgdmFyIGRyYWc7XHJcbiAgICAgICAgX3RoaXMuZHJhZyA9IGZ1bmN0aW9uICgpIHtcclxuICAgICAgICAgICAgaWYgKCFkcmFnKSB7XHJcbiAgICAgICAgICAgICAgICB2YXIgZHJhZyA9IGQzLmJlaGF2aW9yLmRyYWcoKVxyXG4gICAgICAgICAgICAgICAgICAgIC5vcmlnaW4obGF5b3V0XzEuTGF5b3V0LmRyYWdPcmlnaW4pXHJcbiAgICAgICAgICAgICAgICAgICAgLm9uKFwiZHJhZ3N0YXJ0LmQzYWRhcHRvclwiLCBsYXlvdXRfMS5MYXlvdXQuZHJhZ1N0YXJ0KVxyXG4gICAgICAgICAgICAgICAgICAgIC5vbihcImRyYWcuZDNhZGFwdG9yXCIsIGZ1bmN0aW9uIChkKSB7XHJcbiAgICAgICAgICAgICAgICAgICAgbGF5b3V0XzEuTGF5b3V0LmRyYWcoZCwgZDMuZXZlbnQpO1xyXG4gICAgICAgICAgICAgICAgICAgIGQzbGF5b3V0LnJlc3VtZSgpO1xyXG4gICAgICAgICAgICAgICAgfSlcclxuICAgICAgICAgICAgICAgICAgICAub24oXCJkcmFnZW5kLmQzYWRhcHRvclwiLCBsYXlvdXRfMS5MYXlvdXQuZHJhZ0VuZCk7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgaWYgKCFhcmd1bWVudHMubGVuZ3RoKVxyXG4gICAgICAgICAgICAgICAgcmV0dXJuIGRyYWc7XHJcbiAgICAgICAgICAgIHRoaXNcclxuICAgICAgICAgICAgICAgIC5jYWxsKGRyYWcpO1xyXG4gICAgICAgIH07XHJcbiAgICAgICAgcmV0dXJuIF90aGlzO1xyXG4gICAgfVxyXG4gICAgRDNTdHlsZUxheW91dEFkYXB0b3IucHJvdG90eXBlLnRyaWdnZXIgPSBmdW5jdGlvbiAoZSkge1xyXG4gICAgICAgIHZhciBkM2V2ZW50ID0geyB0eXBlOiBsYXlvdXRfMS5FdmVudFR5cGVbZS50eXBlXSwgYWxwaGE6IGUuYWxwaGEsIHN0cmVzczogZS5zdHJlc3MgfTtcclxuICAgICAgICB0aGlzLmV2ZW50W2QzZXZlbnQudHlwZV0oZDNldmVudCk7XHJcbiAgICB9O1xyXG4gICAgRDNTdHlsZUxheW91dEFkYXB0b3IucHJvdG90eXBlLmtpY2sgPSBmdW5jdGlvbiAoKSB7XHJcbiAgICAgICAgdmFyIF90aGlzID0gdGhpcztcclxuICAgICAgICBkMy50aW1lcihmdW5jdGlvbiAoKSB7IHJldHVybiBfc3VwZXIucHJvdG90eXBlLnRpY2suY2FsbChfdGhpcyk7IH0pO1xyXG4gICAgfTtcclxuICAgIEQzU3R5bGVMYXlvdXRBZGFwdG9yLnByb3RvdHlwZS5vbiA9IGZ1bmN0aW9uIChldmVudFR5cGUsIGxpc3RlbmVyKSB7XHJcbiAgICAgICAgaWYgKHR5cGVvZiBldmVudFR5cGUgPT09ICdzdHJpbmcnKSB7XHJcbiAgICAgICAgICAgIHRoaXMuZXZlbnQub24oZXZlbnRUeXBlLCBsaXN0ZW5lcik7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIGVsc2Uge1xyXG4gICAgICAgICAgICB0aGlzLmV2ZW50Lm9uKGxheW91dF8xLkV2ZW50VHlwZVtldmVudFR5cGVdLCBsaXN0ZW5lcik7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIHJldHVybiB0aGlzO1xyXG4gICAgfTtcclxuICAgIHJldHVybiBEM1N0eWxlTGF5b3V0QWRhcHRvcjtcclxufShsYXlvdXRfMS5MYXlvdXQpKTtcclxuZXhwb3J0cy5EM1N0eWxlTGF5b3V0QWRhcHRvciA9IEQzU3R5bGVMYXlvdXRBZGFwdG9yO1xyXG5mdW5jdGlvbiBkM2FkYXB0b3IoKSB7XHJcbiAgICByZXR1cm4gbmV3IEQzU3R5bGVMYXlvdXRBZGFwdG9yKCk7XHJcbn1cclxuZXhwb3J0cy5kM2FkYXB0b3IgPSBkM2FkYXB0b3I7XHJcbi8vIyBzb3VyY2VNYXBwaW5nVVJMPWRhdGE6YXBwbGljYXRpb24vanNvbjtiYXNlNjQsZXlKMlpYSnphVzl1SWpvekxDSm1hV3hsSWpvaVpETjJNMkZrWVhCMGIzSXVhbk1pTENKemIzVnlZMlZTYjI5MElqb2lJaXdpYzI5MWNtTmxjeUk2V3lJdUxpOHVMaTlYWldKRGIyeGhMM055WXk5a00zWXpZV1JoY0hSdmNpNTBjeUpkTENKdVlXMWxjeUk2VzEwc0ltMWhjSEJwYm1keklqb2lPenM3T3pzN096czdPenM3T3pzN1FVRk5RU3h0UTBGQmEwUTdRVUZIT1VNN1NVRkJNRU1zZDBOQlFVMDdTVUZuUWpWRE8xRkJRVUVzV1VGRFNTeHBRa0ZCVHl4VFFYVkNWanRSUVhaRFJDeFhRVUZMTEVkQlFVY3NSVUZCUlN4RFFVRkRMRkZCUVZFc1EwRkJReXhyUWtGQlV5eERRVUZETEd0Q1FVRlRMRU5CUVVNc1MwRkJTeXhEUVVGRExFVkJRVVVzYTBKQlFWTXNRMEZCUXl4clFrRkJVeXhEUVVGRExFbEJRVWtzUTBGQlF5eEZRVUZGTEd0Q1FVRlRMRU5CUVVNc2EwSkJRVk1zUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXl4RFFVRkRPMUZCYTBKcVJ5eEpRVUZKTEZGQlFWRXNSMEZCUnl4TFFVRkpMRU5CUVVNN1VVRkRjRUlzU1VGQlNTeEpRVUZKTEVOQlFVTTdVVUZEVkN4TFFVRkpMRU5CUVVNc1NVRkJTU3hIUVVGSE8xbEJRMUlzU1VGQlNTeERRVUZETEVsQlFVa3NSVUZCUlR0blFrRkRVQ3hKUVVGSkxFbEJRVWtzUjBGQlJ5eEZRVUZGTEVOQlFVTXNVVUZCVVN4RFFVRkRMRWxCUVVrc1JVRkJSVHR4UWtGRGVFSXNUVUZCVFN4RFFVRkRMR1ZCUVUwc1EwRkJReXhWUVVGVkxFTkJRVU03Y1VKQlEzcENMRVZCUVVVc1EwRkJReXh4UWtGQmNVSXNSVUZCUlN4bFFVRk5MRU5CUVVNc1UwRkJVeXhEUVVGRE8zRkNRVU16UXl4RlFVRkZMRU5CUVVNc1owSkJRV2RDTEVWQlFVVXNWVUZCUVN4RFFVRkRPMjlDUVVOdVFpeGxRVUZOTEVOQlFVTXNTVUZCU1N4RFFVRkRMRU5CUVVNc1JVRkJUeXhGUVVGRkxFTkJRVU1zUzBGQlN5eERRVUZETEVOQlFVTTdiMEpCUXpsQ0xGRkJRVkVzUTBGQlF5eE5RVUZOTEVWQlFVVXNRMEZCUXp0blFrRkRkRUlzUTBGQlF5eERRVUZETzNGQ1FVTkVMRVZCUVVVc1EwRkJReXh0UWtGQmJVSXNSVUZCUlN4bFFVRk5MRU5CUVVNc1QwRkJUeXhEUVVGRExFTkJRVU03WVVGRGFFUTdXVUZGUkN4SlFVRkpMRU5CUVVNc1UwRkJVeXhEUVVGRExFMUJRVTA3WjBKQlFVVXNUMEZCVHl4SlFVRkpMRU5CUVVNN1dVRkhia01zU1VGQlNUdHBRa0ZGUXl4SlFVRkpMRU5CUVVNc1NVRkJTU3hEUVVGRExFTkJRVU03VVVGRGNFSXNRMEZCUXl4RFFVRkJPenRKUVVOTUxFTkJRVU03U1VGeVEwUXNjME5CUVU4c1IwRkJVQ3hWUVVGUkxFTkJRVkU3VVVGRFdpeEpRVUZKTEU5QlFVOHNSMEZCUnl4RlFVRkZMRWxCUVVrc1JVRkJSU3hyUWtGQlV5eERRVUZETEVOQlFVTXNRMEZCUXl4SlFVRkpMRU5CUVVNc1JVRkJSU3hMUVVGTExFVkJRVVVzUTBGQlF5eERRVUZETEV0QlFVc3NSVUZCUlN4TlFVRk5MRVZCUVVVc1EwRkJReXhEUVVGRExFMUJRVTBzUlVGQlJTeERRVUZETzFGQlF6VkZMRWxCUVVrc1EwRkJReXhMUVVGTExFTkJRVU1zVDBGQlR5eERRVUZETEVsQlFVa3NRMEZCUXl4RFFVRkRMRTlCUVU4c1EwRkJReXhEUVVGRE8wbEJRM1JETEVOQlFVTTdTVUZIUkN4dFEwRkJTU3hIUVVGS08xRkJRVUVzYVVKQlJVTTdVVUZFUnl4RlFVRkZMRU5CUVVNc1MwRkJTeXhEUVVGRExHTkJRVTBzVDBGQlFTeHBRa0ZCVFN4SlFVRkpMRmxCUVVVc1JVRkJXaXhEUVVGWkxFTkJRVU1zUTBGQlF6dEpRVU5xUXl4RFFVRkRPMGxCWjBORUxHbERRVUZGTEVkQlFVWXNWVUZCUnl4VFFVRTJRaXhGUVVGRkxGRkJRVzlDTzFGQlEyeEVMRWxCUVVrc1QwRkJUeXhUUVVGVExFdEJRVXNzVVVGQlVTeEZRVUZGTzFsQlF5OUNMRWxCUVVrc1EwRkJReXhMUVVGTExFTkJRVU1zUlVGQlJTeERRVUZETEZOQlFWTXNSVUZCUlN4UlFVRlJMRU5CUVVNc1EwRkJRenRUUVVOMFF6dGhRVUZOTzFsQlEwZ3NTVUZCU1N4RFFVRkRMRXRCUVVzc1EwRkJReXhGUVVGRkxFTkJRVU1zYTBKQlFWTXNRMEZCUXl4VFFVRlRMRU5CUVVNc1JVRkJSU3hSUVVGUkxFTkJRVU1zUTBGQlF6dFRRVU5xUkR0UlFVTkVMRTlCUVU4c1NVRkJTU3hEUVVGRE8wbEJRMmhDTEVOQlFVTTdTVUZEVEN3eVFrRkJRenRCUVVGRUxFTkJRVU1zUVVGdVJFUXNRMEZCTUVNc1pVRkJUU3hIUVcxRUwwTTdRVUZ1UkZrc2IwUkJRVzlDTzBGQmFVVnFReXhUUVVGblFpeFRRVUZUTzBsQlEzSkNMRTlCUVU4c1NVRkJTU3h2UWtGQmIwSXNSVUZCUlN4RFFVRkRPMEZCUTNSRExFTkJRVU03UVVGR1JDdzRRa0ZGUXlKOSIsIlwidXNlIHN0cmljdFwiO1xyXG52YXIgX19leHRlbmRzID0gKHRoaXMgJiYgdGhpcy5fX2V4dGVuZHMpIHx8IChmdW5jdGlvbiAoKSB7XHJcbiAgICB2YXIgZXh0ZW5kU3RhdGljcyA9IGZ1bmN0aW9uIChkLCBiKSB7XHJcbiAgICAgICAgZXh0ZW5kU3RhdGljcyA9IE9iamVjdC5zZXRQcm90b3R5cGVPZiB8fFxyXG4gICAgICAgICAgICAoeyBfX3Byb3RvX186IFtdIH0gaW5zdGFuY2VvZiBBcnJheSAmJiBmdW5jdGlvbiAoZCwgYikgeyBkLl9fcHJvdG9fXyA9IGI7IH0pIHx8XHJcbiAgICAgICAgICAgIGZ1bmN0aW9uIChkLCBiKSB7IGZvciAodmFyIHAgaW4gYikgaWYgKGIuaGFzT3duUHJvcGVydHkocCkpIGRbcF0gPSBiW3BdOyB9O1xyXG4gICAgICAgIHJldHVybiBleHRlbmRTdGF0aWNzKGQsIGIpO1xyXG4gICAgfTtcclxuICAgIHJldHVybiBmdW5jdGlvbiAoZCwgYikge1xyXG4gICAgICAgIGV4dGVuZFN0YXRpY3MoZCwgYik7XHJcbiAgICAgICAgZnVuY3Rpb24gX18oKSB7IHRoaXMuY29uc3RydWN0b3IgPSBkOyB9XHJcbiAgICAgICAgZC5wcm90b3R5cGUgPSBiID09PSBudWxsID8gT2JqZWN0LmNyZWF0ZShiKSA6IChfXy5wcm90b3R5cGUgPSBiLnByb3RvdHlwZSwgbmV3IF9fKCkpO1xyXG4gICAgfTtcclxufSkoKTtcclxuT2JqZWN0LmRlZmluZVByb3BlcnR5KGV4cG9ydHMsIFwiX19lc01vZHVsZVwiLCB7IHZhbHVlOiB0cnVlIH0pO1xyXG52YXIgbGF5b3V0XzEgPSByZXF1aXJlKFwiLi9sYXlvdXRcIik7XHJcbnZhciBEM1N0eWxlTGF5b3V0QWRhcHRvciA9IChmdW5jdGlvbiAoX3N1cGVyKSB7XHJcbiAgICBfX2V4dGVuZHMoRDNTdHlsZUxheW91dEFkYXB0b3IsIF9zdXBlcik7XHJcbiAgICBmdW5jdGlvbiBEM1N0eWxlTGF5b3V0QWRhcHRvcihkM0NvbnRleHQpIHtcclxuICAgICAgICB2YXIgX3RoaXMgPSBfc3VwZXIuY2FsbCh0aGlzKSB8fCB0aGlzO1xyXG4gICAgICAgIF90aGlzLmQzQ29udGV4dCA9IGQzQ29udGV4dDtcclxuICAgICAgICBfdGhpcy5ldmVudCA9IGQzQ29udGV4dC5kaXNwYXRjaChsYXlvdXRfMS5FdmVudFR5cGVbbGF5b3V0XzEuRXZlbnRUeXBlLnN0YXJ0XSwgbGF5b3V0XzEuRXZlbnRUeXBlW2xheW91dF8xLkV2ZW50VHlwZS50aWNrXSwgbGF5b3V0XzEuRXZlbnRUeXBlW2xheW91dF8xLkV2ZW50VHlwZS5lbmRdKTtcclxuICAgICAgICB2YXIgZDNsYXlvdXQgPSBfdGhpcztcclxuICAgICAgICB2YXIgZHJhZztcclxuICAgICAgICBfdGhpcy5kcmFnID0gZnVuY3Rpb24gKCkge1xyXG4gICAgICAgICAgICBpZiAoIWRyYWcpIHtcclxuICAgICAgICAgICAgICAgIHZhciBkcmFnID0gZDNDb250ZXh0LmRyYWcoKVxyXG4gICAgICAgICAgICAgICAgICAgIC5zdWJqZWN0KGxheW91dF8xLkxheW91dC5kcmFnT3JpZ2luKVxyXG4gICAgICAgICAgICAgICAgICAgIC5vbihcInN0YXJ0LmQzYWRhcHRvclwiLCBsYXlvdXRfMS5MYXlvdXQuZHJhZ1N0YXJ0KVxyXG4gICAgICAgICAgICAgICAgICAgIC5vbihcImRyYWcuZDNhZGFwdG9yXCIsIGZ1bmN0aW9uIChkKSB7XHJcbiAgICAgICAgICAgICAgICAgICAgbGF5b3V0XzEuTGF5b3V0LmRyYWcoZCwgZDNDb250ZXh0LmV2ZW50KTtcclxuICAgICAgICAgICAgICAgICAgICBkM2xheW91dC5yZXN1bWUoKTtcclxuICAgICAgICAgICAgICAgIH0pXHJcbiAgICAgICAgICAgICAgICAgICAgLm9uKFwiZW5kLmQzYWRhcHRvclwiLCBsYXlvdXRfMS5MYXlvdXQuZHJhZ0VuZCk7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgaWYgKCFhcmd1bWVudHMubGVuZ3RoKVxyXG4gICAgICAgICAgICAgICAgcmV0dXJuIGRyYWc7XHJcbiAgICAgICAgICAgIGFyZ3VtZW50c1swXS5jYWxsKGRyYWcpO1xyXG4gICAgICAgIH07XHJcbiAgICAgICAgcmV0dXJuIF90aGlzO1xyXG4gICAgfVxyXG4gICAgRDNTdHlsZUxheW91dEFkYXB0b3IucHJvdG90eXBlLnRyaWdnZXIgPSBmdW5jdGlvbiAoZSkge1xyXG4gICAgICAgIHZhciBkM2V2ZW50ID0geyB0eXBlOiBsYXlvdXRfMS5FdmVudFR5cGVbZS50eXBlXSwgYWxwaGE6IGUuYWxwaGEsIHN0cmVzczogZS5zdHJlc3MgfTtcclxuICAgICAgICB0aGlzLmV2ZW50LmNhbGwoZDNldmVudC50eXBlLCBkM2V2ZW50KTtcclxuICAgIH07XHJcbiAgICBEM1N0eWxlTGF5b3V0QWRhcHRvci5wcm90b3R5cGUua2ljayA9IGZ1bmN0aW9uICgpIHtcclxuICAgICAgICB2YXIgX3RoaXMgPSB0aGlzO1xyXG4gICAgICAgIHZhciB0ID0gdGhpcy5kM0NvbnRleHQudGltZXIoZnVuY3Rpb24gKCkgeyByZXR1cm4gX3N1cGVyLnByb3RvdHlwZS50aWNrLmNhbGwoX3RoaXMpICYmIHQuc3RvcCgpOyB9KTtcclxuICAgIH07XHJcbiAgICBEM1N0eWxlTGF5b3V0QWRhcHRvci5wcm90b3R5cGUub24gPSBmdW5jdGlvbiAoZXZlbnRUeXBlLCBsaXN0ZW5lcikge1xyXG4gICAgICAgIGlmICh0eXBlb2YgZXZlbnRUeXBlID09PSAnc3RyaW5nJykge1xyXG4gICAgICAgICAgICB0aGlzLmV2ZW50Lm9uKGV2ZW50VHlwZSwgbGlzdGVuZXIpO1xyXG4gICAgICAgIH1cclxuICAgICAgICBlbHNlIHtcclxuICAgICAgICAgICAgdGhpcy5ldmVudC5vbihsYXlvdXRfMS5FdmVudFR5cGVbZXZlbnRUeXBlXSwgbGlzdGVuZXIpO1xyXG4gICAgICAgIH1cclxuICAgICAgICByZXR1cm4gdGhpcztcclxuICAgIH07XHJcbiAgICByZXR1cm4gRDNTdHlsZUxheW91dEFkYXB0b3I7XHJcbn0obGF5b3V0XzEuTGF5b3V0KSk7XHJcbmV4cG9ydHMuRDNTdHlsZUxheW91dEFkYXB0b3IgPSBEM1N0eWxlTGF5b3V0QWRhcHRvcjtcclxuLy8jIHNvdXJjZU1hcHBpbmdVUkw9ZGF0YTphcHBsaWNhdGlvbi9qc29uO2Jhc2U2NCxleUoyWlhKemFXOXVJam96TENKbWFXeGxJam9pWkROMk5HRmtZWEIwYjNJdWFuTWlMQ0p6YjNWeVkyVlNiMjkwSWpvaUlpd2ljMjkxY21ObGN5STZXeUl1TGk4dUxpOVhaV0pEYjJ4aEwzTnlZeTlrTTNZMFlXUmhjSFJ2Y2k1MGN5SmRMQ0p1WVcxbGN5STZXMTBzSW0xaGNIQnBibWR6SWpvaU96czdPenM3T3pzN096czdPenM3UVVGSFFTeHRRMEZCYVVRN1FVRlZha1E3U1VGQk1FTXNkME5CUVUwN1NVRnBRalZETERoQ1FVRnZRaXhUUVVGdlFqdFJRVUY0UXl4WlFVTkpMR2xDUVVGUExGTkJlVUpXTzFGQk1VSnRRaXhsUVVGVExFZEJRVlFzVTBGQlV5eERRVUZYTzFGQlJYQkRMRXRCUVVrc1EwRkJReXhMUVVGTExFZEJRVWNzVTBGQlV5eERRVUZETEZGQlFWRXNRMEZCUXl4clFrRkJVeXhEUVVGRExHdENRVUZUTEVOQlFVTXNTMEZCU3l4RFFVRkRMRVZCUVVVc2EwSkJRVk1zUTBGQlF5eHJRa0ZCVXl4RFFVRkRMRWxCUVVrc1EwRkJReXhGUVVGRkxHdENRVUZUTEVOQlFVTXNhMEpCUVZNc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETzFGQlIycElMRWxCUVVrc1VVRkJVU3hIUVVGSExFdEJRVWtzUTBGQlF6dFJRVU53UWl4SlFVRkpMRWxCUVVrc1EwRkJRenRSUVVOVUxFdEJRVWtzUTBGQlF5eEpRVUZKTEVkQlFVYzdXVUZEVWl4SlFVRkpMRU5CUVVNc1NVRkJTU3hGUVVGRk8yZENRVU5RTEVsQlFVa3NTVUZCU1N4SFFVRkhMRk5CUVZNc1EwRkJReXhKUVVGSkxFVkJRVVU3Y1VKQlEzUkNMRTlCUVU4c1EwRkJReXhsUVVGTkxFTkJRVU1zVlVGQlZTeERRVUZETzNGQ1FVTXhRaXhGUVVGRkxFTkJRVU1zYVVKQlFXbENMRVZCUVVVc1pVRkJUU3hEUVVGRExGTkJRVk1zUTBGQlF6dHhRa0ZEZGtNc1JVRkJSU3hEUVVGRExHZENRVUZuUWl4RlFVRkZMRlZCUVVFc1EwRkJRenR2UWtGRGJrSXNaVUZCVFN4RFFVRkRMRWxCUVVrc1EwRkJUU3hEUVVGRExFVkJRVVVzVTBGQlV5eERRVUZETEV0QlFVc3NRMEZCUXl4RFFVRkRPMjlDUVVOeVF5eFJRVUZSTEVOQlFVTXNUVUZCVFN4RlFVRkZMRU5CUVVNN1owSkJRM1JDTEVOQlFVTXNRMEZCUXp0eFFrRkRSQ3hGUVVGRkxFTkJRVU1zWlVGQlpTeEZRVUZGTEdWQlFVMHNRMEZCUXl4UFFVRlBMRU5CUVVNc1EwRkJRenRoUVVNMVF6dFpRVVZFTEVsQlFVa3NRMEZCUXl4VFFVRlRMRU5CUVVNc1RVRkJUVHRuUWtGQlJTeFBRVUZQTEVsQlFVa3NRMEZCUXp0WlFVdHVReXhUUVVGVExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNTVUZCU1N4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRE8xRkJRelZDTEVOQlFVTXNRMEZCUVRzN1NVRkRUQ3hEUVVGRE8wbEJla05FTEhORFFVRlBMRWRCUVZBc1ZVRkJVU3hEUVVGUk8xRkJRMW9zU1VGQlNTeFBRVUZQTEVkQlFVY3NSVUZCUlN4SlFVRkpMRVZCUVVVc2EwSkJRVk1zUTBGQlF5eERRVUZETEVOQlFVTXNTVUZCU1N4RFFVRkRMRVZCUVVVc1MwRkJTeXhGUVVGRkxFTkJRVU1zUTBGQlF5eExRVUZMTEVWQlFVVXNUVUZCVFN4RlFVRkZMRU5CUVVNc1EwRkJReXhOUVVGTkxFVkJRVVVzUTBGQlF6dFJRVWMxUlN4SlFVRkpMRU5CUVVNc1MwRkJTeXhEUVVGRExFbEJRVWtzUTBGQlF5eFBRVUZQTEVOQlFVTXNTVUZCU1N4RlFVRlBMRTlCUVU4c1EwRkJReXhEUVVGRE8wbEJRMmhFTEVOQlFVTTdTVUZIUkN4dFEwRkJTU3hIUVVGS08xRkJRVUVzYVVKQlJVTTdVVUZFUnl4SlFVRkpMRU5CUVVNc1IwRkJSeXhKUVVGSkxFTkJRVU1zVTBGQlV5eERRVUZETEV0QlFVc3NRMEZCUXl4alFVRk5MRTlCUVVFc2FVSkJRVTBzU1VGQlNTeFpRVUZGTEVsQlFVa3NRMEZCUXl4RFFVRkRMRWxCUVVrc1JVRkJSU3hGUVVGNFFpeERRVUYzUWl4RFFVRkRMRU5CUVVNN1NVRkRha1VzUTBGQlF6dEpRV3REUkN4cFEwRkJSU3hIUVVGR0xGVkJRVWNzVTBGQk5rSXNSVUZCUlN4UlFVRnZRanRSUVVOc1JDeEpRVUZKTEU5QlFVOHNVMEZCVXl4TFFVRkxMRkZCUVZFc1JVRkJSVHRaUVVNdlFpeEpRVUZKTEVOQlFVTXNTMEZCU3l4RFFVRkRMRVZCUVVVc1EwRkJReXhUUVVGVExFVkJRVVVzVVVGQlVTeERRVUZETEVOQlFVTTdVMEZEZEVNN1lVRkJUVHRaUVVOSUxFbEJRVWtzUTBGQlF5eExRVUZMTEVOQlFVTXNSVUZCUlN4RFFVRkRMR3RDUVVGVExFTkJRVU1zVTBGQlV5eERRVUZETEVWQlFVVXNVVUZCVVN4RFFVRkRMRU5CUVVNN1UwRkRha1E3VVVGRFJDeFBRVUZQTEVsQlFVa3NRMEZCUXp0SlFVTm9RaXhEUVVGRE8wbEJRMHdzTWtKQlFVTTdRVUZCUkN4RFFVRkRMRUZCZEVSRUxFTkJRVEJETEdWQlFVMHNSMEZ6UkM5RE8wRkJkRVJaTEc5RVFVRnZRaUo5IiwiXCJ1c2Ugc3RyaWN0XCI7XHJcbk9iamVjdC5kZWZpbmVQcm9wZXJ0eShleHBvcnRzLCBcIl9fZXNNb2R1bGVcIiwgeyB2YWx1ZTogdHJ1ZSB9KTtcclxudmFyIExvY2tzID0gKGZ1bmN0aW9uICgpIHtcclxuICAgIGZ1bmN0aW9uIExvY2tzKCkge1xyXG4gICAgICAgIHRoaXMubG9ja3MgPSB7fTtcclxuICAgIH1cclxuICAgIExvY2tzLnByb3RvdHlwZS5hZGQgPSBmdW5jdGlvbiAoaWQsIHgpIHtcclxuICAgICAgICB0aGlzLmxvY2tzW2lkXSA9IHg7XHJcbiAgICB9O1xyXG4gICAgTG9ja3MucHJvdG90eXBlLmNsZWFyID0gZnVuY3Rpb24gKCkge1xyXG4gICAgICAgIHRoaXMubG9ja3MgPSB7fTtcclxuICAgIH07XHJcbiAgICBMb2Nrcy5wcm90b3R5cGUuaXNFbXB0eSA9IGZ1bmN0aW9uICgpIHtcclxuICAgICAgICBmb3IgKHZhciBsIGluIHRoaXMubG9ja3MpXHJcbiAgICAgICAgICAgIHJldHVybiBmYWxzZTtcclxuICAgICAgICByZXR1cm4gdHJ1ZTtcclxuICAgIH07XHJcbiAgICBMb2Nrcy5wcm90b3R5cGUuYXBwbHkgPSBmdW5jdGlvbiAoZikge1xyXG4gICAgICAgIGZvciAodmFyIGwgaW4gdGhpcy5sb2Nrcykge1xyXG4gICAgICAgICAgICBmKE51bWJlcihsKSwgdGhpcy5sb2Nrc1tsXSk7XHJcbiAgICAgICAgfVxyXG4gICAgfTtcclxuICAgIHJldHVybiBMb2NrcztcclxufSgpKTtcclxuZXhwb3J0cy5Mb2NrcyA9IExvY2tzO1xyXG52YXIgRGVzY2VudCA9IChmdW5jdGlvbiAoKSB7XHJcbiAgICBmdW5jdGlvbiBEZXNjZW50KHgsIEQsIEcpIHtcclxuICAgICAgICBpZiAoRyA9PT0gdm9pZCAwKSB7IEcgPSBudWxsOyB9XHJcbiAgICAgICAgdGhpcy5EID0gRDtcclxuICAgICAgICB0aGlzLkcgPSBHO1xyXG4gICAgICAgIHRoaXMudGhyZXNob2xkID0gMC4wMDAxO1xyXG4gICAgICAgIHRoaXMubnVtR3JpZFNuYXBOb2RlcyA9IDA7XHJcbiAgICAgICAgdGhpcy5zbmFwR3JpZFNpemUgPSAxMDA7XHJcbiAgICAgICAgdGhpcy5zbmFwU3RyZW5ndGggPSAxMDAwO1xyXG4gICAgICAgIHRoaXMuc2NhbGVTbmFwQnlNYXhIID0gZmFsc2U7XHJcbiAgICAgICAgdGhpcy5yYW5kb20gPSBuZXcgUHNldWRvUmFuZG9tKCk7XHJcbiAgICAgICAgdGhpcy5wcm9qZWN0ID0gbnVsbDtcclxuICAgICAgICB0aGlzLnggPSB4O1xyXG4gICAgICAgIHRoaXMuayA9IHgubGVuZ3RoO1xyXG4gICAgICAgIHZhciBuID0gdGhpcy5uID0geFswXS5sZW5ndGg7XHJcbiAgICAgICAgdGhpcy5IID0gbmV3IEFycmF5KHRoaXMuayk7XHJcbiAgICAgICAgdGhpcy5nID0gbmV3IEFycmF5KHRoaXMuayk7XHJcbiAgICAgICAgdGhpcy5IZCA9IG5ldyBBcnJheSh0aGlzLmspO1xyXG4gICAgICAgIHRoaXMuYSA9IG5ldyBBcnJheSh0aGlzLmspO1xyXG4gICAgICAgIHRoaXMuYiA9IG5ldyBBcnJheSh0aGlzLmspO1xyXG4gICAgICAgIHRoaXMuYyA9IG5ldyBBcnJheSh0aGlzLmspO1xyXG4gICAgICAgIHRoaXMuZCA9IG5ldyBBcnJheSh0aGlzLmspO1xyXG4gICAgICAgIHRoaXMuZSA9IG5ldyBBcnJheSh0aGlzLmspO1xyXG4gICAgICAgIHRoaXMuaWEgPSBuZXcgQXJyYXkodGhpcy5rKTtcclxuICAgICAgICB0aGlzLmliID0gbmV3IEFycmF5KHRoaXMuayk7XHJcbiAgICAgICAgdGhpcy54dG1wID0gbmV3IEFycmF5KHRoaXMuayk7XHJcbiAgICAgICAgdGhpcy5sb2NrcyA9IG5ldyBMb2NrcygpO1xyXG4gICAgICAgIHRoaXMubWluRCA9IE51bWJlci5NQVhfVkFMVUU7XHJcbiAgICAgICAgdmFyIGkgPSBuLCBqO1xyXG4gICAgICAgIHdoaWxlIChpLS0pIHtcclxuICAgICAgICAgICAgaiA9IG47XHJcbiAgICAgICAgICAgIHdoaWxlICgtLWogPiBpKSB7XHJcbiAgICAgICAgICAgICAgICB2YXIgZCA9IERbaV1bal07XHJcbiAgICAgICAgICAgICAgICBpZiAoZCA+IDAgJiYgZCA8IHRoaXMubWluRCkge1xyXG4gICAgICAgICAgICAgICAgICAgIHRoaXMubWluRCA9IGQ7XHJcbiAgICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICB9XHJcbiAgICAgICAgaWYgKHRoaXMubWluRCA9PT0gTnVtYmVyLk1BWF9WQUxVRSlcclxuICAgICAgICAgICAgdGhpcy5taW5EID0gMTtcclxuICAgICAgICBpID0gdGhpcy5rO1xyXG4gICAgICAgIHdoaWxlIChpLS0pIHtcclxuICAgICAgICAgICAgdGhpcy5nW2ldID0gbmV3IEFycmF5KG4pO1xyXG4gICAgICAgICAgICB0aGlzLkhbaV0gPSBuZXcgQXJyYXkobik7XHJcbiAgICAgICAgICAgIGogPSBuO1xyXG4gICAgICAgICAgICB3aGlsZSAoai0tKSB7XHJcbiAgICAgICAgICAgICAgICB0aGlzLkhbaV1bal0gPSBuZXcgQXJyYXkobik7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgdGhpcy5IZFtpXSA9IG5ldyBBcnJheShuKTtcclxuICAgICAgICAgICAgdGhpcy5hW2ldID0gbmV3IEFycmF5KG4pO1xyXG4gICAgICAgICAgICB0aGlzLmJbaV0gPSBuZXcgQXJyYXkobik7XHJcbiAgICAgICAgICAgIHRoaXMuY1tpXSA9IG5ldyBBcnJheShuKTtcclxuICAgICAgICAgICAgdGhpcy5kW2ldID0gbmV3IEFycmF5KG4pO1xyXG4gICAgICAgICAgICB0aGlzLmVbaV0gPSBuZXcgQXJyYXkobik7XHJcbiAgICAgICAgICAgIHRoaXMuaWFbaV0gPSBuZXcgQXJyYXkobik7XHJcbiAgICAgICAgICAgIHRoaXMuaWJbaV0gPSBuZXcgQXJyYXkobik7XHJcbiAgICAgICAgICAgIHRoaXMueHRtcFtpXSA9IG5ldyBBcnJheShuKTtcclxuICAgICAgICB9XHJcbiAgICB9XHJcbiAgICBEZXNjZW50LmNyZWF0ZVNxdWFyZU1hdHJpeCA9IGZ1bmN0aW9uIChuLCBmKSB7XHJcbiAgICAgICAgdmFyIE0gPSBuZXcgQXJyYXkobik7XHJcbiAgICAgICAgZm9yICh2YXIgaSA9IDA7IGkgPCBuOyArK2kpIHtcclxuICAgICAgICAgICAgTVtpXSA9IG5ldyBBcnJheShuKTtcclxuICAgICAgICAgICAgZm9yICh2YXIgaiA9IDA7IGogPCBuOyArK2opIHtcclxuICAgICAgICAgICAgICAgIE1baV1bal0gPSBmKGksIGopO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgfVxyXG4gICAgICAgIHJldHVybiBNO1xyXG4gICAgfTtcclxuICAgIERlc2NlbnQucHJvdG90eXBlLm9mZnNldERpciA9IGZ1bmN0aW9uICgpIHtcclxuICAgICAgICB2YXIgX3RoaXMgPSB0aGlzO1xyXG4gICAgICAgIHZhciB1ID0gbmV3IEFycmF5KHRoaXMuayk7XHJcbiAgICAgICAgdmFyIGwgPSAwO1xyXG4gICAgICAgIGZvciAodmFyIGkgPSAwOyBpIDwgdGhpcy5rOyArK2kpIHtcclxuICAgICAgICAgICAgdmFyIHggPSB1W2ldID0gdGhpcy5yYW5kb20uZ2V0TmV4dEJldHdlZW4oMC4wMSwgMSkgLSAwLjU7XHJcbiAgICAgICAgICAgIGwgKz0geCAqIHg7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIGwgPSBNYXRoLnNxcnQobCk7XHJcbiAgICAgICAgcmV0dXJuIHUubWFwKGZ1bmN0aW9uICh4KSB7IHJldHVybiB4ICo9IF90aGlzLm1pbkQgLyBsOyB9KTtcclxuICAgIH07XHJcbiAgICBEZXNjZW50LnByb3RvdHlwZS5jb21wdXRlRGVyaXZhdGl2ZXMgPSBmdW5jdGlvbiAoeCkge1xyXG4gICAgICAgIHZhciBfdGhpcyA9IHRoaXM7XHJcbiAgICAgICAgdmFyIG4gPSB0aGlzLm47XHJcbiAgICAgICAgaWYgKG4gPCAxKVxyXG4gICAgICAgICAgICByZXR1cm47XHJcbiAgICAgICAgdmFyIGk7XHJcbiAgICAgICAgdmFyIGQgPSBuZXcgQXJyYXkodGhpcy5rKTtcclxuICAgICAgICB2YXIgZDIgPSBuZXcgQXJyYXkodGhpcy5rKTtcclxuICAgICAgICB2YXIgSHV1ID0gbmV3IEFycmF5KHRoaXMuayk7XHJcbiAgICAgICAgdmFyIG1heEggPSAwO1xyXG4gICAgICAgIGZvciAodmFyIHVfMSA9IDA7IHVfMSA8IG47ICsrdV8xKSB7XHJcbiAgICAgICAgICAgIGZvciAoaSA9IDA7IGkgPCB0aGlzLms7ICsraSlcclxuICAgICAgICAgICAgICAgIEh1dVtpXSA9IHRoaXMuZ1tpXVt1XzFdID0gMDtcclxuICAgICAgICAgICAgZm9yICh2YXIgdiA9IDA7IHYgPCBuOyArK3YpIHtcclxuICAgICAgICAgICAgICAgIGlmICh1XzEgPT09IHYpXHJcbiAgICAgICAgICAgICAgICAgICAgY29udGludWU7XHJcbiAgICAgICAgICAgICAgICB2YXIgbWF4RGlzcGxhY2VzID0gbjtcclxuICAgICAgICAgICAgICAgIHZhciBkaXN0YW5jZVNxdWFyZWQgPSAwO1xyXG4gICAgICAgICAgICAgICAgd2hpbGUgKG1heERpc3BsYWNlcy0tKSB7XHJcbiAgICAgICAgICAgICAgICAgICAgZGlzdGFuY2VTcXVhcmVkID0gMDtcclxuICAgICAgICAgICAgICAgICAgICBmb3IgKGkgPSAwOyBpIDwgdGhpcy5rOyArK2kpIHtcclxuICAgICAgICAgICAgICAgICAgICAgICAgdmFyIGR4XzEgPSBkW2ldID0geFtpXVt1XzFdIC0geFtpXVt2XTtcclxuICAgICAgICAgICAgICAgICAgICAgICAgZGlzdGFuY2VTcXVhcmVkICs9IGQyW2ldID0gZHhfMSAqIGR4XzE7XHJcbiAgICAgICAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICAgICAgICAgIGlmIChkaXN0YW5jZVNxdWFyZWQgPiAxZS05KVxyXG4gICAgICAgICAgICAgICAgICAgICAgICBicmVhaztcclxuICAgICAgICAgICAgICAgICAgICB2YXIgcmQgPSB0aGlzLm9mZnNldERpcigpO1xyXG4gICAgICAgICAgICAgICAgICAgIGZvciAoaSA9IDA7IGkgPCB0aGlzLms7ICsraSlcclxuICAgICAgICAgICAgICAgICAgICAgICAgeFtpXVt2XSArPSByZFtpXTtcclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgIHZhciBkaXN0YW5jZSA9IE1hdGguc3FydChkaXN0YW5jZVNxdWFyZWQpO1xyXG4gICAgICAgICAgICAgICAgdmFyIGlkZWFsRGlzdGFuY2UgPSB0aGlzLkRbdV8xXVt2XTtcclxuICAgICAgICAgICAgICAgIHZhciB3ZWlnaHQgPSB0aGlzLkcgIT0gbnVsbCA/IHRoaXMuR1t1XzFdW3ZdIDogMTtcclxuICAgICAgICAgICAgICAgIGlmICh3ZWlnaHQgPiAxICYmIGRpc3RhbmNlID4gaWRlYWxEaXN0YW5jZSB8fCAhaXNGaW5pdGUoaWRlYWxEaXN0YW5jZSkpIHtcclxuICAgICAgICAgICAgICAgICAgICBmb3IgKGkgPSAwOyBpIDwgdGhpcy5rOyArK2kpXHJcbiAgICAgICAgICAgICAgICAgICAgICAgIHRoaXMuSFtpXVt1XzFdW3ZdID0gMDtcclxuICAgICAgICAgICAgICAgICAgICBjb250aW51ZTtcclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgIGlmICh3ZWlnaHQgPiAxKSB7XHJcbiAgICAgICAgICAgICAgICAgICAgd2VpZ2h0ID0gMTtcclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgIHZhciBpZGVhbERpc3RTcXVhcmVkID0gaWRlYWxEaXN0YW5jZSAqIGlkZWFsRGlzdGFuY2UsIGdzID0gMiAqIHdlaWdodCAqIChkaXN0YW5jZSAtIGlkZWFsRGlzdGFuY2UpIC8gKGlkZWFsRGlzdFNxdWFyZWQgKiBkaXN0YW5jZSksIGRpc3RhbmNlQ3ViZWQgPSBkaXN0YW5jZVNxdWFyZWQgKiBkaXN0YW5jZSwgaHMgPSAyICogLXdlaWdodCAvIChpZGVhbERpc3RTcXVhcmVkICogZGlzdGFuY2VDdWJlZCk7XHJcbiAgICAgICAgICAgICAgICBpZiAoIWlzRmluaXRlKGdzKSlcclxuICAgICAgICAgICAgICAgICAgICBjb25zb2xlLmxvZyhncyk7XHJcbiAgICAgICAgICAgICAgICBmb3IgKGkgPSAwOyBpIDwgdGhpcy5rOyArK2kpIHtcclxuICAgICAgICAgICAgICAgICAgICB0aGlzLmdbaV1bdV8xXSArPSBkW2ldICogZ3M7XHJcbiAgICAgICAgICAgICAgICAgICAgSHV1W2ldIC09IHRoaXMuSFtpXVt1XzFdW3ZdID0gaHMgKiAoMiAqIGRpc3RhbmNlQ3ViZWQgKyBpZGVhbERpc3RhbmNlICogKGQyW2ldIC0gZGlzdGFuY2VTcXVhcmVkKSk7XHJcbiAgICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgZm9yIChpID0gMDsgaSA8IHRoaXMuazsgKytpKVxyXG4gICAgICAgICAgICAgICAgbWF4SCA9IE1hdGgubWF4KG1heEgsIHRoaXMuSFtpXVt1XzFdW3VfMV0gPSBIdXVbaV0pO1xyXG4gICAgICAgIH1cclxuICAgICAgICB2YXIgciA9IHRoaXMuc25hcEdyaWRTaXplIC8gMjtcclxuICAgICAgICB2YXIgZyA9IHRoaXMuc25hcEdyaWRTaXplO1xyXG4gICAgICAgIHZhciB3ID0gdGhpcy5zbmFwU3RyZW5ndGg7XHJcbiAgICAgICAgdmFyIGsgPSB3IC8gKHIgKiByKTtcclxuICAgICAgICB2YXIgbnVtTm9kZXMgPSB0aGlzLm51bUdyaWRTbmFwTm9kZXM7XHJcbiAgICAgICAgZm9yICh2YXIgdSA9IDA7IHUgPCBudW1Ob2RlczsgKyt1KSB7XHJcbiAgICAgICAgICAgIGZvciAoaSA9IDA7IGkgPCB0aGlzLms7ICsraSkge1xyXG4gICAgICAgICAgICAgICAgdmFyIHhpdSA9IHRoaXMueFtpXVt1XTtcclxuICAgICAgICAgICAgICAgIHZhciBtID0geGl1IC8gZztcclxuICAgICAgICAgICAgICAgIHZhciBmID0gbSAlIDE7XHJcbiAgICAgICAgICAgICAgICB2YXIgcSA9IG0gLSBmO1xyXG4gICAgICAgICAgICAgICAgdmFyIGEgPSBNYXRoLmFicyhmKTtcclxuICAgICAgICAgICAgICAgIHZhciBkeCA9IChhIDw9IDAuNSkgPyB4aXUgLSBxICogZyA6XHJcbiAgICAgICAgICAgICAgICAgICAgKHhpdSA+IDApID8geGl1IC0gKHEgKyAxKSAqIGcgOiB4aXUgLSAocSAtIDEpICogZztcclxuICAgICAgICAgICAgICAgIGlmICgtciA8IGR4ICYmIGR4IDw9IHIpIHtcclxuICAgICAgICAgICAgICAgICAgICBpZiAodGhpcy5zY2FsZVNuYXBCeU1heEgpIHtcclxuICAgICAgICAgICAgICAgICAgICAgICAgdGhpcy5nW2ldW3VdICs9IG1heEggKiBrICogZHg7XHJcbiAgICAgICAgICAgICAgICAgICAgICAgIHRoaXMuSFtpXVt1XVt1XSArPSBtYXhIICogaztcclxuICAgICAgICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgICAgICAgICAgZWxzZSB7XHJcbiAgICAgICAgICAgICAgICAgICAgICAgIHRoaXMuZ1tpXVt1XSArPSBrICogZHg7XHJcbiAgICAgICAgICAgICAgICAgICAgICAgIHRoaXMuSFtpXVt1XVt1XSArPSBrO1xyXG4gICAgICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgfVxyXG4gICAgICAgIH1cclxuICAgICAgICBpZiAoIXRoaXMubG9ja3MuaXNFbXB0eSgpKSB7XHJcbiAgICAgICAgICAgIHRoaXMubG9ja3MuYXBwbHkoZnVuY3Rpb24gKHUsIHApIHtcclxuICAgICAgICAgICAgICAgIGZvciAoaSA9IDA7IGkgPCBfdGhpcy5rOyArK2kpIHtcclxuICAgICAgICAgICAgICAgICAgICBfdGhpcy5IW2ldW3VdW3VdICs9IG1heEg7XHJcbiAgICAgICAgICAgICAgICAgICAgX3RoaXMuZ1tpXVt1XSAtPSBtYXhIICogKHBbaV0gLSB4W2ldW3VdKTtcclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgfSk7XHJcbiAgICAgICAgfVxyXG4gICAgfTtcclxuICAgIERlc2NlbnQuZG90UHJvZCA9IGZ1bmN0aW9uIChhLCBiKSB7XHJcbiAgICAgICAgdmFyIHggPSAwLCBpID0gYS5sZW5ndGg7XHJcbiAgICAgICAgd2hpbGUgKGktLSlcclxuICAgICAgICAgICAgeCArPSBhW2ldICogYltpXTtcclxuICAgICAgICByZXR1cm4geDtcclxuICAgIH07XHJcbiAgICBEZXNjZW50LnJpZ2h0TXVsdGlwbHkgPSBmdW5jdGlvbiAobSwgdiwgcikge1xyXG4gICAgICAgIHZhciBpID0gbS5sZW5ndGg7XHJcbiAgICAgICAgd2hpbGUgKGktLSlcclxuICAgICAgICAgICAgcltpXSA9IERlc2NlbnQuZG90UHJvZChtW2ldLCB2KTtcclxuICAgIH07XHJcbiAgICBEZXNjZW50LnByb3RvdHlwZS5jb21wdXRlU3RlcFNpemUgPSBmdW5jdGlvbiAoZCkge1xyXG4gICAgICAgIHZhciBudW1lcmF0b3IgPSAwLCBkZW5vbWluYXRvciA9IDA7XHJcbiAgICAgICAgZm9yICh2YXIgaSA9IDA7IGkgPCB0aGlzLms7ICsraSkge1xyXG4gICAgICAgICAgICBudW1lcmF0b3IgKz0gRGVzY2VudC5kb3RQcm9kKHRoaXMuZ1tpXSwgZFtpXSk7XHJcbiAgICAgICAgICAgIERlc2NlbnQucmlnaHRNdWx0aXBseSh0aGlzLkhbaV0sIGRbaV0sIHRoaXMuSGRbaV0pO1xyXG4gICAgICAgICAgICBkZW5vbWluYXRvciArPSBEZXNjZW50LmRvdFByb2QoZFtpXSwgdGhpcy5IZFtpXSk7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIGlmIChkZW5vbWluYXRvciA9PT0gMCB8fCAhaXNGaW5pdGUoZGVub21pbmF0b3IpKVxyXG4gICAgICAgICAgICByZXR1cm4gMDtcclxuICAgICAgICByZXR1cm4gMSAqIG51bWVyYXRvciAvIGRlbm9taW5hdG9yO1xyXG4gICAgfTtcclxuICAgIERlc2NlbnQucHJvdG90eXBlLnJlZHVjZVN0cmVzcyA9IGZ1bmN0aW9uICgpIHtcclxuICAgICAgICB0aGlzLmNvbXB1dGVEZXJpdmF0aXZlcyh0aGlzLngpO1xyXG4gICAgICAgIHZhciBhbHBoYSA9IHRoaXMuY29tcHV0ZVN0ZXBTaXplKHRoaXMuZyk7XHJcbiAgICAgICAgZm9yICh2YXIgaSA9IDA7IGkgPCB0aGlzLms7ICsraSkge1xyXG4gICAgICAgICAgICB0aGlzLnRha2VEZXNjZW50U3RlcCh0aGlzLnhbaV0sIHRoaXMuZ1tpXSwgYWxwaGEpO1xyXG4gICAgICAgIH1cclxuICAgICAgICByZXR1cm4gdGhpcy5jb21wdXRlU3RyZXNzKCk7XHJcbiAgICB9O1xyXG4gICAgRGVzY2VudC5jb3B5ID0gZnVuY3Rpb24gKGEsIGIpIHtcclxuICAgICAgICB2YXIgbSA9IGEubGVuZ3RoLCBuID0gYlswXS5sZW5ndGg7XHJcbiAgICAgICAgZm9yICh2YXIgaSA9IDA7IGkgPCBtOyArK2kpIHtcclxuICAgICAgICAgICAgZm9yICh2YXIgaiA9IDA7IGogPCBuOyArK2opIHtcclxuICAgICAgICAgICAgICAgIGJbaV1bal0gPSBhW2ldW2pdO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgfVxyXG4gICAgfTtcclxuICAgIERlc2NlbnQucHJvdG90eXBlLnN0ZXBBbmRQcm9qZWN0ID0gZnVuY3Rpb24gKHgwLCByLCBkLCBzdGVwU2l6ZSkge1xyXG4gICAgICAgIERlc2NlbnQuY29weSh4MCwgcik7XHJcbiAgICAgICAgdGhpcy50YWtlRGVzY2VudFN0ZXAoclswXSwgZFswXSwgc3RlcFNpemUpO1xyXG4gICAgICAgIGlmICh0aGlzLnByb2plY3QpXHJcbiAgICAgICAgICAgIHRoaXMucHJvamVjdFswXSh4MFswXSwgeDBbMV0sIHJbMF0pO1xyXG4gICAgICAgIHRoaXMudGFrZURlc2NlbnRTdGVwKHJbMV0sIGRbMV0sIHN0ZXBTaXplKTtcclxuICAgICAgICBpZiAodGhpcy5wcm9qZWN0KVxyXG4gICAgICAgICAgICB0aGlzLnByb2plY3RbMV0oclswXSwgeDBbMV0sIHJbMV0pO1xyXG4gICAgICAgIGZvciAodmFyIGkgPSAyOyBpIDwgdGhpcy5rOyBpKyspXHJcbiAgICAgICAgICAgIHRoaXMudGFrZURlc2NlbnRTdGVwKHJbaV0sIGRbaV0sIHN0ZXBTaXplKTtcclxuICAgIH07XHJcbiAgICBEZXNjZW50Lm1BcHBseSA9IGZ1bmN0aW9uIChtLCBuLCBmKSB7XHJcbiAgICAgICAgdmFyIGkgPSBtO1xyXG4gICAgICAgIHdoaWxlIChpLS0gPiAwKSB7XHJcbiAgICAgICAgICAgIHZhciBqID0gbjtcclxuICAgICAgICAgICAgd2hpbGUgKGotLSA+IDApXHJcbiAgICAgICAgICAgICAgICBmKGksIGopO1xyXG4gICAgICAgIH1cclxuICAgIH07XHJcbiAgICBEZXNjZW50LnByb3RvdHlwZS5tYXRyaXhBcHBseSA9IGZ1bmN0aW9uIChmKSB7XHJcbiAgICAgICAgRGVzY2VudC5tQXBwbHkodGhpcy5rLCB0aGlzLm4sIGYpO1xyXG4gICAgfTtcclxuICAgIERlc2NlbnQucHJvdG90eXBlLmNvbXB1dGVOZXh0UG9zaXRpb24gPSBmdW5jdGlvbiAoeDAsIHIpIHtcclxuICAgICAgICB2YXIgX3RoaXMgPSB0aGlzO1xyXG4gICAgICAgIHRoaXMuY29tcHV0ZURlcml2YXRpdmVzKHgwKTtcclxuICAgICAgICB2YXIgYWxwaGEgPSB0aGlzLmNvbXB1dGVTdGVwU2l6ZSh0aGlzLmcpO1xyXG4gICAgICAgIHRoaXMuc3RlcEFuZFByb2plY3QoeDAsIHIsIHRoaXMuZywgYWxwaGEpO1xyXG4gICAgICAgIGlmICh0aGlzLnByb2plY3QpIHtcclxuICAgICAgICAgICAgdGhpcy5tYXRyaXhBcHBseShmdW5jdGlvbiAoaSwgaikgeyByZXR1cm4gX3RoaXMuZVtpXVtqXSA9IHgwW2ldW2pdIC0gcltpXVtqXTsgfSk7XHJcbiAgICAgICAgICAgIHZhciBiZXRhID0gdGhpcy5jb21wdXRlU3RlcFNpemUodGhpcy5lKTtcclxuICAgICAgICAgICAgYmV0YSA9IE1hdGgubWF4KDAuMiwgTWF0aC5taW4oYmV0YSwgMSkpO1xyXG4gICAgICAgICAgICB0aGlzLnN0ZXBBbmRQcm9qZWN0KHgwLCByLCB0aGlzLmUsIGJldGEpO1xyXG4gICAgICAgIH1cclxuICAgIH07XHJcbiAgICBEZXNjZW50LnByb3RvdHlwZS5ydW4gPSBmdW5jdGlvbiAoaXRlcmF0aW9ucykge1xyXG4gICAgICAgIHZhciBzdHJlc3MgPSBOdW1iZXIuTUFYX1ZBTFVFLCBjb252ZXJnZWQgPSBmYWxzZTtcclxuICAgICAgICB3aGlsZSAoIWNvbnZlcmdlZCAmJiBpdGVyYXRpb25zLS0gPiAwKSB7XHJcbiAgICAgICAgICAgIHZhciBzID0gdGhpcy5ydW5nZUt1dHRhKCk7XHJcbiAgICAgICAgICAgIGNvbnZlcmdlZCA9IE1hdGguYWJzKHN0cmVzcyAvIHMgLSAxKSA8IHRoaXMudGhyZXNob2xkO1xyXG4gICAgICAgICAgICBzdHJlc3MgPSBzO1xyXG4gICAgICAgIH1cclxuICAgICAgICByZXR1cm4gc3RyZXNzO1xyXG4gICAgfTtcclxuICAgIERlc2NlbnQucHJvdG90eXBlLnJ1bmdlS3V0dGEgPSBmdW5jdGlvbiAoKSB7XHJcbiAgICAgICAgdmFyIF90aGlzID0gdGhpcztcclxuICAgICAgICB0aGlzLmNvbXB1dGVOZXh0UG9zaXRpb24odGhpcy54LCB0aGlzLmEpO1xyXG4gICAgICAgIERlc2NlbnQubWlkKHRoaXMueCwgdGhpcy5hLCB0aGlzLmlhKTtcclxuICAgICAgICB0aGlzLmNvbXB1dGVOZXh0UG9zaXRpb24odGhpcy5pYSwgdGhpcy5iKTtcclxuICAgICAgICBEZXNjZW50Lm1pZCh0aGlzLngsIHRoaXMuYiwgdGhpcy5pYik7XHJcbiAgICAgICAgdGhpcy5jb21wdXRlTmV4dFBvc2l0aW9uKHRoaXMuaWIsIHRoaXMuYyk7XHJcbiAgICAgICAgdGhpcy5jb21wdXRlTmV4dFBvc2l0aW9uKHRoaXMuYywgdGhpcy5kKTtcclxuICAgICAgICB2YXIgZGlzcCA9IDA7XHJcbiAgICAgICAgdGhpcy5tYXRyaXhBcHBseShmdW5jdGlvbiAoaSwgaikge1xyXG4gICAgICAgICAgICB2YXIgeCA9IChfdGhpcy5hW2ldW2pdICsgMi4wICogX3RoaXMuYltpXVtqXSArIDIuMCAqIF90aGlzLmNbaV1bal0gKyBfdGhpcy5kW2ldW2pdKSAvIDYuMCwgZCA9IF90aGlzLnhbaV1bal0gLSB4O1xyXG4gICAgICAgICAgICBkaXNwICs9IGQgKiBkO1xyXG4gICAgICAgICAgICBfdGhpcy54W2ldW2pdID0geDtcclxuICAgICAgICB9KTtcclxuICAgICAgICByZXR1cm4gZGlzcDtcclxuICAgIH07XHJcbiAgICBEZXNjZW50Lm1pZCA9IGZ1bmN0aW9uIChhLCBiLCBtKSB7XHJcbiAgICAgICAgRGVzY2VudC5tQXBwbHkoYS5sZW5ndGgsIGFbMF0ubGVuZ3RoLCBmdW5jdGlvbiAoaSwgaikge1xyXG4gICAgICAgICAgICByZXR1cm4gbVtpXVtqXSA9IGFbaV1bal0gKyAoYltpXVtqXSAtIGFbaV1bal0pIC8gMi4wO1xyXG4gICAgICAgIH0pO1xyXG4gICAgfTtcclxuICAgIERlc2NlbnQucHJvdG90eXBlLnRha2VEZXNjZW50U3RlcCA9IGZ1bmN0aW9uICh4LCBkLCBzdGVwU2l6ZSkge1xyXG4gICAgICAgIGZvciAodmFyIGkgPSAwOyBpIDwgdGhpcy5uOyArK2kpIHtcclxuICAgICAgICAgICAgeFtpXSA9IHhbaV0gLSBzdGVwU2l6ZSAqIGRbaV07XHJcbiAgICAgICAgfVxyXG4gICAgfTtcclxuICAgIERlc2NlbnQucHJvdG90eXBlLmNvbXB1dGVTdHJlc3MgPSBmdW5jdGlvbiAoKSB7XHJcbiAgICAgICAgdmFyIHN0cmVzcyA9IDA7XHJcbiAgICAgICAgZm9yICh2YXIgdSA9IDAsIG5NaW51czEgPSB0aGlzLm4gLSAxOyB1IDwgbk1pbnVzMTsgKyt1KSB7XHJcbiAgICAgICAgICAgIGZvciAodmFyIHYgPSB1ICsgMSwgbiA9IHRoaXMubjsgdiA8IG47ICsrdikge1xyXG4gICAgICAgICAgICAgICAgdmFyIGwgPSAwO1xyXG4gICAgICAgICAgICAgICAgZm9yICh2YXIgaSA9IDA7IGkgPCB0aGlzLms7ICsraSkge1xyXG4gICAgICAgICAgICAgICAgICAgIHZhciBkeCA9IHRoaXMueFtpXVt1XSAtIHRoaXMueFtpXVt2XTtcclxuICAgICAgICAgICAgICAgICAgICBsICs9IGR4ICogZHg7XHJcbiAgICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgICAgICBsID0gTWF0aC5zcXJ0KGwpO1xyXG4gICAgICAgICAgICAgICAgdmFyIGQgPSB0aGlzLkRbdV1bdl07XHJcbiAgICAgICAgICAgICAgICBpZiAoIWlzRmluaXRlKGQpKVxyXG4gICAgICAgICAgICAgICAgICAgIGNvbnRpbnVlO1xyXG4gICAgICAgICAgICAgICAgdmFyIHJsID0gZCAtIGw7XHJcbiAgICAgICAgICAgICAgICB2YXIgZDIgPSBkICogZDtcclxuICAgICAgICAgICAgICAgIHN0cmVzcyArPSBybCAqIHJsIC8gZDI7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICB9XHJcbiAgICAgICAgcmV0dXJuIHN0cmVzcztcclxuICAgIH07XHJcbiAgICBEZXNjZW50Lnplcm9EaXN0YW5jZSA9IDFlLTEwO1xyXG4gICAgcmV0dXJuIERlc2NlbnQ7XHJcbn0oKSk7XHJcbmV4cG9ydHMuRGVzY2VudCA9IERlc2NlbnQ7XHJcbnZhciBQc2V1ZG9SYW5kb20gPSAoZnVuY3Rpb24gKCkge1xyXG4gICAgZnVuY3Rpb24gUHNldWRvUmFuZG9tKHNlZWQpIHtcclxuICAgICAgICBpZiAoc2VlZCA9PT0gdm9pZCAwKSB7IHNlZWQgPSAxOyB9XHJcbiAgICAgICAgdGhpcy5zZWVkID0gc2VlZDtcclxuICAgICAgICB0aGlzLmEgPSAyMTQwMTM7XHJcbiAgICAgICAgdGhpcy5jID0gMjUzMTAxMTtcclxuICAgICAgICB0aGlzLm0gPSAyMTQ3NDgzNjQ4O1xyXG4gICAgICAgIHRoaXMucmFuZ2UgPSAzMjc2NztcclxuICAgIH1cclxuICAgIFBzZXVkb1JhbmRvbS5wcm90b3R5cGUuZ2V0TmV4dCA9IGZ1bmN0aW9uICgpIHtcclxuICAgICAgICB0aGlzLnNlZWQgPSAodGhpcy5zZWVkICogdGhpcy5hICsgdGhpcy5jKSAlIHRoaXMubTtcclxuICAgICAgICByZXR1cm4gKHRoaXMuc2VlZCA+PiAxNikgLyB0aGlzLnJhbmdlO1xyXG4gICAgfTtcclxuICAgIFBzZXVkb1JhbmRvbS5wcm90b3R5cGUuZ2V0TmV4dEJldHdlZW4gPSBmdW5jdGlvbiAobWluLCBtYXgpIHtcclxuICAgICAgICByZXR1cm4gbWluICsgdGhpcy5nZXROZXh0KCkgKiAobWF4IC0gbWluKTtcclxuICAgIH07XHJcbiAgICByZXR1cm4gUHNldWRvUmFuZG9tO1xyXG59KCkpO1xyXG5leHBvcnRzLlBzZXVkb1JhbmRvbSA9IFBzZXVkb1JhbmRvbTtcclxuLy8jIHNvdXJjZU1hcHBpbmdVUkw9ZGF0YTphcHBsaWNhdGlvbi9qc29uO2Jhc2U2NCxleUoyWlhKemFXOXVJam96TENKbWFXeGxJam9pWkdWelkyVnVkQzVxY3lJc0luTnZkWEpqWlZKdmIzUWlPaUlpTENKemIzVnlZMlZ6SWpwYklpNHVMeTR1TDFkbFlrTnZiR0V2YzNKakwyUmxjMk5sYm5RdWRITWlYU3dpYm1GdFpYTWlPbHRkTENKdFlYQndhVzVuY3lJNklqczdRVUZKU1R0SlFVRkJPMUZCUTBrc1ZVRkJTeXhIUVVFMlFpeEZRVUZGTEVOQlFVTTdTVUZ2UTNwRExFTkJRVU03U1VFM1FrY3NiVUpCUVVjc1IwRkJTQ3hWUVVGSkxFVkJRVlVzUlVGQlJTeERRVUZYTzFGQlNYWkNMRWxCUVVrc1EwRkJReXhMUVVGTExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRPMGxCUTNaQ0xFTkJRVU03U1VGSlJDeHhRa0ZCU3l4SFFVRk1PMUZCUTBrc1NVRkJTU3hEUVVGRExFdEJRVXNzUjBGQlJ5eEZRVUZGTEVOQlFVTTdTVUZEY0VJc1EwRkJRenRKUVV0RUxIVkNRVUZQTEVkQlFWQTdVVUZEU1N4TFFVRkxMRWxCUVVrc1EwRkJReXhKUVVGSkxFbEJRVWtzUTBGQlF5eExRVUZMTzFsQlFVVXNUMEZCVHl4TFFVRkxMRU5CUVVNN1VVRkRka01zVDBGQlR5eEpRVUZKTEVOQlFVTTdTVUZEYUVJc1EwRkJRenRKUVV0RUxIRkNRVUZMTEVkQlFVd3NWVUZCVFN4RFFVRnZRenRSUVVOMFF5eExRVUZMTEVsQlFVa3NRMEZCUXl4SlFVRkpMRWxCUVVrc1EwRkJReXhMUVVGTExFVkJRVVU3V1VGRGRFSXNRMEZCUXl4RFFVRkRMRTFCUVUwc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQlJTeEpRVUZKTEVOQlFVTXNTMEZCU3l4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03VTBGREwwSTdTVUZEVEN4RFFVRkRPMGxCUTB3c1dVRkJRenRCUVVGRUxFTkJRVU1zUVVGeVEwUXNTVUZ4UTBNN1FVRnlRMWtzYzBKQlFVczdRVUZwUkd4Q08wbEJOa1JKTEdsQ1FVRlpMRU5CUVdFc1JVRkJVeXhEUVVGaExFVkJRVk1zUTBGQmJVSTdVVUZCYmtJc2EwSkJRVUVzUlVGQlFTeFJRVUZ0UWp0UlFVRjZReXhOUVVGRExFZEJRVVFzUTBGQlF5eERRVUZaTzFGQlFWTXNUVUZCUXl4SFFVRkVMRU5CUVVNc1EwRkJhMEk3VVVFMVJIQkZMR05CUVZNc1IwRkJWeXhOUVVGTkxFTkJRVU03VVVFeVF6TkNMSEZDUVVGblFpeEhRVUZYTEVOQlFVTXNRMEZCUXp0UlFVTTNRaXhwUWtGQldTeEhRVUZYTEVkQlFVY3NRMEZCUXp0UlFVTXpRaXhwUWtGQldTeEhRVUZYTEVsQlFVa3NRMEZCUXp0UlFVTTFRaXh2UWtGQlpTeEhRVUZaTEV0QlFVc3NRMEZCUXp0UlFVVm9ReXhYUVVGTkxFZEJRVWNzU1VGQlNTeFpRVUZaTEVWQlFVVXNRMEZCUXp0UlFVVTNRaXhaUVVGUExFZEJRVEJFTEVsQlFVa3NRMEZCUXp0UlFWZDZSU3hKUVVGSkxFTkJRVU1zUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXp0UlFVTllMRWxCUVVrc1EwRkJReXhEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETEUxQlFVMHNRMEZCUXp0UlFVTnNRaXhKUVVGSkxFTkJRVU1zUjBGQlJ5eEpRVUZKTEVOQlFVTXNRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eE5RVUZOTEVOQlFVTTdVVUZETjBJc1NVRkJTU3hEUVVGRExFTkJRVU1zUjBGQlJ5eEpRVUZKTEV0QlFVc3NRMEZCUXl4SlFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03VVVGRE0wSXNTVUZCU1N4RFFVRkRMRU5CUVVNc1IwRkJSeXhKUVVGSkxFdEJRVXNzUTBGQlF5eEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1VVRkRNMElzU1VGQlNTeERRVUZETEVWQlFVVXNSMEZCUnl4SlFVRkpMRXRCUVVzc1EwRkJReXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdVVUZETlVJc1NVRkJTU3hEUVVGRExFTkJRVU1zUjBGQlJ5eEpRVUZKTEV0QlFVc3NRMEZCUXl4SlFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03VVVGRE0wSXNTVUZCU1N4RFFVRkRMRU5CUVVNc1IwRkJSeXhKUVVGSkxFdEJRVXNzUTBGQlF5eEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1VVRkRNMElzU1VGQlNTeERRVUZETEVOQlFVTXNSMEZCUnl4SlFVRkpMRXRCUVVzc1EwRkJReXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdVVUZETTBJc1NVRkJTU3hEUVVGRExFTkJRVU1zUjBGQlJ5eEpRVUZKTEV0QlFVc3NRMEZCUXl4SlFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03VVVGRE0wSXNTVUZCU1N4RFFVRkRMRU5CUVVNc1IwRkJSeXhKUVVGSkxFdEJRVXNzUTBGQlF5eEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1VVRkRNMElzU1VGQlNTeERRVUZETEVWQlFVVXNSMEZCUnl4SlFVRkpMRXRCUVVzc1EwRkJReXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdVVUZETlVJc1NVRkJTU3hEUVVGRExFVkJRVVVzUjBGQlJ5eEpRVUZKTEV0QlFVc3NRMEZCUXl4SlFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03VVVGRE5VSXNTVUZCU1N4RFFVRkRMRWxCUVVrc1IwRkJSeXhKUVVGSkxFdEJRVXNzUTBGQlF5eEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1VVRkRPVUlzU1VGQlNTeERRVUZETEV0QlFVc3NSMEZCUnl4SlFVRkpMRXRCUVVzc1JVRkJSU3hEUVVGRE8xRkJRM3BDTEVsQlFVa3NRMEZCUXl4SlFVRkpMRWRCUVVjc1RVRkJUU3hEUVVGRExGTkJRVk1zUTBGQlF6dFJRVU0zUWl4SlFVRkpMRU5CUVVNc1IwRkJSeXhEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETzFGQlEySXNUMEZCVHl4RFFVRkRMRVZCUVVVc1JVRkJSVHRaUVVOU0xFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTTdXVUZEVGl4UFFVRlBMRVZCUVVVc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJUdG5Ra0ZEV2l4SlFVRkpMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1owSkJRMmhDTEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1NVRkJTU3hEUVVGRExFZEJRVWNzU1VGQlNTeERRVUZETEVsQlFVa3NSVUZCUlR0dlFrRkRlRUlzU1VGQlNTeERRVUZETEVsQlFVa3NSMEZCUnl4RFFVRkRMRU5CUVVNN2FVSkJRMnBDTzJGQlEwbzdVMEZEU2p0UlFVTkVMRWxCUVVrc1NVRkJTU3hEUVVGRExFbEJRVWtzUzBGQlN5eE5RVUZOTEVOQlFVTXNVMEZCVXp0WlFVRkZMRWxCUVVrc1EwRkJReXhKUVVGSkxFZEJRVWNzUTBGQlF5eERRVUZETzFGQlEyeEVMRU5CUVVNc1IwRkJSeXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETzFGQlExZ3NUMEZCVHl4RFFVRkRMRVZCUVVVc1JVRkJSVHRaUVVOU0xFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1NVRkJTU3hMUVVGTExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdXVUZEZWtJc1NVRkJTU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4SlFVRkpMRXRCUVVzc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFpRVU42UWl4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRE8xbEJRMDRzVDBGQlR5eERRVUZETEVWQlFVVXNSVUZCUlR0blFrRkRVaXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFbEJRVWtzUzBGQlN5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMkZCUXk5Q08xbEJRMFFzU1VGQlNTeERRVUZETEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1IwRkJSeXhKUVVGSkxFdEJRVXNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0WlFVTXhRaXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRWxCUVVrc1MwRkJTeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzFsQlEzcENMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NTVUZCU1N4TFFVRkxMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03V1VGRGVrSXNTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlJ5eEpRVUZKTEV0QlFVc3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRaUVVONlFpeEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFbEJRVWtzUzBGQlN5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMWxCUTNwQ0xFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1NVRkJTU3hMUVVGTExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdXVUZEZWtJc1NVRkJTU3hEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4SlFVRkpMRXRCUVVzc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFpRVU14UWl4SlFVRkpMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF5eEhRVUZITEVsQlFVa3NTMEZCU3l4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8xbEJRekZDTEVsQlFVa3NRMEZCUXl4SlFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRExFZEJRVWNzU1VGQlNTeExRVUZMTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1UwRkRMMEk3U1VGRFRDeERRVUZETzBsQlJXRXNNRUpCUVd0Q0xFZEJRV2hETEZWQlFXbERMRU5CUVZNc1JVRkJSU3hEUVVGdFF6dFJRVU16UlN4SlFVRkpMRU5CUVVNc1IwRkJSeXhKUVVGSkxFdEJRVXNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0UlFVTnlRaXhMUVVGTExFbEJRVWtzUTBGQlF5eEhRVUZITEVOQlFVTXNSVUZCUlN4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRkxFVkJRVVVzUTBGQlF5eEZRVUZGTzFsQlEzaENMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlJ5eEpRVUZKTEV0QlFVc3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRaUVVOd1FpeExRVUZMTEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1JVRkJSU3hEUVVGRExFZEJRVWNzUTBGQlF5eEZRVUZGTEVWQlFVVXNRMEZCUXl4RlFVRkZPMmRDUVVONFFpeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJRenRoUVVOeVFqdFRRVU5LTzFGQlEwUXNUMEZCVHl4RFFVRkRMRU5CUVVNN1NVRkRZaXhEUVVGRE8wbEJSVThzTWtKQlFWTXNSMEZCYWtJN1VVRkJRU3hwUWtGVFF6dFJRVkpITEVsQlFVa3NRMEZCUXl4SFFVRkhMRWxCUVVrc1MwRkJTeXhEUVVGRExFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0UlFVTXhRaXhKUVVGSkxFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTTdVVUZEVml4TFFVRkxMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NTVUZCU1N4RFFVRkRMRU5CUVVNc1JVRkJSU3hGUVVGRkxFTkJRVU1zUlVGQlJUdFpRVU0zUWl4SlFVRkpMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NTVUZCU1N4RFFVRkRMRTFCUVUwc1EwRkJReXhqUVVGakxFTkJRVU1zU1VGQlNTeEZRVUZGTEVOQlFVTXNRMEZCUXl4SFFVRkhMRWRCUVVjc1EwRkJRenRaUVVONlJDeERRVUZETEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJRenRUUVVOa08xRkJRMFFzUTBGQlF5eEhRVUZITEVsQlFVa3NRMEZCUXl4SlFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03VVVGRGFrSXNUMEZCVHl4RFFVRkRMRU5CUVVNc1IwRkJSeXhEUVVGRExGVkJRVUVzUTBGQlF5eEpRVUZITEU5QlFVRXNRMEZCUXl4SlFVRkpMRXRCUVVrc1EwRkJReXhKUVVGSkxFZEJRVWNzUTBGQlF5eEZRVUZzUWl4RFFVRnJRaXhEUVVGRExFTkJRVU03U1VGRGVrTXNRMEZCUXp0SlFVZE5MRzlEUVVGclFpeEhRVUY2UWl4VlFVRXdRaXhEUVVGaE8xRkJRWFpETEdsQ1FTdEhRenRSUVRsSFJ5eEpRVUZOTEVOQlFVTXNSMEZCUnl4SlFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRE8xRkJRMnBDTEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNN1dVRkJSU3hQUVVGUE8xRkJRMnhDTEVsQlFVa3NRMEZCVXl4RFFVRkRPMUZCVDJRc1NVRkJTU3hEUVVGRExFZEJRVWNzU1VGQlNTeExRVUZMTEVOQlFWTXNTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8xRkJRMnhETEVsQlFVa3NSVUZCUlN4SFFVRkhMRWxCUVVrc1MwRkJTeXhEUVVGVExFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0UlFVTnVReXhKUVVGSkxFZEJRVWNzUjBGQlJ5eEpRVUZKTEV0QlFVc3NRMEZCVXl4SlFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03VVVGRGNFTXNTVUZCU1N4SlFVRkpMRWRCUVVjc1EwRkJReXhEUVVGRE8xRkJSMklzUzBGQlN5eEpRVUZKTEVkQlFVTXNSMEZCUnl4RFFVRkRMRVZCUVVVc1IwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeEZRVUZGTEVkQlFVTXNSVUZCUlR0WlFVVjRRaXhMUVVGTExFTkJRVU1zUjBGQlJ5eERRVUZETEVWQlFVVXNRMEZCUXl4SFFVRkhMRWxCUVVrc1EwRkJReXhEUVVGRExFVkJRVVVzUlVGQlJTeERRVUZETzJkQ1FVRkZMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlJ5eEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFZEJRVU1zUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXp0WlFVZDJSQ3hMUVVGTExFbEJRVWtzUTBGQlF5eEhRVUZITEVOQlFVTXNSVUZCUlN4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRkxFVkJRVVVzUTBGQlF5eEZRVUZGTzJkQ1FVTjRRaXhKUVVGSkxFZEJRVU1zUzBGQlN5eERRVUZETzI5Q1FVRkZMRk5CUVZNN1owSkJTWFJDTEVsQlFVa3NXVUZCV1N4SFFVRkhMRU5CUVVNc1EwRkJRenRuUWtGRGNrSXNTVUZCU1N4bFFVRmxMRWRCUVVjc1EwRkJReXhEUVVGRE8yZENRVU40UWl4UFFVRlBMRmxCUVZrc1JVRkJSU3hGUVVGRk8yOUNRVU51UWl4bFFVRmxMRWRCUVVjc1EwRkJReXhEUVVGRE8yOUNRVU53UWl4TFFVRkxMRU5CUVVNc1IwRkJSeXhEUVVGRExFVkJRVVVzUTBGQlF5eEhRVUZITEVsQlFVa3NRMEZCUXl4RFFVRkRMRVZCUVVVc1JVRkJSU3hEUVVGRExFVkJRVVU3ZDBKQlEzcENMRWxCUVUwc1NVRkJSU3hIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlF5eERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzNkQ1FVTndReXhsUVVGbExFbEJRVWtzUlVGQlJTeERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRWxCUVVVc1IwRkJSeXhKUVVGRkxFTkJRVU03Y1VKQlEzUkRPMjlDUVVORUxFbEJRVWtzWlVGQlpTeEhRVUZITEVsQlFVazdkMEpCUVVVc1RVRkJUVHR2UWtGRGJFTXNTVUZCVFN4RlFVRkZMRWRCUVVjc1NVRkJTU3hEUVVGRExGTkJRVk1zUlVGQlJTeERRVUZETzI5Q1FVTTFRaXhMUVVGTExFTkJRVU1zUjBGQlJ5eERRVUZETEVWQlFVVXNRMEZCUXl4SFFVRkhMRWxCUVVrc1EwRkJReXhEUVVGRExFVkJRVVVzUlVGQlJTeERRVUZETzNkQ1FVRkZMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNTVUZCU1N4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03YVVKQlEycEVPMmRDUVVORUxFbEJRVTBzVVVGQlVTeEhRVUZITEVsQlFVa3NRMEZCUXl4SlFVRkpMRU5CUVVNc1pVRkJaU3hEUVVGRExFTkJRVU03WjBKQlF6VkRMRWxCUVUwc1lVRkJZU3hIUVVGSExFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03WjBKQlNXNURMRWxCUVVrc1RVRkJUU3hIUVVGSExFbEJRVWtzUTBGQlF5eERRVUZETEVsQlFVa3NTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJReXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdaMEpCUnk5RExFbEJRVWtzVFVGQlRTeEhRVUZITEVOQlFVTXNTVUZCU1N4UlFVRlJMRWRCUVVjc1lVRkJZU3hKUVVGSkxFTkJRVU1zVVVGQlVTeERRVUZETEdGQlFXRXNRMEZCUXl4RlFVRkZPMjlDUVVOd1JTeExRVUZMTEVOQlFVTXNSMEZCUnl4RFFVRkRMRVZCUVVVc1EwRkJReXhIUVVGSExFbEJRVWtzUTBGQlF5eERRVUZETEVWQlFVVXNSVUZCUlN4RFFVRkRPM2RDUVVGRkxFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1IwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRPMjlDUVVOcVJDeFRRVUZUTzJsQ1FVTmFPMmRDUVVkRUxFbEJRVWtzVFVGQlRTeEhRVUZITEVOQlFVTXNSVUZCUlR0dlFrRkRXaXhOUVVGTkxFZEJRVWNzUTBGQlF5eERRVUZETzJsQ1FVTmtPMmRDUVVORUxFbEJRVTBzWjBKQlFXZENMRWRCUVVjc1lVRkJZU3hIUVVGSExHRkJRV0VzUlVGRGJFUXNSVUZCUlN4SFFVRkhMRU5CUVVNc1IwRkJSeXhOUVVGTkxFZEJRVWNzUTBGQlF5eFJRVUZSTEVkQlFVY3NZVUZCWVN4RFFVRkRMRWRCUVVjc1EwRkJReXhuUWtGQlowSXNSMEZCUnl4UlFVRlJMRU5CUVVNc1JVRkROVVVzWVVGQllTeEhRVUZITEdWQlFXVXNSMEZCUnl4UlFVRlJMRVZCUXpGRExFVkJRVVVzUjBGQlJ5eERRVUZETEVkQlFVY3NRMEZCUXl4TlFVRk5MRWRCUVVjc1EwRkJReXhuUWtGQlowSXNSMEZCUnl4aFFVRmhMRU5CUVVNc1EwRkJRenRuUWtGRE1VUXNTVUZCU1N4RFFVRkRMRkZCUVZFc1EwRkJReXhGUVVGRkxFTkJRVU03YjBKQlEySXNUMEZCVHl4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF6dG5Ra0ZEY0VJc1MwRkJTeXhEUVVGRExFZEJRVWNzUTBGQlF5eEZRVUZGTEVOQlFVTXNSMEZCUnl4SlFVRkpMRU5CUVVNc1EwRkJReXhGUVVGRkxFVkJRVVVzUTBGQlF5eEZRVUZGTzI5Q1FVTjZRaXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVNc1EwRkJReXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4RlFVRkZMRU5CUVVNN2IwSkJRekZDTEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1NVRkJTU3hKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEhRVUZITEVWQlFVVXNSMEZCUnl4RFFVRkRMRU5CUVVNc1IwRkJSeXhoUVVGaExFZEJRVWNzWVVGQllTeEhRVUZITEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExHVkJRV1VzUTBGQlF5eERRVUZETEVOQlFVTTdhVUpCUTNCSE8yRkJRMG83V1VGRFJDeExRVUZMTEVOQlFVTXNSMEZCUnl4RFFVRkRMRVZCUVVVc1EwRkJReXhIUVVGSExFbEJRVWtzUTBGQlF5eERRVUZETEVWQlFVVXNSVUZCUlN4RFFVRkRPMmRDUVVGRkxFbEJRVWtzUjBGQlJ5eEpRVUZKTEVOQlFVTXNSMEZCUnl4RFFVRkRMRWxCUVVrc1JVRkJSU3hKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVNc1EwRkJReXhEUVVGRExFZEJRVU1zUTBGQlF5eEhRVUZITEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8xTkJRMmhHTzFGQlJVUXNTVUZCU1N4RFFVRkRMRWRCUVVjc1NVRkJTU3hEUVVGRExGbEJRVmtzUjBGQlF5eERRVUZETEVOQlFVTTdVVUZETlVJc1NVRkJTU3hEUVVGRExFZEJRVWNzU1VGQlNTeERRVUZETEZsQlFWa3NRMEZCUXp0UlFVTXhRaXhKUVVGSkxFTkJRVU1zUjBGQlJ5eEpRVUZKTEVOQlFVTXNXVUZCV1N4RFFVRkRPMUZCUXpGQ0xFbEJRVWtzUTBGQlF5eEhRVUZITEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF6dFJRVU53UWl4SlFVRkpMRkZCUVZFc1IwRkJSeXhKUVVGSkxFTkJRVU1zWjBKQlFXZENMRU5CUVVNN1VVRkZja01zUzBGQlN5eEpRVUZKTEVOQlFVTXNSMEZCVnl4RFFVRkRMRVZCUVVVc1EwRkJReXhIUVVGSExGRkJRVkVzUlVGQlJTeEZRVUZGTEVOQlFVTXNSVUZCUlR0WlFVTjJReXhMUVVGTExFTkJRVU1zUjBGQlJ5eERRVUZETEVWQlFVVXNRMEZCUXl4SFFVRkhMRWxCUVVrc1EwRkJReXhEUVVGRExFVkJRVVVzUlVGQlJTeERRVUZETEVWQlFVVTdaMEpCUTNwQ0xFbEJRVWtzUjBGQlJ5eEhRVUZITEVsQlFVa3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdaMEpCUTNaQ0xFbEJRVWtzUTBGQlF5eEhRVUZITEVkQlFVY3NSMEZCUnl4RFFVRkRMRU5CUVVNN1owSkJRMmhDTEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU03WjBKQlEyUXNTVUZCU1N4RFFVRkRMRWRCUVVjc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF6dG5Ra0ZEWkN4SlFVRkpMRU5CUVVNc1IwRkJSeXhKUVVGSkxFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMmRDUVVOd1FpeEpRVUZKTEVWQlFVVXNSMEZCUnl4RFFVRkRMRU5CUVVNc1NVRkJTU3hIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4SFFVRkhMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF6dHZRa0ZETDBJc1EwRkJReXhIUVVGSExFZEJRVWNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1IwRkJSeXhEUVVGRExFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFZEJRVWNzUjBGQlJ5eERRVUZETEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU03WjBKQlEzUkVMRWxCUVVrc1EwRkJReXhEUVVGRExFZEJRVWNzUlVGQlJTeEpRVUZKTEVWQlFVVXNTVUZCU1N4RFFVRkRMRVZCUVVVN2IwSkJRM0JDTEVsQlFVa3NTVUZCU1N4RFFVRkRMR1ZCUVdVc1JVRkJSVHQzUWtGRGRFSXNTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNTVUZCU1N4SlFVRkpMRWRCUVVjc1EwRkJReXhIUVVGSExFVkJRVVVzUTBGQlF6dDNRa0ZET1VJc1NVRkJTU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zU1VGQlNTeEpRVUZKTEVkQlFVY3NRMEZCUXl4RFFVRkRPM0ZDUVVNdlFqdDVRa0ZCVFR0M1FrRkRTQ3hKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhKUVVGSkxFTkJRVU1zUjBGQlJ5eEZRVUZGTEVOQlFVTTdkMEpCUTNaQ0xFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVsQlFVa3NRMEZCUXl4RFFVRkRPM0ZDUVVONFFqdHBRa0ZEU2p0aFFVTktPMU5CUTBvN1VVRkRSQ3hKUVVGSkxFTkJRVU1zU1VGQlNTeERRVUZETEV0QlFVc3NRMEZCUXl4UFFVRlBMRVZCUVVVc1JVRkJSVHRaUVVOMlFpeEpRVUZKTEVOQlFVTXNTMEZCU3l4RFFVRkRMRXRCUVVzc1EwRkJReXhWUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETzJkQ1FVTnNRaXhMUVVGTExFTkJRVU1zUjBGQlJ5eERRVUZETEVWQlFVVXNRMEZCUXl4SFFVRkhMRXRCUVVrc1EwRkJReXhEUVVGRExFVkJRVVVzUlVGQlJTeERRVUZETEVWQlFVVTdiMEpCUTNwQ0xFdEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVsQlFVa3NTVUZCU1N4RFFVRkRPMjlDUVVONFFpeExRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEpRVUZKTEVsQlFVa3NSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dHBRa0ZETTBNN1dVRkRUQ3hEUVVGRExFTkJRVU1zUTBGQlF6dFRRVU5PTzBsQlUwd3NRMEZCUXp0SlFVVmpMR1ZCUVU4c1IwRkJkRUlzVlVGQmRVSXNRMEZCVnl4RlFVRkZMRU5CUVZjN1VVRkRNME1zU1VGQlNTeERRVUZETEVkQlFVY3NRMEZCUXl4RlFVRkZMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zVFVGQlRTeERRVUZETzFGQlEzaENMRTlCUVU4c1EwRkJReXhGUVVGRk8xbEJRVVVzUTBGQlF5eEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdVVUZETjBJc1QwRkJUeXhEUVVGRExFTkJRVU03U1VGRFlpeERRVUZETzBsQlIyTXNjVUpCUVdFc1IwRkJOVUlzVlVGQk5rSXNRMEZCWVN4RlFVRkZMRU5CUVZjc1JVRkJSU3hEUVVGWE8xRkJRMmhGTEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJReXhOUVVGTkxFTkJRVU03VVVGRGFrSXNUMEZCVHl4RFFVRkRMRVZCUVVVN1dVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NUMEZCVHl4RFFVRkRMRTlCUVU4c1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNN1NVRkRhRVFzUTBGQlF6dEpRVXROTEdsRFFVRmxMRWRCUVhSQ0xGVkJRWFZDTEVOQlFXRTdVVUZEYUVNc1NVRkJTU3hUUVVGVExFZEJRVWNzUTBGQlF5eEZRVUZGTEZkQlFWY3NSMEZCUnl4RFFVRkRMRU5CUVVNN1VVRkRia01zUzBGQlN5eEpRVUZKTEVOQlFVTXNSMEZCUnl4RFFVRkRMRVZCUVVVc1EwRkJReXhIUVVGSExFbEJRVWtzUTBGQlF5eERRVUZETEVWQlFVVXNSVUZCUlN4RFFVRkRMRVZCUVVVN1dVRkROMElzVTBGQlV5eEpRVUZKTEU5QlFVOHNRMEZCUXl4UFFVRlBMRU5CUVVNc1NVRkJTU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFpRVU01UXl4UFFVRlBMRU5CUVVNc1lVRkJZU3hEUVVGRExFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEZRVUZGTEVsQlFVa3NRMEZCUXl4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFpRVU51UkN4WFFVRlhMRWxCUVVrc1QwRkJUeXhEUVVGRExFOUJRVThzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUVVVc1NVRkJTU3hEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMU5CUTNCRU8xRkJRMFFzU1VGQlNTeFhRVUZYTEV0QlFVc3NRMEZCUXl4SlFVRkpMRU5CUVVNc1VVRkJVU3hEUVVGRExGZEJRVmNzUTBGQlF6dFpRVUZGTEU5QlFVOHNRMEZCUXl4RFFVRkRPMUZCUXpGRUxFOUJRVThzUTBGQlF5eEhRVUZITEZOQlFWTXNSMEZCUnl4WFFVRlhMRU5CUVVNN1NVRkRka01zUTBGQlF6dEpRVVZOTERoQ1FVRlpMRWRCUVc1Q08xRkJRMGtzU1VGQlNTeERRVUZETEd0Q1FVRnJRaXhEUVVGRExFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0UlFVTm9ReXhKUVVGSkxFdEJRVXNzUjBGQlJ5eEpRVUZKTEVOQlFVTXNaVUZCWlN4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFJRVU42UXl4TFFVRkxMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NTVUZCU1N4RFFVRkRMRU5CUVVNc1JVRkJSU3hGUVVGRkxFTkJRVU1zUlVGQlJUdFpRVU0zUWl4SlFVRkpMRU5CUVVNc1pVRkJaU3hEUVVGRExFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUVVVc1NVRkJTU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSVUZCUlN4TFFVRkxMRU5CUVVNc1EwRkJRenRUUVVOeVJEdFJRVU5FTEU5QlFVOHNTVUZCU1N4RFFVRkRMR0ZCUVdFc1JVRkJSU3hEUVVGRE8wbEJRMmhETEVOQlFVTTdTVUZGWXl4WlFVRkpMRWRCUVc1Q0xGVkJRVzlDTEVOQlFXRXNSVUZCUlN4RFFVRmhPMUZCUXpWRExFbEJRVWtzUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXl4TlFVRk5MRVZCUVVVc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4TlFVRk5MRU5CUVVNN1VVRkRiRU1zUzBGQlN5eEpRVUZKTEVOQlFVTXNSMEZCUnl4RFFVRkRMRVZCUVVVc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeEZRVUZGTEVOQlFVTXNSVUZCUlR0WlFVTjRRaXhMUVVGTExFbEJRVWtzUTBGQlF5eEhRVUZITEVOQlFVTXNSVUZCUlN4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRkxFVkJRVVVzUTBGQlF5eEZRVUZGTzJkQ1FVTjRRaXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMkZCUTNKQ08xTkJRMG83U1VGRFRDeERRVUZETzBsQlVVOHNaME5CUVdNc1IwRkJkRUlzVlVGQmRVSXNSVUZCWXl4RlFVRkZMRU5CUVdFc1JVRkJSU3hEUVVGaExFVkJRVVVzVVVGQlowSTdVVUZEYWtZc1QwRkJUeXhEUVVGRExFbEJRVWtzUTBGQlF5eEZRVUZGTEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNN1VVRkRjRUlzU1VGQlNTeERRVUZETEdWQlFXVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RlFVRkZMRkZCUVZFc1EwRkJReXhEUVVGRE8xRkJRek5ETEVsQlFVa3NTVUZCU1N4RFFVRkRMRTlCUVU4N1dVRkJSU3hKUVVGSkxFTkJRVU1zVDBGQlR5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQlJTeEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdVVUZEZEVRc1NVRkJTU3hEUVVGRExHVkJRV1VzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEZRVUZGTEZGQlFWRXNRMEZCUXl4RFFVRkRPMUZCUXpORExFbEJRVWtzU1VGQlNTeERRVUZETEU5QlFVODdXVUZCUlN4SlFVRkpMRU5CUVVNc1QwRkJUeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkJSU3hGUVVGRkxFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03VVVGSGNrUXNTMEZCU3l4SlFVRkpMRU5CUVVNc1IwRkJSeXhEUVVGRExFVkJRVVVzUTBGQlF5eEhRVUZITEVsQlFVa3NRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhGUVVGRk8xbEJRek5DTEVsQlFVa3NRMEZCUXl4bFFVRmxMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkJSU3hSUVVGUkxFTkJRVU1zUTBGQlF6dEpRVlZ1UkN4RFFVRkRPMGxCUldNc1kwRkJUU3hIUVVGeVFpeFZRVUZ6UWl4RFFVRlRMRVZCUVVVc1EwRkJVeXhGUVVGRkxFTkJRV2RETzFGQlEzaEZMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF6dFJRVUZETEU5QlFVOHNRMEZCUXl4RlFVRkZMRWRCUVVjc1EwRkJReXhGUVVGRk8xbEJRM1pDTEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJRenRaUVVGRExFOUJRVThzUTBGQlF5eEZRVUZGTEVkQlFVY3NRMEZCUXp0blFrRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRPMU5CUTNSRE8wbEJRMHdzUTBGQlF6dEpRVU5QTERaQ1FVRlhMRWRCUVc1Q0xGVkJRVzlDTEVOQlFXZERPMUZCUTJoRUxFOUJRVThzUTBGQlF5eE5RVUZOTEVOQlFVTXNTVUZCU1N4RFFVRkRMRU5CUVVNc1JVRkJSU3hKUVVGSkxFTkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRPMGxCUTNSRExFTkJRVU03U1VGRlR5eHhRMEZCYlVJc1IwRkJNMElzVlVGQk5FSXNSVUZCWXl4RlFVRkZMRU5CUVdFN1VVRkJla1FzYVVKQlpVTTdVVUZrUnl4SlFVRkpMRU5CUVVNc2EwSkJRV3RDTEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNN1VVRkROVUlzU1VGQlNTeExRVUZMTEVkQlFVY3NTVUZCU1N4RFFVRkRMR1ZCUVdVc1EwRkJReXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdVVUZEZWtNc1NVRkJTU3hEUVVGRExHTkJRV01zUTBGQlF5eEZRVUZGTEVWQlFVVXNRMEZCUXl4RlFVRkZMRWxCUVVrc1EwRkJReXhEUVVGRExFVkJRVVVzUzBGQlN5eERRVUZETEVOQlFVTTdVVUZOTVVNc1NVRkJTU3hKUVVGSkxFTkJRVU1zVDBGQlR5eEZRVUZGTzFsQlEyUXNTVUZCU1N4RFFVRkRMRmRCUVZjc1EwRkJReXhWUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVsQlFVc3NUMEZCUVN4TFFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRVZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFXcERMRU5CUVdsRExFTkJRVU1zUTBGQlF6dFpRVU01UkN4SlFVRkpMRWxCUVVrc1IwRkJSeXhKUVVGSkxFTkJRVU1zWlVGQlpTeERRVUZETEVsQlFVa3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRaUVVONFF5eEpRVUZKTEVkQlFVY3NTVUZCU1N4RFFVRkRMRWRCUVVjc1EwRkJReXhIUVVGSExFVkJRVVVzU1VGQlNTeERRVUZETEVkQlFVY3NRMEZCUXl4SlFVRkpMRVZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFpRVU40UXl4SlFVRkpMRU5CUVVNc1kwRkJZeXhEUVVGRExFVkJRVVVzUlVGQlJTeERRVUZETEVWQlFVVXNTVUZCU1N4RFFVRkRMRU5CUVVNc1JVRkJSU3hKUVVGSkxFTkJRVU1zUTBGQlF6dFRRVU0xUXp0SlFVTk1MRU5CUVVNN1NVRkZUU3h4UWtGQlJ5eEhRVUZXTEZWQlFWY3NWVUZCYTBJN1VVRkRla0lzU1VGQlNTeE5RVUZOTEVkQlFVY3NUVUZCVFN4RFFVRkRMRk5CUVZNc1JVRkJSU3hUUVVGVExFZEJRVWNzUzBGQlN5eERRVUZETzFGQlEycEVMRTlCUVU4c1EwRkJReXhUUVVGVExFbEJRVWtzVlVGQlZTeEZRVUZGTEVkQlFVY3NRMEZCUXl4RlFVRkZPMWxCUTI1RExFbEJRVWtzUTBGQlF5eEhRVUZITEVsQlFVa3NRMEZCUXl4VlFVRlZMRVZCUVVVc1EwRkJRenRaUVVNeFFpeFRRVUZUTEVkQlFVY3NTVUZCU1N4RFFVRkRMRWRCUVVjc1EwRkJReXhOUVVGTkxFZEJRVWNzUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXl4SFFVRkhMRWxCUVVrc1EwRkJReXhUUVVGVExFTkJRVU03V1VGRGRFUXNUVUZCVFN4SFFVRkhMRU5CUVVNc1EwRkJRenRUUVVOa08xRkJRMFFzVDBGQlR5eE5RVUZOTEVOQlFVTTdTVUZEYkVJc1EwRkJRenRKUVVWTkxEUkNRVUZWTEVkQlFXcENPMUZCUVVFc2FVSkJaVU03VVVGa1J5eEpRVUZKTEVOQlFVTXNiVUpCUVcxQ0xFTkJRVU1zU1VGQlNTeERRVUZETEVOQlFVTXNSVUZCUlN4SlFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03VVVGRGVrTXNUMEZCVHl4RFFVRkRMRWRCUVVjc1EwRkJReXhKUVVGSkxFTkJRVU1zUTBGQlF5eEZRVUZGTEVsQlFVa3NRMEZCUXl4RFFVRkRMRVZCUVVVc1NVRkJTU3hEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETzFGQlEzSkRMRWxCUVVrc1EwRkJReXh0UWtGQmJVSXNRMEZCUXl4SlFVRkpMRU5CUVVNc1JVRkJSU3hGUVVGRkxFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0UlFVTXhReXhQUVVGUExFTkJRVU1zUjBGQlJ5eERRVUZETEVsQlFVa3NRMEZCUXl4RFFVRkRMRVZCUVVVc1NVRkJTU3hEUVVGRExFTkJRVU1zUlVGQlJTeEpRVUZKTEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNN1VVRkRja01zU1VGQlNTeERRVUZETEcxQ1FVRnRRaXhEUVVGRExFbEJRVWtzUTBGQlF5eEZRVUZGTEVWQlFVVXNTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8xRkJRekZETEVsQlFVa3NRMEZCUXl4dFFrRkJiVUlzUTBGQlF5eEpRVUZKTEVOQlFVTXNRMEZCUXl4RlFVRkZMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFJRVU42UXl4SlFVRkpMRWxCUVVrc1IwRkJSeXhEUVVGRExFTkJRVU03VVVGRFlpeEpRVUZKTEVOQlFVTXNWMEZCVnl4RFFVRkRMRlZCUVVNc1EwRkJReXhGUVVGRkxFTkJRVU03V1VGRGJFSXNTVUZCU1N4RFFVRkRMRWRCUVVjc1EwRkJReXhMUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFZEJRVWNzUjBGQlJ5eExRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEhRVUZITEVkQlFVY3NSMEZCUnl4TFFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRXRCUVVrc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1IwRkJSeXhIUVVGSExFVkJRMnBHTEVOQlFVTXNSMEZCUnl4TFFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJRenRaUVVONlFpeEpRVUZKTEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJRenRaUVVOa0xFdEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETzFGQlEzSkNMRU5CUVVNc1EwRkJReXhEUVVGRE8xRkJRMGdzVDBGQlR5eEpRVUZKTEVOQlFVTTdTVUZEYUVJc1EwRkJRenRKUVVWakxGZEJRVWNzUjBGQmJFSXNWVUZCYlVJc1EwRkJZU3hGUVVGRkxFTkJRV0VzUlVGQlJTeERRVUZoTzFGQlF6RkVMRTlCUVU4c1EwRkJReXhOUVVGTkxFTkJRVU1zUTBGQlF5eERRVUZETEUxQlFVMHNSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zVFVGQlRTeEZRVUZGTEZWQlFVTXNRMEZCUXl4RlFVRkZMRU5CUVVNN1dVRkRka01zVDBGQlFTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFZEJRVWM3VVVGQk4wTXNRMEZCTmtNc1EwRkJReXhEUVVGRE8wbEJRM1pFTEVOQlFVTTdTVUZGVFN4cFEwRkJaU3hIUVVGMFFpeFZRVUYxUWl4RFFVRlhMRVZCUVVVc1EwRkJWeXhGUVVGRkxGRkJRV2RDTzFGQlF6ZEVMRXRCUVVzc1NVRkJTU3hEUVVGRExFZEJRVWNzUTBGQlF5eEZRVUZGTEVOQlFVTXNSMEZCUnl4SlFVRkpMRU5CUVVNc1EwRkJReXhGUVVGRkxFVkJRVVVzUTBGQlF5eEZRVUZGTzFsQlF6ZENMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1VVRkJVU3hIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0VFFVTnFRenRKUVVOTUxFTkJRVU03U1VGRlRTd3JRa0ZCWVN4SFFVRndRanRSUVVOSkxFbEJRVWtzVFVGQlRTeEhRVUZITEVOQlFVTXNRMEZCUXp0UlFVTm1MRXRCUVVzc1NVRkJTU3hEUVVGRExFZEJRVWNzUTBGQlF5eEZRVUZGTEU5QlFVOHNSMEZCUnl4SlFVRkpMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NUMEZCVHl4RlFVRkZMRVZCUVVVc1EwRkJReXhGUVVGRk8xbEJRM0JFTEV0QlFVc3NTVUZCU1N4RFFVRkRMRWRCUVVjc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NTVUZCU1N4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFZEJRVWNzUTBGQlF5eEZRVUZGTEVWQlFVVXNRMEZCUXl4RlFVRkZPMmRDUVVONFF5eEpRVUZKTEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNN1owSkJRMVlzUzBGQlN5eEpRVUZKTEVOQlFVTXNSMEZCUnl4RFFVRkRMRVZCUVVVc1EwRkJReXhIUVVGSExFbEJRVWtzUTBGQlF5eERRVUZETEVWQlFVVXNSVUZCUlN4RFFVRkRMRVZCUVVVN2IwSkJRemRDTEVsQlFVa3NSVUZCUlN4SFFVRkhMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1NVRkJTU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenR2UWtGRGNrTXNRMEZCUXl4SlFVRkpMRVZCUVVVc1IwRkJSeXhGUVVGRkxFTkJRVU03YVVKQlEyaENPMmRDUVVORUxFTkJRVU1zUjBGQlJ5eEpRVUZKTEVOQlFVTXNTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8yZENRVU5xUWl4SlFVRkpMRU5CUVVNc1IwRkJSeXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8yZENRVU55UWl4SlFVRkpMRU5CUVVNc1VVRkJVU3hEUVVGRExFTkJRVU1zUTBGQlF6dHZRa0ZCUlN4VFFVRlRPMmRDUVVNelFpeEpRVUZKTEVWQlFVVXNSMEZCUnl4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRE8yZENRVU5tTEVsQlFVa3NSVUZCUlN4SFFVRkhMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU03WjBKQlEyWXNUVUZCVFN4SlFVRkpMRVZCUVVVc1IwRkJSeXhGUVVGRkxFZEJRVWNzUlVGQlJTeERRVUZETzJGQlF6RkNPMU5CUTBvN1VVRkRSQ3hQUVVGUExFMUJRVTBzUTBGQlF6dEpRVU5zUWl4RFFVRkRPMGxCY0ZoakxHOUNRVUZaTEVkQlFWY3NTMEZCU3l4RFFVRkRPMGxCY1Zob1JDeGpRVUZETzBOQlFVRXNRVUV2V1VRc1NVRXJXVU03UVVFdldWa3NNRUpCUVU4N1FVRnJXbkJDTzBsQlRVa3NjMEpCUVcxQ0xFbEJRV2RDTzFGQlFXaENMSEZDUVVGQkxFVkJRVUVzVVVGQlowSTdVVUZCYUVJc1UwRkJTU3hIUVVGS0xFbEJRVWtzUTBGQldUdFJRVXd6UWl4TlFVRkRMRWRCUVZjc1RVRkJUU3hEUVVGRE8xRkJRMjVDTEUxQlFVTXNSMEZCVnl4UFFVRlBMRU5CUVVNN1VVRkRjRUlzVFVGQlF5eEhRVUZYTEZWQlFWVXNRMEZCUXp0UlFVTjJRaXhWUVVGTExFZEJRVmNzUzBGQlN5eERRVUZETzBsQlJWTXNRMEZCUXp0SlFVZDRReXc0UWtGQlR5eEhRVUZRTzFGQlEwa3NTVUZCU1N4RFFVRkRMRWxCUVVrc1IwRkJSeXhEUVVGRExFbEJRVWtzUTBGQlF5eEpRVUZKTEVkQlFVY3NTVUZCU1N4RFFVRkRMRU5CUVVNc1IwRkJSeXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJRenRSUVVOdVJDeFBRVUZQTEVOQlFVTXNTVUZCU1N4RFFVRkRMRWxCUVVrc1NVRkJTU3hGUVVGRkxFTkJRVU1zUjBGQlJ5eEpRVUZKTEVOQlFVTXNTMEZCU3l4RFFVRkRPMGxCUXpGRExFTkJRVU03U1VGSFJDeHhRMEZCWXl4SFFVRmtMRlZCUVdVc1IwRkJWeXhGUVVGRkxFZEJRVmM3VVVGRGJrTXNUMEZCVHl4SFFVRkhMRWRCUVVjc1NVRkJTU3hEUVVGRExFOUJRVThzUlVGQlJTeEhRVUZITEVOQlFVTXNSMEZCUnl4SFFVRkhMRWRCUVVjc1EwRkJReXhEUVVGRE8wbEJRemxETEVOQlFVTTdTVUZEVEN4dFFrRkJRenRCUVVGRUxFTkJRVU1zUVVGc1FrUXNTVUZyUWtNN1FVRnNRbGtzYjBOQlFWa2lmUT09IiwiXCJ1c2Ugc3RyaWN0XCI7XHJcbnZhciBfX2V4dGVuZHMgPSAodGhpcyAmJiB0aGlzLl9fZXh0ZW5kcykgfHwgKGZ1bmN0aW9uICgpIHtcclxuICAgIHZhciBleHRlbmRTdGF0aWNzID0gZnVuY3Rpb24gKGQsIGIpIHtcclxuICAgICAgICBleHRlbmRTdGF0aWNzID0gT2JqZWN0LnNldFByb3RvdHlwZU9mIHx8XHJcbiAgICAgICAgICAgICh7IF9fcHJvdG9fXzogW10gfSBpbnN0YW5jZW9mIEFycmF5ICYmIGZ1bmN0aW9uIChkLCBiKSB7IGQuX19wcm90b19fID0gYjsgfSkgfHxcclxuICAgICAgICAgICAgZnVuY3Rpb24gKGQsIGIpIHsgZm9yICh2YXIgcCBpbiBiKSBpZiAoYi5oYXNPd25Qcm9wZXJ0eShwKSkgZFtwXSA9IGJbcF07IH07XHJcbiAgICAgICAgcmV0dXJuIGV4dGVuZFN0YXRpY3MoZCwgYik7XHJcbiAgICB9O1xyXG4gICAgcmV0dXJuIGZ1bmN0aW9uIChkLCBiKSB7XHJcbiAgICAgICAgZXh0ZW5kU3RhdGljcyhkLCBiKTtcclxuICAgICAgICBmdW5jdGlvbiBfXygpIHsgdGhpcy5jb25zdHJ1Y3RvciA9IGQ7IH1cclxuICAgICAgICBkLnByb3RvdHlwZSA9IGIgPT09IG51bGwgPyBPYmplY3QuY3JlYXRlKGIpIDogKF9fLnByb3RvdHlwZSA9IGIucHJvdG90eXBlLCBuZXcgX18oKSk7XHJcbiAgICB9O1xyXG59KSgpO1xyXG5PYmplY3QuZGVmaW5lUHJvcGVydHkoZXhwb3J0cywgXCJfX2VzTW9kdWxlXCIsIHsgdmFsdWU6IHRydWUgfSk7XHJcbnZhciByZWN0YW5nbGVfMSA9IHJlcXVpcmUoXCIuL3JlY3RhbmdsZVwiKTtcclxudmFyIFBvaW50ID0gKGZ1bmN0aW9uICgpIHtcclxuICAgIGZ1bmN0aW9uIFBvaW50KCkge1xyXG4gICAgfVxyXG4gICAgcmV0dXJuIFBvaW50O1xyXG59KCkpO1xyXG5leHBvcnRzLlBvaW50ID0gUG9pbnQ7XHJcbnZhciBMaW5lU2VnbWVudCA9IChmdW5jdGlvbiAoKSB7XHJcbiAgICBmdW5jdGlvbiBMaW5lU2VnbWVudCh4MSwgeTEsIHgyLCB5Mikge1xyXG4gICAgICAgIHRoaXMueDEgPSB4MTtcclxuICAgICAgICB0aGlzLnkxID0geTE7XHJcbiAgICAgICAgdGhpcy54MiA9IHgyO1xyXG4gICAgICAgIHRoaXMueTIgPSB5MjtcclxuICAgIH1cclxuICAgIHJldHVybiBMaW5lU2VnbWVudDtcclxufSgpKTtcclxuZXhwb3J0cy5MaW5lU2VnbWVudCA9IExpbmVTZWdtZW50O1xyXG52YXIgUG9seVBvaW50ID0gKGZ1bmN0aW9uIChfc3VwZXIpIHtcclxuICAgIF9fZXh0ZW5kcyhQb2x5UG9pbnQsIF9zdXBlcik7XHJcbiAgICBmdW5jdGlvbiBQb2x5UG9pbnQoKSB7XHJcbiAgICAgICAgcmV0dXJuIF9zdXBlciAhPT0gbnVsbCAmJiBfc3VwZXIuYXBwbHkodGhpcywgYXJndW1lbnRzKSB8fCB0aGlzO1xyXG4gICAgfVxyXG4gICAgcmV0dXJuIFBvbHlQb2ludDtcclxufShQb2ludCkpO1xyXG5leHBvcnRzLlBvbHlQb2ludCA9IFBvbHlQb2ludDtcclxuZnVuY3Rpb24gaXNMZWZ0KFAwLCBQMSwgUDIpIHtcclxuICAgIHJldHVybiAoUDEueCAtIFAwLngpICogKFAyLnkgLSBQMC55KSAtIChQMi54IC0gUDAueCkgKiAoUDEueSAtIFAwLnkpO1xyXG59XHJcbmV4cG9ydHMuaXNMZWZ0ID0gaXNMZWZ0O1xyXG5mdW5jdGlvbiBhYm92ZShwLCB2aSwgdmopIHtcclxuICAgIHJldHVybiBpc0xlZnQocCwgdmksIHZqKSA+IDA7XHJcbn1cclxuZnVuY3Rpb24gYmVsb3cocCwgdmksIHZqKSB7XHJcbiAgICByZXR1cm4gaXNMZWZ0KHAsIHZpLCB2aikgPCAwO1xyXG59XHJcbmZ1bmN0aW9uIENvbnZleEh1bGwoUykge1xyXG4gICAgdmFyIFAgPSBTLnNsaWNlKDApLnNvcnQoZnVuY3Rpb24gKGEsIGIpIHsgcmV0dXJuIGEueCAhPT0gYi54ID8gYi54IC0gYS54IDogYi55IC0gYS55OyB9KTtcclxuICAgIHZhciBuID0gUy5sZW5ndGgsIGk7XHJcbiAgICB2YXIgbWlubWluID0gMDtcclxuICAgIHZhciB4bWluID0gUFswXS54O1xyXG4gICAgZm9yIChpID0gMTsgaSA8IG47ICsraSkge1xyXG4gICAgICAgIGlmIChQW2ldLnggIT09IHhtaW4pXHJcbiAgICAgICAgICAgIGJyZWFrO1xyXG4gICAgfVxyXG4gICAgdmFyIG1pbm1heCA9IGkgLSAxO1xyXG4gICAgdmFyIEggPSBbXTtcclxuICAgIEgucHVzaChQW21pbm1pbl0pO1xyXG4gICAgaWYgKG1pbm1heCA9PT0gbiAtIDEpIHtcclxuICAgICAgICBpZiAoUFttaW5tYXhdLnkgIT09IFBbbWlubWluXS55KVxyXG4gICAgICAgICAgICBILnB1c2goUFttaW5tYXhdKTtcclxuICAgIH1cclxuICAgIGVsc2Uge1xyXG4gICAgICAgIHZhciBtYXhtaW4sIG1heG1heCA9IG4gLSAxO1xyXG4gICAgICAgIHZhciB4bWF4ID0gUFtuIC0gMV0ueDtcclxuICAgICAgICBmb3IgKGkgPSBuIC0gMjsgaSA+PSAwOyBpLS0pXHJcbiAgICAgICAgICAgIGlmIChQW2ldLnggIT09IHhtYXgpXHJcbiAgICAgICAgICAgICAgICBicmVhaztcclxuICAgICAgICBtYXhtaW4gPSBpICsgMTtcclxuICAgICAgICBpID0gbWlubWF4O1xyXG4gICAgICAgIHdoaWxlICgrK2kgPD0gbWF4bWluKSB7XHJcbiAgICAgICAgICAgIGlmIChpc0xlZnQoUFttaW5taW5dLCBQW21heG1pbl0sIFBbaV0pID49IDAgJiYgaSA8IG1heG1pbilcclxuICAgICAgICAgICAgICAgIGNvbnRpbnVlO1xyXG4gICAgICAgICAgICB3aGlsZSAoSC5sZW5ndGggPiAxKSB7XHJcbiAgICAgICAgICAgICAgICBpZiAoaXNMZWZ0KEhbSC5sZW5ndGggLSAyXSwgSFtILmxlbmd0aCAtIDFdLCBQW2ldKSA+IDApXHJcbiAgICAgICAgICAgICAgICAgICAgYnJlYWs7XHJcbiAgICAgICAgICAgICAgICBlbHNlXHJcbiAgICAgICAgICAgICAgICAgICAgSC5sZW5ndGggLT0gMTtcclxuICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICBpZiAoaSAhPSBtaW5taW4pXHJcbiAgICAgICAgICAgICAgICBILnB1c2goUFtpXSk7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIGlmIChtYXhtYXggIT0gbWF4bWluKVxyXG4gICAgICAgICAgICBILnB1c2goUFttYXhtYXhdKTtcclxuICAgICAgICB2YXIgYm90ID0gSC5sZW5ndGg7XHJcbiAgICAgICAgaSA9IG1heG1pbjtcclxuICAgICAgICB3aGlsZSAoLS1pID49IG1pbm1heCkge1xyXG4gICAgICAgICAgICBpZiAoaXNMZWZ0KFBbbWF4bWF4XSwgUFttaW5tYXhdLCBQW2ldKSA+PSAwICYmIGkgPiBtaW5tYXgpXHJcbiAgICAgICAgICAgICAgICBjb250aW51ZTtcclxuICAgICAgICAgICAgd2hpbGUgKEgubGVuZ3RoID4gYm90KSB7XHJcbiAgICAgICAgICAgICAgICBpZiAoaXNMZWZ0KEhbSC5sZW5ndGggLSAyXSwgSFtILmxlbmd0aCAtIDFdLCBQW2ldKSA+IDApXHJcbiAgICAgICAgICAgICAgICAgICAgYnJlYWs7XHJcbiAgICAgICAgICAgICAgICBlbHNlXHJcbiAgICAgICAgICAgICAgICAgICAgSC5sZW5ndGggLT0gMTtcclxuICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICBpZiAoaSAhPSBtaW5taW4pXHJcbiAgICAgICAgICAgICAgICBILnB1c2goUFtpXSk7XHJcbiAgICAgICAgfVxyXG4gICAgfVxyXG4gICAgcmV0dXJuIEg7XHJcbn1cclxuZXhwb3J0cy5Db252ZXhIdWxsID0gQ29udmV4SHVsbDtcclxuZnVuY3Rpb24gY2xvY2t3aXNlUmFkaWFsU3dlZXAocCwgUCwgZikge1xyXG4gICAgUC5zbGljZSgwKS5zb3J0KGZ1bmN0aW9uIChhLCBiKSB7IHJldHVybiBNYXRoLmF0YW4yKGEueSAtIHAueSwgYS54IC0gcC54KSAtIE1hdGguYXRhbjIoYi55IC0gcC55LCBiLnggLSBwLngpOyB9KS5mb3JFYWNoKGYpO1xyXG59XHJcbmV4cG9ydHMuY2xvY2t3aXNlUmFkaWFsU3dlZXAgPSBjbG9ja3dpc2VSYWRpYWxTd2VlcDtcclxuZnVuY3Rpb24gbmV4dFBvbHlQb2ludChwLCBwcykge1xyXG4gICAgaWYgKHAucG9seUluZGV4ID09PSBwcy5sZW5ndGggLSAxKVxyXG4gICAgICAgIHJldHVybiBwc1swXTtcclxuICAgIHJldHVybiBwc1twLnBvbHlJbmRleCArIDFdO1xyXG59XHJcbmZ1bmN0aW9uIHByZXZQb2x5UG9pbnQocCwgcHMpIHtcclxuICAgIGlmIChwLnBvbHlJbmRleCA9PT0gMClcclxuICAgICAgICByZXR1cm4gcHNbcHMubGVuZ3RoIC0gMV07XHJcbiAgICByZXR1cm4gcHNbcC5wb2x5SW5kZXggLSAxXTtcclxufVxyXG5mdW5jdGlvbiB0YW5nZW50X1BvaW50UG9seUMoUCwgVikge1xyXG4gICAgdmFyIFZjbG9zZWQgPSBWLnNsaWNlKDApO1xyXG4gICAgVmNsb3NlZC5wdXNoKFZbMF0pO1xyXG4gICAgcmV0dXJuIHsgcnRhbjogUnRhbmdlbnRfUG9pbnRQb2x5QyhQLCBWY2xvc2VkKSwgbHRhbjogTHRhbmdlbnRfUG9pbnRQb2x5QyhQLCBWY2xvc2VkKSB9O1xyXG59XHJcbmZ1bmN0aW9uIFJ0YW5nZW50X1BvaW50UG9seUMoUCwgVikge1xyXG4gICAgdmFyIG4gPSBWLmxlbmd0aCAtIDE7XHJcbiAgICB2YXIgYSwgYiwgYztcclxuICAgIHZhciB1cEEsIGRuQztcclxuICAgIGlmIChiZWxvdyhQLCBWWzFdLCBWWzBdKSAmJiAhYWJvdmUoUCwgVltuIC0gMV0sIFZbMF0pKVxyXG4gICAgICAgIHJldHVybiAwO1xyXG4gICAgZm9yIChhID0gMCwgYiA9IG47Oykge1xyXG4gICAgICAgIGlmIChiIC0gYSA9PT0gMSlcclxuICAgICAgICAgICAgaWYgKGFib3ZlKFAsIFZbYV0sIFZbYl0pKVxyXG4gICAgICAgICAgICAgICAgcmV0dXJuIGE7XHJcbiAgICAgICAgICAgIGVsc2VcclxuICAgICAgICAgICAgICAgIHJldHVybiBiO1xyXG4gICAgICAgIGMgPSBNYXRoLmZsb29yKChhICsgYikgLyAyKTtcclxuICAgICAgICBkbkMgPSBiZWxvdyhQLCBWW2MgKyAxXSwgVltjXSk7XHJcbiAgICAgICAgaWYgKGRuQyAmJiAhYWJvdmUoUCwgVltjIC0gMV0sIFZbY10pKVxyXG4gICAgICAgICAgICByZXR1cm4gYztcclxuICAgICAgICB1cEEgPSBhYm92ZShQLCBWW2EgKyAxXSwgVlthXSk7XHJcbiAgICAgICAgaWYgKHVwQSkge1xyXG4gICAgICAgICAgICBpZiAoZG5DKVxyXG4gICAgICAgICAgICAgICAgYiA9IGM7XHJcbiAgICAgICAgICAgIGVsc2Uge1xyXG4gICAgICAgICAgICAgICAgaWYgKGFib3ZlKFAsIFZbYV0sIFZbY10pKVxyXG4gICAgICAgICAgICAgICAgICAgIGIgPSBjO1xyXG4gICAgICAgICAgICAgICAgZWxzZVxyXG4gICAgICAgICAgICAgICAgICAgIGEgPSBjO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgfVxyXG4gICAgICAgIGVsc2Uge1xyXG4gICAgICAgICAgICBpZiAoIWRuQylcclxuICAgICAgICAgICAgICAgIGEgPSBjO1xyXG4gICAgICAgICAgICBlbHNlIHtcclxuICAgICAgICAgICAgICAgIGlmIChiZWxvdyhQLCBWW2FdLCBWW2NdKSlcclxuICAgICAgICAgICAgICAgICAgICBiID0gYztcclxuICAgICAgICAgICAgICAgIGVsc2VcclxuICAgICAgICAgICAgICAgICAgICBhID0gYztcclxuICAgICAgICAgICAgfVxyXG4gICAgICAgIH1cclxuICAgIH1cclxufVxyXG5mdW5jdGlvbiBMdGFuZ2VudF9Qb2ludFBvbHlDKFAsIFYpIHtcclxuICAgIHZhciBuID0gVi5sZW5ndGggLSAxO1xyXG4gICAgdmFyIGEsIGIsIGM7XHJcbiAgICB2YXIgZG5BLCBkbkM7XHJcbiAgICBpZiAoYWJvdmUoUCwgVltuIC0gMV0sIFZbMF0pICYmICFiZWxvdyhQLCBWWzFdLCBWWzBdKSlcclxuICAgICAgICByZXR1cm4gMDtcclxuICAgIGZvciAoYSA9IDAsIGIgPSBuOzspIHtcclxuICAgICAgICBpZiAoYiAtIGEgPT09IDEpXHJcbiAgICAgICAgICAgIGlmIChiZWxvdyhQLCBWW2FdLCBWW2JdKSlcclxuICAgICAgICAgICAgICAgIHJldHVybiBhO1xyXG4gICAgICAgICAgICBlbHNlXHJcbiAgICAgICAgICAgICAgICByZXR1cm4gYjtcclxuICAgICAgICBjID0gTWF0aC5mbG9vcigoYSArIGIpIC8gMik7XHJcbiAgICAgICAgZG5DID0gYmVsb3coUCwgVltjICsgMV0sIFZbY10pO1xyXG4gICAgICAgIGlmIChhYm92ZShQLCBWW2MgLSAxXSwgVltjXSkgJiYgIWRuQylcclxuICAgICAgICAgICAgcmV0dXJuIGM7XHJcbiAgICAgICAgZG5BID0gYmVsb3coUCwgVlthICsgMV0sIFZbYV0pO1xyXG4gICAgICAgIGlmIChkbkEpIHtcclxuICAgICAgICAgICAgaWYgKCFkbkMpXHJcbiAgICAgICAgICAgICAgICBiID0gYztcclxuICAgICAgICAgICAgZWxzZSB7XHJcbiAgICAgICAgICAgICAgICBpZiAoYmVsb3coUCwgVlthXSwgVltjXSkpXHJcbiAgICAgICAgICAgICAgICAgICAgYiA9IGM7XHJcbiAgICAgICAgICAgICAgICBlbHNlXHJcbiAgICAgICAgICAgICAgICAgICAgYSA9IGM7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICB9XHJcbiAgICAgICAgZWxzZSB7XHJcbiAgICAgICAgICAgIGlmIChkbkMpXHJcbiAgICAgICAgICAgICAgICBhID0gYztcclxuICAgICAgICAgICAgZWxzZSB7XHJcbiAgICAgICAgICAgICAgICBpZiAoYWJvdmUoUCwgVlthXSwgVltjXSkpXHJcbiAgICAgICAgICAgICAgICAgICAgYiA9IGM7XHJcbiAgICAgICAgICAgICAgICBlbHNlXHJcbiAgICAgICAgICAgICAgICAgICAgYSA9IGM7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICB9XHJcbiAgICB9XHJcbn1cclxuZnVuY3Rpb24gdGFuZ2VudF9Qb2x5UG9seUMoViwgVywgdDEsIHQyLCBjbXAxLCBjbXAyKSB7XHJcbiAgICB2YXIgaXgxLCBpeDI7XHJcbiAgICBpeDEgPSB0MShXWzBdLCBWKTtcclxuICAgIGl4MiA9IHQyKFZbaXgxXSwgVyk7XHJcbiAgICB2YXIgZG9uZSA9IGZhbHNlO1xyXG4gICAgd2hpbGUgKCFkb25lKSB7XHJcbiAgICAgICAgZG9uZSA9IHRydWU7XHJcbiAgICAgICAgd2hpbGUgKHRydWUpIHtcclxuICAgICAgICAgICAgaWYgKGl4MSA9PT0gVi5sZW5ndGggLSAxKVxyXG4gICAgICAgICAgICAgICAgaXgxID0gMDtcclxuICAgICAgICAgICAgaWYgKGNtcDEoV1tpeDJdLCBWW2l4MV0sIFZbaXgxICsgMV0pKVxyXG4gICAgICAgICAgICAgICAgYnJlYWs7XHJcbiAgICAgICAgICAgICsraXgxO1xyXG4gICAgICAgIH1cclxuICAgICAgICB3aGlsZSAodHJ1ZSkge1xyXG4gICAgICAgICAgICBpZiAoaXgyID09PSAwKVxyXG4gICAgICAgICAgICAgICAgaXgyID0gVy5sZW5ndGggLSAxO1xyXG4gICAgICAgICAgICBpZiAoY21wMihWW2l4MV0sIFdbaXgyXSwgV1tpeDIgLSAxXSkpXHJcbiAgICAgICAgICAgICAgICBicmVhaztcclxuICAgICAgICAgICAgLS1peDI7XHJcbiAgICAgICAgICAgIGRvbmUgPSBmYWxzZTtcclxuICAgICAgICB9XHJcbiAgICB9XHJcbiAgICByZXR1cm4geyB0MTogaXgxLCB0MjogaXgyIH07XHJcbn1cclxuZXhwb3J0cy50YW5nZW50X1BvbHlQb2x5QyA9IHRhbmdlbnRfUG9seVBvbHlDO1xyXG5mdW5jdGlvbiBMUnRhbmdlbnRfUG9seVBvbHlDKFYsIFcpIHtcclxuICAgIHZhciBybCA9IFJMdGFuZ2VudF9Qb2x5UG9seUMoVywgVik7XHJcbiAgICByZXR1cm4geyB0MTogcmwudDIsIHQyOiBybC50MSB9O1xyXG59XHJcbmV4cG9ydHMuTFJ0YW5nZW50X1BvbHlQb2x5QyA9IExSdGFuZ2VudF9Qb2x5UG9seUM7XHJcbmZ1bmN0aW9uIFJMdGFuZ2VudF9Qb2x5UG9seUMoViwgVykge1xyXG4gICAgcmV0dXJuIHRhbmdlbnRfUG9seVBvbHlDKFYsIFcsIFJ0YW5nZW50X1BvaW50UG9seUMsIEx0YW5nZW50X1BvaW50UG9seUMsIGFib3ZlLCBiZWxvdyk7XHJcbn1cclxuZXhwb3J0cy5STHRhbmdlbnRfUG9seVBvbHlDID0gUkx0YW5nZW50X1BvbHlQb2x5QztcclxuZnVuY3Rpb24gTEx0YW5nZW50X1BvbHlQb2x5QyhWLCBXKSB7XHJcbiAgICByZXR1cm4gdGFuZ2VudF9Qb2x5UG9seUMoViwgVywgTHRhbmdlbnRfUG9pbnRQb2x5QywgTHRhbmdlbnRfUG9pbnRQb2x5QywgYmVsb3csIGJlbG93KTtcclxufVxyXG5leHBvcnRzLkxMdGFuZ2VudF9Qb2x5UG9seUMgPSBMTHRhbmdlbnRfUG9seVBvbHlDO1xyXG5mdW5jdGlvbiBSUnRhbmdlbnRfUG9seVBvbHlDKFYsIFcpIHtcclxuICAgIHJldHVybiB0YW5nZW50X1BvbHlQb2x5QyhWLCBXLCBSdGFuZ2VudF9Qb2ludFBvbHlDLCBSdGFuZ2VudF9Qb2ludFBvbHlDLCBhYm92ZSwgYWJvdmUpO1xyXG59XHJcbmV4cG9ydHMuUlJ0YW5nZW50X1BvbHlQb2x5QyA9IFJSdGFuZ2VudF9Qb2x5UG9seUM7XHJcbnZhciBCaVRhbmdlbnQgPSAoZnVuY3Rpb24gKCkge1xyXG4gICAgZnVuY3Rpb24gQmlUYW5nZW50KHQxLCB0Mikge1xyXG4gICAgICAgIHRoaXMudDEgPSB0MTtcclxuICAgICAgICB0aGlzLnQyID0gdDI7XHJcbiAgICB9XHJcbiAgICByZXR1cm4gQmlUYW5nZW50O1xyXG59KCkpO1xyXG5leHBvcnRzLkJpVGFuZ2VudCA9IEJpVGFuZ2VudDtcclxudmFyIEJpVGFuZ2VudHMgPSAoZnVuY3Rpb24gKCkge1xyXG4gICAgZnVuY3Rpb24gQmlUYW5nZW50cygpIHtcclxuICAgIH1cclxuICAgIHJldHVybiBCaVRhbmdlbnRzO1xyXG59KCkpO1xyXG5leHBvcnRzLkJpVGFuZ2VudHMgPSBCaVRhbmdlbnRzO1xyXG52YXIgVFZHUG9pbnQgPSAoZnVuY3Rpb24gKF9zdXBlcikge1xyXG4gICAgX19leHRlbmRzKFRWR1BvaW50LCBfc3VwZXIpO1xyXG4gICAgZnVuY3Rpb24gVFZHUG9pbnQoKSB7XHJcbiAgICAgICAgcmV0dXJuIF9zdXBlciAhPT0gbnVsbCAmJiBfc3VwZXIuYXBwbHkodGhpcywgYXJndW1lbnRzKSB8fCB0aGlzO1xyXG4gICAgfVxyXG4gICAgcmV0dXJuIFRWR1BvaW50O1xyXG59KFBvaW50KSk7XHJcbmV4cG9ydHMuVFZHUG9pbnQgPSBUVkdQb2ludDtcclxudmFyIFZpc2liaWxpdHlWZXJ0ZXggPSAoZnVuY3Rpb24gKCkge1xyXG4gICAgZnVuY3Rpb24gVmlzaWJpbGl0eVZlcnRleChpZCwgcG9seWlkLCBwb2x5dmVydGlkLCBwKSB7XHJcbiAgICAgICAgdGhpcy5pZCA9IGlkO1xyXG4gICAgICAgIHRoaXMucG9seWlkID0gcG9seWlkO1xyXG4gICAgICAgIHRoaXMucG9seXZlcnRpZCA9IHBvbHl2ZXJ0aWQ7XHJcbiAgICAgICAgdGhpcy5wID0gcDtcclxuICAgICAgICBwLnZ2ID0gdGhpcztcclxuICAgIH1cclxuICAgIHJldHVybiBWaXNpYmlsaXR5VmVydGV4O1xyXG59KCkpO1xyXG5leHBvcnRzLlZpc2liaWxpdHlWZXJ0ZXggPSBWaXNpYmlsaXR5VmVydGV4O1xyXG52YXIgVmlzaWJpbGl0eUVkZ2UgPSAoZnVuY3Rpb24gKCkge1xyXG4gICAgZnVuY3Rpb24gVmlzaWJpbGl0eUVkZ2Uoc291cmNlLCB0YXJnZXQpIHtcclxuICAgICAgICB0aGlzLnNvdXJjZSA9IHNvdXJjZTtcclxuICAgICAgICB0aGlzLnRhcmdldCA9IHRhcmdldDtcclxuICAgIH1cclxuICAgIFZpc2liaWxpdHlFZGdlLnByb3RvdHlwZS5sZW5ndGggPSBmdW5jdGlvbiAoKSB7XHJcbiAgICAgICAgdmFyIGR4ID0gdGhpcy5zb3VyY2UucC54IC0gdGhpcy50YXJnZXQucC54O1xyXG4gICAgICAgIHZhciBkeSA9IHRoaXMuc291cmNlLnAueSAtIHRoaXMudGFyZ2V0LnAueTtcclxuICAgICAgICByZXR1cm4gTWF0aC5zcXJ0KGR4ICogZHggKyBkeSAqIGR5KTtcclxuICAgIH07XHJcbiAgICByZXR1cm4gVmlzaWJpbGl0eUVkZ2U7XHJcbn0oKSk7XHJcbmV4cG9ydHMuVmlzaWJpbGl0eUVkZ2UgPSBWaXNpYmlsaXR5RWRnZTtcclxudmFyIFRhbmdlbnRWaXNpYmlsaXR5R3JhcGggPSAoZnVuY3Rpb24gKCkge1xyXG4gICAgZnVuY3Rpb24gVGFuZ2VudFZpc2liaWxpdHlHcmFwaChQLCBnMCkge1xyXG4gICAgICAgIHRoaXMuUCA9IFA7XHJcbiAgICAgICAgdGhpcy5WID0gW107XHJcbiAgICAgICAgdGhpcy5FID0gW107XHJcbiAgICAgICAgaWYgKCFnMCkge1xyXG4gICAgICAgICAgICB2YXIgbiA9IFAubGVuZ3RoO1xyXG4gICAgICAgICAgICBmb3IgKHZhciBpID0gMDsgaSA8IG47IGkrKykge1xyXG4gICAgICAgICAgICAgICAgdmFyIHAgPSBQW2ldO1xyXG4gICAgICAgICAgICAgICAgZm9yICh2YXIgaiA9IDA7IGogPCBwLmxlbmd0aDsgKytqKSB7XHJcbiAgICAgICAgICAgICAgICAgICAgdmFyIHBqID0gcFtqXSwgdnYgPSBuZXcgVmlzaWJpbGl0eVZlcnRleCh0aGlzLlYubGVuZ3RoLCBpLCBqLCBwaik7XHJcbiAgICAgICAgICAgICAgICAgICAgdGhpcy5WLnB1c2godnYpO1xyXG4gICAgICAgICAgICAgICAgICAgIGlmIChqID4gMClcclxuICAgICAgICAgICAgICAgICAgICAgICAgdGhpcy5FLnB1c2gobmV3IFZpc2liaWxpdHlFZGdlKHBbaiAtIDFdLnZ2LCB2dikpO1xyXG4gICAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICAgICAgaWYgKHAubGVuZ3RoID4gMSlcclxuICAgICAgICAgICAgICAgICAgICB0aGlzLkUucHVzaChuZXcgVmlzaWJpbGl0eUVkZ2UocFswXS52diwgcFtwLmxlbmd0aCAtIDFdLnZ2KSk7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgZm9yICh2YXIgaSA9IDA7IGkgPCBuIC0gMTsgaSsrKSB7XHJcbiAgICAgICAgICAgICAgICB2YXIgUGkgPSBQW2ldO1xyXG4gICAgICAgICAgICAgICAgZm9yICh2YXIgaiA9IGkgKyAxOyBqIDwgbjsgaisrKSB7XHJcbiAgICAgICAgICAgICAgICAgICAgdmFyIFBqID0gUFtqXSwgdCA9IHRhbmdlbnRzKFBpLCBQaik7XHJcbiAgICAgICAgICAgICAgICAgICAgZm9yICh2YXIgcSBpbiB0KSB7XHJcbiAgICAgICAgICAgICAgICAgICAgICAgIHZhciBjID0gdFtxXSwgc291cmNlID0gUGlbYy50MV0sIHRhcmdldCA9IFBqW2MudDJdO1xyXG4gICAgICAgICAgICAgICAgICAgICAgICB0aGlzLmFkZEVkZ2VJZlZpc2libGUoc291cmNlLCB0YXJnZXQsIGksIGopO1xyXG4gICAgICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgfVxyXG4gICAgICAgIH1cclxuICAgICAgICBlbHNlIHtcclxuICAgICAgICAgICAgdGhpcy5WID0gZzAuVi5zbGljZSgwKTtcclxuICAgICAgICAgICAgdGhpcy5FID0gZzAuRS5zbGljZSgwKTtcclxuICAgICAgICB9XHJcbiAgICB9XHJcbiAgICBUYW5nZW50VmlzaWJpbGl0eUdyYXBoLnByb3RvdHlwZS5hZGRFZGdlSWZWaXNpYmxlID0gZnVuY3Rpb24gKHUsIHYsIGkxLCBpMikge1xyXG4gICAgICAgIGlmICghdGhpcy5pbnRlcnNlY3RzUG9seXMobmV3IExpbmVTZWdtZW50KHUueCwgdS55LCB2LngsIHYueSksIGkxLCBpMikpIHtcclxuICAgICAgICAgICAgdGhpcy5FLnB1c2gobmV3IFZpc2liaWxpdHlFZGdlKHUudnYsIHYudnYpKTtcclxuICAgICAgICB9XHJcbiAgICB9O1xyXG4gICAgVGFuZ2VudFZpc2liaWxpdHlHcmFwaC5wcm90b3R5cGUuYWRkUG9pbnQgPSBmdW5jdGlvbiAocCwgaTEpIHtcclxuICAgICAgICB2YXIgbiA9IHRoaXMuUC5sZW5ndGg7XHJcbiAgICAgICAgdGhpcy5WLnB1c2gobmV3IFZpc2liaWxpdHlWZXJ0ZXgodGhpcy5WLmxlbmd0aCwgbiwgMCwgcCkpO1xyXG4gICAgICAgIGZvciAodmFyIGkgPSAwOyBpIDwgbjsgKytpKSB7XHJcbiAgICAgICAgICAgIGlmIChpID09PSBpMSlcclxuICAgICAgICAgICAgICAgIGNvbnRpbnVlO1xyXG4gICAgICAgICAgICB2YXIgcG9seSA9IHRoaXMuUFtpXSwgdCA9IHRhbmdlbnRfUG9pbnRQb2x5QyhwLCBwb2x5KTtcclxuICAgICAgICAgICAgdGhpcy5hZGRFZGdlSWZWaXNpYmxlKHAsIHBvbHlbdC5sdGFuXSwgaTEsIGkpO1xyXG4gICAgICAgICAgICB0aGlzLmFkZEVkZ2VJZlZpc2libGUocCwgcG9seVt0LnJ0YW5dLCBpMSwgaSk7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIHJldHVybiBwLnZ2O1xyXG4gICAgfTtcclxuICAgIFRhbmdlbnRWaXNpYmlsaXR5R3JhcGgucHJvdG90eXBlLmludGVyc2VjdHNQb2x5cyA9IGZ1bmN0aW9uIChsLCBpMSwgaTIpIHtcclxuICAgICAgICBmb3IgKHZhciBpID0gMCwgbiA9IHRoaXMuUC5sZW5ndGg7IGkgPCBuOyArK2kpIHtcclxuICAgICAgICAgICAgaWYgKGkgIT0gaTEgJiYgaSAhPSBpMiAmJiBpbnRlcnNlY3RzKGwsIHRoaXMuUFtpXSkubGVuZ3RoID4gMCkge1xyXG4gICAgICAgICAgICAgICAgcmV0dXJuIHRydWU7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICB9XHJcbiAgICAgICAgcmV0dXJuIGZhbHNlO1xyXG4gICAgfTtcclxuICAgIHJldHVybiBUYW5nZW50VmlzaWJpbGl0eUdyYXBoO1xyXG59KCkpO1xyXG5leHBvcnRzLlRhbmdlbnRWaXNpYmlsaXR5R3JhcGggPSBUYW5nZW50VmlzaWJpbGl0eUdyYXBoO1xyXG5mdW5jdGlvbiBpbnRlcnNlY3RzKGwsIFApIHtcclxuICAgIHZhciBpbnRzID0gW107XHJcbiAgICBmb3IgKHZhciBpID0gMSwgbiA9IFAubGVuZ3RoOyBpIDwgbjsgKytpKSB7XHJcbiAgICAgICAgdmFyIGludCA9IHJlY3RhbmdsZV8xLlJlY3RhbmdsZS5saW5lSW50ZXJzZWN0aW9uKGwueDEsIGwueTEsIGwueDIsIGwueTIsIFBbaSAtIDFdLngsIFBbaSAtIDFdLnksIFBbaV0ueCwgUFtpXS55KTtcclxuICAgICAgICBpZiAoaW50KVxyXG4gICAgICAgICAgICBpbnRzLnB1c2goaW50KTtcclxuICAgIH1cclxuICAgIHJldHVybiBpbnRzO1xyXG59XHJcbmZ1bmN0aW9uIHRhbmdlbnRzKFYsIFcpIHtcclxuICAgIHZhciBtID0gVi5sZW5ndGggLSAxLCBuID0gVy5sZW5ndGggLSAxO1xyXG4gICAgdmFyIGJ0ID0gbmV3IEJpVGFuZ2VudHMoKTtcclxuICAgIGZvciAodmFyIGkgPSAwOyBpIDw9IG07ICsraSkge1xyXG4gICAgICAgIGZvciAodmFyIGogPSAwOyBqIDw9IG47ICsraikge1xyXG4gICAgICAgICAgICB2YXIgdjEgPSBWW2kgPT0gMCA/IG0gOiBpIC0gMV07XHJcbiAgICAgICAgICAgIHZhciB2MiA9IFZbaV07XHJcbiAgICAgICAgICAgIHZhciB2MyA9IFZbaSA9PSBtID8gMCA6IGkgKyAxXTtcclxuICAgICAgICAgICAgdmFyIHcxID0gV1tqID09IDAgPyBuIDogaiAtIDFdO1xyXG4gICAgICAgICAgICB2YXIgdzIgPSBXW2pdO1xyXG4gICAgICAgICAgICB2YXIgdzMgPSBXW2ogPT0gbiA/IDAgOiBqICsgMV07XHJcbiAgICAgICAgICAgIHZhciB2MXYydzIgPSBpc0xlZnQodjEsIHYyLCB3Mik7XHJcbiAgICAgICAgICAgIHZhciB2MncxdzIgPSBpc0xlZnQodjIsIHcxLCB3Mik7XHJcbiAgICAgICAgICAgIHZhciB2MncydzMgPSBpc0xlZnQodjIsIHcyLCB3Myk7XHJcbiAgICAgICAgICAgIHZhciB3MXcydjIgPSBpc0xlZnQodzEsIHcyLCB2Mik7XHJcbiAgICAgICAgICAgIHZhciB3MnYxdjIgPSBpc0xlZnQodzIsIHYxLCB2Mik7XHJcbiAgICAgICAgICAgIHZhciB3MnYydjMgPSBpc0xlZnQodzIsIHYyLCB2Myk7XHJcbiAgICAgICAgICAgIGlmICh2MXYydzIgPj0gMCAmJiB2MncxdzIgPj0gMCAmJiB2MncydzMgPCAwXHJcbiAgICAgICAgICAgICAgICAmJiB3MXcydjIgPj0gMCAmJiB3MnYxdjIgPj0gMCAmJiB3MnYydjMgPCAwKSB7XHJcbiAgICAgICAgICAgICAgICBidC5sbCA9IG5ldyBCaVRhbmdlbnQoaSwgaik7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgZWxzZSBpZiAodjF2MncyIDw9IDAgJiYgdjJ3MXcyIDw9IDAgJiYgdjJ3MnczID4gMFxyXG4gICAgICAgICAgICAgICAgJiYgdzF3MnYyIDw9IDAgJiYgdzJ2MXYyIDw9IDAgJiYgdzJ2MnYzID4gMCkge1xyXG4gICAgICAgICAgICAgICAgYnQucnIgPSBuZXcgQmlUYW5nZW50KGksIGopO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgICAgIGVsc2UgaWYgKHYxdjJ3MiA8PSAwICYmIHYydzF3MiA+IDAgJiYgdjJ3MnczIDw9IDBcclxuICAgICAgICAgICAgICAgICYmIHcxdzJ2MiA+PSAwICYmIHcydjF2MiA8IDAgJiYgdzJ2MnYzID49IDApIHtcclxuICAgICAgICAgICAgICAgIGJ0LnJsID0gbmV3IEJpVGFuZ2VudChpLCBqKTtcclxuICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICBlbHNlIGlmICh2MXYydzIgPj0gMCAmJiB2MncxdzIgPCAwICYmIHYydzJ3MyA+PSAwXHJcbiAgICAgICAgICAgICAgICAmJiB3MXcydjIgPD0gMCAmJiB3MnYxdjIgPiAwICYmIHcydjJ2MyA8PSAwKSB7XHJcbiAgICAgICAgICAgICAgICBidC5sciA9IG5ldyBCaVRhbmdlbnQoaSwgaik7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICB9XHJcbiAgICB9XHJcbiAgICByZXR1cm4gYnQ7XHJcbn1cclxuZXhwb3J0cy50YW5nZW50cyA9IHRhbmdlbnRzO1xyXG5mdW5jdGlvbiBpc1BvaW50SW5zaWRlUG9seShwLCBwb2x5KSB7XHJcbiAgICBmb3IgKHZhciBpID0gMSwgbiA9IHBvbHkubGVuZ3RoOyBpIDwgbjsgKytpKVxyXG4gICAgICAgIGlmIChiZWxvdyhwb2x5W2kgLSAxXSwgcG9seVtpXSwgcCkpXHJcbiAgICAgICAgICAgIHJldHVybiBmYWxzZTtcclxuICAgIHJldHVybiB0cnVlO1xyXG59XHJcbmZ1bmN0aW9uIGlzQW55UEluUShwLCBxKSB7XHJcbiAgICByZXR1cm4gIXAuZXZlcnkoZnVuY3Rpb24gKHYpIHsgcmV0dXJuICFpc1BvaW50SW5zaWRlUG9seSh2LCBxKTsgfSk7XHJcbn1cclxuZnVuY3Rpb24gcG9seXNPdmVybGFwKHAsIHEpIHtcclxuICAgIGlmIChpc0FueVBJblEocCwgcSkpXHJcbiAgICAgICAgcmV0dXJuIHRydWU7XHJcbiAgICBpZiAoaXNBbnlQSW5RKHEsIHApKVxyXG4gICAgICAgIHJldHVybiB0cnVlO1xyXG4gICAgZm9yICh2YXIgaSA9IDEsIG4gPSBwLmxlbmd0aDsgaSA8IG47ICsraSkge1xyXG4gICAgICAgIHZhciB2ID0gcFtpXSwgdSA9IHBbaSAtIDFdO1xyXG4gICAgICAgIGlmIChpbnRlcnNlY3RzKG5ldyBMaW5lU2VnbWVudCh1LngsIHUueSwgdi54LCB2LnkpLCBxKS5sZW5ndGggPiAwKVxyXG4gICAgICAgICAgICByZXR1cm4gdHJ1ZTtcclxuICAgIH1cclxuICAgIHJldHVybiBmYWxzZTtcclxufVxyXG5leHBvcnRzLnBvbHlzT3ZlcmxhcCA9IHBvbHlzT3ZlcmxhcDtcclxuLy8jIHNvdXJjZU1hcHBpbmdVUkw9ZGF0YTphcHBsaWNhdGlvbi9qc29uO2Jhc2U2NCxleUoyWlhKemFXOXVJam96TENKbWFXeGxJam9pWjJWdmJTNXFjeUlzSW5OdmRYSmpaVkp2YjNRaU9pSWlMQ0p6YjNWeVkyVnpJanBiSWk0dUx5NHVMMWRsWWtOdmJHRXZjM0pqTDJkbGIyMHVkSE1pWFN3aWJtRnRaWE1pT2x0ZExDSnRZWEJ3YVc1bmN5STZJanM3T3pzN096czdPenM3T3pzN08wRkJRVUVzZVVOQlFYRkRPMEZCUTJwRE8wbEJRVUU3U1VGSFFTeERRVUZETzBsQlFVUXNXVUZCUXp0QlFVRkVMRU5CUVVNc1FVRklSQ3hKUVVkRE8wRkJTRmtzYzBKQlFVczdRVUZMYkVJN1NVRkRTU3h4UWtGQmJVSXNSVUZCVlN4RlFVRlRMRVZCUVZVc1JVRkJVeXhGUVVGVkxFVkJRVk1zUlVGQlZUdFJRVUZ1UlN4UFFVRkZMRWRCUVVZc1JVRkJSU3hEUVVGUk8xRkJRVk1zVDBGQlJTeEhRVUZHTEVWQlFVVXNRMEZCVVR0UlFVRlRMRTlCUVVVc1IwRkJSaXhGUVVGRkxFTkJRVkU3VVVGQlV5eFBRVUZGTEVkQlFVWXNSVUZCUlN4RFFVRlJPMGxCUVVrc1EwRkJRenRKUVVNdlJpeHJRa0ZCUXp0QlFVRkVMRU5CUVVNc1FVRkdSQ3hKUVVWRE8wRkJSbGtzYTBOQlFWYzdRVUZKZUVJN1NVRkJLMElzTmtKQlFVczdTVUZCY0VNN08wbEJSVUVzUTBGQlF6dEpRVUZFTEdkQ1FVRkRPMEZCUVVRc1EwRkJReXhCUVVaRUxFTkJRU3RDTEV0QlFVc3NSMEZGYmtNN1FVRkdXU3c0UWtGQlV6dEJRVlYwUWl4VFFVRm5RaXhOUVVGTkxFTkJRVU1zUlVGQlV5eEZRVUZGTEVWQlFWTXNSVUZCUlN4RlFVRlRPMGxCUTJ4RUxFOUJRVThzUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXl4SFFVRkhMRVZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlJ5eERRVUZETEVWQlFVVXNRMEZCUXl4RFFVRkRMRWRCUVVjc1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF5eEhRVUZITEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1IwRkJSeXhGUVVGRkxFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NRMEZCUXl4RlFVRkZMRU5CUVVNc1EwRkJReXhIUVVGSExFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0QlFVTjZSU3hEUVVGRE8wRkJSa1FzZDBKQlJVTTdRVUZGUkN4VFFVRlRMRXRCUVVzc1EwRkJReXhEUVVGUkxFVkJRVVVzUlVGQlV5eEZRVUZGTEVWQlFWTTdTVUZEZWtNc1QwRkJUeXhOUVVGTkxFTkJRVU1zUTBGQlF5eEZRVUZGTEVWQlFVVXNSVUZCUlN4RlFVRkZMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU03UVVGRGFrTXNRMEZCUXp0QlFVVkVMRk5CUVZNc1MwRkJTeXhEUVVGRExFTkJRVkVzUlVGQlJTeEZRVUZUTEVWQlFVVXNSVUZCVXp0SlFVTjZReXhQUVVGUExFMUJRVTBzUTBGQlF5eERRVUZETEVWQlFVVXNSVUZCUlN4RlFVRkZMRVZCUVVVc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF6dEJRVU5xUXl4RFFVRkRPMEZCVTBRc1UwRkJaMElzVlVGQlZTeERRVUZETEVOQlFWVTdTVUZEYWtNc1NVRkJTU3hEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETEV0QlFVc3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhKUVVGSkxFTkJRVU1zVlVGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4SlFVRkxMRTlCUVVFc1EwRkJReXhEUVVGRExFTkJRVU1zUzBGQlN5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkJia01zUTBGQmJVTXNRMEZCUXl4RFFVRkRPMGxCUTNaRkxFbEJRVWtzUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXl4TlFVRk5MRVZCUVVVc1EwRkJReXhEUVVGRE8wbEJRM0JDTEVsQlFVa3NUVUZCVFN4SFFVRkhMRU5CUVVNc1EwRkJRenRKUVVObUxFbEJRVWtzU1VGQlNTeEhRVUZITEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03U1VGRGJFSXNTMEZCU3l4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRkxFTkJRVU1zUjBGQlJ5eERRVUZETEVWQlFVVXNSVUZCUlN4RFFVRkRMRVZCUVVVN1VVRkRjRUlzU1VGQlNTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhMUVVGTExFbEJRVWs3V1VGQlJTeE5RVUZOTzB0QlF6bENPMGxCUTBRc1NVRkJTU3hOUVVGTkxFZEJRVWNzUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXp0SlFVTnVRaXhKUVVGSkxFTkJRVU1zUjBGQldTeEZRVUZGTEVOQlFVTTdTVUZEY0VJc1EwRkJReXhEUVVGRExFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNUVUZCVFN4RFFVRkRMRU5CUVVNc1EwRkJRenRKUVVOc1FpeEpRVUZKTEUxQlFVMHNTMEZCU3l4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRk8xRkJRMnhDTEVsQlFVa3NRMEZCUXl4RFFVRkRMRTFCUVUwc1EwRkJReXhEUVVGRExFTkJRVU1zUzBGQlN5eERRVUZETEVOQlFVTXNUVUZCVFN4RFFVRkRMRU5CUVVNc1EwRkJRenRaUVVNelFpeERRVUZETEVOQlFVTXNTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJReXhOUVVGTkxFTkJRVU1zUTBGQlF5eERRVUZETzB0QlEzcENPMU5CUVUwN1VVRkZTQ3hKUVVGSkxFMUJRVTBzUlVGQlJTeE5RVUZOTEVkQlFVY3NRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJRenRSUVVNelFpeEpRVUZKTEVsQlFVa3NSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0UlFVTjBRaXhMUVVGTExFTkJRVU1zUjBGQlJ5eERRVUZETEVkQlFVY3NRMEZCUXl4RlFVRkZMRU5CUVVNc1NVRkJTU3hEUVVGRExFVkJRVVVzUTBGQlF5eEZRVUZGTzFsQlEzWkNMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNTMEZCU3l4SlFVRkpPMmRDUVVGRkxFMUJRVTA3VVVGREwwSXNUVUZCVFN4SFFVRkhMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU03VVVGSFppeERRVUZETEVkQlFVY3NUVUZCVFN4RFFVRkRPMUZCUTFnc1QwRkJUeXhGUVVGRkxFTkJRVU1zU1VGQlNTeE5RVUZOTEVWQlFVVTdXVUZGYkVJc1NVRkJTU3hOUVVGTkxFTkJRVU1zUTBGQlF5eERRVUZETEUxQlFVMHNRMEZCUXl4RlFVRkZMRU5CUVVNc1EwRkJReXhOUVVGTkxFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1NVRkJTU3hEUVVGRExFbEJRVWtzUTBGQlF5eEhRVUZITEUxQlFVMDdaMEpCUTNKRUxGTkJRVk03V1VGRllpeFBRVUZQTEVOQlFVTXNRMEZCUXl4TlFVRk5MRWRCUVVjc1EwRkJReXhGUVVOdVFqdG5Ra0ZGU1N4SlFVRkpMRTFCUVUwc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEUxQlFVMHNSMEZCUnl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEUxQlFVMHNSMEZCUnl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4RFFVRkRPMjlDUVVOc1JDeE5RVUZOT3p0dlFrRkZUaXhEUVVGRExFTkJRVU1zVFVGQlRTeEpRVUZKTEVOQlFVTXNRMEZCUXp0aFFVTnlRanRaUVVORUxFbEJRVWtzUTBGQlF5eEpRVUZKTEUxQlFVMDdaMEpCUVVVc1EwRkJReXhEUVVGRExFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRUUVVOcVF6dFJRVWRFTEVsQlFVa3NUVUZCVFN4SlFVRkpMRTFCUVUwN1dVRkRhRUlzUTBGQlF5eERRVUZETEVsQlFVa3NRMEZCUXl4RFFVRkRMRU5CUVVNc1RVRkJUU3hEUVVGRExFTkJRVU1zUTBGQlF6dFJRVU4wUWl4SlFVRkpMRWRCUVVjc1IwRkJSeXhEUVVGRExFTkJRVU1zVFVGQlRTeERRVUZETzFGQlEyNUNMRU5CUVVNc1IwRkJSeXhOUVVGTkxFTkJRVU03VVVGRFdDeFBRVUZQTEVWQlFVVXNRMEZCUXl4SlFVRkpMRTFCUVUwc1JVRkJSVHRaUVVWc1FpeEpRVUZKTEUxQlFVMHNRMEZCUXl4RFFVRkRMRU5CUVVNc1RVRkJUU3hEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETEUxQlFVMHNRMEZCUXl4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEpRVUZKTEVOQlFVTXNTVUZCU1N4RFFVRkRMRWRCUVVjc1RVRkJUVHRuUWtGRGNrUXNVMEZCVXp0WlFVVmlMRTlCUVU4c1EwRkJReXhEUVVGRExFMUJRVTBzUjBGQlJ5eEhRVUZITEVWQlEzSkNPMmRDUVVWSkxFbEJRVWtzVFVGQlRTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1RVRkJUU3hIUVVGSExFTkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1RVRkJUU3hIUVVGSExFTkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU03YjBKQlEyeEVMRTFCUVUwN08yOUNRVVZPTEVOQlFVTXNRMEZCUXl4TlFVRk5MRWxCUVVrc1EwRkJReXhEUVVGRE8yRkJRM0pDTzFsQlEwUXNTVUZCU1N4RFFVRkRMRWxCUVVrc1RVRkJUVHRuUWtGQlJTeERRVUZETEVOQlFVTXNTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzFOQlEycERPMHRCUTBvN1NVRkRSQ3hQUVVGUExFTkJRVU1zUTBGQlF6dEJRVU5pTEVOQlFVTTdRVUU1UkVRc1owTkJPRVJETzBGQlIwUXNVMEZCWjBJc2IwSkJRVzlDTEVOQlFVTXNRMEZCVVN4RlFVRkZMRU5CUVZVc1JVRkJSU3hEUVVGeFFqdEpRVU0xUlN4RFFVRkRMRU5CUVVNc1MwRkJTeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVsQlFVa3NRMEZEV0N4VlFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFbEJRVXNzVDBGQlFTeEpRVUZKTEVOQlFVTXNTMEZCU3l4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4SlFVRkpMRU5CUVVNc1MwRkJTeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkJia1VzUTBGQmJVVXNRMEZETlVVc1EwRkJReXhQUVVGUExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdRVUZEY2tJc1EwRkJRenRCUVVwRUxHOUVRVWxETzBGQlJVUXNVMEZCVXl4aFFVRmhMRU5CUVVNc1EwRkJXU3hGUVVGRkxFVkJRV1U3U1VGRGFFUXNTVUZCU1N4RFFVRkRMRU5CUVVNc1UwRkJVeXhMUVVGTExFVkJRVVVzUTBGQlF5eE5RVUZOTEVkQlFVY3NRMEZCUXp0UlFVRkZMRTlCUVU4c1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzBsQlEyaEVMRTlCUVU4c1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF5eFRRVUZUTEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNN1FVRkRMMElzUTBGQlF6dEJRVVZFTEZOQlFWTXNZVUZCWVN4RFFVRkRMRU5CUVZrc1JVRkJSU3hGUVVGbE8wbEJRMmhFTEVsQlFVa3NRMEZCUXl4RFFVRkRMRk5CUVZNc1MwRkJTeXhEUVVGRE8xRkJRVVVzVDBGQlR5eEZRVUZGTEVOQlFVTXNSVUZCUlN4RFFVRkRMRTFCUVUwc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF6dEpRVU5vUkN4UFFVRlBMRVZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU1zVTBGQlV5eEhRVUZITEVOQlFVTXNRMEZCUXl4RFFVRkRPMEZCUXk5Q0xFTkJRVU03UVVGUlJDeFRRVUZUTEd0Q1FVRnJRaXhEUVVGRExFTkJRVkVzUlVGQlJTeERRVUZWTzBsQlJ6VkRMRWxCUVVrc1QwRkJUeXhIUVVGSExFTkJRVU1zUTBGQlF5eExRVUZMTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1NVRkRla0lzVDBGQlR5eERRVUZETEVsQlFVa3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dEpRVVZ1UWl4UFFVRlBMRVZCUVVVc1NVRkJTU3hGUVVGRkxHMUNRVUZ0UWl4RFFVRkRMRU5CUVVNc1JVRkJSU3hQUVVGUExFTkJRVU1zUlVGQlJTeEpRVUZKTEVWQlFVVXNiVUpCUVcxQ0xFTkJRVU1zUTBGQlF5eEZRVUZGTEU5QlFVOHNRMEZCUXl4RlFVRkZMRU5CUVVNN1FVRkROVVlzUTBGQlF6dEJRVk5FTEZOQlFWTXNiVUpCUVcxQ0xFTkJRVU1zUTBGQlVTeEZRVUZGTEVOQlFWVTdTVUZETjBNc1NVRkJTU3hEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETEUxQlFVMHNSMEZCUnl4RFFVRkRMRU5CUVVNN1NVRkhja0lzU1VGQlNTeERRVUZUTEVWQlFVVXNRMEZCVXl4RlFVRkZMRU5CUVZNc1EwRkJRenRKUVVOd1F5eEpRVUZKTEVkQlFWa3NSVUZCUlN4SFFVRlpMRU5CUVVNN1NVRkpMMElzU1VGQlNTeExRVUZMTEVOQlFVTXNRMEZCUXl4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1NVRkJTU3hEUVVGRExFdEJRVXNzUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1VVRkRha1FzVDBGQlR5eERRVUZETEVOQlFVTTdTVUZGWWl4TFFVRkxMRU5CUVVNc1IwRkJSeXhEUVVGRExFVkJRVVVzUTBGQlF5eEhRVUZITEVOQlFVTXNTVUZCU3p0UlFVTnNRaXhKUVVGSkxFTkJRVU1zUjBGQlJ5eERRVUZETEV0QlFVc3NRMEZCUXp0WlFVTllMRWxCUVVrc1MwRkJTeXhEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzJkQ1FVTndRaXhQUVVGUExFTkJRVU1zUTBGQlF6czdaMEpCUlZRc1QwRkJUeXhEUVVGRExFTkJRVU03VVVGRmFrSXNRMEZCUXl4SFFVRkhMRWxCUVVrc1EwRkJReXhMUVVGTExFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU03VVVGRE5VSXNSMEZCUnl4SFFVRkhMRXRCUVVzc1EwRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0UlFVTXZRaXhKUVVGSkxFZEJRVWNzU1VGQlNTeERRVUZETEV0QlFVc3NRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03V1VGRGFFTXNUMEZCVHl4RFFVRkRMRU5CUVVNN1VVRkpZaXhIUVVGSExFZEJRVWNzUzBGQlN5eERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8xRkJReTlDTEVsQlFVa3NSMEZCUnl4RlFVRkZPMWxCUTB3c1NVRkJTU3hIUVVGSE8yZENRVU5JTEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNN2FVSkJRMHc3WjBKQlEwUXNTVUZCU1N4TFFVRkxMRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03YjBKQlEzQkNMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU03TzI5Q1FVVk9MRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU03WVVGRFlqdFRRVU5LTzJGQlEwazdXVUZEUkN4SlFVRkpMRU5CUVVNc1IwRkJSenRuUWtGRFNpeERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRPMmxDUVVOTU8yZENRVU5FTEVsQlFVa3NTMEZCU3l4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8yOUNRVU53UWl4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRE96dHZRa0ZGVGl4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRE8yRkJRMkk3VTBGRFNqdExRVU5LTzBGQlEwd3NRMEZCUXp0QlFWRkVMRk5CUVZNc2JVSkJRVzFDTEVOQlFVTXNRMEZCVVN4RlFVRkZMRU5CUVZVN1NVRkROME1zU1VGQlNTeERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRTFCUVUwc1IwRkJSeXhEUVVGRExFTkJRVU03U1VGRmNrSXNTVUZCU1N4RFFVRlRMRVZCUVVVc1EwRkJVeXhGUVVGRkxFTkJRVk1zUTBGQlF6dEpRVU53UXl4SlFVRkpMRWRCUVZrc1JVRkJSU3hIUVVGWkxFTkJRVU03U1VGSkwwSXNTVUZCU1N4TFFVRkxMRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVsQlFVa3NRMEZCUXl4TFFVRkxMRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03VVVGRGFrUXNUMEZCVHl4RFFVRkRMRU5CUVVNN1NVRkZZaXhMUVVGTExFTkJRVU1zUjBGQlJ5eERRVUZETEVWQlFVVXNRMEZCUXl4SFFVRkhMRU5CUVVNc1NVRkJTenRSUVVOc1FpeEpRVUZKTEVOQlFVTXNSMEZCUnl4RFFVRkRMRXRCUVVzc1EwRkJRenRaUVVOWUxFbEJRVWtzUzBGQlN5eERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMmRDUVVOd1FpeFBRVUZQTEVOQlFVTXNRMEZCUXpzN1owSkJSVlFzVDBGQlR5eERRVUZETEVOQlFVTTdVVUZGYWtJc1EwRkJReXhIUVVGSExFbEJRVWtzUTBGQlF5eExRVUZMTEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETEVOQlFVTTdVVUZETlVJc1IwRkJSeXhIUVVGSExFdEJRVXNzUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRSUVVNdlFpeEpRVUZKTEV0QlFVc3NRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zU1VGQlNTeERRVUZETEVkQlFVYzdXVUZEYUVNc1QwRkJUeXhEUVVGRExFTkJRVU03VVVGSllpeEhRVUZITEVkQlFVY3NTMEZCU3l4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXl4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzFGQlF5OUNMRWxCUVVrc1IwRkJSeXhGUVVGRk8xbEJRMHdzU1VGQlNTeERRVUZETEVkQlFVYzdaMEpCUTBvc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF6dHBRa0ZEVER0blFrRkRSQ3hKUVVGSkxFdEJRVXNzUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0dlFrRkRjRUlzUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXpzN2IwSkJSVTRzUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXp0aFFVTmlPMU5CUTBvN1lVRkRTVHRaUVVORUxFbEJRVWtzUjBGQlJ6dG5Ra0ZEU0N4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRE8ybENRVU5NTzJkQ1FVTkVMRWxCUVVrc1MwRkJTeXhEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzI5Q1FVTndRaXhEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZET3p0dlFrRkZUaXhEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETzJGQlEySTdVMEZEU2p0TFFVTktPMEZCUTB3c1EwRkJRenRCUVZORUxGTkJRV2RDTEdsQ1FVRnBRaXhEUVVGRExFTkJRVlVzUlVGQlJTeERRVUZWTEVWQlFVVXNSVUZCYjBNc1JVRkJSU3hGUVVGdlF5eEZRVUZGTEVsQlFTdERMRVZCUVVVc1NVRkJLME03U1VGRGJFOHNTVUZCU1N4SFFVRlhMRVZCUVVVc1IwRkJWeXhEUVVGRE8wbEJSemRDTEVkQlFVY3NSMEZCUnl4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRPMGxCUTJ4Q0xFZEJRVWNzUjBGQlJ5eEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF5eERRVUZETzBsQlIzQkNMRWxCUVVrc1NVRkJTU3hIUVVGSExFdEJRVXNzUTBGQlF6dEpRVU5xUWl4UFFVRlBMRU5CUVVNc1NVRkJTU3hGUVVGRk8xRkJRMVlzU1VGQlNTeEhRVUZITEVsQlFVa3NRMEZCUXp0UlFVTmFMRTlCUVU4c1NVRkJTU3hGUVVGRk8xbEJRMVFzU1VGQlNTeEhRVUZITEV0QlFVc3NRMEZCUXl4RFFVRkRMRTFCUVUwc1IwRkJSeXhEUVVGRE8yZENRVUZGTEVkQlFVY3NSMEZCUnl4RFFVRkRMRU5CUVVNN1dVRkRiRU1zU1VGQlNTeEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF5eEhRVUZITEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1IwRkJSeXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETzJkQ1FVRkZMRTFCUVUwN1dVRkROVU1zUlVGQlJTeEhRVUZITEVOQlFVTTdVMEZEVkR0UlFVTkVMRTlCUVU4c1NVRkJTU3hGUVVGRk8xbEJRMVFzU1VGQlNTeEhRVUZITEV0QlFVc3NRMEZCUXp0blFrRkJSU3hIUVVGSExFZEJRVWNzUTBGQlF5eERRVUZETEUxQlFVMHNSMEZCUnl4RFFVRkRMRU5CUVVNN1dVRkRiRU1zU1VGQlNTeEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF5eEhRVUZITEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1IwRkJSeXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETzJkQ1FVRkZMRTFCUVUwN1dVRkROVU1zUlVGQlJTeEhRVUZITEVOQlFVTTdXVUZEVGl4SlFVRkpMRWRCUVVjc1MwRkJTeXhEUVVGRE8xTkJRMmhDTzB0QlEwbzdTVUZEUkN4UFFVRlBMRVZCUVVVc1JVRkJSU3hGUVVGRkxFZEJRVWNzUlVGQlJTeEZRVUZGTEVWQlFVVXNSMEZCUnl4RlFVRkZMRU5CUVVNN1FVRkRhRU1zUTBGQlF6dEJRWGhDUkN3NFEwRjNRa003UVVGRlJDeFRRVUZuUWl4dFFrRkJiVUlzUTBGQlF5eERRVUZWTEVWQlFVVXNRMEZCVlR0SlFVTjBSQ3hKUVVGSkxFVkJRVVVzUjBGQlJ5eHRRa0ZCYlVJc1EwRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTTdTVUZEYmtNc1QwRkJUeXhGUVVGRkxFVkJRVVVzUlVGQlJTeEZRVUZGTEVOQlFVTXNSVUZCUlN4RlFVRkZMRVZCUVVVc1JVRkJSU3hGUVVGRkxFTkJRVU1zUlVGQlJTeEZRVUZGTEVOQlFVTTdRVUZEY0VNc1EwRkJRenRCUVVoRUxHdEVRVWRETzBGQlJVUXNVMEZCWjBJc2JVSkJRVzFDTEVOQlFVTXNRMEZCVlN4RlFVRkZMRU5CUVZVN1NVRkRkRVFzVDBGQlR5eHBRa0ZCYVVJc1EwRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eEZRVUZGTEcxQ1FVRnRRaXhGUVVGRkxHMUNRVUZ0UWl4RlFVRkZMRXRCUVVzc1JVRkJSU3hMUVVGTExFTkJRVU1zUTBGQlF6dEJRVU16Uml4RFFVRkRPMEZCUmtRc2EwUkJSVU03UVVGRlJDeFRRVUZuUWl4dFFrRkJiVUlzUTBGQlF5eERRVUZWTEVWQlFVVXNRMEZCVlR0SlFVTjBSQ3hQUVVGUExHbENRVUZwUWl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFVkJRVVVzYlVKQlFXMUNMRVZCUVVVc2JVSkJRVzFDTEVWQlFVVXNTMEZCU3l4RlFVRkZMRXRCUVVzc1EwRkJReXhEUVVGRE8wRkJRek5HTEVOQlFVTTdRVUZHUkN4clJFRkZRenRCUVVWRUxGTkJRV2RDTEcxQ1FVRnRRaXhEUVVGRExFTkJRVlVzUlVGQlJTeERRVUZWTzBsQlEzUkVMRTlCUVU4c2FVSkJRV2xDTEVOQlFVTXNRMEZCUXl4RlFVRkZMRU5CUVVNc1JVRkJSU3h0UWtGQmJVSXNSVUZCUlN4dFFrRkJiVUlzUlVGQlJTeExRVUZMTEVWQlFVVXNTMEZCU3l4RFFVRkRMRU5CUVVNN1FVRkRNMFlzUTBGQlF6dEJRVVpFTEd0RVFVVkRPMEZCUlVRN1NVRkRTU3h0UWtGQmJVSXNSVUZCVlN4RlFVRlRMRVZCUVZVN1VVRkJOMElzVDBGQlJTeEhRVUZHTEVWQlFVVXNRMEZCVVR0UlFVRlRMRTlCUVVVc1IwRkJSaXhGUVVGRkxFTkJRVkU3U1VGQlNTeERRVUZETzBsQlEzcEVMR2RDUVVGRE8wRkJRVVFzUTBGQlF5eEJRVVpFTEVsQlJVTTdRVUZHV1N3NFFrRkJVenRCUVVsMFFqdEpRVUZCTzBsQlMwRXNRMEZCUXp0SlFVRkVMR2xDUVVGRE8wRkJRVVFzUTBGQlF5eEJRVXhFTEVsQlMwTTdRVUZNV1N4blEwRkJWVHRCUVU5MlFqdEpRVUU0UWl3MFFrRkJTenRKUVVGdVF6czdTVUZGUVN4RFFVRkRPMGxCUVVRc1pVRkJRenRCUVVGRUxFTkJRVU1zUVVGR1JDeERRVUU0UWl4TFFVRkxMRWRCUld4RE8wRkJSbGtzTkVKQlFWRTdRVUZKY2tJN1NVRkRTU3d3UWtGRFZ5eEZRVUZWTEVWQlExWXNUVUZCWXl4RlFVTmtMRlZCUVd0Q0xFVkJRMnhDTEVOQlFWYzdVVUZJV0N4UFFVRkZMRWRCUVVZc1JVRkJSU3hEUVVGUk8xRkJRMVlzVjBGQlRTeEhRVUZPTEUxQlFVMHNRMEZCVVR0UlFVTmtMR1ZCUVZVc1IwRkJWaXhWUVVGVkxFTkJRVkU3VVVGRGJFSXNUVUZCUXl4SFFVRkVMRU5CUVVNc1EwRkJWVHRSUVVWc1FpeERRVUZETEVOQlFVTXNSVUZCUlN4SFFVRkhMRWxCUVVrc1EwRkJRenRKUVVOb1FpeERRVUZETzBsQlEwd3NkVUpCUVVNN1FVRkJSQ3hEUVVGRExFRkJWRVFzU1VGVFF6dEJRVlJaTERSRFFVRm5RanRCUVZjM1FqdEpRVU5KTEhkQ1FVTlhMRTFCUVhkQ0xFVkJRM2hDTEUxQlFYZENPMUZCUkhoQ0xGZEJRVTBzUjBGQlRpeE5RVUZOTEVOQlFXdENPMUZCUTNoQ0xGZEJRVTBzUjBGQlRpeE5RVUZOTEVOQlFXdENPMGxCUVVrc1EwRkJRenRKUVVONFF5d3JRa0ZCVFN4SFFVRk9PMUZCUTBrc1NVRkJTU3hGUVVGRkxFZEJRVWNzU1VGQlNTeERRVUZETEUxQlFVMHNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFbEJRVWtzUTBGQlF5eE5RVUZOTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRSUVVNelF5eEpRVUZKTEVWQlFVVXNSMEZCUnl4SlFVRkpMRU5CUVVNc1RVRkJUU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NTVUZCU1N4RFFVRkRMRTFCUVUwc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzFGQlF6TkRMRTlCUVU4c1NVRkJTU3hEUVVGRExFbEJRVWtzUTBGQlF5eEZRVUZGTEVkQlFVY3NSVUZCUlN4SFFVRkhMRVZCUVVVc1IwRkJSeXhGUVVGRkxFTkJRVU1zUTBGQlF6dEpRVU40UXl4RFFVRkRPMGxCUTB3c2NVSkJRVU03UVVGQlJDeERRVUZETEVGQlZFUXNTVUZUUXp0QlFWUlpMSGREUVVGak8wRkJWek5DTzBsQlIwa3NaME5CUVcxQ0xFTkJRV1VzUlVGQlJTeEZRVUZ0UkR0UlFVRndSU3hOUVVGRExFZEJRVVFzUTBGQlF5eERRVUZqTzFGQlJteERMRTFCUVVNc1IwRkJkVUlzUlVGQlJTeERRVUZETzFGQlF6TkNMRTFCUVVNc1IwRkJjVUlzUlVGQlJTeERRVUZETzFGQlJYSkNMRWxCUVVrc1EwRkJReXhGUVVGRkxFVkJRVVU3V1VGRFRDeEpRVUZKTEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1RVRkJUU3hEUVVGRE8xbEJSV3BDTEV0QlFVc3NTVUZCU1N4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRkxFTkJRVU1zUjBGQlJ5eERRVUZETEVWQlFVVXNRMEZCUXl4RlFVRkZMRVZCUVVVN1owSkJRM2hDTEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dG5Ra0ZGWWl4TFFVRkxMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRTFCUVUwc1JVRkJSU3hGUVVGRkxFTkJRVU1zUlVGQlJUdHZRa0ZETDBJc1NVRkJTU3hGUVVGRkxFZEJRVWNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RlFVTlVMRVZCUVVVc1IwRkJSeXhKUVVGSkxHZENRVUZuUWl4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU1zVFVGQlRTeEZRVUZGTEVOQlFVTXNSVUZCUlN4RFFVRkRMRVZCUVVVc1JVRkJSU3hEUVVGRExFTkJRVU03YjBKQlEzWkVMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU1zU1VGQlNTeERRVUZETEVWQlFVVXNRMEZCUXl4RFFVRkRPMjlDUVVsb1FpeEpRVUZKTEVOQlFVTXNSMEZCUnl4RFFVRkRPM2RDUVVGRkxFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNTVUZCU1N4RFFVRkRMRWxCUVVrc1kwRkJZeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkJSU3hGUVVGRkxFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTTdhVUpCUXk5RU8yZENRVVZFTEVsQlFVa3NRMEZCUXl4RFFVRkRMRTFCUVUwc1IwRkJSeXhEUVVGRE8yOUNRVUZGTEVsQlFVa3NRMEZCUXl4RFFVRkRMRU5CUVVNc1NVRkJTU3hEUVVGRExFbEJRVWtzWTBGQll5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGRkxFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4TlFVRk5MRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTXNRMEZCUXp0aFFVTnNSanRaUVVORUxFdEJRVXNzU1VGQlNTeERRVUZETEVkQlFVY3NRMEZCUXl4RlFVRkZMRU5CUVVNc1IwRkJSeXhEUVVGRExFZEJRVWNzUTBGQlF5eEZRVUZGTEVOQlFVTXNSVUZCUlN4RlFVRkZPMmRDUVVNMVFpeEpRVUZKTEVWQlFVVXNSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03WjBKQlEyUXNTMEZCU3l4SlFVRkpMRU5CUVVNc1IwRkJSeXhEUVVGRExFZEJRVWNzUTBGQlF5eEZRVUZGTEVOQlFVTXNSMEZCUnl4RFFVRkRMRVZCUVVVc1EwRkJReXhGUVVGRkxFVkJRVVU3YjBKQlF6VkNMRWxCUVVrc1JVRkJSU3hIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSVUZEVkN4RFFVRkRMRWRCUVVjc1VVRkJVU3hEUVVGRExFVkJRVVVzUlVGQlJTeEZRVUZGTEVOQlFVTXNRMEZCUXp0dlFrRkRla0lzUzBGQlN5eEpRVUZKTEVOQlFVTXNTVUZCU1N4RFFVRkRMRVZCUVVVN2QwSkJRMklzU1VGQlNTeERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVOU0xFMUJRVTBzUjBGQlJ5eEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhGUVVGRkxFMUJRVTBzUjBGQlJ5eEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhEUVVGRE8zZENRVU42UXl4SlFVRkpMRU5CUVVNc1owSkJRV2RDTEVOQlFVTXNUVUZCVFN4RlFVRkZMRTFCUVUwc1JVRkJSU3hEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTTdjVUpCUXk5RE8ybENRVU5LTzJGQlEwbzdVMEZEU2p0aFFVRk5PMWxCUTBnc1NVRkJTU3hEUVVGRExFTkJRVU1zUjBGQlJ5eEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRMRXRCUVVzc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFpRVU4yUWl4SlFVRkpMRU5CUVVNc1EwRkJReXhIUVVGSExFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTXNTMEZCU3l4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8xTkJRekZDTzBsQlEwd3NRMEZCUXp0SlFVTkVMR2xFUVVGblFpeEhRVUZvUWl4VlFVRnBRaXhEUVVGWExFVkJRVVVzUTBGQlZ5eEZRVUZGTEVWQlFWVXNSVUZCUlN4RlFVRlZPMUZCUXpkRUxFbEJRVWtzUTBGQlF5eEpRVUZKTEVOQlFVTXNaVUZCWlN4RFFVRkRMRWxCUVVrc1YwRkJWeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkJSU3hGUVVGRkxFVkJRVVVzUlVGQlJTeERRVUZETEVWQlFVVTdXVUZEY0VVc1NVRkJTU3hEUVVGRExFTkJRVU1zUTBGQlF5eEpRVUZKTEVOQlFVTXNTVUZCU1N4alFVRmpMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRVVVzUlVGQlJTeERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJRenRUUVVNdlF6dEpRVU5NTEVOQlFVTTdTVUZEUkN4NVEwRkJVU3hIUVVGU0xGVkJRVk1zUTBGQlZ5eEZRVUZGTEVWQlFWVTdVVUZETlVJc1NVRkJTU3hEUVVGRExFZEJRVWNzU1VGQlNTeERRVUZETEVOQlFVTXNRMEZCUXl4TlFVRk5MRU5CUVVNN1VVRkRkRUlzU1VGQlNTeERRVUZETEVOQlFVTXNRMEZCUXl4SlFVRkpMRU5CUVVNc1NVRkJTU3huUWtGQlowSXNRMEZCUXl4SlFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRExFMUJRVTBzUlVGQlJTeERRVUZETEVWQlFVVXNRMEZCUXl4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03VVVGRE1VUXNTMEZCU3l4SlFVRkpMRU5CUVVNc1IwRkJSeXhEUVVGRExFVkJRVVVzUTBGQlF5eEhRVUZITEVOQlFVTXNSVUZCUlN4RlFVRkZMRU5CUVVNc1JVRkJSVHRaUVVONFFpeEpRVUZKTEVOQlFVTXNTMEZCU3l4RlFVRkZPMmRDUVVGRkxGTkJRVk03V1VGRGRrSXNTVUZCU1N4SlFVRkpMRWRCUVVjc1NVRkJTU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSVUZEYUVJc1EwRkJReXhIUVVGSExHdENRVUZyUWl4RFFVRkRMRU5CUVVNc1JVRkJSU3hKUVVGSkxFTkJRVU1zUTBGQlF6dFpRVU53UXl4SlFVRkpMRU5CUVVNc1owSkJRV2RDTEVOQlFVTXNRMEZCUXl4RlFVRkZMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU1zU1VGQlNTeERRVUZETEVWQlFVVXNSVUZCUlN4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRE8xbEJRemxETEVsQlFVa3NRMEZCUXl4blFrRkJaMElzUTBGQlF5eERRVUZETEVWQlFVVXNTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJReXhKUVVGSkxFTkJRVU1zUlVGQlJTeEZRVUZGTEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNN1UwRkRha1E3VVVGRFJDeFBRVUZQTEVOQlFVTXNRMEZCUXl4RlFVRkZMRU5CUVVNN1NVRkRhRUlzUTBGQlF6dEpRVU5QTEdkRVFVRmxMRWRCUVhaQ0xGVkJRWGRDTEVOQlFXTXNSVUZCUlN4RlFVRlZMRVZCUVVVc1JVRkJWVHRSUVVNeFJDeExRVUZMTEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1JVRkJSU3hEUVVGRExFZEJRVWNzU1VGQlNTeERRVUZETEVOQlFVTXNRMEZCUXl4TlFVRk5MRVZCUVVVc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeEZRVUZGTEVOQlFVTXNSVUZCUlR0WlFVTXpReXhKUVVGSkxFTkJRVU1zU1VGQlNTeEZRVUZGTEVsQlFVa3NRMEZCUXl4SlFVRkpMRVZCUVVVc1NVRkJTU3hWUVVGVkxFTkJRVU1zUTBGQlF5eEZRVUZGTEVsQlFVa3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eE5RVUZOTEVkQlFVY3NRMEZCUXl4RlFVRkZPMmRDUVVNelJDeFBRVUZQTEVsQlFVa3NRMEZCUXp0aFFVTm1PMU5CUTBvN1VVRkRSQ3hQUVVGUExFdEJRVXNzUTBGQlF6dEpRVU5xUWl4RFFVRkRPMGxCUTB3c05rSkJRVU03UVVGQlJDeERRVUZETEVGQmFFVkVMRWxCWjBWRE8wRkJhRVZaTEhkRVFVRnpRanRCUVd0RmJrTXNVMEZCVXl4VlFVRlZMRU5CUVVNc1EwRkJZeXhGUVVGRkxFTkJRVlU3U1VGRE1VTXNTVUZCU1N4SlFVRkpMRWRCUVVjc1JVRkJSU3hEUVVGRE8wbEJRMlFzUzBGQlN5eEpRVUZKTEVOQlFVTXNSMEZCUnl4RFFVRkRMRVZCUVVVc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eE5RVUZOTEVWQlFVVXNRMEZCUXl4SFFVRkhMRU5CUVVNc1JVRkJSU3hGUVVGRkxFTkJRVU1zUlVGQlJUdFJRVU4wUXl4SlFVRkpMRWRCUVVjc1IwRkJSeXh4UWtGQlV5eERRVUZETEdkQ1FVRm5RaXhEUVVOb1F5eERRVUZETEVOQlFVTXNSVUZCUlN4RlFVRkZMRU5CUVVNc1EwRkJReXhGUVVGRkxFVkJRMVlzUTBGQlF5eERRVUZETEVWQlFVVXNSVUZCUlN4RFFVRkRMRU5CUVVNc1JVRkJSU3hGUVVOV0xFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVOMFFpeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUTJJc1EwRkJRenRSUVVOT0xFbEJRVWtzUjBGQlJ6dFpRVUZGTEVsQlFVa3NRMEZCUXl4SlFVRkpMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU03UzBGRE0wSTdTVUZEUkN4UFFVRlBMRWxCUVVrc1EwRkJRenRCUVVOb1FpeERRVUZETzBGQlJVUXNVMEZCWjBJc1VVRkJVU3hEUVVGRExFTkJRVlVzUlVGQlJTeERRVUZWTzBsQlJUTkRMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eE5RVUZOTEVkQlFVY3NRMEZCUXl4RlFVRkZMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zVFVGQlRTeEhRVUZITEVOQlFVTXNRMEZCUXp0SlFVTjJReXhKUVVGSkxFVkJRVVVzUjBGQlJ5eEpRVUZKTEZWQlFWVXNSVUZCUlN4RFFVRkRPMGxCUXpGQ0xFdEJRVXNzU1VGQlNTeERRVUZETEVkQlFVY3NRMEZCUXl4RlFVRkZMRU5CUVVNc1NVRkJTU3hEUVVGRExFVkJRVVVzUlVGQlJTeERRVUZETEVWQlFVVTdVVUZEZWtJc1MwRkJTeXhKUVVGSkxFTkJRVU1zUjBGQlJ5eERRVUZETEVWQlFVVXNRMEZCUXl4SlFVRkpMRU5CUVVNc1JVRkJSU3hGUVVGRkxFTkJRVU1zUlVGQlJUdFpRVU42UWl4SlFVRkpMRVZCUVVVc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF5eEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNN1dVRkRMMElzU1VGQlNTeEZRVUZGTEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8xbEJRMlFzU1VGQlNTeEZRVUZGTEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1NVRkJTU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETzFsQlF5OUNMRWxCUVVrc1JVRkJSU3hIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVsQlFVa3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJRenRaUVVNdlFpeEpRVUZKTEVWQlFVVXNSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03V1VGRFpDeEpRVUZKTEVWQlFVVXNSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJReXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETEVOQlFVTTdXVUZETDBJc1NVRkJTU3hOUVVGTkxFZEJRVWNzVFVGQlRTeERRVUZETEVWQlFVVXNSVUZCUlN4RlFVRkZMRVZCUVVVc1JVRkJSU3hEUVVGRExFTkJRVU03V1VGRGFFTXNTVUZCU1N4TlFVRk5MRWRCUVVjc1RVRkJUU3hEUVVGRExFVkJRVVVzUlVGQlJTeEZRVUZGTEVWQlFVVXNSVUZCUlN4RFFVRkRMRU5CUVVNN1dVRkRhRU1zU1VGQlNTeE5RVUZOTEVkQlFVY3NUVUZCVFN4RFFVRkRMRVZCUVVVc1JVRkJSU3hGUVVGRkxFVkJRVVVzUlVGQlJTeERRVUZETEVOQlFVTTdXVUZEYUVNc1NVRkJTU3hOUVVGTkxFZEJRVWNzVFVGQlRTeERRVUZETEVWQlFVVXNSVUZCUlN4RlFVRkZMRVZCUVVVc1JVRkJSU3hEUVVGRExFTkJRVU03V1VGRGFFTXNTVUZCU1N4TlFVRk5MRWRCUVVjc1RVRkJUU3hEUVVGRExFVkJRVVVzUlVGQlJTeEZRVUZGTEVWQlFVVXNSVUZCUlN4RFFVRkRMRU5CUVVNN1dVRkRhRU1zU1VGQlNTeE5RVUZOTEVkQlFVY3NUVUZCVFN4RFFVRkRMRVZCUVVVc1JVRkJSU3hGUVVGRkxFVkJRVVVzUlVGQlJTeERRVUZETEVOQlFVTTdXVUZEYUVNc1NVRkJTU3hOUVVGTkxFbEJRVWtzUTBGQlF5eEpRVUZKTEUxQlFVMHNTVUZCU1N4RFFVRkRMRWxCUVVrc1RVRkJUU3hIUVVGSExFTkJRVU03YlVKQlEzSkRMRTFCUVUwc1NVRkJTU3hEUVVGRExFbEJRVWtzVFVGQlRTeEpRVUZKTEVOQlFVTXNTVUZCU1N4TlFVRk5MRWRCUVVjc1EwRkJReXhGUVVGRk8yZENRVU42UXl4RlFVRkZMRU5CUVVNc1JVRkJSU3hIUVVGSExFbEJRVWtzVTBGQlV5eERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJRenRoUVVOdVF6dHBRa0ZCVFN4SlFVRkpMRTFCUVUwc1NVRkJTU3hEUVVGRExFbEJRVWtzVFVGQlRTeEpRVUZKTEVOQlFVTXNTVUZCU1N4TlFVRk5MRWRCUVVjc1EwRkJRenR0UWtGRE5VTXNUVUZCVFN4SlFVRkpMRU5CUVVNc1NVRkJTU3hOUVVGTkxFbEJRVWtzUTBGQlF5eEpRVUZKTEUxQlFVMHNSMEZCUnl4RFFVRkRMRVZCUVVVN1owSkJRM3BETEVWQlFVVXNRMEZCUXl4RlFVRkZMRWRCUVVjc1NVRkJTU3hUUVVGVExFTkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRPMkZCUTI1RE8ybENRVUZOTEVsQlFVa3NUVUZCVFN4SlFVRkpMRU5CUVVNc1NVRkJTU3hOUVVGTkxFZEJRVWNzUTBGQlF5eEpRVUZKTEUxQlFVMHNTVUZCU1N4RFFVRkRPMjFDUVVNMVF5eE5RVUZOTEVsQlFVa3NRMEZCUXl4SlFVRkpMRTFCUVUwc1IwRkJSeXhEUVVGRExFbEJRVWtzVFVGQlRTeEpRVUZKTEVOQlFVTXNSVUZCUlR0blFrRkRla01zUlVGQlJTeERRVUZETEVWQlFVVXNSMEZCUnl4SlFVRkpMRk5CUVZNc1EwRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTTdZVUZEYmtNN2FVSkJRVTBzU1VGQlNTeE5RVUZOTEVsQlFVa3NRMEZCUXl4SlFVRkpMRTFCUVUwc1IwRkJSeXhEUVVGRExFbEJRVWtzVFVGQlRTeEpRVUZKTEVOQlFVTTdiVUpCUXpWRExFMUJRVTBzU1VGQlNTeERRVUZETEVsQlFVa3NUVUZCVFN4SFFVRkhMRU5CUVVNc1NVRkJTU3hOUVVGTkxFbEJRVWtzUTBGQlF5eEZRVUZGTzJkQ1FVTjZReXhGUVVGRkxFTkJRVU1zUlVGQlJTeEhRVUZITEVsQlFVa3NVMEZCVXl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF6dGhRVU51UXp0VFFVTktPMHRCUTBvN1NVRkRSQ3hQUVVGUExFVkJRVVVzUTBGQlF6dEJRVU5rTEVOQlFVTTdRVUZzUTBRc05FSkJhME5ETzBGQlJVUXNVMEZCVXl4cFFrRkJhVUlzUTBGQlF5eERRVUZSTEVWQlFVVXNTVUZCWVR0SlFVTTVReXhMUVVGTExFbEJRVWtzUTBGQlF5eEhRVUZITEVOQlFVTXNSVUZCUlN4RFFVRkRMRWRCUVVjc1NVRkJTU3hEUVVGRExFMUJRVTBzUlVGQlJTeERRVUZETEVkQlFVY3NRMEZCUXl4RlFVRkZMRVZCUVVVc1EwRkJRenRSUVVOMlF5eEpRVUZKTEV0QlFVc3NRMEZCUXl4SlFVRkpMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eEZRVUZGTEVsQlFVa3NRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU03V1VGQlJTeFBRVUZQTEV0QlFVc3NRMEZCUXp0SlFVTnlSQ3hQUVVGUExFbEJRVWtzUTBGQlF6dEJRVU5vUWl4RFFVRkRPMEZCUlVRc1UwRkJVeXhUUVVGVExFTkJRVU1zUTBGQlZTeEZRVUZGTEVOQlFWVTdTVUZEY2tNc1QwRkJUeXhEUVVGRExFTkJRVU1zUTBGQlF5eExRVUZMTEVOQlFVTXNWVUZCUVN4RFFVRkRMRWxCUVVrc1QwRkJRU3hEUVVGRExHbENRVUZwUWl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zUlVGQmVFSXNRMEZCZDBJc1EwRkJReXhEUVVGRE8wRkJRMjVFTEVOQlFVTTdRVUZGUkN4VFFVRm5RaXhaUVVGWkxFTkJRVU1zUTBGQlZTeEZRVUZGTEVOQlFWVTdTVUZETDBNc1NVRkJTU3hUUVVGVExFTkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXp0UlFVRkZMRTlCUVU4c1NVRkJTU3hEUVVGRE8wbEJRMnBETEVsQlFVa3NVMEZCVXl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU03VVVGQlJTeFBRVUZQTEVsQlFVa3NRMEZCUXp0SlFVTnFReXhMUVVGTExFbEJRVWtzUTBGQlF5eEhRVUZITEVOQlFVTXNSVUZCUlN4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFMUJRVTBzUlVGQlJTeERRVUZETEVkQlFVY3NRMEZCUXl4RlFVRkZMRVZCUVVVc1EwRkJReXhGUVVGRk8xRkJRM1JETEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF6dFJRVU16UWl4SlFVRkpMRlZCUVZVc1EwRkJReXhKUVVGSkxGZEJRVmNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTXNUVUZCVFN4SFFVRkhMRU5CUVVNN1dVRkJSU3hQUVVGUExFbEJRVWtzUTBGQlF6dExRVU5zUmp0SlFVTkVMRTlCUVU4c1MwRkJTeXhEUVVGRE8wRkJRMnBDTEVOQlFVTTdRVUZTUkN4dlEwRlJReUo5IiwiXCJ1c2Ugc3RyaWN0XCI7XHJcbk9iamVjdC5kZWZpbmVQcm9wZXJ0eShleHBvcnRzLCBcIl9fZXNNb2R1bGVcIiwgeyB2YWx1ZTogdHJ1ZSB9KTtcclxudmFyIHJlY3RhbmdsZV8xID0gcmVxdWlyZShcIi4vcmVjdGFuZ2xlXCIpO1xyXG52YXIgdnBzY18xID0gcmVxdWlyZShcIi4vdnBzY1wiKTtcclxudmFyIHNob3J0ZXN0cGF0aHNfMSA9IHJlcXVpcmUoXCIuL3Nob3J0ZXN0cGF0aHNcIik7XHJcbnZhciBOb2RlV3JhcHBlciA9IChmdW5jdGlvbiAoKSB7XHJcbiAgICBmdW5jdGlvbiBOb2RlV3JhcHBlcihpZCwgcmVjdCwgY2hpbGRyZW4pIHtcclxuICAgICAgICB0aGlzLmlkID0gaWQ7XHJcbiAgICAgICAgdGhpcy5yZWN0ID0gcmVjdDtcclxuICAgICAgICB0aGlzLmNoaWxkcmVuID0gY2hpbGRyZW47XHJcbiAgICAgICAgdGhpcy5sZWFmID0gdHlwZW9mIGNoaWxkcmVuID09PSAndW5kZWZpbmVkJyB8fCBjaGlsZHJlbi5sZW5ndGggPT09IDA7XHJcbiAgICB9XHJcbiAgICByZXR1cm4gTm9kZVdyYXBwZXI7XHJcbn0oKSk7XHJcbmV4cG9ydHMuTm9kZVdyYXBwZXIgPSBOb2RlV3JhcHBlcjtcclxudmFyIFZlcnQgPSAoZnVuY3Rpb24gKCkge1xyXG4gICAgZnVuY3Rpb24gVmVydChpZCwgeCwgeSwgbm9kZSwgbGluZSkge1xyXG4gICAgICAgIGlmIChub2RlID09PSB2b2lkIDApIHsgbm9kZSA9IG51bGw7IH1cclxuICAgICAgICBpZiAobGluZSA9PT0gdm9pZCAwKSB7IGxpbmUgPSBudWxsOyB9XHJcbiAgICAgICAgdGhpcy5pZCA9IGlkO1xyXG4gICAgICAgIHRoaXMueCA9IHg7XHJcbiAgICAgICAgdGhpcy55ID0geTtcclxuICAgICAgICB0aGlzLm5vZGUgPSBub2RlO1xyXG4gICAgICAgIHRoaXMubGluZSA9IGxpbmU7XHJcbiAgICB9XHJcbiAgICByZXR1cm4gVmVydDtcclxufSgpKTtcclxuZXhwb3J0cy5WZXJ0ID0gVmVydDtcclxudmFyIExvbmdlc3RDb21tb25TdWJzZXF1ZW5jZSA9IChmdW5jdGlvbiAoKSB7XHJcbiAgICBmdW5jdGlvbiBMb25nZXN0Q29tbW9uU3Vic2VxdWVuY2UocywgdCkge1xyXG4gICAgICAgIHRoaXMucyA9IHM7XHJcbiAgICAgICAgdGhpcy50ID0gdDtcclxuICAgICAgICB2YXIgbWYgPSBMb25nZXN0Q29tbW9uU3Vic2VxdWVuY2UuZmluZE1hdGNoKHMsIHQpO1xyXG4gICAgICAgIHZhciB0ciA9IHQuc2xpY2UoMCkucmV2ZXJzZSgpO1xyXG4gICAgICAgIHZhciBtciA9IExvbmdlc3RDb21tb25TdWJzZXF1ZW5jZS5maW5kTWF0Y2gocywgdHIpO1xyXG4gICAgICAgIGlmIChtZi5sZW5ndGggPj0gbXIubGVuZ3RoKSB7XHJcbiAgICAgICAgICAgIHRoaXMubGVuZ3RoID0gbWYubGVuZ3RoO1xyXG4gICAgICAgICAgICB0aGlzLnNpID0gbWYuc2k7XHJcbiAgICAgICAgICAgIHRoaXMudGkgPSBtZi50aTtcclxuICAgICAgICAgICAgdGhpcy5yZXZlcnNlZCA9IGZhbHNlO1xyXG4gICAgICAgIH1cclxuICAgICAgICBlbHNlIHtcclxuICAgICAgICAgICAgdGhpcy5sZW5ndGggPSBtci5sZW5ndGg7XHJcbiAgICAgICAgICAgIHRoaXMuc2kgPSBtci5zaTtcclxuICAgICAgICAgICAgdGhpcy50aSA9IHQubGVuZ3RoIC0gbXIudGkgLSBtci5sZW5ndGg7XHJcbiAgICAgICAgICAgIHRoaXMucmV2ZXJzZWQgPSB0cnVlO1xyXG4gICAgICAgIH1cclxuICAgIH1cclxuICAgIExvbmdlc3RDb21tb25TdWJzZXF1ZW5jZS5maW5kTWF0Y2ggPSBmdW5jdGlvbiAocywgdCkge1xyXG4gICAgICAgIHZhciBtID0gcy5sZW5ndGg7XHJcbiAgICAgICAgdmFyIG4gPSB0Lmxlbmd0aDtcclxuICAgICAgICB2YXIgbWF0Y2ggPSB7IGxlbmd0aDogMCwgc2k6IC0xLCB0aTogLTEgfTtcclxuICAgICAgICB2YXIgbCA9IG5ldyBBcnJheShtKTtcclxuICAgICAgICBmb3IgKHZhciBpID0gMDsgaSA8IG07IGkrKykge1xyXG4gICAgICAgICAgICBsW2ldID0gbmV3IEFycmF5KG4pO1xyXG4gICAgICAgICAgICBmb3IgKHZhciBqID0gMDsgaiA8IG47IGorKylcclxuICAgICAgICAgICAgICAgIGlmIChzW2ldID09PSB0W2pdKSB7XHJcbiAgICAgICAgICAgICAgICAgICAgdmFyIHYgPSBsW2ldW2pdID0gKGkgPT09IDAgfHwgaiA9PT0gMCkgPyAxIDogbFtpIC0gMV1baiAtIDFdICsgMTtcclxuICAgICAgICAgICAgICAgICAgICBpZiAodiA+IG1hdGNoLmxlbmd0aCkge1xyXG4gICAgICAgICAgICAgICAgICAgICAgICBtYXRjaC5sZW5ndGggPSB2O1xyXG4gICAgICAgICAgICAgICAgICAgICAgICBtYXRjaC5zaSA9IGkgLSB2ICsgMTtcclxuICAgICAgICAgICAgICAgICAgICAgICAgbWF0Y2gudGkgPSBqIC0gdiArIDE7XHJcbiAgICAgICAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICAgICAgICAgIDtcclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgIGVsc2VcclxuICAgICAgICAgICAgICAgICAgICBsW2ldW2pdID0gMDtcclxuICAgICAgICB9XHJcbiAgICAgICAgcmV0dXJuIG1hdGNoO1xyXG4gICAgfTtcclxuICAgIExvbmdlc3RDb21tb25TdWJzZXF1ZW5jZS5wcm90b3R5cGUuZ2V0U2VxdWVuY2UgPSBmdW5jdGlvbiAoKSB7XHJcbiAgICAgICAgcmV0dXJuIHRoaXMubGVuZ3RoID49IDAgPyB0aGlzLnMuc2xpY2UodGhpcy5zaSwgdGhpcy5zaSArIHRoaXMubGVuZ3RoKSA6IFtdO1xyXG4gICAgfTtcclxuICAgIHJldHVybiBMb25nZXN0Q29tbW9uU3Vic2VxdWVuY2U7XHJcbn0oKSk7XHJcbmV4cG9ydHMuTG9uZ2VzdENvbW1vblN1YnNlcXVlbmNlID0gTG9uZ2VzdENvbW1vblN1YnNlcXVlbmNlO1xyXG52YXIgR3JpZFJvdXRlciA9IChmdW5jdGlvbiAoKSB7XHJcbiAgICBmdW5jdGlvbiBHcmlkUm91dGVyKG9yaWdpbmFsbm9kZXMsIGFjY2Vzc29yLCBncm91cFBhZGRpbmcpIHtcclxuICAgICAgICB2YXIgX3RoaXMgPSB0aGlzO1xyXG4gICAgICAgIGlmIChncm91cFBhZGRpbmcgPT09IHZvaWQgMCkgeyBncm91cFBhZGRpbmcgPSAxMjsgfVxyXG4gICAgICAgIHRoaXMub3JpZ2luYWxub2RlcyA9IG9yaWdpbmFsbm9kZXM7XHJcbiAgICAgICAgdGhpcy5ncm91cFBhZGRpbmcgPSBncm91cFBhZGRpbmc7XHJcbiAgICAgICAgdGhpcy5sZWF2ZXMgPSBudWxsO1xyXG4gICAgICAgIHRoaXMubm9kZXMgPSBvcmlnaW5hbG5vZGVzLm1hcChmdW5jdGlvbiAodiwgaSkgeyByZXR1cm4gbmV3IE5vZGVXcmFwcGVyKGksIGFjY2Vzc29yLmdldEJvdW5kcyh2KSwgYWNjZXNzb3IuZ2V0Q2hpbGRyZW4odikpOyB9KTtcclxuICAgICAgICB0aGlzLmxlYXZlcyA9IHRoaXMubm9kZXMuZmlsdGVyKGZ1bmN0aW9uICh2KSB7IHJldHVybiB2LmxlYWY7IH0pO1xyXG4gICAgICAgIHRoaXMuZ3JvdXBzID0gdGhpcy5ub2Rlcy5maWx0ZXIoZnVuY3Rpb24gKGcpIHsgcmV0dXJuICFnLmxlYWY7IH0pO1xyXG4gICAgICAgIHRoaXMuY29scyA9IHRoaXMuZ2V0R3JpZExpbmVzKCd4Jyk7XHJcbiAgICAgICAgdGhpcy5yb3dzID0gdGhpcy5nZXRHcmlkTGluZXMoJ3knKTtcclxuICAgICAgICB0aGlzLmdyb3Vwcy5mb3JFYWNoKGZ1bmN0aW9uICh2KSB7XHJcbiAgICAgICAgICAgIHJldHVybiB2LmNoaWxkcmVuLmZvckVhY2goZnVuY3Rpb24gKGMpIHsgcmV0dXJuIF90aGlzLm5vZGVzW2NdLnBhcmVudCA9IHY7IH0pO1xyXG4gICAgICAgIH0pO1xyXG4gICAgICAgIHRoaXMucm9vdCA9IHsgY2hpbGRyZW46IFtdIH07XHJcbiAgICAgICAgdGhpcy5ub2Rlcy5mb3JFYWNoKGZ1bmN0aW9uICh2KSB7XHJcbiAgICAgICAgICAgIGlmICh0eXBlb2Ygdi5wYXJlbnQgPT09ICd1bmRlZmluZWQnKSB7XHJcbiAgICAgICAgICAgICAgICB2LnBhcmVudCA9IF90aGlzLnJvb3Q7XHJcbiAgICAgICAgICAgICAgICBfdGhpcy5yb290LmNoaWxkcmVuLnB1c2godi5pZCk7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgdi5wb3J0cyA9IFtdO1xyXG4gICAgICAgIH0pO1xyXG4gICAgICAgIHRoaXMuYmFja1RvRnJvbnQgPSB0aGlzLm5vZGVzLnNsaWNlKDApO1xyXG4gICAgICAgIHRoaXMuYmFja1RvRnJvbnQuc29ydChmdW5jdGlvbiAoeCwgeSkgeyByZXR1cm4gX3RoaXMuZ2V0RGVwdGgoeCkgLSBfdGhpcy5nZXREZXB0aCh5KTsgfSk7XHJcbiAgICAgICAgdmFyIGZyb250VG9CYWNrR3JvdXBzID0gdGhpcy5iYWNrVG9Gcm9udC5zbGljZSgwKS5yZXZlcnNlKCkuZmlsdGVyKGZ1bmN0aW9uIChnKSB7IHJldHVybiAhZy5sZWFmOyB9KTtcclxuICAgICAgICBmcm9udFRvQmFja0dyb3Vwcy5mb3JFYWNoKGZ1bmN0aW9uICh2KSB7XHJcbiAgICAgICAgICAgIHZhciByID0gcmVjdGFuZ2xlXzEuUmVjdGFuZ2xlLmVtcHR5KCk7XHJcbiAgICAgICAgICAgIHYuY2hpbGRyZW4uZm9yRWFjaChmdW5jdGlvbiAoYykgeyByZXR1cm4gciA9IHIudW5pb24oX3RoaXMubm9kZXNbY10ucmVjdCk7IH0pO1xyXG4gICAgICAgICAgICB2LnJlY3QgPSByLmluZmxhdGUoX3RoaXMuZ3JvdXBQYWRkaW5nKTtcclxuICAgICAgICB9KTtcclxuICAgICAgICB2YXIgY29sTWlkcyA9IHRoaXMubWlkUG9pbnRzKHRoaXMuY29scy5tYXAoZnVuY3Rpb24gKHIpIHsgcmV0dXJuIHIucG9zOyB9KSk7XHJcbiAgICAgICAgdmFyIHJvd01pZHMgPSB0aGlzLm1pZFBvaW50cyh0aGlzLnJvd3MubWFwKGZ1bmN0aW9uIChyKSB7IHJldHVybiByLnBvczsgfSkpO1xyXG4gICAgICAgIHZhciByb3d4ID0gY29sTWlkc1swXSwgcm93WCA9IGNvbE1pZHNbY29sTWlkcy5sZW5ndGggLSAxXTtcclxuICAgICAgICB2YXIgY29seSA9IHJvd01pZHNbMF0sIGNvbFkgPSByb3dNaWRzW3Jvd01pZHMubGVuZ3RoIC0gMV07XHJcbiAgICAgICAgdmFyIGhsaW5lcyA9IHRoaXMucm93cy5tYXAoZnVuY3Rpb24gKHIpIHsgcmV0dXJuICh7IHgxOiByb3d4LCB4Mjogcm93WCwgeTE6IHIucG9zLCB5Mjogci5wb3MgfSk7IH0pXHJcbiAgICAgICAgICAgIC5jb25jYXQocm93TWlkcy5tYXAoZnVuY3Rpb24gKG0pIHsgcmV0dXJuICh7IHgxOiByb3d4LCB4Mjogcm93WCwgeTE6IG0sIHkyOiBtIH0pOyB9KSk7XHJcbiAgICAgICAgdmFyIHZsaW5lcyA9IHRoaXMuY29scy5tYXAoZnVuY3Rpb24gKGMpIHsgcmV0dXJuICh7IHgxOiBjLnBvcywgeDI6IGMucG9zLCB5MTogY29seSwgeTI6IGNvbFkgfSk7IH0pXHJcbiAgICAgICAgICAgIC5jb25jYXQoY29sTWlkcy5tYXAoZnVuY3Rpb24gKG0pIHsgcmV0dXJuICh7IHgxOiBtLCB4MjogbSwgeTE6IGNvbHksIHkyOiBjb2xZIH0pOyB9KSk7XHJcbiAgICAgICAgdmFyIGxpbmVzID0gaGxpbmVzLmNvbmNhdCh2bGluZXMpO1xyXG4gICAgICAgIGxpbmVzLmZvckVhY2goZnVuY3Rpb24gKGwpIHsgcmV0dXJuIGwudmVydHMgPSBbXTsgfSk7XHJcbiAgICAgICAgdGhpcy52ZXJ0cyA9IFtdO1xyXG4gICAgICAgIHRoaXMuZWRnZXMgPSBbXTtcclxuICAgICAgICBobGluZXMuZm9yRWFjaChmdW5jdGlvbiAoaCkge1xyXG4gICAgICAgICAgICByZXR1cm4gdmxpbmVzLmZvckVhY2goZnVuY3Rpb24gKHYpIHtcclxuICAgICAgICAgICAgICAgIHZhciBwID0gbmV3IFZlcnQoX3RoaXMudmVydHMubGVuZ3RoLCB2LngxLCBoLnkxKTtcclxuICAgICAgICAgICAgICAgIGgudmVydHMucHVzaChwKTtcclxuICAgICAgICAgICAgICAgIHYudmVydHMucHVzaChwKTtcclxuICAgICAgICAgICAgICAgIF90aGlzLnZlcnRzLnB1c2gocCk7XHJcbiAgICAgICAgICAgICAgICB2YXIgaSA9IF90aGlzLmJhY2tUb0Zyb250Lmxlbmd0aDtcclxuICAgICAgICAgICAgICAgIHdoaWxlIChpLS0gPiAwKSB7XHJcbiAgICAgICAgICAgICAgICAgICAgdmFyIG5vZGUgPSBfdGhpcy5iYWNrVG9Gcm9udFtpXSwgciA9IG5vZGUucmVjdDtcclxuICAgICAgICAgICAgICAgICAgICB2YXIgZHggPSBNYXRoLmFicyhwLnggLSByLmN4KCkpLCBkeSA9IE1hdGguYWJzKHAueSAtIHIuY3koKSk7XHJcbiAgICAgICAgICAgICAgICAgICAgaWYgKGR4IDwgci53aWR0aCgpIC8gMiAmJiBkeSA8IHIuaGVpZ2h0KCkgLyAyKSB7XHJcbiAgICAgICAgICAgICAgICAgICAgICAgIHAubm9kZSA9IG5vZGU7XHJcbiAgICAgICAgICAgICAgICAgICAgICAgIGJyZWFrO1xyXG4gICAgICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgfSk7XHJcbiAgICAgICAgfSk7XHJcbiAgICAgICAgbGluZXMuZm9yRWFjaChmdW5jdGlvbiAobCwgbGkpIHtcclxuICAgICAgICAgICAgX3RoaXMubm9kZXMuZm9yRWFjaChmdW5jdGlvbiAodiwgaSkge1xyXG4gICAgICAgICAgICAgICAgdi5yZWN0LmxpbmVJbnRlcnNlY3Rpb25zKGwueDEsIGwueTEsIGwueDIsIGwueTIpLmZvckVhY2goZnVuY3Rpb24gKGludGVyc2VjdCwgaikge1xyXG4gICAgICAgICAgICAgICAgICAgIHZhciBwID0gbmV3IFZlcnQoX3RoaXMudmVydHMubGVuZ3RoLCBpbnRlcnNlY3QueCwgaW50ZXJzZWN0LnksIHYsIGwpO1xyXG4gICAgICAgICAgICAgICAgICAgIF90aGlzLnZlcnRzLnB1c2gocCk7XHJcbiAgICAgICAgICAgICAgICAgICAgbC52ZXJ0cy5wdXNoKHApO1xyXG4gICAgICAgICAgICAgICAgICAgIHYucG9ydHMucHVzaChwKTtcclxuICAgICAgICAgICAgICAgIH0pO1xyXG4gICAgICAgICAgICB9KTtcclxuICAgICAgICAgICAgdmFyIGlzSG9yaXogPSBNYXRoLmFicyhsLnkxIC0gbC55MikgPCAwLjE7XHJcbiAgICAgICAgICAgIHZhciBkZWx0YSA9IGZ1bmN0aW9uIChhLCBiKSB7IHJldHVybiBpc0hvcml6ID8gYi54IC0gYS54IDogYi55IC0gYS55OyB9O1xyXG4gICAgICAgICAgICBsLnZlcnRzLnNvcnQoZGVsdGEpO1xyXG4gICAgICAgICAgICBmb3IgKHZhciBpID0gMTsgaSA8IGwudmVydHMubGVuZ3RoOyBpKyspIHtcclxuICAgICAgICAgICAgICAgIHZhciB1ID0gbC52ZXJ0c1tpIC0gMV0sIHYgPSBsLnZlcnRzW2ldO1xyXG4gICAgICAgICAgICAgICAgaWYgKHUubm9kZSAmJiB1Lm5vZGUgPT09IHYubm9kZSAmJiB1Lm5vZGUubGVhZilcclxuICAgICAgICAgICAgICAgICAgICBjb250aW51ZTtcclxuICAgICAgICAgICAgICAgIF90aGlzLmVkZ2VzLnB1c2goeyBzb3VyY2U6IHUuaWQsIHRhcmdldDogdi5pZCwgbGVuZ3RoOiBNYXRoLmFicyhkZWx0YSh1LCB2KSkgfSk7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICB9KTtcclxuICAgIH1cclxuICAgIEdyaWRSb3V0ZXIucHJvdG90eXBlLmF2ZyA9IGZ1bmN0aW9uIChhKSB7IHJldHVybiBhLnJlZHVjZShmdW5jdGlvbiAoeCwgeSkgeyByZXR1cm4geCArIHk7IH0pIC8gYS5sZW5ndGg7IH07XHJcbiAgICBHcmlkUm91dGVyLnByb3RvdHlwZS5nZXRHcmlkTGluZXMgPSBmdW5jdGlvbiAoYXhpcykge1xyXG4gICAgICAgIHZhciBjb2x1bW5zID0gW107XHJcbiAgICAgICAgdmFyIGxzID0gdGhpcy5sZWF2ZXMuc2xpY2UoMCwgdGhpcy5sZWF2ZXMubGVuZ3RoKTtcclxuICAgICAgICB3aGlsZSAobHMubGVuZ3RoID4gMCkge1xyXG4gICAgICAgICAgICB2YXIgb3ZlcmxhcHBpbmcgPSBscy5maWx0ZXIoZnVuY3Rpb24gKHYpIHsgcmV0dXJuIHYucmVjdFsnb3ZlcmxhcCcgKyBheGlzLnRvVXBwZXJDYXNlKCldKGxzWzBdLnJlY3QpOyB9KTtcclxuICAgICAgICAgICAgdmFyIGNvbCA9IHtcclxuICAgICAgICAgICAgICAgIG5vZGVzOiBvdmVybGFwcGluZyxcclxuICAgICAgICAgICAgICAgIHBvczogdGhpcy5hdmcob3ZlcmxhcHBpbmcubWFwKGZ1bmN0aW9uICh2KSB7IHJldHVybiB2LnJlY3RbJ2MnICsgYXhpc10oKTsgfSkpXHJcbiAgICAgICAgICAgIH07XHJcbiAgICAgICAgICAgIGNvbHVtbnMucHVzaChjb2wpO1xyXG4gICAgICAgICAgICBjb2wubm9kZXMuZm9yRWFjaChmdW5jdGlvbiAodikgeyByZXR1cm4gbHMuc3BsaWNlKGxzLmluZGV4T2YodiksIDEpOyB9KTtcclxuICAgICAgICB9XHJcbiAgICAgICAgY29sdW1ucy5zb3J0KGZ1bmN0aW9uIChhLCBiKSB7IHJldHVybiBhLnBvcyAtIGIucG9zOyB9KTtcclxuICAgICAgICByZXR1cm4gY29sdW1ucztcclxuICAgIH07XHJcbiAgICBHcmlkUm91dGVyLnByb3RvdHlwZS5nZXREZXB0aCA9IGZ1bmN0aW9uICh2KSB7XHJcbiAgICAgICAgdmFyIGRlcHRoID0gMDtcclxuICAgICAgICB3aGlsZSAodi5wYXJlbnQgIT09IHRoaXMucm9vdCkge1xyXG4gICAgICAgICAgICBkZXB0aCsrO1xyXG4gICAgICAgICAgICB2ID0gdi5wYXJlbnQ7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIHJldHVybiBkZXB0aDtcclxuICAgIH07XHJcbiAgICBHcmlkUm91dGVyLnByb3RvdHlwZS5taWRQb2ludHMgPSBmdW5jdGlvbiAoYSkge1xyXG4gICAgICAgIHZhciBnYXAgPSBhWzFdIC0gYVswXTtcclxuICAgICAgICB2YXIgbWlkcyA9IFthWzBdIC0gZ2FwIC8gMl07XHJcbiAgICAgICAgZm9yICh2YXIgaSA9IDE7IGkgPCBhLmxlbmd0aDsgaSsrKSB7XHJcbiAgICAgICAgICAgIG1pZHMucHVzaCgoYVtpXSArIGFbaSAtIDFdKSAvIDIpO1xyXG4gICAgICAgIH1cclxuICAgICAgICBtaWRzLnB1c2goYVthLmxlbmd0aCAtIDFdICsgZ2FwIC8gMik7XHJcbiAgICAgICAgcmV0dXJuIG1pZHM7XHJcbiAgICB9O1xyXG4gICAgR3JpZFJvdXRlci5wcm90b3R5cGUuZmluZExpbmVhZ2UgPSBmdW5jdGlvbiAodikge1xyXG4gICAgICAgIHZhciBsaW5lYWdlID0gW3ZdO1xyXG4gICAgICAgIGRvIHtcclxuICAgICAgICAgICAgdiA9IHYucGFyZW50O1xyXG4gICAgICAgICAgICBsaW5lYWdlLnB1c2godik7XHJcbiAgICAgICAgfSB3aGlsZSAodiAhPT0gdGhpcy5yb290KTtcclxuICAgICAgICByZXR1cm4gbGluZWFnZS5yZXZlcnNlKCk7XHJcbiAgICB9O1xyXG4gICAgR3JpZFJvdXRlci5wcm90b3R5cGUuZmluZEFuY2VzdG9yUGF0aEJldHdlZW4gPSBmdW5jdGlvbiAoYSwgYikge1xyXG4gICAgICAgIHZhciBhYSA9IHRoaXMuZmluZExpbmVhZ2UoYSksIGJhID0gdGhpcy5maW5kTGluZWFnZShiKSwgaSA9IDA7XHJcbiAgICAgICAgd2hpbGUgKGFhW2ldID09PSBiYVtpXSlcclxuICAgICAgICAgICAgaSsrO1xyXG4gICAgICAgIHJldHVybiB7IGNvbW1vbkFuY2VzdG9yOiBhYVtpIC0gMV0sIGxpbmVhZ2VzOiBhYS5zbGljZShpKS5jb25jYXQoYmEuc2xpY2UoaSkpIH07XHJcbiAgICB9O1xyXG4gICAgR3JpZFJvdXRlci5wcm90b3R5cGUuc2libGluZ09ic3RhY2xlcyA9IGZ1bmN0aW9uIChhLCBiKSB7XHJcbiAgICAgICAgdmFyIF90aGlzID0gdGhpcztcclxuICAgICAgICB2YXIgcGF0aCA9IHRoaXMuZmluZEFuY2VzdG9yUGF0aEJldHdlZW4oYSwgYik7XHJcbiAgICAgICAgdmFyIGxpbmVhZ2VMb29rdXAgPSB7fTtcclxuICAgICAgICBwYXRoLmxpbmVhZ2VzLmZvckVhY2goZnVuY3Rpb24gKHYpIHsgcmV0dXJuIGxpbmVhZ2VMb29rdXBbdi5pZF0gPSB7fTsgfSk7XHJcbiAgICAgICAgdmFyIG9ic3RhY2xlcyA9IHBhdGguY29tbW9uQW5jZXN0b3IuY2hpbGRyZW4uZmlsdGVyKGZ1bmN0aW9uICh2KSB7IHJldHVybiAhKHYgaW4gbGluZWFnZUxvb2t1cCk7IH0pO1xyXG4gICAgICAgIHBhdGgubGluZWFnZXNcclxuICAgICAgICAgICAgLmZpbHRlcihmdW5jdGlvbiAodikgeyByZXR1cm4gdi5wYXJlbnQgIT09IHBhdGguY29tbW9uQW5jZXN0b3I7IH0pXHJcbiAgICAgICAgICAgIC5mb3JFYWNoKGZ1bmN0aW9uICh2KSB7IHJldHVybiBvYnN0YWNsZXMgPSBvYnN0YWNsZXMuY29uY2F0KHYucGFyZW50LmNoaWxkcmVuLmZpbHRlcihmdW5jdGlvbiAoYykgeyByZXR1cm4gYyAhPT0gdi5pZDsgfSkpOyB9KTtcclxuICAgICAgICByZXR1cm4gb2JzdGFjbGVzLm1hcChmdW5jdGlvbiAodikgeyByZXR1cm4gX3RoaXMubm9kZXNbdl07IH0pO1xyXG4gICAgfTtcclxuICAgIEdyaWRSb3V0ZXIuZ2V0U2VnbWVudFNldHMgPSBmdW5jdGlvbiAocm91dGVzLCB4LCB5KSB7XHJcbiAgICAgICAgdmFyIHZzZWdtZW50cyA9IFtdO1xyXG4gICAgICAgIGZvciAodmFyIGVpID0gMDsgZWkgPCByb3V0ZXMubGVuZ3RoOyBlaSsrKSB7XHJcbiAgICAgICAgICAgIHZhciByb3V0ZSA9IHJvdXRlc1tlaV07XHJcbiAgICAgICAgICAgIGZvciAodmFyIHNpID0gMDsgc2kgPCByb3V0ZS5sZW5ndGg7IHNpKyspIHtcclxuICAgICAgICAgICAgICAgIHZhciBzID0gcm91dGVbc2ldO1xyXG4gICAgICAgICAgICAgICAgcy5lZGdlaWQgPSBlaTtcclxuICAgICAgICAgICAgICAgIHMuaSA9IHNpO1xyXG4gICAgICAgICAgICAgICAgdmFyIHNkeCA9IHNbMV1beF0gLSBzWzBdW3hdO1xyXG4gICAgICAgICAgICAgICAgaWYgKE1hdGguYWJzKHNkeCkgPCAwLjEpIHtcclxuICAgICAgICAgICAgICAgICAgICB2c2VnbWVudHMucHVzaChzKTtcclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgfVxyXG4gICAgICAgIH1cclxuICAgICAgICB2c2VnbWVudHMuc29ydChmdW5jdGlvbiAoYSwgYikgeyByZXR1cm4gYVswXVt4XSAtIGJbMF1beF07IH0pO1xyXG4gICAgICAgIHZhciB2c2VnbWVudHNldHMgPSBbXTtcclxuICAgICAgICB2YXIgc2VnbWVudHNldCA9IG51bGw7XHJcbiAgICAgICAgZm9yICh2YXIgaSA9IDA7IGkgPCB2c2VnbWVudHMubGVuZ3RoOyBpKyspIHtcclxuICAgICAgICAgICAgdmFyIHMgPSB2c2VnbWVudHNbaV07XHJcbiAgICAgICAgICAgIGlmICghc2VnbWVudHNldCB8fCBNYXRoLmFicyhzWzBdW3hdIC0gc2VnbWVudHNldC5wb3MpID4gMC4xKSB7XHJcbiAgICAgICAgICAgICAgICBzZWdtZW50c2V0ID0geyBwb3M6IHNbMF1beF0sIHNlZ21lbnRzOiBbXSB9O1xyXG4gICAgICAgICAgICAgICAgdnNlZ21lbnRzZXRzLnB1c2goc2VnbWVudHNldCk7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgc2VnbWVudHNldC5zZWdtZW50cy5wdXNoKHMpO1xyXG4gICAgICAgIH1cclxuICAgICAgICByZXR1cm4gdnNlZ21lbnRzZXRzO1xyXG4gICAgfTtcclxuICAgIEdyaWRSb3V0ZXIubnVkZ2VTZWdzID0gZnVuY3Rpb24gKHgsIHksIHJvdXRlcywgc2VnbWVudHMsIGxlZnRPZiwgZ2FwKSB7XHJcbiAgICAgICAgdmFyIG4gPSBzZWdtZW50cy5sZW5ndGg7XHJcbiAgICAgICAgaWYgKG4gPD0gMSlcclxuICAgICAgICAgICAgcmV0dXJuO1xyXG4gICAgICAgIHZhciB2cyA9IHNlZ21lbnRzLm1hcChmdW5jdGlvbiAocykgeyByZXR1cm4gbmV3IHZwc2NfMS5WYXJpYWJsZShzWzBdW3hdKTsgfSk7XHJcbiAgICAgICAgdmFyIGNzID0gW107XHJcbiAgICAgICAgZm9yICh2YXIgaSA9IDA7IGkgPCBuOyBpKyspIHtcclxuICAgICAgICAgICAgZm9yICh2YXIgaiA9IDA7IGogPCBuOyBqKyspIHtcclxuICAgICAgICAgICAgICAgIGlmIChpID09PSBqKVxyXG4gICAgICAgICAgICAgICAgICAgIGNvbnRpbnVlO1xyXG4gICAgICAgICAgICAgICAgdmFyIHMxID0gc2VnbWVudHNbaV0sIHMyID0gc2VnbWVudHNbal0sIGUxID0gczEuZWRnZWlkLCBlMiA9IHMyLmVkZ2VpZCwgbGluZCA9IC0xLCByaW5kID0gLTE7XHJcbiAgICAgICAgICAgICAgICBpZiAoeCA9PSAneCcpIHtcclxuICAgICAgICAgICAgICAgICAgICBpZiAobGVmdE9mKGUxLCBlMikpIHtcclxuICAgICAgICAgICAgICAgICAgICAgICAgaWYgKHMxWzBdW3ldIDwgczFbMV1beV0pIHtcclxuICAgICAgICAgICAgICAgICAgICAgICAgICAgIGxpbmQgPSBqLCByaW5kID0gaTtcclxuICAgICAgICAgICAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICAgICAgICAgICAgICBlbHNlIHtcclxuICAgICAgICAgICAgICAgICAgICAgICAgICAgIGxpbmQgPSBpLCByaW5kID0gajtcclxuICAgICAgICAgICAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgIGVsc2Uge1xyXG4gICAgICAgICAgICAgICAgICAgIGlmIChsZWZ0T2YoZTEsIGUyKSkge1xyXG4gICAgICAgICAgICAgICAgICAgICAgICBpZiAoczFbMF1beV0gPCBzMVsxXVt5XSkge1xyXG4gICAgICAgICAgICAgICAgICAgICAgICAgICAgbGluZCA9IGksIHJpbmQgPSBqO1xyXG4gICAgICAgICAgICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgICAgICAgICAgICAgIGVsc2Uge1xyXG4gICAgICAgICAgICAgICAgICAgICAgICAgICAgbGluZCA9IGosIHJpbmQgPSBpO1xyXG4gICAgICAgICAgICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICAgICAgaWYgKGxpbmQgPj0gMCkge1xyXG4gICAgICAgICAgICAgICAgICAgIGNzLnB1c2gobmV3IHZwc2NfMS5Db25zdHJhaW50KHZzW2xpbmRdLCB2c1tyaW5kXSwgZ2FwKSk7XHJcbiAgICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICB9XHJcbiAgICAgICAgdmFyIHNvbHZlciA9IG5ldyB2cHNjXzEuU29sdmVyKHZzLCBjcyk7XHJcbiAgICAgICAgc29sdmVyLnNvbHZlKCk7XHJcbiAgICAgICAgdnMuZm9yRWFjaChmdW5jdGlvbiAodiwgaSkge1xyXG4gICAgICAgICAgICB2YXIgcyA9IHNlZ21lbnRzW2ldO1xyXG4gICAgICAgICAgICB2YXIgcG9zID0gdi5wb3NpdGlvbigpO1xyXG4gICAgICAgICAgICBzWzBdW3hdID0gc1sxXVt4XSA9IHBvcztcclxuICAgICAgICAgICAgdmFyIHJvdXRlID0gcm91dGVzW3MuZWRnZWlkXTtcclxuICAgICAgICAgICAgaWYgKHMuaSA+IDApXHJcbiAgICAgICAgICAgICAgICByb3V0ZVtzLmkgLSAxXVsxXVt4XSA9IHBvcztcclxuICAgICAgICAgICAgaWYgKHMuaSA8IHJvdXRlLmxlbmd0aCAtIDEpXHJcbiAgICAgICAgICAgICAgICByb3V0ZVtzLmkgKyAxXVswXVt4XSA9IHBvcztcclxuICAgICAgICB9KTtcclxuICAgIH07XHJcbiAgICBHcmlkUm91dGVyLm51ZGdlU2VnbWVudHMgPSBmdW5jdGlvbiAocm91dGVzLCB4LCB5LCBsZWZ0T2YsIGdhcCkge1xyXG4gICAgICAgIHZhciB2c2VnbWVudHNldHMgPSBHcmlkUm91dGVyLmdldFNlZ21lbnRTZXRzKHJvdXRlcywgeCwgeSk7XHJcbiAgICAgICAgZm9yICh2YXIgaSA9IDA7IGkgPCB2c2VnbWVudHNldHMubGVuZ3RoOyBpKyspIHtcclxuICAgICAgICAgICAgdmFyIHNzID0gdnNlZ21lbnRzZXRzW2ldO1xyXG4gICAgICAgICAgICB2YXIgZXZlbnRzID0gW107XHJcbiAgICAgICAgICAgIGZvciAodmFyIGogPSAwOyBqIDwgc3Muc2VnbWVudHMubGVuZ3RoOyBqKyspIHtcclxuICAgICAgICAgICAgICAgIHZhciBzID0gc3Muc2VnbWVudHNbal07XHJcbiAgICAgICAgICAgICAgICBldmVudHMucHVzaCh7IHR5cGU6IDAsIHM6IHMsIHBvczogTWF0aC5taW4oc1swXVt5XSwgc1sxXVt5XSkgfSk7XHJcbiAgICAgICAgICAgICAgICBldmVudHMucHVzaCh7IHR5cGU6IDEsIHM6IHMsIHBvczogTWF0aC5tYXgoc1swXVt5XSwgc1sxXVt5XSkgfSk7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgZXZlbnRzLnNvcnQoZnVuY3Rpb24gKGEsIGIpIHsgcmV0dXJuIGEucG9zIC0gYi5wb3MgKyBhLnR5cGUgLSBiLnR5cGU7IH0pO1xyXG4gICAgICAgICAgICB2YXIgb3BlbiA9IFtdO1xyXG4gICAgICAgICAgICB2YXIgb3BlbkNvdW50ID0gMDtcclxuICAgICAgICAgICAgZXZlbnRzLmZvckVhY2goZnVuY3Rpb24gKGUpIHtcclxuICAgICAgICAgICAgICAgIGlmIChlLnR5cGUgPT09IDApIHtcclxuICAgICAgICAgICAgICAgICAgICBvcGVuLnB1c2goZS5zKTtcclxuICAgICAgICAgICAgICAgICAgICBvcGVuQ291bnQrKztcclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgIGVsc2Uge1xyXG4gICAgICAgICAgICAgICAgICAgIG9wZW5Db3VudC0tO1xyXG4gICAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICAgICAgaWYgKG9wZW5Db3VudCA9PSAwKSB7XHJcbiAgICAgICAgICAgICAgICAgICAgR3JpZFJvdXRlci5udWRnZVNlZ3MoeCwgeSwgcm91dGVzLCBvcGVuLCBsZWZ0T2YsIGdhcCk7XHJcbiAgICAgICAgICAgICAgICAgICAgb3BlbiA9IFtdO1xyXG4gICAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICB9KTtcclxuICAgICAgICB9XHJcbiAgICB9O1xyXG4gICAgR3JpZFJvdXRlci5wcm90b3R5cGUucm91dGVFZGdlcyA9IGZ1bmN0aW9uIChlZGdlcywgbnVkZ2VHYXAsIHNvdXJjZSwgdGFyZ2V0KSB7XHJcbiAgICAgICAgdmFyIF90aGlzID0gdGhpcztcclxuICAgICAgICB2YXIgcm91dGVQYXRocyA9IGVkZ2VzLm1hcChmdW5jdGlvbiAoZSkgeyByZXR1cm4gX3RoaXMucm91dGUoc291cmNlKGUpLCB0YXJnZXQoZSkpOyB9KTtcclxuICAgICAgICB2YXIgb3JkZXIgPSBHcmlkUm91dGVyLm9yZGVyRWRnZXMocm91dGVQYXRocyk7XHJcbiAgICAgICAgdmFyIHJvdXRlcyA9IHJvdXRlUGF0aHMubWFwKGZ1bmN0aW9uIChlKSB7IHJldHVybiBHcmlkUm91dGVyLm1ha2VTZWdtZW50cyhlKTsgfSk7XHJcbiAgICAgICAgR3JpZFJvdXRlci5udWRnZVNlZ21lbnRzKHJvdXRlcywgJ3gnLCAneScsIG9yZGVyLCBudWRnZUdhcCk7XHJcbiAgICAgICAgR3JpZFJvdXRlci5udWRnZVNlZ21lbnRzKHJvdXRlcywgJ3knLCAneCcsIG9yZGVyLCBudWRnZUdhcCk7XHJcbiAgICAgICAgR3JpZFJvdXRlci51bnJldmVyc2VFZGdlcyhyb3V0ZXMsIHJvdXRlUGF0aHMpO1xyXG4gICAgICAgIHJldHVybiByb3V0ZXM7XHJcbiAgICB9O1xyXG4gICAgR3JpZFJvdXRlci51bnJldmVyc2VFZGdlcyA9IGZ1bmN0aW9uIChyb3V0ZXMsIHJvdXRlUGF0aHMpIHtcclxuICAgICAgICByb3V0ZXMuZm9yRWFjaChmdW5jdGlvbiAoc2VnbWVudHMsIGkpIHtcclxuICAgICAgICAgICAgdmFyIHBhdGggPSByb3V0ZVBhdGhzW2ldO1xyXG4gICAgICAgICAgICBpZiAocGF0aC5yZXZlcnNlZCkge1xyXG4gICAgICAgICAgICAgICAgc2VnbWVudHMucmV2ZXJzZSgpO1xyXG4gICAgICAgICAgICAgICAgc2VnbWVudHMuZm9yRWFjaChmdW5jdGlvbiAoc2VnbWVudCkge1xyXG4gICAgICAgICAgICAgICAgICAgIHNlZ21lbnQucmV2ZXJzZSgpO1xyXG4gICAgICAgICAgICAgICAgfSk7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICB9KTtcclxuICAgIH07XHJcbiAgICBHcmlkUm91dGVyLmFuZ2xlQmV0d2VlbjJMaW5lcyA9IGZ1bmN0aW9uIChsaW5lMSwgbGluZTIpIHtcclxuICAgICAgICB2YXIgYW5nbGUxID0gTWF0aC5hdGFuMihsaW5lMVswXS55IC0gbGluZTFbMV0ueSwgbGluZTFbMF0ueCAtIGxpbmUxWzFdLngpO1xyXG4gICAgICAgIHZhciBhbmdsZTIgPSBNYXRoLmF0YW4yKGxpbmUyWzBdLnkgLSBsaW5lMlsxXS55LCBsaW5lMlswXS54IC0gbGluZTJbMV0ueCk7XHJcbiAgICAgICAgdmFyIGRpZmYgPSBhbmdsZTEgLSBhbmdsZTI7XHJcbiAgICAgICAgaWYgKGRpZmYgPiBNYXRoLlBJIHx8IGRpZmYgPCAtTWF0aC5QSSkge1xyXG4gICAgICAgICAgICBkaWZmID0gYW5nbGUyIC0gYW5nbGUxO1xyXG4gICAgICAgIH1cclxuICAgICAgICByZXR1cm4gZGlmZjtcclxuICAgIH07XHJcbiAgICBHcmlkUm91dGVyLmlzTGVmdCA9IGZ1bmN0aW9uIChhLCBiLCBjKSB7XHJcbiAgICAgICAgcmV0dXJuICgoYi54IC0gYS54KSAqIChjLnkgLSBhLnkpIC0gKGIueSAtIGEueSkgKiAoYy54IC0gYS54KSkgPD0gMDtcclxuICAgIH07XHJcbiAgICBHcmlkUm91dGVyLmdldE9yZGVyID0gZnVuY3Rpb24gKHBhaXJzKSB7XHJcbiAgICAgICAgdmFyIG91dGdvaW5nID0ge307XHJcbiAgICAgICAgZm9yICh2YXIgaSA9IDA7IGkgPCBwYWlycy5sZW5ndGg7IGkrKykge1xyXG4gICAgICAgICAgICB2YXIgcCA9IHBhaXJzW2ldO1xyXG4gICAgICAgICAgICBpZiAodHlwZW9mIG91dGdvaW5nW3AubF0gPT09ICd1bmRlZmluZWQnKVxyXG4gICAgICAgICAgICAgICAgb3V0Z29pbmdbcC5sXSA9IHt9O1xyXG4gICAgICAgICAgICBvdXRnb2luZ1twLmxdW3Aucl0gPSB0cnVlO1xyXG4gICAgICAgIH1cclxuICAgICAgICByZXR1cm4gZnVuY3Rpb24gKGwsIHIpIHsgcmV0dXJuIHR5cGVvZiBvdXRnb2luZ1tsXSAhPT0gJ3VuZGVmaW5lZCcgJiYgb3V0Z29pbmdbbF1bcl07IH07XHJcbiAgICB9O1xyXG4gICAgR3JpZFJvdXRlci5vcmRlckVkZ2VzID0gZnVuY3Rpb24gKGVkZ2VzKSB7XHJcbiAgICAgICAgdmFyIGVkZ2VPcmRlciA9IFtdO1xyXG4gICAgICAgIGZvciAodmFyIGkgPSAwOyBpIDwgZWRnZXMubGVuZ3RoIC0gMTsgaSsrKSB7XHJcbiAgICAgICAgICAgIGZvciAodmFyIGogPSBpICsgMTsgaiA8IGVkZ2VzLmxlbmd0aDsgaisrKSB7XHJcbiAgICAgICAgICAgICAgICB2YXIgZSA9IGVkZ2VzW2ldLCBmID0gZWRnZXNbal0sIGxjcyA9IG5ldyBMb25nZXN0Q29tbW9uU3Vic2VxdWVuY2UoZSwgZik7XHJcbiAgICAgICAgICAgICAgICB2YXIgdSwgdmksIHZqO1xyXG4gICAgICAgICAgICAgICAgaWYgKGxjcy5sZW5ndGggPT09IDApXHJcbiAgICAgICAgICAgICAgICAgICAgY29udGludWU7XHJcbiAgICAgICAgICAgICAgICBpZiAobGNzLnJldmVyc2VkKSB7XHJcbiAgICAgICAgICAgICAgICAgICAgZi5yZXZlcnNlKCk7XHJcbiAgICAgICAgICAgICAgICAgICAgZi5yZXZlcnNlZCA9IHRydWU7XHJcbiAgICAgICAgICAgICAgICAgICAgbGNzID0gbmV3IExvbmdlc3RDb21tb25TdWJzZXF1ZW5jZShlLCBmKTtcclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgIGlmICgobGNzLnNpIDw9IDAgfHwgbGNzLnRpIDw9IDApICYmXHJcbiAgICAgICAgICAgICAgICAgICAgKGxjcy5zaSArIGxjcy5sZW5ndGggPj0gZS5sZW5ndGggfHwgbGNzLnRpICsgbGNzLmxlbmd0aCA+PSBmLmxlbmd0aCkpIHtcclxuICAgICAgICAgICAgICAgICAgICBlZGdlT3JkZXIucHVzaCh7IGw6IGksIHI6IGogfSk7XHJcbiAgICAgICAgICAgICAgICAgICAgY29udGludWU7XHJcbiAgICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgICAgICBpZiAobGNzLnNpICsgbGNzLmxlbmd0aCA+PSBlLmxlbmd0aCB8fCBsY3MudGkgKyBsY3MubGVuZ3RoID49IGYubGVuZ3RoKSB7XHJcbiAgICAgICAgICAgICAgICAgICAgdSA9IGVbbGNzLnNpICsgMV07XHJcbiAgICAgICAgICAgICAgICAgICAgdmogPSBlW2xjcy5zaSAtIDFdO1xyXG4gICAgICAgICAgICAgICAgICAgIHZpID0gZltsY3MudGkgLSAxXTtcclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgIGVsc2Uge1xyXG4gICAgICAgICAgICAgICAgICAgIHUgPSBlW2xjcy5zaSArIGxjcy5sZW5ndGggLSAyXTtcclxuICAgICAgICAgICAgICAgICAgICB2aSA9IGVbbGNzLnNpICsgbGNzLmxlbmd0aF07XHJcbiAgICAgICAgICAgICAgICAgICAgdmogPSBmW2xjcy50aSArIGxjcy5sZW5ndGhdO1xyXG4gICAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICAgICAgaWYgKEdyaWRSb3V0ZXIuaXNMZWZ0KHUsIHZpLCB2aikpIHtcclxuICAgICAgICAgICAgICAgICAgICBlZGdlT3JkZXIucHVzaCh7IGw6IGosIHI6IGkgfSk7XHJcbiAgICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgICAgICBlbHNlIHtcclxuICAgICAgICAgICAgICAgICAgICBlZGdlT3JkZXIucHVzaCh7IGw6IGksIHI6IGogfSk7XHJcbiAgICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICB9XHJcbiAgICAgICAgcmV0dXJuIEdyaWRSb3V0ZXIuZ2V0T3JkZXIoZWRnZU9yZGVyKTtcclxuICAgIH07XHJcbiAgICBHcmlkUm91dGVyLm1ha2VTZWdtZW50cyA9IGZ1bmN0aW9uIChwYXRoKSB7XHJcbiAgICAgICAgZnVuY3Rpb24gY29weVBvaW50KHApIHtcclxuICAgICAgICAgICAgcmV0dXJuIHsgeDogcC54LCB5OiBwLnkgfTtcclxuICAgICAgICB9XHJcbiAgICAgICAgdmFyIGlzU3RyYWlnaHQgPSBmdW5jdGlvbiAoYSwgYiwgYykgeyByZXR1cm4gTWF0aC5hYnMoKGIueCAtIGEueCkgKiAoYy55IC0gYS55KSAtIChiLnkgLSBhLnkpICogKGMueCAtIGEueCkpIDwgMC4wMDE7IH07XHJcbiAgICAgICAgdmFyIHNlZ21lbnRzID0gW107XHJcbiAgICAgICAgdmFyIGEgPSBjb3B5UG9pbnQocGF0aFswXSk7XHJcbiAgICAgICAgZm9yICh2YXIgaSA9IDE7IGkgPCBwYXRoLmxlbmd0aDsgaSsrKSB7XHJcbiAgICAgICAgICAgIHZhciBiID0gY29weVBvaW50KHBhdGhbaV0pLCBjID0gaSA8IHBhdGgubGVuZ3RoIC0gMSA/IHBhdGhbaSArIDFdIDogbnVsbDtcclxuICAgICAgICAgICAgaWYgKCFjIHx8ICFpc1N0cmFpZ2h0KGEsIGIsIGMpKSB7XHJcbiAgICAgICAgICAgICAgICBzZWdtZW50cy5wdXNoKFthLCBiXSk7XHJcbiAgICAgICAgICAgICAgICBhID0gYjtcclxuICAgICAgICAgICAgfVxyXG4gICAgICAgIH1cclxuICAgICAgICByZXR1cm4gc2VnbWVudHM7XHJcbiAgICB9O1xyXG4gICAgR3JpZFJvdXRlci5wcm90b3R5cGUucm91dGUgPSBmdW5jdGlvbiAocywgdCkge1xyXG4gICAgICAgIHZhciBfdGhpcyA9IHRoaXM7XHJcbiAgICAgICAgdmFyIHNvdXJjZSA9IHRoaXMubm9kZXNbc10sIHRhcmdldCA9IHRoaXMubm9kZXNbdF07XHJcbiAgICAgICAgdGhpcy5vYnN0YWNsZXMgPSB0aGlzLnNpYmxpbmdPYnN0YWNsZXMoc291cmNlLCB0YXJnZXQpO1xyXG4gICAgICAgIHZhciBvYnN0YWNsZUxvb2t1cCA9IHt9O1xyXG4gICAgICAgIHRoaXMub2JzdGFjbGVzLmZvckVhY2goZnVuY3Rpb24gKG8pIHsgcmV0dXJuIG9ic3RhY2xlTG9va3VwW28uaWRdID0gbzsgfSk7XHJcbiAgICAgICAgdGhpcy5wYXNzYWJsZUVkZ2VzID0gdGhpcy5lZGdlcy5maWx0ZXIoZnVuY3Rpb24gKGUpIHtcclxuICAgICAgICAgICAgdmFyIHUgPSBfdGhpcy52ZXJ0c1tlLnNvdXJjZV0sIHYgPSBfdGhpcy52ZXJ0c1tlLnRhcmdldF07XHJcbiAgICAgICAgICAgIHJldHVybiAhKHUubm9kZSAmJiB1Lm5vZGUuaWQgaW4gb2JzdGFjbGVMb29rdXBcclxuICAgICAgICAgICAgICAgIHx8IHYubm9kZSAmJiB2Lm5vZGUuaWQgaW4gb2JzdGFjbGVMb29rdXApO1xyXG4gICAgICAgIH0pO1xyXG4gICAgICAgIGZvciAodmFyIGkgPSAxOyBpIDwgc291cmNlLnBvcnRzLmxlbmd0aDsgaSsrKSB7XHJcbiAgICAgICAgICAgIHZhciB1ID0gc291cmNlLnBvcnRzWzBdLmlkO1xyXG4gICAgICAgICAgICB2YXIgdiA9IHNvdXJjZS5wb3J0c1tpXS5pZDtcclxuICAgICAgICAgICAgdGhpcy5wYXNzYWJsZUVkZ2VzLnB1c2goe1xyXG4gICAgICAgICAgICAgICAgc291cmNlOiB1LFxyXG4gICAgICAgICAgICAgICAgdGFyZ2V0OiB2LFxyXG4gICAgICAgICAgICAgICAgbGVuZ3RoOiAwXHJcbiAgICAgICAgICAgIH0pO1xyXG4gICAgICAgIH1cclxuICAgICAgICBmb3IgKHZhciBpID0gMTsgaSA8IHRhcmdldC5wb3J0cy5sZW5ndGg7IGkrKykge1xyXG4gICAgICAgICAgICB2YXIgdSA9IHRhcmdldC5wb3J0c1swXS5pZDtcclxuICAgICAgICAgICAgdmFyIHYgPSB0YXJnZXQucG9ydHNbaV0uaWQ7XHJcbiAgICAgICAgICAgIHRoaXMucGFzc2FibGVFZGdlcy5wdXNoKHtcclxuICAgICAgICAgICAgICAgIHNvdXJjZTogdSxcclxuICAgICAgICAgICAgICAgIHRhcmdldDogdixcclxuICAgICAgICAgICAgICAgIGxlbmd0aDogMFxyXG4gICAgICAgICAgICB9KTtcclxuICAgICAgICB9XHJcbiAgICAgICAgdmFyIGdldFNvdXJjZSA9IGZ1bmN0aW9uIChlKSB7IHJldHVybiBlLnNvdXJjZTsgfSwgZ2V0VGFyZ2V0ID0gZnVuY3Rpb24gKGUpIHsgcmV0dXJuIGUudGFyZ2V0OyB9LCBnZXRMZW5ndGggPSBmdW5jdGlvbiAoZSkgeyByZXR1cm4gZS5sZW5ndGg7IH07XHJcbiAgICAgICAgdmFyIHNob3J0ZXN0UGF0aENhbGN1bGF0b3IgPSBuZXcgc2hvcnRlc3RwYXRoc18xLkNhbGN1bGF0b3IodGhpcy52ZXJ0cy5sZW5ndGgsIHRoaXMucGFzc2FibGVFZGdlcywgZ2V0U291cmNlLCBnZXRUYXJnZXQsIGdldExlbmd0aCk7XHJcbiAgICAgICAgdmFyIGJlbmRQZW5hbHR5ID0gZnVuY3Rpb24gKHUsIHYsIHcpIHtcclxuICAgICAgICAgICAgdmFyIGEgPSBfdGhpcy52ZXJ0c1t1XSwgYiA9IF90aGlzLnZlcnRzW3ZdLCBjID0gX3RoaXMudmVydHNbd107XHJcbiAgICAgICAgICAgIHZhciBkeCA9IE1hdGguYWJzKGMueCAtIGEueCksIGR5ID0gTWF0aC5hYnMoYy55IC0gYS55KTtcclxuICAgICAgICAgICAgaWYgKGEubm9kZSA9PT0gc291cmNlICYmIGEubm9kZSA9PT0gYi5ub2RlIHx8IGIubm9kZSA9PT0gdGFyZ2V0ICYmIGIubm9kZSA9PT0gYy5ub2RlKVxyXG4gICAgICAgICAgICAgICAgcmV0dXJuIDA7XHJcbiAgICAgICAgICAgIHJldHVybiBkeCA+IDEgJiYgZHkgPiAxID8gMTAwMCA6IDA7XHJcbiAgICAgICAgfTtcclxuICAgICAgICB2YXIgc2hvcnRlc3RQYXRoID0gc2hvcnRlc3RQYXRoQ2FsY3VsYXRvci5QYXRoRnJvbU5vZGVUb05vZGVXaXRoUHJldkNvc3Qoc291cmNlLnBvcnRzWzBdLmlkLCB0YXJnZXQucG9ydHNbMF0uaWQsIGJlbmRQZW5hbHR5KTtcclxuICAgICAgICB2YXIgcGF0aFBvaW50cyA9IHNob3J0ZXN0UGF0aC5yZXZlcnNlKCkubWFwKGZ1bmN0aW9uICh2aSkgeyByZXR1cm4gX3RoaXMudmVydHNbdmldOyB9KTtcclxuICAgICAgICBwYXRoUG9pbnRzLnB1c2godGhpcy5ub2Rlc1t0YXJnZXQuaWRdLnBvcnRzWzBdKTtcclxuICAgICAgICByZXR1cm4gcGF0aFBvaW50cy5maWx0ZXIoZnVuY3Rpb24gKHYsIGkpIHtcclxuICAgICAgICAgICAgcmV0dXJuICEoaSA8IHBhdGhQb2ludHMubGVuZ3RoIC0gMSAmJiBwYXRoUG9pbnRzW2kgKyAxXS5ub2RlID09PSBzb3VyY2UgJiYgdi5ub2RlID09PSBzb3VyY2VcclxuICAgICAgICAgICAgICAgIHx8IGkgPiAwICYmIHYubm9kZSA9PT0gdGFyZ2V0ICYmIHBhdGhQb2ludHNbaSAtIDFdLm5vZGUgPT09IHRhcmdldCk7XHJcbiAgICAgICAgfSk7XHJcbiAgICB9O1xyXG4gICAgR3JpZFJvdXRlci5nZXRSb3V0ZVBhdGggPSBmdW5jdGlvbiAocm91dGUsIGNvcm5lcnJhZGl1cywgYXJyb3d3aWR0aCwgYXJyb3doZWlnaHQpIHtcclxuICAgICAgICB2YXIgcmVzdWx0ID0ge1xyXG4gICAgICAgICAgICByb3V0ZXBhdGg6ICdNICcgKyByb3V0ZVswXVswXS54ICsgJyAnICsgcm91dGVbMF1bMF0ueSArICcgJyxcclxuICAgICAgICAgICAgYXJyb3dwYXRoOiAnJ1xyXG4gICAgICAgIH07XHJcbiAgICAgICAgaWYgKHJvdXRlLmxlbmd0aCA+IDEpIHtcclxuICAgICAgICAgICAgZm9yICh2YXIgaSA9IDA7IGkgPCByb3V0ZS5sZW5ndGg7IGkrKykge1xyXG4gICAgICAgICAgICAgICAgdmFyIGxpID0gcm91dGVbaV07XHJcbiAgICAgICAgICAgICAgICB2YXIgeCA9IGxpWzFdLngsIHkgPSBsaVsxXS55O1xyXG4gICAgICAgICAgICAgICAgdmFyIGR4ID0geCAtIGxpWzBdLng7XHJcbiAgICAgICAgICAgICAgICB2YXIgZHkgPSB5IC0gbGlbMF0ueTtcclxuICAgICAgICAgICAgICAgIGlmIChpIDwgcm91dGUubGVuZ3RoIC0gMSkge1xyXG4gICAgICAgICAgICAgICAgICAgIGlmIChNYXRoLmFicyhkeCkgPiAwKSB7XHJcbiAgICAgICAgICAgICAgICAgICAgICAgIHggLT0gZHggLyBNYXRoLmFicyhkeCkgKiBjb3JuZXJyYWRpdXM7XHJcbiAgICAgICAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICAgICAgICAgIGVsc2Uge1xyXG4gICAgICAgICAgICAgICAgICAgICAgICB5IC09IGR5IC8gTWF0aC5hYnMoZHkpICogY29ybmVycmFkaXVzO1xyXG4gICAgICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgICAgICByZXN1bHQucm91dGVwYXRoICs9ICdMICcgKyB4ICsgJyAnICsgeSArICcgJztcclxuICAgICAgICAgICAgICAgICAgICB2YXIgbCA9IHJvdXRlW2kgKyAxXTtcclxuICAgICAgICAgICAgICAgICAgICB2YXIgeDAgPSBsWzBdLngsIHkwID0gbFswXS55O1xyXG4gICAgICAgICAgICAgICAgICAgIHZhciB4MSA9IGxbMV0ueDtcclxuICAgICAgICAgICAgICAgICAgICB2YXIgeTEgPSBsWzFdLnk7XHJcbiAgICAgICAgICAgICAgICAgICAgZHggPSB4MSAtIHgwO1xyXG4gICAgICAgICAgICAgICAgICAgIGR5ID0geTEgLSB5MDtcclxuICAgICAgICAgICAgICAgICAgICB2YXIgYW5nbGUgPSBHcmlkUm91dGVyLmFuZ2xlQmV0d2VlbjJMaW5lcyhsaSwgbCkgPCAwID8gMSA6IDA7XHJcbiAgICAgICAgICAgICAgICAgICAgdmFyIHgyLCB5MjtcclxuICAgICAgICAgICAgICAgICAgICBpZiAoTWF0aC5hYnMoZHgpID4gMCkge1xyXG4gICAgICAgICAgICAgICAgICAgICAgICB4MiA9IHgwICsgZHggLyBNYXRoLmFicyhkeCkgKiBjb3JuZXJyYWRpdXM7XHJcbiAgICAgICAgICAgICAgICAgICAgICAgIHkyID0geTA7XHJcbiAgICAgICAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICAgICAgICAgIGVsc2Uge1xyXG4gICAgICAgICAgICAgICAgICAgICAgICB4MiA9IHgwO1xyXG4gICAgICAgICAgICAgICAgICAgICAgICB5MiA9IHkwICsgZHkgLyBNYXRoLmFicyhkeSkgKiBjb3JuZXJyYWRpdXM7XHJcbiAgICAgICAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICAgICAgICAgIHZhciBjeCA9IE1hdGguYWJzKHgyIC0geCk7XHJcbiAgICAgICAgICAgICAgICAgICAgdmFyIGN5ID0gTWF0aC5hYnMoeTIgLSB5KTtcclxuICAgICAgICAgICAgICAgICAgICByZXN1bHQucm91dGVwYXRoICs9ICdBICcgKyBjeCArICcgJyArIGN5ICsgJyAwIDAgJyArIGFuZ2xlICsgJyAnICsgeDIgKyAnICcgKyB5MiArICcgJztcclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgIGVsc2Uge1xyXG4gICAgICAgICAgICAgICAgICAgIHZhciBhcnJvd3RpcCA9IFt4LCB5XTtcclxuICAgICAgICAgICAgICAgICAgICB2YXIgYXJyb3djb3JuZXIxLCBhcnJvd2Nvcm5lcjI7XHJcbiAgICAgICAgICAgICAgICAgICAgaWYgKE1hdGguYWJzKGR4KSA+IDApIHtcclxuICAgICAgICAgICAgICAgICAgICAgICAgeCAtPSBkeCAvIE1hdGguYWJzKGR4KSAqIGFycm93aGVpZ2h0O1xyXG4gICAgICAgICAgICAgICAgICAgICAgICBhcnJvd2Nvcm5lcjEgPSBbeCwgeSArIGFycm93d2lkdGhdO1xyXG4gICAgICAgICAgICAgICAgICAgICAgICBhcnJvd2Nvcm5lcjIgPSBbeCwgeSAtIGFycm93d2lkdGhdO1xyXG4gICAgICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgICAgICBlbHNlIHtcclxuICAgICAgICAgICAgICAgICAgICAgICAgeSAtPSBkeSAvIE1hdGguYWJzKGR5KSAqIGFycm93aGVpZ2h0O1xyXG4gICAgICAgICAgICAgICAgICAgICAgICBhcnJvd2Nvcm5lcjEgPSBbeCArIGFycm93d2lkdGgsIHldO1xyXG4gICAgICAgICAgICAgICAgICAgICAgICBhcnJvd2Nvcm5lcjIgPSBbeCAtIGFycm93d2lkdGgsIHldO1xyXG4gICAgICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgICAgICByZXN1bHQucm91dGVwYXRoICs9ICdMICcgKyB4ICsgJyAnICsgeSArICcgJztcclxuICAgICAgICAgICAgICAgICAgICBpZiAoYXJyb3doZWlnaHQgPiAwKSB7XHJcbiAgICAgICAgICAgICAgICAgICAgICAgIHJlc3VsdC5hcnJvd3BhdGggPSAnTSAnICsgYXJyb3d0aXBbMF0gKyAnICcgKyBhcnJvd3RpcFsxXSArICcgTCAnICsgYXJyb3djb3JuZXIxWzBdICsgJyAnICsgYXJyb3djb3JuZXIxWzFdXHJcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICArICcgTCAnICsgYXJyb3djb3JuZXIyWzBdICsgJyAnICsgYXJyb3djb3JuZXIyWzFdO1xyXG4gICAgICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgfVxyXG4gICAgICAgIH1cclxuICAgICAgICBlbHNlIHtcclxuICAgICAgICAgICAgdmFyIGxpID0gcm91dGVbMF07XHJcbiAgICAgICAgICAgIHZhciB4ID0gbGlbMV0ueCwgeSA9IGxpWzFdLnk7XHJcbiAgICAgICAgICAgIHZhciBkeCA9IHggLSBsaVswXS54O1xyXG4gICAgICAgICAgICB2YXIgZHkgPSB5IC0gbGlbMF0ueTtcclxuICAgICAgICAgICAgdmFyIGFycm93dGlwID0gW3gsIHldO1xyXG4gICAgICAgICAgICB2YXIgYXJyb3djb3JuZXIxLCBhcnJvd2Nvcm5lcjI7XHJcbiAgICAgICAgICAgIGlmIChNYXRoLmFicyhkeCkgPiAwKSB7XHJcbiAgICAgICAgICAgICAgICB4IC09IGR4IC8gTWF0aC5hYnMoZHgpICogYXJyb3doZWlnaHQ7XHJcbiAgICAgICAgICAgICAgICBhcnJvd2Nvcm5lcjEgPSBbeCwgeSArIGFycm93d2lkdGhdO1xyXG4gICAgICAgICAgICAgICAgYXJyb3djb3JuZXIyID0gW3gsIHkgLSBhcnJvd3dpZHRoXTtcclxuICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICBlbHNlIHtcclxuICAgICAgICAgICAgICAgIHkgLT0gZHkgLyBNYXRoLmFicyhkeSkgKiBhcnJvd2hlaWdodDtcclxuICAgICAgICAgICAgICAgIGFycm93Y29ybmVyMSA9IFt4ICsgYXJyb3d3aWR0aCwgeV07XHJcbiAgICAgICAgICAgICAgICBhcnJvd2Nvcm5lcjIgPSBbeCAtIGFycm93d2lkdGgsIHldO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgICAgIHJlc3VsdC5yb3V0ZXBhdGggKz0gJ0wgJyArIHggKyAnICcgKyB5ICsgJyAnO1xyXG4gICAgICAgICAgICBpZiAoYXJyb3doZWlnaHQgPiAwKSB7XHJcbiAgICAgICAgICAgICAgICByZXN1bHQuYXJyb3dwYXRoID0gJ00gJyArIGFycm93dGlwWzBdICsgJyAnICsgYXJyb3d0aXBbMV0gKyAnIEwgJyArIGFycm93Y29ybmVyMVswXSArICcgJyArIGFycm93Y29ybmVyMVsxXVxyXG4gICAgICAgICAgICAgICAgICAgICsgJyBMICcgKyBhcnJvd2Nvcm5lcjJbMF0gKyAnICcgKyBhcnJvd2Nvcm5lcjJbMV07XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICB9XHJcbiAgICAgICAgcmV0dXJuIHJlc3VsdDtcclxuICAgIH07XHJcbiAgICByZXR1cm4gR3JpZFJvdXRlcjtcclxufSgpKTtcclxuZXhwb3J0cy5HcmlkUm91dGVyID0gR3JpZFJvdXRlcjtcclxuLy8jIHNvdXJjZU1hcHBpbmdVUkw9ZGF0YTphcHBsaWNhdGlvbi9qc29uO2Jhc2U2NCxleUoyWlhKemFXOXVJam96TENKbWFXeGxJam9pWjNKcFpISnZkWFJsY2k1cWN5SXNJbk52ZFhKalpWSnZiM1FpT2lJaUxDSnpiM1Z5WTJWeklqcGJJaTR1THk0dUwxZGxZa052YkdFdmMzSmpMMmR5YVdSeWIzVjBaWEl1ZEhNaVhTd2libUZ0WlhNaU9sdGRMQ0p0WVhCd2FXNW5jeUk2SWpzN1FVRkRRU3g1UTBGQmNVTTdRVUZEY2tNc0swSkJRVzFFTzBGQlEyNUVMR2xFUVVFd1F6dEJRVXQwUXp0SlFVbEpMSEZDUVVGdFFpeEZRVUZWTEVWQlFWTXNTVUZCWlN4RlFVRlRMRkZCUVd0Q08xRkJRVGRFTEU5QlFVVXNSMEZCUml4RlFVRkZMRU5CUVZFN1VVRkJVeXhUUVVGSkxFZEJRVW9zU1VGQlNTeERRVUZYTzFGQlFWTXNZVUZCVVN4SFFVRlNMRkZCUVZFc1EwRkJWVHRSUVVNMVJTeEpRVUZKTEVOQlFVTXNTVUZCU1N4SFFVRkhMRTlCUVU4c1VVRkJVU3hMUVVGTExGZEJRVmNzU1VGQlNTeFJRVUZSTEVOQlFVTXNUVUZCVFN4TFFVRkxMRU5CUVVNc1EwRkJRenRKUVVONlJTeERRVUZETzBsQlEwd3NhMEpCUVVNN1FVRkJSQ3hEUVVGRExFRkJVRVFzU1VGUFF6dEJRVkJaTEd0RFFVRlhPMEZCVVhoQ08wbEJRMGtzWTBGQmJVSXNSVUZCVlN4RlFVRlRMRU5CUVZFc1JVRkJVeXhEUVVGVExFVkJRVk1zU1VGQmQwSXNSVUZCVXl4SlFVRlhPMUZCUVRWRExIRkNRVUZCTEVWQlFVRXNWMEZCZDBJN1VVRkJVeXh4UWtGQlFTeEZRVUZCTEZkQlFWYzdVVUZCYkVjc1QwRkJSU3hIUVVGR0xFVkJRVVVzUTBGQlVUdFJRVUZUTEUxQlFVTXNSMEZCUkN4RFFVRkRMRU5CUVU4N1VVRkJVeXhOUVVGRExFZEJRVVFzUTBGQlF5eERRVUZSTzFGQlFWTXNVMEZCU1N4SFFVRktMRWxCUVVrc1EwRkJiMEk3VVVGQlV5eFRRVUZKTEVkQlFVb3NTVUZCU1N4RFFVRlBPMGxCUVVjc1EwRkJRenRKUVVNM1NDeFhRVUZETzBGQlFVUXNRMEZCUXl4QlFVWkVMRWxCUlVNN1FVRkdXU3h2UWtGQlNUdEJRVWxxUWp0SlFVdEpMR3REUVVGdFFpeERRVUZOTEVWQlFWTXNRMEZCVFR0UlFVRnlRaXhOUVVGRExFZEJRVVFzUTBGQlF5eERRVUZMTzFGQlFWTXNUVUZCUXl4SFFVRkVMRU5CUVVNc1EwRkJTenRSUVVOd1F5eEpRVUZKTEVWQlFVVXNSMEZCUnl4M1FrRkJkMElzUTBGQlF5eFRRVUZUTEVOQlFVTXNRMEZCUXl4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRE8xRkJRMnhFTEVsQlFVa3NSVUZCUlN4SFFVRkhMRU5CUVVNc1EwRkJReXhMUVVGTExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNUMEZCVHl4RlFVRkZMRU5CUVVNN1VVRkRPVUlzU1VGQlNTeEZRVUZGTEVkQlFVY3NkMEpCUVhkQ0xFTkJRVU1zVTBGQlV5eERRVUZETEVOQlFVTXNSVUZCUlN4RlFVRkZMRU5CUVVNc1EwRkJRenRSUVVOdVJDeEpRVUZKTEVWQlFVVXNRMEZCUXl4TlFVRk5MRWxCUVVrc1JVRkJSU3hEUVVGRExFMUJRVTBzUlVGQlJUdFpRVU40UWl4SlFVRkpMRU5CUVVNc1RVRkJUU3hIUVVGSExFVkJRVVVzUTBGQlF5eE5RVUZOTEVOQlFVTTdXVUZEZUVJc1NVRkJTU3hEUVVGRExFVkJRVVVzUjBGQlJ5eEZRVUZGTEVOQlFVTXNSVUZCUlN4RFFVRkRPMWxCUTJoQ0xFbEJRVWtzUTBGQlF5eEZRVUZGTEVkQlFVY3NSVUZCUlN4RFFVRkRMRVZCUVVVc1EwRkJRenRaUVVOb1FpeEpRVUZKTEVOQlFVTXNVVUZCVVN4SFFVRkhMRXRCUVVzc1EwRkJRenRUUVVONlFqdGhRVUZOTzFsQlEwZ3NTVUZCU1N4RFFVRkRMRTFCUVUwc1IwRkJSeXhGUVVGRkxFTkJRVU1zVFVGQlRTeERRVUZETzFsQlEzaENMRWxCUVVrc1EwRkJReXhGUVVGRkxFZEJRVWNzUlVGQlJTeERRVUZETEVWQlFVVXNRMEZCUXp0WlFVTm9RaXhKUVVGSkxFTkJRVU1zUlVGQlJTeEhRVUZITEVOQlFVTXNRMEZCUXl4TlFVRk5MRWRCUVVjc1JVRkJSU3hEUVVGRExFVkJRVVVzUjBGQlJ5eEZRVUZGTEVOQlFVTXNUVUZCVFN4RFFVRkRPMWxCUTNaRExFbEJRVWtzUTBGQlF5eFJRVUZSTEVkQlFVY3NTVUZCU1N4RFFVRkRPMU5CUTNoQ08wbEJRMHdzUTBGQlF6dEpRVU5qTEd0RFFVRlRMRWRCUVhoQ0xGVkJRVFJDTEVOQlFVMHNSVUZCUlN4RFFVRk5PMUZCUTNSRExFbEJRVWtzUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXl4TlFVRk5MRU5CUVVNN1VVRkRha0lzU1VGQlNTeERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRTFCUVUwc1EwRkJRenRSUVVOcVFpeEpRVUZKTEV0QlFVc3NSMEZCUnl4RlFVRkZMRTFCUVUwc1JVRkJSU3hEUVVGRExFVkJRVVVzUlVGQlJTeEZRVUZGTEVOQlFVTXNRMEZCUXl4RlFVRkZMRVZCUVVVc1JVRkJSU3hEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETzFGQlF6RkRMRWxCUVVrc1EwRkJReXhIUVVGSExFbEJRVWtzUzBGQlN5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMUZCUTNKQ0xFdEJRVXNzU1VGQlNTeERRVUZETEVkQlFVY3NRMEZCUXl4RlFVRkZMRU5CUVVNc1IwRkJSeXhEUVVGRExFVkJRVVVzUTBGQlF5eEZRVUZGTEVWQlFVVTdXVUZEZUVJc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEhRVUZITEVsQlFVa3NTMEZCU3l4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8xbEJRM0JDTEV0QlFVc3NTVUZCU1N4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRkxFTkJRVU1zUjBGQlJ5eERRVUZETEVWQlFVVXNRMEZCUXl4RlFVRkZPMmRDUVVOMFFpeEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1MwRkJTeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVVTdiMEpCUTJZc1NVRkJTU3hEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eExRVUZMTEVOQlFVTXNTVUZCU1N4RFFVRkRMRXRCUVVzc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETzI5Q1FVTnFSU3hKUVVGSkxFTkJRVU1zUjBGQlJ5eExRVUZMTEVOQlFVTXNUVUZCVFN4RlFVRkZPM2RDUVVOc1FpeExRVUZMTEVOQlFVTXNUVUZCVFN4SFFVRkhMRU5CUVVNc1EwRkJRenQzUWtGRGFrSXNTMEZCU3l4RFFVRkRMRVZCUVVVc1IwRkJSeXhEUVVGRExFZEJRVWNzUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXp0M1FrRkRja0lzUzBGQlN5eERRVUZETEVWQlFVVXNSMEZCUnl4RFFVRkRMRWRCUVVjc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF6dHhRa0ZEZUVJN2IwSkJRVUVzUTBGQlF6dHBRa0ZEVERzN2IwSkJRVTBzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF6dFRRVU14UWp0UlFVTkVMRTlCUVU4c1MwRkJTeXhEUVVGRE8wbEJRMnBDTEVOQlFVTTdTVUZEUkN3NFEwRkJWeXhIUVVGWU8xRkJRMGtzVDBGQlR5eEpRVUZKTEVOQlFVTXNUVUZCVFN4SlFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zU1VGQlNTeERRVUZETEVOQlFVTXNRMEZCUXl4TFFVRkxMRU5CUVVNc1NVRkJTU3hEUVVGRExFVkJRVVVzUlVGQlJTeEpRVUZKTEVOQlFVTXNSVUZCUlN4SFFVRkhMRWxCUVVrc1EwRkJReXhOUVVGTkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRPMGxCUTJoR0xFTkJRVU03U1VGRFRDd3JRa0ZCUXp0QlFVRkVMRU5CUVVNc1FVRXpRMFFzU1VFeVEwTTdRVUV6UTFrc05FUkJRWGRDTzBGQmFVUnlRenRKUVhORVNTeHZRa0ZCYlVJc1lVRkJjVUlzUlVGQlJTeFJRVUUwUWl4RlFVRlRMRmxCUVhsQ08xRkJRWGhITEdsQ1FXdElRenRSUVd4SU9FVXNOa0pCUVVFc1JVRkJRU3hwUWtGQmVVSTdVVUZCY2tZc2EwSkJRV0VzUjBGQllpeGhRVUZoTEVOQlFWRTdVVUZCZFVNc2FVSkJRVmtzUjBGQldpeFpRVUZaTEVOQlFXRTdVVUZ5UkhoSExGZEJRVTBzUjBGQmEwSXNTVUZCU1N4RFFVRkRPMUZCYzBSNlFpeEpRVUZKTEVOQlFVTXNTMEZCU3l4SFFVRkhMR0ZCUVdFc1EwRkJReXhIUVVGSExFTkJRVU1zVlVGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4SlFVRkxMRTlCUVVFc1NVRkJTU3hYUVVGWExFTkJRVU1zUTBGQlF5eEZRVUZGTEZGQlFWRXNRMEZCUXl4VFFVRlRMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRVVVzVVVGQlVTeERRVUZETEZkQlFWY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGc1JTeERRVUZyUlN4RFFVRkRMRU5CUVVNN1VVRkROMGNzU1VGQlNTeERRVUZETEUxQlFVMHNSMEZCUnl4SlFVRkpMRU5CUVVNc1MwRkJTeXhEUVVGRExFMUJRVTBzUTBGQlF5eFZRVUZCTEVOQlFVTXNTVUZCUnl4UFFVRkJMRU5CUVVNc1EwRkJReXhKUVVGSkxFVkJRVTRzUTBGQlRTeERRVUZETEVOQlFVTTdVVUZETlVNc1NVRkJTU3hEUVVGRExFMUJRVTBzUjBGQlJ5eEpRVUZKTEVOQlFVTXNTMEZCU3l4RFFVRkRMRTFCUVUwc1EwRkJReXhWUVVGQkxFTkJRVU1zU1VGQlJ5eFBRVUZCTEVOQlFVTXNRMEZCUXl4RFFVRkRMRWxCUVVrc1JVRkJVQ3hEUVVGUExFTkJRVU1zUTBGQlF6dFJRVU0zUXl4SlFVRkpMRU5CUVVNc1NVRkJTU3hIUVVGSExFbEJRVWtzUTBGQlF5eFpRVUZaTEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNN1VVRkRia01zU1VGQlNTeERRVUZETEVsQlFVa3NSMEZCUnl4SlFVRkpMRU5CUVVNc1dVRkJXU3hEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETzFGQlIyNURMRWxCUVVrc1EwRkJReXhOUVVGTkxFTkJRVU1zVDBGQlR5eERRVUZETEZWQlFVRXNRMEZCUXp0WlFVTnFRaXhQUVVGQkxFTkJRVU1zUTBGQlF5eFJRVUZSTEVOQlFVTXNUMEZCVHl4RFFVRkRMRlZCUVVFc1EwRkJReXhKUVVGSExFOUJRVUVzUzBGQlNTeERRVUZETEV0QlFVc3NRMEZCVXl4RFFVRkRMRU5CUVVNc1EwRkJReXhOUVVGTkxFZEJRVWNzUTBGQlF5eEZRVUZvUXl4RFFVRm5ReXhEUVVGRE8xRkJRWGhFTEVOQlFYZEVMRU5CUVVNc1EwRkJRenRSUVVjNVJDeEpRVUZKTEVOQlFVTXNTVUZCU1N4SFFVRkhMRVZCUVVVc1VVRkJVU3hGUVVGRkxFVkJRVVVzUlVGQlJTeERRVUZETzFGQlF6ZENMRWxCUVVrc1EwRkJReXhMUVVGTExFTkJRVU1zVDBGQlR5eERRVUZETEZWQlFVRXNRMEZCUXp0WlFVTm9RaXhKUVVGSkxFOUJRVThzUTBGQlF5eERRVUZETEUxQlFVMHNTMEZCU3l4WFFVRlhMRVZCUVVVN1owSkJRMnBETEVOQlFVTXNRMEZCUXl4TlFVRk5MRWRCUVVjc1MwRkJTU3hEUVVGRExFbEJRVWtzUTBGQlF6dG5Ra0ZEY2tJc1MwRkJTU3hEUVVGRExFbEJRVWtzUTBGQlF5eFJRVUZSTEVOQlFVTXNTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF6dGhRVU5xUXp0WlFVOUVMRU5CUVVNc1EwRkJReXhMUVVGTExFZEJRVWNzUlVGQlJTeERRVUZCTzFGQlEyaENMRU5CUVVNc1EwRkJReXhEUVVGRE8xRkJSMGdzU1VGQlNTeERRVUZETEZkQlFWY3NSMEZCUnl4SlFVRkpMRU5CUVVNc1MwRkJTeXhEUVVGRExFdEJRVXNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0UlFVTjJReXhKUVVGSkxFTkJRVU1zVjBGQlZ5eERRVUZETEVsQlFVa3NRMEZCUXl4VlFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFbEJRVXNzVDBGQlFTeExRVUZKTEVOQlFVTXNVVUZCVVN4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFdEJRVWtzUTBGQlF5eFJRVUZSTEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUVc1RExFTkJRVzFETEVOQlFVTXNRMEZCUXp0UlFVdHlSU3hKUVVGSkxHbENRVUZwUWl4SFFVRkhMRWxCUVVrc1EwRkJReXhYUVVGWExFTkJRVU1zUzBGQlN5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRTlCUVU4c1JVRkJSU3hEUVVGRExFMUJRVTBzUTBGQlF5eFZRVUZCTEVOQlFVTXNTVUZCUnl4UFFVRkJMRU5CUVVNc1EwRkJReXhEUVVGRExFbEJRVWtzUlVGQlVDeERRVUZQTEVOQlFVTXNRMEZCUXp0UlFVTm9SaXhwUWtGQmFVSXNRMEZCUXl4UFFVRlBMRU5CUVVNc1ZVRkJRU3hEUVVGRE8xbEJRM1pDTEVsQlFVa3NRMEZCUXl4SFFVRkhMSEZDUVVGVExFTkJRVU1zUzBGQlN5eEZRVUZGTEVOQlFVTTdXVUZETVVJc1EwRkJReXhEUVVGRExGRkJRVkVzUTBGQlF5eFBRVUZQTEVOQlFVTXNWVUZCUVN4RFFVRkRMRWxCUVVjc1QwRkJRU3hEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETEV0QlFVc3NRMEZCUXl4TFFVRkpMRU5CUVVNc1MwRkJTeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVsQlFVa3NRMEZCUXl4RlFVRXZRaXhEUVVFclFpeERRVUZETEVOQlFVTTdXVUZEZUVRc1EwRkJReXhEUVVGRExFbEJRVWtzUjBGQlJ5eERRVUZETEVOQlFVTXNUMEZCVHl4RFFVRkRMRXRCUVVrc1EwRkJReXhaUVVGWkxFTkJRVU1zUTBGQlF6dFJRVU14UXl4RFFVRkRMRU5CUVVNc1EwRkJRenRSUVVWSUxFbEJRVWtzVDBGQlR5eEhRVUZITEVsQlFVa3NRMEZCUXl4VFFVRlRMRU5CUVVNc1NVRkJTU3hEUVVGRExFbEJRVWtzUTBGQlF5eEhRVUZITEVOQlFVTXNWVUZCUVN4RFFVRkRMRWxCUVVjc1QwRkJRU3hEUVVGRExFTkJRVU1zUjBGQlJ5eEZRVUZNTEVOQlFVc3NRMEZCUXl4RFFVRkRMRU5CUVVNN1VVRkRka1FzU1VGQlNTeFBRVUZQTEVkQlFVY3NTVUZCU1N4RFFVRkRMRk5CUVZNc1EwRkJReXhKUVVGSkxFTkJRVU1zU1VGQlNTeERRVUZETEVkQlFVY3NRMEZCUXl4VlFVRkJMRU5CUVVNc1NVRkJSeXhQUVVGQkxFTkJRVU1zUTBGQlF5eEhRVUZITEVWQlFVd3NRMEZCU3l4RFFVRkRMRU5CUVVNc1EwRkJRenRSUVVkMlJDeEpRVUZKTEVsQlFVa3NSMEZCUnl4UFFVRlBMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRVVVzU1VGQlNTeEhRVUZITEU5QlFVOHNRMEZCUXl4UFFVRlBMRU5CUVVNc1RVRkJUU3hIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETzFGQlF6RkVMRWxCUVVrc1NVRkJTU3hIUVVGSExFOUJRVThzUTBGQlF5eERRVUZETEVOQlFVTXNSVUZCUlN4SlFVRkpMRWRCUVVjc1QwRkJUeXhEUVVGRExFOUJRVThzUTBGQlF5eE5RVUZOTEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNN1VVRkhNVVFzU1VGQlNTeE5RVUZOTEVkQlFVY3NTVUZCU1N4RFFVRkRMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zVlVGQlFTeERRVUZETEVsQlFVY3NUMEZCUVN4RFFVRkxMRVZCUVVVc1JVRkJSU3hGUVVGRkxFbEJRVWtzUlVGQlJTeEZRVUZGTEVWQlFVVXNTVUZCU1N4RlFVRkZMRVZCUVVVc1JVRkJSU3hEUVVGRExFTkJRVU1zUjBGQlJ5eEZRVUZGTEVWQlFVVXNSVUZCUlN4RFFVRkRMRU5CUVVNc1IwRkJSeXhGUVVGRkxFTkJRVUVzUlVGQmFrUXNRMEZCYVVRc1EwRkJRenRoUVVNMVJTeE5RVUZOTEVOQlFVTXNUMEZCVHl4RFFVRkRMRWRCUVVjc1EwRkJReXhWUVVGQkxFTkJRVU1zU1VGQlJ5eFBRVUZCTEVOQlFVc3NSVUZCUlN4RlFVRkZMRVZCUVVVc1NVRkJTU3hGUVVGRkxFVkJRVVVzUlVGQlJTeEpRVUZKTEVWQlFVVXNSVUZCUlN4RlFVRkZMRU5CUVVNc1JVRkJSU3hGUVVGRkxFVkJRVVVzUTBGQlF5eEZRVUZGTEVOQlFVRXNSVUZCZWtNc1EwRkJlVU1zUTBGQlF5eERRVUZETEVOQlFVTTdVVUZIZUVVc1NVRkJTU3hOUVVGTkxFZEJRVWNzU1VGQlNTeERRVUZETEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1ZVRkJRU3hEUVVGRExFbEJRVWNzVDBGQlFTeERRVUZMTEVWQlFVVXNSVUZCUlN4RlFVRkZMRU5CUVVNc1EwRkJReXhIUVVGSExFVkJRVVVzUlVGQlJTeEZRVUZGTEVOQlFVTXNRMEZCUXl4SFFVRkhMRVZCUVVVc1JVRkJSU3hGUVVGRkxFbEJRVWtzUlVGQlJTeEZRVUZGTEVWQlFVVXNTVUZCU1N4RlFVRkZMRU5CUVVFc1JVRkJha1FzUTBGQmFVUXNRMEZCUXp0aFFVTTFSU3hOUVVGTkxFTkJRVU1zVDBGQlR5eERRVUZETEVkQlFVY3NRMEZCUXl4VlFVRkJMRU5CUVVNc1NVRkJSeXhQUVVGQkxFTkJRVXNzUlVGQlJTeEZRVUZGTEVWQlFVVXNRMEZCUXl4RlFVRkZMRVZCUVVVc1JVRkJSU3hEUVVGRExFVkJRVVVzUlVGQlJTeEZRVUZGTEVsQlFVa3NSVUZCUlN4RlFVRkZMRVZCUVVVc1NVRkJTU3hGUVVGRkxFTkJRVUVzUlVGQmVrTXNRMEZCZVVNc1EwRkJReXhEUVVGRExFTkJRVU03VVVGSGVFVXNTVUZCU1N4TFFVRkxMRWRCUVVjc1RVRkJUU3hEUVVGRExFMUJRVTBzUTBGQlF5eE5RVUZOTEVOQlFVTXNRMEZCUXp0UlFVZHNReXhMUVVGTExFTkJRVU1zVDBGQlR5eERRVUZETEZWQlFVRXNRMEZCUXl4SlFVRkhMRTlCUVVFc1EwRkJReXhEUVVGRExFdEJRVXNzUjBGQlJ5eEZRVUZGTEVWQlFWb3NRMEZCV1N4RFFVRkRMRU5CUVVNN1VVRkhhRU1zU1VGQlNTeERRVUZETEV0QlFVc3NSMEZCUnl4RlFVRkZMRU5CUVVNN1VVRkRhRUlzU1VGQlNTeERRVUZETEV0QlFVc3NSMEZCUnl4RlFVRkZMRU5CUVVNN1VVRkhhRUlzVFVGQlRTeERRVUZETEU5QlFVOHNRMEZCUXl4VlFVRkJMRU5CUVVNN1dVRkRXaXhQUVVGQkxFMUJRVTBzUTBGQlF5eFBRVUZQTEVOQlFVTXNWVUZCUVN4RFFVRkRPMmRDUVVOYUxFbEJRVWtzUTBGQlF5eEhRVUZITEVsQlFVa3NTVUZCU1N4RFFVRkRMRXRCUVVrc1EwRkJReXhMUVVGTExFTkJRVU1zVFVGQlRTeEZRVUZGTEVOQlFVTXNRMEZCUXl4RlFVRkZMRVZCUVVVc1EwRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETzJkQ1FVTm9SQ3hEUVVGRExFTkJRVU1zUzBGQlN5eERRVUZETEVsQlFVa3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRuUWtGRGFFSXNRMEZCUXl4RFFVRkRMRXRCUVVzc1EwRkJReXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdaMEpCUTJoQ0xFdEJRVWtzUTBGQlF5eExRVUZMTEVOQlFVTXNTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8yZENRVWR1UWl4SlFVRkpMRU5CUVVNc1IwRkJSeXhMUVVGSkxFTkJRVU1zVjBGQlZ5eERRVUZETEUxQlFVMHNRMEZCUXp0blFrRkRhRU1zVDBGQlR5eERRVUZETEVWQlFVVXNSMEZCUnl4RFFVRkRMRVZCUVVVN2IwSkJRMW9zU1VGQlNTeEpRVUZKTEVkQlFVY3NTMEZCU1N4RFFVRkRMRmRCUVZjc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGRE1VSXNRMEZCUXl4SFFVRkhMRWxCUVVrc1EwRkJReXhKUVVGSkxFTkJRVU03YjBKQlEyeENMRWxCUVVrc1JVRkJSU3hIUVVGSExFbEJRVWtzUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUlVGQlJTeEZRVUZGTEVOQlFVTXNSVUZETTBJc1JVRkJSU3hIUVVGSExFbEJRVWtzUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUlVGQlJTeEZRVUZGTEVOQlFVTXNRMEZCUXp0dlFrRkRhRU1zU1VGQlNTeEZRVUZGTEVkQlFVY3NRMEZCUXl4RFFVRkRMRXRCUVVzc1JVRkJSU3hIUVVGSExFTkJRVU1zU1VGQlNTeEZRVUZGTEVkQlFVY3NRMEZCUXl4RFFVRkRMRTFCUVUwc1JVRkJSU3hIUVVGSExFTkJRVU1zUlVGQlJUdDNRa0ZEY2tNc1EwRkJSU3hEUVVGRExFbEJRVWtzUjBGQlJ5eEpRVUZKTEVOQlFVTTdkMEpCUTNKQ0xFMUJRVTA3Y1VKQlExUTdhVUpCUTBvN1dVRkRUQ3hEUVVGRExFTkJRVU03VVVGc1FrWXNRMEZyUWtVc1EwRkRSQ3hEUVVGRE8xRkJSVTRzUzBGQlN5eERRVUZETEU5QlFVOHNRMEZCUXl4VlFVRkRMRU5CUVVNc1JVRkJSU3hGUVVGRk8xbEJSV2hDTEV0QlFVa3NRMEZCUXl4TFFVRkxMRU5CUVVNc1QwRkJUeXhEUVVGRExGVkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTTdaMEpCUTNCQ0xFTkJRVU1zUTBGQlF5eEpRVUZKTEVOQlFVTXNhVUpCUVdsQ0xFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVVXNSVUZCUlN4RFFVRkRMRU5CUVVNc1JVRkJSU3hGUVVGRkxFTkJRVU1zUTBGQlF5eEZRVUZGTEVWQlFVVXNRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhEUVVGRExFOUJRVThzUTBGQlF5eFZRVUZETEZOQlFWTXNSVUZCUlN4RFFVRkRPMjlDUVVWc1JTeEpRVUZKTEVOQlFVTXNSMEZCUnl4SlFVRkpMRWxCUVVrc1EwRkJReXhMUVVGSkxFTkJRVU1zUzBGQlN5eERRVUZETEUxQlFVMHNSVUZCUlN4VFFVRlRMRU5CUVVNc1EwRkJReXhGUVVGRkxGTkJRVk1zUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRE8yOUNRVU53UlN4TFFVRkpMRU5CUVVNc1MwRkJTeXhEUVVGRExFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0dlFrRkRia0lzUTBGQlF5eERRVUZETEV0QlFVc3NRMEZCUXl4SlFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03YjBKQlEyaENMRU5CUVVNc1EwRkJReXhMUVVGTExFTkJRVU1zU1VGQlNTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMmRDUVVOd1FpeERRVUZETEVOQlFVTXNRMEZCUXp0WlFVTlFMRU5CUVVNc1EwRkJReXhEUVVGRE8xbEJSMGdzU1VGQlNTeFBRVUZQTEVkQlFVY3NTVUZCU1N4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQlJTeEhRVUZITEVOQlFVTXNRMEZCUXl4RlFVRkZMRU5CUVVNc1IwRkJSeXhIUVVGSExFTkJRVU03V1VGRE1VTXNTVUZCU1N4TFFVRkxMRWRCUVVjc1ZVRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eEpRVUZMTEU5QlFVRXNUMEZCVHl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkJMMElzUTBGQkswSXNRMEZCUXp0WlFVTjBSQ3hEUVVGRExFTkJRVU1zUzBGQlN5eERRVUZETEVsQlFVa3NRMEZCUXl4TFFVRkxMRU5CUVVNc1EwRkJRenRaUVVOd1FpeExRVUZMTEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1JVRkJSU3hEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETEV0QlFVc3NRMEZCUXl4TlFVRk5MRVZCUVVVc1EwRkJReXhGUVVGRkxFVkJRVVU3WjBKQlEzSkRMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eExRVUZMTEVOQlFVTXNRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNTMEZCU3l4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8yZENRVU4yUXl4SlFVRkpMRU5CUVVNc1EwRkJReXhKUVVGSkxFbEJRVWtzUTBGQlF5eERRVUZETEVsQlFVa3NTMEZCU3l4RFFVRkRMRU5CUVVNc1NVRkJTU3hKUVVGSkxFTkJRVU1zUTBGQlF5eEpRVUZKTEVOQlFVTXNTVUZCU1R0dlFrRkJSU3hUUVVGVE8yZENRVU42UkN4TFFVRkpMRU5CUVVNc1MwRkJTeXhEUVVGRExFbEJRVWtzUTBGQlF5eEZRVUZGTEUxQlFVMHNSVUZCUlN4RFFVRkRMRU5CUVVNc1JVRkJSU3hGUVVGRkxFMUJRVTBzUlVGQlJTeERRVUZETEVOQlFVTXNSVUZCUlN4RlFVRkZMRTFCUVUwc1JVRkJSU3hKUVVGSkxFTkJRVU1zUjBGQlJ5eERRVUZETEV0QlFVc3NRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTTdZVUZEYkVZN1VVRkRUQ3hEUVVGRExFTkJRVU1zUTBGQlF6dEpRVWxRTEVOQlFVTTdTVUUxU2s4c2QwSkJRVWNzUjBGQldDeFZRVUZaTEVOQlFVTXNTVUZCU1N4UFFVRlBMRU5CUVVNc1EwRkJReXhOUVVGTkxFTkJRVU1zVlVGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4SlFVRkxMRTlCUVVFc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlRDeERRVUZMTEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1RVRkJUU3hEUVVGQkxFTkJRVU1zUTBGQlF6dEpRVWwwUkN4cFEwRkJXU3hIUVVGd1FpeFZRVUZ4UWl4SlFVRkpPMUZCUTNKQ0xFbEJRVWtzVDBGQlR5eEhRVUZITEVWQlFVVXNRMEZCUXp0UlFVTnFRaXhKUVVGSkxFVkJRVVVzUjBGQlJ5eEpRVUZKTEVOQlFVTXNUVUZCVFN4RFFVRkRMRXRCUVVzc1EwRkJReXhEUVVGRExFVkJRVVVzU1VGQlNTeERRVUZETEUxQlFVMHNRMEZCUXl4TlFVRk5MRU5CUVVNc1EwRkJRenRSUVVOc1JDeFBRVUZQTEVWQlFVVXNRMEZCUXl4TlFVRk5MRWRCUVVjc1EwRkJReXhGUVVGRk8xbEJSV3hDTEVsQlFVa3NWMEZCVnl4SFFVRkhMRVZCUVVVc1EwRkJReXhOUVVGTkxFTkJRVU1zVlVGQlFTeERRVUZETEVsQlFVY3NUMEZCUVN4RFFVRkRMRU5CUVVNc1NVRkJTU3hEUVVGRExGTkJRVk1zUjBGQlJ5eEpRVUZKTEVOQlFVTXNWMEZCVnl4RlFVRkZMRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNTVUZCU1N4RFFVRkRMRVZCUVd4RUxFTkJRV3RFTEVOQlFVTXNRMEZCUXp0WlFVTndSaXhKUVVGSkxFZEJRVWNzUjBGQlJ6dG5Ra0ZEVGl4TFFVRkxMRVZCUVVVc1YwRkJWenRuUWtGRGJFSXNSMEZCUnl4RlFVRkZMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zVjBGQlZ5eERRVUZETEVkQlFVY3NRMEZCUXl4VlFVRkJMRU5CUVVNc1NVRkJSeXhQUVVGQkxFTkJRVU1zUTBGQlF5eEpRVUZKTEVOQlFVTXNSMEZCUnl4SFFVRkhMRWxCUVVrc1EwRkJReXhGUVVGRkxFVkJRWEJDTEVOQlFXOUNMRU5CUVVNc1EwRkJRenRoUVVNelJDeERRVUZETzFsQlEwWXNUMEZCVHl4RFFVRkRMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF6dFpRVU5zUWl4SFFVRkhMRU5CUVVNc1MwRkJTeXhEUVVGRExFOUJRVThzUTBGQlF5eFZRVUZCTEVOQlFVTXNTVUZCUnl4UFFVRkJMRVZCUVVVc1EwRkJReXhOUVVGTkxFTkJRVU1zUlVGQlJTeERRVUZETEU5QlFVOHNRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zUlVGQk0wSXNRMEZCTWtJc1EwRkJReXhEUVVGRE8xTkJRM1JFTzFGQlEwUXNUMEZCVHl4RFFVRkRMRWxCUVVrc1EwRkJReXhWUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVsQlFVc3NUMEZCUVN4RFFVRkRMRU5CUVVNc1IwRkJSeXhIUVVGSExFTkJRVU1zUTBGQlF5eEhRVUZITEVWQlFXSXNRMEZCWVN4RFFVRkRMRU5CUVVFN1VVRkRja01zVDBGQlR5eFBRVUZQTEVOQlFVTTdTVUZEYmtJc1EwRkJRenRKUVVkUExEWkNRVUZSTEVkQlFXaENMRlZCUVdsQ0xFTkJRVU03VVVGRFpDeEpRVUZKTEV0QlFVc3NSMEZCUnl4RFFVRkRMRU5CUVVNN1VVRkRaQ3hQUVVGUExFTkJRVU1zUTBGQlF5eE5RVUZOTEV0QlFVc3NTVUZCU1N4RFFVRkRMRWxCUVVrc1JVRkJSVHRaUVVNelFpeExRVUZMTEVWQlFVVXNRMEZCUXp0WlFVTlNMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zVFVGQlRTeERRVUZETzFOQlEyaENPMUZCUTBRc1QwRkJUeXhMUVVGTExFTkJRVU03U1VGRGFrSXNRMEZCUXp0SlFVZFBMRGhDUVVGVExFZEJRV3BDTEZWQlFXdENMRU5CUVVNN1VVRkRaaXhKUVVGSkxFZEJRVWNzUjBGQlJ5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzFGQlEzUkNMRWxCUVVrc1NVRkJTU3hIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRWRCUVVjc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF6dFJRVU0xUWl4TFFVRkxMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRTFCUVUwc1JVRkJSU3hEUVVGRExFVkJRVVVzUlVGQlJUdFpRVU12UWl4SlFVRkpMRU5CUVVNc1NVRkJTU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJReXhEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJRenRUUVVOd1F6dFJRVU5FTEVsQlFVa3NRMEZCUXl4SlFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eE5RVUZOTEVkQlFVY3NRMEZCUXl4RFFVRkRMRWRCUVVjc1IwRkJSeXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETzFGQlEzSkRMRTlCUVU4c1NVRkJTU3hEUVVGRE8wbEJRMmhDTEVOQlFVTTdTVUYxU0U4c1owTkJRVmNzUjBGQmJrSXNWVUZCYjBJc1EwRkJRenRSUVVOcVFpeEpRVUZKTEU5QlFVOHNSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8xRkJRMnhDTEVkQlFVYzdXVUZEUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFMUJRVTBzUTBGQlF6dFpRVU5pTEU5QlFVOHNRMEZCUXl4SlFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03VTBGRGJrSXNVVUZCVVN4RFFVRkRMRXRCUVVzc1NVRkJTU3hEUVVGRExFbEJRVWtzUlVGQlJUdFJRVU14UWl4UFFVRlBMRTlCUVU4c1EwRkJReXhQUVVGUExFVkJRVVVzUTBGQlF6dEpRVU0zUWl4RFFVRkRPMGxCUjA4c05FTkJRWFZDTEVkQlFTOUNMRlZCUVdkRExFTkJRVU1zUlVGQlJTeERRVUZETzFGQlEyaERMRWxCUVVrc1JVRkJSU3hIUVVGSExFbEJRVWtzUTBGQlF5eFhRVUZYTEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUVVVc1JVRkJSU3hIUVVGSExFbEJRVWtzUTBGQlF5eFhRVUZYTEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF6dFJRVU01UkN4UFFVRlBMRVZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU1zUzBGQlN5eEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRPMWxCUVVVc1EwRkJReXhGUVVGRkxFTkJRVU03VVVGRk5VSXNUMEZCVHl4RlFVRkZMR05CUVdNc1JVRkJSU3hGUVVGRkxFTkJRVU1zUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXl4RlFVRkZMRkZCUVZFc1JVRkJSU3hGUVVGRkxFTkJRVU1zUzBGQlN5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRTFCUVUwc1EwRkJReXhGUVVGRkxFTkJRVU1zUzBGQlN5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJRenRKUVVOd1JpeERRVUZETzBsQlNVUXNjVU5CUVdkQ0xFZEJRV2hDTEZWQlFXbENMRU5CUVVNc1JVRkJSU3hEUVVGRE8xRkJRWEpDTEdsQ1FWZERPMUZCVmtjc1NVRkJTU3hKUVVGSkxFZEJRVWNzU1VGQlNTeERRVUZETEhWQ1FVRjFRaXhEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTXNRMEZCUXp0UlFVTTVReXhKUVVGSkxHRkJRV0VzUjBGQlJ5eEZRVUZGTEVOQlFVTTdVVUZEZGtJc1NVRkJTU3hEUVVGRExGRkJRVkVzUTBGQlF5eFBRVUZQTEVOQlFVTXNWVUZCUVN4RFFVRkRMRWxCUVVjc1QwRkJRU3hoUVVGaExFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4SFFVRkhMRVZCUVVVc1JVRkJlRUlzUTBGQmQwSXNRMEZCUXl4RFFVRkRPMUZCUTNCRUxFbEJRVWtzVTBGQlV5eEhRVUZITEVsQlFVa3NRMEZCUXl4alFVRmpMRU5CUVVNc1VVRkJVU3hEUVVGRExFMUJRVTBzUTBGQlF5eFZRVUZCTEVOQlFVTXNTVUZCUnl4UFFVRkJMRU5CUVVNc1EwRkJReXhEUVVGRExFbEJRVWtzWVVGQllTeERRVUZETEVWQlFYSkNMRU5CUVhGQ0xFTkJRVU1zUTBGQlF6dFJRVVV2UlN4SlFVRkpMRU5CUVVNc1VVRkJVVHRoUVVOU0xFMUJRVTBzUTBGQlF5eFZRVUZCTEVOQlFVTXNTVUZCUnl4UFFVRkJMRU5CUVVNc1EwRkJReXhOUVVGTkxFdEJRVXNzU1VGQlNTeERRVUZETEdOQlFXTXNSVUZCYUVNc1EwRkJaME1zUTBGQlF6dGhRVU0xUXl4UFFVRlBMRU5CUVVNc1ZVRkJRU3hEUVVGRExFbEJRVWNzVDBGQlFTeFRRVUZUTEVkQlFVY3NVMEZCVXl4RFFVRkRMRTFCUVUwc1EwRkJReXhEUVVGRExFTkJRVU1zVFVGQlRTeERRVUZETEZGQlFWRXNRMEZCUXl4TlFVRk5MRU5CUVVNc1ZVRkJRU3hEUVVGRExFbEJRVWNzVDBGQlFTeERRVUZETEV0QlFVc3NRMEZCUXl4RFFVRkRMRVZCUVVVc1JVRkJWaXhEUVVGVkxFTkJRVU1zUTBGQlF5eEZRVUYwUlN4RFFVRnpSU3hEUVVGRExFTkJRVU03VVVGRmVrWXNUMEZCVHl4VFFVRlRMRU5CUVVNc1IwRkJSeXhEUVVGRExGVkJRVUVzUTBGQlF5eEpRVUZITEU5QlFVRXNTMEZCU1N4RFFVRkRMRXRCUVVzc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQllpeERRVUZoTEVOQlFVTXNRMEZCUXp0SlFVTTFReXhEUVVGRE8wbEJTVTBzZVVKQlFXTXNSMEZCY2tJc1ZVRkJjMElzVFVGQlRTeEZRVUZGTEVOQlFVTXNSVUZCUlN4RFFVRkRPMUZCUlRsQ0xFbEJRVWtzVTBGQlV5eEhRVUZITEVWQlFVVXNRMEZCUXp0UlFVTnVRaXhMUVVGTExFbEJRVWtzUlVGQlJTeEhRVUZITEVOQlFVTXNSVUZCUlN4RlFVRkZMRWRCUVVjc1RVRkJUU3hEUVVGRExFMUJRVTBzUlVGQlJTeEZRVUZGTEVWQlFVVXNSVUZCUlR0WlFVTjJReXhKUVVGSkxFdEJRVXNzUjBGQlJ5eE5RVUZOTEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNN1dVRkRka0lzUzBGQlN5eEpRVUZKTEVWQlFVVXNSMEZCUnl4RFFVRkRMRVZCUVVVc1JVRkJSU3hIUVVGSExFdEJRVXNzUTBGQlF5eE5RVUZOTEVWQlFVVXNSVUZCUlN4RlFVRkZMRVZCUVVVN1owSkJRM1JETEVsQlFVa3NRMEZCUXl4SFFVRlJMRXRCUVVzc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF6dG5Ra0ZEZGtJc1EwRkJReXhEUVVGRExFMUJRVTBzUjBGQlJ5eEZRVUZGTEVOQlFVTTdaMEpCUTJRc1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlJ5eEZRVUZGTEVOQlFVTTdaMEpCUTFRc1NVRkJTU3hIUVVGSExFZEJRVWNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRuUWtGRE5VSXNTVUZCU1N4SlFVRkpMRU5CUVVNc1IwRkJSeXhEUVVGRExFZEJRVWNzUTBGQlF5eEhRVUZITEVkQlFVY3NSVUZCUlR0dlFrRkRja0lzVTBGQlV5eERRVUZETEVsQlFVa3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRwUWtGRGNrSTdZVUZEU2p0VFFVTktPMUZCUTBRc1UwRkJVeXhEUVVGRExFbEJRVWtzUTBGQlF5eFZRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRWxCUVVzc1QwRkJRU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RlFVRnFRaXhEUVVGcFFpeERRVUZETEVOQlFVTTdVVUZITlVNc1NVRkJTU3haUVVGWkxFZEJRVWNzUlVGQlJTeERRVUZETzFGQlEzUkNMRWxCUVVrc1ZVRkJWU3hIUVVGSExFbEJRVWtzUTBGQlF6dFJRVU4wUWl4TFFVRkxMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NVMEZCVXl4RFFVRkRMRTFCUVUwc1JVRkJSU3hEUVVGRExFVkJRVVVzUlVGQlJUdFpRVU4yUXl4SlFVRkpMRU5CUVVNc1IwRkJSeXhUUVVGVExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdXVUZEY2tJc1NVRkJTU3hEUVVGRExGVkJRVlVzU1VGQlNTeEpRVUZKTEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4VlFVRlZMRU5CUVVNc1IwRkJSeXhEUVVGRExFZEJRVWNzUjBGQlJ5eEZRVUZGTzJkQ1FVTjZSQ3hWUVVGVkxFZEJRVWNzUlVGQlJTeEhRVUZITEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEZRVUZGTEZGQlFWRXNSVUZCUlN4RlFVRkZMRVZCUVVVc1EwRkJRenRuUWtGRE5VTXNXVUZCV1N4RFFVRkRMRWxCUVVrc1EwRkJReXhWUVVGVkxFTkJRVU1zUTBGQlF6dGhRVU5xUXp0WlFVTkVMRlZCUVZVc1EwRkJReXhSUVVGUkxFTkJRVU1zU1VGQlNTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMU5CUXk5Q08xRkJRMFFzVDBGQlR5eFpRVUZaTEVOQlFVTTdTVUZEZUVJc1EwRkJRenRKUVZOTkxHOUNRVUZUTEVkQlFXaENMRlZCUVdsQ0xFTkJRVk1zUlVGQlJTeERRVUZUTEVWQlFVVXNUVUZCVFN4RlFVRkZMRkZCUVZFc1JVRkJSU3hOUVVGTkxFVkJRVVVzUjBGQlZ6dFJRVU40UlN4SlFVRkpMRU5CUVVNc1IwRkJSeXhSUVVGUkxFTkJRVU1zVFVGQlRTeERRVUZETzFGQlEzaENMRWxCUVVrc1EwRkJReXhKUVVGSkxFTkJRVU03V1VGQlJTeFBRVUZQTzFGQlEyNUNMRWxCUVVrc1JVRkJSU3hIUVVGSExGRkJRVkVzUTBGQlF5eEhRVUZITEVOQlFVTXNWVUZCUVN4RFFVRkRMRWxCUVVrc1QwRkJRU3hKUVVGSkxHVkJRVkVzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQmNrSXNRMEZCY1VJc1EwRkJReXhEUVVGRE8xRkJRMnhFTEVsQlFVa3NSVUZCUlN4SFFVRkhMRVZCUVVVc1EwRkJRenRSUVVOYUxFdEJRVXNzU1VGQlNTeERRVUZETEVkQlFVY3NRMEZCUXl4RlFVRkZMRU5CUVVNc1IwRkJSeXhEUVVGRExFVkJRVVVzUTBGQlF5eEZRVUZGTEVWQlFVVTdXVUZEZUVJc1MwRkJTeXhKUVVGSkxFTkJRVU1zUjBGQlJ5eERRVUZETEVWQlFVVXNRMEZCUXl4SFFVRkhMRU5CUVVNc1JVRkJSU3hEUVVGRExFVkJRVVVzUlVGQlJUdG5Ra0ZEZUVJc1NVRkJTU3hEUVVGRExFdEJRVXNzUTBGQlF6dHZRa0ZCUlN4VFFVRlRPMmRDUVVOMFFpeEpRVUZKTEVWQlFVVXNSMEZCUnl4UlFVRlJMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRMmhDTEVWQlFVVXNSMEZCUnl4UlFVRlJMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRMmhDTEVWQlFVVXNSMEZCUnl4RlFVRkZMRU5CUVVNc1RVRkJUU3hGUVVOa0xFVkJRVVVzUjBGQlJ5eEZRVUZGTEVOQlFVTXNUVUZCVFN4RlFVTmtMRWxCUVVrc1IwRkJSeXhEUVVGRExFTkJRVU1zUlVGRFZDeEpRVUZKTEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNN1owSkJUV1FzU1VGQlNTeERRVUZETEVsQlFVa3NSMEZCUnl4RlFVRkZPMjlDUVVOV0xFbEJRVWtzVFVGQlRTeERRVUZETEVWQlFVVXNSVUZCUlN4RlFVRkZMRU5CUVVNc1JVRkJSVHQzUWtGRmFFSXNTVUZCU1N4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEZRVUZGT3pSQ1FVTnlRaXhKUVVGSkxFZEJRVWNzUTBGQlF5eEZRVUZGTEVsQlFVa3NSMEZCUnl4RFFVRkRMRU5CUVVNN2VVSkJRM1JDT3paQ1FVRk5PelJDUVVOSUxFbEJRVWtzUjBGQlJ5eERRVUZETEVWQlFVVXNTVUZCU1N4SFFVRkhMRU5CUVVNc1EwRkJRenQ1UWtGRGRFSTdjVUpCUTBvN2FVSkJRMG83Y1VKQlFVMDdiMEpCUTBnc1NVRkJTU3hOUVVGTkxFTkJRVU1zUlVGQlJTeEZRVUZGTEVWQlFVVXNRMEZCUXl4RlFVRkZPM2RDUVVOb1FpeEpRVUZKTEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlJ5eEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRVVU3TkVKQlEzSkNMRWxCUVVrc1IwRkJSeXhEUVVGRExFVkJRVVVzU1VGQlNTeEhRVUZITEVOQlFVTXNRMEZCUXp0NVFrRkRkRUk3TmtKQlFVMDdORUpCUTBnc1NVRkJTU3hIUVVGSExFTkJRVU1zUlVGQlJTeEpRVUZKTEVkQlFVY3NRMEZCUXl4RFFVRkRPM2xDUVVOMFFqdHhRa0ZEU2p0cFFrRkRTanRuUWtGRFJDeEpRVUZKTEVsQlFVa3NTVUZCU1N4RFFVRkRMRVZCUVVVN2IwSkJSVmdzUlVGQlJTeERRVUZETEVsQlFVa3NRMEZCUXl4SlFVRkpMR2xDUVVGVkxFTkJRVU1zUlVGQlJTeERRVUZETEVsQlFVa3NRMEZCUXl4RlFVRkZMRVZCUVVVc1EwRkJReXhKUVVGSkxFTkJRVU1zUlVGQlJTeEhRVUZITEVOQlFVTXNRMEZCUXl4RFFVRkRPMmxDUVVOd1JEdGhRVU5LTzFOQlEwbzdVVUZEUkN4SlFVRkpMRTFCUVUwc1IwRkJSeXhKUVVGSkxHRkJRVTBzUTBGQlF5eEZRVUZGTEVWQlFVVXNSVUZCUlN4RFFVRkRMRU5CUVVNN1VVRkRhRU1zVFVGQlRTeERRVUZETEV0QlFVc3NSVUZCUlN4RFFVRkRPMUZCUTJZc1JVRkJSU3hEUVVGRExFOUJRVThzUTBGQlF5eFZRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRPMWxCUTFvc1NVRkJTU3hEUVVGRExFZEJRVWNzVVVGQlVTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMWxCUTNCQ0xFbEJRVWtzUjBGQlJ5eEhRVUZITEVOQlFVTXNRMEZCUXl4UlFVRlJMRVZCUVVVc1EwRkJRenRaUVVOMlFpeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFZEJRVWNzUTBGQlF6dFpRVU40UWl4SlFVRkpMRXRCUVVzc1IwRkJSeXhOUVVGTkxFTkJRVU1zUTBGQlF5eERRVUZETEUxQlFVMHNRMEZCUXl4RFFVRkRPMWxCUXpkQ0xFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4RFFVRkRPMmRDUVVGRkxFdEJRVXNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRWRCUVVjc1EwRkJRenRaUVVONFF5eEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1MwRkJTeXhEUVVGRExFMUJRVTBzUjBGQlJ5eERRVUZETzJkQ1FVRkZMRXRCUVVzc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEhRVUZITEVkQlFVY3NRMEZCUXp0UlFVTXpSQ3hEUVVGRExFTkJRVU1zUTBGQlF6dEpRVU5RTEVOQlFVTTdTVUZGVFN4M1FrRkJZU3hIUVVGd1FpeFZRVUZ4UWl4TlFVRk5MRVZCUVVVc1EwRkJVeXhGUVVGRkxFTkJRVk1zUlVGQlJTeE5RVUV5UXl4RlFVRkZMRWRCUVZjN1VVRkRka2NzU1VGQlNTeFpRVUZaTEVkQlFVY3NWVUZCVlN4RFFVRkRMR05CUVdNc1EwRkJReXhOUVVGTkxFVkJRVVVzUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRPMUZCUlRORUxFdEJRVXNzU1VGQlNTeERRVUZETEVkQlFVY3NRMEZCUXl4RlFVRkZMRU5CUVVNc1IwRkJSeXhaUVVGWkxFTkJRVU1zVFVGQlRTeEZRVUZGTEVOQlFVTXNSVUZCUlN4RlFVRkZPMWxCUXpGRExFbEJRVWtzUlVGQlJTeEhRVUZITEZsQlFWa3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRaUVVONlFpeEpRVUZKTEUxQlFVMHNSMEZCUnl4RlFVRkZMRU5CUVVNN1dVRkRhRUlzUzBGQlN5eEpRVUZKTEVOQlFVTXNSMEZCUnl4RFFVRkRMRVZCUVVVc1EwRkJReXhIUVVGSExFVkJRVVVzUTBGQlF5eFJRVUZSTEVOQlFVTXNUVUZCVFN4RlFVRkZMRU5CUVVNc1JVRkJSU3hGUVVGRk8yZENRVU42UXl4SlFVRkpMRU5CUVVNc1IwRkJSeXhGUVVGRkxFTkJRVU1zVVVGQlVTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMmRDUVVOMlFpeE5RVUZOTEVOQlFVTXNTVUZCU1N4RFFVRkRMRVZCUVVVc1NVRkJTU3hGUVVGRkxFTkJRVU1zUlVGQlJTeERRVUZETEVWQlFVVXNRMEZCUXl4RlFVRkZMRWRCUVVjc1JVRkJSU3hKUVVGSkxFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTTdaMEpCUTJoRkxFMUJRVTBzUTBGQlF5eEpRVUZKTEVOQlFVTXNSVUZCUlN4SlFVRkpMRVZCUVVVc1EwRkJReXhGUVVGRkxFTkJRVU1zUlVGQlJTeERRVUZETEVWQlFVVXNSMEZCUnl4RlFVRkZMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF6dGhRVU51UlR0WlFVTkVMRTFCUVUwc1EwRkJReXhKUVVGSkxFTkJRVU1zVlVGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4SlFVRkxMRTlCUVVFc1EwRkJReXhEUVVGRExFZEJRVWNzUjBGQlJ5eERRVUZETEVOQlFVTXNSMEZCUnl4SFFVRkhMRU5CUVVNc1EwRkJReXhKUVVGSkxFZEJRVWNzUTBGQlF5eERRVUZETEVsQlFVa3NSVUZCTDBJc1EwRkJLMElzUTBGQlF5eERRVUZETzFsQlEzWkVMRWxCUVVrc1NVRkJTU3hIUVVGSExFVkJRVVVzUTBGQlF6dFpRVU5rTEVsQlFVa3NVMEZCVXl4SFFVRkhMRU5CUVVNc1EwRkJRenRaUVVOc1FpeE5RVUZOTEVOQlFVTXNUMEZCVHl4RFFVRkRMRlZCUVVFc1EwRkJRenRuUWtGRFdpeEpRVUZKTEVOQlFVTXNRMEZCUXl4SlFVRkpMRXRCUVVzc1EwRkJReXhGUVVGRk8yOUNRVU5rTEVsQlFVa3NRMEZCUXl4SlFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzI5Q1FVTm1MRk5CUVZNc1JVRkJSU3hEUVVGRE8ybENRVU5tTzNGQ1FVRk5PMjlDUVVOSUxGTkJRVk1zUlVGQlJTeERRVUZETzJsQ1FVTm1PMmRDUVVORUxFbEJRVWtzVTBGQlV5eEpRVUZKTEVOQlFVTXNSVUZCUlR0dlFrRkRhRUlzVlVGQlZTeERRVUZETEZOQlFWTXNRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhGUVVGRkxFMUJRVTBzUlVGQlJTeEpRVUZKTEVWQlFVVXNUVUZCVFN4RlFVRkZMRWRCUVVjc1EwRkJReXhEUVVGRE8yOUNRVU4wUkN4SlFVRkpMRWRCUVVjc1JVRkJSU3hEUVVGRE8ybENRVU5pTzFsQlEwd3NRMEZCUXl4RFFVRkRMRU5CUVVNN1UwRkRUanRKUVVOTUxFTkJRVU03U1VGVFJDd3JRa0ZCVlN4SFFVRldMRlZCUVdsQ0xFdEJRV0VzUlVGQlJTeFJRVUZuUWl4RlFVRkZMRTFCUVRKQ0xFVkJRVVVzVFVGQk1rSTdVVUZCTVVjc2FVSkJVVU03VVVGUVJ5eEpRVUZKTEZWQlFWVXNSMEZCUnl4TFFVRkxMRU5CUVVNc1IwRkJSeXhEUVVGRExGVkJRVUVzUTBGQlF5eEpRVUZITEU5QlFVRXNTMEZCU1N4RFFVRkRMRXRCUVVzc1EwRkJReXhOUVVGTkxFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVVXNUVUZCVFN4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRV2hETEVOQlFXZERMRU5CUVVNc1EwRkJRenRSUVVOcVJTeEpRVUZKTEV0QlFVc3NSMEZCUnl4VlFVRlZMRU5CUVVNc1ZVRkJWU3hEUVVGRExGVkJRVlVzUTBGQlF5eERRVUZETzFGQlF6bERMRWxCUVVrc1RVRkJUU3hIUVVGSExGVkJRVlVzUTBGQlF5eEhRVUZITEVOQlFVTXNWVUZCVlN4RFFVRkRMRWxCUVVrc1QwRkJUeXhWUVVGVkxFTkJRVU1zV1VGQldTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03VVVGRGFrWXNWVUZCVlN4RFFVRkRMR0ZCUVdFc1EwRkJReXhOUVVGTkxFVkJRVVVzUjBGQlJ5eEZRVUZGTEVkQlFVY3NSVUZCUlN4TFFVRkxMRVZCUVVVc1VVRkJVU3hEUVVGRExFTkJRVU03VVVGRE5VUXNWVUZCVlN4RFFVRkRMR0ZCUVdFc1EwRkJReXhOUVVGTkxFVkJRVVVzUjBGQlJ5eEZRVUZGTEVkQlFVY3NSVUZCUlN4TFFVRkxMRVZCUVVVc1VVRkJVU3hEUVVGRExFTkJRVU03VVVGRE5VUXNWVUZCVlN4RFFVRkRMR05CUVdNc1EwRkJReXhOUVVGTkxFVkJRVVVzVlVGQlZTeERRVUZETEVOQlFVTTdVVUZET1VNc1QwRkJUeXhOUVVGTkxFTkJRVU03U1VGRGJFSXNRMEZCUXp0SlFVbE5MSGxDUVVGakxFZEJRWEpDTEZWQlFYTkNMRTFCUVUwc1JVRkJSU3hWUVVGVk8xRkJRM0JETEUxQlFVMHNRMEZCUXl4UFFVRlBMRU5CUVVNc1ZVRkJReXhSUVVGUkxFVkJRVVVzUTBGQlF6dFpRVU4yUWl4SlFVRkpMRWxCUVVrc1IwRkJSeXhWUVVGVkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdXVUZEZWtJc1NVRkJWU3hKUVVGTExFTkJRVU1zVVVGQlVTeEZRVUZGTzJkQ1FVTjBRaXhSUVVGUkxFTkJRVU1zVDBGQlR5eEZRVUZGTEVOQlFVTTdaMEpCUTI1Q0xGRkJRVkVzUTBGQlF5eFBRVUZQTEVOQlFVTXNWVUZCVlN4UFFVRlBPMjlDUVVNNVFpeFBRVUZQTEVOQlFVTXNUMEZCVHl4RlFVRkZMRU5CUVVNN1owSkJRM1JDTEVOQlFVTXNRMEZCUXl4RFFVRkRPMkZCUTA0N1VVRkRUQ3hEUVVGRExFTkJRVU1zUTBGQlF6dEpRVU5RTEVOQlFVTTdTVUZGVFN3MlFrRkJhMElzUjBGQmVrSXNWVUZCTUVJc1MwRkJZeXhGUVVGRkxFdEJRV003VVVGRGNFUXNTVUZCU1N4TlFVRk5MRWRCUVVjc1NVRkJTU3hEUVVGRExFdEJRVXNzUTBGQlF5eExRVUZMTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFdEJRVXNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUXpORExFdEJRVXNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1MwRkJTeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMUZCUXpkQ0xFbEJRVWtzVFVGQlRTeEhRVUZITEVsQlFVa3NRMEZCUXl4TFFVRkxMRU5CUVVNc1MwRkJTeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4TFFVRkxMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEZRVU16UXl4TFFVRkxMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEhRVUZITEV0QlFVc3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFJRVU0zUWl4SlFVRkpMRWxCUVVrc1IwRkJSeXhOUVVGTkxFZEJRVWNzVFVGQlRTeERRVUZETzFGQlF6TkNMRWxCUVVrc1NVRkJTU3hIUVVGSExFbEJRVWtzUTBGQlF5eEZRVUZGTEVsQlFVa3NTVUZCU1N4SFFVRkhMRU5CUVVNc1NVRkJTU3hEUVVGRExFVkJRVVVzUlVGQlJUdFpRVU51UXl4SlFVRkpMRWRCUVVjc1RVRkJUU3hIUVVGSExFMUJRVTBzUTBGQlF6dFRRVU14UWp0UlFVTkVMRTlCUVU4c1NVRkJTU3hEUVVGRE8wbEJRMmhDTEVOQlFVTTdTVUZIWXl4cFFrRkJUU3hIUVVGeVFpeFZRVUZ6UWl4RFFVRkRMRVZCUVVVc1EwRkJReXhGUVVGRkxFTkJRVU03VVVGRGVrSXNUMEZCVHl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zU1VGQlNTeERRVUZETEVOQlFVTTdTVUZEZUVVc1EwRkJRenRKUVVsakxHMUNRVUZSTEVkQlFYWkNMRlZCUVhkQ0xFdEJRV2xETzFGQlEzSkVMRWxCUVVrc1VVRkJVU3hIUVVGSExFVkJRVVVzUTBGQlF6dFJRVU5zUWl4TFFVRkxMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NTMEZCU3l4RFFVRkRMRTFCUVUwc1JVRkJSU3hEUVVGRExFVkJRVVVzUlVGQlJUdFpRVU51UXl4SlFVRkpMRU5CUVVNc1IwRkJSeXhMUVVGTExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdXVUZEYWtJc1NVRkJTU3hQUVVGUExGRkJRVkVzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRXRCUVVzc1YwRkJWenRuUWtGQlJTeFJRVUZSTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFVkJRVVVzUTBGQlF6dFpRVU0zUkN4UlFVRlJMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1IwRkJSeXhKUVVGSkxFTkJRVU03VTBGRE4wSTdVVUZEUkN4UFFVRlBMRlZCUVVNc1EwRkJReXhGUVVGRkxFTkJRVU1zU1VGQlN5eFBRVUZCTEU5QlFVOHNVVUZCVVN4RFFVRkRMRU5CUVVNc1EwRkJReXhMUVVGTExGZEJRVmNzU1VGQlNTeFJRVUZSTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRWEJFTEVOQlFXOUVMRU5CUVVNN1NVRkRNVVVzUTBGQlF6dEpRVWxOTEhGQ1FVRlZMRWRCUVdwQ0xGVkJRV3RDTEV0QlFVczdVVUZEYmtJc1NVRkJTU3hUUVVGVExFZEJRVWNzUlVGQlJTeERRVUZETzFGQlEyNUNMRXRCUVVzc1NVRkJTU3hEUVVGRExFZEJRVWNzUTBGQlF5eEZRVUZGTEVOQlFVTXNSMEZCUnl4TFFVRkxMRU5CUVVNc1RVRkJUU3hIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETEVWQlFVVXNSVUZCUlR0WlFVTjJReXhMUVVGTExFbEJRVWtzUTBGQlF5eEhRVUZITEVOQlFVTXNSMEZCUnl4RFFVRkRMRVZCUVVVc1EwRkJReXhIUVVGSExFdEJRVXNzUTBGQlF5eE5RVUZOTEVWQlFVVXNRMEZCUXl4RlFVRkZMRVZCUVVVN1owSkJRM1pETEVsQlFVa3NRMEZCUXl4SFFVRkhMRXRCUVVzc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGRFdpeERRVUZETEVkQlFVY3NTMEZCU3l4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVOYUxFZEJRVWNzUjBGQlJ5eEpRVUZKTEhkQ1FVRjNRaXhEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTXNRMEZCUXp0blFrRkROME1zU1VGQlNTeERRVUZETEVWQlFVVXNSVUZCUlN4RlFVRkZMRVZCUVVVc1EwRkJRenRuUWtGRFpDeEpRVUZKTEVkQlFVY3NRMEZCUXl4TlFVRk5MRXRCUVVzc1EwRkJRenR2UWtGRGFFSXNVMEZCVXp0blFrRkRZaXhKUVVGSkxFZEJRVWNzUTBGQlF5eFJRVUZSTEVWQlFVVTdiMEpCUjJRc1EwRkJReXhEUVVGRExFOUJRVThzUlVGQlJTeERRVUZETzI5Q1FVTmFMRU5CUVVNc1EwRkJReXhSUVVGUkxFZEJRVWNzU1VGQlNTeERRVUZETzI5Q1FVTnNRaXhIUVVGSExFZEJRVWNzU1VGQlNTeDNRa0ZCZDBJc1EwRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTTdhVUpCUXpWRE8yZENRVU5FTEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1JVRkJSU3hKUVVGSkxFTkJRVU1zU1VGQlNTeEhRVUZITEVOQlFVTXNSVUZCUlN4SlFVRkpMRU5CUVVNc1EwRkJRenR2UWtGRE5VSXNRMEZCUXl4SFFVRkhMRU5CUVVNc1JVRkJSU3hIUVVGSExFZEJRVWNzUTBGQlF5eE5RVUZOTEVsQlFVa3NRMEZCUXl4RFFVRkRMRTFCUVUwc1NVRkJTU3hIUVVGSExFTkJRVU1zUlVGQlJTeEhRVUZITEVkQlFVY3NRMEZCUXl4TlFVRk5MRWxCUVVrc1EwRkJReXhEUVVGRExFMUJRVTBzUTBGQlF5eEZRVUZGTzI5Q1FVVjBSU3hUUVVGVExFTkJRVU1zU1VGQlNTeERRVUZETEVWQlFVVXNRMEZCUXl4RlFVRkZMRU5CUVVNc1JVRkJSU3hEUVVGRExFVkJRVVVzUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXp0dlFrRkRMMElzVTBGQlV6dHBRa0ZEV2p0blFrRkRSQ3hKUVVGSkxFZEJRVWNzUTBGQlF5eEZRVUZGTEVkQlFVY3NSMEZCUnl4RFFVRkRMRTFCUVUwc1NVRkJTU3hEUVVGRExFTkJRVU1zVFVGQlRTeEpRVUZKTEVkQlFVY3NRMEZCUXl4RlFVRkZMRWRCUVVjc1IwRkJSeXhEUVVGRExFMUJRVTBzU1VGQlNTeERRVUZETEVOQlFVTXNUVUZCVFN4RlFVRkZPMjlDUVUxd1JTeERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRkxFZEJRVWNzUTBGQlF5eERRVUZETEVOQlFVTTdiMEpCUTJ4Q0xFVkJRVVVzUjBGQlJ5eERRVUZETEVOQlFVTXNSMEZCUnl4RFFVRkRMRVZCUVVVc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF6dHZRa0ZEYmtJc1JVRkJSU3hIUVVGSExFTkJRVU1zUTBGQlF5eEhRVUZITEVOQlFVTXNSVUZCUlN4SFFVRkhMRU5CUVVNc1EwRkJReXhEUVVGRE8ybENRVU4wUWp0eFFrRkJUVHR2UWtGRFNDeERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRkxFZEJRVWNzUjBGQlJ5eERRVUZETEUxQlFVMHNSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJRenR2UWtGREwwSXNSVUZCUlN4SFFVRkhMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeEhRVUZITEVkQlFVY3NRMEZCUXl4TlFVRk5MRU5CUVVNc1EwRkJRenR2UWtGRE5VSXNSVUZCUlN4SFFVRkhMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeEhRVUZITEVkQlFVY3NRMEZCUXl4TlFVRk5MRU5CUVVNc1EwRkJRenRwUWtGREwwSTdaMEpCUTBRc1NVRkJTU3hWUVVGVkxFTkJRVU1zVFVGQlRTeERRVUZETEVOQlFVTXNSVUZCUlN4RlFVRkZMRVZCUVVVc1JVRkJSU3hEUVVGRExFVkJRVVU3YjBKQlF6bENMRk5CUVZNc1EwRkJReXhKUVVGSkxFTkJRVU1zUlVGQlJTeERRVUZETEVWQlFVVXNRMEZCUXl4RlFVRkZMRU5CUVVNc1JVRkJSU3hEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETzJsQ1FVTnNRenR4UWtGQlRUdHZRa0ZEU0N4VFFVRlRMRU5CUVVNc1NVRkJTU3hEUVVGRExFVkJRVVVzUTBGQlF5eEZRVUZGTEVOQlFVTXNSVUZCUlN4RFFVRkRMRVZCUVVVc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF6dHBRa0ZEYkVNN1lVRkRTanRUUVVOS08xRkJSVVFzVDBGQlR5eFZRVUZWTEVOQlFVTXNVVUZCVVN4RFFVRkRMRk5CUVZNc1EwRkJReXhEUVVGRE8wbEJRekZETEVOQlFVTTdTVUZMVFN4MVFrRkJXU3hIUVVGdVFpeFZRVUZ2UWl4SlFVRmhPMUZCUXpkQ0xGTkJRVk1zVTBGQlV5eERRVUZETEVOQlFWRTdXVUZEZGtJc1QwRkJZeXhGUVVGRkxFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTXNRMEZCUXl4RlFVRkZMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTTdVVUZEY2tNc1EwRkJRenRSUVVORUxFbEJRVWtzVlVGQlZTeEhRVUZITEZWQlFVTXNRMEZCUXl4RlFVRkZMRU5CUVVNc1JVRkJSU3hEUVVGRExFbEJRVXNzVDBGQlFTeEpRVUZKTEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlJ5eExRVUZMTEVWQlFYWkZMRU5CUVhWRkxFTkJRVU03VVVGRGRFY3NTVUZCU1N4UlFVRlJMRWRCUVVjc1JVRkJSU3hEUVVGRE8xRkJRMnhDTEVsQlFVa3NRMEZCUXl4SFFVRkhMRk5CUVZNc1EwRkJReXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0UlFVTXpRaXhMUVVGTExFbEJRVWtzUTBGQlF5eEhRVUZITEVOQlFVTXNSVUZCUlN4RFFVRkRMRWRCUVVjc1NVRkJTU3hEUVVGRExFMUJRVTBzUlVGQlJTeERRVUZETEVWQlFVVXNSVUZCUlR0WlFVTnNReXhKUVVGSkxFTkJRVU1zUjBGQlJ5eFRRVUZUTEVOQlFVTXNTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eEhRVUZITEVOQlFVTXNSMEZCUnl4SlFVRkpMRU5CUVVNc1RVRkJUU3hIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNTVUZCU1N4RFFVRkRMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNTVUZCU1N4RFFVRkRPMWxCUTNwRkxFbEJRVWtzUTBGQlF5eERRVUZETEVsQlFVa3NRMEZCUXl4VlFVRlZMRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTXNSVUZCUlR0blFrRkROVUlzVVVGQlVTeERRVUZETEVsQlFVa3NRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzJkQ1FVTjBRaXhEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETzJGQlExUTdVMEZEU2p0UlFVTkVMRTlCUVU4c1VVRkJVU3hEUVVGRE8wbEJRM0JDTEVOQlFVTTdTVUZKUkN3d1FrRkJTeXhIUVVGTUxGVkJRVTBzUTBGQlV5eEZRVUZGTEVOQlFWTTdVVUZCTVVJc2FVSkJORVJETzFGQk0wUkhMRWxCUVVrc1RVRkJUU3hIUVVGSExFbEJRVWtzUTBGQlF5eExRVUZMTEVOQlFWTXNRMEZCUXl4RFFVRkRMRVZCUVVVc1RVRkJUU3hIUVVGSExFbEJRVWtzUTBGQlF5eExRVUZMTEVOQlFWTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1VVRkRia1VzU1VGQlNTeERRVUZETEZOQlFWTXNSMEZCUnl4SlFVRkpMRU5CUVVNc1owSkJRV2RDTEVOQlFVTXNUVUZCVFN4RlFVRkZMRTFCUVUwc1EwRkJReXhEUVVGRE8xRkJSWFpFTEVsQlFVa3NZMEZCWXl4SFFVRkhMRVZCUVVVc1EwRkJRenRSUVVONFFpeEpRVUZKTEVOQlFVTXNVMEZCVXl4RFFVRkRMRTlCUVU4c1EwRkJReXhWUVVGQkxFTkJRVU1zU1VGQlNTeFBRVUZCTEdOQlFXTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFZEJRVWNzUTBGQlF5eEZRVUY0UWl4RFFVRjNRaXhEUVVGRExFTkJRVU03VVVGRGRFUXNTVUZCU1N4RFFVRkRMR0ZCUVdFc1IwRkJSeXhKUVVGSkxFTkJRVU1zUzBGQlN5eERRVUZETEUxQlFVMHNRMEZCUXl4VlFVRkJMRU5CUVVNN1dVRkRjRU1zU1VGQlNTeERRVUZETEVkQlFVY3NTMEZCU1N4RFFVRkRMRXRCUVVzc1EwRkJReXhEUVVGRExFTkJRVU1zVFVGQlRTeERRVUZETEVWQlEzaENMRU5CUVVNc1IwRkJSeXhMUVVGSkxFTkJRVU1zUzBGQlN5eERRVUZETEVOQlFVTXNRMEZCUXl4TlFVRk5MRU5CUVVNc1EwRkJRenRaUVVNM1FpeFBRVUZQTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1NVRkJTU3hKUVVGSkxFTkJRVU1zUTBGQlF5eEpRVUZKTEVOQlFVTXNSVUZCUlN4SlFVRkpMR05CUVdNN2JVSkJRM1pETEVOQlFVTXNRMEZCUXl4SlFVRkpMRWxCUVVrc1EwRkJReXhEUVVGRExFbEJRVWtzUTBGQlF5eEZRVUZGTEVsQlFVa3NZMEZCWXl4RFFVRkRMRU5CUVVNN1VVRkRiRVFzUTBGQlF5eERRVUZETEVOQlFVTTdVVUZIU0N4TFFVRkxMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NUVUZCVFN4RFFVRkRMRXRCUVVzc1EwRkJReXhOUVVGTkxFVkJRVVVzUTBGQlF5eEZRVUZGTEVWQlFVVTdXVUZETVVNc1NVRkJTU3hEUVVGRExFZEJRVWNzVFVGQlRTeERRVUZETEV0QlFVc3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU03V1VGRE0wSXNTVUZCU1N4RFFVRkRMRWRCUVVjc1RVRkJUU3hEUVVGRExFdEJRVXNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RlFVRkZMRU5CUVVNN1dVRkRNMElzU1VGQlNTeERRVUZETEdGQlFXRXNRMEZCUXl4SlFVRkpMRU5CUVVNN1owSkJRM0JDTEUxQlFVMHNSVUZCUlN4RFFVRkRPMmRDUVVOVUxFMUJRVTBzUlVGQlJTeERRVUZETzJkQ1FVTlVMRTFCUVUwc1JVRkJSU3hEUVVGRE8yRkJRMW9zUTBGQlF5eERRVUZETzFOQlEwNDdVVUZEUkN4TFFVRkxMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NUVUZCVFN4RFFVRkRMRXRCUVVzc1EwRkJReXhOUVVGTkxFVkJRVVVzUTBGQlF5eEZRVUZGTEVWQlFVVTdXVUZETVVNc1NVRkJTU3hEUVVGRExFZEJRVWNzVFVGQlRTeERRVUZETEV0QlFVc3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU03V1VGRE0wSXNTVUZCU1N4RFFVRkRMRWRCUVVjc1RVRkJUU3hEUVVGRExFdEJRVXNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RlFVRkZMRU5CUVVNN1dVRkRNMElzU1VGQlNTeERRVUZETEdGQlFXRXNRMEZCUXl4SlFVRkpMRU5CUVVNN1owSkJRM0JDTEUxQlFVMHNSVUZCUlN4RFFVRkRPMmRDUVVOVUxFMUJRVTBzUlVGQlJTeERRVUZETzJkQ1FVTlVMRTFCUVUwc1JVRkJSU3hEUVVGRE8yRkJRMW9zUTBGQlF5eERRVUZETzFOQlEwNDdVVUZGUkN4SlFVRkpMRk5CUVZNc1IwRkJSeXhWUVVGQkxFTkJRVU1zU1VGQlJ5eFBRVUZCTEVOQlFVTXNRMEZCUXl4TlFVRk5MRVZCUVZJc1EwRkJVU3hGUVVONFFpeFRRVUZUTEVkQlFVY3NWVUZCUVN4RFFVRkRMRWxCUVVjc1QwRkJRU3hEUVVGRExFTkJRVU1zVFVGQlRTeEZRVUZTTEVOQlFWRXNSVUZEZUVJc1UwRkJVeXhIUVVGSExGVkJRVUVzUTBGQlF5eEpRVUZITEU5QlFVRXNRMEZCUXl4RFFVRkRMRTFCUVUwc1JVRkJVaXhEUVVGUkxFTkJRVU03VVVGRk4wSXNTVUZCU1N4elFrRkJjMElzUjBGQlJ5eEpRVUZKTERCQ1FVRlZMRU5CUVVNc1NVRkJTU3hEUVVGRExFdEJRVXNzUTBGQlF5eE5RVUZOTEVWQlFVVXNTVUZCU1N4RFFVRkRMR0ZCUVdFc1JVRkJSU3hUUVVGVExFVkJRVVVzVTBGQlV5eEZRVUZGTEZOQlFWTXNRMEZCUXl4RFFVRkRPMUZCUTNCSUxFbEJRVWtzVjBGQlZ5eEhRVUZITEZWQlFVTXNRMEZCUXl4RlFVRkZMRU5CUVVNc1JVRkJSU3hEUVVGRE8xbEJRM1JDTEVsQlFVa3NRMEZCUXl4SFFVRkhMRXRCUVVrc1EwRkJReXhMUVVGTExFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4SFFVRkhMRXRCUVVrc1EwRkJReXhMUVVGTExFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4SFFVRkhMRXRCUVVrc1EwRkJReXhMUVVGTExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdXVUZETlVRc1NVRkJTU3hGUVVGRkxFZEJRVWNzU1VGQlNTeERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSVUZCUlN4RlFVRkZMRWRCUVVjc1NVRkJTU3hEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFpRVVYyUkN4SlFVRkpMRU5CUVVNc1EwRkJReXhKUVVGSkxFdEJRVXNzVFVGQlRTeEpRVUZKTEVOQlFVTXNRMEZCUXl4SlFVRkpMRXRCUVVzc1EwRkJReXhEUVVGRExFbEJRVWtzU1VGQlNTeERRVUZETEVOQlFVTXNTVUZCU1N4TFFVRkxMRTFCUVUwc1NVRkJTU3hEUVVGRExFTkJRVU1zU1VGQlNTeExRVUZMTEVOQlFVTXNRMEZCUXl4SlFVRkpPMmRDUVVOb1JpeFBRVUZQTEVOQlFVTXNRMEZCUXp0WlFVTmlMRTlCUVU4c1JVRkJSU3hIUVVGSExFTkJRVU1zU1VGQlNTeEZRVUZGTEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0UlFVTjJReXhEUVVGRExFTkJRVU03VVVGSFJpeEpRVUZKTEZsQlFWa3NSMEZCUnl4elFrRkJjMElzUTBGQlF5dzRRa0ZCT0VJc1EwRkRjRVVzVFVGQlRTeERRVUZETEV0QlFVc3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGRkxFVkJRVVVzVFVGQlRTeERRVUZETEV0QlFVc3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGRkxFVkJRM1JETEZkQlFWY3NRMEZCUXl4RFFVRkRPMUZCUjJwQ0xFbEJRVWtzVlVGQlZTeEhRVUZITEZsQlFWa3NRMEZCUXl4UFFVRlBMRVZCUVVVc1EwRkJReXhIUVVGSExFTkJRVU1zVlVGQlFTeEZRVUZGTEVsQlFVa3NUMEZCUVN4TFFVRkpMRU5CUVVNc1MwRkJTeXhEUVVGRExFVkJRVVVzUTBGQlF5eEZRVUZrTEVOQlFXTXNRMEZCUXl4RFFVRkRPMUZCUTJ4RkxGVkJRVlVzUTBGQlF5eEpRVUZKTEVOQlFVTXNTVUZCU1N4RFFVRkRMRXRCUVVzc1EwRkJReXhOUVVGTkxFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTXNTMEZCU3l4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03VVVGSGFFUXNUMEZCVHl4VlFVRlZMRU5CUVVNc1RVRkJUU3hEUVVGRExGVkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTTdXVUZETVVJc1QwRkJRU3hEUVVGRExFTkJRVU1zUTBGQlF5eEhRVUZITEZWQlFWVXNRMEZCUXl4TlFVRk5MRWRCUVVjc1EwRkJReXhKUVVGSkxGVkJRVlVzUTBGQlF5eERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1NVRkJTU3hMUVVGTExFMUJRVTBzU1VGQlNTeERRVUZETEVOQlFVTXNTVUZCU1N4TFFVRkxMRTFCUVUwN2JVSkJRemxGTEVOQlFVTXNSMEZCUnl4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRExFbEJRVWtzUzBGQlN5eE5RVUZOTEVsQlFVa3NWVUZCVlN4RFFVRkRMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF5eEpRVUZKTEV0QlFVc3NUVUZCVFN4RFFVRkRPMUZCUkhaRkxFTkJRM1ZGTEVOQlFVTXNRMEZCUXp0SlFVTnFSaXhEUVVGRE8wbEJSVTBzZFVKQlFWa3NSMEZCYmtJc1ZVRkJiMElzUzBGQlowSXNSVUZCUlN4WlFVRnZRaXhGUVVGRkxGVkJRV3RDTEVWQlFVVXNWMEZCYlVJN1VVRkRMMFlzU1VGQlNTeE5RVUZOTEVkQlFVYzdXVUZEVkN4VFFVRlRMRVZCUVVVc1NVRkJTU3hIUVVGSExFdEJRVXNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFZEJRVWNzUjBGQlJ5eEhRVUZITEV0QlFVc3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NSMEZCUnp0WlFVTXpSQ3hUUVVGVExFVkJRVVVzUlVGQlJUdFRRVU5vUWl4RFFVRkRPMUZCUTBZc1NVRkJTU3hMUVVGTExFTkJRVU1zVFVGQlRTeEhRVUZITEVOQlFVTXNSVUZCUlR0WlFVTnNRaXhMUVVGTExFbEJRVWtzUTBGQlF5eEhRVUZITEVOQlFVTXNSVUZCUlN4RFFVRkRMRWRCUVVjc1MwRkJTeXhEUVVGRExFMUJRVTBzUlVGQlJTeERRVUZETEVWQlFVVXNSVUZCUlR0blFrRkRia01zU1VGQlNTeEZRVUZGTEVkQlFVY3NTMEZCU3l4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8yZENRVU5zUWl4SlFVRkpMRU5CUVVNc1IwRkJSeXhGUVVGRkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RlFVRkZMRU5CUVVNc1IwRkJSeXhGUVVGRkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMmRDUVVNM1FpeEpRVUZKTEVWQlFVVXNSMEZCUnl4RFFVRkRMRWRCUVVjc1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0blFrRkRja0lzU1VGQlNTeEZRVUZGTEVkQlFVY3NRMEZCUXl4SFFVRkhMRVZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdaMEpCUTNKQ0xFbEJRVWtzUTBGQlF5eEhRVUZITEV0QlFVc3NRMEZCUXl4TlFVRk5MRWRCUVVjc1EwRkJReXhGUVVGRk8yOUNRVU4wUWl4SlFVRkpMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NRMEZCUXl4RlFVRkZPM2RDUVVOc1FpeERRVUZETEVsQlFVa3NSVUZCUlN4SFFVRkhMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NXVUZCV1N4RFFVRkRPM0ZDUVVONlF6dDVRa0ZCVFR0M1FrRkRTQ3hEUVVGRExFbEJRVWtzUlVGQlJTeEhRVUZITEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1JVRkJSU3hEUVVGRExFZEJRVWNzV1VGQldTeERRVUZETzNGQ1FVTjZRenR2UWtGRFJDeE5RVUZOTEVOQlFVTXNVMEZCVXl4SlFVRkpMRWxCUVVrc1IwRkJSeXhEUVVGRExFZEJRVWNzUjBGQlJ5eEhRVUZITEVOQlFVTXNSMEZCUnl4SFFVRkhMRU5CUVVNN2IwSkJRemRETEVsQlFVa3NRMEZCUXl4SFFVRkhMRXRCUVVzc1EwRkJReXhEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETEVOQlFVTTdiMEpCUTNKQ0xFbEJRVWtzUlVGQlJTeEhRVUZITEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRVVVzUlVGQlJTeEhRVUZITEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03YjBKQlF6ZENMRWxCUVVrc1JVRkJSU3hIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN2IwSkJRMmhDTEVsQlFVa3NSVUZCUlN4SFFVRkhMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdiMEpCUTJoQ0xFVkJRVVVzUjBGQlJ5eEZRVUZGTEVkQlFVY3NSVUZCUlN4RFFVRkRPMjlDUVVOaUxFVkJRVVVzUjBGQlJ5eEZRVUZGTEVkQlFVY3NSVUZCUlN4RFFVRkRPMjlDUVVOaUxFbEJRVWtzUzBGQlN5eEhRVUZITEZWQlFWVXNRMEZCUXl4clFrRkJhMElzUTBGQlF5eEZRVUZGTEVWQlFVVXNRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenR2UWtGRk4wUXNTVUZCU1N4RlFVRkZMRVZCUVVVc1JVRkJSU3hEUVVGRE8yOUNRVU5ZTEVsQlFVa3NTVUZCU1N4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRkxFTkJRVU1zUjBGQlJ5eERRVUZETEVWQlFVVTdkMEpCUTJ4Q0xFVkJRVVVzUjBGQlJ5eEZRVUZGTEVkQlFVY3NSVUZCUlN4SFFVRkhMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NXVUZCV1N4RFFVRkRPM2RDUVVNelF5eEZRVUZGTEVkQlFVY3NSVUZCUlN4RFFVRkRPM0ZDUVVOWU8zbENRVUZOTzNkQ1FVTklMRVZCUVVVc1IwRkJSeXhGUVVGRkxFTkJRVU03ZDBKQlExSXNSVUZCUlN4SFFVRkhMRVZCUVVVc1IwRkJSeXhGUVVGRkxFZEJRVWNzU1VGQlNTeERRVUZETEVkQlFVY3NRMEZCUXl4RlFVRkZMRU5CUVVNc1IwRkJSeXhaUVVGWkxFTkJRVU03Y1VKQlF6bERPMjlDUVVORUxFbEJRVWtzUlVGQlJTeEhRVUZITEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1JVRkJSU3hIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETzI5Q1FVTXhRaXhKUVVGSkxFVkJRVVVzUjBGQlJ5eEpRVUZKTEVOQlFVTXNSMEZCUnl4RFFVRkRMRVZCUVVVc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF6dHZRa0ZETVVJc1RVRkJUU3hEUVVGRExGTkJRVk1zU1VGQlNTeEpRVUZKTEVkQlFVY3NSVUZCUlN4SFFVRkhMRWRCUVVjc1IwRkJSeXhGUVVGRkxFZEJRVWNzVDBGQlR5eEhRVUZITEV0QlFVc3NSMEZCUnl4SFFVRkhMRWRCUVVjc1JVRkJSU3hIUVVGSExFZEJRVWNzUjBGQlJ5eEZRVUZGTEVkQlFVY3NSMEZCUnl4RFFVRkRPMmxDUVVNeFJqdHhRa0ZCVFR0dlFrRkRTQ3hKUVVGSkxGRkJRVkVzUjBGQlJ5eERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJRenR2UWtGRGRFSXNTVUZCU1N4WlFVRlpMRVZCUVVVc1dVRkJXU3hEUVVGRE8yOUNRVU12UWl4SlFVRkpMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NRMEZCUXl4RlFVRkZPM2RDUVVOc1FpeERRVUZETEVsQlFVa3NSVUZCUlN4SFFVRkhMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NWMEZCVnl4RFFVRkRPM2RDUVVOeVF5eFpRVUZaTEVkQlFVY3NRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhIUVVGSExGVkJRVlVzUTBGQlF5eERRVUZETzNkQ1FVTnVReXhaUVVGWkxFZEJRVWNzUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4SFFVRkhMRlZCUVZVc1EwRkJReXhEUVVGRE8zRkNRVU4wUXp0NVFrRkJUVHQzUWtGRFNDeERRVUZETEVsQlFVa3NSVUZCUlN4SFFVRkhMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NWMEZCVnl4RFFVRkRPM2RDUVVOeVF5eFpRVUZaTEVkQlFVY3NRMEZCUXl4RFFVRkRMRWRCUVVjc1ZVRkJWU3hGUVVGRkxFTkJRVU1zUTBGQlF5eERRVUZETzNkQ1FVTnVReXhaUVVGWkxFZEJRVWNzUTBGQlF5eERRVUZETEVkQlFVY3NWVUZCVlN4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRE8zRkNRVU4wUXp0dlFrRkRSQ3hOUVVGTkxFTkJRVU1zVTBGQlV5eEpRVUZKTEVsQlFVa3NSMEZCUnl4RFFVRkRMRWRCUVVjc1IwRkJSeXhIUVVGSExFTkJRVU1zUjBGQlJ5eEhRVUZITEVOQlFVTTdiMEpCUXpkRExFbEJRVWtzVjBGQlZ5eEhRVUZITEVOQlFVTXNSVUZCUlR0M1FrRkRha0lzVFVGQlRTeERRVUZETEZOQlFWTXNSMEZCUnl4SlFVRkpMRWRCUVVjc1VVRkJVU3hEUVVGRExFTkJRVU1zUTBGQlF5eEhRVUZITEVkQlFVY3NSMEZCUnl4UlFVRlJMRU5CUVVNc1EwRkJReXhEUVVGRExFZEJRVWNzUzBGQlN5eEhRVUZITEZsQlFWa3NRMEZCUXl4RFFVRkRMRU5CUVVNc1IwRkJSeXhIUVVGSExFZEJRVWNzV1VGQldTeERRVUZETEVOQlFVTXNRMEZCUXpzNFFrRkRla2NzUzBGQlN5eEhRVUZITEZsQlFWa3NRMEZCUXl4RFFVRkRMRU5CUVVNc1IwRkJSeXhIUVVGSExFZEJRVWNzV1VGQldTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPM0ZDUVVOeVJEdHBRa0ZEU2p0aFFVTktPMU5CUTBvN1lVRkJUVHRaUVVOSUxFbEJRVWtzUlVGQlJTeEhRVUZITEV0QlFVc3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRaUVVOc1FpeEpRVUZKTEVOQlFVTXNSMEZCUnl4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTXNSMEZCUnl4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzFsQlF6ZENMRWxCUVVrc1JVRkJSU3hIUVVGSExFTkJRVU1zUjBGQlJ5eEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8xbEJRM0pDTEVsQlFVa3NSVUZCUlN4SFFVRkhMRU5CUVVNc1IwRkJSeXhGUVVGRkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMWxCUTNKQ0xFbEJRVWtzVVVGQlVTeEhRVUZITEVOQlFVTXNRMEZCUXl4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRE8xbEJRM1JDTEVsQlFVa3NXVUZCV1N4RlFVRkZMRmxCUVZrc1EwRkJRenRaUVVNdlFpeEpRVUZKTEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1JVRkJSU3hEUVVGRExFZEJRVWNzUTBGQlF5eEZRVUZGTzJkQ1FVTnNRaXhEUVVGRExFbEJRVWtzUlVGQlJTeEhRVUZITEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1JVRkJSU3hEUVVGRExFZEJRVWNzVjBGQlZ5eERRVUZETzJkQ1FVTnlReXhaUVVGWkxFZEJRVWNzUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4SFFVRkhMRlZCUVZVc1EwRkJReXhEUVVGRE8yZENRVU51UXl4WlFVRlpMRWRCUVVjc1EwRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eEhRVUZITEZWQlFWVXNRMEZCUXl4RFFVRkRPMkZCUTNSRE8ybENRVUZOTzJkQ1FVTklMRU5CUVVNc1NVRkJTU3hGUVVGRkxFZEJRVWNzU1VGQlNTeERRVUZETEVkQlFVY3NRMEZCUXl4RlFVRkZMRU5CUVVNc1IwRkJSeXhYUVVGWExFTkJRVU03WjBKQlEzSkRMRmxCUVZrc1IwRkJSeXhEUVVGRExFTkJRVU1zUjBGQlJ5eFZRVUZWTEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNN1owSkJRMjVETEZsQlFWa3NSMEZCUnl4RFFVRkRMRU5CUVVNc1IwRkJSeXhWUVVGVkxFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTTdZVUZEZEVNN1dVRkRSQ3hOUVVGTkxFTkJRVU1zVTBGQlV5eEpRVUZKTEVsQlFVa3NSMEZCUnl4RFFVRkRMRWRCUVVjc1IwRkJSeXhIUVVGSExFTkJRVU1zUjBGQlJ5eEhRVUZITEVOQlFVTTdXVUZETjBNc1NVRkJTU3hYUVVGWExFZEJRVWNzUTBGQlF5eEZRVUZGTzJkQ1FVTnFRaXhOUVVGTkxFTkJRVU1zVTBGQlV5eEhRVUZITEVsQlFVa3NSMEZCUnl4UlFVRlJMRU5CUVVNc1EwRkJReXhEUVVGRExFZEJRVWNzUjBGQlJ5eEhRVUZITEZGQlFWRXNRMEZCUXl4RFFVRkRMRU5CUVVNc1IwRkJSeXhMUVVGTExFZEJRVWNzV1VGQldTeERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRWRCUVVjc1IwRkJSeXhaUVVGWkxFTkJRVU1zUTBGQlF5eERRVUZETzNOQ1FVTjZSeXhMUVVGTExFZEJRVWNzV1VGQldTeERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRWRCUVVjc1IwRkJSeXhaUVVGWkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdZVUZEY2tRN1UwRkRTanRSUVVORUxFOUJRVThzVFVGQlRTeERRVUZETzBsQlEyeENMRU5CUVVNN1NVRkRUQ3hwUWtGQlF6dEJRVUZFTEVOQlFVTXNRVUY2YkVKRUxFbEJlV3hDUXp0QlFYcHNRbGtzWjBOQlFWVWlmUT09IiwiXCJ1c2Ugc3RyaWN0XCI7XHJcbk9iamVjdC5kZWZpbmVQcm9wZXJ0eShleHBvcnRzLCBcIl9fZXNNb2R1bGVcIiwgeyB2YWx1ZTogdHJ1ZSB9KTtcclxudmFyIHBhY2tpbmdPcHRpb25zID0ge1xyXG4gICAgUEFERElORzogMTAsXHJcbiAgICBHT0xERU5fU0VDVElPTjogKDEgKyBNYXRoLnNxcnQoNSkpIC8gMixcclxuICAgIEZMT0FUX0VQU0lMT046IDAuMDAwMSxcclxuICAgIE1BWF9JTkVSQVRJT05TOiAxMDBcclxufTtcclxuZnVuY3Rpb24gYXBwbHlQYWNraW5nKGdyYXBocywgdywgaCwgbm9kZV9zaXplLCBkZXNpcmVkX3JhdGlvLCBjZW50ZXJHcmFwaCkge1xyXG4gICAgaWYgKGRlc2lyZWRfcmF0aW8gPT09IHZvaWQgMCkgeyBkZXNpcmVkX3JhdGlvID0gMTsgfVxyXG4gICAgaWYgKGNlbnRlckdyYXBoID09PSB2b2lkIDApIHsgY2VudGVyR3JhcGggPSB0cnVlOyB9XHJcbiAgICB2YXIgaW5pdF94ID0gMCwgaW5pdF95ID0gMCwgc3ZnX3dpZHRoID0gdywgc3ZnX2hlaWdodCA9IGgsIGRlc2lyZWRfcmF0aW8gPSB0eXBlb2YgZGVzaXJlZF9yYXRpbyAhPT0gJ3VuZGVmaW5lZCcgPyBkZXNpcmVkX3JhdGlvIDogMSwgbm9kZV9zaXplID0gdHlwZW9mIG5vZGVfc2l6ZSAhPT0gJ3VuZGVmaW5lZCcgPyBub2RlX3NpemUgOiAwLCByZWFsX3dpZHRoID0gMCwgcmVhbF9oZWlnaHQgPSAwLCBtaW5fd2lkdGggPSAwLCBnbG9iYWxfYm90dG9tID0gMCwgbGluZSA9IFtdO1xyXG4gICAgaWYgKGdyYXBocy5sZW5ndGggPT0gMClcclxuICAgICAgICByZXR1cm47XHJcbiAgICBjYWxjdWxhdGVfYmIoZ3JhcGhzKTtcclxuICAgIGFwcGx5KGdyYXBocywgZGVzaXJlZF9yYXRpbyk7XHJcbiAgICBpZiAoY2VudGVyR3JhcGgpIHtcclxuICAgICAgICBwdXRfbm9kZXNfdG9fcmlnaHRfcG9zaXRpb25zKGdyYXBocyk7XHJcbiAgICB9XHJcbiAgICBmdW5jdGlvbiBjYWxjdWxhdGVfYmIoZ3JhcGhzKSB7XHJcbiAgICAgICAgZ3JhcGhzLmZvckVhY2goZnVuY3Rpb24gKGcpIHtcclxuICAgICAgICAgICAgY2FsY3VsYXRlX3NpbmdsZV9iYihnKTtcclxuICAgICAgICB9KTtcclxuICAgICAgICBmdW5jdGlvbiBjYWxjdWxhdGVfc2luZ2xlX2JiKGdyYXBoKSB7XHJcbiAgICAgICAgICAgIHZhciBtaW5feCA9IE51bWJlci5NQVhfVkFMVUUsIG1pbl95ID0gTnVtYmVyLk1BWF9WQUxVRSwgbWF4X3ggPSAwLCBtYXhfeSA9IDA7XHJcbiAgICAgICAgICAgIGdyYXBoLmFycmF5LmZvckVhY2goZnVuY3Rpb24gKHYpIHtcclxuICAgICAgICAgICAgICAgIHZhciB3ID0gdHlwZW9mIHYud2lkdGggIT09ICd1bmRlZmluZWQnID8gdi53aWR0aCA6IG5vZGVfc2l6ZTtcclxuICAgICAgICAgICAgICAgIHZhciBoID0gdHlwZW9mIHYuaGVpZ2h0ICE9PSAndW5kZWZpbmVkJyA/IHYuaGVpZ2h0IDogbm9kZV9zaXplO1xyXG4gICAgICAgICAgICAgICAgdyAvPSAyO1xyXG4gICAgICAgICAgICAgICAgaCAvPSAyO1xyXG4gICAgICAgICAgICAgICAgbWF4X3ggPSBNYXRoLm1heCh2LnggKyB3LCBtYXhfeCk7XHJcbiAgICAgICAgICAgICAgICBtaW5feCA9IE1hdGgubWluKHYueCAtIHcsIG1pbl94KTtcclxuICAgICAgICAgICAgICAgIG1heF95ID0gTWF0aC5tYXgodi55ICsgaCwgbWF4X3kpO1xyXG4gICAgICAgICAgICAgICAgbWluX3kgPSBNYXRoLm1pbih2LnkgLSBoLCBtaW5feSk7XHJcbiAgICAgICAgICAgIH0pO1xyXG4gICAgICAgICAgICBncmFwaC53aWR0aCA9IG1heF94IC0gbWluX3g7XHJcbiAgICAgICAgICAgIGdyYXBoLmhlaWdodCA9IG1heF95IC0gbWluX3k7XHJcbiAgICAgICAgfVxyXG4gICAgfVxyXG4gICAgZnVuY3Rpb24gcHV0X25vZGVzX3RvX3JpZ2h0X3Bvc2l0aW9ucyhncmFwaHMpIHtcclxuICAgICAgICBncmFwaHMuZm9yRWFjaChmdW5jdGlvbiAoZykge1xyXG4gICAgICAgICAgICB2YXIgY2VudGVyID0geyB4OiAwLCB5OiAwIH07XHJcbiAgICAgICAgICAgIGcuYXJyYXkuZm9yRWFjaChmdW5jdGlvbiAobm9kZSkge1xyXG4gICAgICAgICAgICAgICAgY2VudGVyLnggKz0gbm9kZS54O1xyXG4gICAgICAgICAgICAgICAgY2VudGVyLnkgKz0gbm9kZS55O1xyXG4gICAgICAgICAgICB9KTtcclxuICAgICAgICAgICAgY2VudGVyLnggLz0gZy5hcnJheS5sZW5ndGg7XHJcbiAgICAgICAgICAgIGNlbnRlci55IC89IGcuYXJyYXkubGVuZ3RoO1xyXG4gICAgICAgICAgICB2YXIgY29ybmVyID0geyB4OiBjZW50ZXIueCAtIGcud2lkdGggLyAyLCB5OiBjZW50ZXIueSAtIGcuaGVpZ2h0IC8gMiB9O1xyXG4gICAgICAgICAgICB2YXIgb2Zmc2V0ID0geyB4OiBnLnggLSBjb3JuZXIueCArIHN2Z193aWR0aCAvIDIgLSByZWFsX3dpZHRoIC8gMiwgeTogZy55IC0gY29ybmVyLnkgKyBzdmdfaGVpZ2h0IC8gMiAtIHJlYWxfaGVpZ2h0IC8gMiB9O1xyXG4gICAgICAgICAgICBnLmFycmF5LmZvckVhY2goZnVuY3Rpb24gKG5vZGUpIHtcclxuICAgICAgICAgICAgICAgIG5vZGUueCArPSBvZmZzZXQueDtcclxuICAgICAgICAgICAgICAgIG5vZGUueSArPSBvZmZzZXQueTtcclxuICAgICAgICAgICAgfSk7XHJcbiAgICAgICAgfSk7XHJcbiAgICB9XHJcbiAgICBmdW5jdGlvbiBhcHBseShkYXRhLCBkZXNpcmVkX3JhdGlvKSB7XHJcbiAgICAgICAgdmFyIGN1cnJfYmVzdF9mID0gTnVtYmVyLlBPU0lUSVZFX0lORklOSVRZO1xyXG4gICAgICAgIHZhciBjdXJyX2Jlc3QgPSAwO1xyXG4gICAgICAgIGRhdGEuc29ydChmdW5jdGlvbiAoYSwgYikgeyByZXR1cm4gYi5oZWlnaHQgLSBhLmhlaWdodDsgfSk7XHJcbiAgICAgICAgbWluX3dpZHRoID0gZGF0YS5yZWR1Y2UoZnVuY3Rpb24gKGEsIGIpIHtcclxuICAgICAgICAgICAgcmV0dXJuIGEud2lkdGggPCBiLndpZHRoID8gYS53aWR0aCA6IGIud2lkdGg7XHJcbiAgICAgICAgfSk7XHJcbiAgICAgICAgdmFyIGxlZnQgPSB4MSA9IG1pbl93aWR0aDtcclxuICAgICAgICB2YXIgcmlnaHQgPSB4MiA9IGdldF9lbnRpcmVfd2lkdGgoZGF0YSk7XHJcbiAgICAgICAgdmFyIGl0ZXJhdGlvbkNvdW50ZXIgPSAwO1xyXG4gICAgICAgIHZhciBmX3gxID0gTnVtYmVyLk1BWF9WQUxVRTtcclxuICAgICAgICB2YXIgZl94MiA9IE51bWJlci5NQVhfVkFMVUU7XHJcbiAgICAgICAgdmFyIGZsYWcgPSAtMTtcclxuICAgICAgICB2YXIgZHggPSBOdW1iZXIuTUFYX1ZBTFVFO1xyXG4gICAgICAgIHZhciBkZiA9IE51bWJlci5NQVhfVkFMVUU7XHJcbiAgICAgICAgd2hpbGUgKChkeCA+IG1pbl93aWR0aCkgfHwgZGYgPiBwYWNraW5nT3B0aW9ucy5GTE9BVF9FUFNJTE9OKSB7XHJcbiAgICAgICAgICAgIGlmIChmbGFnICE9IDEpIHtcclxuICAgICAgICAgICAgICAgIHZhciB4MSA9IHJpZ2h0IC0gKHJpZ2h0IC0gbGVmdCkgLyBwYWNraW5nT3B0aW9ucy5HT0xERU5fU0VDVElPTjtcclxuICAgICAgICAgICAgICAgIHZhciBmX3gxID0gc3RlcChkYXRhLCB4MSk7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgaWYgKGZsYWcgIT0gMCkge1xyXG4gICAgICAgICAgICAgICAgdmFyIHgyID0gbGVmdCArIChyaWdodCAtIGxlZnQpIC8gcGFja2luZ09wdGlvbnMuR09MREVOX1NFQ1RJT047XHJcbiAgICAgICAgICAgICAgICB2YXIgZl94MiA9IHN0ZXAoZGF0YSwgeDIpO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgICAgIGR4ID0gTWF0aC5hYnMoeDEgLSB4Mik7XHJcbiAgICAgICAgICAgIGRmID0gTWF0aC5hYnMoZl94MSAtIGZfeDIpO1xyXG4gICAgICAgICAgICBpZiAoZl94MSA8IGN1cnJfYmVzdF9mKSB7XHJcbiAgICAgICAgICAgICAgICBjdXJyX2Jlc3RfZiA9IGZfeDE7XHJcbiAgICAgICAgICAgICAgICBjdXJyX2Jlc3QgPSB4MTtcclxuICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICBpZiAoZl94MiA8IGN1cnJfYmVzdF9mKSB7XHJcbiAgICAgICAgICAgICAgICBjdXJyX2Jlc3RfZiA9IGZfeDI7XHJcbiAgICAgICAgICAgICAgICBjdXJyX2Jlc3QgPSB4MjtcclxuICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICBpZiAoZl94MSA+IGZfeDIpIHtcclxuICAgICAgICAgICAgICAgIGxlZnQgPSB4MTtcclxuICAgICAgICAgICAgICAgIHgxID0geDI7XHJcbiAgICAgICAgICAgICAgICBmX3gxID0gZl94MjtcclxuICAgICAgICAgICAgICAgIGZsYWcgPSAxO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgICAgIGVsc2Uge1xyXG4gICAgICAgICAgICAgICAgcmlnaHQgPSB4MjtcclxuICAgICAgICAgICAgICAgIHgyID0geDE7XHJcbiAgICAgICAgICAgICAgICBmX3gyID0gZl94MTtcclxuICAgICAgICAgICAgICAgIGZsYWcgPSAwO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgICAgIGlmIChpdGVyYXRpb25Db3VudGVyKysgPiAxMDApIHtcclxuICAgICAgICAgICAgICAgIGJyZWFrO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgfVxyXG4gICAgICAgIHN0ZXAoZGF0YSwgY3Vycl9iZXN0KTtcclxuICAgIH1cclxuICAgIGZ1bmN0aW9uIHN0ZXAoZGF0YSwgbWF4X3dpZHRoKSB7XHJcbiAgICAgICAgbGluZSA9IFtdO1xyXG4gICAgICAgIHJlYWxfd2lkdGggPSAwO1xyXG4gICAgICAgIHJlYWxfaGVpZ2h0ID0gMDtcclxuICAgICAgICBnbG9iYWxfYm90dG9tID0gaW5pdF95O1xyXG4gICAgICAgIGZvciAodmFyIGkgPSAwOyBpIDwgZGF0YS5sZW5ndGg7IGkrKykge1xyXG4gICAgICAgICAgICB2YXIgbyA9IGRhdGFbaV07XHJcbiAgICAgICAgICAgIHB1dF9yZWN0KG8sIG1heF93aWR0aCk7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIHJldHVybiBNYXRoLmFicyhnZXRfcmVhbF9yYXRpbygpIC0gZGVzaXJlZF9yYXRpbyk7XHJcbiAgICB9XHJcbiAgICBmdW5jdGlvbiBwdXRfcmVjdChyZWN0LCBtYXhfd2lkdGgpIHtcclxuICAgICAgICB2YXIgcGFyZW50ID0gdW5kZWZpbmVkO1xyXG4gICAgICAgIGZvciAodmFyIGkgPSAwOyBpIDwgbGluZS5sZW5ndGg7IGkrKykge1xyXG4gICAgICAgICAgICBpZiAoKGxpbmVbaV0uc3BhY2VfbGVmdCA+PSByZWN0LmhlaWdodCkgJiYgKGxpbmVbaV0ueCArIGxpbmVbaV0ud2lkdGggKyByZWN0LndpZHRoICsgcGFja2luZ09wdGlvbnMuUEFERElORyAtIG1heF93aWR0aCkgPD0gcGFja2luZ09wdGlvbnMuRkxPQVRfRVBTSUxPTikge1xyXG4gICAgICAgICAgICAgICAgcGFyZW50ID0gbGluZVtpXTtcclxuICAgICAgICAgICAgICAgIGJyZWFrO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgfVxyXG4gICAgICAgIGxpbmUucHVzaChyZWN0KTtcclxuICAgICAgICBpZiAocGFyZW50ICE9PSB1bmRlZmluZWQpIHtcclxuICAgICAgICAgICAgcmVjdC54ID0gcGFyZW50LnggKyBwYXJlbnQud2lkdGggKyBwYWNraW5nT3B0aW9ucy5QQURESU5HO1xyXG4gICAgICAgICAgICByZWN0LnkgPSBwYXJlbnQuYm90dG9tO1xyXG4gICAgICAgICAgICByZWN0LnNwYWNlX2xlZnQgPSByZWN0LmhlaWdodDtcclxuICAgICAgICAgICAgcmVjdC5ib3R0b20gPSByZWN0Lnk7XHJcbiAgICAgICAgICAgIHBhcmVudC5zcGFjZV9sZWZ0IC09IHJlY3QuaGVpZ2h0ICsgcGFja2luZ09wdGlvbnMuUEFERElORztcclxuICAgICAgICAgICAgcGFyZW50LmJvdHRvbSArPSByZWN0LmhlaWdodCArIHBhY2tpbmdPcHRpb25zLlBBRERJTkc7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIGVsc2Uge1xyXG4gICAgICAgICAgICByZWN0LnkgPSBnbG9iYWxfYm90dG9tO1xyXG4gICAgICAgICAgICBnbG9iYWxfYm90dG9tICs9IHJlY3QuaGVpZ2h0ICsgcGFja2luZ09wdGlvbnMuUEFERElORztcclxuICAgICAgICAgICAgcmVjdC54ID0gaW5pdF94O1xyXG4gICAgICAgICAgICByZWN0LmJvdHRvbSA9IHJlY3QueTtcclxuICAgICAgICAgICAgcmVjdC5zcGFjZV9sZWZ0ID0gcmVjdC5oZWlnaHQ7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIGlmIChyZWN0LnkgKyByZWN0LmhlaWdodCAtIHJlYWxfaGVpZ2h0ID4gLXBhY2tpbmdPcHRpb25zLkZMT0FUX0VQU0lMT04pXHJcbiAgICAgICAgICAgIHJlYWxfaGVpZ2h0ID0gcmVjdC55ICsgcmVjdC5oZWlnaHQgLSBpbml0X3k7XHJcbiAgICAgICAgaWYgKHJlY3QueCArIHJlY3Qud2lkdGggLSByZWFsX3dpZHRoID4gLXBhY2tpbmdPcHRpb25zLkZMT0FUX0VQU0lMT04pXHJcbiAgICAgICAgICAgIHJlYWxfd2lkdGggPSByZWN0LnggKyByZWN0LndpZHRoIC0gaW5pdF94O1xyXG4gICAgfVxyXG4gICAgO1xyXG4gICAgZnVuY3Rpb24gZ2V0X2VudGlyZV93aWR0aChkYXRhKSB7XHJcbiAgICAgICAgdmFyIHdpZHRoID0gMDtcclxuICAgICAgICBkYXRhLmZvckVhY2goZnVuY3Rpb24gKGQpIHsgcmV0dXJuIHdpZHRoICs9IGQud2lkdGggKyBwYWNraW5nT3B0aW9ucy5QQURESU5HOyB9KTtcclxuICAgICAgICByZXR1cm4gd2lkdGg7XHJcbiAgICB9XHJcbiAgICBmdW5jdGlvbiBnZXRfcmVhbF9yYXRpbygpIHtcclxuICAgICAgICByZXR1cm4gKHJlYWxfd2lkdGggLyByZWFsX2hlaWdodCk7XHJcbiAgICB9XHJcbn1cclxuZXhwb3J0cy5hcHBseVBhY2tpbmcgPSBhcHBseVBhY2tpbmc7XHJcbmZ1bmN0aW9uIHNlcGFyYXRlR3JhcGhzKG5vZGVzLCBsaW5rcykge1xyXG4gICAgdmFyIG1hcmtzID0ge307XHJcbiAgICB2YXIgd2F5cyA9IHt9O1xyXG4gICAgdmFyIGdyYXBocyA9IFtdO1xyXG4gICAgdmFyIGNsdXN0ZXJzID0gMDtcclxuICAgIGZvciAodmFyIGkgPSAwOyBpIDwgbGlua3MubGVuZ3RoOyBpKyspIHtcclxuICAgICAgICB2YXIgbGluayA9IGxpbmtzW2ldO1xyXG4gICAgICAgIHZhciBuMSA9IGxpbmsuc291cmNlO1xyXG4gICAgICAgIHZhciBuMiA9IGxpbmsudGFyZ2V0O1xyXG4gICAgICAgIGlmICh3YXlzW24xLmluZGV4XSlcclxuICAgICAgICAgICAgd2F5c1tuMS5pbmRleF0ucHVzaChuMik7XHJcbiAgICAgICAgZWxzZVxyXG4gICAgICAgICAgICB3YXlzW24xLmluZGV4XSA9IFtuMl07XHJcbiAgICAgICAgaWYgKHdheXNbbjIuaW5kZXhdKVxyXG4gICAgICAgICAgICB3YXlzW24yLmluZGV4XS5wdXNoKG4xKTtcclxuICAgICAgICBlbHNlXHJcbiAgICAgICAgICAgIHdheXNbbjIuaW5kZXhdID0gW24xXTtcclxuICAgIH1cclxuICAgIGZvciAodmFyIGkgPSAwOyBpIDwgbm9kZXMubGVuZ3RoOyBpKyspIHtcclxuICAgICAgICB2YXIgbm9kZSA9IG5vZGVzW2ldO1xyXG4gICAgICAgIGlmIChtYXJrc1tub2RlLmluZGV4XSlcclxuICAgICAgICAgICAgY29udGludWU7XHJcbiAgICAgICAgZXhwbG9yZV9ub2RlKG5vZGUsIHRydWUpO1xyXG4gICAgfVxyXG4gICAgZnVuY3Rpb24gZXhwbG9yZV9ub2RlKG4sIGlzX25ldykge1xyXG4gICAgICAgIGlmIChtYXJrc1tuLmluZGV4XSAhPT0gdW5kZWZpbmVkKVxyXG4gICAgICAgICAgICByZXR1cm47XHJcbiAgICAgICAgaWYgKGlzX25ldykge1xyXG4gICAgICAgICAgICBjbHVzdGVycysrO1xyXG4gICAgICAgICAgICBncmFwaHMucHVzaCh7IGFycmF5OiBbXSB9KTtcclxuICAgICAgICB9XHJcbiAgICAgICAgbWFya3Nbbi5pbmRleF0gPSBjbHVzdGVycztcclxuICAgICAgICBncmFwaHNbY2x1c3RlcnMgLSAxXS5hcnJheS5wdXNoKG4pO1xyXG4gICAgICAgIHZhciBhZGphY2VudCA9IHdheXNbbi5pbmRleF07XHJcbiAgICAgICAgaWYgKCFhZGphY2VudClcclxuICAgICAgICAgICAgcmV0dXJuO1xyXG4gICAgICAgIGZvciAodmFyIGogPSAwOyBqIDwgYWRqYWNlbnQubGVuZ3RoOyBqKyspIHtcclxuICAgICAgICAgICAgZXhwbG9yZV9ub2RlKGFkamFjZW50W2pdLCBmYWxzZSk7XHJcbiAgICAgICAgfVxyXG4gICAgfVxyXG4gICAgcmV0dXJuIGdyYXBocztcclxufVxyXG5leHBvcnRzLnNlcGFyYXRlR3JhcGhzID0gc2VwYXJhdGVHcmFwaHM7XHJcbi8vIyBzb3VyY2VNYXBwaW5nVVJMPWRhdGE6YXBwbGljYXRpb24vanNvbjtiYXNlNjQsZXlKMlpYSnphVzl1SWpvekxDSm1hV3hsSWpvaWFHRnVaR3hsWkdselkyOXVibVZqZEdWa0xtcHpJaXdpYzI5MWNtTmxVbTl2ZENJNklpSXNJbk52ZFhKalpYTWlPbHNpTGk0dkxpNHZWMlZpUTI5c1lTOXpjbU12YUdGdVpHeGxaR2x6WTI5dWJtVmpkR1ZrTG5SeklsMHNJbTVoYldWeklqcGJYU3dpYldGd2NHbHVaM01pT2lJN08wRkJRVWtzU1VGQlNTeGpRVUZqTEVkQlFVYzdTVUZEYWtJc1QwRkJUeXhGUVVGRkxFVkJRVVU3U1VGRFdDeGpRVUZqTEVWQlFVVXNRMEZCUXl4RFFVRkRMRWRCUVVjc1NVRkJTU3hEUVVGRExFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRU5CUVVNN1NVRkRkRU1zWVVGQllTeEZRVUZGTEUxQlFVMDdTVUZEY2tJc1kwRkJZeXhGUVVGRkxFZEJRVWM3UTBGRGRFSXNRMEZCUXp0QlFVZEdMRk5CUVdkQ0xGbEJRVmtzUTBGQlF5eE5RVUZwUWl4RlFVRkZMRU5CUVVNc1JVRkJSU3hEUVVGRExFVkJRVVVzVTBGQlV5eEZRVUZGTEdGQlFXbENMRVZCUVVVc1YwRkJhMEk3U1VGQmNrTXNPRUpCUVVFc1JVRkJRU3hwUWtGQmFVSTdTVUZCUlN3MFFrRkJRU3hGUVVGQkxHdENRVUZyUWp0SlFVVnNSeXhKUVVGSkxFMUJRVTBzUjBGQlJ5eERRVUZETEVWQlExWXNUVUZCVFN4SFFVRkhMRU5CUVVNc1JVRkZWaXhUUVVGVExFZEJRVWNzUTBGQlF5eEZRVU5pTEZWQlFWVXNSMEZCUnl4RFFVRkRMRVZCUldRc1lVRkJZU3hIUVVGSExFOUJRVThzWVVGQllTeExRVUZMTEZkQlFWY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1lVRkJZU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVWQlEzaEZMRk5CUVZNc1IwRkJSeXhQUVVGUExGTkJRVk1zUzBGQlN5eFhRVUZYTEVOQlFVTXNRMEZCUXl4RFFVRkRMRk5CUVZNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEZRVVUxUkN4VlFVRlZMRWRCUVVjc1EwRkJReXhGUVVOa0xGZEJRVmNzUjBGQlJ5eERRVUZETEVWQlEyWXNVMEZCVXl4SFFVRkhMRU5CUVVNc1JVRkZZaXhoUVVGaExFZEJRVWNzUTBGQlF5eEZRVU5xUWl4SlFVRkpMRWRCUVVjc1JVRkJSU3hEUVVGRE8wbEJSV1FzU1VGQlNTeE5RVUZOTEVOQlFVTXNUVUZCVFN4SlFVRkpMRU5CUVVNN1VVRkRiRUlzVDBGQlR6dEpRVlZZTEZsQlFWa3NRMEZCUXl4TlFVRk5MRU5CUVVNc1EwRkJRenRKUVVOeVFpeExRVUZMTEVOQlFVTXNUVUZCVFN4RlFVRkZMR0ZCUVdFc1EwRkJReXhEUVVGRE8wbEJRemRDTEVsQlFVY3NWMEZCVnl4RlFVRkZPMUZCUTFvc05FSkJRVFJDTEVOQlFVTXNUVUZCVFN4RFFVRkRMRU5CUVVNN1MwRkRlRU03U1VGSFJDeFRRVUZUTEZsQlFWa3NRMEZCUXl4TlFVRk5PMUZCUlhoQ0xFMUJRVTBzUTBGQlF5eFBRVUZQTEVOQlFVTXNWVUZCVlN4RFFVRkRPMWxCUTNSQ0xHMUNRVUZ0UWl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGQk8xRkJRekZDTEVOQlFVTXNRMEZCUXl4RFFVRkRPMUZCUlVnc1UwRkJVeXh0UWtGQmJVSXNRMEZCUXl4TFFVRkxPMWxCUXpsQ0xFbEJRVWtzUzBGQlN5eEhRVUZITEUxQlFVMHNRMEZCUXl4VFFVRlRMRVZCUVVVc1MwRkJTeXhIUVVGSExFMUJRVTBzUTBGQlF5eFRRVUZUTEVWQlEyeEVMRXRCUVVzc1IwRkJSeXhEUVVGRExFVkJRVVVzUzBGQlN5eEhRVUZITEVOQlFVTXNRMEZCUXp0WlFVVjZRaXhMUVVGTExFTkJRVU1zUzBGQlN5eERRVUZETEU5QlFVOHNRMEZCUXl4VlFVRlZMRU5CUVVNN1owSkJRek5DTEVsQlFVa3NRMEZCUXl4SFFVRkhMRTlCUVU4c1EwRkJReXhEUVVGRExFdEJRVXNzUzBGQlN5eFhRVUZYTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhMUVVGTExFTkJRVU1zUTBGQlF5eERRVUZETEZOQlFWTXNRMEZCUXp0blFrRkROMFFzU1VGQlNTeERRVUZETEVkQlFVY3NUMEZCVHl4RFFVRkRMRU5CUVVNc1RVRkJUU3hMUVVGTExGZEJRVmNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRTFCUVUwc1EwRkJReXhEUVVGRExFTkJRVU1zVTBGQlV5eERRVUZETzJkQ1FVTXZSQ3hEUVVGRExFbEJRVWtzUTBGQlF5eERRVUZETzJkQ1FVTlFMRU5CUVVNc1NVRkJTU3hEUVVGRExFTkJRVU03WjBKQlExQXNTMEZCU3l4SFFVRkhMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4RFFVRkRMRVZCUVVVc1MwRkJTeXhEUVVGRExFTkJRVU03WjBKQlEycERMRXRCUVVzc1IwRkJSeXhKUVVGSkxFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRkxFdEJRVXNzUTBGQlF5eERRVUZETzJkQ1FVTnFReXhMUVVGTExFZEJRVWNzU1VGQlNTeERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeExRVUZMTEVOQlFVTXNRMEZCUXp0blFrRkRha01zUzBGQlN5eEhRVUZITEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlJ5eERRVUZETEVWQlFVVXNTMEZCU3l4RFFVRkRMRU5CUVVNN1dVRkRja01zUTBGQlF5eERRVUZETEVOQlFVTTdXVUZGU0N4TFFVRkxMRU5CUVVNc1MwRkJTeXhIUVVGSExFdEJRVXNzUjBGQlJ5eExRVUZMTEVOQlFVTTdXVUZETlVJc1MwRkJTeXhEUVVGRExFMUJRVTBzUjBGQlJ5eExRVUZMTEVkQlFVY3NTMEZCU3l4RFFVRkRPMUZCUTJwRExFTkJRVU03U1VGRFRDeERRVUZETzBsQmRVTkVMRk5CUVZNc05FSkJRVFJDTEVOQlFVTXNUVUZCVFR0UlFVTjRReXhOUVVGTkxFTkJRVU1zVDBGQlR5eERRVUZETEZWQlFWVXNRMEZCUXp0WlFVVjBRaXhKUVVGSkxFMUJRVTBzUjBGQlJ5eEZRVUZGTEVOQlFVTXNSVUZCUlN4RFFVRkRMRVZCUVVVc1EwRkJReXhGUVVGRkxFTkJRVU1zUlVGQlJTeERRVUZETzFsQlJUVkNMRU5CUVVNc1EwRkJReXhMUVVGTExFTkJRVU1zVDBGQlR5eERRVUZETEZWQlFWVXNTVUZCU1R0blFrRkRNVUlzVFVGQlRTeERRVUZETEVOQlFVTXNTVUZCU1N4SlFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRE8yZENRVU51UWl4TlFVRk5MRU5CUVVNc1EwRkJReXhKUVVGSkxFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTTdXVUZEZGtJc1EwRkJReXhEUVVGRExFTkJRVU03V1VGRlNDeE5RVUZOTEVOQlFVTXNRMEZCUXl4SlFVRkpMRU5CUVVNc1EwRkJReXhMUVVGTExFTkJRVU1zVFVGQlRTeERRVUZETzFsQlF6TkNMRTFCUVUwc1EwRkJReXhEUVVGRExFbEJRVWtzUTBGQlF5eERRVUZETEV0QlFVc3NRMEZCUXl4TlFVRk5MRU5CUVVNN1dVRkhNMElzU1VGQlNTeE5RVUZOTEVkQlFVY3NSVUZCUlN4RFFVRkRMRVZCUVVVc1RVRkJUU3hEUVVGRExFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNTMEZCU3l4SFFVRkhMRU5CUVVNc1JVRkJSU3hEUVVGRExFVkJRVVVzVFVGQlRTeERRVUZETEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1RVRkJUU3hIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETzFsQlEzWkZMRWxCUVVrc1RVRkJUU3hIUVVGSExFVkJRVVVzUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1RVRkJUU3hEUVVGRExFTkJRVU1zUjBGQlJ5eFRRVUZUTEVkQlFVY3NRMEZCUXl4SFFVRkhMRlZCUVZVc1IwRkJSeXhEUVVGRExFVkJRVVVzUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1RVRkJUU3hEUVVGRExFTkJRVU1zUjBGQlJ5eFZRVUZWTEVkQlFVY3NRMEZCUXl4SFFVRkhMRmRCUVZjc1IwRkJSeXhEUVVGRExFVkJRVU1zUTBGQlF6dFpRVWQ2U0N4RFFVRkRMRU5CUVVNc1MwRkJTeXhEUVVGRExFOUJRVThzUTBGQlF5eFZRVUZWTEVsQlFVazdaMEpCUXpGQ0xFbEJRVWtzUTBGQlF5eERRVUZETEVsQlFVa3NUVUZCVFN4RFFVRkRMRU5CUVVNc1EwRkJRenRuUWtGRGJrSXNTVUZCU1N4RFFVRkRMRU5CUVVNc1NVRkJTU3hOUVVGTkxFTkJRVU1zUTBGQlF5eERRVUZETzFsQlEzWkNMRU5CUVVNc1EwRkJReXhEUVVGRE8xRkJRMUFzUTBGQlF5eERRVUZETEVOQlFVTTdTVUZEVUN4RFFVRkRPMGxCU1VRc1UwRkJVeXhMUVVGTExFTkJRVU1zU1VGQlNTeEZRVUZGTEdGQlFXRTdVVUZET1VJc1NVRkJTU3hYUVVGWExFZEJRVWNzVFVGQlRTeERRVUZETEdsQ1FVRnBRaXhEUVVGRE8xRkJRek5ETEVsQlFVa3NVMEZCVXl4SFFVRkhMRU5CUVVNc1EwRkJRenRSUVVOc1FpeEpRVUZKTEVOQlFVTXNTVUZCU1N4RFFVRkRMRlZCUVZVc1EwRkJReXhGUVVGRkxFTkJRVU1zU1VGQlNTeFBRVUZQTEVOQlFVTXNRMEZCUXl4TlFVRk5MRWRCUVVjc1EwRkJReXhEUVVGRExFMUJRVTBzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMUZCUlRORUxGTkJRVk1zUjBGQlJ5eEpRVUZKTEVOQlFVTXNUVUZCVFN4RFFVRkRMRlZCUVZVc1EwRkJReXhGUVVGRkxFTkJRVU03V1VGRGJFTXNUMEZCVHl4RFFVRkRMRU5CUVVNc1MwRkJTeXhIUVVGSExFTkJRVU1zUTBGQlF5eExRVUZMTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhMUVVGTExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4TFFVRkxMRU5CUVVNN1VVRkRha1FzUTBGQlF5eERRVUZETEVOQlFVTTdVVUZGU0N4SlFVRkpMRWxCUVVrc1IwRkJSeXhGUVVGRkxFZEJRVWNzVTBGQlV5eERRVUZETzFGQlF6RkNMRWxCUVVrc1MwRkJTeXhIUVVGSExFVkJRVVVzUjBGQlJ5eG5Ra0ZCWjBJc1EwRkJReXhKUVVGSkxFTkJRVU1zUTBGQlF6dFJRVU40UXl4SlFVRkpMR2RDUVVGblFpeEhRVUZITEVOQlFVTXNRMEZCUXp0UlFVVjZRaXhKUVVGSkxFbEJRVWtzUjBGQlJ5eE5RVUZOTEVOQlFVTXNVMEZCVXl4RFFVRkRPMUZCUXpWQ0xFbEJRVWtzU1VGQlNTeEhRVUZITEUxQlFVMHNRMEZCUXl4VFFVRlRMRU5CUVVNN1VVRkROVUlzU1VGQlNTeEpRVUZKTEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNN1VVRkhaQ3hKUVVGSkxFVkJRVVVzUjBGQlJ5eE5RVUZOTEVOQlFVTXNVMEZCVXl4RFFVRkRPMUZCUXpGQ0xFbEJRVWtzUlVGQlJTeEhRVUZITEUxQlFVMHNRMEZCUXl4VFFVRlRMRU5CUVVNN1VVRkZNVUlzVDBGQlR5eERRVUZETEVWQlFVVXNSMEZCUnl4VFFVRlRMRU5CUVVNc1NVRkJTU3hGUVVGRkxFZEJRVWNzWTBGQll5eERRVUZETEdGQlFXRXNSVUZCUlR0WlFVVXhSQ3hKUVVGSkxFbEJRVWtzU1VGQlNTeERRVUZETEVWQlFVVTdaMEpCUTFnc1NVRkJTU3hGUVVGRkxFZEJRVWNzUzBGQlN5eEhRVUZITEVOQlFVTXNTMEZCU3l4SFFVRkhMRWxCUVVrc1EwRkJReXhIUVVGSExHTkJRV01zUTBGQlF5eGpRVUZqTEVOQlFVTTdaMEpCUTJoRkxFbEJRVWtzU1VGQlNTeEhRVUZITEVsQlFVa3NRMEZCUXl4SlFVRkpMRVZCUVVVc1JVRkJSU3hEUVVGRExFTkJRVU03WVVGRE4wSTdXVUZEUkN4SlFVRkpMRWxCUVVrc1NVRkJTU3hEUVVGRExFVkJRVVU3WjBKQlExZ3NTVUZCU1N4RlFVRkZMRWRCUVVjc1NVRkJTU3hIUVVGSExFTkJRVU1zUzBGQlN5eEhRVUZITEVsQlFVa3NRMEZCUXl4SFFVRkhMR05CUVdNc1EwRkJReXhqUVVGakxFTkJRVU03WjBKQlF5OUVMRWxCUVVrc1NVRkJTU3hIUVVGSExFbEJRVWtzUTBGQlF5eEpRVUZKTEVWQlFVVXNSVUZCUlN4RFFVRkRMRU5CUVVNN1lVRkROMEk3V1VGRlJDeEZRVUZGTEVkQlFVY3NTVUZCU1N4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRkxFZEJRVWNzUlVGQlJTeERRVUZETEVOQlFVTTdXVUZEZGtJc1JVRkJSU3hIUVVGSExFbEJRVWtzUTBGQlF5eEhRVUZITEVOQlFVTXNTVUZCU1N4SFFVRkhMRWxCUVVrc1EwRkJReXhEUVVGRE8xbEJSVE5DTEVsQlFVa3NTVUZCU1N4SFFVRkhMRmRCUVZjc1JVRkJSVHRuUWtGRGNFSXNWMEZCVnl4SFFVRkhMRWxCUVVrc1EwRkJRenRuUWtGRGJrSXNVMEZCVXl4SFFVRkhMRVZCUVVVc1EwRkJRenRoUVVOc1FqdFpRVVZFTEVsQlFVa3NTVUZCU1N4SFFVRkhMRmRCUVZjc1JVRkJSVHRuUWtGRGNFSXNWMEZCVnl4SFFVRkhMRWxCUVVrc1EwRkJRenRuUWtGRGJrSXNVMEZCVXl4SFFVRkhMRVZCUVVVc1EwRkJRenRoUVVOc1FqdFpRVVZFTEVsQlFVa3NTVUZCU1N4SFFVRkhMRWxCUVVrc1JVRkJSVHRuUWtGRFlpeEpRVUZKTEVkQlFVY3NSVUZCUlN4RFFVRkRPMmRDUVVOV0xFVkJRVVVzUjBGQlJ5eEZRVUZGTEVOQlFVTTdaMEpCUTFJc1NVRkJTU3hIUVVGSExFbEJRVWtzUTBGQlF6dG5Ra0ZEV2l4SlFVRkpMRWRCUVVjc1EwRkJReXhEUVVGRE8yRkJRMW83YVVKQlFVMDdaMEpCUTBnc1MwRkJTeXhIUVVGSExFVkJRVVVzUTBGQlF6dG5Ra0ZEV0N4RlFVRkZMRWRCUVVjc1JVRkJSU3hEUVVGRE8yZENRVU5TTEVsQlFVa3NSMEZCUnl4SlFVRkpMRU5CUVVNN1owSkJRMW9zU1VGQlNTeEhRVUZITEVOQlFVTXNRMEZCUXp0aFFVTmFPMWxCUlVRc1NVRkJTU3huUWtGQlowSXNSVUZCUlN4SFFVRkhMRWRCUVVjc1JVRkJSVHRuUWtGRE1VSXNUVUZCVFR0aFFVTlVPMU5CUTBvN1VVRkZSQ3hKUVVGSkxFTkJRVU1zU1VGQlNTeEZRVUZGTEZOQlFWTXNRMEZCUXl4RFFVRkRPMGxCUXpGQ0xFTkJRVU03U1VGSlJDeFRRVUZUTEVsQlFVa3NRMEZCUXl4SlFVRkpMRVZCUVVVc1UwRkJVenRSUVVONlFpeEpRVUZKTEVkQlFVY3NSVUZCUlN4RFFVRkRPMUZCUTFZc1ZVRkJWU3hIUVVGSExFTkJRVU1zUTBGQlF6dFJRVU5tTEZkQlFWY3NSMEZCUnl4RFFVRkRMRU5CUVVNN1VVRkRhRUlzWVVGQllTeEhRVUZITEUxQlFVMHNRMEZCUXp0UlFVVjJRaXhMUVVGTExFbEJRVWtzUTBGQlF5eEhRVUZITEVOQlFVTXNSVUZCUlN4RFFVRkRMRWRCUVVjc1NVRkJTU3hEUVVGRExFMUJRVTBzUlVGQlJTeERRVUZETEVWQlFVVXNSVUZCUlR0WlFVTnNReXhKUVVGSkxFTkJRVU1zUjBGQlJ5eEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1dVRkRhRUlzVVVGQlVTeERRVUZETEVOQlFVTXNSVUZCUlN4VFFVRlRMRU5CUVVNc1EwRkJRenRUUVVNeFFqdFJRVVZFTEU5QlFVOHNTVUZCU1N4RFFVRkRMRWRCUVVjc1EwRkJReXhqUVVGakxFVkJRVVVzUjBGQlJ5eGhRVUZoTEVOQlFVTXNRMEZCUXp0SlFVTjBSQ3hEUVVGRE8wbEJSMFFzVTBGQlV5eFJRVUZSTEVOQlFVTXNTVUZCU1N4RlFVRkZMRk5CUVZNN1VVRkhOMElzU1VGQlNTeE5RVUZOTEVkQlFVY3NVMEZCVXl4RFFVRkRPMUZCUlhaQ0xFdEJRVXNzU1VGQlNTeERRVUZETEVkQlFVY3NRMEZCUXl4RlFVRkZMRU5CUVVNc1IwRkJSeXhKUVVGSkxFTkJRVU1zVFVGQlRTeEZRVUZGTEVOQlFVTXNSVUZCUlN4RlFVRkZPMWxCUTJ4RExFbEJRVWtzUTBGQlF5eEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1ZVRkJWU3hKUVVGSkxFbEJRVWtzUTBGQlF5eE5RVUZOTEVOQlFVTXNTVUZCU1N4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFdEJRVXNzUjBGQlJ5eEpRVUZKTEVOQlFVTXNTMEZCU3l4SFFVRkhMR05CUVdNc1EwRkJReXhQUVVGUExFZEJRVWNzVTBGQlV5eERRVUZETEVsQlFVa3NZMEZCWXl4RFFVRkRMR0ZCUVdFc1JVRkJSVHRuUWtGRGRFb3NUVUZCVFN4SFFVRkhMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dG5Ra0ZEYWtJc1RVRkJUVHRoUVVOVU8xTkJRMG83VVVGRlJDeEpRVUZKTEVOQlFVTXNTVUZCU1N4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRE8xRkJSV2hDTEVsQlFVa3NUVUZCVFN4TFFVRkxMRk5CUVZNc1JVRkJSVHRaUVVOMFFpeEpRVUZKTEVOQlFVTXNRMEZCUXl4SFFVRkhMRTFCUVUwc1EwRkJReXhEUVVGRExFZEJRVWNzVFVGQlRTeERRVUZETEV0QlFVc3NSMEZCUnl4alFVRmpMRU5CUVVNc1QwRkJUeXhEUVVGRE8xbEJRekZFTEVsQlFVa3NRMEZCUXl4RFFVRkRMRWRCUVVjc1RVRkJUU3hEUVVGRExFMUJRVTBzUTBGQlF6dFpRVU4yUWl4SlFVRkpMRU5CUVVNc1ZVRkJWU3hIUVVGSExFbEJRVWtzUTBGQlF5eE5RVUZOTEVOQlFVTTdXVUZET1VJc1NVRkJTU3hEUVVGRExFMUJRVTBzUjBGQlJ5eEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRPMWxCUTNKQ0xFMUJRVTBzUTBGQlF5eFZRVUZWTEVsQlFVa3NTVUZCU1N4RFFVRkRMRTFCUVUwc1IwRkJSeXhqUVVGakxFTkJRVU1zVDBGQlR5eERRVUZETzFsQlF6RkVMRTFCUVUwc1EwRkJReXhOUVVGTkxFbEJRVWtzU1VGQlNTeERRVUZETEUxQlFVMHNSMEZCUnl4alFVRmpMRU5CUVVNc1QwRkJUeXhEUVVGRE8xTkJRM3BFTzJGQlFVMDdXVUZEU0N4SlFVRkpMRU5CUVVNc1EwRkJReXhIUVVGSExHRkJRV0VzUTBGQlF6dFpRVU4yUWl4aFFVRmhMRWxCUVVrc1NVRkJTU3hEUVVGRExFMUJRVTBzUjBGQlJ5eGpRVUZqTEVOQlFVTXNUMEZCVHl4RFFVRkRPMWxCUTNSRUxFbEJRVWtzUTBGQlF5eERRVUZETEVkQlFVY3NUVUZCVFN4RFFVRkRPMWxCUTJoQ0xFbEJRVWtzUTBGQlF5eE5RVUZOTEVkQlFVY3NTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJRenRaUVVOeVFpeEpRVUZKTEVOQlFVTXNWVUZCVlN4SFFVRkhMRWxCUVVrc1EwRkJReXhOUVVGTkxFTkJRVU03VTBGRGFrTTdVVUZGUkN4SlFVRkpMRWxCUVVrc1EwRkJReXhEUVVGRExFZEJRVWNzU1VGQlNTeERRVUZETEUxQlFVMHNSMEZCUnl4WFFVRlhMRWRCUVVjc1EwRkJReXhqUVVGakxFTkJRVU1zWVVGQllUdFpRVUZGTEZkQlFWY3NSMEZCUnl4SlFVRkpMRU5CUVVNc1EwRkJReXhIUVVGSExFbEJRVWtzUTBGQlF5eE5RVUZOTEVkQlFVY3NUVUZCVFN4RFFVRkRPMUZCUTNCSUxFbEJRVWtzU1VGQlNTeERRVUZETEVOQlFVTXNSMEZCUnl4SlFVRkpMRU5CUVVNc1MwRkJTeXhIUVVGSExGVkJRVlVzUjBGQlJ5eERRVUZETEdOQlFXTXNRMEZCUXl4aFFVRmhPMWxCUVVVc1ZVRkJWU3hIUVVGSExFbEJRVWtzUTBGQlF5eERRVUZETEVkQlFVY3NTVUZCU1N4RFFVRkRMRXRCUVVzc1IwRkJSeXhOUVVGTkxFTkJRVU03U1VGRGNFZ3NRMEZCUXp0SlFVRkJMRU5CUVVNN1NVRkZSaXhUUVVGVExHZENRVUZuUWl4RFFVRkRMRWxCUVVrN1VVRkRNVUlzU1VGQlNTeExRVUZMTEVkQlFVY3NRMEZCUXl4RFFVRkRPMUZCUTJRc1NVRkJTU3hEUVVGRExFOUJRVThzUTBGQlF5eFZRVUZWTEVOQlFVTXNTVUZCU1N4UFFVRlBMRXRCUVVzc1NVRkJTU3hEUVVGRExFTkJRVU1zUzBGQlN5eEhRVUZITEdOQlFXTXNRMEZCUXl4UFFVRlBMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFJRVU5xUml4UFFVRlBMRXRCUVVzc1EwRkJRenRKUVVOcVFpeERRVUZETzBsQlJVUXNVMEZCVXl4alFVRmpPMUZCUTI1Q0xFOUJRVThzUTBGQlF5eFZRVUZWTEVkQlFVY3NWMEZCVnl4RFFVRkRMRU5CUVVNN1NVRkRkRU1zUTBGQlF6dEJRVU5NTEVOQlFVTTdRVUV4VUVRc2IwTkJNRkJETzBGQlRVUXNVMEZCWjBJc1kwRkJZeXhEUVVGRExFdEJRVXNzUlVGQlJTeExRVUZMTzBsQlEzWkRMRWxCUVVrc1MwRkJTeXhIUVVGSExFVkJRVVVzUTBGQlF6dEpRVU5tTEVsQlFVa3NTVUZCU1N4SFFVRkhMRVZCUVVVc1EwRkJRenRKUVVOa0xFbEJRVWtzVFVGQlRTeEhRVUZITEVWQlFVVXNRMEZCUXp0SlFVTm9RaXhKUVVGSkxGRkJRVkVzUjBGQlJ5eERRVUZETEVOQlFVTTdTVUZGYWtJc1MwRkJTeXhKUVVGSkxFTkJRVU1zUjBGQlJ5eERRVUZETEVWQlFVVXNRMEZCUXl4SFFVRkhMRXRCUVVzc1EwRkJReXhOUVVGTkxFVkJRVVVzUTBGQlF5eEZRVUZGTEVWQlFVVTdVVUZEYmtNc1NVRkJTU3hKUVVGSkxFZEJRVWNzUzBGQlN5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMUZCUTNCQ0xFbEJRVWtzUlVGQlJTeEhRVUZITEVsQlFVa3NRMEZCUXl4TlFVRk5MRU5CUVVNN1VVRkRja0lzU1VGQlNTeEZRVUZGTEVkQlFVY3NTVUZCU1N4RFFVRkRMRTFCUVUwc1EwRkJRenRSUVVOeVFpeEpRVUZKTEVsQlFVa3NRMEZCUXl4RlFVRkZMRU5CUVVNc1MwRkJTeXhEUVVGRE8xbEJRMlFzU1VGQlNTeERRVUZETEVWQlFVVXNRMEZCUXl4TFFVRkxMRU5CUVVNc1EwRkJReXhKUVVGSkxFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTTdPMWxCUlhoQ0xFbEJRVWtzUTBGQlF5eEZRVUZGTEVOQlFVTXNTMEZCU3l4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF6dFJRVVV4UWl4SlFVRkpMRWxCUVVrc1EwRkJReXhGUVVGRkxFTkJRVU1zUzBGQlN5eERRVUZETzFsQlEyUXNTVUZCU1N4RFFVRkRMRVZCUVVVc1EwRkJReXhMUVVGTExFTkJRVU1zUTBGQlF5eEpRVUZKTEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNN08xbEJSWGhDTEVsQlFVa3NRMEZCUXl4RlFVRkZMRU5CUVVNc1MwRkJTeXhEUVVGRExFZEJRVWNzUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXp0TFFVTTNRanRKUVVWRUxFdEJRVXNzU1VGQlNTeERRVUZETEVkQlFVY3NRMEZCUXl4RlFVRkZMRU5CUVVNc1IwRkJSeXhMUVVGTExFTkJRVU1zVFVGQlRTeEZRVUZGTEVOQlFVTXNSVUZCUlN4RlFVRkZPMUZCUTI1RExFbEJRVWtzU1VGQlNTeEhRVUZITEV0QlFVc3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRSUVVOd1FpeEpRVUZKTEV0QlFVc3NRMEZCUXl4SlFVRkpMRU5CUVVNc1MwRkJTeXhEUVVGRE8xbEJRVVVzVTBGQlV6dFJRVU5vUXl4WlFVRlpMRU5CUVVNc1NVRkJTU3hGUVVGRkxFbEJRVWtzUTBGQlF5eERRVUZETzB0QlF6VkNPMGxCUlVRc1UwRkJVeXhaUVVGWkxFTkJRVU1zUTBGQlF5eEZRVUZGTEUxQlFVMDdVVUZETTBJc1NVRkJTU3hMUVVGTExFTkJRVU1zUTBGQlF5eERRVUZETEV0QlFVc3NRMEZCUXl4TFFVRkxMRk5CUVZNN1dVRkJSU3hQUVVGUE8xRkJRM3BETEVsQlFVa3NUVUZCVFN4RlFVRkZPMWxCUTFJc1VVRkJVU3hGUVVGRkxFTkJRVU03V1VGRFdDeE5RVUZOTEVOQlFVTXNTVUZCU1N4RFFVRkRMRVZCUVVVc1MwRkJTeXhGUVVGRkxFVkJRVVVzUlVGQlJTeERRVUZETEVOQlFVTTdVMEZET1VJN1VVRkRSQ3hMUVVGTExFTkJRVU1zUTBGQlF5eERRVUZETEV0QlFVc3NRMEZCUXl4SFFVRkhMRkZCUVZFc1EwRkJRenRSUVVNeFFpeE5RVUZOTEVOQlFVTXNVVUZCVVN4SFFVRkhMRU5CUVVNc1EwRkJReXhEUVVGRExFdEJRVXNzUTBGQlF5eEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1VVRkRia01zU1VGQlNTeFJRVUZSTEVkQlFVY3NTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJReXhMUVVGTExFTkJRVU1zUTBGQlF6dFJRVU0zUWl4SlFVRkpMRU5CUVVNc1VVRkJVVHRaUVVGRkxFOUJRVTg3VVVGRmRFSXNTMEZCU3l4SlFVRkpMRU5CUVVNc1IwRkJSeXhEUVVGRExFVkJRVVVzUTBGQlF5eEhRVUZITEZGQlFWRXNRMEZCUXl4TlFVRk5MRVZCUVVVc1EwRkJReXhGUVVGRkxFVkJRVVU3V1VGRGRFTXNXVUZCV1N4RFFVRkRMRkZCUVZFc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQlJTeExRVUZMTEVOQlFVTXNRMEZCUXp0VFFVTndRenRKUVVOTUxFTkJRVU03U1VGRlJDeFBRVUZQTEUxQlFVMHNRMEZCUXp0QlFVTnNRaXhEUVVGRE8wRkJOVU5FTEhkRFFUUkRReUo5IiwiXCJ1c2Ugc3RyaWN0XCI7XHJcbk9iamVjdC5kZWZpbmVQcm9wZXJ0eShleHBvcnRzLCBcIl9fZXNNb2R1bGVcIiwgeyB2YWx1ZTogdHJ1ZSB9KTtcclxudmFyIHBvd2VyZ3JhcGggPSByZXF1aXJlKFwiLi9wb3dlcmdyYXBoXCIpO1xyXG52YXIgbGlua2xlbmd0aHNfMSA9IHJlcXVpcmUoXCIuL2xpbmtsZW5ndGhzXCIpO1xyXG52YXIgZGVzY2VudF8xID0gcmVxdWlyZShcIi4vZGVzY2VudFwiKTtcclxudmFyIHJlY3RhbmdsZV8xID0gcmVxdWlyZShcIi4vcmVjdGFuZ2xlXCIpO1xyXG52YXIgc2hvcnRlc3RwYXRoc18xID0gcmVxdWlyZShcIi4vc2hvcnRlc3RwYXRoc1wiKTtcclxudmFyIGdlb21fMSA9IHJlcXVpcmUoXCIuL2dlb21cIik7XHJcbnZhciBoYW5kbGVkaXNjb25uZWN0ZWRfMSA9IHJlcXVpcmUoXCIuL2hhbmRsZWRpc2Nvbm5lY3RlZFwiKTtcclxudmFyIEV2ZW50VHlwZTtcclxuKGZ1bmN0aW9uIChFdmVudFR5cGUpIHtcclxuICAgIEV2ZW50VHlwZVtFdmVudFR5cGVbXCJzdGFydFwiXSA9IDBdID0gXCJzdGFydFwiO1xyXG4gICAgRXZlbnRUeXBlW0V2ZW50VHlwZVtcInRpY2tcIl0gPSAxXSA9IFwidGlja1wiO1xyXG4gICAgRXZlbnRUeXBlW0V2ZW50VHlwZVtcImVuZFwiXSA9IDJdID0gXCJlbmRcIjtcclxufSkoRXZlbnRUeXBlID0gZXhwb3J0cy5FdmVudFR5cGUgfHwgKGV4cG9ydHMuRXZlbnRUeXBlID0ge30pKTtcclxuO1xyXG5mdW5jdGlvbiBpc0dyb3VwKGcpIHtcclxuICAgIHJldHVybiB0eXBlb2YgZy5sZWF2ZXMgIT09ICd1bmRlZmluZWQnIHx8IHR5cGVvZiBnLmdyb3VwcyAhPT0gJ3VuZGVmaW5lZCc7XHJcbn1cclxudmFyIExheW91dCA9IChmdW5jdGlvbiAoKSB7XHJcbiAgICBmdW5jdGlvbiBMYXlvdXQoKSB7XHJcbiAgICAgICAgdmFyIF90aGlzID0gdGhpcztcclxuICAgICAgICB0aGlzLl9jYW52YXNTaXplID0gWzEsIDFdO1xyXG4gICAgICAgIHRoaXMuX2xpbmtEaXN0YW5jZSA9IDIwO1xyXG4gICAgICAgIHRoaXMuX2RlZmF1bHROb2RlU2l6ZSA9IDEwO1xyXG4gICAgICAgIHRoaXMuX2xpbmtMZW5ndGhDYWxjdWxhdG9yID0gbnVsbDtcclxuICAgICAgICB0aGlzLl9saW5rVHlwZSA9IG51bGw7XHJcbiAgICAgICAgdGhpcy5fYXZvaWRPdmVybGFwcyA9IGZhbHNlO1xyXG4gICAgICAgIHRoaXMuX2hhbmRsZURpc2Nvbm5lY3RlZCA9IHRydWU7XHJcbiAgICAgICAgdGhpcy5fcnVubmluZyA9IGZhbHNlO1xyXG4gICAgICAgIHRoaXMuX25vZGVzID0gW107XHJcbiAgICAgICAgdGhpcy5fZ3JvdXBzID0gW107XHJcbiAgICAgICAgdGhpcy5fcm9vdEdyb3VwID0gbnVsbDtcclxuICAgICAgICB0aGlzLl9saW5rcyA9IFtdO1xyXG4gICAgICAgIHRoaXMuX2NvbnN0cmFpbnRzID0gW107XHJcbiAgICAgICAgdGhpcy5fZGlzdGFuY2VNYXRyaXggPSBudWxsO1xyXG4gICAgICAgIHRoaXMuX2Rlc2NlbnQgPSBudWxsO1xyXG4gICAgICAgIHRoaXMuX2RpcmVjdGVkTGlua0NvbnN0cmFpbnRzID0gbnVsbDtcclxuICAgICAgICB0aGlzLl90aHJlc2hvbGQgPSAwLjAxO1xyXG4gICAgICAgIHRoaXMuX3Zpc2liaWxpdHlHcmFwaCA9IG51bGw7XHJcbiAgICAgICAgdGhpcy5fZ3JvdXBDb21wYWN0bmVzcyA9IDFlLTY7XHJcbiAgICAgICAgdGhpcy5ldmVudCA9IG51bGw7XHJcbiAgICAgICAgdGhpcy5saW5rQWNjZXNzb3IgPSB7XHJcbiAgICAgICAgICAgIGdldFNvdXJjZUluZGV4OiBMYXlvdXQuZ2V0U291cmNlSW5kZXgsXHJcbiAgICAgICAgICAgIGdldFRhcmdldEluZGV4OiBMYXlvdXQuZ2V0VGFyZ2V0SW5kZXgsXHJcbiAgICAgICAgICAgIHNldExlbmd0aDogTGF5b3V0LnNldExpbmtMZW5ndGgsXHJcbiAgICAgICAgICAgIGdldFR5cGU6IGZ1bmN0aW9uIChsKSB7IHJldHVybiB0eXBlb2YgX3RoaXMuX2xpbmtUeXBlID09PSBcImZ1bmN0aW9uXCIgPyBfdGhpcy5fbGlua1R5cGUobCkgOiAwOyB9XHJcbiAgICAgICAgfTtcclxuICAgIH1cclxuICAgIExheW91dC5wcm90b3R5cGUub24gPSBmdW5jdGlvbiAoZSwgbGlzdGVuZXIpIHtcclxuICAgICAgICBpZiAoIXRoaXMuZXZlbnQpXHJcbiAgICAgICAgICAgIHRoaXMuZXZlbnQgPSB7fTtcclxuICAgICAgICBpZiAodHlwZW9mIGUgPT09ICdzdHJpbmcnKSB7XHJcbiAgICAgICAgICAgIHRoaXMuZXZlbnRbRXZlbnRUeXBlW2VdXSA9IGxpc3RlbmVyO1xyXG4gICAgICAgIH1cclxuICAgICAgICBlbHNlIHtcclxuICAgICAgICAgICAgdGhpcy5ldmVudFtlXSA9IGxpc3RlbmVyO1xyXG4gICAgICAgIH1cclxuICAgICAgICByZXR1cm4gdGhpcztcclxuICAgIH07XHJcbiAgICBMYXlvdXQucHJvdG90eXBlLnRyaWdnZXIgPSBmdW5jdGlvbiAoZSkge1xyXG4gICAgICAgIGlmICh0aGlzLmV2ZW50ICYmIHR5cGVvZiB0aGlzLmV2ZW50W2UudHlwZV0gIT09ICd1bmRlZmluZWQnKSB7XHJcbiAgICAgICAgICAgIHRoaXMuZXZlbnRbZS50eXBlXShlKTtcclxuICAgICAgICB9XHJcbiAgICB9O1xyXG4gICAgTGF5b3V0LnByb3RvdHlwZS5raWNrID0gZnVuY3Rpb24gKCkge1xyXG4gICAgICAgIHdoaWxlICghdGhpcy50aWNrKCkpXHJcbiAgICAgICAgICAgIDtcclxuICAgIH07XHJcbiAgICBMYXlvdXQucHJvdG90eXBlLnRpY2sgPSBmdW5jdGlvbiAoKSB7XHJcbiAgICAgICAgaWYgKHRoaXMuX2FscGhhIDwgdGhpcy5fdGhyZXNob2xkKSB7XHJcbiAgICAgICAgICAgIHRoaXMuX3J1bm5pbmcgPSBmYWxzZTtcclxuICAgICAgICAgICAgdGhpcy50cmlnZ2VyKHsgdHlwZTogRXZlbnRUeXBlLmVuZCwgYWxwaGE6IHRoaXMuX2FscGhhID0gMCwgc3RyZXNzOiB0aGlzLl9sYXN0U3RyZXNzIH0pO1xyXG4gICAgICAgICAgICByZXR1cm4gdHJ1ZTtcclxuICAgICAgICB9XHJcbiAgICAgICAgdmFyIG4gPSB0aGlzLl9ub2Rlcy5sZW5ndGgsIG0gPSB0aGlzLl9saW5rcy5sZW5ndGg7XHJcbiAgICAgICAgdmFyIG8sIGk7XHJcbiAgICAgICAgdGhpcy5fZGVzY2VudC5sb2Nrcy5jbGVhcigpO1xyXG4gICAgICAgIGZvciAoaSA9IDA7IGkgPCBuOyArK2kpIHtcclxuICAgICAgICAgICAgbyA9IHRoaXMuX25vZGVzW2ldO1xyXG4gICAgICAgICAgICBpZiAoby5maXhlZCkge1xyXG4gICAgICAgICAgICAgICAgaWYgKHR5cGVvZiBvLnB4ID09PSAndW5kZWZpbmVkJyB8fCB0eXBlb2Ygby5weSA9PT0gJ3VuZGVmaW5lZCcpIHtcclxuICAgICAgICAgICAgICAgICAgICBvLnB4ID0gby54O1xyXG4gICAgICAgICAgICAgICAgICAgIG8ucHkgPSBvLnk7XHJcbiAgICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgICAgICB2YXIgcCA9IFtvLnB4LCBvLnB5XTtcclxuICAgICAgICAgICAgICAgIHRoaXMuX2Rlc2NlbnQubG9ja3MuYWRkKGksIHApO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgfVxyXG4gICAgICAgIHZhciBzMSA9IHRoaXMuX2Rlc2NlbnQucnVuZ2VLdXR0YSgpO1xyXG4gICAgICAgIGlmIChzMSA9PT0gMCkge1xyXG4gICAgICAgICAgICB0aGlzLl9hbHBoYSA9IDA7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIGVsc2UgaWYgKHR5cGVvZiB0aGlzLl9sYXN0U3RyZXNzICE9PSAndW5kZWZpbmVkJykge1xyXG4gICAgICAgICAgICB0aGlzLl9hbHBoYSA9IHMxO1xyXG4gICAgICAgIH1cclxuICAgICAgICB0aGlzLl9sYXN0U3RyZXNzID0gczE7XHJcbiAgICAgICAgdGhpcy51cGRhdGVOb2RlUG9zaXRpb25zKCk7XHJcbiAgICAgICAgdGhpcy50cmlnZ2VyKHsgdHlwZTogRXZlbnRUeXBlLnRpY2ssIGFscGhhOiB0aGlzLl9hbHBoYSwgc3RyZXNzOiB0aGlzLl9sYXN0U3RyZXNzIH0pO1xyXG4gICAgICAgIHJldHVybiBmYWxzZTtcclxuICAgIH07XHJcbiAgICBMYXlvdXQucHJvdG90eXBlLnVwZGF0ZU5vZGVQb3NpdGlvbnMgPSBmdW5jdGlvbiAoKSB7XHJcbiAgICAgICAgdmFyIHggPSB0aGlzLl9kZXNjZW50LnhbMF0sIHkgPSB0aGlzLl9kZXNjZW50LnhbMV07XHJcbiAgICAgICAgdmFyIG8sIGkgPSB0aGlzLl9ub2Rlcy5sZW5ndGg7XHJcbiAgICAgICAgd2hpbGUgKGktLSkge1xyXG4gICAgICAgICAgICBvID0gdGhpcy5fbm9kZXNbaV07XHJcbiAgICAgICAgICAgIG8ueCA9IHhbaV07XHJcbiAgICAgICAgICAgIG8ueSA9IHlbaV07XHJcbiAgICAgICAgfVxyXG4gICAgfTtcclxuICAgIExheW91dC5wcm90b3R5cGUubm9kZXMgPSBmdW5jdGlvbiAodikge1xyXG4gICAgICAgIGlmICghdikge1xyXG4gICAgICAgICAgICBpZiAodGhpcy5fbm9kZXMubGVuZ3RoID09PSAwICYmIHRoaXMuX2xpbmtzLmxlbmd0aCA+IDApIHtcclxuICAgICAgICAgICAgICAgIHZhciBuID0gMDtcclxuICAgICAgICAgICAgICAgIHRoaXMuX2xpbmtzLmZvckVhY2goZnVuY3Rpb24gKGwpIHtcclxuICAgICAgICAgICAgICAgICAgICBuID0gTWF0aC5tYXgobiwgbC5zb3VyY2UsIGwudGFyZ2V0KTtcclxuICAgICAgICAgICAgICAgIH0pO1xyXG4gICAgICAgICAgICAgICAgdGhpcy5fbm9kZXMgPSBuZXcgQXJyYXkoKytuKTtcclxuICAgICAgICAgICAgICAgIGZvciAodmFyIGkgPSAwOyBpIDwgbjsgKytpKSB7XHJcbiAgICAgICAgICAgICAgICAgICAgdGhpcy5fbm9kZXNbaV0gPSB7fTtcclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICByZXR1cm4gdGhpcy5fbm9kZXM7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIHRoaXMuX25vZGVzID0gdjtcclxuICAgICAgICByZXR1cm4gdGhpcztcclxuICAgIH07XHJcbiAgICBMYXlvdXQucHJvdG90eXBlLmdyb3VwcyA9IGZ1bmN0aW9uICh4KSB7XHJcbiAgICAgICAgdmFyIF90aGlzID0gdGhpcztcclxuICAgICAgICBpZiAoIXgpXHJcbiAgICAgICAgICAgIHJldHVybiB0aGlzLl9ncm91cHM7XHJcbiAgICAgICAgdGhpcy5fZ3JvdXBzID0geDtcclxuICAgICAgICB0aGlzLl9yb290R3JvdXAgPSB7fTtcclxuICAgICAgICB0aGlzLl9ncm91cHMuZm9yRWFjaChmdW5jdGlvbiAoZykge1xyXG4gICAgICAgICAgICBpZiAodHlwZW9mIGcucGFkZGluZyA9PT0gXCJ1bmRlZmluZWRcIilcclxuICAgICAgICAgICAgICAgIGcucGFkZGluZyA9IDE7XHJcbiAgICAgICAgICAgIGlmICh0eXBlb2YgZy5sZWF2ZXMgIT09IFwidW5kZWZpbmVkXCIpIHtcclxuICAgICAgICAgICAgICAgIGcubGVhdmVzLmZvckVhY2goZnVuY3Rpb24gKHYsIGkpIHtcclxuICAgICAgICAgICAgICAgICAgICBpZiAodHlwZW9mIHYgPT09ICdudW1iZXInKVxyXG4gICAgICAgICAgICAgICAgICAgICAgICAoZy5sZWF2ZXNbaV0gPSBfdGhpcy5fbm9kZXNbdl0pLnBhcmVudCA9IGc7XHJcbiAgICAgICAgICAgICAgICB9KTtcclxuICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICBpZiAodHlwZW9mIGcuZ3JvdXBzICE9PSBcInVuZGVmaW5lZFwiKSB7XHJcbiAgICAgICAgICAgICAgICBnLmdyb3Vwcy5mb3JFYWNoKGZ1bmN0aW9uIChnaSwgaSkge1xyXG4gICAgICAgICAgICAgICAgICAgIGlmICh0eXBlb2YgZ2kgPT09ICdudW1iZXInKVxyXG4gICAgICAgICAgICAgICAgICAgICAgICAoZy5ncm91cHNbaV0gPSBfdGhpcy5fZ3JvdXBzW2dpXSkucGFyZW50ID0gZztcclxuICAgICAgICAgICAgICAgIH0pO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgfSk7XHJcbiAgICAgICAgdGhpcy5fcm9vdEdyb3VwLmxlYXZlcyA9IHRoaXMuX25vZGVzLmZpbHRlcihmdW5jdGlvbiAodikgeyByZXR1cm4gdHlwZW9mIHYucGFyZW50ID09PSAndW5kZWZpbmVkJzsgfSk7XHJcbiAgICAgICAgdGhpcy5fcm9vdEdyb3VwLmdyb3VwcyA9IHRoaXMuX2dyb3Vwcy5maWx0ZXIoZnVuY3Rpb24gKGcpIHsgcmV0dXJuIHR5cGVvZiBnLnBhcmVudCA9PT0gJ3VuZGVmaW5lZCc7IH0pO1xyXG4gICAgICAgIHJldHVybiB0aGlzO1xyXG4gICAgfTtcclxuICAgIExheW91dC5wcm90b3R5cGUucG93ZXJHcmFwaEdyb3VwcyA9IGZ1bmN0aW9uIChmKSB7XHJcbiAgICAgICAgdmFyIGcgPSBwb3dlcmdyYXBoLmdldEdyb3Vwcyh0aGlzLl9ub2RlcywgdGhpcy5fbGlua3MsIHRoaXMubGlua0FjY2Vzc29yLCB0aGlzLl9yb290R3JvdXApO1xyXG4gICAgICAgIHRoaXMuZ3JvdXBzKGcuZ3JvdXBzKTtcclxuICAgICAgICBmKGcpO1xyXG4gICAgICAgIHJldHVybiB0aGlzO1xyXG4gICAgfTtcclxuICAgIExheW91dC5wcm90b3R5cGUuYXZvaWRPdmVybGFwcyA9IGZ1bmN0aW9uICh2KSB7XHJcbiAgICAgICAgaWYgKCFhcmd1bWVudHMubGVuZ3RoKVxyXG4gICAgICAgICAgICByZXR1cm4gdGhpcy5fYXZvaWRPdmVybGFwcztcclxuICAgICAgICB0aGlzLl9hdm9pZE92ZXJsYXBzID0gdjtcclxuICAgICAgICByZXR1cm4gdGhpcztcclxuICAgIH07XHJcbiAgICBMYXlvdXQucHJvdG90eXBlLmhhbmRsZURpc2Nvbm5lY3RlZCA9IGZ1bmN0aW9uICh2KSB7XHJcbiAgICAgICAgaWYgKCFhcmd1bWVudHMubGVuZ3RoKVxyXG4gICAgICAgICAgICByZXR1cm4gdGhpcy5faGFuZGxlRGlzY29ubmVjdGVkO1xyXG4gICAgICAgIHRoaXMuX2hhbmRsZURpc2Nvbm5lY3RlZCA9IHY7XHJcbiAgICAgICAgcmV0dXJuIHRoaXM7XHJcbiAgICB9O1xyXG4gICAgTGF5b3V0LnByb3RvdHlwZS5mbG93TGF5b3V0ID0gZnVuY3Rpb24gKGF4aXMsIG1pblNlcGFyYXRpb24pIHtcclxuICAgICAgICBpZiAoIWFyZ3VtZW50cy5sZW5ndGgpXHJcbiAgICAgICAgICAgIGF4aXMgPSAneSc7XHJcbiAgICAgICAgdGhpcy5fZGlyZWN0ZWRMaW5rQ29uc3RyYWludHMgPSB7XHJcbiAgICAgICAgICAgIGF4aXM6IGF4aXMsXHJcbiAgICAgICAgICAgIGdldE1pblNlcGFyYXRpb246IHR5cGVvZiBtaW5TZXBhcmF0aW9uID09PSAnbnVtYmVyJyA/IGZ1bmN0aW9uICgpIHsgcmV0dXJuIG1pblNlcGFyYXRpb247IH0gOiBtaW5TZXBhcmF0aW9uXHJcbiAgICAgICAgfTtcclxuICAgICAgICByZXR1cm4gdGhpcztcclxuICAgIH07XHJcbiAgICBMYXlvdXQucHJvdG90eXBlLmxpbmtzID0gZnVuY3Rpb24gKHgpIHtcclxuICAgICAgICBpZiAoIWFyZ3VtZW50cy5sZW5ndGgpXHJcbiAgICAgICAgICAgIHJldHVybiB0aGlzLl9saW5rcztcclxuICAgICAgICB0aGlzLl9saW5rcyA9IHg7XHJcbiAgICAgICAgcmV0dXJuIHRoaXM7XHJcbiAgICB9O1xyXG4gICAgTGF5b3V0LnByb3RvdHlwZS5jb25zdHJhaW50cyA9IGZ1bmN0aW9uIChjKSB7XHJcbiAgICAgICAgaWYgKCFhcmd1bWVudHMubGVuZ3RoKVxyXG4gICAgICAgICAgICByZXR1cm4gdGhpcy5fY29uc3RyYWludHM7XHJcbiAgICAgICAgdGhpcy5fY29uc3RyYWludHMgPSBjO1xyXG4gICAgICAgIHJldHVybiB0aGlzO1xyXG4gICAgfTtcclxuICAgIExheW91dC5wcm90b3R5cGUuZGlzdGFuY2VNYXRyaXggPSBmdW5jdGlvbiAoZCkge1xyXG4gICAgICAgIGlmICghYXJndW1lbnRzLmxlbmd0aClcclxuICAgICAgICAgICAgcmV0dXJuIHRoaXMuX2Rpc3RhbmNlTWF0cml4O1xyXG4gICAgICAgIHRoaXMuX2Rpc3RhbmNlTWF0cml4ID0gZDtcclxuICAgICAgICByZXR1cm4gdGhpcztcclxuICAgIH07XHJcbiAgICBMYXlvdXQucHJvdG90eXBlLnNpemUgPSBmdW5jdGlvbiAoeCkge1xyXG4gICAgICAgIGlmICgheClcclxuICAgICAgICAgICAgcmV0dXJuIHRoaXMuX2NhbnZhc1NpemU7XHJcbiAgICAgICAgdGhpcy5fY2FudmFzU2l6ZSA9IHg7XHJcbiAgICAgICAgcmV0dXJuIHRoaXM7XHJcbiAgICB9O1xyXG4gICAgTGF5b3V0LnByb3RvdHlwZS5kZWZhdWx0Tm9kZVNpemUgPSBmdW5jdGlvbiAoeCkge1xyXG4gICAgICAgIGlmICgheClcclxuICAgICAgICAgICAgcmV0dXJuIHRoaXMuX2RlZmF1bHROb2RlU2l6ZTtcclxuICAgICAgICB0aGlzLl9kZWZhdWx0Tm9kZVNpemUgPSB4O1xyXG4gICAgICAgIHJldHVybiB0aGlzO1xyXG4gICAgfTtcclxuICAgIExheW91dC5wcm90b3R5cGUuZ3JvdXBDb21wYWN0bmVzcyA9IGZ1bmN0aW9uICh4KSB7XHJcbiAgICAgICAgaWYgKCF4KVxyXG4gICAgICAgICAgICByZXR1cm4gdGhpcy5fZ3JvdXBDb21wYWN0bmVzcztcclxuICAgICAgICB0aGlzLl9ncm91cENvbXBhY3RuZXNzID0geDtcclxuICAgICAgICByZXR1cm4gdGhpcztcclxuICAgIH07XHJcbiAgICBMYXlvdXQucHJvdG90eXBlLmxpbmtEaXN0YW5jZSA9IGZ1bmN0aW9uICh4KSB7XHJcbiAgICAgICAgaWYgKCF4KSB7XHJcbiAgICAgICAgICAgIHJldHVybiB0aGlzLl9saW5rRGlzdGFuY2U7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIHRoaXMuX2xpbmtEaXN0YW5jZSA9IHR5cGVvZiB4ID09PSBcImZ1bmN0aW9uXCIgPyB4IDogK3g7XHJcbiAgICAgICAgdGhpcy5fbGlua0xlbmd0aENhbGN1bGF0b3IgPSBudWxsO1xyXG4gICAgICAgIHJldHVybiB0aGlzO1xyXG4gICAgfTtcclxuICAgIExheW91dC5wcm90b3R5cGUubGlua1R5cGUgPSBmdW5jdGlvbiAoZikge1xyXG4gICAgICAgIHRoaXMuX2xpbmtUeXBlID0gZjtcclxuICAgICAgICByZXR1cm4gdGhpcztcclxuICAgIH07XHJcbiAgICBMYXlvdXQucHJvdG90eXBlLmNvbnZlcmdlbmNlVGhyZXNob2xkID0gZnVuY3Rpb24gKHgpIHtcclxuICAgICAgICBpZiAoIXgpXHJcbiAgICAgICAgICAgIHJldHVybiB0aGlzLl90aHJlc2hvbGQ7XHJcbiAgICAgICAgdGhpcy5fdGhyZXNob2xkID0gdHlwZW9mIHggPT09IFwiZnVuY3Rpb25cIiA/IHggOiAreDtcclxuICAgICAgICByZXR1cm4gdGhpcztcclxuICAgIH07XHJcbiAgICBMYXlvdXQucHJvdG90eXBlLmFscGhhID0gZnVuY3Rpb24gKHgpIHtcclxuICAgICAgICBpZiAoIWFyZ3VtZW50cy5sZW5ndGgpXHJcbiAgICAgICAgICAgIHJldHVybiB0aGlzLl9hbHBoYTtcclxuICAgICAgICBlbHNlIHtcclxuICAgICAgICAgICAgeCA9ICt4O1xyXG4gICAgICAgICAgICBpZiAodGhpcy5fYWxwaGEpIHtcclxuICAgICAgICAgICAgICAgIGlmICh4ID4gMClcclxuICAgICAgICAgICAgICAgICAgICB0aGlzLl9hbHBoYSA9IHg7XHJcbiAgICAgICAgICAgICAgICBlbHNlXHJcbiAgICAgICAgICAgICAgICAgICAgdGhpcy5fYWxwaGEgPSAwO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgICAgIGVsc2UgaWYgKHggPiAwKSB7XHJcbiAgICAgICAgICAgICAgICBpZiAoIXRoaXMuX3J1bm5pbmcpIHtcclxuICAgICAgICAgICAgICAgICAgICB0aGlzLl9ydW5uaW5nID0gdHJ1ZTtcclxuICAgICAgICAgICAgICAgICAgICB0aGlzLnRyaWdnZXIoeyB0eXBlOiBFdmVudFR5cGUuc3RhcnQsIGFscGhhOiB0aGlzLl9hbHBoYSA9IHggfSk7XHJcbiAgICAgICAgICAgICAgICAgICAgdGhpcy5raWNrKCk7XHJcbiAgICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgcmV0dXJuIHRoaXM7XHJcbiAgICAgICAgfVxyXG4gICAgfTtcclxuICAgIExheW91dC5wcm90b3R5cGUuZ2V0TGlua0xlbmd0aCA9IGZ1bmN0aW9uIChsaW5rKSB7XHJcbiAgICAgICAgcmV0dXJuIHR5cGVvZiB0aGlzLl9saW5rRGlzdGFuY2UgPT09IFwiZnVuY3Rpb25cIiA/ICsodGhpcy5fbGlua0Rpc3RhbmNlKGxpbmspKSA6IHRoaXMuX2xpbmtEaXN0YW5jZTtcclxuICAgIH07XHJcbiAgICBMYXlvdXQuc2V0TGlua0xlbmd0aCA9IGZ1bmN0aW9uIChsaW5rLCBsZW5ndGgpIHtcclxuICAgICAgICBsaW5rLmxlbmd0aCA9IGxlbmd0aDtcclxuICAgIH07XHJcbiAgICBMYXlvdXQucHJvdG90eXBlLmdldExpbmtUeXBlID0gZnVuY3Rpb24gKGxpbmspIHtcclxuICAgICAgICByZXR1cm4gdHlwZW9mIHRoaXMuX2xpbmtUeXBlID09PSBcImZ1bmN0aW9uXCIgPyB0aGlzLl9saW5rVHlwZShsaW5rKSA6IDA7XHJcbiAgICB9O1xyXG4gICAgTGF5b3V0LnByb3RvdHlwZS5zeW1tZXRyaWNEaWZmTGlua0xlbmd0aHMgPSBmdW5jdGlvbiAoaWRlYWxMZW5ndGgsIHcpIHtcclxuICAgICAgICB2YXIgX3RoaXMgPSB0aGlzO1xyXG4gICAgICAgIGlmICh3ID09PSB2b2lkIDApIHsgdyA9IDE7IH1cclxuICAgICAgICB0aGlzLmxpbmtEaXN0YW5jZShmdW5jdGlvbiAobCkgeyByZXR1cm4gaWRlYWxMZW5ndGggKiBsLmxlbmd0aDsgfSk7XHJcbiAgICAgICAgdGhpcy5fbGlua0xlbmd0aENhbGN1bGF0b3IgPSBmdW5jdGlvbiAoKSB7IHJldHVybiBsaW5rbGVuZ3Roc18xLnN5bW1ldHJpY0RpZmZMaW5rTGVuZ3RocyhfdGhpcy5fbGlua3MsIF90aGlzLmxpbmtBY2Nlc3Nvciwgdyk7IH07XHJcbiAgICAgICAgcmV0dXJuIHRoaXM7XHJcbiAgICB9O1xyXG4gICAgTGF5b3V0LnByb3RvdHlwZS5qYWNjYXJkTGlua0xlbmd0aHMgPSBmdW5jdGlvbiAoaWRlYWxMZW5ndGgsIHcpIHtcclxuICAgICAgICB2YXIgX3RoaXMgPSB0aGlzO1xyXG4gICAgICAgIGlmICh3ID09PSB2b2lkIDApIHsgdyA9IDE7IH1cclxuICAgICAgICB0aGlzLmxpbmtEaXN0YW5jZShmdW5jdGlvbiAobCkgeyByZXR1cm4gaWRlYWxMZW5ndGggKiBsLmxlbmd0aDsgfSk7XHJcbiAgICAgICAgdGhpcy5fbGlua0xlbmd0aENhbGN1bGF0b3IgPSBmdW5jdGlvbiAoKSB7IHJldHVybiBsaW5rbGVuZ3Roc18xLmphY2NhcmRMaW5rTGVuZ3RocyhfdGhpcy5fbGlua3MsIF90aGlzLmxpbmtBY2Nlc3Nvciwgdyk7IH07XHJcbiAgICAgICAgcmV0dXJuIHRoaXM7XHJcbiAgICB9O1xyXG4gICAgTGF5b3V0LnByb3RvdHlwZS5zdGFydCA9IGZ1bmN0aW9uIChpbml0aWFsVW5jb25zdHJhaW5lZEl0ZXJhdGlvbnMsIGluaXRpYWxVc2VyQ29uc3RyYWludEl0ZXJhdGlvbnMsIGluaXRpYWxBbGxDb25zdHJhaW50c0l0ZXJhdGlvbnMsIGdyaWRTbmFwSXRlcmF0aW9ucywga2VlcFJ1bm5pbmcsIGNlbnRlckdyYXBoKSB7XHJcbiAgICAgICAgdmFyIF90aGlzID0gdGhpcztcclxuICAgICAgICBpZiAoaW5pdGlhbFVuY29uc3RyYWluZWRJdGVyYXRpb25zID09PSB2b2lkIDApIHsgaW5pdGlhbFVuY29uc3RyYWluZWRJdGVyYXRpb25zID0gMDsgfVxyXG4gICAgICAgIGlmIChpbml0aWFsVXNlckNvbnN0cmFpbnRJdGVyYXRpb25zID09PSB2b2lkIDApIHsgaW5pdGlhbFVzZXJDb25zdHJhaW50SXRlcmF0aW9ucyA9IDA7IH1cclxuICAgICAgICBpZiAoaW5pdGlhbEFsbENvbnN0cmFpbnRzSXRlcmF0aW9ucyA9PT0gdm9pZCAwKSB7IGluaXRpYWxBbGxDb25zdHJhaW50c0l0ZXJhdGlvbnMgPSAwOyB9XHJcbiAgICAgICAgaWYgKGdyaWRTbmFwSXRlcmF0aW9ucyA9PT0gdm9pZCAwKSB7IGdyaWRTbmFwSXRlcmF0aW9ucyA9IDA7IH1cclxuICAgICAgICBpZiAoa2VlcFJ1bm5pbmcgPT09IHZvaWQgMCkgeyBrZWVwUnVubmluZyA9IHRydWU7IH1cclxuICAgICAgICBpZiAoY2VudGVyR3JhcGggPT09IHZvaWQgMCkgeyBjZW50ZXJHcmFwaCA9IHRydWU7IH1cclxuICAgICAgICB2YXIgaSwgaiwgbiA9IHRoaXMubm9kZXMoKS5sZW5ndGgsIE4gPSBuICsgMiAqIHRoaXMuX2dyb3Vwcy5sZW5ndGgsIG0gPSB0aGlzLl9saW5rcy5sZW5ndGgsIHcgPSB0aGlzLl9jYW52YXNTaXplWzBdLCBoID0gdGhpcy5fY2FudmFzU2l6ZVsxXTtcclxuICAgICAgICB2YXIgeCA9IG5ldyBBcnJheShOKSwgeSA9IG5ldyBBcnJheShOKTtcclxuICAgICAgICB2YXIgRyA9IG51bGw7XHJcbiAgICAgICAgdmFyIGFvID0gdGhpcy5fYXZvaWRPdmVybGFwcztcclxuICAgICAgICB0aGlzLl9ub2Rlcy5mb3JFYWNoKGZ1bmN0aW9uICh2LCBpKSB7XHJcbiAgICAgICAgICAgIHYuaW5kZXggPSBpO1xyXG4gICAgICAgICAgICBpZiAodHlwZW9mIHYueCA9PT0gJ3VuZGVmaW5lZCcpIHtcclxuICAgICAgICAgICAgICAgIHYueCA9IHcgLyAyLCB2LnkgPSBoIC8gMjtcclxuICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICB4W2ldID0gdi54LCB5W2ldID0gdi55O1xyXG4gICAgICAgIH0pO1xyXG4gICAgICAgIGlmICh0aGlzLl9saW5rTGVuZ3RoQ2FsY3VsYXRvcilcclxuICAgICAgICAgICAgdGhpcy5fbGlua0xlbmd0aENhbGN1bGF0b3IoKTtcclxuICAgICAgICB2YXIgZGlzdGFuY2VzO1xyXG4gICAgICAgIGlmICh0aGlzLl9kaXN0YW5jZU1hdHJpeCkge1xyXG4gICAgICAgICAgICBkaXN0YW5jZXMgPSB0aGlzLl9kaXN0YW5jZU1hdHJpeDtcclxuICAgICAgICB9XHJcbiAgICAgICAgZWxzZSB7XHJcbiAgICAgICAgICAgIGRpc3RhbmNlcyA9IChuZXcgc2hvcnRlc3RwYXRoc18xLkNhbGN1bGF0b3IoTiwgdGhpcy5fbGlua3MsIExheW91dC5nZXRTb3VyY2VJbmRleCwgTGF5b3V0LmdldFRhcmdldEluZGV4LCBmdW5jdGlvbiAobCkgeyByZXR1cm4gX3RoaXMuZ2V0TGlua0xlbmd0aChsKTsgfSkpLkRpc3RhbmNlTWF0cml4KCk7XHJcbiAgICAgICAgICAgIEcgPSBkZXNjZW50XzEuRGVzY2VudC5jcmVhdGVTcXVhcmVNYXRyaXgoTiwgZnVuY3Rpb24gKCkgeyByZXR1cm4gMjsgfSk7XHJcbiAgICAgICAgICAgIHRoaXMuX2xpbmtzLmZvckVhY2goZnVuY3Rpb24gKGwpIHtcclxuICAgICAgICAgICAgICAgIGlmICh0eXBlb2YgbC5zb3VyY2UgPT0gXCJudW1iZXJcIilcclxuICAgICAgICAgICAgICAgICAgICBsLnNvdXJjZSA9IF90aGlzLl9ub2Rlc1tsLnNvdXJjZV07XHJcbiAgICAgICAgICAgICAgICBpZiAodHlwZW9mIGwudGFyZ2V0ID09IFwibnVtYmVyXCIpXHJcbiAgICAgICAgICAgICAgICAgICAgbC50YXJnZXQgPSBfdGhpcy5fbm9kZXNbbC50YXJnZXRdO1xyXG4gICAgICAgICAgICB9KTtcclxuICAgICAgICAgICAgdGhpcy5fbGlua3MuZm9yRWFjaChmdW5jdGlvbiAoZSkge1xyXG4gICAgICAgICAgICAgICAgdmFyIHUgPSBMYXlvdXQuZ2V0U291cmNlSW5kZXgoZSksIHYgPSBMYXlvdXQuZ2V0VGFyZ2V0SW5kZXgoZSk7XHJcbiAgICAgICAgICAgICAgICBHW3VdW3ZdID0gR1t2XVt1XSA9IGUud2VpZ2h0IHx8IDE7XHJcbiAgICAgICAgICAgIH0pO1xyXG4gICAgICAgIH1cclxuICAgICAgICB2YXIgRCA9IGRlc2NlbnRfMS5EZXNjZW50LmNyZWF0ZVNxdWFyZU1hdHJpeChOLCBmdW5jdGlvbiAoaSwgaikge1xyXG4gICAgICAgICAgICByZXR1cm4gZGlzdGFuY2VzW2ldW2pdO1xyXG4gICAgICAgIH0pO1xyXG4gICAgICAgIGlmICh0aGlzLl9yb290R3JvdXAgJiYgdHlwZW9mIHRoaXMuX3Jvb3RHcm91cC5ncm91cHMgIT09ICd1bmRlZmluZWQnKSB7XHJcbiAgICAgICAgICAgIHZhciBpID0gbjtcclxuICAgICAgICAgICAgdmFyIGFkZEF0dHJhY3Rpb24gPSBmdW5jdGlvbiAoaSwgaiwgc3RyZW5ndGgsIGlkZWFsRGlzdGFuY2UpIHtcclxuICAgICAgICAgICAgICAgIEdbaV1bal0gPSBHW2pdW2ldID0gc3RyZW5ndGg7XHJcbiAgICAgICAgICAgICAgICBEW2ldW2pdID0gRFtqXVtpXSA9IGlkZWFsRGlzdGFuY2U7XHJcbiAgICAgICAgICAgIH07XHJcbiAgICAgICAgICAgIHRoaXMuX2dyb3Vwcy5mb3JFYWNoKGZ1bmN0aW9uIChnKSB7XHJcbiAgICAgICAgICAgICAgICBhZGRBdHRyYWN0aW9uKGksIGkgKyAxLCBfdGhpcy5fZ3JvdXBDb21wYWN0bmVzcywgMC4xKTtcclxuICAgICAgICAgICAgICAgIGlmICh0eXBlb2YgZy5ib3VuZHMgPT09ICd1bmRlZmluZWQnKSB7XHJcbiAgICAgICAgICAgICAgICAgICAgeFtpXSA9IHcgLyAyLCB5W2krK10gPSBoIC8gMjtcclxuICAgICAgICAgICAgICAgICAgICB4W2ldID0gdyAvIDIsIHlbaSsrXSA9IGggLyAyO1xyXG4gICAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICAgICAgZWxzZSB7XHJcbiAgICAgICAgICAgICAgICAgICAgeFtpXSA9IGcuYm91bmRzLngsIHlbaSsrXSA9IGcuYm91bmRzLnk7XHJcbiAgICAgICAgICAgICAgICAgICAgeFtpXSA9IGcuYm91bmRzLlgsIHlbaSsrXSA9IGcuYm91bmRzLlk7XHJcbiAgICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgIH0pO1xyXG4gICAgICAgIH1cclxuICAgICAgICBlbHNlXHJcbiAgICAgICAgICAgIHRoaXMuX3Jvb3RHcm91cCA9IHsgbGVhdmVzOiB0aGlzLl9ub2RlcywgZ3JvdXBzOiBbXSB9O1xyXG4gICAgICAgIHZhciBjdXJDb25zdHJhaW50cyA9IHRoaXMuX2NvbnN0cmFpbnRzIHx8IFtdO1xyXG4gICAgICAgIGlmICh0aGlzLl9kaXJlY3RlZExpbmtDb25zdHJhaW50cykge1xyXG4gICAgICAgICAgICB0aGlzLmxpbmtBY2Nlc3Nvci5nZXRNaW5TZXBhcmF0aW9uID0gdGhpcy5fZGlyZWN0ZWRMaW5rQ29uc3RyYWludHMuZ2V0TWluU2VwYXJhdGlvbjtcclxuICAgICAgICAgICAgY3VyQ29uc3RyYWludHMgPSBjdXJDb25zdHJhaW50cy5jb25jYXQobGlua2xlbmd0aHNfMS5nZW5lcmF0ZURpcmVjdGVkRWRnZUNvbnN0cmFpbnRzKG4sIHRoaXMuX2xpbmtzLCB0aGlzLl9kaXJlY3RlZExpbmtDb25zdHJhaW50cy5heGlzLCAodGhpcy5saW5rQWNjZXNzb3IpKSk7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIHRoaXMuYXZvaWRPdmVybGFwcyhmYWxzZSk7XHJcbiAgICAgICAgdGhpcy5fZGVzY2VudCA9IG5ldyBkZXNjZW50XzEuRGVzY2VudChbeCwgeV0sIEQpO1xyXG4gICAgICAgIHRoaXMuX2Rlc2NlbnQubG9ja3MuY2xlYXIoKTtcclxuICAgICAgICBmb3IgKHZhciBpID0gMDsgaSA8IG47ICsraSkge1xyXG4gICAgICAgICAgICB2YXIgbyA9IHRoaXMuX25vZGVzW2ldO1xyXG4gICAgICAgICAgICBpZiAoby5maXhlZCkge1xyXG4gICAgICAgICAgICAgICAgby5weCA9IG8ueDtcclxuICAgICAgICAgICAgICAgIG8ucHkgPSBvLnk7XHJcbiAgICAgICAgICAgICAgICB2YXIgcCA9IFtvLngsIG8ueV07XHJcbiAgICAgICAgICAgICAgICB0aGlzLl9kZXNjZW50LmxvY2tzLmFkZChpLCBwKTtcclxuICAgICAgICAgICAgfVxyXG4gICAgICAgIH1cclxuICAgICAgICB0aGlzLl9kZXNjZW50LnRocmVzaG9sZCA9IHRoaXMuX3RocmVzaG9sZDtcclxuICAgICAgICB0aGlzLmluaXRpYWxMYXlvdXQoaW5pdGlhbFVuY29uc3RyYWluZWRJdGVyYXRpb25zLCB4LCB5KTtcclxuICAgICAgICBpZiAoY3VyQ29uc3RyYWludHMubGVuZ3RoID4gMClcclxuICAgICAgICAgICAgdGhpcy5fZGVzY2VudC5wcm9qZWN0ID0gbmV3IHJlY3RhbmdsZV8xLlByb2plY3Rpb24odGhpcy5fbm9kZXMsIHRoaXMuX2dyb3VwcywgdGhpcy5fcm9vdEdyb3VwLCBjdXJDb25zdHJhaW50cykucHJvamVjdEZ1bmN0aW9ucygpO1xyXG4gICAgICAgIHRoaXMuX2Rlc2NlbnQucnVuKGluaXRpYWxVc2VyQ29uc3RyYWludEl0ZXJhdGlvbnMpO1xyXG4gICAgICAgIHRoaXMuc2VwYXJhdGVPdmVybGFwcGluZ0NvbXBvbmVudHModywgaCwgY2VudGVyR3JhcGgpO1xyXG4gICAgICAgIHRoaXMuYXZvaWRPdmVybGFwcyhhbyk7XHJcbiAgICAgICAgaWYgKGFvKSB7XHJcbiAgICAgICAgICAgIHRoaXMuX25vZGVzLmZvckVhY2goZnVuY3Rpb24gKHYsIGkpIHsgdi54ID0geFtpXSwgdi55ID0geVtpXTsgfSk7XHJcbiAgICAgICAgICAgIHRoaXMuX2Rlc2NlbnQucHJvamVjdCA9IG5ldyByZWN0YW5nbGVfMS5Qcm9qZWN0aW9uKHRoaXMuX25vZGVzLCB0aGlzLl9ncm91cHMsIHRoaXMuX3Jvb3RHcm91cCwgY3VyQ29uc3RyYWludHMsIHRydWUpLnByb2plY3RGdW5jdGlvbnMoKTtcclxuICAgICAgICAgICAgdGhpcy5fbm9kZXMuZm9yRWFjaChmdW5jdGlvbiAodiwgaSkgeyB4W2ldID0gdi54LCB5W2ldID0gdi55OyB9KTtcclxuICAgICAgICB9XHJcbiAgICAgICAgdGhpcy5fZGVzY2VudC5HID0gRztcclxuICAgICAgICB0aGlzLl9kZXNjZW50LnJ1bihpbml0aWFsQWxsQ29uc3RyYWludHNJdGVyYXRpb25zKTtcclxuICAgICAgICBpZiAoZ3JpZFNuYXBJdGVyYXRpb25zKSB7XHJcbiAgICAgICAgICAgIHRoaXMuX2Rlc2NlbnQuc25hcFN0cmVuZ3RoID0gMTAwMDtcclxuICAgICAgICAgICAgdGhpcy5fZGVzY2VudC5zbmFwR3JpZFNpemUgPSB0aGlzLl9ub2Rlc1swXS53aWR0aDtcclxuICAgICAgICAgICAgdGhpcy5fZGVzY2VudC5udW1HcmlkU25hcE5vZGVzID0gbjtcclxuICAgICAgICAgICAgdGhpcy5fZGVzY2VudC5zY2FsZVNuYXBCeU1heEggPSBuICE9IE47XHJcbiAgICAgICAgICAgIHZhciBHMCA9IGRlc2NlbnRfMS5EZXNjZW50LmNyZWF0ZVNxdWFyZU1hdHJpeChOLCBmdW5jdGlvbiAoaSwgaikge1xyXG4gICAgICAgICAgICAgICAgaWYgKGkgPj0gbiB8fCBqID49IG4pXHJcbiAgICAgICAgICAgICAgICAgICAgcmV0dXJuIEdbaV1bal07XHJcbiAgICAgICAgICAgICAgICByZXR1cm4gMDtcclxuICAgICAgICAgICAgfSk7XHJcbiAgICAgICAgICAgIHRoaXMuX2Rlc2NlbnQuRyA9IEcwO1xyXG4gICAgICAgICAgICB0aGlzLl9kZXNjZW50LnJ1bihncmlkU25hcEl0ZXJhdGlvbnMpO1xyXG4gICAgICAgIH1cclxuICAgICAgICB0aGlzLnVwZGF0ZU5vZGVQb3NpdGlvbnMoKTtcclxuICAgICAgICB0aGlzLnNlcGFyYXRlT3ZlcmxhcHBpbmdDb21wb25lbnRzKHcsIGgsIGNlbnRlckdyYXBoKTtcclxuICAgICAgICByZXR1cm4ga2VlcFJ1bm5pbmcgPyB0aGlzLnJlc3VtZSgpIDogdGhpcztcclxuICAgIH07XHJcbiAgICBMYXlvdXQucHJvdG90eXBlLmluaXRpYWxMYXlvdXQgPSBmdW5jdGlvbiAoaXRlcmF0aW9ucywgeCwgeSkge1xyXG4gICAgICAgIGlmICh0aGlzLl9ncm91cHMubGVuZ3RoID4gMCAmJiBpdGVyYXRpb25zID4gMCkge1xyXG4gICAgICAgICAgICB2YXIgbiA9IHRoaXMuX25vZGVzLmxlbmd0aDtcclxuICAgICAgICAgICAgdmFyIGVkZ2VzID0gdGhpcy5fbGlua3MubWFwKGZ1bmN0aW9uIChlKSB7IHJldHVybiAoeyBzb3VyY2U6IGUuc291cmNlLmluZGV4LCB0YXJnZXQ6IGUudGFyZ2V0LmluZGV4IH0pOyB9KTtcclxuICAgICAgICAgICAgdmFyIHZzID0gdGhpcy5fbm9kZXMubWFwKGZ1bmN0aW9uICh2KSB7IHJldHVybiAoeyBpbmRleDogdi5pbmRleCB9KTsgfSk7XHJcbiAgICAgICAgICAgIHRoaXMuX2dyb3Vwcy5mb3JFYWNoKGZ1bmN0aW9uIChnLCBpKSB7XHJcbiAgICAgICAgICAgICAgICB2cy5wdXNoKHsgaW5kZXg6IGcuaW5kZXggPSBuICsgaSB9KTtcclxuICAgICAgICAgICAgfSk7XHJcbiAgICAgICAgICAgIHRoaXMuX2dyb3Vwcy5mb3JFYWNoKGZ1bmN0aW9uIChnLCBpKSB7XHJcbiAgICAgICAgICAgICAgICBpZiAodHlwZW9mIGcubGVhdmVzICE9PSAndW5kZWZpbmVkJylcclxuICAgICAgICAgICAgICAgICAgICBnLmxlYXZlcy5mb3JFYWNoKGZ1bmN0aW9uICh2KSB7IHJldHVybiBlZGdlcy5wdXNoKHsgc291cmNlOiBnLmluZGV4LCB0YXJnZXQ6IHYuaW5kZXggfSk7IH0pO1xyXG4gICAgICAgICAgICAgICAgaWYgKHR5cGVvZiBnLmdyb3VwcyAhPT0gJ3VuZGVmaW5lZCcpXHJcbiAgICAgICAgICAgICAgICAgICAgZy5ncm91cHMuZm9yRWFjaChmdW5jdGlvbiAoZ2cpIHsgcmV0dXJuIGVkZ2VzLnB1c2goeyBzb3VyY2U6IGcuaW5kZXgsIHRhcmdldDogZ2cuaW5kZXggfSk7IH0pO1xyXG4gICAgICAgICAgICB9KTtcclxuICAgICAgICAgICAgbmV3IExheW91dCgpXHJcbiAgICAgICAgICAgICAgICAuc2l6ZSh0aGlzLnNpemUoKSlcclxuICAgICAgICAgICAgICAgIC5ub2Rlcyh2cylcclxuICAgICAgICAgICAgICAgIC5saW5rcyhlZGdlcylcclxuICAgICAgICAgICAgICAgIC5hdm9pZE92ZXJsYXBzKGZhbHNlKVxyXG4gICAgICAgICAgICAgICAgLmxpbmtEaXN0YW5jZSh0aGlzLmxpbmtEaXN0YW5jZSgpKVxyXG4gICAgICAgICAgICAgICAgLnN5bW1ldHJpY0RpZmZMaW5rTGVuZ3Rocyg1KVxyXG4gICAgICAgICAgICAgICAgLmNvbnZlcmdlbmNlVGhyZXNob2xkKDFlLTQpXHJcbiAgICAgICAgICAgICAgICAuc3RhcnQoaXRlcmF0aW9ucywgMCwgMCwgMCwgZmFsc2UpO1xyXG4gICAgICAgICAgICB0aGlzLl9ub2Rlcy5mb3JFYWNoKGZ1bmN0aW9uICh2KSB7XHJcbiAgICAgICAgICAgICAgICB4W3YuaW5kZXhdID0gdnNbdi5pbmRleF0ueDtcclxuICAgICAgICAgICAgICAgIHlbdi5pbmRleF0gPSB2c1t2LmluZGV4XS55O1xyXG4gICAgICAgICAgICB9KTtcclxuICAgICAgICB9XHJcbiAgICAgICAgZWxzZSB7XHJcbiAgICAgICAgICAgIHRoaXMuX2Rlc2NlbnQucnVuKGl0ZXJhdGlvbnMpO1xyXG4gICAgICAgIH1cclxuICAgIH07XHJcbiAgICBMYXlvdXQucHJvdG90eXBlLnNlcGFyYXRlT3ZlcmxhcHBpbmdDb21wb25lbnRzID0gZnVuY3Rpb24gKHdpZHRoLCBoZWlnaHQsIGNlbnRlckdyYXBoKSB7XHJcbiAgICAgICAgdmFyIF90aGlzID0gdGhpcztcclxuICAgICAgICBpZiAoY2VudGVyR3JhcGggPT09IHZvaWQgMCkgeyBjZW50ZXJHcmFwaCA9IHRydWU7IH1cclxuICAgICAgICBpZiAoIXRoaXMuX2Rpc3RhbmNlTWF0cml4ICYmIHRoaXMuX2hhbmRsZURpc2Nvbm5lY3RlZCkge1xyXG4gICAgICAgICAgICB2YXIgeF8xID0gdGhpcy5fZGVzY2VudC54WzBdLCB5XzEgPSB0aGlzLl9kZXNjZW50LnhbMV07XHJcbiAgICAgICAgICAgIHRoaXMuX25vZGVzLmZvckVhY2goZnVuY3Rpb24gKHYsIGkpIHsgdi54ID0geF8xW2ldLCB2LnkgPSB5XzFbaV07IH0pO1xyXG4gICAgICAgICAgICB2YXIgZ3JhcGhzID0gaGFuZGxlZGlzY29ubmVjdGVkXzEuc2VwYXJhdGVHcmFwaHModGhpcy5fbm9kZXMsIHRoaXMuX2xpbmtzKTtcclxuICAgICAgICAgICAgaGFuZGxlZGlzY29ubmVjdGVkXzEuYXBwbHlQYWNraW5nKGdyYXBocywgd2lkdGgsIGhlaWdodCwgdGhpcy5fZGVmYXVsdE5vZGVTaXplLCAxLCBjZW50ZXJHcmFwaCk7XHJcbiAgICAgICAgICAgIHRoaXMuX25vZGVzLmZvckVhY2goZnVuY3Rpb24gKHYsIGkpIHtcclxuICAgICAgICAgICAgICAgIF90aGlzLl9kZXNjZW50LnhbMF1baV0gPSB2LngsIF90aGlzLl9kZXNjZW50LnhbMV1baV0gPSB2Lnk7XHJcbiAgICAgICAgICAgICAgICBpZiAodi5ib3VuZHMpIHtcclxuICAgICAgICAgICAgICAgICAgICB2LmJvdW5kcy5zZXRYQ2VudHJlKHYueCk7XHJcbiAgICAgICAgICAgICAgICAgICAgdi5ib3VuZHMuc2V0WUNlbnRyZSh2LnkpO1xyXG4gICAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICB9KTtcclxuICAgICAgICB9XHJcbiAgICB9O1xyXG4gICAgTGF5b3V0LnByb3RvdHlwZS5yZXN1bWUgPSBmdW5jdGlvbiAoKSB7XHJcbiAgICAgICAgcmV0dXJuIHRoaXMuYWxwaGEoMC4xKTtcclxuICAgIH07XHJcbiAgICBMYXlvdXQucHJvdG90eXBlLnN0b3AgPSBmdW5jdGlvbiAoKSB7XHJcbiAgICAgICAgcmV0dXJuIHRoaXMuYWxwaGEoMCk7XHJcbiAgICB9O1xyXG4gICAgTGF5b3V0LnByb3RvdHlwZS5wcmVwYXJlRWRnZVJvdXRpbmcgPSBmdW5jdGlvbiAobm9kZU1hcmdpbikge1xyXG4gICAgICAgIGlmIChub2RlTWFyZ2luID09PSB2b2lkIDApIHsgbm9kZU1hcmdpbiA9IDA7IH1cclxuICAgICAgICB0aGlzLl92aXNpYmlsaXR5R3JhcGggPSBuZXcgZ2VvbV8xLlRhbmdlbnRWaXNpYmlsaXR5R3JhcGgodGhpcy5fbm9kZXMubWFwKGZ1bmN0aW9uICh2KSB7XHJcbiAgICAgICAgICAgIHJldHVybiB2LmJvdW5kcy5pbmZsYXRlKC1ub2RlTWFyZ2luKS52ZXJ0aWNlcygpO1xyXG4gICAgICAgIH0pKTtcclxuICAgIH07XHJcbiAgICBMYXlvdXQucHJvdG90eXBlLnJvdXRlRWRnZSA9IGZ1bmN0aW9uIChlZGdlLCBhaCwgZHJhdykge1xyXG4gICAgICAgIGlmIChhaCA9PT0gdm9pZCAwKSB7IGFoID0gNTsgfVxyXG4gICAgICAgIHZhciBsaW5lRGF0YSA9IFtdO1xyXG4gICAgICAgIHZhciB2ZzIgPSBuZXcgZ2VvbV8xLlRhbmdlbnRWaXNpYmlsaXR5R3JhcGgodGhpcy5fdmlzaWJpbGl0eUdyYXBoLlAsIHsgVjogdGhpcy5fdmlzaWJpbGl0eUdyYXBoLlYsIEU6IHRoaXMuX3Zpc2liaWxpdHlHcmFwaC5FIH0pLCBwb3J0MSA9IHsgeDogZWRnZS5zb3VyY2UueCwgeTogZWRnZS5zb3VyY2UueSB9LCBwb3J0MiA9IHsgeDogZWRnZS50YXJnZXQueCwgeTogZWRnZS50YXJnZXQueSB9LCBzdGFydCA9IHZnMi5hZGRQb2ludChwb3J0MSwgZWRnZS5zb3VyY2UuaW5kZXgpLCBlbmQgPSB2ZzIuYWRkUG9pbnQocG9ydDIsIGVkZ2UudGFyZ2V0LmluZGV4KTtcclxuICAgICAgICB2ZzIuYWRkRWRnZUlmVmlzaWJsZShwb3J0MSwgcG9ydDIsIGVkZ2Uuc291cmNlLmluZGV4LCBlZGdlLnRhcmdldC5pbmRleCk7XHJcbiAgICAgICAgaWYgKHR5cGVvZiBkcmF3ICE9PSAndW5kZWZpbmVkJykge1xyXG4gICAgICAgICAgICBkcmF3KHZnMik7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIHZhciBzb3VyY2VJbmQgPSBmdW5jdGlvbiAoZSkgeyByZXR1cm4gZS5zb3VyY2UuaWQ7IH0sIHRhcmdldEluZCA9IGZ1bmN0aW9uIChlKSB7IHJldHVybiBlLnRhcmdldC5pZDsgfSwgbGVuZ3RoID0gZnVuY3Rpb24gKGUpIHsgcmV0dXJuIGUubGVuZ3RoKCk7IH0sIHNwQ2FsYyA9IG5ldyBzaG9ydGVzdHBhdGhzXzEuQ2FsY3VsYXRvcih2ZzIuVi5sZW5ndGgsIHZnMi5FLCBzb3VyY2VJbmQsIHRhcmdldEluZCwgbGVuZ3RoKSwgc2hvcnRlc3RQYXRoID0gc3BDYWxjLlBhdGhGcm9tTm9kZVRvTm9kZShzdGFydC5pZCwgZW5kLmlkKTtcclxuICAgICAgICBpZiAoc2hvcnRlc3RQYXRoLmxlbmd0aCA9PT0gMSB8fCBzaG9ydGVzdFBhdGgubGVuZ3RoID09PSB2ZzIuVi5sZW5ndGgpIHtcclxuICAgICAgICAgICAgdmFyIHJvdXRlID0gcmVjdGFuZ2xlXzEubWFrZUVkZ2VCZXR3ZWVuKGVkZ2Uuc291cmNlLmlubmVyQm91bmRzLCBlZGdlLnRhcmdldC5pbm5lckJvdW5kcywgYWgpO1xyXG4gICAgICAgICAgICBsaW5lRGF0YSA9IFtyb3V0ZS5zb3VyY2VJbnRlcnNlY3Rpb24sIHJvdXRlLmFycm93U3RhcnRdO1xyXG4gICAgICAgIH1cclxuICAgICAgICBlbHNlIHtcclxuICAgICAgICAgICAgdmFyIG4gPSBzaG9ydGVzdFBhdGgubGVuZ3RoIC0gMiwgcCA9IHZnMi5WW3Nob3J0ZXN0UGF0aFtuXV0ucCwgcSA9IHZnMi5WW3Nob3J0ZXN0UGF0aFswXV0ucCwgbGluZURhdGEgPSBbZWRnZS5zb3VyY2UuaW5uZXJCb3VuZHMucmF5SW50ZXJzZWN0aW9uKHAueCwgcC55KV07XHJcbiAgICAgICAgICAgIGZvciAodmFyIGkgPSBuOyBpID49IDA7IC0taSlcclxuICAgICAgICAgICAgICAgIGxpbmVEYXRhLnB1c2godmcyLlZbc2hvcnRlc3RQYXRoW2ldXS5wKTtcclxuICAgICAgICAgICAgbGluZURhdGEucHVzaChyZWN0YW5nbGVfMS5tYWtlRWRnZVRvKHEsIGVkZ2UudGFyZ2V0LmlubmVyQm91bmRzLCBhaCkpO1xyXG4gICAgICAgIH1cclxuICAgICAgICByZXR1cm4gbGluZURhdGE7XHJcbiAgICB9O1xyXG4gICAgTGF5b3V0LmdldFNvdXJjZUluZGV4ID0gZnVuY3Rpb24gKGUpIHtcclxuICAgICAgICByZXR1cm4gdHlwZW9mIGUuc291cmNlID09PSAnbnVtYmVyJyA/IGUuc291cmNlIDogZS5zb3VyY2UuaW5kZXg7XHJcbiAgICB9O1xyXG4gICAgTGF5b3V0LmdldFRhcmdldEluZGV4ID0gZnVuY3Rpb24gKGUpIHtcclxuICAgICAgICByZXR1cm4gdHlwZW9mIGUudGFyZ2V0ID09PSAnbnVtYmVyJyA/IGUudGFyZ2V0IDogZS50YXJnZXQuaW5kZXg7XHJcbiAgICB9O1xyXG4gICAgTGF5b3V0LmxpbmtJZCA9IGZ1bmN0aW9uIChlKSB7XHJcbiAgICAgICAgcmV0dXJuIExheW91dC5nZXRTb3VyY2VJbmRleChlKSArIFwiLVwiICsgTGF5b3V0LmdldFRhcmdldEluZGV4KGUpO1xyXG4gICAgfTtcclxuICAgIExheW91dC5kcmFnU3RhcnQgPSBmdW5jdGlvbiAoZCkge1xyXG4gICAgICAgIGlmIChpc0dyb3VwKGQpKSB7XHJcbiAgICAgICAgICAgIExheW91dC5zdG9yZU9mZnNldChkLCBMYXlvdXQuZHJhZ09yaWdpbihkKSk7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIGVsc2Uge1xyXG4gICAgICAgICAgICBMYXlvdXQuc3RvcE5vZGUoZCk7XHJcbiAgICAgICAgICAgIGQuZml4ZWQgfD0gMjtcclxuICAgICAgICB9XHJcbiAgICB9O1xyXG4gICAgTGF5b3V0LnN0b3BOb2RlID0gZnVuY3Rpb24gKHYpIHtcclxuICAgICAgICB2LnB4ID0gdi54O1xyXG4gICAgICAgIHYucHkgPSB2Lnk7XHJcbiAgICB9O1xyXG4gICAgTGF5b3V0LnN0b3JlT2Zmc2V0ID0gZnVuY3Rpb24gKGQsIG9yaWdpbikge1xyXG4gICAgICAgIGlmICh0eXBlb2YgZC5sZWF2ZXMgIT09ICd1bmRlZmluZWQnKSB7XHJcbiAgICAgICAgICAgIGQubGVhdmVzLmZvckVhY2goZnVuY3Rpb24gKHYpIHtcclxuICAgICAgICAgICAgICAgIHYuZml4ZWQgfD0gMjtcclxuICAgICAgICAgICAgICAgIExheW91dC5zdG9wTm9kZSh2KTtcclxuICAgICAgICAgICAgICAgIHYuX2RyYWdHcm91cE9mZnNldFggPSB2LnggLSBvcmlnaW4ueDtcclxuICAgICAgICAgICAgICAgIHYuX2RyYWdHcm91cE9mZnNldFkgPSB2LnkgLSBvcmlnaW4ueTtcclxuICAgICAgICAgICAgfSk7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIGlmICh0eXBlb2YgZC5ncm91cHMgIT09ICd1bmRlZmluZWQnKSB7XHJcbiAgICAgICAgICAgIGQuZ3JvdXBzLmZvckVhY2goZnVuY3Rpb24gKGcpIHsgcmV0dXJuIExheW91dC5zdG9yZU9mZnNldChnLCBvcmlnaW4pOyB9KTtcclxuICAgICAgICB9XHJcbiAgICB9O1xyXG4gICAgTGF5b3V0LmRyYWdPcmlnaW4gPSBmdW5jdGlvbiAoZCkge1xyXG4gICAgICAgIGlmIChpc0dyb3VwKGQpKSB7XHJcbiAgICAgICAgICAgIHJldHVybiB7XHJcbiAgICAgICAgICAgICAgICB4OiBkLmJvdW5kcy5jeCgpLFxyXG4gICAgICAgICAgICAgICAgeTogZC5ib3VuZHMuY3koKVxyXG4gICAgICAgICAgICB9O1xyXG4gICAgICAgIH1cclxuICAgICAgICBlbHNlIHtcclxuICAgICAgICAgICAgcmV0dXJuIGQ7XHJcbiAgICAgICAgfVxyXG4gICAgfTtcclxuICAgIExheW91dC5kcmFnID0gZnVuY3Rpb24gKGQsIHBvc2l0aW9uKSB7XHJcbiAgICAgICAgaWYgKGlzR3JvdXAoZCkpIHtcclxuICAgICAgICAgICAgaWYgKHR5cGVvZiBkLmxlYXZlcyAhPT0gJ3VuZGVmaW5lZCcpIHtcclxuICAgICAgICAgICAgICAgIGQubGVhdmVzLmZvckVhY2goZnVuY3Rpb24gKHYpIHtcclxuICAgICAgICAgICAgICAgICAgICBkLmJvdW5kcy5zZXRYQ2VudHJlKHBvc2l0aW9uLngpO1xyXG4gICAgICAgICAgICAgICAgICAgIGQuYm91bmRzLnNldFlDZW50cmUocG9zaXRpb24ueSk7XHJcbiAgICAgICAgICAgICAgICAgICAgdi5weCA9IHYuX2RyYWdHcm91cE9mZnNldFggKyBwb3NpdGlvbi54O1xyXG4gICAgICAgICAgICAgICAgICAgIHYucHkgPSB2Ll9kcmFnR3JvdXBPZmZzZXRZICsgcG9zaXRpb24ueTtcclxuICAgICAgICAgICAgICAgIH0pO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgICAgIGlmICh0eXBlb2YgZC5ncm91cHMgIT09ICd1bmRlZmluZWQnKSB7XHJcbiAgICAgICAgICAgICAgICBkLmdyb3Vwcy5mb3JFYWNoKGZ1bmN0aW9uIChnKSB7IHJldHVybiBMYXlvdXQuZHJhZyhnLCBwb3NpdGlvbik7IH0pO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgfVxyXG4gICAgICAgIGVsc2Uge1xyXG4gICAgICAgICAgICBkLnB4ID0gcG9zaXRpb24ueDtcclxuICAgICAgICAgICAgZC5weSA9IHBvc2l0aW9uLnk7XHJcbiAgICAgICAgfVxyXG4gICAgfTtcclxuICAgIExheW91dC5kcmFnRW5kID0gZnVuY3Rpb24gKGQpIHtcclxuICAgICAgICBpZiAoaXNHcm91cChkKSkge1xyXG4gICAgICAgICAgICBpZiAodHlwZW9mIGQubGVhdmVzICE9PSAndW5kZWZpbmVkJykge1xyXG4gICAgICAgICAgICAgICAgZC5sZWF2ZXMuZm9yRWFjaChmdW5jdGlvbiAodikge1xyXG4gICAgICAgICAgICAgICAgICAgIExheW91dC5kcmFnRW5kKHYpO1xyXG4gICAgICAgICAgICAgICAgICAgIGRlbGV0ZSB2Ll9kcmFnR3JvdXBPZmZzZXRYO1xyXG4gICAgICAgICAgICAgICAgICAgIGRlbGV0ZSB2Ll9kcmFnR3JvdXBPZmZzZXRZO1xyXG4gICAgICAgICAgICAgICAgfSk7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgaWYgKHR5cGVvZiBkLmdyb3VwcyAhPT0gJ3VuZGVmaW5lZCcpIHtcclxuICAgICAgICAgICAgICAgIGQuZ3JvdXBzLmZvckVhY2goTGF5b3V0LmRyYWdFbmQpO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgfVxyXG4gICAgICAgIGVsc2Uge1xyXG4gICAgICAgICAgICBkLmZpeGVkICY9IH42O1xyXG4gICAgICAgIH1cclxuICAgIH07XHJcbiAgICBMYXlvdXQubW91c2VPdmVyID0gZnVuY3Rpb24gKGQpIHtcclxuICAgICAgICBkLmZpeGVkIHw9IDQ7XHJcbiAgICAgICAgZC5weCA9IGQueCwgZC5weSA9IGQueTtcclxuICAgIH07XHJcbiAgICBMYXlvdXQubW91c2VPdXQgPSBmdW5jdGlvbiAoZCkge1xyXG4gICAgICAgIGQuZml4ZWQgJj0gfjQ7XHJcbiAgICB9O1xyXG4gICAgcmV0dXJuIExheW91dDtcclxufSgpKTtcclxuZXhwb3J0cy5MYXlvdXQgPSBMYXlvdXQ7XHJcbi8vIyBzb3VyY2VNYXBwaW5nVVJMPWRhdGE6YXBwbGljYXRpb24vanNvbjtiYXNlNjQsZXlKMlpYSnphVzl1SWpvekxDSm1hV3hsSWpvaWJHRjViM1YwTG1weklpd2ljMjkxY21ObFVtOXZkQ0k2SWlJc0luTnZkWEpqWlhNaU9sc2lMaTR2TGk0dlYyVmlRMjlzWVM5emNtTXZiR0Y1YjNWMExuUnpJbDBzSW01aGJXVnpJanBiWFN3aWJXRndjR2x1WjNNaU9pSTdPMEZCUVVFc2VVTkJRVEJETzBGQlF6RkRMRFpEUVVFclNEdEJRVU12U0N4eFEwRkJhVU03UVVGRGFrTXNlVU5CUVRoRk8wRkJRemxGTEdsRVFVRXdRenRCUVVNeFF5d3JRa0ZCZFVRN1FVRkRka1FzTWtSQlFXbEZPMEZCVHpkRUxFbEJRVmtzVTBGQk9FSTdRVUZCTVVNc1YwRkJXU3hUUVVGVE8wbEJRVWNzTWtOQlFVc3NRMEZCUVR0SlFVRkZMSGxEUVVGSkxFTkJRVUU3U1VGQlJTeDFRMEZCUnl4RFFVRkJPMEZCUVVNc1EwRkJReXhGUVVFNVFpeFRRVUZUTEVkQlFWUXNhVUpCUVZNc1MwRkJWQ3hwUWtGQlV5eFJRVUZ4UWp0QlFVRkJMRU5CUVVNN1FVRXJRek5ETEZOQlFWTXNUMEZCVHl4RFFVRkRMRU5CUVUwN1NVRkRia0lzVDBGQlR5eFBRVUZQTEVOQlFVTXNRMEZCUXl4TlFVRk5MRXRCUVVzc1YwRkJWeXhKUVVGSkxFOUJRVThzUTBGQlF5eERRVUZETEUxQlFVMHNTMEZCU3l4WFFVRlhMRU5CUVVNN1FVRkRPVVVzUTBGQlF6dEJRWGRDUkR0SlFVRkJPMUZCUVVFc2FVSkJkWGxDUXp0UlFYUjVRbGNzWjBKQlFWY3NSMEZCUnl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF6dFJRVU55UWl4clFrRkJZU3hIUVVGNVF5eEZRVUZGTEVOQlFVTTdVVUZEZWtRc2NVSkJRV2RDTEVkQlFWY3NSVUZCUlN4RFFVRkRPMUZCUXpsQ0xEQkNRVUZ4UWl4SFFVRkhMRWxCUVVrc1EwRkJRenRSUVVNM1FpeGpRVUZUTEVkQlFVY3NTVUZCU1N4RFFVRkRPMUZCUTJwQ0xHMUNRVUZqTEVkQlFVY3NTMEZCU3l4RFFVRkRPMUZCUTNaQ0xIZENRVUZ0UWl4SFFVRkhMRWxCUVVrc1EwRkJRenRSUVVjelFpeGhRVUZSTEVkQlFVY3NTMEZCU3l4RFFVRkRPMUZCUTJwQ0xGZEJRVTBzUjBGQlJ5eEZRVUZGTEVOQlFVTTdVVUZEV2l4WlFVRlBMRWRCUVVjc1JVRkJSU3hEUVVGRE8xRkJRMklzWlVGQlZTeEhRVUZITEVsQlFVa3NRMEZCUXp0UlFVTnNRaXhYUVVGTkxFZEJRVEJDTEVWQlFVVXNRMEZCUXp0UlFVTnVReXhwUWtGQldTeEhRVUZITEVWQlFVVXNRMEZCUXp0UlFVTnNRaXh2UWtGQlpTeEhRVUZITEVsQlFVa3NRMEZCUXp0UlFVTjJRaXhoUVVGUkxFZEJRVmtzU1VGQlNTeERRVUZETzFGQlEzcENMRFpDUVVGM1FpeEhRVUZITEVsQlFVa3NRMEZCUXp0UlFVTm9ReXhsUVVGVkxFZEJRVWNzU1VGQlNTeERRVUZETzFGQlEyeENMSEZDUVVGblFpeEhRVUZITEVsQlFVa3NRMEZCUXp0UlFVTjRRaXh6UWtGQmFVSXNSMEZCUnl4SlFVRkpMRU5CUVVNN1VVRkhka0lzVlVGQlN5eEhRVUZITEVsQlFVa3NRMEZCUXp0UlFXdFdka0lzYVVKQlFWa3NSMEZCTWtJN1dVRkRia01zWTBGQll5eEZRVUZGTEUxQlFVMHNRMEZCUXl4alFVRmpPMWxCUTNKRExHTkJRV01zUlVGQlJTeE5RVUZOTEVOQlFVTXNZMEZCWXp0WlFVTnlReXhUUVVGVExFVkJRVVVzVFVGQlRTeERRVUZETEdGQlFXRTdXVUZETDBJc1QwRkJUeXhGUVVGRkxGVkJRVUVzUTBGQlF5eEpRVUZKTEU5QlFVRXNUMEZCVHl4TFFVRkpMRU5CUVVNc1UwRkJVeXhMUVVGTExGVkJRVlVzUTBGQlF5eERRVUZETEVOQlFVTXNTMEZCU1N4RFFVRkRMRk5CUVZNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RlFVRTFSQ3hEUVVFMFJEdFRRVU0zUlN4RFFVRkRPMGxCZDJKT0xFTkJRVU03U1VFemQwSlZMRzFDUVVGRkxFZEJRVlFzVlVGQlZTeERRVUZ4UWl4RlFVRkZMRkZCUVdsRE8xRkJSVGxFTEVsQlFVa3NRMEZCUXl4SlFVRkpMRU5CUVVNc1MwRkJTenRaUVVGRkxFbEJRVWtzUTBGQlF5eExRVUZMTEVkQlFVY3NSVUZCUlN4RFFVRkRPMUZCUTJwRExFbEJRVWtzVDBGQlR5eERRVUZETEV0QlFVc3NVVUZCVVN4RlFVRkZPMWxCUTNaQ0xFbEJRVWtzUTBGQlF5eExRVUZMTEVOQlFVTXNVMEZCVXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFZEJRVWNzVVVGQlVTeERRVUZETzFOQlEzWkRPMkZCUVUwN1dVRkRTQ3hKUVVGSkxFTkJRVU1zUzBGQlN5eERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRkZCUVZFc1EwRkJRenRUUVVNMVFqdFJRVU5FTEU5QlFVOHNTVUZCU1N4RFFVRkRPMGxCUTJoQ0xFTkJRVU03U1VGSlV5eDNRa0ZCVHl4SFFVRnFRaXhWUVVGclFpeERRVUZSTzFGQlEzUkNMRWxCUVVrc1NVRkJTU3hEUVVGRExFdEJRVXNzU1VGQlNTeFBRVUZQTEVsQlFVa3NRMEZCUXl4TFFVRkxMRU5CUVVNc1EwRkJReXhEUVVGRExFbEJRVWtzUTBGQlF5eExRVUZMTEZkQlFWY3NSVUZCUlR0WlFVTjZSQ3hKUVVGSkxFTkJRVU1zUzBGQlN5eERRVUZETEVOQlFVTXNRMEZCUXl4SlFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFRRVU42UWp0SlFVTk1MRU5CUVVNN1NVRkxVeXh4UWtGQlNTeEhRVUZrTzFGQlEwa3NUMEZCVHl4RFFVRkRMRWxCUVVrc1EwRkJReXhKUVVGSkxFVkJRVVU3V1VGQlF5eERRVUZETzBsQlEzcENMRU5CUVVNN1NVRkxVeXh4UWtGQlNTeEhRVUZrTzFGQlEwa3NTVUZCU1N4SlFVRkpMRU5CUVVNc1RVRkJUU3hIUVVGSExFbEJRVWtzUTBGQlF5eFZRVUZWTEVWQlFVVTdXVUZETDBJc1NVRkJTU3hEUVVGRExGRkJRVkVzUjBGQlJ5eExRVUZMTEVOQlFVTTdXVUZEZEVJc1NVRkJTU3hEUVVGRExFOUJRVThzUTBGQlF5eEZRVUZGTEVsQlFVa3NSVUZCUlN4VFFVRlRMRU5CUVVNc1IwRkJSeXhGUVVGRkxFdEJRVXNzUlVGQlJTeEpRVUZKTEVOQlFVTXNUVUZCVFN4SFFVRkhMRU5CUVVNc1JVRkJSU3hOUVVGTkxFVkJRVVVzU1VGQlNTeERRVUZETEZkQlFWY3NSVUZCUlN4RFFVRkRMRU5CUVVNN1dVRkRlRVlzVDBGQlR5eEpRVUZKTEVOQlFVTTdVMEZEWmp0UlFVTkVMRWxCUVUwc1EwRkJReXhIUVVGSExFbEJRVWtzUTBGQlF5eE5RVUZOTEVOQlFVTXNUVUZCVFN4RlFVTjBRaXhEUVVGRExFZEJRVWNzU1VGQlNTeERRVUZETEUxQlFVMHNRMEZCUXl4TlFVRk5MRU5CUVVNN1VVRkROMElzU1VGQlNTeERRVUZETEVWQlFVVXNRMEZCUXl4RFFVRkRPMUZCUlZRc1NVRkJTU3hEUVVGRExGRkJRVkVzUTBGQlF5eExRVUZMTEVOQlFVTXNTMEZCU3l4RlFVRkZMRU5CUVVNN1VVRkROVUlzUzBGQlN5eERRVUZETEVkQlFVY3NRMEZCUXl4RlFVRkZMRU5CUVVNc1IwRkJSeXhEUVVGRExFVkJRVVVzUlVGQlJTeERRVUZETEVWQlFVVTdXVUZEY0VJc1EwRkJReXhIUVVGSExFbEJRVWtzUTBGQlF5eE5RVUZOTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1dVRkRia0lzU1VGQlNTeERRVUZETEVOQlFVTXNTMEZCU3l4RlFVRkZPMmRDUVVOVUxFbEJRVWtzVDBGQlR5eERRVUZETEVOQlFVTXNSVUZCUlN4TFFVRkxMRmRCUVZjc1NVRkJTU3hQUVVGUExFTkJRVU1zUTBGQlF5eEZRVUZGTEV0QlFVc3NWMEZCVnl4RlFVRkZPMjlDUVVNMVJDeERRVUZETEVOQlFVTXNSVUZCUlN4SFFVRkhMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03YjBKQlExZ3NRMEZCUXl4RFFVRkRMRVZCUVVVc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzJsQ1FVTmtPMmRDUVVORUxFbEJRVWtzUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUVVVc1JVRkJSU3hEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTTdaMEpCUTNKQ0xFbEJRVWtzUTBGQlF5eFJRVUZSTEVOQlFVTXNTMEZCU3l4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTTdZVUZEYWtNN1UwRkRTanRSUVVWRUxFbEJRVWtzUlVGQlJTeEhRVUZITEVsQlFVa3NRMEZCUXl4UlFVRlJMRU5CUVVNc1ZVRkJWU3hGUVVGRkxFTkJRVU03VVVGRmNFTXNTVUZCU1N4RlFVRkZMRXRCUVVzc1EwRkJReXhGUVVGRk8xbEJRMVlzU1VGQlNTeERRVUZETEUxQlFVMHNSMEZCUnl4RFFVRkRMRU5CUVVNN1UwRkRia0k3WVVGQlRTeEpRVUZKTEU5QlFVOHNTVUZCU1N4RFFVRkRMRmRCUVZjc1MwRkJTeXhYUVVGWExFVkJRVVU3V1VGRGFFUXNTVUZCU1N4RFFVRkRMRTFCUVUwc1IwRkJSeXhGUVVGRkxFTkJRVU03VTBGRGNFSTdVVUZEUkN4SlFVRkpMRU5CUVVNc1YwRkJWeXhIUVVGSExFVkJRVVVzUTBGQlF6dFJRVVYwUWl4SlFVRkpMRU5CUVVNc2JVSkJRVzFDTEVWQlFVVXNRMEZCUXp0UlFVVXpRaXhKUVVGSkxFTkJRVU1zVDBGQlR5eERRVUZETEVWQlFVVXNTVUZCU1N4RlFVRkZMRk5CUVZNc1EwRkJReXhKUVVGSkxFVkJRVVVzUzBGQlN5eEZRVUZGTEVsQlFVa3NRMEZCUXl4TlFVRk5MRVZCUVVVc1RVRkJUU3hGUVVGRkxFbEJRVWtzUTBGQlF5eFhRVUZYTEVWQlFVVXNRMEZCUXl4RFFVRkRPMUZCUTNKR0xFOUJRVThzUzBGQlN5eERRVUZETzBsQlEycENMRU5CUVVNN1NVRkhUeXh2UTBGQmJVSXNSMEZCTTBJN1VVRkRTU3hKUVVGTkxFTkJRVU1zUjBGQlJ5eEpRVUZKTEVOQlFVTXNVVUZCVVN4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NTVUZCU1N4RFFVRkRMRkZCUVZFc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdVVUZEY2tRc1NVRkJTU3hEUVVGRExFVkJRVVVzUTBGQlF5eEhRVUZITEVsQlFVa3NRMEZCUXl4TlFVRk5MRU5CUVVNc1RVRkJUU3hEUVVGRE8xRkJRemxDTEU5QlFVOHNRMEZCUXl4RlFVRkZMRVZCUVVVN1dVRkRVaXhEUVVGRExFZEJRVWNzU1VGQlNTeERRVUZETEUxQlFVMHNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRaUVVOdVFpeERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFpRVU5ZTEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzFOQlEyUTdTVUZEVEN4RFFVRkRPMGxCVjBRc2MwSkJRVXNzUjBGQlRDeFZRVUZOTEVOQlFVODdVVUZEVkN4SlFVRkpMRU5CUVVNc1EwRkJReXhGUVVGRk8xbEJRMG9zU1VGQlNTeEpRVUZKTEVOQlFVTXNUVUZCVFN4RFFVRkRMRTFCUVUwc1MwRkJTeXhEUVVGRExFbEJRVWtzU1VGQlNTeERRVUZETEUxQlFVMHNRMEZCUXl4TlFVRk5MRWRCUVVjc1EwRkJReXhGUVVGRk8yZENRVWR3UkN4SlFVRkpMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU03WjBKQlExWXNTVUZCU1N4RFFVRkRMRTFCUVUwc1EwRkJReXhQUVVGUExFTkJRVU1zVlVGQlZTeERRVUZETzI5Q1FVTXpRaXhEUVVGRExFZEJRVWNzU1VGQlNTeERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRVZCUVZVc1EwRkJReXhEUVVGRExFMUJRVTBzUlVGQlZTeERRVUZETEVOQlFVTXNUVUZCVFN4RFFVRkRMRU5CUVVNN1owSkJRM2hFTEVOQlFVTXNRMEZCUXl4RFFVRkRPMmRDUVVOSUxFbEJRVWtzUTBGQlF5eE5RVUZOTEVkQlFVY3NTVUZCU1N4TFFVRkxMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF6dG5Ra0ZETjBJc1MwRkJTeXhKUVVGSkxFTkJRVU1zUjBGQlJ5eERRVUZETEVWQlFVVXNRMEZCUXl4SFFVRkhMRU5CUVVNc1JVRkJSU3hGUVVGRkxFTkJRVU1zUlVGQlJUdHZRa0ZEZUVJc1NVRkJTU3hEUVVGRExFMUJRVTBzUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4RlFVRkZMRU5CUVVNN2FVSkJRM1pDTzJGQlEwbzdXVUZEUkN4UFFVRlBMRWxCUVVrc1EwRkJReXhOUVVGTkxFTkJRVU03VTBGRGRFSTdVVUZEUkN4SlFVRkpMRU5CUVVNc1RVRkJUU3hIUVVGSExFTkJRVU1zUTBGQlF6dFJRVU5vUWl4UFFVRlBMRWxCUVVrc1EwRkJRenRKUVVOb1FpeERRVUZETzBsQlUwUXNkVUpCUVUwc1IwRkJUaXhWUVVGUExFTkJRV2RDTzFGQlFYWkNMR2xDUVhWQ1F6dFJRWFJDUnl4SlFVRkpMRU5CUVVNc1EwRkJRenRaUVVGRkxFOUJRVThzU1VGQlNTeERRVUZETEU5QlFVOHNRMEZCUXp0UlFVTTFRaXhKUVVGSkxFTkJRVU1zVDBGQlR5eEhRVUZITEVOQlFVTXNRMEZCUXp0UlFVTnFRaXhKUVVGSkxFTkJRVU1zVlVGQlZTeEhRVUZITEVWQlFVVXNRMEZCUXp0UlFVTnlRaXhKUVVGSkxFTkJRVU1zVDBGQlR5eERRVUZETEU5QlFVOHNRMEZCUXl4VlFVRkJMRU5CUVVNN1dVRkRiRUlzU1VGQlNTeFBRVUZQTEVOQlFVTXNRMEZCUXl4UFFVRlBMRXRCUVVzc1YwRkJWenRuUWtGRGFFTXNRMEZCUXl4RFFVRkRMRTlCUVU4c1IwRkJSeXhEUVVGRExFTkJRVU03V1VGRGJFSXNTVUZCU1N4UFFVRlBMRU5CUVVNc1EwRkJReXhOUVVGTkxFdEJRVXNzVjBGQlZ5eEZRVUZGTzJkQ1FVTnFReXhEUVVGRExFTkJRVU1zVFVGQlRTeERRVUZETEU5QlFVOHNRMEZCUXl4VlFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRE8yOUNRVU5zUWl4SlFVRkpMRTlCUVU4c1EwRkJReXhMUVVGTExGRkJRVkU3ZDBKQlEzSkNMRU5CUVVNc1EwRkJReXhEUVVGRExFMUJRVTBzUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4TFFVRkpMRU5CUVVNc1RVRkJUU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNUVUZCVFN4SFFVRkhMRU5CUVVNc1EwRkJRVHRuUWtGRGFrUXNRMEZCUXl4RFFVRkRMRU5CUVVNN1lVRkRUanRaUVVORUxFbEJRVWtzVDBGQlR5eERRVUZETEVOQlFVTXNUVUZCVFN4TFFVRkxMRmRCUVZjc1JVRkJSVHRuUWtGRGFrTXNRMEZCUXl4RFFVRkRMRTFCUVUwc1EwRkJReXhQUVVGUExFTkJRVU1zVlVGQlF5eEZRVUZGTEVWQlFVVXNRMEZCUXp0dlFrRkRia0lzU1VGQlNTeFBRVUZQTEVWQlFVVXNTMEZCU3l4UlFVRlJPM2RDUVVOMFFpeERRVUZETEVOQlFVTXNRMEZCUXl4TlFVRk5MRU5CUVVNc1EwRkJReXhEUVVGRExFZEJRVWNzUzBGQlNTeERRVUZETEU5QlFVOHNRMEZCUXl4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRExFMUJRVTBzUjBGQlJ5eERRVUZETEVOQlFVRTdaMEpCUTI1RUxFTkJRVU1zUTBGQlF5eERRVUZETzJGQlEwNDdVVUZEVEN4RFFVRkRMRU5CUVVNc1EwRkJRenRSUVVOSUxFbEJRVWtzUTBGQlF5eFZRVUZWTEVOQlFVTXNUVUZCVFN4SFFVRkhMRWxCUVVrc1EwRkJReXhOUVVGTkxFTkJRVU1zVFVGQlRTeERRVUZETEZWQlFVRXNRMEZCUXl4SlFVRkpMRTlCUVVFc1QwRkJUeXhEUVVGRExFTkJRVU1zVFVGQlRTeExRVUZMTEZkQlFWY3NSVUZCTDBJc1EwRkJLMElzUTBGQlF5eERRVUZETzFGQlEyeEdMRWxCUVVrc1EwRkJReXhWUVVGVkxFTkJRVU1zVFVGQlRTeEhRVUZITEVsQlFVa3NRMEZCUXl4UFFVRlBMRU5CUVVNc1RVRkJUU3hEUVVGRExGVkJRVUVzUTBGQlF5eEpRVUZKTEU5QlFVRXNUMEZCVHl4RFFVRkRMRU5CUVVNc1RVRkJUU3hMUVVGTExGZEJRVmNzUlVGQkwwSXNRMEZCSzBJc1EwRkJReXhEUVVGRE8xRkJRMjVHTEU5QlFVOHNTVUZCU1N4RFFVRkRPMGxCUTJoQ0xFTkJRVU03U1VGRlJDeHBRMEZCWjBJc1IwRkJhRUlzVlVGQmFVSXNRMEZCVnp0UlFVTjRRaXhKUVVGSkxFTkJRVU1zUjBGQlJ5eFZRVUZWTEVOQlFVTXNVMEZCVXl4RFFVRkRMRWxCUVVrc1EwRkJReXhOUVVGTkxFVkJRVVVzU1VGQlNTeERRVUZETEUxQlFVMHNSVUZCUlN4SlFVRkpMRU5CUVVNc1dVRkJXU3hGUVVGRkxFbEJRVWtzUTBGQlF5eFZRVUZWTEVOQlFVTXNRMEZCUXp0UlFVTXpSaXhKUVVGSkxFTkJRVU1zVFVGQlRTeERRVUZETEVOQlFVTXNRMEZCUXl4TlFVRk5MRU5CUVVNc1EwRkJRenRSUVVOMFFpeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1VVRkRUQ3hQUVVGUExFbEJRVWtzUTBGQlF6dEpRVU5vUWl4RFFVRkRPMGxCVlVRc09FSkJRV0VzUjBGQllpeFZRVUZqTEVOQlFWYzdVVUZEY2tJc1NVRkJTU3hEUVVGRExGTkJRVk1zUTBGQlF5eE5RVUZOTzFsQlFVVXNUMEZCVHl4SlFVRkpMRU5CUVVNc1kwRkJZeXhEUVVGRE8xRkJRMnhFTEVsQlFVa3NRMEZCUXl4alFVRmpMRWRCUVVjc1EwRkJReXhEUVVGRE8xRkJRM2hDTEU5QlFVOHNTVUZCU1N4RFFVRkRPMGxCUTJoQ0xFTkJRVU03U1VGWlJDeHRRMEZCYTBJc1IwRkJiRUlzVlVGQmJVSXNRMEZCVnp0UlFVTXhRaXhKUVVGSkxFTkJRVU1zVTBGQlV5eERRVUZETEUxQlFVMDdXVUZCUlN4UFFVRlBMRWxCUVVrc1EwRkJReXh0UWtGQmJVSXNRMEZCUXp0UlFVTjJSQ3hKUVVGSkxFTkJRVU1zYlVKQlFXMUNMRWRCUVVjc1EwRkJReXhEUVVGRE8xRkJRemRDTEU5QlFVOHNTVUZCU1N4RFFVRkRPMGxCUTJoQ0xFTkJRVU03U1VGUlJDd3lRa0ZCVlN4SFFVRldMRlZCUVZjc1NVRkJXU3hGUVVGRkxHRkJRWGRETzFGQlF6ZEVMRWxCUVVrc1EwRkJReXhUUVVGVExFTkJRVU1zVFVGQlRUdFpRVUZGTEVsQlFVa3NSMEZCUnl4SFFVRkhMRU5CUVVNN1VVRkRiRU1zU1VGQlNTeERRVUZETEhkQ1FVRjNRaXhIUVVGSE8xbEJRelZDTEVsQlFVa3NSVUZCUlN4SlFVRkpPMWxCUTFZc1owSkJRV2RDTEVWQlFVVXNUMEZCVHl4aFFVRmhMRXRCUVVzc1VVRkJVU3hEUVVGRExFTkJRVU1zUTBGQlF5eGpRVUZqTEU5QlFVOHNZVUZCWVN4RFFVRkJMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eGhRVUZoTzFOQlF6ZEhMRU5CUVVNN1VVRkRSaXhQUVVGUExFbEJRVWtzUTBGQlF6dEpRVU5vUWl4RFFVRkRPMGxCVTBRc2MwSkJRVXNzUjBGQlRDeFZRVUZOTEVOQlFUUkNPMUZCUXpsQ0xFbEJRVWtzUTBGQlF5eFRRVUZUTEVOQlFVTXNUVUZCVFR0WlFVRkZMRTlCUVU4c1NVRkJTU3hEUVVGRExFMUJRVTBzUTBGQlF6dFJRVU14UXl4SlFVRkpMRU5CUVVNc1RVRkJUU3hIUVVGSExFTkJRVU1zUTBGQlF6dFJRVU5vUWl4UFFVRlBMRWxCUVVrc1EwRkJRenRKUVVOb1FpeERRVUZETzBsQlZVUXNORUpCUVZjc1IwRkJXQ3hWUVVGWkxFTkJRV003VVVGRGRFSXNTVUZCU1N4RFFVRkRMRk5CUVZNc1EwRkJReXhOUVVGTk8xbEJRVVVzVDBGQlR5eEpRVUZKTEVOQlFVTXNXVUZCV1N4RFFVRkRPMUZCUTJoRUxFbEJRVWtzUTBGQlF5eFpRVUZaTEVkQlFVY3NRMEZCUXl4RFFVRkRPMUZCUTNSQ0xFOUJRVThzU1VGQlNTeERRVUZETzBsQlEyaENMRU5CUVVNN1NVRlhSQ3dyUWtGQll5eEhRVUZrTEZWQlFXVXNRMEZCVHp0UlFVTnNRaXhKUVVGSkxFTkJRVU1zVTBGQlV5eERRVUZETEUxQlFVMDdXVUZCUlN4UFFVRlBMRWxCUVVrc1EwRkJReXhsUVVGbExFTkJRVU03VVVGRGJrUXNTVUZCU1N4RFFVRkRMR1ZCUVdVc1IwRkJSeXhEUVVGRExFTkJRVU03VVVGRGVrSXNUMEZCVHl4SlFVRkpMRU5CUVVNN1NVRkRhRUlzUTBGQlF6dEpRVlZFTEhGQ1FVRkpMRWRCUVVvc1ZVRkJTeXhEUVVGcFFqdFJRVU5zUWl4SlFVRkpMRU5CUVVNc1EwRkJRenRaUVVGRkxFOUJRVThzU1VGQlNTeERRVUZETEZkQlFWY3NRMEZCUXp0UlFVTm9ReXhKUVVGSkxFTkJRVU1zVjBGQlZ5eEhRVUZITEVOQlFVTXNRMEZCUXp0UlFVTnlRaXhQUVVGUExFbEJRVWtzUTBGQlF6dEpRVU5vUWl4RFFVRkRPMGxCVTBRc1owTkJRV1VzUjBGQlppeFZRVUZuUWl4RFFVRlBPMUZCUTI1Q0xFbEJRVWtzUTBGQlF5eERRVUZETzFsQlFVVXNUMEZCVHl4SlFVRkpMRU5CUVVNc1owSkJRV2RDTEVOQlFVTTdVVUZEY2tNc1NVRkJTU3hEUVVGRExHZENRVUZuUWl4SFFVRkhMRU5CUVVNc1EwRkJRenRSUVVNeFFpeFBRVUZQTEVsQlFVa3NRMEZCUXp0SlFVTm9RaXhEUVVGRE8wbEJVMFFzYVVOQlFXZENMRWRCUVdoQ0xGVkJRV2xDTEVOQlFVODdVVUZEY0VJc1NVRkJTU3hEUVVGRExFTkJRVU03V1VGQlJTeFBRVUZQTEVsQlFVa3NRMEZCUXl4cFFrRkJhVUlzUTBGQlF6dFJRVU4wUXl4SlFVRkpMRU5CUVVNc2FVSkJRV2xDTEVkQlFVY3NRMEZCUXl4RFFVRkRPMUZCUXpOQ0xFOUJRVThzU1VGQlNTeERRVUZETzBsQlEyaENMRU5CUVVNN1NVRlRSQ3cyUWtGQldTeEhRVUZhTEZWQlFXRXNRMEZCVHp0UlFVTm9RaXhKUVVGSkxFTkJRVU1zUTBGQlF5eEZRVUZGTzFsQlEwb3NUMEZCVHl4SlFVRkpMRU5CUVVNc1lVRkJZU3hEUVVGRE8xTkJRemRDTzFGQlEwUXNTVUZCU1N4RFFVRkRMR0ZCUVdFc1IwRkJSeXhQUVVGUExFTkJRVU1zUzBGQlN5eFZRVUZWTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdVVUZEZEVRc1NVRkJTU3hEUVVGRExIRkNRVUZ4UWl4SFFVRkhMRWxCUVVrc1EwRkJRenRSUVVOc1F5eFBRVUZQTEVsQlFVa3NRMEZCUXp0SlFVTm9RaXhEUVVGRE8wbEJSVVFzZVVKQlFWRXNSMEZCVWl4VlFVRlRMRU5CUVc5Q08xRkJRM3BDTEVsQlFVa3NRMEZCUXl4VFFVRlRMRWRCUVVjc1EwRkJReXhEUVVGRE8xRkJRMjVDTEU5QlFVOHNTVUZCU1N4RFFVRkRPMGxCUTJoQ0xFTkJRVU03U1VGSlJDeHhRMEZCYjBJc1IwRkJjRUlzVlVGQmNVSXNRMEZCVlR0UlFVTXpRaXhKUVVGSkxFTkJRVU1zUTBGQlF6dFpRVUZGTEU5QlFVOHNTVUZCU1N4RFFVRkRMRlZCUVZVc1EwRkJRenRSUVVNdlFpeEpRVUZKTEVOQlFVTXNWVUZCVlN4SFFVRkhMRTlCUVU4c1EwRkJReXhMUVVGTExGVkJRVlVzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFJRVU51UkN4UFFVRlBMRWxCUVVrc1EwRkJRenRKUVVOb1FpeERRVUZETzBsQlNVUXNjMEpCUVVzc1IwRkJUQ3hWUVVGTkxFTkJRVlU3VVVGRFdpeEpRVUZKTEVOQlFVTXNVMEZCVXl4RFFVRkRMRTFCUVUwN1dVRkJSU3hQUVVGUExFbEJRVWtzUTBGQlF5eE5RVUZOTEVOQlFVTTdZVUZEY2tNN1dVRkRSQ3hEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETEVOQlFVTTdXVUZEVUN4SlFVRkpMRWxCUVVrc1EwRkJReXhOUVVGTkxFVkJRVVU3WjBKQlEySXNTVUZCU1N4RFFVRkRMRWRCUVVjc1EwRkJRenR2UWtGQlJTeEpRVUZKTEVOQlFVTXNUVUZCVFN4SFFVRkhMRU5CUVVNc1EwRkJRenM3YjBKQlEzUkNMRWxCUVVrc1EwRkJReXhOUVVGTkxFZEJRVWNzUTBGQlF5eERRVUZETzJGQlEzaENPMmxDUVVGTkxFbEJRVWtzUTBGQlF5eEhRVUZITEVOQlFVTXNSVUZCUlR0blFrRkRaQ3hKUVVGSkxFTkJRVU1zU1VGQlNTeERRVUZETEZGQlFWRXNSVUZCUlR0dlFrRkRhRUlzU1VGQlNTeERRVUZETEZGQlFWRXNSMEZCUnl4SlFVRkpMRU5CUVVNN2IwSkJRM0pDTEVsQlFVa3NRMEZCUXl4UFFVRlBMRU5CUVVNc1JVRkJSU3hKUVVGSkxFVkJRVVVzVTBGQlV5eERRVUZETEV0QlFVc3NSVUZCUlN4TFFVRkxMRVZCUVVVc1NVRkJTU3hEUVVGRExFMUJRVTBzUjBGQlJ5eERRVUZETEVWQlFVTXNRMEZCUXl4RFFVRkRPMjlDUVVNdlJDeEpRVUZKTEVOQlFVTXNTVUZCU1N4RlFVRkZMRU5CUVVNN2FVSkJRMlk3WVVGRFNqdFpRVU5FTEU5QlFVOHNTVUZCU1N4RFFVRkRPMU5CUTJZN1NVRkRUQ3hEUVVGRE8wbEJSVVFzT0VKQlFXRXNSMEZCWWl4VlFVRmpMRWxCUVhsQ08xRkJRMjVETEU5QlFVOHNUMEZCVHl4SlFVRkpMRU5CUVVNc1lVRkJZU3hMUVVGTExGVkJRVlVzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRXJRaXhKUVVGSkxFTkJRVU1zWVVGQll5eERRVUZETEVsQlFVa3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGVExFbEJRVWtzUTBGQlF5eGhRVUZoTEVOQlFVTTdTVUZET1Vrc1EwRkJRenRKUVVWTkxHOUNRVUZoTEVkQlFYQkNMRlZCUVhGQ0xFbEJRWFZDTEVWQlFVVXNUVUZCWXp0UlFVTjRSQ3hKUVVGSkxFTkJRVU1zVFVGQlRTeEhRVUZITEUxQlFVMHNRMEZCUXp0SlFVTjZRaXhEUVVGRE8wbEJSVVFzTkVKQlFWY3NSMEZCV0N4VlFVRlpMRWxCUVhsQ08xRkJRMnBETEU5QlFVOHNUMEZCVHl4SlFVRkpMRU5CUVVNc1UwRkJVeXhMUVVGTExGVkJRVlVzUTBGQlF5eERRVUZETEVOQlFVTXNTVUZCU1N4RFFVRkRMRk5CUVZNc1EwRkJReXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMGxCUXpORkxFTkJRVU03U1VGdFFrUXNlVU5CUVhkQ0xFZEJRWGhDTEZWQlFYbENMRmRCUVcxQ0xFVkJRVVVzUTBGQllUdFJRVUV6UkN4cFFrRkpRenRSUVVvMlF5eHJRa0ZCUVN4RlFVRkJMRXRCUVdFN1VVRkRka1FzU1VGQlNTeERRVUZETEZsQlFWa3NRMEZCUXl4VlFVRkJMRU5CUVVNc1NVRkJTU3hQUVVGQkxGZEJRVmNzUjBGQlJ5eERRVUZETEVOQlFVTXNUVUZCVFN4RlFVRjBRaXhEUVVGelFpeERRVUZETEVOQlFVTTdVVUZETDBNc1NVRkJTU3hEUVVGRExIRkNRVUZ4UWl4SFFVRkhMR05CUVUwc1QwRkJRU3h6UTBGQmQwSXNRMEZCUXl4TFFVRkpMRU5CUVVNc1RVRkJUU3hGUVVGRkxFdEJRVWtzUTBGQlF5eFpRVUZaTEVWQlFVVXNRMEZCUXl4RFFVRkRMRVZCUVRORUxFTkJRVEpFTEVOQlFVTTdVVUZETDBZc1QwRkJUeXhKUVVGSkxFTkJRVU03U1VGRGFFSXNRMEZCUXp0SlFWbEVMRzFEUVVGclFpeEhRVUZzUWl4VlFVRnRRaXhYUVVGdFFpeEZRVUZGTEVOQlFXRTdVVUZCY2tRc2FVSkJTVU03VVVGS2RVTXNhMEpCUVVFc1JVRkJRU3hMUVVGaE8xRkJRMnBFTEVsQlFVa3NRMEZCUXl4WlFVRlpMRU5CUVVNc1ZVRkJRU3hEUVVGRExFbEJRVWtzVDBGQlFTeFhRVUZYTEVkQlFVY3NRMEZCUXl4RFFVRkRMRTFCUVUwc1JVRkJkRUlzUTBGQmMwSXNRMEZCUXl4RFFVRkRPMUZCUXk5RExFbEJRVWtzUTBGQlF5eHhRa0ZCY1VJc1IwRkJSeXhqUVVGTkxFOUJRVUVzWjBOQlFXdENMRU5CUVVNc1MwRkJTU3hEUVVGRExFMUJRVTBzUlVGQlJTeExRVUZKTEVOQlFVTXNXVUZCV1N4RlFVRkZMRU5CUVVNc1EwRkJReXhGUVVGeVJDeERRVUZ4UkN4RFFVRkRPMUZCUTNwR0xFOUJRVThzU1VGQlNTeERRVUZETzBsQlEyaENMRU5CUVVNN1NVRlpSQ3h6UWtGQlN5eEhRVUZNTEZWQlEwa3NPRUpCUVRCRExFVkJRekZETEN0Q1FVRXlReXhGUVVNelF5d3JRa0ZCTWtNc1JVRkRNME1zYTBKQlFUaENMRVZCUXpsQ0xGZEJRV3RDTEVWQlEyeENMRmRCUVd0Q08xRkJUblJDTEdsQ1FUSktRenRSUVRGS1J5d3JRMEZCUVN4RlFVRkJMR3REUVVFd1F6dFJRVU14UXl4blJFRkJRU3hGUVVGQkxHMURRVUV5UXp0UlFVTXpReXhuUkVGQlFTeEZRVUZCTEcxRFFVRXlRenRSUVVNelF5eHRRMEZCUVN4RlFVRkJMSE5DUVVFNFFqdFJRVU01UWl3MFFrRkJRU3hGUVVGQkxHdENRVUZyUWp0UlFVTnNRaXcwUWtGQlFTeEZRVUZCTEd0Q1FVRnJRanRSUVVWc1FpeEpRVUZKTEVOQlFWTXNSVUZEVkN4RFFVRlRMRVZCUTFRc1EwRkJReXhIUVVGblFpeEpRVUZKTEVOQlFVTXNTMEZCU3l4RlFVRkhMRU5CUVVNc1RVRkJUU3hGUVVOeVF5eERRVUZETEVkQlFVY3NRMEZCUXl4SFFVRkhMRU5CUVVNc1IwRkJSeXhKUVVGSkxFTkJRVU1zVDBGQlR5eERRVUZETEUxQlFVMHNSVUZETDBJc1EwRkJReXhIUVVGSExFbEJRVWtzUTBGQlF5eE5RVUZOTEVOQlFVTXNUVUZCVFN4RlFVTjBRaXhEUVVGRExFZEJRVWNzU1VGQlNTeERRVUZETEZkQlFWY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkRka0lzUTBGQlF5eEhRVUZITEVsQlFVa3NRMEZCUXl4WFFVRlhMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03VVVGRk5VSXNTVUZCU1N4RFFVRkRMRWRCUVVjc1NVRkJTU3hMUVVGTExFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4SFFVRkhMRWxCUVVrc1MwRkJTeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzFGQlJYWkRMRWxCUVVrc1EwRkJReXhIUVVGSExFbEJRVWtzUTBGQlF6dFJRVVZpTEVsQlFVa3NSVUZCUlN4SFFVRkhMRWxCUVVrc1EwRkJReXhqUVVGakxFTkJRVU03VVVGRk4wSXNTVUZCU1N4RFFVRkRMRTFCUVUwc1EwRkJReXhQUVVGUExFTkJRVU1zVlVGQlF5eERRVUZETEVWQlFVVXNRMEZCUXp0WlFVTnlRaXhEUVVGRExFTkJRVU1zUzBGQlN5eEhRVUZITEVOQlFVTXNRMEZCUXp0WlFVTmFMRWxCUVVrc1QwRkJUeXhEUVVGRExFTkJRVU1zUTBGQlF5eExRVUZMTEZkQlFWY3NSVUZCUlR0blFrRkROVUlzUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJRenRoUVVNMVFqdFpRVU5FTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzFGQlF6TkNMRU5CUVVNc1EwRkJReXhEUVVGRE8xRkJSVWdzU1VGQlNTeEpRVUZKTEVOQlFVTXNjVUpCUVhGQ08xbEJRVVVzU1VGQlNTeERRVUZETEhGQ1FVRnhRaXhGUVVGRkxFTkJRVU03VVVGTE4wUXNTVUZCU1N4VFFVRlRMRU5CUVVNN1VVRkRaQ3hKUVVGSkxFbEJRVWtzUTBGQlF5eGxRVUZsTEVWQlFVVTdXVUZGZEVJc1UwRkJVeXhIUVVGSExFbEJRVWtzUTBGQlF5eGxRVUZsTEVOQlFVTTdVMEZEY0VNN1lVRkJUVHRaUVVWSUxGTkJRVk1zUjBGQlJ5eERRVUZETEVsQlFVa3NNRUpCUVZVc1EwRkJReXhEUVVGRExFVkJRVVVzU1VGQlNTeERRVUZETEUxQlFVMHNSVUZCUlN4TlFVRk5MRU5CUVVNc1kwRkJZeXhGUVVGRkxFMUJRVTBzUTBGQlF5eGpRVUZqTEVWQlFVVXNWVUZCUVN4RFFVRkRMRWxCUVVjc1QwRkJRU3hMUVVGSkxFTkJRVU1zWVVGQllTeERRVUZETEVOQlFVTXNRMEZCUXl4RlFVRnlRaXhEUVVGeFFpeERRVUZETEVOQlFVTXNRMEZCUXl4alFVRmpMRVZCUVVVc1EwRkJRenRaUVVsMlNTeERRVUZETEVkQlFVY3NhVUpCUVU4c1EwRkJReXhyUWtGQmEwSXNRMEZCUXl4RFFVRkRMRVZCUVVVc1kwRkJUU3hQUVVGQkxFTkJRVU1zUlVGQlJDeERRVUZETEVOQlFVTXNRMEZCUXp0WlFVTXpReXhKUVVGSkxFTkJRVU1zVFVGQlRTeERRVUZETEU5QlFVOHNRMEZCUXl4VlFVRkJMRU5CUVVNN1owSkJRMnBDTEVsQlFVa3NUMEZCVHl4RFFVRkRMRU5CUVVNc1RVRkJUU3hKUVVGSkxGRkJRVkU3YjBKQlFVVXNRMEZCUXl4RFFVRkRMRTFCUVUwc1IwRkJSeXhMUVVGSkxFTkJRVU1zVFVGQlRTeERRVUZUTEVOQlFVTXNRMEZCUXl4TlFVRk5MRU5CUVVNc1EwRkJRenRuUWtGRE1VVXNTVUZCU1N4UFFVRlBMRU5CUVVNc1EwRkJReXhOUVVGTkxFbEJRVWtzVVVGQlVUdHZRa0ZCUlN4RFFVRkRMRU5CUVVNc1RVRkJUU3hIUVVGSExFdEJRVWtzUTBGQlF5eE5RVUZOTEVOQlFWTXNRMEZCUXl4RFFVRkRMRTFCUVUwc1EwRkJReXhEUVVGRE8xbEJRemxGTEVOQlFVTXNRMEZCUXl4RFFVRkRPMWxCUTBnc1NVRkJTU3hEUVVGRExFMUJRVTBzUTBGQlF5eFBRVUZQTEVOQlFVTXNWVUZCUVN4RFFVRkRPMmRDUVVOcVFpeEpRVUZOTEVOQlFVTXNSMEZCUnl4TlFVRk5MRU5CUVVNc1kwRkJZeXhEUVVGRExFTkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTXNSMEZCUnl4TlFVRk5MRU5CUVVNc1kwRkJZeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzJkQ1FVTnFSU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJReXhOUVVGTkxFbEJRVWtzUTBGQlF5eERRVUZETzFsQlEzUkRMRU5CUVVNc1EwRkJReXhEUVVGRE8xTkJRMDQ3VVVGRlJDeEpRVUZKTEVOQlFVTXNSMEZCUnl4cFFrRkJUeXhEUVVGRExHdENRVUZyUWl4RFFVRkRMRU5CUVVNc1JVRkJSU3hWUVVGVkxFTkJRVU1zUlVGQlJTeERRVUZETzFsQlEyaEVMRTlCUVU4c1UwRkJVeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMUZCUXpOQ0xFTkJRVU1zUTBGQlF5eERRVUZETzFGQlJVZ3NTVUZCU1N4SlFVRkpMRU5CUVVNc1ZVRkJWU3hKUVVGSkxFOUJRVThzU1VGQlNTeERRVUZETEZWQlFWVXNRMEZCUXl4TlFVRk5MRXRCUVVzc1YwRkJWeXhGUVVGRk8xbEJRMnhGTEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJRenRaUVVOV0xFbEJRVWtzWVVGQllTeEhRVUZITEZWQlFVTXNRMEZCUXl4RlFVRkZMRU5CUVVNc1JVRkJSU3hSUVVGUkxFVkJRVVVzWVVGQllUdG5Ra0ZET1VNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4UlFVRlJMRU5CUVVNN1owSkJRemRDTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFZEJRVWNzWVVGQllTeERRVUZETzFsQlEzUkRMRU5CUVVNc1EwRkJRenRaUVVOR0xFbEJRVWtzUTBGQlF5eFBRVUZQTEVOQlFVTXNUMEZCVHl4RFFVRkRMRlZCUVVFc1EwRkJRenRuUWtGRGJFSXNZVUZCWVN4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFZEJRVWNzUTBGQlF5eEZRVUZGTEV0QlFVa3NRMEZCUXl4cFFrRkJhVUlzUlVGQlJTeEhRVUZITEVOQlFVTXNRMEZCUXp0blFrRnBRbkpFTEVsQlFVa3NUMEZCVHl4RFFVRkRMRU5CUVVNc1RVRkJUU3hMUVVGTExGZEJRVmNzUlVGQlJUdHZRa0ZEYWtNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEhRVUZITEVOQlFVTXNSMEZCUnl4RFFVRkRMRVZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJRenR2UWtGRE4wSXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUjBGQlJ5eERRVUZETEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFZEJRVWNzUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXp0cFFrRkRhRU03Y1VKQlFVMDdiMEpCUTBnc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXl4TlFVRk5MRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJReXhOUVVGTkxFTkJRVU1zUTBGQlF5eERRVUZETzI5Q1FVTjJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRTFCUVUwc1EwRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFMUJRVTBzUTBGQlF5eERRVUZETEVOQlFVTTdhVUpCUXpGRE8xbEJRMHdzUTBGQlF5eERRVUZETEVOQlFVTTdVMEZEVGpzN1dVRkJUU3hKUVVGSkxFTkJRVU1zVlVGQlZTeEhRVUZITEVWQlFVVXNUVUZCVFN4RlFVRkZMRWxCUVVrc1EwRkJReXhOUVVGTkxFVkJRVVVzVFVGQlRTeEZRVUZGTEVWQlFVVXNSVUZCUlN4RFFVRkRPMUZCUlRkRUxFbEJRVWtzWTBGQll5eEhRVUZITEVsQlFVa3NRMEZCUXl4WlFVRlpMRWxCUVVrc1JVRkJSU3hEUVVGRE8xRkJRemRETEVsQlFVa3NTVUZCU1N4RFFVRkRMSGRDUVVGM1FpeEZRVUZGTzFsQlEzcENMRWxCUVVrc1EwRkJReXhaUVVGaExFTkJRVU1zWjBKQlFXZENMRWRCUVVjc1NVRkJTU3hEUVVGRExIZENRVUYzUWl4RFFVRkRMR2RDUVVGblFpeERRVUZETzFsQlF6TkdMR05CUVdNc1IwRkJSeXhqUVVGakxFTkJRVU1zVFVGQlRTeERRVUZETERaRFFVRXJRaXhEUVVGRExFTkJRVU1zUlVGQlJTeEpRVUZKTEVOQlFVTXNUVUZCVFN4RlFVRkZMRWxCUVVrc1EwRkJReXgzUWtGQmQwSXNRMEZCUXl4SlFVRkpMRVZCUVU4c1EwRkJReXhKUVVGSkxFTkJRVU1zV1VGQldTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMU5CUjNwS08xRkJSVVFzU1VGQlNTeERRVUZETEdGQlFXRXNRMEZCUXl4TFFVRkxMRU5CUVVNc1EwRkJRenRSUVVNeFFpeEpRVUZKTEVOQlFVTXNVVUZCVVN4SFFVRkhMRWxCUVVrc2FVSkJRVThzUTBGQlF5eERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF6dFJRVVYyUXl4SlFVRkpMRU5CUVVNc1VVRkJVU3hEUVVGRExFdEJRVXNzUTBGQlF5eExRVUZMTEVWQlFVVXNRMEZCUXp0UlFVTTFRaXhMUVVGTExFbEJRVWtzUTBGQlF5eEhRVUZITEVOQlFVTXNSVUZCUlN4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRkxFVkJRVVVzUTBGQlF5eEZRVUZGTzFsQlEzaENMRWxCUVVrc1EwRkJReXhIUVVGSExFbEJRVWtzUTBGQlF5eE5RVUZOTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1dVRkRka0lzU1VGQlNTeERRVUZETEVOQlFVTXNTMEZCU3l4RlFVRkZPMmRDUVVOVUxFTkJRVU1zUTBGQlF5eEZRVUZGTEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRuUWtGRFdDeERRVUZETEVOQlFVTXNSVUZCUlN4SFFVRkhMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03WjBKQlExZ3NTVUZCU1N4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRuUWtGRGJrSXNTVUZCU1N4RFFVRkRMRkZCUVZFc1EwRkJReXhMUVVGTExFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJRenRoUVVOcVF6dFRRVU5LTzFGQlEwUXNTVUZCU1N4RFFVRkRMRkZCUVZFc1EwRkJReXhUUVVGVExFZEJRVWNzU1VGQlNTeERRVUZETEZWQlFWVXNRMEZCUXp0UlFVc3hReXhKUVVGSkxFTkJRVU1zWVVGQllTeERRVUZETERoQ1FVRTRRaXhGUVVGRkxFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTXNRMEZCUXp0UlFVZDZSQ3hKUVVGSkxHTkJRV01zUTBGQlF5eE5RVUZOTEVkQlFVY3NRMEZCUXp0WlFVRkZMRWxCUVVrc1EwRkJReXhSUVVGUkxFTkJRVU1zVDBGQlR5eEhRVUZITEVsQlFVa3NjMEpCUVZVc1EwRkJReXhKUVVGSkxFTkJRVU1zVFVGQlRTeEZRVUZGTEVsQlFVa3NRMEZCUXl4UFFVRlBMRVZCUVVVc1NVRkJTU3hEUVVGRExGVkJRVlVzUlVGQlJTeGpRVUZqTEVOQlFVTXNRMEZCUXl4blFrRkJaMElzUlVGQlJTeERRVUZETzFGQlEzSktMRWxCUVVrc1EwRkJReXhSUVVGUkxFTkJRVU1zUjBGQlJ5eERRVUZETEN0Q1FVRXJRaXhEUVVGRExFTkJRVU03VVVGRGJrUXNTVUZCU1N4RFFVRkRMRFpDUVVFMlFpeERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRVZCUVVVc1YwRkJWeXhEUVVGRExFTkJRVU03VVVGSGRFUXNTVUZCU1N4RFFVRkRMR0ZCUVdFc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF6dFJRVU4yUWl4SlFVRkpMRVZCUVVVc1JVRkJSVHRaUVVOS0xFbEJRVWtzUTBGQlF5eE5RVUZOTEVOQlFVTXNUMEZCVHl4RFFVRkRMRlZCUVZVc1EwRkJReXhGUVVGRkxFTkJRVU1zU1VGQlNTeERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMWxCUTJwRkxFbEJRVWtzUTBGQlF5eFJRVUZSTEVOQlFVTXNUMEZCVHl4SFFVRkhMRWxCUVVrc2MwSkJRVlVzUTBGQlF5eEpRVUZKTEVOQlFVTXNUVUZCVFN4RlFVRkZMRWxCUVVrc1EwRkJReXhQUVVGUExFVkJRVVVzU1VGQlNTeERRVUZETEZWQlFWVXNSVUZCUlN4alFVRmpMRVZCUVVVc1NVRkJTU3hEUVVGRExFTkJRVU1zWjBKQlFXZENMRVZCUVVVc1EwRkJRenRaUVVNMVNDeEpRVUZKTEVOQlFVTXNUVUZCVFN4RFFVRkRMRTlCUVU4c1EwRkJReXhWUVVGVkxFTkJRVU1zUlVGQlJTeERRVUZETEVsQlFVa3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRUUVVOd1JUdFJRVWRFTEVsQlFVa3NRMEZCUXl4UlFVRlJMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF6dFJRVU53UWl4SlFVRkpMRU5CUVVNc1VVRkJVU3hEUVVGRExFZEJRVWNzUTBGQlF5d3JRa0ZCSzBJc1EwRkJReXhEUVVGRE8xRkJSVzVFTEVsQlFVa3NhMEpCUVd0Q0xFVkJRVVU3V1VGRGNFSXNTVUZCU1N4RFFVRkRMRkZCUVZFc1EwRkJReXhaUVVGWkxFZEJRVWNzU1VGQlNTeERRVUZETzFsQlEyeERMRWxCUVVrc1EwRkJReXhSUVVGUkxFTkJRVU1zV1VGQldTeEhRVUZITEVsQlFVa3NRMEZCUXl4TlFVRk5MRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUzBGQlN5eERRVUZETzFsQlEyeEVMRWxCUVVrc1EwRkJReXhSUVVGUkxFTkJRVU1zWjBKQlFXZENMRWRCUVVjc1EwRkJReXhEUVVGRE8xbEJRMjVETEVsQlFVa3NRMEZCUXl4UlFVRlJMRU5CUVVNc1pVRkJaU3hIUVVGSExFTkJRVU1zU1VGQlNTeERRVUZETEVOQlFVTTdXVUZEZGtNc1NVRkJTU3hGUVVGRkxFZEJRVWNzYVVKQlFVOHNRMEZCUXl4clFrRkJhMElzUTBGQlF5eERRVUZETEVWQlFVTXNWVUZCUXl4RFFVRkRMRVZCUVVVc1EwRkJRenRuUWtGRGRrTXNTVUZCU1N4RFFVRkRMRWxCUVVrc1EwRkJReXhKUVVGSkxFTkJRVU1zU1VGQlNTeERRVUZETzI5Q1FVRkZMRTlCUVU4c1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMmRDUVVOeVF5eFBRVUZQTEVOQlFVTXNRMEZCUVR0WlFVTmFMRU5CUVVNc1EwRkJReXhEUVVGRE8xbEJRMGdzU1VGQlNTeERRVUZETEZGQlFWRXNRMEZCUXl4RFFVRkRMRWRCUVVjc1JVRkJSU3hEUVVGRE8xbEJRM0pDTEVsQlFVa3NRMEZCUXl4UlFVRlJMRU5CUVVNc1IwRkJSeXhEUVVGRExHdENRVUZyUWl4RFFVRkRMRU5CUVVNN1UwRkRla003VVVGRlJDeEpRVUZKTEVOQlFVTXNiVUpCUVcxQ0xFVkJRVVVzUTBGQlF6dFJRVU16UWl4SlFVRkpMRU5CUVVNc05rSkJRVFpDTEVOQlFVTXNRMEZCUXl4RlFVRkZMRU5CUVVNc1JVRkJSU3hYUVVGWExFTkJRVU1zUTBGQlF6dFJRVU4wUkN4UFFVRlBMRmRCUVZjc1EwRkJReXhEUVVGRExFTkJRVU1zU1VGQlNTeERRVUZETEUxQlFVMHNSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJReXhKUVVGSkxFTkJRVU03U1VGRE9VTXNRMEZCUXp0SlFVVlBMRGhDUVVGaExFZEJRWEpDTEZWQlFYTkNMRlZCUVd0Q0xFVkJRVVVzUTBGQlZ5eEZRVUZGTEVOQlFWYzdVVUZET1VRc1NVRkJTU3hKUVVGSkxFTkJRVU1zVDBGQlR5eERRVUZETEUxQlFVMHNSMEZCUnl4RFFVRkRMRWxCUVVrc1ZVRkJWU3hIUVVGSExFTkJRVU1zUlVGQlJUdFpRVWN6UXl4SlFVRkpMRU5CUVVNc1IwRkJSeXhKUVVGSkxFTkJRVU1zVFVGQlRTeERRVUZETEUxQlFVMHNRMEZCUXp0WlFVTXpRaXhKUVVGSkxFdEJRVXNzUjBGQlJ5eEpRVUZKTEVOQlFVTXNUVUZCVFN4RFFVRkRMRWRCUVVjc1EwRkJReXhWUVVGQkxFTkJRVU1zU1VGQlNTeFBRVUZCTEVOQlFVc3NSVUZCUlN4TlFVRk5MRVZCUVZNc1EwRkJReXhEUVVGRExFMUJRVThzUTBGQlF5eExRVUZMTEVWQlFVVXNUVUZCVFN4RlFVRlRMRU5CUVVNc1EwRkJReXhOUVVGUExFTkJRVU1zUzBGQlN5eEZRVUZGTEVOQlFVRXNSVUZCZGtVc1EwRkJkVVVzUTBGQlF5eERRVUZETzFsQlF6RkhMRWxCUVVrc1JVRkJSU3hIUVVGSExFbEJRVWtzUTBGQlF5eE5RVUZOTEVOQlFVTXNSMEZCUnl4RFFVRkRMRlZCUVVFc1EwRkJReXhKUVVGSkxFOUJRVUVzUTBGQlN5eEZRVUZGTEV0QlFVc3NSVUZCUlN4RFFVRkRMRU5CUVVNc1MwRkJTeXhGUVVGRkxFTkJRVUVzUlVGQmRrSXNRMEZCZFVJc1EwRkJReXhEUVVGRE8xbEJRM1pFTEVsQlFVa3NRMEZCUXl4UFFVRlBMRU5CUVVNc1QwRkJUeXhEUVVGRExGVkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTTdaMEpCUTNSQ0xFVkJRVVVzUTBGQlF5eEpRVUZKTEVOQlFVMHNSVUZCUlN4TFFVRkxMRVZCUVVVc1EwRkJReXhEUVVGRExFdEJRVXNzUjBGQlJ5eERRVUZETEVkQlFVY3NRMEZCUXl4RlFVRkZMRU5CUVVNc1EwRkJRenRaUVVNM1F5eERRVUZETEVOQlFVTXNRMEZCUXp0WlFVTklMRWxCUVVrc1EwRkJReXhQUVVGUExFTkJRVU1zVDBGQlR5eERRVUZETEZWQlFVTXNRMEZCUXl4RlFVRkZMRU5CUVVNN1owSkJRM1JDTEVsQlFVa3NUMEZCVHl4RFFVRkRMRU5CUVVNc1RVRkJUU3hMUVVGTExGZEJRVmM3YjBKQlF5OUNMRU5CUVVNc1EwRkJReXhOUVVGTkxFTkJRVU1zVDBGQlR5eERRVUZETEZWQlFVRXNRMEZCUXl4SlFVRkpMRTlCUVVFc1MwRkJTeXhEUVVGRExFbEJRVWtzUTBGQlF5eEZRVUZGTEUxQlFVMHNSVUZCUlN4RFFVRkRMRU5CUVVNc1MwRkJTeXhGUVVGRkxFMUJRVTBzUlVGQlJTeERRVUZETEVOQlFVTXNTMEZCU3l4RlFVRkZMRU5CUVVNc1JVRkJhRVFzUTBGQlowUXNRMEZCUXl4RFFVRkRPMmRDUVVNMVJTeEpRVUZKTEU5QlFVOHNRMEZCUXl4RFFVRkRMRTFCUVUwc1MwRkJTeXhYUVVGWE8yOUNRVU12UWl4RFFVRkRMRU5CUVVNc1RVRkJUU3hEUVVGRExFOUJRVThzUTBGQlF5eFZRVUZCTEVWQlFVVXNTVUZCU1N4UFFVRkJMRXRCUVVzc1EwRkJReXhKUVVGSkxFTkJRVU1zUlVGQlJTeE5RVUZOTEVWQlFVVXNRMEZCUXl4RFFVRkRMRXRCUVVzc1JVRkJSU3hOUVVGTkxFVkJRVVVzUlVGQlJTeERRVUZETEV0QlFVc3NSVUZCUlN4RFFVRkRMRVZCUVdwRUxFTkJRV2xFTEVOQlFVTXNRMEZCUXp0WlFVTnNSaXhEUVVGRExFTkJRVU1zUTBGQlF6dFpRVWRJTEVsQlFVa3NUVUZCVFN4RlFVRkZPMmxDUVVOUUxFbEJRVWtzUTBGQlF5eEpRVUZKTEVOQlFVTXNTVUZCU1N4RlFVRkZMRU5CUVVNN2FVSkJRMnBDTEV0QlFVc3NRMEZCUXl4RlFVRkZMRU5CUVVNN2FVSkJRMVFzUzBGQlN5eERRVUZETEV0QlFVc3NRMEZCUXp0cFFrRkRXaXhoUVVGaExFTkJRVU1zUzBGQlN5eERRVUZETzJsQ1FVTndRaXhaUVVGWkxFTkJRVU1zU1VGQlNTeERRVUZETEZsQlFWa3NSVUZCUlN4RFFVRkRPMmxDUVVOcVF5eDNRa0ZCZDBJc1EwRkJReXhEUVVGRExFTkJRVU03YVVKQlF6TkNMRzlDUVVGdlFpeERRVUZETEVsQlFVa3NRMEZCUXp0cFFrRkRNVUlzUzBGQlN5eERRVUZETEZWQlFWVXNSVUZCUlN4RFFVRkRMRVZCUVVVc1EwRkJReXhGUVVGRkxFTkJRVU1zUlVGQlJTeExRVUZMTEVOQlFVTXNRMEZCUXp0WlFVVjJReXhKUVVGSkxFTkJRVU1zVFVGQlRTeERRVUZETEU5QlFVOHNRMEZCUXl4VlFVRkJMRU5CUVVNN1owSkJRMnBDTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1MwRkJTeXhEUVVGRExFZEJRVWNzUlVGQlJTeERRVUZETEVOQlFVTXNRMEZCUXl4TFFVRkxMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03WjBKQlF6TkNMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUzBGQlN5eERRVUZETEVkQlFVY3NSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJReXhMUVVGTExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdXVUZETDBJc1EwRkJReXhEUVVGRExFTkJRVU03VTBGRFRqdGhRVUZOTzFsQlEwZ3NTVUZCU1N4RFFVRkRMRkZCUVZFc1EwRkJReXhIUVVGSExFTkJRVU1zVlVGQlZTeERRVUZETEVOQlFVTTdVMEZEYWtNN1NVRkRUQ3hEUVVGRE8wbEJSMDhzT0VOQlFUWkNMRWRCUVhKRExGVkJRWE5ETEV0QlFXRXNSVUZCUlN4TlFVRmpMRVZCUVVVc1YwRkJNa0k3VVVGQmFFY3NhVUpCWlVNN1VVRm1iMFVzTkVKQlFVRXNSVUZCUVN4clFrRkJNa0k3VVVGRk5VWXNTVUZCU1N4RFFVRkRMRWxCUVVrc1EwRkJReXhsUVVGbExFbEJRVWtzU1VGQlNTeERRVUZETEcxQ1FVRnRRaXhGUVVGRk8xbEJRMjVFTEVsQlFVa3NSMEZCUXl4SFFVRkhMRWxCUVVrc1EwRkJReXhSUVVGUkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RlFVRkZMRWRCUVVNc1IwRkJSeXhKUVVGSkxFTkJRVU1zVVVGQlVTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRaUVVOdVJDeEpRVUZKTEVOQlFVTXNUVUZCVFN4RFFVRkRMRTlCUVU4c1EwRkJReXhWUVVGVkxFTkJRVU1zUlVGQlJTeERRVUZETEVsQlFVa3NRMEZCUXl4RFFVRkRMRU5CUVVNc1IwRkJSeXhIUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1IwRkJSeXhIUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRaUVVOcVJTeEpRVUZKTEUxQlFVMHNSMEZCUnl4dFEwRkJZeXhEUVVGRExFbEJRVWtzUTBGQlF5eE5RVUZOTEVWQlFVVXNTVUZCU1N4RFFVRkRMRTFCUVUwc1EwRkJReXhEUVVGRE8xbEJRM1JFTEdsRFFVRlpMRU5CUVVNc1RVRkJUU3hGUVVGRkxFdEJRVXNzUlVGQlJTeE5RVUZOTEVWQlFVVXNTVUZCU1N4RFFVRkRMR2RDUVVGblFpeEZRVUZGTEVOQlFVTXNSVUZCUlN4WFFVRlhMRU5CUVVNc1EwRkJRenRaUVVNelJTeEpRVUZKTEVOQlFVTXNUVUZCVFN4RFFVRkRMRTlCUVU4c1EwRkJReXhWUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETzJkQ1FVTnlRaXhMUVVGSkxFTkJRVU1zVVVGQlVTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNRMEZCUXl4RlFVRkZMRXRCUVVrc1EwRkJReXhSUVVGUkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdaMEpCUTNwRUxFbEJRVWtzUTBGQlF5eERRVUZETEUxQlFVMHNSVUZCUlR0dlFrRkRWaXhEUVVGRExFTkJRVU1zVFVGQlRTeERRVUZETEZWQlFWVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03YjBKQlEzcENMRU5CUVVNc1EwRkJReXhOUVVGTkxFTkJRVU1zVlVGQlZTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRwUWtGRE5VSTdXVUZEVEN4RFFVRkRMRU5CUVVNc1EwRkJRenRUUVVOT08wbEJRMHdzUTBGQlF6dEpRVVZFTEhWQ1FVRk5MRWRCUVU0N1VVRkRTU3hQUVVGUExFbEJRVWtzUTBGQlF5eExRVUZMTEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNN1NVRkRNMElzUTBGQlF6dEpRVVZFTEhGQ1FVRkpMRWRCUVVvN1VVRkRTU3hQUVVGUExFbEJRVWtzUTBGQlF5eExRVUZMTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1NVRkRla0lzUTBGQlF6dEpRVWxFTEcxRFFVRnJRaXhIUVVGc1FpeFZRVUZ0UWl4VlFVRnpRanRSUVVGMFFpd3lRa0ZCUVN4RlFVRkJMR05CUVhOQ08xRkJRM0pETEVsQlFVa3NRMEZCUXl4blFrRkJaMElzUjBGQlJ5eEpRVUZKTERaQ1FVRnpRaXhEUVVNNVF5eEpRVUZKTEVOQlFVTXNUVUZCVFN4RFFVRkRMRWRCUVVjc1EwRkJReXhWUVVGVkxFTkJRVU03V1VGRGRrSXNUMEZCVHl4RFFVRkRMRU5CUVVNc1RVRkJUU3hEUVVGRExFOUJRVThzUTBGQlF5eERRVUZETEZWQlFWVXNRMEZCUXl4RFFVRkRMRkZCUVZFc1JVRkJSU3hEUVVGRE8xRkJRM0JFTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1NVRkRXaXhEUVVGRE8wbEJWMFFzTUVKQlFWTXNSMEZCVkN4VlFVRlZMRWxCUVVrc1JVRkJSU3hGUVVGakxFVkJRVVVzU1VGQlNUdFJRVUZ3UWl4dFFrRkJRU3hGUVVGQkxFMUJRV003VVVGRE1VSXNTVUZCU1N4UlFVRlJMRWRCUVVjc1JVRkJSU3hEUVVGRE8xRkJTV3hDTEVsQlFVa3NSMEZCUnl4SFFVRkhMRWxCUVVrc05rSkJRWE5DTEVOQlFVTXNTVUZCU1N4RFFVRkRMR2RDUVVGblFpeERRVUZETEVOQlFVTXNSVUZCUlN4RlFVRkZMRU5CUVVNc1JVRkJSU3hKUVVGSkxFTkJRVU1zWjBKQlFXZENMRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU1zUlVGQlJTeEpRVUZKTEVOQlFVTXNaMEpCUVdkQ0xFTkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTXNSVUZEY2tnc1MwRkJTeXhIUVVGaExFVkJRVVVzUTBGQlF5eEZRVUZGTEVsQlFVa3NRMEZCUXl4TlFVRk5MRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU1zUlVGQlJTeEpRVUZKTEVOQlFVTXNUVUZCVFN4RFFVRkRMRU5CUVVNc1JVRkJSU3hGUVVONFJDeExRVUZMTEVkQlFXRXNSVUZCUlN4RFFVRkRMRVZCUVVVc1NVRkJTU3hEUVVGRExFMUJRVTBzUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4RlFVRkZMRWxCUVVrc1EwRkJReXhOUVVGTkxFTkJRVU1zUTBGQlF5eEZRVUZGTEVWQlEzaEVMRXRCUVVzc1IwRkJSeXhIUVVGSExFTkJRVU1zVVVGQlVTeERRVUZETEV0QlFVc3NSVUZCUlN4SlFVRkpMRU5CUVVNc1RVRkJUU3hEUVVGRExFdEJRVXNzUTBGQlF5eEZRVU01UXl4SFFVRkhMRWRCUVVjc1IwRkJSeXhEUVVGRExGRkJRVkVzUTBGQlF5eExRVUZMTEVWQlFVVXNTVUZCU1N4RFFVRkRMRTFCUVUwc1EwRkJReXhMUVVGTExFTkJRVU1zUTBGQlF6dFJRVU5xUkN4SFFVRkhMRU5CUVVNc1owSkJRV2RDTEVOQlFVTXNTMEZCU3l4RlFVRkZMRXRCUVVzc1JVRkJSU3hKUVVGSkxFTkJRVU1zVFVGQlRTeERRVUZETEV0QlFVc3NSVUZCUlN4SlFVRkpMRU5CUVVNc1RVRkJUU3hEUVVGRExFdEJRVXNzUTBGQlF5eERRVUZETzFGQlEzcEZMRWxCUVVrc1QwRkJUeXhKUVVGSkxFdEJRVXNzVjBGQlZ5eEZRVUZGTzFsQlF6ZENMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF6dFRRVU5pTzFGQlEwUXNTVUZCU1N4VFFVRlRMRWRCUVVjc1ZVRkJRU3hEUVVGRExFbEJRVWtzVDBGQlFTeERRVUZETEVOQlFVTXNUVUZCVFN4RFFVRkRMRVZCUVVVc1JVRkJXQ3hEUVVGWExFVkJRVVVzVTBGQlV5eEhRVUZITEZWQlFVRXNRMEZCUXl4SlFVRkpMRTlCUVVFc1EwRkJReXhEUVVGRExFMUJRVTBzUTBGQlF5eEZRVUZGTEVWQlFWZ3NRMEZCVnl4RlFVRkZMRTFCUVUwc1IwRkJSeXhWUVVGQkxFTkJRVU1zU1VGQlNTeFBRVUZCTEVOQlFVTXNRMEZCUXl4TlFVRk5MRVZCUVVVc1JVRkJWaXhEUVVGVkxFVkJRM0JHTEUxQlFVMHNSMEZCUnl4SlFVRkpMREJDUVVGVkxFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNRMEZCUXl4TlFVRk5MRVZCUVVVc1IwRkJSeXhEUVVGRExFTkJRVU1zUlVGQlJTeFRRVUZUTEVWQlFVVXNVMEZCVXl4RlFVRkZMRTFCUVUwc1EwRkJReXhGUVVNeFJTeFpRVUZaTEVkQlFVY3NUVUZCVFN4RFFVRkRMR3RDUVVGclFpeERRVUZETEV0QlFVc3NRMEZCUXl4RlFVRkZMRVZCUVVVc1IwRkJSeXhEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETzFGQlF5OUVMRWxCUVVrc1dVRkJXU3hEUVVGRExFMUJRVTBzUzBGQlN5eERRVUZETEVsQlFVa3NXVUZCV1N4RFFVRkRMRTFCUVUwc1MwRkJTeXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEUxQlFVMHNSVUZCUlR0WlFVTnVSU3hKUVVGSkxFdEJRVXNzUjBGQlJ5d3lRa0ZCWlN4RFFVRkRMRWxCUVVrc1EwRkJReXhOUVVGTkxFTkJRVU1zVjBGQlZ5eEZRVUZGTEVsQlFVa3NRMEZCUXl4TlFVRk5MRU5CUVVNc1YwRkJWeXhGUVVGRkxFVkJRVVVzUTBGQlF5eERRVUZETzFsQlEyeEdMRkZCUVZFc1IwRkJSeXhEUVVGRExFdEJRVXNzUTBGQlF5eHJRa0ZCYTBJc1JVRkJSU3hMUVVGTExFTkJRVU1zVlVGQlZTeERRVUZETEVOQlFVTTdVMEZETTBRN1lVRkJUVHRaUVVOSUxFbEJRVWtzUTBGQlF5eEhRVUZITEZsQlFWa3NRMEZCUXl4TlFVRk5MRWRCUVVjc1EwRkJReXhGUVVNelFpeERRVUZETEVkQlFVY3NSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJReXhaUVVGWkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUXpWQ0xFTkJRVU1zUjBGQlJ5eEhRVUZITEVOQlFVTXNRMEZCUXl4RFFVRkRMRmxCUVZrc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSVUZETlVJc1VVRkJVU3hIUVVGSExFTkJRVU1zU1VGQlNTeERRVUZETEUxQlFVMHNRMEZCUXl4WFFVRlhMRU5CUVVNc1pVRkJaU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03V1VGRGJrVXNTMEZCU3l4SlFVRkpMRU5CUVVNc1IwRkJSeXhEUVVGRExFVkJRVVVzUTBGQlF5eEpRVUZKTEVOQlFVTXNSVUZCUlN4RlFVRkZMRU5CUVVNN1owSkJRM1pDTEZGQlFWRXNRMEZCUXl4SlFVRkpMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF5eFpRVUZaTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFpRVU0xUXl4UlFVRlJMRU5CUVVNc1NVRkJTU3hEUVVGRExITkNRVUZWTEVOQlFVTXNRMEZCUXl4RlFVRkZMRWxCUVVrc1EwRkJReXhOUVVGTkxFTkJRVU1zVjBGQlZ5eEZRVUZGTEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNN1UwRkROMFE3VVVGaFJDeFBRVUZQTEZGQlFWRXNRMEZCUXp0SlFVTndRaXhEUVVGRE8wbEJSMDBzY1VKQlFXTXNSMEZCY2tJc1ZVRkJjMElzUTBGQmMwSTdVVUZEZUVNc1QwRkJUeXhQUVVGUExFTkJRVU1zUTBGQlF5eE5RVUZOTEV0QlFVc3NVVUZCVVN4RFFVRkRMRU5CUVVNc1EwRkJVeXhEUVVGRExFTkJRVU1zVFVGQlRTeERRVUZETEVOQlFVTXNRMEZCVVN4RFFVRkRMRU5CUVVNc1RVRkJUeXhEUVVGRExFdEJRVXNzUTBGQlF6dEpRVU53Uml4RFFVRkRPMGxCUjAwc2NVSkJRV01zUjBGQmNrSXNWVUZCYzBJc1EwRkJjMEk3VVVGRGVFTXNUMEZCVHl4UFFVRlBMRU5CUVVNc1EwRkJReXhOUVVGTkxFdEJRVXNzVVVGQlVTeERRVUZETEVOQlFVTXNRMEZCVXl4RFFVRkRMRU5CUVVNc1RVRkJUU3hEUVVGRExFTkJRVU1zUTBGQlVTeERRVUZETEVOQlFVTXNUVUZCVHl4RFFVRkRMRXRCUVVzc1EwRkJRenRKUVVOd1JpeERRVUZETzBsQlIwMHNZVUZCVFN4SFFVRmlMRlZCUVdNc1EwRkJjMEk3VVVGRGFFTXNUMEZCVHl4TlFVRk5MRU5CUVVNc1kwRkJZeXhEUVVGRExFTkJRVU1zUTBGQlF5eEhRVUZITEVkQlFVY3NSMEZCUnl4TlFVRk5MRU5CUVVNc1kwRkJZeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzBsQlEzSkZMRU5CUVVNN1NVRk5UU3huUWtGQlV5eEhRVUZvUWl4VlFVRnBRaXhEUVVGbE8xRkJRelZDTEVsQlFVa3NUMEZCVHl4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGRk8xbEJRMW9zVFVGQlRTeERRVUZETEZkQlFWY3NRMEZCUXl4RFFVRkRMRVZCUVVVc1RVRkJUU3hEUVVGRExGVkJRVlVzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMU5CUXk5RE8yRkJRVTA3V1VGRFNDeE5RVUZOTEVOQlFVTXNVVUZCVVN4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8xbEJRMjVDTEVOQlFVTXNRMEZCUXl4TFFVRkxMRWxCUVVrc1EwRkJReXhEUVVGRE8xTkJRMmhDTzBsQlEwd3NRMEZCUXp0SlFVbGpMR1ZCUVZFc1IwRkJka0lzVlVGQmQwSXNRMEZCVHp0UlFVTnlRaXhEUVVGRkxFTkJRVU1zUlVGQlJTeEhRVUZITEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1VVRkRXaXhEUVVGRkxFTkJRVU1zUlVGQlJTeEhRVUZITEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1NVRkRkRUlzUTBGQlF6dEpRVWxqTEd0Q1FVRlhMRWRCUVRGQ0xGVkJRVEpDTEVOQlFWRXNSVUZCUlN4TlFVRm5RenRSUVVOcVJTeEpRVUZKTEU5QlFVOHNRMEZCUXl4RFFVRkRMRTFCUVUwc1MwRkJTeXhYUVVGWExFVkJRVVU3V1VGRGFrTXNRMEZCUXl4RFFVRkRMRTFCUVUwc1EwRkJReXhQUVVGUExFTkJRVU1zVlVGQlFTeERRVUZETzJkQ1FVTmtMRU5CUVVNc1EwRkJReXhMUVVGTExFbEJRVWtzUTBGQlF5eERRVUZETzJkQ1FVTmlMRTFCUVUwc1EwRkJReXhSUVVGUkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdaMEpCUTJJc1EwRkJSU3hEUVVGRExHbENRVUZwUWl4SFFVRkhMRU5CUVVNc1EwRkJReXhEUVVGRExFZEJRVWNzVFVGQlRTeERRVUZETEVOQlFVTXNRMEZCUXp0blFrRkRkRU1zUTBGQlJTeERRVUZETEdsQ1FVRnBRaXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NUVUZCVFN4RFFVRkRMRU5CUVVNc1EwRkJRenRaUVVOb1JDeERRVUZETEVOQlFVTXNRMEZCUXp0VFFVTk9PMUZCUTBRc1NVRkJTU3hQUVVGUExFTkJRVU1zUTBGQlF5eE5RVUZOTEV0QlFVc3NWMEZCVnl4RlFVRkZPMWxCUTJwRExFTkJRVU1zUTBGQlF5eE5RVUZOTEVOQlFVTXNUMEZCVHl4RFFVRkRMRlZCUVVFc1EwRkJReXhKUVVGSkxFOUJRVUVzVFVGQlRTeERRVUZETEZkQlFWY3NRMEZCUXl4RFFVRkRMRVZCUVVVc1RVRkJUU3hEUVVGRExFVkJRVGRDTEVOQlFUWkNMRU5CUVVNc1EwRkJRenRUUVVONFJEdEpRVU5NTEVOQlFVTTdTVUZIVFN4cFFrRkJWU3hIUVVGcVFpeFZRVUZyUWl4RFFVRmxPMUZCUXpkQ0xFbEJRVWtzVDBGQlR5eERRVUZETEVOQlFVTXNRMEZCUXl4RlFVRkZPMWxCUTFvc1QwRkJUenRuUWtGRFNDeERRVUZETEVWQlFVVXNRMEZCUXl4RFFVRkRMRTFCUVUwc1EwRkJReXhGUVVGRkxFVkJRVVU3WjBKQlEyaENMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zVFVGQlRTeERRVUZETEVWQlFVVXNSVUZCUlR0aFFVTnVRaXhEUVVGRE8xTkJRMHc3WVVGQlRUdFpRVU5JTEU5QlFVOHNRMEZCUXl4RFFVRkRPMU5CUTFvN1NVRkRUQ3hEUVVGRE8wbEJTVTBzVjBGQlNTeEhRVUZZTEZWQlFWa3NRMEZCWlN4RlFVRkZMRkZCUVd0RE8xRkJRek5FTEVsQlFVa3NUMEZCVHl4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGRk8xbEJRMW9zU1VGQlNTeFBRVUZQTEVOQlFVTXNRMEZCUXl4TlFVRk5MRXRCUVVzc1YwRkJWeXhGUVVGRk8yZENRVU5xUXl4RFFVRkRMRU5CUVVNc1RVRkJUU3hEUVVGRExFOUJRVThzUTBGQlF5eFZRVUZCTEVOQlFVTTdiMEpCUTJRc1EwRkJReXhEUVVGRExFMUJRVTBzUTBGQlF5eFZRVUZWTEVOQlFVTXNVVUZCVVN4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8yOUNRVU5vUXl4RFFVRkRMRU5CUVVNc1RVRkJUU3hEUVVGRExGVkJRVlVzUTBGQlF5eFJRVUZSTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN2IwSkJRekZDTEVOQlFVVXNRMEZCUXl4RlFVRkZMRWRCUVZNc1EwRkJSU3hEUVVGRExHbENRVUZwUWl4SFFVRkhMRkZCUVZFc1EwRkJReXhEUVVGRExFTkJRVU03YjBKQlEyaEVMRU5CUVVVc1EwRkJReXhGUVVGRkxFZEJRVk1zUTBGQlJTeERRVUZETEdsQ1FVRnBRaXhIUVVGSExGRkJRVkVzUTBGQlF5eERRVUZETEVOQlFVTTdaMEpCUXpGRUxFTkJRVU1zUTBGQlF5eERRVUZETzJGQlEwNDdXVUZEUkN4SlFVRkpMRTlCUVU4c1EwRkJReXhEUVVGRExFMUJRVTBzUzBGQlN5eFhRVUZYTEVWQlFVVTdaMEpCUTJwRExFTkJRVU1zUTBGQlF5eE5RVUZOTEVOQlFVTXNUMEZCVHl4RFFVRkRMRlZCUVVFc1EwRkJReXhKUVVGSkxFOUJRVUVzVFVGQlRTeERRVUZETEVsQlFVa3NRMEZCUXl4RFFVRkRMRVZCUVVVc1VVRkJVU3hEUVVGRExFVkJRWGhDTEVOQlFYZENMRU5CUVVNc1EwRkJRenRoUVVOdVJEdFRRVU5LTzJGQlFVMDdXVUZEUnl4RFFVRkZMRU5CUVVNc1JVRkJSU3hIUVVGSExGRkJRVkVzUTBGQlF5eERRVUZETEVOQlFVTTdXVUZEYmtJc1EwRkJSU3hEUVVGRExFVkJRVVVzUjBGQlJ5eFJRVUZSTEVOQlFVTXNRMEZCUXl4RFFVRkRPMU5CUXpWQ08wbEJRMHdzUTBGQlF6dEpRVWxOTEdOQlFVOHNSMEZCWkN4VlFVRmxMRU5CUVVNN1VVRkRXaXhKUVVGSkxFOUJRVThzUTBGQlF5eERRVUZETEVOQlFVTXNSVUZCUlR0WlFVTmFMRWxCUVVrc1QwRkJUeXhEUVVGRExFTkJRVU1zVFVGQlRTeExRVUZMTEZkQlFWY3NSVUZCUlR0blFrRkRha01zUTBGQlF5eERRVUZETEUxQlFVMHNRMEZCUXl4UFFVRlBMRU5CUVVNc1ZVRkJRU3hEUVVGRE8yOUNRVU5rTEUxQlFVMHNRMEZCUXl4UFFVRlBMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03YjBKQlEyeENMRTlCUVdFc1EwRkJSU3hEUVVGRExHbENRVUZwUWl4RFFVRkRPMjlDUVVOc1F5eFBRVUZoTEVOQlFVVXNRMEZCUXl4cFFrRkJhVUlzUTBGQlF6dG5Ra0ZEZEVNc1EwRkJReXhEUVVGRExFTkJRVU03WVVGRFRqdFpRVU5FTEVsQlFVa3NUMEZCVHl4RFFVRkRMRU5CUVVNc1RVRkJUU3hMUVVGTExGZEJRVmNzUlVGQlJUdG5Ra0ZEYWtNc1EwRkJReXhEUVVGRExFMUJRVTBzUTBGQlF5eFBRVUZQTEVOQlFVTXNUVUZCVFN4RFFVRkRMRTlCUVU4c1EwRkJReXhEUVVGRE8yRkJRM0JETzFOQlEwbzdZVUZCVFR0WlFVTklMRU5CUVVNc1EwRkJReXhMUVVGTExFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTTdVMEZGYWtJN1NVRkRUQ3hEUVVGRE8wbEJSMDBzWjBKQlFWTXNSMEZCYUVJc1ZVRkJhVUlzUTBGQlF6dFJRVU5rTEVOQlFVTXNRMEZCUXl4TFFVRkxMRWxCUVVrc1EwRkJReXhEUVVGRE8xRkJRMklzUTBGQlF5eERRVUZETEVWQlFVVXNSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF5eEZRVUZGTEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRKUVVNelFpeERRVUZETzBsQlIwMHNaVUZCVVN4SFFVRm1MRlZCUVdkQ0xFTkJRVU03VVVGRFlpeERRVUZETEVOQlFVTXNTMEZCU3l4SlFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRE8wbEJRMnhDTEVOQlFVTTdTVUZEVEN4aFFVRkRPMEZCUVVRc1EwRkJReXhCUVhaNVFrUXNTVUYxZVVKRE8wRkJkbmxDV1N4M1FrRkJUU0o5IiwiXCJ1c2Ugc3RyaWN0XCI7XHJcbk9iamVjdC5kZWZpbmVQcm9wZXJ0eShleHBvcnRzLCBcIl9fZXNNb2R1bGVcIiwgeyB2YWx1ZTogdHJ1ZSB9KTtcclxudmFyIHNob3J0ZXN0cGF0aHNfMSA9IHJlcXVpcmUoXCIuL3Nob3J0ZXN0cGF0aHNcIik7XHJcbnZhciBkZXNjZW50XzEgPSByZXF1aXJlKFwiLi9kZXNjZW50XCIpO1xyXG52YXIgcmVjdGFuZ2xlXzEgPSByZXF1aXJlKFwiLi9yZWN0YW5nbGVcIik7XHJcbnZhciBsaW5rbGVuZ3Roc18xID0gcmVxdWlyZShcIi4vbGlua2xlbmd0aHNcIik7XHJcbnZhciBMaW5rM0QgPSAoZnVuY3Rpb24gKCkge1xyXG4gICAgZnVuY3Rpb24gTGluazNEKHNvdXJjZSwgdGFyZ2V0KSB7XHJcbiAgICAgICAgdGhpcy5zb3VyY2UgPSBzb3VyY2U7XHJcbiAgICAgICAgdGhpcy50YXJnZXQgPSB0YXJnZXQ7XHJcbiAgICB9XHJcbiAgICBMaW5rM0QucHJvdG90eXBlLmFjdHVhbExlbmd0aCA9IGZ1bmN0aW9uICh4KSB7XHJcbiAgICAgICAgdmFyIF90aGlzID0gdGhpcztcclxuICAgICAgICByZXR1cm4gTWF0aC5zcXJ0KHgucmVkdWNlKGZ1bmN0aW9uIChjLCB2KSB7XHJcbiAgICAgICAgICAgIHZhciBkeCA9IHZbX3RoaXMudGFyZ2V0XSAtIHZbX3RoaXMuc291cmNlXTtcclxuICAgICAgICAgICAgcmV0dXJuIGMgKyBkeCAqIGR4O1xyXG4gICAgICAgIH0sIDApKTtcclxuICAgIH07XHJcbiAgICByZXR1cm4gTGluazNEO1xyXG59KCkpO1xyXG5leHBvcnRzLkxpbmszRCA9IExpbmszRDtcclxudmFyIE5vZGUzRCA9IChmdW5jdGlvbiAoKSB7XHJcbiAgICBmdW5jdGlvbiBOb2RlM0QoeCwgeSwgeikge1xyXG4gICAgICAgIGlmICh4ID09PSB2b2lkIDApIHsgeCA9IDA7IH1cclxuICAgICAgICBpZiAoeSA9PT0gdm9pZCAwKSB7IHkgPSAwOyB9XHJcbiAgICAgICAgaWYgKHogPT09IHZvaWQgMCkgeyB6ID0gMDsgfVxyXG4gICAgICAgIHRoaXMueCA9IHg7XHJcbiAgICAgICAgdGhpcy55ID0geTtcclxuICAgICAgICB0aGlzLnogPSB6O1xyXG4gICAgfVxyXG4gICAgcmV0dXJuIE5vZGUzRDtcclxufSgpKTtcclxuZXhwb3J0cy5Ob2RlM0QgPSBOb2RlM0Q7XHJcbnZhciBMYXlvdXQzRCA9IChmdW5jdGlvbiAoKSB7XHJcbiAgICBmdW5jdGlvbiBMYXlvdXQzRChub2RlcywgbGlua3MsIGlkZWFsTGlua0xlbmd0aCkge1xyXG4gICAgICAgIHZhciBfdGhpcyA9IHRoaXM7XHJcbiAgICAgICAgaWYgKGlkZWFsTGlua0xlbmd0aCA9PT0gdm9pZCAwKSB7IGlkZWFsTGlua0xlbmd0aCA9IDE7IH1cclxuICAgICAgICB0aGlzLm5vZGVzID0gbm9kZXM7XHJcbiAgICAgICAgdGhpcy5saW5rcyA9IGxpbmtzO1xyXG4gICAgICAgIHRoaXMuaWRlYWxMaW5rTGVuZ3RoID0gaWRlYWxMaW5rTGVuZ3RoO1xyXG4gICAgICAgIHRoaXMuY29uc3RyYWludHMgPSBudWxsO1xyXG4gICAgICAgIHRoaXMudXNlSmFjY2FyZExpbmtMZW5ndGhzID0gdHJ1ZTtcclxuICAgICAgICB0aGlzLnJlc3VsdCA9IG5ldyBBcnJheShMYXlvdXQzRC5rKTtcclxuICAgICAgICBmb3IgKHZhciBpID0gMDsgaSA8IExheW91dDNELms7ICsraSkge1xyXG4gICAgICAgICAgICB0aGlzLnJlc3VsdFtpXSA9IG5ldyBBcnJheShub2Rlcy5sZW5ndGgpO1xyXG4gICAgICAgIH1cclxuICAgICAgICBub2Rlcy5mb3JFYWNoKGZ1bmN0aW9uICh2LCBpKSB7XHJcbiAgICAgICAgICAgIGZvciAodmFyIF9pID0gMCwgX2EgPSBMYXlvdXQzRC5kaW1zOyBfaSA8IF9hLmxlbmd0aDsgX2krKykge1xyXG4gICAgICAgICAgICAgICAgdmFyIGRpbSA9IF9hW19pXTtcclxuICAgICAgICAgICAgICAgIGlmICh0eXBlb2YgdltkaW1dID09ICd1bmRlZmluZWQnKVxyXG4gICAgICAgICAgICAgICAgICAgIHZbZGltXSA9IE1hdGgucmFuZG9tKCk7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgX3RoaXMucmVzdWx0WzBdW2ldID0gdi54O1xyXG4gICAgICAgICAgICBfdGhpcy5yZXN1bHRbMV1baV0gPSB2Lnk7XHJcbiAgICAgICAgICAgIF90aGlzLnJlc3VsdFsyXVtpXSA9IHYuejtcclxuICAgICAgICB9KTtcclxuICAgIH1cclxuICAgIDtcclxuICAgIExheW91dDNELnByb3RvdHlwZS5saW5rTGVuZ3RoID0gZnVuY3Rpb24gKGwpIHtcclxuICAgICAgICByZXR1cm4gbC5hY3R1YWxMZW5ndGgodGhpcy5yZXN1bHQpO1xyXG4gICAgfTtcclxuICAgIExheW91dDNELnByb3RvdHlwZS5zdGFydCA9IGZ1bmN0aW9uIChpdGVyYXRpb25zKSB7XHJcbiAgICAgICAgdmFyIF90aGlzID0gdGhpcztcclxuICAgICAgICBpZiAoaXRlcmF0aW9ucyA9PT0gdm9pZCAwKSB7IGl0ZXJhdGlvbnMgPSAxMDA7IH1cclxuICAgICAgICB2YXIgbiA9IHRoaXMubm9kZXMubGVuZ3RoO1xyXG4gICAgICAgIHZhciBsaW5rQWNjZXNzb3IgPSBuZXcgTGlua0FjY2Vzc29yKCk7XHJcbiAgICAgICAgaWYgKHRoaXMudXNlSmFjY2FyZExpbmtMZW5ndGhzKVxyXG4gICAgICAgICAgICBsaW5rbGVuZ3Roc18xLmphY2NhcmRMaW5rTGVuZ3Rocyh0aGlzLmxpbmtzLCBsaW5rQWNjZXNzb3IsIDEuNSk7XHJcbiAgICAgICAgdGhpcy5saW5rcy5mb3JFYWNoKGZ1bmN0aW9uIChlKSB7IHJldHVybiBlLmxlbmd0aCAqPSBfdGhpcy5pZGVhbExpbmtMZW5ndGg7IH0pO1xyXG4gICAgICAgIHZhciBkaXN0YW5jZU1hdHJpeCA9IChuZXcgc2hvcnRlc3RwYXRoc18xLkNhbGN1bGF0b3IobiwgdGhpcy5saW5rcywgZnVuY3Rpb24gKGUpIHsgcmV0dXJuIGUuc291cmNlOyB9LCBmdW5jdGlvbiAoZSkgeyByZXR1cm4gZS50YXJnZXQ7IH0sIGZ1bmN0aW9uIChlKSB7IHJldHVybiBlLmxlbmd0aDsgfSkpLkRpc3RhbmNlTWF0cml4KCk7XHJcbiAgICAgICAgdmFyIEQgPSBkZXNjZW50XzEuRGVzY2VudC5jcmVhdGVTcXVhcmVNYXRyaXgobiwgZnVuY3Rpb24gKGksIGopIHsgcmV0dXJuIGRpc3RhbmNlTWF0cml4W2ldW2pdOyB9KTtcclxuICAgICAgICB2YXIgRyA9IGRlc2NlbnRfMS5EZXNjZW50LmNyZWF0ZVNxdWFyZU1hdHJpeChuLCBmdW5jdGlvbiAoKSB7IHJldHVybiAyOyB9KTtcclxuICAgICAgICB0aGlzLmxpbmtzLmZvckVhY2goZnVuY3Rpb24gKF9hKSB7XHJcbiAgICAgICAgICAgIHZhciBzb3VyY2UgPSBfYS5zb3VyY2UsIHRhcmdldCA9IF9hLnRhcmdldDtcclxuICAgICAgICAgICAgcmV0dXJuIEdbc291cmNlXVt0YXJnZXRdID0gR1t0YXJnZXRdW3NvdXJjZV0gPSAxO1xyXG4gICAgICAgIH0pO1xyXG4gICAgICAgIHRoaXMuZGVzY2VudCA9IG5ldyBkZXNjZW50XzEuRGVzY2VudCh0aGlzLnJlc3VsdCwgRCk7XHJcbiAgICAgICAgdGhpcy5kZXNjZW50LnRocmVzaG9sZCA9IDFlLTM7XHJcbiAgICAgICAgdGhpcy5kZXNjZW50LkcgPSBHO1xyXG4gICAgICAgIGlmICh0aGlzLmNvbnN0cmFpbnRzKVxyXG4gICAgICAgICAgICB0aGlzLmRlc2NlbnQucHJvamVjdCA9IG5ldyByZWN0YW5nbGVfMS5Qcm9qZWN0aW9uKHRoaXMubm9kZXMsIG51bGwsIG51bGwsIHRoaXMuY29uc3RyYWludHMpLnByb2plY3RGdW5jdGlvbnMoKTtcclxuICAgICAgICBmb3IgKHZhciBpID0gMDsgaSA8IHRoaXMubm9kZXMubGVuZ3RoOyBpKyspIHtcclxuICAgICAgICAgICAgdmFyIHYgPSB0aGlzLm5vZGVzW2ldO1xyXG4gICAgICAgICAgICBpZiAodi5maXhlZCkge1xyXG4gICAgICAgICAgICAgICAgdGhpcy5kZXNjZW50LmxvY2tzLmFkZChpLCBbdi54LCB2LnksIHYuel0pO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgfVxyXG4gICAgICAgIHRoaXMuZGVzY2VudC5ydW4oaXRlcmF0aW9ucyk7XHJcbiAgICAgICAgcmV0dXJuIHRoaXM7XHJcbiAgICB9O1xyXG4gICAgTGF5b3V0M0QucHJvdG90eXBlLnRpY2sgPSBmdW5jdGlvbiAoKSB7XHJcbiAgICAgICAgdGhpcy5kZXNjZW50LmxvY2tzLmNsZWFyKCk7XHJcbiAgICAgICAgZm9yICh2YXIgaSA9IDA7IGkgPCB0aGlzLm5vZGVzLmxlbmd0aDsgaSsrKSB7XHJcbiAgICAgICAgICAgIHZhciB2ID0gdGhpcy5ub2Rlc1tpXTtcclxuICAgICAgICAgICAgaWYgKHYuZml4ZWQpIHtcclxuICAgICAgICAgICAgICAgIHRoaXMuZGVzY2VudC5sb2Nrcy5hZGQoaSwgW3YueCwgdi55LCB2LnpdKTtcclxuICAgICAgICAgICAgfVxyXG4gICAgICAgIH1cclxuICAgICAgICByZXR1cm4gdGhpcy5kZXNjZW50LnJ1bmdlS3V0dGEoKTtcclxuICAgIH07XHJcbiAgICBMYXlvdXQzRC5kaW1zID0gWyd4JywgJ3knLCAneiddO1xyXG4gICAgTGF5b3V0M0QuayA9IExheW91dDNELmRpbXMubGVuZ3RoO1xyXG4gICAgcmV0dXJuIExheW91dDNEO1xyXG59KCkpO1xyXG5leHBvcnRzLkxheW91dDNEID0gTGF5b3V0M0Q7XHJcbnZhciBMaW5rQWNjZXNzb3IgPSAoZnVuY3Rpb24gKCkge1xyXG4gICAgZnVuY3Rpb24gTGlua0FjY2Vzc29yKCkge1xyXG4gICAgfVxyXG4gICAgTGlua0FjY2Vzc29yLnByb3RvdHlwZS5nZXRTb3VyY2VJbmRleCA9IGZ1bmN0aW9uIChlKSB7IHJldHVybiBlLnNvdXJjZTsgfTtcclxuICAgIExpbmtBY2Nlc3Nvci5wcm90b3R5cGUuZ2V0VGFyZ2V0SW5kZXggPSBmdW5jdGlvbiAoZSkgeyByZXR1cm4gZS50YXJnZXQ7IH07XHJcbiAgICBMaW5rQWNjZXNzb3IucHJvdG90eXBlLmdldExlbmd0aCA9IGZ1bmN0aW9uIChlKSB7IHJldHVybiBlLmxlbmd0aDsgfTtcclxuICAgIExpbmtBY2Nlc3Nvci5wcm90b3R5cGUuc2V0TGVuZ3RoID0gZnVuY3Rpb24gKGUsIGwpIHsgZS5sZW5ndGggPSBsOyB9O1xyXG4gICAgcmV0dXJuIExpbmtBY2Nlc3NvcjtcclxufSgpKTtcclxuLy8jIHNvdXJjZU1hcHBpbmdVUkw9ZGF0YTphcHBsaWNhdGlvbi9qc29uO2Jhc2U2NCxleUoyWlhKemFXOXVJam96TENKbWFXeGxJam9pYkdGNWIzVjBNMlF1YW5NaUxDSnpiM1Z5WTJWU2IyOTBJam9pSWl3aWMyOTFjbU5sY3lJNld5SXVMaTh1TGk5WFpXSkRiMnhoTDNOeVl5OXNZWGx2ZFhRelpDNTBjeUpkTENKdVlXMWxjeUk2VzEwc0ltMWhjSEJwYm1keklqb2lPenRCUVVGQkxHbEVRVUV3UXp0QlFVTXhReXh4UTBGQmFVTTdRVUZEYWtNc2VVTkJRVFJFTzBGQlJUVkVMRFpEUVVGdlJUdEJRVVZ3UlR0SlFVVlJMR2RDUVVGdFFpeE5RVUZqTEVWQlFWTXNUVUZCWXp0UlFVRnlReXhYUVVGTkxFZEJRVTRzVFVGQlRTeERRVUZSTzFGQlFWTXNWMEZCVFN4SFFVRk9MRTFCUVUwc1EwRkJVVHRKUVVGSkxFTkJRVU03U1VGRE4wUXNOa0pCUVZrc1IwRkJXaXhWUVVGaExFTkJRV0U3VVVGQk1VSXNhVUpCVFVNN1VVRk1SeXhQUVVGUExFbEJRVWtzUTBGQlF5eEpRVUZKTEVOQlExb3NRMEZCUXl4RFFVRkRMRTFCUVUwc1EwRkJReXhWUVVGRExFTkJRVk1zUlVGQlJTeERRVUZYTzFsQlF6VkNMRWxCUVUwc1JVRkJSU3hIUVVGSExFTkJRVU1zUTBGQlF5eExRVUZKTEVOQlFVTXNUVUZCVFN4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFdEJRVWtzUTBGQlF5eE5RVUZOTEVOQlFVTXNRMEZCUXp0WlFVTXpReXhQUVVGUExFTkJRVU1zUjBGQlJ5eEZRVUZGTEVkQlFVY3NSVUZCUlN4RFFVRkRPMUZCUTNaQ0xFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMGxCUTJZc1EwRkJRenRKUVVOTUxHRkJRVU03UVVGQlJDeERRVUZETEVGQlZrd3NTVUZWU3p0QlFWWlJMSGRDUVVGTk8wRkJWMlk3U1VGVFNTeG5Ra0ZEVnl4RFFVRmhMRVZCUTJJc1EwRkJZU3hGUVVOaUxFTkJRV0U3VVVGR1lpeHJRa0ZCUVN4RlFVRkJMRXRCUVdFN1VVRkRZaXhyUWtGQlFTeEZRVUZCTEV0QlFXRTdVVUZEWWl4clFrRkJRU3hGUVVGQkxFdEJRV0U3VVVGR1lpeE5RVUZETEVkQlFVUXNRMEZCUXl4RFFVRlpPMUZCUTJJc1RVRkJReXhIUVVGRUxFTkJRVU1zUTBGQldUdFJRVU5pTEUxQlFVTXNSMEZCUkN4RFFVRkRMRU5CUVZrN1NVRkJTU3hEUVVGRE8wbEJRMnBETEdGQlFVTTdRVUZCUkN4RFFVRkRMRUZCWWtRc1NVRmhRenRCUVdKWkxIZENRVUZOTzBGQlkyNUNPMGxCVFVrc2EwSkJRVzFDTEV0QlFXVXNSVUZCVXl4TFFVRmxMRVZCUVZNc1pVRkJNa0k3VVVGQk9VWXNhVUpCWVVNN1VVRmlhMFVzWjBOQlFVRXNSVUZCUVN4dFFrRkJNa0k3VVVGQk0wVXNWVUZCU3l4SFFVRk1MRXRCUVVzc1EwRkJWVHRSUVVGVExGVkJRVXNzUjBGQlRDeExRVUZMTEVOQlFWVTdVVUZCVXl4dlFrRkJaU3hIUVVGbUxHVkJRV1VzUTBGQldUdFJRVVk1Uml4blFrRkJWeXhIUVVGVkxFbEJRVWtzUTBGQlF6dFJRWEZDTVVJc01FSkJRWEZDTEVkQlFWa3NTVUZCU1N4RFFVRkRPMUZCYkVKc1F5eEpRVUZKTEVOQlFVTXNUVUZCVFN4SFFVRkhMRWxCUVVrc1MwRkJTeXhEUVVGRExGRkJRVkVzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0UlFVTndReXhMUVVGTExFbEJRVWtzUTBGQlF5eEhRVUZITEVOQlFVTXNSVUZCUlN4RFFVRkRMRWRCUVVjc1VVRkJVU3hEUVVGRExFTkJRVU1zUlVGQlJTeEZRVUZGTEVOQlFVTXNSVUZCUlR0WlFVTnFReXhKUVVGSkxFTkJRVU1zVFVGQlRTeERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRWxCUVVrc1MwRkJTeXhEUVVGRExFdEJRVXNzUTBGQlF5eE5RVUZOTEVOQlFVTXNRMEZCUXp0VFFVTTFRenRSUVVORUxFdEJRVXNzUTBGQlF5eFBRVUZQTEVOQlFVTXNWVUZCUXl4RFFVRkRMRVZCUVVVc1EwRkJRenRaUVVObUxFdEJRV2RDTEZWQlFXRXNSVUZCWWl4TFFVRkJMRkZCUVZFc1EwRkJReXhKUVVGSkxFVkJRV0lzWTBGQllTeEZRVUZpTEVsQlFXRXNSVUZCUlR0blFrRkJNVUlzU1VGQlNTeEhRVUZITEZOQlFVRTdaMEpCUTFJc1NVRkJTU3hQUVVGUExFTkJRVU1zUTBGQlF5eEhRVUZITEVOQlFVTXNTVUZCU1N4WFFVRlhPMjlDUVVGRkxFTkJRVU1zUTBGQlF5eEhRVUZITEVOQlFVTXNSMEZCUnl4SlFVRkpMRU5CUVVNc1RVRkJUU3hGUVVGRkxFTkJRVU03WVVGRE5VUTdXVUZEUkN4TFFVRkpMRU5CUVVNc1RVRkJUU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03V1VGRGVFSXNTMEZCU1N4RFFVRkRMRTFCUVUwc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8xbEJRM2hDTEV0QlFVa3NRMEZCUXl4TlFVRk5MRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRSUVVNMVFpeERRVUZETEVOQlFVTXNRMEZCUXp0SlFVTlFMRU5CUVVNN1NVRkJRU3hEUVVGRE8wbEJSVVlzTmtKQlFWVXNSMEZCVml4VlFVRlhMRU5CUVZNN1VVRkRhRUlzVDBGQlR5eERRVUZETEVOQlFVTXNXVUZCV1N4RFFVRkRMRWxCUVVrc1EwRkJReXhOUVVGTkxFTkJRVU1zUTBGQlF6dEpRVU4yUXl4RFFVRkRPMGxCUzBRc2QwSkJRVXNzUjBGQlRDeFZRVUZOTEZWQlFYZENPMUZCUVRsQ0xHbENRWFZEUXp0UlFYWkRTeXd5UWtGQlFTeEZRVUZCTEdkQ1FVRjNRanRSUVVNeFFpeEpRVUZOTEVOQlFVTXNSMEZCUnl4SlFVRkpMRU5CUVVNc1MwRkJTeXhEUVVGRExFMUJRVTBzUTBGQlF6dFJRVVUxUWl4SlFVRkpMRmxCUVZrc1IwRkJSeXhKUVVGSkxGbEJRVmtzUlVGQlJTeERRVUZETzFGQlJYUkRMRWxCUVVrc1NVRkJTU3hEUVVGRExIRkNRVUZ4UWp0WlFVTXhRaXhuUTBGQmEwSXNRMEZCUXl4SlFVRkpMRU5CUVVNc1MwRkJTeXhGUVVGRkxGbEJRVmtzUlVGQlJTeEhRVUZITEVOQlFVTXNRMEZCUXp0UlFVVjBSQ3hKUVVGSkxFTkJRVU1zUzBGQlN5eERRVUZETEU5QlFVOHNRMEZCUXl4VlFVRkJMRU5CUVVNc1NVRkJTU3hQUVVGQkxFTkJRVU1zUTBGQlF5eE5RVUZOTEVsQlFVa3NTMEZCU1N4RFFVRkRMR1ZCUVdVc1JVRkJhRU1zUTBGQlowTXNRMEZCUXl4RFFVRkRPMUZCUnpGRUxFbEJRVTBzWTBGQll5eEhRVUZITEVOQlFVTXNTVUZCU1N3d1FrRkJWU3hEUVVGRExFTkJRVU1zUlVGQlJTeEpRVUZKTEVOQlFVTXNTMEZCU3l4RlFVTm9SQ3hWUVVGQkxFTkJRVU1zU1VGQlJ5eFBRVUZCTEVOQlFVTXNRMEZCUXl4TlFVRk5MRVZCUVZJc1EwRkJVU3hGUVVGRkxGVkJRVUVzUTBGQlF5eEpRVUZITEU5QlFVRXNRMEZCUXl4RFFVRkRMRTFCUVUwc1JVRkJVaXhEUVVGUkxFVkJRVVVzVlVGQlFTeERRVUZETEVsQlFVa3NUMEZCUVN4RFFVRkRMRU5CUVVNc1RVRkJUU3hGUVVGU0xFTkJRVkVzUTBGQlF5eERRVUZETEVOQlFVTXNZMEZCWXl4RlFVRkZMRU5CUVVNN1VVRkZha1VzU1VGQlRTeERRVUZETEVkQlFVY3NhVUpCUVU4c1EwRkJReXhyUWtGQmEwSXNRMEZCUXl4RFFVRkRMRVZCUVVVc1ZVRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eEpRVUZMTEU5QlFVRXNZMEZCWXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEZRVUZ3UWl4RFFVRnZRaXhEUVVGRExFTkJRVU03VVVGSmVFVXNTVUZCU1N4RFFVRkRMRWRCUVVjc2FVSkJRVThzUTBGQlF5eHJRa0ZCYTBJc1EwRkJReXhEUVVGRExFVkJRVVVzWTBGQll5eFBRVUZQTEVOQlFVTXNRMEZCUVN4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8xRkJRMmhGTEVsQlFVa3NRMEZCUXl4TFFVRkxMRU5CUVVNc1QwRkJUeXhEUVVGRExGVkJRVU1zUlVGQmEwSTdaMEpCUVdoQ0xHdENRVUZOTEVWQlFVVXNhMEpCUVUwN1dVRkJUeXhQUVVGQkxFTkJRVU1zUTBGQlF5eE5RVUZOTEVOQlFVTXNRMEZCUXl4TlFVRk5MRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zVFVGQlRTeERRVUZETEVOQlFVTXNUVUZCVFN4RFFVRkRMRWRCUVVjc1EwRkJRenRSUVVGNlF5eERRVUY1UXl4RFFVRkRMRU5CUVVNN1VVRkZkRVlzU1VGQlNTeERRVUZETEU5QlFVOHNSMEZCUnl4SlFVRkpMR2xDUVVGUExFTkJRVU1zU1VGQlNTeERRVUZETEUxQlFVMHNSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJRenRSUVVNelF5eEpRVUZKTEVOQlFVTXNUMEZCVHl4RFFVRkRMRk5CUVZNc1IwRkJSeXhKUVVGSkxFTkJRVU03VVVGRE9VSXNTVUZCU1N4RFFVRkRMRTlCUVU4c1EwRkJReXhEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETzFGQlNXNUNMRWxCUVVrc1NVRkJTU3hEUVVGRExGZEJRVmM3V1VGRGFFSXNTVUZCU1N4RFFVRkRMRTlCUVU4c1EwRkJReXhQUVVGUExFZEJRVWNzU1VGQlNTeHpRa0ZCVlN4RFFVRmpMRWxCUVVrc1EwRkJReXhMUVVGTExFVkJRVVVzU1VGQlNTeEZRVUZGTEVsQlFVa3NSVUZCUlN4SlFVRkpMRU5CUVVNc1YwRkJWeXhEUVVGRExFTkJRVU1zWjBKQlFXZENMRVZCUVVVc1EwRkJRenRSUVVWd1NDeExRVUZMTEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1JVRkJSU3hEUVVGRExFZEJRVWNzU1VGQlNTeERRVUZETEV0QlFVc3NRMEZCUXl4TlFVRk5MRVZCUVVVc1EwRkJReXhGUVVGRkxFVkJRVVU3V1VGRGVFTXNTVUZCU1N4RFFVRkRMRWRCUVVjc1NVRkJTU3hEUVVGRExFdEJRVXNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0WlFVTjBRaXhKUVVGSkxFTkJRVU1zUTBGQlF5eExRVUZMTEVWQlFVVTdaMEpCUTFRc1NVRkJTU3hEUVVGRExFOUJRVThzUTBGQlF5eExRVUZMTEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0aFFVTTVRenRUUVVOS08xRkJSVVFzU1VGQlNTeERRVUZETEU5QlFVOHNRMEZCUXl4SFFVRkhMRU5CUVVNc1ZVRkJWU3hEUVVGRExFTkJRVU03VVVGRE4wSXNUMEZCVHl4SlFVRkpMRU5CUVVNN1NVRkRhRUlzUTBGQlF6dEpRVVZFTEhWQ1FVRkpMRWRCUVVvN1VVRkRTU3hKUVVGSkxFTkJRVU1zVDBGQlR5eERRVUZETEV0QlFVc3NRMEZCUXl4TFFVRkxMRVZCUVVVc1EwRkJRenRSUVVNelFpeExRVUZMTEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1JVRkJSU3hEUVVGRExFZEJRVWNzU1VGQlNTeERRVUZETEV0QlFVc3NRMEZCUXl4TlFVRk5MRVZCUVVVc1EwRkJReXhGUVVGRkxFVkJRVVU3V1VGRGVFTXNTVUZCU1N4RFFVRkRMRWRCUVVjc1NVRkJTU3hEUVVGRExFdEJRVXNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0WlFVTjBRaXhKUVVGSkxFTkJRVU1zUTBGQlF5eExRVUZMTEVWQlFVVTdaMEpCUTFRc1NVRkJTU3hEUVVGRExFOUJRVThzUTBGQlF5eExRVUZMTEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0aFFVTTVRenRUUVVOS08xRkJRMFFzVDBGQlR5eEpRVUZKTEVOQlFVTXNUMEZCVHl4RFFVRkRMRlZCUVZVc1JVRkJSU3hEUVVGRE8wbEJRM0pETEVOQlFVTTdTVUUzUlUwc1lVRkJTU3hIUVVGSExFTkJRVU1zUjBGQlJ5eEZRVUZGTEVkQlFVY3NSVUZCUlN4SFFVRkhMRU5CUVVNc1EwRkJRenRKUVVOMlFpeFZRVUZETEVkQlFVY3NVVUZCVVN4RFFVRkRMRWxCUVVrc1EwRkJReXhOUVVGTkxFTkJRVU03U1VFMlJYQkRMR1ZCUVVNN1EwRkJRU3hCUVM5RlJDeEpRU3RGUXp0QlFTOUZXU3cwUWtGQlVUdEJRV2xHY2tJN1NVRkJRVHRKUVV0QkxFTkJRVU03U1VGS1J5eHhRMEZCWXl4SFFVRmtMRlZCUVdVc1EwRkJUU3hKUVVGWkxFOUJRVThzUTBGQlF5eERRVUZETEUxQlFVMHNRMEZCUXl4RFFVRkRMRU5CUVVNN1NVRkRia1FzY1VOQlFXTXNSMEZCWkN4VlFVRmxMRU5CUVUwc1NVRkJXU3hQUVVGUExFTkJRVU1zUTBGQlF5eE5RVUZOTEVOQlFVTXNRMEZCUXl4RFFVRkRPMGxCUTI1RUxHZERRVUZUTEVkQlFWUXNWVUZCVlN4RFFVRk5MRWxCUVZrc1QwRkJUeXhEUVVGRExFTkJRVU1zVFVGQlRTeERRVUZETEVOQlFVTXNRMEZCUXp0SlFVTTVReXhuUTBGQlV5eEhRVUZVTEZWQlFWVXNRMEZCVFN4RlFVRkZMRU5CUVZNc1NVRkJTU3hEUVVGRExFTkJRVU1zVFVGQlRTeEhRVUZITEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1NVRkRiRVFzYlVKQlFVTTdRVUZCUkN4RFFVRkRMRUZCVEVRc1NVRkxReUo5IiwiXCJ1c2Ugc3RyaWN0XCI7XHJcbk9iamVjdC5kZWZpbmVQcm9wZXJ0eShleHBvcnRzLCBcIl9fZXNNb2R1bGVcIiwgeyB2YWx1ZTogdHJ1ZSB9KTtcclxuZnVuY3Rpb24gdW5pb25Db3VudChhLCBiKSB7XHJcbiAgICB2YXIgdSA9IHt9O1xyXG4gICAgZm9yICh2YXIgaSBpbiBhKVxyXG4gICAgICAgIHVbaV0gPSB7fTtcclxuICAgIGZvciAodmFyIGkgaW4gYilcclxuICAgICAgICB1W2ldID0ge307XHJcbiAgICByZXR1cm4gT2JqZWN0LmtleXModSkubGVuZ3RoO1xyXG59XHJcbmZ1bmN0aW9uIGludGVyc2VjdGlvbkNvdW50KGEsIGIpIHtcclxuICAgIHZhciBuID0gMDtcclxuICAgIGZvciAodmFyIGkgaW4gYSlcclxuICAgICAgICBpZiAodHlwZW9mIGJbaV0gIT09ICd1bmRlZmluZWQnKVxyXG4gICAgICAgICAgICArK247XHJcbiAgICByZXR1cm4gbjtcclxufVxyXG5mdW5jdGlvbiBnZXROZWlnaGJvdXJzKGxpbmtzLCBsYSkge1xyXG4gICAgdmFyIG5laWdoYm91cnMgPSB7fTtcclxuICAgIHZhciBhZGROZWlnaGJvdXJzID0gZnVuY3Rpb24gKHUsIHYpIHtcclxuICAgICAgICBpZiAodHlwZW9mIG5laWdoYm91cnNbdV0gPT09ICd1bmRlZmluZWQnKVxyXG4gICAgICAgICAgICBuZWlnaGJvdXJzW3VdID0ge307XHJcbiAgICAgICAgbmVpZ2hib3Vyc1t1XVt2XSA9IHt9O1xyXG4gICAgfTtcclxuICAgIGxpbmtzLmZvckVhY2goZnVuY3Rpb24gKGUpIHtcclxuICAgICAgICB2YXIgdSA9IGxhLmdldFNvdXJjZUluZGV4KGUpLCB2ID0gbGEuZ2V0VGFyZ2V0SW5kZXgoZSk7XHJcbiAgICAgICAgYWRkTmVpZ2hib3Vycyh1LCB2KTtcclxuICAgICAgICBhZGROZWlnaGJvdXJzKHYsIHUpO1xyXG4gICAgfSk7XHJcbiAgICByZXR1cm4gbmVpZ2hib3VycztcclxufVxyXG5mdW5jdGlvbiBjb21wdXRlTGlua0xlbmd0aHMobGlua3MsIHcsIGYsIGxhKSB7XHJcbiAgICB2YXIgbmVpZ2hib3VycyA9IGdldE5laWdoYm91cnMobGlua3MsIGxhKTtcclxuICAgIGxpbmtzLmZvckVhY2goZnVuY3Rpb24gKGwpIHtcclxuICAgICAgICB2YXIgYSA9IG5laWdoYm91cnNbbGEuZ2V0U291cmNlSW5kZXgobCldO1xyXG4gICAgICAgIHZhciBiID0gbmVpZ2hib3Vyc1tsYS5nZXRUYXJnZXRJbmRleChsKV07XHJcbiAgICAgICAgbGEuc2V0TGVuZ3RoKGwsIDEgKyB3ICogZihhLCBiKSk7XHJcbiAgICB9KTtcclxufVxyXG5mdW5jdGlvbiBzeW1tZXRyaWNEaWZmTGlua0xlbmd0aHMobGlua3MsIGxhLCB3KSB7XHJcbiAgICBpZiAodyA9PT0gdm9pZCAwKSB7IHcgPSAxOyB9XHJcbiAgICBjb21wdXRlTGlua0xlbmd0aHMobGlua3MsIHcsIGZ1bmN0aW9uIChhLCBiKSB7IHJldHVybiBNYXRoLnNxcnQodW5pb25Db3VudChhLCBiKSAtIGludGVyc2VjdGlvbkNvdW50KGEsIGIpKTsgfSwgbGEpO1xyXG59XHJcbmV4cG9ydHMuc3ltbWV0cmljRGlmZkxpbmtMZW5ndGhzID0gc3ltbWV0cmljRGlmZkxpbmtMZW5ndGhzO1xyXG5mdW5jdGlvbiBqYWNjYXJkTGlua0xlbmd0aHMobGlua3MsIGxhLCB3KSB7XHJcbiAgICBpZiAodyA9PT0gdm9pZCAwKSB7IHcgPSAxOyB9XHJcbiAgICBjb21wdXRlTGlua0xlbmd0aHMobGlua3MsIHcsIGZ1bmN0aW9uIChhLCBiKSB7XHJcbiAgICAgICAgcmV0dXJuIE1hdGgubWluKE9iamVjdC5rZXlzKGEpLmxlbmd0aCwgT2JqZWN0LmtleXMoYikubGVuZ3RoKSA8IDEuMSA/IDAgOiBpbnRlcnNlY3Rpb25Db3VudChhLCBiKSAvIHVuaW9uQ291bnQoYSwgYik7XHJcbiAgICB9LCBsYSk7XHJcbn1cclxuZXhwb3J0cy5qYWNjYXJkTGlua0xlbmd0aHMgPSBqYWNjYXJkTGlua0xlbmd0aHM7XHJcbmZ1bmN0aW9uIGdlbmVyYXRlRGlyZWN0ZWRFZGdlQ29uc3RyYWludHMobiwgbGlua3MsIGF4aXMsIGxhKSB7XHJcbiAgICB2YXIgY29tcG9uZW50cyA9IHN0cm9uZ2x5Q29ubmVjdGVkQ29tcG9uZW50cyhuLCBsaW5rcywgbGEpO1xyXG4gICAgdmFyIG5vZGVzID0ge307XHJcbiAgICBjb21wb25lbnRzLmZvckVhY2goZnVuY3Rpb24gKGMsIGkpIHtcclxuICAgICAgICByZXR1cm4gYy5mb3JFYWNoKGZ1bmN0aW9uICh2KSB7IHJldHVybiBub2Rlc1t2XSA9IGk7IH0pO1xyXG4gICAgfSk7XHJcbiAgICB2YXIgY29uc3RyYWludHMgPSBbXTtcclxuICAgIGxpbmtzLmZvckVhY2goZnVuY3Rpb24gKGwpIHtcclxuICAgICAgICB2YXIgdWkgPSBsYS5nZXRTb3VyY2VJbmRleChsKSwgdmkgPSBsYS5nZXRUYXJnZXRJbmRleChsKSwgdSA9IG5vZGVzW3VpXSwgdiA9IG5vZGVzW3ZpXTtcclxuICAgICAgICBpZiAodSAhPT0gdikge1xyXG4gICAgICAgICAgICBjb25zdHJhaW50cy5wdXNoKHtcclxuICAgICAgICAgICAgICAgIGF4aXM6IGF4aXMsXHJcbiAgICAgICAgICAgICAgICBsZWZ0OiB1aSxcclxuICAgICAgICAgICAgICAgIHJpZ2h0OiB2aSxcclxuICAgICAgICAgICAgICAgIGdhcDogbGEuZ2V0TWluU2VwYXJhdGlvbihsKVxyXG4gICAgICAgICAgICB9KTtcclxuICAgICAgICB9XHJcbiAgICB9KTtcclxuICAgIHJldHVybiBjb25zdHJhaW50cztcclxufVxyXG5leHBvcnRzLmdlbmVyYXRlRGlyZWN0ZWRFZGdlQ29uc3RyYWludHMgPSBnZW5lcmF0ZURpcmVjdGVkRWRnZUNvbnN0cmFpbnRzO1xyXG5mdW5jdGlvbiBzdHJvbmdseUNvbm5lY3RlZENvbXBvbmVudHMobnVtVmVydGljZXMsIGVkZ2VzLCBsYSkge1xyXG4gICAgdmFyIG5vZGVzID0gW107XHJcbiAgICB2YXIgaW5kZXggPSAwO1xyXG4gICAgdmFyIHN0YWNrID0gW107XHJcbiAgICB2YXIgY29tcG9uZW50cyA9IFtdO1xyXG4gICAgZnVuY3Rpb24gc3Ryb25nQ29ubmVjdCh2KSB7XHJcbiAgICAgICAgdi5pbmRleCA9IHYubG93bGluayA9IGluZGV4Kys7XHJcbiAgICAgICAgc3RhY2sucHVzaCh2KTtcclxuICAgICAgICB2Lm9uU3RhY2sgPSB0cnVlO1xyXG4gICAgICAgIGZvciAodmFyIF9pID0gMCwgX2EgPSB2Lm91dDsgX2kgPCBfYS5sZW5ndGg7IF9pKyspIHtcclxuICAgICAgICAgICAgdmFyIHcgPSBfYVtfaV07XHJcbiAgICAgICAgICAgIGlmICh0eXBlb2Ygdy5pbmRleCA9PT0gJ3VuZGVmaW5lZCcpIHtcclxuICAgICAgICAgICAgICAgIHN0cm9uZ0Nvbm5lY3Qodyk7XHJcbiAgICAgICAgICAgICAgICB2Lmxvd2xpbmsgPSBNYXRoLm1pbih2Lmxvd2xpbmssIHcubG93bGluayk7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgZWxzZSBpZiAody5vblN0YWNrKSB7XHJcbiAgICAgICAgICAgICAgICB2Lmxvd2xpbmsgPSBNYXRoLm1pbih2Lmxvd2xpbmssIHcuaW5kZXgpO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgfVxyXG4gICAgICAgIGlmICh2Lmxvd2xpbmsgPT09IHYuaW5kZXgpIHtcclxuICAgICAgICAgICAgdmFyIGNvbXBvbmVudCA9IFtdO1xyXG4gICAgICAgICAgICB3aGlsZSAoc3RhY2subGVuZ3RoKSB7XHJcbiAgICAgICAgICAgICAgICB3ID0gc3RhY2sucG9wKCk7XHJcbiAgICAgICAgICAgICAgICB3Lm9uU3RhY2sgPSBmYWxzZTtcclxuICAgICAgICAgICAgICAgIGNvbXBvbmVudC5wdXNoKHcpO1xyXG4gICAgICAgICAgICAgICAgaWYgKHcgPT09IHYpXHJcbiAgICAgICAgICAgICAgICAgICAgYnJlYWs7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgY29tcG9uZW50cy5wdXNoKGNvbXBvbmVudC5tYXAoZnVuY3Rpb24gKHYpIHsgcmV0dXJuIHYuaWQ7IH0pKTtcclxuICAgICAgICB9XHJcbiAgICB9XHJcbiAgICBmb3IgKHZhciBpID0gMDsgaSA8IG51bVZlcnRpY2VzOyBpKyspIHtcclxuICAgICAgICBub2Rlcy5wdXNoKHsgaWQ6IGksIG91dDogW10gfSk7XHJcbiAgICB9XHJcbiAgICBmb3IgKHZhciBfaSA9IDAsIGVkZ2VzXzEgPSBlZGdlczsgX2kgPCBlZGdlc18xLmxlbmd0aDsgX2krKykge1xyXG4gICAgICAgIHZhciBlID0gZWRnZXNfMVtfaV07XHJcbiAgICAgICAgdmFyIHZfMSA9IG5vZGVzW2xhLmdldFNvdXJjZUluZGV4KGUpXSwgdyA9IG5vZGVzW2xhLmdldFRhcmdldEluZGV4KGUpXTtcclxuICAgICAgICB2XzEub3V0LnB1c2godyk7XHJcbiAgICB9XHJcbiAgICBmb3IgKHZhciBfYSA9IDAsIG5vZGVzXzEgPSBub2RlczsgX2EgPCBub2Rlc18xLmxlbmd0aDsgX2ErKykge1xyXG4gICAgICAgIHZhciB2ID0gbm9kZXNfMVtfYV07XHJcbiAgICAgICAgaWYgKHR5cGVvZiB2LmluZGV4ID09PSAndW5kZWZpbmVkJylcclxuICAgICAgICAgICAgc3Ryb25nQ29ubmVjdCh2KTtcclxuICAgIH1cclxuICAgIHJldHVybiBjb21wb25lbnRzO1xyXG59XHJcbmV4cG9ydHMuc3Ryb25nbHlDb25uZWN0ZWRDb21wb25lbnRzID0gc3Ryb25nbHlDb25uZWN0ZWRDb21wb25lbnRzO1xyXG4vLyMgc291cmNlTWFwcGluZ1VSTD1kYXRhOmFwcGxpY2F0aW9uL2pzb247YmFzZTY0LGV5SjJaWEp6YVc5dUlqb3pMQ0ptYVd4bElqb2liR2x1YTJ4bGJtZDBhSE11YW5NaUxDSnpiM1Z5WTJWU2IyOTBJam9pSWl3aWMyOTFjbU5sY3lJNld5SXVMaTh1TGk5WFpXSkRiMnhoTDNOeVl5OXNhVzVyYkdWdVozUm9jeTUwY3lKZExDSnVZVzFsY3lJNlcxMHNJbTFoY0hCcGJtZHpJam9pT3p0QlFWVkpMRk5CUVZNc1ZVRkJWU3hEUVVGRExFTkJRVTBzUlVGQlJTeERRVUZOTzBsQlF6bENMRWxCUVVrc1EwRkJReXhIUVVGSExFVkJRVVVzUTBGQlF6dEpRVU5ZTEV0QlFVc3NTVUZCU1N4RFFVRkRMRWxCUVVrc1EwRkJRenRSUVVGRkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4RlFVRkZMRU5CUVVNN1NVRkRNMElzUzBGQlN5eEpRVUZKTEVOQlFVTXNTVUZCU1N4RFFVRkRPMUZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEhRVUZITEVWQlFVVXNRMEZCUXp0SlFVTXpRaXhQUVVGUExFMUJRVTBzUTBGQlF5eEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1RVRkJUU3hEUVVGRE8wRkJRMnBETEVOQlFVTTdRVUZIUkN4VFFVRlRMR2xDUVVGcFFpeERRVUZETEVOQlFWY3NSVUZCUlN4RFFVRlhPMGxCUXk5RExFbEJRVWtzUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXp0SlFVTldMRXRCUVVzc1NVRkJTU3hEUVVGRExFbEJRVWtzUTBGQlF6dFJRVUZGTEVsQlFVa3NUMEZCVHl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFdEJRVXNzVjBGQlZ6dFpRVUZGTEVWQlFVVXNRMEZCUXl4RFFVRkRPMGxCUTNSRUxFOUJRVThzUTBGQlF5eERRVUZETzBGQlEySXNRMEZCUXp0QlFVVkVMRk5CUVZNc1lVRkJZU3hEUVVGUExFdEJRV0VzUlVGQlJTeEZRVUZ6UWp0SlFVTTVSQ3hKUVVGSkxGVkJRVlVzUjBGQlJ5eEZRVUZGTEVOQlFVTTdTVUZEY0VJc1NVRkJTU3hoUVVGaExFZEJRVWNzVlVGQlF5eERRVUZETEVWQlFVVXNRMEZCUXp0UlFVTnlRaXhKUVVGSkxFOUJRVThzVlVGQlZTeERRVUZETEVOQlFVTXNRMEZCUXl4TFFVRkxMRmRCUVZjN1dVRkRjRU1zVlVGQlZTeERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRVZCUVVVc1EwRkJRenRSUVVOMlFpeFZRVUZWTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFZEJRVWNzUlVGQlJTeERRVUZETzBsQlF6RkNMRU5CUVVNc1EwRkJRenRKUVVOR0xFdEJRVXNzUTBGQlF5eFBRVUZQTEVOQlFVTXNWVUZCUVN4RFFVRkRPMUZCUTFnc1NVRkJTU3hEUVVGRExFZEJRVWNzUlVGQlJTeERRVUZETEdOQlFXTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFZEJRVWNzUlVGQlJTeERRVUZETEdOQlFXTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRSUVVOMlJDeGhRVUZoTEVOQlFVTXNRMEZCUXl4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRE8xRkJRM0JDTEdGQlFXRXNRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU03U1VGRGVFSXNRMEZCUXl4RFFVRkRMRU5CUVVNN1NVRkRTQ3hQUVVGUExGVkJRVlVzUTBGQlF6dEJRVU4wUWl4RFFVRkRPMEZCUjBRc1UwRkJVeXhyUWtGQmEwSXNRMEZCVHl4TFFVRmhMRVZCUVVVc1EwRkJVeXhGUVVGRkxFTkJRVFpDTEVWQlFVVXNSVUZCTkVJN1NVRkRia2dzU1VGQlNTeFZRVUZWTEVkQlFVY3NZVUZCWVN4RFFVRkRMRXRCUVVzc1JVRkJSU3hGUVVGRkxFTkJRVU1zUTBGQlF6dEpRVU14UXl4TFFVRkxMRU5CUVVNc1QwRkJUeXhEUVVGRExGVkJRVUVzUTBGQlF6dFJRVU5ZTEVsQlFVa3NRMEZCUXl4SFFVRkhMRlZCUVZVc1EwRkJReXhGUVVGRkxFTkJRVU1zWTBGQll5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1VVRkRla01zU1VGQlNTeERRVUZETEVkQlFVY3NWVUZCVlN4RFFVRkRMRVZCUVVVc1EwRkJReXhqUVVGakxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0UlFVTjZReXhGUVVGRkxFTkJRVU1zVTBGQlV5eERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRWRCUVVjc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRKUVVOeVF5eERRVUZETEVOQlFVTXNRMEZCUXp0QlFVTlFMRU5CUVVNN1FVRkxSQ3hUUVVGblFpeDNRa0ZCZDBJc1EwRkJUeXhMUVVGaExFVkJRVVVzUlVGQk5FSXNSVUZCUlN4RFFVRmhPMGxCUVdJc2EwSkJRVUVzUlVGQlFTeExRVUZoTzBsQlEzSkhMR3RDUVVGclFpeERRVUZETEV0QlFVc3NSVUZCUlN4RFFVRkRMRVZCUVVVc1ZVRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eEpRVUZMTEU5QlFVRXNTVUZCU1N4RFFVRkRMRWxCUVVrc1EwRkJReXhWUVVGVkxFTkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXl4SFFVRkhMR2xDUVVGcFFpeERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGeVJDeERRVUZ4UkN4RlFVRkZMRVZCUVVVc1EwRkJReXhEUVVGRE8wRkJRM1JITEVOQlFVTTdRVUZHUkN3MFJFRkZRenRCUVV0RUxGTkJRV2RDTEd0Q1FVRnJRaXhEUVVGUExFdEJRV0VzUlVGQlJTeEZRVUUwUWl4RlFVRkZMRU5CUVdFN1NVRkJZaXhyUWtGQlFTeEZRVUZCTEV0QlFXRTdTVUZETDBZc2EwSkJRV3RDTEVOQlFVTXNTMEZCU3l4RlFVRkZMRU5CUVVNc1JVRkJSU3hWUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETzFGQlF6bENMRTlCUVVFc1NVRkJTU3hEUVVGRExFZEJRVWNzUTBGQlF5eE5RVUZOTEVOQlFVTXNTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFMUJRVTBzUlVGQlJTeE5RVUZOTEVOQlFVTXNTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFMUJRVTBzUTBGQlF5eEhRVUZITEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eHBRa0ZCYVVJc1EwRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETEVkQlFVY3NWVUZCVlN4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU03U1VGQk4wY3NRMEZCTmtjc1JVRkRNMGNzUlVGQlJTeERRVUZETEVOQlFVTTdRVUZEWkN4RFFVRkRPMEZCU2tRc1owUkJTVU03UVVGdlFrUXNVMEZCWjBJc0swSkJRU3RDTEVOQlFVOHNRMEZCVXl4RlFVRkZMRXRCUVdFc1JVRkJSU3hKUVVGWkxFVkJRM2hHTEVWQlFYbENPMGxCUlhwQ0xFbEJRVWtzVlVGQlZTeEhRVUZITERKQ1FVRXlRaXhEUVVGRExFTkJRVU1zUlVGQlJTeExRVUZMTEVWQlFVVXNSVUZCUlN4RFFVRkRMRU5CUVVNN1NVRkRNMFFzU1VGQlNTeExRVUZMTEVkQlFVY3NSVUZCUlN4RFFVRkRPMGxCUTJZc1ZVRkJWU3hEUVVGRExFOUJRVThzUTBGQlF5eFZRVUZETEVOQlFVTXNSVUZCUXl4RFFVRkRPMUZCUTI1Q0xFOUJRVUVzUTBGQlF5eERRVUZETEU5QlFVOHNRMEZCUXl4VlFVRkJMRU5CUVVNc1NVRkJTU3hQUVVGQkxFdEJRVXNzUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4RFFVRkRMRVZCUVZvc1EwRkJXU3hEUVVGRE8wbEJRVFZDTEVOQlFUUkNMRU5CUXk5Q0xFTkJRVU03U1VGRFJpeEpRVUZKTEZkQlFWY3NSMEZCVlN4RlFVRkZMRU5CUVVNN1NVRkROVUlzUzBGQlN5eERRVUZETEU5QlFVOHNRMEZCUXl4VlFVRkJMRU5CUVVNN1VVRkRXQ3hKUVVGSkxFVkJRVVVzUjBGQlJ5eEZRVUZGTEVOQlFVTXNZMEZCWXl4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGRkxFVkJRVVVzUjBGQlJ5eEZRVUZGTEVOQlFVTXNZMEZCWXl4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVOd1JDeERRVUZETEVkQlFVY3NTMEZCU3l4RFFVRkRMRVZCUVVVc1EwRkJReXhGUVVGRkxFTkJRVU1zUjBGQlJ5eExRVUZMTEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNN1VVRkRha01zU1VGQlNTeERRVUZETEV0QlFVc3NRMEZCUXl4RlFVRkZPMWxCUTFRc1YwRkJWeXhEUVVGRExFbEJRVWtzUTBGQlF6dG5Ra0ZEWWl4SlFVRkpMRVZCUVVVc1NVRkJTVHRuUWtGRFZpeEpRVUZKTEVWQlFVVXNSVUZCUlR0blFrRkRVaXhMUVVGTExFVkJRVVVzUlVGQlJUdG5Ra0ZEVkN4SFFVRkhMRVZCUVVVc1JVRkJSU3hEUVVGRExHZENRVUZuUWl4RFFVRkRMRU5CUVVNc1EwRkJRenRoUVVNNVFpeERRVUZETEVOQlFVTTdVMEZEVGp0SlFVTk1MRU5CUVVNc1EwRkJReXhEUVVGRE8wbEJRMGdzVDBGQlR5eFhRVUZYTEVOQlFVTTdRVUZEZGtJc1EwRkJRenRCUVhSQ1JDd3dSVUZ6UWtNN1FVRlJSQ3hUUVVGblFpd3lRa0ZCTWtJc1EwRkJUeXhYUVVGdFFpeEZRVUZGTEV0QlFXRXNSVUZCUlN4RlFVRnpRanRKUVVONFJ5eEpRVUZKTEV0QlFVc3NSMEZCUnl4RlFVRkZMRU5CUVVNN1NVRkRaaXhKUVVGSkxFdEJRVXNzUjBGQlJ5eERRVUZETEVOQlFVTTdTVUZEWkN4SlFVRkpMRXRCUVVzc1IwRkJSeXhGUVVGRkxFTkJRVU03U1VGRFppeEpRVUZKTEZWQlFWVXNSMEZCUnl4RlFVRkZMRU5CUVVNN1NVRkRjRUlzVTBGQlV5eGhRVUZoTEVOQlFVTXNRMEZCUXp0UlFVVndRaXhEUVVGRExFTkJRVU1zUzBGQlN5eEhRVUZITEVOQlFVTXNRMEZCUXl4UFFVRlBMRWRCUVVjc1MwRkJTeXhGUVVGRkxFTkJRVU03VVVGRE9VSXNTMEZCU3l4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFJRVU5rTEVOQlFVTXNRMEZCUXl4UFFVRlBMRWRCUVVjc1NVRkJTU3hEUVVGRE8xRkJSMnBDTEV0QlFXTXNWVUZCU3l4RlFVRk1MRXRCUVVFc1EwRkJReXhEUVVGRExFZEJRVWNzUlVGQlRDeGpRVUZMTEVWQlFVd3NTVUZCU3l4RlFVRkZPMWxCUVdoQ0xFbEJRVWtzUTBGQlF5eFRRVUZCTzFsQlEwNHNTVUZCU1N4UFFVRlBMRU5CUVVNc1EwRkJReXhMUVVGTExFdEJRVXNzVjBGQlZ5eEZRVUZGTzJkQ1FVVm9ReXhoUVVGaExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdaMEpCUTJwQ0xFTkJRVU1zUTBGQlF5eFBRVUZQTEVkQlFVY3NTVUZCU1N4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zVDBGQlR5eEZRVUZGTEVOQlFVTXNRMEZCUXl4UFFVRlBMRU5CUVVNc1EwRkJRenRoUVVNNVF6dHBRa0ZCVFN4SlFVRkpMRU5CUVVNc1EwRkJReXhQUVVGUExFVkJRVVU3WjBKQlJXeENMRU5CUVVNc1EwRkJReXhQUVVGUExFZEJRVWNzU1VGQlNTeERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1QwRkJUeXhGUVVGRkxFTkJRVU1zUTBGQlF5eExRVUZMTEVOQlFVTXNRMEZCUXp0aFFVTTFRenRUUVVOS08xRkJSMFFzU1VGQlNTeERRVUZETEVOQlFVTXNUMEZCVHl4TFFVRkxMRU5CUVVNc1EwRkJReXhMUVVGTExFVkJRVVU3V1VGRmRrSXNTVUZCU1N4VFFVRlRMRWRCUVVjc1JVRkJSU3hEUVVGRE8xbEJRMjVDTEU5QlFVOHNTMEZCU3l4RFFVRkRMRTFCUVUwc1JVRkJSVHRuUWtGRGFrSXNRMEZCUXl4SFFVRkhMRXRCUVVzc1EwRkJReXhIUVVGSExFVkJRVVVzUTBGQlF6dG5Ra0ZEYUVJc1EwRkJReXhEUVVGRExFOUJRVThzUjBGQlJ5eExRVUZMTEVOQlFVTTdaMEpCUld4Q0xGTkJRVk1zUTBGQlF5eEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1owSkJRMnhDTEVsQlFVa3NRMEZCUXl4TFFVRkxMRU5CUVVNN2IwSkJRVVVzVFVGQlRUdGhRVU4wUWp0WlFVVkVMRlZCUVZVc1EwRkJReXhKUVVGSkxFTkJRVU1zVTBGQlV5eERRVUZETEVkQlFVY3NRMEZCUXl4VlFVRkJMRU5CUVVNc1NVRkJTU3hQUVVGQkxFTkJRVU1zUTBGQlF5eEZRVUZGTEVWQlFVb3NRMEZCU1N4RFFVRkRMRU5CUVVNc1EwRkJRenRUUVVNM1F6dEpRVU5NTEVOQlFVTTdTVUZEUkN4TFFVRkxMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NWMEZCVnl4RlFVRkZMRU5CUVVNc1JVRkJSU3hGUVVGRk8xRkJRMnhETEV0QlFVc3NRMEZCUXl4SlFVRkpMRU5CUVVNc1JVRkJReXhGUVVGRkxFVkJRVVVzUTBGQlF5eEZRVUZGTEVkQlFVY3NSVUZCUlN4RlFVRkZMRVZCUVVNc1EwRkJReXhEUVVGRE8wdEJRMmhETzBsQlEwUXNTMEZCWXl4VlFVRkxMRVZCUVV3c1pVRkJTeXhGUVVGTUxHMUNRVUZMTEVWQlFVd3NTVUZCU3l4RlFVRkZPMUZCUVdoQ0xFbEJRVWtzUTBGQlF5eGpRVUZCTzFGQlEwNHNTVUZCU1N4SFFVRkRMRWRCUVVjc1MwRkJTeXhEUVVGRExFVkJRVVVzUTBGQlF5eGpRVUZqTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkRMMElzUTBGQlF5eEhRVUZITEV0QlFVc3NRMEZCUXl4RlFVRkZMRU5CUVVNc1kwRkJZeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdVVUZEY0VNc1IwRkJReXhEUVVGRExFZEJRVWNzUTBGQlF5eEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1MwRkRha0k3U1VGRFJDeExRVUZqTEZWQlFVc3NSVUZCVEN4bFFVRkxMRVZCUVV3c2JVSkJRVXNzUlVGQlRDeEpRVUZMTzFGQlFXUXNTVUZCU1N4RFFVRkRMR05CUVVFN1VVRkJWeXhKUVVGSkxFOUJRVThzUTBGQlF5eERRVUZETEV0QlFVc3NTMEZCU3l4WFFVRlhPMWxCUVVVc1lVRkJZU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzB0QlFVRTdTVUZETVVVc1QwRkJUeXhWUVVGVkxFTkJRVU03UVVGRGRFSXNRMEZCUXp0QlFXaEVSQ3hyUlVGblJFTWlmUT09IiwiXCJ1c2Ugc3RyaWN0XCI7XHJcbk9iamVjdC5kZWZpbmVQcm9wZXJ0eShleHBvcnRzLCBcIl9fZXNNb2R1bGVcIiwgeyB2YWx1ZTogdHJ1ZSB9KTtcclxudmFyIFBvd2VyRWRnZSA9IChmdW5jdGlvbiAoKSB7XHJcbiAgICBmdW5jdGlvbiBQb3dlckVkZ2Uoc291cmNlLCB0YXJnZXQsIHR5cGUpIHtcclxuICAgICAgICB0aGlzLnNvdXJjZSA9IHNvdXJjZTtcclxuICAgICAgICB0aGlzLnRhcmdldCA9IHRhcmdldDtcclxuICAgICAgICB0aGlzLnR5cGUgPSB0eXBlO1xyXG4gICAgfVxyXG4gICAgcmV0dXJuIFBvd2VyRWRnZTtcclxufSgpKTtcclxuZXhwb3J0cy5Qb3dlckVkZ2UgPSBQb3dlckVkZ2U7XHJcbnZhciBDb25maWd1cmF0aW9uID0gKGZ1bmN0aW9uICgpIHtcclxuICAgIGZ1bmN0aW9uIENvbmZpZ3VyYXRpb24obiwgZWRnZXMsIGxpbmtBY2Nlc3Nvciwgcm9vdEdyb3VwKSB7XHJcbiAgICAgICAgdmFyIF90aGlzID0gdGhpcztcclxuICAgICAgICB0aGlzLmxpbmtBY2Nlc3NvciA9IGxpbmtBY2Nlc3NvcjtcclxuICAgICAgICB0aGlzLm1vZHVsZXMgPSBuZXcgQXJyYXkobik7XHJcbiAgICAgICAgdGhpcy5yb290cyA9IFtdO1xyXG4gICAgICAgIGlmIChyb290R3JvdXApIHtcclxuICAgICAgICAgICAgdGhpcy5pbml0TW9kdWxlc0Zyb21Hcm91cChyb290R3JvdXApO1xyXG4gICAgICAgIH1cclxuICAgICAgICBlbHNlIHtcclxuICAgICAgICAgICAgdGhpcy5yb290cy5wdXNoKG5ldyBNb2R1bGVTZXQoKSk7XHJcbiAgICAgICAgICAgIGZvciAodmFyIGkgPSAwOyBpIDwgbjsgKytpKVxyXG4gICAgICAgICAgICAgICAgdGhpcy5yb290c1swXS5hZGQodGhpcy5tb2R1bGVzW2ldID0gbmV3IE1vZHVsZShpKSk7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIHRoaXMuUiA9IGVkZ2VzLmxlbmd0aDtcclxuICAgICAgICBlZGdlcy5mb3JFYWNoKGZ1bmN0aW9uIChlKSB7XHJcbiAgICAgICAgICAgIHZhciBzID0gX3RoaXMubW9kdWxlc1tsaW5rQWNjZXNzb3IuZ2V0U291cmNlSW5kZXgoZSldLCB0ID0gX3RoaXMubW9kdWxlc1tsaW5rQWNjZXNzb3IuZ2V0VGFyZ2V0SW5kZXgoZSldLCB0eXBlID0gbGlua0FjY2Vzc29yLmdldFR5cGUoZSk7XHJcbiAgICAgICAgICAgIHMub3V0Z29pbmcuYWRkKHR5cGUsIHQpO1xyXG4gICAgICAgICAgICB0LmluY29taW5nLmFkZCh0eXBlLCBzKTtcclxuICAgICAgICB9KTtcclxuICAgIH1cclxuICAgIENvbmZpZ3VyYXRpb24ucHJvdG90eXBlLmluaXRNb2R1bGVzRnJvbUdyb3VwID0gZnVuY3Rpb24gKGdyb3VwKSB7XHJcbiAgICAgICAgdmFyIG1vZHVsZVNldCA9IG5ldyBNb2R1bGVTZXQoKTtcclxuICAgICAgICB0aGlzLnJvb3RzLnB1c2gobW9kdWxlU2V0KTtcclxuICAgICAgICBmb3IgKHZhciBpID0gMDsgaSA8IGdyb3VwLmxlYXZlcy5sZW5ndGg7ICsraSkge1xyXG4gICAgICAgICAgICB2YXIgbm9kZSA9IGdyb3VwLmxlYXZlc1tpXTtcclxuICAgICAgICAgICAgdmFyIG1vZHVsZSA9IG5ldyBNb2R1bGUobm9kZS5pZCk7XHJcbiAgICAgICAgICAgIHRoaXMubW9kdWxlc1tub2RlLmlkXSA9IG1vZHVsZTtcclxuICAgICAgICAgICAgbW9kdWxlU2V0LmFkZChtb2R1bGUpO1xyXG4gICAgICAgIH1cclxuICAgICAgICBpZiAoZ3JvdXAuZ3JvdXBzKSB7XHJcbiAgICAgICAgICAgIGZvciAodmFyIGogPSAwOyBqIDwgZ3JvdXAuZ3JvdXBzLmxlbmd0aDsgKytqKSB7XHJcbiAgICAgICAgICAgICAgICB2YXIgY2hpbGQgPSBncm91cC5ncm91cHNbal07XHJcbiAgICAgICAgICAgICAgICB2YXIgZGVmaW5pdGlvbiA9IHt9O1xyXG4gICAgICAgICAgICAgICAgZm9yICh2YXIgcHJvcCBpbiBjaGlsZClcclxuICAgICAgICAgICAgICAgICAgICBpZiAocHJvcCAhPT0gXCJsZWF2ZXNcIiAmJiBwcm9wICE9PSBcImdyb3Vwc1wiICYmIGNoaWxkLmhhc093blByb3BlcnR5KHByb3ApKVxyXG4gICAgICAgICAgICAgICAgICAgICAgICBkZWZpbml0aW9uW3Byb3BdID0gY2hpbGRbcHJvcF07XHJcbiAgICAgICAgICAgICAgICBtb2R1bGVTZXQuYWRkKG5ldyBNb2R1bGUoLTEgLSBqLCBuZXcgTGlua1NldHMoKSwgbmV3IExpbmtTZXRzKCksIHRoaXMuaW5pdE1vZHVsZXNGcm9tR3JvdXAoY2hpbGQpLCBkZWZpbml0aW9uKSk7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICB9XHJcbiAgICAgICAgcmV0dXJuIG1vZHVsZVNldDtcclxuICAgIH07XHJcbiAgICBDb25maWd1cmF0aW9uLnByb3RvdHlwZS5tZXJnZSA9IGZ1bmN0aW9uIChhLCBiLCBrKSB7XHJcbiAgICAgICAgaWYgKGsgPT09IHZvaWQgMCkgeyBrID0gMDsgfVxyXG4gICAgICAgIHZhciBpbkludCA9IGEuaW5jb21pbmcuaW50ZXJzZWN0aW9uKGIuaW5jb21pbmcpLCBvdXRJbnQgPSBhLm91dGdvaW5nLmludGVyc2VjdGlvbihiLm91dGdvaW5nKTtcclxuICAgICAgICB2YXIgY2hpbGRyZW4gPSBuZXcgTW9kdWxlU2V0KCk7XHJcbiAgICAgICAgY2hpbGRyZW4uYWRkKGEpO1xyXG4gICAgICAgIGNoaWxkcmVuLmFkZChiKTtcclxuICAgICAgICB2YXIgbSA9IG5ldyBNb2R1bGUodGhpcy5tb2R1bGVzLmxlbmd0aCwgb3V0SW50LCBpbkludCwgY2hpbGRyZW4pO1xyXG4gICAgICAgIHRoaXMubW9kdWxlcy5wdXNoKG0pO1xyXG4gICAgICAgIHZhciB1cGRhdGUgPSBmdW5jdGlvbiAocywgaSwgbykge1xyXG4gICAgICAgICAgICBzLmZvckFsbChmdW5jdGlvbiAobXMsIGxpbmt0eXBlKSB7XHJcbiAgICAgICAgICAgICAgICBtcy5mb3JBbGwoZnVuY3Rpb24gKG4pIHtcclxuICAgICAgICAgICAgICAgICAgICB2YXIgbmxzID0gbltpXTtcclxuICAgICAgICAgICAgICAgICAgICBubHMuYWRkKGxpbmt0eXBlLCBtKTtcclxuICAgICAgICAgICAgICAgICAgICBubHMucmVtb3ZlKGxpbmt0eXBlLCBhKTtcclxuICAgICAgICAgICAgICAgICAgICBubHMucmVtb3ZlKGxpbmt0eXBlLCBiKTtcclxuICAgICAgICAgICAgICAgICAgICBhW29dLnJlbW92ZShsaW5rdHlwZSwgbik7XHJcbiAgICAgICAgICAgICAgICAgICAgYltvXS5yZW1vdmUobGlua3R5cGUsIG4pO1xyXG4gICAgICAgICAgICAgICAgfSk7XHJcbiAgICAgICAgICAgIH0pO1xyXG4gICAgICAgIH07XHJcbiAgICAgICAgdXBkYXRlKG91dEludCwgXCJpbmNvbWluZ1wiLCBcIm91dGdvaW5nXCIpO1xyXG4gICAgICAgIHVwZGF0ZShpbkludCwgXCJvdXRnb2luZ1wiLCBcImluY29taW5nXCIpO1xyXG4gICAgICAgIHRoaXMuUiAtPSBpbkludC5jb3VudCgpICsgb3V0SW50LmNvdW50KCk7XHJcbiAgICAgICAgdGhpcy5yb290c1trXS5yZW1vdmUoYSk7XHJcbiAgICAgICAgdGhpcy5yb290c1trXS5yZW1vdmUoYik7XHJcbiAgICAgICAgdGhpcy5yb290c1trXS5hZGQobSk7XHJcbiAgICAgICAgcmV0dXJuIG07XHJcbiAgICB9O1xyXG4gICAgQ29uZmlndXJhdGlvbi5wcm90b3R5cGUucm9vdE1lcmdlcyA9IGZ1bmN0aW9uIChrKSB7XHJcbiAgICAgICAgaWYgKGsgPT09IHZvaWQgMCkgeyBrID0gMDsgfVxyXG4gICAgICAgIHZhciBycyA9IHRoaXMucm9vdHNba10ubW9kdWxlcygpO1xyXG4gICAgICAgIHZhciBuID0gcnMubGVuZ3RoO1xyXG4gICAgICAgIHZhciBtZXJnZXMgPSBuZXcgQXJyYXkobiAqIChuIC0gMSkpO1xyXG4gICAgICAgIHZhciBjdHIgPSAwO1xyXG4gICAgICAgIGZvciAodmFyIGkgPSAwLCBpXyA9IG4gLSAxOyBpIDwgaV87ICsraSkge1xyXG4gICAgICAgICAgICBmb3IgKHZhciBqID0gaSArIDE7IGogPCBuOyArK2opIHtcclxuICAgICAgICAgICAgICAgIHZhciBhID0gcnNbaV0sIGIgPSByc1tqXTtcclxuICAgICAgICAgICAgICAgIG1lcmdlc1tjdHJdID0geyBpZDogY3RyLCBuRWRnZXM6IHRoaXMubkVkZ2VzKGEsIGIpLCBhOiBhLCBiOiBiIH07XHJcbiAgICAgICAgICAgICAgICBjdHIrKztcclxuICAgICAgICAgICAgfVxyXG4gICAgICAgIH1cclxuICAgICAgICByZXR1cm4gbWVyZ2VzO1xyXG4gICAgfTtcclxuICAgIENvbmZpZ3VyYXRpb24ucHJvdG90eXBlLmdyZWVkeU1lcmdlID0gZnVuY3Rpb24gKCkge1xyXG4gICAgICAgIGZvciAodmFyIGkgPSAwOyBpIDwgdGhpcy5yb290cy5sZW5ndGg7ICsraSkge1xyXG4gICAgICAgICAgICBpZiAodGhpcy5yb290c1tpXS5tb2R1bGVzKCkubGVuZ3RoIDwgMilcclxuICAgICAgICAgICAgICAgIGNvbnRpbnVlO1xyXG4gICAgICAgICAgICB2YXIgbXMgPSB0aGlzLnJvb3RNZXJnZXMoaSkuc29ydChmdW5jdGlvbiAoYSwgYikgeyByZXR1cm4gYS5uRWRnZXMgPT0gYi5uRWRnZXMgPyBhLmlkIC0gYi5pZCA6IGEubkVkZ2VzIC0gYi5uRWRnZXM7IH0pO1xyXG4gICAgICAgICAgICB2YXIgbSA9IG1zWzBdO1xyXG4gICAgICAgICAgICBpZiAobS5uRWRnZXMgPj0gdGhpcy5SKVxyXG4gICAgICAgICAgICAgICAgY29udGludWU7XHJcbiAgICAgICAgICAgIHRoaXMubWVyZ2UobS5hLCBtLmIsIGkpO1xyXG4gICAgICAgICAgICByZXR1cm4gdHJ1ZTtcclxuICAgICAgICB9XHJcbiAgICB9O1xyXG4gICAgQ29uZmlndXJhdGlvbi5wcm90b3R5cGUubkVkZ2VzID0gZnVuY3Rpb24gKGEsIGIpIHtcclxuICAgICAgICB2YXIgaW5JbnQgPSBhLmluY29taW5nLmludGVyc2VjdGlvbihiLmluY29taW5nKSwgb3V0SW50ID0gYS5vdXRnb2luZy5pbnRlcnNlY3Rpb24oYi5vdXRnb2luZyk7XHJcbiAgICAgICAgcmV0dXJuIHRoaXMuUiAtIGluSW50LmNvdW50KCkgLSBvdXRJbnQuY291bnQoKTtcclxuICAgIH07XHJcbiAgICBDb25maWd1cmF0aW9uLnByb3RvdHlwZS5nZXRHcm91cEhpZXJhcmNoeSA9IGZ1bmN0aW9uIChyZXRhcmdldGVkRWRnZXMpIHtcclxuICAgICAgICB2YXIgX3RoaXMgPSB0aGlzO1xyXG4gICAgICAgIHZhciBncm91cHMgPSBbXTtcclxuICAgICAgICB2YXIgcm9vdCA9IHt9O1xyXG4gICAgICAgIHRvR3JvdXBzKHRoaXMucm9vdHNbMF0sIHJvb3QsIGdyb3Vwcyk7XHJcbiAgICAgICAgdmFyIGVzID0gdGhpcy5hbGxFZGdlcygpO1xyXG4gICAgICAgIGVzLmZvckVhY2goZnVuY3Rpb24gKGUpIHtcclxuICAgICAgICAgICAgdmFyIGEgPSBfdGhpcy5tb2R1bGVzW2Uuc291cmNlXTtcclxuICAgICAgICAgICAgdmFyIGIgPSBfdGhpcy5tb2R1bGVzW2UudGFyZ2V0XTtcclxuICAgICAgICAgICAgcmV0YXJnZXRlZEVkZ2VzLnB1c2gobmV3IFBvd2VyRWRnZSh0eXBlb2YgYS5naWQgPT09IFwidW5kZWZpbmVkXCIgPyBlLnNvdXJjZSA6IGdyb3Vwc1thLmdpZF0sIHR5cGVvZiBiLmdpZCA9PT0gXCJ1bmRlZmluZWRcIiA/IGUudGFyZ2V0IDogZ3JvdXBzW2IuZ2lkXSwgZS50eXBlKSk7XHJcbiAgICAgICAgfSk7XHJcbiAgICAgICAgcmV0dXJuIGdyb3VwcztcclxuICAgIH07XHJcbiAgICBDb25maWd1cmF0aW9uLnByb3RvdHlwZS5hbGxFZGdlcyA9IGZ1bmN0aW9uICgpIHtcclxuICAgICAgICB2YXIgZXMgPSBbXTtcclxuICAgICAgICBDb25maWd1cmF0aW9uLmdldEVkZ2VzKHRoaXMucm9vdHNbMF0sIGVzKTtcclxuICAgICAgICByZXR1cm4gZXM7XHJcbiAgICB9O1xyXG4gICAgQ29uZmlndXJhdGlvbi5nZXRFZGdlcyA9IGZ1bmN0aW9uIChtb2R1bGVzLCBlcykge1xyXG4gICAgICAgIG1vZHVsZXMuZm9yQWxsKGZ1bmN0aW9uIChtKSB7XHJcbiAgICAgICAgICAgIG0uZ2V0RWRnZXMoZXMpO1xyXG4gICAgICAgICAgICBDb25maWd1cmF0aW9uLmdldEVkZ2VzKG0uY2hpbGRyZW4sIGVzKTtcclxuICAgICAgICB9KTtcclxuICAgIH07XHJcbiAgICByZXR1cm4gQ29uZmlndXJhdGlvbjtcclxufSgpKTtcclxuZXhwb3J0cy5Db25maWd1cmF0aW9uID0gQ29uZmlndXJhdGlvbjtcclxuZnVuY3Rpb24gdG9Hcm91cHMobW9kdWxlcywgZ3JvdXAsIGdyb3Vwcykge1xyXG4gICAgbW9kdWxlcy5mb3JBbGwoZnVuY3Rpb24gKG0pIHtcclxuICAgICAgICBpZiAobS5pc0xlYWYoKSkge1xyXG4gICAgICAgICAgICBpZiAoIWdyb3VwLmxlYXZlcylcclxuICAgICAgICAgICAgICAgIGdyb3VwLmxlYXZlcyA9IFtdO1xyXG4gICAgICAgICAgICBncm91cC5sZWF2ZXMucHVzaChtLmlkKTtcclxuICAgICAgICB9XHJcbiAgICAgICAgZWxzZSB7XHJcbiAgICAgICAgICAgIHZhciBnID0gZ3JvdXA7XHJcbiAgICAgICAgICAgIG0uZ2lkID0gZ3JvdXBzLmxlbmd0aDtcclxuICAgICAgICAgICAgaWYgKCFtLmlzSXNsYW5kKCkgfHwgbS5pc1ByZWRlZmluZWQoKSkge1xyXG4gICAgICAgICAgICAgICAgZyA9IHsgaWQ6IG0uZ2lkIH07XHJcbiAgICAgICAgICAgICAgICBpZiAobS5pc1ByZWRlZmluZWQoKSlcclxuICAgICAgICAgICAgICAgICAgICBmb3IgKHZhciBwcm9wIGluIG0uZGVmaW5pdGlvbilcclxuICAgICAgICAgICAgICAgICAgICAgICAgZ1twcm9wXSA9IG0uZGVmaW5pdGlvbltwcm9wXTtcclxuICAgICAgICAgICAgICAgIGlmICghZ3JvdXAuZ3JvdXBzKVxyXG4gICAgICAgICAgICAgICAgICAgIGdyb3VwLmdyb3VwcyA9IFtdO1xyXG4gICAgICAgICAgICAgICAgZ3JvdXAuZ3JvdXBzLnB1c2gobS5naWQpO1xyXG4gICAgICAgICAgICAgICAgZ3JvdXBzLnB1c2goZyk7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgdG9Hcm91cHMobS5jaGlsZHJlbiwgZywgZ3JvdXBzKTtcclxuICAgICAgICB9XHJcbiAgICB9KTtcclxufVxyXG52YXIgTW9kdWxlID0gKGZ1bmN0aW9uICgpIHtcclxuICAgIGZ1bmN0aW9uIE1vZHVsZShpZCwgb3V0Z29pbmcsIGluY29taW5nLCBjaGlsZHJlbiwgZGVmaW5pdGlvbikge1xyXG4gICAgICAgIGlmIChvdXRnb2luZyA9PT0gdm9pZCAwKSB7IG91dGdvaW5nID0gbmV3IExpbmtTZXRzKCk7IH1cclxuICAgICAgICBpZiAoaW5jb21pbmcgPT09IHZvaWQgMCkgeyBpbmNvbWluZyA9IG5ldyBMaW5rU2V0cygpOyB9XHJcbiAgICAgICAgaWYgKGNoaWxkcmVuID09PSB2b2lkIDApIHsgY2hpbGRyZW4gPSBuZXcgTW9kdWxlU2V0KCk7IH1cclxuICAgICAgICB0aGlzLmlkID0gaWQ7XHJcbiAgICAgICAgdGhpcy5vdXRnb2luZyA9IG91dGdvaW5nO1xyXG4gICAgICAgIHRoaXMuaW5jb21pbmcgPSBpbmNvbWluZztcclxuICAgICAgICB0aGlzLmNoaWxkcmVuID0gY2hpbGRyZW47XHJcbiAgICAgICAgdGhpcy5kZWZpbml0aW9uID0gZGVmaW5pdGlvbjtcclxuICAgIH1cclxuICAgIE1vZHVsZS5wcm90b3R5cGUuZ2V0RWRnZXMgPSBmdW5jdGlvbiAoZXMpIHtcclxuICAgICAgICB2YXIgX3RoaXMgPSB0aGlzO1xyXG4gICAgICAgIHRoaXMub3V0Z29pbmcuZm9yQWxsKGZ1bmN0aW9uIChtcywgZWRnZXR5cGUpIHtcclxuICAgICAgICAgICAgbXMuZm9yQWxsKGZ1bmN0aW9uICh0YXJnZXQpIHtcclxuICAgICAgICAgICAgICAgIGVzLnB1c2gobmV3IFBvd2VyRWRnZShfdGhpcy5pZCwgdGFyZ2V0LmlkLCBlZGdldHlwZSkpO1xyXG4gICAgICAgICAgICB9KTtcclxuICAgICAgICB9KTtcclxuICAgIH07XHJcbiAgICBNb2R1bGUucHJvdG90eXBlLmlzTGVhZiA9IGZ1bmN0aW9uICgpIHtcclxuICAgICAgICByZXR1cm4gdGhpcy5jaGlsZHJlbi5jb3VudCgpID09PSAwO1xyXG4gICAgfTtcclxuICAgIE1vZHVsZS5wcm90b3R5cGUuaXNJc2xhbmQgPSBmdW5jdGlvbiAoKSB7XHJcbiAgICAgICAgcmV0dXJuIHRoaXMub3V0Z29pbmcuY291bnQoKSA9PT0gMCAmJiB0aGlzLmluY29taW5nLmNvdW50KCkgPT09IDA7XHJcbiAgICB9O1xyXG4gICAgTW9kdWxlLnByb3RvdHlwZS5pc1ByZWRlZmluZWQgPSBmdW5jdGlvbiAoKSB7XHJcbiAgICAgICAgcmV0dXJuIHR5cGVvZiB0aGlzLmRlZmluaXRpb24gIT09IFwidW5kZWZpbmVkXCI7XHJcbiAgICB9O1xyXG4gICAgcmV0dXJuIE1vZHVsZTtcclxufSgpKTtcclxuZXhwb3J0cy5Nb2R1bGUgPSBNb2R1bGU7XHJcbmZ1bmN0aW9uIGludGVyc2VjdGlvbihtLCBuKSB7XHJcbiAgICB2YXIgaSA9IHt9O1xyXG4gICAgZm9yICh2YXIgdiBpbiBtKVxyXG4gICAgICAgIGlmICh2IGluIG4pXHJcbiAgICAgICAgICAgIGlbdl0gPSBtW3ZdO1xyXG4gICAgcmV0dXJuIGk7XHJcbn1cclxudmFyIE1vZHVsZVNldCA9IChmdW5jdGlvbiAoKSB7XHJcbiAgICBmdW5jdGlvbiBNb2R1bGVTZXQoKSB7XHJcbiAgICAgICAgdGhpcy50YWJsZSA9IHt9O1xyXG4gICAgfVxyXG4gICAgTW9kdWxlU2V0LnByb3RvdHlwZS5jb3VudCA9IGZ1bmN0aW9uICgpIHtcclxuICAgICAgICByZXR1cm4gT2JqZWN0LmtleXModGhpcy50YWJsZSkubGVuZ3RoO1xyXG4gICAgfTtcclxuICAgIE1vZHVsZVNldC5wcm90b3R5cGUuaW50ZXJzZWN0aW9uID0gZnVuY3Rpb24gKG90aGVyKSB7XHJcbiAgICAgICAgdmFyIHJlc3VsdCA9IG5ldyBNb2R1bGVTZXQoKTtcclxuICAgICAgICByZXN1bHQudGFibGUgPSBpbnRlcnNlY3Rpb24odGhpcy50YWJsZSwgb3RoZXIudGFibGUpO1xyXG4gICAgICAgIHJldHVybiByZXN1bHQ7XHJcbiAgICB9O1xyXG4gICAgTW9kdWxlU2V0LnByb3RvdHlwZS5pbnRlcnNlY3Rpb25Db3VudCA9IGZ1bmN0aW9uIChvdGhlcikge1xyXG4gICAgICAgIHJldHVybiB0aGlzLmludGVyc2VjdGlvbihvdGhlcikuY291bnQoKTtcclxuICAgIH07XHJcbiAgICBNb2R1bGVTZXQucHJvdG90eXBlLmNvbnRhaW5zID0gZnVuY3Rpb24gKGlkKSB7XHJcbiAgICAgICAgcmV0dXJuIGlkIGluIHRoaXMudGFibGU7XHJcbiAgICB9O1xyXG4gICAgTW9kdWxlU2V0LnByb3RvdHlwZS5hZGQgPSBmdW5jdGlvbiAobSkge1xyXG4gICAgICAgIHRoaXMudGFibGVbbS5pZF0gPSBtO1xyXG4gICAgfTtcclxuICAgIE1vZHVsZVNldC5wcm90b3R5cGUucmVtb3ZlID0gZnVuY3Rpb24gKG0pIHtcclxuICAgICAgICBkZWxldGUgdGhpcy50YWJsZVttLmlkXTtcclxuICAgIH07XHJcbiAgICBNb2R1bGVTZXQucHJvdG90eXBlLmZvckFsbCA9IGZ1bmN0aW9uIChmKSB7XHJcbiAgICAgICAgZm9yICh2YXIgbWlkIGluIHRoaXMudGFibGUpIHtcclxuICAgICAgICAgICAgZih0aGlzLnRhYmxlW21pZF0pO1xyXG4gICAgICAgIH1cclxuICAgIH07XHJcbiAgICBNb2R1bGVTZXQucHJvdG90eXBlLm1vZHVsZXMgPSBmdW5jdGlvbiAoKSB7XHJcbiAgICAgICAgdmFyIHZzID0gW107XHJcbiAgICAgICAgdGhpcy5mb3JBbGwoZnVuY3Rpb24gKG0pIHtcclxuICAgICAgICAgICAgaWYgKCFtLmlzUHJlZGVmaW5lZCgpKVxyXG4gICAgICAgICAgICAgICAgdnMucHVzaChtKTtcclxuICAgICAgICB9KTtcclxuICAgICAgICByZXR1cm4gdnM7XHJcbiAgICB9O1xyXG4gICAgcmV0dXJuIE1vZHVsZVNldDtcclxufSgpKTtcclxuZXhwb3J0cy5Nb2R1bGVTZXQgPSBNb2R1bGVTZXQ7XHJcbnZhciBMaW5rU2V0cyA9IChmdW5jdGlvbiAoKSB7XHJcbiAgICBmdW5jdGlvbiBMaW5rU2V0cygpIHtcclxuICAgICAgICB0aGlzLnNldHMgPSB7fTtcclxuICAgICAgICB0aGlzLm4gPSAwO1xyXG4gICAgfVxyXG4gICAgTGlua1NldHMucHJvdG90eXBlLmNvdW50ID0gZnVuY3Rpb24gKCkge1xyXG4gICAgICAgIHJldHVybiB0aGlzLm47XHJcbiAgICB9O1xyXG4gICAgTGlua1NldHMucHJvdG90eXBlLmNvbnRhaW5zID0gZnVuY3Rpb24gKGlkKSB7XHJcbiAgICAgICAgdmFyIHJlc3VsdCA9IGZhbHNlO1xyXG4gICAgICAgIHRoaXMuZm9yQWxsTW9kdWxlcyhmdW5jdGlvbiAobSkge1xyXG4gICAgICAgICAgICBpZiAoIXJlc3VsdCAmJiBtLmlkID09IGlkKSB7XHJcbiAgICAgICAgICAgICAgICByZXN1bHQgPSB0cnVlO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgfSk7XHJcbiAgICAgICAgcmV0dXJuIHJlc3VsdDtcclxuICAgIH07XHJcbiAgICBMaW5rU2V0cy5wcm90b3R5cGUuYWRkID0gZnVuY3Rpb24gKGxpbmt0eXBlLCBtKSB7XHJcbiAgICAgICAgdmFyIHMgPSBsaW5rdHlwZSBpbiB0aGlzLnNldHMgPyB0aGlzLnNldHNbbGlua3R5cGVdIDogdGhpcy5zZXRzW2xpbmt0eXBlXSA9IG5ldyBNb2R1bGVTZXQoKTtcclxuICAgICAgICBzLmFkZChtKTtcclxuICAgICAgICArK3RoaXMubjtcclxuICAgIH07XHJcbiAgICBMaW5rU2V0cy5wcm90b3R5cGUucmVtb3ZlID0gZnVuY3Rpb24gKGxpbmt0eXBlLCBtKSB7XHJcbiAgICAgICAgdmFyIG1zID0gdGhpcy5zZXRzW2xpbmt0eXBlXTtcclxuICAgICAgICBtcy5yZW1vdmUobSk7XHJcbiAgICAgICAgaWYgKG1zLmNvdW50KCkgPT09IDApIHtcclxuICAgICAgICAgICAgZGVsZXRlIHRoaXMuc2V0c1tsaW5rdHlwZV07XHJcbiAgICAgICAgfVxyXG4gICAgICAgIC0tdGhpcy5uO1xyXG4gICAgfTtcclxuICAgIExpbmtTZXRzLnByb3RvdHlwZS5mb3JBbGwgPSBmdW5jdGlvbiAoZikge1xyXG4gICAgICAgIGZvciAodmFyIGxpbmt0eXBlIGluIHRoaXMuc2V0cykge1xyXG4gICAgICAgICAgICBmKHRoaXMuc2V0c1tsaW5rdHlwZV0sIE51bWJlcihsaW5rdHlwZSkpO1xyXG4gICAgICAgIH1cclxuICAgIH07XHJcbiAgICBMaW5rU2V0cy5wcm90b3R5cGUuZm9yQWxsTW9kdWxlcyA9IGZ1bmN0aW9uIChmKSB7XHJcbiAgICAgICAgdGhpcy5mb3JBbGwoZnVuY3Rpb24gKG1zLCBsdCkgeyByZXR1cm4gbXMuZm9yQWxsKGYpOyB9KTtcclxuICAgIH07XHJcbiAgICBMaW5rU2V0cy5wcm90b3R5cGUuaW50ZXJzZWN0aW9uID0gZnVuY3Rpb24gKG90aGVyKSB7XHJcbiAgICAgICAgdmFyIHJlc3VsdCA9IG5ldyBMaW5rU2V0cygpO1xyXG4gICAgICAgIHRoaXMuZm9yQWxsKGZ1bmN0aW9uIChtcywgbHQpIHtcclxuICAgICAgICAgICAgaWYgKGx0IGluIG90aGVyLnNldHMpIHtcclxuICAgICAgICAgICAgICAgIHZhciBpID0gbXMuaW50ZXJzZWN0aW9uKG90aGVyLnNldHNbbHRdKSwgbiA9IGkuY291bnQoKTtcclxuICAgICAgICAgICAgICAgIGlmIChuID4gMCkge1xyXG4gICAgICAgICAgICAgICAgICAgIHJlc3VsdC5zZXRzW2x0XSA9IGk7XHJcbiAgICAgICAgICAgICAgICAgICAgcmVzdWx0Lm4gKz0gbjtcclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgfVxyXG4gICAgICAgIH0pO1xyXG4gICAgICAgIHJldHVybiByZXN1bHQ7XHJcbiAgICB9O1xyXG4gICAgcmV0dXJuIExpbmtTZXRzO1xyXG59KCkpO1xyXG5leHBvcnRzLkxpbmtTZXRzID0gTGlua1NldHM7XHJcbmZ1bmN0aW9uIGludGVyc2VjdGlvbkNvdW50KG0sIG4pIHtcclxuICAgIHJldHVybiBPYmplY3Qua2V5cyhpbnRlcnNlY3Rpb24obSwgbikpLmxlbmd0aDtcclxufVxyXG5mdW5jdGlvbiBnZXRHcm91cHMobm9kZXMsIGxpbmtzLCBsYSwgcm9vdEdyb3VwKSB7XHJcbiAgICB2YXIgbiA9IG5vZGVzLmxlbmd0aCwgYyA9IG5ldyBDb25maWd1cmF0aW9uKG4sIGxpbmtzLCBsYSwgcm9vdEdyb3VwKTtcclxuICAgIHdoaWxlIChjLmdyZWVkeU1lcmdlKCkpXHJcbiAgICAgICAgO1xyXG4gICAgdmFyIHBvd2VyRWRnZXMgPSBbXTtcclxuICAgIHZhciBnID0gYy5nZXRHcm91cEhpZXJhcmNoeShwb3dlckVkZ2VzKTtcclxuICAgIHBvd2VyRWRnZXMuZm9yRWFjaChmdW5jdGlvbiAoZSkge1xyXG4gICAgICAgIHZhciBmID0gZnVuY3Rpb24gKGVuZCkge1xyXG4gICAgICAgICAgICB2YXIgZyA9IGVbZW5kXTtcclxuICAgICAgICAgICAgaWYgKHR5cGVvZiBnID09IFwibnVtYmVyXCIpXHJcbiAgICAgICAgICAgICAgICBlW2VuZF0gPSBub2Rlc1tnXTtcclxuICAgICAgICB9O1xyXG4gICAgICAgIGYoXCJzb3VyY2VcIik7XHJcbiAgICAgICAgZihcInRhcmdldFwiKTtcclxuICAgIH0pO1xyXG4gICAgcmV0dXJuIHsgZ3JvdXBzOiBnLCBwb3dlckVkZ2VzOiBwb3dlckVkZ2VzIH07XHJcbn1cclxuZXhwb3J0cy5nZXRHcm91cHMgPSBnZXRHcm91cHM7XHJcbi8vIyBzb3VyY2VNYXBwaW5nVVJMPWRhdGE6YXBwbGljYXRpb24vanNvbjtiYXNlNjQsZXlKMlpYSnphVzl1SWpvekxDSm1hV3hsSWpvaWNHOTNaWEpuY21Gd2FDNXFjeUlzSW5OdmRYSmpaVkp2YjNRaU9pSWlMQ0p6YjNWeVkyVnpJanBiSWk0dUx5NHVMMWRsWWtOdmJHRXZjM0pqTDNCdmQyVnlaM0poY0dndWRITWlYU3dpYm1GdFpYTWlPbHRkTENKdFlYQndhVzVuY3lJNklqczdRVUZQU1R0SlFVTkpMRzFDUVVOWExFMUJRVmNzUlVGRFdDeE5RVUZYTEVWQlExZ3NTVUZCV1R0UlFVWmFMRmRCUVUwc1IwRkJUaXhOUVVGTkxFTkJRVXM3VVVGRFdDeFhRVUZOTEVkQlFVNHNUVUZCVFN4RFFVRkxPMUZCUTFnc1UwRkJTU3hIUVVGS0xFbEJRVWtzUTBGQlVUdEpRVUZKTEVOQlFVTTdTVUZEYUVNc1owSkJRVU03UVVGQlJDeERRVUZETEVGQlRFUXNTVUZMUXp0QlFVeFpMRGhDUVVGVE8wRkJUM1JDTzBsQlUwa3NkVUpCUVZrc1EwRkJVeXhGUVVGRkxFdEJRV0VzUlVGQlZTeFpRVUZ2UXl4RlFVRkZMRk5CUVdsQ08xRkJRWEpITEdsQ1FXdENRenRSUVd4Q05rTXNhVUpCUVZrc1IwRkJXaXhaUVVGWkxFTkJRWGRDTzFGQlF6bEZMRWxCUVVrc1EwRkJReXhQUVVGUExFZEJRVWNzU1VGQlNTeExRVUZMTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1VVRkROVUlzU1VGQlNTeERRVUZETEV0QlFVc3NSMEZCUnl4RlFVRkZMRU5CUVVNN1VVRkRhRUlzU1VGQlNTeFRRVUZUTEVWQlFVVTdXVUZEV0N4SlFVRkpMRU5CUVVNc2IwSkJRVzlDTEVOQlFVTXNVMEZCVXl4RFFVRkRMRU5CUVVNN1UwRkRlRU03WVVGQlRUdFpRVU5JTEVsQlFVa3NRMEZCUXl4TFFVRkxMRU5CUVVNc1NVRkJTU3hEUVVGRExFbEJRVWtzVTBGQlV5eEZRVUZGTEVOQlFVTXNRMEZCUXp0WlFVTnFReXhMUVVGTExFbEJRVWtzUTBGQlF5eEhRVUZITEVOQlFVTXNSVUZCUlN4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRkxFVkJRVVVzUTBGQlF6dG5Ra0ZEZEVJc1NVRkJTU3hEUVVGRExFdEJRVXNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRU5CUVVNc1NVRkJTU3hEUVVGRExFOUJRVThzUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4SlFVRkpMRTFCUVUwc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzFOQlF6RkVPMUZCUTBRc1NVRkJTU3hEUVVGRExFTkJRVU1zUjBGQlJ5eExRVUZMTEVOQlFVTXNUVUZCVFN4RFFVRkRPMUZCUTNSQ0xFdEJRVXNzUTBGQlF5eFBRVUZQTEVOQlFVTXNWVUZCUVN4RFFVRkRPMWxCUTFnc1NVRkJTU3hEUVVGRExFZEJRVWNzUzBGQlNTeERRVUZETEU5QlFVOHNRMEZCUXl4WlFVRlpMRU5CUVVNc1kwRkJZeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVWQlEyaEVMRU5CUVVNc1IwRkJSeXhMUVVGSkxFTkJRVU1zVDBGQlR5eERRVUZETEZsQlFWa3NRMEZCUXl4alFVRmpMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGRGFFUXNTVUZCU1N4SFFVRkhMRmxCUVZrc1EwRkJReXhQUVVGUExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdXVUZEYmtNc1EwRkJReXhEUVVGRExGRkJRVkVzUTBGQlF5eEhRVUZITEVOQlFVTXNTVUZCU1N4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRE8xbEJRM2hDTEVOQlFVTXNRMEZCUXl4UlFVRlJMRU5CUVVNc1IwRkJSeXhEUVVGRExFbEJRVWtzUlVGQlJTeERRVUZETEVOQlFVTXNRMEZCUXp0UlFVTTFRaXhEUVVGRExFTkJRVU1zUTBGQlF6dEpRVU5RTEVOQlFVTTdTVUZGVHl3MFEwRkJiMElzUjBGQk5VSXNWVUZCTmtJc1MwRkJTenRSUVVNNVFpeEpRVUZKTEZOQlFWTXNSMEZCUnl4SlFVRkpMRk5CUVZNc1JVRkJSU3hEUVVGRE8xRkJRMmhETEVsQlFVa3NRMEZCUXl4TFFVRkxMRU5CUVVNc1NVRkJTU3hEUVVGRExGTkJRVk1zUTBGQlF5eERRVUZETzFGQlF6TkNMRXRCUVVzc1NVRkJTU3hEUVVGRExFZEJRVWNzUTBGQlF5eEZRVUZGTEVOQlFVTXNSMEZCUnl4TFFVRkxMRU5CUVVNc1RVRkJUU3hEUVVGRExFMUJRVTBzUlVGQlJTeEZRVUZGTEVOQlFVTXNSVUZCUlR0WlFVTXhReXhKUVVGSkxFbEJRVWtzUjBGQlJ5eExRVUZMTEVOQlFVTXNUVUZCVFN4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8xbEJRek5DTEVsQlFVa3NUVUZCVFN4SFFVRkhMRWxCUVVrc1RVRkJUU3hEUVVGRExFbEJRVWtzUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXp0WlFVTnFReXhKUVVGSkxFTkJRVU1zVDBGQlR5eERRVUZETEVsQlFVa3NRMEZCUXl4RlFVRkZMRU5CUVVNc1IwRkJSeXhOUVVGTkxFTkJRVU03V1VGREwwSXNVMEZCVXl4RFFVRkRMRWRCUVVjc1EwRkJReXhOUVVGTkxFTkJRVU1zUTBGQlF6dFRRVU42UWp0UlFVTkVMRWxCUVVrc1MwRkJTeXhEUVVGRExFMUJRVTBzUlVGQlJUdFpRVU5rTEV0QlFVc3NTVUZCU1N4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRkxFTkJRVU1zUjBGQlJ5eExRVUZMTEVOQlFVTXNUVUZCVFN4RFFVRkRMRTFCUVUwc1JVRkJSU3hGUVVGRkxFTkJRVU1zUlVGQlJUdG5Ra0ZETVVNc1NVRkJTU3hMUVVGTExFZEJRVWNzUzBGQlN5eERRVUZETEUxQlFVMHNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRuUWtGRk5VSXNTVUZCU1N4VlFVRlZMRWRCUVVjc1JVRkJSU3hEUVVGRE8yZENRVU53UWl4TFFVRkxMRWxCUVVrc1NVRkJTU3hKUVVGSkxFdEJRVXM3YjBKQlEyeENMRWxCUVVrc1NVRkJTU3hMUVVGTExGRkJRVkVzU1VGQlNTeEpRVUZKTEV0QlFVc3NVVUZCVVN4SlFVRkpMRXRCUVVzc1EwRkJReXhqUVVGakxFTkJRVU1zU1VGQlNTeERRVUZETzNkQ1FVTndSU3hWUVVGVkxFTkJRVU1zU1VGQlNTeERRVUZETEVkQlFVY3NTMEZCU3l4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRE8yZENRVVYyUXl4VFFVRlRMRU5CUVVNc1IwRkJSeXhEUVVGRExFbEJRVWtzVFVGQlRTeERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkRMRU5CUVVNc1JVRkJSU3hKUVVGSkxGRkJRVkVzUlVGQlJTeEZRVUZGTEVsQlFVa3NVVUZCVVN4RlFVRkZMRVZCUVVVc1NVRkJTU3hEUVVGRExHOUNRVUZ2UWl4RFFVRkRMRXRCUVVzc1EwRkJReXhGUVVGRkxGVkJRVlVzUTBGQlF5eERRVUZETEVOQlFVTTdZVUZEYWtnN1UwRkRTanRSUVVORUxFOUJRVThzVTBGQlV5eERRVUZETzBsQlEzQkNMRU5CUVVNN1NVRkhSaXcyUWtGQlN5eEhRVUZNTEZWQlFVMHNRMEZCVXl4RlFVRkZMRU5CUVZNc1JVRkJSU3hEUVVGaE8xRkJRV0lzYTBKQlFVRXNSVUZCUVN4TFFVRmhPMUZCUTNKRExFbEJRVWtzUzBGQlN5eEhRVUZITEVOQlFVTXNRMEZCUXl4UlFVRlJMRU5CUVVNc1dVRkJXU3hEUVVGRExFTkJRVU1zUTBGQlF5eFJRVUZSTEVOQlFVTXNSVUZETTBNc1RVRkJUU3hIUVVGSExFTkJRVU1zUTBGQlF5eFJRVUZSTEVOQlFVTXNXVUZCV1N4RFFVRkRMRU5CUVVNc1EwRkJReXhSUVVGUkxFTkJRVU1zUTBGQlF6dFJRVU5xUkN4SlFVRkpMRkZCUVZFc1IwRkJSeXhKUVVGSkxGTkJRVk1zUlVGQlJTeERRVUZETzFGQlF5OUNMRkZCUVZFc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdVVUZEYUVJc1VVRkJVU3hEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0UlFVTm9RaXhKUVVGSkxFTkJRVU1zUjBGQlJ5eEpRVUZKTEUxQlFVMHNRMEZCUXl4SlFVRkpMRU5CUVVNc1QwRkJUeXhEUVVGRExFMUJRVTBzUlVGQlJTeE5RVUZOTEVWQlFVVXNTMEZCU3l4RlFVRkZMRkZCUVZFc1EwRkJReXhEUVVGRE8xRkJRMnBGTEVsQlFVa3NRMEZCUXl4UFFVRlBMRU5CUVVNc1NVRkJTU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzFGQlEzSkNMRWxCUVVrc1RVRkJUU3hIUVVGSExGVkJRVU1zUTBGQlZ5eEZRVUZGTEVOQlFWTXNSVUZCUlN4RFFVRlRPMWxCUXpORExFTkJRVU1zUTBGQlF5eE5RVUZOTEVOQlFVTXNWVUZCUXl4RlFVRkZMRVZCUVVVc1VVRkJVVHRuUWtGRGJFSXNSVUZCUlN4RFFVRkRMRTFCUVUwc1EwRkJReXhWUVVGQkxFTkJRVU03YjBKQlExQXNTVUZCU1N4SFFVRkhMRWRCUVdFc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzI5Q1FVTjZRaXhIUVVGSExFTkJRVU1zUjBGQlJ5eERRVUZETEZGQlFWRXNSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJRenR2UWtGRGNrSXNSMEZCUnl4RFFVRkRMRTFCUVUwc1EwRkJReXhSUVVGUkxFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTTdiMEpCUTNoQ0xFZEJRVWNzUTBGQlF5eE5RVUZOTEVOQlFVTXNVVUZCVVN4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRE8yOUNRVU5pTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVVc1EwRkJReXhOUVVGTkxFTkJRVU1zVVVGQlVTeEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRPMjlDUVVNeFFpeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkZMRU5CUVVNc1RVRkJUU3hEUVVGRExGRkJRVkVzUlVGQlJTeERRVUZETEVOQlFVTXNRMEZCUXp0blFrRkRla01zUTBGQlF5eERRVUZETEVOQlFVTTdXVUZEVUN4RFFVRkRMRU5CUVVNc1EwRkJRenRSUVVOUUxFTkJRVU1zUTBGQlF6dFJRVU5HTEUxQlFVMHNRMEZCUXl4TlFVRk5MRVZCUVVVc1ZVRkJWU3hGUVVGRkxGVkJRVlVzUTBGQlF5eERRVUZETzFGQlEzWkRMRTFCUVUwc1EwRkJReXhMUVVGTExFVkJRVVVzVlVGQlZTeEZRVUZGTEZWQlFWVXNRMEZCUXl4RFFVRkRPMUZCUTNSRExFbEJRVWtzUTBGQlF5eERRVUZETEVsQlFVa3NTMEZCU3l4RFFVRkRMRXRCUVVzc1JVRkJSU3hIUVVGSExFMUJRVTBzUTBGQlF5eExRVUZMTEVWQlFVVXNRMEZCUXp0UlFVTjZReXhKUVVGSkxFTkJRVU1zUzBGQlN5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRTFCUVUwc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFJRVU40UWl4SlFVRkpMRU5CUVVNc1MwRkJTeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEUxQlFVMHNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRSUVVONFFpeEpRVUZKTEVOQlFVTXNTMEZCU3l4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0UlFVTnlRaXhQUVVGUExFTkJRVU1zUTBGQlF6dEpRVU5pTEVOQlFVTTdTVUZGVHl4clEwRkJWU3hIUVVGc1FpeFZRVUZ0UWl4RFFVRmhPMUZCUVdJc2EwSkJRVUVzUlVGQlFTeExRVUZoTzFGQlRUVkNMRWxCUVVrc1JVRkJSU3hIUVVGSExFbEJRVWtzUTBGQlF5eExRVUZMTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1QwRkJUeXhGUVVGRkxFTkJRVU03VVVGRGFrTXNTVUZCU1N4RFFVRkRMRWRCUVVjc1JVRkJSU3hEUVVGRExFMUJRVTBzUTBGQlF6dFJRVU5zUWl4SlFVRkpMRTFCUVUwc1IwRkJSeXhKUVVGSkxFdEJRVXNzUTBGQlF5eERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFJRVU53UXl4SlFVRkpMRWRCUVVjc1IwRkJSeXhEUVVGRExFTkJRVU03VVVGRFdpeExRVUZMTEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1JVRkJSU3hGUVVGRkxFZEJRVWNzUTBGQlF5eEhRVUZITEVOQlFVTXNSVUZCUlN4RFFVRkRMRWRCUVVjc1JVRkJSU3hGUVVGRkxFVkJRVVVzUTBGQlF5eEZRVUZGTzFsQlEzSkRMRXRCUVVzc1NVRkJTU3hEUVVGRExFZEJRVWNzUTBGQlF5eEhRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRkxFVkJRVVVzUTBGQlF5eEZRVUZGTzJkQ1FVTXhRaXhKUVVGSkxFTkJRVU1zUjBGQlJ5eEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhIUVVGSExFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0blFrRkRla0lzVFVGQlRTeERRVUZETEVkQlFVY3NRMEZCUXl4SFFVRkhMRVZCUVVVc1JVRkJSU3hGUVVGRkxFZEJRVWNzUlVGQlJTeE5RVUZOTEVWQlFVVXNTVUZCU1N4RFFVRkRMRTFCUVUwc1EwRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4RlFVRkZMRU5CUVVNc1JVRkJSU3hEUVVGRExFVkJRVVVzUTBGQlF5eEZRVUZGTEVOQlFVTTdaMEpCUTJwRkxFZEJRVWNzUlVGQlJTeERRVUZETzJGQlExUTdVMEZEU2p0UlFVTkVMRTlCUVU4c1RVRkJUU3hEUVVGRE8wbEJRMnhDTEVOQlFVTTdTVUZGUkN4dFEwRkJWeXhIUVVGWU8xRkJRMGtzUzBGQlN5eEpRVUZKTEVOQlFVTXNSMEZCUnl4RFFVRkRMRVZCUVVVc1EwRkJReXhIUVVGSExFbEJRVWtzUTBGQlF5eExRVUZMTEVOQlFVTXNUVUZCVFN4RlFVRkZMRVZCUVVVc1EwRkJReXhGUVVGRk8xbEJSWGhETEVsQlFVa3NTVUZCU1N4RFFVRkRMRXRCUVVzc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eFBRVUZQTEVWQlFVVXNRMEZCUXl4TlFVRk5MRWRCUVVjc1EwRkJRenRuUWtGQlJTeFRRVUZUTzFsQlIycEVMRWxCUVVrc1JVRkJSU3hIUVVGSExFbEJRVWtzUTBGQlF5eFZRVUZWTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1NVRkJTU3hEUVVGRExGVkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTXNTVUZCU3l4UFFVRkJMRU5CUVVNc1EwRkJReXhOUVVGTkxFbEJRVWtzUTBGQlF5eERRVUZETEUxQlFVMHNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRVVVzUjBGQlJ5eERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zVFVGQlRTeEhRVUZITEVOQlFVTXNRMEZCUXl4TlFVRk5MRVZCUVhoRUxFTkJRWGRFTEVOQlFVTXNRMEZCUXp0WlFVTnlSeXhKUVVGSkxFTkJRVU1zUjBGQlJ5eEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1dVRkRaQ3hKUVVGSkxFTkJRVU1zUTBGQlF5eE5RVUZOTEVsQlFVa3NTVUZCU1N4RFFVRkRMRU5CUVVNN1owSkJRVVVzVTBGQlV6dFpRVU5xUXl4SlFVRkpMRU5CUVVNc1MwRkJTeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF6dFpRVU40UWl4UFFVRlBMRWxCUVVrc1EwRkJRenRUUVVObU8wbEJRMHdzUTBGQlF6dEpRVVZQTERoQ1FVRk5MRWRCUVdRc1ZVRkJaU3hEUVVGVExFVkJRVVVzUTBGQlV6dFJRVU12UWl4SlFVRkpMRXRCUVVzc1IwRkJSeXhEUVVGRExFTkJRVU1zVVVGQlVTeERRVUZETEZsQlFWa3NRMEZCUXl4RFFVRkRMRU5CUVVNc1VVRkJVU3hEUVVGRExFVkJRek5ETEUxQlFVMHNSMEZCUnl4RFFVRkRMRU5CUVVNc1VVRkJVU3hEUVVGRExGbEJRVmtzUTBGQlF5eERRVUZETEVOQlFVTXNVVUZCVVN4RFFVRkRMRU5CUVVNN1VVRkRha1FzVDBGQlR5eEpRVUZKTEVOQlFVTXNRMEZCUXl4SFFVRkhMRXRCUVVzc1EwRkJReXhMUVVGTExFVkJRVVVzUjBGQlJ5eE5RVUZOTEVOQlFVTXNTMEZCU3l4RlFVRkZMRU5CUVVNN1NVRkRia1FzUTBGQlF6dEpRVVZFTEhsRFFVRnBRaXhIUVVGcVFpeFZRVUZyUWl4bFFVRTBRanRSUVVFNVF5eHBRa0ZsUXp0UlFXUkhMRWxCUVVrc1RVRkJUU3hIUVVGSExFVkJRVVVzUTBGQlF6dFJRVU5vUWl4SlFVRkpMRWxCUVVrc1IwRkJSeXhGUVVGRkxFTkJRVU03VVVGRFpDeFJRVUZSTEVOQlFVTXNTVUZCU1N4RFFVRkRMRXRCUVVzc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQlJTeEpRVUZKTEVWQlFVVXNUVUZCVFN4RFFVRkRMRU5CUVVNN1VVRkRkRU1zU1VGQlNTeEZRVUZGTEVkQlFVY3NTVUZCU1N4RFFVRkRMRkZCUVZFc1JVRkJSU3hEUVVGRE8xRkJRM3BDTEVWQlFVVXNRMEZCUXl4UFFVRlBMRU5CUVVNc1ZVRkJRU3hEUVVGRE8xbEJRMUlzU1VGQlNTeERRVUZETEVkQlFVY3NTMEZCU1N4RFFVRkRMRTlCUVU4c1EwRkJReXhEUVVGRExFTkJRVU1zVFVGQlRTeERRVUZETEVOQlFVTTdXVUZETDBJc1NVRkJTU3hEUVVGRExFZEJRVWNzUzBGQlNTeERRVUZETEU5QlFVOHNRMEZCUXl4RFFVRkRMRU5CUVVNc1RVRkJUU3hEUVVGRExFTkJRVU03V1VGREwwSXNaVUZCWlN4RFFVRkRMRWxCUVVrc1EwRkJReXhKUVVGSkxGTkJRVk1zUTBGRE9VSXNUMEZCVHl4RFFVRkRMRU5CUVVNc1IwRkJSeXhMUVVGTExGZEJRVmNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRTFCUVUwc1EwRkJReXhEUVVGRExFTkJRVU1zVFVGQlRTeERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRU5CUVVNc1JVRkRka1FzVDBGQlR5eERRVUZETEVOQlFVTXNSMEZCUnl4TFFVRkxMRmRCUVZjc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEUxQlFVMHNRMEZCUXl4RFFVRkRMRU5CUVVNc1RVRkJUU3hEUVVGRExFTkJRVU1zUTBGQlF5eEhRVUZITEVOQlFVTXNSVUZEZGtRc1EwRkJReXhEUVVGRExFbEJRVWtzUTBGRFZDeERRVUZETEVOQlFVTTdVVUZEVUN4RFFVRkRMRU5CUVVNc1EwRkJRenRSUVVOSUxFOUJRVThzVFVGQlRTeERRVUZETzBsQlEyeENMRU5CUVVNN1NVRkZSQ3huUTBGQlVTeEhRVUZTTzFGQlEwa3NTVUZCU1N4RlFVRkZMRWRCUVVjc1JVRkJSU3hEUVVGRE8xRkJRMW9zWVVGQllTeERRVUZETEZGQlFWRXNRMEZCUXl4SlFVRkpMRU5CUVVNc1MwRkJTeXhEUVVGRExFTkJRVU1zUTBGQlF5eEZRVUZGTEVWQlFVVXNRMEZCUXl4RFFVRkRPMUZCUXpGRExFOUJRVThzUlVGQlJTeERRVUZETzBsQlEyUXNRMEZCUXp0SlFVVk5MSE5DUVVGUkxFZEJRV1lzVlVGQlowSXNUMEZCYTBJc1JVRkJSU3hGUVVGbE8xRkJReTlETEU5QlFVOHNRMEZCUXl4TlFVRk5MRU5CUVVNc1ZVRkJRU3hEUVVGRE8xbEJRMW9zUTBGQlF5eERRVUZETEZGQlFWRXNRMEZCUXl4RlFVRkZMRU5CUVVNc1EwRkJRenRaUVVObUxHRkJRV0VzUTBGQlF5eFJRVUZSTEVOQlFVTXNRMEZCUXl4RFFVRkRMRkZCUVZFc1JVRkJSU3hGUVVGRkxFTkJRVU1zUTBGQlF6dFJRVU16UXl4RFFVRkRMRU5CUVVNc1EwRkJRenRKUVVOUUxFTkJRVU03U1VGRFRDeHZRa0ZCUXp0QlFVRkVMRU5CUVVNc1FVRjRTa1FzU1VGM1NrTTdRVUY0U2xrc2MwTkJRV0U3UVVFd1NqRkNMRk5CUVZNc1VVRkJVU3hEUVVGRExFOUJRV3RDTEVWQlFVVXNTMEZCU3l4RlFVRkZMRTFCUVUwN1NVRkRMME1zVDBGQlR5eERRVUZETEUxQlFVMHNRMEZCUXl4VlFVRkJMRU5CUVVNN1VVRkRXaXhKUVVGSkxFTkJRVU1zUTBGQlF5eE5RVUZOTEVWQlFVVXNSVUZCUlR0WlFVTmFMRWxCUVVrc1EwRkJReXhMUVVGTExFTkJRVU1zVFVGQlRUdG5Ra0ZCUlN4TFFVRkxMRU5CUVVNc1RVRkJUU3hIUVVGSExFVkJRVVVzUTBGQlF6dFpRVU55UXl4TFFVRkxMRU5CUVVNc1RVRkJUU3hEUVVGRExFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNN1UwRkRNMEk3WVVGQlRUdFpRVU5JTEVsQlFVa3NRMEZCUXl4SFFVRkhMRXRCUVVzc1EwRkJRenRaUVVOa0xFTkJRVU1zUTBGQlF5eEhRVUZITEVkQlFVY3NUVUZCVFN4RFFVRkRMRTFCUVUwc1EwRkJRenRaUVVOMFFpeEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRkZCUVZFc1JVRkJSU3hKUVVGSkxFTkJRVU1zUTBGQlF5eFpRVUZaTEVWQlFVVXNSVUZCUlR0blFrRkRia01zUTBGQlF5eEhRVUZITEVWQlFVVXNSVUZCUlN4RlFVRkZMRU5CUVVNc1EwRkJReXhIUVVGSExFVkJRVVVzUTBGQlF6dG5Ra0ZEYkVJc1NVRkJTU3hEUVVGRExFTkJRVU1zV1VGQldTeEZRVUZGTzI5Q1FVVm9RaXhMUVVGTExFbEJRVWtzU1VGQlNTeEpRVUZKTEVOQlFVTXNRMEZCUXl4VlFVRlZPM2RDUVVONlFpeERRVUZETEVOQlFVTXNTVUZCU1N4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExGVkJRVlVzUTBGQlF5eEpRVUZKTEVOQlFVTXNRMEZCUXp0blFrRkRja01zU1VGQlNTeERRVUZETEV0QlFVc3NRMEZCUXl4TlFVRk5PMjlDUVVGRkxFdEJRVXNzUTBGQlF5eE5RVUZOTEVkQlFVY3NSVUZCUlN4RFFVRkRPMmRDUVVOeVF5eExRVUZMTEVOQlFVTXNUVUZCVFN4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTTdaMEpCUTNwQ0xFMUJRVTBzUTBGQlF5eEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1lVRkRiRUk3V1VGRFJDeFJRVUZSTEVOQlFVTXNRMEZCUXl4RFFVRkRMRkZCUVZFc1JVRkJSU3hEUVVGRExFVkJRVVVzVFVGQlRTeERRVUZETEVOQlFVTTdVMEZEYmtNN1NVRkRUQ3hEUVVGRExFTkJRVU1zUTBGQlF6dEJRVU5RTEVOQlFVTTdRVUZGUkR0SlFVZEpMR2RDUVVOWExFVkJRVlVzUlVGRFZpeFJRVUZ0UXl4RlFVTnVReXhSUVVGdFF5eEZRVU51UXl4UlFVRnhReXhGUVVOeVF5eFZRVUZuUWp0UlFVaG9RaXg1UWtGQlFTeEZRVUZCTEdWQlFYbENMRkZCUVZFc1JVRkJSVHRSUVVOdVF5eDVRa0ZCUVN4RlFVRkJMR1ZCUVhsQ0xGRkJRVkVzUlVGQlJUdFJRVU51UXl4NVFrRkJRU3hGUVVGQkxHVkJRVEJDTEZOQlFWTXNSVUZCUlR0UlFVaHlReXhQUVVGRkxFZEJRVVlzUlVGQlJTeERRVUZSTzFGQlExWXNZVUZCVVN4SFFVRlNMRkZCUVZFc1EwRkJNa0k3VVVGRGJrTXNZVUZCVVN4SFFVRlNMRkZCUVZFc1EwRkJNa0k3VVVGRGJrTXNZVUZCVVN4SFFVRlNMRkZCUVZFc1EwRkJOa0k3VVVGRGNrTXNaVUZCVlN4SFFVRldMRlZCUVZVc1EwRkJUVHRKUVVGSkxFTkJRVU03U1VGRmFFTXNlVUpCUVZFc1IwRkJVaXhWUVVGVExFVkJRV1U3VVVGQmVFSXNhVUpCVFVNN1VVRk1SeXhKUVVGSkxFTkJRVU1zVVVGQlVTeERRVUZETEUxQlFVMHNRMEZCUXl4VlFVRkRMRVZCUVVVc1JVRkJSU3hSUVVGUk8xbEJRemxDTEVWQlFVVXNRMEZCUXl4TlFVRk5MRU5CUVVNc1ZVRkJRU3hOUVVGTk8yZENRVU5hTEVWQlFVVXNRMEZCUXl4SlFVRkpMRU5CUVVNc1NVRkJTU3hUUVVGVExFTkJRVU1zUzBGQlNTeERRVUZETEVWQlFVVXNSVUZCUlN4TlFVRk5MRU5CUVVNc1JVRkJSU3hGUVVGRkxGRkJRVkVzUTBGQlF5eERRVUZETEVOQlFVTTdXVUZEZWtRc1EwRkJReXhEUVVGRExFTkJRVU03VVVGRFVDeERRVUZETEVOQlFVTXNRMEZCUXp0SlFVTlFMRU5CUVVNN1NVRkZSQ3gxUWtGQlRTeEhRVUZPTzFGQlEwa3NUMEZCVHl4SlFVRkpMRU5CUVVNc1VVRkJVU3hEUVVGRExFdEJRVXNzUlVGQlJTeExRVUZMTEVOQlFVTXNRMEZCUXp0SlFVTjJReXhEUVVGRE8wbEJSVVFzZVVKQlFWRXNSMEZCVWp0UlFVTkpMRTlCUVU4c1NVRkJTU3hEUVVGRExGRkJRVkVzUTBGQlF5eExRVUZMTEVWQlFVVXNTMEZCU3l4RFFVRkRMRWxCUVVrc1NVRkJTU3hEUVVGRExGRkJRVkVzUTBGQlF5eExRVUZMTEVWQlFVVXNTMEZCU3l4RFFVRkRMRU5CUVVNN1NVRkRkRVVzUTBGQlF6dEpRVVZFTERaQ1FVRlpMRWRCUVZvN1VVRkRTU3hQUVVGUExFOUJRVThzU1VGQlNTeERRVUZETEZWQlFWVXNTMEZCU3l4WFFVRlhMRU5CUVVNN1NVRkRiRVFzUTBGQlF6dEpRVU5NTEdGQlFVTTdRVUZCUkN4RFFVRkRMRUZCTjBKRUxFbEJOa0pETzBGQk4wSlpMSGRDUVVGTk8wRkJLMEp1UWl4VFFVRlRMRmxCUVZrc1EwRkJReXhEUVVGTkxFVkJRVVVzUTBGQlRUdEpRVU5vUXl4SlFVRkpMRU5CUVVNc1IwRkJSeXhGUVVGRkxFTkJRVU03U1VGRFdDeExRVUZMTEVsQlFVa3NRMEZCUXl4SlFVRkpMRU5CUVVNN1VVRkJSU3hKUVVGSkxFTkJRVU1zU1VGQlNTeERRVUZETzFsQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0SlFVTjZReXhQUVVGUExFTkJRVU1zUTBGQlF6dEJRVU5pTEVOQlFVTTdRVUZGUkR0SlFVRkJPMUZCUTBrc1ZVRkJTeXhIUVVGUkxFVkJRVVVzUTBGQlF6dEpRV3REY0VJc1EwRkJRenRKUVdwRFJ5eDVRa0ZCU3l4SFFVRk1PMUZCUTBrc1QwRkJUeXhOUVVGTkxFTkJRVU1zU1VGQlNTeERRVUZETEVsQlFVa3NRMEZCUXl4TFFVRkxMRU5CUVVNc1EwRkJReXhOUVVGTkxFTkJRVU03U1VGRE1VTXNRMEZCUXp0SlFVTkVMR2REUVVGWkxFZEJRVm9zVlVGQllTeExRVUZuUWp0UlFVTjZRaXhKUVVGSkxFMUJRVTBzUjBGQlJ5eEpRVUZKTEZOQlFWTXNSVUZCUlN4RFFVRkRPMUZCUXpkQ0xFMUJRVTBzUTBGQlF5eExRVUZMTEVkQlFVY3NXVUZCV1N4RFFVRkRMRWxCUVVrc1EwRkJReXhMUVVGTExFVkJRVVVzUzBGQlN5eERRVUZETEV0QlFVc3NRMEZCUXl4RFFVRkRPMUZCUTNKRUxFOUJRVThzVFVGQlRTeERRVUZETzBsQlEyeENMRU5CUVVNN1NVRkRSQ3h4UTBGQmFVSXNSMEZCYWtJc1ZVRkJhMElzUzBGQlowSTdVVUZET1VJc1QwRkJUeXhKUVVGSkxFTkJRVU1zV1VGQldTeERRVUZETEV0QlFVc3NRMEZCUXl4RFFVRkRMRXRCUVVzc1JVRkJSU3hEUVVGRE8wbEJRelZETEVOQlFVTTdTVUZEUkN3MFFrRkJVU3hIUVVGU0xGVkJRVk1zUlVGQlZUdFJRVU5tTEU5QlFVOHNSVUZCUlN4SlFVRkpMRWxCUVVrc1EwRkJReXhMUVVGTExFTkJRVU03U1VGRE5VSXNRMEZCUXp0SlFVTkVMSFZDUVVGSExFZEJRVWdzVlVGQlNTeERRVUZUTzFGQlExUXNTVUZCU1N4RFFVRkRMRXRCUVVzc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRPMGxCUTNwQ0xFTkJRVU03U1VGRFJDd3dRa0ZCVFN4SFFVRk9MRlZCUVU4c1EwRkJVenRSUVVOYUxFOUJRVThzU1VGQlNTeERRVUZETEV0QlFVc3NRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU03U1VGRE5VSXNRMEZCUXp0SlFVTkVMREJDUVVGTkxFZEJRVTRzVlVGQlR5eERRVUZ6UWp0UlFVTjZRaXhMUVVGTExFbEJRVWtzUjBGQlJ5eEpRVUZKTEVsQlFVa3NRMEZCUXl4TFFVRkxMRVZCUVVVN1dVRkRlRUlzUTBGQlF5eERRVUZETEVsQlFVa3NRMEZCUXl4TFFVRkxMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF6dFRRVU4wUWp0SlFVTk1MRU5CUVVNN1NVRkRSQ3d5UWtGQlR5eEhRVUZRTzFGQlEwa3NTVUZCU1N4RlFVRkZMRWRCUVVjc1JVRkJSU3hEUVVGRE8xRkJRMW9zU1VGQlNTeERRVUZETEUxQlFVMHNRMEZCUXl4VlFVRkJMRU5CUVVNN1dVRkRWQ3hKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEZsQlFWa3NSVUZCUlR0blFrRkRha0lzUlVGQlJTeERRVUZETEVsQlFVa3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRSUVVOdVFpeERRVUZETEVOQlFVTXNRMEZCUXp0UlFVTklMRTlCUVU4c1JVRkJSU3hEUVVGRE8wbEJRMlFzUTBGQlF6dEpRVU5NTEdkQ1FVRkRPMEZCUVVRc1EwRkJReXhCUVc1RFJDeEpRVzFEUXp0QlFXNURXU3c0UWtGQlV6dEJRWEZEZEVJN1NVRkJRVHRSUVVOSkxGTkJRVWtzUjBGQlVTeEZRVUZGTEVOQlFVTTdVVUZEWml4TlFVRkRMRWRCUVZjc1EwRkJReXhEUVVGRE8wbEJaMFJzUWl4RFFVRkRPMGxCTDBOSExIZENRVUZMTEVkQlFVdzdVVUZEU1N4UFFVRlBMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU03U1VGRGJFSXNRMEZCUXp0SlFVTkVMREpDUVVGUkxFZEJRVklzVlVGQlV5eEZRVUZWTzFGQlEyWXNTVUZCU1N4TlFVRk5MRWRCUVVjc1MwRkJTeXhEUVVGRE8xRkJRMjVDTEVsQlFVa3NRMEZCUXl4aFFVRmhMRU5CUVVNc1ZVRkJRU3hEUVVGRE8xbEJRMmhDTEVsQlFVa3NRMEZCUXl4TlFVRk5MRWxCUVVrc1EwRkJReXhEUVVGRExFVkJRVVVzU1VGQlNTeEZRVUZGTEVWQlFVVTdaMEpCUTNaQ0xFMUJRVTBzUjBGQlJ5eEpRVUZKTEVOQlFVTTdZVUZEYWtJN1VVRkRUQ3hEUVVGRExFTkJRVU1zUTBGQlF6dFJRVU5JTEU5QlFVOHNUVUZCVFN4RFFVRkRPMGxCUTJ4Q0xFTkJRVU03U1VGRFJDeHpRa0ZCUnl4SFFVRklMRlZCUVVrc1VVRkJaMElzUlVGQlJTeERRVUZUTzFGQlF6TkNMRWxCUVVrc1EwRkJReXhIUVVGakxGRkJRVkVzU1VGQlNTeEpRVUZKTEVOQlFVTXNTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJReXhKUVVGSkxFTkJRVU1zU1VGQlNTeERRVUZETEZGQlFWRXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhKUVVGSkxFTkJRVU1zU1VGQlNTeERRVUZETEZGQlFWRXNRMEZCUXl4SFFVRkhMRWxCUVVrc1UwRkJVeXhGUVVGRkxFTkJRVU03VVVGRGRrY3NRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFJRVU5VTEVWQlFVVXNTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJRenRKUVVOaUxFTkJRVU03U1VGRFJDeDVRa0ZCVFN4SFFVRk9MRlZCUVU4c1VVRkJaMElzUlVGQlJTeERRVUZUTzFGQlF6bENMRWxCUVVrc1JVRkJSU3hIUVVGakxFbEJRVWtzUTBGQlF5eEpRVUZKTEVOQlFVTXNVVUZCVVN4RFFVRkRMRU5CUVVNN1VVRkRlRU1zUlVGQlJTeERRVUZETEUxQlFVMHNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRSUVVOaUxFbEJRVWtzUlVGQlJTeERRVUZETEV0QlFVc3NSVUZCUlN4TFFVRkxMRU5CUVVNc1JVRkJSVHRaUVVOc1FpeFBRVUZQTEVsQlFVa3NRMEZCUXl4SlFVRkpMRU5CUVVNc1VVRkJVU3hEUVVGRExFTkJRVU03VTBGRE9VSTdVVUZEUkN4RlFVRkZMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU03U1VGRFlpeERRVUZETzBsQlEwUXNlVUpCUVUwc1IwRkJUaXhWUVVGUExFTkJRVFJETzFGQlF5OURMRXRCUVVzc1NVRkJTU3hSUVVGUkxFbEJRVWtzU1VGQlNTeERRVUZETEVsQlFVa3NSVUZCUlR0WlFVTTFRaXhEUVVGRExFTkJRVmtzU1VGQlNTeERRVUZETEVsQlFVa3NRMEZCUXl4UlFVRlJMRU5CUVVNc1JVRkJSU3hOUVVGTkxFTkJRVU1zVVVGQlVTeERRVUZETEVOQlFVTXNRMEZCUXp0VFFVTjJSRHRKUVVOTUxFTkJRVU03U1VGRFJDeG5RMEZCWVN4SFFVRmlMRlZCUVdNc1EwRkJjMEk3VVVGRGFFTXNTVUZCU1N4RFFVRkRMRTFCUVUwc1EwRkJReXhWUVVGRExFVkJRVVVzUlVGQlJTeEZRVUZGTEVsQlFVc3NUMEZCUVN4RlFVRkZMRU5CUVVNc1RVRkJUU3hEUVVGRExFTkJRVU1zUTBGQlF5eEZRVUZhTEVOQlFWa3NRMEZCUXl4RFFVRkRPMGxCUXpGRExFTkJRVU03U1VGRFJDd3JRa0ZCV1N4SFFVRmFMRlZCUVdFc1MwRkJaVHRSUVVONFFpeEpRVUZKTEUxQlFVMHNSMEZCWVN4SlFVRkpMRkZCUVZFc1JVRkJSU3hEUVVGRE8xRkJRM1JETEVsQlFVa3NRMEZCUXl4TlFVRk5MRU5CUVVNc1ZVRkJReXhGUVVGRkxFVkJRVVVzUlVGQlJUdFpRVU5tTEVsQlFVa3NSVUZCUlN4SlFVRkpMRXRCUVVzc1EwRkJReXhKUVVGSkxFVkJRVVU3WjBKQlEyeENMRWxCUVVrc1EwRkJReXhIUVVGSExFVkJRVVVzUTBGQlF5eFpRVUZaTEVOQlFVTXNTMEZCU3l4RFFVRkRMRWxCUVVrc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF5eEZRVU51UXl4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFdEJRVXNzUlVGQlJTeERRVUZETzJkQ1FVTnNRaXhKUVVGSkxFTkJRVU1zUjBGQlJ5eERRVUZETEVWQlFVVTdiMEpCUTFBc1RVRkJUU3hEUVVGRExFbEJRVWtzUTBGQlF5eEZRVUZGTEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNN2IwSkJRM0JDTEUxQlFVMHNRMEZCUXl4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRE8ybENRVU5xUWp0aFFVTktPMUZCUTB3c1EwRkJReXhEUVVGRExFTkJRVU03VVVGRFNDeFBRVUZQTEUxQlFVMHNRMEZCUXp0SlFVTnNRaXhEUVVGRE8wbEJRMHdzWlVGQlF6dEJRVUZFTEVOQlFVTXNRVUZzUkVRc1NVRnJSRU03UVVGc1JGa3NORUpCUVZFN1FVRnZSSEpDTEZOQlFWTXNhVUpCUVdsQ0xFTkJRVU1zUTBGQlRTeEZRVUZGTEVOQlFVMDdTVUZEY2tNc1QwRkJUeXhOUVVGTkxFTkJRVU1zU1VGQlNTeERRVUZETEZsQlFWa3NRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eE5RVUZOTEVOQlFVRTdRVUZEYWtRc1EwRkJRenRCUVVWRUxGTkJRV2RDTEZOQlFWTXNRMEZCVHl4TFFVRlpMRVZCUVVVc1MwRkJZU3hGUVVGRkxFVkJRVEJDTEVWQlFVVXNVMEZCYVVJN1NVRkRkRWNzU1VGQlNTeERRVUZETEVkQlFVY3NTMEZCU3l4RFFVRkRMRTFCUVUwc1JVRkRhRUlzUTBGQlF5eEhRVUZITEVsQlFVa3NZVUZCWVN4RFFVRkRMRU5CUVVNc1JVRkJSU3hMUVVGTExFVkJRVVVzUlVGQlJTeEZRVUZGTEZOQlFWTXNRMEZCUXl4RFFVRkRPMGxCUTI1RUxFOUJRVThzUTBGQlF5eERRVUZETEZkQlFWY3NSVUZCUlR0UlFVRkRMRU5CUVVNN1NVRkRlRUlzU1VGQlNTeFZRVUZWTEVkQlFXZENMRVZCUVVVc1EwRkJRenRKUVVOcVF5eEpRVUZKTEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc2FVSkJRV2xDTEVOQlFVTXNWVUZCVlN4RFFVRkRMRU5CUVVNN1NVRkRlRU1zVlVGQlZTeERRVUZETEU5QlFVOHNRMEZCUXl4VlFVRlZMRU5CUVVNN1VVRkRNVUlzU1VGQlNTeERRVUZETEVkQlFVY3NWVUZCUXl4SFFVRkhPMWxCUTFJc1NVRkJTU3hEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRPMWxCUTJZc1NVRkJTU3hQUVVGUExFTkJRVU1zU1VGQlNTeFJRVUZSTzJkQ1FVRkZMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUjBGQlJ5eExRVUZMTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1VVRkRhRVFzUTBGQlF5eERRVUZETzFGQlEwWXNRMEZCUXl4RFFVRkRMRkZCUVZFc1EwRkJReXhEUVVGRE8xRkJRMW9zUTBGQlF5eERRVUZETEZGQlFWRXNRMEZCUXl4RFFVRkRPMGxCUTJoQ0xFTkJRVU1zUTBGQlF5eERRVUZETzBsQlEwZ3NUMEZCVHl4RlFVRkZMRTFCUVUwc1JVRkJSU3hEUVVGRExFVkJRVVVzVlVGQlZTeEZRVUZGTEZWQlFWVXNSVUZCUlN4RFFVRkRPMEZCUTJwRUxFTkJRVU03UVVGbVJDdzRRa0ZsUXlKOSIsIlwidXNlIHN0cmljdFwiO1xyXG5PYmplY3QuZGVmaW5lUHJvcGVydHkoZXhwb3J0cywgXCJfX2VzTW9kdWxlXCIsIHsgdmFsdWU6IHRydWUgfSk7XHJcbnZhciBQYWlyaW5nSGVhcCA9IChmdW5jdGlvbiAoKSB7XHJcbiAgICBmdW5jdGlvbiBQYWlyaW5nSGVhcChlbGVtKSB7XHJcbiAgICAgICAgdGhpcy5lbGVtID0gZWxlbTtcclxuICAgICAgICB0aGlzLnN1YmhlYXBzID0gW107XHJcbiAgICB9XHJcbiAgICBQYWlyaW5nSGVhcC5wcm90b3R5cGUudG9TdHJpbmcgPSBmdW5jdGlvbiAoc2VsZWN0b3IpIHtcclxuICAgICAgICB2YXIgc3RyID0gXCJcIiwgbmVlZENvbW1hID0gZmFsc2U7XHJcbiAgICAgICAgZm9yICh2YXIgaSA9IDA7IGkgPCB0aGlzLnN1YmhlYXBzLmxlbmd0aDsgKytpKSB7XHJcbiAgICAgICAgICAgIHZhciBzdWJoZWFwID0gdGhpcy5zdWJoZWFwc1tpXTtcclxuICAgICAgICAgICAgaWYgKCFzdWJoZWFwLmVsZW0pIHtcclxuICAgICAgICAgICAgICAgIG5lZWRDb21tYSA9IGZhbHNlO1xyXG4gICAgICAgICAgICAgICAgY29udGludWU7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgaWYgKG5lZWRDb21tYSkge1xyXG4gICAgICAgICAgICAgICAgc3RyID0gc3RyICsgXCIsXCI7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgc3RyID0gc3RyICsgc3ViaGVhcC50b1N0cmluZyhzZWxlY3Rvcik7XHJcbiAgICAgICAgICAgIG5lZWRDb21tYSA9IHRydWU7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIGlmIChzdHIgIT09IFwiXCIpIHtcclxuICAgICAgICAgICAgc3RyID0gXCIoXCIgKyBzdHIgKyBcIilcIjtcclxuICAgICAgICB9XHJcbiAgICAgICAgcmV0dXJuICh0aGlzLmVsZW0gPyBzZWxlY3Rvcih0aGlzLmVsZW0pIDogXCJcIikgKyBzdHI7XHJcbiAgICB9O1xyXG4gICAgUGFpcmluZ0hlYXAucHJvdG90eXBlLmZvckVhY2ggPSBmdW5jdGlvbiAoZikge1xyXG4gICAgICAgIGlmICghdGhpcy5lbXB0eSgpKSB7XHJcbiAgICAgICAgICAgIGYodGhpcy5lbGVtLCB0aGlzKTtcclxuICAgICAgICAgICAgdGhpcy5zdWJoZWFwcy5mb3JFYWNoKGZ1bmN0aW9uIChzKSB7IHJldHVybiBzLmZvckVhY2goZik7IH0pO1xyXG4gICAgICAgIH1cclxuICAgIH07XHJcbiAgICBQYWlyaW5nSGVhcC5wcm90b3R5cGUuY291bnQgPSBmdW5jdGlvbiAoKSB7XHJcbiAgICAgICAgcmV0dXJuIHRoaXMuZW1wdHkoKSA/IDAgOiAxICsgdGhpcy5zdWJoZWFwcy5yZWR1Y2UoZnVuY3Rpb24gKG4sIGgpIHtcclxuICAgICAgICAgICAgcmV0dXJuIG4gKyBoLmNvdW50KCk7XHJcbiAgICAgICAgfSwgMCk7XHJcbiAgICB9O1xyXG4gICAgUGFpcmluZ0hlYXAucHJvdG90eXBlLm1pbiA9IGZ1bmN0aW9uICgpIHtcclxuICAgICAgICByZXR1cm4gdGhpcy5lbGVtO1xyXG4gICAgfTtcclxuICAgIFBhaXJpbmdIZWFwLnByb3RvdHlwZS5lbXB0eSA9IGZ1bmN0aW9uICgpIHtcclxuICAgICAgICByZXR1cm4gdGhpcy5lbGVtID09IG51bGw7XHJcbiAgICB9O1xyXG4gICAgUGFpcmluZ0hlYXAucHJvdG90eXBlLmNvbnRhaW5zID0gZnVuY3Rpb24gKGgpIHtcclxuICAgICAgICBpZiAodGhpcyA9PT0gaClcclxuICAgICAgICAgICAgcmV0dXJuIHRydWU7XHJcbiAgICAgICAgZm9yICh2YXIgaSA9IDA7IGkgPCB0aGlzLnN1YmhlYXBzLmxlbmd0aDsgaSsrKSB7XHJcbiAgICAgICAgICAgIGlmICh0aGlzLnN1YmhlYXBzW2ldLmNvbnRhaW5zKGgpKVxyXG4gICAgICAgICAgICAgICAgcmV0dXJuIHRydWU7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIHJldHVybiBmYWxzZTtcclxuICAgIH07XHJcbiAgICBQYWlyaW5nSGVhcC5wcm90b3R5cGUuaXNIZWFwID0gZnVuY3Rpb24gKGxlc3NUaGFuKSB7XHJcbiAgICAgICAgdmFyIF90aGlzID0gdGhpcztcclxuICAgICAgICByZXR1cm4gdGhpcy5zdWJoZWFwcy5ldmVyeShmdW5jdGlvbiAoaCkgeyByZXR1cm4gbGVzc1RoYW4oX3RoaXMuZWxlbSwgaC5lbGVtKSAmJiBoLmlzSGVhcChsZXNzVGhhbik7IH0pO1xyXG4gICAgfTtcclxuICAgIFBhaXJpbmdIZWFwLnByb3RvdHlwZS5pbnNlcnQgPSBmdW5jdGlvbiAob2JqLCBsZXNzVGhhbikge1xyXG4gICAgICAgIHJldHVybiB0aGlzLm1lcmdlKG5ldyBQYWlyaW5nSGVhcChvYmopLCBsZXNzVGhhbik7XHJcbiAgICB9O1xyXG4gICAgUGFpcmluZ0hlYXAucHJvdG90eXBlLm1lcmdlID0gZnVuY3Rpb24gKGhlYXAyLCBsZXNzVGhhbikge1xyXG4gICAgICAgIGlmICh0aGlzLmVtcHR5KCkpXHJcbiAgICAgICAgICAgIHJldHVybiBoZWFwMjtcclxuICAgICAgICBlbHNlIGlmIChoZWFwMi5lbXB0eSgpKVxyXG4gICAgICAgICAgICByZXR1cm4gdGhpcztcclxuICAgICAgICBlbHNlIGlmIChsZXNzVGhhbih0aGlzLmVsZW0sIGhlYXAyLmVsZW0pKSB7XHJcbiAgICAgICAgICAgIHRoaXMuc3ViaGVhcHMucHVzaChoZWFwMik7XHJcbiAgICAgICAgICAgIHJldHVybiB0aGlzO1xyXG4gICAgICAgIH1cclxuICAgICAgICBlbHNlIHtcclxuICAgICAgICAgICAgaGVhcDIuc3ViaGVhcHMucHVzaCh0aGlzKTtcclxuICAgICAgICAgICAgcmV0dXJuIGhlYXAyO1xyXG4gICAgICAgIH1cclxuICAgIH07XHJcbiAgICBQYWlyaW5nSGVhcC5wcm90b3R5cGUucmVtb3ZlTWluID0gZnVuY3Rpb24gKGxlc3NUaGFuKSB7XHJcbiAgICAgICAgaWYgKHRoaXMuZW1wdHkoKSlcclxuICAgICAgICAgICAgcmV0dXJuIG51bGw7XHJcbiAgICAgICAgZWxzZVxyXG4gICAgICAgICAgICByZXR1cm4gdGhpcy5tZXJnZVBhaXJzKGxlc3NUaGFuKTtcclxuICAgIH07XHJcbiAgICBQYWlyaW5nSGVhcC5wcm90b3R5cGUubWVyZ2VQYWlycyA9IGZ1bmN0aW9uIChsZXNzVGhhbikge1xyXG4gICAgICAgIGlmICh0aGlzLnN1YmhlYXBzLmxlbmd0aCA9PSAwKVxyXG4gICAgICAgICAgICByZXR1cm4gbmV3IFBhaXJpbmdIZWFwKG51bGwpO1xyXG4gICAgICAgIGVsc2UgaWYgKHRoaXMuc3ViaGVhcHMubGVuZ3RoID09IDEpIHtcclxuICAgICAgICAgICAgcmV0dXJuIHRoaXMuc3ViaGVhcHNbMF07XHJcbiAgICAgICAgfVxyXG4gICAgICAgIGVsc2Uge1xyXG4gICAgICAgICAgICB2YXIgZmlyc3RQYWlyID0gdGhpcy5zdWJoZWFwcy5wb3AoKS5tZXJnZSh0aGlzLnN1YmhlYXBzLnBvcCgpLCBsZXNzVGhhbik7XHJcbiAgICAgICAgICAgIHZhciByZW1haW5pbmcgPSB0aGlzLm1lcmdlUGFpcnMobGVzc1RoYW4pO1xyXG4gICAgICAgICAgICByZXR1cm4gZmlyc3RQYWlyLm1lcmdlKHJlbWFpbmluZywgbGVzc1RoYW4pO1xyXG4gICAgICAgIH1cclxuICAgIH07XHJcbiAgICBQYWlyaW5nSGVhcC5wcm90b3R5cGUuZGVjcmVhc2VLZXkgPSBmdW5jdGlvbiAoc3ViaGVhcCwgbmV3VmFsdWUsIHNldEhlYXBOb2RlLCBsZXNzVGhhbikge1xyXG4gICAgICAgIHZhciBuZXdIZWFwID0gc3ViaGVhcC5yZW1vdmVNaW4obGVzc1RoYW4pO1xyXG4gICAgICAgIHN1YmhlYXAuZWxlbSA9IG5ld0hlYXAuZWxlbTtcclxuICAgICAgICBzdWJoZWFwLnN1YmhlYXBzID0gbmV3SGVhcC5zdWJoZWFwcztcclxuICAgICAgICBpZiAoc2V0SGVhcE5vZGUgIT09IG51bGwgJiYgbmV3SGVhcC5lbGVtICE9PSBudWxsKSB7XHJcbiAgICAgICAgICAgIHNldEhlYXBOb2RlKHN1YmhlYXAuZWxlbSwgc3ViaGVhcCk7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIHZhciBwYWlyaW5nTm9kZSA9IG5ldyBQYWlyaW5nSGVhcChuZXdWYWx1ZSk7XHJcbiAgICAgICAgaWYgKHNldEhlYXBOb2RlICE9PSBudWxsKSB7XHJcbiAgICAgICAgICAgIHNldEhlYXBOb2RlKG5ld1ZhbHVlLCBwYWlyaW5nTm9kZSk7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIHJldHVybiB0aGlzLm1lcmdlKHBhaXJpbmdOb2RlLCBsZXNzVGhhbik7XHJcbiAgICB9O1xyXG4gICAgcmV0dXJuIFBhaXJpbmdIZWFwO1xyXG59KCkpO1xyXG5leHBvcnRzLlBhaXJpbmdIZWFwID0gUGFpcmluZ0hlYXA7XHJcbnZhciBQcmlvcml0eVF1ZXVlID0gKGZ1bmN0aW9uICgpIHtcclxuICAgIGZ1bmN0aW9uIFByaW9yaXR5UXVldWUobGVzc1RoYW4pIHtcclxuICAgICAgICB0aGlzLmxlc3NUaGFuID0gbGVzc1RoYW47XHJcbiAgICB9XHJcbiAgICBQcmlvcml0eVF1ZXVlLnByb3RvdHlwZS50b3AgPSBmdW5jdGlvbiAoKSB7XHJcbiAgICAgICAgaWYgKHRoaXMuZW1wdHkoKSkge1xyXG4gICAgICAgICAgICByZXR1cm4gbnVsbDtcclxuICAgICAgICB9XHJcbiAgICAgICAgcmV0dXJuIHRoaXMucm9vdC5lbGVtO1xyXG4gICAgfTtcclxuICAgIFByaW9yaXR5UXVldWUucHJvdG90eXBlLnB1c2ggPSBmdW5jdGlvbiAoKSB7XHJcbiAgICAgICAgdmFyIGFyZ3MgPSBbXTtcclxuICAgICAgICBmb3IgKHZhciBfaSA9IDA7IF9pIDwgYXJndW1lbnRzLmxlbmd0aDsgX2krKykge1xyXG4gICAgICAgICAgICBhcmdzW19pXSA9IGFyZ3VtZW50c1tfaV07XHJcbiAgICAgICAgfVxyXG4gICAgICAgIHZhciBwYWlyaW5nTm9kZTtcclxuICAgICAgICBmb3IgKHZhciBpID0gMCwgYXJnOyBhcmcgPSBhcmdzW2ldOyArK2kpIHtcclxuICAgICAgICAgICAgcGFpcmluZ05vZGUgPSBuZXcgUGFpcmluZ0hlYXAoYXJnKTtcclxuICAgICAgICAgICAgdGhpcy5yb290ID0gdGhpcy5lbXB0eSgpID9cclxuICAgICAgICAgICAgICAgIHBhaXJpbmdOb2RlIDogdGhpcy5yb290Lm1lcmdlKHBhaXJpbmdOb2RlLCB0aGlzLmxlc3NUaGFuKTtcclxuICAgICAgICB9XHJcbiAgICAgICAgcmV0dXJuIHBhaXJpbmdOb2RlO1xyXG4gICAgfTtcclxuICAgIFByaW9yaXR5UXVldWUucHJvdG90eXBlLmVtcHR5ID0gZnVuY3Rpb24gKCkge1xyXG4gICAgICAgIHJldHVybiAhdGhpcy5yb290IHx8ICF0aGlzLnJvb3QuZWxlbTtcclxuICAgIH07XHJcbiAgICBQcmlvcml0eVF1ZXVlLnByb3RvdHlwZS5pc0hlYXAgPSBmdW5jdGlvbiAoKSB7XHJcbiAgICAgICAgcmV0dXJuIHRoaXMucm9vdC5pc0hlYXAodGhpcy5sZXNzVGhhbik7XHJcbiAgICB9O1xyXG4gICAgUHJpb3JpdHlRdWV1ZS5wcm90b3R5cGUuZm9yRWFjaCA9IGZ1bmN0aW9uIChmKSB7XHJcbiAgICAgICAgdGhpcy5yb290LmZvckVhY2goZik7XHJcbiAgICB9O1xyXG4gICAgUHJpb3JpdHlRdWV1ZS5wcm90b3R5cGUucG9wID0gZnVuY3Rpb24gKCkge1xyXG4gICAgICAgIGlmICh0aGlzLmVtcHR5KCkpIHtcclxuICAgICAgICAgICAgcmV0dXJuIG51bGw7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIHZhciBvYmogPSB0aGlzLnJvb3QubWluKCk7XHJcbiAgICAgICAgdGhpcy5yb290ID0gdGhpcy5yb290LnJlbW92ZU1pbih0aGlzLmxlc3NUaGFuKTtcclxuICAgICAgICByZXR1cm4gb2JqO1xyXG4gICAgfTtcclxuICAgIFByaW9yaXR5UXVldWUucHJvdG90eXBlLnJlZHVjZUtleSA9IGZ1bmN0aW9uIChoZWFwTm9kZSwgbmV3S2V5LCBzZXRIZWFwTm9kZSkge1xyXG4gICAgICAgIGlmIChzZXRIZWFwTm9kZSA9PT0gdm9pZCAwKSB7IHNldEhlYXBOb2RlID0gbnVsbDsgfVxyXG4gICAgICAgIHRoaXMucm9vdCA9IHRoaXMucm9vdC5kZWNyZWFzZUtleShoZWFwTm9kZSwgbmV3S2V5LCBzZXRIZWFwTm9kZSwgdGhpcy5sZXNzVGhhbik7XHJcbiAgICB9O1xyXG4gICAgUHJpb3JpdHlRdWV1ZS5wcm90b3R5cGUudG9TdHJpbmcgPSBmdW5jdGlvbiAoc2VsZWN0b3IpIHtcclxuICAgICAgICByZXR1cm4gdGhpcy5yb290LnRvU3RyaW5nKHNlbGVjdG9yKTtcclxuICAgIH07XHJcbiAgICBQcmlvcml0eVF1ZXVlLnByb3RvdHlwZS5jb3VudCA9IGZ1bmN0aW9uICgpIHtcclxuICAgICAgICByZXR1cm4gdGhpcy5yb290LmNvdW50KCk7XHJcbiAgICB9O1xyXG4gICAgcmV0dXJuIFByaW9yaXR5UXVldWU7XHJcbn0oKSk7XHJcbmV4cG9ydHMuUHJpb3JpdHlRdWV1ZSA9IFByaW9yaXR5UXVldWU7XHJcbi8vIyBzb3VyY2VNYXBwaW5nVVJMPWRhdGE6YXBwbGljYXRpb24vanNvbjtiYXNlNjQsZXlKMlpYSnphVzl1SWpvekxDSm1hV3hsSWpvaWNIRjFaWFZsTG1weklpd2ljMjkxY21ObFVtOXZkQ0k2SWlJc0luTnZkWEpqWlhNaU9sc2lMaTR2TGk0dlYyVmlRMjlzWVM5emNtTXZjSEYxWlhWbExuUnpJbDBzSW01aGJXVnpJanBiWFN3aWJXRndjR2x1WjNNaU9pSTdPMEZCUTBFN1NVRkpTU3h4UWtGQmJVSXNTVUZCVHp0UlFVRlFMRk5CUVVrc1IwRkJTaXhKUVVGSkxFTkJRVWM3VVVGRGRFSXNTVUZCU1N4RFFVRkRMRkZCUVZFc1IwRkJSeXhGUVVGRkxFTkJRVU03U1VGRGRrSXNRMEZCUXp0SlFVVk5MRGhDUVVGUkxFZEJRV1lzVlVGQlowSXNVVUZCVVR0UlFVTndRaXhKUVVGSkxFZEJRVWNzUjBGQlJ5eEZRVUZGTEVWQlFVVXNVMEZCVXl4SFFVRkhMRXRCUVVzc1EwRkJRenRSUVVOb1F5eExRVUZMTEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1JVRkJSU3hEUVVGRExFZEJRVWNzU1VGQlNTeERRVUZETEZGQlFWRXNRMEZCUXl4TlFVRk5MRVZCUVVVc1JVRkJSU3hEUVVGRExFVkJRVVU3V1VGRE0wTXNTVUZCU1N4UFFVRlBMRWRCUVcxQ0xFbEJRVWtzUTBGQlF5eFJRVUZSTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1dVRkRMME1zU1VGQlNTeERRVUZETEU5QlFVOHNRMEZCUXl4SlFVRkpMRVZCUVVVN1owSkJRMllzVTBGQlV5eEhRVUZITEV0QlFVc3NRMEZCUXp0blFrRkRiRUlzVTBGQlV6dGhRVU5hTzFsQlEwUXNTVUZCU1N4VFFVRlRMRVZCUVVVN1owSkJRMWdzUjBGQlJ5eEhRVUZITEVkQlFVY3NSMEZCUnl4SFFVRkhMRU5CUVVNN1lVRkRia0k3V1VGRFJDeEhRVUZITEVkQlFVY3NSMEZCUnl4SFFVRkhMRTlCUVU4c1EwRkJReXhSUVVGUkxFTkJRVU1zVVVGQlVTeERRVUZETEVOQlFVTTdXVUZEZGtNc1UwRkJVeXhIUVVGSExFbEJRVWtzUTBGQlF6dFRRVU53UWp0UlFVTkVMRWxCUVVrc1IwRkJSeXhMUVVGTExFVkJRVVVzUlVGQlJUdFpRVU5hTEVkQlFVY3NSMEZCUnl4SFFVRkhMRWRCUVVjc1IwRkJSeXhIUVVGSExFZEJRVWNzUTBGQlF6dFRRVU42UWp0UlFVTkVMRTlCUVU4c1EwRkJReXhKUVVGSkxFTkJRVU1zU1VGQlNTeERRVUZETEVOQlFVTXNRMEZCUXl4UlFVRlJMRU5CUVVNc1NVRkJTU3hEUVVGRExFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RlFVRkZMRU5CUVVNc1IwRkJSeXhIUVVGSExFTkJRVU03U1VGRGVFUXNRMEZCUXp0SlFVVk5MRFpDUVVGUExFZEJRV1FzVlVGQlpTeERRVUZETzFGQlExb3NTVUZCU1N4RFFVRkRMRWxCUVVrc1EwRkJReXhMUVVGTExFVkJRVVVzUlVGQlJUdFpRVU5tTEVOQlFVTXNRMEZCUXl4SlFVRkpMRU5CUVVNc1NVRkJTU3hGUVVGRkxFbEJRVWtzUTBGQlF5eERRVUZETzFsQlEyNUNMRWxCUVVrc1EwRkJReXhSUVVGUkxFTkJRVU1zVDBGQlR5eERRVUZETEZWQlFVRXNRMEZCUXl4SlFVRkpMRTlCUVVFc1EwRkJReXhEUVVGRExFOUJRVThzUTBGQlF5eERRVUZETEVOQlFVTXNSVUZCV2l4RFFVRlpMRU5CUVVNc1EwRkJRenRUUVVNMVF6dEpRVU5NTEVOQlFVTTdTVUZGVFN3eVFrRkJTeXhIUVVGYU8xRkJRMGtzVDBGQlR5eEpRVUZKTEVOQlFVTXNTMEZCU3l4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRWxCUVVrc1EwRkJReXhSUVVGUkxFTkJRVU1zVFVGQlRTeERRVUZETEZWQlFVTXNRMEZCVXl4RlFVRkZMRU5CUVdsQ08xbEJRelZGTEU5QlFVOHNRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJReXhMUVVGTExFVkJRVVVzUTBGQlF6dFJRVU42UWl4RFFVRkRMRVZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU03U1VGRFZpeERRVUZETzBsQlJVMHNlVUpCUVVjc1IwRkJWanRSUVVOSkxFOUJRVThzU1VGQlNTeERRVUZETEVsQlFVa3NRMEZCUXp0SlFVTnlRaXhEUVVGRE8wbEJSVTBzTWtKQlFVc3NSMEZCV2p0UlFVTkpMRTlCUVU4c1NVRkJTU3hEUVVGRExFbEJRVWtzU1VGQlNTeEpRVUZKTEVOQlFVTTdTVUZETjBJc1EwRkJRenRKUVVWTkxEaENRVUZSTEVkQlFXWXNWVUZCWjBJc1EwRkJhVUk3VVVGRE4wSXNTVUZCU1N4SlFVRkpMRXRCUVVzc1EwRkJRenRaUVVGRkxFOUJRVThzU1VGQlNTeERRVUZETzFGQlF6VkNMRXRCUVVzc1NVRkJTU3hEUVVGRExFZEJRVWNzUTBGQlF5eEZRVUZGTEVOQlFVTXNSMEZCUnl4SlFVRkpMRU5CUVVNc1VVRkJVU3hEUVVGRExFMUJRVTBzUlVGQlJTeERRVUZETEVWQlFVVXNSVUZCUlR0WlFVTXpReXhKUVVGSkxFbEJRVWtzUTBGQlF5eFJRVUZSTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1VVRkJVU3hEUVVGRExFTkJRVU1zUTBGQlF6dG5Ra0ZCUlN4UFFVRlBMRWxCUVVrc1EwRkJRenRUUVVOcVJEdFJRVU5FTEU5QlFVOHNTMEZCU3l4RFFVRkRPMGxCUTJwQ0xFTkJRVU03U1VGRlRTdzBRa0ZCVFN4SFFVRmlMRlZCUVdNc1VVRkJhVU03VVVGQkwwTXNhVUpCUlVNN1VVRkVSeXhQUVVGUExFbEJRVWtzUTBGQlF5eFJRVUZSTEVOQlFVTXNTMEZCU3l4RFFVRkRMRlZCUVVFc1EwRkJReXhKUVVGSExFOUJRVUVzVVVGQlVTeERRVUZETEV0QlFVa3NRMEZCUXl4SlFVRkpMRVZCUVVVc1EwRkJReXhEUVVGRExFbEJRVWtzUTBGQlF5eEpRVUZKTEVOQlFVTXNRMEZCUXl4TlFVRk5MRU5CUVVNc1VVRkJVU3hEUVVGRExFVkJRV3BFTEVOQlFXbEVMRU5CUVVNc1EwRkJRenRKUVVOMFJpeERRVUZETzBsQlJVMHNORUpCUVUwc1IwRkJZaXhWUVVGakxFZEJRVThzUlVGQlJTeFJRVUZSTzFGQlF6TkNMRTlCUVU4c1NVRkJTU3hEUVVGRExFdEJRVXNzUTBGQlF5eEpRVUZKTEZkQlFWY3NRMEZCU1N4SFFVRkhMRU5CUVVNc1JVRkJSU3hSUVVGUkxFTkJRVU1zUTBGQlF6dEpRVU42UkN4RFFVRkRPMGxCUlUwc01rSkJRVXNzUjBGQldpeFZRVUZoTEV0QlFYRkNMRVZCUVVVc1VVRkJVVHRSUVVONFF5eEpRVUZKTEVsQlFVa3NRMEZCUXl4TFFVRkxMRVZCUVVVN1dVRkJSU3hQUVVGUExFdEJRVXNzUTBGQlF6dGhRVU14UWl4SlFVRkpMRXRCUVVzc1EwRkJReXhMUVVGTExFVkJRVVU3V1VGQlJTeFBRVUZQTEVsQlFVa3NRMEZCUXp0aFFVTXZRaXhKUVVGSkxGRkJRVkVzUTBGQlF5eEpRVUZKTEVOQlFVTXNTVUZCU1N4RlFVRkZMRXRCUVVzc1EwRkJReXhKUVVGSkxFTkJRVU1zUlVGQlJUdFpRVU4wUXl4SlFVRkpMRU5CUVVNc1VVRkJVU3hEUVVGRExFbEJRVWtzUTBGQlF5eExRVUZMTEVOQlFVTXNRMEZCUXp0WlFVTXhRaXhQUVVGUExFbEJRVWtzUTBGQlF6dFRRVU5tTzJGQlFVMDdXVUZEU0N4TFFVRkxMRU5CUVVNc1VVRkJVU3hEUVVGRExFbEJRVWtzUTBGQlF5eEpRVUZKTEVOQlFVTXNRMEZCUXp0WlFVTXhRaXhQUVVGUExFdEJRVXNzUTBGQlF6dFRRVU5vUWp0SlFVTk1MRU5CUVVNN1NVRkZUU3dyUWtGQlV5eEhRVUZvUWl4VlFVRnBRaXhSUVVGcFF6dFJRVU01UXl4SlFVRkpMRWxCUVVrc1EwRkJReXhMUVVGTExFVkJRVVU3V1VGQlJTeFBRVUZQTEVsQlFVa3NRMEZCUXpzN1dVRkRla0lzVDBGQlR5eEpRVUZKTEVOQlFVTXNWVUZCVlN4RFFVRkRMRkZCUVZFc1EwRkJReXhEUVVGRE8wbEJRekZETEVOQlFVTTdTVUZGVFN4blEwRkJWU3hIUVVGcVFpeFZRVUZyUWl4UlFVRnBRenRSUVVNdlF5eEpRVUZKTEVsQlFVa3NRMEZCUXl4UlFVRlJMRU5CUVVNc1RVRkJUU3hKUVVGSkxFTkJRVU03V1VGQlJTeFBRVUZQTEVsQlFVa3NWMEZCVnl4RFFVRkpMRWxCUVVrc1EwRkJReXhEUVVGRE8yRkJRekZFTEVsQlFVa3NTVUZCU1N4RFFVRkRMRkZCUVZFc1EwRkJReXhOUVVGTkxFbEJRVWtzUTBGQlF5eEZRVUZGTzFsQlFVVXNUMEZCVHl4SlFVRkpMRU5CUVVNc1VVRkJVU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzFOQlFVVTdZVUZETTBRN1dVRkRSQ3hKUVVGSkxGTkJRVk1zUjBGQlJ5eEpRVUZKTEVOQlFVTXNVVUZCVVN4RFFVRkRMRWRCUVVjc1JVRkJSU3hEUVVGRExFdEJRVXNzUTBGQlF5eEpRVUZKTEVOQlFVTXNVVUZCVVN4RFFVRkRMRWRCUVVjc1JVRkJSU3hGUVVGRkxGRkJRVkVzUTBGQlF5eERRVUZETzFsQlEzcEZMRWxCUVVrc1UwRkJVeXhIUVVGSExFbEJRVWtzUTBGQlF5eFZRVUZWTEVOQlFVTXNVVUZCVVN4RFFVRkRMRU5CUVVNN1dVRkRNVU1zVDBGQlR5eFRRVUZUTEVOQlFVTXNTMEZCU3l4RFFVRkRMRk5CUVZNc1JVRkJSU3hSUVVGUkxFTkJRVU1zUTBGQlF6dFRRVU12UXp0SlFVTk1MRU5CUVVNN1NVRkRUU3hwUTBGQlZ5eEhRVUZzUWl4VlFVRnRRaXhQUVVGMVFpeEZRVUZGTEZGQlFWY3NSVUZCUlN4WFFVRTBReXhGUVVGRkxGRkJRV2xETzFGQlEzQkpMRWxCUVVrc1QwRkJUeXhIUVVGSExFOUJRVThzUTBGQlF5eFRRVUZUTEVOQlFVTXNVVUZCVVN4RFFVRkRMRU5CUVVNN1VVRkZNVU1zVDBGQlR5eERRVUZETEVsQlFVa3NSMEZCUnl4UFFVRlBMRU5CUVVNc1NVRkJTU3hEUVVGRE8xRkJRelZDTEU5QlFVOHNRMEZCUXl4UlFVRlJMRWRCUVVjc1QwRkJUeXhEUVVGRExGRkJRVkVzUTBGQlF6dFJRVU53UXl4SlFVRkpMRmRCUVZjc1MwRkJTeXhKUVVGSkxFbEJRVWtzVDBGQlR5eERRVUZETEVsQlFVa3NTMEZCU3l4SlFVRkpMRVZCUVVVN1dVRkRMME1zVjBGQlZ5eERRVUZETEU5QlFVOHNRMEZCUXl4SlFVRkpMRVZCUVVVc1QwRkJUeXhEUVVGRExFTkJRVU03VTBGRGRFTTdVVUZEUkN4SlFVRkpMRmRCUVZjc1IwRkJSeXhKUVVGSkxGZEJRVmNzUTBGQlF5eFJRVUZSTEVOQlFVTXNRMEZCUXp0UlFVTTFReXhKUVVGSkxGZEJRVmNzUzBGQlN5eEpRVUZKTEVWQlFVVTdXVUZEZEVJc1YwRkJWeXhEUVVGRExGRkJRVkVzUlVGQlJTeFhRVUZYTEVOQlFVTXNRMEZCUXp0VFFVTjBRenRSUVVORUxFOUJRVThzU1VGQlNTeERRVUZETEV0QlFVc3NRMEZCUXl4WFFVRlhMRVZCUVVVc1VVRkJVU3hEUVVGRExFTkJRVU03U1VGRE4wTXNRMEZCUXp0SlFVTk1MR3RDUVVGRE8wRkJRVVFzUTBGQlF5eEJRWHBIUkN4SlFYbEhRenRCUVhwSFdTeHJRMEZCVnp0QlFUaEhlRUk3U1VGRlNTeDFRa0ZCYjBJc1VVRkJhVU03VVVGQmFrTXNZVUZCVVN4SFFVRlNMRkZCUVZFc1EwRkJlVUk3U1VGQlNTeERRVUZETzBsQlMyNUVMREpDUVVGSExFZEJRVlk3VVVGRFNTeEpRVUZKTEVsQlFVa3NRMEZCUXl4TFFVRkxMRVZCUVVVc1JVRkJSVHRaUVVGRkxFOUJRVThzU1VGQlNTeERRVUZETzFOQlFVVTdVVUZEYkVNc1QwRkJUeXhKUVVGSkxFTkJRVU1zU1VGQlNTeERRVUZETEVsQlFVa3NRMEZCUXp0SlFVTXhRaXhEUVVGRE8wbEJTMDBzTkVKQlFVa3NSMEZCV0R0UlFVRlpMR05CUVZrN1lVRkJXaXhWUVVGWkxFVkJRVm9zY1VKQlFWa3NSVUZCV2l4SlFVRlpPMWxCUVZvc2VVSkJRVms3TzFGQlEzQkNMRWxCUVVrc1YwRkJWeXhEUVVGRE8xRkJRMmhDTEV0QlFVc3NTVUZCU1N4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRkxFZEJRVWNzUlVGQlJTeEhRVUZITEVkQlFVTXNTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGRkxFVkJRVVVzUTBGQlF5eEZRVUZGTzFsQlEyNURMRmRCUVZjc1IwRkJSeXhKUVVGSkxGZEJRVmNzUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXp0WlFVTnVReXhKUVVGSkxFTkJRVU1zU1VGQlNTeEhRVUZITEVsQlFVa3NRMEZCUXl4TFFVRkxMRVZCUVVVc1EwRkJReXhEUVVGRE8yZENRVU4wUWl4WFFVRlhMRU5CUVVNc1EwRkJReXhEUVVGRExFbEJRVWtzUTBGQlF5eEpRVUZKTEVOQlFVTXNTMEZCU3l4RFFVRkRMRmRCUVZjc1JVRkJSU3hKUVVGSkxFTkJRVU1zVVVGQlVTeERRVUZETEVOQlFVTTdVMEZEYWtVN1VVRkRSQ3hQUVVGUExGZEJRVmNzUTBGQlF6dEpRVU4yUWl4RFFVRkRPMGxCUzAwc05rSkJRVXNzUjBGQldqdFJRVU5KTEU5QlFVOHNRMEZCUXl4SlFVRkpMRU5CUVVNc1NVRkJTU3hKUVVGSkxFTkJRVU1zU1VGQlNTeERRVUZETEVsQlFVa3NRMEZCUXl4SlFVRkpMRU5CUVVNN1NVRkRla01zUTBGQlF6dEpRVXROTERoQ1FVRk5MRWRCUVdJN1VVRkRTU3hQUVVGUExFbEJRVWtzUTBGQlF5eEpRVUZKTEVOQlFVTXNUVUZCVFN4RFFVRkRMRWxCUVVrc1EwRkJReXhSUVVGUkxFTkJRVU1zUTBGQlF6dEpRVU16UXl4RFFVRkRPMGxCUzAwc0swSkJRVThzUjBGQlpDeFZRVUZsTEVOQlFVTTdVVUZEV2l4SlFVRkpMRU5CUVVNc1NVRkJTU3hEUVVGRExFOUJRVThzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0SlFVTjZRaXhEUVVGRE8wbEJTVTBzTWtKQlFVY3NSMEZCVmp0UlFVTkpMRWxCUVVrc1NVRkJTU3hEUVVGRExFdEJRVXNzUlVGQlJTeEZRVUZGTzFsQlEyUXNUMEZCVHl4SlFVRkpMRU5CUVVNN1UwRkRaanRSUVVORUxFbEJRVWtzUjBGQlJ5eEhRVUZITEVsQlFVa3NRMEZCUXl4SlFVRkpMRU5CUVVNc1IwRkJSeXhGUVVGRkxFTkJRVU03VVVGRE1VSXNTVUZCU1N4RFFVRkRMRWxCUVVrc1IwRkJSeXhKUVVGSkxFTkJRVU1zU1VGQlNTeERRVUZETEZOQlFWTXNRMEZCUXl4SlFVRkpMRU5CUVVNc1VVRkJVU3hEUVVGRExFTkJRVU03VVVGREwwTXNUMEZCVHl4SFFVRkhMRU5CUVVNN1NVRkRaaXhEUVVGRE8wbEJTVTBzYVVOQlFWTXNSMEZCYUVJc1ZVRkJhVUlzVVVGQmQwSXNSVUZCUlN4TlFVRlRMRVZCUVVVc1YwRkJiVVE3VVVGQmJrUXNORUpCUVVFc1JVRkJRU3hyUWtGQmJVUTdVVUZEY2tjc1NVRkJTU3hEUVVGRExFbEJRVWtzUjBGQlJ5eEpRVUZKTEVOQlFVTXNTVUZCU1N4RFFVRkRMRmRCUVZjc1EwRkJReXhSUVVGUkxFVkJRVVVzVFVGQlRTeEZRVUZGTEZkQlFWY3NSVUZCUlN4SlFVRkpMRU5CUVVNc1VVRkJVU3hEUVVGRExFTkJRVU03U1VGRGNFWXNRMEZCUXp0SlFVTk5MR2REUVVGUkxFZEJRV1lzVlVGQlowSXNVVUZCVVR0UlFVTndRaXhQUVVGUExFbEJRVWtzUTBGQlF5eEpRVUZKTEVOQlFVTXNVVUZCVVN4RFFVRkRMRkZCUVZFc1EwRkJReXhEUVVGRE8wbEJRM2hETEVOQlFVTTdTVUZMVFN3MlFrRkJTeXhIUVVGYU8xRkJRMGtzVDBGQlR5eEpRVUZKTEVOQlFVTXNTVUZCU1N4RFFVRkRMRXRCUVVzc1JVRkJSU3hEUVVGRE8wbEJRemRDTEVOQlFVTTdTVUZEVEN4dlFrRkJRenRCUVVGRUxFTkJRVU1zUVVGNFJVUXNTVUYzUlVNN1FVRjRSVmtzYzBOQlFXRWlmUT09IiwiXCJ1c2Ugc3RyaWN0XCI7XHJcbnZhciBfX2V4dGVuZHMgPSAodGhpcyAmJiB0aGlzLl9fZXh0ZW5kcykgfHwgKGZ1bmN0aW9uICgpIHtcclxuICAgIHZhciBleHRlbmRTdGF0aWNzID0gZnVuY3Rpb24gKGQsIGIpIHtcclxuICAgICAgICBleHRlbmRTdGF0aWNzID0gT2JqZWN0LnNldFByb3RvdHlwZU9mIHx8XHJcbiAgICAgICAgICAgICh7IF9fcHJvdG9fXzogW10gfSBpbnN0YW5jZW9mIEFycmF5ICYmIGZ1bmN0aW9uIChkLCBiKSB7IGQuX19wcm90b19fID0gYjsgfSkgfHxcclxuICAgICAgICAgICAgZnVuY3Rpb24gKGQsIGIpIHsgZm9yICh2YXIgcCBpbiBiKSBpZiAoYi5oYXNPd25Qcm9wZXJ0eShwKSkgZFtwXSA9IGJbcF07IH07XHJcbiAgICAgICAgcmV0dXJuIGV4dGVuZFN0YXRpY3MoZCwgYik7XHJcbiAgICB9O1xyXG4gICAgcmV0dXJuIGZ1bmN0aW9uIChkLCBiKSB7XHJcbiAgICAgICAgZXh0ZW5kU3RhdGljcyhkLCBiKTtcclxuICAgICAgICBmdW5jdGlvbiBfXygpIHsgdGhpcy5jb25zdHJ1Y3RvciA9IGQ7IH1cclxuICAgICAgICBkLnByb3RvdHlwZSA9IGIgPT09IG51bGwgPyBPYmplY3QuY3JlYXRlKGIpIDogKF9fLnByb3RvdHlwZSA9IGIucHJvdG90eXBlLCBuZXcgX18oKSk7XHJcbiAgICB9O1xyXG59KSgpO1xyXG5PYmplY3QuZGVmaW5lUHJvcGVydHkoZXhwb3J0cywgXCJfX2VzTW9kdWxlXCIsIHsgdmFsdWU6IHRydWUgfSk7XHJcbnZhciBUcmVlQmFzZSA9IChmdW5jdGlvbiAoKSB7XHJcbiAgICBmdW5jdGlvbiBUcmVlQmFzZSgpIHtcclxuICAgICAgICB0aGlzLmZpbmRJdGVyID0gZnVuY3Rpb24gKGRhdGEpIHtcclxuICAgICAgICAgICAgdmFyIHJlcyA9IHRoaXMuX3Jvb3Q7XHJcbiAgICAgICAgICAgIHZhciBpdGVyID0gdGhpcy5pdGVyYXRvcigpO1xyXG4gICAgICAgICAgICB3aGlsZSAocmVzICE9PSBudWxsKSB7XHJcbiAgICAgICAgICAgICAgICB2YXIgYyA9IHRoaXMuX2NvbXBhcmF0b3IoZGF0YSwgcmVzLmRhdGEpO1xyXG4gICAgICAgICAgICAgICAgaWYgKGMgPT09IDApIHtcclxuICAgICAgICAgICAgICAgICAgICBpdGVyLl9jdXJzb3IgPSByZXM7XHJcbiAgICAgICAgICAgICAgICAgICAgcmV0dXJuIGl0ZXI7XHJcbiAgICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgICAgICBlbHNlIHtcclxuICAgICAgICAgICAgICAgICAgICBpdGVyLl9hbmNlc3RvcnMucHVzaChyZXMpO1xyXG4gICAgICAgICAgICAgICAgICAgIHJlcyA9IHJlcy5nZXRfY2hpbGQoYyA+IDApO1xyXG4gICAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgICAgIHJldHVybiBudWxsO1xyXG4gICAgICAgIH07XHJcbiAgICB9XHJcbiAgICBUcmVlQmFzZS5wcm90b3R5cGUuY2xlYXIgPSBmdW5jdGlvbiAoKSB7XHJcbiAgICAgICAgdGhpcy5fcm9vdCA9IG51bGw7XHJcbiAgICAgICAgdGhpcy5zaXplID0gMDtcclxuICAgIH07XHJcbiAgICA7XHJcbiAgICBUcmVlQmFzZS5wcm90b3R5cGUuZmluZCA9IGZ1bmN0aW9uIChkYXRhKSB7XHJcbiAgICAgICAgdmFyIHJlcyA9IHRoaXMuX3Jvb3Q7XHJcbiAgICAgICAgd2hpbGUgKHJlcyAhPT0gbnVsbCkge1xyXG4gICAgICAgICAgICB2YXIgYyA9IHRoaXMuX2NvbXBhcmF0b3IoZGF0YSwgcmVzLmRhdGEpO1xyXG4gICAgICAgICAgICBpZiAoYyA9PT0gMCkge1xyXG4gICAgICAgICAgICAgICAgcmV0dXJuIHJlcy5kYXRhO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgICAgIGVsc2Uge1xyXG4gICAgICAgICAgICAgICAgcmVzID0gcmVzLmdldF9jaGlsZChjID4gMCk7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICB9XHJcbiAgICAgICAgcmV0dXJuIG51bGw7XHJcbiAgICB9O1xyXG4gICAgO1xyXG4gICAgVHJlZUJhc2UucHJvdG90eXBlLmxvd2VyQm91bmQgPSBmdW5jdGlvbiAoZGF0YSkge1xyXG4gICAgICAgIHJldHVybiB0aGlzLl9ib3VuZChkYXRhLCB0aGlzLl9jb21wYXJhdG9yKTtcclxuICAgIH07XHJcbiAgICA7XHJcbiAgICBUcmVlQmFzZS5wcm90b3R5cGUudXBwZXJCb3VuZCA9IGZ1bmN0aW9uIChkYXRhKSB7XHJcbiAgICAgICAgdmFyIGNtcCA9IHRoaXMuX2NvbXBhcmF0b3I7XHJcbiAgICAgICAgZnVuY3Rpb24gcmV2ZXJzZV9jbXAoYSwgYikge1xyXG4gICAgICAgICAgICByZXR1cm4gY21wKGIsIGEpO1xyXG4gICAgICAgIH1cclxuICAgICAgICByZXR1cm4gdGhpcy5fYm91bmQoZGF0YSwgcmV2ZXJzZV9jbXApO1xyXG4gICAgfTtcclxuICAgIDtcclxuICAgIFRyZWVCYXNlLnByb3RvdHlwZS5taW4gPSBmdW5jdGlvbiAoKSB7XHJcbiAgICAgICAgdmFyIHJlcyA9IHRoaXMuX3Jvb3Q7XHJcbiAgICAgICAgaWYgKHJlcyA9PT0gbnVsbCkge1xyXG4gICAgICAgICAgICByZXR1cm4gbnVsbDtcclxuICAgICAgICB9XHJcbiAgICAgICAgd2hpbGUgKHJlcy5sZWZ0ICE9PSBudWxsKSB7XHJcbiAgICAgICAgICAgIHJlcyA9IHJlcy5sZWZ0O1xyXG4gICAgICAgIH1cclxuICAgICAgICByZXR1cm4gcmVzLmRhdGE7XHJcbiAgICB9O1xyXG4gICAgO1xyXG4gICAgVHJlZUJhc2UucHJvdG90eXBlLm1heCA9IGZ1bmN0aW9uICgpIHtcclxuICAgICAgICB2YXIgcmVzID0gdGhpcy5fcm9vdDtcclxuICAgICAgICBpZiAocmVzID09PSBudWxsKSB7XHJcbiAgICAgICAgICAgIHJldHVybiBudWxsO1xyXG4gICAgICAgIH1cclxuICAgICAgICB3aGlsZSAocmVzLnJpZ2h0ICE9PSBudWxsKSB7XHJcbiAgICAgICAgICAgIHJlcyA9IHJlcy5yaWdodDtcclxuICAgICAgICB9XHJcbiAgICAgICAgcmV0dXJuIHJlcy5kYXRhO1xyXG4gICAgfTtcclxuICAgIDtcclxuICAgIFRyZWVCYXNlLnByb3RvdHlwZS5pdGVyYXRvciA9IGZ1bmN0aW9uICgpIHtcclxuICAgICAgICByZXR1cm4gbmV3IEl0ZXJhdG9yKHRoaXMpO1xyXG4gICAgfTtcclxuICAgIDtcclxuICAgIFRyZWVCYXNlLnByb3RvdHlwZS5lYWNoID0gZnVuY3Rpb24gKGNiKSB7XHJcbiAgICAgICAgdmFyIGl0ID0gdGhpcy5pdGVyYXRvcigpLCBkYXRhO1xyXG4gICAgICAgIHdoaWxlICgoZGF0YSA9IGl0Lm5leHQoKSkgIT09IG51bGwpIHtcclxuICAgICAgICAgICAgY2IoZGF0YSk7XHJcbiAgICAgICAgfVxyXG4gICAgfTtcclxuICAgIDtcclxuICAgIFRyZWVCYXNlLnByb3RvdHlwZS5yZWFjaCA9IGZ1bmN0aW9uIChjYikge1xyXG4gICAgICAgIHZhciBpdCA9IHRoaXMuaXRlcmF0b3IoKSwgZGF0YTtcclxuICAgICAgICB3aGlsZSAoKGRhdGEgPSBpdC5wcmV2KCkpICE9PSBudWxsKSB7XHJcbiAgICAgICAgICAgIGNiKGRhdGEpO1xyXG4gICAgICAgIH1cclxuICAgIH07XHJcbiAgICA7XHJcbiAgICBUcmVlQmFzZS5wcm90b3R5cGUuX2JvdW5kID0gZnVuY3Rpb24gKGRhdGEsIGNtcCkge1xyXG4gICAgICAgIHZhciBjdXIgPSB0aGlzLl9yb290O1xyXG4gICAgICAgIHZhciBpdGVyID0gdGhpcy5pdGVyYXRvcigpO1xyXG4gICAgICAgIHdoaWxlIChjdXIgIT09IG51bGwpIHtcclxuICAgICAgICAgICAgdmFyIGMgPSB0aGlzLl9jb21wYXJhdG9yKGRhdGEsIGN1ci5kYXRhKTtcclxuICAgICAgICAgICAgaWYgKGMgPT09IDApIHtcclxuICAgICAgICAgICAgICAgIGl0ZXIuX2N1cnNvciA9IGN1cjtcclxuICAgICAgICAgICAgICAgIHJldHVybiBpdGVyO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgICAgIGl0ZXIuX2FuY2VzdG9ycy5wdXNoKGN1cik7XHJcbiAgICAgICAgICAgIGN1ciA9IGN1ci5nZXRfY2hpbGQoYyA+IDApO1xyXG4gICAgICAgIH1cclxuICAgICAgICBmb3IgKHZhciBpID0gaXRlci5fYW5jZXN0b3JzLmxlbmd0aCAtIDE7IGkgPj0gMDsgLS1pKSB7XHJcbiAgICAgICAgICAgIGN1ciA9IGl0ZXIuX2FuY2VzdG9yc1tpXTtcclxuICAgICAgICAgICAgaWYgKGNtcChkYXRhLCBjdXIuZGF0YSkgPiAwKSB7XHJcbiAgICAgICAgICAgICAgICBpdGVyLl9jdXJzb3IgPSBjdXI7XHJcbiAgICAgICAgICAgICAgICBpdGVyLl9hbmNlc3RvcnMubGVuZ3RoID0gaTtcclxuICAgICAgICAgICAgICAgIHJldHVybiBpdGVyO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgfVxyXG4gICAgICAgIGl0ZXIuX2FuY2VzdG9ycy5sZW5ndGggPSAwO1xyXG4gICAgICAgIHJldHVybiBpdGVyO1xyXG4gICAgfTtcclxuICAgIDtcclxuICAgIHJldHVybiBUcmVlQmFzZTtcclxufSgpKTtcclxuZXhwb3J0cy5UcmVlQmFzZSA9IFRyZWVCYXNlO1xyXG52YXIgSXRlcmF0b3IgPSAoZnVuY3Rpb24gKCkge1xyXG4gICAgZnVuY3Rpb24gSXRlcmF0b3IodHJlZSkge1xyXG4gICAgICAgIHRoaXMuX3RyZWUgPSB0cmVlO1xyXG4gICAgICAgIHRoaXMuX2FuY2VzdG9ycyA9IFtdO1xyXG4gICAgICAgIHRoaXMuX2N1cnNvciA9IG51bGw7XHJcbiAgICB9XHJcbiAgICBJdGVyYXRvci5wcm90b3R5cGUuZGF0YSA9IGZ1bmN0aW9uICgpIHtcclxuICAgICAgICByZXR1cm4gdGhpcy5fY3Vyc29yICE9PSBudWxsID8gdGhpcy5fY3Vyc29yLmRhdGEgOiBudWxsO1xyXG4gICAgfTtcclxuICAgIDtcclxuICAgIEl0ZXJhdG9yLnByb3RvdHlwZS5uZXh0ID0gZnVuY3Rpb24gKCkge1xyXG4gICAgICAgIGlmICh0aGlzLl9jdXJzb3IgPT09IG51bGwpIHtcclxuICAgICAgICAgICAgdmFyIHJvb3QgPSB0aGlzLl90cmVlLl9yb290O1xyXG4gICAgICAgICAgICBpZiAocm9vdCAhPT0gbnVsbCkge1xyXG4gICAgICAgICAgICAgICAgdGhpcy5fbWluTm9kZShyb290KTtcclxuICAgICAgICAgICAgfVxyXG4gICAgICAgIH1cclxuICAgICAgICBlbHNlIHtcclxuICAgICAgICAgICAgaWYgKHRoaXMuX2N1cnNvci5yaWdodCA9PT0gbnVsbCkge1xyXG4gICAgICAgICAgICAgICAgdmFyIHNhdmU7XHJcbiAgICAgICAgICAgICAgICBkbyB7XHJcbiAgICAgICAgICAgICAgICAgICAgc2F2ZSA9IHRoaXMuX2N1cnNvcjtcclxuICAgICAgICAgICAgICAgICAgICBpZiAodGhpcy5fYW5jZXN0b3JzLmxlbmd0aCkge1xyXG4gICAgICAgICAgICAgICAgICAgICAgICB0aGlzLl9jdXJzb3IgPSB0aGlzLl9hbmNlc3RvcnMucG9wKCk7XHJcbiAgICAgICAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICAgICAgICAgIGVsc2Uge1xyXG4gICAgICAgICAgICAgICAgICAgICAgICB0aGlzLl9jdXJzb3IgPSBudWxsO1xyXG4gICAgICAgICAgICAgICAgICAgICAgICBicmVhaztcclxuICAgICAgICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgICAgICB9IHdoaWxlICh0aGlzLl9jdXJzb3IucmlnaHQgPT09IHNhdmUpO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgICAgIGVsc2Uge1xyXG4gICAgICAgICAgICAgICAgdGhpcy5fYW5jZXN0b3JzLnB1c2godGhpcy5fY3Vyc29yKTtcclxuICAgICAgICAgICAgICAgIHRoaXMuX21pbk5vZGUodGhpcy5fY3Vyc29yLnJpZ2h0KTtcclxuICAgICAgICAgICAgfVxyXG4gICAgICAgIH1cclxuICAgICAgICByZXR1cm4gdGhpcy5fY3Vyc29yICE9PSBudWxsID8gdGhpcy5fY3Vyc29yLmRhdGEgOiBudWxsO1xyXG4gICAgfTtcclxuICAgIDtcclxuICAgIEl0ZXJhdG9yLnByb3RvdHlwZS5wcmV2ID0gZnVuY3Rpb24gKCkge1xyXG4gICAgICAgIGlmICh0aGlzLl9jdXJzb3IgPT09IG51bGwpIHtcclxuICAgICAgICAgICAgdmFyIHJvb3QgPSB0aGlzLl90cmVlLl9yb290O1xyXG4gICAgICAgICAgICBpZiAocm9vdCAhPT0gbnVsbCkge1xyXG4gICAgICAgICAgICAgICAgdGhpcy5fbWF4Tm9kZShyb290KTtcclxuICAgICAgICAgICAgfVxyXG4gICAgICAgIH1cclxuICAgICAgICBlbHNlIHtcclxuICAgICAgICAgICAgaWYgKHRoaXMuX2N1cnNvci5sZWZ0ID09PSBudWxsKSB7XHJcbiAgICAgICAgICAgICAgICB2YXIgc2F2ZTtcclxuICAgICAgICAgICAgICAgIGRvIHtcclxuICAgICAgICAgICAgICAgICAgICBzYXZlID0gdGhpcy5fY3Vyc29yO1xyXG4gICAgICAgICAgICAgICAgICAgIGlmICh0aGlzLl9hbmNlc3RvcnMubGVuZ3RoKSB7XHJcbiAgICAgICAgICAgICAgICAgICAgICAgIHRoaXMuX2N1cnNvciA9IHRoaXMuX2FuY2VzdG9ycy5wb3AoKTtcclxuICAgICAgICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgICAgICAgICAgZWxzZSB7XHJcbiAgICAgICAgICAgICAgICAgICAgICAgIHRoaXMuX2N1cnNvciA9IG51bGw7XHJcbiAgICAgICAgICAgICAgICAgICAgICAgIGJyZWFrO1xyXG4gICAgICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgIH0gd2hpbGUgKHRoaXMuX2N1cnNvci5sZWZ0ID09PSBzYXZlKTtcclxuICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICBlbHNlIHtcclxuICAgICAgICAgICAgICAgIHRoaXMuX2FuY2VzdG9ycy5wdXNoKHRoaXMuX2N1cnNvcik7XHJcbiAgICAgICAgICAgICAgICB0aGlzLl9tYXhOb2RlKHRoaXMuX2N1cnNvci5sZWZ0KTtcclxuICAgICAgICAgICAgfVxyXG4gICAgICAgIH1cclxuICAgICAgICByZXR1cm4gdGhpcy5fY3Vyc29yICE9PSBudWxsID8gdGhpcy5fY3Vyc29yLmRhdGEgOiBudWxsO1xyXG4gICAgfTtcclxuICAgIDtcclxuICAgIEl0ZXJhdG9yLnByb3RvdHlwZS5fbWluTm9kZSA9IGZ1bmN0aW9uIChzdGFydCkge1xyXG4gICAgICAgIHdoaWxlIChzdGFydC5sZWZ0ICE9PSBudWxsKSB7XHJcbiAgICAgICAgICAgIHRoaXMuX2FuY2VzdG9ycy5wdXNoKHN0YXJ0KTtcclxuICAgICAgICAgICAgc3RhcnQgPSBzdGFydC5sZWZ0O1xyXG4gICAgICAgIH1cclxuICAgICAgICB0aGlzLl9jdXJzb3IgPSBzdGFydDtcclxuICAgIH07XHJcbiAgICA7XHJcbiAgICBJdGVyYXRvci5wcm90b3R5cGUuX21heE5vZGUgPSBmdW5jdGlvbiAoc3RhcnQpIHtcclxuICAgICAgICB3aGlsZSAoc3RhcnQucmlnaHQgIT09IG51bGwpIHtcclxuICAgICAgICAgICAgdGhpcy5fYW5jZXN0b3JzLnB1c2goc3RhcnQpO1xyXG4gICAgICAgICAgICBzdGFydCA9IHN0YXJ0LnJpZ2h0O1xyXG4gICAgICAgIH1cclxuICAgICAgICB0aGlzLl9jdXJzb3IgPSBzdGFydDtcclxuICAgIH07XHJcbiAgICA7XHJcbiAgICByZXR1cm4gSXRlcmF0b3I7XHJcbn0oKSk7XHJcbmV4cG9ydHMuSXRlcmF0b3IgPSBJdGVyYXRvcjtcclxudmFyIE5vZGUgPSAoZnVuY3Rpb24gKCkge1xyXG4gICAgZnVuY3Rpb24gTm9kZShkYXRhKSB7XHJcbiAgICAgICAgdGhpcy5kYXRhID0gZGF0YTtcclxuICAgICAgICB0aGlzLmxlZnQgPSBudWxsO1xyXG4gICAgICAgIHRoaXMucmlnaHQgPSBudWxsO1xyXG4gICAgICAgIHRoaXMucmVkID0gdHJ1ZTtcclxuICAgIH1cclxuICAgIE5vZGUucHJvdG90eXBlLmdldF9jaGlsZCA9IGZ1bmN0aW9uIChkaXIpIHtcclxuICAgICAgICByZXR1cm4gZGlyID8gdGhpcy5yaWdodCA6IHRoaXMubGVmdDtcclxuICAgIH07XHJcbiAgICA7XHJcbiAgICBOb2RlLnByb3RvdHlwZS5zZXRfY2hpbGQgPSBmdW5jdGlvbiAoZGlyLCB2YWwpIHtcclxuICAgICAgICBpZiAoZGlyKSB7XHJcbiAgICAgICAgICAgIHRoaXMucmlnaHQgPSB2YWw7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIGVsc2Uge1xyXG4gICAgICAgICAgICB0aGlzLmxlZnQgPSB2YWw7XHJcbiAgICAgICAgfVxyXG4gICAgfTtcclxuICAgIDtcclxuICAgIHJldHVybiBOb2RlO1xyXG59KCkpO1xyXG52YXIgUkJUcmVlID0gKGZ1bmN0aW9uIChfc3VwZXIpIHtcclxuICAgIF9fZXh0ZW5kcyhSQlRyZWUsIF9zdXBlcik7XHJcbiAgICBmdW5jdGlvbiBSQlRyZWUoY29tcGFyYXRvcikge1xyXG4gICAgICAgIHZhciBfdGhpcyA9IF9zdXBlci5jYWxsKHRoaXMpIHx8IHRoaXM7XHJcbiAgICAgICAgX3RoaXMuX3Jvb3QgPSBudWxsO1xyXG4gICAgICAgIF90aGlzLl9jb21wYXJhdG9yID0gY29tcGFyYXRvcjtcclxuICAgICAgICBfdGhpcy5zaXplID0gMDtcclxuICAgICAgICByZXR1cm4gX3RoaXM7XHJcbiAgICB9XHJcbiAgICBSQlRyZWUucHJvdG90eXBlLmluc2VydCA9IGZ1bmN0aW9uIChkYXRhKSB7XHJcbiAgICAgICAgdmFyIHJldCA9IGZhbHNlO1xyXG4gICAgICAgIGlmICh0aGlzLl9yb290ID09PSBudWxsKSB7XHJcbiAgICAgICAgICAgIHRoaXMuX3Jvb3QgPSBuZXcgTm9kZShkYXRhKTtcclxuICAgICAgICAgICAgcmV0ID0gdHJ1ZTtcclxuICAgICAgICAgICAgdGhpcy5zaXplKys7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIGVsc2Uge1xyXG4gICAgICAgICAgICB2YXIgaGVhZCA9IG5ldyBOb2RlKHVuZGVmaW5lZCk7XHJcbiAgICAgICAgICAgIHZhciBkaXIgPSBmYWxzZTtcclxuICAgICAgICAgICAgdmFyIGxhc3QgPSBmYWxzZTtcclxuICAgICAgICAgICAgdmFyIGdwID0gbnVsbDtcclxuICAgICAgICAgICAgdmFyIGdncCA9IGhlYWQ7XHJcbiAgICAgICAgICAgIHZhciBwID0gbnVsbDtcclxuICAgICAgICAgICAgdmFyIG5vZGUgPSB0aGlzLl9yb290O1xyXG4gICAgICAgICAgICBnZ3AucmlnaHQgPSB0aGlzLl9yb290O1xyXG4gICAgICAgICAgICB3aGlsZSAodHJ1ZSkge1xyXG4gICAgICAgICAgICAgICAgaWYgKG5vZGUgPT09IG51bGwpIHtcclxuICAgICAgICAgICAgICAgICAgICBub2RlID0gbmV3IE5vZGUoZGF0YSk7XHJcbiAgICAgICAgICAgICAgICAgICAgcC5zZXRfY2hpbGQoZGlyLCBub2RlKTtcclxuICAgICAgICAgICAgICAgICAgICByZXQgPSB0cnVlO1xyXG4gICAgICAgICAgICAgICAgICAgIHRoaXMuc2l6ZSsrO1xyXG4gICAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICAgICAgZWxzZSBpZiAoUkJUcmVlLmlzX3JlZChub2RlLmxlZnQpICYmIFJCVHJlZS5pc19yZWQobm9kZS5yaWdodCkpIHtcclxuICAgICAgICAgICAgICAgICAgICBub2RlLnJlZCA9IHRydWU7XHJcbiAgICAgICAgICAgICAgICAgICAgbm9kZS5sZWZ0LnJlZCA9IGZhbHNlO1xyXG4gICAgICAgICAgICAgICAgICAgIG5vZGUucmlnaHQucmVkID0gZmFsc2U7XHJcbiAgICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgICAgICBpZiAoUkJUcmVlLmlzX3JlZChub2RlKSAmJiBSQlRyZWUuaXNfcmVkKHApKSB7XHJcbiAgICAgICAgICAgICAgICAgICAgdmFyIGRpcjIgPSBnZ3AucmlnaHQgPT09IGdwO1xyXG4gICAgICAgICAgICAgICAgICAgIGlmIChub2RlID09PSBwLmdldF9jaGlsZChsYXN0KSkge1xyXG4gICAgICAgICAgICAgICAgICAgICAgICBnZ3Auc2V0X2NoaWxkKGRpcjIsIFJCVHJlZS5zaW5nbGVfcm90YXRlKGdwLCAhbGFzdCkpO1xyXG4gICAgICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgICAgICBlbHNlIHtcclxuICAgICAgICAgICAgICAgICAgICAgICAgZ2dwLnNldF9jaGlsZChkaXIyLCBSQlRyZWUuZG91YmxlX3JvdGF0ZShncCwgIWxhc3QpKTtcclxuICAgICAgICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgICAgICB2YXIgY21wID0gdGhpcy5fY29tcGFyYXRvcihub2RlLmRhdGEsIGRhdGEpO1xyXG4gICAgICAgICAgICAgICAgaWYgKGNtcCA9PT0gMCkge1xyXG4gICAgICAgICAgICAgICAgICAgIGJyZWFrO1xyXG4gICAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICAgICAgbGFzdCA9IGRpcjtcclxuICAgICAgICAgICAgICAgIGRpciA9IGNtcCA8IDA7XHJcbiAgICAgICAgICAgICAgICBpZiAoZ3AgIT09IG51bGwpIHtcclxuICAgICAgICAgICAgICAgICAgICBnZ3AgPSBncDtcclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgIGdwID0gcDtcclxuICAgICAgICAgICAgICAgIHAgPSBub2RlO1xyXG4gICAgICAgICAgICAgICAgbm9kZSA9IG5vZGUuZ2V0X2NoaWxkKGRpcik7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgdGhpcy5fcm9vdCA9IGhlYWQucmlnaHQ7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIHRoaXMuX3Jvb3QucmVkID0gZmFsc2U7XHJcbiAgICAgICAgcmV0dXJuIHJldDtcclxuICAgIH07XHJcbiAgICA7XHJcbiAgICBSQlRyZWUucHJvdG90eXBlLnJlbW92ZSA9IGZ1bmN0aW9uIChkYXRhKSB7XHJcbiAgICAgICAgaWYgKHRoaXMuX3Jvb3QgPT09IG51bGwpIHtcclxuICAgICAgICAgICAgcmV0dXJuIGZhbHNlO1xyXG4gICAgICAgIH1cclxuICAgICAgICB2YXIgaGVhZCA9IG5ldyBOb2RlKHVuZGVmaW5lZCk7XHJcbiAgICAgICAgdmFyIG5vZGUgPSBoZWFkO1xyXG4gICAgICAgIG5vZGUucmlnaHQgPSB0aGlzLl9yb290O1xyXG4gICAgICAgIHZhciBwID0gbnVsbDtcclxuICAgICAgICB2YXIgZ3AgPSBudWxsO1xyXG4gICAgICAgIHZhciBmb3VuZCA9IG51bGw7XHJcbiAgICAgICAgdmFyIGRpciA9IHRydWU7XHJcbiAgICAgICAgd2hpbGUgKG5vZGUuZ2V0X2NoaWxkKGRpcikgIT09IG51bGwpIHtcclxuICAgICAgICAgICAgdmFyIGxhc3QgPSBkaXI7XHJcbiAgICAgICAgICAgIGdwID0gcDtcclxuICAgICAgICAgICAgcCA9IG5vZGU7XHJcbiAgICAgICAgICAgIG5vZGUgPSBub2RlLmdldF9jaGlsZChkaXIpO1xyXG4gICAgICAgICAgICB2YXIgY21wID0gdGhpcy5fY29tcGFyYXRvcihkYXRhLCBub2RlLmRhdGEpO1xyXG4gICAgICAgICAgICBkaXIgPSBjbXAgPiAwO1xyXG4gICAgICAgICAgICBpZiAoY21wID09PSAwKSB7XHJcbiAgICAgICAgICAgICAgICBmb3VuZCA9IG5vZGU7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgaWYgKCFSQlRyZWUuaXNfcmVkKG5vZGUpICYmICFSQlRyZWUuaXNfcmVkKG5vZGUuZ2V0X2NoaWxkKGRpcikpKSB7XHJcbiAgICAgICAgICAgICAgICBpZiAoUkJUcmVlLmlzX3JlZChub2RlLmdldF9jaGlsZCghZGlyKSkpIHtcclxuICAgICAgICAgICAgICAgICAgICB2YXIgc3IgPSBSQlRyZWUuc2luZ2xlX3JvdGF0ZShub2RlLCBkaXIpO1xyXG4gICAgICAgICAgICAgICAgICAgIHAuc2V0X2NoaWxkKGxhc3QsIHNyKTtcclxuICAgICAgICAgICAgICAgICAgICBwID0gc3I7XHJcbiAgICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgICAgICBlbHNlIGlmICghUkJUcmVlLmlzX3JlZChub2RlLmdldF9jaGlsZCghZGlyKSkpIHtcclxuICAgICAgICAgICAgICAgICAgICB2YXIgc2libGluZyA9IHAuZ2V0X2NoaWxkKCFsYXN0KTtcclxuICAgICAgICAgICAgICAgICAgICBpZiAoc2libGluZyAhPT0gbnVsbCkge1xyXG4gICAgICAgICAgICAgICAgICAgICAgICBpZiAoIVJCVHJlZS5pc19yZWQoc2libGluZy5nZXRfY2hpbGQoIWxhc3QpKSAmJiAhUkJUcmVlLmlzX3JlZChzaWJsaW5nLmdldF9jaGlsZChsYXN0KSkpIHtcclxuICAgICAgICAgICAgICAgICAgICAgICAgICAgIHAucmVkID0gZmFsc2U7XHJcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICBzaWJsaW5nLnJlZCA9IHRydWU7XHJcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICBub2RlLnJlZCA9IHRydWU7XHJcbiAgICAgICAgICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgICAgICAgICAgZWxzZSB7XHJcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICB2YXIgZGlyMiA9IGdwLnJpZ2h0ID09PSBwO1xyXG4gICAgICAgICAgICAgICAgICAgICAgICAgICAgaWYgKFJCVHJlZS5pc19yZWQoc2libGluZy5nZXRfY2hpbGQobGFzdCkpKSB7XHJcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgZ3Auc2V0X2NoaWxkKGRpcjIsIFJCVHJlZS5kb3VibGVfcm90YXRlKHAsIGxhc3QpKTtcclxuICAgICAgICAgICAgICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgICAgICAgICAgICAgIGVsc2UgaWYgKFJCVHJlZS5pc19yZWQoc2libGluZy5nZXRfY2hpbGQoIWxhc3QpKSkge1xyXG4gICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIGdwLnNldF9jaGlsZChkaXIyLCBSQlRyZWUuc2luZ2xlX3JvdGF0ZShwLCBsYXN0KSk7XHJcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICB2YXIgZ3BjID0gZ3AuZ2V0X2NoaWxkKGRpcjIpO1xyXG4gICAgICAgICAgICAgICAgICAgICAgICAgICAgZ3BjLnJlZCA9IHRydWU7XHJcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICBub2RlLnJlZCA9IHRydWU7XHJcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICBncGMubGVmdC5yZWQgPSBmYWxzZTtcclxuICAgICAgICAgICAgICAgICAgICAgICAgICAgIGdwYy5yaWdodC5yZWQgPSBmYWxzZTtcclxuICAgICAgICAgICAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgfVxyXG4gICAgICAgIH1cclxuICAgICAgICBpZiAoZm91bmQgIT09IG51bGwpIHtcclxuICAgICAgICAgICAgZm91bmQuZGF0YSA9IG5vZGUuZGF0YTtcclxuICAgICAgICAgICAgcC5zZXRfY2hpbGQocC5yaWdodCA9PT0gbm9kZSwgbm9kZS5nZXRfY2hpbGQobm9kZS5sZWZ0ID09PSBudWxsKSk7XHJcbiAgICAgICAgICAgIHRoaXMuc2l6ZS0tO1xyXG4gICAgICAgIH1cclxuICAgICAgICB0aGlzLl9yb290ID0gaGVhZC5yaWdodDtcclxuICAgICAgICBpZiAodGhpcy5fcm9vdCAhPT0gbnVsbCkge1xyXG4gICAgICAgICAgICB0aGlzLl9yb290LnJlZCA9IGZhbHNlO1xyXG4gICAgICAgIH1cclxuICAgICAgICByZXR1cm4gZm91bmQgIT09IG51bGw7XHJcbiAgICB9O1xyXG4gICAgO1xyXG4gICAgUkJUcmVlLmlzX3JlZCA9IGZ1bmN0aW9uIChub2RlKSB7XHJcbiAgICAgICAgcmV0dXJuIG5vZGUgIT09IG51bGwgJiYgbm9kZS5yZWQ7XHJcbiAgICB9O1xyXG4gICAgUkJUcmVlLnNpbmdsZV9yb3RhdGUgPSBmdW5jdGlvbiAocm9vdCwgZGlyKSB7XHJcbiAgICAgICAgdmFyIHNhdmUgPSByb290LmdldF9jaGlsZCghZGlyKTtcclxuICAgICAgICByb290LnNldF9jaGlsZCghZGlyLCBzYXZlLmdldF9jaGlsZChkaXIpKTtcclxuICAgICAgICBzYXZlLnNldF9jaGlsZChkaXIsIHJvb3QpO1xyXG4gICAgICAgIHJvb3QucmVkID0gdHJ1ZTtcclxuICAgICAgICBzYXZlLnJlZCA9IGZhbHNlO1xyXG4gICAgICAgIHJldHVybiBzYXZlO1xyXG4gICAgfTtcclxuICAgIFJCVHJlZS5kb3VibGVfcm90YXRlID0gZnVuY3Rpb24gKHJvb3QsIGRpcikge1xyXG4gICAgICAgIHJvb3Quc2V0X2NoaWxkKCFkaXIsIFJCVHJlZS5zaW5nbGVfcm90YXRlKHJvb3QuZ2V0X2NoaWxkKCFkaXIpLCAhZGlyKSk7XHJcbiAgICAgICAgcmV0dXJuIFJCVHJlZS5zaW5nbGVfcm90YXRlKHJvb3QsIGRpcik7XHJcbiAgICB9O1xyXG4gICAgcmV0dXJuIFJCVHJlZTtcclxufShUcmVlQmFzZSkpO1xyXG5leHBvcnRzLlJCVHJlZSA9IFJCVHJlZTtcclxuLy8jIHNvdXJjZU1hcHBpbmdVUkw9ZGF0YTphcHBsaWNhdGlvbi9qc29uO2Jhc2U2NCxleUoyWlhKemFXOXVJam96TENKbWFXeGxJam9pY21KMGNtVmxMbXB6SWl3aWMyOTFjbU5sVW05dmRDSTZJaUlzSW5OdmRYSmpaWE1pT2xzaUxpNHZMaTR2VjJWaVEyOXNZUzl6Y21NdmNtSjBjbVZsTG5SeklsMHNJbTVoYldWeklqcGJYU3dpYldGd2NHbHVaM01pT2lJN096czdPenM3T3pzN096czdPenRCUVhWQ1NUdEpRVUZCTzFGQk5FSkpMR0ZCUVZFc1IwRkJSeXhWUVVGVkxFbEJRVWs3V1VGRGNrSXNTVUZCU1N4SFFVRkhMRWRCUVVjc1NVRkJTU3hEUVVGRExFdEJRVXNzUTBGQlF6dFpRVU55UWl4SlFVRkpMRWxCUVVrc1IwRkJSeXhKUVVGSkxFTkJRVU1zVVVGQlVTeEZRVUZGTEVOQlFVTTdXVUZGTTBJc1QwRkJUeXhIUVVGSExFdEJRVXNzU1VGQlNTeEZRVUZGTzJkQ1FVTnFRaXhKUVVGSkxFTkJRVU1zUjBGQlJ5eEpRVUZKTEVOQlFVTXNWMEZCVnl4RFFVRkRMRWxCUVVrc1JVRkJSU3hIUVVGSExFTkJRVU1zU1VGQlNTeERRVUZETEVOQlFVTTdaMEpCUTNwRExFbEJRVWtzUTBGQlF5eExRVUZMTEVOQlFVTXNSVUZCUlR0dlFrRkRWQ3hKUVVGSkxFTkJRVU1zVDBGQlR5eEhRVUZITEVkQlFVY3NRMEZCUXp0dlFrRkRia0lzVDBGQlR5eEpRVUZKTEVOQlFVTTdhVUpCUTJZN2NVSkJRMGs3YjBKQlEwUXNTVUZCU1N4RFFVRkRMRlZCUVZVc1EwRkJReXhKUVVGSkxFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTTdiMEpCUXpGQ0xFZEJRVWNzUjBGQlJ5eEhRVUZITEVOQlFVTXNVMEZCVXl4RFFVRkRMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF6dHBRa0ZET1VJN1lVRkRTanRaUVVWRUxFOUJRVThzU1VGQlNTeERRVUZETzFGQlEyaENMRU5CUVVNc1EwRkJRenRKUVN0R1RpeERRVUZETzBsQmRrbEhMSGRDUVVGTExFZEJRVXc3VVVGRFNTeEpRVUZKTEVOQlFVTXNTMEZCU3l4SFFVRkhMRWxCUVVrc1EwRkJRenRSUVVOc1FpeEpRVUZKTEVOQlFVTXNTVUZCU1N4SFFVRkhMRU5CUVVNc1EwRkJRenRKUVVOc1FpeERRVUZETzBsQlFVRXNRMEZCUXp0SlFVZEdMSFZDUVVGSkxFZEJRVW9zVlVGQlN5eEpRVUZKTzFGQlEwd3NTVUZCU1N4SFFVRkhMRWRCUVVjc1NVRkJTU3hEUVVGRExFdEJRVXNzUTBGQlF6dFJRVVZ5UWl4UFFVRlBMRWRCUVVjc1MwRkJTeXhKUVVGSkxFVkJRVVU3V1VGRGFrSXNTVUZCU1N4RFFVRkRMRWRCUVVjc1NVRkJTU3hEUVVGRExGZEJRVmNzUTBGQlF5eEpRVUZKTEVWQlFVVXNSMEZCUnl4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRE8xbEJRM3BETEVsQlFVa3NRMEZCUXl4TFFVRkxMRU5CUVVNc1JVRkJSVHRuUWtGRFZDeFBRVUZQTEVkQlFVY3NRMEZCUXl4SlFVRkpMRU5CUVVNN1lVRkRia0k3YVVKQlEwazdaMEpCUTBRc1IwRkJSeXhIUVVGSExFZEJRVWNzUTBGQlF5eFRRVUZUTEVOQlFVTXNRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJReXhEUVVGRE8yRkJRemxDTzFOQlEwbzdVVUZGUkN4UFFVRlBMRWxCUVVrc1EwRkJRenRKUVVOb1FpeERRVUZETzBsQlFVRXNRMEZCUXp0SlFYVkNSaXcyUWtGQlZTeEhRVUZXTEZWQlFWY3NTVUZCU1R0UlFVTllMRTlCUVU4c1NVRkJTU3hEUVVGRExFMUJRVTBzUTBGQlF5eEpRVUZKTEVWQlFVVXNTVUZCU1N4RFFVRkRMRmRCUVZjc1EwRkJReXhEUVVGRE8wbEJReTlETEVOQlFVTTdTVUZCUVN4RFFVRkRPMGxCUjBZc05rSkJRVlVzUjBGQlZpeFZRVUZYTEVsQlFVazdVVUZEV0N4SlFVRkpMRWRCUVVjc1IwRkJSeXhKUVVGSkxFTkJRVU1zVjBGQlZ5eERRVUZETzFGQlJUTkNMRk5CUVZNc1YwRkJWeXhEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETzFsQlEzSkNMRTlCUVU4c1IwRkJSeXhEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTXNRMEZCUXp0UlFVTnlRaXhEUVVGRE8xRkJSVVFzVDBGQlR5eEpRVUZKTEVOQlFVTXNUVUZCVFN4RFFVRkRMRWxCUVVrc1JVRkJSU3hYUVVGWExFTkJRVU1zUTBGQlF6dEpRVU14UXl4RFFVRkRPMGxCUVVFc1EwRkJRenRKUVVkR0xITkNRVUZITEVkQlFVZzdVVUZEU1N4SlFVRkpMRWRCUVVjc1IwRkJSeXhKUVVGSkxFTkJRVU1zUzBGQlN5eERRVUZETzFGQlEzSkNMRWxCUVVrc1IwRkJSeXhMUVVGTExFbEJRVWtzUlVGQlJUdFpRVU5rTEU5QlFVOHNTVUZCU1N4RFFVRkRPMU5CUTJZN1VVRkZSQ3hQUVVGUExFZEJRVWNzUTBGQlF5eEpRVUZKTEV0QlFVc3NTVUZCU1N4RlFVRkZPMWxCUTNSQ0xFZEJRVWNzUjBGQlJ5eEhRVUZITEVOQlFVTXNTVUZCU1N4RFFVRkRPMU5CUTJ4Q08xRkJSVVFzVDBGQlR5eEhRVUZITEVOQlFVTXNTVUZCU1N4RFFVRkRPMGxCUTNCQ0xFTkJRVU03U1VGQlFTeERRVUZETzBsQlIwWXNjMEpCUVVjc1IwRkJTRHRSUVVOSkxFbEJRVWtzUjBGQlJ5eEhRVUZITEVsQlFVa3NRMEZCUXl4TFFVRkxMRU5CUVVNN1VVRkRja0lzU1VGQlNTeEhRVUZITEV0QlFVc3NTVUZCU1N4RlFVRkZPMWxCUTJRc1QwRkJUeXhKUVVGSkxFTkJRVU03VTBGRFpqdFJRVVZFTEU5QlFVOHNSMEZCUnl4RFFVRkRMRXRCUVVzc1MwRkJTeXhKUVVGSkxFVkJRVVU3V1VGRGRrSXNSMEZCUnl4SFFVRkhMRWRCUVVjc1EwRkJReXhMUVVGTExFTkJRVU03VTBGRGJrSTdVVUZGUkN4UFFVRlBMRWRCUVVjc1EwRkJReXhKUVVGSkxFTkJRVU03U1VGRGNFSXNRMEZCUXp0SlFVRkJMRU5CUVVNN1NVRkpSaXd5UWtGQlVTeEhRVUZTTzFGQlEwa3NUMEZCVHl4SlFVRkpMRkZCUVZFc1EwRkJReXhKUVVGSkxFTkJRVU1zUTBGQlF6dEpRVU01UWl4RFFVRkRPMGxCUVVFc1EwRkJRenRKUVVkR0xIVkNRVUZKTEVkQlFVb3NWVUZCU3l4RlFVRkZPMUZCUTBnc1NVRkJTU3hGUVVGRkxFZEJRVWNzU1VGQlNTeERRVUZETEZGQlFWRXNSVUZCUlN4RlFVRkZMRWxCUVVrc1EwRkJRenRSUVVNdlFpeFBRVUZQTEVOQlFVTXNTVUZCU1N4SFFVRkhMRVZCUVVVc1EwRkJReXhKUVVGSkxFVkJRVVVzUTBGQlF5eExRVUZMTEVsQlFVa3NSVUZCUlR0WlFVTm9ReXhGUVVGRkxFTkJRVU1zU1VGQlNTeERRVUZETEVOQlFVTTdVMEZEV2p0SlFVTk1MRU5CUVVNN1NVRkJRU3hEUVVGRE8wbEJSMFlzZDBKQlFVc3NSMEZCVEN4VlFVRk5MRVZCUVVVN1VVRkRTaXhKUVVGSkxFVkJRVVVzUjBGQlJ5eEpRVUZKTEVOQlFVTXNVVUZCVVN4RlFVRkZMRVZCUVVVc1NVRkJTU3hEUVVGRE8xRkJReTlDTEU5QlFVOHNRMEZCUXl4SlFVRkpMRWRCUVVjc1JVRkJSU3hEUVVGRExFbEJRVWtzUlVGQlJTeERRVUZETEV0QlFVc3NTVUZCU1N4RlFVRkZPMWxCUTJoRExFVkJRVVVzUTBGQlF5eEpRVUZKTEVOQlFVTXNRMEZCUXp0VFFVTmFPMGxCUTB3c1EwRkJRenRKUVVGQkxFTkJRVU03U1VGSFJpeDVRa0ZCVFN4SFFVRk9MRlZCUVU4c1NVRkJTU3hGUVVGRkxFZEJRVWM3VVVGRFdpeEpRVUZKTEVkQlFVY3NSMEZCUnl4SlFVRkpMRU5CUVVNc1MwRkJTeXhEUVVGRE8xRkJRM0pDTEVsQlFVa3NTVUZCU1N4SFFVRkhMRWxCUVVrc1EwRkJReXhSUVVGUkxFVkJRVVVzUTBGQlF6dFJRVVV6UWl4UFFVRlBMRWRCUVVjc1MwRkJTeXhKUVVGSkxFVkJRVVU3V1VGRGFrSXNTVUZCU1N4RFFVRkRMRWRCUVVjc1NVRkJTU3hEUVVGRExGZEJRVmNzUTBGQlF5eEpRVUZKTEVWQlFVVXNSMEZCUnl4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRE8xbEJRM3BETEVsQlFVa3NRMEZCUXl4TFFVRkxMRU5CUVVNc1JVRkJSVHRuUWtGRFZDeEpRVUZKTEVOQlFVTXNUMEZCVHl4SFFVRkhMRWRCUVVjc1EwRkJRenRuUWtGRGJrSXNUMEZCVHl4SlFVRkpMRU5CUVVNN1lVRkRaanRaUVVORUxFbEJRVWtzUTBGQlF5eFZRVUZWTEVOQlFVTXNTVUZCU1N4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRE8xbEJRekZDTEVkQlFVY3NSMEZCUnl4SFFVRkhMRU5CUVVNc1UwRkJVeXhEUVVGRExFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNRMEZCUXp0VFFVTTVRanRSUVVWRUxFdEJRVXNzU1VGQlNTeERRVUZETEVkQlFVY3NTVUZCU1N4RFFVRkRMRlZCUVZVc1EwRkJReXhOUVVGTkxFZEJRVWNzUTBGQlF5eEZRVUZGTEVOQlFVTXNTVUZCU1N4RFFVRkRMRVZCUVVVc1JVRkJSU3hEUVVGRExFVkJRVVU3V1VGRGJFUXNSMEZCUnl4SFFVRkhMRWxCUVVrc1EwRkJReXhWUVVGVkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdXVUZEZWtJc1NVRkJTU3hIUVVGSExFTkJRVU1zU1VGQlNTeEZRVUZGTEVkQlFVY3NRMEZCUXl4SlFVRkpMRU5CUVVNc1IwRkJSeXhEUVVGRExFVkJRVVU3WjBKQlEzcENMRWxCUVVrc1EwRkJReXhQUVVGUExFZEJRVWNzUjBGQlJ5eERRVUZETzJkQ1FVTnVRaXhKUVVGSkxFTkJRVU1zVlVGQlZTeERRVUZETEUxQlFVMHNSMEZCUnl4RFFVRkRMRU5CUVVNN1owSkJRek5DTEU5QlFVOHNTVUZCU1N4RFFVRkRPMkZCUTJZN1UwRkRTanRSUVVWRUxFbEJRVWtzUTBGQlF5eFZRVUZWTEVOQlFVTXNUVUZCVFN4SFFVRkhMRU5CUVVNc1EwRkJRenRSUVVNelFpeFBRVUZQTEVsQlFVa3NRMEZCUXp0SlFVTm9RaXhEUVVGRE8wbEJRVUVzUTBGQlF6dEpRVU5PTEdWQlFVTTdRVUZCUkN4RFFVRkRMRUZCTlVsRUxFbEJORWxETzBGQk5VbFpMRFJDUVVGUk8wRkJOa2x5UWp0SlFVbEpMR3RDUVVGWkxFbEJRVWs3VVVGRFdpeEpRVUZKTEVOQlFVTXNTMEZCU3l4SFFVRkhMRWxCUVVrc1EwRkJRenRSUVVOc1FpeEpRVUZKTEVOQlFVTXNWVUZCVlN4SFFVRkhMRVZCUVVVc1EwRkJRenRSUVVOeVFpeEpRVUZKTEVOQlFVTXNUMEZCVHl4SFFVRkhMRWxCUVVrc1EwRkJRenRKUVVONFFpeERRVUZETzBsQlJVUXNkVUpCUVVrc1IwRkJTanRSUVVOSkxFOUJRVThzU1VGQlNTeERRVUZETEU5QlFVOHNTMEZCU3l4SlFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRExFbEJRVWtzUTBGQlF5eFBRVUZQTEVOQlFVTXNTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJReXhKUVVGSkxFTkJRVU03U1VGRE5VUXNRMEZCUXp0SlFVRkJMRU5CUVVNN1NVRkpSaXgxUWtGQlNTeEhRVUZLTzFGQlEwa3NTVUZCU1N4SlFVRkpMRU5CUVVNc1QwRkJUeXhMUVVGTExFbEJRVWtzUlVGQlJUdFpRVU4yUWl4SlFVRkpMRWxCUVVrc1IwRkJSeXhKUVVGSkxFTkJRVU1zUzBGQlN5eERRVUZETEV0QlFVc3NRMEZCUXp0WlFVTTFRaXhKUVVGSkxFbEJRVWtzUzBGQlN5eEpRVUZKTEVWQlFVVTdaMEpCUTJZc1NVRkJTU3hEUVVGRExGRkJRVkVzUTBGQlF5eEpRVUZKTEVOQlFVTXNRMEZCUXp0aFFVTjJRanRUUVVOS08yRkJRMGs3V1VGRFJDeEpRVUZKTEVsQlFVa3NRMEZCUXl4UFFVRlBMRU5CUVVNc1MwRkJTeXhMUVVGTExFbEJRVWtzUlVGQlJUdG5Ra0ZITjBJc1NVRkJTU3hKUVVGSkxFTkJRVU03WjBKQlExUXNSMEZCUnp0dlFrRkRReXhKUVVGSkxFZEJRVWNzU1VGQlNTeERRVUZETEU5QlFVOHNRMEZCUXp0dlFrRkRjRUlzU1VGQlNTeEpRVUZKTEVOQlFVTXNWVUZCVlN4RFFVRkRMRTFCUVUwc1JVRkJSVHQzUWtGRGVFSXNTVUZCU1N4RFFVRkRMRTlCUVU4c1IwRkJSeXhKUVVGSkxFTkJRVU1zVlVGQlZTeERRVUZETEVkQlFVY3NSVUZCUlN4RFFVRkRPM0ZDUVVONFF6dDVRa0ZEU1R0M1FrRkRSQ3hKUVVGSkxFTkJRVU1zVDBGQlR5eEhRVUZITEVsQlFVa3NRMEZCUXp0M1FrRkRjRUlzVFVGQlRUdHhRa0ZEVkR0cFFrRkRTaXhSUVVGUkxFbEJRVWtzUTBGQlF5eFBRVUZQTEVOQlFVTXNTMEZCU3l4TFFVRkxMRWxCUVVrc1JVRkJSVHRoUVVONlF6dHBRa0ZEU1R0blFrRkZSQ3hKUVVGSkxFTkJRVU1zVlVGQlZTeERRVUZETEVsQlFVa3NRMEZCUXl4SlFVRkpMRU5CUVVNc1QwRkJUeXhEUVVGRExFTkJRVU03WjBKQlEyNURMRWxCUVVrc1EwRkJReXhSUVVGUkxFTkJRVU1zU1VGQlNTeERRVUZETEU5QlFVOHNRMEZCUXl4TFFVRkxMRU5CUVVNc1EwRkJRenRoUVVOeVF6dFRRVU5LTzFGQlEwUXNUMEZCVHl4SlFVRkpMRU5CUVVNc1QwRkJUeXhMUVVGTExFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNTVUZCU1N4RFFVRkRMRTlCUVU4c1EwRkJReXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVsQlFVa3NRMEZCUXp0SlFVTTFSQ3hEUVVGRE8wbEJRVUVzUTBGQlF6dEpRVWxHTEhWQ1FVRkpMRWRCUVVvN1VVRkRTU3hKUVVGSkxFbEJRVWtzUTBGQlF5eFBRVUZQTEV0QlFVc3NTVUZCU1N4RlFVRkZPMWxCUTNaQ0xFbEJRVWtzU1VGQlNTeEhRVUZITEVsQlFVa3NRMEZCUXl4TFFVRkxMRU5CUVVNc1MwRkJTeXhEUVVGRE8xbEJRelZDTEVsQlFVa3NTVUZCU1N4TFFVRkxMRWxCUVVrc1JVRkJSVHRuUWtGRFppeEpRVUZKTEVOQlFVTXNVVUZCVVN4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRE8yRkJRM1pDTzFOQlEwbzdZVUZEU1R0WlFVTkVMRWxCUVVrc1NVRkJTU3hEUVVGRExFOUJRVThzUTBGQlF5eEpRVUZKTEV0QlFVc3NTVUZCU1N4RlFVRkZPMmRDUVVNMVFpeEpRVUZKTEVsQlFVa3NRMEZCUXp0blFrRkRWQ3hIUVVGSE8yOUNRVU5ETEVsQlFVa3NSMEZCUnl4SlFVRkpMRU5CUVVNc1QwRkJUeXhEUVVGRE8yOUNRVU53UWl4SlFVRkpMRWxCUVVrc1EwRkJReXhWUVVGVkxFTkJRVU1zVFVGQlRTeEZRVUZGTzNkQ1FVTjRRaXhKUVVGSkxFTkJRVU1zVDBGQlR5eEhRVUZITEVsQlFVa3NRMEZCUXl4VlFVRlZMRU5CUVVNc1IwRkJSeXhGUVVGRkxFTkJRVU03Y1VKQlEzaERPM2xDUVVOSk8zZENRVU5FTEVsQlFVa3NRMEZCUXl4UFFVRlBMRWRCUVVjc1NVRkJTU3hEUVVGRE8zZENRVU53UWl4TlFVRk5PM0ZDUVVOVU8ybENRVU5LTEZGQlFWRXNTVUZCU1N4RFFVRkRMRTlCUVU4c1EwRkJReXhKUVVGSkxFdEJRVXNzU1VGQlNTeEZRVUZGTzJGQlEzaERPMmxDUVVOSk8yZENRVU5FTEVsQlFVa3NRMEZCUXl4VlFVRlZMRU5CUVVNc1NVRkJTU3hEUVVGRExFbEJRVWtzUTBGQlF5eFBRVUZQTEVOQlFVTXNRMEZCUXp0blFrRkRia01zU1VGQlNTeERRVUZETEZGQlFWRXNRMEZCUXl4SlFVRkpMRU5CUVVNc1QwRkJUeXhEUVVGRExFbEJRVWtzUTBGQlF5eERRVUZETzJGQlEzQkRPMU5CUTBvN1VVRkRSQ3hQUVVGUExFbEJRVWtzUTBGQlF5eFBRVUZQTEV0QlFVc3NTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJReXhKUVVGSkxFTkJRVU1zVDBGQlR5eERRVUZETEVsQlFVa3NRMEZCUXl4RFFVRkRMRU5CUVVNc1NVRkJTU3hEUVVGRE8wbEJRelZFTEVOQlFVTTdTVUZCUVN4RFFVRkRPMGxCUlVZc01rSkJRVkVzUjBGQlVpeFZRVUZUTEV0QlFVczdVVUZEVml4UFFVRlBMRXRCUVVzc1EwRkJReXhKUVVGSkxFdEJRVXNzU1VGQlNTeEZRVUZGTzFsQlEzaENMRWxCUVVrc1EwRkJReXhWUVVGVkxFTkJRVU1zU1VGQlNTeERRVUZETEV0QlFVc3NRMEZCUXl4RFFVRkRPMWxCUXpWQ0xFdEJRVXNzUjBGQlJ5eExRVUZMTEVOQlFVTXNTVUZCU1N4RFFVRkRPMU5CUTNSQ08xRkJRMFFzU1VGQlNTeERRVUZETEU5QlFVOHNSMEZCUnl4TFFVRkxMRU5CUVVNN1NVRkRla0lzUTBGQlF6dEpRVUZCTEVOQlFVTTdTVUZGUml3eVFrRkJVU3hIUVVGU0xGVkJRVk1zUzBGQlN6dFJRVU5XTEU5QlFVOHNTMEZCU3l4RFFVRkRMRXRCUVVzc1MwRkJTeXhKUVVGSkxFVkJRVVU3V1VGRGVrSXNTVUZCU1N4RFFVRkRMRlZCUVZVc1EwRkJReXhKUVVGSkxFTkJRVU1zUzBGQlN5eERRVUZETEVOQlFVTTdXVUZETlVJc1MwRkJTeXhIUVVGSExFdEJRVXNzUTBGQlF5eExRVUZMTEVOQlFVTTdVMEZEZGtJN1VVRkRSQ3hKUVVGSkxFTkJRVU1zVDBGQlR5eEhRVUZITEV0QlFVc3NRMEZCUXp0SlFVTjZRaXhEUVVGRE8wbEJRVUVzUTBGQlF6dEpRVU5PTEdWQlFVTTdRVUZCUkN4RFFVRkRMRUZCT1VaRUxFbEJPRVpETzBGQk9VWlpMRFJDUVVGUk8wRkJaMGR5UWp0SlFVdEpMR05CUVZrc1NVRkJTVHRSUVVOYUxFbEJRVWtzUTBGQlF5eEpRVUZKTEVkQlFVY3NTVUZCU1N4RFFVRkRPMUZCUTJwQ0xFbEJRVWtzUTBGQlF5eEpRVUZKTEVkQlFVY3NTVUZCU1N4RFFVRkRPMUZCUTJwQ0xFbEJRVWtzUTBGQlF5eExRVUZMTEVkQlFVY3NTVUZCU1N4RFFVRkRPMUZCUTJ4Q0xFbEJRVWtzUTBGQlF5eEhRVUZITEVkQlFVY3NTVUZCU1N4RFFVRkRPMGxCUTNCQ0xFTkJRVU03U1VGRlJDeDNRa0ZCVXl4SFFVRlVMRlZCUVZVc1IwRkJSenRSUVVOVUxFOUJRVThzUjBGQlJ5eERRVUZETEVOQlFVTXNRMEZCUXl4SlFVRkpMRU5CUVVNc1MwRkJTeXhEUVVGRExFTkJRVU1zUTBGQlF5eEpRVUZKTEVOQlFVTXNTVUZCU1N4RFFVRkRPMGxCUTNoRExFTkJRVU03U1VGQlFTeERRVUZETzBsQlJVWXNkMEpCUVZNc1IwRkJWQ3hWUVVGVkxFZEJRVWNzUlVGQlJTeEhRVUZITzFGQlEyUXNTVUZCU1N4SFFVRkhMRVZCUVVVN1dVRkRUQ3hKUVVGSkxFTkJRVU1zUzBGQlN5eEhRVUZITEVkQlFVY3NRMEZCUXp0VFFVTndRanRoUVVOSk8xbEJRMFFzU1VGQlNTeERRVUZETEVsQlFVa3NSMEZCUnl4SFFVRkhMRU5CUVVNN1UwRkRia0k3U1VGRFRDeERRVUZETzBsQlFVRXNRMEZCUXp0SlFVTk9MRmRCUVVNN1FVRkJSQ3hEUVVGRExFRkJlRUpFTEVsQmQwSkRPMEZCUlVRN1NVRkJLMElzTUVKQlFWRTdTVUZMYmtNc1owSkJRVmtzVlVGQmEwTTdVVUZCT1VNc1dVRkRTU3hwUWtGQlR5eFRRVWxXTzFGQlNFY3NTMEZCU1N4RFFVRkRMRXRCUVVzc1IwRkJSeXhKUVVGSkxFTkJRVU03VVVGRGJFSXNTMEZCU1N4RFFVRkRMRmRCUVZjc1IwRkJSeXhWUVVGVkxFTkJRVU03VVVGRE9VSXNTMEZCU1N4RFFVRkRMRWxCUVVrc1IwRkJSeXhEUVVGRExFTkJRVU03TzBsQlEyeENMRU5CUVVNN1NVRkhSQ3gxUWtGQlRTeEhRVUZPTEZWQlFVOHNTVUZCU1R0UlFVTlFMRWxCUVVrc1IwRkJSeXhIUVVGSExFdEJRVXNzUTBGQlF6dFJRVVZvUWl4SlFVRkpMRWxCUVVrc1EwRkJReXhMUVVGTExFdEJRVXNzU1VGQlNTeEZRVUZGTzFsQlJYSkNMRWxCUVVrc1EwRkJReXhMUVVGTExFZEJRVWNzU1VGQlNTeEpRVUZKTEVOQlFVTXNTVUZCU1N4RFFVRkRMRU5CUVVNN1dVRkROVUlzUjBGQlJ5eEhRVUZITEVsQlFVa3NRMEZCUXp0WlFVTllMRWxCUVVrc1EwRkJReXhKUVVGSkxFVkJRVVVzUTBGQlF6dFRRVU5tTzJGQlEwazdXVUZEUkN4SlFVRkpMRWxCUVVrc1IwRkJSeXhKUVVGSkxFbEJRVWtzUTBGQlF5eFRRVUZUTEVOQlFVTXNRMEZCUXp0WlFVVXZRaXhKUVVGSkxFZEJRVWNzUjBGQlJ5eExRVUZMTEVOQlFVTTdXVUZEYUVJc1NVRkJTU3hKUVVGSkxFZEJRVWNzUzBGQlN5eERRVUZETzFsQlIycENMRWxCUVVrc1JVRkJSU3hIUVVGSExFbEJRVWtzUTBGQlF6dFpRVU5rTEVsQlFVa3NSMEZCUnl4SFFVRkhMRWxCUVVrc1EwRkJRenRaUVVObUxFbEJRVWtzUTBGQlF5eEhRVUZITEVsQlFVa3NRMEZCUXp0WlFVTmlMRWxCUVVrc1NVRkJTU3hIUVVGSExFbEJRVWtzUTBGQlF5eExRVUZMTEVOQlFVTTdXVUZEZEVJc1IwRkJSeXhEUVVGRExFdEJRVXNzUjBGQlJ5eEpRVUZKTEVOQlFVTXNTMEZCU3l4RFFVRkRPMWxCUjNaQ0xFOUJRVThzU1VGQlNTeEZRVUZGTzJkQ1FVTlVMRWxCUVVrc1NVRkJTU3hMUVVGTExFbEJRVWtzUlVGQlJUdHZRa0ZGWml4SlFVRkpMRWRCUVVjc1NVRkJTU3hKUVVGSkxFTkJRVU1zU1VGQlNTeERRVUZETEVOQlFVTTdiMEpCUTNSQ0xFTkJRVU1zUTBGQlF5eFRRVUZUTEVOQlFVTXNSMEZCUnl4RlFVRkZMRWxCUVVrc1EwRkJReXhEUVVGRE8yOUNRVU4yUWl4SFFVRkhMRWRCUVVjc1NVRkJTU3hEUVVGRE8yOUNRVU5ZTEVsQlFVa3NRMEZCUXl4SlFVRkpMRVZCUVVVc1EwRkJRenRwUWtGRFpqdHhRa0ZEU1N4SlFVRkpMRTFCUVUwc1EwRkJReXhOUVVGTkxFTkJRVU1zU1VGQlNTeERRVUZETEVsQlFVa3NRMEZCUXl4SlFVRkpMRTFCUVUwc1EwRkJReXhOUVVGTkxFTkJRVU1zU1VGQlNTeERRVUZETEV0QlFVc3NRMEZCUXl4RlFVRkZPMjlDUVVVMVJDeEpRVUZKTEVOQlFVTXNSMEZCUnl4SFFVRkhMRWxCUVVrc1EwRkJRenR2UWtGRGFFSXNTVUZCU1N4RFFVRkRMRWxCUVVrc1EwRkJReXhIUVVGSExFZEJRVWNzUzBGQlN5eERRVUZETzI5Q1FVTjBRaXhKUVVGSkxFTkJRVU1zUzBGQlN5eERRVUZETEVkQlFVY3NSMEZCUnl4TFFVRkxMRU5CUVVNN2FVSkJRekZDTzJkQ1FVZEVMRWxCUVVrc1RVRkJUU3hEUVVGRExFMUJRVTBzUTBGQlF5eEpRVUZKTEVOQlFVTXNTVUZCU1N4TlFVRk5MRU5CUVVNc1RVRkJUU3hEUVVGRExFTkJRVU1zUTBGQlF5eEZRVUZGTzI5Q1FVTjZReXhKUVVGSkxFbEJRVWtzUjBGQlJ5eEhRVUZITEVOQlFVTXNTMEZCU3l4TFFVRkxMRVZCUVVVc1EwRkJRenR2UWtGRk5VSXNTVUZCU1N4SlFVRkpMRXRCUVVzc1EwRkJReXhEUVVGRExGTkJRVk1zUTBGQlF5eEpRVUZKTEVOQlFVTXNSVUZCUlR0M1FrRkROVUlzUjBGQlJ5eERRVUZETEZOQlFWTXNRMEZCUXl4SlFVRkpMRVZCUVVVc1RVRkJUU3hEUVVGRExHRkJRV0VzUTBGQlF5eEZRVUZGTEVWQlFVVXNRMEZCUXl4SlFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRE8zRkNRVU40UkR0NVFrRkRTVHQzUWtGRFJDeEhRVUZITEVOQlFVTXNVMEZCVXl4RFFVRkRMRWxCUVVrc1JVRkJSU3hOUVVGTkxFTkJRVU1zWVVGQllTeERRVUZETEVWQlFVVXNSVUZCUlN4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU03Y1VKQlEzaEVPMmxDUVVOS08yZENRVVZFTEVsQlFVa3NSMEZCUnl4SFFVRkhMRWxCUVVrc1EwRkJReXhYUVVGWExFTkJRVU1zU1VGQlNTeERRVUZETEVsQlFVa3NSVUZCUlN4SlFVRkpMRU5CUVVNc1EwRkJRenRuUWtGSE5VTXNTVUZCU1N4SFFVRkhMRXRCUVVzc1EwRkJReXhGUVVGRk8yOUNRVU5ZTEUxQlFVMDdhVUpCUTFRN1owSkJSVVFzU1VGQlNTeEhRVUZITEVkQlFVY3NRMEZCUXp0blFrRkRXQ3hIUVVGSExFZEJRVWNzUjBGQlJ5eEhRVUZITEVOQlFVTXNRMEZCUXp0blFrRkhaQ3hKUVVGSkxFVkJRVVVzUzBGQlN5eEpRVUZKTEVWQlFVVTdiMEpCUTJJc1IwRkJSeXhIUVVGSExFVkJRVVVzUTBGQlF6dHBRa0ZEV2p0blFrRkRSQ3hGUVVGRkxFZEJRVWNzUTBGQlF5eERRVUZETzJkQ1FVTlFMRU5CUVVNc1IwRkJSeXhKUVVGSkxFTkJRVU03WjBKQlExUXNTVUZCU1N4SFFVRkhMRWxCUVVrc1EwRkJReXhUUVVGVExFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTTdZVUZET1VJN1dVRkhSQ3hKUVVGSkxFTkJRVU1zUzBGQlN5eEhRVUZITEVsQlFVa3NRMEZCUXl4TFFVRkxMRU5CUVVNN1UwRkRNMEk3VVVGSFJDeEpRVUZKTEVOQlFVTXNTMEZCU3l4RFFVRkRMRWRCUVVjc1IwRkJSeXhMUVVGTExFTkJRVU03VVVGRmRrSXNUMEZCVHl4SFFVRkhMRU5CUVVNN1NVRkRaaXhEUVVGRE8wbEJRVUVzUTBGQlF6dEpRVWRHTEhWQ1FVRk5MRWRCUVU0c1ZVRkJUeXhKUVVGSk8xRkJRMUFzU1VGQlNTeEpRVUZKTEVOQlFVTXNTMEZCU3l4TFFVRkxMRWxCUVVrc1JVRkJSVHRaUVVOeVFpeFBRVUZQTEV0QlFVc3NRMEZCUXp0VFFVTm9RanRSUVVWRUxFbEJRVWtzU1VGQlNTeEhRVUZITEVsQlFVa3NTVUZCU1N4RFFVRkRMRk5CUVZNc1EwRkJReXhEUVVGRE8xRkJReTlDTEVsQlFVa3NTVUZCU1N4SFFVRkhMRWxCUVVrc1EwRkJRenRSUVVOb1FpeEpRVUZKTEVOQlFVTXNTMEZCU3l4SFFVRkhMRWxCUVVrc1EwRkJReXhMUVVGTExFTkJRVU03VVVGRGVFSXNTVUZCU1N4RFFVRkRMRWRCUVVjc1NVRkJTU3hEUVVGRE8xRkJRMklzU1VGQlNTeEZRVUZGTEVkQlFVY3NTVUZCU1N4RFFVRkRPMUZCUTJRc1NVRkJTU3hMUVVGTExFZEJRVWNzU1VGQlNTeERRVUZETzFGQlEycENMRWxCUVVrc1IwRkJSeXhIUVVGSExFbEJRVWtzUTBGQlF6dFJRVVZtTEU5QlFVOHNTVUZCU1N4RFFVRkRMRk5CUVZNc1EwRkJReXhIUVVGSExFTkJRVU1zUzBGQlN5eEpRVUZKTEVWQlFVVTdXVUZEYWtNc1NVRkJTU3hKUVVGSkxFZEJRVWNzUjBGQlJ5eERRVUZETzFsQlIyWXNSVUZCUlN4SFFVRkhMRU5CUVVNc1EwRkJRenRaUVVOUUxFTkJRVU1zUjBGQlJ5eEpRVUZKTEVOQlFVTTdXVUZEVkN4SlFVRkpMRWRCUVVjc1NVRkJTU3hEUVVGRExGTkJRVk1zUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXp0WlFVVXpRaXhKUVVGSkxFZEJRVWNzUjBGQlJ5eEpRVUZKTEVOQlFVTXNWMEZCVnl4RFFVRkRMRWxCUVVrc1JVRkJSU3hKUVVGSkxFTkJRVU1zU1VGQlNTeERRVUZETEVOQlFVTTdXVUZGTlVNc1IwRkJSeXhIUVVGSExFZEJRVWNzUjBGQlJ5eERRVUZETEVOQlFVTTdXVUZIWkN4SlFVRkpMRWRCUVVjc1MwRkJTeXhEUVVGRExFVkJRVVU3WjBKQlExZ3NTMEZCU3l4SFFVRkhMRWxCUVVrc1EwRkJRenRoUVVOb1FqdFpRVWRFTEVsQlFVa3NRMEZCUXl4TlFVRk5MRU5CUVVNc1RVRkJUU3hEUVVGRExFbEJRVWtzUTBGQlF5eEpRVUZKTEVOQlFVTXNUVUZCVFN4RFFVRkRMRTFCUVUwc1EwRkJReXhKUVVGSkxFTkJRVU1zVTBGQlV5eERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRVZCUVVVN1owSkJRemRFTEVsQlFVa3NUVUZCVFN4RFFVRkRMRTFCUVUwc1EwRkJReXhKUVVGSkxFTkJRVU1zVTBGQlV5eERRVUZETEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1JVRkJSVHR2UWtGRGNrTXNTVUZCU1N4RlFVRkZMRWRCUVVjc1RVRkJUU3hEUVVGRExHRkJRV0VzUTBGQlF5eEpRVUZKTEVWQlFVVXNSMEZCUnl4RFFVRkRMRU5CUVVNN2IwSkJRM3BETEVOQlFVTXNRMEZCUXl4VFFVRlRMRU5CUVVNc1NVRkJTU3hGUVVGRkxFVkJRVVVzUTBGQlF5eERRVUZETzI5Q1FVTjBRaXhEUVVGRExFZEJRVWNzUlVGQlJTeERRVUZETzJsQ1FVTldPM0ZDUVVOSkxFbEJRVWtzUTBGQlF5eE5RVUZOTEVOQlFVTXNUVUZCVFN4RFFVRkRMRWxCUVVrc1EwRkJReXhUUVVGVExFTkJRVU1zUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXl4RlFVRkZPMjlDUVVNelF5eEpRVUZKTEU5QlFVOHNSMEZCUnl4RFFVRkRMRU5CUVVNc1UwRkJVeXhEUVVGRExFTkJRVU1zU1VGQlNTeERRVUZETEVOQlFVTTdiMEpCUTJwRExFbEJRVWtzVDBGQlR5eExRVUZMTEVsQlFVa3NSVUZCUlR0M1FrRkRiRUlzU1VGQlNTeERRVUZETEUxQlFVMHNRMEZCUXl4TlFVRk5MRU5CUVVNc1QwRkJUeXhEUVVGRExGTkJRVk1zUTBGQlF5eERRVUZETEVsQlFVa3NRMEZCUXl4RFFVRkRMRWxCUVVrc1EwRkJReXhOUVVGTkxFTkJRVU1zVFVGQlRTeERRVUZETEU5QlFVOHNRMEZCUXl4VFFVRlRMRU5CUVVNc1NVRkJTU3hEUVVGRExFTkJRVU1zUlVGQlJUczBRa0ZGY2tZc1EwRkJReXhEUVVGRExFZEJRVWNzUjBGQlJ5eExRVUZMTEVOQlFVTTdORUpCUTJRc1QwRkJUeXhEUVVGRExFZEJRVWNzUjBGQlJ5eEpRVUZKTEVOQlFVTTdORUpCUTI1Q0xFbEJRVWtzUTBGQlF5eEhRVUZITEVkQlFVY3NTVUZCU1N4RFFVRkRPM2xDUVVOdVFqczJRa0ZEU1RzMFFrRkRSQ3hKUVVGSkxFbEJRVWtzUjBGQlJ5eEZRVUZGTEVOQlFVTXNTMEZCU3l4TFFVRkxMRU5CUVVNc1EwRkJRenMwUWtGRk1VSXNTVUZCU1N4TlFVRk5MRU5CUVVNc1RVRkJUU3hEUVVGRExFOUJRVThzUTBGQlF5eFRRVUZUTEVOQlFVTXNTVUZCU1N4RFFVRkRMRU5CUVVNc1JVRkJSVHRuUTBGRGVFTXNSVUZCUlN4RFFVRkRMRk5CUVZNc1EwRkJReXhKUVVGSkxFVkJRVVVzVFVGQlRTeERRVUZETEdGQlFXRXNRMEZCUXl4RFFVRkRMRVZCUVVVc1NVRkJTU3hEUVVGRExFTkJRVU1zUTBGQlF6czJRa0ZEY2tRN2FVTkJRMGtzU1VGQlNTeE5RVUZOTEVOQlFVTXNUVUZCVFN4RFFVRkRMRTlCUVU4c1EwRkJReXhUUVVGVExFTkJRVU1zUTBGQlF5eEpRVUZKTEVOQlFVTXNRMEZCUXl4RlFVRkZPMmREUVVNNVF5eEZRVUZGTEVOQlFVTXNVMEZCVXl4RFFVRkRMRWxCUVVrc1JVRkJSU3hOUVVGTkxFTkJRVU1zWVVGQllTeERRVUZETEVOQlFVTXNSVUZCUlN4SlFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRE96WkNRVU55UkRzMFFrRkhSQ3hKUVVGSkxFZEJRVWNzUjBGQlJ5eEZRVUZGTEVOQlFVTXNVMEZCVXl4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRE96UkNRVU0zUWl4SFFVRkhMRU5CUVVNc1IwRkJSeXhIUVVGSExFbEJRVWtzUTBGQlF6czBRa0ZEWml4SlFVRkpMRU5CUVVNc1IwRkJSeXhIUVVGSExFbEJRVWtzUTBGQlF6czBRa0ZEYUVJc1IwRkJSeXhEUVVGRExFbEJRVWtzUTBGQlF5eEhRVUZITEVkQlFVY3NTMEZCU3l4RFFVRkRPelJDUVVOeVFpeEhRVUZITEVOQlFVTXNTMEZCU3l4RFFVRkRMRWRCUVVjc1IwRkJSeXhMUVVGTExFTkJRVU03ZVVKQlEzcENPM0ZDUVVOS08ybENRVU5LTzJGQlEwbzdVMEZEU2p0UlFVZEVMRWxCUVVrc1MwRkJTeXhMUVVGTExFbEJRVWtzUlVGQlJUdFpRVU5vUWl4TFFVRkxMRU5CUVVNc1NVRkJTU3hIUVVGSExFbEJRVWtzUTBGQlF5eEpRVUZKTEVOQlFVTTdXVUZEZGtJc1EwRkJReXhEUVVGRExGTkJRVk1zUTBGQlF5eERRVUZETEVOQlFVTXNTMEZCU3l4TFFVRkxMRWxCUVVrc1JVRkJSU3hKUVVGSkxFTkJRVU1zVTBGQlV5eERRVUZETEVsQlFVa3NRMEZCUXl4SlFVRkpMRXRCUVVzc1NVRkJTU3hEUVVGRExFTkJRVU1zUTBGQlF6dFpRVU5zUlN4SlFVRkpMRU5CUVVNc1NVRkJTU3hGUVVGRkxFTkJRVU03VTBGRFpqdFJRVWRFTEVsQlFVa3NRMEZCUXl4TFFVRkxMRWRCUVVjc1NVRkJTU3hEUVVGRExFdEJRVXNzUTBGQlF6dFJRVU40UWl4SlFVRkpMRWxCUVVrc1EwRkJReXhMUVVGTExFdEJRVXNzU1VGQlNTeEZRVUZGTzFsQlEzSkNMRWxCUVVrc1EwRkJReXhMUVVGTExFTkJRVU1zUjBGQlJ5eEhRVUZITEV0QlFVc3NRMEZCUXp0VFFVTXhRanRSUVVWRUxFOUJRVThzUzBGQlN5eExRVUZMTEVsQlFVa3NRMEZCUXp0SlFVTXhRaXhEUVVGRE8wbEJRVUVzUTBGQlF6dEpRVVZMTEdGQlFVMHNSMEZCWWl4VlFVRmpMRWxCUVVrN1VVRkRaQ3hQUVVGUExFbEJRVWtzUzBGQlN5eEpRVUZKTEVsQlFVa3NTVUZCU1N4RFFVRkRMRWRCUVVjc1EwRkJRenRKUVVOeVF5eERRVUZETzBsQlJVMHNiMEpCUVdFc1IwRkJjRUlzVlVGQmNVSXNTVUZCU1N4RlFVRkZMRWRCUVVjN1VVRkRNVUlzU1VGQlNTeEpRVUZKTEVkQlFVY3NTVUZCU1N4RFFVRkRMRk5CUVZNc1EwRkJReXhEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETzFGQlJXaERMRWxCUVVrc1EwRkJReXhUUVVGVExFTkJRVU1zUTBGQlF5eEhRVUZITEVWQlFVVXNTVUZCU1N4RFFVRkRMRk5CUVZNc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETzFGQlF6RkRMRWxCUVVrc1EwRkJReXhUUVVGVExFTkJRVU1zUjBGQlJ5eEZRVUZGTEVsQlFVa3NRMEZCUXl4RFFVRkRPMUZCUlRGQ0xFbEJRVWtzUTBGQlF5eEhRVUZITEVkQlFVY3NTVUZCU1N4RFFVRkRPMUZCUTJoQ0xFbEJRVWtzUTBGQlF5eEhRVUZITEVkQlFVY3NTMEZCU3l4RFFVRkRPMUZCUldwQ0xFOUJRVThzU1VGQlNTeERRVUZETzBsQlEyaENMRU5CUVVNN1NVRkZUU3h2UWtGQllTeEhRVUZ3UWl4VlFVRnhRaXhKUVVGSkxFVkJRVVVzUjBGQlJ6dFJRVU14UWl4SlFVRkpMRU5CUVVNc1UwRkJVeXhEUVVGRExFTkJRVU1zUjBGQlJ5eEZRVUZGTEUxQlFVMHNRMEZCUXl4aFFVRmhMRU5CUVVNc1NVRkJTU3hEUVVGRExGTkJRVk1zUTBGQlF5eERRVUZETEVkQlFVY3NRMEZCUXl4RlFVRkZMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF6dFJRVU4yUlN4UFFVRlBMRTFCUVUwc1EwRkJReXhoUVVGaExFTkJRVU1zU1VGQlNTeEZRVUZGTEVkQlFVY3NRMEZCUXl4RFFVRkRPMGxCUXpORExFTkJRVU03U1VGRFRDeGhRVUZETzBGQlFVUXNRMEZCUXl4QlFYSk5SQ3hEUVVFclFpeFJRVUZSTEVkQmNVMTBRenRCUVhKTldTeDNRa0ZCVFNKOSIsIlwidXNlIHN0cmljdFwiO1xyXG52YXIgX19leHRlbmRzID0gKHRoaXMgJiYgdGhpcy5fX2V4dGVuZHMpIHx8IChmdW5jdGlvbiAoKSB7XHJcbiAgICB2YXIgZXh0ZW5kU3RhdGljcyA9IGZ1bmN0aW9uIChkLCBiKSB7XHJcbiAgICAgICAgZXh0ZW5kU3RhdGljcyA9IE9iamVjdC5zZXRQcm90b3R5cGVPZiB8fFxyXG4gICAgICAgICAgICAoeyBfX3Byb3RvX186IFtdIH0gaW5zdGFuY2VvZiBBcnJheSAmJiBmdW5jdGlvbiAoZCwgYikgeyBkLl9fcHJvdG9fXyA9IGI7IH0pIHx8XHJcbiAgICAgICAgICAgIGZ1bmN0aW9uIChkLCBiKSB7IGZvciAodmFyIHAgaW4gYikgaWYgKGIuaGFzT3duUHJvcGVydHkocCkpIGRbcF0gPSBiW3BdOyB9O1xyXG4gICAgICAgIHJldHVybiBleHRlbmRTdGF0aWNzKGQsIGIpO1xyXG4gICAgfTtcclxuICAgIHJldHVybiBmdW5jdGlvbiAoZCwgYikge1xyXG4gICAgICAgIGV4dGVuZFN0YXRpY3MoZCwgYik7XHJcbiAgICAgICAgZnVuY3Rpb24gX18oKSB7IHRoaXMuY29uc3RydWN0b3IgPSBkOyB9XHJcbiAgICAgICAgZC5wcm90b3R5cGUgPSBiID09PSBudWxsID8gT2JqZWN0LmNyZWF0ZShiKSA6IChfXy5wcm90b3R5cGUgPSBiLnByb3RvdHlwZSwgbmV3IF9fKCkpO1xyXG4gICAgfTtcclxufSkoKTtcclxuT2JqZWN0LmRlZmluZVByb3BlcnR5KGV4cG9ydHMsIFwiX19lc01vZHVsZVwiLCB7IHZhbHVlOiB0cnVlIH0pO1xyXG52YXIgdnBzY18xID0gcmVxdWlyZShcIi4vdnBzY1wiKTtcclxudmFyIHJidHJlZV8xID0gcmVxdWlyZShcIi4vcmJ0cmVlXCIpO1xyXG5mdW5jdGlvbiBjb21wdXRlR3JvdXBCb3VuZHMoZykge1xyXG4gICAgZy5ib3VuZHMgPSB0eXBlb2YgZy5sZWF2ZXMgIT09IFwidW5kZWZpbmVkXCIgP1xyXG4gICAgICAgIGcubGVhdmVzLnJlZHVjZShmdW5jdGlvbiAociwgYykgeyByZXR1cm4gYy5ib3VuZHMudW5pb24ocik7IH0sIFJlY3RhbmdsZS5lbXB0eSgpKSA6XHJcbiAgICAgICAgUmVjdGFuZ2xlLmVtcHR5KCk7XHJcbiAgICBpZiAodHlwZW9mIGcuZ3JvdXBzICE9PSBcInVuZGVmaW5lZFwiKVxyXG4gICAgICAgIGcuYm91bmRzID0gZy5ncm91cHMucmVkdWNlKGZ1bmN0aW9uIChyLCBjKSB7IHJldHVybiBjb21wdXRlR3JvdXBCb3VuZHMoYykudW5pb24ocik7IH0sIGcuYm91bmRzKTtcclxuICAgIGcuYm91bmRzID0gZy5ib3VuZHMuaW5mbGF0ZShnLnBhZGRpbmcpO1xyXG4gICAgcmV0dXJuIGcuYm91bmRzO1xyXG59XHJcbmV4cG9ydHMuY29tcHV0ZUdyb3VwQm91bmRzID0gY29tcHV0ZUdyb3VwQm91bmRzO1xyXG52YXIgUmVjdGFuZ2xlID0gKGZ1bmN0aW9uICgpIHtcclxuICAgIGZ1bmN0aW9uIFJlY3RhbmdsZSh4LCBYLCB5LCBZKSB7XHJcbiAgICAgICAgdGhpcy54ID0geDtcclxuICAgICAgICB0aGlzLlggPSBYO1xyXG4gICAgICAgIHRoaXMueSA9IHk7XHJcbiAgICAgICAgdGhpcy5ZID0gWTtcclxuICAgIH1cclxuICAgIFJlY3RhbmdsZS5lbXB0eSA9IGZ1bmN0aW9uICgpIHsgcmV0dXJuIG5ldyBSZWN0YW5nbGUoTnVtYmVyLlBPU0lUSVZFX0lORklOSVRZLCBOdW1iZXIuTkVHQVRJVkVfSU5GSU5JVFksIE51bWJlci5QT1NJVElWRV9JTkZJTklUWSwgTnVtYmVyLk5FR0FUSVZFX0lORklOSVRZKTsgfTtcclxuICAgIFJlY3RhbmdsZS5wcm90b3R5cGUuY3ggPSBmdW5jdGlvbiAoKSB7IHJldHVybiAodGhpcy54ICsgdGhpcy5YKSAvIDI7IH07XHJcbiAgICBSZWN0YW5nbGUucHJvdG90eXBlLmN5ID0gZnVuY3Rpb24gKCkgeyByZXR1cm4gKHRoaXMueSArIHRoaXMuWSkgLyAyOyB9O1xyXG4gICAgUmVjdGFuZ2xlLnByb3RvdHlwZS5vdmVybGFwWCA9IGZ1bmN0aW9uIChyKSB7XHJcbiAgICAgICAgdmFyIHV4ID0gdGhpcy5jeCgpLCB2eCA9IHIuY3goKTtcclxuICAgICAgICBpZiAodXggPD0gdnggJiYgci54IDwgdGhpcy5YKVxyXG4gICAgICAgICAgICByZXR1cm4gdGhpcy5YIC0gci54O1xyXG4gICAgICAgIGlmICh2eCA8PSB1eCAmJiB0aGlzLnggPCByLlgpXHJcbiAgICAgICAgICAgIHJldHVybiByLlggLSB0aGlzLng7XHJcbiAgICAgICAgcmV0dXJuIDA7XHJcbiAgICB9O1xyXG4gICAgUmVjdGFuZ2xlLnByb3RvdHlwZS5vdmVybGFwWSA9IGZ1bmN0aW9uIChyKSB7XHJcbiAgICAgICAgdmFyIHV5ID0gdGhpcy5jeSgpLCB2eSA9IHIuY3koKTtcclxuICAgICAgICBpZiAodXkgPD0gdnkgJiYgci55IDwgdGhpcy5ZKVxyXG4gICAgICAgICAgICByZXR1cm4gdGhpcy5ZIC0gci55O1xyXG4gICAgICAgIGlmICh2eSA8PSB1eSAmJiB0aGlzLnkgPCByLlkpXHJcbiAgICAgICAgICAgIHJldHVybiByLlkgLSB0aGlzLnk7XHJcbiAgICAgICAgcmV0dXJuIDA7XHJcbiAgICB9O1xyXG4gICAgUmVjdGFuZ2xlLnByb3RvdHlwZS5zZXRYQ2VudHJlID0gZnVuY3Rpb24gKGN4KSB7XHJcbiAgICAgICAgdmFyIGR4ID0gY3ggLSB0aGlzLmN4KCk7XHJcbiAgICAgICAgdGhpcy54ICs9IGR4O1xyXG4gICAgICAgIHRoaXMuWCArPSBkeDtcclxuICAgIH07XHJcbiAgICBSZWN0YW5nbGUucHJvdG90eXBlLnNldFlDZW50cmUgPSBmdW5jdGlvbiAoY3kpIHtcclxuICAgICAgICB2YXIgZHkgPSBjeSAtIHRoaXMuY3koKTtcclxuICAgICAgICB0aGlzLnkgKz0gZHk7XHJcbiAgICAgICAgdGhpcy5ZICs9IGR5O1xyXG4gICAgfTtcclxuICAgIFJlY3RhbmdsZS5wcm90b3R5cGUud2lkdGggPSBmdW5jdGlvbiAoKSB7XHJcbiAgICAgICAgcmV0dXJuIHRoaXMuWCAtIHRoaXMueDtcclxuICAgIH07XHJcbiAgICBSZWN0YW5nbGUucHJvdG90eXBlLmhlaWdodCA9IGZ1bmN0aW9uICgpIHtcclxuICAgICAgICByZXR1cm4gdGhpcy5ZIC0gdGhpcy55O1xyXG4gICAgfTtcclxuICAgIFJlY3RhbmdsZS5wcm90b3R5cGUudW5pb24gPSBmdW5jdGlvbiAocikge1xyXG4gICAgICAgIHJldHVybiBuZXcgUmVjdGFuZ2xlKE1hdGgubWluKHRoaXMueCwgci54KSwgTWF0aC5tYXgodGhpcy5YLCByLlgpLCBNYXRoLm1pbih0aGlzLnksIHIueSksIE1hdGgubWF4KHRoaXMuWSwgci5ZKSk7XHJcbiAgICB9O1xyXG4gICAgUmVjdGFuZ2xlLnByb3RvdHlwZS5saW5lSW50ZXJzZWN0aW9ucyA9IGZ1bmN0aW9uICh4MSwgeTEsIHgyLCB5Mikge1xyXG4gICAgICAgIHZhciBzaWRlcyA9IFtbdGhpcy54LCB0aGlzLnksIHRoaXMuWCwgdGhpcy55XSxcclxuICAgICAgICAgICAgW3RoaXMuWCwgdGhpcy55LCB0aGlzLlgsIHRoaXMuWV0sXHJcbiAgICAgICAgICAgIFt0aGlzLlgsIHRoaXMuWSwgdGhpcy54LCB0aGlzLlldLFxyXG4gICAgICAgICAgICBbdGhpcy54LCB0aGlzLlksIHRoaXMueCwgdGhpcy55XV07XHJcbiAgICAgICAgdmFyIGludGVyc2VjdGlvbnMgPSBbXTtcclxuICAgICAgICBmb3IgKHZhciBpID0gMDsgaSA8IDQ7ICsraSkge1xyXG4gICAgICAgICAgICB2YXIgciA9IFJlY3RhbmdsZS5saW5lSW50ZXJzZWN0aW9uKHgxLCB5MSwgeDIsIHkyLCBzaWRlc1tpXVswXSwgc2lkZXNbaV1bMV0sIHNpZGVzW2ldWzJdLCBzaWRlc1tpXVszXSk7XHJcbiAgICAgICAgICAgIGlmIChyICE9PSBudWxsKVxyXG4gICAgICAgICAgICAgICAgaW50ZXJzZWN0aW9ucy5wdXNoKHsgeDogci54LCB5OiByLnkgfSk7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIHJldHVybiBpbnRlcnNlY3Rpb25zO1xyXG4gICAgfTtcclxuICAgIFJlY3RhbmdsZS5wcm90b3R5cGUucmF5SW50ZXJzZWN0aW9uID0gZnVuY3Rpb24gKHgyLCB5Mikge1xyXG4gICAgICAgIHZhciBpbnRzID0gdGhpcy5saW5lSW50ZXJzZWN0aW9ucyh0aGlzLmN4KCksIHRoaXMuY3koKSwgeDIsIHkyKTtcclxuICAgICAgICByZXR1cm4gaW50cy5sZW5ndGggPiAwID8gaW50c1swXSA6IG51bGw7XHJcbiAgICB9O1xyXG4gICAgUmVjdGFuZ2xlLnByb3RvdHlwZS52ZXJ0aWNlcyA9IGZ1bmN0aW9uICgpIHtcclxuICAgICAgICByZXR1cm4gW1xyXG4gICAgICAgICAgICB7IHg6IHRoaXMueCwgeTogdGhpcy55IH0sXHJcbiAgICAgICAgICAgIHsgeDogdGhpcy5YLCB5OiB0aGlzLnkgfSxcclxuICAgICAgICAgICAgeyB4OiB0aGlzLlgsIHk6IHRoaXMuWSB9LFxyXG4gICAgICAgICAgICB7IHg6IHRoaXMueCwgeTogdGhpcy5ZIH1cclxuICAgICAgICBdO1xyXG4gICAgfTtcclxuICAgIFJlY3RhbmdsZS5saW5lSW50ZXJzZWN0aW9uID0gZnVuY3Rpb24gKHgxLCB5MSwgeDIsIHkyLCB4MywgeTMsIHg0LCB5NCkge1xyXG4gICAgICAgIHZhciBkeDEyID0geDIgLSB4MSwgZHgzNCA9IHg0IC0geDMsIGR5MTIgPSB5MiAtIHkxLCBkeTM0ID0geTQgLSB5MywgZGVub21pbmF0b3IgPSBkeTM0ICogZHgxMiAtIGR4MzQgKiBkeTEyO1xyXG4gICAgICAgIGlmIChkZW5vbWluYXRvciA9PSAwKVxyXG4gICAgICAgICAgICByZXR1cm4gbnVsbDtcclxuICAgICAgICB2YXIgZHgzMSA9IHgxIC0geDMsIGR5MzEgPSB5MSAtIHkzLCBudW1hID0gZHgzNCAqIGR5MzEgLSBkeTM0ICogZHgzMSwgYSA9IG51bWEgLyBkZW5vbWluYXRvciwgbnVtYiA9IGR4MTIgKiBkeTMxIC0gZHkxMiAqIGR4MzEsIGIgPSBudW1iIC8gZGVub21pbmF0b3I7XHJcbiAgICAgICAgaWYgKGEgPj0gMCAmJiBhIDw9IDEgJiYgYiA+PSAwICYmIGIgPD0gMSkge1xyXG4gICAgICAgICAgICByZXR1cm4ge1xyXG4gICAgICAgICAgICAgICAgeDogeDEgKyBhICogZHgxMixcclxuICAgICAgICAgICAgICAgIHk6IHkxICsgYSAqIGR5MTJcclxuICAgICAgICAgICAgfTtcclxuICAgICAgICB9XHJcbiAgICAgICAgcmV0dXJuIG51bGw7XHJcbiAgICB9O1xyXG4gICAgUmVjdGFuZ2xlLnByb3RvdHlwZS5pbmZsYXRlID0gZnVuY3Rpb24gKHBhZCkge1xyXG4gICAgICAgIHJldHVybiBuZXcgUmVjdGFuZ2xlKHRoaXMueCAtIHBhZCwgdGhpcy5YICsgcGFkLCB0aGlzLnkgLSBwYWQsIHRoaXMuWSArIHBhZCk7XHJcbiAgICB9O1xyXG4gICAgcmV0dXJuIFJlY3RhbmdsZTtcclxufSgpKTtcclxuZXhwb3J0cy5SZWN0YW5nbGUgPSBSZWN0YW5nbGU7XHJcbmZ1bmN0aW9uIG1ha2VFZGdlQmV0d2Vlbihzb3VyY2UsIHRhcmdldCwgYWgpIHtcclxuICAgIHZhciBzaSA9IHNvdXJjZS5yYXlJbnRlcnNlY3Rpb24odGFyZ2V0LmN4KCksIHRhcmdldC5jeSgpKSB8fCB7IHg6IHNvdXJjZS5jeCgpLCB5OiBzb3VyY2UuY3koKSB9LCB0aSA9IHRhcmdldC5yYXlJbnRlcnNlY3Rpb24oc291cmNlLmN4KCksIHNvdXJjZS5jeSgpKSB8fCB7IHg6IHRhcmdldC5jeCgpLCB5OiB0YXJnZXQuY3koKSB9LCBkeCA9IHRpLnggLSBzaS54LCBkeSA9IHRpLnkgLSBzaS55LCBsID0gTWF0aC5zcXJ0KGR4ICogZHggKyBkeSAqIGR5KSwgYWwgPSBsIC0gYWg7XHJcbiAgICByZXR1cm4ge1xyXG4gICAgICAgIHNvdXJjZUludGVyc2VjdGlvbjogc2ksXHJcbiAgICAgICAgdGFyZ2V0SW50ZXJzZWN0aW9uOiB0aSxcclxuICAgICAgICBhcnJvd1N0YXJ0OiB7IHg6IHNpLnggKyBhbCAqIGR4IC8gbCwgeTogc2kueSArIGFsICogZHkgLyBsIH1cclxuICAgIH07XHJcbn1cclxuZXhwb3J0cy5tYWtlRWRnZUJldHdlZW4gPSBtYWtlRWRnZUJldHdlZW47XHJcbmZ1bmN0aW9uIG1ha2VFZGdlVG8ocywgdGFyZ2V0LCBhaCkge1xyXG4gICAgdmFyIHRpID0gdGFyZ2V0LnJheUludGVyc2VjdGlvbihzLngsIHMueSk7XHJcbiAgICBpZiAoIXRpKVxyXG4gICAgICAgIHRpID0geyB4OiB0YXJnZXQuY3goKSwgeTogdGFyZ2V0LmN5KCkgfTtcclxuICAgIHZhciBkeCA9IHRpLnggLSBzLngsIGR5ID0gdGkueSAtIHMueSwgbCA9IE1hdGguc3FydChkeCAqIGR4ICsgZHkgKiBkeSk7XHJcbiAgICByZXR1cm4geyB4OiB0aS54IC0gYWggKiBkeCAvIGwsIHk6IHRpLnkgLSBhaCAqIGR5IC8gbCB9O1xyXG59XHJcbmV4cG9ydHMubWFrZUVkZ2VUbyA9IG1ha2VFZGdlVG87XHJcbnZhciBOb2RlID0gKGZ1bmN0aW9uICgpIHtcclxuICAgIGZ1bmN0aW9uIE5vZGUodiwgciwgcG9zKSB7XHJcbiAgICAgICAgdGhpcy52ID0gdjtcclxuICAgICAgICB0aGlzLnIgPSByO1xyXG4gICAgICAgIHRoaXMucG9zID0gcG9zO1xyXG4gICAgICAgIHRoaXMucHJldiA9IG1ha2VSQlRyZWUoKTtcclxuICAgICAgICB0aGlzLm5leHQgPSBtYWtlUkJUcmVlKCk7XHJcbiAgICB9XHJcbiAgICByZXR1cm4gTm9kZTtcclxufSgpKTtcclxudmFyIEV2ZW50ID0gKGZ1bmN0aW9uICgpIHtcclxuICAgIGZ1bmN0aW9uIEV2ZW50KGlzT3BlbiwgdiwgcG9zKSB7XHJcbiAgICAgICAgdGhpcy5pc09wZW4gPSBpc09wZW47XHJcbiAgICAgICAgdGhpcy52ID0gdjtcclxuICAgICAgICB0aGlzLnBvcyA9IHBvcztcclxuICAgIH1cclxuICAgIHJldHVybiBFdmVudDtcclxufSgpKTtcclxuZnVuY3Rpb24gY29tcGFyZUV2ZW50cyhhLCBiKSB7XHJcbiAgICBpZiAoYS5wb3MgPiBiLnBvcykge1xyXG4gICAgICAgIHJldHVybiAxO1xyXG4gICAgfVxyXG4gICAgaWYgKGEucG9zIDwgYi5wb3MpIHtcclxuICAgICAgICByZXR1cm4gLTE7XHJcbiAgICB9XHJcbiAgICBpZiAoYS5pc09wZW4pIHtcclxuICAgICAgICByZXR1cm4gLTE7XHJcbiAgICB9XHJcbiAgICBpZiAoYi5pc09wZW4pIHtcclxuICAgICAgICByZXR1cm4gMTtcclxuICAgIH1cclxuICAgIHJldHVybiAwO1xyXG59XHJcbmZ1bmN0aW9uIG1ha2VSQlRyZWUoKSB7XHJcbiAgICByZXR1cm4gbmV3IHJidHJlZV8xLlJCVHJlZShmdW5jdGlvbiAoYSwgYikgeyByZXR1cm4gYS5wb3MgLSBiLnBvczsgfSk7XHJcbn1cclxudmFyIHhSZWN0ID0ge1xyXG4gICAgZ2V0Q2VudHJlOiBmdW5jdGlvbiAocikgeyByZXR1cm4gci5jeCgpOyB9LFxyXG4gICAgZ2V0T3BlbjogZnVuY3Rpb24gKHIpIHsgcmV0dXJuIHIueTsgfSxcclxuICAgIGdldENsb3NlOiBmdW5jdGlvbiAocikgeyByZXR1cm4gci5ZOyB9LFxyXG4gICAgZ2V0U2l6ZTogZnVuY3Rpb24gKHIpIHsgcmV0dXJuIHIud2lkdGgoKTsgfSxcclxuICAgIG1ha2VSZWN0OiBmdW5jdGlvbiAob3BlbiwgY2xvc2UsIGNlbnRlciwgc2l6ZSkgeyByZXR1cm4gbmV3IFJlY3RhbmdsZShjZW50ZXIgLSBzaXplIC8gMiwgY2VudGVyICsgc2l6ZSAvIDIsIG9wZW4sIGNsb3NlKTsgfSxcclxuICAgIGZpbmROZWlnaGJvdXJzOiBmaW5kWE5laWdoYm91cnNcclxufTtcclxudmFyIHlSZWN0ID0ge1xyXG4gICAgZ2V0Q2VudHJlOiBmdW5jdGlvbiAocikgeyByZXR1cm4gci5jeSgpOyB9LFxyXG4gICAgZ2V0T3BlbjogZnVuY3Rpb24gKHIpIHsgcmV0dXJuIHIueDsgfSxcclxuICAgIGdldENsb3NlOiBmdW5jdGlvbiAocikgeyByZXR1cm4gci5YOyB9LFxyXG4gICAgZ2V0U2l6ZTogZnVuY3Rpb24gKHIpIHsgcmV0dXJuIHIuaGVpZ2h0KCk7IH0sXHJcbiAgICBtYWtlUmVjdDogZnVuY3Rpb24gKG9wZW4sIGNsb3NlLCBjZW50ZXIsIHNpemUpIHsgcmV0dXJuIG5ldyBSZWN0YW5nbGUob3BlbiwgY2xvc2UsIGNlbnRlciAtIHNpemUgLyAyLCBjZW50ZXIgKyBzaXplIC8gMik7IH0sXHJcbiAgICBmaW5kTmVpZ2hib3VyczogZmluZFlOZWlnaGJvdXJzXHJcbn07XHJcbmZ1bmN0aW9uIGdlbmVyYXRlR3JvdXBDb25zdHJhaW50cyhyb290LCBmLCBtaW5TZXAsIGlzQ29udGFpbmVkKSB7XHJcbiAgICBpZiAoaXNDb250YWluZWQgPT09IHZvaWQgMCkgeyBpc0NvbnRhaW5lZCA9IGZhbHNlOyB9XHJcbiAgICB2YXIgcGFkZGluZyA9IHJvb3QucGFkZGluZywgZ24gPSB0eXBlb2Ygcm9vdC5ncm91cHMgIT09ICd1bmRlZmluZWQnID8gcm9vdC5ncm91cHMubGVuZ3RoIDogMCwgbG4gPSB0eXBlb2Ygcm9vdC5sZWF2ZXMgIT09ICd1bmRlZmluZWQnID8gcm9vdC5sZWF2ZXMubGVuZ3RoIDogMCwgY2hpbGRDb25zdHJhaW50cyA9ICFnbiA/IFtdXHJcbiAgICAgICAgOiByb290Lmdyb3Vwcy5yZWR1Y2UoZnVuY3Rpb24gKGNjcywgZykgeyByZXR1cm4gY2NzLmNvbmNhdChnZW5lcmF0ZUdyb3VwQ29uc3RyYWludHMoZywgZiwgbWluU2VwLCB0cnVlKSk7IH0sIFtdKSwgbiA9IChpc0NvbnRhaW5lZCA/IDIgOiAwKSArIGxuICsgZ24sIHZzID0gbmV3IEFycmF5KG4pLCBycyA9IG5ldyBBcnJheShuKSwgaSA9IDAsIGFkZCA9IGZ1bmN0aW9uIChyLCB2KSB7IHJzW2ldID0gcjsgdnNbaSsrXSA9IHY7IH07XHJcbiAgICBpZiAoaXNDb250YWluZWQpIHtcclxuICAgICAgICB2YXIgYiA9IHJvb3QuYm91bmRzLCBjID0gZi5nZXRDZW50cmUoYiksIHMgPSBmLmdldFNpemUoYikgLyAyLCBvcGVuID0gZi5nZXRPcGVuKGIpLCBjbG9zZSA9IGYuZ2V0Q2xvc2UoYiksIG1pbiA9IGMgLSBzICsgcGFkZGluZyAvIDIsIG1heCA9IGMgKyBzIC0gcGFkZGluZyAvIDI7XHJcbiAgICAgICAgcm9vdC5taW5WYXIuZGVzaXJlZFBvc2l0aW9uID0gbWluO1xyXG4gICAgICAgIGFkZChmLm1ha2VSZWN0KG9wZW4sIGNsb3NlLCBtaW4sIHBhZGRpbmcpLCByb290Lm1pblZhcik7XHJcbiAgICAgICAgcm9vdC5tYXhWYXIuZGVzaXJlZFBvc2l0aW9uID0gbWF4O1xyXG4gICAgICAgIGFkZChmLm1ha2VSZWN0KG9wZW4sIGNsb3NlLCBtYXgsIHBhZGRpbmcpLCByb290Lm1heFZhcik7XHJcbiAgICB9XHJcbiAgICBpZiAobG4pXHJcbiAgICAgICAgcm9vdC5sZWF2ZXMuZm9yRWFjaChmdW5jdGlvbiAobCkgeyByZXR1cm4gYWRkKGwuYm91bmRzLCBsLnZhcmlhYmxlKTsgfSk7XHJcbiAgICBpZiAoZ24pXHJcbiAgICAgICAgcm9vdC5ncm91cHMuZm9yRWFjaChmdW5jdGlvbiAoZykge1xyXG4gICAgICAgICAgICB2YXIgYiA9IGcuYm91bmRzO1xyXG4gICAgICAgICAgICBhZGQoZi5tYWtlUmVjdChmLmdldE9wZW4oYiksIGYuZ2V0Q2xvc2UoYiksIGYuZ2V0Q2VudHJlKGIpLCBmLmdldFNpemUoYikpLCBnLm1pblZhcik7XHJcbiAgICAgICAgfSk7XHJcbiAgICB2YXIgY3MgPSBnZW5lcmF0ZUNvbnN0cmFpbnRzKHJzLCB2cywgZiwgbWluU2VwKTtcclxuICAgIGlmIChnbikge1xyXG4gICAgICAgIHZzLmZvckVhY2goZnVuY3Rpb24gKHYpIHsgdi5jT3V0ID0gW10sIHYuY0luID0gW107IH0pO1xyXG4gICAgICAgIGNzLmZvckVhY2goZnVuY3Rpb24gKGMpIHsgYy5sZWZ0LmNPdXQucHVzaChjKSwgYy5yaWdodC5jSW4ucHVzaChjKTsgfSk7XHJcbiAgICAgICAgcm9vdC5ncm91cHMuZm9yRWFjaChmdW5jdGlvbiAoZykge1xyXG4gICAgICAgICAgICB2YXIgZ2FwQWRqdXN0bWVudCA9IChnLnBhZGRpbmcgLSBmLmdldFNpemUoZy5ib3VuZHMpKSAvIDI7XHJcbiAgICAgICAgICAgIGcubWluVmFyLmNJbi5mb3JFYWNoKGZ1bmN0aW9uIChjKSB7IHJldHVybiBjLmdhcCArPSBnYXBBZGp1c3RtZW50OyB9KTtcclxuICAgICAgICAgICAgZy5taW5WYXIuY091dC5mb3JFYWNoKGZ1bmN0aW9uIChjKSB7IGMubGVmdCA9IGcubWF4VmFyOyBjLmdhcCArPSBnYXBBZGp1c3RtZW50OyB9KTtcclxuICAgICAgICB9KTtcclxuICAgIH1cclxuICAgIHJldHVybiBjaGlsZENvbnN0cmFpbnRzLmNvbmNhdChjcyk7XHJcbn1cclxuZnVuY3Rpb24gZ2VuZXJhdGVDb25zdHJhaW50cyhycywgdmFycywgcmVjdCwgbWluU2VwKSB7XHJcbiAgICB2YXIgaSwgbiA9IHJzLmxlbmd0aDtcclxuICAgIHZhciBOID0gMiAqIG47XHJcbiAgICBjb25zb2xlLmFzc2VydCh2YXJzLmxlbmd0aCA+PSBuKTtcclxuICAgIHZhciBldmVudHMgPSBuZXcgQXJyYXkoTik7XHJcbiAgICBmb3IgKGkgPSAwOyBpIDwgbjsgKytpKSB7XHJcbiAgICAgICAgdmFyIHIgPSByc1tpXTtcclxuICAgICAgICB2YXIgdiA9IG5ldyBOb2RlKHZhcnNbaV0sIHIsIHJlY3QuZ2V0Q2VudHJlKHIpKTtcclxuICAgICAgICBldmVudHNbaV0gPSBuZXcgRXZlbnQodHJ1ZSwgdiwgcmVjdC5nZXRPcGVuKHIpKTtcclxuICAgICAgICBldmVudHNbaSArIG5dID0gbmV3IEV2ZW50KGZhbHNlLCB2LCByZWN0LmdldENsb3NlKHIpKTtcclxuICAgIH1cclxuICAgIGV2ZW50cy5zb3J0KGNvbXBhcmVFdmVudHMpO1xyXG4gICAgdmFyIGNzID0gbmV3IEFycmF5KCk7XHJcbiAgICB2YXIgc2NhbmxpbmUgPSBtYWtlUkJUcmVlKCk7XHJcbiAgICBmb3IgKGkgPSAwOyBpIDwgTjsgKytpKSB7XHJcbiAgICAgICAgdmFyIGUgPSBldmVudHNbaV07XHJcbiAgICAgICAgdmFyIHYgPSBlLnY7XHJcbiAgICAgICAgaWYgKGUuaXNPcGVuKSB7XHJcbiAgICAgICAgICAgIHNjYW5saW5lLmluc2VydCh2KTtcclxuICAgICAgICAgICAgcmVjdC5maW5kTmVpZ2hib3Vycyh2LCBzY2FubGluZSk7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIGVsc2Uge1xyXG4gICAgICAgICAgICBzY2FubGluZS5yZW1vdmUodik7XHJcbiAgICAgICAgICAgIHZhciBtYWtlQ29uc3RyYWludCA9IGZ1bmN0aW9uIChsLCByKSB7XHJcbiAgICAgICAgICAgICAgICB2YXIgc2VwID0gKHJlY3QuZ2V0U2l6ZShsLnIpICsgcmVjdC5nZXRTaXplKHIucikpIC8gMiArIG1pblNlcDtcclxuICAgICAgICAgICAgICAgIGNzLnB1c2gobmV3IHZwc2NfMS5Db25zdHJhaW50KGwudiwgci52LCBzZXApKTtcclxuICAgICAgICAgICAgfTtcclxuICAgICAgICAgICAgdmFyIHZpc2l0TmVpZ2hib3VycyA9IGZ1bmN0aW9uIChmb3J3YXJkLCByZXZlcnNlLCBta2Nvbikge1xyXG4gICAgICAgICAgICAgICAgdmFyIHUsIGl0ID0gdltmb3J3YXJkXS5pdGVyYXRvcigpO1xyXG4gICAgICAgICAgICAgICAgd2hpbGUgKCh1ID0gaXRbZm9yd2FyZF0oKSkgIT09IG51bGwpIHtcclxuICAgICAgICAgICAgICAgICAgICBta2Nvbih1LCB2KTtcclxuICAgICAgICAgICAgICAgICAgICB1W3JldmVyc2VdLnJlbW92ZSh2KTtcclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgfTtcclxuICAgICAgICAgICAgdmlzaXROZWlnaGJvdXJzKFwicHJldlwiLCBcIm5leHRcIiwgZnVuY3Rpb24gKHUsIHYpIHsgcmV0dXJuIG1ha2VDb25zdHJhaW50KHUsIHYpOyB9KTtcclxuICAgICAgICAgICAgdmlzaXROZWlnaGJvdXJzKFwibmV4dFwiLCBcInByZXZcIiwgZnVuY3Rpb24gKHUsIHYpIHsgcmV0dXJuIG1ha2VDb25zdHJhaW50KHYsIHUpOyB9KTtcclxuICAgICAgICB9XHJcbiAgICB9XHJcbiAgICBjb25zb2xlLmFzc2VydChzY2FubGluZS5zaXplID09PSAwKTtcclxuICAgIHJldHVybiBjcztcclxufVxyXG5mdW5jdGlvbiBmaW5kWE5laWdoYm91cnModiwgc2NhbmxpbmUpIHtcclxuICAgIHZhciBmID0gZnVuY3Rpb24gKGZvcndhcmQsIHJldmVyc2UpIHtcclxuICAgICAgICB2YXIgaXQgPSBzY2FubGluZS5maW5kSXRlcih2KTtcclxuICAgICAgICB2YXIgdTtcclxuICAgICAgICB3aGlsZSAoKHUgPSBpdFtmb3J3YXJkXSgpKSAhPT0gbnVsbCkge1xyXG4gICAgICAgICAgICB2YXIgdW92ZXJ2WCA9IHUuci5vdmVybGFwWCh2LnIpO1xyXG4gICAgICAgICAgICBpZiAodW92ZXJ2WCA8PSAwIHx8IHVvdmVydlggPD0gdS5yLm92ZXJsYXBZKHYucikpIHtcclxuICAgICAgICAgICAgICAgIHZbZm9yd2FyZF0uaW5zZXJ0KHUpO1xyXG4gICAgICAgICAgICAgICAgdVtyZXZlcnNlXS5pbnNlcnQodik7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgaWYgKHVvdmVydlggPD0gMCkge1xyXG4gICAgICAgICAgICAgICAgYnJlYWs7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICB9XHJcbiAgICB9O1xyXG4gICAgZihcIm5leHRcIiwgXCJwcmV2XCIpO1xyXG4gICAgZihcInByZXZcIiwgXCJuZXh0XCIpO1xyXG59XHJcbmZ1bmN0aW9uIGZpbmRZTmVpZ2hib3Vycyh2LCBzY2FubGluZSkge1xyXG4gICAgdmFyIGYgPSBmdW5jdGlvbiAoZm9yd2FyZCwgcmV2ZXJzZSkge1xyXG4gICAgICAgIHZhciB1ID0gc2NhbmxpbmUuZmluZEl0ZXIodilbZm9yd2FyZF0oKTtcclxuICAgICAgICBpZiAodSAhPT0gbnVsbCAmJiB1LnIub3ZlcmxhcFgodi5yKSA+IDApIHtcclxuICAgICAgICAgICAgdltmb3J3YXJkXS5pbnNlcnQodSk7XHJcbiAgICAgICAgICAgIHVbcmV2ZXJzZV0uaW5zZXJ0KHYpO1xyXG4gICAgICAgIH1cclxuICAgIH07XHJcbiAgICBmKFwibmV4dFwiLCBcInByZXZcIik7XHJcbiAgICBmKFwicHJldlwiLCBcIm5leHRcIik7XHJcbn1cclxuZnVuY3Rpb24gZ2VuZXJhdGVYQ29uc3RyYWludHMocnMsIHZhcnMpIHtcclxuICAgIHJldHVybiBnZW5lcmF0ZUNvbnN0cmFpbnRzKHJzLCB2YXJzLCB4UmVjdCwgMWUtNik7XHJcbn1cclxuZXhwb3J0cy5nZW5lcmF0ZVhDb25zdHJhaW50cyA9IGdlbmVyYXRlWENvbnN0cmFpbnRzO1xyXG5mdW5jdGlvbiBnZW5lcmF0ZVlDb25zdHJhaW50cyhycywgdmFycykge1xyXG4gICAgcmV0dXJuIGdlbmVyYXRlQ29uc3RyYWludHMocnMsIHZhcnMsIHlSZWN0LCAxZS02KTtcclxufVxyXG5leHBvcnRzLmdlbmVyYXRlWUNvbnN0cmFpbnRzID0gZ2VuZXJhdGVZQ29uc3RyYWludHM7XHJcbmZ1bmN0aW9uIGdlbmVyYXRlWEdyb3VwQ29uc3RyYWludHMocm9vdCkge1xyXG4gICAgcmV0dXJuIGdlbmVyYXRlR3JvdXBDb25zdHJhaW50cyhyb290LCB4UmVjdCwgMWUtNik7XHJcbn1cclxuZXhwb3J0cy5nZW5lcmF0ZVhHcm91cENvbnN0cmFpbnRzID0gZ2VuZXJhdGVYR3JvdXBDb25zdHJhaW50cztcclxuZnVuY3Rpb24gZ2VuZXJhdGVZR3JvdXBDb25zdHJhaW50cyhyb290KSB7XHJcbiAgICByZXR1cm4gZ2VuZXJhdGVHcm91cENvbnN0cmFpbnRzKHJvb3QsIHlSZWN0LCAxZS02KTtcclxufVxyXG5leHBvcnRzLmdlbmVyYXRlWUdyb3VwQ29uc3RyYWludHMgPSBnZW5lcmF0ZVlHcm91cENvbnN0cmFpbnRzO1xyXG5mdW5jdGlvbiByZW1vdmVPdmVybGFwcyhycykge1xyXG4gICAgdmFyIHZzID0gcnMubWFwKGZ1bmN0aW9uIChyKSB7IHJldHVybiBuZXcgdnBzY18xLlZhcmlhYmxlKHIuY3goKSk7IH0pO1xyXG4gICAgdmFyIGNzID0gZ2VuZXJhdGVYQ29uc3RyYWludHMocnMsIHZzKTtcclxuICAgIHZhciBzb2x2ZXIgPSBuZXcgdnBzY18xLlNvbHZlcih2cywgY3MpO1xyXG4gICAgc29sdmVyLnNvbHZlKCk7XHJcbiAgICB2cy5mb3JFYWNoKGZ1bmN0aW9uICh2LCBpKSB7IHJldHVybiByc1tpXS5zZXRYQ2VudHJlKHYucG9zaXRpb24oKSk7IH0pO1xyXG4gICAgdnMgPSBycy5tYXAoZnVuY3Rpb24gKHIpIHsgcmV0dXJuIG5ldyB2cHNjXzEuVmFyaWFibGUoci5jeSgpKTsgfSk7XHJcbiAgICBjcyA9IGdlbmVyYXRlWUNvbnN0cmFpbnRzKHJzLCB2cyk7XHJcbiAgICBzb2x2ZXIgPSBuZXcgdnBzY18xLlNvbHZlcih2cywgY3MpO1xyXG4gICAgc29sdmVyLnNvbHZlKCk7XHJcbiAgICB2cy5mb3JFYWNoKGZ1bmN0aW9uICh2LCBpKSB7IHJldHVybiByc1tpXS5zZXRZQ2VudHJlKHYucG9zaXRpb24oKSk7IH0pO1xyXG59XHJcbmV4cG9ydHMucmVtb3ZlT3ZlcmxhcHMgPSByZW1vdmVPdmVybGFwcztcclxudmFyIEluZGV4ZWRWYXJpYWJsZSA9IChmdW5jdGlvbiAoX3N1cGVyKSB7XHJcbiAgICBfX2V4dGVuZHMoSW5kZXhlZFZhcmlhYmxlLCBfc3VwZXIpO1xyXG4gICAgZnVuY3Rpb24gSW5kZXhlZFZhcmlhYmxlKGluZGV4LCB3KSB7XHJcbiAgICAgICAgdmFyIF90aGlzID0gX3N1cGVyLmNhbGwodGhpcywgMCwgdykgfHwgdGhpcztcclxuICAgICAgICBfdGhpcy5pbmRleCA9IGluZGV4O1xyXG4gICAgICAgIHJldHVybiBfdGhpcztcclxuICAgIH1cclxuICAgIHJldHVybiBJbmRleGVkVmFyaWFibGU7XHJcbn0odnBzY18xLlZhcmlhYmxlKSk7XHJcbmV4cG9ydHMuSW5kZXhlZFZhcmlhYmxlID0gSW5kZXhlZFZhcmlhYmxlO1xyXG52YXIgUHJvamVjdGlvbiA9IChmdW5jdGlvbiAoKSB7XHJcbiAgICBmdW5jdGlvbiBQcm9qZWN0aW9uKG5vZGVzLCBncm91cHMsIHJvb3RHcm91cCwgY29uc3RyYWludHMsIGF2b2lkT3ZlcmxhcHMpIHtcclxuICAgICAgICB2YXIgX3RoaXMgPSB0aGlzO1xyXG4gICAgICAgIGlmIChyb290R3JvdXAgPT09IHZvaWQgMCkgeyByb290R3JvdXAgPSBudWxsOyB9XHJcbiAgICAgICAgaWYgKGNvbnN0cmFpbnRzID09PSB2b2lkIDApIHsgY29uc3RyYWludHMgPSBudWxsOyB9XHJcbiAgICAgICAgaWYgKGF2b2lkT3ZlcmxhcHMgPT09IHZvaWQgMCkgeyBhdm9pZE92ZXJsYXBzID0gZmFsc2U7IH1cclxuICAgICAgICB0aGlzLm5vZGVzID0gbm9kZXM7XHJcbiAgICAgICAgdGhpcy5ncm91cHMgPSBncm91cHM7XHJcbiAgICAgICAgdGhpcy5yb290R3JvdXAgPSByb290R3JvdXA7XHJcbiAgICAgICAgdGhpcy5hdm9pZE92ZXJsYXBzID0gYXZvaWRPdmVybGFwcztcclxuICAgICAgICB0aGlzLnZhcmlhYmxlcyA9IG5vZGVzLm1hcChmdW5jdGlvbiAodiwgaSkge1xyXG4gICAgICAgICAgICByZXR1cm4gdi52YXJpYWJsZSA9IG5ldyBJbmRleGVkVmFyaWFibGUoaSwgMSk7XHJcbiAgICAgICAgfSk7XHJcbiAgICAgICAgaWYgKGNvbnN0cmFpbnRzKVxyXG4gICAgICAgICAgICB0aGlzLmNyZWF0ZUNvbnN0cmFpbnRzKGNvbnN0cmFpbnRzKTtcclxuICAgICAgICBpZiAoYXZvaWRPdmVybGFwcyAmJiByb290R3JvdXAgJiYgdHlwZW9mIHJvb3RHcm91cC5ncm91cHMgIT09ICd1bmRlZmluZWQnKSB7XHJcbiAgICAgICAgICAgIG5vZGVzLmZvckVhY2goZnVuY3Rpb24gKHYpIHtcclxuICAgICAgICAgICAgICAgIGlmICghdi53aWR0aCB8fCAhdi5oZWlnaHQpIHtcclxuICAgICAgICAgICAgICAgICAgICB2LmJvdW5kcyA9IG5ldyBSZWN0YW5nbGUodi54LCB2LngsIHYueSwgdi55KTtcclxuICAgICAgICAgICAgICAgICAgICByZXR1cm47XHJcbiAgICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgICAgICB2YXIgdzIgPSB2LndpZHRoIC8gMiwgaDIgPSB2LmhlaWdodCAvIDI7XHJcbiAgICAgICAgICAgICAgICB2LmJvdW5kcyA9IG5ldyBSZWN0YW5nbGUodi54IC0gdzIsIHYueCArIHcyLCB2LnkgLSBoMiwgdi55ICsgaDIpO1xyXG4gICAgICAgICAgICB9KTtcclxuICAgICAgICAgICAgY29tcHV0ZUdyb3VwQm91bmRzKHJvb3RHcm91cCk7XHJcbiAgICAgICAgICAgIHZhciBpID0gbm9kZXMubGVuZ3RoO1xyXG4gICAgICAgICAgICBncm91cHMuZm9yRWFjaChmdW5jdGlvbiAoZykge1xyXG4gICAgICAgICAgICAgICAgX3RoaXMudmFyaWFibGVzW2ldID0gZy5taW5WYXIgPSBuZXcgSW5kZXhlZFZhcmlhYmxlKGkrKywgdHlwZW9mIGcuc3RpZmZuZXNzICE9PSBcInVuZGVmaW5lZFwiID8gZy5zdGlmZm5lc3MgOiAwLjAxKTtcclxuICAgICAgICAgICAgICAgIF90aGlzLnZhcmlhYmxlc1tpXSA9IGcubWF4VmFyID0gbmV3IEluZGV4ZWRWYXJpYWJsZShpKyssIHR5cGVvZiBnLnN0aWZmbmVzcyAhPT0gXCJ1bmRlZmluZWRcIiA/IGcuc3RpZmZuZXNzIDogMC4wMSk7XHJcbiAgICAgICAgICAgIH0pO1xyXG4gICAgICAgIH1cclxuICAgIH1cclxuICAgIFByb2plY3Rpb24ucHJvdG90eXBlLmNyZWF0ZVNlcGFyYXRpb24gPSBmdW5jdGlvbiAoYykge1xyXG4gICAgICAgIHJldHVybiBuZXcgdnBzY18xLkNvbnN0cmFpbnQodGhpcy5ub2Rlc1tjLmxlZnRdLnZhcmlhYmxlLCB0aGlzLm5vZGVzW2MucmlnaHRdLnZhcmlhYmxlLCBjLmdhcCwgdHlwZW9mIGMuZXF1YWxpdHkgIT09IFwidW5kZWZpbmVkXCIgPyBjLmVxdWFsaXR5IDogZmFsc2UpO1xyXG4gICAgfTtcclxuICAgIFByb2plY3Rpb24ucHJvdG90eXBlLm1ha2VGZWFzaWJsZSA9IGZ1bmN0aW9uIChjKSB7XHJcbiAgICAgICAgdmFyIF90aGlzID0gdGhpcztcclxuICAgICAgICBpZiAoIXRoaXMuYXZvaWRPdmVybGFwcylcclxuICAgICAgICAgICAgcmV0dXJuO1xyXG4gICAgICAgIHZhciBheGlzID0gJ3gnLCBkaW0gPSAnd2lkdGgnO1xyXG4gICAgICAgIGlmIChjLmF4aXMgPT09ICd4JylcclxuICAgICAgICAgICAgYXhpcyA9ICd5JywgZGltID0gJ2hlaWdodCc7XHJcbiAgICAgICAgdmFyIHZzID0gYy5vZmZzZXRzLm1hcChmdW5jdGlvbiAobykgeyByZXR1cm4gX3RoaXMubm9kZXNbby5ub2RlXTsgfSkuc29ydChmdW5jdGlvbiAoYSwgYikgeyByZXR1cm4gYVtheGlzXSAtIGJbYXhpc107IH0pO1xyXG4gICAgICAgIHZhciBwID0gbnVsbDtcclxuICAgICAgICB2cy5mb3JFYWNoKGZ1bmN0aW9uICh2KSB7XHJcbiAgICAgICAgICAgIGlmIChwKSB7XHJcbiAgICAgICAgICAgICAgICB2YXIgbmV4dFBvcyA9IHBbYXhpc10gKyBwW2RpbV07XHJcbiAgICAgICAgICAgICAgICBpZiAobmV4dFBvcyA+IHZbYXhpc10pIHtcclxuICAgICAgICAgICAgICAgICAgICB2W2F4aXNdID0gbmV4dFBvcztcclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICBwID0gdjtcclxuICAgICAgICB9KTtcclxuICAgIH07XHJcbiAgICBQcm9qZWN0aW9uLnByb3RvdHlwZS5jcmVhdGVBbGlnbm1lbnQgPSBmdW5jdGlvbiAoYykge1xyXG4gICAgICAgIHZhciBfdGhpcyA9IHRoaXM7XHJcbiAgICAgICAgdmFyIHUgPSB0aGlzLm5vZGVzW2Mub2Zmc2V0c1swXS5ub2RlXS52YXJpYWJsZTtcclxuICAgICAgICB0aGlzLm1ha2VGZWFzaWJsZShjKTtcclxuICAgICAgICB2YXIgY3MgPSBjLmF4aXMgPT09ICd4JyA/IHRoaXMueENvbnN0cmFpbnRzIDogdGhpcy55Q29uc3RyYWludHM7XHJcbiAgICAgICAgYy5vZmZzZXRzLnNsaWNlKDEpLmZvckVhY2goZnVuY3Rpb24gKG8pIHtcclxuICAgICAgICAgICAgdmFyIHYgPSBfdGhpcy5ub2Rlc1tvLm5vZGVdLnZhcmlhYmxlO1xyXG4gICAgICAgICAgICBjcy5wdXNoKG5ldyB2cHNjXzEuQ29uc3RyYWludCh1LCB2LCBvLm9mZnNldCwgdHJ1ZSkpO1xyXG4gICAgICAgIH0pO1xyXG4gICAgfTtcclxuICAgIFByb2plY3Rpb24ucHJvdG90eXBlLmNyZWF0ZUNvbnN0cmFpbnRzID0gZnVuY3Rpb24gKGNvbnN0cmFpbnRzKSB7XHJcbiAgICAgICAgdmFyIF90aGlzID0gdGhpcztcclxuICAgICAgICB2YXIgaXNTZXAgPSBmdW5jdGlvbiAoYykgeyByZXR1cm4gdHlwZW9mIGMudHlwZSA9PT0gJ3VuZGVmaW5lZCcgfHwgYy50eXBlID09PSAnc2VwYXJhdGlvbic7IH07XHJcbiAgICAgICAgdGhpcy54Q29uc3RyYWludHMgPSBjb25zdHJhaW50c1xyXG4gICAgICAgICAgICAuZmlsdGVyKGZ1bmN0aW9uIChjKSB7IHJldHVybiBjLmF4aXMgPT09IFwieFwiICYmIGlzU2VwKGMpOyB9KVxyXG4gICAgICAgICAgICAubWFwKGZ1bmN0aW9uIChjKSB7IHJldHVybiBfdGhpcy5jcmVhdGVTZXBhcmF0aW9uKGMpOyB9KTtcclxuICAgICAgICB0aGlzLnlDb25zdHJhaW50cyA9IGNvbnN0cmFpbnRzXHJcbiAgICAgICAgICAgIC5maWx0ZXIoZnVuY3Rpb24gKGMpIHsgcmV0dXJuIGMuYXhpcyA9PT0gXCJ5XCIgJiYgaXNTZXAoYyk7IH0pXHJcbiAgICAgICAgICAgIC5tYXAoZnVuY3Rpb24gKGMpIHsgcmV0dXJuIF90aGlzLmNyZWF0ZVNlcGFyYXRpb24oYyk7IH0pO1xyXG4gICAgICAgIGNvbnN0cmFpbnRzXHJcbiAgICAgICAgICAgIC5maWx0ZXIoZnVuY3Rpb24gKGMpIHsgcmV0dXJuIGMudHlwZSA9PT0gJ2FsaWdubWVudCc7IH0pXHJcbiAgICAgICAgICAgIC5mb3JFYWNoKGZ1bmN0aW9uIChjKSB7IHJldHVybiBfdGhpcy5jcmVhdGVBbGlnbm1lbnQoYyk7IH0pO1xyXG4gICAgfTtcclxuICAgIFByb2plY3Rpb24ucHJvdG90eXBlLnNldHVwVmFyaWFibGVzQW5kQm91bmRzID0gZnVuY3Rpb24gKHgwLCB5MCwgZGVzaXJlZCwgZ2V0RGVzaXJlZCkge1xyXG4gICAgICAgIHRoaXMubm9kZXMuZm9yRWFjaChmdW5jdGlvbiAodiwgaSkge1xyXG4gICAgICAgICAgICBpZiAodi5maXhlZCkge1xyXG4gICAgICAgICAgICAgICAgdi52YXJpYWJsZS53ZWlnaHQgPSB2LmZpeGVkV2VpZ2h0ID8gdi5maXhlZFdlaWdodCA6IDEwMDA7XHJcbiAgICAgICAgICAgICAgICBkZXNpcmVkW2ldID0gZ2V0RGVzaXJlZCh2KTtcclxuICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICBlbHNlIHtcclxuICAgICAgICAgICAgICAgIHYudmFyaWFibGUud2VpZ2h0ID0gMTtcclxuICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICB2YXIgdyA9ICh2LndpZHRoIHx8IDApIC8gMiwgaCA9ICh2LmhlaWdodCB8fCAwKSAvIDI7XHJcbiAgICAgICAgICAgIHZhciBpeCA9IHgwW2ldLCBpeSA9IHkwW2ldO1xyXG4gICAgICAgICAgICB2LmJvdW5kcyA9IG5ldyBSZWN0YW5nbGUoaXggLSB3LCBpeCArIHcsIGl5IC0gaCwgaXkgKyBoKTtcclxuICAgICAgICB9KTtcclxuICAgIH07XHJcbiAgICBQcm9qZWN0aW9uLnByb3RvdHlwZS54UHJvamVjdCA9IGZ1bmN0aW9uICh4MCwgeTAsIHgpIHtcclxuICAgICAgICBpZiAoIXRoaXMucm9vdEdyb3VwICYmICEodGhpcy5hdm9pZE92ZXJsYXBzIHx8IHRoaXMueENvbnN0cmFpbnRzKSlcclxuICAgICAgICAgICAgcmV0dXJuO1xyXG4gICAgICAgIHRoaXMucHJvamVjdCh4MCwgeTAsIHgwLCB4LCBmdW5jdGlvbiAodikgeyByZXR1cm4gdi5weDsgfSwgdGhpcy54Q29uc3RyYWludHMsIGdlbmVyYXRlWEdyb3VwQ29uc3RyYWludHMsIGZ1bmN0aW9uICh2KSB7IHJldHVybiB2LmJvdW5kcy5zZXRYQ2VudHJlKHhbdi52YXJpYWJsZS5pbmRleF0gPSB2LnZhcmlhYmxlLnBvc2l0aW9uKCkpOyB9LCBmdW5jdGlvbiAoZykge1xyXG4gICAgICAgICAgICB2YXIgeG1pbiA9IHhbZy5taW5WYXIuaW5kZXhdID0gZy5taW5WYXIucG9zaXRpb24oKTtcclxuICAgICAgICAgICAgdmFyIHhtYXggPSB4W2cubWF4VmFyLmluZGV4XSA9IGcubWF4VmFyLnBvc2l0aW9uKCk7XHJcbiAgICAgICAgICAgIHZhciBwMiA9IGcucGFkZGluZyAvIDI7XHJcbiAgICAgICAgICAgIGcuYm91bmRzLnggPSB4bWluIC0gcDI7XHJcbiAgICAgICAgICAgIGcuYm91bmRzLlggPSB4bWF4ICsgcDI7XHJcbiAgICAgICAgfSk7XHJcbiAgICB9O1xyXG4gICAgUHJvamVjdGlvbi5wcm90b3R5cGUueVByb2plY3QgPSBmdW5jdGlvbiAoeDAsIHkwLCB5KSB7XHJcbiAgICAgICAgaWYgKCF0aGlzLnJvb3RHcm91cCAmJiAhdGhpcy55Q29uc3RyYWludHMpXHJcbiAgICAgICAgICAgIHJldHVybjtcclxuICAgICAgICB0aGlzLnByb2plY3QoeDAsIHkwLCB5MCwgeSwgZnVuY3Rpb24gKHYpIHsgcmV0dXJuIHYucHk7IH0sIHRoaXMueUNvbnN0cmFpbnRzLCBnZW5lcmF0ZVlHcm91cENvbnN0cmFpbnRzLCBmdW5jdGlvbiAodikgeyByZXR1cm4gdi5ib3VuZHMuc2V0WUNlbnRyZSh5W3YudmFyaWFibGUuaW5kZXhdID0gdi52YXJpYWJsZS5wb3NpdGlvbigpKTsgfSwgZnVuY3Rpb24gKGcpIHtcclxuICAgICAgICAgICAgdmFyIHltaW4gPSB5W2cubWluVmFyLmluZGV4XSA9IGcubWluVmFyLnBvc2l0aW9uKCk7XHJcbiAgICAgICAgICAgIHZhciB5bWF4ID0geVtnLm1heFZhci5pbmRleF0gPSBnLm1heFZhci5wb3NpdGlvbigpO1xyXG4gICAgICAgICAgICB2YXIgcDIgPSBnLnBhZGRpbmcgLyAyO1xyXG4gICAgICAgICAgICBnLmJvdW5kcy55ID0geW1pbiAtIHAyO1xyXG4gICAgICAgICAgICA7XHJcbiAgICAgICAgICAgIGcuYm91bmRzLlkgPSB5bWF4ICsgcDI7XHJcbiAgICAgICAgfSk7XHJcbiAgICB9O1xyXG4gICAgUHJvamVjdGlvbi5wcm90b3R5cGUucHJvamVjdEZ1bmN0aW9ucyA9IGZ1bmN0aW9uICgpIHtcclxuICAgICAgICB2YXIgX3RoaXMgPSB0aGlzO1xyXG4gICAgICAgIHJldHVybiBbXHJcbiAgICAgICAgICAgIGZ1bmN0aW9uICh4MCwgeTAsIHgpIHsgcmV0dXJuIF90aGlzLnhQcm9qZWN0KHgwLCB5MCwgeCk7IH0sXHJcbiAgICAgICAgICAgIGZ1bmN0aW9uICh4MCwgeTAsIHkpIHsgcmV0dXJuIF90aGlzLnlQcm9qZWN0KHgwLCB5MCwgeSk7IH1cclxuICAgICAgICBdO1xyXG4gICAgfTtcclxuICAgIFByb2plY3Rpb24ucHJvdG90eXBlLnByb2plY3QgPSBmdW5jdGlvbiAoeDAsIHkwLCBzdGFydCwgZGVzaXJlZCwgZ2V0RGVzaXJlZCwgY3MsIGdlbmVyYXRlQ29uc3RyYWludHMsIHVwZGF0ZU5vZGVCb3VuZHMsIHVwZGF0ZUdyb3VwQm91bmRzKSB7XHJcbiAgICAgICAgdGhpcy5zZXR1cFZhcmlhYmxlc0FuZEJvdW5kcyh4MCwgeTAsIGRlc2lyZWQsIGdldERlc2lyZWQpO1xyXG4gICAgICAgIGlmICh0aGlzLnJvb3RHcm91cCAmJiB0aGlzLmF2b2lkT3ZlcmxhcHMpIHtcclxuICAgICAgICAgICAgY29tcHV0ZUdyb3VwQm91bmRzKHRoaXMucm9vdEdyb3VwKTtcclxuICAgICAgICAgICAgY3MgPSBjcy5jb25jYXQoZ2VuZXJhdGVDb25zdHJhaW50cyh0aGlzLnJvb3RHcm91cCkpO1xyXG4gICAgICAgIH1cclxuICAgICAgICB0aGlzLnNvbHZlKHRoaXMudmFyaWFibGVzLCBjcywgc3RhcnQsIGRlc2lyZWQpO1xyXG4gICAgICAgIHRoaXMubm9kZXMuZm9yRWFjaCh1cGRhdGVOb2RlQm91bmRzKTtcclxuICAgICAgICBpZiAodGhpcy5yb290R3JvdXAgJiYgdGhpcy5hdm9pZE92ZXJsYXBzKSB7XHJcbiAgICAgICAgICAgIHRoaXMuZ3JvdXBzLmZvckVhY2godXBkYXRlR3JvdXBCb3VuZHMpO1xyXG4gICAgICAgICAgICBjb21wdXRlR3JvdXBCb3VuZHModGhpcy5yb290R3JvdXApO1xyXG4gICAgICAgIH1cclxuICAgIH07XHJcbiAgICBQcm9qZWN0aW9uLnByb3RvdHlwZS5zb2x2ZSA9IGZ1bmN0aW9uICh2cywgY3MsIHN0YXJ0aW5nLCBkZXNpcmVkKSB7XHJcbiAgICAgICAgdmFyIHNvbHZlciA9IG5ldyB2cHNjXzEuU29sdmVyKHZzLCBjcyk7XHJcbiAgICAgICAgc29sdmVyLnNldFN0YXJ0aW5nUG9zaXRpb25zKHN0YXJ0aW5nKTtcclxuICAgICAgICBzb2x2ZXIuc2V0RGVzaXJlZFBvc2l0aW9ucyhkZXNpcmVkKTtcclxuICAgICAgICBzb2x2ZXIuc29sdmUoKTtcclxuICAgIH07XHJcbiAgICByZXR1cm4gUHJvamVjdGlvbjtcclxufSgpKTtcclxuZXhwb3J0cy5Qcm9qZWN0aW9uID0gUHJvamVjdGlvbjtcclxuLy8jIHNvdXJjZU1hcHBpbmdVUkw9ZGF0YTphcHBsaWNhdGlvbi9qc29uO2Jhc2U2NCxleUoyWlhKemFXOXVJam96TENKbWFXeGxJam9pY21WamRHRnVaMnhsTG1weklpd2ljMjkxY21ObFVtOXZkQ0k2SWlJc0luTnZkWEpqWlhNaU9sc2lMaTR2TGk0dlYyVmlRMjlzWVM5emNtTXZjbVZqZEdGdVoyeGxMblJ6SWwwc0ltNWhiV1Z6SWpwYlhTd2liV0Z3Y0dsdVozTWlPaUk3T3pzN096czdPenM3T3pzN096dEJRVUZCTEN0Q1FVRnRSRHRCUVVOdVJDeHRRMEZCSzBJN1FVRnJRak5DTEZOQlFXZENMR3RDUVVGclFpeERRVUZETEVOQlFXdENPMGxCUTJwRUxFTkJRVU1zUTBGQlF5eE5RVUZOTEVkQlFVY3NUMEZCVHl4RFFVRkRMRU5CUVVNc1RVRkJUU3hMUVVGTExGZEJRVmNzUTBGQlF5eERRVUZETzFGQlEzaERMRU5CUVVNc1EwRkJReXhOUVVGTkxFTkJRVU1zVFVGQlRTeERRVUZETEZWQlFVTXNRMEZCV1N4RlFVRkZMRU5CUVVNc1NVRkJTeXhQUVVGQkxFTkJRVU1zUTBGQlF5eE5RVUZOTEVOQlFVTXNTMEZCU3l4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGcVFpeERRVUZwUWl4RlFVRkZMRk5CUVZNc1EwRkJReXhMUVVGTExFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTTdVVUZETlVVc1UwRkJVeXhEUVVGRExFdEJRVXNzUlVGQlJTeERRVUZETzBsQlEzUkNMRWxCUVVrc1QwRkJUeXhEUVVGRExFTkJRVU1zVFVGQlRTeExRVUZMTEZkQlFWYzdVVUZETDBJc1EwRkJReXhEUVVGRExFMUJRVTBzUjBGQll5eERRVUZETEVOQlFVTXNUVUZCVFN4RFFVRkRMRTFCUVUwc1EwRkJReXhWUVVGRExFTkJRVmtzUlVGQlJTeERRVUZETEVsQlFVc3NUMEZCUVN4clFrRkJhMElzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4TFFVRkxMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRVGxDTEVOQlFUaENMRVZCUVVVc1EwRkJReXhEUVVGRExFMUJRVTBzUTBGQlF5eERRVUZETzBsQlEzcEhMRU5CUVVNc1EwRkJReXhOUVVGTkxFZEJRVWNzUTBGQlF5eERRVUZETEUxQlFVMHNRMEZCUXl4UFFVRlBMRU5CUVVNc1EwRkJReXhEUVVGRExFOUJRVThzUTBGQlF5eERRVUZETzBsQlEzWkRMRTlCUVU4c1EwRkJReXhEUVVGRExFMUJRVTBzUTBGQlF6dEJRVU53UWl4RFFVRkRPMEZCVWtRc1owUkJVVU03UVVGRlJEdEpRVU5KTEcxQ1FVTlhMRU5CUVZNc1JVRkRWQ3hEUVVGVExFVkJRMVFzUTBGQlV5eEZRVU5VTEVOQlFWTTdVVUZJVkN4TlFVRkRMRWRCUVVRc1EwRkJReXhEUVVGUk8xRkJRMVFzVFVGQlF5eEhRVUZFTEVOQlFVTXNRMEZCVVR0UlFVTlVMRTFCUVVNc1IwRkJSQ3hEUVVGRExFTkJRVkU3VVVGRFZDeE5RVUZETEVkQlFVUXNRMEZCUXl4RFFVRlJPMGxCUVVrc1EwRkJRenRKUVVWc1FpeGxRVUZMTEVkQlFWb3NZMEZCTkVJc1QwRkJUeXhKUVVGSkxGTkJRVk1zUTBGQlF5eE5RVUZOTEVOQlFVTXNhVUpCUVdsQ0xFVkJRVVVzVFVGQlRTeERRVUZETEdsQ1FVRnBRaXhGUVVGRkxFMUJRVTBzUTBGQlF5eHBRa0ZCYVVJc1JVRkJSU3hOUVVGTkxFTkJRVU1zYVVKQlFXbENMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03U1VGRk0wb3NjMEpCUVVVc1IwRkJSaXhqUVVGbExFOUJRVThzUTBGQlF5eEpRVUZKTEVOQlFVTXNRMEZCUXl4SFFVRkhMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMGxCUlRsRExITkNRVUZGTEVkQlFVWXNZMEZCWlN4UFFVRlBMRU5CUVVNc1NVRkJTU3hEUVVGRExFTkJRVU1zUjBGQlJ5eEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dEpRVVU1UXl3MFFrRkJVU3hIUVVGU0xGVkJRVk1zUTBGQldUdFJRVU5xUWl4SlFVRkpMRVZCUVVVc1IwRkJSeXhKUVVGSkxFTkJRVU1zUlVGQlJTeEZRVUZGTEVWQlFVVXNSVUZCUlN4SFFVRkhMRU5CUVVNc1EwRkJReXhGUVVGRkxFVkJRVVVzUTBGQlF6dFJRVU5vUXl4SlFVRkpMRVZCUVVVc1NVRkJTU3hGUVVGRkxFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4SlFVRkpMRU5CUVVNc1EwRkJRenRaUVVGRkxFOUJRVThzU1VGQlNTeERRVUZETEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8xRkJRMnhFTEVsQlFVa3NSVUZCUlN4SlFVRkpMRVZCUVVVc1NVRkJTU3hKUVVGSkxFTkJRVU1zUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXl4RFFVRkRPMWxCUVVVc1QwRkJUeXhEUVVGRExFTkJRVU1zUTBGQlF5eEhRVUZITEVsQlFVa3NRMEZCUXl4RFFVRkRMRU5CUVVNN1VVRkRiRVFzVDBGQlR5eERRVUZETEVOQlFVTTdTVUZEWWl4RFFVRkRPMGxCUlVRc05FSkJRVkVzUjBGQlVpeFZRVUZUTEVOQlFWazdVVUZEYWtJc1NVRkJTU3hGUVVGRkxFZEJRVWNzU1VGQlNTeERRVUZETEVWQlFVVXNSVUZCUlN4RlFVRkZMRVZCUVVVc1IwRkJSeXhEUVVGRExFTkJRVU1zUlVGQlJTeEZRVUZGTEVOQlFVTTdVVUZEYUVNc1NVRkJTU3hGUVVGRkxFbEJRVWtzUlVGQlJTeEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1NVRkJTU3hEUVVGRExFTkJRVU03V1VGQlJTeFBRVUZQTEVsQlFVa3NRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFJRVU5zUkN4SlFVRkpMRVZCUVVVc1NVRkJTU3hGUVVGRkxFbEJRVWtzU1VGQlNTeERRVUZETEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJRenRaUVVGRkxFOUJRVThzUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4SlFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRE8xRkJRMnhFTEU5QlFVOHNRMEZCUXl4RFFVRkRPMGxCUTJJc1EwRkJRenRKUVVWRUxEaENRVUZWTEVkQlFWWXNWVUZCVnl4RlFVRlZPMUZCUTJwQ0xFbEJRVWtzUlVGQlJTeEhRVUZITEVWQlFVVXNSMEZCUnl4SlFVRkpMRU5CUVVNc1JVRkJSU3hGUVVGRkxFTkJRVU03VVVGRGVFSXNTVUZCU1N4RFFVRkRMRU5CUVVNc1NVRkJTU3hGUVVGRkxFTkJRVU03VVVGRFlpeEpRVUZKTEVOQlFVTXNRMEZCUXl4SlFVRkpMRVZCUVVVc1EwRkJRenRKUVVOcVFpeERRVUZETzBsQlJVUXNPRUpCUVZVc1IwRkJWaXhWUVVGWExFVkJRVlU3VVVGRGFrSXNTVUZCU1N4RlFVRkZMRWRCUVVjc1JVRkJSU3hIUVVGSExFbEJRVWtzUTBGQlF5eEZRVUZGTEVWQlFVVXNRMEZCUXp0UlFVTjRRaXhKUVVGSkxFTkJRVU1zUTBGQlF5eEpRVUZKTEVWQlFVVXNRMEZCUXp0UlFVTmlMRWxCUVVrc1EwRkJReXhEUVVGRExFbEJRVWtzUlVGQlJTeERRVUZETzBsQlEycENMRU5CUVVNN1NVRkZSQ3g1UWtGQlN5eEhRVUZNTzFGQlEwa3NUMEZCVHl4SlFVRkpMRU5CUVVNc1EwRkJReXhIUVVGSExFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTTdTVUZETTBJc1EwRkJRenRKUVVWRUxEQkNRVUZOTEVkQlFVNDdVVUZEU1N4UFFVRlBMRWxCUVVrc1EwRkJReXhEUVVGRExFZEJRVWNzU1VGQlNTeERRVUZETEVOQlFVTXNRMEZCUXp0SlFVTXpRaXhEUVVGRE8wbEJSVVFzZVVKQlFVc3NSMEZCVEN4VlFVRk5MRU5CUVZrN1VVRkRaQ3hQUVVGUExFbEJRVWtzVTBGQlV5eERRVUZETEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1NVRkJTU3hEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUVVVc1NVRkJTU3hEUVVGRExFZEJRVWNzUTBGQlF5eEpRVUZKTEVOQlFVTXNRMEZCUXl4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQlJTeEpRVUZKTEVOQlFVTXNSMEZCUnl4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RlFVRkZMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zU1VGQlNTeERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dEpRVU55U0N4RFFVRkRPMGxCVjBRc2NVTkJRV2xDTEVkQlFXcENMRlZCUVd0Q0xFVkJRVlVzUlVGQlJTeEZRVUZWTEVWQlFVVXNSVUZCVlN4RlFVRkZMRVZCUVZVN1VVRkROVVFzU1VGQlNTeExRVUZMTEVkQlFVY3NRMEZCUXl4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRExFVkJRVVVzU1VGQlNTeERRVUZETEVOQlFVTXNSVUZCUlN4SlFVRkpMRU5CUVVNc1EwRkJReXhGUVVGRkxFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTTdXVUZEY2tNc1EwRkJReXhKUVVGSkxFTkJRVU1zUTBGQlF5eEZRVUZGTEVsQlFVa3NRMEZCUXl4RFFVRkRMRVZCUVVVc1NVRkJTU3hEUVVGRExFTkJRVU1zUlVGQlJTeEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRPMWxCUTJoRExFTkJRVU1zU1VGQlNTeERRVUZETEVOQlFVTXNSVUZCUlN4SlFVRkpMRU5CUVVNc1EwRkJReXhGUVVGRkxFbEJRVWtzUTBGQlF5eERRVUZETEVWQlFVVXNTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJRenRaUVVOd1F5eERRVUZETEVsQlFVa3NRMEZCUXl4RFFVRkRMRVZCUVVVc1NVRkJTU3hEUVVGRExFTkJRVU1zUlVGQlJTeEpRVUZKTEVOQlFVTXNRMEZCUXl4RlFVRkZMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzFGQlEzUkRMRWxCUVVrc1lVRkJZU3hIUVVGSExFVkJRVVVzUTBGQlF6dFJRVU4yUWl4TFFVRkxMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NRMEZCUXl4RlFVRkZMRVZCUVVVc1EwRkJReXhGUVVGRk8xbEJRM2hDTEVsQlFVa3NRMEZCUXl4SFFVRkhMRk5CUVZNc1EwRkJReXhuUWtGQlowSXNRMEZCUXl4RlFVRkZMRVZCUVVVc1JVRkJSU3hGUVVGRkxFVkJRVVVzUlVGQlJTeEZRVUZGTEVWQlFVVXNTMEZCU3l4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEZRVUZGTEV0QlFVc3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQlJTeExRVUZMTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRVVVzUzBGQlN5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03V1VGRGRrY3NTVUZCU1N4RFFVRkRMRXRCUVVzc1NVRkJTVHRuUWtGQlJTeGhRVUZoTEVOQlFVTXNTVUZCU1N4RFFVRkRMRVZCUVVVc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETzFOQlF6RkVPMUZCUTBRc1QwRkJUeXhoUVVGaExFTkJRVU03U1VGRGVrSXNRMEZCUXp0SlFWVkVMRzFEUVVGbExFZEJRV1lzVlVGQlowSXNSVUZCVlN4RlFVRkZMRVZCUVZVN1VVRkRiRU1zU1VGQlNTeEpRVUZKTEVkQlFVY3NTVUZCU1N4RFFVRkRMR2xDUVVGcFFpeERRVUZETEVsQlFVa3NRMEZCUXl4RlFVRkZMRVZCUVVVc1JVRkJSU3hKUVVGSkxFTkJRVU1zUlVGQlJTeEZRVUZGTEVWQlFVVXNSVUZCUlN4RlFVRkZMRVZCUVVVc1EwRkJReXhEUVVGRE8xRkJRMmhGTEU5QlFVOHNTVUZCU1N4RFFVRkRMRTFCUVUwc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVsQlFVa3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zU1VGQlNTeERRVUZETzBsQlF6VkRMRU5CUVVNN1NVRkZSQ3cwUWtGQlVTeEhRVUZTTzFGQlEwa3NUMEZCVHp0WlFVTklMRVZCUVVVc1EwRkJReXhGUVVGRkxFbEJRVWtzUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4RlFVRkZMRWxCUVVrc1EwRkJReXhEUVVGRExFVkJRVVU3V1VGRGVFSXNSVUZCUlN4RFFVRkRMRVZCUVVVc1NVRkJTU3hEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVWQlFVVXNTVUZCU1N4RFFVRkRMRU5CUVVNc1JVRkJSVHRaUVVONFFpeEZRVUZGTEVOQlFVTXNSVUZCUlN4SlFVRkpMRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU1zUlVGQlJTeEpRVUZKTEVOQlFVTXNRMEZCUXl4RlFVRkZPMWxCUTNoQ0xFVkJRVVVzUTBGQlF5eEZRVUZGTEVsQlFVa3NRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhGUVVGRkxFbEJRVWtzUTBGQlF5eERRVUZETEVWQlFVVTdVMEZCUXl4RFFVRkRPMGxCUTJ4RExFTkJRVU03U1VGRlRTd3dRa0ZCWjBJc1IwRkJka0lzVlVGRFNTeEZRVUZWTEVWQlFVVXNSVUZCVlN4RlFVTjBRaXhGUVVGVkxFVkJRVVVzUlVGQlZTeEZRVU4wUWl4RlFVRlZMRVZCUVVVc1JVRkJWU3hGUVVOMFFpeEZRVUZWTEVWQlFVVXNSVUZCVlR0UlFVTjBRaXhKUVVGSkxFbEJRVWtzUjBGQlJ5eEZRVUZGTEVkQlFVY3NSVUZCUlN4RlFVRkZMRWxCUVVrc1IwRkJSeXhGUVVGRkxFZEJRVWNzUlVGQlJTeEZRVU01UWl4SlFVRkpMRWRCUVVjc1JVRkJSU3hIUVVGSExFVkJRVVVzUlVGQlJTeEpRVUZKTEVkQlFVY3NSVUZCUlN4SFFVRkhMRVZCUVVVc1JVRkRPVUlzVjBGQlZ5eEhRVUZITEVsQlFVa3NSMEZCUnl4SlFVRkpMRWRCUVVjc1NVRkJTU3hIUVVGSExFbEJRVWtzUTBGQlF6dFJRVU0xUXl4SlFVRkpMRmRCUVZjc1NVRkJTU3hEUVVGRE8xbEJRVVVzVDBGQlR5eEpRVUZKTEVOQlFVTTdVVUZEYkVNc1NVRkJTU3hKUVVGSkxFZEJRVWNzUlVGQlJTeEhRVUZITEVWQlFVVXNSVUZCUlN4SlFVRkpMRWRCUVVjc1JVRkJSU3hIUVVGSExFVkJRVVVzUlVGRE9VSXNTVUZCU1N4SFFVRkhMRWxCUVVrc1IwRkJSeXhKUVVGSkxFZEJRVWNzU1VGQlNTeEhRVUZITEVsQlFVa3NSVUZEYUVNc1EwRkJReXhIUVVGSExFbEJRVWtzUjBGQlJ5eFhRVUZYTEVWQlEzUkNMRWxCUVVrc1IwRkJSeXhKUVVGSkxFZEJRVWNzU1VGQlNTeEhRVUZITEVsQlFVa3NSMEZCUnl4SlFVRkpMRVZCUTJoRExFTkJRVU1zUjBGQlJ5eEpRVUZKTEVkQlFVY3NWMEZCVnl4RFFVRkRPMUZCUXpOQ0xFbEJRVWtzUTBGQlF5eEpRVUZKTEVOQlFVTXNTVUZCU1N4RFFVRkRMRWxCUVVrc1EwRkJReXhKUVVGSkxFTkJRVU1zU1VGQlNTeERRVUZETEVsQlFVa3NRMEZCUXl4SlFVRkpMRU5CUVVNc1JVRkJSVHRaUVVOMFF5eFBRVUZQTzJkQ1FVTklMRU5CUVVNc1JVRkJSU3hGUVVGRkxFZEJRVWNzUTBGQlF5eEhRVUZITEVsQlFVazdaMEpCUTJoQ0xFTkJRVU1zUlVGQlJTeEZRVUZGTEVkQlFVY3NRMEZCUXl4SFFVRkhMRWxCUVVrN1lVRkRia0lzUTBGQlF6dFRRVU5NTzFGQlEwUXNUMEZCVHl4SlFVRkpMRU5CUVVNN1NVRkRhRUlzUTBGQlF6dEpRVVZFTERKQ1FVRlBMRWRCUVZBc1ZVRkJVU3hIUVVGWE8xRkJRMllzVDBGQlR5eEpRVUZKTEZOQlFWTXNRMEZCUXl4SlFVRkpMRU5CUVVNc1EwRkJReXhIUVVGSExFZEJRVWNzUlVGQlJTeEpRVUZKTEVOQlFVTXNRMEZCUXl4SFFVRkhMRWRCUVVjc1JVRkJSU3hKUVVGSkxFTkJRVU1zUTBGQlF5eEhRVUZITEVkQlFVY3NSVUZCUlN4SlFVRkpMRU5CUVVNc1EwRkJReXhIUVVGSExFZEJRVWNzUTBGQlF5eERRVUZETzBsQlEycEdMRU5CUVVNN1NVRkRUQ3huUWtGQlF6dEJRVUZFTEVOQlFVTXNRVUY0U0VRc1NVRjNTRU03UVVGNFNGa3NPRUpCUVZNN1FVRnhTWFJDTEZOQlFXZENMR1ZCUVdVc1EwRkJReXhOUVVGcFFpeEZRVUZGTEUxQlFXbENMRVZCUVVVc1JVRkJWVHRKUVVVMVJTeEpRVUZOTEVWQlFVVXNSMEZCUnl4TlFVRk5MRU5CUVVNc1pVRkJaU3hEUVVGRExFMUJRVTBzUTBGQlF5eEZRVUZGTEVWQlFVVXNSVUZCUlN4TlFVRk5MRU5CUVVNc1JVRkJSU3hGUVVGRkxFTkJRVU1zU1VGQlNTeEZRVUZGTEVOQlFVTXNSVUZCUlN4TlFVRk5MRU5CUVVNc1JVRkJSU3hGUVVGRkxFVkJRVVVzUTBGQlF5eEZRVUZGTEUxQlFVMHNRMEZCUXl4RlFVRkZMRVZCUVVVc1JVRkJSU3hGUVVNM1JpeEZRVUZGTEVkQlFVY3NUVUZCVFN4RFFVRkRMR1ZCUVdVc1EwRkJReXhOUVVGTkxFTkJRVU1zUlVGQlJTeEZRVUZGTEVWQlFVVXNUVUZCVFN4RFFVRkRMRVZCUVVVc1JVRkJSU3hEUVVGRExFbEJRVWtzUlVGQlJTeERRVUZETEVWQlFVVXNUVUZCVFN4RFFVRkRMRVZCUVVVc1JVRkJSU3hGUVVGRkxFTkJRVU1zUlVGQlJTeE5RVUZOTEVOQlFVTXNSVUZCUlN4RlFVRkZMRVZCUVVVc1JVRkRNMFlzUlVGQlJTeEhRVUZITEVWQlFVVXNRMEZCUXl4RFFVRkRMRWRCUVVjc1JVRkJSU3hEUVVGRExFTkJRVU1zUlVGRGFFSXNSVUZCUlN4SFFVRkhMRVZCUVVVc1EwRkJReXhEUVVGRExFZEJRVWNzUlVGQlJTeERRVUZETEVOQlFVTXNSVUZEYUVJc1EwRkJReXhIUVVGSExFbEJRVWtzUTBGQlF5eEpRVUZKTEVOQlFVTXNSVUZCUlN4SFFVRkhMRVZCUVVVc1IwRkJSeXhGUVVGRkxFZEJRVWNzUlVGQlJTeERRVUZETEVWQlFVVXNSVUZCUlN4SFFVRkhMRU5CUVVNc1IwRkJSeXhGUVVGRkxFTkJRVU03U1VGRGJFUXNUMEZCVHp0UlFVTklMR3RDUVVGclFpeEZRVUZGTEVWQlFVVTdVVUZEZEVJc2EwSkJRV3RDTEVWQlFVVXNSVUZCUlR0UlFVTjBRaXhWUVVGVkxFVkJRVVVzUlVGQlJTeERRVUZETEVWQlFVVXNSVUZCUlN4RFFVRkRMRU5CUVVNc1IwRkJSeXhGUVVGRkxFZEJRVWNzUlVGQlJTeEhRVUZITEVOQlFVTXNSVUZCUlN4RFFVRkRMRVZCUVVVc1JVRkJSU3hEUVVGRExFTkJRVU1zUjBGQlJ5eEZRVUZGTEVkQlFVY3NSVUZCUlN4SFFVRkhMRU5CUVVNc1JVRkJSVHRMUVVNdlJDeERRVUZCTzBGQlEwd3NRMEZCUXp0QlFWcEVMREJEUVZsRE8wRkJWMFFzVTBGQlowSXNWVUZCVlN4RFFVRkRMRU5CUVRKQ0xFVkJRVVVzVFVGQmFVSXNSVUZCUlN4RlFVRlZPMGxCUTJwR0xFbEJRVWtzUlVGQlJTeEhRVUZITEUxQlFVMHNRMEZCUXl4bFFVRmxMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1NVRkRNVU1zU1VGQlNTeERRVUZETEVWQlFVVTdVVUZCUlN4RlFVRkZMRWRCUVVjc1JVRkJSU3hEUVVGRExFVkJRVVVzVFVGQlRTeERRVUZETEVWQlFVVXNSVUZCUlN4RlFVRkZMRU5CUVVNc1JVRkJSU3hOUVVGTkxFTkJRVU1zUlVGQlJTeEZRVUZGTEVWQlFVVXNRMEZCUXp0SlFVTnFSQ3hKUVVGSkxFVkJRVVVzUjBGQlJ5eEZRVUZGTEVOQlFVTXNRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRMllzUlVGQlJTeEhRVUZITEVWQlFVVXNRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGRFppeERRVUZETEVkQlFVY3NTVUZCU1N4RFFVRkRMRWxCUVVrc1EwRkJReXhGUVVGRkxFZEJRVWNzUlVGQlJTeEhRVUZITEVWQlFVVXNSMEZCUnl4RlFVRkZMRU5CUVVNc1EwRkJRenRKUVVOeVF5eFBRVUZQTEVWQlFVVXNRMEZCUXl4RlFVRkZMRVZCUVVVc1EwRkJReXhEUVVGRExFZEJRVWNzUlVGQlJTeEhRVUZITEVWQlFVVXNSMEZCUnl4RFFVRkRMRVZCUVVVc1EwRkJReXhGUVVGRkxFVkJRVVVzUTBGQlF5eERRVUZETEVkQlFVY3NSVUZCUlN4SFFVRkhMRVZCUVVVc1IwRkJSeXhEUVVGRExFVkJRVVVzUTBGQlF6dEJRVU0xUkN4RFFVRkRPMEZCVUVRc1owTkJUME03UVVGRlJEdEpRVWxKTEdOQlFXMUNMRU5CUVZjc1JVRkJVeXhEUVVGWkxFVkJRVk1zUjBGQlZ6dFJRVUZ3UkN4TlFVRkRMRWRCUVVRc1EwRkJReXhEUVVGVk8xRkJRVk1zVFVGQlF5eEhRVUZFTEVOQlFVTXNRMEZCVnp0UlFVRlRMRkZCUVVjc1IwRkJTQ3hIUVVGSExFTkJRVkU3VVVGRGJrVXNTVUZCU1N4RFFVRkRMRWxCUVVrc1IwRkJSeXhWUVVGVkxFVkJRVVVzUTBGQlF6dFJRVU42UWl4SlFVRkpMRU5CUVVNc1NVRkJTU3hIUVVGSExGVkJRVlVzUlVGQlJTeERRVUZETzBsQlF6ZENMRU5CUVVNN1NVRkRUQ3hYUVVGRE8wRkJRVVFzUTBGQlF5eEJRVkpFTEVsQlVVTTdRVUZGUkR0SlFVTkpMR1ZCUVcxQ0xFMUJRV1VzUlVGQlV5eERRVUZQTEVWQlFWTXNSMEZCVnp0UlFVRnVSQ3hYUVVGTkxFZEJRVTRzVFVGQlRTeERRVUZUTzFGQlFWTXNUVUZCUXl4SFFVRkVMRU5CUVVNc1EwRkJUVHRSUVVGVExGRkJRVWNzUjBGQlNDeEhRVUZITEVOQlFWRTdTVUZCUnl4RFFVRkRPMGxCUXpsRkxGbEJRVU03UVVGQlJDeERRVUZETEVGQlJrUXNTVUZGUXp0QlFVVkVMRk5CUVZNc1lVRkJZU3hEUVVGRExFTkJRVkVzUlVGQlJTeERRVUZSTzBsQlEzSkRMRWxCUVVrc1EwRkJReXhEUVVGRExFZEJRVWNzUjBGQlJ5eERRVUZETEVOQlFVTXNSMEZCUnl4RlFVRkZPMUZCUTJZc1QwRkJUeXhEUVVGRExFTkJRVU03UzBGRFdqdEpRVU5FTEVsQlFVa3NRMEZCUXl4RFFVRkRMRWRCUVVjc1IwRkJSeXhEUVVGRExFTkJRVU1zUjBGQlJ5eEZRVUZGTzFGQlEyWXNUMEZCVHl4RFFVRkRMRU5CUVVNc1EwRkJRenRMUVVOaU8wbEJRMFFzU1VGQlNTeERRVUZETEVOQlFVTXNUVUZCVFN4RlFVRkZPMUZCUlZZc1QwRkJUeXhEUVVGRExFTkJRVU1zUTBGQlF6dExRVU5pTzBsQlEwUXNTVUZCU1N4RFFVRkRMRU5CUVVNc1RVRkJUU3hGUVVGRk8xRkJSVllzVDBGQlR5eERRVUZETEVOQlFVTTdTMEZEV2p0SlFVTkVMRTlCUVU4c1EwRkJReXhEUVVGRE8wRkJRMklzUTBGQlF6dEJRVVZFTEZOQlFWTXNWVUZCVlR0SlFVTm1MRTlCUVU4c1NVRkJTU3hsUVVGTkxFTkJRVThzVlVGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4SlFVRkxMRTlCUVVFc1EwRkJReXhEUVVGRExFZEJRVWNzUjBGQlJ5eERRVUZETEVOQlFVTXNSMEZCUnl4RlFVRmlMRU5CUVdFc1EwRkJReXhEUVVGRE8wRkJRM0pFTEVOQlFVTTdRVUZYUkN4SlFVRkpMRXRCUVVzc1IwRkJhMEk3U1VGRGRrSXNVMEZCVXl4RlFVRkZMRlZCUVVFc1EwRkJReXhKUVVGSExFOUJRVUVzUTBGQlF5eERRVUZETEVWQlFVVXNSVUZCUlN4RlFVRk9MRU5CUVUwN1NVRkRja0lzVDBGQlR5eEZRVUZGTEZWQlFVRXNRMEZCUXl4SlFVRkhMRTlCUVVFc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQlNDeERRVUZITzBsQlEyaENMRkZCUVZFc1JVRkJSU3hWUVVGQkxFTkJRVU1zU1VGQlJ5eFBRVUZCTEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUVVnc1EwRkJSenRKUVVOcVFpeFBRVUZQTEVWQlFVVXNWVUZCUVN4RFFVRkRMRWxCUVVjc1QwRkJRU3hEUVVGRExFTkJRVU1zUzBGQlN5eEZRVUZGTEVWQlFWUXNRMEZCVXp0SlFVTjBRaXhSUVVGUkxFVkJRVVVzVlVGQlF5eEpRVUZKTEVWQlFVVXNTMEZCU3l4RlFVRkZMRTFCUVUwc1JVRkJSU3hKUVVGSkxFbEJRVXNzVDBGQlFTeEpRVUZKTEZOQlFWTXNRMEZCUXl4TlFVRk5MRWRCUVVjc1NVRkJTU3hIUVVGSExFTkJRVU1zUlVGQlJTeE5RVUZOTEVkQlFVY3NTVUZCU1N4SFFVRkhMRU5CUVVNc1JVRkJSU3hKUVVGSkxFVkJRVVVzUzBGQlN5eERRVUZETEVWQlFXaEZMRU5CUVdkRk8wbEJRM3BITEdOQlFXTXNSVUZCUlN4bFFVRmxPME5CUTJ4RExFTkJRVU03UVVGRlJpeEpRVUZKTEV0QlFVc3NSMEZCYTBJN1NVRkRka0lzVTBGQlV5eEZRVUZGTEZWQlFVRXNRMEZCUXl4SlFVRkhMRTlCUVVFc1EwRkJReXhEUVVGRExFVkJRVVVzUlVGQlJTeEZRVUZPTEVOQlFVMDdTVUZEY2tJc1QwRkJUeXhGUVVGRkxGVkJRVUVzUTBGQlF5eEpRVUZITEU5QlFVRXNRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkJTQ3hEUVVGSE8wbEJRMmhDTEZGQlFWRXNSVUZCUlN4VlFVRkJMRU5CUVVNc1NVRkJSeXhQUVVGQkxFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVZ3NRMEZCUnp0SlFVTnFRaXhQUVVGUExFVkJRVVVzVlVGQlFTeERRVUZETEVsQlFVY3NUMEZCUVN4RFFVRkRMRU5CUVVNc1RVRkJUU3hGUVVGRkxFVkJRVllzUTBGQlZUdEpRVU4yUWl4UlFVRlJMRVZCUVVVc1ZVRkJReXhKUVVGSkxFVkJRVVVzUzBGQlN5eEZRVUZGTEUxQlFVMHNSVUZCUlN4SlFVRkpMRWxCUVVzc1QwRkJRU3hKUVVGSkxGTkJRVk1zUTBGQlF5eEpRVUZKTEVWQlFVVXNTMEZCU3l4RlFVRkZMRTFCUVUwc1IwRkJSeXhKUVVGSkxFZEJRVWNzUTBGQlF5eEZRVUZGTEUxQlFVMHNSMEZCUnl4SlFVRkpMRWRCUVVjc1EwRkJReXhEUVVGRExFVkJRV2hGTEVOQlFXZEZPMGxCUTNwSExHTkJRV01zUlVGQlJTeGxRVUZsTzBOQlEyeERMRU5CUVVNN1FVRkZSaXhUUVVGVExIZENRVUYzUWl4RFFVRkRMRWxCUVhGQ0xFVkJRVVVzUTBGQlowSXNSVUZCUlN4TlFVRmpMRVZCUVVVc1YwRkJORUk3U1VGQk5VSXNORUpCUVVFc1JVRkJRU3h0UWtGQk5FSTdTVUZGYmtnc1NVRkJTU3hQUVVGUExFZEJRVWNzU1VGQlNTeERRVUZETEU5QlFVOHNSVUZEZEVJc1JVRkJSU3hIUVVGSExFOUJRVThzU1VGQlNTeERRVUZETEUxQlFVMHNTMEZCU3l4WFFVRlhMRU5CUVVNc1EwRkJReXhEUVVGRExFbEJRVWtzUTBGQlF5eE5RVUZOTEVOQlFVTXNUVUZCVFN4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRMmhGTEVWQlFVVXNSMEZCUnl4UFFVRlBMRWxCUVVrc1EwRkJReXhOUVVGTkxFdEJRVXNzVjBGQlZ5eERRVUZETEVOQlFVTXNRMEZCUXl4SlFVRkpMRU5CUVVNc1RVRkJUU3hEUVVGRExFMUJRVTBzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RlFVTm9SU3huUWtGQlowSXNSMEZCYVVJc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVVTdVVUZEZWtNc1EwRkJReXhEUVVGRExFbEJRVWtzUTBGQlF5eE5RVUZOTEVOQlFVTXNUVUZCVFN4RFFVRkRMRlZCUVVNc1IwRkJhVUlzUlVGQlJTeERRVUZETEVsQlFVc3NUMEZCUVN4SFFVRkhMRU5CUVVNc1RVRkJUU3hEUVVGRExIZENRVUYzUWl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFVkJRVVVzVFVGQlRTeEZRVUZGTEVsQlFVa3NRMEZCUXl4RFFVRkRMRVZCUVhoRUxFTkJRWGRFTEVWQlFVVXNSVUZCUlN4RFFVRkRMRVZCUXpWSExFTkJRVU1zUjBGQlJ5eERRVUZETEZkQlFWY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4RlFVRkZMRWRCUVVjc1JVRkJSU3hGUVVOdVF5eEZRVUZGTEVkQlFXVXNTVUZCU1N4TFFVRkxMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRemRDTEVWQlFVVXNSMEZCWjBJc1NVRkJTU3hMUVVGTExFTkJRVU1zUTBGQlF5eERRVUZETEVWQlF6bENMRU5CUVVNc1IwRkJSeXhEUVVGRExFVkJRMHdzUjBGQlJ5eEhRVUZITEZWQlFVTXNRMEZCUXl4RlFVRkZMRU5CUVVNc1NVRkJUeXhGUVVGRkxFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkJMRU5CUVVNc1EwRkJReXhEUVVGRE8wbEJReTlETEVsQlFVa3NWMEZCVnl4RlFVRkZPMUZCUldJc1NVRkJTU3hEUVVGRExFZEJRV01zU1VGQlNTeERRVUZETEUxQlFVMHNSVUZETVVJc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eFRRVUZUTEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eFBRVUZQTEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVONFF5eEpRVUZKTEVkQlFVY3NRMEZCUXl4RFFVRkRMRTlCUVU4c1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQlJTeExRVUZMTEVkQlFVY3NRMEZCUXl4RFFVRkRMRkZCUVZFc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGRE1VTXNSMEZCUnl4SFFVRkhMRU5CUVVNc1IwRkJSeXhEUVVGRExFZEJRVWNzVDBGQlR5eEhRVUZITEVOQlFVTXNSVUZCUlN4SFFVRkhMRWRCUVVjc1EwRkJReXhIUVVGSExFTkJRVU1zUjBGQlJ5eFBRVUZQTEVkQlFVY3NRMEZCUXl4RFFVRkRPMUZCUTNwRUxFbEJRVWtzUTBGQlF5eE5RVUZOTEVOQlFVTXNaVUZCWlN4SFFVRkhMRWRCUVVjc1EwRkJRenRSUVVOc1F5eEhRVUZITEVOQlFVTXNRMEZCUXl4RFFVRkRMRkZCUVZFc1EwRkJReXhKUVVGSkxFVkJRVVVzUzBGQlN5eEZRVUZGTEVkQlFVY3NSVUZCUlN4UFFVRlBMRU5CUVVNc1JVRkJSU3hKUVVGSkxFTkJRVU1zVFVGQlRTeERRVUZETEVOQlFVTTdVVUZEZUVRc1NVRkJTU3hEUVVGRExFMUJRVTBzUTBGQlF5eGxRVUZsTEVkQlFVY3NSMEZCUnl4RFFVRkRPMUZCUTJ4RExFZEJRVWNzUTBGQlF5eERRVUZETEVOQlFVTXNVVUZCVVN4RFFVRkRMRWxCUVVrc1JVRkJSU3hMUVVGTExFVkJRVVVzUjBGQlJ5eEZRVUZGTEU5QlFVOHNRMEZCUXl4RlFVRkZMRWxCUVVrc1EwRkJReXhOUVVGTkxFTkJRVU1zUTBGQlF6dExRVU16UkR0SlFVTkVMRWxCUVVrc1JVRkJSVHRSUVVGRkxFbEJRVWtzUTBGQlF5eE5RVUZOTEVOQlFVTXNUMEZCVHl4RFFVRkRMRlZCUVVFc1EwRkJReXhKUVVGSkxFOUJRVUVzUjBGQlJ5eERRVUZETEVOQlFVTXNRMEZCUXl4TlFVRk5MRVZCUVVVc1EwRkJReXhEUVVGRExGRkJRVkVzUTBGQlF5eEZRVUY2UWl4RFFVRjVRaXhEUVVGRExFTkJRVU03U1VGRE5VUXNTVUZCU1N4RlFVRkZPMUZCUVVVc1NVRkJTU3hEUVVGRExFMUJRVTBzUTBGQlF5eFBRVUZQTEVOQlFVTXNWVUZCUVN4RFFVRkRPMWxCUTNwQ0xFbEJRVWtzUTBGQlF5eEhRVUZqTEVOQlFVTXNRMEZCUXl4TlFVRk5MRU5CUVVNN1dVRkROVUlzUjBGQlJ5eERRVUZETEVOQlFVTXNRMEZCUXl4UlFVRlJMRU5CUVVNc1EwRkJReXhEUVVGRExFOUJRVThzUTBGQlF5eERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1VVRkJVU3hEUVVGRExFTkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXl4VFFVRlRMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETEU5QlFVOHNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF5eE5RVUZOTEVOQlFVTXNRMEZCUXp0UlFVTjZSaXhEUVVGRExFTkJRVU1zUTBGQlF6dEpRVU5JTEVsQlFVa3NSVUZCUlN4SFFVRkhMRzFDUVVGdFFpeERRVUZETEVWQlFVVXNSVUZCUlN4RlFVRkZMRVZCUVVVc1EwRkJReXhGUVVGRkxFMUJRVTBzUTBGQlF5eERRVUZETzBsQlEyaEVMRWxCUVVrc1JVRkJSU3hGUVVGRk8xRkJRMG9zUlVGQlJTeERRVUZETEU5QlFVOHNRMEZCUXl4VlFVRkJMRU5CUVVNc1NVRkJUU3hEUVVGRExFTkJRVU1zU1VGQlNTeEhRVUZITEVWQlFVVXNSVUZCUlN4RFFVRkRMRU5CUVVNc1IwRkJSeXhIUVVGSExFVkJRVVVzUTBGQlFTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMUZCUXpkRExFVkJRVVVzUTBGQlF5eFBRVUZQTEVOQlFVTXNWVUZCUVN4RFFVRkRMRWxCUVUwc1EwRkJReXhEUVVGRExFbEJRVWtzUTBGQlF5eEpRVUZKTEVOQlFVTXNTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF5eExRVUZMTEVOQlFVTXNSMEZCUnl4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlFTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMUZCUXpsRUxFbEJRVWtzUTBGQlF5eE5RVUZOTEVOQlFVTXNUMEZCVHl4RFFVRkRMRlZCUVVFc1EwRkJRenRaUVVOcVFpeEpRVUZKTEdGQlFXRXNSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJReXhQUVVGUExFZEJRVWNzUTBGQlF5eERRVUZETEU5QlFVOHNRMEZCUXl4RFFVRkRMRU5CUVVNc1RVRkJUU3hEUVVGRExFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTTdXVUZETVVRc1EwRkJReXhEUVVGRExFMUJRVTBzUTBGQlF5eEhRVUZITEVOQlFVTXNUMEZCVHl4RFFVRkRMRlZCUVVFc1EwRkJReXhKUVVGSkxFOUJRVUVzUTBGQlF5eERRVUZETEVkQlFVY3NTVUZCU1N4aFFVRmhMRVZCUVhSQ0xFTkJRWE5DTEVOQlFVTXNRMEZCUXp0WlFVTnNSQ3hEUVVGRExFTkJRVU1zVFVGQlRTeERRVUZETEVsQlFVa3NRMEZCUXl4UFFVRlBMRU5CUVVNc1ZVRkJRU3hEUVVGRExFbEJRVTBzUTBGQlF5eERRVUZETEVsQlFVa3NSMEZCUnl4RFFVRkRMRU5CUVVNc1RVRkJUU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVkQlFVY3NTVUZCU1N4aFFVRmhMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFJRVU12UlN4RFFVRkRMRU5CUVVNc1EwRkJRenRMUVVOT08wbEJRMFFzVDBGQlR5eG5Ra0ZCWjBJc1EwRkJReXhOUVVGTkxFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTTdRVUZEZGtNc1EwRkJRenRCUVVWRUxGTkJRVk1zYlVKQlFXMUNMRU5CUVVNc1JVRkJaU3hGUVVGRkxFbEJRV2RDTEVWQlF6RkVMRWxCUVcxQ0xFVkJRVVVzVFVGQll6dEpRVVZ1UXl4SlFVRkpMRU5CUVVNc1JVRkJSU3hEUVVGRExFZEJRVWNzUlVGQlJTeERRVUZETEUxQlFVMHNRMEZCUXp0SlFVTnlRaXhKUVVGSkxFTkJRVU1zUjBGQlJ5eERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRPMGxCUTJRc1QwRkJUeXhEUVVGRExFMUJRVTBzUTBGQlF5eEpRVUZKTEVOQlFVTXNUVUZCVFN4SlFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRE8wbEJRMnBETEVsQlFVa3NUVUZCVFN4SFFVRkhMRWxCUVVrc1MwRkJTeXhEUVVGUkxFTkJRVU1zUTBGQlF5eERRVUZETzBsQlEycERMRXRCUVVzc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NRMEZCUXl4RlFVRkZMRVZCUVVVc1EwRkJReXhGUVVGRk8xRkJRM0JDTEVsQlFVa3NRMEZCUXl4SFFVRkhMRVZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFJRVU5rTEVsQlFVa3NRMEZCUXl4SFFVRkhMRWxCUVVrc1NVRkJTU3hEUVVGRExFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRVZCUVVVc1NVRkJTU3hEUVVGRExGTkJRVk1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMUZCUTJoRUxFMUJRVTBzUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4SlFVRkpMRXRCUVVzc1EwRkJReXhKUVVGSkxFVkJRVVVzUTBGQlF5eEZRVUZGTEVsQlFVa3NRMEZCUXl4UFFVRlBMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFJRVU5vUkN4TlFVRk5MRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eEhRVUZITEVsQlFVa3NTMEZCU3l4RFFVRkRMRXRCUVVzc1JVRkJSU3hEUVVGRExFVkJRVVVzU1VGQlNTeERRVUZETEZGQlFWRXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8wdEJRM3BFTzBsQlEwUXNUVUZCVFN4RFFVRkRMRWxCUVVrc1EwRkJReXhoUVVGaExFTkJRVU1zUTBGQlF6dEpRVU16UWl4SlFVRkpMRVZCUVVVc1IwRkJSeXhKUVVGSkxFdEJRVXNzUlVGQll5eERRVUZETzBsQlEycERMRWxCUVVrc1VVRkJVU3hIUVVGSExGVkJRVlVzUlVGQlJTeERRVUZETzBsQlF6VkNMRXRCUVVzc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NRMEZCUXl4RlFVRkZMRVZCUVVVc1EwRkJReXhGUVVGRk8xRkJRM0JDTEVsQlFVa3NRMEZCUXl4SFFVRkhMRTFCUVUwc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFJRVU5zUWl4SlFVRkpMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzFGQlExb3NTVUZCU1N4RFFVRkRMRU5CUVVNc1RVRkJUU3hGUVVGRk8xbEJRMVlzVVVGQlVTeERRVUZETEUxQlFVMHNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRaUVVOdVFpeEpRVUZKTEVOQlFVTXNZMEZCWXl4RFFVRkRMRU5CUVVNc1JVRkJSU3hSUVVGUkxFTkJRVU1zUTBGQlF6dFRRVU53UXp0aFFVRk5PMWxCUlVnc1VVRkJVU3hEUVVGRExFMUJRVTBzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0WlFVTnVRaXhKUVVGSkxHTkJRV01zUjBGQlJ5eFZRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRPMmRDUVVOMFFpeEpRVUZKTEVkQlFVY3NSMEZCUnl4RFFVRkRMRWxCUVVrc1EwRkJReXhQUVVGUExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRWxCUVVrc1EwRkJReXhQUVVGUExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhIUVVGSExFMUJRVTBzUTBGQlF6dG5Ra0ZETDBRc1JVRkJSU3hEUVVGRExFbEJRVWtzUTBGQlF5eEpRVUZKTEdsQ1FVRlZMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTXNRMEZCUXl4RlFVRkZMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU03V1VGRE0wTXNRMEZCUXl4RFFVRkRPMWxCUTBZc1NVRkJTU3hsUVVGbExFZEJRVWNzVlVGQlF5eFBRVUZQTEVWQlFVVXNUMEZCVHl4RlFVRkZMRXRCUVVzN1owSkJRekZETEVsQlFVa3NRMEZCUXl4RlFVRkZMRVZCUVVVc1IwRkJSeXhEUVVGRExFTkJRVU1zVDBGQlR5eERRVUZETEVOQlFVTXNVVUZCVVN4RlFVRkZMRU5CUVVNN1owSkJRMnhETEU5QlFVOHNRMEZCUXl4RFFVRkRMRWRCUVVjc1JVRkJSU3hEUVVGRExFOUJRVThzUTBGQlF5eEZRVUZGTEVOQlFVTXNTMEZCU3l4SlFVRkpMRVZCUVVVN2IwSkJRMnBETEV0QlFVc3NRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU03YjBKQlExb3NRMEZCUXl4RFFVRkRMRTlCUVU4c1EwRkJReXhEUVVGRExFMUJRVTBzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0cFFrRkRlRUk3V1VGRFRDeERRVUZETEVOQlFVTTdXVUZEUml4bFFVRmxMRU5CUVVNc1RVRkJUU3hGUVVGRkxFMUJRVTBzUlVGQlJTeFZRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRWxCUVVzc1QwRkJRU3hqUVVGakxFTkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXl4RlFVRndRaXhEUVVGdlFpeERRVUZETEVOQlFVTTdXVUZEYUVVc1pVRkJaU3hEUVVGRExFMUJRVTBzUlVGQlJTeE5RVUZOTEVWQlFVVXNWVUZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhKUVVGTExFOUJRVUVzWTBGQll5eERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1JVRkJjRUlzUTBGQmIwSXNRMEZCUXl4RFFVRkRPMU5CUTI1Rk8wdEJRMG83U1VGRFJDeFBRVUZQTEVOQlFVTXNUVUZCVFN4RFFVRkRMRkZCUVZFc1EwRkJReXhKUVVGSkxFdEJRVXNzUTBGQlF5eERRVUZETEVOQlFVTTdTVUZEY0VNc1QwRkJUeXhGUVVGRkxFTkJRVU03UVVGRFpDeERRVUZETzBGQlJVUXNVMEZCVXl4bFFVRmxMRU5CUVVNc1EwRkJUeXhGUVVGRkxGRkJRWE5DTzBsQlEzQkVMRWxCUVVrc1EwRkJReXhIUVVGSExGVkJRVU1zVDBGQlR5eEZRVUZGTEU5QlFVODdVVUZEY2tJc1NVRkJTU3hGUVVGRkxFZEJRVWNzVVVGQlVTeERRVUZETEZGQlFWRXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRSUVVNNVFpeEpRVUZKTEVOQlFVTXNRMEZCUXp0UlFVTk9MRTlCUVU4c1EwRkJReXhEUVVGRExFZEJRVWNzUlVGQlJTeERRVUZETEU5QlFVOHNRMEZCUXl4RlFVRkZMRU5CUVVNc1MwRkJTeXhKUVVGSkxFVkJRVVU3V1VGRGFrTXNTVUZCU1N4UFFVRlBMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eFJRVUZSTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8xbEJRMmhETEVsQlFVa3NUMEZCVHl4SlFVRkpMRU5CUVVNc1NVRkJTU3hQUVVGUExFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4UlFVRlJMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEZRVUZGTzJkQ1FVTTVReXhEUVVGRExFTkJRVU1zVDBGQlR5eERRVUZETEVOQlFVTXNUVUZCVFN4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8yZENRVU55UWl4RFFVRkRMRU5CUVVNc1QwRkJUeXhEUVVGRExFTkJRVU1zVFVGQlRTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMkZCUTNoQ08xbEJRMFFzU1VGQlNTeFBRVUZQTEVsQlFVa3NRMEZCUXl4RlFVRkZPMmRDUVVOa0xFMUJRVTA3WVVGRFZEdFRRVU5LTzBsQlEwd3NRMEZCUXl4RFFVRkJPMGxCUTBRc1EwRkJReXhEUVVGRExFMUJRVTBzUlVGQlJTeE5RVUZOTEVOQlFVTXNRMEZCUXp0SlFVTnNRaXhEUVVGRExFTkJRVU1zVFVGQlRTeEZRVUZGTEUxQlFVMHNRMEZCUXl4RFFVRkRPMEZCUTNSQ0xFTkJRVU03UVVGRlJDeFRRVUZUTEdWQlFXVXNRMEZCUXl4RFFVRlBMRVZCUVVVc1VVRkJjMEk3U1VGRGNFUXNTVUZCU1N4RFFVRkRMRWRCUVVjc1ZVRkJReXhQUVVGUExFVkJRVVVzVDBGQlR6dFJRVU55UWl4SlFVRkpMRU5CUVVNc1IwRkJSeXhSUVVGUkxFTkJRVU1zVVVGQlVTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRTlCUVU4c1EwRkJReXhGUVVGRkxFTkJRVU03VVVGRGVFTXNTVUZCU1N4RFFVRkRMRXRCUVVzc1NVRkJTU3hKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNVVUZCVVN4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlJ5eERRVUZETEVWQlFVVTdXVUZEY2tNc1EwRkJReXhEUVVGRExFOUJRVThzUTBGQlF5eERRVUZETEUxQlFVMHNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRaUVVOeVFpeERRVUZETEVOQlFVTXNUMEZCVHl4RFFVRkRMRU5CUVVNc1RVRkJUU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzFOQlEzaENPMGxCUTB3c1EwRkJReXhEUVVGQk8wbEJRMFFzUTBGQlF5eERRVUZETEUxQlFVMHNSVUZCUlN4TlFVRk5MRU5CUVVNc1EwRkJRenRKUVVOc1FpeERRVUZETEVOQlFVTXNUVUZCVFN4RlFVRkZMRTFCUVUwc1EwRkJReXhEUVVGRE8wRkJRM1JDTEVOQlFVTTdRVUZGUkN4VFFVRm5RaXh2UWtGQmIwSXNRMEZCUXl4RlFVRmxMRVZCUVVVc1NVRkJaMEk3U1VGRGJFVXNUMEZCVHl4dFFrRkJiVUlzUTBGQlF5eEZRVUZGTEVWQlFVVXNTVUZCU1N4RlFVRkZMRXRCUVVzc1JVRkJSU3hKUVVGSkxFTkJRVU1zUTBGQlF6dEJRVU4wUkN4RFFVRkRPMEZCUmtRc2IwUkJSVU03UVVGRlJDeFRRVUZuUWl4dlFrRkJiMElzUTBGQlF5eEZRVUZsTEVWQlFVVXNTVUZCWjBJN1NVRkRiRVVzVDBGQlR5eHRRa0ZCYlVJc1EwRkJReXhGUVVGRkxFVkJRVVVzU1VGQlNTeEZRVUZGTEV0QlFVc3NSVUZCUlN4SlFVRkpMRU5CUVVNc1EwRkJRenRCUVVOMFJDeERRVUZETzBGQlJrUXNiMFJCUlVNN1FVRkZSQ3hUUVVGblFpeDVRa0ZCZVVJc1EwRkJReXhKUVVGeFFqdEpRVU16UkN4UFFVRlBMSGRDUVVGM1FpeERRVUZETEVsQlFVa3NSVUZCUlN4TFFVRkxMRVZCUVVVc1NVRkJTU3hEUVVGRExFTkJRVU03UVVGRGRrUXNRMEZCUXp0QlFVWkVMRGhFUVVWRE8wRkJSVVFzVTBGQlowSXNlVUpCUVhsQ0xFTkJRVU1zU1VGQmNVSTdTVUZETTBRc1QwRkJUeXgzUWtGQmQwSXNRMEZCUXl4SlFVRkpMRVZCUVVVc1MwRkJTeXhGUVVGRkxFbEJRVWtzUTBGQlF5eERRVUZETzBGQlEzWkVMRU5CUVVNN1FVRkdSQ3c0UkVGRlF6dEJRVVZFTEZOQlFXZENMR05CUVdNc1EwRkJReXhGUVVGbE8wbEJRekZETEVsQlFVa3NSVUZCUlN4SFFVRkhMRVZCUVVVc1EwRkJReXhIUVVGSExFTkJRVU1zVlVGQlFTeERRVUZETEVsQlFVa3NUMEZCUVN4SlFVRkpMR1ZCUVZFc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQlJTeEZRVUZGTEVOQlFVTXNSVUZCY0VJc1EwRkJiMElzUTBGQlF5eERRVUZETzBsQlF6TkRMRWxCUVVrc1JVRkJSU3hIUVVGSExHOUNRVUZ2UWl4RFFVRkRMRVZCUVVVc1JVRkJSU3hGUVVGRkxFTkJRVU1zUTBGQlF6dEpRVU4wUXl4SlFVRkpMRTFCUVUwc1IwRkJSeXhKUVVGSkxHRkJRVTBzUTBGQlF5eEZRVUZGTEVWQlFVVXNSVUZCUlN4RFFVRkRMRU5CUVVNN1NVRkRhRU1zVFVGQlRTeERRVUZETEV0QlFVc3NSVUZCUlN4RFFVRkRPMGxCUTJZc1JVRkJSU3hEUVVGRExFOUJRVThzUTBGQlF5eFZRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRWxCUVVzc1QwRkJRU3hGUVVGRkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNWVUZCVlN4RFFVRkRMRU5CUVVNc1EwRkJReXhSUVVGUkxFVkJRVVVzUTBGQlF5eEZRVUU1UWl4RFFVRTRRaXhEUVVGRExFTkJRVU03U1VGRGNrUXNSVUZCUlN4SFFVRkhMRVZCUVVVc1EwRkJReXhIUVVGSExFTkJRVU1zVlVGQlFTeERRVUZETEVsQlFVY3NUMEZCUVN4SlFVRkpMR1ZCUVZFc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQlJTeEZRVUZGTEVOQlFVTXNSVUZCY0VJc1EwRkJiMElzUTBGQlF5eERRVUZETzBsQlEzUkRMRVZCUVVVc1IwRkJSeXh2UWtGQmIwSXNRMEZCUXl4RlFVRkZMRVZCUVVVc1JVRkJSU3hEUVVGRExFTkJRVU03U1VGRGJFTXNUVUZCVFN4SFFVRkhMRWxCUVVrc1lVRkJUU3hEUVVGRExFVkJRVVVzUlVGQlJTeEZRVUZGTEVOQlFVTXNRMEZCUXp0SlFVTTFRaXhOUVVGTkxFTkJRVU1zUzBGQlN5eEZRVUZGTEVOQlFVTTdTVUZEWml4RlFVRkZMRU5CUVVNc1QwRkJUeXhEUVVGRExGVkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTXNTVUZCU3l4UFFVRkJMRVZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eFZRVUZWTEVOQlFVTXNRMEZCUXl4RFFVRkRMRkZCUVZFc1JVRkJSU3hEUVVGRExFVkJRVGxDTEVOQlFUaENMRU5CUVVNc1EwRkJRenRCUVVONlJDeERRVUZETzBGQldFUXNkME5CVjBNN1FVRmhSRHRKUVVGeFF5eHRRMEZCVVR0SlFVTjZReXg1UWtGQmJVSXNTMEZCWVN4RlFVRkZMRU5CUVZNN1VVRkJNME1zV1VGRFNTeHJRa0ZCVFN4RFFVRkRMRVZCUVVVc1EwRkJReXhEUVVGRExGTkJRMlE3VVVGR2EwSXNWMEZCU3l4SFFVRk1MRXRCUVVzc1EwRkJVVHM3U1VGRmFFTXNRMEZCUXp0SlFVTk1MSE5DUVVGRE8wRkJRVVFzUTBGQlF5eEJRVXBFTEVOQlFYRkRMR1ZCUVZFc1IwRkpOVU03UVVGS1dTd3dRMEZCWlR0QlFVMDFRanRKUVV0SkxHOUNRVUZ2UWl4TFFVRnJRaXhGUVVNeFFpeE5RVUY1UWl4RlFVTjZRaXhUUVVGcFF5eEZRVU42UXl4WFFVRjNRaXhGUVVOb1FpeGhRVUU0UWp0UlFVb3hReXhwUWtFNFFrTTdVVUUxUWxjc01FSkJRVUVzUlVGQlFTeG5Ra0ZCYVVNN1VVRkRla01zTkVKQlFVRXNSVUZCUVN4clFrRkJkMEk3VVVGRGFFSXNPRUpCUVVFc1JVRkJRU3h4UWtGQk9FSTdVVUZLZEVJc1ZVRkJTeXhIUVVGTUxFdEJRVXNzUTBGQllUdFJRVU14UWl4WFFVRk5MRWRCUVU0c1RVRkJUU3hEUVVGdFFqdFJRVU42UWl4alFVRlRMRWRCUVZRc1UwRkJVeXhEUVVGM1FqdFJRVVZxUXl4clFrRkJZU3hIUVVGaUxHRkJRV0VzUTBGQmFVSTdVVUZGZEVNc1NVRkJTU3hEUVVGRExGTkJRVk1zUjBGQlJ5eExRVUZMTEVOQlFVTXNSMEZCUnl4RFFVRkRMRlZCUVVNc1EwRkJReXhGUVVGRkxFTkJRVU03V1VGRE5VSXNUMEZCVHl4RFFVRkRMRU5CUVVNc1VVRkJVU3hIUVVGSExFbEJRVWtzWlVGQlpTeERRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJRenRSUVVOc1JDeERRVUZETEVOQlFVTXNRMEZCUXp0UlFVVklMRWxCUVVrc1YwRkJWenRaUVVGRkxFbEJRVWtzUTBGQlF5eHBRa0ZCYVVJc1EwRkJReXhYUVVGWExFTkJRVU1zUTBGQlF6dFJRVVZ5UkN4SlFVRkpMR0ZCUVdFc1NVRkJTU3hUUVVGVExFbEJRVWtzVDBGQlR5eFRRVUZUTEVOQlFVTXNUVUZCVFN4TFFVRkxMRmRCUVZjc1JVRkJSVHRaUVVOMlJTeExRVUZMTEVOQlFVTXNUMEZCVHl4RFFVRkRMRlZCUVVFc1EwRkJRenRuUWtGRE1VSXNTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJReXhMUVVGTExFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNUVUZCVFN4RlFVTjZRanR2UWtGRlF5eERRVUZETEVOQlFVTXNUVUZCVFN4SFFVRkhMRWxCUVVrc1UwRkJVeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenR2UWtGRE4wTXNUMEZCVHp0cFFrRkRVRHRuUWtGRFl5eEpRVUZKTEVWQlFVVXNSMEZCUnl4RFFVRkRMRU5CUVVNc1MwRkJTeXhIUVVGSExFTkJRVU1zUlVGQlJTeEZRVUZGTEVkQlFVY3NRMEZCUXl4RFFVRkRMRTFCUVUwc1IwRkJSeXhEUVVGRExFTkJRVU03WjBKQlEzaERMRU5CUVVNc1EwRkJReXhOUVVGTkxFZEJRVWNzU1VGQlNTeFRRVUZUTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNc1IwRkJSeXhGUVVGRkxFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4RlFVRkZMRVZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlJ5eEZRVUZGTEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1IwRkJSeXhGUVVGRkxFTkJRVU1zUTBGQlF6dFpRVU55UlN4RFFVRkRMRU5CUVVNc1EwRkJRenRaUVVOSUxHdENRVUZyUWl4RFFVRkRMRk5CUVZNc1EwRkJReXhEUVVGRE8xbEJRemxDTEVsQlFVa3NRMEZCUXl4SFFVRkhMRXRCUVVzc1EwRkJReXhOUVVGTkxFTkJRVU03V1VGRGNrSXNUVUZCVFN4RFFVRkRMRTlCUVU4c1EwRkJReXhWUVVGQkxFTkJRVU03WjBKQlExb3NTMEZCU1N4RFFVRkRMRk5CUVZNc1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNUVUZCVFN4SFFVRkhMRWxCUVVrc1pVRkJaU3hEUVVGRExFTkJRVU1zUlVGQlJTeEZRVUZGTEU5QlFVOHNRMEZCUXl4RFFVRkRMRk5CUVZNc1MwRkJTeXhYUVVGWExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4VFFVRlRMRU5CUVVNc1EwRkJReXhEUVVGRExFbEJRVWtzUTBGQlF5eERRVUZETzJkQ1FVTnFTQ3hMUVVGSkxFTkJRVU1zVTBGQlV5eERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJReXhOUVVGTkxFZEJRVWNzU1VGQlNTeGxRVUZsTEVOQlFVTXNRMEZCUXl4RlFVRkZMRVZCUVVVc1QwRkJUeXhEUVVGRExFTkJRVU1zVTBGQlV5eExRVUZMTEZkQlFWY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExGTkJRVk1zUTBGQlF5eERRVUZETEVOQlFVTXNTVUZCU1N4RFFVRkRMRU5CUVVNN1dVRkRja2dzUTBGQlF5eERRVUZETEVOQlFVTTdVMEZEVGp0SlFVTk1MRU5CUVVNN1NVRkhUeXh4UTBGQlowSXNSMEZCZUVJc1ZVRkJlVUlzUTBGQlRUdFJRVU16UWl4UFFVRlBMRWxCUVVrc2FVSkJRVlVzUTBGRGFrSXNTVUZCU1N4RFFVRkRMRXRCUVVzc1EwRkJReXhEUVVGRExFTkJRVU1zU1VGQlNTeERRVUZETEVOQlFVTXNVVUZCVVN4RlFVTXpRaXhKUVVGSkxFTkJRVU1zUzBGQlN5eERRVUZETEVOQlFVTXNRMEZCUXl4TFFVRkxMRU5CUVVNc1EwRkJReXhSUVVGUkxFVkJRelZDTEVOQlFVTXNRMEZCUXl4SFFVRkhMRVZCUTB3c1QwRkJUeXhEUVVGRExFTkJRVU1zVVVGQlVTeExRVUZMTEZkQlFWY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExGRkJRVkVzUTBGQlF5eERRVUZETEVOQlFVTXNTMEZCU3l4RFFVRkRMRU5CUVVNN1NVRkRhRVVzUTBGQlF6dEpRVWRQTEdsRFFVRlpMRWRCUVhCQ0xGVkJRWEZDTEVOQlFVMDdVVUZCTTBJc2FVSkJhVUpETzFGQmFFSkhMRWxCUVVrc1EwRkJReXhKUVVGSkxFTkJRVU1zWVVGQllUdFpRVUZGTEU5QlFVODdVVUZGYUVNc1NVRkJTU3hKUVVGSkxFZEJRVWNzUjBGQlJ5eEZRVUZGTEVkQlFVY3NSMEZCUnl4UFFVRlBMRU5CUVVNN1VVRkRPVUlzU1VGQlNTeERRVUZETEVOQlFVTXNTVUZCU1N4TFFVRkxMRWRCUVVjN1dVRkJSU3hKUVVGSkxFZEJRVWNzUjBGQlJ5eEZRVUZGTEVkQlFVY3NSMEZCUnl4UlFVRlJMRU5CUVVNN1VVRkRMME1zU1VGQlNTeEZRVUZGTEVkQlFXZENMRU5CUVVNc1EwRkJReXhQUVVGUExFTkJRVU1zUjBGQlJ5eERRVUZETEZWQlFVRXNRMEZCUXl4SlFVRkpMRTlCUVVFc1MwRkJTU3hEUVVGRExFdEJRVXNzUTBGQlF5eERRVUZETEVOQlFVTXNTVUZCU1N4RFFVRkRMRVZCUVd4Q0xFTkJRV3RDTEVOQlFVTXNRMEZCUXl4SlFVRkpMRU5CUVVNc1ZVRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eEpRVUZMTEU5QlFVRXNRMEZCUXl4RFFVRkRMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eEpRVUZKTEVOQlFVTXNSVUZCYWtJc1EwRkJhVUlzUTBGQlF5eERRVUZETzFGQlF5OUdMRWxCUVVrc1EwRkJReXhIUVVGakxFbEJRVWtzUTBGQlF6dFJRVU40UWl4RlFVRkZMRU5CUVVNc1QwRkJUeXhEUVVGRExGVkJRVUVzUTBGQlF6dFpRVVZTTEVsQlFVa3NRMEZCUXl4RlFVRkZPMmRDUVVOSUxFbEJRVWtzVDBGQlR5eEhRVUZITEVOQlFVTXNRMEZCUXl4SlFVRkpMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTTdaMEpCUXk5Q0xFbEJRVWtzVDBGQlR5eEhRVUZITEVOQlFVTXNRMEZCUXl4SlFVRkpMRU5CUVVNc1JVRkJSVHR2UWtGRGJrSXNRMEZCUXl4RFFVRkRMRWxCUVVrc1EwRkJReXhIUVVGSExFOUJRVThzUTBGQlF6dHBRa0ZEY2tJN1lVRkRTanRaUVVORUxFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTTdVVUZEVml4RFFVRkRMRU5CUVVNc1EwRkJRenRKUVVOUUxFTkJRVU03U1VGRlR5eHZRMEZCWlN4SFFVRjJRaXhWUVVGM1FpeERRVUZOTzFGQlFUbENMR2xDUVZGRE8xRkJVRWNzU1VGQlNTeERRVUZETEVkQlFVY3NTVUZCU1N4RFFVRkRMRXRCUVVzc1EwRkJReXhEUVVGRExFTkJRVU1zVDBGQlR5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRExGRkJRVkVzUTBGQlF6dFJRVU12UXl4SlFVRkpMRU5CUVVNc1dVRkJXU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzFGQlEzSkNMRWxCUVVrc1JVRkJSU3hIUVVGSExFTkJRVU1zUTBGQlF5eEpRVUZKTEV0QlFVc3NSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJReXhKUVVGSkxFTkJRVU1zV1VGQldTeERRVUZETEVOQlFVTXNRMEZCUXl4SlFVRkpMRU5CUVVNc1dVRkJXU3hEUVVGRE8xRkJRMmhGTEVOQlFVTXNRMEZCUXl4UFFVRlBMRU5CUVVNc1MwRkJTeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEU5QlFVOHNRMEZCUXl4VlFVRkJMRU5CUVVNN1dVRkRlRUlzU1VGQlNTeERRVUZETEVkQlFVY3NTMEZCU1N4RFFVRkRMRXRCUVVzc1EwRkJReXhEUVVGRExFTkJRVU1zU1VGQlNTeERRVUZETEVOQlFVTXNVVUZCVVN4RFFVRkRPMWxCUTNCRExFVkJRVVVzUTBGQlF5eEpRVUZKTEVOQlFVTXNTVUZCU1N4cFFrRkJWU3hEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVWQlFVVXNRMEZCUXl4RFFVRkRMRTFCUVUwc1JVRkJSU3hKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETzFGQlEyeEVMRU5CUVVNc1EwRkJReXhEUVVGRE8wbEJRMUFzUTBGQlF6dEpRVVZQTEhORFFVRnBRaXhIUVVGNlFpeFZRVUV3UWl4WFFVRnJRanRSUVVFMVF5eHBRa0ZYUXp0UlFWWkhMRWxCUVVrc1MwRkJTeXhIUVVGSExGVkJRVUVzUTBGQlF5eEpRVUZKTEU5QlFVRXNUMEZCVHl4RFFVRkRMRU5CUVVNc1NVRkJTU3hMUVVGTExGZEJRVmNzU1VGQlNTeERRVUZETEVOQlFVTXNTVUZCU1N4TFFVRkxMRmxCUVZrc1JVRkJlRVFzUTBGQmQwUXNRMEZCUXp0UlFVTXhSU3hKUVVGSkxFTkJRVU1zV1VGQldTeEhRVUZITEZkQlFWYzdZVUZETVVJc1RVRkJUU3hEUVVGRExGVkJRVUVzUTBGQlF5eEpRVUZKTEU5QlFVRXNRMEZCUXl4RFFVRkRMRWxCUVVrc1MwRkJTeXhIUVVGSExFbEJRVWtzUzBGQlN5eERRVUZETEVOQlFVTXNRMEZCUXl4RlFVRXhRaXhEUVVFd1FpeERRVUZETzJGQlEzWkRMRWRCUVVjc1EwRkJReXhWUVVGQkxFTkJRVU1zU1VGQlNTeFBRVUZCTEV0QlFVa3NRMEZCUXl4blFrRkJaMElzUTBGQlF5eERRVUZETEVOQlFVTXNSVUZCZUVJc1EwRkJkMElzUTBGQlF5eERRVUZETzFGQlEzaERMRWxCUVVrc1EwRkJReXhaUVVGWkxFZEJRVWNzVjBGQlZ6dGhRVU14UWl4TlFVRk5MRU5CUVVNc1ZVRkJRU3hEUVVGRExFbEJRVWtzVDBGQlFTeERRVUZETEVOQlFVTXNTVUZCU1N4TFFVRkxMRWRCUVVjc1NVRkJTU3hMUVVGTExFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFURkNMRU5CUVRCQ0xFTkJRVU03WVVGRGRrTXNSMEZCUnl4RFFVRkRMRlZCUVVFc1EwRkJReXhKUVVGSkxFOUJRVUVzUzBGQlNTeERRVUZETEdkQ1FVRm5RaXhEUVVGRExFTkJRVU1zUTBGQlF5eEZRVUY0UWl4RFFVRjNRaXhEUVVGRExFTkJRVU03VVVGRGVFTXNWMEZCVnp0aFFVTk9MRTFCUVUwc1EwRkJReXhWUVVGQkxFTkJRVU1zU1VGQlNTeFBRVUZCTEVOQlFVTXNRMEZCUXl4SlFVRkpMRXRCUVVzc1YwRkJWeXhGUVVGMFFpeERRVUZ6UWl4RFFVRkRPMkZCUTI1RExFOUJRVThzUTBGQlF5eFZRVUZCTEVOQlFVTXNTVUZCU1N4UFFVRkJMRXRCUVVrc1EwRkJReXhsUVVGbExFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFYWkNMRU5CUVhWQ0xFTkJRVU1zUTBGQlF6dEpRVU12UXl4RFFVRkRPMGxCUlU4c05FTkJRWFZDTEVkQlFTOUNMRlZCUVdkRExFVkJRVmtzUlVGQlJTeEZRVUZaTEVWQlFVVXNUMEZCYVVJc1JVRkJSU3hWUVVGdlF6dFJRVU12Unl4SlFVRkpMRU5CUVVNc1MwRkJTeXhEUVVGRExFOUJRVThzUTBGQlF5eFZRVUZETEVOQlFVTXNSVUZCUlN4RFFVRkRPMWxCUTNCQ0xFbEJRVWtzUTBGQlF5eERRVUZETEV0QlFVc3NSVUZCUlR0blFrRkRWQ3hEUVVGRExFTkJRVU1zVVVGQlVTeERRVUZETEUxQlFVMHNSMEZCUnl4RFFVRkRMRU5CUVVNc1YwRkJWeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNWMEZCVnl4RFFVRkRMRU5CUVVNc1EwRkJReXhKUVVGSkxFTkJRVU03WjBKQlEzcEVMRTlCUVU4c1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlJ5eFZRVUZWTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1lVRkRPVUk3YVVKQlFVMDdaMEpCUTBnc1EwRkJReXhEUVVGRExGRkJRVkVzUTBGQlF5eE5RVUZOTEVkQlFVY3NRMEZCUXl4RFFVRkRPMkZCUTNwQ08xbEJRMFFzU1VGQlNTeERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1MwRkJTeXhKUVVGSkxFTkJRVU1zUTBGQlF5eEhRVUZITEVOQlFVTXNSVUZCUlN4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zVFVGQlRTeEpRVUZKTEVOQlFVTXNRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJRenRaUVVOd1JDeEpRVUZKTEVWQlFVVXNSMEZCUnl4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRVVVzUlVGQlJTeEhRVUZITEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRaUVVNelFpeERRVUZETEVOQlFVTXNUVUZCVFN4SFFVRkhMRWxCUVVrc1UwRkJVeXhEUVVGRExFVkJRVVVzUjBGQlJ5eERRVUZETEVWQlFVVXNSVUZCUlN4SFFVRkhMRU5CUVVNc1JVRkJSU3hGUVVGRkxFZEJRVWNzUTBGQlF5eEZRVUZGTEVWQlFVVXNSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJRenRSUVVNM1JDeERRVUZETEVOQlFVTXNRMEZCUXp0SlFVTlFMRU5CUVVNN1NVRkZSQ3cyUWtGQlVTeEhRVUZTTEZWQlFWTXNSVUZCV1N4RlFVRkZMRVZCUVZrc1JVRkJSU3hEUVVGWE8xRkJRelZETEVsQlFVa3NRMEZCUXl4SlFVRkpMRU5CUVVNc1UwRkJVeXhKUVVGSkxFTkJRVU1zUTBGQlF5eEpRVUZKTEVOQlFVTXNZVUZCWVN4SlFVRkpMRWxCUVVrc1EwRkJReXhaUVVGWkxFTkJRVU03V1VGQlJTeFBRVUZQTzFGQlF6RkZMRWxCUVVrc1EwRkJReXhQUVVGUExFTkJRVU1zUlVGQlJTeEZRVUZGTEVWQlFVVXNSVUZCUlN4RlFVRkZMRVZCUVVVc1EwRkJReXhGUVVGRkxGVkJRVUVzUTBGQlF5eEpRVUZITEU5QlFVRXNRMEZCUXl4RFFVRkRMRVZCUVVVc1JVRkJTaXhEUVVGSkxFVkJRVVVzU1VGQlNTeERRVUZETEZsQlFWa3NSVUZCUlN4NVFrRkJlVUlzUlVGRE9VVXNWVUZCUVN4RFFVRkRMRWxCUVVrc1QwRkJRU3hEUVVGRExFTkJRVU1zVFVGQlRTeERRVUZETEZWQlFWVXNRMEZCUXl4RFFVRkRMRU5CUVcxQ0xFTkJRVU1zUTBGQlF5eFJRVUZUTEVOQlFVTXNTMEZCU3l4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExGRkJRVkVzUTBGQlF5eFJRVUZSTEVWQlFVVXNRMEZCUXl4RlFVRnVSaXhEUVVGdFJpeEZRVU40Uml4VlFVRkJMRU5CUVVNN1dVRkRSeXhKUVVGSkxFbEJRVWtzUjBGQlJ5eERRVUZETEVOQlFXMUNMRU5CUVVNc1EwRkJReXhOUVVGUExFTkJRVU1zUzBGQlN5eERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRTFCUVUwc1EwRkJReXhSUVVGUkxFVkJRVVVzUTBGQlF6dFpRVU4wUlN4SlFVRkpMRWxCUVVrc1IwRkJSeXhEUVVGRExFTkJRVzFDTEVOQlFVTXNRMEZCUXl4TlFVRlBMRU5CUVVNc1MwRkJTeXhEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETEUxQlFVMHNRMEZCUXl4UlFVRlJMRVZCUVVVc1EwRkJRenRaUVVOMFJTeEpRVUZKTEVWQlFVVXNSMEZCUnl4RFFVRkRMRU5CUVVNc1QwRkJUeXhIUVVGSExFTkJRVU1zUTBGQlF6dFpRVU4yUWl4RFFVRkRMRU5CUVVNc1RVRkJUU3hEUVVGRExFTkJRVU1zUjBGQlJ5eEpRVUZKTEVkQlFVY3NSVUZCUlN4RFFVRkRPMWxCUTNaQ0xFTkJRVU1zUTBGQlF5eE5RVUZOTEVOQlFVTXNRMEZCUXl4SFFVRkhMRWxCUVVrc1IwRkJSeXhGUVVGRkxFTkJRVU03VVVGRE0wSXNRMEZCUXl4RFFVRkRMRU5CUVVNN1NVRkRXQ3hEUVVGRE8wbEJSVVFzTmtKQlFWRXNSMEZCVWl4VlFVRlRMRVZCUVZrc1JVRkJSU3hGUVVGWkxFVkJRVVVzUTBGQlZ6dFJRVU0xUXl4SlFVRkpMRU5CUVVNc1NVRkJTU3hEUVVGRExGTkJRVk1zU1VGQlNTeERRVUZETEVsQlFVa3NRMEZCUXl4WlFVRlpPMWxCUVVVc1QwRkJUenRSUVVOc1JDeEpRVUZKTEVOQlFVTXNUMEZCVHl4RFFVRkRMRVZCUVVVc1JVRkJSU3hGUVVGRkxFVkJRVVVzUlVGQlJTeEZRVUZGTEVOQlFVTXNSVUZCUlN4VlFVRkJMRU5CUVVNc1NVRkJSeXhQUVVGQkxFTkJRVU1zUTBGQlF5eEZRVUZGTEVWQlFVb3NRMEZCU1N4RlFVRkZMRWxCUVVrc1EwRkJReXhaUVVGWkxFVkJRVVVzZVVKQlFYbENMRVZCUXpsRkxGVkJRVUVzUTBGQlF5eEpRVUZKTEU5QlFVRXNRMEZCUXl4RFFVRkRMRTFCUVUwc1EwRkJReXhWUVVGVkxFTkJRVU1zUTBGQlF5eERRVUZ0UWl4RFFVRkRMRU5CUVVNc1VVRkJVeXhEUVVGRExFdEJRVXNzUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXl4UlFVRlJMRU5CUVVNc1VVRkJVU3hGUVVGRkxFTkJRVU1zUlVGQmJrWXNRMEZCYlVZc1JVRkRlRVlzVlVGQlFTeERRVUZETzFsQlEwY3NTVUZCU1N4SlFVRkpMRWRCUVVjc1EwRkJReXhEUVVGdFFpeERRVUZETEVOQlFVTXNUVUZCVHl4RFFVRkRMRXRCUVVzc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eE5RVUZOTEVOQlFVTXNVVUZCVVN4RlFVRkZMRU5CUVVNN1dVRkRkRVVzU1VGQlNTeEpRVUZKTEVkQlFVY3NRMEZCUXl4RFFVRnRRaXhEUVVGRExFTkJRVU1zVFVGQlR5eERRVUZETEV0QlFVc3NRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJReXhOUVVGTkxFTkJRVU1zVVVGQlVTeEZRVUZGTEVOQlFVTTdXVUZEZEVVc1NVRkJTU3hGUVVGRkxFZEJRVWNzUTBGQlF5eERRVUZETEU5QlFVOHNSMEZCUnl4RFFVRkRMRU5CUVVNN1dVRkRka0lzUTBGQlF5eERRVUZETEUxQlFVMHNRMEZCUXl4RFFVRkRMRWRCUVVjc1NVRkJTU3hIUVVGSExFVkJRVVVzUTBGQlF6dFpRVUZCTEVOQlFVTTdXVUZEZUVJc1EwRkJReXhEUVVGRExFMUJRVTBzUTBGQlF5eERRVUZETEVkQlFVY3NTVUZCU1N4SFFVRkhMRVZCUVVVc1EwRkJRenRSUVVNelFpeERRVUZETEVOQlFVTXNRMEZCUXp0SlFVTllMRU5CUVVNN1NVRkZSQ3h4UTBGQlowSXNSMEZCYUVJN1VVRkJRU3hwUWtGTFF6dFJRVXBITEU5QlFVODdXVUZEU0N4VlFVRkRMRVZCUVVVc1JVRkJSU3hGUVVGRkxFVkJRVVVzUTBGQlF5eEpRVUZMTEU5QlFVRXNTMEZCU1N4RFFVRkRMRkZCUVZFc1EwRkJReXhGUVVGRkxFVkJRVVVzUlVGQlJTeEZRVUZGTEVOQlFVTXNRMEZCUXl4RlFVRjRRaXhEUVVGM1FqdFpRVU4yUXl4VlFVRkRMRVZCUVVVc1JVRkJSU3hGUVVGRkxFVkJRVVVzUTBGQlF5eEpRVUZMTEU5QlFVRXNTMEZCU1N4RFFVRkRMRkZCUVZFc1EwRkJReXhGUVVGRkxFVkJRVVVzUlVGQlJTeEZRVUZGTEVOQlFVTXNRMEZCUXl4RlFVRjRRaXhEUVVGM1FqdFRRVU14UXl4RFFVRkRPMGxCUTA0c1EwRkJRenRKUVVWUExEUkNRVUZQTEVkQlFXWXNWVUZCWjBJc1JVRkJXU3hGUVVGRkxFVkJRVmtzUlVGQlJTeExRVUZsTEVWQlFVVXNUMEZCYVVJc1JVRkRNVVVzVlVGQmIwTXNSVUZEY0VNc1JVRkJaMElzUlVGRGFFSXNiVUpCUVhsRUxFVkJRM3BFTEdkQ1FVRjFReXhGUVVOMlF5eHBRa0ZCT0VNN1VVRkZPVU1zU1VGQlNTeERRVUZETEhWQ1FVRjFRaXhEUVVGRExFVkJRVVVzUlVGQlJTeEZRVUZGTEVWQlFVVXNUMEZCVHl4RlFVRkZMRlZCUVZVc1EwRkJReXhEUVVGRE8xRkJRekZFTEVsQlFVa3NTVUZCU1N4RFFVRkRMRk5CUVZNc1NVRkJTU3hKUVVGSkxFTkJRVU1zWVVGQllTeEZRVUZGTzFsQlEzUkRMR3RDUVVGclFpeERRVUZETEVsQlFVa3NRMEZCUXl4VFFVRlRMRU5CUVVNc1EwRkJRenRaUVVOdVF5eEZRVUZGTEVkQlFVY3NSVUZCUlN4RFFVRkRMRTFCUVUwc1EwRkJReXh0UWtGQmJVSXNRMEZCUXl4SlFVRkpMRU5CUVVNc1UwRkJVeXhEUVVGRExFTkJRVU1zUTBGQlF6dFRRVU4yUkR0UlFVTkVMRWxCUVVrc1EwRkJReXhMUVVGTExFTkJRVU1zU1VGQlNTeERRVUZETEZOQlFWTXNSVUZCUlN4RlFVRkZMRVZCUVVVc1MwRkJTeXhGUVVGRkxFOUJRVThzUTBGQlF5eERRVUZETzFGQlF5OURMRWxCUVVrc1EwRkJReXhMUVVGTExFTkJRVU1zVDBGQlR5eERRVUZETEdkQ1FVRm5RaXhEUVVGRExFTkJRVU03VVVGRGNrTXNTVUZCU1N4SlFVRkpMRU5CUVVNc1UwRkJVeXhKUVVGSkxFbEJRVWtzUTBGQlF5eGhRVUZoTEVWQlFVVTdXVUZEZEVNc1NVRkJTU3hEUVVGRExFMUJRVTBzUTBGQlF5eFBRVUZQTEVOQlFVTXNhVUpCUVdsQ0xFTkJRVU1zUTBGQlF6dFpRVU4yUXl4clFrRkJhMElzUTBGQlF5eEpRVUZKTEVOQlFVTXNVMEZCVXl4RFFVRkRMRU5CUVVNN1UwRkRkRU03U1VGRFRDeERRVUZETzBsQlJVOHNNRUpCUVVzc1IwRkJZaXhWUVVGakxFVkJRV01zUlVGQlJTeEZRVUZuUWl4RlFVRkZMRkZCUVd0Q0xFVkJRVVVzVDBGQmFVSTdVVUZEYWtZc1NVRkJTU3hOUVVGTkxFZEJRVWNzU1VGQlNTeGhRVUZOTEVOQlFVTXNSVUZCUlN4RlFVRkZMRVZCUVVVc1EwRkJReXhEUVVGRE8xRkJRMmhETEUxQlFVMHNRMEZCUXl4dlFrRkJiMElzUTBGQlF5eFJRVUZSTEVOQlFVTXNRMEZCUXp0UlFVTjBReXhOUVVGTkxFTkJRVU1zYlVKQlFXMUNMRU5CUVVNc1QwRkJUeXhEUVVGRExFTkJRVU03VVVGRGNFTXNUVUZCVFN4RFFVRkRMRXRCUVVzc1JVRkJSU3hEUVVGRE8wbEJRMjVDTEVOQlFVTTdTVUZEVEN4cFFrRkJRenRCUVVGRUxFTkJRVU1zUVVGc1MwUXNTVUZyUzBNN1FVRnNTMWtzWjBOQlFWVWlmUT09IiwiXCJ1c2Ugc3RyaWN0XCI7XHJcbk9iamVjdC5kZWZpbmVQcm9wZXJ0eShleHBvcnRzLCBcIl9fZXNNb2R1bGVcIiwgeyB2YWx1ZTogdHJ1ZSB9KTtcclxudmFyIHBxdWV1ZV8xID0gcmVxdWlyZShcIi4vcHF1ZXVlXCIpO1xyXG52YXIgTmVpZ2hib3VyID0gKGZ1bmN0aW9uICgpIHtcclxuICAgIGZ1bmN0aW9uIE5laWdoYm91cihpZCwgZGlzdGFuY2UpIHtcclxuICAgICAgICB0aGlzLmlkID0gaWQ7XHJcbiAgICAgICAgdGhpcy5kaXN0YW5jZSA9IGRpc3RhbmNlO1xyXG4gICAgfVxyXG4gICAgcmV0dXJuIE5laWdoYm91cjtcclxufSgpKTtcclxudmFyIE5vZGUgPSAoZnVuY3Rpb24gKCkge1xyXG4gICAgZnVuY3Rpb24gTm9kZShpZCkge1xyXG4gICAgICAgIHRoaXMuaWQgPSBpZDtcclxuICAgICAgICB0aGlzLm5laWdoYm91cnMgPSBbXTtcclxuICAgIH1cclxuICAgIHJldHVybiBOb2RlO1xyXG59KCkpO1xyXG52YXIgUXVldWVFbnRyeSA9IChmdW5jdGlvbiAoKSB7XHJcbiAgICBmdW5jdGlvbiBRdWV1ZUVudHJ5KG5vZGUsIHByZXYsIGQpIHtcclxuICAgICAgICB0aGlzLm5vZGUgPSBub2RlO1xyXG4gICAgICAgIHRoaXMucHJldiA9IHByZXY7XHJcbiAgICAgICAgdGhpcy5kID0gZDtcclxuICAgIH1cclxuICAgIHJldHVybiBRdWV1ZUVudHJ5O1xyXG59KCkpO1xyXG52YXIgQ2FsY3VsYXRvciA9IChmdW5jdGlvbiAoKSB7XHJcbiAgICBmdW5jdGlvbiBDYWxjdWxhdG9yKG4sIGVzLCBnZXRTb3VyY2VJbmRleCwgZ2V0VGFyZ2V0SW5kZXgsIGdldExlbmd0aCkge1xyXG4gICAgICAgIHRoaXMubiA9IG47XHJcbiAgICAgICAgdGhpcy5lcyA9IGVzO1xyXG4gICAgICAgIHRoaXMubmVpZ2hib3VycyA9IG5ldyBBcnJheSh0aGlzLm4pO1xyXG4gICAgICAgIHZhciBpID0gdGhpcy5uO1xyXG4gICAgICAgIHdoaWxlIChpLS0pXHJcbiAgICAgICAgICAgIHRoaXMubmVpZ2hib3Vyc1tpXSA9IG5ldyBOb2RlKGkpO1xyXG4gICAgICAgIGkgPSB0aGlzLmVzLmxlbmd0aDtcclxuICAgICAgICB3aGlsZSAoaS0tKSB7XHJcbiAgICAgICAgICAgIHZhciBlID0gdGhpcy5lc1tpXTtcclxuICAgICAgICAgICAgdmFyIHUgPSBnZXRTb3VyY2VJbmRleChlKSwgdiA9IGdldFRhcmdldEluZGV4KGUpO1xyXG4gICAgICAgICAgICB2YXIgZCA9IGdldExlbmd0aChlKTtcclxuICAgICAgICAgICAgdGhpcy5uZWlnaGJvdXJzW3VdLm5laWdoYm91cnMucHVzaChuZXcgTmVpZ2hib3VyKHYsIGQpKTtcclxuICAgICAgICAgICAgdGhpcy5uZWlnaGJvdXJzW3ZdLm5laWdoYm91cnMucHVzaChuZXcgTmVpZ2hib3VyKHUsIGQpKTtcclxuICAgICAgICB9XHJcbiAgICB9XHJcbiAgICBDYWxjdWxhdG9yLnByb3RvdHlwZS5EaXN0YW5jZU1hdHJpeCA9IGZ1bmN0aW9uICgpIHtcclxuICAgICAgICB2YXIgRCA9IG5ldyBBcnJheSh0aGlzLm4pO1xyXG4gICAgICAgIGZvciAodmFyIGkgPSAwOyBpIDwgdGhpcy5uOyArK2kpIHtcclxuICAgICAgICAgICAgRFtpXSA9IHRoaXMuZGlqa3N0cmFOZWlnaGJvdXJzKGkpO1xyXG4gICAgICAgIH1cclxuICAgICAgICByZXR1cm4gRDtcclxuICAgIH07XHJcbiAgICBDYWxjdWxhdG9yLnByb3RvdHlwZS5EaXN0YW5jZXNGcm9tTm9kZSA9IGZ1bmN0aW9uIChzdGFydCkge1xyXG4gICAgICAgIHJldHVybiB0aGlzLmRpamtzdHJhTmVpZ2hib3VycyhzdGFydCk7XHJcbiAgICB9O1xyXG4gICAgQ2FsY3VsYXRvci5wcm90b3R5cGUuUGF0aEZyb21Ob2RlVG9Ob2RlID0gZnVuY3Rpb24gKHN0YXJ0LCBlbmQpIHtcclxuICAgICAgICByZXR1cm4gdGhpcy5kaWprc3RyYU5laWdoYm91cnMoc3RhcnQsIGVuZCk7XHJcbiAgICB9O1xyXG4gICAgQ2FsY3VsYXRvci5wcm90b3R5cGUuUGF0aEZyb21Ob2RlVG9Ob2RlV2l0aFByZXZDb3N0ID0gZnVuY3Rpb24gKHN0YXJ0LCBlbmQsIHByZXZDb3N0KSB7XHJcbiAgICAgICAgdmFyIHEgPSBuZXcgcHF1ZXVlXzEuUHJpb3JpdHlRdWV1ZShmdW5jdGlvbiAoYSwgYikgeyByZXR1cm4gYS5kIDw9IGIuZDsgfSksIHUgPSB0aGlzLm5laWdoYm91cnNbc3RhcnRdLCBxdSA9IG5ldyBRdWV1ZUVudHJ5KHUsIG51bGwsIDApLCB2aXNpdGVkRnJvbSA9IHt9O1xyXG4gICAgICAgIHEucHVzaChxdSk7XHJcbiAgICAgICAgd2hpbGUgKCFxLmVtcHR5KCkpIHtcclxuICAgICAgICAgICAgcXUgPSBxLnBvcCgpO1xyXG4gICAgICAgICAgICB1ID0gcXUubm9kZTtcclxuICAgICAgICAgICAgaWYgKHUuaWQgPT09IGVuZCkge1xyXG4gICAgICAgICAgICAgICAgYnJlYWs7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgdmFyIGkgPSB1Lm5laWdoYm91cnMubGVuZ3RoO1xyXG4gICAgICAgICAgICB3aGlsZSAoaS0tKSB7XHJcbiAgICAgICAgICAgICAgICB2YXIgbmVpZ2hib3VyID0gdS5uZWlnaGJvdXJzW2ldLCB2ID0gdGhpcy5uZWlnaGJvdXJzW25laWdoYm91ci5pZF07XHJcbiAgICAgICAgICAgICAgICBpZiAocXUucHJldiAmJiB2LmlkID09PSBxdS5wcmV2Lm5vZGUuaWQpXHJcbiAgICAgICAgICAgICAgICAgICAgY29udGludWU7XHJcbiAgICAgICAgICAgICAgICB2YXIgdmlkdWlkID0gdi5pZCArICcsJyArIHUuaWQ7XHJcbiAgICAgICAgICAgICAgICBpZiAodmlkdWlkIGluIHZpc2l0ZWRGcm9tICYmIHZpc2l0ZWRGcm9tW3ZpZHVpZF0gPD0gcXUuZClcclxuICAgICAgICAgICAgICAgICAgICBjb250aW51ZTtcclxuICAgICAgICAgICAgICAgIHZhciBjYyA9IHF1LnByZXYgPyBwcmV2Q29zdChxdS5wcmV2Lm5vZGUuaWQsIHUuaWQsIHYuaWQpIDogMCwgdCA9IHF1LmQgKyBuZWlnaGJvdXIuZGlzdGFuY2UgKyBjYztcclxuICAgICAgICAgICAgICAgIHZpc2l0ZWRGcm9tW3ZpZHVpZF0gPSB0O1xyXG4gICAgICAgICAgICAgICAgcS5wdXNoKG5ldyBRdWV1ZUVudHJ5KHYsIHF1LCB0KSk7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICB9XHJcbiAgICAgICAgdmFyIHBhdGggPSBbXTtcclxuICAgICAgICB3aGlsZSAocXUucHJldikge1xyXG4gICAgICAgICAgICBxdSA9IHF1LnByZXY7XHJcbiAgICAgICAgICAgIHBhdGgucHVzaChxdS5ub2RlLmlkKTtcclxuICAgICAgICB9XHJcbiAgICAgICAgcmV0dXJuIHBhdGg7XHJcbiAgICB9O1xyXG4gICAgQ2FsY3VsYXRvci5wcm90b3R5cGUuZGlqa3N0cmFOZWlnaGJvdXJzID0gZnVuY3Rpb24gKHN0YXJ0LCBkZXN0KSB7XHJcbiAgICAgICAgaWYgKGRlc3QgPT09IHZvaWQgMCkgeyBkZXN0ID0gLTE7IH1cclxuICAgICAgICB2YXIgcSA9IG5ldyBwcXVldWVfMS5Qcmlvcml0eVF1ZXVlKGZ1bmN0aW9uIChhLCBiKSB7IHJldHVybiBhLmQgPD0gYi5kOyB9KSwgaSA9IHRoaXMubmVpZ2hib3Vycy5sZW5ndGgsIGQgPSBuZXcgQXJyYXkoaSk7XHJcbiAgICAgICAgd2hpbGUgKGktLSkge1xyXG4gICAgICAgICAgICB2YXIgbm9kZSA9IHRoaXMubmVpZ2hib3Vyc1tpXTtcclxuICAgICAgICAgICAgbm9kZS5kID0gaSA9PT0gc3RhcnQgPyAwIDogTnVtYmVyLlBPU0lUSVZFX0lORklOSVRZO1xyXG4gICAgICAgICAgICBub2RlLnEgPSBxLnB1c2gobm9kZSk7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIHdoaWxlICghcS5lbXB0eSgpKSB7XHJcbiAgICAgICAgICAgIHZhciB1ID0gcS5wb3AoKTtcclxuICAgICAgICAgICAgZFt1LmlkXSA9IHUuZDtcclxuICAgICAgICAgICAgaWYgKHUuaWQgPT09IGRlc3QpIHtcclxuICAgICAgICAgICAgICAgIHZhciBwYXRoID0gW107XHJcbiAgICAgICAgICAgICAgICB2YXIgdiA9IHU7XHJcbiAgICAgICAgICAgICAgICB3aGlsZSAodHlwZW9mIHYucHJldiAhPT0gJ3VuZGVmaW5lZCcpIHtcclxuICAgICAgICAgICAgICAgICAgICBwYXRoLnB1c2godi5wcmV2LmlkKTtcclxuICAgICAgICAgICAgICAgICAgICB2ID0gdi5wcmV2O1xyXG4gICAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICAgICAgcmV0dXJuIHBhdGg7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgaSA9IHUubmVpZ2hib3Vycy5sZW5ndGg7XHJcbiAgICAgICAgICAgIHdoaWxlIChpLS0pIHtcclxuICAgICAgICAgICAgICAgIHZhciBuZWlnaGJvdXIgPSB1Lm5laWdoYm91cnNbaV07XHJcbiAgICAgICAgICAgICAgICB2YXIgdiA9IHRoaXMubmVpZ2hib3Vyc1tuZWlnaGJvdXIuaWRdO1xyXG4gICAgICAgICAgICAgICAgdmFyIHQgPSB1LmQgKyBuZWlnaGJvdXIuZGlzdGFuY2U7XHJcbiAgICAgICAgICAgICAgICBpZiAodS5kICE9PSBOdW1iZXIuTUFYX1ZBTFVFICYmIHYuZCA+IHQpIHtcclxuICAgICAgICAgICAgICAgICAgICB2LmQgPSB0O1xyXG4gICAgICAgICAgICAgICAgICAgIHYucHJldiA9IHU7XHJcbiAgICAgICAgICAgICAgICAgICAgcS5yZWR1Y2VLZXkodi5xLCB2LCBmdW5jdGlvbiAoZSwgcSkgeyByZXR1cm4gZS5xID0gcTsgfSk7XHJcbiAgICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICB9XHJcbiAgICAgICAgcmV0dXJuIGQ7XHJcbiAgICB9O1xyXG4gICAgcmV0dXJuIENhbGN1bGF0b3I7XHJcbn0oKSk7XHJcbmV4cG9ydHMuQ2FsY3VsYXRvciA9IENhbGN1bGF0b3I7XHJcbi8vIyBzb3VyY2VNYXBwaW5nVVJMPWRhdGE6YXBwbGljYXRpb24vanNvbjtiYXNlNjQsZXlKMlpYSnphVzl1SWpvekxDSm1hV3hsSWpvaWMyaHZjblJsYzNSd1lYUm9jeTVxY3lJc0luTnZkWEpqWlZKdmIzUWlPaUlpTENKemIzVnlZMlZ6SWpwYklpNHVMeTR1TDFkbFlrTnZiR0V2YzNKakwzTm9iM0owWlhOMGNHRjBhSE11ZEhNaVhTd2libUZ0WlhNaU9sdGRMQ0p0WVhCd2FXNW5jeUk2SWpzN1FVRkJRU3h0UTBGQmJVUTdRVUZGYmtRN1NVRkRTU3h0UWtGQmJVSXNSVUZCVlN4RlFVRlRMRkZCUVdkQ08xRkJRVzVETEU5QlFVVXNSMEZCUml4RlFVRkZMRU5CUVZFN1VVRkJVeXhoUVVGUkxFZEJRVklzVVVGQlVTeERRVUZSTzBsQlFVa3NRMEZCUXp0SlFVTXZSQ3huUWtGQlF6dEJRVUZFTEVOQlFVTXNRVUZHUkN4SlFVVkRPMEZCUlVRN1NVRkRTU3hqUVVGdFFpeEZRVUZWTzFGQlFWWXNUMEZCUlN4SFFVRkdMRVZCUVVVc1EwRkJVVHRSUVVONlFpeEpRVUZKTEVOQlFVTXNWVUZCVlN4SFFVRkhMRVZCUVVVc1EwRkJRenRKUVVONlFpeERRVUZETzBsQlMwd3NWMEZCUXp0QlFVRkVMRU5CUVVNc1FVRlNSQ3hKUVZGRE8wRkJSVVE3U1VGRFNTeHZRa0ZCYlVJc1NVRkJWU3hGUVVGVExFbEJRV2RDTEVWQlFWTXNRMEZCVXp0UlFVRnlSQ3hUUVVGSkxFZEJRVW9zU1VGQlNTeERRVUZOTzFGQlFWTXNVMEZCU1N4SFFVRktMRWxCUVVrc1EwRkJXVHRSUVVGVExFMUJRVU1zUjBGQlJDeERRVUZETEVOQlFWRTdTVUZCUnl4RFFVRkRPMGxCUTJoR0xHbENRVUZETzBGQlFVUXNRMEZCUXl4QlFVWkVMRWxCUlVNN1FVRlRSRHRKUVVkSkxHOUNRVUZ0UWl4RFFVRlRMRVZCUVZNc1JVRkJWU3hGUVVGRkxHTkJRVzFETEVWQlFVVXNZMEZCYlVNc1JVRkJSU3hUUVVFNFFqdFJRVUYwU1N4TlFVRkRMRWRCUVVRc1EwRkJReXhEUVVGUk8xRkJRVk1zVDBGQlJTeEhRVUZHTEVWQlFVVXNRMEZCVVR0UlFVTXpReXhKUVVGSkxFTkJRVU1zVlVGQlZTeEhRVUZITEVsQlFVa3NTMEZCU3l4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFJRVU53UXl4SlFVRkpMRU5CUVVNc1IwRkJSeXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETzFGQlFVTXNUMEZCVHl4RFFVRkRMRVZCUVVVN1dVRkJSU3hKUVVGSkxFTkJRVU1zVlVGQlZTeERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRWxCUVVrc1NVRkJTU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzFGQlJUZEVMRU5CUVVNc1IwRkJSeXhKUVVGSkxFTkJRVU1zUlVGQlJTeERRVUZETEUxQlFVMHNRMEZCUXp0UlFVRkRMRTlCUVU4c1EwRkJReXhGUVVGRkxFVkJRVVU3V1VGRE5VSXNTVUZCU1N4RFFVRkRMRWRCUVVjc1NVRkJTU3hEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0WlFVTnVRaXhKUVVGSkxFTkJRVU1zUjBGQlZ5eGpRVUZqTEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhIUVVGWExHTkJRV01zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0WlFVTnFSU3hKUVVGSkxFTkJRVU1zUjBGQlJ5eFRRVUZUTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1dVRkRja0lzU1VGQlNTeERRVUZETEZWQlFWVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhWUVVGVkxFTkJRVU1zU1VGQlNTeERRVUZETEVsQlFVa3NVMEZCVXl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzFsQlEzaEVMRWxCUVVrc1EwRkJReXhWUVVGVkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNWVUZCVlN4RFFVRkRMRWxCUVVrc1EwRkJReXhKUVVGSkxGTkJRVk1zUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRUUVVNelJEdEpRVU5NTEVOQlFVTTdTVUZWUkN4dFEwRkJZeXhIUVVGa08xRkJRMGtzU1VGQlNTeERRVUZETEVkQlFVY3NTVUZCU1N4TFFVRkxMRU5CUVVNc1NVRkJTU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzFGQlF6RkNMRXRCUVVzc1NVRkJTU3hEUVVGRExFZEJRVWNzUTBGQlF5eEZRVUZGTEVOQlFVTXNSMEZCUnl4SlFVRkpMRU5CUVVNc1EwRkJReXhGUVVGRkxFVkJRVVVzUTBGQlF5eEZRVUZGTzFsQlF6ZENMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlJ5eEpRVUZKTEVOQlFVTXNhMEpCUVd0Q0xFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdVMEZEY2tNN1VVRkRSQ3hQUVVGUExFTkJRVU1zUTBGQlF6dEpRVU5pTEVOQlFVTTdTVUZSUkN4elEwRkJhVUlzUjBGQmFrSXNWVUZCYTBJc1MwRkJZVHRSUVVNelFpeFBRVUZQTEVsQlFVa3NRMEZCUXl4clFrRkJhMElzUTBGQlF5eExRVUZMTEVOQlFVTXNRMEZCUXp0SlFVTXhReXhEUVVGRE8wbEJSVVFzZFVOQlFXdENMRWRCUVd4Q0xGVkJRVzFDTEV0QlFXRXNSVUZCUlN4SFFVRlhPMUZCUTNwRExFOUJRVThzU1VGQlNTeERRVUZETEd0Q1FVRnJRaXhEUVVGRExFdEJRVXNzUlVGQlJTeEhRVUZITEVOQlFVTXNRMEZCUXp0SlFVTXZReXhEUVVGRE8wbEJTMFFzYlVSQlFUaENMRWRCUVRsQ0xGVkJRMGtzUzBGQllTeEZRVU5pTEVkQlFWY3NSVUZEV0N4UlFVRTRRenRSUVVVNVF5eEpRVUZKTEVOQlFVTXNSMEZCUnl4SlFVRkpMSE5DUVVGaExFTkJRV0VzVlVGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4SlFVRkxMRTlCUVVFc1EwRkJReXhEUVVGRExFTkJRVU1zU1VGQlNTeERRVUZETEVOQlFVTXNRMEZCUXl4RlFVRldMRU5CUVZVc1EwRkJReXhGUVVOMlJDeERRVUZETEVkQlFWTXNTVUZCU1N4RFFVRkRMRlZCUVZVc1EwRkJReXhMUVVGTExFTkJRVU1zUlVGRGFFTXNSVUZCUlN4SFFVRmxMRWxCUVVrc1ZVRkJWU3hEUVVGRExFTkJRVU1zUlVGQlF5eEpRVUZKTEVWQlFVTXNRMEZCUXl4RFFVRkRMRVZCUTNwRExGZEJRVmNzUjBGQlJ5eEZRVUZGTEVOQlFVTTdVVUZEY2tJc1EwRkJReXhEUVVGRExFbEJRVWtzUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXp0UlFVTllMRTlCUVUwc1EwRkJReXhEUVVGRExFTkJRVU1zUzBGQlN5eEZRVUZGTEVWQlFVVTdXVUZEWkN4RlFVRkZMRWRCUVVjc1EwRkJReXhEUVVGRExFZEJRVWNzUlVGQlJTeERRVUZETzFsQlEySXNRMEZCUXl4SFFVRkhMRVZCUVVVc1EwRkJReXhKUVVGSkxFTkJRVU03V1VGRFdpeEpRVUZKTEVOQlFVTXNRMEZCUXl4RlFVRkZMRXRCUVVzc1IwRkJSeXhGUVVGRk8yZENRVU5rTEUxQlFVMDdZVUZEVkR0WlFVTkVMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eFZRVUZWTEVOQlFVTXNUVUZCVFN4RFFVRkRPMWxCUVVNc1QwRkJUeXhEUVVGRExFVkJRVVVzUlVGQlJUdG5Ra0ZEY2tNc1NVRkJTU3hUUVVGVExFZEJRVWNzUTBGQlF5eERRVUZETEZWQlFWVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkRNMElzUTBGQlF5eEhRVUZITEVsQlFVa3NRMEZCUXl4VlFVRlZMRU5CUVVNc1UwRkJVeXhEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETzJkQ1FVZDBReXhKUVVGSkxFVkJRVVVzUTBGQlF5eEpRVUZKTEVsQlFVa3NRMEZCUXl4RFFVRkRMRVZCUVVVc1MwRkJTeXhGUVVGRkxFTkJRVU1zU1VGQlNTeERRVUZETEVsQlFVa3NRMEZCUXl4RlFVRkZPMjlDUVVGRkxGTkJRVk03WjBKQlNXeEVMRWxCUVVrc1RVRkJUU3hIUVVGSExFTkJRVU1zUTBGQlF5eEZRVUZGTEVkQlFVY3NSMEZCUnl4SFFVRkhMRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU03WjBKQlF5OUNMRWxCUVVjc1RVRkJUU3hKUVVGSkxGZEJRVmNzU1VGQlNTeFhRVUZYTEVOQlFVTXNUVUZCVFN4RFFVRkRMRWxCUVVrc1JVRkJSU3hEUVVGRExFTkJRVU03YjBKQlEyNUVMRk5CUVZNN1owSkJSV0lzU1VGQlNTeEZRVUZGTEVkQlFVY3NSVUZCUlN4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU1zVVVGQlVTeERRVUZETEVWQlFVVXNRMEZCUXl4SlFVRkpMRU5CUVVNc1NVRkJTU3hEUVVGRExFVkJRVVVzUlVGQlJTeERRVUZETEVOQlFVTXNSVUZCUlN4RlFVRkZMRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RlFVTjRSQ3hEUVVGRExFZEJRVWNzUlVGQlJTeERRVUZETEVOQlFVTXNSMEZCUnl4VFFVRlRMRU5CUVVNc1VVRkJVU3hIUVVGSExFVkJRVVVzUTBGQlF6dG5Ra0ZIZGtNc1YwRkJWeXhEUVVGRExFMUJRVTBzUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXp0blFrRkRlRUlzUTBGQlF5eERRVUZETEVsQlFVa3NRMEZCUXl4SlFVRkpMRlZCUVZVc1EwRkJReXhEUVVGRExFVkJRVVVzUlVGQlJTeEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1lVRkRjRU03VTBGRFNqdFJRVU5FTEVsQlFVa3NTVUZCU1N4SFFVRlpMRVZCUVVVc1EwRkJRenRSUVVOMlFpeFBRVUZQTEVWQlFVVXNRMEZCUXl4SlFVRkpMRVZCUVVVN1dVRkRXaXhGUVVGRkxFZEJRVWNzUlVGQlJTeERRVUZETEVsQlFVa3NRMEZCUXp0WlFVTmlMRWxCUVVrc1EwRkJReXhKUVVGSkxFTkJRVU1zUlVGQlJTeERRVUZETEVsQlFVa3NRMEZCUXl4RlFVRkZMRU5CUVVNc1EwRkJRenRUUVVONlFqdFJRVU5FTEU5QlFVOHNTVUZCU1N4RFFVRkRPMGxCUTJoQ0xFTkJRVU03U1VGRlR5eDFRMEZCYTBJc1IwRkJNVUlzVlVGQk1rSXNTMEZCWVN4RlFVRkZMRWxCUVdsQ08xRkJRV3BDTEhGQ1FVRkJMRVZCUVVFc1VVRkJaMElzUTBGQlF6dFJRVU4yUkN4SlFVRkpMRU5CUVVNc1IwRkJSeXhKUVVGSkxITkNRVUZoTEVOQlFVOHNWVUZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhKUVVGTExFOUJRVUVzUTBGQlF5eERRVUZETEVOQlFVTXNTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGV0xFTkJRVlVzUTBGQlF5eEZRVU5xUkN4RFFVRkRMRWRCUVVjc1NVRkJTU3hEUVVGRExGVkJRVlVzUTBGQlF5eE5RVUZOTEVWQlF6RkNMRU5CUVVNc1IwRkJZU3hKUVVGSkxFdEJRVXNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0UlFVTXZRaXhQUVVGUExFTkJRVU1zUlVGQlJTeEZRVUZGTzFsQlExSXNTVUZCU1N4SlFVRkpMRWRCUVZNc1NVRkJTU3hEUVVGRExGVkJRVlVzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0WlFVTndReXhKUVVGSkxFTkJRVU1zUTBGQlF5eEhRVUZITEVOQlFVTXNTMEZCU3l4TFFVRkxMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNUVUZCVFN4RFFVRkRMR2xDUVVGcFFpeERRVUZETzFsQlEzQkVMRWxCUVVrc1EwRkJReXhEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETEVsQlFVa3NRMEZCUXl4SlFVRkpMRU5CUVVNc1EwRkJRenRUUVVONlFqdFJRVU5FTEU5QlFVOHNRMEZCUXl4RFFVRkRMRU5CUVVNc1MwRkJTeXhGUVVGRkxFVkJRVVU3V1VGRlppeEpRVUZKTEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1IwRkJSeXhGUVVGRkxFTkJRVU03V1VGRGFFSXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMWxCUTJRc1NVRkJTU3hEUVVGRExFTkJRVU1zUlVGQlJTeExRVUZMTEVsQlFVa3NSVUZCUlR0blFrRkRaaXhKUVVGSkxFbEJRVWtzUjBGQllTeEZRVUZGTEVOQlFVTTdaMEpCUTNoQ0xFbEJRVWtzUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXp0blFrRkRWaXhQUVVGUExFOUJRVThzUTBGQlF5eERRVUZETEVsQlFVa3NTMEZCU3l4WFFVRlhMRVZCUVVVN2IwSkJRMnhETEVsQlFVa3NRMEZCUXl4SlFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRExFbEJRVWtzUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXp0dlFrRkRja0lzUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXl4SlFVRkpMRU5CUVVNN2FVSkJRMlE3WjBKQlEwUXNUMEZCVHl4SlFVRkpMRU5CUVVNN1lVRkRaanRaUVVORUxFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNWVUZCVlN4RFFVRkRMRTFCUVUwc1EwRkJRenRaUVVGRExFOUJRVThzUTBGQlF5eEZRVUZGTEVWQlFVVTdaMEpCUTJwRExFbEJRVWtzVTBGQlV5eEhRVUZITEVOQlFVTXNRMEZCUXl4VlFVRlZMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03WjBKQlEyaERMRWxCUVVrc1EwRkJReXhIUVVGSExFbEJRVWtzUTBGQlF5eFZRVUZWTEVOQlFVTXNVMEZCVXl4RFFVRkRMRVZCUVVVc1EwRkJReXhEUVVGRE8yZENRVU4wUXl4SlFVRkpMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF5eEhRVUZITEZOQlFWTXNRMEZCUXl4UlFVRlJMRU5CUVVNN1owSkJRMnBETEVsQlFVa3NRMEZCUXl4RFFVRkRMRU5CUVVNc1MwRkJTeXhOUVVGTkxFTkJRVU1zVTBGQlV5eEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRk8yOUNRVU55UXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF6dHZRa0ZEVWl4RFFVRkRMRU5CUVVNc1NVRkJTU3hIUVVGSExFTkJRVU1zUTBGQlF6dHZRa0ZEV0N4RFFVRkRMRU5CUVVNc1UwRkJVeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4RlFVRkZMRlZCUVVNc1EwRkJReXhGUVVGRExFTkJRVU1zU1VGQlJ5eFBRVUZCTEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGUUxFTkJRVThzUTBGQlF5eERRVUZETzJsQ1FVTjJRenRoUVVOS08xTkJRMG83VVVGRFJDeFBRVUZQTEVOQlFVTXNRMEZCUXp0SlFVTmlMRU5CUVVNN1NVRkRUQ3hwUWtGQlF6dEJRVUZFTEVOQlFVTXNRVUZxU1VRc1NVRnBTVU03UVVGcVNWa3NaME5CUVZVaWZRPT0iLCJcInVzZSBzdHJpY3RcIjtcclxuT2JqZWN0LmRlZmluZVByb3BlcnR5KGV4cG9ydHMsIFwiX19lc01vZHVsZVwiLCB7IHZhbHVlOiB0cnVlIH0pO1xyXG52YXIgUG9zaXRpb25TdGF0cyA9IChmdW5jdGlvbiAoKSB7XHJcbiAgICBmdW5jdGlvbiBQb3NpdGlvblN0YXRzKHNjYWxlKSB7XHJcbiAgICAgICAgdGhpcy5zY2FsZSA9IHNjYWxlO1xyXG4gICAgICAgIHRoaXMuQUIgPSAwO1xyXG4gICAgICAgIHRoaXMuQUQgPSAwO1xyXG4gICAgICAgIHRoaXMuQTIgPSAwO1xyXG4gICAgfVxyXG4gICAgUG9zaXRpb25TdGF0cy5wcm90b3R5cGUuYWRkVmFyaWFibGUgPSBmdW5jdGlvbiAodikge1xyXG4gICAgICAgIHZhciBhaSA9IHRoaXMuc2NhbGUgLyB2LnNjYWxlO1xyXG4gICAgICAgIHZhciBiaSA9IHYub2Zmc2V0IC8gdi5zY2FsZTtcclxuICAgICAgICB2YXIgd2kgPSB2LndlaWdodDtcclxuICAgICAgICB0aGlzLkFCICs9IHdpICogYWkgKiBiaTtcclxuICAgICAgICB0aGlzLkFEICs9IHdpICogYWkgKiB2LmRlc2lyZWRQb3NpdGlvbjtcclxuICAgICAgICB0aGlzLkEyICs9IHdpICogYWkgKiBhaTtcclxuICAgIH07XHJcbiAgICBQb3NpdGlvblN0YXRzLnByb3RvdHlwZS5nZXRQb3NuID0gZnVuY3Rpb24gKCkge1xyXG4gICAgICAgIHJldHVybiAodGhpcy5BRCAtIHRoaXMuQUIpIC8gdGhpcy5BMjtcclxuICAgIH07XHJcbiAgICByZXR1cm4gUG9zaXRpb25TdGF0cztcclxufSgpKTtcclxuZXhwb3J0cy5Qb3NpdGlvblN0YXRzID0gUG9zaXRpb25TdGF0cztcclxudmFyIENvbnN0cmFpbnQgPSAoZnVuY3Rpb24gKCkge1xyXG4gICAgZnVuY3Rpb24gQ29uc3RyYWludChsZWZ0LCByaWdodCwgZ2FwLCBlcXVhbGl0eSkge1xyXG4gICAgICAgIGlmIChlcXVhbGl0eSA9PT0gdm9pZCAwKSB7IGVxdWFsaXR5ID0gZmFsc2U7IH1cclxuICAgICAgICB0aGlzLmxlZnQgPSBsZWZ0O1xyXG4gICAgICAgIHRoaXMucmlnaHQgPSByaWdodDtcclxuICAgICAgICB0aGlzLmdhcCA9IGdhcDtcclxuICAgICAgICB0aGlzLmVxdWFsaXR5ID0gZXF1YWxpdHk7XHJcbiAgICAgICAgdGhpcy5hY3RpdmUgPSBmYWxzZTtcclxuICAgICAgICB0aGlzLnVuc2F0aXNmaWFibGUgPSBmYWxzZTtcclxuICAgICAgICB0aGlzLmxlZnQgPSBsZWZ0O1xyXG4gICAgICAgIHRoaXMucmlnaHQgPSByaWdodDtcclxuICAgICAgICB0aGlzLmdhcCA9IGdhcDtcclxuICAgICAgICB0aGlzLmVxdWFsaXR5ID0gZXF1YWxpdHk7XHJcbiAgICB9XHJcbiAgICBDb25zdHJhaW50LnByb3RvdHlwZS5zbGFjayA9IGZ1bmN0aW9uICgpIHtcclxuICAgICAgICByZXR1cm4gdGhpcy51bnNhdGlzZmlhYmxlID8gTnVtYmVyLk1BWF9WQUxVRVxyXG4gICAgICAgICAgICA6IHRoaXMucmlnaHQuc2NhbGUgKiB0aGlzLnJpZ2h0LnBvc2l0aW9uKCkgLSB0aGlzLmdhcFxyXG4gICAgICAgICAgICAgICAgLSB0aGlzLmxlZnQuc2NhbGUgKiB0aGlzLmxlZnQucG9zaXRpb24oKTtcclxuICAgIH07XHJcbiAgICByZXR1cm4gQ29uc3RyYWludDtcclxufSgpKTtcclxuZXhwb3J0cy5Db25zdHJhaW50ID0gQ29uc3RyYWludDtcclxudmFyIFZhcmlhYmxlID0gKGZ1bmN0aW9uICgpIHtcclxuICAgIGZ1bmN0aW9uIFZhcmlhYmxlKGRlc2lyZWRQb3NpdGlvbiwgd2VpZ2h0LCBzY2FsZSkge1xyXG4gICAgICAgIGlmICh3ZWlnaHQgPT09IHZvaWQgMCkgeyB3ZWlnaHQgPSAxOyB9XHJcbiAgICAgICAgaWYgKHNjYWxlID09PSB2b2lkIDApIHsgc2NhbGUgPSAxOyB9XHJcbiAgICAgICAgdGhpcy5kZXNpcmVkUG9zaXRpb24gPSBkZXNpcmVkUG9zaXRpb247XHJcbiAgICAgICAgdGhpcy53ZWlnaHQgPSB3ZWlnaHQ7XHJcbiAgICAgICAgdGhpcy5zY2FsZSA9IHNjYWxlO1xyXG4gICAgICAgIHRoaXMub2Zmc2V0ID0gMDtcclxuICAgIH1cclxuICAgIFZhcmlhYmxlLnByb3RvdHlwZS5kZmR2ID0gZnVuY3Rpb24gKCkge1xyXG4gICAgICAgIHJldHVybiAyLjAgKiB0aGlzLndlaWdodCAqICh0aGlzLnBvc2l0aW9uKCkgLSB0aGlzLmRlc2lyZWRQb3NpdGlvbik7XHJcbiAgICB9O1xyXG4gICAgVmFyaWFibGUucHJvdG90eXBlLnBvc2l0aW9uID0gZnVuY3Rpb24gKCkge1xyXG4gICAgICAgIHJldHVybiAodGhpcy5ibG9jay5wcy5zY2FsZSAqIHRoaXMuYmxvY2sucG9zbiArIHRoaXMub2Zmc2V0KSAvIHRoaXMuc2NhbGU7XHJcbiAgICB9O1xyXG4gICAgVmFyaWFibGUucHJvdG90eXBlLnZpc2l0TmVpZ2hib3VycyA9IGZ1bmN0aW9uIChwcmV2LCBmKSB7XHJcbiAgICAgICAgdmFyIGZmID0gZnVuY3Rpb24gKGMsIG5leHQpIHsgcmV0dXJuIGMuYWN0aXZlICYmIHByZXYgIT09IG5leHQgJiYgZihjLCBuZXh0KTsgfTtcclxuICAgICAgICB0aGlzLmNPdXQuZm9yRWFjaChmdW5jdGlvbiAoYykgeyByZXR1cm4gZmYoYywgYy5yaWdodCk7IH0pO1xyXG4gICAgICAgIHRoaXMuY0luLmZvckVhY2goZnVuY3Rpb24gKGMpIHsgcmV0dXJuIGZmKGMsIGMubGVmdCk7IH0pO1xyXG4gICAgfTtcclxuICAgIHJldHVybiBWYXJpYWJsZTtcclxufSgpKTtcclxuZXhwb3J0cy5WYXJpYWJsZSA9IFZhcmlhYmxlO1xyXG52YXIgQmxvY2sgPSAoZnVuY3Rpb24gKCkge1xyXG4gICAgZnVuY3Rpb24gQmxvY2sodikge1xyXG4gICAgICAgIHRoaXMudmFycyA9IFtdO1xyXG4gICAgICAgIHYub2Zmc2V0ID0gMDtcclxuICAgICAgICB0aGlzLnBzID0gbmV3IFBvc2l0aW9uU3RhdHModi5zY2FsZSk7XHJcbiAgICAgICAgdGhpcy5hZGRWYXJpYWJsZSh2KTtcclxuICAgIH1cclxuICAgIEJsb2NrLnByb3RvdHlwZS5hZGRWYXJpYWJsZSA9IGZ1bmN0aW9uICh2KSB7XHJcbiAgICAgICAgdi5ibG9jayA9IHRoaXM7XHJcbiAgICAgICAgdGhpcy52YXJzLnB1c2godik7XHJcbiAgICAgICAgdGhpcy5wcy5hZGRWYXJpYWJsZSh2KTtcclxuICAgICAgICB0aGlzLnBvc24gPSB0aGlzLnBzLmdldFBvc24oKTtcclxuICAgIH07XHJcbiAgICBCbG9jay5wcm90b3R5cGUudXBkYXRlV2VpZ2h0ZWRQb3NpdGlvbiA9IGZ1bmN0aW9uICgpIHtcclxuICAgICAgICB0aGlzLnBzLkFCID0gdGhpcy5wcy5BRCA9IHRoaXMucHMuQTIgPSAwO1xyXG4gICAgICAgIGZvciAodmFyIGkgPSAwLCBuID0gdGhpcy52YXJzLmxlbmd0aDsgaSA8IG47ICsraSlcclxuICAgICAgICAgICAgdGhpcy5wcy5hZGRWYXJpYWJsZSh0aGlzLnZhcnNbaV0pO1xyXG4gICAgICAgIHRoaXMucG9zbiA9IHRoaXMucHMuZ2V0UG9zbigpO1xyXG4gICAgfTtcclxuICAgIEJsb2NrLnByb3RvdHlwZS5jb21wdXRlX2xtID0gZnVuY3Rpb24gKHYsIHUsIHBvc3RBY3Rpb24pIHtcclxuICAgICAgICB2YXIgX3RoaXMgPSB0aGlzO1xyXG4gICAgICAgIHZhciBkZmR2ID0gdi5kZmR2KCk7XHJcbiAgICAgICAgdi52aXNpdE5laWdoYm91cnModSwgZnVuY3Rpb24gKGMsIG5leHQpIHtcclxuICAgICAgICAgICAgdmFyIF9kZmR2ID0gX3RoaXMuY29tcHV0ZV9sbShuZXh0LCB2LCBwb3N0QWN0aW9uKTtcclxuICAgICAgICAgICAgaWYgKG5leHQgPT09IGMucmlnaHQpIHtcclxuICAgICAgICAgICAgICAgIGRmZHYgKz0gX2RmZHYgKiBjLmxlZnQuc2NhbGU7XHJcbiAgICAgICAgICAgICAgICBjLmxtID0gX2RmZHY7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgZWxzZSB7XHJcbiAgICAgICAgICAgICAgICBkZmR2ICs9IF9kZmR2ICogYy5yaWdodC5zY2FsZTtcclxuICAgICAgICAgICAgICAgIGMubG0gPSAtX2RmZHY7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgcG9zdEFjdGlvbihjKTtcclxuICAgICAgICB9KTtcclxuICAgICAgICByZXR1cm4gZGZkdiAvIHYuc2NhbGU7XHJcbiAgICB9O1xyXG4gICAgQmxvY2sucHJvdG90eXBlLnBvcHVsYXRlU3BsaXRCbG9jayA9IGZ1bmN0aW9uICh2LCBwcmV2KSB7XHJcbiAgICAgICAgdmFyIF90aGlzID0gdGhpcztcclxuICAgICAgICB2LnZpc2l0TmVpZ2hib3VycyhwcmV2LCBmdW5jdGlvbiAoYywgbmV4dCkge1xyXG4gICAgICAgICAgICBuZXh0Lm9mZnNldCA9IHYub2Zmc2V0ICsgKG5leHQgPT09IGMucmlnaHQgPyBjLmdhcCA6IC1jLmdhcCk7XHJcbiAgICAgICAgICAgIF90aGlzLmFkZFZhcmlhYmxlKG5leHQpO1xyXG4gICAgICAgICAgICBfdGhpcy5wb3B1bGF0ZVNwbGl0QmxvY2sobmV4dCwgdik7XHJcbiAgICAgICAgfSk7XHJcbiAgICB9O1xyXG4gICAgQmxvY2sucHJvdG90eXBlLnRyYXZlcnNlID0gZnVuY3Rpb24gKHZpc2l0LCBhY2MsIHYsIHByZXYpIHtcclxuICAgICAgICB2YXIgX3RoaXMgPSB0aGlzO1xyXG4gICAgICAgIGlmICh2ID09PSB2b2lkIDApIHsgdiA9IHRoaXMudmFyc1swXTsgfVxyXG4gICAgICAgIGlmIChwcmV2ID09PSB2b2lkIDApIHsgcHJldiA9IG51bGw7IH1cclxuICAgICAgICB2LnZpc2l0TmVpZ2hib3VycyhwcmV2LCBmdW5jdGlvbiAoYywgbmV4dCkge1xyXG4gICAgICAgICAgICBhY2MucHVzaCh2aXNpdChjKSk7XHJcbiAgICAgICAgICAgIF90aGlzLnRyYXZlcnNlKHZpc2l0LCBhY2MsIG5leHQsIHYpO1xyXG4gICAgICAgIH0pO1xyXG4gICAgfTtcclxuICAgIEJsb2NrLnByb3RvdHlwZS5maW5kTWluTE0gPSBmdW5jdGlvbiAoKSB7XHJcbiAgICAgICAgdmFyIG0gPSBudWxsO1xyXG4gICAgICAgIHRoaXMuY29tcHV0ZV9sbSh0aGlzLnZhcnNbMF0sIG51bGwsIGZ1bmN0aW9uIChjKSB7XHJcbiAgICAgICAgICAgIGlmICghYy5lcXVhbGl0eSAmJiAobSA9PT0gbnVsbCB8fCBjLmxtIDwgbS5sbSkpXHJcbiAgICAgICAgICAgICAgICBtID0gYztcclxuICAgICAgICB9KTtcclxuICAgICAgICByZXR1cm4gbTtcclxuICAgIH07XHJcbiAgICBCbG9jay5wcm90b3R5cGUuZmluZE1pbkxNQmV0d2VlbiA9IGZ1bmN0aW9uIChsdiwgcnYpIHtcclxuICAgICAgICB0aGlzLmNvbXB1dGVfbG0obHYsIG51bGwsIGZ1bmN0aW9uICgpIHsgfSk7XHJcbiAgICAgICAgdmFyIG0gPSBudWxsO1xyXG4gICAgICAgIHRoaXMuZmluZFBhdGgobHYsIG51bGwsIHJ2LCBmdW5jdGlvbiAoYywgbmV4dCkge1xyXG4gICAgICAgICAgICBpZiAoIWMuZXF1YWxpdHkgJiYgYy5yaWdodCA9PT0gbmV4dCAmJiAobSA9PT0gbnVsbCB8fCBjLmxtIDwgbS5sbSkpXHJcbiAgICAgICAgICAgICAgICBtID0gYztcclxuICAgICAgICB9KTtcclxuICAgICAgICByZXR1cm4gbTtcclxuICAgIH07XHJcbiAgICBCbG9jay5wcm90b3R5cGUuZmluZFBhdGggPSBmdW5jdGlvbiAodiwgcHJldiwgdG8sIHZpc2l0KSB7XHJcbiAgICAgICAgdmFyIF90aGlzID0gdGhpcztcclxuICAgICAgICB2YXIgZW5kRm91bmQgPSBmYWxzZTtcclxuICAgICAgICB2LnZpc2l0TmVpZ2hib3VycyhwcmV2LCBmdW5jdGlvbiAoYywgbmV4dCkge1xyXG4gICAgICAgICAgICBpZiAoIWVuZEZvdW5kICYmIChuZXh0ID09PSB0byB8fCBfdGhpcy5maW5kUGF0aChuZXh0LCB2LCB0bywgdmlzaXQpKSkge1xyXG4gICAgICAgICAgICAgICAgZW5kRm91bmQgPSB0cnVlO1xyXG4gICAgICAgICAgICAgICAgdmlzaXQoYywgbmV4dCk7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICB9KTtcclxuICAgICAgICByZXR1cm4gZW5kRm91bmQ7XHJcbiAgICB9O1xyXG4gICAgQmxvY2sucHJvdG90eXBlLmlzQWN0aXZlRGlyZWN0ZWRQYXRoQmV0d2VlbiA9IGZ1bmN0aW9uICh1LCB2KSB7XHJcbiAgICAgICAgaWYgKHUgPT09IHYpXHJcbiAgICAgICAgICAgIHJldHVybiB0cnVlO1xyXG4gICAgICAgIHZhciBpID0gdS5jT3V0Lmxlbmd0aDtcclxuICAgICAgICB3aGlsZSAoaS0tKSB7XHJcbiAgICAgICAgICAgIHZhciBjID0gdS5jT3V0W2ldO1xyXG4gICAgICAgICAgICBpZiAoYy5hY3RpdmUgJiYgdGhpcy5pc0FjdGl2ZURpcmVjdGVkUGF0aEJldHdlZW4oYy5yaWdodCwgdikpXHJcbiAgICAgICAgICAgICAgICByZXR1cm4gdHJ1ZTtcclxuICAgICAgICB9XHJcbiAgICAgICAgcmV0dXJuIGZhbHNlO1xyXG4gICAgfTtcclxuICAgIEJsb2NrLnNwbGl0ID0gZnVuY3Rpb24gKGMpIHtcclxuICAgICAgICBjLmFjdGl2ZSA9IGZhbHNlO1xyXG4gICAgICAgIHJldHVybiBbQmxvY2suY3JlYXRlU3BsaXRCbG9jayhjLmxlZnQpLCBCbG9jay5jcmVhdGVTcGxpdEJsb2NrKGMucmlnaHQpXTtcclxuICAgIH07XHJcbiAgICBCbG9jay5jcmVhdGVTcGxpdEJsb2NrID0gZnVuY3Rpb24gKHN0YXJ0VmFyKSB7XHJcbiAgICAgICAgdmFyIGIgPSBuZXcgQmxvY2soc3RhcnRWYXIpO1xyXG4gICAgICAgIGIucG9wdWxhdGVTcGxpdEJsb2NrKHN0YXJ0VmFyLCBudWxsKTtcclxuICAgICAgICByZXR1cm4gYjtcclxuICAgIH07XHJcbiAgICBCbG9jay5wcm90b3R5cGUuc3BsaXRCZXR3ZWVuID0gZnVuY3Rpb24gKHZsLCB2cikge1xyXG4gICAgICAgIHZhciBjID0gdGhpcy5maW5kTWluTE1CZXR3ZWVuKHZsLCB2cik7XHJcbiAgICAgICAgaWYgKGMgIT09IG51bGwpIHtcclxuICAgICAgICAgICAgdmFyIGJzID0gQmxvY2suc3BsaXQoYyk7XHJcbiAgICAgICAgICAgIHJldHVybiB7IGNvbnN0cmFpbnQ6IGMsIGxiOiBic1swXSwgcmI6IGJzWzFdIH07XHJcbiAgICAgICAgfVxyXG4gICAgICAgIHJldHVybiBudWxsO1xyXG4gICAgfTtcclxuICAgIEJsb2NrLnByb3RvdHlwZS5tZXJnZUFjcm9zcyA9IGZ1bmN0aW9uIChiLCBjLCBkaXN0KSB7XHJcbiAgICAgICAgYy5hY3RpdmUgPSB0cnVlO1xyXG4gICAgICAgIGZvciAodmFyIGkgPSAwLCBuID0gYi52YXJzLmxlbmd0aDsgaSA8IG47ICsraSkge1xyXG4gICAgICAgICAgICB2YXIgdiA9IGIudmFyc1tpXTtcclxuICAgICAgICAgICAgdi5vZmZzZXQgKz0gZGlzdDtcclxuICAgICAgICAgICAgdGhpcy5hZGRWYXJpYWJsZSh2KTtcclxuICAgICAgICB9XHJcbiAgICAgICAgdGhpcy5wb3NuID0gdGhpcy5wcy5nZXRQb3NuKCk7XHJcbiAgICB9O1xyXG4gICAgQmxvY2sucHJvdG90eXBlLmNvc3QgPSBmdW5jdGlvbiAoKSB7XHJcbiAgICAgICAgdmFyIHN1bSA9IDAsIGkgPSB0aGlzLnZhcnMubGVuZ3RoO1xyXG4gICAgICAgIHdoaWxlIChpLS0pIHtcclxuICAgICAgICAgICAgdmFyIHYgPSB0aGlzLnZhcnNbaV0sIGQgPSB2LnBvc2l0aW9uKCkgLSB2LmRlc2lyZWRQb3NpdGlvbjtcclxuICAgICAgICAgICAgc3VtICs9IGQgKiBkICogdi53ZWlnaHQ7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIHJldHVybiBzdW07XHJcbiAgICB9O1xyXG4gICAgcmV0dXJuIEJsb2NrO1xyXG59KCkpO1xyXG5leHBvcnRzLkJsb2NrID0gQmxvY2s7XHJcbnZhciBCbG9ja3MgPSAoZnVuY3Rpb24gKCkge1xyXG4gICAgZnVuY3Rpb24gQmxvY2tzKHZzKSB7XHJcbiAgICAgICAgdGhpcy52cyA9IHZzO1xyXG4gICAgICAgIHZhciBuID0gdnMubGVuZ3RoO1xyXG4gICAgICAgIHRoaXMubGlzdCA9IG5ldyBBcnJheShuKTtcclxuICAgICAgICB3aGlsZSAobi0tKSB7XHJcbiAgICAgICAgICAgIHZhciBiID0gbmV3IEJsb2NrKHZzW25dKTtcclxuICAgICAgICAgICAgdGhpcy5saXN0W25dID0gYjtcclxuICAgICAgICAgICAgYi5ibG9ja0luZCA9IG47XHJcbiAgICAgICAgfVxyXG4gICAgfVxyXG4gICAgQmxvY2tzLnByb3RvdHlwZS5jb3N0ID0gZnVuY3Rpb24gKCkge1xyXG4gICAgICAgIHZhciBzdW0gPSAwLCBpID0gdGhpcy5saXN0Lmxlbmd0aDtcclxuICAgICAgICB3aGlsZSAoaS0tKVxyXG4gICAgICAgICAgICBzdW0gKz0gdGhpcy5saXN0W2ldLmNvc3QoKTtcclxuICAgICAgICByZXR1cm4gc3VtO1xyXG4gICAgfTtcclxuICAgIEJsb2Nrcy5wcm90b3R5cGUuaW5zZXJ0ID0gZnVuY3Rpb24gKGIpIHtcclxuICAgICAgICBiLmJsb2NrSW5kID0gdGhpcy5saXN0Lmxlbmd0aDtcclxuICAgICAgICB0aGlzLmxpc3QucHVzaChiKTtcclxuICAgIH07XHJcbiAgICBCbG9ja3MucHJvdG90eXBlLnJlbW92ZSA9IGZ1bmN0aW9uIChiKSB7XHJcbiAgICAgICAgdmFyIGxhc3QgPSB0aGlzLmxpc3QubGVuZ3RoIC0gMTtcclxuICAgICAgICB2YXIgc3dhcEJsb2NrID0gdGhpcy5saXN0W2xhc3RdO1xyXG4gICAgICAgIHRoaXMubGlzdC5sZW5ndGggPSBsYXN0O1xyXG4gICAgICAgIGlmIChiICE9PSBzd2FwQmxvY2spIHtcclxuICAgICAgICAgICAgdGhpcy5saXN0W2IuYmxvY2tJbmRdID0gc3dhcEJsb2NrO1xyXG4gICAgICAgICAgICBzd2FwQmxvY2suYmxvY2tJbmQgPSBiLmJsb2NrSW5kO1xyXG4gICAgICAgIH1cclxuICAgIH07XHJcbiAgICBCbG9ja3MucHJvdG90eXBlLm1lcmdlID0gZnVuY3Rpb24gKGMpIHtcclxuICAgICAgICB2YXIgbCA9IGMubGVmdC5ibG9jaywgciA9IGMucmlnaHQuYmxvY2s7XHJcbiAgICAgICAgdmFyIGRpc3QgPSBjLnJpZ2h0Lm9mZnNldCAtIGMubGVmdC5vZmZzZXQgLSBjLmdhcDtcclxuICAgICAgICBpZiAobC52YXJzLmxlbmd0aCA8IHIudmFycy5sZW5ndGgpIHtcclxuICAgICAgICAgICAgci5tZXJnZUFjcm9zcyhsLCBjLCBkaXN0KTtcclxuICAgICAgICAgICAgdGhpcy5yZW1vdmUobCk7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIGVsc2Uge1xyXG4gICAgICAgICAgICBsLm1lcmdlQWNyb3NzKHIsIGMsIC1kaXN0KTtcclxuICAgICAgICAgICAgdGhpcy5yZW1vdmUocik7XHJcbiAgICAgICAgfVxyXG4gICAgfTtcclxuICAgIEJsb2Nrcy5wcm90b3R5cGUuZm9yRWFjaCA9IGZ1bmN0aW9uIChmKSB7XHJcbiAgICAgICAgdGhpcy5saXN0LmZvckVhY2goZik7XHJcbiAgICB9O1xyXG4gICAgQmxvY2tzLnByb3RvdHlwZS51cGRhdGVCbG9ja1Bvc2l0aW9ucyA9IGZ1bmN0aW9uICgpIHtcclxuICAgICAgICB0aGlzLmxpc3QuZm9yRWFjaChmdW5jdGlvbiAoYikgeyByZXR1cm4gYi51cGRhdGVXZWlnaHRlZFBvc2l0aW9uKCk7IH0pO1xyXG4gICAgfTtcclxuICAgIEJsb2Nrcy5wcm90b3R5cGUuc3BsaXQgPSBmdW5jdGlvbiAoaW5hY3RpdmUpIHtcclxuICAgICAgICB2YXIgX3RoaXMgPSB0aGlzO1xyXG4gICAgICAgIHRoaXMudXBkYXRlQmxvY2tQb3NpdGlvbnMoKTtcclxuICAgICAgICB0aGlzLmxpc3QuZm9yRWFjaChmdW5jdGlvbiAoYikge1xyXG4gICAgICAgICAgICB2YXIgdiA9IGIuZmluZE1pbkxNKCk7XHJcbiAgICAgICAgICAgIGlmICh2ICE9PSBudWxsICYmIHYubG0gPCBTb2x2ZXIuTEFHUkFOR0lBTl9UT0xFUkFOQ0UpIHtcclxuICAgICAgICAgICAgICAgIGIgPSB2LmxlZnQuYmxvY2s7XHJcbiAgICAgICAgICAgICAgICBCbG9jay5zcGxpdCh2KS5mb3JFYWNoKGZ1bmN0aW9uIChuYikgeyByZXR1cm4gX3RoaXMuaW5zZXJ0KG5iKTsgfSk7XHJcbiAgICAgICAgICAgICAgICBfdGhpcy5yZW1vdmUoYik7XHJcbiAgICAgICAgICAgICAgICBpbmFjdGl2ZS5wdXNoKHYpO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgfSk7XHJcbiAgICB9O1xyXG4gICAgcmV0dXJuIEJsb2NrcztcclxufSgpKTtcclxuZXhwb3J0cy5CbG9ja3MgPSBCbG9ja3M7XHJcbnZhciBTb2x2ZXIgPSAoZnVuY3Rpb24gKCkge1xyXG4gICAgZnVuY3Rpb24gU29sdmVyKHZzLCBjcykge1xyXG4gICAgICAgIHRoaXMudnMgPSB2cztcclxuICAgICAgICB0aGlzLmNzID0gY3M7XHJcbiAgICAgICAgdGhpcy52cyA9IHZzO1xyXG4gICAgICAgIHZzLmZvckVhY2goZnVuY3Rpb24gKHYpIHtcclxuICAgICAgICAgICAgdi5jSW4gPSBbXSwgdi5jT3V0ID0gW107XHJcbiAgICAgICAgfSk7XHJcbiAgICAgICAgdGhpcy5jcyA9IGNzO1xyXG4gICAgICAgIGNzLmZvckVhY2goZnVuY3Rpb24gKGMpIHtcclxuICAgICAgICAgICAgYy5sZWZ0LmNPdXQucHVzaChjKTtcclxuICAgICAgICAgICAgYy5yaWdodC5jSW4ucHVzaChjKTtcclxuICAgICAgICB9KTtcclxuICAgICAgICB0aGlzLmluYWN0aXZlID0gY3MubWFwKGZ1bmN0aW9uIChjKSB7IGMuYWN0aXZlID0gZmFsc2U7IHJldHVybiBjOyB9KTtcclxuICAgICAgICB0aGlzLmJzID0gbnVsbDtcclxuICAgIH1cclxuICAgIFNvbHZlci5wcm90b3R5cGUuY29zdCA9IGZ1bmN0aW9uICgpIHtcclxuICAgICAgICByZXR1cm4gdGhpcy5icy5jb3N0KCk7XHJcbiAgICB9O1xyXG4gICAgU29sdmVyLnByb3RvdHlwZS5zZXRTdGFydGluZ1Bvc2l0aW9ucyA9IGZ1bmN0aW9uIChwcykge1xyXG4gICAgICAgIHRoaXMuaW5hY3RpdmUgPSB0aGlzLmNzLm1hcChmdW5jdGlvbiAoYykgeyBjLmFjdGl2ZSA9IGZhbHNlOyByZXR1cm4gYzsgfSk7XHJcbiAgICAgICAgdGhpcy5icyA9IG5ldyBCbG9ja3ModGhpcy52cyk7XHJcbiAgICAgICAgdGhpcy5icy5mb3JFYWNoKGZ1bmN0aW9uIChiLCBpKSB7IHJldHVybiBiLnBvc24gPSBwc1tpXTsgfSk7XHJcbiAgICB9O1xyXG4gICAgU29sdmVyLnByb3RvdHlwZS5zZXREZXNpcmVkUG9zaXRpb25zID0gZnVuY3Rpb24gKHBzKSB7XHJcbiAgICAgICAgdGhpcy52cy5mb3JFYWNoKGZ1bmN0aW9uICh2LCBpKSB7IHJldHVybiB2LmRlc2lyZWRQb3NpdGlvbiA9IHBzW2ldOyB9KTtcclxuICAgIH07XHJcbiAgICBTb2x2ZXIucHJvdG90eXBlLm1vc3RWaW9sYXRlZCA9IGZ1bmN0aW9uICgpIHtcclxuICAgICAgICB2YXIgbWluU2xhY2sgPSBOdW1iZXIuTUFYX1ZBTFVFLCB2ID0gbnVsbCwgbCA9IHRoaXMuaW5hY3RpdmUsIG4gPSBsLmxlbmd0aCwgZGVsZXRlUG9pbnQgPSBuO1xyXG4gICAgICAgIGZvciAodmFyIGkgPSAwOyBpIDwgbjsgKytpKSB7XHJcbiAgICAgICAgICAgIHZhciBjID0gbFtpXTtcclxuICAgICAgICAgICAgaWYgKGMudW5zYXRpc2ZpYWJsZSlcclxuICAgICAgICAgICAgICAgIGNvbnRpbnVlO1xyXG4gICAgICAgICAgICB2YXIgc2xhY2sgPSBjLnNsYWNrKCk7XHJcbiAgICAgICAgICAgIGlmIChjLmVxdWFsaXR5IHx8IHNsYWNrIDwgbWluU2xhY2spIHtcclxuICAgICAgICAgICAgICAgIG1pblNsYWNrID0gc2xhY2s7XHJcbiAgICAgICAgICAgICAgICB2ID0gYztcclxuICAgICAgICAgICAgICAgIGRlbGV0ZVBvaW50ID0gaTtcclxuICAgICAgICAgICAgICAgIGlmIChjLmVxdWFsaXR5KVxyXG4gICAgICAgICAgICAgICAgICAgIGJyZWFrO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgfVxyXG4gICAgICAgIGlmIChkZWxldGVQb2ludCAhPT0gbiAmJlxyXG4gICAgICAgICAgICAobWluU2xhY2sgPCBTb2x2ZXIuWkVST19VUFBFUkJPVU5EICYmICF2LmFjdGl2ZSB8fCB2LmVxdWFsaXR5KSkge1xyXG4gICAgICAgICAgICBsW2RlbGV0ZVBvaW50XSA9IGxbbiAtIDFdO1xyXG4gICAgICAgICAgICBsLmxlbmd0aCA9IG4gLSAxO1xyXG4gICAgICAgIH1cclxuICAgICAgICByZXR1cm4gdjtcclxuICAgIH07XHJcbiAgICBTb2x2ZXIucHJvdG90eXBlLnNhdGlzZnkgPSBmdW5jdGlvbiAoKSB7XHJcbiAgICAgICAgaWYgKHRoaXMuYnMgPT0gbnVsbCkge1xyXG4gICAgICAgICAgICB0aGlzLmJzID0gbmV3IEJsb2Nrcyh0aGlzLnZzKTtcclxuICAgICAgICB9XHJcbiAgICAgICAgdGhpcy5icy5zcGxpdCh0aGlzLmluYWN0aXZlKTtcclxuICAgICAgICB2YXIgdiA9IG51bGw7XHJcbiAgICAgICAgd2hpbGUgKCh2ID0gdGhpcy5tb3N0VmlvbGF0ZWQoKSkgJiYgKHYuZXF1YWxpdHkgfHwgdi5zbGFjaygpIDwgU29sdmVyLlpFUk9fVVBQRVJCT1VORCAmJiAhdi5hY3RpdmUpKSB7XHJcbiAgICAgICAgICAgIHZhciBsYiA9IHYubGVmdC5ibG9jaywgcmIgPSB2LnJpZ2h0LmJsb2NrO1xyXG4gICAgICAgICAgICBpZiAobGIgIT09IHJiKSB7XHJcbiAgICAgICAgICAgICAgICB0aGlzLmJzLm1lcmdlKHYpO1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgICAgIGVsc2Uge1xyXG4gICAgICAgICAgICAgICAgaWYgKGxiLmlzQWN0aXZlRGlyZWN0ZWRQYXRoQmV0d2Vlbih2LnJpZ2h0LCB2LmxlZnQpKSB7XHJcbiAgICAgICAgICAgICAgICAgICAgdi51bnNhdGlzZmlhYmxlID0gdHJ1ZTtcclxuICAgICAgICAgICAgICAgICAgICBjb250aW51ZTtcclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgIHZhciBzcGxpdCA9IGxiLnNwbGl0QmV0d2Vlbih2LmxlZnQsIHYucmlnaHQpO1xyXG4gICAgICAgICAgICAgICAgaWYgKHNwbGl0ICE9PSBudWxsKSB7XHJcbiAgICAgICAgICAgICAgICAgICAgdGhpcy5icy5pbnNlcnQoc3BsaXQubGIpO1xyXG4gICAgICAgICAgICAgICAgICAgIHRoaXMuYnMuaW5zZXJ0KHNwbGl0LnJiKTtcclxuICAgICAgICAgICAgICAgICAgICB0aGlzLmJzLnJlbW92ZShsYik7XHJcbiAgICAgICAgICAgICAgICAgICAgdGhpcy5pbmFjdGl2ZS5wdXNoKHNwbGl0LmNvbnN0cmFpbnQpO1xyXG4gICAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICAgICAgZWxzZSB7XHJcbiAgICAgICAgICAgICAgICAgICAgdi51bnNhdGlzZmlhYmxlID0gdHJ1ZTtcclxuICAgICAgICAgICAgICAgICAgICBjb250aW51ZTtcclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgIGlmICh2LnNsYWNrKCkgPj0gMCkge1xyXG4gICAgICAgICAgICAgICAgICAgIHRoaXMuaW5hY3RpdmUucHVzaCh2KTtcclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgIGVsc2Uge1xyXG4gICAgICAgICAgICAgICAgICAgIHRoaXMuYnMubWVyZ2Uodik7XHJcbiAgICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICB9XHJcbiAgICB9O1xyXG4gICAgU29sdmVyLnByb3RvdHlwZS5zb2x2ZSA9IGZ1bmN0aW9uICgpIHtcclxuICAgICAgICB0aGlzLnNhdGlzZnkoKTtcclxuICAgICAgICB2YXIgbGFzdGNvc3QgPSBOdW1iZXIuTUFYX1ZBTFVFLCBjb3N0ID0gdGhpcy5icy5jb3N0KCk7XHJcbiAgICAgICAgd2hpbGUgKE1hdGguYWJzKGxhc3Rjb3N0IC0gY29zdCkgPiAwLjAwMDEpIHtcclxuICAgICAgICAgICAgdGhpcy5zYXRpc2Z5KCk7XHJcbiAgICAgICAgICAgIGxhc3Rjb3N0ID0gY29zdDtcclxuICAgICAgICAgICAgY29zdCA9IHRoaXMuYnMuY29zdCgpO1xyXG4gICAgICAgIH1cclxuICAgICAgICByZXR1cm4gY29zdDtcclxuICAgIH07XHJcbiAgICBTb2x2ZXIuTEFHUkFOR0lBTl9UT0xFUkFOQ0UgPSAtMWUtNDtcclxuICAgIFNvbHZlci5aRVJPX1VQUEVSQk9VTkQgPSAtMWUtMTA7XHJcbiAgICByZXR1cm4gU29sdmVyO1xyXG59KCkpO1xyXG5leHBvcnRzLlNvbHZlciA9IFNvbHZlcjtcclxuZnVuY3Rpb24gcmVtb3ZlT3ZlcmxhcEluT25lRGltZW5zaW9uKHNwYW5zLCBsb3dlckJvdW5kLCB1cHBlckJvdW5kKSB7XHJcbiAgICB2YXIgdnMgPSBzcGFucy5tYXAoZnVuY3Rpb24gKHMpIHsgcmV0dXJuIG5ldyBWYXJpYWJsZShzLmRlc2lyZWRDZW50ZXIpOyB9KTtcclxuICAgIHZhciBjcyA9IFtdO1xyXG4gICAgdmFyIG4gPSBzcGFucy5sZW5ndGg7XHJcbiAgICBmb3IgKHZhciBpID0gMDsgaSA8IG4gLSAxOyBpKyspIHtcclxuICAgICAgICB2YXIgbGVmdCA9IHNwYW5zW2ldLCByaWdodCA9IHNwYW5zW2kgKyAxXTtcclxuICAgICAgICBjcy5wdXNoKG5ldyBDb25zdHJhaW50KHZzW2ldLCB2c1tpICsgMV0sIChsZWZ0LnNpemUgKyByaWdodC5zaXplKSAvIDIpKTtcclxuICAgIH1cclxuICAgIHZhciBsZWZ0TW9zdCA9IHZzWzBdLCByaWdodE1vc3QgPSB2c1tuIC0gMV0sIGxlZnRNb3N0U2l6ZSA9IHNwYW5zWzBdLnNpemUgLyAyLCByaWdodE1vc3RTaXplID0gc3BhbnNbbiAtIDFdLnNpemUgLyAyO1xyXG4gICAgdmFyIHZMb3dlciA9IG51bGwsIHZVcHBlciA9IG51bGw7XHJcbiAgICBpZiAobG93ZXJCb3VuZCkge1xyXG4gICAgICAgIHZMb3dlciA9IG5ldyBWYXJpYWJsZShsb3dlckJvdW5kLCBsZWZ0TW9zdC53ZWlnaHQgKiAxMDAwKTtcclxuICAgICAgICB2cy5wdXNoKHZMb3dlcik7XHJcbiAgICAgICAgY3MucHVzaChuZXcgQ29uc3RyYWludCh2TG93ZXIsIGxlZnRNb3N0LCBsZWZ0TW9zdFNpemUpKTtcclxuICAgIH1cclxuICAgIGlmICh1cHBlckJvdW5kKSB7XHJcbiAgICAgICAgdlVwcGVyID0gbmV3IFZhcmlhYmxlKHVwcGVyQm91bmQsIHJpZ2h0TW9zdC53ZWlnaHQgKiAxMDAwKTtcclxuICAgICAgICB2cy5wdXNoKHZVcHBlcik7XHJcbiAgICAgICAgY3MucHVzaChuZXcgQ29uc3RyYWludChyaWdodE1vc3QsIHZVcHBlciwgcmlnaHRNb3N0U2l6ZSkpO1xyXG4gICAgfVxyXG4gICAgdmFyIHNvbHZlciA9IG5ldyBTb2x2ZXIodnMsIGNzKTtcclxuICAgIHNvbHZlci5zb2x2ZSgpO1xyXG4gICAgcmV0dXJuIHtcclxuICAgICAgICBuZXdDZW50ZXJzOiB2cy5zbGljZSgwLCBzcGFucy5sZW5ndGgpLm1hcChmdW5jdGlvbiAodikgeyByZXR1cm4gdi5wb3NpdGlvbigpOyB9KSxcclxuICAgICAgICBsb3dlckJvdW5kOiB2TG93ZXIgPyB2TG93ZXIucG9zaXRpb24oKSA6IGxlZnRNb3N0LnBvc2l0aW9uKCkgLSBsZWZ0TW9zdFNpemUsXHJcbiAgICAgICAgdXBwZXJCb3VuZDogdlVwcGVyID8gdlVwcGVyLnBvc2l0aW9uKCkgOiByaWdodE1vc3QucG9zaXRpb24oKSArIHJpZ2h0TW9zdFNpemVcclxuICAgIH07XHJcbn1cclxuZXhwb3J0cy5yZW1vdmVPdmVybGFwSW5PbmVEaW1lbnNpb24gPSByZW1vdmVPdmVybGFwSW5PbmVEaW1lbnNpb247XHJcbi8vIyBzb3VyY2VNYXBwaW5nVVJMPWRhdGE6YXBwbGljYXRpb24vanNvbjtiYXNlNjQsZXlKMlpYSnphVzl1SWpvekxDSm1hV3hsSWpvaWRuQnpZeTVxY3lJc0luTnZkWEpqWlZKdmIzUWlPaUlpTENKemIzVnlZMlZ6SWpwYklpNHVMeTR1TDFkbFlrTnZiR0V2YzNKakwzWndjMk11ZEhNaVhTd2libUZ0WlhNaU9sdGRMQ0p0WVhCd2FXNW5jeUk2SWpzN1FVRkJTVHRKUVV0SkxIVkNRVUZ0UWl4TFFVRmhPMUZCUVdJc1ZVRkJTeXhIUVVGTUxFdEJRVXNzUTBGQlVUdFJRVXBvUXl4UFFVRkZMRWRCUVZjc1EwRkJReXhEUVVGRE8xRkJRMllzVDBGQlJTeEhRVUZYTEVOQlFVTXNRMEZCUXp0UlFVTm1MRTlCUVVVc1IwRkJWeXhEUVVGRExFTkJRVU03U1VGRmIwSXNRMEZCUXp0SlFVVndReXh0UTBGQlZ5eEhRVUZZTEZWQlFWa3NRMEZCVnp0UlFVTnVRaXhKUVVGSkxFVkJRVVVzUjBGQlJ5eEpRVUZKTEVOQlFVTXNTMEZCU3l4SFFVRkhMRU5CUVVNc1EwRkJReXhMUVVGTExFTkJRVU03VVVGRE9VSXNTVUZCU1N4RlFVRkZMRWRCUVVjc1EwRkJReXhEUVVGRExFMUJRVTBzUjBGQlJ5eERRVUZETEVOQlFVTXNTMEZCU3l4RFFVRkRPMUZCUXpWQ0xFbEJRVWtzUlVGQlJTeEhRVUZITEVOQlFVTXNRMEZCUXl4TlFVRk5MRU5CUVVNN1VVRkRiRUlzU1VGQlNTeERRVUZETEVWQlFVVXNTVUZCU1N4RlFVRkZMRWRCUVVjc1JVRkJSU3hIUVVGSExFVkJRVVVzUTBGQlF6dFJRVU40UWl4SlFVRkpMRU5CUVVNc1JVRkJSU3hKUVVGSkxFVkJRVVVzUjBGQlJ5eEZRVUZGTEVkQlFVY3NRMEZCUXl4RFFVRkRMR1ZCUVdVc1EwRkJRenRSUVVOMlF5eEpRVUZKTEVOQlFVTXNSVUZCUlN4SlFVRkpMRVZCUVVVc1IwRkJSeXhGUVVGRkxFZEJRVWNzUlVGQlJTeERRVUZETzBsQlF6VkNMRU5CUVVNN1NVRkZSQ3dyUWtGQlR5eEhRVUZRTzFGQlEwa3NUMEZCVHl4RFFVRkRMRWxCUVVrc1EwRkJReXhGUVVGRkxFZEJRVWNzU1VGQlNTeERRVUZETEVWQlFVVXNRMEZCUXl4SFFVRkhMRWxCUVVrc1EwRkJReXhGUVVGRkxFTkJRVU03U1VGRGVrTXNRMEZCUXp0SlFVTk1MRzlDUVVGRE8wRkJRVVFzUTBGQlF5eEJRVzVDUkN4SlFXMUNRenRCUVc1Q1dTeHpRMEZCWVR0QlFYRkNNVUk3U1VGTFNTeHZRa0ZCYlVJc1NVRkJZeXhGUVVGVExFdEJRV1VzUlVGQlV5eEhRVUZYTEVWQlFWTXNVVUZCZVVJN1VVRkJla0lzZVVKQlFVRXNSVUZCUVN4blFrRkJlVUk3VVVGQk5VWXNVMEZCU1N4SFFVRktMRWxCUVVrc1EwRkJWVHRSUVVGVExGVkJRVXNzUjBGQlRDeExRVUZMTEVOQlFWVTdVVUZCVXl4UlFVRkhMRWRCUVVnc1IwRkJSeXhEUVVGUk8xRkJRVk1zWVVGQlVTeEhRVUZTTEZGQlFWRXNRMEZCYVVJN1VVRklMMGNzVjBGQlRTeEhRVUZaTEV0QlFVc3NRMEZCUXp0UlFVTjRRaXhyUWtGQllTeEhRVUZaTEV0QlFVc3NRMEZCUXp0UlFVY3pRaXhKUVVGSkxFTkJRVU1zU1VGQlNTeEhRVUZITEVsQlFVa3NRMEZCUXp0UlFVTnFRaXhKUVVGSkxFTkJRVU1zUzBGQlN5eEhRVUZITEV0QlFVc3NRMEZCUXp0UlFVTnVRaXhKUVVGSkxFTkJRVU1zUjBGQlJ5eEhRVUZITEVkQlFVY3NRMEZCUXp0UlFVTm1MRWxCUVVrc1EwRkJReXhSUVVGUkxFZEJRVWNzVVVGQlVTeERRVUZETzBsQlF6ZENMRU5CUVVNN1NVRkZSQ3d3UWtGQlN5eEhRVUZNTzFGQlEwa3NUMEZCVHl4SlFVRkpMRU5CUVVNc1lVRkJZU3hEUVVGRExFTkJRVU1zUTBGQlF5eE5RVUZOTEVOQlFVTXNVMEZCVXp0WlFVTjRReXhEUVVGRExFTkJRVU1zU1VGQlNTeERRVUZETEV0QlFVc3NRMEZCUXl4TFFVRkxMRWRCUVVjc1NVRkJTU3hEUVVGRExFdEJRVXNzUTBGQlF5eFJRVUZSTEVWQlFVVXNSMEZCUnl4SlFVRkpMRU5CUVVNc1IwRkJSenRyUWtGRGJrUXNTVUZCU1N4RFFVRkRMRWxCUVVrc1EwRkJReXhMUVVGTExFZEJRVWNzU1VGQlNTeERRVUZETEVsQlFVa3NRMEZCUXl4UlFVRlJMRVZCUVVVc1EwRkJRenRKUVVOcVJDeERRVUZETzBsQlEwd3NhVUpCUVVNN1FVRkJSQ3hEUVVGRExFRkJha0pFTEVsQmFVSkRPMEZCYWtKWkxHZERRVUZWTzBGQmJVSjJRanRKUVUxSkxHdENRVUZ0UWl4bFFVRjFRaXhGUVVGVExFMUJRV3RDTEVWQlFWTXNTMEZCYVVJN1VVRkJOVU1zZFVKQlFVRXNSVUZCUVN4VlFVRnJRanRSUVVGVExITkNRVUZCTEVWQlFVRXNVMEZCYVVJN1VVRkJOVVVzYjBKQlFXVXNSMEZCWml4bFFVRmxMRU5CUVZFN1VVRkJVeXhYUVVGTkxFZEJRVTRzVFVGQlRTeERRVUZaTzFGQlFWTXNWVUZCU3l4SFFVRk1MRXRCUVVzc1EwRkJXVHRSUVV3dlJpeFhRVUZOTEVkQlFWY3NRMEZCUXl4RFFVRkRPMGxCU3l0RkxFTkJRVU03U1VGRmJrY3NkVUpCUVVrc1IwRkJTanRSUVVOSkxFOUJRVThzUjBGQlJ5eEhRVUZITEVsQlFVa3NRMEZCUXl4TlFVRk5MRWRCUVVjc1EwRkJReXhKUVVGSkxFTkJRVU1zVVVGQlVTeEZRVUZGTEVkQlFVY3NTVUZCU1N4RFFVRkRMR1ZCUVdVc1EwRkJReXhEUVVGRE8wbEJRM2hGTEVOQlFVTTdTVUZGUkN3eVFrRkJVU3hIUVVGU08xRkJRMGtzVDBGQlR5eERRVUZETEVsQlFVa3NRMEZCUXl4TFFVRkxMRU5CUVVNc1JVRkJSU3hEUVVGRExFdEJRVXNzUjBGQlJ5eEpRVUZKTEVOQlFVTXNTMEZCU3l4RFFVRkRMRWxCUVVrc1IwRkJSeXhKUVVGSkxFTkJRVU1zVFVGQlRTeERRVUZETEVkQlFVY3NTVUZCU1N4RFFVRkRMRXRCUVVzc1EwRkJRenRKUVVNNVJTeERRVUZETzBsQlIwUXNhME5CUVdVc1IwRkJaaXhWUVVGblFpeEpRVUZqTEVWQlFVVXNRMEZCTUVNN1VVRkRkRVVzU1VGQlNTeEZRVUZGTEVkQlFVY3NWVUZCUXl4RFFVRkRMRVZCUVVVc1NVRkJTU3hKUVVGTExFOUJRVUVzUTBGQlF5eERRVUZETEUxQlFVMHNTVUZCU1N4SlFVRkpMRXRCUVVzc1NVRkJTU3hKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVWQlFVVXNTVUZCU1N4RFFVRkRMRVZCUVhaRExFTkJRWFZETEVOQlFVTTdVVUZET1VRc1NVRkJTU3hEUVVGRExFbEJRVWtzUTBGQlF5eFBRVUZQTEVOQlFVTXNWVUZCUVN4RFFVRkRMRWxCUVVjc1QwRkJRU3hGUVVGRkxFTkJRVU1zUTBGQlF5eEZRVUZGTEVOQlFVTXNRMEZCUXl4TFFVRkxMRU5CUVVNc1JVRkJaQ3hEUVVGakxFTkJRVU1zUTBGQlF6dFJRVU4wUXl4SlFVRkpMRU5CUVVNc1IwRkJSeXhEUVVGRExFOUJRVThzUTBGQlF5eFZRVUZCTEVOQlFVTXNTVUZCUnl4UFFVRkJMRVZCUVVVc1EwRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETEVsQlFVa3NRMEZCUXl4RlFVRmlMRU5CUVdFc1EwRkJReXhEUVVGRE8wbEJRM2hETEVOQlFVTTdTVUZEVEN4bFFVRkRPMEZCUVVRc1EwRkJReXhCUVhSQ1JDeEpRWE5DUXp0QlFYUkNXU3cwUWtGQlVUdEJRWGRDY2tJN1NVRk5TU3hsUVVGWkxFTkJRVmM3VVVGTWRrSXNVMEZCU1N4SFFVRmxMRVZCUVVVc1EwRkJRenRSUVUxc1FpeERRVUZETEVOQlFVTXNUVUZCVFN4SFFVRkhMRU5CUVVNc1EwRkJRenRSUVVOaUxFbEJRVWtzUTBGQlF5eEZRVUZGTEVkQlFVY3NTVUZCU1N4aFFVRmhMRU5CUVVNc1EwRkJReXhEUVVGRExFdEJRVXNzUTBGQlF5eERRVUZETzFGQlEzSkRMRWxCUVVrc1EwRkJReXhYUVVGWExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdTVUZEZUVJc1EwRkJRenRKUVVWUExESkNRVUZYTEVkQlFXNUNMRlZCUVc5Q0xFTkJRVmM3VVVGRE0wSXNRMEZCUXl4RFFVRkRMRXRCUVVzc1IwRkJSeXhKUVVGSkxFTkJRVU03VVVGRFppeEpRVUZKTEVOQlFVTXNTVUZCU1N4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFJRVU5zUWl4SlFVRkpMRU5CUVVNc1JVRkJSU3hEUVVGRExGZEJRVmNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0UlFVTjJRaXhKUVVGSkxFTkJRVU1zU1VGQlNTeEhRVUZITEVsQlFVa3NRMEZCUXl4RlFVRkZMRU5CUVVNc1QwRkJUeXhGUVVGRkxFTkJRVU03U1VGRGJFTXNRMEZCUXp0SlFVZEVMSE5EUVVGelFpeEhRVUYwUWp0UlFVTkpMRWxCUVVrc1EwRkJReXhGUVVGRkxFTkJRVU1zUlVGQlJTeEhRVUZITEVsQlFVa3NRMEZCUXl4RlFVRkZMRU5CUVVNc1JVRkJSU3hIUVVGSExFbEJRVWtzUTBGQlF5eEZRVUZGTEVOQlFVTXNSVUZCUlN4SFFVRkhMRU5CUVVNc1EwRkJRenRSUVVONlF5eExRVUZMTEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1JVRkJSU3hEUVVGRExFZEJRVWNzU1VGQlNTeERRVUZETEVsQlFVa3NRMEZCUXl4TlFVRk5MRVZCUVVVc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeEZRVUZGTEVOQlFVTTdXVUZETlVNc1NVRkJTU3hEUVVGRExFVkJRVVVzUTBGQlF5eFhRVUZYTEVOQlFVTXNTVUZCU1N4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzFGQlEzUkRMRWxCUVVrc1EwRkJReXhKUVVGSkxFZEJRVWNzU1VGQlNTeERRVUZETEVWQlFVVXNRMEZCUXl4UFFVRlBMRVZCUVVVc1EwRkJRenRKUVVOc1F5eERRVUZETzBsQlJVOHNNRUpCUVZVc1IwRkJiRUlzVlVGQmJVSXNRMEZCVnl4RlFVRkZMRU5CUVZjc1JVRkJSU3hWUVVGcFF6dFJRVUU1UlN4cFFrRmpRenRSUVdKSExFbEJRVWtzU1VGQlNTeEhRVUZITEVOQlFVTXNRMEZCUXl4SlFVRkpMRVZCUVVVc1EwRkJRenRSUVVOd1FpeERRVUZETEVOQlFVTXNaVUZCWlN4RFFVRkRMRU5CUVVNc1JVRkJSU3hWUVVGRExFTkJRVU1zUlVGQlJTeEpRVUZKTzFsQlEzcENMRWxCUVVrc1MwRkJTeXhIUVVGSExFdEJRVWtzUTBGQlF5eFZRVUZWTEVOQlFVTXNTVUZCU1N4RlFVRkZMRU5CUVVNc1JVRkJSU3hWUVVGVkxFTkJRVU1zUTBGQlF6dFpRVU5xUkN4SlFVRkpMRWxCUVVrc1MwRkJTeXhEUVVGRExFTkJRVU1zUzBGQlN5eEZRVUZGTzJkQ1FVTnNRaXhKUVVGSkxFbEJRVWtzUzBGQlN5eEhRVUZITEVOQlFVTXNRMEZCUXl4SlFVRkpMRU5CUVVNc1MwRkJTeXhEUVVGRE8yZENRVU0zUWl4RFFVRkRMRU5CUVVNc1JVRkJSU3hIUVVGSExFdEJRVXNzUTBGQlF6dGhRVU5vUWp0cFFrRkJUVHRuUWtGRFNDeEpRVUZKTEVsQlFVa3NTMEZCU3l4SFFVRkhMRU5CUVVNc1EwRkJReXhMUVVGTExFTkJRVU1zUzBGQlN5eERRVUZETzJkQ1FVTTVRaXhEUVVGRExFTkJRVU1zUlVGQlJTeEhRVUZITEVOQlFVTXNTMEZCU3l4RFFVRkRPMkZCUTJwQ08xbEJRMFFzVlVGQlZTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMUZCUTJ4Q0xFTkJRVU1zUTBGQlF5eERRVUZETzFGQlEwZ3NUMEZCVHl4SlFVRkpMRWRCUVVjc1EwRkJReXhEUVVGRExFdEJRVXNzUTBGQlF6dEpRVU14UWl4RFFVRkRPMGxCUlU4c2EwTkJRV3RDTEVkQlFURkNMRlZCUVRKQ0xFTkJRVmNzUlVGQlJTeEpRVUZqTzFGQlFYUkVMR2xDUVUxRE8xRkJURWNzUTBGQlF5eERRVUZETEdWQlFXVXNRMEZCUXl4SlFVRkpMRVZCUVVVc1ZVRkJReXhEUVVGRExFVkJRVVVzU1VGQlNUdFpRVU0xUWl4SlFVRkpMRU5CUVVNc1RVRkJUU3hIUVVGSExFTkJRVU1zUTBGQlF5eE5RVUZOTEVkQlFVY3NRMEZCUXl4SlFVRkpMRXRCUVVzc1EwRkJReXhEUVVGRExFdEJRVXNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNN1dVRkROMFFzUzBGQlNTeERRVUZETEZkQlFWY3NRMEZCUXl4SlFVRkpMRU5CUVVNc1EwRkJRenRaUVVOMlFpeExRVUZKTEVOQlFVTXNhMEpCUVd0Q0xFTkJRVU1zU1VGQlNTeEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRPMUZCUTNKRExFTkJRVU1zUTBGQlF5eERRVUZETzBsQlExQXNRMEZCUXp0SlFVZEVMSGRDUVVGUkxFZEJRVklzVlVGQlV5eExRVUUyUWl4RlFVRkZMRWRCUVZVc1JVRkJSU3hEUVVFd1FpeEZRVUZGTEVsQlFXMUNPMUZCUVc1SExHbENRVXRETzFGQlRHMUVMR3RDUVVGQkxFVkJRVUVzU1VGQll5eEpRVUZKTEVOQlFVTXNTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJRenRSUVVGRkxIRkNRVUZCTEVWQlFVRXNWMEZCYlVJN1VVRkRMMFlzUTBGQlF5eERRVUZETEdWQlFXVXNRMEZCUXl4SlFVRkpMRVZCUVVVc1ZVRkJReXhEUVVGRExFVkJRVVVzU1VGQlNUdFpRVU0xUWl4SFFVRkhMRU5CUVVNc1NVRkJTU3hEUVVGRExFdEJRVXNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMWxCUTI1Q0xFdEJRVWtzUTBGQlF5eFJRVUZSTEVOQlFVTXNTMEZCU3l4RlFVRkZMRWRCUVVjc1JVRkJSU3hKUVVGSkxFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTTdVVUZEZGtNc1EwRkJReXhEUVVGRExFTkJRVU03U1VGRFVDeERRVUZETzBsQlMwUXNlVUpCUVZNc1IwRkJWRHRSUVVOSkxFbEJRVWtzUTBGQlF5eEhRVUZsTEVsQlFVa3NRMEZCUXp0UlFVTjZRaXhKUVVGSkxFTkJRVU1zVlVGQlZTeERRVUZETEVsQlFVa3NRMEZCUXl4SlFVRkpMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRVVVzU1VGQlNTeEZRVUZGTEZWQlFVRXNRMEZCUXp0WlFVTnFReXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEZGQlFWRXNTVUZCU1N4RFFVRkRMRU5CUVVNc1MwRkJTeXhKUVVGSkxFbEJRVWtzUTBGQlF5eERRVUZETEVWQlFVVXNSMEZCUnl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRE8yZENRVUZGTEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNN1VVRkRNVVFzUTBGQlF5eERRVUZETEVOQlFVTTdVVUZEU0N4UFFVRlBMRU5CUVVNc1EwRkJRenRKUVVOaUxFTkJRVU03U1VGRlR5eG5RMEZCWjBJc1IwRkJlRUlzVlVGQmVVSXNSVUZCV1N4RlFVRkZMRVZCUVZrN1VVRkRMME1zU1VGQlNTeERRVUZETEZWQlFWVXNRMEZCUXl4RlFVRkZMRVZCUVVVc1NVRkJTU3hGUVVGRkxHTkJRVThzUTBGQlF5eERRVUZETEVOQlFVTTdVVUZEY0VNc1NVRkJTU3hEUVVGRExFZEJRVWNzU1VGQlNTeERRVUZETzFGQlEySXNTVUZCU1N4RFFVRkRMRkZCUVZFc1EwRkJReXhGUVVGRkxFVkJRVVVzU1VGQlNTeEZRVUZGTEVWQlFVVXNSVUZCUlN4VlFVRkRMRU5CUVVNc1JVRkJSU3hKUVVGSk8xbEJRMmhETEVsQlFVa3NRMEZCUXl4RFFVRkRMRU5CUVVNc1VVRkJVU3hKUVVGSkxFTkJRVU1zUTBGQlF5eExRVUZMTEV0QlFVc3NTVUZCU1N4SlFVRkpMRU5CUVVNc1EwRkJReXhMUVVGTExFbEJRVWtzU1VGQlNTeERRVUZETEVOQlFVTXNSVUZCUlN4SFFVRkhMRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU03WjBKQlFVVXNRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJRenRSUVVNNVJTeERRVUZETEVOQlFVTXNRMEZCUXp0UlFVTklMRTlCUVU4c1EwRkJReXhEUVVGRE8wbEJRMklzUTBGQlF6dEpRVVZQTEhkQ1FVRlJMRWRCUVdoQ0xGVkJRV2xDTEVOQlFWY3NSVUZCUlN4SlFVRmpMRVZCUVVVc1JVRkJXU3hGUVVGRkxFdEJRVEpETzFGQlFYWkhMR2xDUVZWRE8xRkJWRWNzU1VGQlNTeFJRVUZSTEVkQlFVY3NTMEZCU3l4RFFVRkRPMUZCUTNKQ0xFTkJRVU1zUTBGQlF5eGxRVUZsTEVOQlFVTXNTVUZCU1N4RlFVRkZMRlZCUVVNc1EwRkJReXhGUVVGRkxFbEJRVWs3V1VGRE5VSXNTVUZCU1N4RFFVRkRMRkZCUVZFc1NVRkJTU3hEUVVGRExFbEJRVWtzUzBGQlN5eEZRVUZGTEVsQlFVa3NTMEZCU1N4RFFVRkRMRkZCUVZFc1EwRkJReXhKUVVGSkxFVkJRVVVzUTBGQlF5eEZRVUZGTEVWQlFVVXNSVUZCUlN4TFFVRkxMRU5CUVVNc1EwRkJReXhGUVVOdVJUdG5Ra0ZEU1N4UlFVRlJMRWRCUVVjc1NVRkJTU3hEUVVGRE8yZENRVU5vUWl4TFFVRkxMRU5CUVVNc1EwRkJReXhGUVVGRkxFbEJRVWtzUTBGQlF5eERRVUZETzJGQlEyeENPMUZCUTB3c1EwRkJReXhEUVVGRExFTkJRVU03VVVGRFNDeFBRVUZQTEZGQlFWRXNRMEZCUXp0SlFVTndRaXhEUVVGRE8wbEJTVVFzTWtOQlFUSkNMRWRCUVROQ0xGVkJRVFJDTEVOQlFWY3NSVUZCUlN4RFFVRlhPMUZCUTJoRUxFbEJRVWtzUTBGQlF5eExRVUZMTEVOQlFVTTdXVUZCUlN4UFFVRlBMRWxCUVVrc1EwRkJRenRSUVVONlFpeEpRVUZKTEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1NVRkJTU3hEUVVGRExFMUJRVTBzUTBGQlF6dFJRVU4wUWl4UFFVRk5MRU5CUVVNc1JVRkJSU3hGUVVGRk8xbEJRMUFzU1VGQlNTeERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFpRVU5zUWl4SlFVRkpMRU5CUVVNc1EwRkJReXhOUVVGTkxFbEJRVWtzU1VGQlNTeERRVUZETERKQ1FVRXlRaXhEUVVGRExFTkJRVU1zUTBGQlF5eExRVUZMTEVWQlFVVXNRMEZCUXl4RFFVRkRPMmRDUVVONFJDeFBRVUZQTEVsQlFVa3NRMEZCUXp0VFFVTnVRanRSUVVORUxFOUJRVThzUzBGQlN5eERRVUZETzBsQlEycENMRU5CUVVNN1NVRkhUU3hYUVVGTExFZEJRVm9zVlVGQllTeERRVUZoTzFGQlMzUkNMRU5CUVVNc1EwRkJReXhOUVVGTkxFZEJRVWNzUzBGQlN5eERRVUZETzFGQlEycENMRTlCUVU4c1EwRkJReXhMUVVGTExFTkJRVU1zWjBKQlFXZENMRU5CUVVNc1EwRkJReXhEUVVGRExFbEJRVWtzUTBGQlF5eEZRVUZGTEV0QlFVc3NRMEZCUXl4blFrRkJaMElzUTBGQlF5eERRVUZETEVOQlFVTXNTMEZCU3l4RFFVRkRMRU5CUVVNc1EwRkJRenRKUVVNM1JTeERRVUZETzBsQlJXTXNjMEpCUVdkQ0xFZEJRUzlDTEZWQlFXZERMRkZCUVd0Q08xRkJRemxETEVsQlFVa3NRMEZCUXl4SFFVRkhMRWxCUVVrc1MwRkJTeXhEUVVGRExGRkJRVkVzUTBGQlF5eERRVUZETzFGQlF6VkNMRU5CUVVNc1EwRkJReXhyUWtGQmEwSXNRMEZCUXl4UlFVRlJMRVZCUVVVc1NVRkJTU3hEUVVGRExFTkJRVU03VVVGRGNrTXNUMEZCVHl4RFFVRkRMRU5CUVVNN1NVRkRZaXhEUVVGRE8wbEJSMFFzTkVKQlFWa3NSMEZCV2l4VlFVRmhMRVZCUVZrc1JVRkJSU3hGUVVGWk8xRkJTMjVETEVsQlFVa3NRMEZCUXl4SFFVRkhMRWxCUVVrc1EwRkJReXhuUWtGQlowSXNRMEZCUXl4RlFVRkZMRVZCUVVVc1JVRkJSU3hEUVVGRExFTkJRVU03VVVGRGRFTXNTVUZCU1N4RFFVRkRMRXRCUVVzc1NVRkJTU3hGUVVGRk8xbEJRMW9zU1VGQlNTeEZRVUZGTEVkQlFVY3NTMEZCU3l4RFFVRkRMRXRCUVVzc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF6dFpRVU40UWl4UFFVRlBMRVZCUVVVc1ZVRkJWU3hGUVVGRkxFTkJRVU1zUlVGQlJTeEZRVUZGTEVWQlFVVXNSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGRkxFVkJRVVVzUlVGQlJTeEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJRenRUUVVOc1JEdFJRVVZFTEU5QlFVOHNTVUZCU1N4RFFVRkRPMGxCUTJoQ0xFTkJRVU03U1VGRlJDd3lRa0ZCVnl4SFFVRllMRlZCUVZrc1EwRkJVU3hGUVVGRkxFTkJRV0VzUlVGQlJTeEpRVUZaTzFGQlF6ZERMRU5CUVVNc1EwRkJReXhOUVVGTkxFZEJRVWNzU1VGQlNTeERRVUZETzFGQlEyaENMRXRCUVVzc1NVRkJTU3hEUVVGRExFZEJRVWNzUTBGQlF5eEZRVUZGTEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1NVRkJTU3hEUVVGRExFMUJRVTBzUlVGQlJTeERRVUZETEVkQlFVY3NRMEZCUXl4RlFVRkZMRVZCUVVVc1EwRkJReXhGUVVGRk8xbEJRek5ETEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJReXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdXVUZEYkVJc1EwRkJReXhEUVVGRExFMUJRVTBzU1VGQlNTeEpRVUZKTEVOQlFVTTdXVUZEYWtJc1NVRkJTU3hEUVVGRExGZEJRVmNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0VFFVTjJRanRSUVVORUxFbEJRVWtzUTBGQlF5eEpRVUZKTEVkQlFVY3NTVUZCU1N4RFFVRkRMRVZCUVVVc1EwRkJReXhQUVVGUExFVkJRVVVzUTBGQlF6dEpRVU5zUXl4RFFVRkRPMGxCUlVRc2IwSkJRVWtzUjBGQlNqdFJRVU5KTEVsQlFVa3NSMEZCUnl4SFFVRkhMRU5CUVVNc1JVRkJSU3hEUVVGRExFZEJRVWNzU1VGQlNTeERRVUZETEVsQlFVa3NRMEZCUXl4TlFVRk5MRU5CUVVNN1VVRkRiRU1zVDBGQlR5eERRVUZETEVWQlFVVXNSVUZCUlR0WlFVTlNMRWxCUVVrc1EwRkJReXhIUVVGSExFbEJRVWtzUTBGQlF5eEpRVUZKTEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUTJoQ0xFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNVVUZCVVN4RlFVRkZMRWRCUVVjc1EwRkJReXhEUVVGRExHVkJRV1VzUTBGQlF6dFpRVU42UXl4SFFVRkhMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNUVUZCVFN4RFFVRkRPMU5CUXpOQ08xRkJRMFFzVDBGQlR5eEhRVUZITEVOQlFVTTdTVUZEWml4RFFVRkRPMGxCVTB3c1dVRkJRenRCUVVGRUxFTkJRVU1zUVVGc1MwUXNTVUZyUzBNN1FVRnNTMWtzYzBKQlFVczdRVUZ2UzJ4Q08wbEJSMGtzWjBKQlFXMUNMRVZCUVdNN1VVRkJaQ3hQUVVGRkxFZEJRVVlzUlVGQlJTeERRVUZaTzFGQlF6ZENMRWxCUVVrc1EwRkJReXhIUVVGSExFVkJRVVVzUTBGQlF5eE5RVUZOTEVOQlFVTTdVVUZEYkVJc1NVRkJTU3hEUVVGRExFbEJRVWtzUjBGQlJ5eEpRVUZKTEV0QlFVc3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRSUVVONlFpeFBRVUZQTEVOQlFVTXNSVUZCUlN4RlFVRkZPMWxCUTFJc1NVRkJTU3hEUVVGRExFZEJRVWNzU1VGQlNTeExRVUZMTEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03V1VGRGVrSXNTVUZCU1N4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTTdXVUZEYWtJc1EwRkJReXhEUVVGRExGRkJRVkVzUjBGQlJ5eERRVUZETEVOQlFVTTdVMEZEYkVJN1NVRkRUQ3hEUVVGRE8wbEJSVVFzY1VKQlFVa3NSMEZCU2p0UlFVTkpMRWxCUVVrc1IwRkJSeXhIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NTVUZCU1N4RFFVRkRMRWxCUVVrc1EwRkJReXhOUVVGTkxFTkJRVU03VVVGRGJFTXNUMEZCVHl4RFFVRkRMRVZCUVVVN1dVRkJSU3hIUVVGSExFbEJRVWtzU1VGQlNTeERRVUZETEVsQlFVa3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhKUVVGSkxFVkJRVVVzUTBGQlF6dFJRVU4yUXl4UFFVRlBMRWRCUVVjc1EwRkJRenRKUVVObUxFTkJRVU03U1VGRlJDeDFRa0ZCVFN4SFFVRk9MRlZCUVU4c1EwRkJVVHRSUVVsWUxFTkJRVU1zUTBGQlF5eFJRVUZSTEVkQlFVY3NTVUZCU1N4RFFVRkRMRWxCUVVrc1EwRkJReXhOUVVGTkxFTkJRVU03VVVGRE9VSXNTVUZCU1N4RFFVRkRMRWxCUVVrc1EwRkJReXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdTVUZMZEVJc1EwRkJRenRKUVVWRUxIVkNRVUZOTEVkQlFVNHNWVUZCVHl4RFFVRlJPMUZCUzFnc1NVRkJTU3hKUVVGSkxFZEJRVWNzU1VGQlNTeERRVUZETEVsQlFVa3NRMEZCUXl4TlFVRk5MRWRCUVVjc1EwRkJReXhEUVVGRE8xRkJRMmhETEVsQlFVa3NVMEZCVXl4SFFVRkhMRWxCUVVrc1EwRkJReXhKUVVGSkxFTkJRVU1zU1VGQlNTeERRVUZETEVOQlFVTTdVVUZEYUVNc1NVRkJTU3hEUVVGRExFbEJRVWtzUTBGQlF5eE5RVUZOTEVkQlFVY3NTVUZCU1N4RFFVRkRPMUZCUTNoQ0xFbEJRVWtzUTBGQlF5eExRVUZMTEZOQlFWTXNSVUZCUlR0WlFVTnFRaXhKUVVGSkxFTkJRVU1zU1VGQlNTeERRVUZETEVOQlFVTXNRMEZCUXl4UlFVRlJMRU5CUVVNc1IwRkJSeXhUUVVGVExFTkJRVU03V1VGRGJFTXNVMEZCVXl4RFFVRkRMRkZCUVZFc1IwRkJSeXhEUVVGRExFTkJRVU1zVVVGQlVTeERRVUZETzFOQlNXNURPMGxCUTB3c1EwRkJRenRKUVVsRUxITkNRVUZMTEVkQlFVd3NWVUZCVFN4RFFVRmhPMUZCUTJZc1NVRkJTU3hEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETEVsQlFVa3NRMEZCUXl4TFFVRkxMRVZCUVVVc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eExRVUZMTEVOQlFVTXNTMEZCU3l4RFFVRkRPMUZCU1hoRExFbEJRVWtzU1VGQlNTeEhRVUZITEVOQlFVTXNRMEZCUXl4TFFVRkxMRU5CUVVNc1RVRkJUU3hIUVVGSExFTkJRVU1zUTBGQlF5eEpRVUZKTEVOQlFVTXNUVUZCVFN4SFFVRkhMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU03VVVGRGJFUXNTVUZCU1N4RFFVRkRMRU5CUVVNc1NVRkJTU3hEUVVGRExFMUJRVTBzUjBGQlJ5eERRVUZETEVOQlFVTXNTVUZCU1N4RFFVRkRMRTFCUVUwc1JVRkJSVHRaUVVNdlFpeERRVUZETEVOQlFVTXNWMEZCVnl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFVkJRVVVzU1VGQlNTeERRVUZETEVOQlFVTTdXVUZETVVJc1NVRkJTU3hEUVVGRExFMUJRVTBzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0VFFVTnNRanRoUVVGTk8xbEJRMGdzUTBGQlF5eERRVUZETEZkQlFWY3NRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhGUVVGRkxFTkJRVU1zU1VGQlNTeERRVUZETEVOQlFVTTdXVUZETTBJc1NVRkJTU3hEUVVGRExFMUJRVTBzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0VFFVTnNRanRKUVV0TUxFTkJRVU03U1VGRlJDeDNRa0ZCVHl4SFFVRlFMRlZCUVZFc1EwRkJaME03VVVGRGNFTXNTVUZCU1N4RFFVRkRMRWxCUVVrc1EwRkJReXhQUVVGUExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdTVUZEZWtJc1EwRkJRenRKUVVkRUxIRkRRVUZ2UWl4SFFVRndRanRSUVVOSkxFbEJRVWtzUTBGQlF5eEpRVUZKTEVOQlFVTXNUMEZCVHl4RFFVRkRMRlZCUVVFc1EwRkJReXhKUVVGSExFOUJRVUVzUTBGQlF5eERRVUZETEhOQ1FVRnpRaXhGUVVGRkxFVkJRVEZDTEVOQlFUQkNMRU5CUVVNc1EwRkJRenRKUVVOMFJDeERRVUZETzBsQlIwUXNjMEpCUVVzc1IwRkJUQ3hWUVVGTkxGRkJRWE5DTzFGQlFUVkNMR2xDUVdWRE8xRkJaRWNzU1VGQlNTeERRVUZETEc5Q1FVRnZRaXhGUVVGRkxFTkJRVU03VVVGRE5VSXNTVUZCU1N4RFFVRkRMRWxCUVVrc1EwRkJReXhQUVVGUExFTkJRVU1zVlVGQlFTeERRVUZETzFsQlEyWXNTVUZCU1N4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExGTkJRVk1zUlVGQlJTeERRVUZETzFsQlEzUkNMRWxCUVVrc1EwRkJReXhMUVVGTExFbEJRVWtzU1VGQlNTeERRVUZETEVOQlFVTXNSVUZCUlN4SFFVRkhMRTFCUVUwc1EwRkJReXh2UWtGQmIwSXNSVUZCUlR0blFrRkRiRVFzUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXl4SlFVRkpMRU5CUVVNc1MwRkJTeXhEUVVGRE8yZENRVU5xUWl4TFFVRkxMRU5CUVVNc1MwRkJTeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEU5QlFVOHNRMEZCUXl4VlFVRkJMRVZCUVVVc1NVRkJSU3hQUVVGQkxFdEJRVWtzUTBGQlF5eE5RVUZOTEVOQlFVTXNSVUZCUlN4RFFVRkRMRVZCUVdZc1EwRkJaU3hEUVVGRExFTkJRVU03WjBKQlF6VkRMRXRCUVVrc1EwRkJReXhOUVVGTkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdaMEpCUTJZc1VVRkJVU3hEUVVGRExFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0aFFVdHdRanRSUVVOTUxFTkJRVU1zUTBGQlF5eERRVUZETzBsQlExQXNRMEZCUXp0SlFXOUNUQ3hoUVVGRE8wRkJRVVFzUTBGQlF5eEJRV3hJUkN4SlFXdElRenRCUVd4SVdTeDNRa0ZCVFR0QlFXOUlia0k3U1VGUFNTeG5Ra0ZCYlVJc1JVRkJZeXhGUVVGVExFVkJRV2RDTzFGQlFYWkRMRTlCUVVVc1IwRkJSaXhGUVVGRkxFTkJRVms3VVVGQlV5eFBRVUZGTEVkQlFVWXNSVUZCUlN4RFFVRmpPMUZCUTNSRUxFbEJRVWtzUTBGQlF5eEZRVUZGTEVkQlFVY3NSVUZCUlN4RFFVRkRPMUZCUTJJc1JVRkJSU3hEUVVGRExFOUJRVThzUTBGQlF5eFZRVUZCTEVOQlFVTTdXVUZEVWl4RFFVRkRMRU5CUVVNc1IwRkJSeXhIUVVGSExFVkJRVVVzUlVGQlJTeERRVUZETEVOQlFVTXNTVUZCU1N4SFFVRkhMRVZCUVVVc1EwRkJRenRSUVVrMVFpeERRVUZETEVOQlFVTXNRMEZCUXp0UlFVTklMRWxCUVVrc1EwRkJReXhGUVVGRkxFZEJRVWNzUlVGQlJTeERRVUZETzFGQlEySXNSVUZCUlN4RFFVRkRMRTlCUVU4c1EwRkJReXhWUVVGQkxFTkJRVU03V1VGRFVpeERRVUZETEVOQlFVTXNTVUZCU1N4RFFVRkRMRWxCUVVrc1EwRkJReXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdXVUZEY0VJc1EwRkJReXhEUVVGRExFdEJRVXNzUTBGQlF5eEhRVUZITEVOQlFVTXNTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8xRkJTWGhDTEVOQlFVTXNRMEZCUXl4RFFVRkRPMUZCUTBnc1NVRkJTU3hEUVVGRExGRkJRVkVzUjBGQlJ5eEZRVUZGTEVOQlFVTXNSMEZCUnl4RFFVRkRMRlZCUVVFc1EwRkJReXhKUVVGTExFTkJRVU1zUTBGQlF5eE5RVUZOTEVkQlFVY3NTMEZCU3l4RFFVRkRMRU5CUVVNc1QwRkJUeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0UlFVTTFSQ3hKUVVGSkxFTkJRVU1zUlVGQlJTeEhRVUZITEVsQlFVa3NRMEZCUXp0SlFVTnVRaXhEUVVGRE8wbEJSVVFzY1VKQlFVa3NSMEZCU2p0UlFVTkpMRTlCUVU4c1NVRkJTU3hEUVVGRExFVkJRVVVzUTBGQlF5eEpRVUZKTEVWQlFVVXNRMEZCUXp0SlFVTXhRaXhEUVVGRE8wbEJTVVFzY1VOQlFXOUNMRWRCUVhCQ0xGVkJRWEZDTEVWQlFWazdVVUZETjBJc1NVRkJTU3hEUVVGRExGRkJRVkVzUjBGQlJ5eEpRVUZKTEVOQlFVTXNSVUZCUlN4RFFVRkRMRWRCUVVjc1EwRkJReXhWUVVGQkxFTkJRVU1zU1VGQlN5eERRVUZETEVOQlFVTXNUVUZCVFN4SFFVRkhMRXRCUVVzc1EwRkJReXhEUVVGRExFOUJRVThzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1VVRkRha1VzU1VGQlNTeERRVUZETEVWQlFVVXNSMEZCUnl4SlFVRkpMRTFCUVUwc1EwRkJReXhKUVVGSkxFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTTdVVUZET1VJc1NVRkJTU3hEUVVGRExFVkJRVVVzUTBGQlF5eFBRVUZQTEVOQlFVTXNWVUZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhKUVVGTExFOUJRVUVzUTBGQlF5eERRVUZETEVsQlFVa3NSMEZCUnl4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRV1FzUTBGQll5eERRVUZETEVOQlFVTTdTVUZET1VNc1EwRkJRenRKUVVWRUxHOURRVUZ0UWl4SFFVRnVRaXhWUVVGdlFpeEZRVUZaTzFGQlF6VkNMRWxCUVVrc1EwRkJReXhGUVVGRkxFTkJRVU1zVDBGQlR5eERRVUZETEZWQlFVTXNRMEZCUXl4RlFVRkZMRU5CUVVNc1NVRkJTeXhQUVVGQkxFTkJRVU1zUTBGQlF5eGxRVUZsTEVkQlFVY3NSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGNlFpeERRVUY1UWl4RFFVRkRMRU5CUVVNN1NVRkRla1FzUTBGQlF6dEpRVEpDVHl3MlFrRkJXU3hIUVVGd1FqdFJRVU5KTEVsQlFVa3NVVUZCVVN4SFFVRkhMRTFCUVUwc1EwRkJReXhUUVVGVExFVkJRek5DTEVOQlFVTXNSMEZCWlN4SlFVRkpMRVZCUTNCQ0xFTkJRVU1zUjBGQlJ5eEpRVUZKTEVOQlFVTXNVVUZCVVN4RlFVTnFRaXhEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETEUxQlFVMHNSVUZEV2l4WFFVRlhMRWRCUVVjc1EwRkJReXhEUVVGRE8xRkJRM0JDTEV0QlFVc3NTVUZCU1N4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRkxFTkJRVU1zUjBGQlJ5eERRVUZETEVWQlFVVXNSVUZCUlN4RFFVRkRMRVZCUVVVN1dVRkRlRUlzU1VGQlNTeERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRE8xbEJRMklzU1VGQlNTeERRVUZETEVOQlFVTXNZVUZCWVR0blFrRkJSU3hUUVVGVE8xbEJRemxDTEVsQlFVa3NTMEZCU3l4SFFVRkhMRU5CUVVNc1EwRkJReXhMUVVGTExFVkJRVVVzUTBGQlF6dFpRVU4wUWl4SlFVRkpMRU5CUVVNc1EwRkJReXhSUVVGUkxFbEJRVWtzUzBGQlN5eEhRVUZITEZGQlFWRXNSVUZCUlR0blFrRkRhRU1zVVVGQlVTeEhRVUZITEV0QlFVc3NRMEZCUXp0blFrRkRha0lzUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXp0blFrRkRUaXhYUVVGWExFZEJRVWNzUTBGQlF5eERRVUZETzJkQ1FVTm9RaXhKUVVGSkxFTkJRVU1zUTBGQlF5eFJRVUZSTzI5Q1FVRkZMRTFCUVUwN1lVRkRla0k3VTBGRFNqdFJRVU5FTEVsQlFVa3NWMEZCVnl4TFFVRkxMRU5CUVVNN1dVRkRha0lzUTBGQlF5eFJRVUZSTEVkQlFVY3NUVUZCVFN4RFFVRkRMR1ZCUVdVc1NVRkJTU3hEUVVGRExFTkJRVU1zUTBGQlF5eE5RVUZOTEVsQlFVa3NRMEZCUXl4RFFVRkRMRkZCUVZFc1EwRkJReXhGUVVOc1JUdFpRVU5KTEVOQlFVTXNRMEZCUXl4WFFVRlhMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXl4RFFVRkRPMWxCUXpGQ0xFTkJRVU1zUTBGQlF5eE5RVUZOTEVkQlFVY3NRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJRenRUUVVOd1FqdFJRVU5FTEU5QlFVOHNRMEZCUXl4RFFVRkRPMGxCUTJJc1EwRkJRenRKUVVsRUxIZENRVUZQTEVkQlFWQTdVVUZEU1N4SlFVRkpMRWxCUVVrc1EwRkJReXhGUVVGRkxFbEJRVWtzU1VGQlNTeEZRVUZGTzFsQlEycENMRWxCUVVrc1EwRkJReXhGUVVGRkxFZEJRVWNzU1VGQlNTeE5RVUZOTEVOQlFVTXNTVUZCU1N4RFFVRkRMRVZCUVVVc1EwRkJReXhEUVVGRE8xTkJRMnBETzFGQlNVUXNTVUZCU1N4RFFVRkRMRVZCUVVVc1EwRkJReXhMUVVGTExFTkJRVU1zU1VGQlNTeERRVUZETEZGQlFWRXNRMEZCUXl4RFFVRkRPMUZCUXpkQ0xFbEJRVWtzUTBGQlF5eEhRVUZsTEVsQlFVa3NRMEZCUXp0UlFVTjZRaXhQUVVGUExFTkJRVU1zUTBGQlF5eEhRVUZITEVsQlFVa3NRMEZCUXl4WlFVRlpMRVZCUVVVc1EwRkJReXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETEZGQlFWRXNTVUZCU1N4RFFVRkRMRU5CUVVNc1MwRkJTeXhGUVVGRkxFZEJRVWNzVFVGQlRTeERRVUZETEdWQlFXVXNTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJReXhOUVVGTkxFTkJRVU1zUlVGQlJUdFpRVU5xUnl4SlFVRkpMRVZCUVVVc1IwRkJSeXhEUVVGRExFTkJRVU1zU1VGQlNTeERRVUZETEV0QlFVc3NSVUZCUlN4RlFVRkZMRWRCUVVjc1EwRkJReXhEUVVGRExFdEJRVXNzUTBGQlF5eExRVUZMTEVOQlFVTTdXVUZOTVVNc1NVRkJTU3hGUVVGRkxFdEJRVXNzUlVGQlJTeEZRVUZGTzJkQ1FVTllMRWxCUVVrc1EwRkJReXhGUVVGRkxFTkJRVU1zUzBGQlN5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMkZCUTNCQ08ybENRVUZOTzJkQ1FVTklMRWxCUVVrc1JVRkJSU3hEUVVGRExESkNRVUV5UWl4RFFVRkRMRU5CUVVNc1EwRkJReXhMUVVGTExFVkJRVVVzUTBGQlF5eERRVUZETEVsQlFVa3NRMEZCUXl4RlFVRkZPMjlDUVVWcVJDeERRVUZETEVOQlFVTXNZVUZCWVN4SFFVRkhMRWxCUVVrc1EwRkJRenR2UWtGRGRrSXNVMEZCVXp0cFFrRkRXanRuUWtGRlJDeEpRVUZKTEV0QlFVc3NSMEZCUnl4RlFVRkZMRU5CUVVNc1dVRkJXU3hEUVVGRExFTkJRVU1zUTBGQlF5eEpRVUZKTEVWQlFVVXNRMEZCUXl4RFFVRkRMRXRCUVVzc1EwRkJReXhEUVVGRE8yZENRVU0zUXl4SlFVRkpMRXRCUVVzc1MwRkJTeXhKUVVGSkxFVkJRVVU3YjBKQlEyaENMRWxCUVVrc1EwRkJReXhGUVVGRkxFTkJRVU1zVFVGQlRTeERRVUZETEV0QlFVc3NRMEZCUXl4RlFVRkZMRU5CUVVNc1EwRkJRenR2UWtGRGVrSXNTVUZCU1N4RFFVRkRMRVZCUVVVc1EwRkJReXhOUVVGTkxFTkJRVU1zUzBGQlN5eERRVUZETEVWQlFVVXNRMEZCUXl4RFFVRkRPMjlDUVVONlFpeEpRVUZKTEVOQlFVTXNSVUZCUlN4RFFVRkRMRTFCUVUwc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF6dHZRa0ZEYmtJc1NVRkJTU3hEUVVGRExGRkJRVkVzUTBGQlF5eEpRVUZKTEVOQlFVTXNTMEZCU3l4RFFVRkRMRlZCUVZVc1EwRkJReXhEUVVGRE8ybENRVU40UXp0eFFrRkJUVHR2UWtGSlNDeERRVUZETEVOQlFVTXNZVUZCWVN4SFFVRkhMRWxCUVVrc1EwRkJRenR2UWtGRGRrSXNVMEZCVXp0cFFrRkRXanRuUWtGRFJDeEpRVUZKTEVOQlFVTXNRMEZCUXl4TFFVRkxMRVZCUVVVc1NVRkJTU3hEUVVGRExFVkJRVVU3YjBKQlMyaENMRWxCUVVrc1EwRkJReXhSUVVGUkxFTkJRVU1zU1VGQlNTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMmxDUVVONlFqdHhRa0ZCVFR0dlFrRkpTQ3hKUVVGSkxFTkJRVU1zUlVGQlJTeERRVUZETEV0QlFVc3NRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJRenRwUWtGRGNFSTdZVUZEU2p0VFFVMUtPMGxCU1V3c1EwRkJRenRKUVVkRUxITkNRVUZMTEVkQlFVdzdVVUZEU1N4SlFVRkpMRU5CUVVNc1QwRkJUeXhGUVVGRkxFTkJRVU03VVVGRFppeEpRVUZKTEZGQlFWRXNSMEZCUnl4TlFVRk5MRU5CUVVNc1UwRkJVeXhGUVVGRkxFbEJRVWtzUjBGQlJ5eEpRVUZKTEVOQlFVTXNSVUZCUlN4RFFVRkRMRWxCUVVrc1JVRkJSU3hEUVVGRE8xRkJRM1pFTEU5QlFVOHNTVUZCU1N4RFFVRkRMRWRCUVVjc1EwRkJReXhSUVVGUkxFZEJRVWNzU1VGQlNTeERRVUZETEVkQlFVY3NUVUZCVFN4RlFVRkZPMWxCUTNaRExFbEJRVWtzUTBGQlF5eFBRVUZQTEVWQlFVVXNRMEZCUXp0WlFVTm1MRkZCUVZFc1IwRkJSeXhKUVVGSkxFTkJRVU03V1VGRGFFSXNTVUZCU1N4SFFVRkhMRWxCUVVrc1EwRkJReXhGUVVGRkxFTkJRVU1zU1VGQlNTeEZRVUZGTEVOQlFVTTdVMEZEZWtJN1VVRkRSQ3hQUVVGUExFbEJRVWtzUTBGQlF6dEpRVU5vUWl4RFFVRkRPMGxCY0V0TkxESkNRVUZ2UWl4SFFVRkhMRU5CUVVNc1NVRkJTU3hEUVVGRE8wbEJRemRDTEhOQ1FVRmxMRWRCUVVjc1EwRkJReXhMUVVGTExFTkJRVU03U1VGdlMzQkRMR0ZCUVVNN1EwRkJRU3hCUVhwTFJDeEpRWGxMUXp0QlFYcExXU3gzUWtGQlRUdEJRV2xNYmtJc1UwRkJaMElzTWtKQlFUSkNMRU5CUVVNc1MwRkJaMFFzUlVGQlJTeFZRVUZ0UWl4RlFVRkZMRlZCUVcxQ08wbEJSMnhKTEVsQlFVMHNSVUZCUlN4SFFVRmxMRXRCUVVzc1EwRkJReXhIUVVGSExFTkJRVU1zVlVGQlFTeERRVUZETEVsQlFVa3NUMEZCUVN4SlFVRkpMRkZCUVZFc1EwRkJReXhEUVVGRExFTkJRVU1zWVVGQllTeERRVUZETEVWQlFUZENMRU5CUVRaQ0xFTkJRVU1zUTBGQlF6dEpRVU55UlN4SlFVRk5MRVZCUVVVc1IwRkJhVUlzUlVGQlJTeERRVUZETzBsQlF6VkNMRWxCUVUwc1EwRkJReXhIUVVGSExFdEJRVXNzUTBGQlF5eE5RVUZOTEVOQlFVTTdTVUZEZGtJc1MwRkJTeXhKUVVGSkxFTkJRVU1zUjBGQlJ5eERRVUZETEVWQlFVVXNRMEZCUXl4SFFVRkhMRU5CUVVNc1IwRkJSeXhEUVVGRExFVkJRVVVzUTBGQlF5eEZRVUZGTEVWQlFVVTdVVUZETlVJc1NVRkJUU3hKUVVGSkxFZEJRVWNzUzBGQlN5eERRVUZETEVOQlFVTXNRMEZCUXl4RlFVRkZMRXRCUVVzc1IwRkJSeXhMUVVGTExFTkJRVU1zUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXl4RFFVRkRPMUZCUXpWRExFVkJRVVVzUTBGQlF5eEpRVUZKTEVOQlFVTXNTVUZCU1N4VlFVRlZMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF5eEZRVUZGTEVWQlFVVXNRMEZCUXl4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eEpRVUZKTEVOQlFVTXNTVUZCU1N4SFFVRkhMRXRCUVVzc1EwRkJReXhKUVVGSkxFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMHRCUXpORk8wbEJRMFFzU1VGQlRTeFJRVUZSTEVkQlFVY3NSVUZCUlN4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVOc1FpeFRRVUZUTEVkQlFVY3NSVUZCUlN4RFFVRkRMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUlVGRGNrSXNXVUZCV1N4SFFVRkhMRXRCUVVzc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eEpRVUZKTEVkQlFVY3NRMEZCUXl4RlFVTm9ReXhoUVVGaExFZEJRVWNzUzBGQlN5eERRVUZETEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJReXhKUVVGSkxFZEJRVWNzUTBGQlF5eERRVUZETzBsQlF6RkRMRWxCUVVrc1RVRkJUU3hIUVVGaExFbEJRVWtzUlVGQlJTeE5RVUZOTEVkQlFXRXNTVUZCU1N4RFFVRkRPMGxCUTNKRUxFbEJRVWtzVlVGQlZTeEZRVUZGTzFGQlExb3NUVUZCVFN4SFFVRkhMRWxCUVVrc1VVRkJVU3hEUVVGRExGVkJRVlVzUlVGQlJTeFJRVUZSTEVOQlFVTXNUVUZCVFN4SFFVRkhMRWxCUVVrc1EwRkJReXhEUVVGRE8xRkJRekZFTEVWQlFVVXNRMEZCUXl4SlFVRkpMRU5CUVVNc1RVRkJUU3hEUVVGRExFTkJRVU03VVVGRGFFSXNSVUZCUlN4RFFVRkRMRWxCUVVrc1EwRkJReXhKUVVGSkxGVkJRVlVzUTBGQlF5eE5RVUZOTEVWQlFVVXNVVUZCVVN4RlFVRkZMRmxCUVZrc1EwRkJReXhEUVVGRExFTkJRVU03UzBGRE0wUTdTVUZEUkN4SlFVRkpMRlZCUVZVc1JVRkJSVHRSUVVOYUxFMUJRVTBzUjBGQlJ5eEpRVUZKTEZGQlFWRXNRMEZCUXl4VlFVRlZMRVZCUVVVc1UwRkJVeXhEUVVGRExFMUJRVTBzUjBGQlJ5eEpRVUZKTEVOQlFVTXNRMEZCUXp0UlFVTXpSQ3hGUVVGRkxFTkJRVU1zU1VGQlNTeERRVUZETEUxQlFVMHNRMEZCUXl4RFFVRkRPMUZCUTJoQ0xFVkJRVVVzUTBGQlF5eEpRVUZKTEVOQlFVTXNTVUZCU1N4VlFVRlZMRU5CUVVNc1UwRkJVeXhGUVVGRkxFMUJRVTBzUlVGQlJTeGhRVUZoTEVOQlFVTXNRMEZCUXl4RFFVRkRPMHRCUXpkRU8wbEJRMFFzU1VGQlNTeE5RVUZOTEVkQlFVY3NTVUZCU1N4TlFVRk5MRU5CUVVNc1JVRkJSU3hGUVVGRkxFVkJRVVVzUTBGQlF5eERRVUZETzBsQlEyaERMRTFCUVUwc1EwRkJReXhMUVVGTExFVkJRVVVzUTBGQlF6dEpRVU5tTEU5QlFVODdVVUZEU0N4VlFVRlZMRVZCUVVVc1JVRkJSU3hEUVVGRExFdEJRVXNzUTBGQlF5eERRVUZETEVWQlFVVXNTMEZCU3l4RFFVRkRMRTFCUVUwc1EwRkJReXhEUVVGRExFZEJRVWNzUTBGQlF5eFZRVUZCTEVOQlFVTXNTVUZCU1N4UFFVRkJMRU5CUVVNc1EwRkJReXhSUVVGUkxFVkJRVVVzUlVGQldpeERRVUZaTEVOQlFVTTdVVUZETlVRc1ZVRkJWU3hGUVVGRkxFMUJRVTBzUTBGQlF5eERRVUZETEVOQlFVTXNUVUZCVFN4RFFVRkRMRkZCUVZFc1JVRkJSU3hEUVVGRExFTkJRVU1zUTBGQlF5eFJRVUZSTEVOQlFVTXNVVUZCVVN4RlFVRkZMRWRCUVVjc1dVRkJXVHRSUVVNelJTeFZRVUZWTEVWQlFVVXNUVUZCVFN4RFFVRkRMRU5CUVVNc1EwRkJReXhOUVVGTkxFTkJRVU1zVVVGQlVTeEZRVUZGTEVOQlFVTXNRMEZCUXl4RFFVRkRMRk5CUVZNc1EwRkJReXhSUVVGUkxFVkJRVVVzUjBGQlJ5eGhRVUZoTzB0QlEyaEdMRU5CUVVNN1FVRkRUaXhEUVVGRE8wRkJhRU5FTEd0RlFXZERReUo5Il19
