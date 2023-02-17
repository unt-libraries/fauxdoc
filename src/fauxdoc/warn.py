"""Contains functions etc. related to deprecating parts of the package."""
from typing import Any, Mapping, Optional, Tuple
import warnings


def get_deprecated_attr(attr_name: str,
                        from_obj_name: str,
                        from_type_name: str,
                        deprecated: Mapping[str, Tuple[Optional[str], object]]
                        ) -> Any:
    """Gets a deprecated attribute and issues a deprecation warning.

    Use this in an object or module's __getattr__ method to issue a
    deprecation warning but still return the deprecated attribute.

    Example: You want to deprecate example.OldClass in favor of
    example.NewClass1 or example.NewClass2 and warn when someone
    imports or uses example.OldClass.

    First, rename example.OldClass -- e.g., example._OldClass. Then add
    the following to the bottom of the 'example' module.

    _OldClass.__name__ = 'OldClass'
    _OldClass.__qualname__ = 'OldClass'
    DEPR = { 'OldClass': ('NewClass1 or NewClass2', _OldClass) }
    def __getattr__(name):
        return get_deprecated_attr(name, __name__, 'module', DEPR)

    Importing OldClass directly and accessing it via 'example.OldClass'
    will continue to work (returning example._OldClass) -- but they
    will both issue a deprecation warning telling the user to switch to
    NewClass. (If there is no replacement for the deprecated attribute,
    then in DEPR you could use { 'OldClass': (None, _OldClass) }
    instead, and the warning will only mention the deprecation.)

    Args:
        attr_name: The name of the attribute the user is trying to get.
        from_obj_name: The name of the object that should have the
            attribute.
        from_type_name: The name of the type of the object that should
            have the attribute.
        deprecated: A dictionary that maps deprecated attribute names
            to tuples. Each tuple should contain two values: first, a
            string containing the name or names of the replacement
            attributes (or None if there is no replacement); second,
            the deprecated attribute value to return.
    """
    if attr_name in deprecated:
        new_name, attr_value = deprecated[attr_name]
        replace_str = f' Please use {new_name} instead.' if new_name else ''
        warnings.warn(
            f'{from_obj_name}.{attr_name} is deprecated and will be removed '
            f'in the next major version release.{replace_str}',
            DeprecationWarning
        )
        return attr_value
    raise AttributeError(
        f'{from_type_name} {from_obj_name} has no attribute {attr_name!r}'
    )
