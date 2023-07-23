# TODO

## rnbo

- can remove:
  - base1.yml - `snapshot` field
  - base2.yml - cosmetic fields:
  ```
      patcher:
        accentcolor:
        - 0.343034118413925
        - 0.506230533123016
        - 0.86220508813858
        - 1.0
        bgfillcolor_angle: 270.0
        bgfillcolor_autogradient: 0.0
        bgfillcolor_color:
        - 0.031372549019608
        - 0.125490196078431
        - 0.211764705882353
        - 1.0
        bgfillcolor_color1:
        - 0.031372549019608
        - 0.125490196078431
        - 0.211764705882353
        - 1.0
        bgfillcolor_color2:
        - 0.263682
        - 0.004541
        - 0.038797
        - 1.0
        bgfillcolor_proportion: 0.39
        bgfillcolor_type: color
        color:
        - 0.929412
        - 0.929412
        - 0.352941
        - 1.0
        default_bgcolor:
        - 0.031372549019608
        - 0.125490196078431
        - 0.211764705882353
        - 1.0
        default_fontface: 0
        default_fontname: Lato
        default_fontsize: 12.0
        elementcolor:
        - 0.357540726661682
        - 0.515565991401672
        - 0.861786782741547
        - 1.0
```
  - base3.yml: remove
    - `dependency_cache`
    - `saved_attribute_attributes`
    - `saved_object_attributes`

  - base4.yml: remove
    - `parameters`
    - `rnboattrcache`
    - `rnboversion`
    - `rnboinfo`


## Layout

- [ ] Anchor certain objects in expected places in the grid. One way of doing it is to specify x,y ratios as percentages of the grid. So if `x` is 0.10 and the grid width is 500, then x is positioned at 50. The following are typical cases:
  - ezadc~ to top left
  - ezdac~ to bottom left
  - visualization object (scope, etc.) to bottom right, etc.

## Consider Renaming

- [ ] add_textbox     -> add_newobj or add_new()
- [ ] add_intbox      -> add_int
- [ ] add_floatbox    -> add_float

## Max Classes

Implement more objects: especially containers / objects with state stored in the `.maxpat` file.

- [ ] codebox
- [ ] funbuff
- ...

## Tranformations

- Convert patchlines to references (send/receive)




