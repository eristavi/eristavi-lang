from __future__ import annotations

from . import c_backend as base
from .c_backend_text import CBackend as TextBackend, TEXT_RUNTIME, _BASE_CTYPE
from .ir_text import IRTextView, IRTextViewCount, IRTextViewIndex


def _view_ctype(t: str) -> str:
    if t == "Text":
        return "eri_text"
    if t in ("Text bytes view", "Text scalars view", "Text characters view"):
        return "eri_text_view"
    return _BASE_CTYPE(t)


VIEW_RUNTIME = TEXT_RUNTIME + r'''

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

static int64_t eri_text_view_count(eri_text_view view){
    if(view.kind==ERI_TEXT_VIEW_BYTES)return (int64_t)view.text.len;
    if(view.kind==ERI_TEXT_VIEW_SCALARS)return (int64_t)eri_text_scalar_count(view.text);
    eri_fault("compiled text.characters requires the pinned Unicode grapheme runtime");
    return 0;
}

static int64_t eri_text_view_byte_get(eri_text_view view,int64_t index){
    if(view.kind!=ERI_TEXT_VIEW_BYTES)eri_fault("internal Text view kind mismatch");
    return eri_text_byte_get(view.text,index);
}

static eri_text eri_text_view_scalar_get(eri_text_view view,int64_t index){
    if(view.kind!=ERI_TEXT_VIEW_SCALARS)eri_fault("internal Text view kind mismatch");
    return eri_text_scalar_get(view.text,index);
}
'''


class CBackend(TextBackend):
    """Length-aware C backend plus compiled UTF-8 byte/scalar Text views."""

    def emit(self, program):
        old_runtime, old_ctype = base.RUNTIME, base.ctype
        base.RUNTIME, base.ctype = VIEW_RUNTIME, _view_ctype
        try:
            # Bypass TextBackend.emit because it would replace the runtime/ctype
            # with its narrower Text-only pair.  base.CBackend.emit still
            # dispatches expression/equality methods on this subclass.
            return base.CBackend.emit(self, program)
        finally:
            base.RUNTIME, base.ctype = old_runtime, old_ctype

    def _expr(self, e):
        if isinstance(e, IRTextView):
            if e.kind == "characters":
                raise ValueError(
                    "compiled text.characters is not available until the pinned Unicode 17 grapheme runtime is embedded"
                )
            kind = "ERI_TEXT_VIEW_BYTES" if e.kind == "bytes" else "ERI_TEXT_VIEW_SCALARS"
            return f"eri_text_view_make({self._expr(e.base)}, {kind})"
        if isinstance(e, IRTextViewCount):
            return f"eri_text_view_count({self._expr(e.view)})"
        if isinstance(e, IRTextViewIndex):
            if e.type_name == "Int":
                return f"eri_text_view_byte_get({self._expr(e.view)}, {self._expr(e.index)})"
            return f"eri_text_view_scalar_get({self._expr(e.view)}, {self._expr(e.index)})"
        return super()._expr(e)
