from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceLocation:
    line: int
    column: int


class EristaviError(Exception):
    kind = "error"

    def __init__(self, message: str, location: SourceLocation | None = None):
        self.message = message
        self.location = location
        super().__init__(self.format())

    def format(self) -> str:
        if self.location is None:
            return f"{self.kind}: {self.message}"
        return f"{self.kind} at {self.location.line}:{self.location.column}: {self.message}"


class LexError(EristaviError):
    kind = "lex error"


class ParseError(EristaviError):
    kind = "parse error"


class SemanticError(EristaviError):
    kind = "semantic error"


class RuntimeFault(EristaviError):
    kind = "runtime fault"
