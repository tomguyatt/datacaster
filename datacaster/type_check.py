from . import value_cast, annotation_tools, exceptions


def check_argument_type(argument_name, argument_value, argument_annotation):
    argument_value_type = repr(argument_value.__class__)

    def _raise_invalid_default_value():
        raise exceptions.InvalidDefaultValue(
            f"Default value '{argument_value}' for field '{argument_name}' should be type {argument_annotation} but is "
            f"a {argument_value_type}. Please change the type annotation or default value."
        )

    if annotation_tools.is_custom_type(argument_annotation):
        try:
            if not value_cast.test_value_class(
                argument_value,
                annotation_tools.get_custom_type_classes(argument_annotation),
            ):
                _raise_invalid_default_value()
        except exceptions.UnsupportedType as e:
            raise exceptions.UnsupportedType(
                f"Failed to type check argument '{argument_name}'. {str(e)}"
            )
    elif argument_value_type != repr(argument_annotation):
        _raise_invalid_default_value()
