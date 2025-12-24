#!/bin/sh
pytest --cov=custom_components/huesyncbox tests/ --cov-report term-missing --cov-report html
mypy custom_components  --check-untyped-defs
