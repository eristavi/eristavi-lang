"""Built-in module contracts; these are libraries, never source keywords."""
from .typesys import BOOL, INT, TEXT

BUILTIN_MODULES = {("std", "files"), ("std", "unicode")}
UNICODE_FUNCTIONS = {
    "isIdentifierStart": (TEXT, BOOL),
    "isIdentifierContinue": (TEXT, BOOL),
    "normalizeNfc": (TEXT, TEXT),
    "fromScalar": (INT, TEXT),
}
