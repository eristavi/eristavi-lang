from __future__ import annotations

from dataclasses import dataclass
import os

from .diagnostics import RuntimeFault
from .runtime import (
    CheckedFailure,
    FileResource,
    Interpreter as BaseInterpreter,
    NO_RUNTIME,
    copy_value,
    file_error,
)
from .syntax import CallExpr, FunctionDecl, IndexExpr, MemberExpr, NameExpr
from .unicode_support import grapheme_clusters, scalar_texts, utf8_bytes


@dataclass(frozen=True)
class TextViewValue:
    kind: str
    text: str

    def items(self):
        if self.kind == "characters":
            return grapheme_clusters(self.text)
        if self.kind == "scalars":
            return scalar_texts(self.text)
        if self.kind == "bytes":
            return utf8_bytes(self.text)
        raise RuntimeFault(f"unknown Text view {self.kind!r}")


class Interpreter(BaseInterpreter):
    """Bootstrap runtime extensions for pinned Unicode/Text and stdlib operations."""

    def _member_value(self, e):
        base = self._expr(e.base)
        if isinstance(base, str) and e.name in ("characters", "scalars", "bytes"):
            return TextViewValue(e.name, base)
        if isinstance(base, TextViewValue):
            if e.name == "count":
                return len(base.items())
            raise RuntimeFault(
                f"Text {base.kind} view has no member {e.name!r} in pre-0.1",
                e.location,
            )
        return super()._member_value(e)

    def _expr(self, e):
        if isinstance(e, IndexExpr):
            base = self._expr(e.base)
            if isinstance(base, TextViewValue):
                idx = self._expr(e.index)
                items = base.items()
                if idx < 0 or idx >= len(items):
                    raise RuntimeFault("Text view index out of bounds", e.location)
                return copy_value(items[idx])
        return super()._expr(e)

    def _call(self, e: CallExpr):
        if (
            isinstance(e.callee, MemberExpr)
            and isinstance(e.callee.base, NameExpr)
            and e.callee.base.name in self.imported_modules
        ):
            mod = self.imported_modules[e.callee.base.name]
            fn = next(
                (
                    item
                    for item in mod.program.statements
                    if isinstance(item, FunctionDecl)
                    and item.name == e.callee.name
                    and item.public
                ),
                None,
            )
            if fn is None:
                raise RuntimeFault(
                    f"module {e.callee.base.name!r} has no public function {e.callee.name!r}",
                    e.location,
                )
            child = type(self)(self.output_sink, mod.module_id, mod.imports)
            child._prepare(mod.program)
            return child._call_function(fn, [self._expr(argument) for argument in e.arguments])

        if (
            isinstance(e.callee, MemberExpr)
            and isinstance(e.callee.base, NameExpr)
            and self.imports.get(e.callee.base.name) == ("std", "files")
            and e.callee.name in ("exists", "remove")
        ):
            path = self._expr(e.arguments[0])
            try:
                if "\0" in path:
                    raise ValueError("file path contains NUL")
                if e.callee.name == "exists":
                    try:
                        os.stat(path)
                        return True
                    except FileNotFoundError:
                        return False
                os.remove(path)
                return NO_RUNTIME
            except (OSError, ValueError) as ex:
                raise CheckedFailure(file_error(str(ex), path))

        # The base bootstrap file model uses Python's UTF-8 text decoder. A
        # decode failure is part of files.readText's checked FileError contract,
        # not an uncaught host-language UnicodeDecodeError.
        if isinstance(e.callee, MemberExpr):
            try:
                base = self._eval_ref(e.callee.base)
            except RuntimeFault:
                base = None
            if isinstance(base, FileResource):
                try:
                    if e.callee.name == "readText":
                        base.handle.seek(0)
                        return base.handle.read()
                    if e.callee.name == "writeText":
                        text = self._expr(e.arguments[0])
                        base.handle.seek(0)
                        base.handle.write(text)
                        base.handle.truncate()
                        base.handle.flush()
                        return NO_RUNTIME
                except (OSError, UnicodeError) as ex:
                    raise CheckedFailure(file_error(str(ex), base.path))
        return super()._call(e)