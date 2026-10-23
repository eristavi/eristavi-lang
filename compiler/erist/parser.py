from __future__ import annotations

from .diagnostics import ParseError
from .lexer import Token, TokenKind
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
    Parameter,
    Program,
    ReturnStmt,
    UnaryExpr,
    WhileStmt,
)


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.i = 0

    def parse(self) -> Program:
        statements = []
        while not self._check(TokenKind.EOF):
            statements.append(self._statement())
        return Program(statements)

    def _statement(self):
        if self._match(TokenKind.PUBLIC):
            public_token = self._previous()
            self._consume(
                TokenKind.FUNCTION,
                "'public' is implemented only for function declarations in the bootstrap",
            )
            return self._function_declaration(True, public_token.location)

        if self._match(TokenKind.FUNCTION):
            return self._function_declaration(False, self._previous().location)

        if self._match(TokenKind.RETURN):
            return self._return_statement(self._previous())

        if self._match(TokenKind.LET):
            return self._let_statement(self._previous())

        if self._match(TokenKind.IF):
            return self._if_statement(self._previous())

        if self._match(TokenKind.WHILE):
            return self._while_statement(self._previous())

        if self._check(TokenKind.IDENTIFIER) and self._peek(1).kind is TokenKind.EQUAL:
            name = self._advance()
            self._advance()
            value = self._expression()
            self._consume(TokenKind.SEMICOLON, "expected ';' after assignment")
            return AssignStmt(str(name.value), value, name.location)

        expr = self._expression()
        self._consume(TokenKind.SEMICOLON, "expected ';' after expression")
        return ExprStmt(expr, expr.location)

    def _function_declaration(self, public: bool, location):
        name = self._consume(TokenKind.IDENTIFIER, "expected function name after 'function'")
        self._consume(TokenKind.LPAREN, "expected '(' after function name")

        parameters = []
        if not self._check(TokenKind.RPAREN):
            while True:
                parameter = self._consume(TokenKind.IDENTIFIER, "expected parameter name")
                type_annotation = None

                if self._check(TokenKind.IDENTIFIER):
                    type_annotation = str(self._advance().value)
                elif self._check(TokenKind.MAYBE) or self._check(TokenKind.IDENTITY):
                    raise ParseError(
                        "bootstrap parser does not yet implement composite parameter types",
                        self._current().location,
                    )

                parameters.append(
                    Parameter(str(parameter.value), type_annotation, parameter.location)
                )

                if not self._match(TokenKind.COMMA):
                    break

        self._consume(TokenKind.RPAREN, "expected ')' after parameters")

        return_type = None
        if self._match(TokenKind.RETURNS):
            if self._check(TokenKind.MAYBE) or self._check(TokenKind.IDENTITY):
                raise ParseError(
                    "bootstrap parser does not yet implement composite return types",
                    self._current().location,
                )
            result_type = self._consume(
                TokenKind.IDENTIFIER,
                "expected result type after 'returns'",
            )
            return_type = str(result_type.value)

        open_brace = self._consume(TokenKind.LBRACE, "expected '{' before function body")
        return FunctionDecl(
            str(name.value),
            parameters,
            return_type,
            self._block(open_brace),
            location,
            public,
        )

    def _return_statement(self, return_token: Token):
        if self._match(TokenKind.SEMICOLON):
            return ReturnStmt(None, return_token.location)

        value = self._expression()
        self._consume(TokenKind.SEMICOLON, "expected ';' after return value")
        return ReturnStmt(value, return_token.location)

    def _let_statement(self, let_token: Token):
        fixed = self._match(TokenKind.FIXED)
        name = self._consume(TokenKind.IDENTIFIER, "expected binding name after 'let'")

        type_annotation = None
        if self._check(TokenKind.IDENTIFIER):
            type_annotation = str(self._advance().value)
        elif self._check(TokenKind.MAYBE) or self._check(TokenKind.IDENTITY):
            raise ParseError(
                "bootstrap parser does not yet implement composite type annotations",
                self._current().location,
            )

        self._consume(TokenKind.BE, "expected 'be' after binding declaration")
        initializer = self._expression()
        self._consume(TokenKind.SEMICOLON, "expected ';' after binding declaration")
        return LetStmt(
            str(name.value),
            fixed,
            type_annotation,
            initializer,
            let_token.location,
        )

    def _if_statement(self, if_token: Token):
        condition = self._expression()
        open_brace = self._consume(TokenKind.LBRACE, "expected '{' after if condition")
        then_branch = self._block(open_brace)

        else_branch = None
        if self._match(TokenKind.ELSE):
            open_brace = self._consume(TokenKind.LBRACE, "expected '{' after else")
            else_branch = self._block(open_brace)

        return IfStmt(condition, then_branch, else_branch, if_token.location)

    def _while_statement(self, while_token: Token):
        condition = self._expression()
        open_brace = self._consume(TokenKind.LBRACE, "expected '{' after while condition")
        return WhileStmt(condition, self._block(open_brace), while_token.location)

    def _block(self, open_brace: Token) -> Block:
        statements = []
        while not self._check(TokenKind.RBRACE):
            if self._check(TokenKind.EOF):
                raise ParseError("unterminated block; expected '}'", open_brace.location)
            statements.append(self._statement())
        self._advance()
        return Block(statements, open_brace.location)

    def _expression(self) -> Expr:
        return self._or()

    def _or(self):
        expr = self._and()
        while self._match(TokenKind.OR):
            op = self._previous()
            expr = BinaryExpr(expr, "or", self._and(), op.location)
        return expr

    def _and(self):
        expr = self._not()
        while self._match(TokenKind.AND):
            op = self._previous()
            expr = BinaryExpr(expr, "and", self._not(), op.location)
        return expr

    def _not(self):
        if self._match(TokenKind.NOT):
            op = self._previous()
            return UnaryExpr("not", self._not(), op.location)
        return self._comparison()

    def _comparison(self):
        expr = self._additive()
        kinds = {
            TokenKind.EQUAL_EQUAL: "==",
            TokenKind.BANG_EQUAL: "!=",
            TokenKind.LESS: "<",
            TokenKind.LESS_EQUAL: "<=",
            TokenKind.GREATER: ">",
            TokenKind.GREATER_EQUAL: ">=",
        }

        if self._current().kind in kinds:
            op = self._advance()
            expr = BinaryExpr(expr, kinds[op.kind], self._additive(), op.location)
            if self._current().kind in kinds:
                raise ParseError(
                    "comparison chaining is not part of pre-0.1; use 'and' explicitly",
                    self._current().location,
                )
        return expr

    def _additive(self):
        expr = self._multiplicative()
        while self._current().kind in (TokenKind.PLUS, TokenKind.MINUS):
            op = self._advance()
            expr = BinaryExpr(
                expr,
                "+" if op.kind is TokenKind.PLUS else "-",
                self._multiplicative(),
                op.location,
            )
        return expr

    def _multiplicative(self):
        expr = self._prefix()
        symbols = {
            TokenKind.STAR: "*",
            TokenKind.SLASH: "/",
            TokenKind.PERCENT: "%",
        }
        while self._current().kind in symbols:
            op = self._advance()
            expr = BinaryExpr(expr, symbols[op.kind], self._prefix(), op.location)
        return expr

    def _prefix(self):
        if self._match(TokenKind.MINUS):
            op = self._previous()
            return UnaryExpr("-", self._prefix(), op.location)
        return self._postfix()

    def _postfix(self):
        expr = self._primary()
        while self._match(TokenKind.LPAREN):
            open_token = self._previous()
            args = []
            if not self._check(TokenKind.RPAREN):
                while True:
                    args.append(self._expression())
                    if not self._match(TokenKind.COMMA):
                        break
            self._consume(TokenKind.RPAREN, "expected ')' after arguments")
            expr = CallExpr(expr, args, open_token.location)
        return expr

    def _primary(self):
        if self._match(TokenKind.INTEGER):
            token = self._previous()
            return LiteralExpr(token.value, "Int", token.location)
        if self._match(TokenKind.FLOAT):
            token = self._previous()
            return LiteralExpr(token.value, "Float", token.location)
        if self._match(TokenKind.TEXT):
            token = self._previous()
            return LiteralExpr(token.value, "Text", token.location)
        if self._match(TokenKind.TRUE):
            token = self._previous()
            return LiteralExpr(True, "Bool", token.location)
        if self._match(TokenKind.FALSE):
            token = self._previous()
            return LiteralExpr(False, "Bool", token.location)
        if self._match(TokenKind.IDENTIFIER):
            token = self._previous()
            return NameExpr(str(token.value), token.location)
        if self._match(TokenKind.LPAREN):
            expr = self._expression()
            self._consume(TokenKind.RPAREN, "expected ')' after grouped expression")
            return expr

        raise ParseError(
            f"expected expression, found {self._current().lexeme!r}",
            self._current().location,
        )

    def _current(self) -> Token:
        return self.tokens[self.i]

    def _peek(self, offset: int) -> Token:
        return self.tokens[min(self.i + offset, len(self.tokens) - 1)]

    def _previous(self) -> Token:
        return self.tokens[self.i - 1]

    def _advance(self) -> Token:
        token = self._current()
        if token.kind is not TokenKind.EOF:
            self.i += 1
        return token

    def _check(self, kind: TokenKind) -> bool:
        return self._current().kind is kind

    def _match(self, *kinds: TokenKind) -> bool:
        if self._current().kind in kinds:
            self._advance()
            return True
        return False

    def _consume(self, kind: TokenKind, message: str) -> Token:
        if self._check(kind):
            return self._advance()
        raise ParseError(message, self._current().location)
