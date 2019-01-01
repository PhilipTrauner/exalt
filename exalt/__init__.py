from types import CodeType, FunctionType
from ctypes import pythonapi, py_object
from dis import _get_name_info
from opcode import opmap, HAVE_ARGUMENT, EXTENDED_ARG
from struct import pack
from typing import Callable, Any, List

# Fetch a reference to the code type from a non-built-in function
CODE_TYPE = type(_get_name_info.__code__)

# Define the opcodes that are going to be swapped
LOAD_GLOBAL = opmap["LOAD_GLOBAL"]
LOAD_DEREF = opmap["LOAD_DEREF"]

# Length of CPython VM instructions (in bytes)
UNPACK_STEP = 2
# Encoding of VM instructions
FORMAT = "BB"

# Fetch reference to cell creation function
_PyCell_New = pythonapi.PyCell_New
# PyCell_New returns a py_object
_PyCell_New.restype = py_object

# CPython internals relevant to function execution
CO_OPTIMIZED = 0x0001
CO_NEWLOCALS = 0x0002
CO_NESTED = 0x0010

__all__ = ["promote", "UnsupportedCallableError", "ShadowingConstantsError"]


class UnsupportedCallableError(TypeError):
    def __init__(self, closure: Callable):
        super().__init__(f"closures that reference cells are not supported ({closure})")


class ShadowingConstantsError(TypeError):
    def __init__(self):
        super().__init__(f"shadowing constants is not yet supported")


def _new_cell(object: Any):
    """Cells are used to give closures access to the scope they were defined in.
    They can not be created without calling into CPython internals.
    """
    return _PyCell_New(py_object(object))


def _unpack_opargs(code: CODE_TYPE):
    """Lifted directly from dis module.
    Extended to also yield the packed instruction.
    """
    extended_arg = 0
    for i in range(0, len(code), UNPACK_STEP):
        op = code[i]
        if op >= HAVE_ARGUMENT:
            arg = code[i + 1] | extended_arg
            extended_arg = (arg << 8) if op == EXTENDED_ARG else 0
        else:
            arg = None
        yield (i, op, arg, code[i : i + UNPACK_STEP])


def _patch_load_global(
    code: CODE_TYPE, override: List[str], varnames: List[str], names: List[str]
):
    """Replaces LOAD_GLOBAL opcodes with LOAD_DEREF opcodes.
    LOAD_DEREF is used to access cell objects.
    """
    for _, op, arg, packed in _unpack_opargs(code):
        argval = None

        if arg is not None:
            if op == LOAD_GLOBAL:
                # Only override instructions that load variables supplied by the namespace
                argval, _ = _get_name_info(arg, names)
                if argval in override:
                    # To-Do: Ensure EXTENDED_ARG support
                    op = LOAD_DEREF
                    packed = pack(FORMAT, LOAD_DEREF, override.index(argval))

        yield packed


def promote(callable_: Callable, **kwargs):
    # Functions that are already closures are not supported.
    if callable_.__closure__ is not None:
        raise UnsupportedCallableError(callable_)

    callable_code = callable_.__code__

    # Create cell vars for given namespace
    cell_var_names = tuple((key for key in kwargs))
    cell_vars = tuple((_new_cell(kwargs[arg]) for arg in kwargs))

    # Do not allow overriding of variables that were defined in the supplied function.
    if any(name in callable_code.co_varnames for name in cell_var_names):
        raise ShadowingConstantsError()

    # Rewrite function bytecode
    patched_code = b"".join(
        _patch_load_global(
            callable_code.co_code,
            cell_var_names,
            callable_code.co_varnames,
            callable_code.co_names,
        )
    )

    # Construct the new function
    func = FunctionType(
        CodeType(
            callable_code.co_argcount,
            callable_code.co_kwonlyargcount,
            callable_code.co_nlocals,
            callable_code.co_stacksize,
            CO_OPTIMIZED | CO_NEWLOCALS | CO_NESTED,
            patched_code,
            callable_code.co_consts,
            tuple(
                (name for name in callable_code.co_names if name not in cell_var_names)
            ),
            cell_var_names,
            callable_code.co_filename,
            callable_code.co_name,
            callable_code.co_firstlineno,
            callable_code.co_lnotab,
            cell_var_names,
            (),
        ),
        callable_.__globals__,
        callable_code.co_name,
        (),
        cell_vars,
    )

    return func
