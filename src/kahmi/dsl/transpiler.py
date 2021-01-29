
"""
Transpiles a Kahmi DSL AST into a pure Python AST.
"""

import ast as pyast
import builtins
import contextlib
import functools
import threading
import sys
import typing as t
from itertools import chain
from dataclasses import dataclass

from nr.pylang.ast.dynamic_eval import rewrite_names  # type: ignore

from . import ast, parser, util
from .macros import MacroPlugin

T_Callable = t.TypeVar('T_Callable', bound=t.Callable)


class Runtime:
  """
  A runtime object supports the execution of a Python module transpiled from the Kahmi DSL. The
  runtime is a thread-safe object that keeps track of the closure targets and local variables in
  order to implement the name resolution.
  """

  def __init__(self, initial: t.Any):
    self._initial = initial
    self._threadlocal = threading.local()

  @property
  def _threadlocal_stack(self) -> t.List[t.Any]:
    try:
      return self._threadlocal.stack
    except AttributeError:
      stack = self._threadlocal.stack = []
      if self._initial is not None:
        stack.append(self._initial)
      return stack

  def closure(self) -> t.Callable[[T_Callable], T_Callable]:
    """
    Mark a function as being a closure. Effectively this just pushes the first argument of the
    closure on the threadlocal stack for name resolution.
    """

    def decorator(func):
      @functools.wraps(func)
      def wrapper(ctx, *args, **kwargs):
        with self.pushing(ctx):
          return func(ctx, *args, **kwargs)
      return wrapper

    return decorator

  def push(self, ctx: t.Any) -> None:
    self._threadlocal_stack.append(ctx)

  def pop(self) -> t.Any:
    return self._threadlocal_stack.pop()

  @contextlib.contextmanager
  def pushing(self, ctx: t.Any) -> t.Iterator[None]:
    try:
      self.push(ctx)
      yield
    finally:
      assert self.pop() is ctx

  def lookup(self, name: str) -> t.Any:
    """
    Performs a lookup for a variable. First, it checks the locals of the calling frame. Then, it
    checks the dictionaries or object's stored on the runtime's thread-local stack. Finally, the
    calling frame's globals are checked.
    """

    frame = sys._getframe(1)
    try:
      for item in chain([frame.f_locals], reversed(self._threadlocal_stack), [frame.f_globals, builtins]):
        if isinstance(item, t.Mapping):
          if name in item:
            return item[name]
        else:
          try:
            return getattr(item, name)
          except AttributeError:
            pass
      raise NameError(name, self._threadlocal_stack)
    finally:
      del frame

  __getitem__ = lookup


@dataclass
class Transpiler:

  #: The name of the #Runtime object that is present in the global scope during execution
  #: of the transpiled module.
  runtime_object_name: str = '__runtime__'

  #: The name of the closure argument.
  closure_arg_name: str = 'self'

  def _lookup_code(self, name: str) -> str:
    return f'{self.runtime_object_name}.lookup({name!r})'

  def transfer_loc(self, loc: ast.Location, node: pyast.AST) -> None:
    node.lineno = loc.lineno
    node.col_offset = loc.colno
    pyast.fix_missing_locations(node)

  def transpile_module(self, module: ast.Module) -> pyast.Module:
    nodes: t.List[pyast.stmt] = list(self.transpile_nodes(module.body))
    pyast_module = util.module(nodes)
    pyast.fix_missing_locations(pyast_module)
    # Rewrite variable references with lookups via the __runtime__.
    pyast_module = rewrite_names(
      pyast_module, self.runtime_object_name,
      store=False, delete=False, scope_inheritance=False)
    return pyast_module

  def transpile_nodes(self, nodes: t.Iterable[ast.Node]) -> t.Iterator[pyast.stmt]:
    for node in nodes:
      if isinstance(node, ast.Let):
        yield from self.transpile_let(node)
      elif isinstance(node, ast.Call):
        yield from self.transpile_call(node)
      elif isinstance(node, ast.Assign):
        yield from self.transpile_assign(node)
      else:
        raise RuntimeError(f'encountered unexpected node: {node!r}')

  def transpile_call(self, node: ast.Call) -> t.Iterator[pyast.stmt]:
    if node.body:
      func_name = '__configure_' + node.target.name.replace('.', '_')
      body = list(self.transpile_nodes(node.body))
      dec = t.cast(pyast.Expr, util.compile_snippet('__runtime__.closure()')[0]).value
      yield util.function_def(
        func_name,
        [self.closure_arg_name],
        body,
        decorator_list=[dec],
        lineno=node.loc.lineno, col_offset=node.loc.colno)

    yield from [x.fdef for x in node.lambdas]

    target = self.transpile_target(None, node.target, pyast.Load())

    # Generate a call expression for the selected method.
    if node.args is not None:
      target = pyast.Call(
        # TODO(NiklasRosenstein): We need to decide whether to prefix it with self() or not.
        func=target,
        args=node.args,
        keywords=[],
        lineno=node.loc.lineno,
        col_offset=node.loc.colno)

    if node.body:
      value_name = func_name + '_' + self.closure_arg_name + '_target'
      yield pyast.Assign(targets=[util.name_expr(value_name, pyast.Store())], value=target)

      # If the value appears to be a context manager, enter it's context before executing
      # the body of the call.
      yield from t.cast(t.List[pyast.stmt], util.compile_snippet(
        f'with {self.runtime_object_name}.pushing(locals()):\n'
        f'  if hasattr({value_name}, "configure"):\n'
        f'    {value_name}.configure({func_name})\n'
        f'  else:\n'
        f'    {value_name}({func_name})\n',
        lineno=node.loc.lineno,
        col_offset=node.loc.colno))

    else:
      yield pyast.Expr(target)

  def transpile_assign(self, node: ast.Assign) -> t.Iterator[pyast.stmt]:
    target = self.transpile_target(self.closure_arg_name, node.target, pyast.Store())
    yield from [x.fdef for x in node.value.lambdas]
    yield pyast.Assign(targets=[target], value=node.value.expr.body)

  def transpile_let(self, node: ast.Let) -> t.Iterator[pyast.stmt]:
    target = self.transpile_target(None, node.target, pyast.Store())
    yield from [x.fdef for x in node.value.lambdas]
    yield pyast.Assign(targets=[target], value=node.value.expr.body)

  def transpile_target(self,
    prefix: t.Optional[str],
    node: ast.Target,
    ctx: pyast.expr_context
  ) -> pyast.expr:
    """
    Converts an #ast.Target node into an expression that identifies the target with the specified
    context (load/store/del).
    """

    name = node.name
    if prefix is not None:
      name = prefix + '.' + name

    if isinstance(ctx, pyast.Store) or prefix:
      return util.name_expr(name, ctx)

    parts = name.split('.')
    code = parts[0]
    if len(parts) > 1:
      code += '.' + '.'.join(parts[1:])
    return util.name_expr(code, ctx, lineno=node.loc.lineno, col_offset=node.loc.colno)

  def transpile_expr(self, node: ast.Expr) -> t.Tuple[t.List[pyast.FunctionDef], pyast.expr]:
    return [x.fdef for x in node.lambdas], node.expr.body


def run_file(
  context: t.Any,
  globals: t.Dict[str, t.Any],
  filename: str,
  fp: t.Optional[t.TextIO] = None,
  macros: t.Optional[t.Dict[str, MacroPlugin]] = None,
) -> None:

  globals['self'] = context
  globals['__runtime__'] = Runtime(context)

  module = compile_file(filename, fp, macros)
  code = compile(module, filename=filename, mode='exec')
  exec(code, globals)


def compile_file(
  filename: str,
  fp: t.Optional[t.TextIO] = None,
  macros: t.Optional[t.Dict[str, MacroPlugin]] = None,
) -> pyast.Module:

  if fp is None:
    with open(filename, 'r') as fp:
      return compile_file(filename, fp, macros)

  module = parser.Parser(fp.read(), filename, macros).parse()
  return Transpiler().transpile_module(module)


__all__ = ['Transpiler', 'run_file', 'compile_file']
