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
            if not values.test_value_class(argument_value, annotations.get_custom_type_classes(argument_annotation)):
                _raise_invalid_default_value()
        except exceptions.UnsupportedType as e:
            raise exceptions.UnsupportedType(f"Failed to type check argument '{argument_name}'. {str(e)}")
    elif argument_value_type != repr(argument_annotation):
        _raise_invalid_default_value()


def _type_check_defaulted_values(kwarg_default_values, argument_annotations, kwargs):
    # Work out which arguments will be fulfilled by their default values so we can check & cast those too.
    defaulted_kwargs = {key: value for key, value in kwarg_default_values.items() if key not in kwargs}

    for argument_name, argument_value in defaulted_kwargs.items():
        _check_argument_type(
            argument_name, argument_value, annotations.parse_annotation(argument_annotations[argument_name])
        )


def cast_attributes(ignore_extra: Optional[bool] = True, set_missing_none: Optional[bool] = True):
    def _dataclass_wrapper(data_class):
        argument_annotations = data_class.__annotations__
        kwarg_default_values = {
            field_name: field_data.default
            for field_name, field_data in data_class.__dataclass_fields__.items()
            if not isinstance(field_data.default, _MISSING_TYPE)
        }

        @functools.wraps(data_class)
        def _cast_attributes(*args, **kwargs):
            # Make sure that any arguments falling back to their default values are the correct type. If this raises
            # it shouldn't get caught and ignored because it means either a type annotation or a default value is wrong.
            _type_check_defaulted_values(kwarg_default_values, argument_annotations, kwargs)

            new_kwargs = {}

            missing_arguments = sorted(
                [
                    argument_name
                    for argument_name in list(argument_annotations.keys())
                    if argument_name not in list(kwargs.keys()) + list(kwarg_default_values.keys())
                ]
            )
            if missing_arguments:
                if not set_missing_none:
                    raise TypeError(
                        f"The following required dataclass arguments have not been supplied - {missing_arguments}. "
                    )
                for argument_name in missing_arguments:
                    new_kwargs[argument_name] = None

            for argument_name, argument_value in kwargs.items():
                # Iterate over the supplied keyword arguments, and compare their types
                # with the expected types collected from the dataclass type annotations.

                # If an argument is supplied that is not defined in annotations, either raise an Exception or ignore the
                # argument. This behaviour is decided by the optional decorator keyword argument IgnoreExtraArgs.
                try:
                    argument_annotation = annotations.parse_annotation(argument_annotations[argument_name])
                except KeyError as e:
                    if ignore_extra:
                        continue
                    raise e

                # If the argument annotation is 'typing.Any' then chuck it straight into the new_kwargs and continue.
                if annotations.is_any(argument_annotation):
                    logger.debug(
                        f"argument {argument_name} has annotation {argument_annotation} so all "
                        "testing and casting will be skipped."
                    )
                    new_kwargs[argument_name] = argument_value
                    continue

                # This can be called from multiple code paths, so define it once inside
                # the scope that contains the annotation, name, and value of each argument.
                def _cast_simple(valid_type):
                    try:
                        logger.debug(f"casting argument {argument_name} to {valid_type}")
                        return values.cast_simple_type(valid_type, argument_value, argument_name)
                    except KeyError:
                        raise exceptions.UnsupportedType(
                            f"Field '{argument_name}' has supplied value '{argument_value}' with invalid "
                            f"type {argument_value.__class__}. A {argument_annotation} type value is required "
                            "but casting the supplied value is not supported yet."
                        )

                if annotations.is_custom_type(argument_annotation):
                    logger.debug(f"argument {argument_name} is custom type {argument_annotation}")
                    # We can support making lists or tuples of simple builtin types. Work out whether this value should
                    # be a list or tuple. If it should be, then check if the supplied value is already a list or tuple.
                    if annotations.is_collection(argument_annotation):

                        collection_type = annotations.get_origin(argument_annotation)
                        valid_types = annotations.get_custom_type_classes(argument_annotation)
                        cast_collection_values = []

                        def _cast_collection_item(value):
                            if not values.test_value_class(value, valid_types):
                                valid_type = valid_types[0]  # There will only be one.
                                logger.debug(
                                    f"casting argument {argument_name} collection value {value} to {valid_type}"
                                )
                                return values.cast_simple_type(valid_type, value, argument_name)
                            return value

                        if not isinstance(argument_value, (list, tuple)):
                            # If the value isn't already a list or tuple, cast it if necessary then put it inside a
                            # new instance of the collection type specified in the annotation.
                            cast_collection_values.append(_cast_collection_item(argument_value))
                        else:
                            for value in argument_value:
                                # Iterate over the supplied values and cast them if necessary.
                                cast_collection_values.append(_cast_collection_item(value))
                                continue

                        new_kwargs[argument_name] = collection_type(cast_collection_values)

                    else:
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
                            new_kwargs[argument_name] = argument_value

                else:
                    if not values.test_value_class(argument_value, [argument_annotation]):
                        new_kwargs[argument_name] = _cast_simple(argument_annotation)
                    else:
                        new_kwargs[argument_name] = argument_value

            return data_class(*args, **new_kwargs)

        return _cast_attributes

    return _dataclass_wrapper
