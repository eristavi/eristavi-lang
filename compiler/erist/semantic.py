from __future__ import annotations

from dataclasses import dataclass

from .diagnostics import SemanticError
from .syntax import (
    AssignStmt,
    BinaryExpr,
    Block,
    CallExpr,
    Expr,
    ExprStmt,
    FunctionDecl,
    IfStmt,
    LetStmt,
    LiteralExpr,
    NameExpr,
    Program,
    ReturnStmt,
    UnaryExpr,
    WhileStmt,
)


BASIC_TYPES = {"Int", "Float", "Bool", "Text"}
NO_VALUE = "<no-value>"
IGNORED_VALUE = "<ignored-call-result>"


@dataclass
class Symbol:
    type_name: str
    fixed: bool


@dataclass
class FunctionSymbol:
    declaration: FunctionDecl
    parameter_types: list[str]
    return_type: str | None
    state: str = "unseen"


@dataclass
class FunctionContext:
    symbol: FunctionSymbol
    value_return_type: str | None = None
    saw_value_return: bool = False
    saw_bare_return: bool = False


class Analyzer:
    def __init__(self):
        self.scopes: list[dict[str, Symbol]] = [{}]
        self.functions: dict[str, FunctionSymbol] = {}
        self.expr_types: dict[int, str] = {}
        self.current_function: FunctionContext | None = None

    def analyze(self, program: Program) -> dict[int, str]:
        self._collect_functions(program)

        for function in self.functions.values():
            self._ensure_function(function)

        for stmt in program.statements:
            if isinstance(stmt, FunctionDecl):
                continue
            self._statement(stmt)

        return self.expr_types

    def _collect_functions(self, program: Program) -> None:
        entry_started = False

        for stmt in program.statements:
            if not isinstance(stmt, FunctionDecl):
                entry_started = True
                continue

            if entry_started:
                raise SemanticError(
                    "module declarations must appear before entry executable statements",
                    stmt.location,
                )

            if stmt.name in self.functions:
                raise SemanticError(
                    f"duplicate module-level function {stmt.name!r}",
                    stmt.location,
                )

            seen_parameters: set[str] = set()
            parameter_types: list[str] = []

            for parameter in stmt.parameters:
                if parameter.name in seen_parameters:
                    raise SemanticError(
                        f"duplicate parameter {parameter.name!r} in function {stmt.name!r}",
                        parameter.location,
                    )
                seen_parameters.add(parameter.name)

                if parameter.type_annotation is None:
                    raise SemanticError(
                        "bootstrap function parameters currently require explicit basic types; "
                        "inferred generic parameters are not implemented yet",
                        parameter.location,
                    )

                if parameter.type_annotation not in BASIC_TYPES:
                    raise SemanticError(
                        f"bootstrap does not yet implement parameter type "
                        f"{parameter.type_annotation!r}",
                        parameter.location,
                    )

                parameter_types.append(parameter.type_annotation)

            if stmt.return_type is not None and stmt.return_type not in BASIC_TYPES:
                raise SemanticError(
                    f"bootstrap does not yet implement return type {stmt.return_type!r}",
                    stmt.location,
                )

            self.functions[stmt.name] = FunctionSymbol(
                stmt,
                parameter_types,
                stmt.return_type,
            )

    def _ensure_function(self, function: FunctionSymbol) -> str:
        if function.state == "done":
            return function.return_type or NO_VALUE

        if function.state == "visiting":
            if function.return_type is not None:
                return function.return_type
            raise SemanticError(
                f"circular result inference for function "
                f"{function.declaration.name!r}; add an explicit 'returns T' contract",
                function.declaration.location,
            )

        function.state = "visiting"
        previous_scopes = self.scopes
        previous_function = self.current_function
        self.scopes = [{}]

        try:
            for parameter, type_name in zip(
                function.declaration.parameters,
                function.parameter_types,
            ):
                self.scopes[0][parameter.name] = Symbol(type_name, False)

            context = FunctionContext(function)
            self.current_function = context
            definitely_returns = self._block(function.declaration.body)
            explicit_return = function.declaration.return_type

            if context.saw_value_return and context.saw_bare_return:
                raise SemanticError(
                    f"function {function.declaration.name!r} cannot mix 'return;' "
                    "with value returns",
                    function.declaration.location,
                )

            if explicit_return is not None:
                function.return_type = explicit_return

                if context.saw_bare_return:
                    raise SemanticError(
                        f"value-producing function {function.declaration.name!r} "
                        "cannot use bare 'return;'",
                        function.declaration.location,
                    )

                if not definitely_returns:
                    raise SemanticError(
                        f"value-producing function {function.declaration.name!r} has a "
                        "reachable successful path without a return value",
                        function.declaration.location,
                    )

            elif context.saw_value_return:
                function.return_type = context.value_return_type

                if not definitely_returns:
                    raise SemanticError(
                        f"value-producing function {function.declaration.name!r} has a "
                        "reachable successful path without a return value",
                        function.declaration.location,
                    )

            else:
                function.return_type = NO_VALUE

            function.state = "done"
            return function.return_type

        except Exception:
            if function.state != "done":
                function.state = "unseen"
            raise

        finally:
            self.scopes = previous_scopes
            self.current_function = previous_function

    def _statement(self, stmt) -> bool:
        if isinstance(stmt, FunctionDecl):
            raise SemanticError(
                "function declarations are module-level only in pre-0.1",
                stmt.location,
            )

        if isinstance(stmt, ReturnStmt):
            if self.current_function is None:
                raise SemanticError("return is valid only inside a function", stmt.location)

            context = self.current_function

            if stmt.value is None:
                context.saw_bare_return = True
                if (
                    context.saw_value_return
                    or context.symbol.declaration.return_type is not None
                ):
                    raise SemanticError(
                        "bare 'return;' is valid only in a no-value function",
                        stmt.location,
                    )
            else:
                result_type = self._expr(stmt.value, True)

                if result_type == NO_VALUE:
                    raise SemanticError(
                        "a no-value function call cannot be returned as a value",
                        stmt.location,
                    )

                context.saw_value_return = True
                if context.saw_bare_return:
                    raise SemanticError(
                        "a function cannot mix bare and value returns",
                        stmt.location,
                    )

                explicit_return = context.symbol.declaration.return_type
                if explicit_return is not None and result_type != explicit_return:
                    raise SemanticError(
                        f"return value has type {result_type}, but function requires "
                        f"{explicit_return}",
                        stmt.location,
                    )

                if context.value_return_type is None:
                    context.value_return_type = result_type
                elif context.value_return_type != result_type:
                    raise SemanticError(
                        f"incompatible inferred return types "
                        f"{context.value_return_type} and {result_type}",
                        stmt.location,
                    )

            return True

        if isinstance(stmt, LetStmt):
            if self._resolve(stmt.name) is not None:
                raise SemanticError(
                    f"name {stmt.name!r} is already visible; pre-0.1 does not allow "
                    "local shadowing",
                    stmt.location,
                )

            inferred_type = self._expr(stmt.initializer, True)
            if inferred_type == NO_VALUE:
                raise SemanticError(
                    "a no-value function call cannot initialize a binding",
                    stmt.location,
                )

            if stmt.type_annotation is not None:
                if stmt.type_annotation not in BASIC_TYPES:
                    raise SemanticError(
                        f"bootstrap does not yet implement type annotation "
                        f"{stmt.type_annotation!r}",
                        stmt.location,
                    )
                if inferred_type != stmt.type_annotation:
                    raise SemanticError(
                        f"cannot initialize {stmt.name!r} of type "
                        f"{stmt.type_annotation} with {inferred_type}",
                        stmt.location,
                    )
                inferred_type = stmt.type_annotation

            self.scopes[-1][stmt.name] = Symbol(inferred_type, stmt.fixed)
            return False

        if isinstance(stmt, AssignStmt):
            symbol = self._resolve(stmt.name)
            if symbol is None:
                raise SemanticError(f"unknown name {stmt.name!r}", stmt.location)
            if symbol.fixed:
                raise SemanticError(
                    f"cannot assign to fixed binding {stmt.name!r}",
                    stmt.location,
                )

            rhs_type = self._expr(stmt.value, True)
            if rhs_type == NO_VALUE:
                raise SemanticError(
                    "a no-value function call cannot be assigned as a value",
                    stmt.location,
                )
            if rhs_type != symbol.type_name:
                raise SemanticError(
                    f"cannot assign {rhs_type} to {stmt.name!r} of type "
                    f"{symbol.type_name}",
                    stmt.location,
                )
            return False

        if isinstance(stmt, ExprStmt):
            self._expr(stmt.expression, False)
            return False

        if isinstance(stmt, IfStmt):
            condition_type = self._expr(stmt.condition, True)
            if condition_type != "Bool":
                raise SemanticError(
                    "if condition must have static type Bool",
                    stmt.condition.location,
                )

            then_returns = self._block(stmt.then_branch)
            else_returns = False
            if stmt.else_branch is not None:
                else_returns = self._block(stmt.else_branch)

            return (
                stmt.else_branch is not None
                and then_returns
                and else_returns
            )

        if isinstance(stmt, WhileStmt):
            condition_type = self._expr(stmt.condition, True)
            if condition_type != "Bool":
                raise SemanticError(
                    "while condition must have static type Bool",
                    stmt.condition.location,
                )
            self._block(stmt.body)
            return False

        raise SemanticError("statement is not implemented by the bootstrap analyzer")

    def _block(self, block: Block) -> bool:
        self.scopes.append({})
        definitely_returns = False

        try:
            for stmt in block.statements:
                if definitely_returns:
                    break
                definitely_returns = self._statement(stmt)
            return definitely_returns
        finally:
            self.scopes.pop()

    def _resolve(self, name: str) -> Symbol | None:
        for scope in reversed(self.scopes):
            symbol = scope.get(name)
            if symbol is not None:
                return symbol
        return None

    def _record(self, expr: Expr, type_name: str) -> str:
        self.expr_types[id(expr)] = type_name
        return type_name

    def _expr(self, expr: Expr, value_required: bool = True) -> str:
        if isinstance(expr, LiteralExpr):
            if expr.type_name == "Int" and not (
                -(2**63) <= int(expr.value) <= 2**63 - 1
            ):
                raise SemanticError(
                    "Int literal is outside the signed 64-bit range",
                    expr.location,
                )
            return self._record(expr, expr.type_name)

        if isinstance(expr, NameExpr):
            if expr.name == "output":
                return self._record(expr, "<function output>")

            symbol = self._resolve(expr.name)
            if symbol is not None:
                return self._record(expr, symbol.type_name)

            if expr.name in self.functions:
                raise SemanticError(
                    "function names are not first-class values in the bootstrap subset; "
                    "call the function instead",
                    expr.location,
                )

            raise SemanticError(f"unknown name {expr.name!r}", expr.location)

        if isinstance(expr, UnaryExpr):
            operand_type = self._expr(expr.operand, True)
            if expr.operator == "-" and operand_type in ("Int", "Float"):
                return self._record(expr, operand_type)
            if expr.operator == "not" and operand_type == "Bool":
                return self._record(expr, "Bool")
            raise SemanticError(
                f"operator {expr.operator!r} is not defined for {operand_type}",
                expr.location,
            )

        if isinstance(expr, BinaryExpr):
            left_type = self._expr(expr.left, True)
            right_type = self._expr(expr.right, True)
            op = expr.operator

            if NO_VALUE in (left_type, right_type):
                raise SemanticError(
                    f"operator {op} requires values, not a no-value function call",
                    expr.location,
                )

            if op in ("and", "or"):
                if left_type == right_type == "Bool":
                    return self._record(expr, "Bool")
                raise SemanticError(f"{op} requires Bool operands", expr.location)

            if op in ("==", "!=", "<", "<=", ">", ">="):
                if left_type != right_type:
                    raise SemanticError(
                        f"cannot compare {left_type} with {right_type} without an "
                        "explicit conversion",
                        expr.location,
                    )
                if left_type in BASIC_TYPES:
                    if op in ("<", "<=", ">", ">=") and left_type == "Bool":
                        raise SemanticError(
                            f"ordered comparison {op} is not defined for Bool",
                            expr.location,
                        )
                    return self._record(expr, "Bool")
                raise SemanticError(
                    f"comparison is not implemented for {left_type} in the bootstrap subset",
                    expr.location,
                )

            if op in ("+", "-", "*", "/", "%"):
                if left_type != right_type:
                    raise SemanticError(
                        f"operator {op} does not implicitly mix {left_type} and "
                        f"{right_type}",
                        expr.location,
                    )
                if left_type == "Int":
                    return self._record(expr, "Int")
                if left_type == "Float" and op != "%":
                    return self._record(expr, "Float")
                if left_type == "Float" and op == "%":
                    raise SemanticError(
                        "% is Int-only in pre-0.1; Float remainder requires a named API",
                        expr.location,
                    )
                raise SemanticError(
                    f"operator {op} is not defined for {left_type}",
                    expr.location,
                )

        if isinstance(expr, CallExpr):
            if isinstance(expr.callee, NameExpr) and expr.callee.name == "output":
                if len(expr.arguments) != 1:
                    raise SemanticError(
                        "output(...) takes exactly one argument in pre-0.1",
                        expr.location,
                    )

                arg_type = self._expr(expr.arguments[0], True)
                if arg_type not in BASIC_TYPES:
                    raise SemanticError(
                        f"bootstrap output does not yet support {arg_type}",
                        expr.location,
                    )
                return self._record(expr, NO_VALUE)

            if not isinstance(expr.callee, NameExpr):
                raise SemanticError(
                    "bootstrap function calls require a named function",
                    expr.location,
                )

            function = self.functions.get(expr.callee.name)
            if function is None:
                raise SemanticError(
                    f"unknown function {expr.callee.name!r}",
                    expr.callee.location,
                )

            if len(expr.arguments) != len(function.parameter_types):
                raise SemanticError(
                    f"function {function.declaration.name!r} expects "
                    f"{len(function.parameter_types)} argument(s), got "
                    f"{len(expr.arguments)}",
                    expr.location,
                )

            for index, (argument, expected_type) in enumerate(
                zip(expr.arguments, function.parameter_types),
                1,
            ):
                actual_type = self._expr(argument, True)
                if actual_type != expected_type:
                    raise SemanticError(
                        f"argument {index} of function {function.declaration.name!r} "
                        f"requires {expected_type}, got {actual_type}",
                        argument.location,
                    )

            if function.return_type is not None:
                result_type = function.return_type
            elif function.state == "visiting":
                if value_required:
                    raise SemanticError(
                        f"circular result inference for function "
                        f"{function.declaration.name!r}; add an explicit 'returns T' "
                        "contract",
                        expr.location,
                    )
                result_type = IGNORED_VALUE
            elif value_required:
                result_type = self._ensure_function(function)
            else:
                result_type = IGNORED_VALUE

            return self._record(expr, result_type)

        raise SemanticError("expression is not implemented by the bootstrap analyzer")
