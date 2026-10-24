from __future__ import annotations
from dataclasses import dataclass
from .diagnostics import SemanticError, SourceLocation
from .syntax import *
from .typesys import describe, resolve, NoValueType, IdentityType, MaybeType, ListType, NamedType

@dataclass(frozen=True)
class IRExpr:
    type_name: str
    location: SourceLocation
@dataclass(frozen=True)
class IRConst(IRExpr): value: object
@dataclass(frozen=True)
class IRVar(IRExpr): name: str
@dataclass(frozen=True)
class IRUnary(IRExpr): operator: str; operand: IRExpr
@dataclass(frozen=True)
class IRBinary(IRExpr): left: IRExpr; operator: str; right: IRExpr
@dataclass(frozen=True)
class IRCall(IRExpr): name: str; arguments: list[IRExpr]
@dataclass(frozen=True)
class IRList(IRExpr): elements: list[IRExpr]
@dataclass(frozen=True)
class IRIndex(IRExpr): base: IRExpr; index: IRExpr
@dataclass(frozen=True)
class IRCount(IRExpr): base: IRExpr
@dataclass(frozen=True)
class IRListAdd(IRExpr): base_name: str; value: IRExpr
@dataclass(frozen=True)
class IRFieldValue:
    name: str; value: IRExpr
@dataclass(frozen=True)
class IRConstruct(IRExpr): fields: list[IRFieldValue]
@dataclass(frozen=True)
class IRMember(IRExpr): base: IRExpr; name: str
@dataclass(frozen=True)
class IRIdentity(IRExpr): value: IRExpr
@dataclass(frozen=True)
class IRMaybeNone(IRExpr): pass
@dataclass(frozen=True)
class IRMaybeSome(IRExpr): value: IRExpr
@dataclass(frozen=True)
class IRMaybeGet(IRExpr): value: IRExpr

class IRStmt: pass
@dataclass(frozen=True)
class IRLet(IRStmt): name: str; type_name: str; fixed: bool; value: IRExpr; location: SourceLocation
@dataclass(frozen=True)
class IRAssign(IRStmt): name: str; type_name: str; value: IRExpr; location: SourceLocation
@dataclass(frozen=True)
class IRIndexAssign(IRStmt): name: str; index: IRExpr; value: IRExpr; location: SourceLocation
@dataclass(frozen=True)
class IRMemberAssign(IRStmt): target: IRMember; value: IRExpr; location: SourceLocation
@dataclass(frozen=True)
class IRExprStmt(IRStmt): expression: IRExpr
@dataclass(frozen=True)
class IRIf(IRStmt): condition: IRExpr; then_body: list[IRStmt]; else_body: list[IRStmt]; location: SourceLocation
@dataclass(frozen=True)
class IRWhile(IRStmt): condition: IRExpr; body: list[IRStmt]; location: SourceLocation
@dataclass(frozen=True)
class IRFor(IRStmt): name: str; iterable: IRExpr; body: list[IRStmt]; location: SourceLocation
@dataclass(frozen=True)
class IRReturn(IRStmt): value: IRExpr|None; location: SourceLocation

@dataclass(frozen=True)
class IRParameter: name: str; type_name: str
@dataclass(frozen=True)
class IRStructField: name: str; type_name: str; fixed: bool=False
@dataclass(frozen=True)
class IRStruct: name: str; fields: list[IRStructField]
@dataclass(frozen=True)
class IRFunction:
    name: str
    parameters: list[IRParameter]
    return_type: str|None
    body: list[IRStmt]
    public: bool=False
@dataclass(frozen=True)
class IRProgram:
    structs: list[IRStruct]
    functions: list[IRFunction]
    entry: list[IRStmt]

class Lowerer:
    """Lower the currently compiled concrete subset to typed, storage-aware Eristavi IR."""
    def __init__(self,analyzer):
        self.a=analyzer
        self.scopes:list[dict[str,str]]=[{}]
        self.current_return:str|None=None
    def lower(self,program:Program)->IRProgram:
        structs=[]; fns=[]; entry=[]
        for s in program.statements:
            if isinstance(s,ImportDecl): raise SemanticError("the current C backend does not yet lower imports",s.location)
            if isinstance(s,ErrorDecl): raise SemanticError("the current typed IR backend does not yet lower checked errors",s.location)
            if isinstance(s,TypeDecl):
                canonical=self.a.local_types[s.name]; info=self.a.structs[canonical]
                fields=[]
                for f in info.fields.values():
                    tn=describe(resolve(f.type)); self._supported_type(tn,s.location)
                    fields.append(IRStructField(f.name,tn,f.fixed))
                structs.append(IRStruct(canonical,fields)); continue
            if isinstance(s,FunctionDecl): fns.append(self._function(s))
            else: entry.append(self._stmt(s))
        return IRProgram(structs,fns,entry)
    def _function(self,f:FunctionDecl):
        if any(p.type_annotation is None for p in f.parameters):
            raise SemanticError("the current C backend requires concrete function parameter types; inferred-generic specialization lowering is not implemented yet",f.location)
        sym=self.a.functions[f.name]
        specs=[x for x in sym.specializations.values() if x.state=="done"]
        if not specs: raise SemanticError(f"function {f.name!r} has no analyzed specialization",f.location)
        rt=resolve(specs[0].return_type)
        ret=None if isinstance(rt,NoValueType) else describe(rt)
        params=[IRParameter(p.name,describe(self.a._resolve_type_ref(p.type_annotation))) for p in f.parameters]
        for p in params: self._supported_type(p.type_name,f.location)
        if ret is not None: self._supported_type(ret,f.location)
        old_scopes=self.scopes; old_ret=self.current_return
        self.scopes=[{p.name:p.type_name for p in params}]; self.current_return=ret
        try: body=self._lower_block(f.body,False)
        finally: self.scopes=old_scopes; self.current_return=old_ret
        return IRFunction(f.name,params,ret,body,f.public)
    def _lower_block(self,b:Block,new_scope=True,bindings:dict[str,str]|None=None):
        if new_scope: self.scopes.append(dict(bindings or {}))
        try: return [self._stmt(s) for s in b.statements]
        finally:
            if new_scope: self.scopes.pop()
    def _declare(self,name,t): self.scopes[-1][name]=t
    def _lookup(self,name):
        for s in reversed(self.scopes):
            if name in s: return s[name]
        return None
    def _stmt(self,s):
        if isinstance(s,LetStmt):
            source_t=describe(resolve(self.a.expr_types[id(s.initializer)]))
            target_t=describe(resolve(self.a._resolve_type_ref(s.type_annotation))) if s.type_annotation else source_t
            self._supported_type(target_t,s.location)
            value=self._coerce(self._expr(s.initializer),target_t,s.location)
            self._declare(s.name,target_t)
            return IRLet(s.name,target_t,s.fixed,value,s.location)
        if isinstance(s,AssignStmt):
            target_t=describe(self._ast_type(s.target)); value=self._coerce(self._expr(s.value),target_t,s.location)
            if isinstance(s.target,NameExpr): return IRAssign(s.target.name,target_t,value,s.location)
            if isinstance(s.target,IndexExpr) and isinstance(s.target.base,NameExpr): return IRIndexAssign(s.target.base.name,self._expr(s.target.index),value,s.location)
            if isinstance(s.target,MemberExpr): return IRMemberAssign(self._member_expr(s.target),value,s.location)
            raise SemanticError("the current C backend does not yet lower this assignment path",s.location)
        if isinstance(s,ExprStmt): return IRExprStmt(self._expr(s.expression))
        if isinstance(s,IfStmt): return IRIf(self._expr(s.condition),self._lower_block(s.then_branch,True),self._lower_block(s.else_branch,True) if s.else_branch else [],s.location)
        if isinstance(s,WhileStmt): return IRWhile(self._expr(s.condition),self._lower_block(s.body,True),s.location)
        if isinstance(s,ForStmt):
            it=self._expr(s.iterable); elem=list_inner(it.type_name)
            return IRFor(s.name,it,self._lower_block(s.body,True,{s.name:elem}),s.location)
        if isinstance(s,ReturnStmt):
            if s.value is None: return IRReturn(None,s.location)
            value=self._expr(s.value)
            if self.current_return is not None: value=self._coerce(value,self.current_return,s.location)
            return IRReturn(value,s.location)
        raise SemanticError(f"the current typed IR backend does not yet lower {type(s).__name__}",getattr(s,"location",None))
    def _ast_type(self,e:Expr):
        if isinstance(e,NameExpr):
            stored=self._lookup(e.name)
            if stored is not None: return self._type_from_name(stored)
        known=self.a.expr_types.get(id(e))
        if known is not None: return resolve(known)
        if isinstance(e,MemberExpr):
            bt=self._ast_type(e.base); base=resolve(bt.inner) if isinstance(bt,IdentityType) else bt
            if isinstance(base,MaybeType): base=resolve(base.inner)
            info=self.a.structs.get(describe(base))
            if info is None or e.name not in info.fields: raise SemanticError(f"cannot derive member type for {e.name!r}",e.location)
            return resolve(info.fields[e.name].type)
        if isinstance(e,IndexExpr):
            bt=resolve(self._ast_type(e.base))
            if isinstance(bt,ListType): return resolve(bt.element)
        raise SemanticError("cannot derive expression type during IR lowering",getattr(e,"location",None))
    def _member_expr(self,e:MemberExpr):
        t=describe(self._ast_type(e)); self._supported_type(t,e.location)
        return IRMember(t,e.location,self._expr(e.base),e.name)
    def _expr(self,e):
        semantic_t=describe(resolve(self.a.expr_types[id(e)]))
        if semantic_t!="no-value": self._supported_type(semantic_t,e.location)
        if isinstance(e,LiteralExpr): return IRConst(semantic_t,e.location,e.value)
        if isinstance(e,NoneExpr): return IRMaybeNone(semantic_t,e.location)
        if isinstance(e,NameExpr):
            stored=self._lookup(e.name)
            if stored is not None and stored.startswith("maybe ") and semantic_t==maybe_inner(stored):
                return IRMaybeGet(semantic_t,e.location,IRVar(stored,e.location,e.name))
            return IRVar(semantic_t,e.location,e.name)
        if isinstance(e,ListExpr): return IRList(semantic_t,e.location,[self._expr(x) for x in e.elements])
        if isinstance(e,IndexExpr): return IRIndex(semantic_t,e.location,self._expr(e.base),self._expr(e.index))
        if isinstance(e,MemberExpr):
            if e.name=="count": return IRCount(semantic_t,e.location,self._expr(e.base))
            return self._member_expr(e)
        if isinstance(e,ConstructionExpr):
            info=self.a.structs.get(semantic_t); fields=[]
            for f in e.fields:
                expected=describe(resolve(info.fields[f.name].type)) if info else describe(resolve(self.a.expr_types[id(f.value)]))
                fields.append(IRFieldValue(f.name,self._coerce(self._expr(f.value),expected,f.location)))
            return IRConstruct(semantic_t,e.location,fields)
        if isinstance(e,IdentityExpr): return IRIdentity(semantic_t,e.location,self._expr(e.value))
        if isinstance(e,UnaryExpr): return IRUnary(semantic_t,e.location,e.operator,self._expr(e.operand))
        if isinstance(e,BinaryExpr):
            left=self._expr(e.left); right=self._expr(e.right)
            if e.operator in ("==","!="):
                if left.type_name.startswith("maybe ") and right.type_name==maybe_inner(left.type_name): right=self._coerce(right,left.type_name,e.location)
                elif right.type_name.startswith("maybe ") and left.type_name==maybe_inner(right.type_name): left=self._coerce(left,right.type_name,e.location)
            return IRBinary(semantic_t,e.location,left,e.operator,right)
        if isinstance(e,CallExpr):
            if isinstance(e.callee,NameExpr):
                fn=self.a.functions.get(e.callee.name); args=[]
                for i,a in enumerate(e.arguments):
                    av=self._expr(a)
                    if fn is not None and i<len(fn.typed_parameters) and fn.typed_parameters[i] is not None: av=self._coerce(av,describe(resolve(fn.typed_parameters[i])),a.location)
                    args.append(av)
                return IRCall(semantic_t,e.location,e.callee.name,args)
            if isinstance(e.callee,MemberExpr) and e.callee.name=="add" and isinstance(e.callee.base,NameExpr):
                if len(e.arguments)!=1: raise SemanticError("List.add lowering expects one argument",e.location)
                return IRListAdd(semantic_t,e.location,e.callee.base.name,self._expr(e.arguments[0]))
        raise SemanticError(f"the current typed IR backend does not yet lower expression {type(e).__name__}",getattr(e,"location",None))
    def _coerce(self,value:IRExpr,target:str,loc)->IRExpr:
        if value.type_name==target: return value
        if target.startswith("maybe ") and value.type_name==maybe_inner(target): return IRMaybeSome(target,loc,value)
        raise SemanticError(f"typed IR cannot coerce {value.type_name} to {target}",loc)
    @staticmethod
    def _type_from_name(t):
        if t.startswith("maybe "): return MaybeType(Lowerer._type_from_name(maybe_inner(t)))
        if t.startswith("identity "): return IdentityType(Lowerer._type_from_name(identity_inner(t)))
        if t.startswith("List of "): return ListType(Lowerer._type_from_name(list_inner(t)))
        return NamedType(t)
    @staticmethod
    def _supported_type(t,loc):
        if t in ("Int","Float","Bool","Text","no-value"): return
        if t.startswith("List of "):
            inner=list_inner(t)
            if inner.startswith("maybe "): raise SemanticError(f"the current C backend does not yet compile Lists of optional values: {t}",loc)
            Lowerer._supported_type(inner,loc); return
        if t.startswith("maybe "):
            inner=maybe_inner(t)
            if inner.startswith("List of "): raise SemanticError(f"the current C backend does not yet compile optional Lists: {t}",loc)
            Lowerer._supported_type(inner,loc); return
        if t.startswith("identity "):
            inner=identity_inner(t)
            if inner and not inner.startswith(("maybe ","identity ","List of ","<")): return
        if not t.startswith(("maybe ","identity ","<")): return
        raise SemanticError(f"the current C backend does not yet support compiled type {t}",loc)

def maybe_inner(t):
    if not t.startswith("maybe "): raise ValueError(t)
    return t[6:]
def identity_inner(t):
    if not t.startswith("identity "): raise ValueError(t)
    return t[9:]
def list_inner(t):
    if not t.startswith("List of "): raise ValueError(t)
    return t[8:]
