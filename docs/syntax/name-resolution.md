# Dynamic name resolution <sup>(non-default)</sup>

For some purposes and applications, dynamic name resolution may be desirable, for
example when writing `self` in front of every name to access a property of the closure
target object is too cumbersome. For this, the Craftr DSL transpiler can generate code that
looks up, sets and deletes keys using subscript syntax on a particular variable name.

Using the `craftr.dsl.runtime` package, you can configure the transpiler and runtime
to use dynamic name resolution. Example usage:

```py
from craftr.dsl.transpiler import transpile_to_ast
from craftr.dsl.runtime import Closure

class Project:
  def task(self, name: str, *, do: callable): ...

code = ...
filename = ...

# Long form:
module = transpile_to_ast(code, filename, Closure.get_options())
code = compile(module, filename, 'exec')
scope = {'__closure__': Closure(None, None, Project())}
exec(code, scope)

# Shorthand form:
Closure(None, None, Project()).run_code(code, filename)
```

The `Closure.get_options()` function returns `TranspileOptions` that instruct the transpiler
to convert name lookups into subscripts on the `__closure__` variable, add a
`@__closure__.child` decoration before every closure function definition and to add a
`__closure__,` argument to their arglist. The `Closure` object passed into the `scope`
on execution deals with the rest.

<table>

<tr><th>Craftr DSL</th><th>Python</th></tr>

<tr><td>

```py
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
```
</td><td>

```py
@__closure__.child
def _closure_1(__closure__, self, *arguments, **kwarguments):
    return __closure__['n_times']
__closure__['task']('foobar', do=_closure_1)

@__closure__.child
def _closure_2(__closure__, self, *arguments, **kwarguments):
    n_times = 1
    return n_times
__closure__['task']('belzebub', do=_closure_2)

@__closure__.child
def _closure_3(__closure__, self, *arguments, **kwarguments):
    n_times = 1
    @__closure__.child
    def _closure_3_closure_3(__closure__):
        return n_times
    return _closure_3_closure_3()
__closure__['task']('cheeky', do=_closure_3)
```

</td></tr>

</table>
