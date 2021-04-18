"""Test helpers."""

from custom_components.huesyncbox import helpers

def test_redacted_readable_output():
    assert("redacted_1" == helpers.redacted(123))
    assert("redacted_2" == helpers.redacted("another value"))

def test_redacted_consistent_output():
    assert(helpers.redacted(1234) == helpers.redacted(1234))

def test_redacted_different_value_different_output():
    assert(helpers.redacted(123) != helpers.redacted("123"))
