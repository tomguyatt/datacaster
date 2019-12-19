import functools


def cast_to_string(value):
    @functools.singledispatch
    def _cast(value):
        raise TypeError(f"Cannot cast value {value} to string. Supplied data type {type(value)} is unsupported.")

    @_cast.register(int)
    @_cast.register(float)
    def _(value):
        return str(value)

    return _cast(value)


def cast_to_int(value):
    @functools.singledispatch
    def _cast(value):
        raise TypeError(f"Cannot cast value {value} to int. Supplied data type {type(value)} is unsupported.")

    @_cast.register(str)
    @_cast.register(float)
    def _(value):
        return int(value)

    return _cast(value)


def cast_to_float(value):
    @functools.singledispatch
    def _cast(value):
        raise TypeError(f"Cannot cast value {value} to float. Supplied data type {type(value)} is unsupported.")

    @_cast.register(str)
    @_cast.register(int)
    def _(value):
        return float(value)

    return _cast(value)


ANNOTATION_CAST_FUNCTIONS = {
    repr("string".__class__): cast_to_string,
    repr((123).__class__): cast_to_int,
    repr(123.0.__class__): cast_to_float,
}


def test_value_class(argument_value, valid_types):
    return repr(argument_value.__class__) in [repr(t) for t in valid_types]


def cast_simple_type(expected_type, value):
    return ANNOTATION_CAST_FUNCTIONS[repr(expected_type)](value)
