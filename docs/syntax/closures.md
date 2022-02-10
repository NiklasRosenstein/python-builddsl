# Closures

Closures are formed with the following syntax: `[ arg -> | (arg1, arg2, ...) -> ] { body }`. A closure without
an argument list automatically has the signature `(self, *argnames, **kwargnames)`.

<table align="center"><tr><th>Craftr DSL</th><th>Python</th></tr>

<tr><td>

```py
filter({ self % 2 }, range(5))
```
</td><td>

```py
def _closure_1(self, *argnames, **kwargnames):
    self % 2
filter(_closure_1, range(5))
```
</td></tr>


<tr><td>

```py
filter(x -> x % 2, range(5))
```
</td><td>

```py
def _closure_1(x):
    return x % 2
filter(_closure_1, range(5))
```
</td></tr>


<tr><td>

```py
reduce((a, b) -> {
  a.append(b * 2)
  return a
}, [1, 2, 3], [])
```
</td><td>

```py
def _closure_1(a, b):
    a.append(b * 2)
    return a
reduce(_closure_1, [1, 2, 3], [])
```
</td></tr>

</table>
