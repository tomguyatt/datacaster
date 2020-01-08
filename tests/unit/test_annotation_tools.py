import re
import pytest

import typing

from datacaster import annotation_tools, exceptions


@pytest.mark.parametrize(
    "value, expected_output",
    [
        [str, "<class 'str'>"],
        [None, "<class 'NoneType'>"],
        [typing.List, "typing.List"],
        [typing.Optional[str], "typing.Union[str, NoneType]"],
    ],
    ids=["str", "none", "typing_list", "optional_str"],
)
def test_parse_annotation(value, expected_output):
    assert repr(annotation_tools.parse_annotation(value)) == expected_output


@pytest.mark.parametrize(
    "value, expected_output",
    [[str, False], [None, False], [typing.List, True], [typing.Optional[str], True]],
    ids=["str", "none", "typing_list", "optional_str"],
)
def test_is_custom_type(value, expected_output):
    assert annotation_tools.is_custom_type(value) == expected_output


@pytest.mark.parametrize(
    "value, expected_type_classes, expected_exception",
    [
        [typing.Optional[str], ("<class 'str'>", "<class 'NoneType'>"), None],
        [typing.Union[str, None], ("<class 'str'>", "<class 'NoneType'>"), None],
        [typing.List[str], ("<class 'str'>",), None],
        [typing.List[int], ("<class 'int'>",), None],
        [typing.Union[str, int, None], None, exceptions.UnsupportedType],
        [typing.Union[str, int], None, exceptions.UnsupportedType],
        [typing.Union[typing.List, None], None, exceptions.UnsupportedType],
        [typing.Callable, None, exceptions.UnsupportedType],
    ],
    ids=[
        "optional_str",
        "union_str_none",
        "list_str",
        "list_int",
        "too_many_union_types",
        "union_must_be_none",
        "union_must_be_builtin",
        "unsupported_callable",
    ],
)
def test_get_custom_type_classes(value, expected_type_classes, expected_exception):
    # This function is only called on custom types, not builtins.
    if expected_exception:
        with pytest.raises(expected_exception):
            annotation_tools.get_custom_type_classes(value)
    else:
        assert (
            tuple(
                [
                    repr(type_class)
                    for type_class in annotation_tools.get_custom_type_classes(value)
                ]
            )
            == expected_type_classes
        )
