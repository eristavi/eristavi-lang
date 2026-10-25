"""Prefix-preserving append buffers for immutable Text concatenation.

Existing Text values retain their byte length and original buffer. Appending can
write only beyond the initialized prefix; growing allocates a new buffer rather
than invalidating aliases. This is an implementation optimization, not identity.
"""
TEXT_APPEND_RUNTIME = r'''
typedef struct eri_text_append_buffer { unsigned char *data; size_t used,capacity; struct eri_text_append_buffer *next; } eri_text_append_buffer;
static eri_text_append_buffer *eri_text_append_buckets[4096];
static size_t eri_text_append_hash(const unsigned char *data){return ((uintptr_t)data>>4)%4096;}
static unsigned char *eri_prefix_append(const unsigned char *prefix,size_t prefix_size,const unsigned char *suffix,size_t suffix_size){
    eri_text a={prefix_size,(unsigned char*)prefix},b={suffix_size,(unsigned char*)suffix};
    if(a.len>SIZE_MAX-b.len)eri_fault("Text size overflow");
    if(!b.len)return a.data;
    size_t length=a.len+b.len;
    eri_text_append_buffer *buffer=eri_text_append_buckets[eri_text_append_hash(a.data)];
    while(buffer && buffer->data!=a.data)buffer=buffer->next;
    if(buffer && buffer->used==a.len && length<=buffer->capacity){memmove(buffer->data+a.len,b.data,b.len);buffer->used=length;return buffer->data;}
    size_t capacity=32;while(capacity<length){if(capacity>SIZE_MAX/2){capacity=length;break;}capacity*=2;}
    unsigned char *data=eri_alloc(capacity);if(a.len)memcpy(data,a.data,a.len);memcpy(data+a.len,b.data,b.len);
    buffer=eri_alloc(sizeof(*buffer));size_t hash=eri_text_append_hash(data);
    *buffer=(eri_text_append_buffer){data,length,capacity,eri_text_append_buckets[hash]};eri_text_append_buckets[hash]=buffer;
    return data;
}
static eri_text eri_text_add(eri_text a,eri_text b){if(!b.len)return a;if(!a.len)return b;unsigned char *data=eri_prefix_append(a.data,a.len,b.data,b.len);return (eri_text){a.len+b.len,data};}
'''
