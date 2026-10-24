from __future__ import annotations

from .universal_ir import UInstruction
from .x86_64_resource_backend import X86_64ResourceLinuxBackend


class X86_64DirectLinuxBackend(X86_64ResourceLinuxBackend):
    """Final composed direct x86-64 backend.

    Text output uses raw length-aware writes so embedded NUL remains valid. The
    scalar output helpers use stdio. Flush stdio before a raw Text write so a
    program's observable output order never depends on libc buffering policy.
    """

    def _instruction(self, ins: UInstruction) -> None:
        if ins.op == "output_text":
            self.lines.extend([
                "    xorl %edi, %edi",
                "    call fflush@PLT",
            ])
        super()._instruction(ins)
