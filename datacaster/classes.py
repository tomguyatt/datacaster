import inspect

from dataclasses import dataclass
from typing import Optional


@dataclass(init=False, frozen=True)
class CastObject:

    def _get_default_values(self):
        """
        Return a {name: default_value} dictionary of all attributes that have default
        values in the class annotation. The self.__dataclass_fields__ attribute is empty
        because annotations come from other classes that inherit from this one.

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
            if attribute_value := getattr(self, attribute_name):
                if not inspect.ismethod(attribute_value):
                    default_values[attribute_name] = attribute_value
        return default_values

    def _get_defaulting_attributes(self, kwargs):
        """
        Return a {name: default_value} dictionary of all arguments that will fall back
        to their default values. We use this to type check default values against each
        argument type annotation early on.
        """
        return {name: value for name, value in self._get_default_values().items() if name not in kwargs}

    def __init__(self, *_, **kwargs):
        """
        - Unpack the type annotations and kwargs.
        - For each annotated argument:
            - If in kwargs:
                - Compare the type annotation to the value -> cast if necessary -> add to new attributes dict.
            - If not in kwargs and SET_DEFAULT_NONE is True -> add to new attributes dict as None.
            - If not in kwargs and SET_DEFAULT_NONE is False -> raise.
        """
        annotations = self.__annotations__
        unfulfilled_attributes = self._get_defaulting_attributes(kwargs)
        new_class_attributes = {}

        for argument_name, argument_type in annotations.items():
            if argument_name not in kwargs:
                if not self.SET_DEFAULT_NONE:
                    raise Exception(f"You did not supply a {argument_name}!")
                else:
                    new_class_attributes[argument_name] = None
            elif argument_name in kwargs:
                print(f"{argument_name} is in annotations *and* kwargs, so I can do stuff!")
                new_class_attributes[argument_name] = kwargs[argument_name]

        for name, value in new_class_attributes.items():
            setattr(self, name, value)

    def lol(self):
        return "I am here to cast the lol attribute"

    def _instance_methods(self) -> tuple:
        return inspect.getmembers(self, predicate=inspect.ismethod)

    def _get_field_caster(self, field_name):
        return next(iter([method_tuple for method_tuple in self._instance_methods() if method_tuple[0] == field_name]))


class Test(CastObject):
    IGNORE_EXTRA = True
    SET_DEFAULT_NONE = True

    lol: Optional[int] = 123
    optional: Optional[str] = "optional string"


t = Test()
