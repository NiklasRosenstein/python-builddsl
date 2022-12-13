# Limitations

BuildDSL is intended to behave as a complete syntactic superset of standard Python. However there are currently
some limitations, namely:

* Literal sets cannot be expressed due to the grammar conflict with parameter-less closures
* Type annotations are not currently supported
* The walrus operator is not currently supported
* Function calls without parenthesis do not support passing `*args` as the first argument as that is
  interpreted as a multiplication expression.
