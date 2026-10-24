from __future__ import annotations

from .x86_64_gc_backend import X86_64GCLinuxBackend


class X86_64PreciseRootGCLinuxBackend(X86_64GCLinuxBackend):
    """Production-facing direct GC composition for the current bootstrap runtime.

    `X86_64GCLinuxBackend` now owns the single compiler-described root-frame
    implementation for both heap-typed locals and heap-typed Universal-IR spill
    slots. Keeping root construction in one place prevents the direct backend and
    this composed entry point from drifting apart.

    This layer currently retains one runtime hardening patch: the sweep cursor is
    preserved across libc `free`, whose System-V ABI permits clobbering `%rcx`.
    Root discovery is precise at compiler slots; heap child traversal still scans
    tracked allocation words by exact pointer identity and therefore remains a
    bootstrap collector rather than the final typed-descriptor collector.
    """

    @staticmethod
    def _gc_runtime() -> str:
        runtime = X86_64GCLinuxBackend._gc_runtime()
        old = '''.Leri_gc_sweep_free:\n    movq -32(%rbp), %rdi\n    call free@PLT\n    incq .Leri_gc_reclaimed(%rip)\n    movq -40(%rbp), %rax\n    jmp .Leri_gc_sweep_loop'''
        new = '''.Leri_gc_sweep_free:\n    movq %rcx, -48(%rbp)\n    movq -32(%rbp), %rdi\n    call free@PLT\n    movq -48(%rbp), %rcx\n    incq .Leri_gc_reclaimed(%rip)\n    movq -40(%rbp), %rax\n    jmp .Leri_gc_sweep_loop'''
        if old not in runtime:
            raise ValueError("GC runtime sweep template changed unexpectedly")
        return runtime.replace(old, new, 1)
