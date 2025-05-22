# Graph Drawing Algorithms

## Research

- [graph drawing layout algorithms](http://cs.brown.edu/people/rtamassi/papers/gd-tutorial/gd-constraints.pdf) - nice overview by one of the current experts in the field.

- [graphdrawing.org](http://graphdrawing.org) - research and publication overview for field of graph drawing edited by same author as above.

## Orthogonal Graph Layout

- [adaptagrams](https://github.com/mjwybrow/adaptagrams) - see swig python wrapper

- [pyhola](https://github.com/shakfu/pyhola): my wrapper of hola algo

### Topology-Shaped-Metric

- see [A Generic Framework for the Topology-Shape-Metrics Based Layout by
Paul Klose](https://rtsys.informatik.uni-kiel.de/~biblio/downloads/theses/pkl-mt.pdf)

- [tsmpy](https://github.com/uknfire/tsmpy)

- A fork of tsmpy - [OrthogonalDrawing](https://github.com/hasii2011/OrthogonalDrawing)

## Python Packages

- [NetworkX](https://networkx.org) -- mature Python package for the creation, manipulation, and study of the structure, dynamics, and functions of complex networks.

- [igraph](https://igraph.org/python/) -- mature general graph analysis and drawing. See in particular [layout algos](https://igraph.org/python/doc/tutorial/tutorial.html#layouts-and-plotting)

- [graphviz](http://www.graphviz.org) -- [python bindings](http://www.graphviz.org/resources/#python) -- mature open source graph visualization software. See also graphviz c library [libgvc](http://www.graphviz.org/pdf/gvc.3.pdf)

- [gandalf](https://github.com/bdcht/grandalf) -- promising new graph and drawing algorithms framework

- [toyplot](https://github.com/sandialabs/toyplot) -- plotting toolkit from one of the major reseach labs.

- [jaal](https://github.com/imohitmayank/jaal) -- interactive network visualization

- [orthogonal-drawing-algorithm](https://github.com/rawfh/orthogonal-drawing-algorithm) and its fork [OrthogonalDrawing](https://github.com/hasii2011/OrthogonalDrawing)

- [netgraph](https://github.com/paulbrodersen/netgraph) -- Python module to make publication quality plots of weighted, directed graphs of medium size (10-100 nodes).see also [here](https://stackoverflow.com/questions/39801880/how-to-use-the-pos-argument-in-networkx-to-create-a-flowchart-style-graph/39863493)

- [tulip-python](https://tulip.labri.fr/site/) --

## Non-Python

- [adaptagrams](http://www.adaptagrams.org) c++ library of tools and reusable code for adaptive diagramming applications, for example: drawing tools, automated document and diagram layout, smart presentation software, graph drawing, chart layout.

- [gephi](https://gephi.org) java based mature graph visualization application.

- [dagre-d3](https://github.com/dagrejs/dagre-d3/) A D3-based renderer for the [Dagre](https://github.com/dagrejs/dagre) graph-drawing engine

## Articles

- [Visualizing Networks in Pythnon](https://towardsdatascience.com/visualizing-networks-in-python-d70f4cbeb259) by the author of Jaal

## Stack Overflow

- <https://stackoverflow.com/questions/21978487/improving-python-networkx-graph-layout>

- <https://stackoverflow.com/questions/5028433/graph-auto-layout-algorithm>

- <https://stackoverflow.com/questions/45174962/getting-layout-coordinates-of-graph-vertices-using-python-networkx-pygraphviz> (includes a trick to  generate svg from graphviz and then get coordinates from the svg)

- <https://stackoverflow.com/questions/13938770/how-to-get-the-coordinates-from-layout-from-graphviz>

- <https://stackoverflow.com/questions/53120739/lots-of-edges-on-a-gr>

```python
In [6]: g.add_edges(zip(range(10), range(1,9)))

In [7]: summary(g)
IGRAPH U--- 10 8 --

In [8]: g.vs.degree()
Out[8]: [1, 2, 2, 2, 2, 2, 2, 2, 1, 0]

In [9]: layout = g.layout_reingold_tilford(root=[2])

In [10]: layout
Out[10]: <Layout with 10 vertices and 2 dimensions>

In [11]: layout.coords
Out[11]:
[[-1.0, 2.0],
 [-1.0, 1.0],
 [0.0, 0.0],
 [0.0, 1.0],
 [0.0, 2.0],
 [0.0, 3.0],
 [0.0, 4.0],
 [0.0, 5.0],
 [0.0, 6.0],
 [1.0, 1.0]]
```
