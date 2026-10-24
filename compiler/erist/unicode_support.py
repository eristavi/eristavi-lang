from __future__ import annotations

import regex
import unicodedata2

# Eristavi pre-0.1 deliberately pins its Unicode semantics rather than inheriting
# whatever tables happen to ship with the host Python interpreter.
UNICODE_VERSION = "17.0.0"

if unicodedata2.unidata_version != UNICODE_VERSION:
    raise RuntimeError(
        f"Eristavi requires Unicode {UNICODE_VERSION}, "
        f"but unicodedata2 provides {unicodedata2.unidata_version}"
    )

_XID_START = regex.compile(r"\A\p{XID_Start}\Z", regex.VERSION1)
_XID_CONTINUE = regex.compile(r"\A\p{XID_Continue}\Z", regex.VERSION1)
_GRAPHEME = regex.compile(r"\X", regex.VERSION1)


def normalize_nfc(text: str) -> str:
    return unicodedata2.normalize("NFC", text)


def is_xid_start(ch: str) -> bool:
    return len(ch) == 1 and bool(_XID_START.fullmatch(ch))


def is_xid_continue(ch: str) -> bool:
    return len(ch) == 1 and bool(_XID_CONTINUE.fullmatch(ch))


def is_identifier(text: str) -> bool:
    if not text:
        return False
    if text[0] == "_":
        start_ok = True
    else:
        start_ok = is_xid_start(text[0])
    return start_ok and all(ch == "_" or is_xid_continue(ch) for ch in text[1:])


def grapheme_clusters(text: str) -> list[str]:
    """Return Unicode 17 extended grapheme clusters (UAX #29 via pinned regex)."""
    return _GRAPHEME.findall(text)


def scalar_texts(text: str) -> list[str]:
    """Return one-Text values, each containing exactly one Unicode scalar."""
    return list(text)


def utf8_bytes(text: str) -> list[int]:
    return list(text.encode("utf-8"))
