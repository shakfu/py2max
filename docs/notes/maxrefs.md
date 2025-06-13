# Using maxrefs to generate pydantic2 models

## Overview

The idea is to use the `*.maxref.xml` files in the four folders (`jit-ref`,  `m4l-ref`,  `max-ref` and `msp-ref`) in `/Applications/Studio/Max.app/Contents/Resources/C74/docs/refpages` which each describe an object in the Max ecosystem as a basis for generating a pydantic2 model in py2max.

The conversion / generation process is described as follows:

1. Convert `obj.maxref.xml` to a python dict, `maxref_dict`,  by `xmltodict`.

2. Convert `maxref_dict` to `json_schema` format.

3. Convert `maxref_dict` or `json_schema` to pydantic2 code, with the following mappings:

    - object to class model
    - object methods to class methods
    - object attributes to class properties

4. Code generation can consist of:

    - **Static generation**: generate all objects based on `*.maxref.xml` files to a respective namespace based on the folder such that `py2max.max.*`, `py2max.jit.*`, `py2max.m4l.*`, and `py2max.msp.*`.

    - **Lazy loading**: dynamically load objects which are generated from their respective `maxref.xml` files.
