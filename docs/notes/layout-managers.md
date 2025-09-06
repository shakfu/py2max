# Layout options



```python
    def set_layout_mgr(self, name: str) -> LayoutManager:
        """takes a name and returns an instance of a layout manager"""

        # grid-horizontal or horizontal
        # grid-vertical or vertical
        # grid-horizontal-clustered
        # grid-vertical-clustered
        # flow-horizontal or flow
        # flow-vertical

        if name in ["grid-horizontal", "grid", "horizontal"]:
            return GridLayoutManager(self, flow_direction="horizontal", cluster_connected=False)
        elif name in ["grid-vertical", "vertical"]:
            return GridLayoutManager(self, flow_direction="vertical",   cluster_connected=False)           
        elif name == "grid-horizontal":
            return GridLayoutManager(self, flow_direction="horizontal", cluster_connected=True)
        elif name == "grid-vertical":
            return GridLayoutManager(self, flow_direction="vertical", cluster_connected=True)
        elif name in ["flow-horizontal", "flow"]:
            return FlowLayoutManager(self, flow_direction="horizontal")
        elif name in ["flow-vertical"]:
            return FlowLayoutManager(self, flow_direction="vertical")
        else:
            raise NotImplementedError(f"layout '{name}' not found")
```
