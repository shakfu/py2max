# Experimenting with Auto-layout Algorithms

This section provides a visual comparison of the results of different layout algorithm applied to the same set of objects.

The default is a very basic grid layout algo that's implemented in the current `LayoutManager`. Other algorithms are provided by the following projects and have been tested in `py2max/tests`:

1. [networkx](https://networkx.org) - a general network analysis library in python.

2. [graphviz](https://graphviz.org) - well known graphing library (activated via networkx and [pygraphviz](https://github.com/pygraphviz/pygraphviz))

3. [adaptagrams hola](http://www.adaptagrams.org) - using the `libdialect` library and its HOLA algo: Human-like Orthogonal Network Layout

4. [pyhola](https://github.com/shakfu/pyhola) - a sibling project which provides a pybind11 wrapper for the adaptagrams HOLA graph layout algorithm.

5. [tsmpy](https://github.com/uknfire/tsmpy) - An orthogonal layout algorithm, using the Topology-Shaped-Metric (TSM) approach covers some of the experimentation in various methods on how to auto-layout objects in a pymax generated file.

6. [OrthogonalDrawing](https://github.com/hasii2011/OrthogonalDrawing) -- a fork of tsmpy using a variant of Topology-Shaped-Metric (TSM)

## Default Layouts

### Default Horizontal Layout

![default_horizontal](assets/imgs/default_h.png)

### Default Vertical Layout

![default_vertical](assets/imgs/default_v.png)

## Adaptagrams Layouts

### adaptagrams-hola Layout

![hola](assets/imgs/hola.png)

### pyhola Layout

![pyhola](assets/imgs/pyhola.png)

## Networkx Layouts

### networkx-spring Layout

![spring-layout](assets/imgs/spring-layout.png)

### networkx-hamada-kawai Layout

![kamada_kawai_layout](assets/imgs/kamada_kawai_layout.png)

### networkx-planar Layout

![planar](assets/imgs/planar.png)

### networkx-shell Layout

![shell](assets/imgs/shell.png)

### networkx-spectral Layout

![spectral](assets/imgs/spectral.png)

### networkx-circular Layout

![circular](assets/imgs/circular.png)

## Graphviz Layouts

### graphviz-dot Layout

![dot](assets/imgs/dot.png)

### graphviz-neato Layout

![neato](assets/imgs/neato.png)

### graphviz-fdp Layout

![fdp](assets/imgs/fdp.png)

### graphviz-sfdp Layout

![sfdp](assets/imgs/sfdp.png)

### graphviz-twopi Layout

![twopi](assets/imgs/twopi.png)

## TSMP Layouts

### tsmpy-uselp-0 Layout

![tsmpy0-uselp](assets/imgs/tsmp0-uselp.png)

### tsmpy-uselp-1 Layout

![tsmpy1-uselp](assets/imgs/tsmp1-uselp.png)

### tsmpy Layout

![tsmpy1](assets/imgs/tsmp1.png)

### OrthogonalDrawing Layout

![orthogonal](assets/imgs/orthogonal.png)
