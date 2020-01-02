import re
import pytest

from dataclasses import dataclass
from typing import Optional, List

from datacaster import decorators, exceptions


@decorators.cast_attributes()
@dataclass(frozen=True)
class SimpleDataClass:
    string: str
    integer: int
    floating: float
    list_string: List[str]
    optional_string: Optional[str] = None


@decorators.cast_attributes()
@dataclass(frozen=True)
class UnsupportedCastRequired:
    bytes: bytes


@decorators.cast_attributes()
@dataclass(frozen=True)
class UnsupportedCustomType:
    unsupported: List[Optional[str]] = None


@decorators.cast_attributes()
@dataclass(frozen=True)
class InvalidDefaultValueSimple:
    integer: int = "lol"


@decorators.cast_attributes()
@dataclass(frozen=True)
class InvalidDefaultValueCustom:
    integer: Optional[int] = "lol"


@decorators.cast_attributes(ignore_extra=False, set_missing_none=False)
@dataclass(frozen=True)
class NoMissingOrIgnore:
    integer: int
    string: str


def test_cast_attributes_simple():
    assert vars(SimpleDataClass(string=123, integer="123", floating="1.0", list_string=["1", "2", "3"])) == {
        "string": "123",
        "integer": 123,
        "floating": 1.0,
        "list_string": ["1", "2", "3"],
        "optional_string": None,
    }

    assert vars(
        SimpleDataClass(string=1.0, integer=123.0, floating=1, list_string=[1, 2, 3], optional_string=None)
    ) == {"string": "1.0", "integer": 123, "floating": 1.0, "list_string": ["1", "2", "3"], "optional_string": None}

    assert vars(
        SimpleDataClass(
            string=None, integer=123.0, floating=1, list_string=[1.0, None, {"lol": "cat"}], optional_string=123
        )
    ) == {
               "string": "None",
               "integer": 123,
               "floating": 1.0,
               "list_string": ["1.0", "None", "{'lol': 'cat'}"],
               "optional_string": "123",
           }

    assert vars(
        SimpleDataClass(string="123", integer=123, floating=1.0, list_string=(1, 2, 3), optional_string="hello")
    ) == {"string": "123", "integer": 123, "floating": 1.0, "list_string": ["1", "2", "3"], "optional_string": "hello"}

    with pytest.raises(exceptions.CastFailed):
        SimpleDataClass(string="123", integer=123, floating=1.0, list_string=1, optional_string="hello")


def test_cast_attributes_unsupported():
    with pytest.raises(exceptions.UnsupportedType):
        UnsupportedCastRequired(bytes=123)
    with pytest.raises(exceptions.UnsupportedType):
        UnsupportedCustomType()
    UnsupportedCastRequired(bytes=b"123")


def test_invalid_default_value():
    with pytest.raises(exceptions.InvalidDefaultValue):
        InvalidDefaultValueCustom()
    with pytest.raises(exceptions.InvalidDefaultValue):
        InvalidDefaultValueSimple()


def test_ignore_extra():
    assert vars(
        SimpleDataClass(string="123", integer=123, floating=1.0, optional_string="hello", extra_to_ignore="hello")
    ) == {"string": "123", "integer": 123, "floating": 1.0, "list_string": None, "optional_string": "hello"}


def test_missing_none():
    assert vars(SimpleDataClass(string="123")) == {
        "string": "123",
        "integer": None,
        "floating": None,
        "list_string": None,
        "optional_string": None,
    }


def test_no_missing_none():
    with pytest.raises(TypeError):
        NoMissingOrIgnore(integer=123)


def test_no_ignore_extra():
    with pytest.raises(KeyError):
        NoMissingOrIgnore(integer=123, string="lol", extra="hello")
