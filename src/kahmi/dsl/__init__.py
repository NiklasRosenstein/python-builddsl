
"""
This package implements the Kahmi DSL laguage.
"""

__author__ = 'Niklas Rosenstein <rosensteinniklas@gmail.com>'
__version__ = '0.0.1'

import ast as pyast
import builtins
import typing as t

from . import parser, transpiler


def _lookup(name: str, *scopes: t.Any) -> None:
  objs = []
  for scope in scopes:
    if isinstance(scope, dict):
      if name in scope:
        return scope[name]
    else:
      try:
        return getattr(scope, name)
      except AttributeError:
        pass
      objs.append(scope)
  try:
    return getattr(builtins, name)
  except AttributeError:
    pass

  msg = f'lookup for {name!r} failed, checked locals and:'
  for obj in objs:
    msg += f'\n  - {type(obj).__name__!r}'
  msg += '\n  - builtins'
  raise NameError(msg)


def run_file(
  context: t.Any,
  globals: t.Mapping[str, t.Any],
  filename: str,
  fp: t.Optional[t.TextIO] = None,
) -> None:

  module = parse_file(filename, fp)

  globals['__lookup__'] = _lookup
  globals['self'] = context

  module = parse_file(filename, fp)
  code = compile(module, filename=filename, mode='exec')
  exec(code, globals)


def parse_file(filename: str, fp: t.Optional[t.TextIO] = None) -> pyast.Module:
  if fp is None:
    with open(filename, 'r') as fp:
      return parse_file(filename, fp)

  module = parser.Parser(fp.read(), filename).parse()
  return transpiler.Transpiler().transpile_module(module)
