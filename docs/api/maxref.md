# maxref

Dynamic Max object information parsed from `.maxref.xml` files (or the bundled
fallback). Provides object help, inlet/outlet counts and types, connection
validation, and the `MaxRefCache` / `MaxRefDB` access layers.

```python
from py2max.maxref import get_object_help, get_available_objects

objects = get_available_objects()        # 1175+ objects
print(get_object_help('umenu'))
```

::: py2max.maxref
    options:
      show_root_heading: false
      members_order: source
      filters: ["!^_"]
