"""
This module provides the interface for Closure targets and a few common implementations for wrapping various
types as targets such as mappings and objects, and chaining them together.
"""

import enum
import types
from typing import Any, MutableMapping

from typing_extensions import Protocol


class _NotSet(enum.Enum):
    Value = 1


undefined = _NotSet.Value


class Target(Protocol):
    """
    A context implements the behaviour for dynamic name resolution in programs transpiled with
    BuildDSL (when dynamic name resolution is enabled). It behaves essentially as a mapping
    that is used to get/set/delete variables.
    """

    def get(self) -> Any:
        """
        Return the underlying object.
        """

        raise NotImplementedError(self)

    def __getitem__(self, key: str) -> Any:
        raise NotImplementedError(self)

    def __setitem__(self, key: str, value: Any) -> None:
        raise NotImplementedError(self)

    def __delitem__(self, key: str) -> None:
        raise NotImplementedError(self)


class ObjectTarget(Target):
    """
    Proxies an object's members for get/set/delete operations of the dynamic name resolution.

    Raises a #RuntimeError if there is an attempted to set or delete an attribute that appears
    to be a method of the object.
    """

    def __init__(self, target: Any) -> None:
        self._target = target

    def _error(self, key: str) -> NameError:
        raise NameError(f"object of type {type(self._target).__name__} does not have an attribute {key!r}")

    def get(self) -> Any:
        return self._target

    def __getitem__(self, key: str) -> Any:
        value = getattr(self._target, key, undefined)
        if value is not undefined:
            return value
        raise self._error(key)

    def __setitem__(self, key: str, value: Any) -> None:
        current = getattr(self._target, key, undefined)
        if current is undefined:
            raise self._error(key)
        if isinstance(current, types.MethodType) and current.__self__ is current:
            raise RuntimeError(f"cannot overwrite method {type(self._target).__name__}.{key}()")
        setattr(self._target, key, value)

    def __delitem__(self, key: str) -> None:
        current = getattr(self._target, key, undefined)
        if current is undefined:
            raise self._error(key)
        if isinstance(current, types.MethodType) and current.__self__ is current:
            raise RuntimeError(f"cannot delete method {type(self._target).__name__}.{key}()")
        delattr(self._target, key)


class MutableMappingTarget(Target):
    """
    Delegates dynamic name resolution to a mapping.
    """

    def __init__(self, target: MutableMapping[str, Any], description: "str | None" = None) -> None:
        self._target = target
        self._description = description

    def _get_description(self) -> str:
        return repr(self._target) if self._description is None else self._description

    def _error(self, key: str) -> NameError:
        raise NameError(f"{self._get_description()} does not have an attribute {key!r}")

    def get(self) -> Any:
        return self._target

    def __getitem__(self, key: str) -> Any:
        if key in self._target:
            return self._target[key]
        raise self._error(key)

    def __setitem__(self, key: str, value: Any) -> None:
        if key in self._target:
            self._target[key] = value
        else:
            raise self._error(key)

    def __delitem__(self, key: str) -> None:
        if key in self._target:
            del self._target[key]
        else:
            raise self._error(key)


class ChainedTarget(Target):
    """
    Chain multiple #Context implementations.
    """

    def __init__(self, *targets: Target) -> None:
        self._targets = targets

    def get(self) -> Any:
        return self._targets[0].get() if self._targets else None

    def __getitem__(self, key: str) -> Any:
        for ctx in self._targets:
            try:
                return ctx[key]
            except NameError:
                pass
        raise NameError(key)

    def __setitem__(self, key: str, value: Any) -> None:
        for ctx in self._targets:
            try:
                ctx[key] = value
                return
            except NameError:
                pass
        raise NameError(key)

    def __delitem__(self, key: str) -> None:
        for ctx in self._targets:
            try:
                del ctx[key]
                return
            except NameError:
                pass
        raise NameError(key)

    def chain_with(self, other: Target) -> "ChainedTarget":
        return ChainedTarget(*self._targets, other)


def object(obj: Any) -> ObjectTarget:
    """
    Return a wrapper for the object *obj* to be usable as a Closure target.
    """

    return ObjectTarget(obj)


def mutable_mapping(mapping: MutableMapping[str, Any], description: "str | None" = None) -> MutableMappingTarget:
    """
    Return a werapper for the specified mutable mapping to be usable as a Closure target.

    :param mapping: The mapping to wrap.
    :param description: The description to include in errors when trying to access a non-existent key in the mapping.
    """

    return MutableMappingTarget(mapping, description)


def chain(*targets: Target) -> ChainedTarget:
    """
    Chain multiple targets together.
    """

    return ChainedTarget(*targets)
