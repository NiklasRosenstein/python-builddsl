# Unseparated arguments & colon keyword arguments

The BuildDSL allows passing arguments to function calls without separation by commas.
Keyword arguments may be specified using colons (`:`) instead of equal signs (`=`).

## Example 1

=== "BuildDSL"

    ```py
    print 'Hello, World!' 42 * 1 + 10 file: sys.stdout
    ```

=== "Python"

    ```py
    print('Hello, World!', 42 * 1 + 10, file=sys.stdout)
    ```

## Example 2

=== "BuildDSL"

    ```py
    task "hello_world" do: {
      print "Hello, World!"
    }
    ```

=== "Python"

    ```py
    def _closure_1(self, *arguments, **kwarguments):
        print('Hello, World!')
    task('hello_world', do=_closure_1)
    ```

## Example 3

=== "BuildDSL"

    ```py
    list(map { print('Hello,', self) } ['John', 'World'])
    ```

=== "Python"

    ```py
    def _closure_1(self, *arguments, **kwarguments):
        print('Hello,', self)
    list(map, _closure_1['John', 'World'])
    ```

!!! danger Pitfall

    Note how this actually passes all arguments to `list()` and it tries to index an element on the closure.
    The outer-most statement has the priority to receive the arguments, and subscripting takes precedence over
    the subscript being treated as a separate argument.

=== "BuildDSL"

    ```py
    list(map({ print('Hello,', self) }, ['John', 'World']))
    ```

=== "Python"

    ```py
    def _closure_1(self, *arguments, **kwarguments):
        print('Hello,', self)

    list(map(_closure_1['John', 'World']))
    ```
