from types import SimpleNamespace

import pytest
from builddsl.api import Context
from builddsl.targets import ObjectTarget

code = """
task "foobar" do: {
  return n_times
}

task "belzebub" do: {
  def n_times = 1
  return n_times
}

task "cheeky" do: {
  def n_times = 1
  return (() -> n_times )()
}
"""


class Project:

  def __init__(self):
    self.tasks = {}

  def task(self, name, *, do):
    self.tasks[name] = do

  n_times = 10


def test_closure():
  print(Context.transpile(code, "<string>"))

  project = Project()
  Context(ObjectTarget(project)).exec(code)

  assert 'foobar' in project.tasks, project.tasks.keys()
  assert project.tasks['foobar'](SimpleNamespace(n_times=3)) == 3
  assert project.tasks['foobar'](SimpleNamespace()) == 10

  assert 'belzebub' in project.tasks, project.tasks.keys()
  assert project.tasks['belzebub'](SimpleNamespace(n_times=3)) == 1
  assert project.tasks['belzebub'](SimpleNamespace()) == 1

  assert 'cheeky' in project.tasks, project.tasks.keys()
  assert project.tasks['cheeky'](SimpleNamespace(n_times=3)) == 1
  assert project.tasks['cheeky'](SimpleNamespace()) == 1


def test_closure_bad_delete():
  with pytest.raises(NameError) as excinfo:
    Context(None).exec("del foobar", "<string>")
  assert str(excinfo.value) == "unclear where to delete 'foobar'"
