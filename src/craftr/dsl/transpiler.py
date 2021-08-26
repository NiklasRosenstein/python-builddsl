
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
      elif isinstance(node, ast.Assign):
        yield from self.transpile_assign(node)
      elif isinstance(node, ast.Expr):
        lambdas, expr = self.transpile_expr(node)
        yield from lambdas
        yield pyast.Expr(expr)
      else:
        raise RuntimeError(f'encountered unexpected node: {node!r}')

  def transpile_closure(self, node: ast.Closure) -> t.Iterator[pyast.stmt]:
    yield from (x.fdef for x in node.lambdas)

    lambdas, target = self.transpile_expr(node.target)
    yield from lambdas

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

  def transpile_assign(self, node: ast.Assign) -> t.Iterator[pyast.stmt]:
    yield from (x.fdef for x in node.target.lambdas)
    yield from (x.fdef for x in node.value.lambdas)
    stmts = util.compile_snippet(f'{astor.to_source(node.target.expr).rstrip()} = {astor.to_source(node.value.expr)}')
    assert len(stmts) == 1
    yield t.cast(pyast.stmt, stmts[0])

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
