#!/bin/sh
echo -- Run pytest with coverage
pytest --cov=custom_components/huesyncbox tests/ --cov-report term-missing --cov-report html

echo -- Run mypy type checks
mypy custom_components --check-untyped-defs