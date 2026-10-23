from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
import unicodedata

from .diagnostics import LexError, SourceLocation


class TokenKind(Enum):
    EOF = auto()
    IDENTIFIER = auto()
    INTEGER = auto()
    FLOAT = auto()
    TEXT = auto()

    LET = auto()
    FIXED = auto()
    BE = auto()
    FUNCTION = auto()
    RETURNS = auto()
    RETURN = auto()
    IF = auto()
    ELSE = auto()
    FOR = auto()
    IN = auto()
    WHILE = auto()
    TYPE = auto()
    IDENTITY = auto()
    MAYBE = auto()
    ERROR = auto()
    FAILS = auto()
    FAIL = auto()
    TRY = auto()
    WITH = auto()
    IMPORT = auto()
    AS = auto()
    PUBLIC = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    TRUE = auto()
    FALSE = auto()
    NONE = auto()

    SEMICOLON = auto()
    COMMA = auto()
    DOT = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    EQUAL = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    EQUAL_EQUAL = auto()
    BANG_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()


KEYWORDS = {
    "let": TokenKind.LET,
    "fixed": TokenKind.FIXED,
    "be": TokenKind.BE,
    "function": TokenKind.FUNCTION,
    "returns": TokenKind.RETURNS,
    "return": TokenKind.RETURN,
    "if": TokenKind.IF,
    "else": TokenKind.ELSE,
    "for": TokenKind.FOR,
    "in": TokenKind.IN,
    "while": TokenKind.WHILE,
    "type": TokenKind.TYPE,
    "identity": TokenKind.IDENTITY,
    "maybe": TokenKind.MAYBE,
    "error": TokenKind.ERROR,
    "fails": TokenKind.FAILS,
    "fail": TokenKind.FAIL,
    "try": TokenKind.TRY,
    "with": TokenKind.WITH,
    "import": TokenKind.IMPORT,
    "as": TokenKind.AS,
    "public": TokenKind.PUBLIC,
    "and": TokenKind.AND,
    "or": TokenKind.OR,
    "not": TokenKind.NOT,
    "true": TokenKind.TRUE,
    "false": TokenKind.FALSE,
    "none": TokenKind.NONE,
}


@dataclass(frozen=True)
class Token:
    kind: TokenKind
    lexeme: str
    value: object | None
    location: SourceLocation


class Lexer:
    def __init__(self, source: str):
        if source.startswith("\ufeff"):
            source = source[1:]
        if "\ufeff" in source:
            idx = source.index("\ufeff")
            line = source.count("\n", 0, idx) + 1
            last_nl = source.rfind("\n", 0, idx)
            column = idx + 1 if last_nl < 0 else idx - last_nl
            raise LexError("BOM is allowed only at the start of a source file", SourceLocation(line, column))
        self.source = source
        self.i = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []

    def lex(self) -> list[Token]:
        while not self._at_end():
            ch = self._peek()
            if ch in " \t\r\n":
                self._consume_whitespace()
                continue
            if ch.isspace():
                raise LexError("only SPACE, TAB, LF, and CR are source whitespace", self._loc())
            if ch == "/" and self._peek(1) == "/":
                self._line_comment()
                continue
            if ch == "/" and self._peek(1) == "*":
                self._block_comment()
                continue
            if ch == '"':
                self._text()
                continue
            if ch.isdigit():
                self._number()
                continue
            if self._is_identifier_start(ch):
                self._identifier()
                continue
            self._symbol()

        self.tokens.append(Token(TokenKind.EOF, "", None, self._loc()))
        return self.tokens

    def _loc(self) -> SourceLocation:
        return SourceLocation(self.line, self.column)

    def _at_end(self) -> bool:
        return self.i >= len(self.source)

    def _peek(self, offset: int = 0) -> str:
        pos = self.i + offset
        return "\0" if pos >= len(self.source) else self.source[pos]

    def _advance(self) -> str:
        ch = self.source[self.i]
        self.i += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _consume_whitespace(self) -> None:
        while not self._at_end() and self._peek() in " \t\r\n":
            self._advance()

    def _line_comment(self) -> None:
        self._advance()
        self._advance()
        while not self._at_end() and self._peek() != "\n":
            self._advance()

    def _block_comment(self) -> None:
        start = self._loc()
        self._advance()
        self._advance()
        depth = 1
        while depth:
            if self._at_end():
                raise LexError("unterminated block comment", start)
            if self._peek() == "/" and self._peek(1) == "*":
                self._advance()
                self._advance()
                depth += 1
            elif self._peek() == "*" and self._peek(1) == "/":
                self._advance()
                self._advance()
                depth -= 1
            else:
                self._advance()

    @staticmethod
    def _is_identifier_start(ch: str) -> bool:
        if ch == "_":
            return True
        return ch != "\0" and not ch.isdigit() and ch.isidentifier()

    @staticmethod
    def _is_identifier_continue(ch: str) -> bool:
        if ch == "_" or ch.isdigit():
            return True
        if ch == "\0":
            return False
        category = unicodedata.category(ch)
        return ch.isidentifier() or category.startswith("M") or category == "Pc"

    def _identifier(self) -> None:
        start_i, start = self.i, self._loc()
        self._advance()
        while self._is_identifier_continue(self._peek()):
            self._advance()
        raw = self.source[start_i:self.i]
        name = unicodedata.normalize("NFC", raw)
        if not name.isidentifier():
            raise LexError(f"invalid identifier {raw!r}", start)
        kind = KEYWORDS.get(name, TokenKind.IDENTIFIER)
        self.tokens.append(Token(kind, raw, name if kind is TokenKind.IDENTIFIER else None, start))

    def _number(self) -> None:
        start_i, start = self.i, self._loc()
        if self._peek() == "0" and self._peek(1) in "bB":
            self._advance()
            self._advance()
            self._digits_for_base(2, start)
            raw = self.source[start_i:self.i]
            self.tokens.append(Token(TokenKind.INTEGER, raw, int(raw[2:].replace("_", ""), 2), start))
            return
        if self._peek() == "0" and self._peek(1) in "xX":
            self._advance()
            self._advance()
            self._digits_for_base(16, start)
            raw = self.source[start_i:self.i]
            self.tokens.append(Token(TokenKind.INTEGER, raw, int(raw[2:].replace("_", ""), 16), start))
            return

        self._decimal_digits(start)
        is_float = False
        if self._peek() == ".":
            if not self._peek(1).isdigit():
                raise LexError("a decimal point in a Float literal requires digits on both sides", self._loc())
            is_float = True
            self._advance()
            self._decimal_digits(start)
        if self._peek() in "eE":
            is_float = True
            self._advance()
            if self._peek() in "+-":
                self._advance()
            if not self._peek().isdigit():
                raise LexError("Float exponent requires decimal digits", self._loc())
            self._decimal_digits(start)

        raw = self.source[start_i:self.i]
        clean = raw.replace("_", "")
        if not is_float and len(clean) > 1 and clean.startswith("0"):
            raise LexError("decimal Int literals may not have leading zeroes", start)
        if is_float:
            self.tokens.append(Token(TokenKind.FLOAT, raw, float(clean), start))
        else:
            self.tokens.append(Token(TokenKind.INTEGER, raw, int(clean, 10), start))

    def _decimal_digits(self, start: SourceLocation) -> None:
        self._digit_sequence(lambda c: c.isdigit(), start, "decimal")

    def _digits_for_base(self, base: int, start: SourceLocation) -> None:
        allowed = (lambda c: c in "01") if base == 2 else (lambda c: c.isdigit() or c.lower() in "abcdef")
        self._digit_sequence(allowed, start, "binary" if base == 2 else "hexadecimal")

    def _digit_sequence(self, allowed, start: SourceLocation, label: str) -> None:
        if not allowed(self._peek()):
            raise LexError(f"{label} literal requires digits", start)
        previous_underscore = False
        while True:
            ch = self._peek()
            if allowed(ch):
                previous_underscore = False
                self._advance()
            elif ch == "_":
                if previous_underscore or not allowed(self._peek(1)):
                    raise LexError("numeric underscores must appear only between digits", self._loc())
                previous_underscore = True
                self._advance()
            else:
                break

    def _text(self) -> None:
        start = self._loc()
        self._advance()
        value: list[str] = []
        while not self._at_end() and self._peek() != '"':
            ch = self._advance()
            if ch in "\r\n":
                raise LexError("Text literals may not contain a raw newline", start)
            if ch != "\\":
                value.append(ch)
                continue
            if self._at_end():
                raise LexError("unterminated Text escape", start)
            esc = self._advance()
            simple = {'"': '"', "\\": "\\", "n": "\n", "r": "\r", "t": "\t", "0": "\0"}
            if esc in simple:
                value.append(simple[esc])
                continue
            if esc == "u" and self._peek() == "{":
                self._advance()
                hex_digits = []
                while self._peek() != "}":
                    if self._at_end() or self._peek() not in "0123456789abcdefABCDEF":
                        raise LexError("invalid Unicode scalar escape", self._loc())
                    hex_digits.append(self._advance())
                    if len(hex_digits) > 6:
                        raise LexError("Unicode scalar escape is too long", self._loc())
                self._advance()
                if not hex_digits:
                    raise LexError("Unicode scalar escape requires hexadecimal digits", self._loc())
                scalar = int("".join(hex_digits), 16)
                if scalar > 0x10FFFF or 0xD800 <= scalar <= 0xDFFF:
                    raise LexError("Unicode escape must name a Unicode scalar value", start)
                value.append(chr(scalar))
                continue
            raise LexError(f"unsupported Text escape \\{esc}", self._loc())
        if self._at_end():
            raise LexError("unterminated Text literal", start)
        self._advance()
        self.tokens.append(Token(TokenKind.TEXT, "", "".join(value), start))

    def _symbol(self) -> None:
        start = self._loc()
        two = self._peek() + self._peek(1)
        two_map = {
            "==": TokenKind.EQUAL_EQUAL,
            "!=": TokenKind.BANG_EQUAL,
            "<=": TokenKind.LESS_EQUAL,
            ">=": TokenKind.GREATER_EQUAL,
        }
        if two in two_map:
            self._advance()
            self._advance()
            self.tokens.append(Token(two_map[two], two, None, start))
            return
        one_map = {
            ";": TokenKind.SEMICOLON,
            ",": TokenKind.COMMA,
            ".": TokenKind.DOT,
            "(": TokenKind.LPAREN,
            ")": TokenKind.RPAREN,
            "{": TokenKind.LBRACE,
            "}": TokenKind.RBRACE,
            "[": TokenKind.LBRACKET,
            "]": TokenKind.RBRACKET,
            "=": TokenKind.EQUAL,
            "+": TokenKind.PLUS,
            "-": TokenKind.MINUS,
            "*": TokenKind.STAR,
            "/": TokenKind.SLASH,
            "%": TokenKind.PERCENT,
            "<": TokenKind.LESS,
            ">": TokenKind.GREATER,
        }
        ch = self._peek()
        kind = one_map.get(ch)
        if kind is None:
            raise LexError(f"unexpected source character {ch!r}", start)
        self._advance()
        self.tokens.append(Token(kind, ch, None, start))
