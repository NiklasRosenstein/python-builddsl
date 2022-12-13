# Closures

Closures are formed with the following syntax: `[ arg -> | (arg1, arg2, ...) -> ] { body }`. A closure without
an argument list automatically has the signature `(self, *argnames, **kwargnames)`.

## Example 1

=== "BuildDSL"

    ```py
    filter({ self % 2 }, range(5))
    ```

=== "Python"

    ```py
    def _closure_1(self, *argnames, **kwargnames):
        self % 2
    filter(_closure_1, range(5))
    ```

!!! note "No return statement"

    Note how a closure surrounded by braces does not have an implicit return statement.

## Example 2

=== "BuildDSL"

    ```py
    filter(x -> x % 2, range(5))
    ```

=== "Python"

    ```py
    def _closure_1(x):
        return x % 2
    filter(_closure_1, range(5))
    ```

## Example 3

=== "BuildDSL"

    ```py
    reduce((a, b) -> {
      a.append(b * 2)
      return a
    }, [1, 2, 3], [])
    ```

=== "Python"

    ```py
    def _closure_1(a, b):
        a.append(b * 2)
        return a
    reduce(_closure_1, [1, 2, 3], [])
    ```

