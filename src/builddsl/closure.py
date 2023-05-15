"""
Helpers for added runtime capabilities of transpiled BuildDSL code, specifically around variable
name resolution when enabling #TranspileOptions.closure_target.
"""

import builtins
import enum
import sys
import types
from dataclasses import dataclass
from typing import Any, Callable

from builddsl.targets import ObjectTarget, Target

# import weakref


class NotSet(enum.Enum):
    Value = 1


undefined = NotSet.Value


class ClosureState(Target):
    """
    This class represents the state of a closure that is passed as the first argument, named `__closure__`, to
    a function defined by the BuildDSL closure syntax. Its purpose is to carry forth the context for every
    subsequently nested closure definition.

    To illustrate this, consider the following BuildDSL code:

    ```py
    project {
        task("b") {
            depends_on task("a")
        }
    }
    ```

    This code defines two closures, nested in each other. The transpiled code will look somewhat like this:

    ```py
    @__closure__.subclosure
    def _closure_1(__closure__, self, *args, **kwargs):
        @__closure__.subclosure
        def _closure_1_closure_2(__closure__, self, *args, **kwargs):
            __closure__["depends_on"](__closure__["task"]("a"))
        __closure__["task"](_closure_1_closure_2)
    ```

    As you can see, we build a hierarchy of :class:`ClosureState` objects by decorating each function definition
    that corresponds to a closure with the :meth:`subclosure` decorator. This allows us to dynamically resolve the
    names `depends_on` and `task` in a depth-first order when they are accessed in the inner-most closure.

    * `depends_on` is a member on `task("b")`
    * `task` is a memeber on `project`
    """

    def __init__(
        self,
        target: "Target | None" = None,
        frame: "types.FrameType | None" = None,
        parent: "Target | None" = None,
        target_factory: Callable[[Any], Target] = ObjectTarget,
    ) -> None:
        """
        :param target: The target which is the priority for name resolution. There may be no target if the
            corresponding function is invoked with no positional arguments.
        :param frame: The frame in which the Closure was defined. This allows local variables defined in an
            outer closure to be resolved.
        :param parent: The parent for the Closure, usually this is another :class:`ClosureState` object which
            serves to further delegate name resolution to the target of the parent closures if a name could not
            be resolved in the current target or frame.
        :param target_factory: A factory that creates the :class:`Target` for the first argument passed into
            a :class:`ClosureFunction` call (created by :meth:`subclosure`).
        """

        self._parent = parent
        self._frame = frame  # weakref.ref(frame) if frame else None  # NOTE (@NiklasRosenstein): Cannot create weakref to frame  # noqa: E501
        self._target = target
        self._target_factory = target_factory

    def __repr__(self) -> str:
        return f"ClosureState(target={self._target!r})"

    def definition(self, func: Callable[..., Any], frame: "types.FrameType | None" = None) -> "ClosureFunction":
        """
        A decorator for a sub-closure function definition.
        """

        if frame is None:
            frame = sys._getframe(1)
        closure = ClosureFunction(self, frame, func)
        del frame
        return closure

    # Target

    def get(self) -> Any:
        return self._target.get() if self._target is not None else None

    def __getitem__(self, key: str) -> Any:
        frame = self._frame
        if frame and key in frame.f_locals:
            return frame.f_locals[key]
        if self._target is not None:
            try:
                return self._target[key]
            except NameError:
                pass
        if self._parent is not None:
            try:
                return self._parent[key]
            except NameError:
                pass
        if hasattr(builtins, key):
            return getattr(builtins, key)
        raise NameError(f"{key!r} in {self!r}")

    def __setitem__(self, key: str, value: Any) -> None:
        frame = self._frame
        if frame and key in frame.f_locals:
            raise RuntimeError("cannot set local variable through context, this should be handled by the transpiler")
        if self._target is not None:
            try:
                self._target[key] = value
                return
            except NameError:
                pass
        if self._parent is not None:
            try:
                self._parent[key] = value
                return
            except NameError:
                pass
        raise NameError(f"unclear where to set {key!r}")

    def __delitem__(self, key: str) -> None:
        frame = self._frame
        if frame and key in frame.f_locals:
            raise RuntimeError("cannot delete local variable through context, this should be handled by the transpiler")
        if self._target is not None:
            try:
                del self._target[key]
                return
            except NameError:
                pass
        if self._parent is not None:
            try:
                del self._parent[key]
                return
            except NameError:
                pass
        raise NameError(f"unclear where to delete {key!r}")


@dataclass
class ClosureFunction:
    """
    Represents the function definition of a sub-closure. Calling this object will invoke the wrapped function
    with a new :class:`ClosureState`.
    """

    parent: ClosureState
    frame: types.FrameType
    func: Callable[..., Any]

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        target = self.parent._target_factory(args[0]) if args else None
        __closure__ = ClosureState(target, self.frame, self.parent, self.parent._target_factory)
        return self.func(__closure__, *args, **kwargs)
