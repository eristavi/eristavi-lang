"""Opt-in U3 scalar shadow ingress gate; no production compiler migration.

This gate accepts only exact source revisions and frozen scalar U1 signatures.
It does not claim to construct canonical UIR or implement U2 semantics.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib

SCALAR_TYPES = frozenset({"pred", "i64", "f64"})
MAX_SOURCES = 4096
MAX_SOURCE_BYTES = 16 * 1024 * 1024

@dataclass(frozen=True)
class SourceRevision:
    logical_name: str
    sha256: str
    size: int

@dataclass(frozen=True)
class ScalarSignature:
    parameters: tuple[str, ...]
    results: tuple[str, ...]

def validate_shadow_ingress(
    revisions: tuple[SourceRevision, ...],
    source_bytes: dict[str, bytes],
    signatures: tuple[ScalarSignature, ...],
) -> None:
    """Fail closed before opt-in shadow lowering; no stamps are trusted."""
    if len(revisions) > MAX_SOURCES or not revisions:
        raise ValueError("invalid shadow source count")
    if set(source_bytes) != {item.logical_name for item in revisions}:
        raise ValueError("source identity mismatch")
    seen = set()
    total = 0
    for item in revisions:
        if not item.logical_name or item.logical_name in seen or item.logical_name.startswith("/") or ".." in item.logical_name.split("/"):
            raise ValueError("invalid or duplicate logical source")
        seen.add(item.logical_name)
        data = source_bytes[item.logical_name]
        if not isinstance(data, bytes) or type(item.size) is not int or item.size != len(data):
            raise ValueError("source length mismatch")
        total += len(data)
        if total > MAX_SOURCE_BYTES:
            raise ValueError("shadow source byte budget")
        if hashlib.sha256(data).hexdigest() != item.sha256:
            raise ValueError("stale shadow source digest")
    if not signatures:
        raise ValueError("missing scalar signatures")
    for signature in signatures:
        if not isinstance(signature, ScalarSignature):
            raise ValueError("invalid signature")
        if any(t not in SCALAR_TYPES for t in signature.parameters + signature.results):
            raise ValueError("unsupported U3 shadow type")
