import functools
import logging

from dataclasses import _MISSING_TYPE

from typing import Optional

from . import exceptions, values, annotations

logger = logging.getLogger(__name__)


def _check_argument_type(argument_name, argument_value, argument_annotation):
    argument_value_type = repr(argument_value.__class__)

    def _raise_invalid_default_value():
        raise exceptions.InvalidDefaultValue(
            f"Default value '{argument_value}' for field '{argument_name}' should be type {argument_annotation} but is "
            f"a {argument_value_type}. Please change the dataclass field type annotation or default value."
        )

    if annotations.is_custom_type(argument_annotation):
        try:
            if not values.test_value_class(
                    argument_value, annotations.get_custom_type_classes(argument_annotation)
            ):
                _raise_invalid_default_value()
        except exceptions.UnsupportedType as e:
            raise exceptions.UnsupportedType(
                f"Failed to type check argument '{argument_name}'. {str(e)}"
            )
    elif argument_value_type != repr(argument_annotation):
        _raise_invalid_default_value()


def _type_check_defaulted_values(kwarg_default_values, argument_annotations, kwargs):
    # Work out which arguments will be fulfilled by their default values so we can check & cast those too.
    defaulted_kwargs = {
        key: value for key, value in kwarg_default_values.items() if key not in kwargs
    }

    for argument_name, argument_value in defaulted_kwargs.items():
        _check_argument_type(
            argument_name,
            argument_value,
            annotations.parse_annotation(argument_annotations[argument_name]),
        )


def cast_attributes(ignore_extra_args: Optional[bool] = False):
    def _wrapper(data_class):
        argument_annotations = data_class.__annotations__
        kwarg_default_values = {
            field_name: field_data.default
            for field_name, field_data in data_class.__dataclass_fields__.items()
            if not isinstance(field_data.default, _MISSING_TYPE)
        }

        @functools.wraps(data_class)
        def _inner(*args, **kwargs):
            # Make sure that any arguments falling back to their default values are the correct type. If this raises
            # it shouldn't get caught and ignored because it means either a type annotation or a default value is wrong.
            _type_check_defaulted_values(kwarg_default_values, argument_annotations, kwargs)

            new_kwargs = {}

            for argument_name, argument_value in kwargs.items():
                # Iterate over the supplied keyword arguments, and compare their types
                # with the expected types collected from the dataclass type annotations.

                # If an argument is supplied that is not defined in annotations, either raise an Exception or ignore the
                # argument. This behaviour is decided by the optional decorator keyword argument IgnoreExtraArgs.
                try:
                    argument_annotation = annotations.parse_annotation(
                        argument_annotations[argument_name]
                    )
                except KeyError as e:
                    if ignore_extra_args:
                        logger.debug(f"ignoring unexpected extra argument {argument_name} supplied to dataclass")
                        continue
                    raise e

                # This can be called from multiple code paths, so define it once inside
                # the scope that contains the annotation, name, and value of each argument.
                def _cast_simple(valid_type):
                    try:
                        logger.info(f"casting argument {argument_name} to {valid_type}")
                        return values.cast_simple_type(valid_type, argument_value)
                    except KeyError:
                        raise exceptions.UnsupportedType(
                            f"Field '{argument_name}' has supplied value '{argument_value}' with invalid "
                            f"type {argument_value.__class__}. A {argument_annotation} type value is required "
                            "but casting the supplied value is not supported yet."
                        )

                if annotations.is_custom_type(argument_annotation):
                    logger.debug(f"argument {argument_name} uses custom type {argument_annotation}")
                    valid_types = annotations.get_custom_type_classes(argument_annotation)
                    if not values.test_value_class(argument_value, valid_types):
                        # The value is not one of the types described by the custom type annotation. As we only
                        # support basic Union[builtin, None] types, and we almost certainly don't want to cast
                        # this value to None, we should try to cast it to the other type in the Union. To get
                        # the type to cast to we need to remove the NoneType entry from the valid_types tuple.
                        valid_type = next(
                            filter(lambda x: x != type(None), valid_types)
                        )  # noqa (ignore E721: using isinstance is not correct here)
                        new_kwargs[argument_name] = _cast_simple(valid_type)
                    else:
                        logger.info(f"argument {argument_name} is already a valid type")
                        new_kwargs[argument_name] = argument_value
                else:
                    logger.debug(f"argument {argument_name} uses simple type {argument_annotation}")
                    if not values.test_value_class(argument_value, [argument_annotation]):
                        new_kwargs[argument_name] = _cast_simple(argument_annotation)
                    else:
                        logger.info(f"argument {argument_name} is already a valid type")
                        new_kwargs[argument_name] = argument_value
            return data_class(*args, **new_kwargs)

        return _inner

    return _wrapper
