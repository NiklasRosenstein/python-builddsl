# API Documentation

This is the API documentation for the `craftr-dsl` package.

## High-level API

The high-level #execute() API is what you'd be using most of the time. It is comparable to the Python built-in
#exec() function in that it takes the code to execute, a scope and compile options and will execute the code, only
that this will first transpile Craftr DSL code to pure Python.

@pydoc craftr.dsl.execute

@pydoc craftr.dsl.TranspileOptions
