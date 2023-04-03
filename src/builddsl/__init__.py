""" A superset of the Python programming language with support for closures and multi-line lambdas. """

from ._execute import execute
from ._rewriter import Grammar, SyntaxError
from ._runtime import ChainContext, Closure, Context, MapContext, ObjectContext, UnboundClosure
from ._transpiler import TranspileOptions, transpile_to_ast, transpile_to_source

__version__ = "1.0.1"

__all__ = [
    "execute",
    "Grammar",
    "SyntaxError",
    "ChainContext",
    "Closure",
    "Context",
    "MapContext",
    "ObjectContext",
    "UnboundClosure",
    "TranspileOptions",
    "transpile_to_ast",
    "transpile_to_source",
]
