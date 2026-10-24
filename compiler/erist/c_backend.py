from __future__ import annotations
from .ir import *

class CBackend:
    def __init__(self): self.indent=0; self.temp=0
    def emit(self,p:IRProgram)->str:
        parts=[RUNTIME]
        for f in p.functions: parts.append(self._function(f))
        body=self._stmts(p.entry)
        parts.append('int main(void) {\n    fesetround(FE_TONEAREST);\n'+self._indent_text(body,1)+'    return 0;\n}\n')
        return '\n'.join(parts)
    def _function(self,f):
        ret='void' if f.return_type is None else ctype(f.return_type)
        params=', '.join(f'{ctype(x.type_name)} {cname(x.name)}' for x in f.parameters) or 'void'
        return f'static {ret} fn_{mangle(f.name)}({params}) {{\n'+self._indent_text(self._stmts(f.body),1)+'}\n'
    def _stmts(self,stmts): return ''.join(self._stmt(s) for s in stmts)
    def _stmt(self,s):
        if isinstance(s,IRLet): return f'{ctype(s.type_name)} {cname(s.name)} = {self._expr(s.value)};\n'
        if isinstance(s,IRAssign): return f'{cname(s.name)} = {self._expr(s.value)};\n'
        if isinstance(s,IRIndexAssign):
            lt=list_element_name_from_value(s.value, None)
            # The target List type is not stored on the statement; the value type is its element type.
            helper=list_helper_from_element(s.value.type_name)
            return f'{helper}_set(&{cname(s.name)}, {self._expr(s.index)}, {self._expr(s.value)});\n'
        if isinstance(s,IRExprStmt): return f'{self._expr(s.expression)};\n'
        if isinstance(s,IRReturn): return 'return;\n' if s.value is None else f'return {self._expr(s.value)};\n'
        if isinstance(s,IRIf):
            out=f'if ({self._expr(s.condition)}) {{\n'+self._indent_text(self._stmts(s.then_body),1)+'}'
            if s.else_body: out+=' else {\n'+self._indent_text(self._stmts(s.else_body),1)+'}'
            return out+'\n'
        if isinstance(s,IRWhile): return f'while ({self._expr(s.condition)}) {{\n'+self._indent_text(self._stmts(s.body),1)+'}\n'
        if isinstance(s,IRFor):
            self.temp+=1; n=self.temp
            snap=f'_eri_iter_{n}'; idx=f'_eri_i_{n}'
            helper=list_helper(s.iterable.type_name); elem=list_element(s.iterable.type_name)
            head=f'{ctype(s.iterable.type_name)} {snap} = {self._expr(s.iterable)};\nfor (int64_t {idx}=0; {idx}<(int64_t){snap}.count; ++{idx}) {{\n'
            binding=f'{ctype(elem)} {cname(s.name)} = {helper}_get({snap}, {idx});\n'
            return head+self._indent_text(binding+self._stmts(s.body),1)+'}\n'
        raise TypeError(s)
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
            if e.left.type_name.startswith('List of ') and op in ('==','!='):
                cmp=f'{list_helper(e.left.type_name)}_eq({a}, {b})'
                return cmp if op=='==' else f'(!{cmp})'
            if e.left.type_name=='Int' and op in '+-*/%': return f'eri_i{OPNAME[op]}({a}, {b})'
            if e.left.type_name=='Float' and op in '+-*/': return f'eri_f{OPNAME[op]}({a}, {b})'
            if e.left.type_name=='Text' and op in ('==','!='):
                cmp=f'(strcmp({a}, {b}) == 0)'
                return cmp if op=='==' else f'(!{cmp})'
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
def list_element(t):
    if not t.startswith('List of '): raise KeyError(t)
    return t[8:]
def list_helper(t): return list_helper_from_element(list_element(t))
def list_helper_from_element(t): return {'Int':'eri_list_int','Float':'eri_list_float','Bool':'eri_list_bool','Text':'eri_list_text'}[t]
def list_element_name_from_value(value, default): return value.type_name if value.type_name in ('Int','Float','Bool','Text') else default
def ctype(t):
    scalars={'Int':'int64_t','Float':'double','Bool':'bool','Text':'const char *'}
    if t in scalars: return scalars[t]
    if t.startswith('List of '): return list_helper(t)
    raise KeyError(t)
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
