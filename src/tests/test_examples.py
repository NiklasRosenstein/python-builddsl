
import contextlib
import os
import io
import itertools
import typing as t

import pytest

from kahmi.dsl import run_file
from kahmi.dsl.macros import get_macro_plugin


examples_dir = os.path.normpath(__file__ + '/../../../examples')


@pytest.mark.parametrize("filename", os.listdir(examples_dir))
def test_examples(filename):
  path = os.path.join(examples_dir, filename)
  with open(path) as fp:
    macros: t.List[str] = []
    expected_lines: t.Optional[t.List[str]] = None

    for line in fp:
      if not line.startswith('#'): break
      line = line[1:]
      if line.startswith(' '):
        line = line[1:]
      if line.startswith('enabled macros:'):
        macros = [x.strip() for x in line[15:].strip().split(',')]
        continue
      if line.startswith('expected output:'):
        expected_lines = []
        continue
      if expected_lines is not None:
        expected_lines.append(line)
        continue
      raise ValueError(f'bad example header: {line!r}')

    if expected_lines[0] == '\n':
      expected_lines.pop(0)

    expected_output = ''.join(expected_lines)

  buffer = io.StringIO()
  with contextlib.redirect_stdout(buffer):
    run_file(object(), {}, filename=path, macros={x: get_macro_plugin(x)() for x in macros})

  assert buffer.getvalue() == expected_output
