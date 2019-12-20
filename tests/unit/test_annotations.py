import re
import pytest

import typing

from datacaster import annotations, exceptions


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
    assert repr(annotations.parse_annotation(value)) == expected_output


@pytest.mark.parametrize(
    "value, expected_output",
    [[str, False], [None, False], [typing.List, True], [typing.Optional[str], True]],
    ids=["str", "none", "typing_list", "optional_str"],
)
def test_is_custom_type(value, expected_output):
    assert annotations.is_custom_type(value) == expected_output


@pytest.mark.parametrize(
    "value, expected_type_classes, expected_exception",
    [
        [typing.Optional[str], ("<class 'str'>", "<class 'NoneType'>"), None],
        [typing.Union[str, None], ("<class 'str'>", "<class 'NoneType'>"), None],
        [typing.Union[str, int, None], None, exceptions.UnsupportedType],
        [typing.Union[str, int], None, exceptions.UnsupportedType],
        [typing.Union[typing.List, None], None, exceptions.UnsupportedType],
        [typing.List[str], None, exceptions.UnsupportedType],
    ],
    ids=[
        "optional_str",
        "union_str_none",
        "too_many_union_types",
        "union_must_be_none",
        "union_must_be_builtin",
        "not_union_or_optional",
    ],
)
def test_get_custom_type_classes(value, expected_type_classes, expected_exception):
    # This function is only called on custom types, not builtins.
    if expected_exception:
        with pytest.raises(expected_exception):
            annotations.get_custom_type_classes(value)
    else:
        assert (
            tuple(
                [
                    repr(type_class)
                    for type_class in annotations.get_custom_type_classes(value)
                ]
            )
            == expected_type_classes
        )
