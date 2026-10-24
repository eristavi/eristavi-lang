from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
from .syntax import *
from .diagnostics import RuntimeFault
from .unicode_support import grapheme_clusters, nfc

class _NoneValue: pass
NONE=_NoneValue()
class _NoValue: pass
NO_RUNTIME=_NoValue()

@dataclass
class UserValue:
    type_name:str
    fields:dict[str,object]
@dataclass
class IdentityValue:
    target:UserValue
@dataclass
class ListValue:
    items:list[object]
@dataclass
class FileResource:
    path:str
    handle:object
@dataclass
class Cell:
    value:object
    fixed:bool=False
@dataclass
class CheckedFailure(Exception):
    error:UserValue
@dataclass
class ReturnSignal(Exception):
    value:object


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
        if isinstance(s,AssignmentStmt): self._assign(s.target,self._expr(s.value),s.location); return
        if isinstance(s,ExprStmt): self._expr(s.expression); return
        if isinstance(s,BlockStmt): self._block(s); return
        if isinstance(s,IfStmt):
            if self._truth(self._expr(s.condition),s.condition.location): self._block(s.then_branch)
            elif s.else_branch is not None: self._block(s.else_branch)
            return
        if isinstance(s,WhileStmt):
            while self._truth(self._expr(s.condition),s.condition.location): self._block(s.body)
            return
        if isinstance(s,ForStmt):
            src=self._expr(s.source)
            if not isinstance(src,ListValue): raise RuntimeFault("for requires List",s.source.location)
            snapshot=copy_value(src)
            for item in snapshot.items:
                self.scopes.append({s.name:Cell(copy_value(item),True)})
                try: self._block(s.body,False)
                finally: self.scopes.pop()
            return
        if isinstance(s,WithStmt):
            resource=self._expr(s.initializer)
            if not isinstance(resource,FileResource): raise RuntimeFault("with requires resource",s.location)
            self.scopes.append({s.name:Cell(resource,True)})
            primary=None
            try:
                try: self._block(s.body,False)
                except BaseException as ex: primary=ex
                try: resource.handle.close()
                except OSError as ex:
                    if primary is None: raise CheckedFailure(file_error(str(ex),resource.path))
            finally: self.scopes.pop()
            if primary is not None: raise primary
            return
        raise RuntimeFault("unsupported statement",s.location)
    def _block(self,b,push=True):
        if push: self.scopes.append({})
        try:
            for s in b.statements: self._statement(s)
        finally:
            if push: self.scopes.pop()
    def _find_cell(self,name,loc):
        for scope in reversed(self.scopes):
            if name in scope: return scope[name]
        raise RuntimeFault(f"unknown name {name!r}",loc)
    def _expr(self,e):
        if isinstance(e,LiteralExpr): return NONE if e.value is None else e.value
        if isinstance(e,NameExpr): return copy_value(self._find_cell(e.name,e.location).value)
        if isinstance(e,ListExpr): return ListValue([copy_value(self._expr(x)) for x in e.items])
        if isinstance(e,ConstructExpr):
            return UserValue(e.type_ref.name,{n:copy_value(self._expr(x)) for n,x in e.fields})
        if isinstance(e,IdentityExpr):
            v=self._expr(e.value)
            if isinstance(v,IdentityValue): return v
            if not isinstance(v,UserValue): raise RuntimeFault("identity requires user value",e.location)
            return IdentityValue(v)
        if isinstance(e,TryExpr): return self._expr(e.value)
        if isinstance(e,HandledExpr): return self._handled(e)
        if isinstance(e,UnaryExpr):
            v=self._expr(e.operand)
            if e.operator=="-": return -v
            if e.operator=="not": return not self._truth(v,e.location)
        if isinstance(e,BinaryExpr): return self._binary(e)
        if isinstance(e,MemberExpr): return self._member_value(e)
        if isinstance(e,IndexExpr):
            v=self._expr(e.base); i=self._expr(e.index)
            if not isinstance(v,ListValue): raise RuntimeFault("indexing requires List",e.location)
            if i<0 or i>=len(v.items): raise RuntimeFault("List index out of bounds",e.location)
            return copy_value(v.items[i])
        if isinstance(e,CallExpr): return self._call(e)
        raise RuntimeFault("unsupported expression",e.location)
    def _truth(self,v,loc):
        if not isinstance(v,bool): raise RuntimeFault("condition requires Bool",loc)
        return v
    def _binary(self,e):
        if e.operator=="and":
            a=self._truth(self._expr(e.left),e.left.location); return a and self._truth(self._expr(e.right),e.right.location)
        if e.operator=="or":
            a=self._truth(self._expr(e.left),e.left.location); return a or self._truth(self._expr(e.right),e.right.location)
        a=self._expr(e.left); b=self._expr(e.right)
        if e.operator=="==": return equal_value(a,b)
        if e.operator=="!=": return not equal_value(a,b)
        if e.operator=="+": return a+b
        if e.operator=="-": return a-b
        if e.operator=="*": return a*b
        if e.operator=="/":
            if isinstance(a,int) and isinstance(b,int):
                if b==0: raise RuntimeFault("division by zero",e.location)
                return int(a/b)
            return a/b
        if e.operator=="%":
            if b==0: raise RuntimeFault("division by zero",e.location)
            q=int(a/b); return a-q*b
        if e.operator=="<": return a<b
        if e.operator=="<=": return a<=b
        if e.operator==">": return a>b
        if e.operator==">=": return a>=b
        raise RuntimeFault("unknown operator",e.location)
    def _member_value(self,e):
        base=self._expr(e.base)
        if isinstance(base,IdentityValue): base=base.target
        if isinstance(base,UserValue):
            if e.name not in base.fields: raise RuntimeFault(f"unknown field {e.name!r}",e.location)
            return copy_value(base.fields[e.name])
        if isinstance(base,ListValue) and e.name=="count": return len(base.items)
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
            # Preserve the active runtime composition when entering imported
            # Eristavi modules.  Using the base Interpreter here would silently
            # drop extensions such as Unicode/Text views and future standard
            # runtime services inside module calls.
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
                        try:
                            for s in h.body.statements: self._statement(s)
                        except ReturnSignal: raise
                        return NO_RUNTIME
                    finally: self.scopes.pop()
            raise

    def _handler_name(self,t):
        if len(t.path)==1:return t.path[0]
        alias=t.path[0]
        mod=self.imported_modules.get(alias)
        return f"{mod.module_id}.{t.path[-1]}" if mod is not None else ".".join(t.path)
    def _eval_ref(self,e):
        if isinstance(e,NameExpr): return self._find_cell(e.name,e.location).value
        if isinstance(e,MemberExpr):
            base=self._eval_ref(e.base)
            if isinstance(base,IdentityValue): base=base.target
            if isinstance(base,UserValue): return base.fields[e.name]
        if isinstance(e,IndexExpr):
            base=self._eval_ref(e.base); idx=self._expr(e.index)
            if isinstance(base,ListValue): return base.items[idx]
        return self._expr(e)
    def _assign(self,target,value,loc):
        if isinstance(target,NameExpr):
            c=self._find_cell(target.name,loc)
            if c.fixed: raise RuntimeFault("cannot assign to fixed binding",loc)
            c.value=copy_value(value); return
        if isinstance(target,MemberExpr):
            base=self._eval_ref(target.base)
            if isinstance(base,IdentityValue): base=base.target
            if not isinstance(base,UserValue): raise RuntimeFault("field assignment requires value",loc)
            base.fields[target.name]=copy_value(value); return
        if isinstance(target,IndexExpr):
            base=self._eval_ref(target.base); idx=self._expr(target.index)
            if not isinstance(base,ListValue): raise RuntimeFault("index assignment requires List",loc)
            if idx<0 or idx>=len(base.items): raise RuntimeFault("List index out of bounds",loc)
            base.items[idx]=copy_value(value); return
        raise RuntimeFault("invalid assignment target",loc)
    def _format(self,v):
        if v is NONE:return "none"
        if isinstance(v,bool):return "true" if v else "false"
        if isinstance(v,float):return format(v,'.15g')
        if isinstance(v,ListValue):return "["+", ".join(self._format(x) for x in v.items)+"]"
        if isinstance(v,IdentityValue):return f"identity {self._format(v.target)}"
        if isinstance(v,UserValue):return f"{v.type_name} {{"+", ".join(f"{k}={self._format(x)}" for k,x in v.fields.items())+"}}"
        return str(v)

def file_error(message,path): return UserValue("std.files.FileError",{"message":str(message),"path":str(path)})
