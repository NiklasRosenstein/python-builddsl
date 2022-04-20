"""
Transpile Craftr DSL code to full fledged Python code.
"""

import ast
import logging
import sys
import typing as t
from contextlib import contextmanager
from dataclasses import dataclass, field

from ._rewriter import Closure, Grammar, Rewriter
from .ast_utils import DynamicLookupRewriter


@dataclass
class TranspileOptions:
  """ Options for transpiling Craftr DSL code. """

  #: If enabled, names are read, written and deleted through the `__getitem__()`, `__setitem__()` and
  #: `__delitem__()` of the given name. If you need extra flexibility, you can set this to the name of
  #: a global object that is then responsible for name resolution.
  closure_target: t.Optional[str] = None  # '__closure__'

  #: Set of builtin names that are "pure", i.e. they are never touched by the #NameRerwriter.
  #: This is only used if #closure_target is set.
  pure_builtins: t.Collection[str] = frozenset()  # frozenset(['__closure_decorator__'])

  #: This is only used if #closure_target is specified and the #NameRewriter kicks in. Variable declarations
  #: prefixed with `def` are prefixed with the given string. Defaults to prefix supplied in the #grammar.
  local_vardef_prefix: str = '_def_'

  #: A preamble of pure Python code to include at the top of the module.
  preamble: str = ''  # 'from craftr.core.closure import closure as __closure_decorator__\n'

  #: Pure python code to include before a closure definition, for example to decorate it.
  closure_def_prefix: str = ''  # '@__closure_decorator__(__closure__)\n'

  #: The default argument list for closures without an explicit argument list. By default a
  #: closure always accepts a "self" argument, but also any other arguments that are passed
  #: to it. This is useful when using a arglist-less closure for a function that passed
  #: multiple arguments, but the closure is only interested in the first.
  closure_default_arglist: str = 'self, *arguments, **kwarguments'

  #: A prefix to the argument list of closures. This prefix is added even to closures without
  #: explicit arglist (so the final arglist will be #closure_arglist_prefix followed by
  #: #closure_default_arglist).
  closure_arglist_prefix: str = ''  # '__closure__,'

  grammar: Grammar = field(default_factory=Grammar)

  def sync(self) -> None:
    """ Synchronize the options to the #Grammar settings, i.e. the #Grammar.local_def setting
    will be enabled or disabled depending on whether #closure_target is set and the
    #local_vardef_prefix is used to set #Grammar.local_prefix. """

    self.grammar.local_def = self.closure_target is not None
    self.grammar.local_prefix = self.local_vardef_prefix


def transpile_to_ast(code: str, filename: str, options: t.Optional[TranspileOptions] = None) -> ast.Module:
  """
  Transpile the Craftr DSL *code* to a Python `ast.Module` that can be executed.
  """

  options = options or TranspileOptions()
  rewrite = Rewriter(code, filename, options.grammar).rewrite()
  if sys.version_info[:2] <= (3, 7):
    module = ast.parse(rewrite.code, filename, mode='exec')
  else:
    module = ast.parse(rewrite.code, filename, mode='exec', type_comments=False)
  module = ClosureRewriter(filename, options, rewrite.closures).visit(module)
  if options.closure_target:
    dynamic_lookup = DynamicLookupRewriter(options.closure_target, options.pure_builtins, options.local_vardef_prefix)
    module = t.cast(ast.Module, dynamic_lookup.visit(module))
  return ast.fix_missing_locations(module)


def transpile_to_source(code: str, filename: str, options: t.Optional[TranspileOptions] = None) -> str:
  """
  Transpile the Craftr DSL *code* to Python code. Requires the `astor` module to be installed.
  """

  from astor import to_source  # type: ignore
  return to_source(transpile_to_ast(code, filename, options))


class ClosureRewriter(ast.NodeTransformer):
  """
  Rewrites references to closure variables and injects Closure function definitions.
  """

  log = logging.getLogger(__module__ + '.' + __qualname__)  # type: ignore

  def __init__(self, filename: str, options: TranspileOptions, closures: t.Dict[str, Closure]) -> None:
    self.filename = filename
    self.options = options
    self.closures = closures

    # Keep track of the hierarchy during the visitation.
    self._hierarchy: t.List[ast.AST] = []

    # Marks the statement nodes in the hierarchy with the closure name(s) to insert.
    self._closure_inserts: t.Dict[ast.stmt, t.List[str]] = {}

  def _get_closure_def(self, closure_id: str) -> ast.FunctionDef:
    """
    Generate a function definition for a closure id.
    """

    closure = self.closures[closure_id]
    if closure.parameters is None:
      arglist = self.options.closure_default_arglist
    else:
      arglist = ', '.join(closure.parameters)
    arglist = self.options.closure_arglist_prefix + arglist

    function_code = f'{self.options.closure_def_prefix}def {closure_id}({arglist}):\n'
    function_code = '\n' * (function_code.count('\n') + closure.line) + function_code
    if closure.expr:
      function_code += ' ' * closure.indent + 'return ' + closure.expr
    else:
      function_code += (closure.body or '').rstrip() or (' ' * closure.indent + 'pass')

    # self.log.debug('_get_closure_def(%r): parse function body\n\n%s\n', closure_id,
    #                '  ' + '\n  '.join(function_code.lstrip().splitlines()))

    if sys.version_info[:2] <= (3, 7):
      module = ast.parse(function_code, self.filename, mode='exec')
    else:
      module = ast.parse(function_code, self.filename, mode='exec', type_comments=False)

    func = module.body[0]
    assert isinstance(func, ast.FunctionDef)
    return func

  def visit_Name(self, name: ast.Name) -> ast.AST:
    if name.id in self.closures:
      for node in reversed(self._hierarchy):
        if isinstance(node, ast.stmt):
          self._closure_inserts.setdefault(node, []).append(name.id)
          break
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
          raise RuntimeError('did not find inner statement to inject closure')
    return self.generic_visit(name)

  def visit_Module(self, node: ast.Module) -> ast.AST:
    preamble = ast.parse(self.options.preamble, self.filename, mode='exec')
    node.body[0:0] = preamble.body
    return self.generic_visit(node)

  def visit(self, node: ast.AST) -> t.Any:
    self._hierarchy.append(node)
    try:
      result: t.Union[ast.AST, t.List[ast.AST]] = super().visit(node)
      if node in self._closure_inserts:
        assert isinstance(node, ast.stmt)
        assert isinstance(result, ast.AST)
        result = [result]
        for closure_id in self._closure_inserts.get(node, []):
          func = self.visit(self._get_closure_def(closure_id))
          result.insert(len(result) - 1, func)
      return result
    finally:
      assert self._hierarchy.pop() == node
