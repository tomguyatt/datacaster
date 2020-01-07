import re
import pytest

from dataclasses import dataclass
from typing import Optional, List, Tuple, Any

from datacaster import decorators, exceptions


@decorators.cast_attributes()
@dataclass(frozen=True)
class SimpleDataClass:
    string: str
    integer: int
    floating: float
    list_string: List[str]
    tuple_int: Tuple[int]
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


@decorators.cast_attributes()
@dataclass(frozen=True)
class TestSkippedAny:
    any: Any


@pytest.mark.parametrize(
    "constructor, expected_dict",
    [
        [
            {"string": 123, "integer": "123", "floating": "1.0", "list_string": ["1", "2", "3"], "tuple_int": "1"},
            {
                "string": "123",
                "integer": 123,
                "floating": 1.0,
                "list_string": ["1", "2", "3"],
                "tuple_int": (1,),
                "optional_string": None,
            },
        ],
        [
            {"string": 1.0, "integer": 123.0, "floating": 1, "list_string": [1, 2, 3], "tuple_int": 1.0},
            {
                "string": "1.0",
                "integer": 123,
                "floating": 1.0,
                "list_string": ["1", "2", "3"],
                "tuple_int": (1,),
                "optional_string": None,
            },
        ],
        [
            {
                "string": None,
                "integer": 123,
                "floating": 1.0,
                "list_string": [1.0, None, {"lol": "cat"}],
                "tuple_int": ("1",),
                "optional_string": 123,
            },
            {
                "string": "None",
                "integer": 123,
                "floating": 1.0,
                "list_string": ["1.0", "None", "{'lol': 'cat'}"],
                "tuple_int": (1,),
                "optional_string": "123",
            },
        ],
        [
            {
                "string": "123",
                "integer": 123,
                "floating": 1.0,
                "list_string": (1, 2, 3),
                "tuple_int": (1,),
                "optional_string": "hello",
            },
            {
                "string": "123",
                "integer": 123,
                "floating": 1.0,
                "list_string": ["1", "2", "3"],
                "tuple_int": (1,),
                "optional_string": "hello",
            },
        ],
        [
            {
                "string": ["test", "list"],
                "integer": "123",
                "floating": "1.0",
                "list_string": "this will be a list",
                "tuple_int": False,
                "optional_string": None,
            },
            {
                "string": "['test', 'list']",
                "integer": 123,
                "floating": 1.0,
                "list_string": ["this will be a list"],
                "tuple_int": (0,),
                "optional_string": None,
            },
        ],
        [
            {
                "string": ["test", "list"],
                "integer": "123",
                "floating": "1.0",
                "list_string": "this will be a list",
                "tuple_int": (True,),
                "optional_string": None,
            },
            {
                "string": "['test', 'list']",
                "integer": 123,
                "floating": 1.0,
                "list_string": ["this will be a list"],
                "tuple_int": (1,),
                "optional_string": None,
            },
        ],
    ],
)
def test_cast_attributes_simple(constructor, expected_dict):
    assert vars(SimpleDataClass(**constructor)) == expected_dict


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
    ) == {
               "string": "123",
               "integer": 123,
               "floating": 1.0,
               "list_string": None,
               "tuple_int": None,
               "optional_string": "hello",
           }


def test_missing_none():
    assert vars(SimpleDataClass(string="123")) == {
        "string": "123",
        "integer": None,
        "floating": None,
        "list_string": None,
        "tuple_int": None,
        "optional_string": None,
    }


def test_no_missing_none():
    with pytest.raises(TypeError):
        NoMissingOrIgnore(integer=123)


def test_no_ignore_extra():
    with pytest.raises(KeyError):
        NoMissingOrIgnore(integer=123, string="lol", extra="hello")


def test_any():
    assert vars(TestSkippedAny(any=None)) == {"any": None}
    assert vars(TestSkippedAny(any=123)) == {"any": 123}
    assert vars(TestSkippedAny(any="123")) == {"any": "123"}
