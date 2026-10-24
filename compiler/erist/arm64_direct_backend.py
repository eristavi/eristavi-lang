from __future__ import annotations

from .arm64_resource_backend import ARM64ResourceRuntimeLinuxBackend
from .universal_ir import UInstruction


class ARM64DirectLinuxBackend(ARM64ResourceRuntimeLinuxBackend):
    """Composed ARM64 direct backend used by the public build path.

    Scalar output is formatted through stdio while Text output is an exact-length
    raw write so embedded NUL remains valid. Flush stdio before each raw Text
    write to preserve Eristavi source-program output order, matching the x86-64
    direct runtime contract.
    """

    def _instruction(self, ins: UInstruction) -> None:
        if ins.op == "output_text":
            self.lines.extend([
                "    mov x0, #0",
                "    bl fflush",
            ])
        super()._instruction(ins)
