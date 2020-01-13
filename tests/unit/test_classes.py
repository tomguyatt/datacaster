import re
import pytest

from typing import Optional, List, Tuple, Any

from datacaster.classes import CastDataClass
from datacaster import exceptions


class SimpleDataClass(CastDataClass):
    string: str
    integer: int
    floating: float
    list_string: List[str]
    tuple_int: Tuple[int]
    optional_string: Optional[str] = None


class UnsupportedCastRequired(CastDataClass):
    bytes: bytes


class UnsupportedCustomType(CastDataClass):
    unsupported: List[Optional[str]] = None


class InvalidDefaultValueSimple(CastDataClass):
    integer: int = "hello"


class InvalidDefaultValueCustom(CastDataClass):
    integer: Optional[int] = "hello"


class AllowMissingAndExtra(CastDataClass):
    integer: int
    string: str


class DisallowMissingAndExtra(CastDataClass):
    IGNORE_EXTRA = False
    SET_MISSING_NONE = False

    integer: int
    string: str


class TestSkippedAny(CastDataClass):
    any: Any


class TestCustomCaster(CastDataClass):
    list_of_strings: str

    def __cast_list_of_strings__(self, value):
        return [str(i) for i in value]


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
                "list_string": [1.0, None, {"hello": "cat"}],
                "tuple_int": ("1",),
                "optional_string": 123,
            },
            {
                "string": "None",
                "integer": 123,
                "floating": 1.0,
                "list_string": ["1.0", "None", "{'hello': 'cat'}"],
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
    instance = SimpleDataClass(**constructor)
    assert vars(instance) == expected_dict, f"Instance {instance} has different attributes to {expected_dict}"


def test_cast_attributes_unsupported():
    with pytest.raises(exceptions.UnsupportedType):
        UnsupportedCastRequired(bytes=123)
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


def test_missing_and_extra():
    assert vars(AllowMissingAndExtra(extra="hello")) == {"integer": None, "string": None}
    with pytest.raises(exceptions.UnexpectedArgument):
        DisallowMissingAndExtra(extra="hello")
    with pytest.raises(exceptions.MissingArgument):
        DisallowMissingAndExtra(string="hello")


def test_any():
    assert vars(TestSkippedAny(any=None)) == {"any": None}
    assert vars(TestSkippedAny(any=123)) == {"any": 123}
    assert vars(TestSkippedAny(any="123")) == {"any": "123"}


def test_custom_caster():
    assert vars(TestCustomCaster(list_of_strings=[1, 2, 3])) == {"list_of_strings": ["1", "2", "3"]}


def test_repr():
    assert repr(TestCustomCaster(list_of_strings=[1, 2, 3])) == "TestCustomCaster(list_of_strings=['1', '2', '3'])"


def test_eq():
    constructor = {"string": 123, "integer": "123", "floating": "1.0", "list_string": ["1", "2", "3"], "tuple_int": "1"}
    assert SimpleDataClass(**constructor) == SimpleDataClass(**constructor)
    assert not SimpleDataClass(**constructor) == SimpleDataClass(
        **{key: value for key, value in constructor.items() if key != "string"}
    )
    assert not SimpleDataClass(**constructor) == TestCustomCaster(string="hello")
