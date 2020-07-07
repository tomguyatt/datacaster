import inspect
import logging

from typeguard import check_type

from . import annotation_tools, value_cast, exceptions

logger = logging.getLogger(__name__)


class CastDataClass:
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    @property
    def _attribute_string(self):
        return ", ".join([f"{key}={repr(value)}" for key, value in vars(self).items()])

    def __repr__(self):
        return f"{self.__class__.__name__}({self._attribute_string})"

    def _test_cast_function_maps(self, field_functions, type_functions):
        invalid_type_cast = {
            annotation: function
            for annotation, function in type_functions.items()
            if len(inspect.signature(function).parameters) != 1
        }
        invalid_field_cast = {
            field: function
            for field, function in field_functions.items()
            if len(inspect.signature(function).parameters) != 1
        }

        if all_invalid := {**invalid_type_cast, **invalid_field_cast}:
            invalid_keys = ", ".join((str(v) for v in all_invalid.keys()))
            raise exceptions.UnsupportedCast(
                "All functions in __class_config__ must take 1 parameter. The functions supplied with the following "
                f"fields/annotations do not: {invalid_keys}"
            )

    def _get_field_class_method(self, field_name, instance_methods):
        try:
            return next(
                iter(
                    [
                        method_tuple
                        for method_tuple in instance_methods
                        if method_tuple[0] == f"__cast_{field_name}__"
                    ]
                )
            )
        except StopIteration:
            return None

    def _get_default_values(self):
        """
        Return a {name: default_value} dictionary of all attributes that have default
        values in the class annotation. We can get default values by looping over the
        attribute names in __annotations__ and seeing if they exist in self **before**
        we go through testing and casting attribute values.

        class Example(CastDataClass):
            mandatory_int: int
            optional_string: Optional[str] = "I am optional!"

        For the code above, this function will return {"optional_string": "I am optional!"}
        """
        default_values = {}
        for attribute_name in self.__annotations__:
            try:
                attribute_value = getattr(self, attribute_name)
                if not inspect.ismethod(attribute_value):
                    default_values[attribute_name] = attribute_value
            except AttributeError:
                pass
        return default_values

    def _get_defaulted_attributes(self, kwargs):
        """
        Return a {name: default_value} dictionary of all arguments that will fall back
        to their default values. We use this to type check default values against each
        argument type annotation early on.
        """
        return {
            name: value
            for name, value in self._get_default_values().items()
            if name not in kwargs
        }

    def _type_check_defaulted_values(self, defaulted_attributes):
        for attribute_name, attribute_value in defaulted_attributes.items():
            annotation = self.__annotations__[attribute_name]
            try:
                check_type(attribute_name, attribute_value, annotation)
            except TypeError:
                raise exceptions.InvalidDefaultValue(
                    f"Default value '{attribute_value}' for field '{attribute_name}' should be type {annotation} but is "
                    f"a {type(attribute_value)}. Please change the type annotation or default value."
                )

    def _get_unexpected_attributes(self, kwargs):
        """
        Return a {name: value_type} dictionary of all kwargs provided to the class
        __init__ that do not have relevant annotations.
        """
        return {
            name: value
            for name, value in kwargs.items()
            if name not in self.__annotations__
        }

    def __init__(self, *_, **kwargs):

        def _get_config_item(func, default_value):
            try:
                return func()
            except (KeyError, AttributeError):
                return default_value

        # The self attributes for these two are read only.
        SET_MISSING_NONE = getattr(self, "SET_MISSING_NONE", True)
        IGNORE_EXTRA = getattr(self, "IGNORE_EXTRA", True)
        INSTANCE_METHODS = inspect.getmembers(self, predicate=inspect.ismethod)

        FIELD_FUNCTIONS = _get_config_item(lambda: self.__class_config__["cast_functions"]["fields"], {})
        TYPE_FUNCTIONS = _get_config_item(lambda: self.__class_config__["cast_functions"]["types"], {})
        ALWAYS_CAST = _get_config_item(lambda: self.__class_config__["always_cast"], [])

        # If any fields are to be renamed, do it now before kwargs are inspected.
        if RENAMED_FIELDS := _get_config_item(lambda: self.__class_config__["rename_fields"], []):
            for original_name, new_name in RENAMED_FIELDS.items():
                # Create a new kwargs item with the new name & original value.
                kwargs[new_name] = kwargs[original_name]
                # Chuck the old kwargs item away.
                _ = kwargs.pop(original_name, None)

        # Type check the default values of any attributes that will be using
        # default values. We want to do this as soon as possible.
        defaulted_attributes = self._get_defaulted_attributes(kwargs)
        self._type_check_defaulted_values(defaulted_attributes)
        self._test_cast_function_maps(FIELD_FUNCTIONS, TYPE_FUNCTIONS)

        # Start the new attribute dictionary with all arguments using their default value.
        new_class_attributes = defaulted_attributes

        # Find any attributes in kwargs that aren't annotated. Their
        # existence can either be ignored or trigger an exception.
        if unexpected_attributes := self._get_unexpected_attributes(kwargs):
            if not IGNORE_EXTRA:
                raise exceptions.UnexpectedArgument(
                    f"Received values for {len(unexpected_attributes)} attribute(s) without "
                    f"annotations: {list(unexpected_attributes.keys())}."
                )

        # Start the main attribute testing & casting loop.
        for annotated_attribute, annotation in self.__annotations__.items():

            annotation = annotation_tools.parse_annotation(annotation)
            try:
                attribute_value = kwargs[annotated_attribute]
            except KeyError:
                attribute_value = None
                if annotated_attribute not in defaulted_attributes:
                    # The attribute has not been supplied and is not in kwargs. This can
                    # either be ignored or trigger an exception.
                    if not SET_MISSING_NONE:
                        raise exceptions.MissingArgument(
                            f"No value supplied for mandatory keyword argument {annotated_attribute}"
                        )
                    else:
                        new_class_attributes[annotated_attribute] = None
                        continue


            if annotated_attribute not in ALWAYS_CAST:
                try:
                    check_type(annotated_attribute, attribute_value, annotation)
                    new_class_attributes[annotated_attribute] = attribute_value
                    ###############################
                    # Type-checking has succeeded #
                    ###############################
                    continue

                except TypeError as e:
                    ############################
                    # Type-checking has failed #
                    ############################
                    logger.debug(f"type-check failed: {e}")

            # If a cast function exists for this field in both the fields dictionary and as a class instance
            # method, raise an exception to avoid any potential confusion as to which of them was executed.
            if all(
                [
                    self._get_field_class_method(annotated_attribute, INSTANCE_METHODS),
                    FIELD_FUNCTIONS.get(annotated_attribute),
                ]
            ):
                raise exceptions.MultipleCastDefinitions(
                    f"Multiple cast definitions for field '{annotated_attribute}'. Found corresponding function in "
                    f"class config, and class instance method __cast_{annotated_attribute}__."
                )

            # Look for a field instance method first.
            if instance_method_tuple := self._get_field_class_method(
                annotated_attribute, INSTANCE_METHODS
            ):
                instance_method_name, instance_method = instance_method_tuple
                new_class_attributes[annotated_attribute] = instance_method(
                    attribute_value
                )
                continue

            # Otherwise look for a field cast function in __class_config__.
            elif field_map_function := FIELD_FUNCTIONS.get(annotated_attribute):
                new_class_attributes[annotated_attribute] = field_map_function(
                    attribute_value
                )
                continue

            # Or a type cast function in __class_config__.
            elif type_map_function := TYPE_FUNCTIONS.get(annotation):
                new_class_attributes[annotated_attribute] = type_map_function(attribute_value)
                continue

            # This can be called from multiple code paths, so define it once inside the scope that contains the
            # annotation, name, and value of each argument.
            def _cast_simple(valid_type):
                try:
                    logger.debug(
                        f"casting argument {annotated_attribute} to simple type {valid_type}"
                    )
                    return value_cast.cast_simple_type(
                        valid_type, attribute_value, annotated_attribute
                    )
                except KeyError:
                    raise exceptions.UnsupportedCast(
                        f"Field '{annotated_attribute}' has supplied value '{attribute_value}' with invalid "
                        f"type {attribute_value.__class__}. A {annotation} type value is required "
                        "but casting the supplied value is not supported yet."
                    )

            if annotation_tools.is_custom_type(annotation):
                # We can support making lists or tuples of simple builtin types. Work out whether this value should
                # be a list or tuple. If it should be, then check if the supplied value is already a list or tuple.
                if annotation_tools.is_collection(annotation):

                    collection_type = annotation_tools.get_origin(annotation)
                    valid_types = annotation_tools.get_custom_type_classes(annotation)
                    cast_collection_values = []

                    def _cast_collection_item(value):
                        # There will only be one because something like typing.List[str, int] isn't valid.
                        valid_type = valid_types[0]
                        logger.debug(
                            f"casting argument {annotated_attribute} collection value {value} to {valid_type}"
                        )
                        return value_cast.cast_simple_type(
                            valid_type, value, annotated_attribute
                        )

                    if not isinstance(attribute_value, (list, tuple)):
                        # If the value isn't already a list or tuple, cast it if necessary then put it inside a
                        # new instance of the collection type specified in the annotation.
                        cast_collection_values.append(
                            _cast_collection_item(attribute_value)
                        )
                    else:
                        for value in attribute_value:
                            # Iterate over the supplied values and cast them if necessary.
                            cast_collection_values.append(_cast_collection_item(value))
                            continue

                    new_class_attributes[annotated_attribute] = collection_type(
                        cast_collection_values
                    )

                else:
                    valid_types = annotation_tools.get_custom_type_classes(annotation)
                    # The value is not one of the types described by the custom type annotation. As we only
                    # support basic Union[builtin, None] types, and we almost certainly don't want to cast
                    # this value to None, we should try to cast it to the other type in the Union. To get
                    # the type to cast to we need to remove the NoneType entry from the valid_types tuple.
                    #
                    # For the annotation typing.Union[str, None] this code will attempt to cast the value
                    # to a string.
                    valid_type = next(
                        filter(lambda x: x != type(None), valid_types)
                    )  # noqa (ignore E721: using isinstance is not correct here)
                    new_class_attributes[annotated_attribute] = _cast_simple(valid_type)

            else:
                # The annotation is not something from the typing module.
                new_class_attributes[annotated_attribute] = _cast_simple(annotation)

        for name, value in new_class_attributes.items():
            setattr(self, name, value)
