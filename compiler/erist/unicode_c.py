from __future__ import annotations

from functools import lru_cache

import regex

from .unicode_support import UNICODE_VERSION

# pyproject.toml pins this exact release. Keeping the generator version explicit
# makes compiled grapheme semantics reproducible rather than host-dependent.
PINNED_REGEX_VERSION = "2026.9.29"

if regex.__version__ != PINNED_REGEX_VERSION:
    raise RuntimeError(
        f"Eristavi compiled Unicode tables require regex {PINNED_REGEX_VERSION}, "
        f"but {regex.__version__} is installed"
    )


@lru_cache(maxsize=1)
def _scalar_text() -> str:
    # Surrogate code points are not Unicode scalar values and can never occur in
    # valid Eristavi Text.  Removing them also keeps property extraction simple.
    return "".join(chr(cp) for cp in range(0x110000) if not 0xD800 <= cp <= 0xDFFF)


def _index_to_scalar(index: int) -> int:
    return index if index < 0xD800 else index + 0x800


@lru_cache(maxsize=None)
def _property_ranges(expression: str) -> tuple[tuple[int, int], ...]:
    text = _scalar_text()
    pattern = regex.compile(rf"(?:\p{{{expression}}})+", regex.VERSION1)
    out: list[tuple[int, int]] = []
    for match in pattern.finditer(text):
        start = match.start()
        end = match.end()
        # Adjacent scalar-string positions on either side of the surrogate hole
        # are not adjacent code points. Split a regex run if it crosses it.
        if start < 0xD800 < end:
            out.append((_index_to_scalar(start), 0xD7FF))
            out.append((0xE000, _index_to_scalar(end - 1)))
        else:
            out.append((_index_to_scalar(start), _index_to_scalar(end - 1)))
    return tuple(out)


def _emit_table(name: str, entries: list[tuple[int, int, int]]) -> str:
    rows = ",\n".join(f"    {{0x{first:X}u,0x{last:X}u,{value}}}" for first, last, value in entries)
    return (
        f"static const eri_unicode_range {name}[] = {{\n{rows}\n}};\n"
        f"static const size_t {name}_count = sizeof({name})/sizeof({name}[0]);\n"
    )


@lru_cache(maxsize=1)
def grapheme_runtime_c() -> str:
    """Return C11 tables/runtime implementing Unicode 17 UAX #29 EGC rules.

    Property ranges are derived from the same pinned regex release used by the
    bootstrap runtime. The generated program therefore carries its own tables;
    it does not consult libc locales or platform Unicode APIs at execution time.
    """

    gcb_properties = [
        ("gcb=CR", 1),
        ("gcb=LF", 2),
        ("gcb=Control", 3),
        ("gcb=Extend", 4),
        ("gcb=ZWJ", 5),
        ("gcb=Regional_Indicator", 6),
        ("gcb=Prepend", 7),
        ("gcb=SpacingMark", 8),
        ("gcb=L", 9),
        ("gcb=V", 10),
        ("gcb=T", 11),
        ("gcb=LV", 12),
        ("gcb=LVT", 13),
    ]
    gcb: list[tuple[int, int, int]] = []
    for expression, value in gcb_properties:
        gcb.extend((first, last, value) for first, last in _property_ranges(expression))
    gcb.sort()

    incb: list[tuple[int, int, int]] = []
    for expression, value in (("InCB=Consonant", 1), ("InCB=Extend", 2), ("InCB=Linker", 3)):
        incb.extend((first, last, value) for first, last in _property_ranges(expression))
    incb.sort()

    ep = [(first, last, 1) for first, last in _property_ranges("Extended_Pictographic")]

    tables = _emit_table("eri_gcb_table", gcb) + _emit_table("eri_incb_table", incb) + _emit_table("eri_ep_table", ep)

    runtime = r'''
typedef struct { uint32_t first; uint32_t last; uint8_t value; } eri_unicode_range;

enum {
    ERI_GCB_OTHER=0, ERI_GCB_CR=1, ERI_GCB_LF=2, ERI_GCB_CONTROL=3,
    ERI_GCB_EXTEND=4, ERI_GCB_ZWJ=5, ERI_GCB_RI=6, ERI_GCB_PREPEND=7,
    ERI_GCB_SPACINGMARK=8, ERI_GCB_L=9, ERI_GCB_V=10, ERI_GCB_T=11,
    ERI_GCB_LV=12, ERI_GCB_LVT=13
};
enum { ERI_INCB_NONE=0, ERI_INCB_CONSONANT=1, ERI_INCB_EXTEND=2, ERI_INCB_LINKER=3 };

static uint8_t eri_unicode_lookup(const eri_unicode_range *table,size_t count,uint32_t cp){
    size_t lo=0,hi=count;
    while(lo<hi){
        size_t mid=lo+(hi-lo)/2;
        eri_unicode_range r=table[mid];
        if(cp<r.first)hi=mid;
        else if(cp>r.last)lo=mid+1;
        else return r.value;
    }
    return 0;
}

static uint8_t eri_gcb(uint32_t cp){ return eri_unicode_lookup(eri_gcb_table,eri_gcb_table_count,cp); }
static uint8_t eri_incb(uint32_t cp){ return eri_unicode_lookup(eri_incb_table,eri_incb_table_count,cp); }
static bool eri_extended_pictographic(uint32_t cp){ return eri_unicode_lookup(eri_ep_table,eri_ep_table_count,cp)!=0; }

static uint32_t eri_utf8_decode_scalar(eri_text text,size_t pos,size_t *next){
    if(pos>=text.len)eri_fault("invalid UTF-8 inside Text");
    unsigned char c0=text.data[pos];
    size_t width=eri_utf8_width(c0);
    if(pos+width>text.len)eri_fault("invalid UTF-8 inside Text");
    if(width==1){*next=pos+1;return c0;}
    uint32_t cp=(uint32_t)(c0 & (width==2?0x1f:(width==3?0x0f:0x07)));
    for(size_t i=1;i<width;i++){
        unsigned char c=text.data[pos+i];
        if((c&0xc0)!=0x80)eri_fault("invalid UTF-8 inside Text");
        cp=(cp<<6)|(uint32_t)(c&0x3f);
    }
    *next=pos+width;
    return cp;
}

static size_t eri_text_decode_scalars(eri_text text,uint32_t **out_cp,size_t **out_offset){
    size_t capacity=text.len?text.len:1;
    uint32_t *cp=(uint32_t*)eri_alloc(sizeof(uint32_t)*capacity);
    size_t *offset=(size_t*)eri_alloc(sizeof(size_t)*(capacity+1));
    size_t count=0,pos=0;
    while(pos<text.len){
        size_t next;
        offset[count]=pos;
        cp[count]=eri_utf8_decode_scalar(text,pos,&next);
        count++;pos=next;
    }
    offset[count]=text.len;
    *out_cp=cp;*out_offset=offset;
    return count;
}

static bool eri_grapheme_break(const uint32_t *cp,size_t count,size_t i){
    (void)count;
    uint8_t a=eri_gcb(cp[i-1]),b=eri_gcb(cp[i]);
    /* GB3 */ if(a==ERI_GCB_CR&&b==ERI_GCB_LF)return false;
    /* GB4 */ if(a==ERI_GCB_CONTROL||a==ERI_GCB_CR||a==ERI_GCB_LF)return true;
    /* GB5 */ if(b==ERI_GCB_CONTROL||b==ERI_GCB_CR||b==ERI_GCB_LF)return true;
    /* GB6 */ if(a==ERI_GCB_L&&(b==ERI_GCB_L||b==ERI_GCB_V||b==ERI_GCB_LV||b==ERI_GCB_LVT))return false;
    /* GB7 */ if((a==ERI_GCB_LV||a==ERI_GCB_V)&&(b==ERI_GCB_V||b==ERI_GCB_T))return false;
    /* GB8 */ if((a==ERI_GCB_LVT||a==ERI_GCB_T)&&b==ERI_GCB_T)return false;
    /* GB9 */ if(b==ERI_GCB_EXTEND||b==ERI_GCB_ZWJ)return false;
    /* GB9a */ if(b==ERI_GCB_SPACINGMARK)return false;
    /* GB9b */ if(a==ERI_GCB_PREPEND)return false;
    /* GB9c: InCB Consonant ... Linker ... x Consonant */
    if(eri_incb(cp[i])==ERI_INCB_CONSONANT){
        size_t j=i;bool saw_linker=false;
        while(j>0){
            uint8_t p=eri_incb(cp[j-1]);
            if(p==ERI_INCB_LINKER){saw_linker=true;j--;continue;}
            if(p==ERI_INCB_EXTEND){j--;continue;}
            break;
        }
        if(saw_linker&&j>0&&eri_incb(cp[j-1])==ERI_INCB_CONSONANT)return false;
    }
    /* GB11: Extended_Pictographic Extend* ZWJ x Extended_Pictographic */
    if(eri_extended_pictographic(cp[i])&&a==ERI_GCB_ZWJ){
        size_t j=i-1;
        if(j>0)j--;
        else j=(size_t)-1;
        while(j!=(size_t)-1&&eri_gcb(cp[j])==ERI_GCB_EXTEND){ if(j==0){j=(size_t)-1;break;} j--; }
        if(j!=(size_t)-1&&eri_extended_pictographic(cp[j]))return false;
    }
    /* GB12/GB13: pair consecutive Regional Indicators. */
    if(a==ERI_GCB_RI&&b==ERI_GCB_RI){
        size_t preceding=0,j=i;
        while(j>0&&eri_gcb(cp[j-1])==ERI_GCB_RI){preceding++;j--;}
        if((preceding&1u)!=0)return false;
    }
    /* GB999 */ return true;
}

static int64_t eri_text_character_count(eri_text text){
    uint32_t *cp;size_t *offset;
    size_t n=eri_text_decode_scalars(text,&cp,&offset);
    (void)offset;
    if(n==0)return 0;
    int64_t clusters=1;
    for(size_t i=1;i<n;i++)if(eri_grapheme_break(cp,n,i))clusters++;
    return clusters;
}

static eri_text eri_text_character_get(eri_text text,int64_t index){
    if(index<0)eri_fault("Text view index out of bounds");
    uint32_t *cp;size_t *offset;
    size_t n=eri_text_decode_scalars(text,&cp,&offset);
    if(n==0)eri_fault("Text view index out of bounds");
    int64_t cluster=0;size_t start=0;
    for(size_t i=1;i<=n;i++){
        bool boundary=(i==n)||eri_grapheme_break(cp,n,i);
        if(boundary){
            if(cluster==index)return eri_text_from_bytes(text.data+offset[start],offset[i]-offset[start]);
            cluster++;start=i;
        }
    }
    eri_fault("Text view index out of bounds");
    return eri_text_from_bytes(NULL,0);
}
'''
    return (
        f"\n/* Unicode {UNICODE_VERSION} grapheme properties generated by pinned regex {PINNED_REGEX_VERSION}. */\n"
        + runtime.split("static uint8_t eri_unicode_lookup", 1)[0]
        + tables
        + "static uint8_t eri_unicode_lookup"
        + runtime.split("static uint8_t eri_unicode_lookup", 1)[1]
    )
