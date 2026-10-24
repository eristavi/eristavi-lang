"""Built-in module contracts; these are libraries, never source keywords."""
from .typesys import BOOL, INT, TEXT, ListType, NO_VALUE

BUILTIN_MODULES = {("std", "files"), ("std", "unicode"), ("std", "process")}
UNICODE_FUNCTIONS = {
    "isIdentifierStart": (TEXT, BOOL),
    "isIdentifierContinue": (TEXT, BOOL),
    "normalizeNfc": (TEXT, TEXT),
    "fromScalar": (INT, TEXT),
}

PROCESS_FUNCTIONS = {"arguments": ((), ListType(TEXT)), "setExitCode": ((INT,), NO_VALUE), "writeError": ((TEXT,), NO_VALUE)}
