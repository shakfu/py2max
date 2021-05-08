# Parsing .maxpat files

## Concept

Convert JSON to py2max objects and then use an ast-to-source-code generator to generator python source code.

### JSON to py2max

see the `@classmethod from_file` in the `Patcher` object.

### Python to Source Code

Doesn't exist generically, so may have to role my own.

The following could help:

- `ast.uparse` in [3.9 stdlib](https://docs.python.org/3/library/ast.html#ast.unparse).

- [astunparse](https://astunparse.readthedocs.io/en/latest/) | [github](https://github.com/simonpercivall/astunparse).

- [astor](https://astor.readthedocs.io) | [github repo](https://github.com/berkerpeksag/astor).

- see also: [redbaron](https://redbaron.readthedocs.io/en/latest/)