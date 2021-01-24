# kahmi-dsl

Kahmi is a build system and DSL for Python heavily inspired by Groovy and Gradle. The `kahmi-dsl`
package implements the parser and transpiler for the Kahmi language.

## Syntax

The Kahmi DSL might look familar to you if you have used Groovy before. While not any Python code
is valid Kahmi DSL code, the full Python language is supported in various places. Additionally,
Kahmi DSL allows you to define multi-line lambdas inline with full Python code.

Every Kahmi file starts with a "context" object. There are four main syntactical elements that
are supported by the Kahmi language:

* `let` definitions for local variables
* member assignments to the current context
* calls and call blocks
* Python expressions (with multi-line lambda support)

```python
let re = __import__('re')

msg = "Hello, World!"

print(re.sub(r'[,!]', '', self.msg))  # prints: Hello World

re.sub(r'[A-z ]', '', self.msg) {
  print(self)  # prints: ,!
}
```

You can transpile it into Python code to see what's going on under the hood:

```
$ python -m kahmi.dsl build.kahmi   -E
re = __import__('re')
self.msg = 'Hello, World!'
__lookup__('print', locals(), self)(re.sub('[,!]', '', self.msg))


def __call_re_sub(self):
    __lookup__('print', locals(), self)(self)


value = __lookup__('re', locals(), self).sub('[A-z ]', '', self.msg)
__call_re_sub(value)
```

What you see as *self* here is the current "context" object and `__lookup__()` is a helper
that allows you to call local variables, members of the context or builtins.

### Lambdas

Lambdas are implemented by placing function definitions for you before they are used. Lambdas
can be nested and they are properly taking the right scope in most cases (exceptions are Python
expressions that introduce a new scope like generator, tuple, list, set and dict comprehensions).

```python
let myFunc = () => {
  return name => { return f'Hello, {name}' }
}

myFunc() {
  print(self('Sam'))  # prints: Hello, Sam
}
```

Again, transpiling into pure Python code help to understand what is going on:

```python
ef lambda_build_kahmi_1_13():

    def lambda_build_kahmi_2_8(name):
        return f'Hello, {name!r}'
    return lambda_build_kahmi_2_8


myFunc = lambda_build_kahmi_1_13


def __call_myFunc(self):
    __lookup__('print', locals(), self)(self('Sam'))


value = __lookup__('myFunc', locals(), self)()
__call_myFunc(value)
```

## CLI

The command-line interface for the `kahmi-dsl` package is very simplistic. It is not expected that
it provides much value outside of development as it only provides a limited method of building
and passing the root context object to the script.

```
usage: python -m kahmi.dsl [-h] [-c ENTRYPOINT] [-E] [file]

positional arguments:
  file

optional arguments:
  -h, --help            show this help message and exit
  -c ENTRYPOINT, --context ENTRYPOINT
  -E, --transpile
```

If no `-c,--context` is provided a `kahmi.dsl.__main__.VoidContext` object is used which is really
just an instance of an empty class.

---

<p align="center">Copyright &copy; 2021 Niklas Rosenstein</p>
