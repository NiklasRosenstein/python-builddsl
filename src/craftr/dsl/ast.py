
import ast as pyast
import types
import typing as t
from dataclasses import dataclass, field

import astor  # type: ignore


@dataclass
class Location:
  """
  Represents a location in a file, uniquely identified by a filename and offset. The line- and
  column number are derived metadata.
  """

  filename: str
  offset: int
  lineno: int
  colno: int


@dataclass
class Node:
  """
  Base class for craftr DSL AST nodes.
  """

  #: The node's parsing location.
  loc: Location = field(repr=False)


@dataclass
class Lambda(Node):
  """
  Represents a Lambda expression that was parsed from inside a Python expression. The lambda
  is replaced with a call to `__lambda_def__("<lambda_id>")` in the same location.
  """

  id: str
  fdef: pyast.FunctionDef

  def __repr__(self):
    return f'Lambda(func={astor.to_source(self.fdef)!r}'


@dataclass
class Expr(Node):
  """
  Represents a Python expression.
  """

  lambdas: t.List[Lambda]
  expr: pyast.Expression

  def __repr__(self):
    return f'Expr(lambdas={self.lambdas!r}, code={astor.to_source(self.expr)!r}'


@dataclass
class Target(Node):
  """
  A target is any valid Python identifier plus (for attribute access).
  """

  name: str

  def set(self, context: t.Union[t.Dict, t.Any], value: t.Any) -> None:
    parts = self.name.split('.')
    for part in parts[:-1]:
      if isinstance(context, t.Mapping):
        context = context[part]
      else:
        context = getattr(context, part)
    if isinstance(context, t.MutableMapping):
      context[parts[-1]] = value
    else:
      setattr(context, parts[-1], value)

  def get(self, context: t.Union[t.Dict, t.Any]) -> t.Any:
    parts = self.name.split('.')
    for part in parts:
      if isinstance(context, t.Mapping):
        context = context[part]
      else:
        context = getattr(context, part)
    return context


# TODO (@NiklasRosenstein): Rename to Closure

@dataclass
class Closure(Node):
  """
  A closure represents a code block that is executed in the context of an "owner" and "delegate". The
  owner is defined by the context in which the closure is defined, wheras the delegate is defined by
  the expression that the closure is defined with.

  ```py
  'Hello, World' {
    print(self())
  }
  ```

  In the above example, the string `'Hello, World'` is the delegate. The context in which the closure
  is defined, in this case the global module context, is the owner of the closure. The `self` argument
  is a #craftr.dsl.closure.ClosureContextProxy which gives access to the underlying closure, and proxies
  attribute access to the delegate and owner object.

  The general construct of a closure is as follows:

  ```
  <Expr> '{'
    <Stmt ...>
  '}'
  ```

  Closures can be nested. The owner of the inner closure will be the delegate of the outer closure.
  """

  #: A unique ID for the call.
  id: str

  #: The target of the block call expression.
  target: Expr

  #: Lambda definitions needed for the call.
  lambdas: t.List[Lambda]

  #: A Python expression that evaluates to the tuple of arguments for the target.
  args: t.Optional[t.List[pyast.expr]]

  #: A list of statements to execute in the block.
  body: t.List[Node]


@dataclass
class Assign(Node):
  """
  Assign a value to a member of the current context. The syntax is as follows:

      <Assign> ::= <Target> '=' <Expr>
  """

  #: The target of the assignment.
  target: Expr

  #: THe value to assign.
  value: Expr


@dataclass
class Module(Node):
  body: t.List[Node]
