from __future__ import annotations

from . import c_backend as base
from .c_backend_text import CBackend as TextBackend, TEXT_RUNTIME, _BASE_CTYPE, _replace_once
from .ir_text import IRProcessCall, IRFileAcquire, IRUnicodeCall, IRFileExists, IRFileRemove, IRTextView, IRTextViewCount, IRTextViewIndex
from .unicode_c import grapheme_runtime_c
from .unicode_library_c import unicode_library_c
from .process_c import PROCESS_RUNTIME
from dataclasses import dataclass, fields, is_dataclass, replace


def _view_ctype(t: str) -> str:
    if t == "Text":
        return "eri_text"
    if t in ("Text bytes view", "Text scalars view", "Text characters view"):
        return "eri_text_view"
    return _BASE_CTYPE(t)


_VIEW_PREFIX = r'''

#include <sys/stat.h>

typedef struct { eri_text text; int kind; } eri_text_view;
enum { ERI_TEXT_VIEW_BYTES=1, ERI_TEXT_VIEW_SCALARS=2, ERI_TEXT_VIEW_CHARACTERS=3 };

static eri_text_view eri_text_view_make(eri_text text,int kind){ return (eri_text_view){text,kind}; }

static size_t eri_utf8_width(unsigned char c){
    if(c<=0x7f)return 1;
    if(c>=0xc2&&c<=0xdf)return 2;
    if(c>=0xe0&&c<=0xef)return 3;
    if(c>=0xf0&&c<=0xf4)return 4;
    eri_fault("invalid UTF-8 inside Text");
    return 0;
}

static size_t eri_text_scalar_count(eri_text text){
    size_t count=0;
    for(size_t i=0;i<text.len;){ i+=eri_utf8_width(text.data[i]); count++; }
    return count;
}

static eri_text eri_text_scalar_get(eri_text text,int64_t index){
    if(index<0)eri_fault("Text view index out of bounds");
    int64_t current=0;
    for(size_t i=0;i<text.len;){
        size_t width=eri_utf8_width(text.data[i]);
        if(current==index)return eri_text_from_bytes(text.data+i,width);
        i+=width; current++;
    }
    eri_fault("Text view index out of bounds");
    return eri_text_from_bytes(NULL,0);
}

static int64_t eri_text_byte_get(eri_text text,int64_t index){
    if(index<0||(uint64_t)index>=text.len)eri_fault("Text view index out of bounds");
    return (int64_t)text.data[index];
}

static bool eri_file_exists_path(eri_text path){
    char *cp=eri_text_to_c_path(path);
    if(!cp)eri_raise_file_failure("file path contains NUL",path);
    struct stat st;
    if(stat(cp,&st)==0)return true;
    if(errno==ENOENT)return false;
    eri_raise_file_failure(strerror(errno),path);
    return false;
}

static void eri_file_remove_path(eri_text path){
    char *cp=eri_text_to_c_path(path);
    if(!cp)eri_raise_file_failure("file path contains NUL",path);
    if(remove(cp)!=0)eri_raise_file_failure(strerror(errno),path);
}
'''

_VIEW_SUFFIX = r'''
static int64_t eri_text_view_count(eri_text_view view){
    if(view.kind==ERI_TEXT_VIEW_BYTES)return (int64_t)view.text.len;
    if(view.kind==ERI_TEXT_VIEW_SCALARS)return (int64_t)eri_text_scalar_count(view.text);
    if(view.kind==ERI_TEXT_VIEW_CHARACTERS)return eri_text_character_count(view.text);
    eri_fault("internal Text view kind mismatch");
    return 0;
}

static int64_t eri_text_view_byte_get(eri_text_view view,int64_t index){
    if(view.kind!=ERI_TEXT_VIEW_BYTES)eri_fault("internal Text view kind mismatch");
    return eri_text_byte_get(view.text,index);
}

static eri_text eri_text_view_text_get(eri_text_view view,int64_t index){
    if(view.kind==ERI_TEXT_VIEW_SCALARS)return eri_text_scalar_get(view.text,index);
    if(view.kind==ERI_TEXT_VIEW_CHARACTERS)return eri_text_character_get(view.text,index);
    eri_fault("internal Text view kind mismatch");
    return eri_text_from_bytes(NULL,0);
}
'''

_HOSTED_FILES = r'''
#ifndef _WIN32
extern char *realpath(const char *restrict path,char *restrict resolved_path);
#endif
static eri_text eri_file_canonical_path(eri_text path){
    char *cp=eri_text_to_c_path(path);
    if(!cp)eri_raise_file_failure("file path contains NUL",path);
#ifdef _WIN32
    struct stat information;
    if(stat(cp,&information)!=0)eri_raise_file_failure(strerror(errno),path);
    char *resolved=_fullpath(NULL,cp,0);
#else
    char *resolved=realpath(cp,NULL);
#endif
    if(!resolved)eri_raise_file_failure(strerror(errno),path);
    eri_text result=eri_text_from_cstr(resolved);free(resolved);return result;
}
static eri_file eri_file_acquire(eri_text path,bool create){
    char *cp=eri_text_to_c_path(path);
    if(!cp)eri_raise_file_failure("file path contains NUL",path);
    FILE *handle=fopen(cp,create ? "wx+" : "r");
    if(!handle)eri_raise_file_failure(strerror(errno),path);
    return (eri_file){path,cp,handle,false,create};
}
'''

# The existing File surface retains read/write behavior. Additional acquisition
# modes share its cleanup/error contract, including an enforced read-only flag.
_HOSTED_TEXT_RUNTIME = _replace_once(
    TEXT_RUNTIME,
    "FILE *handle; bool closed; } eri_file;",
    "FILE *handle; bool closed; bool writable; } eri_file;",
)
_HOSTED_TEXT_RUNTIME = _replace_once(
    _HOSTED_TEXT_RUNTIME, "(eri_file){path,cp,h,false}", "(eri_file){path,cp,h,false,true}",
)
_HOSTED_TEXT_RUNTIME = _replace_once(
    _HOSTED_TEXT_RUNTIME,
    "static void eri_file_write_text(eri_file *f,eri_text text){",
    'static void eri_file_write_text(eri_file *f,eri_text text){ if(f&&!f->writable)eri_raise_file_failure("file was opened read-only",f->path);',
)
VIEW_RUNTIME = _HOSTED_TEXT_RUNTIME + _VIEW_PREFIX + grapheme_runtime_c() + _VIEW_SUFFIX + _HOSTED_FILES + PROCESS_RUNTIME


@dataclass(frozen=True)
class _CValue(base.IRExpr):
    code: str


class CBackend(TextBackend):
    """Length-aware C backend with Unicode Text views and stdlib path operations."""

    def emit(self, program):
        self._ordered_declarations = []
        old_runtime, old_ctype = base.RUNTIME, base.ctype
        def uses_unicode(value):
            if isinstance(value, IRUnicodeCall):
                return True
            if isinstance(value, (list, tuple)):
                return any(uses_unicode(item) for item in value)
            if is_dataclass(value):
                return any(uses_unicode(getattr(value, field.name)) for field in fields(value))
            return False
        runtime = VIEW_RUNTIME + (unicode_library_c() if uses_unicode(program) else "")
        base.RUNTIME, base.ctype = runtime, _view_ctype
        try:
            # Bypass TextBackend.emit because it would replace the runtime/ctype
            # with its narrower Text-only pair. base.CBackend.emit still
            # dispatches expression/equality methods on this subclass.
            return base.CBackend.emit(self, program)
        finally:
            base.RUNTIME, base.ctype = old_runtime, old_ctype

    def _function(self, routine):
        self._ordered_declarations = []
        result = super()._function(routine)
        declarations = self._ordered_declarations
        self._ordered_declarations = []
        if declarations:
            before, separator, after = result.partition("{\n")
            result = before + separator + self._indent_text("".join(declarations), 1) + after
        return result

    def _ordered(self, children, rebuild):
        assignments = []
        values = []
        for child in children:
            code = self._expr(child)
            self.temp += 1
            name = f"_eri_order_{self.temp}"
            self._ordered_declarations.append(f"{base.ctype(child.type_name)} {name};\n")
            assignments.append(f"{name} = ({code})")
            values.append(_CValue(child.type_name, child.location, name))
        result = super()._expr(rebuild(values))
        return "(" + ", ".join([*assignments, result]) + ")"

    def _entry_function(self, body):
        # Hosted argc/argv do not change Eristavi's implicit source entry body.
        return ("int main(int argc,char **argv) {\n"
                "    eri_process_argc=argc; eri_process_argv=argv;\n"
                "    fesetround(FE_TONEAREST);\n" + self._indent_text("".join(self._ordered_declarations) + body, 1)
                + "    return eri_process_exit_code;\n}\n")

    def _expr(self, e):
        if isinstance(e, _CValue):
            return e.code
        # Standard C comma expressions sequence operand evaluations without
        # GNU statement expressions. Only declarations are hoisted; evaluation
        # stays inside its original loop/short-circuit/failure-handler boundary.
        if isinstance(e, base.IRBinary) and e.operator not in ("and", "or"):
            return self._ordered([e.left, e.right],
                                 lambda values: replace(e, left=values[0], right=values[1]))
        if isinstance(e, base.IRCall) and len(e.arguments) > 1:
            return self._ordered(e.arguments, lambda values: replace(e, arguments=values))
        if isinstance(e, IRProcessCall):
            arguments = ", ".join(self._expr(arg) for arg in e.arguments)
            return f"eri_process_{e.name}({arguments})"
        if isinstance(e, IRFileAcquire):
            if e.name == "canonicalPath":
                return f"eri_file_canonical_path({self._expr(e.path)})"
            create = "true" if e.name == "create" else "false"
            return f"eri_file_acquire({self._expr(e.path)}, {create})"
        if isinstance(e, IRUnicodeCall):
            return f"eri_unicode_{e.name}({self._expr(e.argument)})"
        if isinstance(e, IRTextView):
            kinds = {
                "bytes": "ERI_TEXT_VIEW_BYTES",
                "scalars": "ERI_TEXT_VIEW_SCALARS",
                "characters": "ERI_TEXT_VIEW_CHARACTERS",
            }
            return f"eri_text_view_make({self._expr(e.base)}, {kinds[e.kind]})"
        if isinstance(e, IRTextViewCount):
            return f"eri_text_view_count({self._expr(e.view)})"
        if isinstance(e, IRTextViewIndex):
            if e.type_name == "Int":
                return f"eri_text_view_byte_get({self._expr(e.view)}, {self._expr(e.index)})"
            return f"eri_text_view_text_get({self._expr(e.view)}, {self._expr(e.index)})"
        if isinstance(e, IRFileExists):
            return f"eri_file_exists_path({self._expr(e.path)})"
        if isinstance(e, IRFileRemove):
            return f"eri_file_remove_path({self._expr(e.path)})"
        return super()._expr(e)
