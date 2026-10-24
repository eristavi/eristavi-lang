"""Pinned Unicode library implementation for the portable C bootstrap route.

No locale, ICU, or host Unicode dependency is consulted by the executable.
Tables are generated from the same Unicode 17 dependencies as Stage-0.
"""
from functools import lru_cache
import unicodedata2

from .unicode_c import _property_ranges, _emit_table
from .unicode_support import UNICODE_VERSION


@lru_cache(maxsize=1)
def unicode_library_c():
    if unicodedata2.unidata_version != UNICODE_VERSION:
        raise RuntimeError("Unicode library table version mismatch")
    tables = []
    for name, prop in (("start", "XID_Start"), ("continue", "XID_Continue")):
        tables.append(_emit_table("eri_xid_" + name, [(a, b, 1) for a, b in _property_ranges(prop)]))
    decompositions, data, compositions, classes = [], [], [], []
    for cp in range(0x110000):
        char = chr(cp)
        ccc = unicodedata2.combining(char)
        if ccc:
            classes.append((cp, cp, ccc))
        decomposition = unicodedata2.decomposition(char)
        if decomposition and not decomposition.startswith("<"):
            values = [int(item, 16) for item in decomposition.split()]
            decompositions.append((cp, len(data), len(values)))
            data.extend(values)
            if len(values) == 2 and unicodedata2.normalize("NFC", "".join(map(chr, values))) == char:
                compositions.append((*values, cp))
    tables.append(_emit_table("eri_ccc", classes))
    tables.append("typedef struct { uint32_t scalar, offset, count; } eri_decomp;\n")
    tables.append("static const eri_decomp eri_decompositions[]={" + ",".join("{%d,%d,%d}" % row for row in decompositions) + "};\n")
    tables.append("static const uint32_t eri_decomposition_data[]={" + ",".join(map(str, data)) + "};\n")
    tables.append("typedef struct { uint32_t first, second, result; } eri_comp;\n")
    tables.append("static const eri_comp eri_compositions[]={" + ",".join("{%d,%d,%d}" % row for row in sorted(compositions)) + "};\n")
    return "\n".join(tables) + _RUNTIME


_RUNTIME = r'''
static unsigned eri_combining_class(uint32_t cp){
    return eri_unicode_lookup(eri_ccc,eri_ccc_count,cp);
}
static bool eri_unicode_identifier(eri_text text,bool start){
    if(!text.len)return false;
    size_t next=0;
    uint32_t cp=eri_utf8_decode_scalar(text,0,&next);
    if(next!=text.len)return false;
    if(cp==95)return true;
    return start ? eri_unicode_lookup(eri_xid_start,eri_xid_start_count,cp)!=0
                 : eri_unicode_lookup(eri_xid_continue,eri_xid_continue_count,cp)!=0;
}
static bool eri_unicode_isIdentifierStart(eri_text text){return eri_unicode_identifier(text,true);}
static bool eri_unicode_isIdentifierContinue(eri_text text){return eri_unicode_identifier(text,false);}
static size_t eri_encode_scalar(uint32_t cp,unsigned char *out){
    if(cp<0x80){out[0]=(unsigned char)cp;return 1;}
    if(cp<0x800){out[0]=0xc0|(cp>>6);out[1]=0x80|(cp&63);return 2;}
    if(cp<0x10000){out[0]=0xe0|(cp>>12);out[1]=0x80|((cp>>6)&63);out[2]=0x80|(cp&63);return 3;}
    out[0]=0xf0|(cp>>18);out[1]=0x80|((cp>>12)&63);out[2]=0x80|((cp>>6)&63);out[3]=0x80|(cp&63);return 4;
}
static eri_text eri_unicode_fromScalar(int64_t scalar){
    if(scalar<0||scalar>0x10ffff||(scalar>=0xd800&&scalar<=0xdfff))eri_fault("invalid Unicode scalar value");
    unsigned char data[4];size_t n=eri_encode_scalar((uint32_t)scalar,data);
    return eri_text_from_bytes(data,n);
}
typedef struct { uint32_t *data;size_t count,capacity; } eri_scalar_buffer;
static void eri_scalar_push(eri_scalar_buffer *buffer,uint32_t cp){
    if(buffer->count==buffer->capacity){
        size_t capacity=buffer->capacity ? buffer->capacity*2 : 16;
        if(capacity<buffer->capacity||capacity>SIZE_MAX/sizeof(uint32_t))eri_fault("Unicode buffer too large");
        uint32_t *data=(uint32_t*)realloc(buffer->data,capacity*sizeof(uint32_t));
        if(!data)eri_fault("out of memory");
        buffer->data=data;buffer->capacity=capacity;
    }
    buffer->data[buffer->count++]=cp;
    /* Stable canonical ordering; never reorder across a starter. */
    unsigned cc=eri_combining_class(cp);
    size_t i=buffer->count-1;
    while(cc&&i&&eri_combining_class(buffer->data[i-1])>cc){
        buffer->data[i]=buffer->data[i-1];buffer->data[--i]=cp;
    }
}
static void eri_canonical_decompose(eri_scalar_buffer *buffer,uint32_t cp){
    if(cp>=0xac00&&cp<0xd7a4){
        uint32_t s=cp-0xac00;
        eri_scalar_push(buffer,0x1100+s/588);
        eri_scalar_push(buffer,0x1161+(s%588)/28);
        if(s%28)eri_scalar_push(buffer,0x11a7+s%28);
        return;
    }
    size_t lo=0,hi=sizeof(eri_decompositions)/sizeof(eri_decompositions[0]);
    while(lo<hi){size_t mid=lo+(hi-lo)/2;const eri_decomp *d=&eri_decompositions[mid];
        if(cp<d->scalar)hi=mid;
        else if(cp>d->scalar)lo=mid+1;
        else {for(size_t i=0;i<d->count;i++)eri_canonical_decompose(buffer,eri_decomposition_data[d->offset+i]);return;}
    }
    eri_scalar_push(buffer,cp);
}
static uint32_t eri_canonical_compose(uint32_t a,uint32_t b){
    if(a>=0x1100&&a<0x1113&&b>=0x1161&&b<0x1176)return 0xac00+(a-0x1100)*588+(b-0x1161)*28;
    if(a>=0xac00&&a<0xd7a4&&(a-0xac00)%28==0&&b>0x11a7&&b<0x11c3)return a+b-0x11a7;
    size_t lo=0,hi=sizeof(eri_compositions)/sizeof(eri_compositions[0]);
    while(lo<hi){size_t mid=lo+(hi-lo)/2;const eri_comp *c=&eri_compositions[mid];
        if(a<c->first||(a==c->first&&b<c->second))hi=mid;
        else if(a>c->first||(a==c->first&&b>c->second))lo=mid+1;
        else return c->result;
    }
    return 0;
}
static eri_text eri_unicode_normalizeNfc(eri_text text){
    eri_scalar_buffer buffer={NULL,0,0};
    for(size_t pos=0;pos<text.len;){size_t next;uint32_t cp=eri_utf8_decode_scalar(text,pos,&next);eri_canonical_decompose(&buffer,cp);pos=next;}
    size_t used=0,starter=0;unsigned previous=0;
    for(size_t i=0;i<buffer.count;i++){
        uint32_t cp=buffer.data[i];unsigned cc=eri_combining_class(cp);
        uint32_t composite=used ? eri_canonical_compose(buffer.data[starter],cp) : 0;
        if(composite&&(previous==0||previous<cc)){buffer.data[starter]=composite;}
        else {if(cc==0)starter=used;buffer.data[used++]=cp;previous=cc;}
    }
    if(used>SIZE_MAX/4)eri_fault("Unicode buffer too large");
    unsigned char *bytes=(unsigned char*)malloc(used ? used*4 : 1);
    if(!bytes)eri_fault("out of memory");
    size_t length=0;
    for(size_t i=0;i<used;i++)length+=eri_encode_scalar(buffer.data[i],bytes+length);
    eri_text result=eri_text_from_bytes(bytes,length);
    free(bytes);free(buffer.data);return result;
}
'''
