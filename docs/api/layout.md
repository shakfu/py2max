# layout

Layout managers position objects automatically. Select one with the `layout=`
argument to `Patcher` (`"grid"`, `"flow"`, `"columnar"`/`"matrix"`,
`"horizontal"`, `"vertical"`) and call `optimize_layout()`.

```python
p = Patcher('patch.maxpat', layout="flow", flow_direction="vertical")
# ... add objects and lines ...
p.optimize_layout()
```

::: py2max.layout
    options:
      show_root_heading: false
      members_order: source
      filters: ["!^_"]
