from __future__ import annotations

from dataclasses import dataclass

from .diagnostics import ParseError, RuntimeFault, SemanticError
from .lexer import TokenKind
from .parser import Parser
from . import runtime as runtime_base
from .runtime import Interpreter as BaseInterpreter, ListValue, UserValue, IdentityValue, FileResource, Cell, ReturnSignal, NO_RUNTIME, NONE
from .semantic import Analyzer as BaseAnalyzer
from .syntax import (
    AssignStmt,
    CallExpr,
    ConstructionExpr,
    IndexExpr,
    LetStmt,
    ListExpr,
    LiteralExpr,
    MapEntry,
    MapExpr,
    MemberExpr,
    NameExpr,
    ReturnStmt,
)
from .typesys import (
    BOOL,
    BYTES,
    INT,
    NO_VALUE,
    TEXT,
    IdentityType,
    ListType,
    MapType,
    NamedType,
    NoValueType,
    ResourceType,
    TypeVar,
    describe,
    resolve,
    unify,
)


@dataclass
class BytesValue:
    data: bytearray


@dataclass
class MapValue:
    # Stable insertion order is observable through output and future iteration.
    # Lookup is intentionally representation-independent; the native runtime may
    # replace this bootstrap linear table with hashing without changing semantics.
    entries: list[tuple[object, object]]


def _is_bytes_ref(ref) -> bool:
    return ref is not None and tuple(ref.path) == ("Bytes",) and not ref.maybe and not ref.identity


def _install_parser() -> None:
    if getattr(Parser, "_eristavi_collections_installed", False):
        return
    base_primary = Parser._primary

    def primary(self):
        if not self._match(TokenKind.LBRACKET):
            return base_primary(self)
        loc = self._previous().location

        # Empty List remains []. Empty Map is [:], which is unambiguous while
        # keeping square brackets as the single visual family for collections.
        if self._match(TokenKind.COLON):
            self._consume(TokenKind.RBRACKET, "expected ']' after empty Map literal")
            return MapExpr([], loc)
        if self._match(TokenKind.RBRACKET):
            return ListExpr([], loc)

        first = self._expression()
        if self._match(TokenKind.COLON):
            entries = []
            value = self._expression()
            self._consume(TokenKind.SEMICOLON, "expected ';' after Map entry")
            entries.append(MapEntry(first, value, first.location))
            while not self._check(TokenKind.RBRACKET):
                if self._check(TokenKind.EOF):
                    raise ParseError("unterminated Map literal; expected ']'", loc)
                key = self._expression()
                self._consume(TokenKind.COLON, "expected ':' between Map key and value")
                value = self._expression()
                self._consume(TokenKind.SEMICOLON, "expected ';' after Map entry")
                entries.append(MapEntry(key, value, key.location))
            self._advance()
            return MapExpr(entries, loc)

        elements = [first]
        while self._match(TokenKind.COMMA):
            if self._check(TokenKind.RBRACKET):
                raise ParseError("trailing commas are not part of List literals", self._current().location)
            elements.append(self._expression())
        self._consume(TokenKind.RBRACKET, "expected ']' after List literal")
        return ListExpr(elements, loc)

    Parser._primary = primary
    Parser._eristavi_collections_installed = True


def _install_semantics() -> None:
    if getattr(BaseAnalyzer, "_eristavi_collections_installed", False):
        return

    old_resolve_type_ref = BaseAnalyzer._resolve_type_ref
    old_statement = BaseAnalyzer._statement
    old_expr = BaseAnalyzer._expr
    old_member = BaseAnalyzer._member
    old_call = BaseAnalyzer._call
    old_target_type = BaseAnalyzer._target_type
    old_equality = BaseAnalyzer._equality_comparable
    old_deep_fixable = BaseAnalyzer._deep_fixable
    old_argument_type = BaseAnalyzer._argument_type

    def with_expected(self, expected, action):
        previous = getattr(self, "_collection_expected_type", None)
        self._collection_expected_type = expected
        try:
            return action()
        finally:
            self._collection_expected_type = previous

    def resolve_type_ref(self, ref):
        if ref is not None and tuple(ref.path) == ("Bytes",):
            base = BYTES
            if ref.identity:
                base = IdentityType(base)
            if ref.maybe:
                from .typesys import MaybeType
                base = MaybeType(base)
            return base
        return old_resolve_type_ref(self, ref)

    def statement(self, stmt):
        expected = None
        if isinstance(stmt, LetStmt) and stmt.type_annotation is not None:
            candidate = self._resolve_type_ref(stmt.type_annotation)
            if resolve(candidate) == BYTES:
                expected = BYTES
        elif isinstance(stmt, AssignStmt):
            try:
                candidate = self._target_type(stmt.target, True)
                if resolve(candidate) == BYTES:
                    expected = BYTES
            except SemanticError:
                pass
        elif isinstance(stmt, ReturnStmt) and stmt.value is not None and self.current_function is not None:
            candidate = self.current_function.function.explicit_return
            if candidate is not None and resolve(candidate) == BYTES:
                expected = BYTES
        if expected is not None:
            return with_expected(self, expected, lambda: old_statement(self, stmt))
        return old_statement(self, stmt)

    def infer_bytes(self, expr, allow_checked):
        failures = set()
        for element in expr.elements:
            previous = getattr(self, "_collection_expected_type", None)
            self._collection_expected_type = None
            try:
                element_type = self._expr(element, True, allow_checked)
            finally:
                self._collection_expected_type = previous
            self._require_type(element_type, INT, element.location, "Bytes elements must have static type Int")
            if isinstance(element, LiteralExpr) and element.type_name == "Int" and not 0 <= int(element.value) <= 255:
                raise SemanticError("Bytes literal elements must be between 0 and 255", element.location)
            failures |= self.expr_failures.get(id(element), set())
        return self._record(expr, BYTES, failures)

    @staticmethod
    def valid_map_key(t):
        t = resolve(t)
        if isinstance(t, TypeVar):
            return True
        return isinstance(t, NamedType) and t.name in ("Int", "Bool", "Text")

    def expr(self, expression, value_required=True, allow_checked=False):
        if isinstance(expression, ListExpr):
            known = self.expr_types.get(id(expression))
            expected = resolve(getattr(self, "_collection_expected_type", None)) if getattr(self, "_collection_expected_type", None) is not None else None
            if known is not None and resolve(known) == BYTES:
                return infer_bytes(self, expression, allow_checked)
            if expected == BYTES:
                return infer_bytes(self, expression, allow_checked)

        if isinstance(expression, MapExpr):
            key_type = TypeVar("key")
            value_type = TypeVar("value")
            failures = set()
            literal_keys = set()
            for entry in expression.entries:
                kt = self._expr(entry.key, True, allow_checked)
                vt = self._expr(entry.value, True, allow_checked)
                if isinstance(resolve(kt), (ResourceType, NoValueType)):
                    raise SemanticError("Map keys require ordinary values", entry.key.location)
                if isinstance(resolve(vt), (ResourceType, NoValueType)):
                    raise SemanticError("Map values require ordinary values; resources cannot be copied", entry.value.location)
                try:
                    key_type = self._join_types(key_type, kt)
                    value_type = self._join_types(value_type, vt)
                except TypeError:
                    raise SemanticError("Map entries must use one key type and one value type", entry.location)
                if not valid_map_key(resolve(key_type)):
                    raise SemanticError("Map keys currently support only Int, Bool, and Text", entry.key.location)
                if isinstance(entry.key, LiteralExpr) and entry.key.type_name in ("Int", "Bool", "Text"):
                    marker = (entry.key.type_name, entry.key.value)
                    if marker in literal_keys:
                        raise SemanticError("duplicate Map key in literal", entry.key.location)
                    literal_keys.add(marker)
                failures |= self.expr_failures.get(id(entry.key), set())
                failures |= self.expr_failures.get(id(entry.value), set())
            return self._record(expression, MapType(key_type, value_type), failures)

        if isinstance(expression, IndexExpr):
            base_type = self._expr(expression.base, True, allow_checked)
            resolved_base = resolve(base_type)
            if isinstance(resolved_base, MapType):
                index_type = self._expr(expression.index, True, allow_checked)
                self._unify_or_error(resolved_base.key, index_type, expression.index.location, "Map key")
                failures = set(self.expr_failures.get(id(expression.base), set())) | set(self.expr_failures.get(id(expression.index), set()))
                return self._record(expression, resolved_base.value, failures)
            if resolved_base == BYTES:
                index_type = self._expr(expression.index, True, allow_checked)
                self._require_type(index_type, INT, expression.index.location, "Bytes index must have static type Int")
                failures = set(self.expr_failures.get(id(expression.base), set())) | set(self.expr_failures.get(id(expression.index), set()))
                return self._record(expression, INT, failures)

        return old_expr(self, expression, value_required, allow_checked)

    def member(self, expression, allow_checked):
        base_type = resolve(self._expr(expression.base, True, allow_checked))
        if isinstance(base_type, MapType) or base_type == BYTES:
            failures = set(self.expr_failures.get(id(expression.base), set()))
            if expression.name == "count":
                return self._record(expression, INT, failures)
            label = "Map" if isinstance(base_type, MapType) else "Bytes"
            raise SemanticError(f"{label} has no member {expression.name!r}", expression.location)
        return old_member(self, expression, allow_checked)

    def outputable(t):
        t = resolve(t)
        if isinstance(t, NamedType):
            return t.name in ("Int", "Float", "Bool", "Text", "Bytes")
        if isinstance(t, ListType):
            return outputable(t.element)
        if isinstance(t, MapType):
            return outputable(t.key) and outputable(t.value)
        return False

    def call(self, expression, value_required, allow_checked):
        if isinstance(expression.callee, NameExpr) and expression.callee.name == "output":
            if len(expression.arguments) != 1:
                raise SemanticError("output(...) takes exactly one argument", expression.location)
            actual = self._expr(expression.arguments[0], True, allow_checked)
            if not outputable(actual):
                raise SemanticError(f"output does not support {describe(actual)}", expression.location)
            return self._record(expression, NO_VALUE, self.expr_failures.get(id(expression.arguments[0]), set()))

        return old_call(self, expression, value_required, allow_checked)

    def argument_type(self, expression, declared_type, allow_checked):
        if declared_type is not None and resolve(declared_type) == BYTES and isinstance(expression, ListExpr):
            return with_expected(self, BYTES, lambda: self._expr(expression, True, allow_checked))
        return old_argument_type(self, expression, declared_type, allow_checked)

    def target_type(self, target, for_write=False):
        if isinstance(target, IndexExpr):
            base_type = resolve(self._expr(target.base, True, False))
            if isinstance(base_type, MapType):
                if for_write:
                    self._ensure_mutable_path(target.base)
                key_type = self._expr(target.index, True, False)
                self._unify_or_error(base_type.key, key_type, target.index.location, "Map key")
                return base_type.value
            if base_type == BYTES:
                if for_write:
                    self._ensure_mutable_path(target.base)
                self._require_type(self._expr(target.index, True, False), INT, target.index.location, "Bytes index must have type Int")
                return INT
        return old_target_type(self, target, for_write)

    def equality(self, t, seen):
        t = resolve(t)
        if t == BYTES:
            return True
        if isinstance(t, MapType):
            return self._equality_comparable(t.key, seen) and self._equality_comparable(t.value, seen)
        return old_equality(self, t, seen)

    def deep_fixable(self, t, seen):
        t = resolve(t)
        if t == BYTES:
            return True
        if isinstance(t, MapType):
            return self._deep_fixable(t.key, seen) and self._deep_fixable(t.value, seen)
        return old_deep_fixable(self, t, seen)

    BaseAnalyzer._resolve_type_ref = resolve_type_ref
    BaseAnalyzer._statement = statement
    BaseAnalyzer._expr = expr
    BaseAnalyzer._member = member
    BaseAnalyzer._call = call
    BaseAnalyzer._target_type = target_type
    BaseAnalyzer._equality_comparable = equality
    BaseAnalyzer._deep_fixable = deep_fixable
    BaseAnalyzer._argument_type = argument_type
    BaseAnalyzer._eristavi_collections_installed = True


def _install_runtime() -> None:
    if getattr(BaseInterpreter, "_eristavi_collections_installed", False):
        return

    old_copy = runtime_base.copy_value
    old_equal = runtime_base.equal_value
    old_statement = BaseInterpreter._statement
    old_expr = BaseInterpreter._expr
    old_member = BaseInterpreter._member_from_value
    old_assign_index = BaseInterpreter._assign_index
    old_index_reference = BaseInterpreter._index_reference
    old_call_function = BaseInterpreter._call_function

    def map_index(value: MapValue, key) -> int:
        for index, (existing, _) in enumerate(value.entries):
            if runtime_base.equal_value(existing, key):
                return index
        return -1

    def copy_value(value):
        if isinstance(value, BytesValue):
            return BytesValue(bytearray(value.data))
        if isinstance(value, MapValue):
            return MapValue([(copy_value(k), copy_value(v)) for k, v in value.entries])
        return old_copy(value)

    def equal_value(first, second):
        if isinstance(first, BytesValue) or isinstance(second, BytesValue):
            return isinstance(first, BytesValue) and isinstance(second, BytesValue) and first.data == second.data
        if isinstance(first, MapValue) or isinstance(second, MapValue):
            if not isinstance(first, MapValue) or not isinstance(second, MapValue) or len(first.entries) != len(second.entries):
                return False
            for key, value in first.entries:
                index = map_index(second, key)
                if index < 0 or not equal_value(value, second.entries[index][1]):
                    return False
            return True
        return old_equal(first, second)

    runtime_base.copy_value = copy_value
    runtime_base.equal_value = equal_value

    def bytes_from(value, location=None):
        if isinstance(value, BytesValue):
            return copy_value(value)
        if not isinstance(value, ListValue):
            raise RuntimeFault("Bytes requires a square-bracket sequence of Int values", location)
        data = bytearray()
        for item in value.items:
            if isinstance(item, bool) or not isinstance(item, int) or not 0 <= item <= 255:
                raise RuntimeFault("Bytes elements must be Int values between 0 and 255", location)
            data.append(item)
        return BytesValue(data)

    def statement(self, stmt):
        if isinstance(stmt, LetStmt) and _is_bytes_ref(stmt.type_annotation):
            if self._resolve_cell(stmt.name) is not None:
                raise RuntimeFault(f"name {stmt.name!r} is already visible", stmt.location)
            self.scopes[-1][stmt.name] = Cell(bytes_from(self._expr(stmt.initializer), stmt.location), stmt.fixed)
            return
        if isinstance(stmt, AssignStmt) and isinstance(stmt.target, NameExpr):
            cell = self._resolve_cell(stmt.target.name)
            if cell is not None and isinstance(cell.value, BytesValue):
                if cell.fixed:
                    raise RuntimeFault(f"cannot assign to fixed binding {stmt.target.name!r}", stmt.location)
                cell.value = bytes_from(self._expr(stmt.value), stmt.location)
                return
        return old_statement(self, stmt)

    def expr(self, expression):
        if isinstance(expression, MapExpr):
            result = MapValue([])
            for entry in expression.entries:
                key = self._expr(entry.key)
                value = self._expr(entry.value)
                if map_index(result, key) >= 0:
                    raise RuntimeFault("duplicate Map key in literal", entry.location)
                result.entries.append((copy_value(key), copy_value(value)))
            return result
        return old_expr(self, expression)

    def member(self, base, expression):
        if isinstance(base, MapValue):
            if expression.name == "count":
                return len(base.entries)
            raise RuntimeFault(f"Map has no member {expression.name!r}", expression.location)
        if isinstance(base, BytesValue):
            if expression.name == "count":
                return len(base.data)
            raise RuntimeFault(f"Bytes has no member {expression.name!r}", expression.location)
        return old_member(self, base, expression)

    def assign_index(self, base, index, value, location):
        if isinstance(base, MapValue):
            position = map_index(base, index)
            if position < 0:
                base.entries.append((copy_value(index), copy_value(value)))
            else:
                key = base.entries[position][0]
                base.entries[position] = (key, copy_value(value))
            return
        if isinstance(base, BytesValue):
            if not isinstance(index, int) or isinstance(index, bool) or index < 0 or index >= len(base.data):
                raise RuntimeFault("Bytes index out of bounds", location)
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 255:
                raise RuntimeFault("Bytes elements must be Int values between 0 and 255", location)
            base.data[index] = value
            return
        return old_assign_index(self, base, index, value, location)

    def index_reference(self, base, index, location):
        if isinstance(base, MapValue):
            position = map_index(base, index)
            if position < 0:
                raise RuntimeFault("Map key not found", location)
            return base.entries[position][1]
        if isinstance(base, BytesValue):
            if not isinstance(index, int) or isinstance(index, bool) or index < 0 or index >= len(base.data):
                raise RuntimeFault("Bytes index out of bounds", location)
            return int(base.data[index])
        return old_index_reference(self, base, index, location)

    def call_function(self, fn, args):
        converted = []
        for parameter, value in zip(fn.parameters, args):
            converted.append(bytes_from(value, parameter.location) if _is_bytes_ref(parameter.type_annotation) else value)
        result = old_call_function(self, fn, converted)
        if _is_bytes_ref(fn.return_type) and result is not NO_RUNTIME:
            result = bytes_from(result, fn.location)
        return result

    @staticmethod
    def nested_format(value):
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is NONE:
            return "none"
        if isinstance(value, str):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t").replace("\0", "\\0")
            return f'"{escaped}"'
        if isinstance(value, BytesValue):
            return "[" + ", ".join(str(int(item)) for item in value.data) + "]"
        if isinstance(value, ListValue):
            return "[" + ", ".join(nested_format(item) for item in value.items) + "]"
        if isinstance(value, MapValue):
            if not value.entries:
                return "[:]"
            return "[" + " ".join(f"{nested_format(key)} : {nested_format(item)};" for key, item in value.entries) + "]"
        return str(value)

    @staticmethod
    def format_value(value):
        if isinstance(value, str):
            return value
        return nested_format(value)

    BaseInterpreter._statement = statement
    BaseInterpreter._expr = expr
    BaseInterpreter._member_from_value = member
    BaseInterpreter._assign_index = assign_index
    BaseInterpreter._index_reference = index_reference
    BaseInterpreter._call_function = call_function
    BaseInterpreter._format = format_value
    BaseInterpreter._eristavi_collections_installed = True


def install_collection_support() -> None:
    _install_parser()
    _install_semantics()
    _install_runtime()
