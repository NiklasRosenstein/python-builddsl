
"""
Transpiles a craftr DSL AST into a pure Python AST.
"""

import ast as pyast
import typing as t
from dataclasses import dataclass

import astor  # type: ignore

from . import ast, parser, util
from .macros import MacroPlugin


@dataclass
class Transpiler:

  #: The name of the #Runtime object that is present in the global scope during execution
  #: of the transpiled module.
  runtime_object_name: str = '__runtime__'

  #: The name of the closure argument.
  closure_arg_name: str = 'self'

  def transfer_loc(self, loc: ast.Location, node: pyast.AST) -> None:
    node.lineno = loc.lineno
    node.col_offset = loc.colno
    pyast.fix_missing_locations(node)

  def transpile_module(self, module: ast.Module) -> pyast.Module:
    nodes: t.List[pyast.stmt] = list(self.transpile_nodes(module.body))
    pyast_module = util.module(nodes)
    pyast.fix_missing_locations(pyast_module)
    return pyast_module

  def transpile_nodes(self, nodes: t.Iterable[ast.Node]) -> t.Iterator[pyast.stmt]:
    for node in nodes:
      if isinstance(node, ast.Closure):
        yield from self.transpile_closure(node)
      elif isinstance(node, ast.Expr):
        yield from (x.fdef for x in node.lambdas)
        yield pyast.Expr(node.expr)
      elif isinstance(node, ast.Lambda):
        yield node.fdef
      elif isinstance(node, ast.Stmt):
        yield from (x.fdef for x in node.lambdas)
        yield node.stmt
      else:
        raise RuntimeError(f'encountered unexpected node: {node!r}')

  def transpile_closure(self, node: ast.Closure) -> t.Iterator[pyast.stmt]:
    yield from (x.fdef for x in node.lambdas)

    yield from node.target.lambdas
    target = node.target.expr

    if node.body:
      func_name = node.id
      body = list(self.transpile_nodes(node.body))
      dec = t.cast(pyast.Expr, util.compile_snippet(f'{self.runtime_object_name}.closure(self.__closure__.delegate)')[0]).value
      t.cast(pyast.Call, dec).args.append(target)
      yield util.function_def(
        func_name,
        [self.closure_arg_name],
        body,
        decorator_list=[dec],
        lineno=node.loc.lineno, col_offset=node.loc.colno)

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
      yield from t.cast(t.Iterable[pyast.stmt], util.compile_snippet(f'{node.id}()'))

    else:
      yield pyast.Expr(target)


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


__all__ = [
  'NameProvider',
  'PropertyOwner',
  'Runtime',
  'Transpiler',
  'run_file',
  'compile_file',
]
