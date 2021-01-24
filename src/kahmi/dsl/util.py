
import ast
import typing as t

T = t.TypeVar('T')
U = t.TypeVar('U')


class maps(t.Generic[T, U]):
  """
  Map a function over a value if it is not None and return the result. Example usage:

  ```py
  value: t.Optional[int] = os.getenv('NUM_CORES') | maps(int)
  ```
  """

  def __init__(self, func: t.Callable[[T], U]) -> None:
    self._func = func

  def __ror__(self, val: t.Optional[T]) -> t.Optional[U]:
    if val is not None:
      return self._func(val)
    return None


def function_def(
  name: str,
  args: t.List[str],
  body: t.List[ast.AST],
  lineno: t.Optional[int] = None,
  col_offset: t.Optional[int] = None,
) -> ast.FunctionDef:
  """
  Helper function to create a function def.
  """

  node = ast.FunctionDef(
    name=name,
    args=ast.arguments(
      args=[ast.arg(x, None) for x in args],
      vararg=None,
      kwonlyargs=[],
      kw_defaults=[],
      kwarg=None,
      defaults=[]),
    body=body,
    decorator_list=[],
    lineno=lineno,
    col_offset=col_offset)
  ast.fix_missing_locations(node)
  return node


def name_expr(
  name: str,
  ctx: ast.expr_context,
  lineno: t.Optional[int] = None,
  col_offset: t.Optional[int] = None
) -> ast.expr:
  """
  Helper function to parse a name/attribute access/indexing to an AST node.
  """

  node = t.cast(ast.Expression, ast.parse(name, mode='eval')).body
  if hasattr(node, 'ctx'):
    node.ctx = ctx  # type: ignore
  if lineno is not None:
    node.lineno = lineno
  if col_offset is not None:
    node.col_offset = col_offset
  ast.fix_missing_locations(node)
  return node
