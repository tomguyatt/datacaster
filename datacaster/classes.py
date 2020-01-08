import inspect
import logging

from typing import Optional

from . import annotation_tools, type_check, value_cast, exceptions

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

    def _instance_methods(self) -> tuple:
        return inspect.getmembers(self, predicate=inspect.ismethod)

    def _get_attribute_cast_function(self, field_name):
        try:
            return next(
                iter(
                    [
                        method_tuple
                        for method_tuple in self._instance_methods()
                        if method_tuple[0] == f"__cast_{field_name}__"
                    ]
                )
            )
        except StopIteration:
            return None

    def _get_default_values(self):
        """
        Return a {name: default_value} dictionary of all attributes that have default
        values in the class annotation. The self.__dataclass_fields__ attribute is empty
        because annotations come from the child classes that inherit from this one.

        Another way we can get default values is by looping over the attribute names in
        __annotations__ and seeing if they exist in self **before** we go through testing
        and casting attribute values.

        class Example(CastObject):
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
            logger.debug(
                f"type-checking default value {attribute_value} for attribute {attribute_name}"
            )
            type_check.check_argument_type(
                attribute_name,
                attribute_value,
                annotation_tools.parse_annotation(self.__annotations__[attribute_name]),
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
        # The self attributes for these two are read only.
        SET_MISSING_NONE = getattr(self, "SET_MISSING_NONE", True)
        IGNORE_EXTRA = getattr(self, "IGNORE_EXTRA", True)

        # Type check the default values of any attributes that will be using
        # default values. We want to do this as soon as possible.
        defaulted_attributes = self._get_defaulted_attributes(kwargs)
        self._type_check_defaulted_values(defaulted_attributes)

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

            # The first thing to do is see if the class instance has a registered magic
            # method specifically for this attribute. If there is one, always use it no
            # matter what type the value already is, then continue to the next attribute.
            if method_tuple := self._get_attribute_cast_function(annotated_attribute):
                method_name, method_object = method_tuple
                logger.debug(
                    f"found instance method {method_name} to be used on {annotated_attribute}"
                )
                new_class_attributes[annotated_attribute] = method_object(
                    attribute_value
                )
                continue

            # If the argument annotation is 'typing.Any' then chuck it straight into
            # new_class_attributes and continue to the next one.
            if annotation_tools.is_any(annotation):
                logger.debug(
                    f"argument {annotated_attribute} has annotation {annotation} so "
                    f"all testing and casting will be skipped."
                )
                new_class_attributes[annotated_attribute] = attribute_value
                continue

            # This can be called from multiple code paths, so define it once inside
            # the scope that contains the annotation, name, and value of each argument.
            def _cast_simple(valid_type):
                try:
                    logger.debug(
                        f"casting argument {annotated_attribute} to {valid_type}"
                    )
                    return value_cast.cast_simple_type(
                        valid_type, attribute_value, annotated_attribute
                    )
                except KeyError:
                    raise exceptions.UnsupportedType(
                        f"Field '{annotated_attribute}' has supplied value '{attribute_value}' with invalid "
                        f"type {attribute_value.__class__}. A {annotation} type value is required "
                        "but casting the supplied value is not supported yet."
                    )

            if annotation_tools.is_custom_type(annotation):
                logger.debug(
                    f"argument {annotated_attribute} is custom type {annotation}"
                )
                # We can support making lists or tuples of simple builtin types. Work out whether this value should
                # be a list or tuple. If it should be, then check if the supplied value is already a list or tuple.
                if annotation_tools.is_collection(annotation):

                    collection_type = annotation_tools.get_origin(annotation)
                    valid_types = annotation_tools.get_custom_type_classes(annotation)
                    cast_collection_values = []

                    def _cast_collection_item(value):
                        if not value_cast.test_value_class(value, valid_types):
                            # There will only be one because something like typing.List[str, int] isn't valid.
                            valid_type = valid_types[0]
                            logger.debug(
                                f"casting argument {annotated_attribute} collection value {value} to {valid_type}"
                            )
                            return value_cast.cast_simple_type(
                                valid_type, value, annotated_attribute
                            )
                        return value

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
                    if not value_cast.test_value_class(attribute_value, valid_types):
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
                        new_class_attributes[annotated_attribute] = _cast_simple(
                            valid_type
                        )
                    else:
                        new_class_attributes[annotated_attribute] = attribute_value

            else:
                if not value_cast.test_value_class(attribute_value, [annotation]):
                    new_class_attributes[annotated_attribute] = _cast_simple(annotation)
                else:
                    new_class_attributes[annotated_attribute] = attribute_value

        for name, value in new_class_attributes.items():
            setattr(self, name, value)
