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

From this blog [article](https://codeyarns.com/tech/2017-02-27-how-to-convert-python-dict-to-class-object-with-fields.html):

```python
>>> from collections import namedtuple
>>> d = {"name": "joe", "age": 20}
>>> d
{'age': 20, 'name': 'joe'}
>>> d_named = namedtuple("Employee", d.keys())(*d.values())
>>> d_named
Employee(name='joe', age=20)
>>> d_named.name
```
