from __future__ import annotations

from functools import lru_cache

from .unicode_c import _property_ranges, PINNED_REGEX_VERSION
from .unicode_support import UNICODE_VERSION


GCB_PROPERTIES = (
    ("gcb=CR", 1),
    ("gcb=LF", 2),
    ("gcb=Control", 3),
    ("gcb=Extend", 4),
    ("gcb=ZWJ", 5),
    ("gcb=Regional_Indicator", 6),
    ("gcb=Prepend", 7),
    ("gcb=SpacingMark", 8),
    ("gcb=L", 9),
    ("gcb=V", 10),
    ("gcb=T", 11),
    ("gcb=LV", 12),
    ("gcb=LVT", 13),
)


def _rows(properties):
    out = []
    for expression, value in properties:
        out.extend((first, last, value) for first, last in _property_ranges(expression))
    out.sort()
    return out


@lru_cache(maxsize=1)
def unicode_asm_tables() -> tuple[list[str], dict[str, int]]:
    """Emit compact read-only tables consumed by direct assembly runtimes.

    Each row is 12 bytes: uint32 first, uint32 last, uint32 property value.
    Tables are generated from the exact pinned Unicode-support dependency used by
    the C and bootstrap runtimes, so a direct CPU backend never consults locale
    or operating-system Unicode data.
    """
    gcb = _rows(GCB_PROPERTIES)
    incb = _rows((("InCB=Consonant", 1), ("InCB=Extend", 2), ("InCB=Linker", 3)))
    ep = [(first, last, 1) for first, last in _property_ranges("Extended_Pictographic")]

    lines = [
        f"# Unicode {UNICODE_VERSION}; regex {PINNED_REGEX_VERSION}",
        ".align 4",
    ]
    counts = {}
    for label, rows in ((".Leri_unicode_gcb", gcb), (".Leri_unicode_incb", incb), (".Leri_unicode_ep", ep)):
        counts[label] = len(rows)
        lines.append(f"{label}:")
        for first, last, value in rows:
            lines.append(f"    .long {first}, {last}, {value}")
    return lines, counts
