""" A superset of the Python programming language with support for closures and multi-line lambdas. """

from builddsl import targets
from builddsl.api import Context, execute
from builddsl.transpiler import TranspileOptions

__version__ = "1.0.1"

__all__ = [
    "Context",
    "execute",
    "targets",
    "TranspileOptions",
]
