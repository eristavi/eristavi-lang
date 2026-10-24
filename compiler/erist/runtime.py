from __future__ import annotations
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from .diagnostics import RuntimeFault
from .syntax import *

INT_MIN=-(2**63); INT_MAX=2**63-1
STD_FILE_ERROR="std.files.FileError"

class _NoneValue:
    def __repr__(self): return "none"
NONE=_NoneValue()
class _NoValue: pass
NO_RUNTIME=_NoValue()

@dataclass
class ListValue: items:list[object]
@dataclass
class UserValue: type_name:str; fields:dict[str,object]
@dataclass
class IdentityValue: value:object
@dataclass
class Cell: value:object; fixed:bool; resource:bool=False

class ReturnSignal(Exception):
    def __init__(self,value=NO_RUNTIME): self.value=value
class CheckedFailure(Exception):
    def __init__(self,error:UserValue,secondary=None): self.error=error; self.secondary=list(secondary or [])

class FileResource:
    def __init__(self,path:str,handle): self.path=path; self.handle=handle; self.closed=False
    def cleanup(self):
        if self.closed: return
        try: self.handle.close(); self.closed=True
        except OSError as e: raise CheckedFailure(file_error(str(e),self.path))

def file_error(message,path=""): return UserValue(STD_FILE_ERROR,{"message":message,"path":path})

def copy_value(v):
    if isinstance(v,(int,float,str,bool,_NoneValue,_NoValue)): return v
    if isinstance(v,IdentityValue): return v
    if isinstance(v,ListValue): return ListValue([copy_value(x) for x in v.items])
    if isinstance(v,UserValue): return UserValue(v.type_name,{k:copy_value(x) for k,x in v.fields.items()})
    if isinstance(v,FileResource): raise RuntimeFault("resource handles cannot be copied")
    return v

def equal_value(a,b):
    if a is NONE or b is NONE: return a is b
    if isinstance(a,IdentityValue) or isinstance(b,IdentityValue): return isinstance(a,IdentityValue) and isinstance(b,IdentityValue) and a is b
    if isinstance(a,ListValue) and isinstance(b,ListValue): return len(a.items)==len(b.items) and all(equal_value(x,y) for x,y in zip(a.items,b.items))
    if isinstance(a,UserValue) and isinstance(b,UserValue): return a.type_name==b.type_name and a.fields.keys()==b.fields.keys() and all(equal_value(a.fields[k],b.fields[k]) for k in a.fields)
    return a==b

class Interpreter:
    def __init__(self,output:Callable[[str],None]=print,module_id: str = "", imported_modules: dict[str,object] | None = None):
        self.scopes=[{}]; self.output_sink=output; self.functions={}; self.imports={}; self.structs={}
        self.module_id=module_id; self.imported_modules=imported_modules or {}
    def _prepare(self,program:Program):
        self.functions={s.name:s for s in program.statements if isinstance(s,FunctionDecl)}
        self.structs={s.name:s for s in program.statements if isinstance(s,(TypeDecl,ErrorDecl))}
        self.imports={(s.alias or s.path[-1]):s.path for s in program.statements if isinstance(s,ImportDecl)}
    def run(self,program:Program):
        self._prepare(program)
        for s in program.statements:
            if isinstance(s,(FunctionDecl,TypeDecl,ErrorDecl,ImportDecl)): continue
            self._statement(s)

    def _statement(self,s):
        if isinstance(s,ReturnStmt): raise ReturnSignal(NO_RUNTIME if s.value is None else copy_value(self._expr(s.value)))
        if isinstance(s,FailStmt):
            v=self._expr(s.value)
            if not isinstance(v,UserValue): raise RuntimeFault("fail requires an error value",s.location)
            raise CheckedFailure(v)
        if isinstance(s,LetStmt): self.scopes[-1][s.name]=Cell(copy_value(self._expr(s.initializer)),s.fixed); return
        if isinstance(s,AssignStmt): self._assign(s.target,copy_value(self._expr(s.value))); return
        if isinstance(s,ExprStmt): self._expr(s.expression); return
        if isinstance(s,IfStmt):
            if self._expr(s.condition): self._block(s.then_branch)
            elif s.else_branch is not None: self._block(s.else_branch)
            return
        if isinstance(s,WhileStmt):
            while self._expr(s.condition): self._block(s.body)
            return
        if isinstance(s,ForStmt):
            src=self._expr(s.iterable)
            if not isinstance(src,ListValue): raise RuntimeFault("for/in requires List",s.location)
            snapshot=[copy_value(x) for x in src.items]
            for item in snapshot:
                self.scopes.append({s.name:Cell(copy_value(item),False)})
                try:
                    for st in s.body.statements: self._statement(st)
                finally: self.scopes.pop()
            return
        if isinstance(s,WithStmt): return self._with(s)
        raise RuntimeFault("statement is not implemented by runtime",getattr(s,"location",None))

    def _block(self,b):
        self.scopes.append({})
        try:
            for s in b.statements: self._statement(s)
        finally: self.scopes.pop()

    def _with(self,s):
        res=self._expr(s.resource)
        if not isinstance(res,FileResource): raise RuntimeFault("with requires a deterministic resource",s.location)
        self.scopes.append({s.name:Cell(res,True,True)}); pending=None
        try:
            try:
                for st in s.body.statements: self._statement(st)
            except (ReturnSignal,CheckedFailure,RuntimeFault) as e: pending=e
            try: res.cleanup()
            except CheckedFailure as cleanup:
                if isinstance(pending,CheckedFailure): pending.secondary.append(cleanup.error); pending.secondary.extend(cleanup.secondary)
                else: pending=cleanup
        finally: self.scopes.pop()
        if pending is not None: raise pending

    def _expr(self,e):
        if isinstance(e,LiteralExpr): return e.value
        if isinstance(e,NoneExpr): return NONE
        if isinstance(e,ListExpr): return ListValue([copy_value(self._expr(x)) for x in e.elements])
        if isinstance(e,NameExpr):
            cell=self._resolve_cell(e.name)
            if cell is not None:
                if cell.resource: return cell.value
                return copy_value(cell.value)
            if e.name=="output": return "<builtin output>"
            if e.name in self.imports: return ("module",e.name)
            raise RuntimeFault(f"unknown name {e.name!r}",e.location)
        if isinstance(e,IdentityExpr): return IdentityValue(copy_value(self._expr(e.value)))
        if isinstance(e,TryExpr): return self._expr(e.value)
        if isinstance(e,HandledExpr): return self._handled(e)
        if isinstance(e,UnaryExpr):
            v=self._expr(e.operand)
            if e.operator=="not": return not v
            if e.operator=="-":
                r=-v
                return self._check_int(r,e) if isinstance(v,int) and not isinstance(v,bool) else r
        if isinstance(e,BinaryExpr): return self._binary(e)
        if isinstance(e,MemberExpr): return self._member_value(e)
        if isinstance(e,IndexExpr):
            base=self._expr(e.base); idx=self._expr(e.index)
            if not isinstance(base,ListValue): raise RuntimeFault("indexing requires List",e.location)
            if idx<0 or idx>=len(base.items): raise RuntimeFault("List index out of bounds",e.location)
            return copy_value(base.items[idx])
        if isinstance(e,ConstructionExpr):
            return UserValue(self._runtime_type_name(e.type_path),{f.name:copy_value(self._expr(f.value)) for f in e.fields})
        if isinstance(e,CallExpr): return self._call(e)
        raise RuntimeFault("expression is not implemented by runtime",getattr(e,"location",None))

    def _binary(self,e):
        if e.operator=="and":
            l=self._expr(e.left); return bool(l) and bool(self._expr(e.right))
        if e.operator=="or":
            l=self._expr(e.left); return bool(l) or bool(self._expr(e.right))
        l=self._expr(e.left); r=self._expr(e.right); op=e.operator
        if op=="+":
            result=l+r; return self._checked_numeric(result,l,e)
        if op=="-": return self._checked_numeric(l-r,l,e)
        if op=="*": return self._checked_numeric(l*r,l,e)
        if op=="/":
            if isinstance(l,int) and not isinstance(l,bool): return self._int_div(l,r,e)
            return self._float_div(float(l),float(r))
        if op=="%": return self._int_rem(int(l),int(r),e)
        if op=="==": return equal_value(l,r)
        if op=="!=": return not equal_value(l,r)
        if op=="<": return l<r
        if op=="<=": return l<=r
        if op==">": return l>r
        if op==">=": return l>=r
        raise RuntimeFault(f"unknown operator {op}",e.location)

    def _member_value(self,e):
        if isinstance(e.base,NameExpr) and e.base.name in self.imports: return ("module-member",e.base.name,e.name)
        base=self._expr(e.base)
        if isinstance(base,IdentityValue): base=base.value
        if isinstance(base,ListValue):
            if e.name=="count": return len(base.items)
            if e.name=="add": return ("list-add",e.base)
        if isinstance(base,UserValue):
            if e.name not in base.fields: raise RuntimeFault(f"{base.type_name} has no field {e.name!r}",e.location)
            return copy_value(base.fields[e.name])
        if isinstance(base,FileResource): return ("file-method",e.base,e.name)
        raise RuntimeFault(f"member access is not defined for runtime value",e.location)

    def _call(self,e):
        if isinstance(e.callee,NameExpr) and e.callee.name=="output":
            v=self._expr(e.arguments[0]); self.output_sink(self._format(v)); return NO_RUNTIME
        if isinstance(e.callee,MemberExpr) and e.callee.name=="add":
            lst=self._eval_ref(e.callee.base)
            if not isinstance(lst,ListValue): raise RuntimeFault("List.add requires List",e.location)
            lst.items.append(copy_value(self._expr(e.arguments[0]))); return NO_RUNTIME
        if isinstance(e.callee,MemberExpr) and isinstance(e.callee.base,NameExpr) and e.callee.base.name in self.imports and self.imports[e.callee.base.name]==("std","files"):
            if e.callee.name=="open":
                path=self._expr(e.arguments[0])
                try: handle=open(path,"r+",encoding="utf-8")
                except OSError as ex: raise CheckedFailure(file_error(str(ex),path))
                return FileResource(path,handle)
        if isinstance(e.callee,MemberExpr) and isinstance(e.callee.base,NameExpr) and e.callee.base.name in self.imported_modules:
            mod=self.imported_modules[e.callee.base.name]
            fn=next((x for x in mod.program.statements if isinstance(x,FunctionDecl) and x.name==e.callee.name and x.public),None)
            if fn is None: raise RuntimeFault(f"module {e.callee.base.name!r} has no public function {e.callee.name!r}",e.location)
            child=type(self)(self.output_sink,mod.module_id,mod.imports)
            child._prepare(mod.program)
            return child._call_function(fn,[self._expr(a) for a in e.arguments])
        if isinstance(e.callee,MemberExpr):
            base=self._eval_ref(e.callee.base)
            if isinstance(base,FileResource):
                try:
                    if e.callee.name=="readText": base.handle.seek(0); return base.handle.read()
                    if e.callee.name=="writeText":
                        text=self._expr(e.arguments[0]); base.handle.seek(0); base.handle.write(text); base.handle.truncate(); base.handle.flush(); return NO_RUNTIME
                except OSError as ex: raise CheckedFailure(file_error(str(ex),base.path))
        if isinstance(e.callee,NameExpr) and e.callee.name in self.functions:
            return self._call_function(self.functions[e.callee.name],[self._expr(a) for a in e.arguments])
        raise RuntimeFault("unsupported call",e.location)

    def _call_function(self,fn,args):
        old=self.scopes; self.scopes=[{}]
        try:
            for p,v in zip(fn.parameters,args): self.scopes[0][p.name]=Cell(copy_value(v),False)
            try:
                for s in fn.body.statements: self._statement(s)
            except ReturnSignal as ret: return copy_value(ret.value)
            return NO_RUNTIME
        finally: self.scopes=old

    def _handled(self,e):
        try: return self._expr(e.value)
        except CheckedFailure as failure:
            for h in e.handlers:
                if h.type_ref is None or self._handler_name(h.type_ref)==failure.error.type_name:
                    self.scopes.append({"error":Cell(failure.error,False)})
                    try:
                        for s in h.block.statements: self._statement(s)
                    finally: self.scopes.pop()
                    return NO_RUNTIME
            raise
    def _runtime_type_name(self,path):
        if len(path)==1:
            return f"{self.module_id}.{path[0]}" if self.module_id else path[0]
        if len(path)==2 and path[0] in self.imported_modules:
            mod=self.imported_modules[path[0]]
            return f"{mod.module_id}.{path[1]}" if mod.module_id else path[1]
        if len(path)==2 and path[0] in self.imports and self.imports[path[0]]==("std","files"):
            return f"std.files.{path[1]}"
        return ".".join(path)
    def _handler_name(self,ref):
        path=ref.path
        if len(path)==2 and path[0] in self.imports and self.imports[path[0]]==("std","files") and path[1]=="FileError": return STD_FILE_ERROR
        return self._runtime_type_name(path)

    def _assign(self,target,value):
        if isinstance(target,NameExpr):
            cell=self._resolve_cell(target.name)
            if cell is None: raise RuntimeFault(f"unknown name {target.name!r}",target.location)
            if cell.fixed: raise RuntimeFault(f"cannot assign to fixed binding {target.name!r}",target.location)
            cell.value=copy_value(value); return
        if isinstance(target,IndexExpr):
            base=self._eval_ref(target.base); idx=self._expr(target.index)
            if not isinstance(base,ListValue): raise RuntimeFault("indexed assignment requires List",target.location)
            if idx<0 or idx>=len(base.items): raise RuntimeFault("List index out of bounds",target.location)
            base.items[idx]=copy_value(value); return
        if isinstance(target,MemberExpr):
            base=self._eval_ref(target.base)
            if isinstance(base,IdentityValue): base=base.value
            if not isinstance(base,UserValue): raise RuntimeFault("member assignment requires a user-defined value",target.location)
            base.fields[target.name]=copy_value(value); return
        raise RuntimeFault("invalid assignment target",getattr(target,"location",None))

    def _eval_ref(self,e):
        if isinstance(e,NameExpr):
            cell=self._resolve_cell(e.name)
            if cell is None: raise RuntimeFault(f"unknown name {e.name!r}",e.location)
            return cell.value
        if isinstance(e,MemberExpr):
            base=self._eval_ref(e.base)
            if isinstance(base,IdentityValue): base=base.value
            if isinstance(base,UserValue): return base.fields[e.name]
            raise RuntimeFault("member reference requires user-defined value",e.location)
        if isinstance(e,IndexExpr):
            base=self._eval_ref(e.base); idx=self._expr(e.index)
            if not isinstance(base,ListValue): raise RuntimeFault("index reference requires List",e.location)
            if idx<0 or idx>=len(base.items): raise RuntimeFault("List index out of bounds",e.location)
            return base.items[idx]
        return self._expr(e)

    def _resolve_cell(self,name):
        for s in reversed(self.scopes):
            if name in s: return s[name]
        return None
    def _checked_numeric(self,result,left,e): return self._check_int(result,e) if isinstance(left,int) and not isinstance(left,bool) else result
    def _check_int(self,v,e):
        if v<INT_MIN or v>INT_MAX: raise RuntimeFault("signed 64-bit Int overflow",e.location)
        return v
    def _int_div(self,a,b,e):
        if b==0: raise RuntimeFault("Int division by zero",e.location)
        if a==INT_MIN and b==-1: raise RuntimeFault("signed 64-bit Int overflow",e.location)
        q=abs(a)//abs(b); return -q if (a<0)!=(b<0) else q
    def _int_rem(self,a,b,e):
        if b==0: raise RuntimeFault("Int remainder by zero",e.location)
        if a==INT_MIN and b==-1: raise RuntimeFault("signed 64-bit Int overflow",e.location)
        q=self._int_div(a,b,e); return a-q*b
    @staticmethod
    def _float_div(a,b):
        if b!=0.0: return a/b
        if math.isnan(a) or a==0.0: return math.nan
        return math.copysign(math.inf,math.copysign(1.0,a)*math.copysign(1.0,b))
    @staticmethod
    def _format(v):
        if isinstance(v,bool): return "true" if v else "false"
        if v is NONE: return "none"
        return str(v)