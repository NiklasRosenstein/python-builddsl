# kahmi-dsl

This is a Python-based configuration language for the [Kahmi](https://github.com/kahmi-build)
build system that is heavily inspired by Groovy and Gradle.

__Example:__

```python
buildscript {
  dependencies = ["kahmi-git", "kahmi-cxx"]
}

let cxx = load("kahmi-cxx")
let git = load("kahmi-git")

name = "myproject"
version = git.version()

cxx.build("main") {
  srcs = glob("src/*.cpp")
  type = "executable"
}
```

## Syntax & Semantics

The Kahmi DSL is not a strict superset of the Python language, instead it wraps Python code and
swaps between DSL parsing and Python code parsing.

### Kahmi DSL Syntax

1. **Define a local variable with the `let` Keyword**

    Local variables are defined using the `let` keyword. The variable can then be addressed in
    Python expressions or as call block targets (see below). The right hand side of the assignment
    must be a Python expression.

    ```python
    let my_variable = 42
    ```

2. **Set a property on the current context object**

    The same syntax but without the `let` keyword assigns the value to a member of the current
    context object instead of to a local variable.

    ```python
    nmae = "my-project"
    version = git.version()
    ```

3. **Configure blocks**

    A configure block basically generates a Python function, called the "closure", and passes it
    to the specified target. The closure that is defined after the target is passed to the target
    by either calling it's `configure()` method or calling the target directly. 

    ```python
    print("Hello, World!")  # Call without body

    buildscript {
      dependencies = ["kahmi-python"]
    }

    cxx.build("main") {
      srcs = glob("src/*.cpp")
    }
    ```

    > At the root level, every Kahmi script is basically a closure that is executed against the
    > main context object.

### Python Syntax Extensions

When parsing a Python expression, Kahmi injects support for multi-line lambdas and macros.

1. **Multi-line lambdas**

    The Kahmi DSL parser injects the ability to define multi-line lambdas in any Python
    expression. The lambda syntax is inspired by Javascript/Typescript and uses `=>` as
    the lambda arrow operation to connect the argument definition with the lambda body.

    A lambda with braces requires a return statement, otherwhise the return value of the
    lambda will be `None`. Single-statement lambdas are not currently supported with this
    syntax (although you can always fall back to standard syntax `lambda: <expr>`).

    ```python
    let myFunc = () => {
      import random
      return random.random()
    }

    print(myFunc())
    ```

    Nesting lambdas is supported and has the expected semantics except if used in comprehensions
    (as they introduce a new scope that can not be captured by the function definition that is
    a multi-line lambda is transpiled to).

2. **Macros**

    Macros are plugins that can be enabled in the Kahmi DSL parser to implement custom parsing
    logic following a macro identifier. The Kahmi DSL parser comes with a YAML plugin out of the
    box:

    ```python
    buildscript {
      dependencies = !yaml {
        - kahmi-git
        - kahmi-python
      }
    }
    ```

3. **Dynamic name lookup**

    Names are resolved slightly different in Kahmi Python expressions. The local scope will always
    be resolved first. Subsequently, the current context object's members are checked, then the
    parent closure's local variables and context object, etc. Then finally, the global variables
    and builtins.

    ```python
    dependencies = ["kahmi-python"]
    print(dependencies)
    print('dependencies' in locals())
    print('dependencies' in vars(self))
    ```

    > __Explanation__: The property assignment sets the `dependencies` attribute on the current
    > context object. Looking up the variable will first search it in the locals, but not find it
    > there and subsequently find it in the context object (also referrable to as `self`).

## Built-ins

Kahmi only provides two additional built-in functions on top of what is provided by Python, and
they are only necessary for the execution of Kahmi's generated Python code.

| Name | Description |
| ---- | ----------- |
| `self` | The root context object for the script. |
| `__lookup__(name, locals_, ctx)` | Helper function to resolve the targets of call blocks. |

## Under the hood

Kahmi comes with a simple cli that allows you to run any Kahmi script, but given the limited
ability to override the root context object it is expected that it does not serve much use outside
of debugging and development.

    $ python -m kahmi.dsl examples/hello.kmi

Using the `-E` option, you can retrieve the Python code that a Kahmi file is transpiled to. This
is especially useful to understand how Kahmi constructs are converted into Python. Below are some
examples:

```python
let msg = (name) => {
  return 'Hello, ' + name
}('World')

print(msg)
```

```python
def lambda_stdin_1_10(name):
    return 'Hello, ' + name


msg = lambda_stdin_1_10('World')
__runtime__['print'](msg)
```

---

```python
buildscript {
  dependencies = ["kahmi-python"]
}
```

```python
@__runtime__.closure()
def __configure_buildscript(self):
    self.dependencies = ['kahmi-python']


__configure_buildscript_self_target = __runtime__['buildscript']
with __runtime__.pushing(__runtime__['locals']()):
    if __runtime__['hasattr'](__configure_buildscript_self_target, 'configure'):
        __configure_buildscript_self_target.configure(__configure_buildscript)
    else:
        __configure_buildscript_self_target(__configure_buildscript)
```

---

<p align="center">Copyright &copy; 2021 Niklas Rosenstein</p>
