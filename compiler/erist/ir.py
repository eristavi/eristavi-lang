from __future__ import annotations
from dataclasses import dataclass
from .diagnostics import SemanticError, SourceLocation
from .syntax import *
from .typesys import (
    describe, resolve, has_unresolved,
    NoValueType, IdentityType, MaybeType, ListType, NamedType, AnyErrorType, ResourceType,
    INT, FLOAT, BOOL, TEXT, NO_VALUE,
)

STD_FILE="std.files.File"
STD_FILE_ERROR="std.files.FileError"

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
@dataclass(frozen=True)
class IRFileOpen(IRExpr): path: IRExpr
@dataclass(frozen=True)
class IRFileRead(IRExpr): resource: IRExpr
@dataclass(frozen=True)
class IRFileWrite(IRExpr): resource: IRExpr; text: IRExpr

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
class IRFail(IRStmt): value: IRExpr; error_type: str; location: SourceLocation
@dataclass(frozen=True)
class IRErrorHandler:
    error_type: str|None
    body: list[IRStmt]
    location: SourceLocation
@dataclass(frozen=True)
class IRHandledLet(IRStmt):
    name: str; type_name: str; fixed: bool; value: IRExpr; handlers: list[IRErrorHandler]; location: SourceLocation
@dataclass(frozen=True)
class IRHandledAssign(IRStmt):
    target: IRExpr; target_type: str; value: IRExpr; handlers: list[IRErrorHandler]; location: SourceLocation
@dataclass(frozen=True)
class IRHandledReturn(IRStmt):
    value: IRExpr; handlers: list[IRErrorHandler]; location: SourceLocation
@dataclass(frozen=True)
class IRHandledExprStmt(IRStmt):
    value: IRExpr; handlers: list[IRErrorHandler]; location: SourceLocation
@dataclass(frozen=True)
class IRWith(IRStmt):
    name: str; resource_type: str; resource: IRExpr; body: list[IRStmt]; cleanup_errors: tuple[str,...]; location: SourceLocation

@dataclass(frozen=True)
class IRParameter: name: str; type_name: str
@dataclass(frozen=True)
class IRStructField: name: str; type_name: str; fixed: bool=False
@dataclass(frozen=True)
class IRStruct:
    name: str; fields: list[IRStructField]; is_error: bool=False
@dataclass(frozen=True)
class IRFunction:
    name: str
    parameters: list[IRParameter]
    return_type: str|None
    body: list[IRStmt]
    public: bool=False
    fails: tuple[str,...]=()
@dataclass(frozen=True)
class IRProgram:
    structs: list[IRStruct]
    functions: list[IRFunction]
    entry: list[IRStmt]

class Lowerer:
    """Lower one analyzed module to concrete typed Eristavi IR."""
    def __init__(self,analyzer,module_id:str=""):
        self.a=analyzer
        self.module_id=module_id or getattr(analyzer,"module_id","")
        self.scopes:list[dict[str,str]]=[{}]
        self.current_return:str|None=None
        self.generic_context=False

    def lower(self,program:Program,include_entry:bool=True)->IRProgram:
        structs=[]; fns=[]; entry=[]
        for s in program.statements:
            if isinstance(s,ImportDecl): continue
            if isinstance(s,(TypeDecl,ErrorDecl)):
                canonical=self.a.local_types[s.name]; info=self.a.structs[canonical]
                fs=[]
                for f in info.fields.values():
                    tn=describe(resolve(f.type)); self._supported_type(tn,s.location)
                    fs.append(IRStructField(f.name,tn,f.fixed))
                structs.append(IRStruct(canonical,fs,isinstance(s,ErrorDecl))); continue
            if isinstance(s,FunctionDecl): fns.extend(self._functions(s))
            elif include_entry: entry.append(self._stmt(s))
        return IRProgram(structs,fns,entry)

    def _function_name(self,name:str)->str:
        return f"{self.module_id}.{name}" if self.module_id else name
    def _specialized_name(self,name:str,param_names:list[str])->str:
        base=self._function_name(name); return base+"$"+"$".join(param_names)
    def _concrete_specs(self,fn):
        out=[]; seen={}
        for spec in fn.specializations.values():
            if spec.state!="done": continue
            params=[resolve(t) for t in spec.parameter_types]; ret=resolve(spec.return_type or NO_VALUE)
            if any(has_unresolved(t) for t in params) or has_unresolved(ret): continue
            key=tuple(describe(t) for t in params)
            result=describe(ret)
            if key in seen:
                if seen[key]!=result:
                    raise SemanticError(f"inconsistent inferred results for function {fn.declaration.name!r}",fn.declaration.location)
                continue
            seen[key]=result
            out.append(spec)
        return out
    def _functions(self,f:FunctionDecl)->list[IRFunction]:
        fn=self.a.functions[f.name]; generic=any(p.type_annotation is None for p in f.parameters); specs=self._concrete_specs(fn)
        if not generic:
            if not specs: raise SemanticError(f"function {f.name!r} has no analyzed specialization",f.location)
            return [self._function_from_spec(f,specs[0],False)]
        return [self._function_from_spec(f,s,True) for s in specs]
    def _function_from_spec(self,f,spec,generic:bool)->IRFunction:
        params=[IRParameter(p.name,describe(resolve(t))) for p,t in zip(f.parameters,spec.parameter_types)]
        rt=resolve(spec.return_type or NO_VALUE); ret=None if isinstance(rt,NoValueType) else describe(rt)
        for p in params: self._supported_type(p.type_name,f.location)
        if ret is not None: self._supported_type(ret,f.location)
        name=self._specialized_name(f.name,[p.type_name for p in params]) if generic else self._function_name(f.name)
        old_scopes=self.scopes; old_ret=self.current_return; old_generic=self.generic_context
        self.scopes=[{p.name:p.type_name for p in params}]; self.current_return=ret; self.generic_context=generic
        try: body=self._lower_block(f.body,False)
        finally: self.scopes=old_scopes; self.current_return=old_ret; self.generic_context=old_generic
        return IRFunction(name,params,ret,body,f.public,tuple(sorted(self.a.functions[f.name].fails)))

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
    def _handlers(self,handlers:list[ErrorHandler])->list[IRErrorHandler]:
        out=[]
        for h in handlers:
            ht=None if h.type_ref is None else describe(resolve(self.a._resolve_type_ref(h.type_ref)))
            out.append(IRErrorHandler(ht,self._lower_block(h.block,True,{"error":ht or "checked error"}),h.location))
        return out

    def _stmt(self,s):
        if isinstance(s,LetStmt):
            if isinstance(s.initializer,HandledExpr):
                source_t=describe(self._expr_type(s.initializer.value)); target_t=describe(resolve(self.a._resolve_type_ref(s.type_annotation))) if s.type_annotation else source_t
                self._supported_type(target_t,s.location); value=self._coerce(self._expr(s.initializer.value),target_t,s.location); self._declare(s.name,target_t)
                return IRHandledLet(s.name,target_t,s.fixed,value,self._handlers(s.initializer.handlers),s.location)
            source_t=describe(self._expr_type(s.initializer)); target_t=describe(resolve(self.a._resolve_type_ref(s.type_annotation))) if s.type_annotation else source_t
            self._supported_type(target_t,s.location); value=self._coerce(self._expr(s.initializer),target_t,s.location); self._declare(s.name,target_t)
            return IRLet(s.name,target_t,s.fixed,value,s.location)
        if isinstance(s,AssignStmt):
            if isinstance(s.value,HandledExpr):
                target_t=describe(self._ast_type(s.target)); value=self._coerce(self._expr(s.value.value),target_t,s.location)
                return IRHandledAssign(self._assignment_target(s.target),target_t,value,self._handlers(s.value.handlers),s.location)
            target_t=describe(self._ast_type(s.target)); value=self._coerce(self._expr(s.value),target_t,s.location)
            if isinstance(s.target,NameExpr): return IRAssign(s.target.name,target_t,value,s.location)
            if isinstance(s.target,IndexExpr) and isinstance(s.target.base,NameExpr): return IRIndexAssign(s.target.base.name,self._expr(s.target.index),value,s.location)
            if isinstance(s.target,MemberExpr): return IRMemberAssign(self._member_expr(s.target),value,s.location)
            raise SemanticError("the current C backend does not yet lower this assignment path",s.location)
        if isinstance(s,ExprStmt):
            if isinstance(s.expression,HandledExpr): return IRHandledExprStmt(self._expr(s.expression.value),self._handlers(s.expression.handlers),s.location)
            return IRExprStmt(self._expr(s.expression))
        if isinstance(s,IfStmt): return IRIf(self._expr(s.condition),self._lower_block(s.then_branch,True),self._lower_block(s.else_branch,True) if s.else_branch else [],s.location)
        if isinstance(s,WhileStmt): return IRWhile(self._expr(s.condition),self._lower_block(s.body,True),s.location)
        if isinstance(s,ForStmt):
            it=self._expr(s.iterable); elem=list_inner(it.type_name); return IRFor(s.name,it,self._lower_block(s.body,True,{s.name:elem}),s.location)
        if isinstance(s,ReturnStmt):
            if s.value is None: return IRReturn(None,s.location)
            if isinstance(s.value,HandledExpr):
                value=self._expr(s.value.value)
                if self.current_return is not None: value=self._coerce(value,self.current_return,s.location)
                return IRHandledReturn(value,self._handlers(s.value.handlers),s.location)
            value=self._expr(s.value)
            if self.current_return is not None: value=self._coerce(value,self.current_return,s.location)
            return IRReturn(value,s.location)
        if isinstance(s,FailStmt):
            value=self._expr(s.value); return IRFail(value,value.type_name,s.location)
        if isinstance(s,WithStmt):
            rt=self._expr_type(s.resource); rt=resolve(rt)
            if not isinstance(rt,ResourceType): raise SemanticError("with requires a deterministic resource",s.location)
            rname=describe(rt); self._supported_type(rname,s.location)
            body=self._lower_block(s.body,True,{s.name:rname})
            return IRWith(s.name,rname,self._expr(s.resource),body,tuple(rt.cleanup_errors),s.location)
        raise SemanticError(f"the current typed IR backend does not yet lower {type(s).__name__}",getattr(s,"location",None))

    def _assignment_target(self,target:Expr)->IRExpr:
        if isinstance(target,NameExpr): return IRVar(describe(self._ast_type(target)),target.location,target.name)
        if isinstance(target,MemberExpr): return self._member_expr(target)
        if isinstance(target,IndexExpr): return IRIndex(describe(self._ast_type(target)),target.location,self._expr(target.base),self._expr(target.index))
        raise SemanticError("unsupported handled assignment target",getattr(target,"location",None))

    def _expr_type(self,e:Expr):
        if isinstance(e,HandledExpr): return self._expr_type(e.value)
        if isinstance(e,TryExpr): return self._expr_type(e.value)
        if not self.generic_context:
            known=self.a.expr_types.get(id(e))
            if known is not None and not has_unresolved(known): return resolve(known)
        if isinstance(e,LiteralExpr): return {"Int":INT,"Float":FLOAT,"Bool":BOOL,"Text":TEXT}[e.type_name]
        if isinstance(e,NoneExpr):
            known=self.a.expr_types.get(id(e))
            if known is not None and not has_unresolved(known): return resolve(known)
            raise SemanticError("generic lowering cannot infer a standalone none without context",e.location)
        if isinstance(e,NameExpr):
            stored=self._lookup(e.name)
            if stored is not None:
                # Generic lowering re-derives concrete types, but presence is a
                # checked flow fact, not a different generic specialization.
                known=self.a.expr_types.get(id(e))
                if stored.startswith("maybe ") and known is not None and describe(resolve(known))==maybe_inner(stored):
                    return resolve(known)
                return self._type_from_name(stored)
            known=self.a.expr_types.get(id(e))
            if known is not None and not has_unresolved(known): return resolve(known)
        if isinstance(e,ListExpr):
            if e.elements: return ListType(self._expr_type(e.elements[0]))
            known=self.a.expr_types.get(id(e))
            if known is not None and not has_unresolved(known): return resolve(known)
        if isinstance(e,IndexExpr):
            bt=resolve(self._expr_type(e.base))
            if isinstance(bt,ListType): return resolve(bt.element)
        if isinstance(e,MemberExpr):
            if e.name=="count" and isinstance(resolve(self._expr_type(e.base)),ListType): return INT
            return self._ast_type(e)
        if isinstance(e,ConstructionExpr):
            known=self.a.expr_types.get(id(e))
            if known is not None: return resolve(known)
        if isinstance(e,IdentityExpr): return IdentityType(self._expr_type(e.value))
        if isinstance(e,UnaryExpr): return BOOL if e.operator=="not" else self._expr_type(e.operand)
        if isinstance(e,BinaryExpr):
            if e.operator in ("==","!=","<","<=",">",">=","and","or"): return BOOL
            return self._expr_type(e.left)
        if isinstance(e,CallExpr):
            if isinstance(e.callee,NameExpr) and e.callee.name=="output": return NO_VALUE
            arg_types=[self._expr_type(a) for a in e.arguments]
            if isinstance(e.callee,NameExpr):
                fn=self.a.functions.get(e.callee.name)
                if fn is not None: return self._spec_return(fn,arg_types,e.location)
            if isinstance(e.callee,MemberExpr) and isinstance(e.callee.base,NameExpr):
                alias=e.callee.base.name
                if alias in self.a.imports and self.a.imports[alias]==("std","files") and e.callee.name=="open": return ResourceType(STD_FILE,(STD_FILE_ERROR,))
                if alias in self.a.imported_modules:
                    fn=self.a.imported_modules[alias].analyzer.functions.get(e.callee.name)
                    if fn is not None: return self._spec_return(fn,arg_types,e.location)
                if e.callee.name=="add": return NO_VALUE
            if isinstance(e.callee,MemberExpr):
                bt=resolve(self._expr_type(e.callee.base))
                if isinstance(bt,ResourceType) and bt.name==STD_FILE:
                    if e.callee.name=="readText": return TEXT
                    if e.callee.name=="writeText": return NO_VALUE
        known=self.a.expr_types.get(id(e))
        if known is not None and not has_unresolved(known): return resolve(known)
        raise SemanticError("cannot derive concrete expression type for generic IR specialization",getattr(e,"location",None))

    def _spec_return(self,fn,arg_types,loc):
        key=tuple(describe(resolve(declared if declared is not None else actual))
                  for declared,actual in zip(fn.typed_parameters,arg_types)); spec=fn.specializations.get(key)
        if spec is None or spec.state!="done" or spec.return_type is None: raise SemanticError(f"no analyzed concrete specialization for function {fn.declaration.name!r} with ({', '.join(key)})",loc)
        return resolve(spec.return_type)

    def _ast_type(self,e:Expr):
        if isinstance(e,NameExpr):
            stored=self._lookup(e.name)
            if stored is not None: return self._type_from_name(stored)
        if not self.generic_context:
            known=self.a.expr_types.get(id(e))
            if known is not None and not has_unresolved(known): return resolve(known)
        if isinstance(e,MemberExpr):
            bt=self._expr_type(e.base); base=resolve(bt.inner) if isinstance(bt,IdentityType) else resolve(bt)
            if isinstance(base,MaybeType): base=resolve(base.inner)
            if isinstance(base,AnyErrorType):
                if e.name=="message": return TEXT
                raise SemanticError(f"catch-all error exposes only message, not {e.name!r}",e.location)
            if isinstance(base,ResourceType):
                raise SemanticError("resource methods are callable but not ordinary stored fields",e.location)
            info=self.a.structs.get(describe(base))
            if info is None or e.name not in info.fields: raise SemanticError(f"cannot derive member type for {e.name!r}",e.location)
            return resolve(info.fields[e.name].type)
        if isinstance(e,IndexExpr):
            bt=resolve(self._expr_type(e.base))
            if isinstance(bt,ListType): return resolve(bt.element)
        return self._expr_type(e)

    def _member_expr(self,e:MemberExpr):
        t=describe(self._ast_type(e)); self._supported_type(t,e.location); return IRMember(t,e.location,self._expr(e.base),e.name)
    def _call_name(self,fn,name,arg_values,module_id=None):
        if all(p.type_annotation is not None for p in fn.declaration.parameters):
            prefix=self.module_id if module_id is None else module_id; return f"{prefix}.{name}" if prefix else name
        prefix=self.module_id if module_id is None else module_id; base=f"{prefix}.{name}" if prefix else name
        return base+"$"+"$".join(v.type_name for v in arg_values)

    def _expr(self,e):
        if isinstance(e,TryExpr): return self._expr(e.value)
        if isinstance(e,HandledExpr): raise SemanticError("handled expressions must be lowered by their containing statement",e.location)
        semantic_t=describe(self._expr_type(e))
        if semantic_t!="no-value": self._supported_type(semantic_t,e.location)
        if isinstance(e,LiteralExpr): return IRConst(semantic_t,e.location,e.value)
        if isinstance(e,NoneExpr): return IRMaybeNone(semantic_t,e.location)
        if isinstance(e,NameExpr):
            stored=self._lookup(e.name)
            if stored is not None and stored.startswith("maybe ") and semantic_t==maybe_inner(stored): return IRMaybeGet(semantic_t,e.location,IRVar(stored,e.location,e.name))
            return IRVar(semantic_t,e.location,e.name)
        if isinstance(e,ListExpr): return IRList(semantic_t,e.location,[self._expr(x) for x in e.elements])
        if isinstance(e,IndexExpr): return IRIndex(semantic_t,e.location,self._expr(e.base),self._expr(e.index))
        if isinstance(e,MemberExpr):
            if e.name=="count" and isinstance(resolve(self._expr_type(e.base)),ListType): return IRCount(semantic_t,e.location,self._expr(e.base))
            return self._member_expr(e)
        if isinstance(e,ConstructionExpr):
            info=self.a.structs.get(semantic_t); fs=[]
            for f in e.fields:
                expected=describe(resolve(info.fields[f.name].type)) if info else describe(self._expr_type(f.value))
                fs.append(IRFieldValue(f.name,self._coerce(self._expr(f.value),expected,f.location)))
            return IRConstruct(semantic_t,e.location,fs)
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
                args=[self._expr(a) for a in e.arguments]
                if e.callee.name=="output": return IRCall(semantic_t,e.location,"output",args)
                fn=self.a.functions.get(e.callee.name)
                if fn is None: raise SemanticError(f"unknown function {e.callee.name!r}",e.location)
                for i,av in enumerate(args):
                    if i<len(fn.typed_parameters) and fn.typed_parameters[i] is not None: args[i]=self._coerce(av,describe(resolve(fn.typed_parameters[i])),e.arguments[i].location)
                return IRCall(semantic_t,e.location,self._call_name(fn,e.callee.name,args),args)
            if isinstance(e.callee,MemberExpr) and isinstance(e.callee.base,NameExpr):
                alias=e.callee.base.name
                if alias in self.a.imports and self.a.imports[alias]==("std","files") and e.callee.name=="open":
                    return IRFileOpen(STD_FILE,e.location,self._expr(e.arguments[0]))
                if alias in self.a.imported_modules:
                    mod=self.a.imported_modules[alias]; fn=mod.analyzer.functions.get(e.callee.name)
                    if fn is None: raise SemanticError(f"unknown imported function {e.callee.name!r}",e.location)
                    args=[self._expr(a) for a in e.arguments]
                    for i,av in enumerate(args):
                        if i<len(fn.typed_parameters) and fn.typed_parameters[i] is not None: args[i]=self._coerce(av,describe(resolve(fn.typed_parameters[i])),e.arguments[i].location)
                    return IRCall(semantic_t,e.location,self._call_name(fn,e.callee.name,args,mod.module_id),args)
            if isinstance(e.callee,MemberExpr):
                bt=resolve(self._expr_type(e.callee.base))
                if isinstance(bt,ResourceType) and bt.name==STD_FILE:
                    resource=self._expr(e.callee.base)
                    if e.callee.name=="readText": return IRFileRead("Text",e.location,resource)
                    if e.callee.name=="writeText": return IRFileWrite("no-value",e.location,resource,self._expr(e.arguments[0]))
                if e.callee.name=="add" and isinstance(e.callee.base,NameExpr):
                    if len(e.arguments)!=1: raise SemanticError("List.add lowering expects one argument",e.location)
                    return IRListAdd(semantic_t,e.location,e.callee.base.name,self._expr(e.arguments[0]))
        raise SemanticError(f"the current typed IR backend does not yet lower expression {type(e).__name__}",getattr(e,"location",None))

    def _coerce(self,value:IRExpr,target:str,loc)->IRExpr:
        if value.type_name==target: return value
        if target.startswith("maybe ") and value.type_name==maybe_inner(target): return IRMaybeSome(target,loc,value)
        raise SemanticError(f"typed IR cannot coerce {value.type_name} to {target}",loc)
    @staticmethod
    def _type_from_name(t):
        if t=="checked error": return AnyErrorType()
        if t==STD_FILE: return ResourceType(STD_FILE,(STD_FILE_ERROR,))
        if t.startswith("maybe "): return MaybeType(Lowerer._type_from_name(maybe_inner(t)))
        if t.startswith("identity "): return IdentityType(Lowerer._type_from_name(identity_inner(t)))
        if t.startswith("List of "): return ListType(Lowerer._type_from_name(list_inner(t)))
        if t=="Int": return INT
        if t=="Float": return FLOAT
        if t=="Bool": return BOOL
        if t=="Text": return TEXT
        return NamedType(t)
    @staticmethod
    def _supported_type(t,loc):
        if t in ("Int","Float","Bool","Text","no-value","checked error",STD_FILE,STD_FILE_ERROR): return
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

class ProjectLowerer:
    def __init__(self,entry_module): self.entry=entry_module
    def lower(self)->IRProgram:
        order=[]; seen=set()
        def visit(mod):
            key=mod.module_id or str(mod.file_path)
            if key in seen: return
            seen.add(key)
            for child in mod.imports.values(): visit(child)
            order.append(mod)
        visit(self.entry)
        structs=[]; functions=[]; entry=[]
        for mod in order:
            module_id="" if mod is self.entry else mod.module_id
            part=Lowerer(mod.analyzer,module_id).lower(mod.program,mod is self.entry)
            structs.extend(part.structs); functions.extend(part.functions)
            if mod is self.entry: entry.extend(part.entry)
        return IRProgram(structs,functions,entry)

def maybe_inner(t):
    if not t.startswith("maybe "): raise ValueError(t)
    return t[6:]
def identity_inner(t):
    if not t.startswith("identity "): raise ValueError(t)
    return t[9:]
def list_inner(t):
    if not t.startswith("List of "): raise ValueError(t)
    return t[8:]
