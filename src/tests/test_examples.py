
import contextlib
import os
import io
import itertools
import typing as t

import astor
import pytest

from kahmi.dsl import compile_file, run_file
from kahmi.dsl.__main__ import VoidContext
from kahmi.dsl.macros import get_macro_plugin


examples_dir = os.path.normpath(__file__ + '/../../../examples')


@pytest.mark.parametrize("filename", os.listdir(examples_dir))
def test_examples(filename):
  path = os.path.join(examples_dir, filename)
  with open(path) as fp:
    macros: t.List[str] = []
    expected_lines: t.Optional[t.List[str]] = None

    it = iter(fp)
    for line in it:
      if not line.startswith('#'): break
      if line.startswith('##'):  # Documentation block
        for line in it:
          print('skip', repr(line))
          if line.startswith('##'):
            break
        continue
      line = line[1:]
      if line.startswith(' '):
        line = line[1:]
      if not line.strip():
        continue
      if line.startswith('enabled macros:'):
        macros = [x.strip() for x in line[15:].strip().split(',')]
        continue
      if line.startswith('expected output:'):
        expected_lines = []
        continue
      if expected_lines is not None:
        expected_lines.append(line)
        continue
      raise ValueError(f'bad header: {line!r}')

    if expected_lines and expected_lines[0] == '\n':
      expected_lines.pop(0)

    expected_output = ''.join(expected_lines or [])

  macros = {x: get_macro_plugin(x)() for x in macros}
  print(astor.to_source(compile_file(path, macros=macros)))

  buffer = io.StringIO()
  with contextlib.redirect_stdout(buffer):
    run_file(VoidContext(), {}, filename=path, macros=macros)

  assert buffer.getvalue() == expected_output
