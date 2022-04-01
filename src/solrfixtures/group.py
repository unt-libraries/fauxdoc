"""Contains classes for grouping and operating on groups of objects."""
from collections import UserList
from typing import Any


class ObjectGroup(UserList):
    """Class for doing batch operations on groups of similar objects.

    This just provides a shorthand way to set the same attribute or
    call the same method on a list of objects, where some objects in
    the list may not have that attribute or method and that's fine --
    just skip them. Note this is a subclass of collections.UserList, so
    it behaves just like a list, aside from the __init__ and added
    methods.
    """

    def __init__(self, *objects: Any) -> None:
        """Inits an ObjectGroup with the given objects.

        Args:
            *objects: The objects you want to include in this group.
                Note this is a star argument, so provide as multiple
                positional arguments.
        """
        super().__init__(objects)

    def setattr(self, attr_name: str, attr_value: Any) -> None:
        """Sets an attribute for all objects in the group.

        The attribute is only set if that attribute already exists on
        the member object. Otherwise that object is skipped silently.
        
        Args:
            attr_name: The name of the attribute to set.
            attr_value: The value to set.
        """
        for obj in self:
            if obj is not None and hasattr(obj, attr_name):
                setattr(obj, attr_name, attr_value)

    def do_method(self, method_name: str, *args: Any, **kwargs: Any) -> None:
        """Runs a method of all objects in the group.

        If the method doesn't exist on any of the member objects, the
        AttributeError is ignored, and that object is skipped. Return
        values are ignored.

        Args:
            method_name: The name of the method to run.
            *args: Positional args to pass to the method.
            **kwargs: Keyword args to pass to the method.
        """
        for obj in self:
            if obj is not None:
                try:
                    getattr(obj, method_name)(*args, **kwargs)
                except AttributeError:
                    pass
