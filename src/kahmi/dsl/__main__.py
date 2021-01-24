
import argparse
import importlib
import os
import sys

import astor

from . import run_file, parse_file

parser = argparse.ArgumentParser(prog=os.path.basename(sys.executable) + ' -m kahmi.dsl')
parser.add_argument('file', nargs='?')
parser.add_argument('-c', '--context', metavar='ENTRYPOINT')
parser.add_argument('-E', '--transpile', action='store_true')


class VoidContext:
  pass


def main():
  args = parser.parse_args()

  if args.transpile:
    if args.context:
      parser.error('conflicting arguments: -c/--context and -E/--transpile')

    module = parse_file(args.file or '<stdin>', sys.stdin if not args.file else None)
    print(astor.to_source(module))
    return

  if args.context:
    module_name, member = args.context.partition(':')
    context = getattr(importlib.import_module(module_name), member)()
  else:
    context = VoidContext()

  run_file(context, {}, args.file or '<stdin>', sys.stdin if not args.file else None)


if __name__ == '__main__':
  main()
