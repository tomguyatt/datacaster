import pytest

from datacaster import values, exceptions


class UnStringableInt(int):
    def __str__(self):
        raise Exception("Can't string me yo!")


@pytest.mark.parametrize(
    "input, expected_output, expected_exception, exception_message",
    [
        ["hello", "hello", None, None],
        [123, "123", None, None],
        [1.0, "1,0", None, None],
        [None, "None", None, None],
        [{}, "{}", None, None],
        [[], "[]", None, None],
        [UnStringableInt(123), None, exceptions.CastFailed, "Can't string me yo!"],
    ],
    ids=["string", "integer", "float"],
)
def test_cast_to_string(input, expected_output, expected_exception, exception_message):
    if expected_exception:
        with pytest.raises(expected_exception, match=exception_message):
            values.cast_to_string(input)
    else:
        assert values.cast_to_string(input) == expected_output


@pytest.mark.parametrize(
    "input, expected_output, expected_exception, exception_message",
    [
        [1.2, 1, None, None],
        [False, 0, None, None],
        ["123", 123, None, None],
        [
            None,
            None,
            exceptions.CastFailed,
            "Cannot cast value None of type <class 'NoneType'> to integer. int() argument must "
            "be a string, a bytes-like object or a number, not 'NoneType'",
        ][
            "hello",
            None,
            exceptions.CastFailed,
            "Cannot cast value hello of type <class 'str'> to integer. invalid literal for "
            "int() with base 10: 'hello'",
        ],
    ],
    ids=["float", "bool", "valid_string", None, "invalid_string"],
)
def test_cast_to_int(input, expected_output, expected_exception, exception_message):
    if expected_exception:
        with pytest.raises(expected_exception, match=exception_message):
            values.cast_to_string(input)
    else:
        assert values.cast_to_string(input) == expected_output
