
"""
Transpiles a Kahmi DSL AST into a pure Python AST.
"""

import astor  # DEBUG
import ast as pyast
import typing as t
from dataclasses import dataclass

from . import ast, util


@dataclass
class Transpiler:

  lookup_func_name: str = '__lookup__'
  context_var_name: str = 'self'

  def transfer_loc(self, loc: ast.Location, node: pyast.AST) -> None:
    node.lineno = loc.lineno
    node.col_offset = loc.colno
    pyast.fix_missing_locations(node)

  def transpile_module(self, module: ast.Module) -> pyast.Module:
    nodes: t.List[pyast.AST] = list(self.transpile_nodes(module.body))
    module = pyast.Module(nodes)
    pyast.fix_missing_locations(module)
    return module

  def transpile_nodes(self, nodes: t.Iterable[ast.Node]) -> t.Iterator[pyast.AST]:
    for node in nodes:
      if isinstance(node, ast.Let):
        yield from self.transpile_let(node)
      elif isinstance(node, ast.Call):
        yield from self.transpile_call(node)
      elif isinstance(node, ast.Assign):
        yield from self.transpile_assign(node)
      else:
        raise RuntimeError(f'encountered unexpected node: {node!r}')

  def transpile_call(self, node: ast.Call) -> t.Iterator[pyast.AST]:
    if node.body:
      func_name = '__call_' + node.target.name.replace('.', '_')
      body = list(self.transpile_nodes(node.body))
      yield util.function_def(
        func_name, [self.context_var_name], body,
        lineno=node.loc.lineno, col_offset=node.loc.colno)

    yield from [x.fdef for x in node.lambdas]

    # Generate a call expression for the selected method.
    invoke_method = pyast.Call(
      # TODO(NiklasRosenstein): We need to decide whether to prefix it with self() or not.
      func=self.transpile_target(None, node.target, pyast.Load()),
      args=node.args,
      keywords=[],
      lineno=node.loc.lineno,
      col_offset=node.loc.colno)

    if node.body:
      yield pyast.Assign(targets=[util.name_expr('value', pyast.Store())], value=invoke_method)
    else:
      yield pyast.Expr(invoke_method)

    if node.body:
      yield pyast.Expr(pyast.Call(
        func=util.name_expr(func_name, pyast.Load()),
        args=[util.name_expr('value', pyast.Load())],
        keywords=[],
        lineno=node.loc.lineno,
        col_offset=node.loc.colno))

  def transpile_assign(self, node: ast.Assign) -> t.Iterator[pyast.AST]:
    target = self.transpile_target(self.context_var_name, node.target, pyast.Store())
    yield from [x.fdef for x in node.value.lambdas]
    yield pyast.Assign(targets=[target], value=node.value.expr.body)

  def transpile_let(self, node: ast.Let) -> t.Iterator[pyast.AST]:
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
    code = f'{self.lookup_func_name}({parts[0]!r}, locals(), {self.context_var_name})'
    if len(parts) > 1:
      code += '.' + '.'.join(parts[1:])
    return util.name_expr(code, ctx, lineno=node.loc.lineno, col_offset=node.loc.colno)

  def transpile_expr(self, node: ast.Expr) -> t.Tuple[t.List[pyast.FunctionDef], pyast.expr]:
    return [x.fdef for x in node.lambdas], node.expr.body
