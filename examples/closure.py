from textwrap import dedent

import builddsl


class HelloSayer:
    def __call__(self, closure: builddsl.UnboundClosure) -> None:
        closure(self)

    def to(self, name: str) -> None:
        print(f"Hello, {name}!")


def main() -> None:
    code = dedent(
        """
        hello {
            to name: "Richard"
        }"""
    )
    builddsl.Closure.from_map({"hello": HelloSayer()}).run_code(code)


if __name__ == "__main__":
    main()
