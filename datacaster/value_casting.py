import functools
import logging

from . import exceptions

logger = logging.getLogger(__name__)


def _raise_on_fail(type_name):
    def _wrapper(func):
        @functools.wraps(func)
        def _inner(value, name):
            try:
                return func(value, name)
            except Exception as e:
                raise exceptions.CastFailed(
                    f"Cannot cast {type(value)} attribute named {name} with value {repr(value)} to {type_name}: {str(e)}"
                )

        return _inner

    return _wrapper


@_raise_on_fail("string")
def cast_to_string(value, _):
    return str(value)


@_raise_on_fail("integer")
def cast_to_int(value, _):
    return int(value)


@_raise_on_fail("float")
def cast_to_float(value, _):
    return float(value)


ANNOTATION_CAST_FUNCTIONS = {
    repr(str): cast_to_string,
    repr(int): cast_to_int,
    repr(float): cast_to_float,
}


def test_value_class(argument_value, valid_types):
    result = repr(argument_value.__class__) in [repr(t) for t in valid_types]
    if not result:
        logger.debug(f"type of value {argument_value} is not one of {valid_types}")
    else:
        logger.debug(f"type of value {argument_value} is one of {valid_types}")
    return result


def cast_simple_type(expected_type, value, name):
    return ANNOTATION_CAST_FUNCTIONS[repr(expected_type)](value, name)
