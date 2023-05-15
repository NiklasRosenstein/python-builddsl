from textwrap import dedent
from typing import Any, Callable

import builddsl


class HelloSayer:
    def __call__(self, closure: Callable[[Any], Any]) -> None:
        closure(self)

    def to(self, name: str) -> None:
        print(f"Hello, {name}!")


def main() -> None:
    code = dedent(
        """
        hello {
            to name: "World"
        }"""
    )

    context = builddsl.Context(builddsl.targets.mutable_mapping({"hello": HelloSayer()}))
    context.exec(code)


if __name__ == "__main__":
    main()
