from __future__ import annotations

from .diagnostics import ParseError
from .lexer import Token, TokenKind
from .syntax import AssignStmt, BinaryExpr, CallExpr, Expr, ExprStmt, LetStmt, LiteralExpr, NameExpr, Program, UnaryExpr


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
        if self._match(TokenKind.LET):
            return self._let_statement(self._previous())
        if self._check(TokenKind.IDENTIFIER) and self._peek(1).kind is TokenKind.EQUAL:
            name = self._advance()
            self._advance()
            value = self._expression()
            self._consume(TokenKind.SEMICOLON, "expected ';' after assignment")
            return AssignStmt(str(name.value), value, name.location)
        expr = self._expression()
        self._consume(TokenKind.SEMICOLON, "expected ';' after expression")
        return ExprStmt(expr, expr.location)

    def _let_statement(self, let_token: Token):
        fixed = self._match(TokenKind.FIXED)
        name = self._consume(TokenKind.IDENTIFIER, "expected binding name after 'let'")
        if not self._match(TokenKind.BE):
            raise ParseError("bootstrap parser does not yet implement explicit type annotations", self._current().location)
        initializer = self._expression()
        self._consume(TokenKind.SEMICOLON, "expected ';' after binding declaration")
        return LetStmt(str(name.value), fixed, initializer, let_token.location)

    def _expression(self) -> Expr:
        return self._or()

    def _or(self):
        expr = self._and()
        while self._match(TokenKind.OR):
            op = self._previous()
            right = self._and()
            expr = BinaryExpr(expr, "or", right, op.location)
        return expr

    def _and(self):
        expr = self._not()
        while self._match(TokenKind.AND):
            op = self._previous()
            right = self._not()
            expr = BinaryExpr(expr, "and", right, op.location)
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
            right = self._additive()
            expr = BinaryExpr(expr, kinds[op.kind], right, op.location)
            if self._current().kind in kinds:
                raise ParseError("comparison chaining is not part of pre-0.1; use 'and' explicitly", self._current().location)
        return expr

    def _additive(self):
        expr = self._multiplicative()
        while self._current().kind in (TokenKind.PLUS, TokenKind.MINUS):
            op = self._advance()
            right = self._multiplicative()
            expr = BinaryExpr(expr, "+" if op.kind is TokenKind.PLUS else "-", right, op.location)
        return expr

    def _multiplicative(self):
        expr = self._prefix()
        symbols = {TokenKind.STAR: "*", TokenKind.SLASH: "/", TokenKind.PERCENT: "%"}
        while self._current().kind in symbols:
            op = self._advance()
            right = self._prefix()
            expr = BinaryExpr(expr, symbols[op.kind], right, op.location)
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
            t = self._previous()
            return LiteralExpr(t.value, "Int", t.location)
        if self._match(TokenKind.FLOAT):
            t = self._previous()
            return LiteralExpr(t.value, "Float", t.location)
        if self._match(TokenKind.TEXT):
            t = self._previous()
            return LiteralExpr(t.value, "Text", t.location)
        if self._match(TokenKind.TRUE):
            t = self._previous()
            return LiteralExpr(True, "Bool", t.location)
        if self._match(TokenKind.FALSE):
            t = self._previous()
            return LiteralExpr(False, "Bool", t.location)
        if self._match(TokenKind.IDENTIFIER):
            t = self._previous()
            return NameExpr(str(t.value), t.location)
        if self._match(TokenKind.LPAREN):
            expr = self._expression()
            self._consume(TokenKind.RPAREN, "expected ')' after grouped expression")
            return expr
        raise ParseError(f"expected expression, found {self._current().lexeme!r}", self._current().location)

    def _current(self) -> Token:
        return self.tokens[self.i]

    def _peek(self, offset: int) -> Token:
        idx = min(self.i + offset, len(self.tokens) - 1)
        return self.tokens[idx]

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
