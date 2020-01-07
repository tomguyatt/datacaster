import logging

from typing import Union, Optional, _GenericAlias

from . import exceptions

logger = logging.getLogger(__name__)


def parse_annotation(annotation):
    # Convert None to `<class 'NoneType'> (other types don't need this).
    return annotation or annotation.__class__


def is_custom_type(annotation):
    # All types from the typing module *seem* to be an instance of typing._GenericAlias.
    return isinstance(annotation, _GenericAlias)


def is_any(annotation):
    try:
        result = annotation._name.lower() == "any"
        logger.debug(f"annotation {annotation} {'is' if result else 'is not'} 'Any'")
        return result
    except Exception:
        # If it couldn't lookup the _name attribute, it isn't "Any".
        return False


def get_origin(annotation):
    return annotation.__origin__


def is_collection(annotation):
    # Return True if the custom annotation is a collection (typing.List, typing.Tuple)
    return get_origin(annotation) in {tuple, list}


def get_custom_type_classes(annotation) -> tuple:
    # Inspect a custom type (formed from the typing module) and either return a tuple of valid classes
    # for that annotation, or raise an Exception if the custom class is not currently supported.
    #
    # Examples:
    #
    #   Optional[str] -> (str, NoneType)
    #   Union[int, None] -> (int, NoneType)
    #   List[str] -> (str)
    #
    def _get_annotation_args():
        valid_types = annotation.__args__
        logger.debug(f"valid types for annotation {annotation} are {annotation.__args__}")
        return valid_types

    if is_collection(annotation):
        if isinstance(annotation.__args__[0], _GenericAlias):
            raise exceptions.UnsupportedType(
                f"Type {annotation} is not supported. Lists and tuples must only contain builtin types."
            )
        return _get_annotation_args()

    elif get_origin(annotation) in {Union, Optional}:
        if len(annotation.__args__) > 2:
            raise exceptions.UnsupportedType(f"Type {annotation} is not supported as it contains too many Union types.")
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
        return _get_annotation_args()
    else:
        raise exceptions.UnsupportedType(
            f"Unsupported custom type {annotation}. Only Optional[builtin], List[builtin], and "
            "Union[builtin, None] are supported ."
        )
