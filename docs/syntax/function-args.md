# Unseparated arguments & colon keyword arguments

The Craftr DSL allows passing arguments to function calls without separation by commas.
Keyword arguments may be specified using colons (`:`) instead of equal signs (`=`).

<table>

<tr><th>Craftr DSL</th><th>Python</th></tr>

<tr><td>

```py
print 'Hello, World!' 42 * 1 + 10 file: sys.stdout
```
</td><td>

```py
print('Hello, World!', 42 * 1 + 10, file=sys.stdout)
```
</td></tr>


<tr><td>

```py
task "hello_world" do: {
  print "Hello, World!"
}
```
</td><td>

```py
def _closure_1(self, *arguments, **kwarguments):
    print('Hello, World!')
task('hello_world', do=_closure_1)
```
</td></tr>


<tr><td>

```py
list(map {
  print('Hello,', self)
}, ['John', 'World'])
```

> **Note**: Pitfall, this actually passes three arguments to `list()`.
</td><td>

```py
def _closure_1(self, *arguments, **kwarguments):
    print('Hello,', self)
list(map, _closure_1, ['John', 'World'])
```
</td></tr>

</table>
