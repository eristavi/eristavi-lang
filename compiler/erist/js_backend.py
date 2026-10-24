from __future__ import annotations

import hashlib
import json
import re

from .universal_ir import BOOL, F64, I64, TEXT, UBranch, UJump, UProgram, UReturn


class JavaScriptBackend:
    """ES2020 backend for the scalar/function Universal-IR contract.

    Eristavi `Int` is emitted as JavaScript `BigInt`, never `Number`, and every
    arithmetic result is range-checked back to signed Int64. This makes the
    target implement Eristavi integer semantics rather than silently inheriting
    JavaScript numeric precision/wrapping behavior.
    """

    SUPPORTED = {
        "const_i64", "const_bool", "const_f64", "const_text",
        "load_local", "store_local", "call", "neg_checked",
        "add_checked", "sub_checked", "mul_checked", "div_checked", "rem_checked",
        "bool_not", "cmp_eq", "cmp_ne", "cmp_lt", "cmp_le", "cmp_gt", "cmp_ge",
        "f64_neg", "f64_add", "f64_sub", "f64_mul", "f64_div",
        "f64_cmp_eq", "f64_cmp_ne", "f64_cmp_lt", "f64_cmp_le", "f64_cmp_gt", "f64_cmp_ge",
        "text_concat", "text_eq", "text_ne",
        "output_i64", "output_bool", "output_f64", "output_text",
    }

    @staticmethod
    def _symbol(name: str) -> str:
        digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:12]
        return "eri_" + digest

    @staticmethod
    def _literal(value):
        return json.dumps(value, ensure_ascii=False)

    def emit(self, program: UProgram) -> str:
        names = {fn.name for fn in program.functions}
        if program.entry not in names:
            raise ValueError("Universal program has no JavaScript entry function")
        lines = [
            '"use strict";',
            "const ERI_MIN = -(1n << 63n);",
            "const ERI_MAX = (1n << 63n) - 1n;",
            "function eriI64(v){ if(v < ERI_MIN || v > ERI_MAX) throw new Error('Eristavi runtime fault: Int arithmetic overflow'); return v; }",
            "function eriDiv(a,b){ if(b===0n) throw new Error('Eristavi runtime fault: Int division by zero'); if(a===ERI_MIN && b===-1n) throw new Error('Eristavi runtime fault: Int arithmetic overflow'); return a/b; }",
            "function eriRem(a,b){ const q=eriDiv(a,b); return a-q*b; }",
            "function eriOut(v){ if(typeof v==='bigint') console.log(v.toString()); else if(typeof v==='boolean') console.log(v?'true':'false'); else console.log(String(v)); }",
        ]
        for fn in program.functions:
            lines.extend(self._function(fn, names))
        lines.append(f"{self._symbol(program.entry)}();")
        lines.append("")
        return "\n".join(lines)

    def _function(self, fn, names):
        params = [f"a{i}" for i in range(len(fn.parameters))]
        lines = [f"function {self._symbol(fn.name)}({', '.join(params)}){{"]
        lines.append(f"  const l=new Array({len(fn.locals)}); const v=new Array({fn.value_count});")
        for index, param in enumerate(fn.parameters):
            lines.append(f"  l[{param.id}]=a{index};")
        lines.append(f"  let pc={self._literal(fn.blocks[0].name)};")
        lines.append("  while(true){ switch(pc){")
        for block in fn.blocks:
            lines.append(f"    case {self._literal(block.name)}:")
            for ins in block.instructions:
                lines.extend("      " + item for item in self._instruction(ins, names))
            term = block.terminator
            if isinstance(term, UJump):
                lines.append(f"      pc={self._literal(term.target)}; continue;")
            elif isinstance(term, UBranch):
                lines.append(f"      pc=v[{term.condition.id}]?{self._literal(term.true_target)}:{self._literal(term.false_target)}; continue;")
            elif isinstance(term, UReturn):
                if term.value is None:
                    lines.append("      return;")
                else:
                    lines.append(f"      return v[{term.value.id}];")
            else:
                raise ValueError(f"JavaScript backend cannot lower terminator in {block.name!r}")
        lines.extend(["    default: throw new Error('invalid Eristavi JavaScript block');", "  }}", "}"])
        return lines

    def _instruction(self, ins, names):
        op = ins.op
        if op not in self.SUPPORTED:
            raise ValueError(f"JavaScript backend does not support Universal-IR op {op!r}")
        dst = None if ins.result is None else f"v[{ins.result.id}]"
        arg = lambda index: f"v[{ins.args[index].id}]"
        if op == "const_i64": return [f"{dst}=BigInt({self._literal(str(int(ins.immediate)))});"]
        if op == "const_bool": return [f"{dst}={'true' if ins.immediate else 'false'};"]
        if op == "const_f64":
            value=float(ins.immediate)
            if value != value: expr="NaN"
            elif value == float("inf"): expr="Infinity"
            elif value == float("-inf"): expr="-Infinity"
            else: expr=repr(value)
            return [f"{dst}={expr};"]
        if op == "const_text": return [f"{dst}={self._literal(str(ins.immediate))};"]
        if op == "load_local": return [f"{dst}=l[{ins.local}];"]
        if op == "store_local": return [f"l[{ins.local}]={arg(0)};"]
        if op == "call":
            target=str(ins.immediate)
            if target not in names: raise ValueError(f"JavaScript call target {target!r} is missing")
            call=f"{self._symbol(target)}({', '.join(f'v[{x.id}]' for x in ins.args)})"
            return [f"{dst}={call};" if dst else call+";"]
        if op == "neg_checked": return [f"{dst}=eriI64(-{arg(0)});"]
        if op in ("add_checked","sub_checked","mul_checked"):
            operator={"add_checked":"+","sub_checked":"-","mul_checked":"*"}[op]
            return [f"{dst}=eriI64({arg(0)}{operator}{arg(1)});"]
        if op == "div_checked": return [f"{dst}=eriDiv({arg(0)},{arg(1)});"]
        if op == "rem_checked": return [f"{dst}=eriRem({arg(0)},{arg(1)});"]
        if op == "bool_not": return [f"{dst}=!{arg(0)};"]
        if op.startswith("cmp_"):
            operator={"cmp_eq":"===","cmp_ne":"!==","cmp_lt":"<","cmp_le":"<=","cmp_gt":">","cmp_ge":">="}[op]
            return [f"{dst}=({arg(0)}{operator}{arg(1)});"]
        if op == "f64_neg": return [f"{dst}=-{arg(0)};"]
        if op.startswith("f64_") and op in ("f64_add","f64_sub","f64_mul","f64_div"):
            operator={"f64_add":"+","f64_sub":"-","f64_mul":"*","f64_div":"/"}[op]
            return [f"{dst}={arg(0)}{operator}{arg(1)};"]
        if op.startswith("f64_cmp_"):
            operator={"f64_cmp_eq":"===","f64_cmp_ne":"!==","f64_cmp_lt":"<","f64_cmp_le":"<=","f64_cmp_gt":">","f64_cmp_ge":">="}[op]
            return [f"{dst}=({arg(0)}{operator}{arg(1)});"]
        if op == "text_concat": return [f"{dst}={arg(0)}+{arg(1)};"]
        if op in ("text_eq","text_ne"):
            operator="===" if op=="text_eq" else "!=="
            return [f"{dst}=({arg(0)}{operator}{arg(1)});"]
        if op.startswith("output_"): return [f"eriOut({arg(0)});"]
        raise AssertionError(op)
