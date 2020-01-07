from . import values, annotations, exceptions


def _check_argument_type(argument_name, argument_value, argument_annotation):
    argument_value_type = repr(argument_value.__class__)

    def _raise_invalid_default_value():
        raise exceptions.InvalidDefaultValue(
            f"Default value '{argument_value}' for field '{argument_name}' should be type {argument_annotation} but is "
            f"a {argument_value_type}. Please change the dataclass field type annotation or default value."
        )

    if annotations.is_custom_type(argument_annotation):
        try:
            if not values.test_value_class(argument_value, annotations.get_custom_type_classes(argument_annotation)):
                _raise_invalid_default_value()
        except exceptions.UnsupportedType as e:
            raise exceptions.UnsupportedType(f"Failed to type check argument '{argument_name}'. {str(e)}")
    elif argument_value_type != repr(argument_annotation):
        _raise_invalid_default_value()
