from __future__ import annotations
from dataclasses import dataclass
from .diagnostics import SemanticError, SourceLocation
from .syntax import *
from .typesys import describe, resolve, NoValueType, ListType

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

class IRStmt: pass
@dataclass(frozen=True)
class IRLet(IRStmt): name: str; type_name: str; fixed: bool; value: IRExpr; location: SourceLocation
@dataclass(frozen=True)
class IRAssign(IRStmt): name: str; value: IRExpr; location: SourceLocation
@dataclass(frozen=True)
class IRIndexAssign(IRStmt): name: str; index: IRExpr; value: IRExpr; location: SourceLocation
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
class IRFunction:
    name: str
    parameters: list[IRParameter]
    return_type: str|None
    body: list[IRStmt]
    public: bool=False
@dataclass(frozen=True)
class IRProgram:
    functions: list[IRFunction]
    entry: list[IRStmt]

class Lowerer:
    """Lower the currently supported concrete subset to typed Eristavi IR.

    The IR remains machine-independent and structured. Lists are represented semantically;
    target backends choose their storage and copy-on-mutation strategy.
    """
    def __init__(self,analyzer): self.a=analyzer
    def lower(self,program:Program)->IRProgram:
        fns=[]; entry=[]
        for s in program.statements:
            if isinstance(s,(ImportDecl,TypeDecl,ErrorDecl)):
                if isinstance(s,ImportDecl): raise SemanticError("the current C backend does not yet lower imports",s.location)
                raise SemanticError("the current typed IR backend does not yet lower user-defined types/errors",s.location)
            if isinstance(s,FunctionDecl): fns.append(self._function(s))
            else: entry.append(self._stmt(s))
        return IRProgram(fns,entry)
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
        return IRFunction(f.name,params,ret,[self._stmt(s) for s in f.body.statements],f.public)
    def _stmt(self,s):
        if isinstance(s,LetStmt):
            t=describe(resolve(self.a.expr_types[id(s.initializer)])); self._supported_type(t,s.location)
            return IRLet(s.name,t,s.fixed,self._expr(s.initializer),s.location)
        if isinstance(s,AssignStmt):
            if isinstance(s.target,NameExpr): return IRAssign(s.target.name,self._expr(s.value),s.location)
            if isinstance(s.target,IndexExpr) and isinstance(s.target.base,NameExpr):
                return IRIndexAssign(s.target.base.name,self._expr(s.target.index),self._expr(s.value),s.location)
            raise SemanticError("the current C backend lowers assignment to names and direct List indexes",s.location)
        if isinstance(s,ExprStmt): return IRExprStmt(self._expr(s.expression))
        if isinstance(s,IfStmt): return IRIf(self._expr(s.condition),[self._stmt(x) for x in s.then_branch.statements],[self._stmt(x) for x in (s.else_branch.statements if s.else_branch else [])],s.location)
        if isinstance(s,WhileStmt): return IRWhile(self._expr(s.condition),[self._stmt(x) for x in s.body.statements],s.location)
        if isinstance(s,ForStmt): return IRFor(s.name,self._expr(s.iterable),[self._stmt(x) for x in s.body.statements],s.location)
        if isinstance(s,ReturnStmt): return IRReturn(self._expr(s.value) if s.value else None,s.location)
        raise SemanticError(f"the current typed IR backend does not yet lower {type(s).__name__}",getattr(s,"location",None))
    def _expr(self,e):
        t=describe(resolve(self.a.expr_types[id(e)]))
        if t!="no-value": self._supported_type(t,e.location)
        if isinstance(e,LiteralExpr): return IRConst(t,e.location,e.value)
        if isinstance(e,NameExpr): return IRVar(t,e.location,e.name)
        if isinstance(e,ListExpr): return IRList(t,e.location,[self._expr(x) for x in e.elements])
        if isinstance(e,IndexExpr): return IRIndex(t,e.location,self._expr(e.base),self._expr(e.index))
        if isinstance(e,MemberExpr) and e.name=="count": return IRCount(t,e.location,self._expr(e.base))
        if isinstance(e,UnaryExpr): return IRUnary(t,e.location,e.operator,self._expr(e.operand))
        if isinstance(e,BinaryExpr):
            if t=="Text" and e.operator=="+": raise SemanticError("Text concatenation is not yet lowered by the current C backend",e.location)
            return IRBinary(t,e.location,self._expr(e.left),e.operator,self._expr(e.right))
        if isinstance(e,CallExpr):
            if isinstance(e.callee,NameExpr): return IRCall(t,e.location,e.callee.name,[self._expr(a) for a in e.arguments])
            if isinstance(e.callee,MemberExpr) and e.callee.name=="add" and isinstance(e.callee.base,NameExpr):
                if len(e.arguments)!=1: raise SemanticError("List.add lowering expects one argument",e.location)
                return IRListAdd(t,e.location,e.callee.base.name,self._expr(e.arguments[0]))
        raise SemanticError(f"the current typed IR backend does not yet lower expression {type(e).__name__}",getattr(e,"location",None))
    @staticmethod
    def _supported_type(t,loc):
        if t in ("Int","Float","Bool","Text","no-value"): return
        if t.startswith("List of ") and t[8:] in ("Int","Float","Bool","Text"): return
        raise SemanticError(f"the current C backend supports scalar types and Lists of scalar values, got {t}",loc)
