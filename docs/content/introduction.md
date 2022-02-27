# Introduction

Craftr DSL is a Python superset language inspired by Gradle. It was designed for as the main configuration language
for the [Craftr build system](https://github.com/craftr-build). Albeit as of writing this (Feb 27, 2022), the Craftr
build system itself is not mature, the DSL is relatively stable.

It introduces additional syntactic constructs into the language, such as paren-less function calls, colon keyword
arguments, paren-less line-spanning statements without newline escaping and multi-line lambdas (called "closures").

Optionally, a feature can be enabled to allow for dynamic variable name resolution which allows for a concise syntax
that does not require prefixing members of the closure target with `self`.

## Example

This might be a bit of a convoluted way to print "Hello, World", but it shows well how closures in Craftr DSL work:

```py
# hello.craftr
world = { self('World!') }
world {
  print('Hello,', self)
}
```

This transpiles to

=== "Standard"

    ```py
    # $ python -m craftr.dsl hello.craftr -E | grep -v -e '^$'
    def _closure_1(self, *arguments, **kwarguments):
        self('World!')
    world = _closure_1
    def _closure_2(self, *arguments, **kwarguments):
        print('Hello,', self)
    world(_closure_2)
    ```

=== "Dynamic name resolution"

    ```py
    # $ python -m craftr.dsl hello.craftr -E -C | grep -v -e '^$'
    @__closure__.child
    def _closure_1(__closure__, self, *arguments, **kwarguments):
        self('World!')
    __closure__['world'] = _closure_1
    @__closure__.child
    def _closure_2(__closure__, self, *arguments, **kwarguments):
        __closure__['print']('Hello,', self)
    __closure__['world'](_closure_2)
    ```

And evaluates to

```py
# $ python -m craftr.dsl hello.craftr
Hello, World!
```

!!! note

    Craftr DSL is not usually designed to be used for standalone scripts, but usually as a configuration language
    for other systems. It is therefore uncommon to run any production code through `python -m craftr.dsl`. Code
    transpiled using **dynamic name resolution** requires a root closure to be supplied as well, which is not possible
    via the command-line.

    However, the command-line interface is very useful to run quick tests and to inspect what the transpiled version
    of the code looks like.
