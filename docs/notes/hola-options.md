hola-options.mc



```cpp
struct HolaOpts {

    //! Tree layout

    //! When the whole graph is a tree, in what direction should the tree grow?
    CardinalDir defaultTreeGrowthDir = CardinalDir::SOUTH;
    //! Minimal gap between nodes on the same rank, as scalar multiplier of ideal
    //! edge length (IEL):
    double treeLayoutScalar_nodeSep = 0.25;
    //! Minimal gap between ranks (again, IEL scalar):
    double treeLayoutScalar_rankSep = 1.0;
    //! Control whether the subtrees are ordered in symmetric tree layout
    //! so as to promote convex layouts.
    bool preferConvexTrees = true;
    //! Control how connectors are routed for peeled trees:
    TreeRoutingType peeledTreeRouting = TreeRoutingType::CORE_ATTACHMENT;
    //! Control how connectors are routed for graphs which are themselves trees:
    TreeRoutingType wholeTreeRouting = TreeRoutingType::MONOTONIC;

    //! In HOLA, we distinguish between "leaves" (nodes of degree 1), "links"
    //! (nodes of degree 2), and "hubs" (nodes of degree 3 or greater).
    //! The leaves -- and nodes that become leaves when the existing leaves are
    //! removed -- are handled separately as "trees".
    //! The following options control hub layout, and link layout.

    //! Hub configuration

    //! Say whether "flat triangles" should be avoided when using the
    //! OrthoHubLayout.
    bool orthoHubAvoidFlatTriangles = true;

    //! Link configuration

    //! You can use the ACA algorithm for links; or you can use the
    //! shape-conforming chain configuration method, which examines whole chains
    //! of links, and tries to put the bends at the locations that the present
    //! geometry favours.
    //!
    //! In tests, ACA has been preferred on medium and large networks, while
    //! the shape-conforming method has performed well on (very) small networks.
    bool useACAforLinks = true;

    //! Routing

    //! For various routing parameters, we find it makes sense to select
    //! the quantity by multiplying the graph's ideal edge length by
    //! a scalar, set here.
    double routingScalar_crossingPenalty = 2;
    double routingScalar_segmentPenalty = 0.5;
    //! Other routing parameters take an absolute value.
    double routingAbs_nudgingDistance = 4.0;


    //! Tree Placement

    //! Prefer trees to be placed in a cardinal, rather than ordinal, direction:
    bool treePlacement_favourCardinal = true;
    //! Prefer trees to be placed in the external, rather than an internal, face:
    bool treePlacement_favourExternal = true;
    //! Prefer trees to be placed where there are the fewest other trees considering
    //! using that same space:
    bool treePlacement_favourIsolation = true;


    //! Expansion

    //! When expanding faces to make room for trees, and choosing a dimension in which
    //! to operate first, you may want to try choosing the costlier dimension. The theory
    //! would be that in some cases this will mean no expansion is needed at all in the
    //! second dimension.
    bool expansion_doCostlierDimensionFirst = false;
    ExpansionEstimateMethod expansion_estimateMethod = ExpansionEstimateMethod::CONSTRAINTS;


    //! Near Alignment (see nearalign.h)

    //! Attempt near alignments?
    bool do_near_align = true;
    //! How many alignment attempts?
    unsigned align_reps = 2;

    //! As with the routing parameters, we find that it makes sense to set parameters
    //! for the "near alignment" process as scalar multiples of the graph's ideal edge length.

    //! What is the maximum width of a "kink" that should be straightened out?
    double nearAlignScalar_kinkWidth = 0.25;
    //! How far away should we look from a given node for others that should be aligned with it?
    double nearAlignScalar_scope = 1.0;


    //! Misc

    //! Padding to be added to nodes during layout, in order to maintain gaps between them:
    //! Again, this is a scalar multiplier of the IEL.
    double nodePaddingScalar = 0.25;


    //! Finishing

    //! If you prefer a particular type of aspect ratio, set it here. The final layout
    //! will be rotated as necessary.
    AspectRatioClass preferredAspectRatio = AspectRatioClass::LANDSCAPE;
    //! If there is a preferred aspect ratio, there are always two rotations that achieve
    //! it. In order to decide between these two, HOLA will try to make more trees have
    //! the preferred tree growth direction.
    CardinalDir preferredTreeGrowthDir = CardinalDir::SOUTH;
    //! A layout can always be translated, so we can normalise by putting the upper left
    //! corner of the bounding box at the origin.
    bool putUlcAtOrigin = true;

};
```