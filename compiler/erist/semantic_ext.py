from __future__ import annotations

from .diagnostics import SemanticError
from .stdlib import UNICODE_FUNCTIONS, PROCESS_FUNCTIONS
from .semantic import Analyzer as BaseAnalyzer, STD_FILE_ERROR, STD_FILE
from .syntax import CallExpr, ForStmt, IndexExpr, MemberExpr, NameExpr
from .typesys import (
    BOOL,
    INT,
    NO_VALUE,
    TEXT,
    TEXT_BYTES,
    TEXT_CHARACTERS,
    TEXT_SCALARS,
    ListType,
    NoValueType,
    NamedType,
    TextViewType,
    TypeVar,
    resolve,
    unify,
)


class Analyzer(BaseAnalyzer):
    """Frontend extensions for pinned Unicode/Text and small stdlib additions."""

    def _statement(self, stmt):
        if isinstance(stmt, ForStmt):
            raw_iterable = self._expr(stmt.iterable, True, False)
            iterable = resolve(raw_iterable)
            if isinstance(iterable, TypeVar):
                element = TypeVar("element")
                unify(raw_iterable, ListType(element))
        return super()._statement(stmt)

    def _member(self, expr, allow_checked):
        bt = resolve(self._expr(expr.base, True, allow_checked))
        fails = set(self.expr_failures.get(id(expr.base), set()))

        if bt == NamedType(STD_FILE_ERROR) and expr.name in ("message", "path"):
            return self._record(expr, TEXT, fails)

        if bt == TEXT:
            if expr.name == "characters":
                return self._record(expr, TEXT_CHARACTERS, fails)
            if expr.name == "scalars":
                return self._record(expr, TEXT_SCALARS, fails)
            if expr.name == "bytes":
                return self._record(expr, TEXT_BYTES, fails)

        if isinstance(bt, TextViewType):
            if expr.name == "count":
                return self._record(expr, INT, fails)
            raise SemanticError(
                f"Text {bt.kind} view has no member {expr.name!r} in pre-0.1",
                expr.location,
            )

        return super()._member(expr, allow_checked)

    def _call(self, expr: CallExpr, value_required, allow_checked):
        if (isinstance(expr.callee, MemberExpr) and isinstance(expr.callee.base, NameExpr)
                and self.imports.get(expr.callee.base.name) == ("std", "process")):
            contract = PROCESS_FUNCTIONS.get(expr.callee.name)
            if contract is None:
                raise SemanticError(f"unknown std.process function {expr.callee.name!r}", expr.location)
            parameters, result = contract
            if len(expr.arguments) != len(parameters):
                raise SemanticError(f"process.{expr.callee.name} expects {len(parameters)} argument(s)", expr.location)
            failures = set()
            for argument, expected in zip(expr.arguments, parameters):
                self._require_type(self._expr(argument, True, allow_checked), expected, argument.location,
                                   f"process.{expr.callee.name} argument has the wrong type")
                failures |= self.expr_failures.get(id(argument), set())
            if value_required and result == NO_VALUE:
                raise SemanticError("a no-value function call cannot be used where a value is required", expr.location)
            return self._record(expr, result, failures)

        if (isinstance(expr.callee, MemberExpr) and isinstance(expr.callee.base, NameExpr)
                and self.imports.get(expr.callee.base.name) == ("std", "files")
                and expr.callee.name in ("openRead", "create", "canonicalPath")):
            if len(expr.arguments) != 1:
                raise SemanticError(f"files.{expr.callee.name} expects one Text path", expr.location)
            argument = expr.arguments[0]
            self._require_type(self._expr(argument, True, allow_checked), TEXT, argument.location,
                               "file path requires Text")
            if not allow_checked:
                raise SemanticError(f"files.{expr.callee.name} may fail; handle it or use try", expr.location)
            return self._record(expr, TEXT if expr.callee.name == "canonicalPath" else STD_FILE, {STD_FILE_ERROR} | self.expr_failures.get(id(argument), set()))

        if (isinstance(expr.callee, MemberExpr)
                and isinstance(expr.callee.base, NameExpr)
                and self.imports.get(expr.callee.base.name) == ("std", "unicode")):
            contract = UNICODE_FUNCTIONS.get(expr.callee.name)
            if contract is None:
                raise SemanticError(f"unknown std.unicode function {expr.callee.name!r}", expr.location)
            argument_type, result_type = contract
            if len(expr.arguments) != 1:
                raise SemanticError(f"unicode.{expr.callee.name} requires one argument", expr.location)
            argument = expr.arguments[0]
            actual = self._expr(argument, True, allow_checked)
            self._require_type(actual, argument_type, argument.location,
                               f"unicode.{expr.callee.name} requires {argument_type.name}")
            return self._record(expr, result_type, self.expr_failures.get(id(argument), set()))

        if (
            isinstance(expr.callee, MemberExpr)
            and isinstance(expr.callee.base, NameExpr)
            and expr.callee.base.name in self.imported_modules
        ):
            mod = self.imported_modules[expr.callee.base.name]
            fn = mod.analyzer.functions.get(expr.callee.name)
            if fn is None or not fn.declaration.public:
                raise SemanticError(
                    f"module {expr.callee.base.name!r} does not expose public function {expr.callee.name!r}",
                    expr.location,
                )
            if len(expr.arguments) != len(fn.typed_parameters):
                raise SemanticError(
                    f"function {expr.callee.name!r} expects {len(fn.typed_parameters)} argument(s), got {len(expr.arguments)}",
                    expr.location,
                )
            args = []
            failures = set()
            for i, (argument, declared_type) in enumerate(zip(expr.arguments, fn.typed_parameters), 1):
                actual_type = self._argument_type(argument, declared_type, allow_checked)
                failures |= self.expr_failures.get(id(argument), set())
                if declared_type is not None:
                    self._assign_or_error(declared_type, actual_type, argument.location, f"argument {i}")
                    args.append(declared_type)
                else:
                    args.append(actual_type)
            failures |= fn.fails
            if fn.fails and not allow_checked:
                raise SemanticError(
                    f"call to {expr.callee.base.name}.{expr.callee.name} may fail with {', '.join(sorted(fn.fails))}; handle it or use try",
                    expr.location,
                )
            result_type = mod.analyzer._ensure_function(fn, args, value_required)
            if value_required and isinstance(resolve(result_type), NoValueType):
                raise SemanticError("a no-value function call cannot be used where a value is required", expr.location)
            return self._record(expr, result_type, failures)

        if (
            isinstance(expr.callee, MemberExpr)
            and isinstance(expr.callee.base, NameExpr)
            and expr.callee.base.name in self.imports
            and self.imports[expr.callee.base.name] == ("std", "files")
            and expr.callee.name in ("exists", "remove")
        ):
            if len(expr.arguments) != 1:
                raise SemanticError(f"files.{expr.callee.name}(path) takes one Text argument", expr.location)
            path_type = self._expr(expr.arguments[0], True, allow_checked)
            self._require_type(path_type, TEXT, expr.arguments[0].location, f"files.{expr.callee.name}(path) requires Text")
            failures = {STD_FILE_ERROR}
            if not allow_checked:
                raise SemanticError(
                    f"files.{expr.callee.name}(path) may fail with std.files.FileError; handle it with 'else error' or propagate it with 'try'",
                    expr.location,
                )
            return self._record(expr, BOOL if expr.callee.name == "exists" else NO_VALUE, failures)
        return super()._call(expr, value_required, allow_checked)

    def _expr(self, expr, value_required=True, allow_checked=False):
        if isinstance(expr, IndexExpr):
            raw_bt = self._expr(expr.base, True, allow_checked)
            bt = resolve(raw_bt)
            if isinstance(bt, TextViewType):
                it = self._expr(expr.index, True, allow_checked)
                self._require_type(
                    it,
                    INT,
                    expr.index.location,
                    "Text view index must have static type Int",
                )
                fails = (
                    set(self.expr_failures.get(id(expr.base), set()))
                    | set(self.expr_failures.get(id(expr.index), set()))
                )
                result = INT if bt.kind == "bytes" else TEXT
                return self._record(expr, result, fails)
        return super()._expr(expr, value_required, allow_checked)

    def _target_type(self, target, for_write=False):
        if isinstance(target, IndexExpr):
            raw_bt = self._expr(target.base, True, False)
            bt = resolve(raw_bt)
            if isinstance(bt, TextViewType):
                self._require_type(
                    self._expr(target.index, True, False),
                    INT,
                    target.index.location,
                    "Text view index must have static type Int",
                )
                if for_write:
                    raise SemanticError("Text views are read-only", target.location)
                return INT if bt.kind == "bytes" else TEXT

            if isinstance(bt, TypeVar):
                element = TypeVar("element")
                shaped = ListType(element)
                unify(raw_bt, shaped)
                self._require_type(
                    self._expr(target.index, True, False),
                    INT,
                    target.index.location,
                    "List index must have type Int",
                )
                return element

        if isinstance(target, MemberExpr):
            bt = resolve(self._expr(target.base, True, False))
            if isinstance(bt, TextViewType):
                raise SemanticError("Text views are read-only", target.location)
        return super()._target_type(target, for_write)

    def _deep_fixable(self, t, seen):
        if isinstance(resolve(t), TextViewType):
            return True
        return super()._deep_fixable(t, seen)
