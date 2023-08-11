#!/usr/bin/env bash

rm -rf ./outputs .coverage .pytest_cache .ruff_cache .mypy_cache
find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

