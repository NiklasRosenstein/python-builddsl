# Unseparated arguments & colon keyword arguments

The Craftr DSL allows passing arguments to function calls without separation by commas.
Keyword arguments may be specified using colons (`:`) instead of equal signs (`=`).

## Example 1

=== "Craftr DSL"

    ```py
    print 'Hello, World!' 42 * 1 + 10 file: sys.stdout
    ```

=== "Python"

    ```py
    print('Hello, World!', 42 * 1 + 10, file=sys.stdout)
    ```

## Example 2

=== "Craftr DSL"

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

=== "Craftr DSL"

    ```py
    list(map {
      print('Hello,', self)
    }, ['John', 'World'])
    ```

=== "Python"

    ```py
    def _closure_1(self, *arguments, **kwarguments):
        print('Hello,', self)
    list(map, _closure_1, ['John', 'World'])
    ```

> **Note**: Pitfall, this actually passes three arguments to `list()`.
