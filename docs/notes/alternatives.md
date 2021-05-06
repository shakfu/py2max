# Alternatives & Prototypes

```python
class SmartBox:
    """prototype minimal textbox"""
    def __init__(self, text: str, **kwds):
        self.text = text
        self._kwds = kwds
        self._parse(text)

    def _parse(self, text):
        maxclass = text.split()[0]
        props = OBJECT_DEFAULTS[maxclass]
        props.update(self._kwds)
        self.__dict__.update(props)

    def to_dict(self):
        """create dict from object with extra kwds included"""
        d = vars(self).copy()
        to_del = [k for k in d if k.startswith("_")]
        for k in to_del:
            del d[k]
        d.update(self._kwds)
        return dict(box=d)
```
