"""
The :class:`Context` class is the main entry point for using the BuildDSL package.
"""

from pathlib import Path
from typing import Any, Callable, Dict, Mapping, TextIO, cast

from builddsl.closure import ClosureState
from builddsl.targets import ObjectTarget, Target
from builddsl.transpiler import TranspileOptions, transpile_to_ast, transpile_to_source


class Context:
    """
    This class provides the APIs to define the context in which BuildDSL code is executed.
    """

    OPTIONS = TranspileOptions(
        closure_target="__closure__",
        closure_def_prefix="@__closure__.definition\n",
        closure_arglist_prefix="__closure__,",
    )

    def __init__(self, target: Target, target_factory: Callable[[Any], Target] = ObjectTarget) -> None:
        """
        :param target: The main target for the global scope of the BuildDSL code. Any names references on the
            global scope will be resolved in this target. Frequently a :class:`MutableMappingTarget` is used
            for the top-level target.
        :param target_factory: A factory function that creates a new :class:`Target` for any object that is
            passed as the target of a BuildDSL closure (i.e. its first argument). The default is the
            :class:`ObjectTarget` class which serves as a proxy for the members of an object.
        """

        self.target = target
        self.target_factory = target_factory

    def exec(self, code: str, filename: "str | Path" = "<string>") -> None:
        """
        Execute a piece of BuildDSL code.

        :param code: The code to execute.
        :param filename: The filename of the code. This is used in case errors occur.
        """

        module = transpile_to_ast(code, str(filename), self.OPTIONS)
        scope = {}
        assert self.OPTIONS.closure_target is not None
        scope[self.OPTIONS.closure_target] = ClosureState(None, None, self.target, self.target_factory)
        exec(compile(module, str(filename), "exec"), scope)

    @classmethod
    def transpile(cls, code: str, filename: "str | Path" = "<string>") -> str:
        """
        Transpile a piece of BuildDSL code to Python code.

        Note that this requires the `astor` package which is not installed by default.

        :param code: The code to transpile to pure Python code.
        :param filename: The filename of the code. This is used for error messages.
        """

        return transpile_to_source(code, str(filename), cls.OPTIONS)


def execute(
    code: "str | TextIO",
    filename: "str | Path | None" = None,
    globals: "Dict[str, Any]  | None" = None,
    locals: "Mapping[str, Any] | None" = None,
    options: "TranspileOptions | None" = None,
) -> None:
    """
    Executes BuildDSL code in the context specified with *globals* and *locals*.

    :param code: The code to execute.
    :param filename: The filename where the code is from; shown in errors.
    :param globals: The globals for the code.
    :param locals: The locals for the code.
    :param options: Options for the DSL transpiler.
    """

    if hasattr(code, "read"):
        code = cast(TextIO, code).read()
        filename = getattr(code, "name", None)

    assert isinstance(code, str)
    filename = filename or "<string>"

    if globals is None:
        globals = {}
    if locals is None:
        locals = globals

    ast = transpile_to_ast(code, str(filename), options)
    compiled_code = compile(ast, str(filename), "exec")
    exec(compiled_code, globals, locals)
