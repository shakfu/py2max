// Combined Dagre + Graphlib bundle for browser use
// First, load graphlib
(function(f){if(typeof exports==="object"&&typeof module!=="undefined"){module.exports=f()}else if(typeof define==="function"&&define.amd){define([],f)}else{var g;if(typeof window!=="undefined"){g=window}else if(typeof global!=="undefined"){g=global}else if(typeof self!=="undefined"){g=self}else{g=this}g.graphlib=f()}})(function(){var define,module,exports;return function(){function r(e,n,t){function o(i,f){if(!n[i]){if(!e[i]){var c="function"==typeof require&&require;if(!f&&c)return c(i,!0);if(u)return u(i,!0);var a=new Error("Cannot find module '"+i+"'");throw a.code="MODULE_NOT_FOUND",a}var p=n[i]={exports:{}};e[i][0].call(p.exports,function(r){var n=e[i][1][r];return o(n||r)},p,p.exports,r,e,n,t)}return n[i].exports}for(var u="function"==typeof require&&require,i=0;i<t.length;i++)o(t[i]);return o}return r}()({1:[function(require,module,exports){
/**
 * Copyright (c) 2014, Chris Pettitt
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 * list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 * this list of conditions and the following disclaimer in the documentation
 * and/or other materials provided with the distribution.
 *
 * 3. Neither the name of the copyright holder nor the names of its contributors
 * may be used to endorse or promote products derived from this software without
 * specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */
var lib=require("./lib");module.exports={Graph:lib.Graph,json:require("./lib/json"),alg:require("./lib/alg"),version:lib.version}},{"./lib":17,"./lib/alg":8,"./lib/json":18}],2:[function(require,module,exports){module.exports=components;function components(g){var visited={};var cmpts=[];var cmpt;function dfs(v){if(Object.hasOwn(visited,v))return;visited[v]=true;cmpt.push(v);g.successors(v).forEach(dfs);g.predecessors(v).forEach(dfs)}g.nodes().forEach(function(v){cmpt=[];dfs(v);if(cmpt.length){cmpts.push(cmpt)}});return cmpts}},{}],3:[function(require,module,exports){module.exports=dfs;
/*
 * A helper that preforms a pre- or post-order traversal on the input graph
 * and returns the nodes in the order they were visited. If the graph is
 * undirected then this algorithm will navigate using neighbors. If the graph
 * is directed then this algorithm will navigate using successors.
 *
 * If the order is not "post", it will be treated as "pre".
 */function dfs(g,vs,order){if(!Array.isArray(vs)){vs=[vs]}var navigation=g.isDirected()?v=>g.successors(v):v=>g.neighbors(v);var orderFunc=order==="post"?postOrderDfs:preOrderDfs;var acc=[];var visited={};vs.forEach(v=>{if(!g.hasNode(v)){throw new Error("Graph does not have node: "+v)}orderFunc(v,navigation,visited,acc)});return acc}function postOrderDfs(v,navigation,visited,acc){var stack=[[v,false]];while(stack.length>0){var curr=stack.pop();if(curr[1]){acc.push(curr[0])}else{if(!Object.hasOwn(visited,curr[0])){visited[curr[0]]=true;stack.push([curr[0],true]);forEachRight(navigation(curr[0]),w=>stack.push([w,false]))}}}}function preOrderDfs(v,navigation,visited,acc){var stack=[v];while(stack.length>0){var curr=stack.pop();if(!Object.hasOwn(visited,curr)){visited[curr]=true;acc.push(curr);forEachRight(navigation(curr),w=>stack.push(w))}}}function forEachRight(array,iteratee){var length=array.length;while(length--){iteratee(array[length],length,array)}return array}},{}],4:[function(require,module,exports){var dijkstra=require("./dijkstra");module.exports=dijkstraAll;function dijkstraAll(g,weightFunc,edgeFunc){return g.nodes().reduce(function(acc,v){acc[v]=dijkstra(g,v,weightFunc,edgeFunc);return acc},{})}},{"./dijkstra":5}],5:[function(require,module,exports){var PriorityQueue=require("../data/priority-queue");module.exports=dijkstra;var DEFAULT_WEIGHT_FUNC=()=>1;function dijkstra(g,source,weightFn,edgeFn){return runDijkstra(g,String(source),weightFn||DEFAULT_WEIGHT_FUNC,edgeFn||function(v){return g.outEdges(v)})}function runDijkstra(g,source,weightFn,edgeFn){var results={};var pq=new PriorityQueue;var v,vEntry;var updateNeighbors=function(edge){var w=edge.v!==v?edge.v:edge.w;var wEntry=results[w];var weight=weightFn(edge);var distance=vEntry.distance+weight;if(weight<0){throw new Error("dijkstra does not allow negative edge weights. "+"Bad edge: "+edge+" Weight: "+weight)}if(distance<wEntry.distance){wEntry.distance=distance;wEntry.predecessor=v;pq.decrease(w,distance)}};g.nodes().forEach(function(v){var distance=v===source?0:Number.POSITIVE_INFINITY;results[v]={distance:distance};pq.add(v,distance)});while(pq.size()>0){v=pq.removeMin();vEntry=results[v];if(vEntry.distance===Number.POSITIVE_INFINITY){break}edgeFn(v).forEach(updateNeighbors)}return results}},{"../data/priority-queue":15}],6:[function(require,module,exports){var tarjan=require("./tarjan");module.exports=findCycles;function findCycles(g){return tarjan(g).filter(function(cmpt){return cmpt.length>1||cmpt.length===1&&g.hasEdge(cmpt[0],cmpt[0])})}},{"./tarjan":13}],7:[function(require,module,exports){module.exports=floydWarshall;var DEFAULT_WEIGHT_FUNC=()=>1;function floydWarshall(g,weightFn,edgeFn){return runFloydWarshall(g,weightFn||DEFAULT_WEIGHT_FUNC,edgeFn||function(v){return g.outEdges(v)})}function runFloydWarshall(g,weightFn,edgeFn){var results={};var nodes=g.nodes();nodes.forEach(function(v){results[v]={};results[v][v]={distance:0};nodes.forEach(function(w){if(v!==w){results[v][w]={distance:Number.POSITIVE_INFINITY}}});edgeFn(v).forEach(function(edge){var w=edge.v===v?edge.w:edge.v;var d=weightFn(edge);results[v][w]={distance:d,predecessor:v}})});nodes.forEach(function(k){var rowK=results[k];nodes.forEach(function(i){var rowI=results[i];nodes.forEach(function(j){var ik=rowI[k];var kj=rowK[j];var ij=rowI[j];var altDistance=ik.distance+kj.distance;if(altDistance<ij.distance){ij.distance=altDistance;ij.predecessor=kj.predecessor}})})});return results}},{}],8:[function(require,module,exports){module.exports={components:require("./components"),dijkstra:require("./dijkstra"),dijkstraAll:require("./dijkstra-all"),findCycles:require("./find-cycles"),floydWarshall:require("./floyd-warshall"),isAcyclic:require("./is-acyclic"),postorder:require("./postorder"),preorder:require("./preorder"),prim:require("./prim"),tarjan:require("./tarjan"),topsort:require("./topsort")}},{"./components":2,"./dijkstra":5,"./dijkstra-all":4,"./find-cycles":6,"./floyd-warshall":7,"./is-acyclic":9,"./postorder":10,"./preorder":11,"./prim":12,"./tarjan":13,"./topsort":14}],9:[function(require,module,exports){var topsort=require("./topsort");module.exports=isAcyclic;function isAcyclic(g){try{topsort(g)}catch(e){if(e instanceof topsort.CycleException){return false}throw e}return true}},{"./topsort":14}],10:[function(require,module,exports){var dfs=require("./dfs");module.exports=postorder;function postorder(g,vs){return dfs(g,vs,"post")}},{"./dfs":3}],11:[function(require,module,exports){var dfs=require("./dfs");module.exports=preorder;function preorder(g,vs){return dfs(g,vs,"pre")}},{"./dfs":3}],12:[function(require,module,exports){var Graph=require("../graph");var PriorityQueue=require("../data/priority-queue");module.exports=prim;function prim(g,weightFunc){var result=new Graph;var parents={};var pq=new PriorityQueue;var v;function updateNeighbors(edge){var w=edge.v===v?edge.w:edge.v;var pri=pq.priority(w);if(pri!==undefined){var edgeWeight=weightFunc(edge);if(edgeWeight<pri){parents[w]=v;pq.decrease(w,edgeWeight)}}}if(g.nodeCount()===0){return result}g.nodes().forEach(function(v){pq.add(v,Number.POSITIVE_INFINITY);result.setNode(v)});
// Start from an arbitrary node
pq.decrease(g.nodes()[0],0);var init=false;while(pq.size()>0){v=pq.removeMin();if(Object.hasOwn(parents,v)){result.setEdge(v,parents[v])}else if(init){throw new Error("Input graph is not connected: "+g)}else{init=true}g.nodeEdges(v).forEach(updateNeighbors)}return result}},{"../data/priority-queue":15,"../graph":16}],13:[function(require,module,exports){module.exports=tarjan;function tarjan(g){var index=0;var stack=[];var visited={};// node id -> { onStack, lowlink, index }
var results=[];function dfs(v){var entry=visited[v]={onStack:true,lowlink:index,index:index++};stack.push(v);g.successors(v).forEach(function(w){if(!Object.hasOwn(visited,w)){dfs(w);entry.lowlink=Math.min(entry.lowlink,visited[w].lowlink)}else if(visited[w].onStack){entry.lowlink=Math.min(entry.lowlink,visited[w].index)}});if(entry.lowlink===entry.index){var cmpt=[];var w;do{w=stack.pop();visited[w].onStack=false;cmpt.push(w)}while(v!==w);results.push(cmpt)}}g.nodes().forEach(function(v){if(!Object.hasOwn(visited,v)){dfs(v)}});return results}},{}],14:[function(require,module,exports){function topsort(g){var visited={};var stack={};var results=[];function visit(node){if(Object.hasOwn(stack,node)){throw new CycleException}if(!Object.hasOwn(visited,node)){stack[node]=true;visited[node]=true;g.predecessors(node).forEach(visit);delete stack[node];results.push(node)}}g.sinks().forEach(visit);if(Object.keys(visited).length!==g.nodeCount()){throw new CycleException}return results}class CycleException extends Error{constructor(){super(...arguments)}}module.exports=topsort;topsort.CycleException=CycleException},{}],15:[function(require,module,exports){
/**
 * A min-priority queue data structure. This algorithm is derived from Cormen,
 * et al., "Introduction to Algorithms". The basic idea of a min-priority
 * queue is that you can efficiently (in O(1) time) get the smallest key in
 * the queue. Adding and removing elements takes O(log n) time. A key can
 * have its priority decreased in O(log n) time.
 */
class PriorityQueue{_arr=[];_keyIndices={};
/**
   * Returns the number of elements in the queue. Takes `O(1)` time.
   */size(){return this._arr.length}
/**
   * Returns the keys that are in the queue. Takes `O(n)` time.
   */keys(){return this._arr.map(function(x){return x.key})}
/**
   * Returns `true` if **key** is in the queue and `false` if not.
   */has(key){return Object.hasOwn(this._keyIndices,key)}
/**
   * Returns the priority for **key**. If **key** is not present in the queue
   * then this function returns `undefined`. Takes `O(1)` time.
   *
   * @param {Object} key
   */priority(key){var index=this._keyIndices[key];if(index!==undefined){return this._arr[index].priority}}
/**
   * Returns the key for the minimum element in this queue. If the queue is
   * empty this function throws an Error. Takes `O(1)` time.
   */min(){if(this.size()===0){throw new Error("Queue underflow")}return this._arr[0].key}
/**
   * Inserts a new key into the priority queue. If the key already exists in
   * the queue this function returns `false`; otherwise it will return `true`.
   * Takes `O(n)` time.
   *
   * @param {Object} key the key to add
   * @param {Number} priority the initial priority for the key
   */add(key,priority){var keyIndices=this._keyIndices;key=String(key);if(!Object.hasOwn(keyIndices,key)){var arr=this._arr;var index=arr.length;keyIndices[key]=index;arr.push({key:key,priority:priority});this._decrease(index);return true}return false}
/**
   * Removes and returns the smallest key in the queue. Takes `O(log n)` time.
   */removeMin(){this._swap(0,this._arr.length-1);var min=this._arr.pop();delete this._keyIndices[min.key];this._heapify(0);return min.key}
/**
   * Decreases the priority for **key** to **priority**. If the new priority is
   * greater than the previous priority, this function will throw an Error.
   *
   * @param {Object} key the key for which to raise priority
   * @param {Number} priority the new priority for the key
   */decrease(key,priority){var index=this._keyIndices[key];if(priority>this._arr[index].priority){throw new Error("New priority is greater than current priority. "+"Key: "+key+" Old: "+this._arr[index].priority+" New: "+priority)}this._arr[index].priority=priority;this._decrease(index)}_heapify(i){var arr=this._arr;var l=2*i;var r=l+1;var largest=i;if(l<arr.length){largest=arr[l].priority<arr[largest].priority?l:largest;if(r<arr.length){largest=arr[r].priority<arr[largest].priority?r:largest}if(largest!==i){this._swap(i,largest);this._heapify(largest)}}}_decrease(index){var arr=this._arr;var priority=arr[index].priority;var parent;while(index!==0){parent=index>>1;if(arr[parent].priority<priority){break}this._swap(index,parent);index=parent}}_swap(i,j){var arr=this._arr;var keyIndices=this._keyIndices;var origArrI=arr[i];var origArrJ=arr[j];arr[i]=origArrJ;arr[j]=origArrI;keyIndices[origArrJ.key]=i;keyIndices[origArrI.key]=j}}module.exports=PriorityQueue},{}],16:[function(require,module,exports){"use strict";var DEFAULT_EDGE_NAME="\0";var GRAPH_NODE="\0";var EDGE_KEY_DELIM="";
// Implementation notes:
//
//  * Node id query functions should return string ids for the nodes
//  * Edge id query functions should return an "edgeObj", edge object, that is
//    composed of enough information to uniquely identify an edge: {v, w, name}.
//  * Internally we use an "edgeId", a stringified form of the edgeObj, to
//    reference edges. This is because we need a performant way to look these
//    edges up and, object properties, which have string keys, are the closest
//    we're going to get to a performant hashtable in JavaScript.
class Graph{_isDirected=true;_isMultigraph=false;_isCompound=false;
// Label for the graph itself
_label;
// Defaults to be set when creating a new node
_defaultNodeLabelFn=()=>undefined;
// Defaults to be set when creating a new edge
_defaultEdgeLabelFn=()=>undefined;
// v -> label
_nodes={};
// v -> edgeObj
_in={};
// u -> v -> Number
_preds={};
// v -> edgeObj
_out={};
// v -> w -> Number
_sucs={};
// e -> edgeObj
_edgeObjs={};
// e -> label
_edgeLabels={};
/* Number of nodes in the graph. Should only be changed by the implementation. */_nodeCount=0;
/* Number of edges in the graph. Should only be changed by the implementation. */_edgeCount=0;_parent;_children;constructor(opts){if(opts){this._isDirected=Object.hasOwn(opts,"directed")?opts.directed:true;this._isMultigraph=Object.hasOwn(opts,"multigraph")?opts.multigraph:false;this._isCompound=Object.hasOwn(opts,"compound")?opts.compound:false}if(this._isCompound){
// v -> parent
this._parent={};
// v -> children
this._children={};this._children[GRAPH_NODE]={}}}
/* === Graph functions ========= */
/**
   * Whether graph was created with 'directed' flag set to true or not.
   */isDirected(){return this._isDirected}
/**
   * Whether graph was created with 'multigraph' flag set to true or not.
   */isMultigraph(){return this._isMultigraph}
/**
   * Whether graph was created with 'compound' flag set to true or not.
   */isCompound(){return this._isCompound}
/**
   * Sets the label of the graph.
   */setGraph(label){this._label=label;return this}
/**
   * Gets the graph label.
   */graph(){return this._label}
/* === Node functions ========== */
/**
   * Sets the default node label. If newDefault is a function, it will be
   * invoked ach time when setting a label for a node. Otherwise, this label
   * will be assigned as default label in case if no label was specified while
   * setting a node.
   * Complexity: O(1).
   */setDefaultNodeLabel(newDefault){this._defaultNodeLabelFn=newDefault;if(typeof newDefault!=="function"){this._defaultNodeLabelFn=()=>newDefault}return this}
/**
   * Gets the number of nodes in the graph.
   * Complexity: O(1).
   */nodeCount(){return this._nodeCount}
/**
   * Gets all nodes of the graph. Note, the in case of compound graph subnodes are
   * not included in list.
   * Complexity: O(1).
   */nodes(){return Object.keys(this._nodes)}
/**
   * Gets list of nodes without in-edges.
   * Complexity: O(|V|).
   */sources(){var self=this;return this.nodes().filter(v=>Object.keys(self._in[v]).length===0)}
/**
   * Gets list of nodes without out-edges.
   * Complexity: O(|V|).
   */sinks(){var self=this;return this.nodes().filter(v=>Object.keys(self._out[v]).length===0)}
/**
   * Invokes setNode method for each node in names list.
   * Complexity: O(|names|).
   */setNodes(vs,value){var args=arguments;var self=this;vs.forEach(function(v){if(args.length>1){self.setNode(v,value)}else{self.setNode(v)}});return this}
/**
   * Creates or updates the value for the node v in the graph. If label is supplied
   * it is set as the value for the node. If label is not supplied and the node was
   * created by this call then the default node label will be assigned.
   * Complexity: O(1).
   */setNode(v,value){if(Object.hasOwn(this._nodes,v)){if(arguments.length>1){this._nodes[v]=value}return this}this._nodes[v]=arguments.length>1?value:this._defaultNodeLabelFn(v);if(this._isCompound){this._parent[v]=GRAPH_NODE;this._children[v]={};this._children[GRAPH_NODE][v]=true}this._in[v]={};this._preds[v]={};this._out[v]={};this._sucs[v]={};++this._nodeCount;return this}
/**
   * Gets the label of node with specified name.
   * Complexity: O(|V|).
   */node(v){return this._nodes[v]}
/**
   * Detects whether graph has a node with specified name or not.
   */hasNode(v){return Object.hasOwn(this._nodes,v)}
/**
   * Remove the node with the name from the graph or do nothing if the node is not in
   * the graph. If the node was removed this function also removes any incident
   * edges.
   * Complexity: O(1).
   */removeNode(v){var self=this;if(Object.hasOwn(this._nodes,v)){var removeEdge=e=>self.removeEdge(self._edgeObjs[e]);delete this._nodes[v];if(this._isCompound){this._removeFromParentsChildList(v);delete this._parent[v];this.children(v).forEach(function(child){self.setParent(child)});delete this._children[v]}Object.keys(this._in[v]).forEach(removeEdge);delete this._in[v];delete this._preds[v];Object.keys(this._out[v]).forEach(removeEdge);delete this._out[v];delete this._sucs[v];--this._nodeCount}return this}
/**
   * Sets node p as a parent for node v if it is defined, or removes the
   * parent for v if p is undefined. Method throws an exception in case of
   * invoking it in context of noncompound graph.
   * Average-case complexity: O(1).
   */setParent(v,parent){if(!this._isCompound){throw new Error("Cannot set parent in a non-compound graph")}if(parent===undefined){parent=GRAPH_NODE}else{
// Coerce parent to string
parent+="";for(var ancestor=parent;ancestor!==undefined;ancestor=this.parent(ancestor)){if(ancestor===v){throw new Error("Setting "+parent+" as parent of "+v+" would create a cycle")}}this.setNode(parent)}this.setNode(v);this._removeFromParentsChildList(v);this._parent[v]=parent;this._children[parent][v]=true;return this}_removeFromParentsChildList(v){delete this._children[this._parent[v]][v]}
/**
   * Gets parent node for node v.
   * Complexity: O(1).
   */parent(v){if(this._isCompound){var parent=this._parent[v];if(parent!==GRAPH_NODE){return parent}}}
/**
   * Gets list of direct children of node v.
   * Complexity: O(1).
   */children(v=GRAPH_NODE){if(this._isCompound){var children=this._children[v];if(children){return Object.keys(children)}}else if(v===GRAPH_NODE){return this.nodes()}else if(this.hasNode(v)){return[]}}
/**
   * Return all nodes that are predecessors of the specified node or undefined if node v is not in
   * the graph. Behavior is undefined for undirected graphs - use neighbors instead.
   * Complexity: O(|V|).
   */predecessors(v){var predsV=this._preds[v];if(predsV){return Object.keys(predsV)}}
/**
   * Return all nodes that are successors of the specified node or undefined if node v is not in
   * the graph. Behavior is undefined for undirected graphs - use neighbors instead.
   * Complexity: O(|V|).
   */successors(v){var sucsV=this._sucs[v];if(sucsV){return Object.keys(sucsV)}}
/**
   * Return all nodes that are predecessors or successors of the specified node or undefined if
   * node v is not in the graph.
   * Complexity: O(|V|).
   */neighbors(v){var preds=this.predecessors(v);if(preds){const union=new Set(preds);for(var succ of this.successors(v)){union.add(succ)}return Array.from(union.values())}}isLeaf(v){var neighbors;if(this.isDirected()){neighbors=this.successors(v)}else{neighbors=this.neighbors(v)}return neighbors.length===0}
/**
   * Creates new graph with nodes filtered via filter. Edges incident to rejected node
   * are also removed. In case of compound graph, if parent is rejected by filter,
   * than all its children are rejected too.
   * Average-case complexity: O(|E|+|V|).
   */filterNodes(filter){var copy=new this.constructor({directed:this._isDirected,multigraph:this._isMultigraph,compound:this._isCompound});copy.setGraph(this.graph());var self=this;Object.entries(this._nodes).forEach(function([v,value]){if(filter(v)){copy.setNode(v,value)}});Object.values(this._edgeObjs).forEach(function(e){if(copy.hasNode(e.v)&&copy.hasNode(e.w)){copy.setEdge(e,self.edge(e))}});var parents={};function findParent(v){var parent=self.parent(v);if(parent===undefined||copy.hasNode(parent)){parents[v]=parent;return parent}else if(parent in parents){return parents[parent]}else{return findParent(parent)}}if(this._isCompound){copy.nodes().forEach(v=>copy.setParent(v,findParent(v)))}return copy}
/* === Edge functions ========== */
/**
   * Sets the default edge label or factory function. This label will be
   * assigned as default label in case if no label was specified while setting
   * an edge or this function will be invoked each time when setting an edge
   * with no label specified and returned value * will be used as a label for edge.
   * Complexity: O(1).
   */setDefaultEdgeLabel(newDefault){this._defaultEdgeLabelFn=newDefault;if(typeof newDefault!=="function"){this._defaultEdgeLabelFn=()=>newDefault}return this}
/**
   * Gets the number of edges in the graph.
   * Complexity: O(1).
   */edgeCount(){return this._edgeCount}
/**
   * Gets edges of the graph. In case of compound graph subgraphs are not considered.
   * Complexity: O(|E|).
   */edges(){return Object.values(this._edgeObjs)}
/**
   * Establish an edges path over the nodes in nodes list. If some edge is already
   * exists, it will update its label, otherwise it will create an edge between pair
   * of nodes with label provided or default label if no label provided.
   * Complexity: O(|nodes|).
   */setPath(vs,value){var self=this;var args=arguments;vs.reduce(function(v,w){if(args.length>1){self.setEdge(v,w,value)}else{self.setEdge(v,w)}return w});return this}
/**
   * Creates or updates the label for the edge (v, w) with the optionally supplied
   * name. If label is supplied it is set as the value for the edge. If label is not
   * supplied and the edge was created by this call then the default edge label will
   * be assigned. The name parameter is only useful with multigraphs.
   */setEdge(){var v,w,name,value;var valueSpecified=false;var arg0=arguments[0];if(typeof arg0==="object"&&arg0!==null&&"v"in arg0){v=arg0.v;w=arg0.w;name=arg0.name;if(arguments.length===2){value=arguments[1];valueSpecified=true}}else{v=arg0;w=arguments[1];name=arguments[3];if(arguments.length>2){value=arguments[2];valueSpecified=true}}v=""+v;w=""+w;if(name!==undefined){name=""+name}var e=edgeArgsToId(this._isDirected,v,w,name);if(Object.hasOwn(this._edgeLabels,e)){if(valueSpecified){this._edgeLabels[e]=value}return this}if(name!==undefined&&!this._isMultigraph){throw new Error("Cannot set a named edge when isMultigraph = false")}
// It didn't exist, so we need to create it.
// First ensure the nodes exist.
this.setNode(v);this.setNode(w);this._edgeLabels[e]=valueSpecified?value:this._defaultEdgeLabelFn(v,w,name);var edgeObj=edgeArgsToObj(this._isDirected,v,w,name);
// Ensure we add undirected edges in a consistent way.
v=edgeObj.v;w=edgeObj.w;Object.freeze(edgeObj);this._edgeObjs[e]=edgeObj;incrementOrInitEntry(this._preds[w],v);incrementOrInitEntry(this._sucs[v],w);this._in[w][e]=edgeObj;this._out[v][e]=edgeObj;this._edgeCount++;return this}
/**
   * Gets the label for the specified edge.
   * Complexity: O(1).
   */edge(v,w,name){var e=arguments.length===1?edgeObjToId(this._isDirected,arguments[0]):edgeArgsToId(this._isDirected,v,w,name);return this._edgeLabels[e]}
/**
   * Gets the label for the specified edge and converts it to an object.
   * Complexity: O(1)
   */edgeAsObj(){const edge=this.edge(...arguments);if(typeof edge!=="object"){return{label:edge}}return edge}
/**
   * Detects whether the graph contains specified edge or not. No subgraphs are considered.
   * Complexity: O(1).
   */hasEdge(v,w,name){var e=arguments.length===1?edgeObjToId(this._isDirected,arguments[0]):edgeArgsToId(this._isDirected,v,w,name);return Object.hasOwn(this._edgeLabels,e)}
/**
   * Removes the specified edge from the graph. No subgraphs are considered.
   * Complexity: O(1).
   */removeEdge(v,w,name){var e=arguments.length===1?edgeObjToId(this._isDirected,arguments[0]):edgeArgsToId(this._isDirected,v,w,name);var edge=this._edgeObjs[e];if(edge){v=edge.v;w=edge.w;delete this._edgeLabels[e];delete this._edgeObjs[e];decrementOrRemoveEntry(this._preds[w],v);decrementOrRemoveEntry(this._sucs[v],w);delete this._in[w][e];delete this._out[v][e];this._edgeCount--}return this}
/**
   * Return all edges that point to the node v. Optionally filters those edges down to just those
   * coming from node u. Behavior is undefined for undirected graphs - use nodeEdges instead.
   * Complexity: O(|E|).
   */inEdges(v,u){var inV=this._in[v];if(inV){var edges=Object.values(inV);if(!u){return edges}return edges.filter(edge=>edge.v===u)}}
/**
   * Return all edges that are pointed at by node v. Optionally filters those edges down to just
   * those point to w. Behavior is undefined for undirected graphs - use nodeEdges instead.
   * Complexity: O(|E|).
   */outEdges(v,w){var outV=this._out[v];if(outV){var edges=Object.values(outV);if(!w){return edges}return edges.filter(edge=>edge.w===w)}}
/**
   * Returns all edges to or from node v regardless of direction. Optionally filters those edges
   * down to just those between nodes v and w regardless of direction.
   * Complexity: O(|E|).
   */nodeEdges(v,w){var inEdges=this.inEdges(v,w);if(inEdges){return inEdges.concat(this.outEdges(v,w))}}}function incrementOrInitEntry(map,k){if(map[k]){map[k]++}else{map[k]=1}}function decrementOrRemoveEntry(map,k){if(!--map[k]){delete map[k]}}function edgeArgsToId(isDirected,v_,w_,name){var v=""+v_;var w=""+w_;if(!isDirected&&v>w){var tmp=v;v=w;w=tmp}return v+EDGE_KEY_DELIM+w+EDGE_KEY_DELIM+(name===undefined?DEFAULT_EDGE_NAME:name)}function edgeArgsToObj(isDirected,v_,w_,name){var v=""+v_;var w=""+w_;if(!isDirected&&v>w){var tmp=v;v=w;w=tmp}var edgeObj={v:v,w:w};if(name){edgeObj.name=name}return edgeObj}function edgeObjToId(isDirected,edgeObj){return edgeArgsToId(isDirected,edgeObj.v,edgeObj.w,edgeObj.name)}module.exports=Graph},{}],17:[function(require,module,exports){
// Includes only the "core" of graphlib
module.exports={Graph:require("./graph"),version:require("./version")}},{"./graph":16,"./version":19}],18:[function(require,module,exports){var Graph=require("./graph");module.exports={write:write,read:read};
/**
 * Creates a JSON representation of the graph that can be serialized to a string with
 * JSON.stringify. The graph can later be restored using json.read.
 */function write(g){var json={options:{directed:g.isDirected(),multigraph:g.isMultigraph(),compound:g.isCompound()},nodes:writeNodes(g),edges:writeEdges(g)};if(g.graph()!==undefined){json.value=structuredClone(g.graph())}return json}function writeNodes(g){return g.nodes().map(function(v){var nodeValue=g.node(v);var parent=g.parent(v);var node={v:v};if(nodeValue!==undefined){node.value=nodeValue}if(parent!==undefined){node.parent=parent}return node})}function writeEdges(g){return g.edges().map(function(e){var edgeValue=g.edge(e);var edge={v:e.v,w:e.w};if(e.name!==undefined){edge.name=e.name}if(edgeValue!==undefined){edge.value=edgeValue}return edge})}
/**
 * Takes JSON as input and returns the graph representation.
 *
 * @example
 * var g2 = graphlib.json.read(JSON.parse(str));
 * g2.nodes();
 * // ['a', 'b']
 * g2.edges()
 * // [ { v: 'a', w: 'b' } ]
 */function read(json){var g=new Graph(json.options).setGraph(json.value);json.nodes.forEach(function(entry){g.setNode(entry.v,entry.value);if(entry.parent){g.setParent(entry.v,entry.parent)}});json.edges.forEach(function(entry){g.setEdge({v:entry.v,w:entry.w,name:entry.name},entry.value)});return g}},{"./graph":16}],19:[function(require,module,exports){module.exports="2.2.4"},{}]},{},[1])(1)});

// Shim require for dagre to find graphlib
(function() {
    var originalRequire = typeof require !== 'undefined' ? require : null;
    window.require = function(name) {
        if (name === '@dagrejs/graphlib') {
            return window.graphlib;
        }
        if (originalRequire) {
            return originalRequire(name);
        }
        throw new Error('Cannot require ' + name);
    };
})();

// Now load dagre
var dagre=(()=>{var g=(e=>typeof require!="undefined"?require:typeof Proxy!="undefined"?new Proxy(e,{get:(t,r)=>(typeof require!="undefined"?require:t)[r]}):e)(function(e){if(typeof require!="undefined")return require.apply(this,arguments);throw Error('Dynamic require of "'+e+'" is not supported')});var p=(e,t)=>()=>(t||e((t={exports:{}}).exports,t),t.exports);var A=p((ai,Y)=>{var L=class{constructor(){let t={};t._next=t._prev=t,this._sentinel=t}dequeue(){let t=this._sentinel,r=t._prev;if(r!==t)return D(r),r}enqueue(t){let r=this._sentinel;t._prev&&t._next&&D(t),t._next=r._next,r._next._prev=t,r._next=t,t._prev=r}toString(){let t=[],r=this._sentinel,n=r._prev;for(;n!==r;)t.push(JSON.stringify(n,Ot)),n=n._prev;return"["+t.join(", ")+"]"}};function D(e){e._prev._next=e._next,e._next._prev=e._prev,delete e._next,delete e._prev}function Ot(e,t){if(e!=="_next"&&e!=="_prev")return t}Y.exports=L});var z=p((li,W)=>{var It=g("@dagrejs/graphlib").Graph,qt=A();W.exports=Rt;var Lt=()=>1;function Rt(e,t){if(e.nodeCount()<=1)return[];let r=Mt(e,t||Lt);return Ct(r.graph,r.buckets,r.zeroIdx).flatMap(i=>e.outEdges(i.v,i.w))}function Ct(e,t,r){let n=[],i=t[t.length-1],a=t[0],o;for(;e.nodeCount();){for(;o=a.dequeue();)R(e,t,r,o);for(;o=i.dequeue();)R(e,t,r,o);if(e.nodeCount()){for(let l=t.length-2;l>0;--l)if(o=t[l].dequeue(),o){n=n.concat(R(e,t,r,o,!0));break}}}return n}function R(e,t,r,n,i){let a=i?[]:void 0;return e.inEdges(n.v).forEach(o=>{let l=e.edge(o),s=e.node(o.v);i&&a.push({v:o.v,w:o.w}),s.out-=l,C(t,r,s)}),e.outEdges(n.v).forEach(o=>{let l=e.edge(o),s=o.w,d=e.node(s);d.in-=l,C(t,r,d)}),e.removeNode(n.v),a}function Mt(e,t){let r=new It,n=0,i=0;e.nodes().forEach(l=>{r.setNode(l,{v:l,in:0,out:0})}),e.edges().forEach(l=>{let s=r.edge(l.v,l.w)||0,d=t(l),u=s+d;r.setEdge(l.v,l.w,u),i=Math.max(i,r.node(l.v).out+=d),n=Math.max(n,r.node(l.w).in+=d)});let a=Tt(i+n+3).map(()=>new qt),o=n+1;return r.nodes().forEach(l=>{C(a,o,r.node(l))}),{graph:r,buckets:a,zeroIdx:o}}function C(e,t,r){r.out?r.in?e[r.out-r.in+t].enqueue(r):e[e.length-1].enqueue(r):e[0].enqueue(r)}function Tt(e){let t=[];for(let r=0;r<e;r++)t.push(r);return t}});var m=p((si,Z)=>{"use strict";var X=g("@dagrejs/graphlib").Graph;Z.exports={addBorderNode:Dt,addDummyNode:H,applyWithChunking:N,asNonCompoundGraph:_t,buildLayerMatrix:Vt,intersectRect:Gt,mapValues:Ut,maxRank:J,normalizeRanks:Ft,notime:zt,partition:At,pick:Ht,predecessorWeights:Pt,range:Q,removeEmptyRanks:Bt,simplify:jt,successorWeights:St,time:Wt,uniqueId:K,zipObject:M};function H(e,t,r,n){for(var i=n;e.hasNode(i);)i=K(n);return r.dummy=t,e.setNode(i,r),i}function jt(e){let t=new X().setGraph(e.graph());return e.nodes().forEach(r=>t.setNode(r,e.node(r))),e.edges().forEach(r=>{let n=t.edge(r.v,r.w)||{weight:0,minlen:1},i=e.edge(r);t.setEdge(r.v,r.w,{weight:n.weight+i.weight,minlen:Math.max(n.minlen,i.minlen)})}),t}function _t(e){let t=new X({multigraph:e.isMultigraph()}).setGraph(e.graph());return e.nodes().forEach(r=>{e.children(r).length||t.setNode(r,e.node(r))}),e.edges().forEach(r=>{t.setEdge(r,e.edge(r))}),t}function St(e){let t=e.nodes().map(r=>{let n={};return e.outEdges(r).forEach(i=>{n[i.w]=(n[i.w]||0)+e.edge(i).weight}),n});return M(e.nodes(),t)}function Pt(e){let t=e.nodes().map(r=>{let n={};return e.inEdges(r).forEach(i=>{n[i.v]=(n[i.v]||0)+e.edge(i).weight}),n});return M(e.nodes(),t)}function Gt(e,t){let r=e.x,n=e.y,i=t.x-r,a=t.y-n,o=e.width/2,l=e.height/2;if(!i&&!a)throw new Error("Not possible to find intersection inside of the rectangle");let s,d;return Math.abs(a)*o>Math.abs(i)*l?(a<0&&(l=-l),s=l*i/a,d=l):(i<0&&(o=-o),s=o,d=o*a/i),{x:r+s,y:n+d}}function Vt(e){let t=Q(J(e)+1).map(()=>[]);return e.nodes().forEach(r=>{let n=e.node(r),i=n.rank;i!==void 0&&(t[i][n.order]=r)}),t}function Ft(e){let t=e.nodes().map(n=>{let i=e.node(n).rank;return i===void 0?Number.MAX_VALUE:i}),r=N(Math.min,t);e.nodes().forEach(n=>{let i=e.node(n);Object.hasOwn(i,"rank")&&(i.rank-=r)})}function Bt(e){let t=e.nodes().map(o=>e.node(o).rank).filter(o=>o!==void 0),r=N(Math.min,t),n=[];e.nodes().forEach(o=>{let l=e.node(o).rank-r;n[l]||(n[l]=[]),n[l].push(o)});let i=0,a=e.graph().nodeRankFactor;Array.from(n).forEach((o,l)=>{o===void 0&&l%a!==0?--i:o!==void 0&&i&&o.forEach(s=>e.node(s).rank+=i)})}function Dt(e,t,r,n){let i={width:0,height:0};return arguments.length>=4&&(i.rank=r,i.order=n),H(e,"border",i,t)}function Yt(e,t=U){let r=[];for(let n=0;n<e.length;n+=t){let i=e.slice(n,n+t);r.push(i)}return r}var U=65535;function N(e,t){if(t.length>U){let r=Yt(t);return e.apply(null,r.map(n=>e.apply(null,n)))}else return e.apply(null,t)}function J(e){let r=e.nodes().map(n=>{let i=e.node(n).rank;return i===void 0?Number.MIN_VALUE:i});return N(Math.max,r)}function At(e,t){let r={lhs:[],rhs:[]};return e.forEach(n=>{t(n)?r.lhs.push(n):r.rhs.push(n)}),r}function Wt(e,t){let r=Date.now();try{return t()}finally{console.log(e+" time: "+(Date.now()-r)+"ms")}}function zt(e,t){return t()}var Xt=0;function K(e){var t=++Xt;return e+(""+t)}function Q(e,t,r=1){t==null&&(t=e,e=0);let n=a=>a<t;r<0&&(n=a=>t<a);let i=[];for(let a=e;n(a);a+=r)i.push(a);return i}function Ht(e,t){let r={};for(let n of t)e[n]!==void 0&&(r[n]=e[n]);return r}function Ut(e,t){let r=t;return typeof t=="string"&&(r=n=>n[t]),Object.entries(e).reduce((n,[i,a])=>(n[i]=r(a,i),n),{})}function M(e,t){return e.reduce((r,n,i)=>(r[n]=t[i],r),{})}});var ee=p((di,$)=>{"use strict";var Jt=z(),Kt=m().uniqueId;$.exports={run:Qt,undo:$t};function Qt(e){(e.graph().acyclicer==="greedy"?Jt(e,r(e)):Zt(e)).forEach(n=>{let i=e.edge(n);e.removeEdge(n),i.forwardName=n.name,i.reversed=!0,e.setEdge(n.w,n.v,i,Kt("rev"))});function r(n){return i=>n.edge(i).weight}}function Zt(e){let t=[],r={},n={};function i(a){Object.hasOwn(n,a)||(n[a]=!0,r[a]=!0,e.outEdges(a).forEach(o=>{Object.hasOwn(r,o.w)?t.push(o):i(o.w)}),delete r[a])}return e.nodes().forEach(i),t}function $t(e){e.edges().forEach(t=>{let r=e.edge(t);if(r.reversed){e.removeEdge(t);let n=r.forwardName;delete r.reversed,delete r.forwardName,e.setEdge(t.w,t.v,r,n)}})}});var re=p((ui,te)=>{"use strict";var er=m();te.exports={run:tr,undo:nr};function tr(e){e.graph().dummyChains=[],e.edges().forEach(t=>rr(e,t))}function rr(e,t){let r=t.v,n=e.node(r).rank,i=t.w,a=e.node(i).rank,o=t.name,l=e.edge(t),s=l.labelRank;if(a===n+1)return;e.removeEdge(t);let d,u,h;for(h=0,++n;n<a;++h,++n)l.points=[],u={width:0,height:0,edgeLabel:l,edgeObj:t,rank:n},d=er.addDummyNode(e,"edge",u,"_d"),n===s&&(u.width=l.width,u.height=l.height,u.dummy="edge-label",u.labelpos=l.labelpos),e.setEdge(r,d,{weight:l.weight},o),h===0&&e.graph().dummyChains.push(d),r=d;e.setEdge(r,i,{weight:l.weight},o)}function nr(e){e.graph().dummyChains.forEach(t=>{let r=e.node(t),n=r.edgeLabel,i;for(e.setEdge(r.edgeObj,n);r.dummy;)i=e.successors(t)[0],e.removeNode(t),n.points.push({x:r.x,y:r.y}),r.dummy==="edge-label"&&(n.x=r.x,n.y=r.y,n.width=r.width,n.height=r.height),t=i,r=e.node(t)})}});var v=p((hi,ne)=>{"use strict";var{applyWithChunking:ir}=m();ne.exports={longestPath:or,slack:ar};function or(e){var t={};function r(n){var i=e.node(n);if(Object.hasOwn(t,n))return i.rank;t[n]=!0;let a=e.outEdges(n).map(l=>l==null?Number.POSITIVE_INFINITY:r(l.w)-e.edge(l).minlen);var o=ir(Math.min,a);return o===Number.POSITIVE_INFINITY&&(o=0),i.rank=o}e.sources().forEach(r)}function ar(e,t){return e.node(t.w).rank-e.node(t.v).rank-e.edge(t).minlen}});var T=p((fi,ie)=>{"use strict";var lr=g("@dagrejs/graphlib").Graph,O=v().slack;ie.exports=sr;function sr(e){var t=new lr({directed:!1}),r=e.nodes()[0],n=e.nodeCount();t.setNode(r,{});for(var i,a;dr(t,e)<n;)i=ur(t,e),a=t.hasNode(i.v)?O(e,i):-O(e,i),hr(t,e,a);return t}function dr(e,t){function r(n){t.nodeEdges(n).forEach(i=>{var a=i.v,o=n===a?i.w:a;!e.hasNode(o)&&!O(t,i)&&(e.setNode(o,{}),e.setEdge(n,o,{}),r(o))})}return e.nodes().forEach(r),e.nodeCount()}function ur(e,t){return t.edges().reduce((n,i)=>{let a=Number.POSITIVE_INFINITY;return e.hasNode(i.v)!==e.hasNode(i.w)&&(a=O(t,i)),a<n[0]?[a,i]:n},[Number.POSITIVE_INFINITY,null])[1]}function hr(e,t,r){e.nodes().forEach(n=>t.node(n).rank+=r)}});var ce=p((ci,fe)=>{"use strict";var fr=T(),oe=v().slack,cr=v().longestPath,pr=g("@dagrejs/graphlib").alg.preorder,mr=g("@dagrejs/graphlib").alg.postorder,br=m().simplify;fe.exports=y;y.initLowLimValues=_;y.initCutValues=j;y.calcCutValue=le;y.leaveEdge=de;y.enterEdge=ue;y.exchangeEdges=he;function y(e){e=br(e),cr(e);var t=fr(e);_(t),j(t,e);for(var r,n;r=de(t);)n=ue(t,e,r),he(t,e,r,n)}function j(e,t){var r=mr(e,e.nodes());r=r.slice(0,r.length-1),r.forEach(n=>wr(e,t,n))}function wr(e,t,r){var n=e.node(r),i=n.parent;e.edge(r,i).cutvalue=le(e,t,r)}function le(e,t,r){var n=e.node(r),i=n.parent,a=!0,o=t.edge(r,i),l=0;return o||(a=!1,o=t.edge(i,r)),l=o.weight,t.nodeEdges(r).forEach(s=>{var d=s.v===r,u=d?s.w:s.v;if(u!==i){var h=d===a,f=t.edge(s).weight;if(l+=h?f:-f,gr(e,r,u)){var c=e.edge(r,u).cutvalue;l+=h?-c:c}}}),l}function _(e,t){arguments.length<2&&(t=e.nodes()[0]),se(e,{},1,t)}function se(e,t,r,n,i){var a=r,o=e.node(n);return t[n]=!0,e.neighbors(n).forEach(l=>{Object.hasOwn(t,l)||(r=se(e,t,r,l,n))}),o.low=a,o.lim=r++,i?o.parent=i:delete o.parent,r}function de(e){return e.edges().find(t=>e.edge(t).cutvalue<0)}function ue(e,t,r){var n=r.v,i=r.w;t.hasEdge(n,i)||(n=r.w,i=r.v);var a=e.node(n),o=e.node(i),l=a,s=!1;a.lim>o.lim&&(l=o,s=!0);var d=t.edges().filter(u=>s===ae(e,e.node(u.v),l)&&s!==ae(e,e.node(u.w),l));return d.reduce((u,h)=>oe(t,h)<oe(t,u)?h:u)}function he(e,t,r,n){var i=r.v,a=r.w;e.removeEdge(i,a),e.setEdge(n.v,n.w,{}),_(e),j(e,t),Er(e,t)}function Er(e,t){var r=e.nodes().find(i=>!t.node(i).parent),n=pr(e,r);n=n.slice(1),n.forEach(i=>{var a=e.node(i).parent,o=t.edge(i,a),l=!1;o||(o=t.edge(a,i),l=!0),t.node(i).rank=t.node(a).rank+(l?o.minlen:-o.minlen)})}function gr(e,t,r){return e.hasEdge(t,r)}function ae(e,t,r){return r.low<=t.lim&&t.lim<=r.lim}});var we=p((pi,be)=>{"use strict";var kr=v(),me=kr.longestPath,xr=T(),yr=ce();be.exports=vr;function vr(e){var t=e.graph().ranker;if(t instanceof Function)return t(e);switch(e.graph().ranker){case"network-simplex":pe(e);break;case"tight-tree":Or(e);break;case"longest-path":Nr(e);break;case"none":break;default:pe(e)}}var Nr=me;function Or(e){me(e),xr(e)}function pe(e){yr(e)}});var ge=p((mi,Ee)=>{Ee.exports=Ir;function Ir(e){let t=Lr(e);e.graph().dummyChains.forEach(r=>{let n=e.node(r),i=n.edgeObj,a=qr(e,t,i.v,i.w),o=a.path,l=a.lca,s=0,d=o[s],u=!0;for(;r!==i.w;){if(n=e.node(r),u){for(;(d=o[s])!==l&&e.node(d).maxRank<n.rank;)s++;d===l&&(u=!1)}if(!u){for(;s<o.length-1&&e.node(d=o[s+1]).minRank<=n.rank;)s++;d=o[s]}e.setParent(r,d),r=e.successors(r)[0]}})}function qr(e,t,r,n){let i=[],a=[],o=Math.min(t[r].low,t[n].low),l=Math.max(t[r].lim,t[n].lim),s,d;s=r;do s=e.parent(s),i.push(s);while(s&&(t[s].low>o||l>t[s].lim));for(d=s,s=n;(s=e.parent(s))!==d;)a.push(s);return{path:i.concat(a.reverse()),lca:d}}function Lr(e){let t={},r=0;function n(i){let a=r;e.children(i).forEach(n),t[i]={low:a,lim:r++}}return e.children().forEach(n),t}});var ye=p((bi,xe)=>{var I=m();xe.exports={run:Rr,cleanup:Tr};function Rr(e){let t=I.addDummyNode(e,"root",{},"_root"),r=Cr(e),n=Object.values(r),i=I.applyWithChunking(Math.max,n)-1,a=2*i+1;e.graph().nestingRoot=t,e.edges().forEach(l=>e.edge(l).minlen*=a);let o=Mr(e)+1;e.children().forEach(l=>ke(e,t,a,o,i,r,l)),e.graph().nodeRankFactor=a}function ke(e,t,r,n,i,a,o){let l=e.children(o);if(!l.length){o!==t&&e.setEdge(t,o,{weight:0,minlen:r});return}let s=I.addBorderNode(e,"_bt"),d=I.addBorderNode(e,"_bb"),u=e.node(o);e.setParent(s,o),u.borderTop=s,e.setParent(d,o),u.borderBottom=d,l.forEach(h=>{ke(e,t,r,n,i,a,h);let f=e.node(h),c=f.borderTop?f.borderTop:h,b=f.borderBottom?f.borderBottom:h,w=f.borderTop?n:2*n,x=c!==b?1:i-a[o]+1;e.setEdge(s,c,{weight:w,minlen:x,nestingEdge:!0}),e.setEdge(b,d,{weight:w,minlen:x,nestingEdge:!0})}),e.parent(o)||e.setEdge(t,s,{weight:0,minlen:i+a[o]})}function Cr(e){var t={};function r(n,i){var a=e.children(n);a&&a.length&&a.forEach(o=>r(o,i+1)),t[n]=i}return e.children().forEach(n=>r(n,1)),t}function Mr(e){return e.edges().reduce((t,r)=>t+e.edge(r).weight,0)}function Tr(e){var t=e.graph();e.removeNode(t.nestingRoot),delete t.nestingRoot,e.edges().forEach(r=>{var n=e.edge(r);n.nestingEdge&&e.removeEdge(r)})}});var Oe=p((wi,Ne)=>{var jr=m();Ne.exports=_r;function _r(e){function t(r){let n=e.children(r),i=e.node(r);if(n.length&&n.forEach(t),Object.hasOwn(i,"minRank")){i.borderLeft=[],i.borderRight=[];for(let a=i.minRank,o=i.maxRank+1;a<o;++a)ve(e,"borderLeft","_bl",r,i,a),ve(e,"borderRight","_br",r,i,a)}}e.children().forEach(t)}function ve(e,t,r,n,i,a){let o={width:0,height:0,rank:a,borderType:t},l=i[t][a-1],s=jr.addDummyNode(e,"border",o,r);i[t][a]=s,e.setParent(s,n),l&&e.setEdge(l,s,{weight:1})}});var Re=p((Ei,Le)=>{"use strict";Le.exports={adjust:Sr,undo:Pr};function Sr(e){let t=e.graph().rankdir.toLowerCase();(t==="lr"||t==="rl")&&qe(e)}function Pr(e){let t=e.graph().rankdir.toLowerCase();(t==="bt"||t==="rl")&&Gr(e),(t==="lr"||t==="rl")&&(Vr(e),qe(e))}function qe(e){e.nodes().forEach(t=>Ie(e.node(t))),e.edges().forEach(t=>Ie(e.edge(t)))}function Ie(e){let t=e.width;e.width=e.height,e.height=t}function Gr(e){e.nodes().forEach(t=>S(e.node(t))),e.edges().forEach(t=>{let r=e.edge(t);r.points.forEach(S),Object.hasOwn(r,"y")&&S(r)})}function S(e){e.y=-e.y}function Vr(e){e.nodes().forEach(t=>P(e.node(t))),e.edges().forEach(t=>{let r=e.edge(t);r.points.forEach(P),Object.hasOwn(r,"x")&&P(r)})}function P(e){let t=e.x;e.x=e.y,e.y=t}});var Te=p((gi,Me)=>{"use strict";var Ce=m();Me.exports=Fr;function Fr(e){let t={},r=e.nodes().filter(s=>!e.children(s).length),n=r.map(s=>e.node(s).rank),i=Ce.applyWithChunking(Math.max,n),a=Ce.range(i+1).map(()=>[]);function o(s){if(t[s])return;t[s]=!0;let d=e.node(s);a[d.rank].push(s),e.successors(s).forEach(o)}return r.sort((s,d)=>e.node(s).rank-e.node(d).rank).forEach(o),a}});var _e=p((ki,je)=>{"use strict";var Br=m().zipObject;je.exports=Dr;function Dr(e,t){let r=0;for(let n=1;n<t.length;++n)r+=Yr(e,t[n-1],t[n]);return r}function Yr(e,t,r){let n=Br(r,r.map((d,u)=>u)),i=t.flatMap(d=>e.outEdges(d).map(u=>({pos:n[u.w],weight:e.edge(u).weight})).sort((u,h)=>u.pos-h.pos)),a=1;for(;a<r.length;)a<<=1;let o=2*a-1;a-=1;let l=new Array(o).fill(0),s=0;return i.forEach(d=>{let u=d.pos+a;l[u]+=d.weight;let h=0;for(;u>0;)u%2&&(h+=l[u+1]),u=u-1>>1,l[u]+=d.weight;s+=d.weight*h}),s}});var Pe=p((xi,Se)=>{Se.exports=Ar;function Ar(e,t=[]){return t.map(r=>{let n=e.inEdges(r);if(n.length){let i=n.reduce((a,o)=>{let l=e.edge(o),s=e.node(o.v);return{sum:a.sum+l.weight*s.order,weight:a.weight+l.weight}},{sum:0,weight:0});return{v:r,barycenter:i.sum/i.weight,weight:i.weight}}else return{v:r}})}});var Ve=p((yi,Ge)=>{"use strict";var Wr=m();Ge.exports=zr;function zr(e,t){let r={};e.forEach((i,a)=>{let o=r[i.v]={indegree:0,in:[],out:[],vs:[i.v],i:a};i.barycenter!==void 0&&(o.barycenter=i.barycenter,o.weight=i.weight)}),t.edges().forEach(i=>{let a=r[i.v],o=r[i.w];a!==void 0&&o!==void 0&&(o.indegree++,a.out.push(r[i.w]))});let n=Object.values(r).filter(i=>!i.indegree);return Xr(n)}function Xr(e){let t=[];function r(i){return a=>{a.merged||(a.barycenter===void 0||i.barycenter===void 0||a.barycenter>=i.barycenter)&&Hr(i,a)}}function n(i){return a=>{a.in.push(i),--a.indegree===0&&e.push(a)}}for(;e.length;){let i=e.pop();t.push(i),i.in.reverse().forEach(r(i)),i.out.forEach(n(i))}return t.filter(i=>!i.merged).map(i=>Wr.pick(i,["vs","i","barycenter","weight"]))}function Hr(e,t){let r=0,n=0;e.weight&&(r+=e.barycenter*e.weight,n+=e.weight),t.weight&&(r+=t.barycenter*t.weight,n+=t.weight),e.vs=t.vs.concat(e.vs),e.barycenter=r/n,e.weight=n,e.i=Math.min(t.i,e.i),t.merged=!0}});var De=p((vi,Be)=>{var Ur=m();Be.exports=Jr;function Jr(e,t){let r=Ur.partition(e,u=>Object.hasOwn(u,"barycenter")),n=r.lhs,i=r.rhs.sort((u,h)=>h.i-u.i),a=[],o=0,l=0,s=0;n.sort(Kr(!!t)),s=Fe(a,i,s),n.forEach(u=>{s+=u.vs.length,a.push(u.vs),o+=u.barycenter*u.weight,l+=u.weight,s=Fe(a,i,s)});let d={vs:a.flat(!0)};return l&&(d.barycenter=o/l,d.weight=l),d}function Fe(e,t,r){let n;for(;t.length&&(n=t[t.length-1]).i<=r;)t.pop(),e.push(n.vs),r++;return r}function Kr(e){return(t,r)=>t.barycenter<r.barycenter?-1:t.barycenter>r.barycenter?1:e?r.i-t.i:t.i-r.i}});var We=p((Ni,Ae)=>{var Qr=Pe(),Zr=Ve(),$r=De();Ae.exports=Ye;function Ye(e,t,r,n){let i=e.children(t),a=e.node(t),o=a?a.borderLeft:void 0,l=a?a.borderRight:void 0,s={};o&&(i=i.filter(f=>f!==o&&f!==l));let d=Qr(e,i);d.forEach(f=>{if(e.children(f.v).length){let c=Ye(e,f.v,r,n);s[f.v]=c,Object.hasOwn(c,"barycenter")&&tn(f,c)}});let u=Zr(d,r);en(u,s);let h=$r(u,n);if(o&&(h.vs=[o,h.vs,l].flat(!0),e.predecessors(o).length)){let f=e.node(e.predecessors(o)[0]),c=e.node(e.predecessors(l)[0]);Object.hasOwn(h,"barycenter")||(h.barycenter=0,h.weight=0),h.barycenter=(h.barycenter*h.weight+f.order+c.order)/(h.weight+2),h.weight+=2}return h}function en(e,t){e.forEach(r=>{r.vs=r.vs.flatMap(n=>t[n]?t[n].vs:n)})}function tn(e,t){e.barycenter!==void 0?(e.barycenter=(e.barycenter*e.weight+t.barycenter*t.weight)/(e.weight+t.weight),e.weight+=t.weight):(e.barycenter=t.barycenter,e.weight=t.weight)}});var Xe=p((Oi,ze)=>{var rn=g("@dagrejs/graphlib").Graph,nn=m();ze.exports=on;function on(e,t,r,n){n||(n=e.nodes());let i=an(e),a=new rn({compound:!0}).setGraph({root:i}).setDefaultNodeLabel(o=>e.node(o));return n.forEach(o=>{let l=e.node(o),s=e.parent(o);(l.rank===t||l.minRank<=t&&t<=l.maxRank)&&(a.setNode(o),a.setParent(o,s||i),e[r](o).forEach(d=>{let u=d.v===o?d.w:d.v,h=a.edge(u,o),f=h!==void 0?h.weight:0;a.setEdge(u,o,{weight:e.edge(d).weight+f})}),Object.hasOwn(l,"minRank")&&a.setNode(o,{borderLeft:l.borderLeft[t],borderRight:l.borderRight[t]}))}),a}function an(e){for(var t;e.hasNode(t=nn.uniqueId("_root")););return t}});var Ue=p((Ii,He)=>{He.exports=ln;function ln(e,t,r){let n={},i;r.forEach(a=>{let o=e.parent(a),l,s;for(;o;){if(l=e.parent(o),l?(s=n[l],n[l]=o):(s=i,i=o),s&&s!==o){t.setEdge(s,o);return}o=l}})}});var $e=p((qi,Ze)=>{"use strict";var sn=Te(),dn=_e(),un=We(),hn=Xe(),fn=Ue(),cn=g("@dagrejs/graphlib").Graph,q=m();Ze.exports=Qe;function Qe(e,t={}){if(typeof t.customOrder=="function"){t.customOrder(e,Qe);return}let r=q.maxRank(e),n=Je(e,q.range(1,r+1),"inEdges"),i=Je(e,q.range(r-1,-1,-1),"outEdges"),a=sn(e);if(Ke(e,a),t.disableOptimalOrderHeuristic)return;let o=Number.POSITIVE_INFINITY,l,s=t.constraints||[];for(let d=0,u=0;u<4;++d,++u){pn(d%2?n:i,d%4>=2,s),a=q.buildLayerMatrix(e);let h=dn(e,a);h<o?(u=0,l=Object.assign({},a),o=h):h===o&&(l=structuredClone(a))}Ke(e,l)}function Je(e,t,r){let n=new Map,i=(a,o)=>{n.has(a)||n.set(a,[]),n.get(a).push(o)};for(let a of e.nodes()){let o=e.node(a);if(typeof o.rank=="number"&&i(o.rank,a),typeof o.minRank=="number"&&typeof o.maxRank=="number")for(let l=o.minRank;l<=o.maxRank;l++)l!==o.rank&&i(l,a)}return t.map(function(a){return hn(e,a,r,n.get(a)||[])})}function pn(e,t,r){let n=new cn;e.forEach(function(i){r.forEach(l=>n.setEdge(l.left,l.right));let a=i.graph().root,o=un(i,a,n,t);o.vs.forEach((l,s)=>i.node(l).order=s),fn(i,n,o.vs)})}function Ke(e,t){Object.values(t).forEach(r=>r.forEach((n,i)=>e.node(n).order=i))}});var dt=p((Li,st)=>{"use strict";var mn=g("@dagrejs/graphlib").Graph,k=m();st.exports={positionX:En,findType1Conflicts:et,findType2Conflicts:tt,addConflict:G,hasConflict:rt,verticalAlignment:nt,horizontalCompaction:it,alignCoordinates:at,findSmallestWidthAlignment:ot,balance:lt};function et(e,t){let r={};function n(i,a){let o=0,l=0,s=i.length,d=a[a.length-1];return a.forEach((u,h)=>{let f=bn(e,u),c=f?e.node(f).order:s;(f||u===d)&&(a.slice(l,h+1).forEach(b=>{e.predecessors(b).forEach(w=>{let x=e.node(w),B=x.order;(B<o||c<B)&&!(x.dummy&&e.node(b).dummy)&&G(r,w,b)})}),l=h+1,o=c)}),a}return t.length&&t.reduce(n),r}function tt(e,t){let r={};function n(a,o,l,s,d){let u;k.range(o,l).forEach(h=>{u=a[h],e.node(u).dummy&&e.predecessors(u).forEach(f=>{let c=e.node(f);c.dummy&&(c.order<s||c.order>d)&&G(r,f,u)})})}function i(a,o){let l=-1,s,d=0;return o.forEach((u,h)=>{if(e.node(u).dummy==="border"){let f=e.predecessors(u);f.length&&(s=e.node(f[0]).order,n(o,d,h,l,s),d=h,l=s)}n(o,d,o.length,s,a.length)}),o}return t.length&&t.reduce(i),r}function bn(e,t){if(e.node(t).dummy)return e.predecessors(t).find(r=>e.node(r).dummy)}function G(e,t,r){if(t>r){let i=t;t=r,r=i}let n=e[t];n||(e[t]=n={}),n[r]=!0}function rt(e,t,r){if(t>r){let n=t;t=r,r=n}return!!e[t]&&Object.hasOwn(e[t],r)}function nt(e,t,r,n){let i={},a={},o={};return t.forEach(l=>{l.forEach((s,d)=>{i[s]=s,a[s]=s,o[s]=d})}),t.forEach(l=>{let s=-1;l.forEach(d=>{let u=n(d);if(u.length){u=u.sort((f,c)=>o[f]-o[c]);let h=(u.length-1)/2;for(let f=Math.floor(h),c=Math.ceil(h);f<=c;++f){let b=u[f];a[d]===d&&s<o[b]&&!rt(r,d,b)&&(a[b]=d,a[d]=i[d]=i[b],s=o[b])}}})}),{root:i,align:a}}function it(e,t,r,n,i){let a={},o=wn(e,t,r,i),l=i?"borderLeft":"borderRight";function s(h,f){let c=o.nodes().slice(),b={},w=c.pop();for(;w;){if(b[w])h(w);else{b[w]=!0,c.push(w);for(let x of f(w))c.push(x)}w=c.pop()}}function d(h){a[h]=o.inEdges(h).reduce((f,c)=>Math.max(f,a[c.v]+o.edge(c)),0)}function u(h){let f=o.outEdges(h).reduce((b,w)=>Math.min(b,a[w.w]-o.edge(w)),Number.POSITIVE_INFINITY),c=e.node(h);f!==Number.POSITIVE_INFINITY&&c.borderType!==l&&(a[h]=Math.max(a[h],f))}return s(d,o.predecessors.bind(o)),s(u,o.successors.bind(o)),Object.keys(n).forEach(h=>a[h]=a[r[h]]),a}function wn(e,t,r,n){let i=new mn,a=e.graph(),o=gn(a.nodesep,a.edgesep,n);return t.forEach(l=>{let s;l.forEach(d=>{let u=r[d];if(i.setNode(u),s){var h=r[s],f=i.edge(h,u);i.setEdge(h,u,Math.max(o(e,d,s),f||0))}s=d})}),i}function ot(e,t){return Object.values(t).reduce((r,n)=>{let i=Number.NEGATIVE_INFINITY,a=Number.POSITIVE_INFINITY;Object.entries(n).forEach(([l,s])=>{let d=kn(e,l)/2;i=Math.max(s+d,i),a=Math.min(s-d,a)});let o=i-a;return o<r[0]&&(r=[o,n]),r},[Number.POSITIVE_INFINITY,null])[1]}function at(e,t){let r=Object.values(t),n=k.applyWithChunking(Math.min,r),i=k.applyWithChunking(Math.max,r);["u","d"].forEach(a=>{["l","r"].forEach(o=>{let l=a+o,s=e[l];if(s===t)return;let d=Object.values(s),u=n-k.applyWithChunking(Math.min,d);o!=="l"&&(u=i-k.applyWithChunking(Math.max,d)),u&&(e[l]=k.mapValues(s,h=>h+u))})})}function lt(e,t){return k.mapValues(e.ul,(r,n)=>{if(t)return e[t.toLowerCase()][n];{let i=Object.values(e).map(a=>a[n]).sort((a,o)=>a-o);return(i[1]+i[2])/2}})}function En(e){let t=k.buildLayerMatrix(e),r=Object.assign(et(e,t),tt(e,t)),n={},i;["u","d"].forEach(o=>{i=o==="u"?t:Object.values(t).reverse(),["l","r"].forEach(l=>{l==="r"&&(i=i.map(h=>Object.values(h).reverse()));let s=(o==="u"?e.predecessors:e.successors).bind(e),d=nt(e,i,r,s),u=it(e,i,d.root,d.align,l==="r");l==="r"&&(u=k.mapValues(u,h=>-h)),n[o+l]=u})});let a=ot(e,n);return at(n,a),lt(n,e.graph().align)}function gn(e,t,r){return(n,i,a)=>{let o=n.node(i),l=n.node(a),s=0,d;if(s+=o.width/2,Object.hasOwn(o,"labelpos"))switch(o.labelpos.toLowerCase()){case"l":d=-o.width/2;break;case"r":d=o.width/2;break}if(d&&(s+=r?d:-d),d=0,s+=(o.dummy?t:e)/2,s+=(l.dummy?t:e)/2,s+=l.width/2,Object.hasOwn(l,"labelpos"))switch(l.labelpos.toLowerCase()){case"l":d=l.width/2;break;case"r":d=-l.width/2;break}return d&&(s+=r?d:-d),d=0,s}}function kn(e,t){return e.node(t).width}});var ft=p((Ri,ht)=>{"use strict";var ut=m(),xn=dt().positionX;ht.exports=yn;function yn(e){e=ut.asNonCompoundGraph(e),vn(e),Object.entries(xn(e)).forEach(([t,r])=>e.node(t).x=r)}function vn(e){let t=ut.buildLayerMatrix(e),r=e.graph().ranksep,n=0;t.forEach(i=>{let a=i.reduce((o,l)=>{let s=e.node(l).height;return o>s?o:s},0);i.forEach(o=>e.node(o).y=n+a/2),n+=a+r})}});var gt=p((Ci,Et)=>{"use strict";var ct=ee(),pt=re(),Nn=we(),On=m().normalizeRanks,In=ge(),qn=m().removeEmptyRanks,mt=ye(),Ln=Oe(),bt=Re(),Rn=$e(),Cn=ft(),E=m(),Mn=g("@dagrejs/graphlib").Graph;Et.exports=Tn;function Tn(e,t={}){let r=t.debugTiming?E.time:E.notime;return r("layout",()=>{let n=r("  buildLayoutGraph",()=>Yn(e));return r("  runLayout",()=>jn(n,r,t)),r("  updateInputGraph",()=>_n(e,n)),n})}function jn(e,t,r){t("    makeSpaceForEdgeLabels",()=>An(e)),t("    removeSelfEdges",()=>Zn(e)),t("    acyclic",()=>ct.run(e)),t("    nestingGraph.run",()=>mt.run(e)),t("    rank",()=>Nn(E.asNonCompoundGraph(e))),t("    injectEdgeLabelProxies",()=>Wn(e)),t("    removeEmptyRanks",()=>qn(e)),t("    nestingGraph.cleanup",()=>mt.cleanup(e)),t("    normalizeRanks",()=>On(e)),t("    assignRankMinMax",()=>zn(e)),t("    removeEdgeLabelProxies",()=>Xn(e)),t("    normalize.run",()=>pt.run(e)),t("    parentDummyChains",()=>In(e)),t("    addBorderSegments",()=>Ln(e)),t("    order",()=>Rn(e,r)),t("    insertSelfEdges",()=>$n(e)),t("    adjustCoordinateSystem",()=>bt.adjust(e)),t("    position",()=>Cn(e)),t("    positionSelfEdges",()=>ei(e)),t("    removeBorderNodes",()=>Qn(e)),t("    normalize.undo",()=>pt.undo(e)),t("    fixupEdgeLabelCoords",()=>Jn(e)),t("    undoCoordinateSystem",()=>bt.undo(e)),t("    translateGraph",()=>Hn(e)),t("    assignNodeIntersects",()=>Un(e)),t("    reversePoints",()=>Kn(e)),t("    acyclic.undo",()=>ct.undo(e))}function _n(e,t){e.nodes().forEach(r=>{let n=e.node(r),i=t.node(r);n&&(n.x=i.x,n.y=i.y,n.order=i.order,n.rank=i.rank,t.children(r).length&&(n.width=i.width,n.height=i.height))}),e.edges().forEach(r=>{let n=e.edge(r),i=t.edge(r);n.points=i.points,Object.hasOwn(i,"x")&&(n.x=i.x,n.y=i.y)}),e.graph().width=t.graph().width,e.graph().height=t.graph().height}var Sn=["nodesep","edgesep","ranksep","marginx","marginy"],Pn={ranksep:50,edgesep:20,nodesep:50,rankdir:"tb"},Gn=["acyclicer","ranker","rankdir","align"],Vn=["width","height","rank"],wt={width:0,height:0},Fn=["minlen","weight","width","height","labeloffset"],Bn={minlen:1,weight:1,width:0,height:0,labeloffset:10,labelpos:"r"},Dn=["labelpos"];function Yn(e){let t=new Mn({multigraph:!0,compound:!0}),r=F(e.graph());return t.setGraph(Object.assign({},Pn,V(r,Sn),E.pick(r,Gn))),e.nodes().forEach(n=>{let i=F(e.node(n)),a=V(i,Vn);Object.keys(wt).forEach(o=>{a[o]===void 0&&(a[o]=wt[o])}),t.setNode(n,a),t.setParent(n,e.parent(n))}),e.edges().forEach(n=>{let i=F(e.edge(n));t.setEdge(n,Object.assign({},Bn,V(i,Fn),E.pick(i,Dn)))}),t}function An(e){let t=e.graph();t.ranksep/=2,e.edges().forEach(r=>{let n=e.edge(r);n.minlen*=2,n.labelpos.toLowerCase()!=="c"&&(t.rankdir==="TB"||t.rankdir==="BT"?n.width+=n.labeloffset:n.height+=n.labeloffset)})}function Wn(e){e.edges().forEach(t=>{let r=e.edge(t);if(r.width&&r.height){let n=e.node(t.v),a={rank:(e.node(t.w).rank-n.rank)/2+n.rank,e:t};E.addDummyNode(e,"edge-proxy",a,"_ep")}})}function zn(e){let t=0;e.nodes().forEach(r=>{let n=e.node(r);n.borderTop&&(n.minRank=e.node(n.borderTop).rank,n.maxRank=e.node(n.borderBottom).rank,t=Math.max(t,n.maxRank))}),e.graph().maxRank=t}function Xn(e){e.nodes().forEach(t=>{let r=e.node(t);r.dummy==="edge-proxy"&&(e.edge(r.e).labelRank=r.rank,e.removeNode(t))})}function Hn(e){let t=Number.POSITIVE_INFINITY,r=0,n=Number.POSITIVE_INFINITY,i=0,a=e.graph(),o=a.marginx||0,l=a.marginy||0;function s(d){let u=d.x,h=d.y,f=d.width,c=d.height;t=Math.min(t,u-f/2),r=Math.max(r,u+f/2),n=Math.min(n,h-c/2),i=Math.max(i,h+c/2)}e.nodes().forEach(d=>s(e.node(d))),e.edges().forEach(d=>{let u=e.edge(d);Object.hasOwn(u,"x")&&s(u)}),t-=o,n-=l,e.nodes().forEach(d=>{let u=e.node(d);u.x-=t,u.y-=n}),e.edges().forEach(d=>{let u=e.edge(d);u.points.forEach(h=>{h.x-=t,h.y-=n}),Object.hasOwn(u,"x")&&(u.x-=t),Object.hasOwn(u,"y")&&(u.y-=n)}),a.width=r-t+o,a.height=i-n+l}function Un(e){e.edges().forEach(t=>{let r=e.edge(t),n=e.node(t.v),i=e.node(t.w),a,o;r.points?(a=r.points[0],o=r.points[r.points.length-1]):(r.points=[],a=i,o=n),r.points.unshift(E.intersectRect(n,a)),r.points.push(E.intersectRect(i,o))})}function Jn(e){e.edges().forEach(t=>{let r=e.edge(t);if(Object.hasOwn(r,"x"))switch((r.labelpos==="l"||r.labelpos==="r")&&(r.width-=r.labeloffset),r.labelpos){case"l":r.x-=r.width/2+r.labeloffset;break;case"r":r.x+=r.width/2+r.labeloffset;break}})}function Kn(e){e.edges().forEach(t=>{let r=e.edge(t);r.reversed&&r.points.reverse()})}function Qn(e){e.nodes().forEach(t=>{if(e.children(t).length){let r=e.node(t),n=e.node(r.borderTop),i=e.node(r.borderBottom),a=e.node(r.borderLeft[r.borderLeft.length-1]),o=e.node(r.borderRight[r.borderRight.length-1]);r.width=Math.abs(o.x-a.x),r.height=Math.abs(i.y-n.y),r.x=a.x+r.width/2,r.y=n.y+r.height/2}}),e.nodes().forEach(t=>{e.node(t).dummy==="border"&&e.removeNode(t)})}function Zn(e){e.edges().forEach(t=>{if(t.v===t.w){var r=e.node(t.v);r.selfEdges||(r.selfEdges=[]),r.selfEdges.push({e:t,label:e.edge(t)}),e.removeEdge(t)}})}function $n(e){var t=E.buildLayerMatrix(e);t.forEach(r=>{var n=0;r.forEach((i,a)=>{var o=e.node(i);o.order=a+n,(o.selfEdges||[]).forEach(l=>{E.addDummyNode(e,"selfedge",{width:l.label.width,height:l.label.height,rank:o.rank,order:a+ ++n,e:l.e,label:l.label},"_se")}),delete o.selfEdges})})}function ei(e){e.nodes().forEach(t=>{var r=e.node(t);if(r.dummy==="selfedge"){var n=e.node(r.e.v),i=n.x+n.width/2,a=n.y,o=r.x-i,l=n.height/2;e.setEdge(r.e,r.label),e.removeNode(t),r.label.points=[{x:i+2*o/3,y:a-l},{x:i+5*o/6,y:a-l},{x:i+o,y:a},{x:i+5*o/6,y:a+l},{x:i+2*o/3,y:a+l}],r.label.x=r.x,r.label.y=r.y}})}function V(e,t){return E.mapValues(E.pick(e,t),Number)}function F(e){var t={};return e&&Object.entries(e).forEach(([r,n])=>{typeof r=="string"&&(r=r.toLowerCase()),t[r]=n}),t}});var xt=p((Mi,kt)=>{var ti=m(),ri=g("@dagrejs/graphlib").Graph;kt.exports={debugOrdering:ni};function ni(e){let t=ti.buildLayerMatrix(e),r=new ri({compound:!0,multigraph:!0}).setGraph({});return e.nodes().forEach(n=>{r.setNode(n,{label:n}),r.setParent(n,"layer"+e.node(n).rank)}),e.edges().forEach(n=>r.setEdge(n.v,n.w,{},n.name)),t.forEach((n,i)=>{let a="layer"+i;r.setNode(a,{rank:"same"}),n.reduce((o,l)=>(r.setEdge(o,l,{style:"invis"}),l))}),r}});var vt=p((Ti,yt)=>{yt.exports="2.0.2"});var ii=p((ji,Nt)=>{Nt.exports={graphlib:g("@dagrejs/graphlib"),layout:gt(),debug:xt(),util:{time:m().time,notime:m().notime},version:vt()}});return ii();})();
/*! For license information please see dagre.min.js.LEGAL.txt */
//# sourceMappingURL=dagre.min.js.map

// Expose dagre.graphlib as the graphlib we loaded
if (typeof dagre !== 'undefined') { dagre.graphlib = window.graphlib; }
