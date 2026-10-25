"""Fail closed at backend boundaries until Map/Bytes representations are implemented."""
from dataclasses import fields, is_dataclass

from .diagnostics import SemanticError
from .ir import IRFunction
from .ir_collections import IRBytes, IRCollectionIndexAssign, IRMap


def require_collection_codegen(program, backend):
    def unsupported(type_name):
        return isinstance(type_name, str) and (
            "Bytes" in type_name.split() or "Map from " in type_name
        )

    def reject(location):
        raise SemanticError(
            f"Map/Bytes code generation is not yet supported by the {backend} backend; "
            "collection parsing, analysis and reference execution remain experimental",
            location,
        )

    def visit(value):
        if isinstance(value, (IRMap, IRBytes, IRCollectionIndexAssign)):
            reject(value.location)
        if isinstance(value, (tuple, list)):
            for item in value:
                visit(item)
        elif is_dataclass(value):
            for name in ("type_name", "return_type", "base_type"):
                if unsupported(getattr(value, name, None)):
                    reject(getattr(value, "location", None))
            if isinstance(value, IRFunction):
                for parameter in value.parameters:
                    if unsupported(parameter.type_name):
                        reject(getattr(value, "location", None))
            for field in fields(value):
                visit(getattr(value, field.name))

    visit(program)
