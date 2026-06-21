# utils

Utility helpers, including `pitch2freq` (pitch name to frequency) and
`object_name` (resolve a box's effective Max object name).

```python
from py2max.utils import pitch2freq

pitch2freq("A4")        # 440.0
pitch2freq("C3")        # 130.81
pitch2freq("A4", A4=442)
```

::: py2max.utils
    options:
      show_root_heading: false
      members_order: source
