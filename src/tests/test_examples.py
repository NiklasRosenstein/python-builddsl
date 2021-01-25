
import contextlib
import os
import io
import itertools

import pytest

from kahmi.dsl import run_file


examples_dir = os.path.normpath(__file__ + '/../../../examples')


@pytest.mark.parametrize("filename", os.listdir(examples_dir))
def test_examples(filename):
  path = os.path.join(examples_dir, filename)
  with open(path) as fp:
    assert fp.readline() == '# Expected output:\n'
    assert fp.readline() == '#\n'
    expected_output = ''.join(x.lstrip('#').lstrip(' ') for x in
      itertools.takewhile(lambda x: x.startswith('#'), fp))

  buffer = io.StringIO()
  with contextlib.redirect_stdout(buffer):
    run_file(object(), {}, filename=path)

  assert buffer.getvalue() == expected_output
