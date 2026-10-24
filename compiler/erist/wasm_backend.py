from __future__ import annotations

import hashlib

from .universal_ir import BOOL, F64, I64, UBranch, UJump, UProgram, UReturn


class WebAssemblyTextBackend:
    """Direct WebAssembly text backend for the scalar/function IR slice.

    Checked Int operations are runtime imports instead of raw `i64.add`/`mul`
    so overflow/division faults remain Eristavi-defined. The emitted module is a
    portable WAT artifact with a tiny explicit host ABI; future standalone WASM
    runtime work can internalize those helpers without changing source semantics.
    """

    SUPPORTED = {
        "const_i64", "const_bool", "const_f64", "load_local", "store_local", "call",
        "neg_checked", "add_checked", "sub_checked", "mul_checked", "div_checked", "rem_checked",
        "bool_not", "cmp_eq", "cmp_ne", "cmp_lt", "cmp_le", "cmp_gt", "cmp_ge",
        "f64_neg", "f64_add", "f64_sub", "f64_mul", "f64_div",
        "f64_cmp_eq", "f64_cmp_ne", "f64_cmp_lt", "f64_cmp_le", "f64_cmp_gt", "f64_cmp_ge",
        "output_i64", "output_bool", "output_f64",
    }

    @staticmethod
    def _symbol(name: str) -> str:
        return "$f_" + hashlib.sha1(name.encode("utf-8")).hexdigest()[:12]

    @staticmethod
    def _wasm_type(type_name: str) -> str:
        if type_name == I64: return "i64"
        if type_name == F64: return "f64"
        if type_name == BOOL: return "i32"
        if type_name == "void": return ""
        raise ValueError(f"WebAssembly scalar backend does not support type {type_name!r}")

    def emit(self, program: UProgram) -> str:
        names = {fn.name for fn in program.functions}
        if program.entry not in names:
            raise ValueError("Universal program has no WebAssembly entry function")
        lines = [
            "(module",
            '  (import "eristavi" "i64_neg_checked" (func $eri_neg (param i64) (result i64)))',
            '  (import "eristavi" "i64_add_checked" (func $eri_add (param i64 i64) (result i64)))',
            '  (import "eristavi" "i64_sub_checked" (func $eri_sub (param i64 i64) (result i64)))',
            '  (import "eristavi" "i64_mul_checked" (func $eri_mul (param i64 i64) (result i64)))',
            '  (import "eristavi" "i64_div_checked" (func $eri_div (param i64 i64) (result i64)))',
            '  (import "eristavi" "i64_rem_checked" (func $eri_rem (param i64 i64) (result i64)))',
            '  (import "eristavi" "output_i64" (func $eri_out_i64 (param i64)))',
            '  (import "eristavi" "output_bool" (func $eri_out_bool (param i32)))',
            '  (import "eristavi" "output_f64" (func $eri_out_f64 (param f64)))',
        ]
        for fn in program.functions:
            lines.extend(self._function(fn, names))
        lines.append(f"  (export \"_start\" (func {self._symbol(program.entry)}))")
        lines.append(")")
        lines.append("")
        return "\n".join(lines)

    def _function(self, fn, names):
        result_type = self._wasm_type(fn.return_type)
        params = " ".join(f"(param $p{i} {self._wasm_type(p.type_name)})" for i,p in enumerate(fn.parameters))
        result = f" (result {result_type})" if result_type else ""
        lines = [f"  (func {self._symbol(fn.name)} {params}{result}"]
        for local in fn.locals:
            lines.append(f"    (local $l{local.id} {self._wasm_type(local.type_name)})")
        for value_id in range(fn.value_count):
            type_name = self._value_type(fn, value_id)
            lines.append(f"    (local $v{value_id} {self._wasm_type(type_name)})")
        lines.append("    (local $pc i32)")
        for index, param in enumerate(fn.parameters):
            lines.extend([f"    local.get $p{index}", f"    local.set $l{param.id}"])
        lines.extend(["    i32.const 0", "    local.set $pc", "    (loop $dispatch"])
        block_index = {block.name: index for index, block in enumerate(fn.blocks)}
        for index, block in enumerate(fn.blocks):
            lines.extend(["      local.get $pc", f"      i32.const {index}", "      i32.eq", "      if"])
            for ins in block.instructions:
                lines.extend("        "+item for item in self._instruction(ins, names))
            term = block.terminator
            if isinstance(term, UJump):
                lines.extend([f"        i32.const {block_index[term.target]}", "        local.set $pc", "        br $dispatch"])
            elif isinstance(term, UBranch):
                lines.extend([
                    f"        local.get $v{term.condition.id}",
                    "        if",
                    f"          i32.const {block_index[term.true_target]}",
                    "        else",
                    f"          i32.const {block_index[term.false_target]}",
                    "        end",
                    "        local.set $pc",
                    "        br $dispatch",
                ])
            elif isinstance(term, UReturn):
                if term.value is not None:
                    lines.append(f"        local.get $v{term.value.id}")
                lines.append("        return")
            else:
                raise ValueError(f"WebAssembly backend cannot lower terminator in {block.name!r}")
            lines.append("      end")
        lines.extend(["      unreachable", "    )", "  )"])
        return lines

    @staticmethod
    def _value_type(fn, value_id):
        for block in fn.blocks:
            for ins in block.instructions:
                if ins.result is not None and ins.result.id == value_id:
                    return ins.result.type_name
        raise ValueError(f"Universal value %{value_id} has no producer")

    def _instruction(self, ins, names):
        op=ins.op
        if op not in self.SUPPORTED:
            raise ValueError(f"WebAssembly backend does not support Universal-IR op {op!r}")
        args=[f"local.get $v{x.id}" for x in ins.args]
        out=[]
        def finish():
            if ins.result is not None: out.append(f"local.set $v{ins.result.id}")
            return out
        if op=="const_i64": out.append(f"i64.const {int(ins.immediate)}"); return finish()
        if op=="const_bool": out.append(f"i32.const {1 if ins.immediate else 0}"); return finish()
        if op=="const_f64": out.append(f"f64.const {float(ins.immediate)!r}"); return finish()
        if op=="load_local": out.append(f"local.get $l{ins.local}"); return finish()
        if op=="store_local": return [args[0],f"local.set $l{ins.local}"]
        if op=="call":
            target=str(ins.immediate)
            if target not in names: raise ValueError(f"WebAssembly call target {target!r} is missing")
            out.extend(args); out.append(f"call {self._symbol(target)}"); return finish()
        helper={"neg_checked":"$eri_neg","add_checked":"$eri_add","sub_checked":"$eri_sub","mul_checked":"$eri_mul","div_checked":"$eri_div","rem_checked":"$eri_rem"}.get(op)
        if helper:
            out.extend(args); out.append(f"call {helper}"); return finish()
        if op=="bool_not": out.extend(args); out.append("i32.eqz"); return finish()
        if op.startswith("cmp_"):
            out.extend(args); out.append({"cmp_eq":"i64.eq","cmp_ne":"i64.ne","cmp_lt":"i64.lt_s","cmp_le":"i64.le_s","cmp_gt":"i64.gt_s","cmp_ge":"i64.ge_s"}[op]); return finish()
        if op=="f64_neg": out.extend(args); out.append("f64.neg"); return finish()
        if op in ("f64_add","f64_sub","f64_mul","f64_div"):
            out.extend(args); out.append({"f64_add":"f64.add","f64_sub":"f64.sub","f64_mul":"f64.mul","f64_div":"f64.div"}[op]); return finish()
        if op.startswith("f64_cmp_"):
            out.extend(args); out.append({"f64_cmp_eq":"f64.eq","f64_cmp_ne":"f64.ne","f64_cmp_lt":"f64.lt","f64_cmp_le":"f64.le","f64_cmp_gt":"f64.gt","f64_cmp_ge":"f64.ge"}[op]); return finish()
        if op.startswith("output_"):
            out.extend(args); out.append("call "+{"output_i64":"$eri_out_i64","output_bool":"$eri_out_bool","output_f64":"$eri_out_f64"}[op]); return out
        raise AssertionError(op)
