# Quickstart

A convoluted Hello, World! example in Craftr DSL might look like this:

```py
# hello.craftr
world = { self('World!') }
world { print('Hello,', self) }
```

This is transpiled to

```py
# $ python -m craftr.dsl hello.craftr -E | grep -v -e '^$'
def _closure_1(self, *arguments, **kwarguments):
    self('World!')
world = _closure_1
def _closure_2(self, *arguments, **kwarguments):
    print('Hello,', self)
world(_closure_2)
```

And evaluates to

```py
# $ python -m craftr.dsl hello.craftr
Hello, World!
```
