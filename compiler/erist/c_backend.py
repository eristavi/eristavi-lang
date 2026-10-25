from __future__ import annotations
from dataclasses import fields as dc_fields, is_dataclass
from .ir import *

class CBackend:
    def __init__(self):
        self.indent=0; self.temp=0; self.struct_names=set(); self.maybe_types=set(); self.maybe_defined=set(); self.extra_list_types=set(); self.structs={}

    def emit(self,p:IRProgram)->str:
        self.struct_names={s.name for s in p.structs}; self.structs={s.name:s for s in p.structs}
        self.maybe_types=self._collect_prefixed_types(p,'maybe ')
        all_lists=self._collect_prefixed_types(p,'List of ')
        self.extra_list_types={t for t in all_lists if list_element(t) not in ('Int','Float','Bool','Text')}
        ordered=self._order_structs(p.structs)
        parts=[RUNTIME]
        if ordered: parts.append('\n'.join(f'typedef struct {struct_tag(s.name)} {ctype(s.name)};' for s in ordered))
        if self.extra_list_types: parts.append('\n'.join(self._list_typedef(t) for t in sorted(self.extra_list_types)))
        for t in sorted(self.maybe_types):
            if self._maybe_ready(t,set()): parts.append(self._maybe_typedef(t)); self.maybe_defined.add(t)
        defined_structs=set()
        for s in ordered:
            for t in [f.type_name for f in s.fields if f.type_name.startswith('maybe ')]:
                if t not in self.maybe_defined and self._maybe_ready(t,defined_structs): parts.append(self._maybe_typedef(t)); self.maybe_defined.add(t)
            parts.append(self._struct_definition(s)); defined_structs.add(s.name)
        for t in sorted(self.maybe_types):
            if t not in self.maybe_defined:
                if not self._maybe_ready(t,defined_structs): raise ValueError(f'cannot lay out {t}')
                parts.append(self._maybe_typedef(t)); self.maybe_defined.add(t)
        if ordered: parts.append('\n'.join(f'static bool {eq_helper(s.name)}({ctype(s.name)} a, {ctype(s.name)} b);' for s in ordered))
        if self.maybe_types: parts.append('\n'.join(f'static bool {maybe_eq(t)}({ctype(t)} a, {ctype(t)} b);' for t in sorted(self.maybe_types)))
        if self.extra_list_types: parts.append('\n'.join(f'static bool {list_helper(t)}_eq({ctype(t)} a, {ctype(t)} b);' for t in sorted(self.extra_list_types)))
        for s in ordered: parts.append(self._identity_helper_for_struct(s.name))
        for s in ordered: parts.append(self._struct_equality(s))
        for s in ordered:
            if s.is_error: parts.append(self._error_raise_helper(s))
        for t in sorted(self.maybe_types): parts.append(self._maybe_equality(t))
        for t in sorted(self.extra_list_types): parts.append(self._list_helpers(t))
        if p.functions: parts.append('\n'.join(self._function_prototype(f) for f in p.functions))
        for f in p.functions: parts.append(self._function(f))
        body=self._stmts(p.entry,[])
        parts.append(self._entry_function(body))
        return '\n'.join(x for x in parts if x)

    def _entry_function(self,body):
        return 'int main(void) {\n    fesetround(FE_TONEAREST);\n'+self._indent_text(body,1)+'    return 0;\n}\n'

    def _collect_prefixed_types(self,p,prefix):
        out=set()
        def add_type(t):
            if not isinstance(t,str): return
            if t.startswith(prefix): out.add(t)
            if t.startswith('maybe '): add_type(maybe_inner(t))
            if t.startswith('List of '): add_type(list_element(t))
        def walk(x):
            if isinstance(x,str): return
            if isinstance(x,(list,tuple,set)):
                for y in x: walk(y)
                return
            if is_dataclass(x):
                if hasattr(x,'type_name'): add_type(getattr(x,'type_name'))
                if isinstance(x,IRFunction) and x.return_type: add_type(x.return_type)
                for f in dc_fields(x): walk(getattr(x,f.name))
        walk(p); return out

    def _maybe_ready(self,t,defined):
        inner=maybe_inner(t)
        if inner.startswith('identity '): return True
        if inner in ('Int','Float','Bool','Text'): return True
        return inner in defined
    def _maybe_typedef(self,t):
        inner=maybe_inner(t); ct=ctype(t); ict=ctype(inner)
        return f'typedef struct {{ bool has; {ict} value; }} {ct};\nstatic {ict} {maybe_get(t)}({ct} v) {{ if(!v.has) eri_fault("optional value is absent"); return v.value; }}\n'
    def _maybe_equality(self,t):
        inner=maybe_inner(t); comp=self._eq_component(inner,'a.value','b.value')
        return f'static bool {maybe_eq(t)}({ctype(t)} a, {ctype(t)} b) {{ if(a.has!=b.has)return false; if(!a.has)return true; return {comp}; }}\n'
    def _list_typedef(self,t): return f'typedef struct {{ size_t count; {ctype(list_element(t))} *data; }} {list_helper(t)};'
    def _list_helpers(self,t):
        elem=list_element(t); ct=ctype(elem); h=list_helper(t); eq=self._eq_component(elem,'a.data[i]','b.data[i]')
        return f'''static {h} {h}_make(size_t n,const {ct} *src){{ {h} r={{n,NULL}}; if(n){{r.data=({ct}*)eri_alloc(sizeof({ct})*n); memcpy(r.data,src,sizeof({ct})*n);}} return r; }}
static void {h}_detach({h} *v){{ if(!v->count){{v->data=NULL;return;}} {ct} *p=({ct}*)eri_alloc(sizeof({ct})*v->count); memcpy(p,v->data,sizeof({ct})*v->count); v->data=p; }}
static {ct} {h}_get({h} v,int64_t i){{ if(i<0||(uint64_t)i>=v.count)eri_fault("List index out of bounds"); return v.data[i]; }}
static void {h}_set({h} *v,int64_t i,{ct} x){{ if(i<0||(uint64_t)i>=v->count)eri_fault("List index out of bounds"); {h}_detach(v); v->data[i]=x; }}
static void {h}_add({h} *v,{ct} x){{ {h}_detach(v); v->data=({ct}*)eri_realloc(v->data,sizeof({ct})*(v->count+1)); v->data[v->count++]=x; }}
static bool {h}_eq({h} a,{h} b){{ if(a.count!=b.count)return false; for(size_t i=0;i<a.count;i++){{if(!({eq}))return false;}} return true; }}
'''

    def _order_structs(self,structs):
        by={s.name:s for s in structs}; out=[]; visiting=set(); done=set()
        def dep_type(t):
            if t.startswith('identity '): return None
            if t.startswith('maybe '):
                inner=maybe_inner(t)
                if inner.startswith('identity '): return None
                return inner
            if t.startswith('List of '): return None
            return t
        def visit(s):
            if s.name in done: return
            if s.name in visiting: raise ValueError(f'recursive by-value struct layout is not supported: {s.name}')
            visiting.add(s.name)
            for f in s.fields:
                dep=dep_type(f.type_name)
                if dep in by: visit(by[dep])
            visiting.remove(s.name); done.add(s.name); out.append(s)
        for s in structs: visit(s)
        return out

    def _struct_definition(self,s):
        fs=''.join(f'    {ctype(f.type_name)} {field_name(f.name)};\n' for f in s.fields)
        return f'struct {struct_tag(s.name)} {{\n{fs}}};\n'
    def _identity_helper_for_struct(self,t):
        ct=ctype(t); return f'static {ct} *{identity_helper(t)}({ct} v) {{ {ct} *p=({ct}*)eri_alloc(sizeof({ct})); *p=v; return p; }}\n'
    def _struct_equality(self,s):
        checks=[self._eq_component(f.type_name,f'a.{field_name(f.name)}',f'b.{field_name(f.name)}') for f in s.fields]
        return f'static bool {eq_helper(s.name)}({ctype(s.name)} a, {ctype(s.name)} b) {{ return {" && ".join(checks) if checks else "true"}; }}\n'
    def _error_raise_helper(self,s):
        ct=ctype(s.name); return f'static void {fail_helper(s.name)}({ct} v) {{ {ct} *p=({ct}*)eri_alloc(sizeof({ct})); *p=v; eri_raise({c_string(s.name)}, p, v.{field_name("message")}); }}\n'
    def _eq_component(self,t,a,b):
        if t.startswith('maybe '): return f'{maybe_eq(t)}({a}, {b})'
        if t.startswith('identity '): return f'({a} == {b})'
        if t=='Text': return f'(strcmp({a}, {b}) == 0)'
        if t in ('Int','Float','Bool'): return f'({a} == {b})'
        if t.startswith('List of '): return f'{list_helper(t)}_eq({a}, {b})'
        return f'{eq_helper(t)}({a}, {b})'

    def _function_signature(self,f,semicolon=False):
        ret='void' if f.return_type is None else ctype(f.return_type)
        params=', '.join(f'{ctype(x.type_name)} {cname(x.name)}' for x in f.parameters) or 'void'
        return f'static {ret} fn_{mangle(f.name)}({params})'+(';' if semicolon else '')
    def _function_prototype(self,f): return self._function_signature(f,True)
    def _function(self,f): return self._function_signature(f)+' {\n'+self._indent_text(self._stmts(f.body,[]),1)+'}\n'

    def _stmts(self,stmts,cleanups=None):
        cleanups=list(cleanups or [])
        return ''.join(self._stmt(s,cleanups) for s in stmts)
    def _stmt(self,s,cleanups):
        if isinstance(s,IRLet): return f'{ctype(s.type_name)} {cname(s.name)} = {self._expr(s.value)};\n'
        if isinstance(s,IRAssign): return f'{cname(s.name)} = {self._expr(s.value)};\n'
        if isinstance(s,IRIndexAssign): return f'{list_helper_from_element(s.value.type_name)}_set(&{cname(s.name)}, {self._expr(s.index)}, {self._expr(s.value)});\n'
        if isinstance(s,IRMemberAssign): return f'{self._lvalue(s.target)} = {self._expr(s.value)};\n'
        if isinstance(s,IRExprStmt): return f'{self._expr(s.expression)};\n'
        if isinstance(s,IRReturn): return self._return_stmt(s,cleanups)
        if isinstance(s,IRFail): return f'{fail_helper(s.error_type)}({self._expr(s.value)});\n'
        if isinstance(s,IRHandledLet): return self._handled_let(s,cleanups)
        if isinstance(s,IRHandledAssign): return self._handled_assign(s,cleanups)
        if isinstance(s,IRHandledReturn): return self._handled_return(s,cleanups)
        if isinstance(s,IRHandledExprStmt): return self._handled_expr(s,cleanups)
        if isinstance(s,IRWith): return self._with_stmt(s,cleanups)
        if isinstance(s,IRIf):
            out=f'if ({self._expr(s.condition)}) {{\n'+self._indent_text(self._stmts(s.then_body,cleanups),1)+'}'
            if s.else_body: out+=' else {\n'+self._indent_text(self._stmts(s.else_body,cleanups),1)+'}'
            return out+'\n'
        if isinstance(s,IRWhile): return f'while ({self._expr(s.condition)}) {{\n'+self._indent_text(self._stmts(s.body,cleanups),1)+'}\n'
        if isinstance(s,IRFor):
            self.temp+=1; n=self.temp; snap=f'_eri_iter_{n}'; idx=f'_eri_i_{n}'; helper=list_helper(s.iterable.type_name); elem=list_element(s.iterable.type_name)
            head=f'{ctype(s.iterable.type_name)} {snap} = {self._expr(s.iterable)};\nfor (int64_t {idx}=0; {idx}<(int64_t){snap}.count; ++{idx}) {{\n'
            binding=f'{ctype(elem)} {cname(s.name)} = {helper}_get({snap}, {idx});\n'
            return head+self._indent_text(binding+self._stmts(s.body,cleanups),1)+'}\n'
        raise TypeError(s)

    def _cleanup_sequence(self,cleanups,after_expr=''):
        if not cleanups: return after_expr
        self.temp+=1; n=self.temp; primary=f'_eri_cleanup_primary_{n}'; one=f'_eri_cleanup_one_{n}'
        out=f'eri_failure_value {primary} = {{0}};\neri_failure_value {one} = {{0}};\n'
        for name,_frame in reversed(cleanups):
            out+=f'if (eri_file_cleanup(&{cname(name)}, &{one})) {{ if (!{primary}.type) {primary}={one}; else eri_attach_secondary(&{primary}, {one}); }}\n'
        out+=f'eri_handler_top = {cleanups[0][1]}.prev;\nif ({primary}.type) eri_propagate_saved({primary});\n'
        return out+after_expr
    def _return_stmt(self,s,cleanups):
        if not cleanups: return 'return;\n' if s.value is None else f'return {self._expr(s.value)};\n'
        self.temp+=1; n=self.temp
        if s.value is None: return self._cleanup_sequence(cleanups,'return;\n')
        tmp=f'_eri_return_{n}'; return f'{ctype(s.value.type_name)} {tmp} = {self._expr(s.value)};\n'+self._cleanup_sequence(cleanups,f'return {tmp};\n')

    def _with_stmt(self,s,cleanups):
        if s.resource_type!='std.files.File': raise TypeError(f'unsupported deterministic resource {s.resource_type}')
        self.temp+=1; n=self.temp; fr=f'_eri_with_{n}'; saved=f'_eri_with_failure_{n}'; cf=f'_eri_with_cleanup_{n}'
        active=cleanups+[(s.name,fr)]
        body=self._stmts(s.body,active)
        normal=body+f'eri_failure_value {cf} = {{0}};\nbool {cf}_failed = eri_file_cleanup(&{cname(s.name)}, &{cf});\neri_handler_top = {fr}.prev;\nif ({cf}_failed) eri_propagate_saved({cf});\n'
        failed=f'eri_failure_value {saved} = eri_failure;\neri_handler_top = {fr}.prev;\neri_failure_value {cf} = {{0}};\nif (eri_file_cleanup(&{cname(s.name)}, &{cf})) eri_attach_secondary(&{saved}, {cf});\neri_propagate_saved({saved});\n'
        return '{\n'+self._indent_text(f'{ctype(s.resource_type)} {cname(s.name)} = {self._expr(s.resource)};\neri_handler_frame {fr}; {fr}.prev=eri_handler_top; eri_handler_top=&{fr};\nif (setjmp({fr}.env)==0) {{\n'+self._indent_text(normal,1)+'} else {\n'+self._indent_text(failed,1)+'}\n',1)+'}\n'

    def _handled_let(self,s,cleanups):
        self.temp+=1; n=self.temp; fr=f'_eri_h_{n}'
        out=f'{ctype(s.type_name)} {cname(s.name)};\neri_handler_frame {fr}; {fr}.prev=eri_handler_top; eri_handler_top=&{fr};\n'
        success=f'{cname(s.name)} = {self._expr(s.value)};\neri_handler_top = {fr}.prev;\n'
        return out+f'if (setjmp({fr}.env)==0) {{\n'+self._indent_text(success,1)+'} else {\n'+self._indent_text(f'eri_handler_top = {fr}.prev;\n'+self._handler_dispatch(s.handlers,True,n,cleanups),1)+'}\n'
    def _handled_assign(self,s,cleanups):
        self.temp+=1; n=self.temp; fr=f'_eri_h_{n}'; tmp=f'_eri_v_{n}'
        out=f'{ctype(s.target_type)} {tmp};\neri_handler_frame {fr}; {fr}.prev=eri_handler_top; eri_handler_top=&{fr};\n'
        success=f'{tmp} = {self._expr(s.value)};\neri_handler_top = {fr}.prev;\n{self._assign_target(s.target,tmp)}'
        return out+f'if (setjmp({fr}.env)==0) {{\n'+self._indent_text(success,1)+'} else {\n'+self._indent_text(f'eri_handler_top = {fr}.prev;\n'+self._handler_dispatch(s.handlers,True,n,cleanups),1)+'}\n'
    def _handled_return(self,s,cleanups):
        self.temp+=1; n=self.temp; fr=f'_eri_h_{n}'; tmp=f'_eri_v_{n}'
        out=f'{ctype(s.value.type_name)} {tmp};\neri_handler_frame {fr}; {fr}.prev=eri_handler_top; eri_handler_top=&{fr};\n'
        after=self._cleanup_sequence(cleanups,f'return {tmp};\n') if cleanups else f'return {tmp};\n'
        success=f'{tmp} = {self._expr(s.value)};\neri_handler_top = {fr}.prev;\n'+after
        return out+f'if (setjmp({fr}.env)==0) {{\n'+self._indent_text(success,1)+'} else {\n'+self._indent_text(f'eri_handler_top = {fr}.prev;\n'+self._handler_dispatch(s.handlers,True,n,cleanups),1)+'}\n'
    def _handled_expr(self,s,cleanups):
        self.temp+=1; n=self.temp; fr=f'_eri_h_{n}'
        out=f'eri_handler_frame {fr}; {fr}.prev=eri_handler_top; eri_handler_top=&{fr};\n'
        success=f'(void)({self._expr(s.value)});\neri_handler_top = {fr}.prev;\n'
        return out+f'if (setjmp({fr}.env)==0) {{\n'+self._indent_text(success,1)+'} else {\n'+self._indent_text(f'eri_handler_top = {fr}.prev;\n'+self._handler_dispatch(s.handlers,False,n,cleanups),1)+'}\n'
    def _handler_dispatch(self,handlers,must_terminate,n,cleanups):
        saved=f'_eri_failure_{n}'; out=f'eri_failure_value {saved} = eri_failure;\n'; parts=[]; catchall=None
        for h in handlers:
            body=self._stmts(h.body,cleanups)
            if h.error_type is None:
                bind=f'eri_error_view {cname("error")} = {{ {saved}.message }};\n'; catchall=bind+body+(('eri_fault("value error handler completed without terminating");\n') if must_terminate else '')
            else:
                bind=f'{ctype(h.error_type)} {cname("error")} = *({ctype(h.error_type)}*){saved}.payload;\n'; branch=bind+body+(('eri_fault("value error handler completed without terminating");\n') if must_terminate else '')
                parts.append((h.error_type,branch))
        for i,(t,b) in enumerate(parts): out+=('if' if i==0 else 'else if')+f' (strcmp({saved}.type, {c_string(t)}) == 0) {{\n'+self._indent_text(b,1)+'}\n'
        if catchall is not None: out+=('else ' if parts else '')+'{\n'+self._indent_text(catchall,1)+'}\n'
        else: out+=('else ' if parts else '')+'{ eri_propagate_saved('+saved+'); }\n'
        return out

    def _assign_target(self,t,value_name):
        if isinstance(t,IRVar): return f'{cname(t.name)} = {value_name};\n'
        if isinstance(t,IRMember): return f'{self._lvalue(t)} = {value_name};\n'
        if isinstance(t,IRIndex): return f'{list_helper(t.base.type_name)}_set(&{self._lvalue(t.base)}, {self._expr(t.index)}, {value_name});\n'
        raise TypeError(t)
    def _lvalue(self,e):
        if isinstance(e,IRVar): return cname(e.name)
        if isinstance(e,IRMaybeGet): return f'({self._lvalue(e.value)}).value'
        if isinstance(e,IRMember):
            base=self._lvalue(e.base); op='->' if e.base.type_name.startswith('identity ') else '.'
            return f'({base}){op}{field_name(e.name)}'
        raise TypeError(f'unsupported C lvalue {e!r}')
    def _resource_ptr(self,e): return '&'+self._lvalue(e)

    def _expr(self,e):
        if isinstance(e,IRConst):
            if e.type_name=='Text': return c_string(str(e.value))
            if e.type_name=='Bool': return 'true' if e.value else 'false'
            if e.type_name=='Float':
                v=float(e.value)
                if v!=v: return 'NAN'
                if v==float('inf'): return 'INFINITY'
                if v==float('-inf'): return '(-INFINITY)'
                return repr(v)
            return str(e.value)
        if isinstance(e,IRVar): return cname(e.name)
        if isinstance(e,IRMaybeNone): return f'({ctype(e.type_name)}){{.has=false}}'
        if isinstance(e,IRMaybeSome): return f'({ctype(e.type_name)}){{.has=true,.value={self._expr(e.value)}}}'
        if isinstance(e,IRMaybeGet): return f'{maybe_get(e.value.type_name)}({self._expr(e.value)})'
        if isinstance(e,IRIdentity): return f'{identity_helper(identity_inner(e.type_name))}({self._expr(e.value)})'
        if isinstance(e,IRFileOpen): return f'eri_file_open({self._expr(e.path)})'
        if isinstance(e,IRFileRead): return f'eri_file_read_text({self._resource_ptr(e.resource)})'
        if isinstance(e,IRFileWrite): return f'eri_file_write_text({self._resource_ptr(e.resource)}, {self._expr(e.text)})'
        if isinstance(e,IRConstruct):
            vals=', '.join(f'.{field_name(x.name)} = {self._expr(x.value)}' for x in e.fields); return f'({ctype(e.type_name)}){{{vals}}}'
        if isinstance(e,IRMember):
            op='->' if e.base.type_name.startswith('identity ') else '.'; return f'({self._expr(e.base)}){op}{field_name(e.name)}'
        if isinstance(e,IRList):
            helper=list_helper(e.type_name); elem=list_element(e.type_name)
            if not e.elements: return f'{helper}_make(0, NULL)'
            return f'{helper}_make({len(e.elements)}, ({ctype(elem)}[]){{{", ".join(self._expr(x) for x in e.elements)}}})'
        if isinstance(e,IRIndex): return f'{list_helper(e.base.type_name)}_get({self._expr(e.base)}, {self._expr(e.index)})'
        if isinstance(e,IRCount): return f'((int64_t)({self._expr(e.base)}).count)'
        if isinstance(e,IRListAdd): return f'{list_helper_from_element(e.value.type_name)}_add(&{cname(e.base_name)}, {self._expr(e.value)})'
        if isinstance(e,IRUnary):
            if e.operator=='not': return f'(!{self._expr(e.operand)})'
            if e.operator=='-' and e.type_name=='Int': return f'eri_ineg({self._expr(e.operand)})'
            if e.operator=='-' and e.type_name=='Float': return f'eri_fneg({self._expr(e.operand)})'
        if isinstance(e,IRBinary):
            a=self._expr(e.left); b=self._expr(e.right); op=e.operator
            if e.left.type_name.startswith('maybe ') and op in ('==','!='):
                cmp=f'{maybe_eq(e.left.type_name)}({a}, {b})'; return cmp if op=='==' else f'(!{cmp})'
            if e.left.type_name.startswith('identity ') and op in ('==','!='):
                cmp=f'({a} == {b})'; return cmp if op=='==' else f'(!{cmp})'
            if e.left.type_name.startswith('List of ') and op in ('==','!='):
                cmp=f'{list_helper(e.left.type_name)}_eq({a}, {b})'; return cmp if op=='==' else f'(!{cmp})'
            if e.left.type_name not in ('Int','Float','Bool','Text') and op in ('==','!='):
                cmp=f'{eq_helper(e.left.type_name)}({a}, {b})'; return cmp if op=='==' else f'(!{cmp})'
            if e.left.type_name=='Int' and op in '+-*/%': return f'eri_i{OPNAME[op]}({a}, {b})'
            if e.left.type_name=='Float' and op in '+-*/': return f'eri_f{OPNAME[op]}({a}, {b})'
            if e.left.type_name=='Text' and op=='+': return f'eri_text_add({a}, {b})'
            if e.left.type_name=='Text' and op in ('==','!='):
                cmp=f'(strcmp({a}, {b}) == 0)'; return cmp if op=='==' else f'(!{cmp})'
            return f'({a} { {"and":"&&","or":"||","==":"==","!=":"!=","<":"<","<=":"<=",">":">",">=":">="}.get(op,op) } {b})'
        if isinstance(e,IRCall):
            args=', '.join(self._expr(a) for a in e.arguments)
            if e.name=='output':
                a=e.arguments[0]
                if a.type_name=='Int': return f'eri_out_int({self._expr(a)})'
                if a.type_name=='Float': return f'eri_out_float({self._expr(a)})'
                if a.type_name=='Bool': return f'eri_out_bool({self._expr(a)})'
                if a.type_name=='Text': return f'eri_out_text({self._expr(a)})'
            return f'fn_{mangle(e.name)}({args})'
        raise TypeError(e)

    @staticmethod
    def _indent_text(text,n):
        if not text: return ''
        pref='    '*n; return ''.join(pref+line if line.strip() else line for line in text.splitlines(True))

OPNAME={'+':'add','-':'sub','*':'mul','/':'div','%':'rem'}
def mangle(n):
    return ''.join(c if c.isascii() and (c.isalnum() or c=='_') else f'_u{ord(c):04x}_' for c in n)
def cname(n): return 'v_'+mangle(n)
def field_name(n): return 'f_'+mangle(n)
def struct_tag(t): return 'eri_struct_tag_'+mangle(t)
def eq_helper(t): return 'eri_eq_'+mangle(t)
def fail_helper(t): return 'eri_fail_'+mangle(t)
def maybe_inner(t):
    if not t.startswith('maybe '): raise KeyError(t)
    return t[6:]
def maybe_name(t): return 'eri_maybe_'+mangle(maybe_inner(t))
def maybe_eq(t): return maybe_name(t)+'_eq'
def maybe_get(t): return maybe_name(t)+'_get'
def identity_inner(t):
    if not t.startswith('identity '): raise KeyError(t)
    return t[9:]
def identity_helper(t): return 'eri_identity_'+mangle(t)+'_new'
def list_element(t):
    if not t.startswith('List of '): raise KeyError(t)
    return t[8:]
def list_helper(t): return list_helper_from_element(list_element(t))
def list_helper_from_element(t): return {'Int':'eri_list_int','Float':'eri_list_float','Bool':'eri_list_bool','Text':'eri_list_text'}.get(t,'eri_list_'+mangle(t))
def ctype(t):
    scalars={'Int':'int64_t','Float':'double','Bool':'bool','Text':'const char *','checked error':'eri_error_view','std.files.File':'eri_file','std.files.FileError':'eri_file_error'}
    if t in scalars: return scalars[t]
    if t.startswith('maybe '): return maybe_name(t)
    if t.startswith('identity '): return ctype(identity_inner(t))+' *'
    if t.startswith('List of '): return list_helper(t)
    return 'eri_struct_'+mangle(t)
def c_string(s): return '"'+s.replace('\\','\\\\').replace('"','\\"').replace('\n','\\n').replace('\r','\\r').replace('\t','\\t').replace('\0','\\0')+'"'

RUNTIME=r'''#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <inttypes.h>
#include <limits.h>
#include <math.h>
#include <fenv.h>
#include <string.h>
#include <stddef.h>
#include <setjmp.h>
#include <errno.h>

typedef struct eri_handler_frame { jmp_buf env; struct eri_handler_frame *prev; } eri_handler_frame;
typedef struct eri_secondary_failure { const char *type; void *payload; const char *message; struct eri_secondary_failure *next; } eri_secondary_failure;
typedef struct { const char *type; void *payload; const char *message; eri_secondary_failure *secondary; } eri_failure_value;
typedef struct { const char *f_message; } eri_error_view;
static eri_handler_frame *eri_handler_top = NULL;
static eri_failure_value eri_failure = {NULL,NULL,NULL,NULL};

static void eri_fault(const char *m) { fprintf(stderr, "Eristavi runtime fault: %s\n", m); exit(1); }
static void *eri_alloc(size_t n){ void *p=malloc(n?n:1); if(!p)eri_fault("out of memory"); return p; }
static void *eri_realloc(void *p,size_t n){ void *q=realloc(p,n?n:1); if(!q)eri_fault("out of memory"); return q; }
static char *eri_text_dup(const char *s){ size_t n=strlen(s); char *r=(char*)eri_alloc(n+1); memcpy(r,s,n+1); return r; }
static void eri_attach_secondary(eri_failure_value *primary, eri_failure_value secondary){ eri_secondary_failure *n=(eri_secondary_failure*)eri_alloc(sizeof(*n)); n->type=secondary.type; n->payload=secondary.payload; n->message=secondary.message; n->next=NULL; eri_secondary_failure **p=&primary->secondary; while(*p)p=&(*p)->next; *p=n; }
static void eri_raise(const char *type, void *payload, const char *message){ eri_failure=(eri_failure_value){type,payload,message,NULL}; if(!eri_handler_top)eri_fault(message?message:"unhandled checked failure"); longjmp(eri_handler_top->env,1); }
static void eri_propagate_saved(eri_failure_value f){ eri_failure=f; if(!eri_handler_top)eri_fault(f.message?f.message:"unhandled checked failure"); longjmp(eri_handler_top->env,1); }
static char *eri_text_add(const char *a,const char *b){ size_t na=strlen(a),nb=strlen(b); char *r=(char*)eri_alloc(na+nb+1); memcpy(r,a,na); memcpy(r+na,b,nb+1); return r; }

typedef struct { const char *f_message; const char *f_path; } eri_file_error;
typedef struct { const char *path; FILE *handle; bool closed; } eri_file;
static eri_failure_value eri_make_file_failure(const char *message,const char *path){ eri_file_error *e=(eri_file_error*)eri_alloc(sizeof(*e)); e->f_message=eri_text_dup(message?message:"file error"); e->f_path=eri_text_dup(path?path:""); return (eri_failure_value){"std.files.FileError",e,e->f_message,NULL}; }
static void eri_raise_file_failure(const char *message,const char *path){ eri_failure_value f=eri_make_file_failure(message,path); eri_raise(f.type,f.payload,f.message); }
static void eri_fail_std_u002e_files_u002e_FileError(eri_file_error v){ eri_file_error *p=(eri_file_error*)eri_alloc(sizeof(*p)); *p=v; eri_raise("std.files.FileError",p,v.f_message); }
static eri_file eri_file_open(const char *path){ FILE *h=fopen(path,"r+"); if(!h)eri_raise_file_failure(strerror(errno),path); return (eri_file){path,h,false}; }
static const char *eri_file_read_text(eri_file *f){ if(!f||f->closed||!f->handle)eri_fault("file resource is closed"); if(fseek(f->handle,0,SEEK_END)!=0)eri_raise_file_failure(strerror(errno),f->path); long n=ftell(f->handle); if(n<0)eri_raise_file_failure(strerror(errno),f->path); rewind(f->handle); char *buf=(char*)eri_alloc((size_t)n+1); size_t got=fread(buf,1,(size_t)n,f->handle); if(got<(size_t)n&&ferror(f->handle))eri_raise_file_failure(strerror(errno),f->path); buf[got]='\0'; return buf; }
static void eri_file_write_text(eri_file *f,const char *text){ if(!f||f->closed||!f->handle)eri_fault("file resource is closed"); FILE *h=freopen(f->path,"w+",f->handle); if(!h){f->handle=NULL; f->closed=true; eri_raise_file_failure(strerror(errno),f->path);} f->handle=h; size_t n=strlen(text); if(fwrite(text,1,n,h)!=n)eri_raise_file_failure(strerror(errno),f->path); if(fflush(h)!=0)eri_raise_file_failure(strerror(errno),f->path); rewind(h); }
static bool eri_file_cleanup(eri_file *f,eri_failure_value *failure){ if(!f||f->closed)return false; FILE *h=f->handle; f->handle=NULL; f->closed=true; if(h&&fclose(h)!=0){ if(failure)*failure=eri_make_file_failure(strerror(errno),f->path); return true; } return false; }

static int64_t *eri_identity_Int_new(int64_t v){ int64_t *p=(int64_t*)eri_alloc(sizeof(int64_t)); *p=v; return p; }
static double *eri_identity_Float_new(double v){ double *p=(double*)eri_alloc(sizeof(double)); *p=v; return p; }
static bool *eri_identity_Bool_new(bool v){ bool *p=(bool*)eri_alloc(sizeof(bool)); *p=v; return p; }
static const char **eri_identity_Text_new(const char *v){ const char **p=(const char**)eri_alloc(sizeof(char*)); *p=v; return p; }
static int64_t eri_iadd(int64_t a,int64_t b){ if((b>0&&a>INT64_MAX-b)||(b<0&&a<INT64_MIN-b))eri_fault("Int overflow"); return a+b; }
static int64_t eri_isub(int64_t a,int64_t b){ if((b<0&&a>INT64_MAX+b)||(b>0&&a<INT64_MIN+b))eri_fault("Int overflow"); return a-b; }
static int64_t eri_imul(int64_t a,int64_t b){ if(a==0||b==0)return 0; if((a==INT64_MIN&&b==-1)||(b==INT64_MIN&&a==-1))eri_fault("Int overflow"); if(a>0){ if(b>0){if(a>INT64_MAX/b)eri_fault("Int overflow");} else {if(b<INT64_MIN/a)eri_fault("Int overflow");}} else { if(b>0){if(a<INT64_MIN/b)eri_fault("Int overflow");} else {if(a!=0&&b<INT64_MAX/a)eri_fault("Int overflow");}} return a*b; }
static int64_t eri_idiv(int64_t a,int64_t b){ if(!b)eri_fault("Int division by zero"); if(a==INT64_MIN&&b==-1)eri_fault("Int overflow"); return a/b; }
static int64_t eri_irem(int64_t a,int64_t b){ if(!b)eri_fault("Int remainder by zero"); if(a==INT64_MIN&&b==-1)eri_fault("Int overflow"); return a%b; }
static int64_t eri_ineg(int64_t a){ if(a==INT64_MIN)eri_fault("Int overflow"); return -a; }
static double eri_fadd(double a,double b){ volatile double r=a+b; return r; }
static double eri_fsub(double a,double b){ volatile double r=a-b; return r; }
static double eri_fmul(double a,double b){ volatile double r=a*b; return r; }
static double eri_fdiv(double a,double b){ volatile double r; if(b==0.0){if(a==0.0||isnan(a))r=NAN;else r=copysign(INFINITY,copysign(1.0,a)*copysign(1.0,b));}else r=a/b; return r; }
static double eri_fneg(double a){ volatile double r=-a; return r; }
static void eri_out_int(int64_t v){ printf("%" PRId64 "\n",v); }
static void eri_out_float(double v){ printf("%.17g\n",v); }
static void eri_out_bool(bool v){ puts(v?"true":"false"); }
static void eri_out_text(const char *v){ puts(v); }

#define ERI_LIST_SCALAR(NAME, TYPE) \
typedef struct { size_t count; TYPE *data; } eri_list_##NAME; \
static eri_list_##NAME eri_list_##NAME##_make(size_t n,const TYPE *src){ eri_list_##NAME r={n,NULL}; if(n){r.data=(TYPE*)eri_alloc(sizeof(TYPE)*n); memcpy(r.data,src,sizeof(TYPE)*n);} return r; } \
static void eri_list_##NAME##_detach(eri_list_##NAME *v){ if(!v->count){v->data=NULL;return;} TYPE *p=(TYPE*)eri_alloc(sizeof(TYPE)*v->count); memcpy(p,v->data,sizeof(TYPE)*v->count); v->data=p; } \
static TYPE eri_list_##NAME##_get(eri_list_##NAME v,int64_t i){ if(i<0||(uint64_t)i>=v.count)eri_fault("List index out of bounds"); return v.data[i]; } \
static void eri_list_##NAME##_set(eri_list_##NAME *v,int64_t i,TYPE x){ if(i<0||(uint64_t)i>=v->count)eri_fault("List index out of bounds"); eri_list_##NAME##_detach(v); v->data[i]=x; } \
static void eri_list_##NAME##_add(eri_list_##NAME *v,TYPE x){ eri_list_##NAME##_detach(v); v->data=(TYPE*)eri_realloc(v->data,sizeof(TYPE)*(v->count+1)); v->data[v->count++]=x; } \
static bool eri_list_##NAME##_eq(eri_list_##NAME a,eri_list_##NAME b){ if(a.count!=b.count)return false; for(size_t i=0;i<a.count;i++){if(!(a.data[i]==b.data[i]))return false;} return true; }
ERI_LIST_SCALAR(int, int64_t)
ERI_LIST_SCALAR(float, double)
ERI_LIST_SCALAR(bool, bool)
typedef struct { size_t count; const char **data; } eri_list_text;
static eri_list_text eri_list_text_make(size_t n,const char **src){ eri_list_text r={n,NULL}; if(n){r.data=(const char**)eri_alloc(sizeof(char*)*n); memcpy(r.data,src,sizeof(char*)*n);} return r; }
static void eri_list_text_detach(eri_list_text *v){ if(!v->count){v->data=NULL;return;} const char **p=(const char**)eri_alloc(sizeof(char*)*v->count); memcpy(p,v->data,sizeof(char*)*v->count); v->data=p; }
static const char *eri_list_text_get(eri_list_text v,int64_t i){ if(i<0||(uint64_t)i>=v.count)eri_fault("List index out of bounds"); return v.data[i]; }
static void eri_list_text_set(eri_list_text *v,int64_t i,const char *x){ if(i<0||(uint64_t)i>=v->count)eri_fault("List index out of bounds"); eri_list_text_detach(v); v->data[i]=x; }
static void eri_list_text_add(eri_list_text *v,const char *x){ eri_list_text_detach(v); v->data=(const char**)eri_realloc(v->data,sizeof(char*)*(v->count+1)); v->data[v->count++]=x; }
static bool eri_list_text_eq(eri_list_text a,eri_list_text b){ if(a.count!=b.count)return false; for(size_t i=0;i<a.count;i++){if(strcmp(a.data[i],b.data[i])!=0)return false;} return true; }
'''
