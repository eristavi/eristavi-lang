from __future__ import annotations
from dataclasses import dataclass, field
from .diagnostics import SemanticError
from .syntax import *
from .typesys import *

BASIC = {"Int":INT,"Float":FLOAT,"Bool":BOOL,"Text":TEXT}
STD_FILE_ERROR = "std.files.FileError"
STD_FILE = ResourceType("std.files.File", (STD_FILE_ERROR,))

@dataclass
class FieldInfo:
    name: str
    type: TypeLike
    fixed: bool=False

@dataclass
class StructInfo:
    name: str
    fields: dict[str, FieldInfo]
    is_error: bool=False
    public: bool=False

@dataclass
class Symbol:
    type: TypeLike
    fixed: bool
    location: object|None=None
    resource_owned: bool=False

@dataclass
class FunctionSpec:
    parameter_types: list[TypeLike]
    return_type: TypeLike|None=None
    state: str="unseen"

@dataclass
class FunctionSymbol:
    declaration: FunctionDecl
    typed_parameters: list[TypeLike|None]
    explicit_return: TypeLike|None
    fails: set[str]
    specializations: dict[tuple[str,...], FunctionSpec]=field(default_factory=dict)

@dataclass
class FunctionContext:
    function: FunctionSymbol
    spec: FunctionSpec
    saw_value_return: bool=False
    saw_bare_return: bool=False
    inferred_return: TypeLike|None=None

class Analyzer:
    def __init__(self, module_id: str = "", imported_modules: dict[str, object] | None = None, is_entry: bool = True):
        self.module_id=module_id
        self.imported_modules=imported_modules or {}
        self.is_entry=is_entry
        self.local_types: dict[str,str]={}
        self.scopes: list[dict[str,Symbol]]=[{}]
        self.narrowings: list[dict[str,TypeLike]]=[{}]
        self.functions: dict[str,FunctionSymbol]={}
        self.structs: dict[str,StructInfo]={}
        for _m in self.imported_modules.values():
            self.structs.update(_m.analyzer.structs)
        self.imports: dict[str,tuple[str,...]]={}
        self.expr_types: dict[int,TypeLike]={}
        self.expr_failures: dict[int,set[str]]={}
        self.current_function: FunctionContext|None=None
        self._pending_inference: list[tuple[TypeLike,object,str]]=[]
        self._fixed_pending: list[tuple[TypeLike,object,str]]=[]

    def analyze(self,program:Program):
        self._collect_module(program)
        for fn in self.functions.values():
            params=[t if t is not None else TypeVar(p.name) for p,t in zip(fn.declaration.parameters,fn.typed_parameters)]
            self._ensure_function(fn,params,True)
        for stmt in program.statements:
            if isinstance(stmt,(ImportDecl,FunctionDecl,TypeDecl,ErrorDecl)): continue
            self._statement(stmt)
        self._validate_scope_inference(self.scopes[0])
        self._validate_pending()
        return self.expr_types

    def _collect_module(self,program):
        phase="imports"; names=set()
        decls=[]
        for stmt in program.statements:
            if isinstance(stmt,ImportDecl):
                if phase!="imports": raise SemanticError("imports must appear before module declarations or entry statements",stmt.location)
                alias=stmt.alias or stmt.path[-1]
                if alias in self.imports: raise SemanticError(f"duplicate import qualifier {alias!r}",stmt.location)
                if stmt.path != ("std","files"):
                    mod=self.imported_modules.get(alias)
                    if mod is None or tuple(mod.path)!=stmt.path:
                        raise SemanticError(f"module {'.'.join(stmt.path)!r} was not loaded by the project compiler",stmt.location)
                self.imports[alias]=stmt.path
                continue
            if isinstance(stmt,(FunctionDecl,TypeDecl,ErrorDecl)):
                if phase=="entry": raise SemanticError("module declarations must appear before entry executable statements",stmt.location)
                phase="decls"; decls.append(stmt)
                if stmt.name in names: raise SemanticError(f"duplicate module-level declaration {stmt.name!r}",stmt.location)
                if stmt.name=="output": raise SemanticError("module declaration cannot replace predeclared standard name 'output'",stmt.location)
                names.add(stmt.name); continue
            if not self.is_entry:
                raise SemanticError("imported modules must be declaration-only and cannot contain top-level executable statements",stmt.location)
            phase="entry"
        # First create type/error shells for order-independent references.
        for d in decls:
            if isinstance(d,(TypeDecl,ErrorDecl)):
                canonical=self._canonical_type_name(d.name)
                self.local_types[d.name]=canonical
                self.structs[canonical]=StructInfo(canonical,{},isinstance(d,ErrorDecl),d.public)
        # Resolve fields.
        for d in decls:
            if isinstance(d,(TypeDecl,ErrorDecl)):
                seen=set(); info=self.structs[self.local_types[d.name]]
                for f in d.fields:
                    if f.name in seen: raise SemanticError(f"duplicate field {f.name!r} in {d.name}",f.location)
                    seen.add(f.name); ft=self._resolve_type_ref(f.type_ref)
                    info.fields[f.name]=FieldInfo(f.name,ft,f.fixed)
                if isinstance(d,ErrorDecl):
                    msgs=[f for f in d.fields if f.name=="message"]
                    if len(msgs)!=1 or describe(self._resolve_type_ref(msgs[0].type_ref))!="Text":
                        raise SemanticError(f"checked error {d.name!r} must declare exactly one 'message Text' field",d.location)
        # Deep-fixed field validation after all shells are populated.
        for d in decls:
            if isinstance(d,TypeDecl):
                for f in d.fields:
                    if f.fixed:
                        ft=self.structs[self.local_types[d.name]].fields[f.name].type
                        if not self._deep_fixable(ft,set()):
                            raise SemanticError(f"fixed field {d.name}.{f.name} is not deep-fixable because its type contains identity",f.location)
        # Functions after errors/types known.
        for d in decls:
            if not isinstance(d,FunctionDecl): continue
            typed=[]
            for p in d.parameters:
                typed.append(self._resolve_type_ref(p.type_annotation) if p.type_annotation else None)
            explicit=self._resolve_type_ref(d.return_type) if d.return_type else None
            fails=set()
            for fr in d.fails:
                et=self._resolve_type_ref(fr)
                if not self._is_error_type(et): raise SemanticError(f"{describe(et)} is not a checked error type",fr.location)
                n=describe(resolve(et))
                if n in fails: raise SemanticError(f"duplicate checked error {n} in fails clause",fr.location)
                fails.add(n)
            self.functions[d.name]=FunctionSymbol(d,typed,explicit,fails)

    def _resolve_type_ref(self,ref:TypeRef|None)->TypeLike:
        if ref is None: raise SemanticError("missing type reference")
        path=ref.path
        if len(path)==1 and path[0] in BASIC: base=BASIC[path[0]]
        elif len(path)==1 and path[0] in self.local_types: base=NamedType(self.local_types[path[0]])
        elif len(path)==2 and path[0] in self.imports and self.imports[path[0]]==("std","files"):
            if path[1]=="File": base=STD_FILE
            elif path[1]=="FileError": base=NamedType(STD_FILE_ERROR)
            else: raise SemanticError(f"unknown std.files type {path[1]!r}",ref.location)
        elif len(path)==2 and path[0] in self.imported_modules:
            mod=self.imported_modules[path[0]]; canonical=mod.analyzer.local_types.get(path[1])
            if canonical is None or not mod.analyzer.structs[canonical].public:
                raise SemanticError(f"module {path[0]!r} does not expose public type/error {path[1]!r}",ref.location)
            base=NamedType(canonical)
        else: raise SemanticError(f"unknown type {'.'.join(path)!r}",ref.location)
        if ref.identity: base=IdentityType(base)
        if ref.maybe: base=MaybeType(base)
        return base

    def _ensure_function(self,fn:FunctionSymbol,param_types:list[TypeLike],value_required:bool)->TypeLike:
        key=tuple(describe(resolve(t)) for t in param_types)
        spec=fn.specializations.get(key)
        if spec is None:
            spec=FunctionSpec([clone_type(t) for t in param_types],fn.explicit_return)
            fn.specializations[key]=spec
        if spec.state=="done": return resolve(spec.return_type or NO_VALUE)
        if spec.state=="visiting":
            if fn.explicit_return is not None: return fn.explicit_return
            if not value_required: return NO_VALUE
            raise SemanticError(f"circular result inference for function {fn.declaration.name!r}; add an explicit 'returns T' contract",fn.declaration.location)
        spec.state="visiting"; old_scopes=self.scopes; old_nar=self.narrowings; old_ctx=self.current_function
        self.scopes=[{}]; self.narrowings=[{}]
        try:
            for p,t in zip(fn.declaration.parameters,spec.parameter_types): self.scopes[0][p.name]=Symbol(t,False,p.location)
            ctx=FunctionContext(fn,spec); self.current_function=ctx
            terminates=self._block(fn.declaration.body,new_scope=True)
            if ctx.saw_value_return and ctx.saw_bare_return: raise SemanticError(f"function {fn.declaration.name!r} cannot mix bare and value returns",fn.declaration.location)
            if fn.explicit_return is not None:
                spec.return_type=fn.explicit_return
                if ctx.saw_bare_return: raise SemanticError(f"value-producing function {fn.declaration.name!r} cannot use bare 'return;'",fn.declaration.location)
                if not terminates: raise SemanticError(f"value-producing function {fn.declaration.name!r} has a reachable successful path without a return value",fn.declaration.location)
            elif ctx.saw_value_return:
                spec.return_type=ctx.inferred_return
                if not terminates: raise SemanticError(f"value-producing function {fn.declaration.name!r} has a reachable successful path without a return value",fn.declaration.location)
            else: spec.return_type=NO_VALUE
            self._validate_scope_inference(self.scopes[0]); spec.state="done"; return resolve(spec.return_type)
        except Exception:
            spec.state="unseen"; raise
        finally:
            self.scopes=old_scopes; self.narrowings=old_nar; self.current_function=old_ctx

    def _statement(self,stmt)->bool:
        if isinstance(stmt,(FunctionDecl,TypeDecl,ErrorDecl,ImportDecl)): raise SemanticError("module declaration is not valid inside an executable block",stmt.location)
        if isinstance(stmt,ReturnStmt): return self._return(stmt)
        if isinstance(stmt,FailStmt):
            if self.current_function is None: raise SemanticError("fail is valid only inside a function with a fails contract",stmt.location)
            t=self._expr(stmt.value,True,False)
            if not self._is_error_type(t): raise SemanticError("fail requires a checked error value",stmt.location)
            n=describe(resolve(t))
            if n not in self.current_function.function.fails: raise SemanticError(f"checked error {n} is not declared by this function's fails contract",stmt.location)
            return True
        if isinstance(stmt,LetStmt):
            if self._resolve_symbol(stmt.name) is not None: raise SemanticError(f"name {stmt.name!r} is already visible; pre-0.1 does not allow local shadowing",stmt.location)
            t=self._expr(stmt.initializer,True,False)
            if isinstance(resolve(t),NoValueType): raise SemanticError("a no-value expression cannot initialize a binding",stmt.location)
            if isinstance(resolve(t),ResourceType): raise SemanticError("resources must be owned by 'with', not ordinary let bindings",stmt.location)
            if stmt.type_annotation:
                expected=self._resolve_type_ref(stmt.type_annotation)
                self._assign_or_error(expected,t,stmt.location,"initializer")
                t=expected
            sym=Symbol(t,stmt.fixed,stmt.location)
            self.scopes[-1][stmt.name]=sym
            if stmt.fixed: self._fixed_pending.append((t,stmt.location,stmt.name))
            return False
        if isinstance(stmt,AssignStmt):
            target_t=self._target_type(stmt.target,True); rhs=self._expr(stmt.value,True,False)
            if isinstance(resolve(rhs),NoValueType): raise SemanticError("a no-value expression cannot be assigned",stmt.location)
            self._assign_or_error(target_t,rhs,stmt.location,"assignment")
            root=self._root_name(stmt.target)
            if root:
                self._clear_narrowing(root)
                if isinstance(stmt.target,NameExpr):
                    sym=self._resolve_symbol(root)
                    declared=resolve(sym.type) if sym else None
                    actual=resolve(rhs)
                    if isinstance(declared,MaybeType) and not isinstance(actual,MaybeType):
                        self.narrowings[-1][root]=declared.inner
            return False
        if isinstance(stmt,ExprStmt): self._expr(stmt.expression,False,False); return False
        if isinstance(stmt,IfStmt):
            ct=self._expr(stmt.condition,True,False)
            self._require_type(ct,BOOL,stmt.condition.location,"if condition must have static type Bool")
            then_n,else_n=self._condition_narrowings(stmt.condition)
            tr=self._block(stmt.then_branch,True,then_n); er=False
            if stmt.else_branch is not None: er=self._block(stmt.else_branch,True,else_n)
            if tr and not er:
                for n,t in else_n.items(): self.narrowings[-1][n]=t
            elif er and not tr:
                for n,t in then_n.items(): self.narrowings[-1][n]=t
            return stmt.else_branch is not None and tr and er
        if isinstance(stmt,WhileStmt):
            self._require_type(self._expr(stmt.condition,True,False),BOOL,stmt.condition.location,"while condition must have static type Bool")
            self._block(stmt.body,True,self._condition_narrowings(stmt.condition)[0]); return False
        if isinstance(stmt,ForStmt):
            if self._resolve_symbol(stmt.name) is not None: raise SemanticError(f"loop binding {stmt.name!r} would shadow an existing name",stmt.location)
            it=resolve(self._expr(stmt.iterable,True,False))
            if not isinstance(it,ListType): raise SemanticError("for/in currently requires a List value",stmt.iterable.location)
            self.scopes.append({stmt.name:Symbol(it.element,False,stmt.location)}); self.narrowings.append({})
            try:
                term=False
                for s in stmt.body.statements:
                    if term: break
                    term=self._statement(s)
                self._validate_scope_inference(self.scopes[-1])
            finally: self.scopes.pop(); self.narrowings.pop()
            return False
        if isinstance(stmt,WithStmt): return self._with(stmt)
        raise SemanticError("statement is not implemented by the bootstrap analyzer",getattr(stmt,"location",None))

    def _return(self,stmt):
        if self.current_function is None: raise SemanticError("return is valid only inside a function",stmt.location)
        ctx=self.current_function
        if stmt.value is None:
            ctx.saw_bare_return=True
            if ctx.saw_value_return or ctx.function.explicit_return is not None: raise SemanticError("bare 'return;' is valid only in a no-value function",stmt.location)
            return True
        t=self._expr(stmt.value,True,False)
        if isinstance(resolve(t),NoValueType): raise SemanticError("a no-value expression cannot be returned as a value",stmt.location)
        if isinstance(resolve(t),ResourceType): raise SemanticError("a resource cannot escape its owning with scope by return",stmt.location)
        ctx.saw_value_return=True
        if ctx.saw_bare_return: raise SemanticError("a function cannot mix bare and value returns",stmt.location)
        if ctx.function.explicit_return is not None: self._assign_or_error(ctx.function.explicit_return,t,stmt.location,"return value"); t=ctx.function.explicit_return
        if ctx.inferred_return is None: ctx.inferred_return=t
        else: ctx.inferred_return=self._join_or_error(ctx.inferred_return,t,stmt.location,"inferred return")
        return True

    def _with(self,stmt):
        if self._resolve_symbol(stmt.name) is not None: raise SemanticError(f"resource binding {stmt.name!r} would shadow an existing name",stmt.location)
        rt=resolve(self._expr(stmt.resource,True,False))
        if not isinstance(rt,ResourceType): raise SemanticError("with requires a deterministic resource value",stmt.resource.location)
        if stmt.type_annotation:
            expected=self._resolve_type_ref(stmt.type_annotation); self._unify_or_error(expected,rt,stmt.location,"resource type")
        cleanup=set(rt.cleanup_errors)
        if cleanup:
            if self.current_function is None: raise SemanticError("top-level with cannot expose an unhandled checked cleanup failure",stmt.location)
            missing=cleanup-self.current_function.function.fails
            if missing: raise SemanticError(f"resource cleanup may fail with {', '.join(sorted(missing))}; add it to the function's fails contract",stmt.location)
        self.scopes.append({stmt.name:Symbol(rt,True,stmt.location,True)}); self.narrowings.append({})
        try:
            term=False
            for s in stmt.body.statements:
                if term: break
                term=self._statement(s)
            self._validate_scope_inference(self.scopes[-1]); return term
        finally: self.scopes.pop(); self.narrowings.pop()

    def _block(self,block,new_scope=True,initial_narrowing=None):
        if new_scope: self.scopes.append({}); self.narrowings.append(dict(initial_narrowing or {}))
        term=False
        try:
            for s in block.statements:
                if term: break
                term=self._statement(s)
            if new_scope: self._validate_scope_inference(self.scopes[-1])
            return term
        finally:
            if new_scope: self.scopes.pop(); self.narrowings.pop()

    def _expr(self,expr:Expr,value_required=True,allow_checked=False)->TypeLike:
        fails:set[str]=set()
        if isinstance(expr,LiteralExpr):
            if expr.type_name=="Int" and not (-(2**63)<=int(expr.value)<=2**63-1): raise SemanticError("Int literal is outside the signed 64-bit range",expr.location)
            return self._record(expr,BASIC[expr.type_name],fails)
        if isinstance(expr,NoneExpr): return self._record(expr,MaybeType(TypeVar("none")),fails)
        if isinstance(expr,ListExpr):
            elem:TypeLike=TypeVar("element")
            for e in expr.elements:
                et=self._expr(e,True,allow_checked); fails|=self.expr_failures.get(id(e),set()); elem=self._join_or_error(elem,et,e.location,"List element")
            return self._record(expr,ListType(elem),fails)
        if isinstance(expr,NameExpr):
            sym=self._resolve_symbol(expr.name)
            if sym is not None:
                t=self._visible_type(expr.name,sym); return self._record(expr,t,fails)
            if expr.name=="output": return self._record(expr,NamedType("<function output>"),fails)
            if expr.name in self.imports: return self._record(expr,NamedType(f"<module {expr.name}>"),fails)
            if expr.name in self.functions: raise SemanticError("function names are not first-class values; call the function instead",expr.location)
            raise SemanticError(f"unknown name {expr.name!r}",expr.location)
        if isinstance(expr,IdentityExpr):
            t=resolve(self._expr(expr.value,True,allow_checked)); fails|=self.expr_failures.get(id(expr.value),set())
            if isinstance(t,(ResourceType,IdentityType,MaybeType,NoValueType)): raise SemanticError(f"identity requires an eligible ordinary non-resource value, got {describe(t)}",expr.location)
            return self._record(expr,IdentityType(t),fails)
        if isinstance(expr,TryExpr):
            if self.current_function is None: raise SemanticError("try cannot propagate a checked failure beyond the entry boundary",expr.location)
            t=self._expr(expr.value,True,True); inner=self.expr_failures.get(id(expr.value),set()); missing=inner-self.current_function.function.fails
            if missing: raise SemanticError(f"try may propagate {', '.join(sorted(missing))}, which is not declared by the current function",expr.location)
            return self._record(expr,t,set())
        if isinstance(expr,HandledExpr): return self._handled(expr,value_required)
        if isinstance(expr,UnaryExpr):
            t=resolve(self._expr(expr.operand,True,allow_checked)); fails|=self.expr_failures.get(id(expr.operand),set())
            if expr.operator=="-" and describe(t) in ("Int","Float"): return self._record(expr,t,fails)
            if expr.operator=="not" and describe(t)=="Bool": return self._record(expr,BOOL,fails)
            raise SemanticError(f"operator {expr.operator!r} is not defined for {describe(t)}",expr.location)
        if isinstance(expr,BinaryExpr): return self._binary(expr,value_required,allow_checked)
        if isinstance(expr,MemberExpr): return self._member(expr,allow_checked)
        if isinstance(expr,IndexExpr):
            raw_bt=self._expr(expr.base,True,allow_checked); bt=resolve(raw_bt); it=self._expr(expr.index,True,allow_checked); fails|=self.expr_failures.get(id(expr.base),set())|self.expr_failures.get(id(expr.index),set())
            self._require_type(it,INT,expr.index.location,"List index must have static type Int")
            if isinstance(bt,TypeVar):
                elem=TypeVar("element"); bt=ListType(elem); unify(raw_bt,bt)
            if not isinstance(bt,ListType): raise SemanticError(f"indexing is not defined for {describe(bt)}",expr.location)
            if isinstance(expr.base,ListExpr) and isinstance(expr.index,LiteralExpr) and expr.index.type_name=="Int":
                idx=int(expr.index.value)
                if idx<0 or idx>=len(expr.base.elements): raise SemanticError("List index is provably out of bounds",expr.index.location)
            return self._record(expr,bt.element,fails)
        if isinstance(expr,ConstructionExpr): return self._construction(expr,allow_checked)
        if isinstance(expr,CallExpr): return self._call(expr,value_required,allow_checked)
        raise SemanticError("expression is not implemented by the bootstrap analyzer",getattr(expr,"location",None))

    def _binary(self,expr,value_required,allow_checked):
        lt=self._expr(expr.left,True,allow_checked); rt=self._expr(expr.right,True,allow_checked); fails=self.expr_failures.get(id(expr.left),set())|self.expr_failures.get(id(expr.right),set()); op=expr.operator
        l=resolve(lt); r=resolve(rt)
        if isinstance(l,NoValueType) or isinstance(r,NoValueType): raise SemanticError(f"operator {op} requires values",expr.location)
        if op in ("and","or"):
            self._require_type(l,BOOL,expr.location,f"{op} requires Bool operands"); self._require_type(r,BOOL,expr.location,f"{op} requires Bool operands"); return self._record(expr,BOOL,fails)
        if op in ("==","!="):
            # none composes with maybe via unification.
            try: self._join_types(lt,rt)
            except TypeError: raise SemanticError(f"cannot compare {describe(l)} with {describe(r)} without an explicit conversion",expr.location)
            t=resolve(lt)
            if not self._equality_comparable(t,set()): raise SemanticError(f"equality is not defined for {describe(t)}",expr.location)
            return self._record(expr,BOOL,fails)
        if op in ("<","<=",">",">="):
            self._unify_or_error(lt,rt,expr.location,"comparison operands"); t=resolve(lt)
            if isinstance(t,TypeVar):
                allowed={"Int","Float"}; t.allowed_names=allowed if t.allowed_names is None else (t.allowed_names & allowed)
                if not t.allowed_names: raise SemanticError(f"ordered comparison {op} has incompatible inferred constraints",expr.location)
            elif describe(t) not in ("Int","Float"): raise SemanticError(f"ordered comparison {op} is not defined for {describe(t)}",expr.location)
            return self._record(expr,BOOL,fails)
        if op in ("+","-","*","/","%"):
            self._unify_or_error(lt,rt,expr.location,f"operator {op}"); t=resolve(lt)
            if isinstance(t,TypeVar):
                allowed={"Int"} if op=="%" else ({"Int","Float","Text"} if op=="+" else {"Int","Float"})
                t.allowed_names = allowed if t.allowed_names is None else (t.allowed_names & allowed)
                if not t.allowed_names: raise SemanticError(f"operator {op} has incompatible inferred constraints",expr.location)
                return self._record(expr,t,fails)
            name=describe(t)
            if op=="+" and name=="Text": return self._record(expr,TEXT,fails)
            if name=="Int": return self._record(expr,INT,fails)
            if name=="Float" and op!="%": return self._record(expr,FLOAT,fails)
            if name=="Float" and op=="%": raise SemanticError("% is Int-only in pre-0.1; Float remainder requires a named API",expr.location)
            raise SemanticError(f"operator {op} is not defined for {name}",expr.location)
        raise SemanticError(f"unknown operator {op}",expr.location)

    def _member(self,expr,allow_checked):
        # Imported std.files namespace members are handled by call/type resolution, not values.
        if isinstance(expr.base,NameExpr) and expr.base.name in self.imports:
            return self._record(expr,NamedType(f"<module member {expr.base.name}.{expr.name}>"),set())
        bt=resolve(self._expr(expr.base,True,allow_checked)); fails=set(self.expr_failures.get(id(expr.base),set()))
        if isinstance(bt,MaybeType): raise SemanticError(f"cannot access member {expr.name!r} on {describe(bt)} before proving it is present",expr.location)
        if isinstance(bt,TypeVar) and expr.name in ("count","add"):
            shaped=ListType(TypeVar("element")); unify(bt,shaped); bt=shaped
        if isinstance(bt,IdentityType): bt=resolve(bt.inner)
        if isinstance(bt,ListType):
            if expr.name=="count": return self._record(expr,INT,fails)
            if expr.name=="add": return self._record(expr,NamedType("<List.add>"),fails)
            raise SemanticError(f"List has no member {expr.name!r} in pre-0.1",expr.location)
        if isinstance(bt,ResourceType):
            if bt.name=="std.files.File" and expr.name in ("readText","writeText"): return self._record(expr,NamedType(f"<File.{expr.name}>"),fails)
            raise SemanticError(f"resource {bt.name} has no member {expr.name!r}",expr.location)
        if isinstance(bt,AnyErrorType):
            if expr.name=="message": return self._record(expr,TEXT,fails)
            raise SemanticError("a catch-all error exposes only the guaranteed message field",expr.location)
        if isinstance(bt,NamedType) and bt.name in self.structs:
            info=self.structs[bt.name]; f=info.fields.get(expr.name)
            if not f: raise SemanticError(f"{bt.name} has no field {expr.name!r}",expr.location)
            return self._record(expr,f.type,fails)
        raise SemanticError(f"member access is not defined for {describe(bt)}",expr.location)

    def _construction(self,expr,allow_checked):
        t=self._resolve_type_path(expr.type_path,expr.location)
        if not isinstance(t,NamedType) or t.name not in self.structs: raise SemanticError(f"{describe(t)} is not directly constructible",expr.location)
        info=self.structs[t.name]; seen=set(); provided={}
        for init in expr.fields:
            if init.name in seen: raise SemanticError(f"field {init.name!r} is initialized more than once",init.location)
            seen.add(init.name)
            if init.name not in info.fields: raise SemanticError(f"unknown field {init.name!r} for {info.name}",init.location)
            et=self._expr(init.value,True,allow_checked); self._assign_or_error(info.fields[init.name].type,et,init.location,f"field {init.name}"); provided[init.name]=True
        missing=[n for n in info.fields if n not in provided]
        if missing: raise SemanticError(f"construction of {info.name} is missing field(s): {', '.join(missing)}",expr.location)
        fails=set()
        for f in expr.fields: fails|=self.expr_failures.get(id(f.value),set())
        return self._record(expr,t,fails)

    def _call(self,expr,value_required,allow_checked):
        # output
        if isinstance(expr.callee,NameExpr) and expr.callee.name=="output":
            if len(expr.arguments)!=1: raise SemanticError("output(...) takes exactly one argument in pre-0.1",expr.location)
            at=resolve(self._expr(expr.arguments[0],True,allow_checked)); fails=set(self.expr_failures.get(id(expr.arguments[0]),set()))
            if describe(at) not in BASIC: raise SemanticError(f"bootstrap output supports only Int, Float, Bool, and Text, got {describe(at)}",expr.location)
            return self._record(expr,NO_VALUE,fails)
        # List.add
        if isinstance(expr.callee,MemberExpr) and expr.callee.name=="add":
            raw_bt=self._expr(expr.callee.base,True,allow_checked); bt=resolve(raw_bt); fails=set(self.expr_failures.get(id(expr.callee.base),set()))
            if isinstance(bt,TypeVar):
                shaped=ListType(TypeVar("element")); unify(raw_bt,shaped); bt=shaped
            if not isinstance(bt,ListType): raise SemanticError("add(value) is defined only for List",expr.location)
            self._ensure_mutable_path(expr.callee.base)
            if len(expr.arguments)!=1: raise SemanticError("List.add(value) takes exactly one argument",expr.location)
            at=self._expr(expr.arguments[0],True,allow_checked); fails|=self.expr_failures.get(id(expr.arguments[0]),set()); self._assign_or_error(bt.element,at,expr.arguments[0].location,"List.add element")
            return self._record(expr,NO_VALUE,fails)
        # std.files open
        if isinstance(expr.callee,MemberExpr) and isinstance(expr.callee.base,NameExpr) and expr.callee.base.name in self.imports and self.imports[expr.callee.base.name]==("std","files"):
            if expr.callee.name!="open": raise SemanticError(f"std.files has no function {expr.callee.name!r}",expr.location)
            if len(expr.arguments)!=1: raise SemanticError("files.open(path) takes one Text argument",expr.location)
            self._require_type(self._expr(expr.arguments[0],True,allow_checked),TEXT,expr.arguments[0].location,"files.open(path) requires Text")
            failures={STD_FILE_ERROR}
            if failures and not allow_checked: raise SemanticError("call may fail with std.files.FileError; handle it with 'else error' or propagate it with 'try'",expr.location)
            return self._record(expr,STD_FILE,failures)
        # Resource methods
        if isinstance(expr.callee,MemberExpr):
            bt=resolve(self._expr(expr.callee.base,True,allow_checked))
            if isinstance(bt,ResourceType) and bt.name=="std.files.File":
                failures={STD_FILE_ERROR}
                if expr.callee.name=="readText":
                    if expr.arguments: raise SemanticError("file.readText() takes no arguments",expr.location)
                    if not allow_checked: raise SemanticError("file.readText() may fail; use 'try' or 'else error'",expr.location)
                    return self._record(expr,TEXT,failures)
                if expr.callee.name=="writeText":
                    if len(expr.arguments)!=1: raise SemanticError("file.writeText(text) takes one argument",expr.location)
                    self._require_type(self._expr(expr.arguments[0],True,allow_checked),TEXT,expr.arguments[0].location,"file.writeText requires Text")
                    if not allow_checked: raise SemanticError("file.writeText() may fail; use 'try' or 'else error'",expr.location)
                    return self._record(expr,NO_VALUE,failures)
        # Imported module function
        if isinstance(expr.callee,MemberExpr) and isinstance(expr.callee.base,NameExpr) and expr.callee.base.name in self.imported_modules:
            mod=self.imported_modules[expr.callee.base.name]
            fn=mod.analyzer.functions.get(expr.callee.name)
            if fn is None or not fn.declaration.public:
                raise SemanticError(f"module {expr.callee.base.name!r} does not expose public function {expr.callee.name!r}",expr.location)
            if len(expr.arguments)!=len(fn.typed_parameters): raise SemanticError(f"function {expr.callee.name!r} expects {len(fn.typed_parameters)} argument(s), got {len(expr.arguments)}",expr.location)
            args=[]; failures=set()
            for i,(a,decl_t) in enumerate(zip(expr.arguments,fn.typed_parameters),1):
                at=self._expr(a,True,allow_checked); failures|=self.expr_failures.get(id(a),set())
                if decl_t is not None: self._assign_or_error(decl_t,at,a.location,f"argument {i}"); args.append(decl_t)
                else: args.append(at)
            failures|=fn.fails
            if fn.fails and not allow_checked: raise SemanticError(f"call to {expr.callee.base.name}.{expr.callee.name} may fail with {', '.join(sorted(fn.fails))}; handle it or use try",expr.location)
            rt=mod.analyzer._ensure_function(fn,args,value_required)
            if value_required and isinstance(resolve(rt),NoValueType): raise SemanticError("a no-value function call cannot be used where a value is required",expr.location)
            return self._record(expr,rt,failures)
        # User function
        if not isinstance(expr.callee,NameExpr): raise SemanticError("bootstrap calls require a named function or supported member operation",expr.location)
        fn=self.functions.get(expr.callee.name)
        if fn is None: raise SemanticError(f"unknown function {expr.callee.name!r}",expr.callee.location)
        if len(expr.arguments)!=len(fn.typed_parameters): raise SemanticError(f"function {fn.declaration.name!r} expects {len(fn.typed_parameters)} argument(s), got {len(expr.arguments)}",expr.location)
        args=[]; failures=set()
        for i,(a,decl_t) in enumerate(zip(expr.arguments,fn.typed_parameters),1):
            at=self._expr(a,True,allow_checked); failures|=self.expr_failures.get(id(a),set())
            if isinstance(resolve(at),NoValueType): raise SemanticError(f"argument {i} cannot be a no-value expression",a.location)
            if isinstance(resolve(at),ResourceType): raise SemanticError("resource handles cannot be passed as ordinary value parameters",a.location)
            if decl_t is not None: self._assign_or_error(decl_t,at,a.location,f"argument {i}"); args.append(decl_t)
            else: args.append(at)
        failures|=fn.fails
        if fn.fails and not allow_checked: raise SemanticError(f"call to {fn.declaration.name} may fail with {', '.join(sorted(fn.fails))}; handle it with 'else error' or propagate it with 'try'",expr.location)
        rt=self._ensure_function(fn,args,value_required)
        if value_required and isinstance(resolve(rt),NoValueType): raise SemanticError("a no-value function call cannot be used where a value is required",expr.location)
        return self._record(expr,rt,failures)

    def _handled(self,expr:HandledExpr,value_required):
        t=self._expr(expr.value,value_required,True); possible=set(self.expr_failures.get(id(expr.value),set()))
        if not possible: raise SemanticError("'else error' is attached to an expression that has no checked failures",expr.location)
        covered=set(); catchall=False
        for i,h in enumerate(expr.handlers):
            if catchall: raise SemanticError("catch-all 'else error' must be the final handler",h.location)
            if h.type_ref is None: catchall=True; ht=ANY_ERROR
            else:
                et=self._resolve_type_ref(h.type_ref); n=describe(resolve(et))
                if not self._is_error_type(et): raise SemanticError(f"handler type {n} is not a checked error",h.location)
                if n in covered: raise SemanticError(f"checked error {n} is handled more than once",h.location)
                covered.add(n); ht=et
            if self._resolve_symbol("error") is not None: raise SemanticError("handler binding 'error' would shadow an existing local name",h.location)
            self.scopes.append({"error":Symbol(ht,False,h.location)}); self.narrowings.append({})
            try:
                term=False
                for s in h.block.statements:
                    if term: break
                    term=self._statement(s)
                self._validate_scope_inference(self.scopes[-1])
            finally: self.scopes.pop(); self.narrowings.pop()
            if value_required and not term: raise SemanticError("an error handler attached to a value expression must terminate the current path",h.location)
        if not catchall:
            missing=possible-covered
            if missing: raise SemanticError(f"checked-error handling is incomplete; missing: {', '.join(sorted(missing))}",expr.location)
        return self._record(expr,t,set())

    def _target_type(self,target,for_write=False):
        if isinstance(target,NameExpr):
            sym=self._resolve_symbol(target.name)
            if sym is None: raise SemanticError(f"unknown name {target.name!r}",target.location)
            if for_write and sym.fixed: raise SemanticError(f"cannot assign to fixed binding {target.name!r}",target.location)
            if sym.resource_owned: raise SemanticError("resource bindings cannot be reassigned",target.location)
            return sym.type
        if isinstance(target,IndexExpr):
            if for_write: self._ensure_mutable_path(target.base)
            bt=resolve(self._expr(target.base,True,False)); self._require_type(self._expr(target.index,True,False),INT,target.index.location,"List index must have type Int")
            if not isinstance(bt,ListType): raise SemanticError("indexed assignment requires a List",target.location)
            return bt.element
        if isinstance(target,MemberExpr):
            if target.name=="count": raise SemanticError("List.count is read-only",target.location)
            if for_write: self._ensure_mutable_path(target.base)
            bt=resolve(self._expr(target.base,True,False)); base=resolve(bt.inner) if isinstance(bt,IdentityType) else bt
            if isinstance(base,NamedType) and base.name in self.structs:
                f=self.structs[base.name].fields.get(target.name)
                if not f: raise SemanticError(f"{base.name} has no field {target.name!r}",target.location)
                if for_write and f.fixed: raise SemanticError(f"field {base.name}.{target.name} is fixed",target.location)
                return f.type
            raise SemanticError(f"member assignment is not defined for {describe(bt)}",target.location)
        raise SemanticError("invalid assignment target",getattr(target,"location",None))

    def _ensure_mutable_path(self,expr):
        root=self._root_name(expr)
        if root:
            sym=self._resolve_symbol(root)
            if sym and sym.fixed: raise SemanticError(f"cannot mutate through fixed binding {root!r}",getattr(expr,"location",sym.location))
            if sym and sym.resource_owned: return
        if isinstance(expr,MemberExpr):
            bt=resolve(self._expr(expr.base,True,False)); base=resolve(bt.inner) if isinstance(bt,IdentityType) else bt
            if isinstance(base,NamedType) and base.name in self.structs:
                f=self.structs[base.name].fields.get(expr.name)
                if f and f.fixed: raise SemanticError(f"field {base.name}.{expr.name} is fixed",expr.location)
            self._ensure_mutable_path(expr.base)
        elif isinstance(expr,IndexExpr): self._ensure_mutable_path(expr.base)

    def _root_name(self,e):
        while isinstance(e,(MemberExpr,IndexExpr)): e=e.base
        return e.name if isinstance(e,NameExpr) else None

    def _condition_narrowings(self,e):
        then={}; other={}
        if isinstance(e,BinaryExpr) and e.operator in ("==","!="):
            name=None
            if isinstance(e.left,NameExpr) and isinstance(e.right,NoneExpr): name=e.left.name
            elif isinstance(e.right,NameExpr) and isinstance(e.left,NoneExpr): name=e.right.name
            if name:
                sym=self._resolve_symbol(name)
                if sym:
                    st=resolve(sym.type)
                    if isinstance(st,MaybeType):
                        present=st.inner
                        if e.operator=="!=": then[name]=present
                        else: other[name]=present
        return then,other

    def _visible_type(self,name,sym):
        for n in reversed(self.narrowings):
            if name in n: return n[name]
        return sym.type
    def _clear_narrowing(self,name):
        for n in self.narrowings: n.pop(name,None)
    def _resolve_symbol(self,name):
        for s in reversed(self.scopes):
            if name in s: return s[name]
        return None

    def _canonical_type_name(self,name):
        return f"{self.module_id}.{name}" if self.module_id else name

    def _resolve_type_path(self,path,loc):
        if len(path)==1:
            if path[0] in BASIC: return BASIC[path[0]]
            if path[0] in self.local_types: return NamedType(self.local_types[path[0]])
        if len(path)==2 and path[0] in self.imports and self.imports[path[0]]==("std","files"):
            if path[1]=="FileError": return NamedType(STD_FILE_ERROR)
            if path[1]=="File": return STD_FILE
        if len(path)==2 and path[0] in self.imported_modules:
            mod=self.imported_modules[path[0]]; canonical=mod.analyzer.local_types.get(path[1])
            if canonical is not None and mod.analyzer.structs[canonical].public: return NamedType(canonical)
        raise SemanticError(f"unknown type {'.'.join(path)!r}",loc)

    def _is_error_type(self,t):
        t=resolve(t)
        return isinstance(t,NamedType) and (t.name==STD_FILE_ERROR or (t.name in self.structs and self.structs[t.name].is_error))
    def _equality_comparable(self,t,seen):
        t=resolve(t)
        if isinstance(t,TypeVar): return True
        if isinstance(t,NamedType):
            if t.name in BASIC: return True
            if t.name in seen: return True
            if t.name in self.structs:
                seen=seen|{t.name}; return all(self._equality_comparable(f.type,seen) for f in self.structs[t.name].fields.values())
            return False
        if isinstance(t,(MaybeType,IdentityType)): return self._equality_comparable(t.inner,seen)
        if isinstance(t,ListType): return self._equality_comparable(t.element,seen)
        return False
    def _deep_fixable(self,t,seen):
        t=resolve(t)
        if isinstance(t,TypeVar): return False
        if isinstance(t,(IdentityType,ResourceType)): return False
        if isinstance(t,MaybeType): return self._deep_fixable(t.inner,seen)
        if isinstance(t,ListType): return self._deep_fixable(t.element,seen)
        if isinstance(t,NamedType):
            if t.name in BASIC: return True
            if t.name in seen: return True
            if t.name in self.structs:
                seen=seen|{t.name}; return all(self._deep_fixable(f.type,seen) for f in self.structs[t.name].fields.values())
            return False
        return False
    def _record(self,e,t,failures): self.expr_types[id(e)]=t; self.expr_failures[id(e)]=set(failures); return t
    def _unify_or_error(self,a,b,loc,context):
        try: return unify(a,b)
        except TypeError: raise SemanticError(f"{context}: expected {describe(a)}, got {describe(b)}",loc)
    def _require_type(self,a,b,loc,msg):
        try: unify(a,b)
        except TypeError: raise SemanticError(msg,loc)
    def _join_types(self,a,b):
        aa=resolve(a); bb=resolve(b)
        if isinstance(aa,MaybeType) and not isinstance(bb,MaybeType):
            unify(aa.inner,bb); return aa
        if isinstance(bb,MaybeType) and not isinstance(aa,MaybeType):
            unify(bb.inner,aa); return bb
        return unify(a,b)
    def _join_or_error(self,a,b,loc,context):
        try: return self._join_types(a,b)
        except TypeError: raise SemanticError(f"{context}: incompatible {describe(a)} and {describe(b)}",loc)
    def _assign_or_error(self,expected,actual,loc,context):
        ee=resolve(expected); aa=resolve(actual)
        try:
            if isinstance(ee,MaybeType) and not isinstance(aa,MaybeType):
                unify(ee.inner,aa); return expected
            return unify(expected,actual)
        except TypeError: raise SemanticError(f"{context}: expected {describe(expected)}, got {describe(actual)}",loc)

    def _validate_scope_inference(self,scope):
        generic_ids=set()
        if self.current_function is not None:
            for decl_t,param_t in zip(self.current_function.function.typed_parameters,self.current_function.spec.parameter_types):
                if decl_t is None: generic_ids |= unresolved_ids(param_t)
        for name,sym in scope.items():
            if sym.resource_owned: continue
            ids=unresolved_ids(sym.type)
            if ids and not ids.issubset(generic_ids): raise SemanticError(f"cannot infer a complete static type for {name!r}",sym.location)
            if sym.fixed and not ids and not self._deep_fixable(sym.type,set()): raise SemanticError(f"cannot make {name!r} fixed: {describe(sym.type)} is not deep-fixable",sym.location)
    def _validate_pending(self):
        for t,loc,name in self._fixed_pending:
            if not has_unresolved(t) and not self._deep_fixable(t,set()): raise SemanticError(f"cannot make {name!r} fixed: {describe(t)} is not deep-fixable",loc)
