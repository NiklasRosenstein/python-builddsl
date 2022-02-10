# Function calls without parentheses

Such function calls are only supported at the statement level. A function can be called without parentheses by
simply omitting them. Variadic and keyword arguments are supported as expected. Applying a closure on an object
is basically the same as calling that object with the function, and arguments following the closure are still
supported.


<table align="center"><tr><th>Craftr DSL</th><th>Python</th></tr>

<tr><td>

```py
print 'Hello, World!', file=sys.stderr
```
</td><td>

```py
print('Hello, World!', file=sys.stderr)
```
</td></tr>


<tr><td>

```py
map {
  print('Hello,', self)
}, ['John', 'World']
```
</td><td>

```py
def _closure_1(self, *arguments, **kwarguments):
    print('Hello,', self)
map(_closure_1, ['John', 'World'])
```
</td></tr>

</table>
