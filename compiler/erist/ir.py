from __future__ import annotations
from dataclasses import dataclass
from .diagnostics import SemanticError, SourceLocation
from .syntax import *
from .typesys import describe, resolve, NoValueType

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

class IRStmt: pass
@dataclass(frozen=True)
class IRLet(IRStmt): name: str; type_name: str; fixed: bool; value: IRExpr; location: SourceLocation
@dataclass(frozen=True)
class IRAssign(IRStmt): name: str; value: IRExpr; location: SourceLocation
@dataclass(frozen=True)
class IRExprStmt(IRStmt): expression: IRExpr
@dataclass(frozen=True)
class IRIf(IRStmt): condition: IRExpr; then_body: list[IRStmt]; else_body: list[IRStmt]; location: SourceLocation
@dataclass(frozen=True)
class IRWhile(IRStmt): condition: IRExpr; body: list[IRStmt]; location: SourceLocation
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
    """Lower the currently supported scalar/control subset to typed Eristavi IR.

    The IR is deliberately machine-independent and structured for the first backend.
    Later lowering passes may make control flow more explicit without changing source semantics.
    """
    def __init__(self,analyzer): self.a=analyzer
    def lower(self,program:Program)->IRProgram:
        fns=[]; entry=[]
        for s in program.statements:
            if isinstance(s,(ImportDecl,TypeDecl,ErrorDecl)):
                if isinstance(s,ImportDecl): raise SemanticError("the first C backend does not yet lower imports",s.location)
                # declarations unused by scalar IR are allowed only when not referenced; conservatively reject.
                raise SemanticError("the first typed IR backend currently supports scalar programs only; user-defined types/errors remain on the bootstrap runtime",s.location)
            if isinstance(s,FunctionDecl): fns.append(self._function(s))
            else: entry.append(self._stmt(s))
        return IRProgram(fns,entry)
    def _function(self,f:FunctionDecl):
        if any(p.type_annotation is None for p in f.parameters): raise SemanticError("the first C backend requires concrete function parameter types; inferred-generic functions remain supported by the bootstrap runtime",f.location)
        sym=self.a.functions[f.name]
        specs=[x for x in sym.specializations.values() if x.state=="done"]
        if not specs: raise SemanticError(f"function {f.name!r} has no analyzed specialization",f.location)
        rt=resolve(specs[0].return_type)
        ret=None if isinstance(rt,NoValueType) else describe(rt)
        params=[IRParameter(p.name,describe(self.a._resolve_type_ref(p.type_annotation))) for p in f.parameters]
        return IRFunction(f.name,params,ret,[self._stmt(s) for s in f.body.statements],f.public)
    def _stmt(self,s):
        if isinstance(s,LetStmt):
            t=describe(resolve(self.a.expr_types[id(s.initializer)])); self._scalar(t,s.location)
            return IRLet(s.name,t,s.fixed,self._expr(s.initializer),s.location)
        if isinstance(s,AssignStmt):
            if not isinstance(s.target,NameExpr): raise SemanticError("the first C backend currently lowers only direct-name assignment",s.location)
            return IRAssign(s.target.name,self._expr(s.value),s.location)
        if isinstance(s,ExprStmt): return IRExprStmt(self._expr(s.expression))
        if isinstance(s,IfStmt): return IRIf(self._expr(s.condition),[self._stmt(x) for x in s.then_branch.statements],[self._stmt(x) for x in (s.else_branch.statements if s.else_branch else [])],s.location)
        if isinstance(s,WhileStmt): return IRWhile(self._expr(s.condition),[self._stmt(x) for x in s.body.statements],s.location)
        if isinstance(s,ReturnStmt): return IRReturn(self._expr(s.value) if s.value else None,s.location)
        raise SemanticError(f"the first typed IR backend does not yet lower {type(s).__name__}",getattr(s,"location",None))
    def _expr(self,e):
        t=describe(resolve(self.a.expr_types[id(e)]));
        if t!="no-value": self._scalar(t,e.location)
        if isinstance(e,LiteralExpr): return IRConst(t,e.location,e.value)
        if isinstance(e,NameExpr): return IRVar(t,e.location,e.name)
        if isinstance(e,UnaryExpr): return IRUnary(t,e.location,e.operator,self._expr(e.operand))
        if isinstance(e,BinaryExpr):
            if t=="Text" and e.operator=="+": raise SemanticError("Text concatenation is not yet lowered by the first C backend",e.location)
            return IRBinary(t,e.location,self._expr(e.left),e.operator,self._expr(e.right))
        if isinstance(e,CallExpr) and isinstance(e.callee,NameExpr): return IRCall(t,e.location,e.callee.name,[self._expr(a) for a in e.arguments])
        raise SemanticError(f"the first typed IR backend does not yet lower expression {type(e).__name__}",getattr(e,"location",None))
    @staticmethod
    def _scalar(t,loc):
        if t not in ("Int","Float","Bool","Text","no-value"): raise SemanticError(f"the first C backend currently supports scalar types only, got {t}",loc)
