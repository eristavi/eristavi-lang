from __future__ import annotations

from dataclasses import dataclass
import os
import sys

from .diagnostics import RuntimeFault
from .runtime import (
    CheckedFailure,
    FileResource,
    ListValue,
    Interpreter as BaseInterpreter,
    NO_RUNTIME,
    copy_value,
    file_error,
)
from .syntax import CallExpr, FunctionDecl, IndexExpr, MemberExpr, NameExpr
from .unicode_support import (grapheme_clusters, scalar_texts, utf8_bytes,
                              is_xid_start, is_xid_continue, normalize_nfc)


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


@dataclass
class ProcessState:
    arguments: tuple[str, ...] = ()
    exit_code: int = 0
    error_sink: object = None


class Interpreter(BaseInterpreter):
    """Bootstrap runtime extensions for pinned Unicode/Text and stdlib operations."""

    def __init__(self, output=print, module_id="", imported_modules=None, *, arguments=(), process_state=None, error_output=None):
        super().__init__(output, module_id, imported_modules)
        self.process_state = process_state if process_state is not None else ProcessState(tuple(arguments), 0, error_output or (lambda text: print(text, file=sys.stderr)))

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
        if (isinstance(e.callee, MemberExpr) and isinstance(e.callee.base, NameExpr)
                and self.imports.get(e.callee.base.name) == ("std", "process")):
            if e.callee.name == "arguments":
                try:
                    for value in self.process_state.arguments:
                        value.encode("utf-8")
                except UnicodeError:
                    raise RuntimeFault("process arguments must be valid UTF-8", e.location)
                return ListValue(list(self.process_state.arguments))
            if e.callee.name == "writeError":
                self.process_state.error_sink(self._expr(e.arguments[0]))
                return NO_RUNTIME
            code = self._expr(e.arguments[0])
            if not 0 <= code <= 255:
                raise RuntimeFault("process exit code must be between 0 and 255", e.location)
            self.process_state.exit_code = code
            return NO_RUNTIME

        if (isinstance(e.callee, MemberExpr) and isinstance(e.callee.base, NameExpr)
                and self.imports.get(e.callee.base.name) == ("std", "files")
                and e.callee.name in ("openRead", "create", "canonicalPath")):
            path = self._expr(e.arguments[0])
            try:
                if e.callee.name == "canonicalPath":
                    return os.path.realpath(path, strict=True)
                mode = "r" if e.callee.name == "openRead" else "x+"
                resource = FileResource(path, open(path, mode, encoding="utf-8", newline=""))
                resource.writable = e.callee.name == "create"
                return resource
            except (OSError, ValueError, UnicodeError) as error:
                raise CheckedFailure(file_error(str(error), path))

        if (isinstance(e.callee, MemberExpr)
                and isinstance(e.callee.base, NameExpr)
                and self.imports.get(e.callee.base.name) == ("std", "unicode")):
            value = self._expr(e.arguments[0])
            name = e.callee.name
            if name == "isIdentifierStart":
                return value == "_" or is_xid_start(value)
            if name == "isIdentifierContinue":
                return value == "_" or is_xid_continue(value)
            if name == "normalizeNfc":
                return normalize_nfc(value)
            if name == "fromScalar":
                if value < 0 or value > 0x10FFFF or 0xD800 <= value <= 0xDFFF:
                    raise RuntimeFault("invalid Unicode scalar value", e.location)
                return chr(value)
            raise RuntimeFault(f"unknown std.unicode function {name!r}", e.location)

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
            child = type(self)(self.output_sink, mod.module_id, mod.imports, process_state=self.process_state)
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
                        if not getattr(base, "writable", True):
                            raise CheckedFailure(file_error("file was opened read-only", base.path))
                        text = self._expr(e.arguments[0])
                        base.handle.seek(0)
                        base.handle.write(text)
                        base.handle.truncate()
                        base.handle.flush()
                        return NO_RUNTIME
                except (OSError, UnicodeError) as ex:
                    raise CheckedFailure(file_error(str(ex), base.path))
        return super()._call(e)