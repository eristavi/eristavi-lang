from __future__ import annotations
from .ir import *

class CBackend:
    def __init__(self): self.indent=0
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
        if isinstance(s,IRExprStmt): return f'{self._expr(s.expression)};\n'
        if isinstance(s,IRReturn): return 'return;\n' if s.value is None else f'return {self._expr(s.value)};\n'
        if isinstance(s,IRIf):
            out=f'if ({self._expr(s.condition)}) {{\n'+self._indent_text(self._stmts(s.then_body),1)+'}'
            if s.else_body: out+=' else {\n'+self._indent_text(self._stmts(s.else_body),1)+'}'
            return out+'\n'
        if isinstance(s,IRWhile): return f'while ({self._expr(s.condition)}) {{\n'+self._indent_text(self._stmts(s.body),1)+'}\n'
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
        if isinstance(e,IRUnary):
            if e.operator=='not': return f'(!{self._expr(e.operand)})'
            if e.operator=='-' and e.type_name=='Int': return f'eri_ineg({self._expr(e.operand)})'
            if e.operator=='-' and e.type_name=='Float': return f'eri_fneg({self._expr(e.operand)})'
        if isinstance(e,IRBinary):
            a=self._expr(e.left); b=self._expr(e.right); op=e.operator
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
def ctype(t): return {'Int':'int64_t','Float':'double','Bool':'bool','Text':'const char *'}[t]
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

static void eri_fault(const char *m) { fprintf(stderr, "Eristavi runtime fault: %s\n", m); exit(1); }
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
'''
