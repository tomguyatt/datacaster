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
    class UnsupportedCastRequired(CastDataClass):
        bytes: bytes

    with pytest.raises(exceptions.UnsupportedCast):
        UnsupportedCastRequired(bytes=123)
    UnsupportedCastRequired(bytes=b"123")


def test_invalid_default_value():
    class InvalidDefaultValueCustom(CastDataClass):
        integer: Optional[int] = "hello"

    class InvalidDefaultValueSimple(CastDataClass):
        integer: int = "hello"

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
    class AllowMissingAndExtra(CastDataClass):
        integer: int
        string: str

    class DisallowMissingAndExtra(CastDataClass):
        IGNORE_EXTRA = False
        SET_MISSING_NONE = False

        integer: int
        string: str

    assert vars(AllowMissingAndExtra(extra="hello")) == {"integer": None, "string": None}
    with pytest.raises(exceptions.UnexpectedArgument):
        DisallowMissingAndExtra(extra="hello")
    with pytest.raises(exceptions.MissingArgument):
        DisallowMissingAndExtra(string="hello")


def test_any():
    class TestSkippedAny(CastDataClass):
        any: Any

    assert vars(TestSkippedAny(any=None)) == {"any": None}
    assert vars(TestSkippedAny(any=123)) == {"any": 123}
    assert vars(TestSkippedAny(any="123")) == {"any": "123"}


def test_field_instance_method():
    class FieldInstanceMethod(CastDataClass):
        list_of_strings: str

        def __cast_list_of_strings__(self, value):
            return [str(i) for i in value]

    assert vars(FieldInstanceMethod(list_of_strings=[1, 2, 3])) == {"list_of_strings": ["1", "2", "3"]}


def test_field_map_function():
    class FieldMap(CastDataClass):
        __class_config__ = {
            "cast_functions": {
                "fields": {"list_of_strings": lambda x: [str(i) for i in x]}
            }
        }
        list_of_strings: str

    assert vars(FieldMap(list_of_strings=[1, 2, 3])) == {"list_of_strings": ["1", "2", "3"]}


def test_type_map_function():
    class TypeMap(CastDataClass):
        __class_config__ = {
            "cast_functions": {
                "types": {List[str]: lambda x: [str(i) for i in x]}
            }
        }
        list_of_strings: List[str]

    assert vars(TypeMap(list_of_strings=[1, 2, 3])) == {"list_of_strings": ["1", "2", "3"]}


def test_duplicate_casters():
    class DuplicateCasters(CastDataClass):
        __class_config__ = {
            "cast_functions": {
                "fields": {"list_of_strings": lambda x: [str(i) for i in x]}
            }
        }
        list_of_strings: str

        def __cast_list_of_strings__(self, value):
            return [str(i) for i in value]

    with pytest.raises(exceptions.MultipleCastDefinitions):
        DuplicateCasters(list_of_strings=[1, 2, 3])


def test_invalid_callables():
    class InvalidFieldFunction(CastDataClass):
        __class_config__ = {
            "cast_functions": {
                "fields": {"list_of_strings": lambda x, y, z: [str(i) for i in x]}
            }
        }
        list_of_strings: List[str]

    class InvalidTypeFunction(CastDataClass):
        __class_config__ = {
            "cast_functions": {
                "types": {List[str]: lambda x, y, z: [str(i) for i in x]}
            }
        }
        list_of_strings: List[str]

    with pytest.raises(exceptions.UnsupportedCast):
        InvalidFieldFunction(list_of_strings=[1, 2, 3])

    with pytest.raises(exceptions.UnsupportedCast):
        InvalidTypeFunction(list_of_strings=[1, 2, 3])


def test_repr():
    class FieldInstanceMethod(CastDataClass):
        list_of_strings: str

        def __cast_list_of_strings__(self, value):
            return [str(i) for i in value]

    assert (
        repr(FieldInstanceMethod(list_of_strings=[1, 2, 3])) == "FieldInstanceMethod(list_of_strings=['1', '2', '3'])"
    )


def test_eq():

    class TypeMap(CastDataClass):
        __class_config__ = {
            "cast_functions": {
                "types": {List[str]: lambda x: [str(i) for i in x]}
            }
        }
        list_of_strings: List[str]

    constructor = {"string": 123, "integer": "123", "floating": "1.0", "list_string": ["1", "2", "3"], "tuple_int": "1"}
    assert SimpleDataClass(**constructor) == SimpleDataClass(**constructor)
    assert SimpleDataClass(**constructor) != SimpleDataClass(
        **{key: value for key, value in constructor.items() if key != "string"}
    )
    assert SimpleDataClass(**constructor) != TypeMap(list_of_strings=[1, 2, 3])


def test_class_config_defaults():
    class TestDefaults(CastDataClass):
        name: str
        age: int

    assert TestDefaults(name=100, age="100").__dict__ == {"name": "100", "age": 100}


def test_cast_always():
    class AlwaysCastString(CastDataClass):
        __class_config__ = {
            "cast_functions": {"fields": {"name": lambda x: f"{x} lol!"}},
            "always_cast": ["name"]
        }
        name: str

    assert AlwaysCastString(name="lol").__dict__ == {"name": "lol lol!"}


def test_rename_fields():
    class Renamed(CastDataClass):
        new_name_1: str
        new_name_2: int

        __class_config__ = {
            "rename_fields": {
                "OriginalNameOne": "new_name_1",
                "OriginalNameTwo": "new_name_2",
            }
        }

    assert Renamed(OriginalNameOne="test value", OriginalNameTwo="1").__dict__ == {"new_name_1": "test value", "new_name_2": 1}
