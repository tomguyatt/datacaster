import re
import pytest

from datacaster import value_cast, exceptions


class UnStringableInt(int):
    def __str__(self):
        raise Exception("Can't string me yo!")


@pytest.mark.parametrize(
    "input, expected_output, expected_exception",
    [
        ["hello", "hello", None],
        [123, "123", None],
        [1.0, "1.0", None],
        [None, "None", None],
        [{}, "{}", None],
        [[], "[]", None],
        [UnStringableInt(123), None, exceptions.CastFailed],
    ],
    ids=["string", "integer", "float", "none", "dict", "list", "un_stringable_int"],
)
def test_cast_to_string(input, expected_output, expected_exception):
    if expected_exception:
        with pytest.raises(expected_exception):
            value_cast.cast_to_string(input, None)
    else:
        assert value_cast.cast_to_string(input, None) == expected_output


@pytest.mark.parametrize(
    "input, expected_output, expected_exception",
    [
        [1.2, 1, None],
        [False, 0, None],
        ["123", 123, None],
        [None, None, exceptions.CastFailed],
        ["hello", None, exceptions.CastFailed],
    ],
    ids=["float", "bool", "valid_string", "none", "invalid_string"],
)
def test_cast_to_int(input, expected_output, expected_exception):
    if expected_exception:
        with pytest.raises(expected_exception):
            value_cast.cast_to_int(input, None)
    else:
        assert value_cast.cast_to_int(input, None) == expected_output
