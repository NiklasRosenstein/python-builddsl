# builddsl

BuildDSL is (almost) a superset of the Python programming language that adds additional syntactical and semantical
features that are strongly inspired by the [Gradle DSL](https://docs.gradle.org/current/dsl/index.html).

* Multi-line lambdas
* Closures with dynamic name resolution (optional feature)
* Parentheses-less function calls (top-level only)
* Optional comma separation in function arguments

## Installation

    $ pip install builddsl

The `builddsl` package requires at least Python 3.6.

## Quickstart

```py
import builddsl
from typing import Callable

def hello(get_name: Callable[[], str]) -> None:
    print("Hello", get_name())

context = builddsl.Context(
    target=builddsl.targets.mutable_mapping({"hello": hello}),
    closures_enabled=True,
)

context.exec("""
hello {
    return "World"
}
""")

# prints: "Hello, World"
```

## Projects using BuildDSL

* [Novella](https://niklasrosenstein.github.io/novella/)
