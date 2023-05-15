import argparse
import importlib
import os
import sys

from builddsl import Context
from builddsl.targets import ChainedTarget, ObjectTarget, Target

parser = argparse.ArgumentParser(prog=os.path.basename(sys.executable) + " -m builddsl")
parser.add_argument(
    "file", nargs="?", help="The file that contains BuildDSL code. If not specified, will read from stdin."
)
parser.add_argument(
    "-t",
    "--target",
    metavar="ENTRYPOINT",
    help="A Python entrypoint pointing to the object to use as the Closure context. If not specified, there will be "
    "no global target.",
)
parser.add_argument(
    "-E",
    "--transpile",
    action="store_true",
    help="Transpile the input BuildDSL code to Python. Requires the `astor` package which must be installed extra.",
)


def main() -> None:
    args = parser.parse_args()

    if args.transpile:
        if args.target:
            parser.error("conflicting arguments: -t/--target and -E/--transpile")

    if args.file:
        with open(args.file) as fp:
            code = fp.read()
        filename = args.file
    else:
        code = sys.stdin.read()
        filename = "<stdin>"

    if args.transpile:
        print(Context.transpile(code, filename))
        return

    if args.target:
        module_name, member = args.target.partition(":")
        target: Target = ObjectTarget(getattr(importlib.import_module(module_name), member)())
    else:
        target = ChainedTarget()  # Intentionally empty

    Context(target).exec(code, filename)


if __name__ == "__main__":
    main()
