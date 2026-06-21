# colors

A named Max color palette, a `resolve_color()` helper, and box `THEMES` used by
`Patcher.apply_theme()`. Colors are Max `[r, g, b, a]` floats (0..1); inputs may
be a name (`"red"`), hex (`"#ff8800"`), or a float sequence.

```python
p.add_textbox('toggle').set_color(bg='blue', text='white')
p.apply_theme('dark')   # 'light' | 'dark' | 'blue' | 'high-contrast'
```

::: py2max.core.colors
    options:
      show_root_heading: false
      members_order: source
      filters: ["!^_"]
