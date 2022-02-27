# Usage example

  [Novella]: https://niklasrosenstein.github.io/novella/

This example is from the [Novella][] project. It uses the `craftr.dsl.Closure` class to execute a file
that contains Craftr DSL code using a `NovellaContext` object as the root closure target. This allows
members of the target object to be invoked at the top-level of the script directly without explicitly
prefixing the member names with `self` or any of the sort. 

```py
class Novella:
  """ This class is the main entrypoint for starting and controlling a Novella build. """

  BUILD_FILE = Path('build.novella')

  def __init__(self, project_directory: Path) -> None:
    self.project_directory = project_directory

  def execute_file(self, file: Path | None = None) -> NovellaContext:
    """ Execute a file, allowing it to populate the Novella pipeline. """

    from craftr.dsl import Closure
    context = NovellaContext(self)
    file = file or self.BUILD_FILE
    Closure(None, None, context).run_code(file.read_text(), str(file))
    return context

class NovellaContext:
  
  def do(
    self,
    action_type_name: str,
    closure: t.Callable | None = None,
    name: str | None = None,
  ) -> None:

  # ...
```

__Example script__

```py
do "copy-files" {
  content = [ "content", "mkdocs.yml" ]
}
```
