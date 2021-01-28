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

The Kahmi DSL basically wraps Python code and even extends it's normal syntax with **multiline
lambdas**.

Every Kahmi script is executed in a given "context", that can be an arbitrary Python object which
is addressable in Python expressions as "self". There are 3 different types of operations one can
perform. Entering a Python expression or multiline lambda reverts the parser back into full Python
mode (with the aforementioned multiline lambda support).

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

4. **Multi-line lambdas**

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

5. **Macros**

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
__lookup__('print', locals(), self)(msg)
```

---

```python
buildscript {
  dependencies = ["kahmi-python"]
}
```

```python
def __configure_buildscript(self):
    self.dependencies = ['kahmi-python']


__configure_buildscript_self_target = __lookup__('buildscript', locals(), self)
if hasattr(__configure_buildscript_self_target, 'configure'):
    __configure_buildscript_self_target.configure(__configure_buildscript)
else:
    __configure_buildscript_self_target(__configure_buildscript)
```

---

<p align="center">Copyright &copy; 2021 Niklas Rosenstein</p>
