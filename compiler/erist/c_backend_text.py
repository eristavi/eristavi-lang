from __future__ import annotations

from . import c_backend as base
from .ir import IRBinary, IRCall, IRConst


_BASE_CTYPE = base.ctype


def _text_ctype(t: str) -> str:
    if t == "Text":
        return "eri_text"
    return _BASE_CTYPE(t)


def _replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError("C bootstrap runtime layout changed; Text runtime patch must be reviewed")
    return text.replace(old, new, 1)


def _text_runtime() -> str:
    r = base.RUNTIME

    r = _replace_once(
        r,
        "typedef struct eri_handler_frame { jmp_buf env; struct eri_handler_frame *prev; } eri_handler_frame;\n"
        "typedef struct eri_secondary_failure { const char *type; void *payload; const char *message; struct eri_secondary_failure *next; } eri_secondary_failure;\n"
        "typedef struct { const char *type; void *payload; const char *message; eri_secondary_failure *secondary; } eri_failure_value;\n"
        "typedef struct { const char *f_message; } eri_error_view;",
        "typedef struct { size_t len; unsigned char *data; } eri_text;\n"
        "typedef struct eri_handler_frame { jmp_buf env; struct eri_handler_frame *prev; } eri_handler_frame;\n"
        "typedef struct eri_secondary_failure { const char *type; void *payload; eri_text message; struct eri_secondary_failure *next; } eri_secondary_failure;\n"
        "typedef struct { const char *type; void *payload; eri_text message; eri_secondary_failure *secondary; } eri_failure_value;\n"
        "typedef struct { eri_text f_message; } eri_error_view;",
    )

    r = _replace_once(
        r,
        "static eri_failure_value eri_failure = {NULL,NULL,NULL,NULL};",
        "static eri_failure_value eri_failure = {NULL,NULL,{0,NULL},NULL};",
    )

    r = _replace_once(
        r,
        "static char *eri_text_dup(const char *s){ size_t n=strlen(s); char *r=(char*)eri_alloc(n+1); memcpy(r,s,n+1); return r; }\n"
        "static void eri_attach_secondary(eri_failure_value *primary, eri_failure_value secondary){ eri_secondary_failure *n=(eri_secondary_failure*)eri_alloc(sizeof(*n)); n->type=secondary.type; n->payload=secondary.payload; n->message=secondary.message; n->next=NULL; eri_secondary_failure **p=&primary->secondary; while(*p)p=&(*p)->next; *p=n; }\n"
        "static _Noreturn void eri_raise(const char *type, void *payload, const char *message){ eri_failure=(eri_failure_value){type,payload,message,NULL}; if(!eri_handler_top)eri_fault(message?message:\"unhandled checked failure\"); longjmp(eri_handler_top->env,1); }\n"
        "static _Noreturn void eri_propagate_saved(eri_failure_value f){ eri_failure=f; if(!eri_handler_top)eri_fault(f.message?f.message:\"unhandled checked failure\"); longjmp(eri_handler_top->env,1); }\n"
        "static char *eri_text_add(const char *a,const char *b){ size_t na=strlen(a),nb=strlen(b); char *r=(char*)eri_alloc(na+nb+1); memcpy(r,a,na); memcpy(r+na,b,nb+1); return r; }",
        "static eri_text eri_text_from_bytes(const unsigned char *s,size_t n){ eri_text r={n,NULL}; if(n){r.data=(unsigned char*)eri_alloc(n); memcpy(r.data,s,n);} return r; }\n"
        "static eri_text eri_text_from_cstr(const char *s){ return eri_text_from_bytes((const unsigned char*)s,strlen(s)); }\n"
        "static bool eri_text_eq(eri_text a,eri_text b){ return a.len==b.len && (!a.len || memcmp(a.data,b.data,a.len)==0); }\n"
        "static eri_text eri_text_add(eri_text a,eri_text b){ eri_text r={a.len+b.len,NULL}; if(r.len){r.data=(unsigned char*)eri_alloc(r.len); if(a.len)memcpy(r.data,a.data,a.len); if(b.len)memcpy(r.data+a.len,b.data,b.len);} return r; }\n"
        "static char *eri_text_to_c_path(eri_text t){ if(t.len && memchr(t.data,0,t.len))return NULL; char *r=(char*)eri_alloc(t.len+1); if(t.len)memcpy(r,t.data,t.len); r[t.len]='\\0'; return r; }\n"
        "static _Noreturn void eri_fault_text(eri_text t){ fputs(\"Eristavi runtime fault: \",stderr); if(t.len)fwrite(t.data,1,t.len,stderr); fputc('\\n',stderr); exit(1); }\n"
        "static void eri_attach_secondary(eri_failure_value *primary, eri_failure_value secondary){ eri_secondary_failure *n=(eri_secondary_failure*)eri_alloc(sizeof(*n)); n->type=secondary.type; n->payload=secondary.payload; n->message=secondary.message; n->next=NULL; eri_secondary_failure **p=&primary->secondary; while(*p)p=&(*p)->next; *p=n; }\n"
        "static _Noreturn void eri_raise(const char *type, void *payload, eri_text message){ eri_failure=(eri_failure_value){type,payload,message,NULL}; if(!eri_handler_top)eri_fault_text(message); longjmp(eri_handler_top->env,1); }\n"
        "static _Noreturn void eri_propagate_saved(eri_failure_value f){ eri_failure=f; if(!eri_handler_top)eri_fault_text(f.message); longjmp(eri_handler_top->env,1); }",
    )

    r = _replace_once(
        r,
        "typedef struct { const char *f_message; const char *f_path; } eri_file_error;\n"
        "typedef struct { const char *path; FILE *handle; bool closed; } eri_file;\n"
        "static eri_failure_value eri_make_file_failure(const char *message,const char *path){ eri_file_error *e=(eri_file_error*)eri_alloc(sizeof(*e)); e->f_message=eri_text_dup(message?message:\"file error\"); e->f_path=eri_text_dup(path?path:\"\"); return (eri_failure_value){\"std.files.FileError\",e,e->f_message,NULL}; }\n"
        "static _Noreturn void eri_raise_file_failure(const char *message,const char *path){ eri_failure_value f=eri_make_file_failure(message,path); eri_raise(f.type,f.payload,f.message); }\n"
        "static _Noreturn void eri_fail_std_u002e_files_u002e_FileError(eri_file_error v){ eri_file_error *p=(eri_file_error*)eri_alloc(sizeof(*p)); *p=v; eri_raise(\"std.files.FileError\",p,v.f_message); }\n"
        "static eri_file eri_file_open(const char *path){ FILE *h=fopen(path,\"r+\"); if(!h)eri_raise_file_failure(strerror(errno),path); return (eri_file){path,h,false}; }\n"
        "static const char *eri_file_read_text(eri_file *f){ if(!f||f->closed||!f->handle)eri_fault(\"file resource is closed\"); if(fseek(f->handle,0,SEEK_END)!=0)eri_raise_file_failure(strerror(errno),f->path); long n=ftell(f->handle); if(n<0)eri_raise_file_failure(strerror(errno),f->path); rewind(f->handle); char *buf=(char*)eri_alloc((size_t)n+1); size_t got=fread(buf,1,(size_t)n,f->handle); if(got<(size_t)n&&ferror(f->handle))eri_raise_file_failure(strerror(errno),f->path); buf[got]='\\0'; return buf; }\n"
        "static void eri_file_write_text(eri_file *f,const char *text){ if(!f||f->closed||!f->handle)eri_fault(\"file resource is closed\"); FILE *h=freopen(f->path,\"w+\",f->handle); if(!h){f->handle=NULL; f->closed=true; eri_raise_file_failure(strerror(errno),f->path);} f->handle=h; size_t n=strlen(text); if(fwrite(text,1,n,h)!=n)eri_raise_file_failure(strerror(errno),f->path); if(fflush(h)!=0)eri_raise_file_failure(strerror(errno),f->path); rewind(h); }\n"
        "static bool eri_file_cleanup(eri_file *f,eri_failure_value *failure){ if(!f||f->closed)return false; FILE *h=f->handle; f->handle=NULL; f->closed=true; if(h&&fclose(h)!=0){ if(failure)*failure=eri_make_file_failure(strerror(errno),f->path); return true; } return false; }",
        "typedef struct { eri_text f_message; eri_text f_path; } eri_file_error;\n"
        "typedef struct { eri_text path; char *c_path; FILE *handle; bool closed; } eri_file;\n"
        "static bool eri_utf8_valid(const unsigned char *s,size_t n){ size_t i=0; while(i<n){ unsigned c=s[i++]; if(c<=0x7f)continue; if(c>=0xc2&&c<=0xdf){ if(i>=n||(s[i]&0xc0)!=0x80)return false; i++; continue; } if(c>=0xe0&&c<=0xef){ if(i+1>=n)return false; unsigned c1=s[i],c2=s[i+1]; if((c1&0xc0)!=0x80||(c2&0xc0)!=0x80)return false; if(c==0xe0&&c1<0xa0)return false; if(c==0xed&&c1>=0xa0)return false; i+=2; continue; } if(c>=0xf0&&c<=0xf4){ if(i+2>=n)return false; unsigned c1=s[i],c2=s[i+1],c3=s[i+2]; if((c1&0xc0)!=0x80||(c2&0xc0)!=0x80||(c3&0xc0)!=0x80)return false; if(c==0xf0&&c1<0x90)return false; if(c==0xf4&&c1>=0x90)return false; i+=3; continue; } return false; } return true; }\n"
        "static eri_failure_value eri_make_file_failure(const char *message,eri_text path){ eri_file_error *e=(eri_file_error*)eri_alloc(sizeof(*e)); e->f_message=eri_text_from_cstr(message?message:\"file error\"); e->f_path=path; return (eri_failure_value){\"std.files.FileError\",e,e->f_message,NULL}; }\n"
        "static _Noreturn void eri_raise_file_failure(const char *message,eri_text path){ eri_failure_value f=eri_make_file_failure(message,path); eri_raise(f.type,f.payload,f.message); }\n"
        "static _Noreturn void eri_fail_std_u002e_files_u002e_FileError(eri_file_error v){ eri_file_error *p=(eri_file_error*)eri_alloc(sizeof(*p)); *p=v; eri_raise(\"std.files.FileError\",p,v.f_message); }\n"
        "static eri_file eri_file_open(eri_text path){ char *cp=eri_text_to_c_path(path); if(!cp)eri_raise_file_failure(\"file path contains NUL\",path); FILE *h=fopen(cp,\"r+\"); if(!h)eri_raise_file_failure(strerror(errno),path); return (eri_file){path,cp,h,false}; }\n"
        "static eri_text eri_file_read_text(eri_file *f){ if(!f||f->closed||!f->handle)eri_fault(\"file resource is closed\"); if(fseek(f->handle,0,SEEK_END)!=0)eri_raise_file_failure(strerror(errno),f->path); long n=ftell(f->handle); if(n<0)eri_raise_file_failure(strerror(errno),f->path); rewind(f->handle); unsigned char *buf=(unsigned char*)eri_alloc((size_t)n?((size_t)n):1); size_t got=fread(buf,1,(size_t)n,f->handle); if(got<(size_t)n&&ferror(f->handle))eri_raise_file_failure(strerror(errno),f->path); if(!eri_utf8_valid(buf,got))eri_raise_file_failure(\"invalid UTF-8\",f->path); return eri_text_from_bytes(buf,got); }\n"
        "static void eri_file_write_text(eri_file *f,eri_text text){ if(!f||f->closed||!f->handle)eri_fault(\"file resource is closed\"); FILE *h=freopen(f->c_path,\"w+\",f->handle); if(!h){f->handle=NULL; f->closed=true; eri_raise_file_failure(strerror(errno),f->path);} f->handle=h; if(text.len&&fwrite(text.data,1,text.len,h)!=text.len)eri_raise_file_failure(strerror(errno),f->path); if(fflush(h)!=0)eri_raise_file_failure(strerror(errno),f->path); rewind(h); }\n"
        "static bool eri_file_cleanup(eri_file *f,eri_failure_value *failure){ if(!f||f->closed)return false; FILE *h=f->handle; f->handle=NULL; f->closed=true; if(h&&fclose(h)!=0){ if(failure)*failure=eri_make_file_failure(strerror(errno),f->path); return true; } return false; }",
    )

    r = _replace_once(
        r,
        "static const char **eri_identity_Text_new(const char *v){ const char **p=(const char**)eri_alloc(sizeof(char*)); *p=v; return p; }",
        "static eri_text *eri_identity_Text_new(eri_text v){ eri_text *p=(eri_text*)eri_alloc(sizeof(eri_text)); *p=v; return p; }",
    )

    r = _replace_once(
        r,
        "static void eri_out_text(const char *v){ puts(v); }",
        "static void eri_out_text(eri_text v){ if(v.len)fwrite(v.data,1,v.len,stdout); fputc('\\n',stdout); }",
    )

    r = _replace_once(
        r,
        "typedef struct { size_t count; const char **data; } eri_list_text;\n"
        "static eri_list_text eri_list_text_make(size_t n,const char **src){ eri_list_text r={n,NULL}; if(n){r.data=(const char**)eri_alloc(sizeof(char*)*n); memcpy(r.data,src,sizeof(char*)*n);} return r; }\n"
        "static void eri_list_text_detach(eri_list_text *v){ if(!v->count){v->data=NULL;return;} const char **p=(const char**)eri_alloc(sizeof(char*)*v->count); memcpy(p,v->data,sizeof(char*)*v->count); v->data=p; }\n"
        "static const char *eri_list_text_get(eri_list_text v,int64_t i){ if(i<0||(uint64_t)i>=v.count)eri_fault(\"List index out of bounds\"); return v.data[i]; }\n"
        "static void eri_list_text_set(eri_list_text *v,int64_t i,const char *x){ if(i<0||(uint64_t)i>=v->count)eri_fault(\"List index out of bounds\"); eri_list_text_detach(v); v->data[i]=x; }\n"
        "static void eri_list_text_add(eri_list_text *v,const char *x){ eri_list_text_detach(v); v->data=(const char**)eri_realloc(v->data,sizeof(char*)*(v->count+1)); v->data[v->count++]=x; }\n"
        "static bool eri_list_text_eq(eri_list_text a,eri_list_text b){ if(a.count!=b.count)return false; for(size_t i=0;i<a.count;i++){if(strcmp(a.data[i],b.data[i])!=0)return false;} return true; }",
        "typedef struct { size_t count; eri_text *data; } eri_list_text;\n"
        "static eri_list_text eri_list_text_make(size_t n,const eri_text *src){ eri_list_text r={n,NULL}; if(n){r.data=(eri_text*)eri_alloc(sizeof(eri_text)*n); memcpy(r.data,src,sizeof(eri_text)*n);} return r; }\n"
        "static void eri_list_text_detach(eri_list_text *v){ if(!v->count){v->data=NULL;return;} eri_text *p=(eri_text*)eri_alloc(sizeof(eri_text)*v->count); memcpy(p,v->data,sizeof(eri_text)*v->count); v->data=p; }\n"
        "static eri_text eri_list_text_get(eri_list_text v,int64_t i){ if(i<0||(uint64_t)i>=v.count)eri_fault(\"List index out of bounds\"); return v.data[i]; }\n"
        "static void eri_list_text_set(eri_list_text *v,int64_t i,eri_text x){ if(i<0||(uint64_t)i>=v->count)eri_fault(\"List index out of bounds\"); eri_list_text_detach(v); v->data[i]=x; }\n"
        "static void eri_list_text_add(eri_list_text *v,eri_text x){ eri_list_text_detach(v); v->data=(eri_text*)eri_realloc(v->data,sizeof(eri_text)*(v->count+1)); v->data[v->count++]=x; }\n"
        "static bool eri_list_text_eq(eri_list_text a,eri_list_text b){ if(a.count!=b.count)return false; for(size_t i=0;i<a.count;i++){if(!eri_text_eq(a.data[i],b.data[i]))return false;} return true; }",
    )

    return r


from .text_builder_c import TEXT_APPEND_RUNTIME

TEXT_RUNTIME = _replace_once(
    _text_runtime(),
    "static eri_text eri_text_add(eri_text a,eri_text b){ eri_text r={a.len+b.len,NULL}; if(r.len){r.data=(unsigned char*)eri_alloc(r.len); if(a.len)memcpy(r.data,a.data,a.len); if(b.len)memcpy(r.data+a.len,b.data,b.len);} return r; }",
    TEXT_APPEND_RUNTIME,
)
TEXT_RUNTIME = TEXT_RUNTIME.replace(
    "eri_list_##NAME##_detach(v); v->data=(TYPE*)eri_realloc(v->data,sizeof(TYPE)*(v->count+1)); v->data[v->count++]=x;",
    "if(v->count>=SIZE_MAX/sizeof(TYPE))eri_fault(\"List size overflow\"); v->data=(TYPE*)eri_prefix_append((const unsigned char*)v->data,v->count*sizeof(TYPE),(const unsigned char*)&x,sizeof(TYPE)); v->count++;",
).replace(
    "eri_list_text_detach(v); v->data=(eri_text*)eri_realloc(v->data,sizeof(eri_text)*(v->count+1)); v->data[v->count++]=x;",
    "if(v->count>=SIZE_MAX/sizeof(eri_text))eri_fault(\"List size overflow\"); v->data=(eri_text*)eri_prefix_append((const unsigned char*)v->data,v->count*sizeof(eri_text),(const unsigned char*)&x,sizeof(eri_text)); v->count++;",
)


def _text_literal(value: str) -> str:
    data = value.encode("utf-8")
    if not data:
        return "eri_text_from_bytes(NULL, 0)"
    bytes_c = ", ".join(f"0x{b:02x}" for b in data)
    return f"eri_text_from_bytes((const unsigned char[]){{{bytes_c}}}, {len(data)})"


class CBackend(base.CBackend):
    """C11 backend with length-aware UTF-8 Text values.

    This removes C-string semantics from Eristavi Text: embedded NUL bytes are
    preserved, equality is length-aware, file I/O validates UTF-8, and output
    writes the complete Text value.
    """

    def emit(self, program):
        old_runtime, old_ctype = base.RUNTIME, base.ctype
        base.RUNTIME, base.ctype = TEXT_RUNTIME, _text_ctype
        try:
            return super().emit(program)
        finally:
            base.RUNTIME, base.ctype = old_runtime, old_ctype

    def _eq_component(self, t, a, b):
        if t == "Text":
            return f"eri_text_eq({a}, {b})"
        return super()._eq_component(t, a, b)

    def _expr(self, e):
        if isinstance(e, IRConst) and e.type_name == "Text":
            return _text_literal(str(e.value))

        if isinstance(e, IRBinary) and e.left.type_name == "Text":
            a = self._expr(e.left)
            b = self._expr(e.right)
            if e.operator == "+":
                return f"eri_text_add({a}, {b})"
            if e.operator in ("==", "!="):
                cmp = f"eri_text_eq({a}, {b})"
                return cmp if e.operator == "==" else f"(!{cmp})"

        if isinstance(e, IRCall) and e.name == "output" and e.arguments and e.arguments[0].type_name == "Text":
            return f"eri_out_text({self._expr(e.arguments[0])})"

        return super()._expr(e)
