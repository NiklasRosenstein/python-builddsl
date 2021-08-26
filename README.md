# craftr-dsl

The Craftr DSL is a transpiler for the Python language that introduces two major concepts into the language
that are found in other languages used for build scripts (like Groovy), namely **closures** and
**multi-line lambdas**. Using JIT transpilation, tracebacks can mostly point to the original line in the
Craftr DSL code.

__Table of Contents__

* [Closures vs. lambdas](#closures-vs-lambdas)
* [Macros](#macros)

---

## Closures vs. lambdas

A closure is similar to a lambda, in that it is represented internally as a function. However, a closure is
bound to a specific "context" and does not accept arguments. The closure context is represented by the `self`
name that is available in the closure's inner scope.

<table>
<tr><th></th><th>Closure</th><th>Lambda</th></tr>
<tr><th>Craftr DSL</th><td>

```py
'Hello, World' {
  print(type(self).__name__)
  print(type(self()).__name__)
  print(self())
  print(self.upper())
}
```

</td><td>

```py
let func = (name) => {
  print(f'Hello, {name}!')
}

func('World')
```

</td></tr>
<tr><th>Python (generated)</th><td>

```py
@__runtime__.closure(self.__closure__.delegate, 'Hello, World')
def _closure_main_craftr_1_0(self):
    print(type(self).__name__)
    print(type(self()).__name__)
    print(self())
    print(self.upper())


_closure_main_craftr_1_0()
```

</td><td>

```py
def _lambda_main_craftr_1_11(name):
    print(f'Hello, {name}!')


func = _lambda_main_craftr_1_11
func('World')
```

</td></tr>
<tr>
<th>Output</th><td>

```
ClosureContextProxy
str
Hello, World
HELLO, WORLD
```

</td><td>

```
Hello, World!
```

</td></tr>
</table>

---

## Macros

In addition to closures and multi-line lambdas, plugins can hook into the parser to parse custom syntax and
convert it to proper Python AST nodes. An example of this is the `yaml` plugin that is available by default
with Craftr DSL, but must be enabled in the transpiler.


<table>
<tr><th>With YAML macro</th><th>Without YAML macro</th></tr>
<tr><td>

```py
buildscript {
  dependencies = !yaml {
    - craftr-git
    - craftr-python
  }
}
```

</td><td>


```py
buildscript {
  dependencies = [
    'craftr-git',
    'craftr-python'
  ]
}
```

</td></tr>
</table>



---

<p align="center">Copyright &copy; 2021 Niklas Rosenstein</p>
