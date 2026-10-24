from __future__ import annotations

from dataclasses import dataclass

from .diagnostics import RuntimeFault
from .runtime import Interpreter as BaseInterpreter
from .runtime import copy_value
from .syntax import IndexExpr
from .unicode_support import grapheme_clusters, scalar_texts, utf8_bytes


@dataclass(frozen=True)
class TextViewValue:
    kind: str
    text: str

    def items(self):
        if self.kind == "characters":
            return grapheme_clusters(self.text)
        if self.kind == "scalars":
            return scalar_texts(self.text)
        if self.kind == "bytes":
            return utf8_bytes(self.text)
        raise RuntimeFault(f"unknown Text view {self.kind!r}")


class Interpreter(BaseInterpreter):
    """Bootstrap runtime with the frozen explicit Unicode Text views."""

    def _member_value(self, e):
        base = self._expr(e.base)
        if isinstance(base, str) and e.name in ("characters", "scalars", "bytes"):
            return TextViewValue(e.name, base)
        if isinstance(base, TextViewValue):
            if e.name == "count":
                return len(base.items())
            raise RuntimeFault(
                f"Text {base.kind} view has no member {e.name!r} in pre-0.1",
                e.location,
            )
        return super()._member_value(e)

    def _expr(self, e):
        if isinstance(e, IndexExpr):
            base = self._expr(e.base)
            if isinstance(base, TextViewValue):
                idx = self._expr(e.index)
                items = base.items()
                if idx < 0 or idx >= len(items):
                    raise RuntimeFault("Text view index out of bounds", e.location)
                return copy_value(items[idx])
        return super()._expr(e)
