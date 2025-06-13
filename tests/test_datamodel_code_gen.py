#!/usr/bin/env python3

"""convert.py

Handles conversion

- from .maxref xml files to json schema
- from json schema to pydantic models
"""

import pytest
pytest.skip("skipping datamodel_code_generator tests", allow_module_level=True)

from pathlib import Path
from tempfile import TemporaryDirectory

try:
    from datamodel_code_generator import InputFileType, generate
    from datamodel_code_generator import DataModelType
    HAS_DATAMODEL_CODE_GENERATOR = True
except ImportError:
    HAS_DATAMODEL_CODE_GENERATOR = False

@pytest.mark.skipif(not HAS_DATAMODEL_CODE_GENERATOR, reason="needs datamodel_code_generator to be installed")
def test_datamodel_code_generator():
    json_schema: str = """
    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://example.com/product.schema.json",
        "title": "Product",
        "description": "A product from Acme's catalog",
        "type": "object",
        "properties": {
        "productId": {
          "description": "The unique identifier for a product",
          "type": "integer"
        },
        "productName": {
          "description": "Name of the product",
          "type": "string"
        },
        "price": {
          "description": "The price of the product",
          "type": "number",
          "exclusiveMinimum": 0
        },
        "tags": {
          "description": "Tags for the product",
          "type": "array",
          "items": {
            "type": "string"
          },
          "minItems": 1,
          "uniqueItems": true
        },
        "dimensions": {
          "type": "object",
          "properties": {
            "length": {
              "type": "number"
            },
            "width": {
              "type": "number"
            },
            "height": {
              "type": "number"
            }
          },
          "required": [ "length", "width", "height" ]
        }
        },
        "required": [ "productId", "productName", "price" ]
    }
    """

    json_schema1: str = """{
        "type": "object",
        "subclass": "Box",
        "title": "MyModel",
        "properties": {
            "number": {"type": "number"},
            "street_name": {"type": "string"},
            "street_type": {"type": "string",
                            "enum": ["Street", "Avenue", "Boulevard"]
                            }
        }
    }"""

    with TemporaryDirectory() as temporary_directory_name:
        temporary_directory = Path(temporary_directory_name)
        output = Path(temporary_directory / 'model.py')
        model = None
        generate(
            json_schema,
            input_file_type=InputFileType.JsonSchema,
            input_filename="example.json",
            output=output,
            # set up the output model types
            output_model_type=DataModelType.PydanticV2BaseModel,
        )
        model: str = output.read_text()
        assert model is not None


