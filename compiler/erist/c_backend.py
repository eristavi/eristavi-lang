from __future__ import annotations
from dataclasses import fields as dc_fields, is_dataclass
from .ir import *

class CBackend:
    def __init__(self):
        self.indent=0; self.temp=0; self.struct_names=set(); self.maybe_types=set(); self.maybe_defined=set(); self.extra_list_types=set()
    def emit(self,p:IRProgram)->str:
        self.struct_names={s.name for s in p.structs}
        self.maybe_types=self._collect_prefixed_types(p,'maybe ')
        all_lists=self._collect_prefixed_types(p,'List of ')
        self.extra_list_types={t for t in all_lists if list_element(t) not in ('Int','Float','Bool','Text')}
        ordered=self._order_structs(p.structs)
        parts=[RUNTIME]
        if ordered: parts.append('\n'.join(f'typedef struct {struct_tag(s.name)} {ctype(s.name)};' for s in ordered))
        if self.extra_list_types:
            parts.append('\n'.join(self._list_typedef(t) for t in sorted(self.extra_list_types)))
        for t in sorted(self.maybe_types):
            if self._maybe_ready(t,set()): parts.append(self._maybe_typedef(t)); self.maybe_defined.add(t)
        defined_structs=set()
        for s in ordered:
            for t in [f.type_name for f in s.fields if f.type_name.startswith('maybe ')]:
                if t not in self.maybe_defined and self._maybe_ready(t,defined_structs):
                    parts.append(self._maybe_typedef(t)); self.maybe_defined.add(t)
            parts.append(self._struct_definition(s)); defined_structs.add(s.name)
        for t in sorted(self.maybe_types):
            if t not in self.maybe_defined:
                if not self._maybe_ready(t,defined_structs): raise ValueError(f'cannot lay out {t}')
                parts.append(self._maybe_typedef(t)); self.maybe_defined.add(t)
        if ordered:
            parts.append('\n'.join(f'static bool {eq_helper(s.name)}({ctype(s.name)} a, {ctype(s.name)} b);' for s in ordered))
        if self.maybe_types:
            parts.append('\n'.join(f'static bool {maybe_eq(t)}({ctype(t)} a, {ctype(t)} b);' for t in sorted(self.maybe_types)))
        if self.extra_list_types:
            parts.append('\n'.join(f'static bool {list_helper(t)}_eq({ctype(t)} a, {ctype(t)} b);' for t in sorted(self.extra_list_types)))
        for s in ordered: parts.append(self._identity_helper_for_struct(s.name))
        for s in ordered: parts.append(self._struct_equality(s))
        for t in sorted(self.maybe_types): parts.append(self._maybe_equality(t))
        for t in sorted(self.extra_list_types): parts.append(self._list_helpers(t))
        for f in p.functions: parts.append(self._function(f))
        body=self._stmts(p.entry)
        parts.append('int main(void) {\n    fesetround(FE_TONEAREST);\n'+self._indent_text(body,1)+'    return 0;\n}\n')
        return '\n'.join(x for x in parts if x)
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
    def _list_typedef(self,t):
        elem=list_element(t)
        return f'typedef struct {{ size_t count; {ctype(elem)} *data; }} {list_helper(t)};'
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
        ct=ctype(t); fn=identity_helper(t)
        return f'static {ct} *{fn}({ct} v) {{ {ct} *p=({ct}*)eri_alloc(sizeof({ct})); *p=v; return p; }}\n'
    def _struct_equality(self,s):
        checks=[self._eq_component(f.type_name,f'a.{field_name(f.name)}',f'b.{field_name(f.name)}') for f in s.fields]
        expr=' && '.join(checks) if checks else 'true'
        return f'static bool {eq_helper(s.name)}({ctype(s.name)} a, {ctype(s.name)} b) {{ return {expr}; }}\n'
    def _eq_component(self,t,a,b):
        if t.startswith('maybe '): return f'{maybe_eq(t)}({a}, {b})'
        if t.startswith('identity '): return f'({a} == {b})'
        if t=='Text': return f'(strcmp({a}, {b}) == 0)'
        if t in ('Int','Float','Bool'): return f'({a} == {b})'
        if t.startswith('List of '): return f'{list_helper(t)}_eq({a}, {b})'
        return f'{eq_helper(t)}({a}, {b})'
    def _function(self,f):
        ret='void' if f.return_type is None else ctype(f.return_type)
        params=', '.join(f'{ctype(x.type_name)} {cname(x.name)}' for x in f.parameters) or 'void'
        return f'static {ret} fn_{mangle(f.name)}({params}) {{\n'+self._indent_text(self._stmts(f.body),1)+'}\n'
    def _stmts(self,stmts): return ''.join(self._stmt(s) for s in stmts)
    def _stmt(self,s):
        if isinstance(s,IRLet): return f'{ctype(s.type_name)} {cname(s.name)} = {self._expr(s.value)};\n'
        if isinstance(s,IRAssign): return f'{cname(s.name)} = {self._expr(s.value)};\n'
        if isinstance(s,IRIndexAssign): return f'{list_helper_from_element(s.value.type_name)}_set(&{cname(s.name)}, {self._expr(s.index)}, {self._expr(s.value)});\n'
        if isinstance(s,IRMemberAssign): return f'{self._lvalue(s.target)} = {self._expr(s.value)};\n'
        if isinstance(s,IRExprStmt): return f'{self._expr(s.expression)};\n'
        if isinstance(s,IRReturn): return 'return;\n' if s.value is None else f'return {self._expr(s.value)};\n'
        if isinstance(s,IRIf):
            out=f'if ({self._expr(s.condition)}) {{\n'+self._indent_text(self._stmts(s.then_body),1)+'}'
            if s.else_body: out+=' else {\n'+self._indent_text(self._stmts(s.else_body),1)+'}'
            return out+'\n'
        if isinstance(s,IRWhile): return f'while ({self._expr(s.condition)}) {{\n'+self._indent_text(self._stmts(s.body),1)+'}\n'
        if isinstance(s,IRFor):
            self.temp+=1; n=self.temp; snap=f'_eri_iter_{n}'; idx=f'_eri_i_{n}'; helper=list_helper(s.iterable.type_name); elem=list_element(s.iterable.type_name)
            head=f'{ctype(s.iterable.type_name)} {snap} = {self._expr(s.iterable)};\nfor (int64_t {idx}=0; {idx}<(int64_t){snap}.count; ++{idx}) {{\n'
            binding=f'{ctype(elem)} {cname(s.name)} = {helper}_get({snap}, {idx});\n'
            return head+self._indent_text(binding+self._stmts(s.body),1)+'}\n'
        raise TypeError(s)
    def _lvalue(self,e):
        if isinstance(e,IRVar): return cname(e.name)
        if isinstance(e,IRMaybeGet): return f'({self._lvalue(e.value)}).value'
        if isinstance(e,IRMember):
            base=self._lvalue(e.base); op='->' if e.base.type_name.startswith('identity ') else '.'
            return f'({base}){op}{field_name(e.name)}'
        raise TypeError(f'unsupported C lvalue {e!r}')
    def _expr(self,e):
        if isinstance(e,IRConst):
            if e.type_name=='Text': return c_string(str(e.value))
            if e.type_name=='Bool': return 'true' if e.value else 'false'
            if e.type_name=='Float':
                v=float(e.value)
                if v!=v: return 'NAN'
                return repr(v)
            return str(e.value)
        if isinstance(e,IRVar): return cname(e.name)
        if isinstance(e,IRMaybeNone): return f'({ctype(e.type_name)}){{.has=false}}'
        if isinstance(e,IRMaybeSome): return f'({ctype(e.type_name)}){{.has=true,.value={self._expr(e.value)}}}'
        if isinstance(e,IRMaybeGet): return f'{maybe_get(e.value.type_name)}({self._expr(e.value)})'
        if isinstance(e,IRIdentity): return f'{identity_helper(identity_inner(e.type_name))}({self._expr(e.value)})'
        if isinstance(e,IRConstruct):
            vals=', '.join(f'.{field_name(x.name)} = {self._expr(x.value)}' for x in e.fields)
            return f'({ctype(e.type_name)}){{{vals}}}'
        if isinstance(e,IRMember):
            op='->' if e.base.type_name.startswith('identity ') else '.'
            return f'({self._expr(e.base)}){op}{field_name(e.name)}'
        if isinstance(e,IRList):
            helper=list_helper(e.type_name); elem=list_element(e.type_name)
            if not e.elements: return f'{helper}_make(0, NULL)'
            values=', '.join(self._expr(x) for x in e.elements)
            return f'{helper}_make({len(e.elements)}, ({ctype(elem)}[]){{{values}}})'
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
            cop={'and':'&&','or':'||','==':'==','!=':'!=','<':'<','<=':'<=','>':'>','>=':'>='}.get(op,op)
            return f'({a} {cop} {b})'
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
        pref='    '*n
        return ''.join(pref+line if line.strip() else line for line in text.splitlines(True))

OPNAME={'+':'add','-':'sub','*':'mul','/':'div','%':'rem'}
def mangle(n):
    parts=[]
    for c in n:
        if c.isascii() and (c.isalnum() or c=='_'): parts.append(c)
        else: parts.append(f'_u{ord(c):04x}_')
    return ''.join(parts)
def cname(n): return 'v_'+mangle(n)
def field_name(n): return 'f_'+mangle(n)
def struct_tag(t): return 'eri_struct_tag_'+mangle(t)
def eq_helper(t): return 'eri_eq_'+mangle(t)
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
def list_helper_from_element(t):
    return {'Int':'eri_list_int','Float':'eri_list_float','Bool':'eri_list_bool','Text':'eri_list_text'}.get(t,'eri_list_'+mangle(t))
def ctype(t):
    scalars={'Int':'int64_t','Float':'double','Bool':'bool','Text':'const char *'}
    if t in scalars: return scalars[t]
    if t.startswith('maybe '): return maybe_name(t)
    if t.startswith('identity '): return ctype(identity_inner(t))+' *'
    if t.startswith('List of '): return list_helper(t)
    return 'eri_struct_'+mangle(t)
def c_string(s):
    return '"'+s.replace('\\','\\\\').replace('"','\\"').replace('\n','\\n').replace('\r','\\r').replace('\t','\\t').replace('\0','\\0')+'"'

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

static void eri_fault(const char *m) { fprintf(stderr, "Eristavi runtime fault: %s\n", m); exit(1); }
static void *eri_alloc(size_t n){ void *p=malloc(n?n:1); if(!p)eri_fault("out of memory"); return p; }
static void *eri_realloc(void *p,size_t n){ void *q=realloc(p,n?n:1); if(!q)eri_fault("out of memory"); return q; }
static char *eri_text_add(const char *a,const char *b){ size_t na=strlen(a),nb=strlen(b); char *r=(char*)eri_alloc(na+nb+1); memcpy(r,a,na); memcpy(r+na,b,nb+1); return r; }
static int64_t *eri_identity_Int_new(int64_t v){ int64_t *p=(int64_t*)eri_alloc(sizeof(int64_t)); *p=v; return p; }
static double *eri_identity_Float_new(double v){ double *p=(double*)eri_alloc(sizeof(double)); *p=v; return p; }
static bool *eri_identity_Bool_new(bool v){ bool *p=(bool*)eri_alloc(sizeof(bool)); *p=v; return p; }
static const char **eri_identity_Text_new(const char *v){ const char **p=(const char**)eri_alloc(sizeof(char*)); *p=v; return p; }
static int64_t eri_iadd(int64_t a,int64_t b){ if((b>0&&a>INT64_MAX-b)||(b<0&&a<INT64_MIN-b))eri_fault("Int overflow"); return a+b; }
static int64_t eri_isub(int64_t a,int64_t b){ if((b<0&&a>INT64_MAX+b)||(b>0&&a<INT64_MIN+b))eri_fault("Int overflow"); return a-b; }
static int64_t eri_imul(int64_t a,int64_t b){
    if(a==0||b==0)return 0;
    if((a==INT64_MIN&&b==-1)||(b==INT64_MIN&&a==-1))eri_fault("Int overflow");
    if(a>0){ if(b>0){if(a>INT64_MAX/b)eri_fault("Int overflow");} else {if(b<INT64_MIN/a)eri_fault("Int overflow");}}
    else { if(b>0){if(a<INT64_MIN/b)eri_fault("Int overflow");} else {if(a!=0&&b<INT64_MAX/a)eri_fault("Int overflow");}}
    return a*b;
}
static int64_t eri_idiv(int64_t a,int64_t b){ if(!b)eri_fault("Int division by zero"); if(a==INT64_MIN&&b==-1)eri_fault("Int overflow"); return a/b; }
static int64_t eri_irem(int64_t a,int64_t b){ if(!b)eri_fault("Int remainder by zero"); if(a==INT64_MIN&&b==-1)eri_fault("Int overflow"); return a%b; }
static int64_t eri_ineg(int64_t a){ if(a==INT64_MIN)eri_fault("Int overflow"); return -a; }
static double eri_fadd(double a,double b){ volatile double r=a+b; return r; }
static double eri_fsub(double a,double b){ volatile double r=a-b; return r; }
static double eri_fmul(double a,double b){ volatile double r=a*b; return r; }
static double eri_fdiv(double a,double b){ volatile double r; if(b==0.0){if(a==0.0||isnan(a))r=NAN;else r=copysign(INFINITY,a*b);}else r=a/b; return r; }
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
