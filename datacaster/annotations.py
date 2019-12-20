from typing import Union, Optional, _GenericAlias

from . import exceptions


def parse_annotation(annotation):
    # Convert None to `<class 'NoneType'> (other types don't need this).
    return annotation or annotation.__class__


def is_custom_type(type_annotation):
    # All types from the typing module *seem* to be an instance of typing._GenericAlias.
    return isinstance(type_annotation, _GenericAlias)


def get_custom_type_classes(annotation) -> tuple:
    # Inspect a custom type (formed from the typing module) and either return a tuple of valid classes
    # for that annotation, or raise an Exception if the custom class is not currently supported.
    #
    # Examples:
    #
    #   Optional[str] -> (str, NoneType)
    #   Union[int, None] -> (int, NoneType)
    #
    if annotation.__origin__ in {Union, Optional}:
        if len(annotation.__args__) > 2:
            raise exceptions.UnsupportedType(
                f"Type {annotation} is not supported as it contains too many Union types."
            )
        elif not any(
            [t == type(None) for t in annotation.__args__]
        ):  # noqa (ignore E721: using isinstance is not correct here)
            raise exceptions.UnsupportedType(
                f"Type {annotation} is not supported. One of the Union types must be None."
            )
        elif any([isinstance(t, _GenericAlias) for t in annotation.__args__]):
            raise exceptions.UnsupportedType(
                f"Type {annotation} is not supported. Only builtin types are "
                "currently supported in Union and Optional custom types."
            )
        return annotation.__args__
    else:
        raise exceptions.UnsupportedType(
            f"Unsupported custom type {annotation}. Only Optional[builtin] and Union[builtin, None] is supported ."
        )
