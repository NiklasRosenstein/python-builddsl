
"""
Helpers for added runtime capabilities of transpiled Craftr DSL code, specifically around variable
name resolution when enabling #TranspileOptions.closure_target.
"""

import builtins
import functools
import sys
import types
import typing as t
# import weakref

from craftr.dsl.transpiler import TranspileOptions

undefined = object()


class Closure:
  r"""
  This class serves as a mapping to use for dynamic name lookup when transpiling Craftr DSL code to Python.
  Several options in the #TranspileOptions need to be tweaked for this to work correctly as the closure
  hierarchy needs to be built up manually:

  * Set #TranspileOptions.closure_target to `__closure__`
  * Set #TranspileOptions.closure_def_prefix to `@__closure__.child\n`
  * Set #TranspileOptions.closure_arglist_prefix to `__closure__,`

  You can initialize a #TranspileOptions object with these values using #init_options().

  When resolving names using #__getitem__(), #__setitem__() and #__delitem__(), the names will be looked
  up in the hierarchy of the closure itself. However do note that #__setitem__() and #__delitem__() cannot
  apply changes to the locals in a function. This is handled by proper rewriting rules in the #NameRewriter.
  """

  @staticmethod
  def init_options(options: TranspileOptions) -> None:
    options.closure_target = '__closure__'
    options.closure_def_prefix = '@__closure__.child\n'
    options.closure_arglist_prefix = '__closure__,'

  @staticmethod
  def get_options() -> TranspileOptions:
    options = TranspileOptions()
    Closure.init_options(options)
    return options

  def __init__(self, parent: t.Optional['Closure'], frame: t.Optional[types.FrameType], target: t.Any) -> None:
    self._parent = parent
    self._frame = frame  # weakref.ref(frame) if frame else None
    self._target = target

  @property
  def frame(self) -> t.Optional[types.FrameType]:
    return self._frame
    # if self._frame is None:
    #   return None
    # frame = self._frame()
    # if frame is None:
    #   raise RuntimeError(f'lost reference to closure frame')
    # return frame

  def child(self, func: t.Callable, frame: t.Optional[types.FrameType] = None) -> t.Callable:

    if frame is None:
      frame = sys._getframe(1)
    closure = Closure(self, frame, None)
    del frame

    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
      __closure__ = Closure(self, closure.frame, args[0]) if args else closure
      return func(__closure__, *args, **kwargs)

    return _wrapper

  def __getitem__(self, key: str) -> t.Any:
    frame = self.frame
    if frame and key in frame.f_locals:
      return frame.f_locals[key]
    if self._target is not None:
      value = getattr(self._target, key, undefined)
      if value is not undefined:
        return value
    if self._parent is not None:
      try:
        return self._parent[key]
      except NameError:
        pass
    if hasattr(builtins, key):
      return getattr(builtins, key)
    raise NameError(key)
