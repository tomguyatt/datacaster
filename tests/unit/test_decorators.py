import re
import pytest

from dataclasses import dataclass
from typing import Optional

from datacaster import decorators, exceptions


@decorators.cast_attributes
@dataclass(frozen=True)
class SimpleDataClass:
    string: str
    integer: int
    floating: float
    optional_string: Optional[str] = None


@decorators.cast_attributes
@dataclass(frozen=True)
class UnsupportedCastRequired:
    bytes: bytes


def test_cast_attributes_simple():
    assert vars(
        SimpleDataClass(string=123, integer="123", floating="1.0")
    ) == {"string": "123", "integer": 123, "floating": 1.0, "optional_string": None}

    assert vars(
        SimpleDataClass(string=1.0, integer=123.0, floating=1, optional_string=None)
    ) == {"string": "1.0", "integer": 123, "floating": 1.0, "optional_string": None}

    assert vars(
        SimpleDataClass(string=None, integer=123.0, floating=1, optional_string=123)
    ) == {"string": "None", "integer": 123, "floating": 1.0, "optional_string": "123"}

    assert vars(
        SimpleDataClass(string="123", integer=123, floating=1.0, optional_string="hello")
    ) == {"string": "123", "integer": 123, "floating": 1.0, "optional_string": "hello"}


def test_cast_attributes_unsupported():
    with pytest.raises(exceptions.UnsupportedType):
        UnsupportedCastRequired(bytes=123)
    UnsupportedCastRequired(bytes=b"123")
