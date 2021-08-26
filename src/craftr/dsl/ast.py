
import ast as pyast
import types
import typing as t
from dataclasses import dataclass, field

import astor  # type: ignore
from nr.preconditions import check_instance_of


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

  def __post_init__(self) -> None:
    check_instance_of(self.fdef, pyast.FunctionDef)

  def __repr__(self):
    return f'Lambda(func={astor.to_source(self.fdef)!r}'


@dataclass
class Expr(Node):
  """
  Represents a Python expression.
  """

  lambdas: t.List[Lambda]
  expr: pyast.expr

  def __post_init__(self) -> None:
    check_instance_of(self.expr, pyast.expr)

  def __repr__(self):
    return f'Expr(lambdas={self.lambdas!r}, code={astor.to_source(self.expr)!r}'


@dataclass
class Stmt(Node):
  lambdas: t.List[Lambda]
  stmt: pyast.stmt

  def __post_init__(self) -> None:
    check_instance_of(self.stmt, pyast.stmt)

  def __repr__(self):
    return f'Stmt(lambdas={self.lambdas!r}, code={astor.to_source(self.stmt)!r}'


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

  def __post_init__(self) -> None:
    check_instance_of(self.target, Expr)


@dataclass
class Module(Node):
  body: t.List[Node]
