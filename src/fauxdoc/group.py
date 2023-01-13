"""Contains classes for grouping and operating on groups of objects."""
from abc import ABC, abstractmethod
from typing import Any, Generic, Iterable, Mapping

from fauxdoc.typing import OrderedDict, T, UserList


class GroupMixin(Generic[T], ABC):
    """Abstract base class for defining Group objects.

    This is implemented via ObjectGroup and ObjectMap, but could be
    applied to other types of groups. Override the `objects_iterable`
    property to return an iterable that iterates through the group.
    """

    @property
    @abstractmethod
    def objects_iterable(self) -> Iterable[T]:
        """Returns an itereable for the objects in this group.

        Override this in your subclass to define how to iterate
        through the object group.
        """

    def setattr(self, attr_name: str, attr_value: Any) -> None:
        """Sets an attribute for all objects in the group.

        The attribute is only set if that attribute already exists on
        the member object. Otherwise that object is skipped silently.

        Args:
            attr_name: The name of the attribute to set.
            attr_value: The value to set.
        """
        for obj in self.objects_iterable:
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
        for obj in self.objects_iterable:
            if obj is not None:
                try:
                    getattr(obj, method_name)(*args, **kwargs)
                except AttributeError:
                    pass


class ObjectGroup(GroupMixin[T], UserList[T]):
    """Class for operating on groups of similar objects (as a list).

    Use this instead of ObjectMap when you need your group to behave
    like a list.

    This provides a shorthand way to set the same attribute or call the
    same method on a group of objects, where some objects in the group
    may not have that attribute or method and that's fine -- we just
    skip them.
    """

    def __init__(self, *objects: T) -> None:
        """Inits an ObjectGroup with the given objects.

        Args:
            *objects: The objects you want to include in this group.
                Note this is a star argument, so provide as multiple
                positional arguments.
        """
        super().__init__(objects)

    @property
    def objects_iterable(self) -> Iterable[T]:
        """Iterates through the objects in this group."""
        return self


class ObjectMap(GroupMixin[T], OrderedDict[str, T]):
    """Class for operating on groups of similar objects (as a dict).

    Use this instead of ObjectGroup when you need your group to behave
    like a dict.

    This provides a shorthand way to set the same attribute or call the
    same method on a group of objects, where some objects in the group
    may not have that attribute or method and that's fine -- we just
    skip them.
    """

    def __init__(self, objects: Mapping[str, T]) -> None:
        """Inits an ObjectMap with the given objects.

        Args:
            objects: Your initial dict that maps keys to objects in
                this group.
        """
        super().__init__(objects)

    @property
    def objects_iterable(self) -> Iterable[T]:
        """Iterates through the objects in this group."""
        return list(self.values())
