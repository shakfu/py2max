# Experimenting with Auto-layout Algorithms

This section provides a visual comparison of the results of different layout algorithm applied to the same set of objects. 

The default is a very basic grid layout algo that's implemented in the current `LayoutManager`. Other algorithms are provided by the following projects and have been tested in `py2max/tests`:

1. [networkx](https://networkx.org) - a general network analysis library in python.

2. [adaptagrams hola](http://www.adaptagrams.org) - using libdialect and HOLA: Human-like Orthogonal Network Layout 

3. [tsmpy](https://github.com/uknfire/tsmpy) - An orthogonal layout algorithm, using TSM approach covers some of the experimentation in various methods on how to auto-layout objects in a pymax generated file.

### Default Layout

![default](assets/imgs/default.png)


## Adaptragrams Layouts

### adptagrams-hola Layout

![hola](assets/imgs/hola.png)


## Networkx Layouts

### networkx-hamada-kawai Layout

![kamada_kawai_layout](assets/imgs/kamada_kawai_layout.png)

### graphviz-neato Layout

![neato](assets/imgs/neato.png)

### networkx-planar Layout

![planar](assets/imgs/planar.png)

### networkx-shell Layout

![shell](assets/imgs/shell.png)

### networkx-spectral Layout

![spectral](assets/imgs/spectral.png)

### networkx-spring-layout Layout

![spring-layout](assets/imgs/spring-layout.png)

### networkx-circular Layout

![circular](assets/imgs/circular.png)



## TSMP Layouts

### tsmp0-uselp Layout

![tsmp0-uselp](assets/imgs/tsmp0-uselp.png)

### tsmp1-uselp Layout

![tsmp1-uselp](assets/imgs/tsmp1-uselp.png)

### tsmp1 Layout

![tsmp1](assets/imgs/tsmp1.png)



## Graphviz Layouts

### graphviz-dot Layout

![dot](assets/imgs/dot.png)

### graphviz-fdp Layout

![fdp](assets/imgs/fdp.png)


### graphviz-twopi Layout

![twopi](assets/imgs/twopi.png)


### graphviz-sfdp Layout

![sfdp](assets/imgs/sfdp.png)

