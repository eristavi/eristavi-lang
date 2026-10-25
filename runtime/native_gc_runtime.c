/* Native-only heap reclamation layer for the pinned bootstrap runtime.
   This file deliberately leaves runtime/value_runtime.c unchanged so the
   generated-C/reference path keeps its independent bootstrap behavior. */
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#ifndef ERIST_NATIVE_RUNTIME
#error "native_gc_runtime.c requires ERIST_NATIVE_RUNTIME"
#endif
#ifdef ERIST_HEAP_STATS
#error "ERIST_HEAP_STATS is a separate diagnostic registry; do not combine it with native heap GC"
#endif

#ifndef ERIST_HEAP_GC_INTERVAL
#define ERIST_HEAP_GC_INTERVAL 65536
#endif
#if ERIST_HEAP_GC_INTERVAL < 1
#error "ERIST_HEAP_GC_INTERVAL must be positive"
#endif

#define ERIST_NATIVE_GC_HASH_BUCKETS 65536u

typedef struct eri_native_gc_block {
    unsigned char *base;
    size_t size;
    bool marked;
    bool traced;
    bool weak_index;
    struct eri_native_gc_block *previous;
    struct eri_native_gc_block *next;
    struct eri_native_gc_block *hash_next;
} eri_native_gc_block;

static eri_native_gc_block *eri_native_gc_blocks;
static eri_native_gc_block *eri_native_gc_hash[ERIST_NATIVE_GC_HASH_BUCKETS];
static eri_native_gc_block **eri_native_gc_ranges;
static size_t eri_native_gc_range_count;
static size_t eri_native_gc_live_blocks;
static size_t eri_native_gc_live_bytes;
static size_t eri_native_gc_peak_bytes;
static size_t eri_native_gc_allocations_since_collection;
static size_t eri_native_gc_next_collection=ERIST_HEAP_GC_INTERVAL;
static size_t eri_native_gc_collections;
static size_t eri_native_gc_reclaimed_blocks;
static size_t eri_native_gc_reclaimed_bytes;
static bool eri_native_gc_collecting;

static void *eri_native_gc_malloc(size_t size);
static void *eri_native_gc_realloc(void *pointer,size_t size);
static void eri_native_gc_free(void *pointer);

/* Track every allocation made by the bootstrap runtime. Collection itself uses
   the system allocator after these macros are removed below. */
#define malloc eri_native_gc_malloc
#define realloc eri_native_gc_realloc
#define free eri_native_gc_free

/* A safe point must run only after the runtime has finished constructing the
   returned value/frame/scope. Rename selected pointer-ABI entries so wrappers can
   collect after the original operation has completed. */
#define evn_scope_enter eri_gc_base_scope_enter
#define evn_scope_leave eri_gc_base_scope_leave
#define evn_void eri_gc_base_void
#define evn_copy eri_gc_base_copy
#define evn_int eri_gc_base_int
#define evn_float eri_gc_base_float
#define evn_bool eri_gc_base_bool
#define evn_text eri_gc_base_text
#define evn_unary eri_gc_base_unary
#define evn_binary eri_gc_base_binary
#define evn_object eri_gc_base_object
#define evn_member eri_gc_base_member
#define evn_index eri_gc_base_index
#define evn_count eri_gc_base_count
#define evn_add eri_gc_base_add
#define evn_wrap eri_gc_base_wrap
#define evn_none eri_gc_base_none
#define evn_get eri_gc_base_get
#define evn_view eri_gc_base_view
#define evn_builtin0 eri_gc_base_builtin0
#define evn_builtin1 eri_gc_base_builtin1
#define evn_builtin2 eri_gc_base_builtin2
#define evn_frame eri_gc_base_frame
#define evn_pop eri_gc_base_pop
#define evn_error eri_gc_base_error

#include "value_runtime.c"

#undef evn_error
#undef evn_pop
#undef evn_frame
#undef evn_builtin2
#undef evn_builtin1
#undef evn_builtin0
#undef evn_view
#undef evn_get
#undef evn_none
#undef evn_wrap
#undef evn_add
#undef evn_count
#undef evn_index
#undef evn_member
#undef evn_object
#undef evn_binary
#undef evn_unary
#undef evn_text
#undef evn_bool
#undef evn_float
#undef evn_int
#undef evn_copy
#undef evn_void
#undef evn_scope_leave
#undef evn_scope_enter
#undef free
#undef realloc
#undef malloc

typedef struct {
    ev_value *items;
    size_t count;
    size_t capacity;
} eri_native_gc_value_queue;

static void eri_native_gc_overflow(void){eri_fault("native heap accounting overflow");}
static size_t eri_native_gc_add_size(size_t first,size_t second){if(first>SIZE_MAX-second)eri_native_gc_overflow();return first+second;}

static size_t eri_native_gc_hash_index(const void *pointer){
    uintptr_t value=(uintptr_t)pointer;
    value^=value>>17;value^=value>>9;
    return (size_t)((value>>4)&(ERIST_NATIVE_GC_HASH_BUCKETS-1u));
}

static void eri_native_gc_hash_insert(eri_native_gc_block *block){
    size_t bucket=eri_native_gc_hash_index(block->base);
    block->hash_next=eri_native_gc_hash[bucket];
    eri_native_gc_hash[bucket]=block;
}

static void eri_native_gc_hash_remove(eri_native_gc_block *block){
    size_t bucket=eri_native_gc_hash_index(block->base);
    eri_native_gc_block **link=&eri_native_gc_hash[bucket];
    while(*link&&*link!=block)link=&(*link)->hash_next;
    if(*link==block)*link=block->hash_next;
    block->hash_next=NULL;
}

static eri_native_gc_block *eri_native_gc_find_exact(const void *pointer){
    if(!pointer)return NULL;
    size_t bucket=eri_native_gc_hash_index(pointer);
    for(eri_native_gc_block *block=eri_native_gc_hash[bucket];block;block=block->hash_next)
        if(block->base==(const unsigned char*)pointer)return block;
    return NULL;
}

static int eri_native_gc_range_compare(const void *first,const void *second){
    uintptr_t a=(uintptr_t)(*(eri_native_gc_block *const *)first)->base;
    uintptr_t b=(uintptr_t)(*(eri_native_gc_block *const *)second)->base;
    return a<b?-1:(a>b?1:0);
}

static void eri_native_gc_build_range_index(void){
    free(eri_native_gc_ranges);
    eri_native_gc_ranges=NULL;
    eri_native_gc_range_count=0;
    if(!eri_native_gc_live_blocks)return;
    if(eri_native_gc_live_blocks>SIZE_MAX/sizeof(*eri_native_gc_ranges))eri_native_gc_overflow();
    eri_native_gc_ranges=(eri_native_gc_block**)malloc(eri_native_gc_live_blocks*sizeof(*eri_native_gc_ranges));
    if(!eri_native_gc_ranges)eri_fault("out of memory");
    for(eri_native_gc_block *block=eri_native_gc_blocks;block;block=block->next)
        eri_native_gc_ranges[eri_native_gc_range_count++]=block;
    qsort(eri_native_gc_ranges,eri_native_gc_range_count,sizeof(*eri_native_gc_ranges),eri_native_gc_range_compare);
}

static void eri_native_gc_release_range_index(void){
    free(eri_native_gc_ranges);
    eri_native_gc_ranges=NULL;
    eri_native_gc_range_count=0;
}

/* Native value roots normally name slot allocations exactly. member_ref/index_ref
   are the intentional exception: they may name an ev_value inside object data.
   Exact addresses stay O(1) through the hash; the sorted address-range index is
   built lazily only after a genuine exact-pointer miss needs containment. */
static eri_native_gc_block *eri_native_gc_find_value_owner(const void *pointer){
    if(!pointer)return NULL;
    eri_native_gc_block *exact=eri_native_gc_find_exact(pointer);
    if(exact)return exact;
    if(!eri_native_gc_range_count){
        if(!eri_native_gc_live_blocks)return NULL;
        eri_native_gc_build_range_index();
    }
    uintptr_t value=(uintptr_t)pointer;
    size_t low=0,high=eri_native_gc_range_count;
    while(low<high){
        size_t middle=low+(high-low)/2;
        if((uintptr_t)eri_native_gc_ranges[middle]->base<=value)low=middle+1;
        else high=middle;
    }
    if(!low)return NULL;
    eri_native_gc_block *block=eri_native_gc_ranges[low-1];
    uintptr_t start=(uintptr_t)block->base;
    return value>=start&&value-start<block->size?block:NULL;
}

static void *eri_native_gc_malloc(size_t size){
    size_t actual=size?size:1;
    void *memory=malloc(actual);
    if(!memory)eri_fault("out of memory");
    eri_native_gc_block *block=(eri_native_gc_block*)malloc(sizeof(*block));
    if(!block){free(memory);eri_fault("out of memory");}
    *block=(eri_native_gc_block){
        .base=(unsigned char*)memory,.size=actual,.marked=false,.traced=false,.weak_index=false,
        .previous=NULL,.next=eri_native_gc_blocks,.hash_next=NULL
    };
    if(eri_native_gc_blocks)eri_native_gc_blocks->previous=block;
    eri_native_gc_blocks=block;
    eri_native_gc_hash_insert(block);
    eri_native_gc_live_blocks=eri_native_gc_add_size(eri_native_gc_live_blocks,1);
    eri_native_gc_live_bytes=eri_native_gc_add_size(eri_native_gc_live_bytes,actual);
    if(eri_native_gc_live_bytes>eri_native_gc_peak_bytes)eri_native_gc_peak_bytes=eri_native_gc_live_bytes;
    eri_native_gc_allocations_since_collection=eri_native_gc_add_size(eri_native_gc_allocations_since_collection,1);
    return memory;
}

static void eri_native_gc_unlink(eri_native_gc_block *block){
    eri_native_gc_hash_remove(block);
    if(block->previous)block->previous->next=block->next;else eri_native_gc_blocks=block->next;
    if(block->next)block->next->previous=block->previous;
}

static void eri_native_gc_free(void *pointer){
    if(!pointer)return;
    eri_native_gc_block *block=eri_native_gc_find_exact(pointer);
    if(!block){free(pointer);return;}
    eri_native_gc_unlink(block);
    eri_native_gc_live_blocks--;
    eri_native_gc_live_bytes-=block->size;
    free(block->base);
    free(block);
}

static void *eri_native_gc_realloc(void *pointer,size_t size){
    if(!pointer)return eri_native_gc_malloc(size);
    eri_native_gc_block *block=eri_native_gc_find_exact(pointer);
    if(!block){
        void *result=realloc(pointer,size?size:1);
        if(!result)eri_fault("out of memory");
        return result;
    }
    size_t actual=size?size:1;
    eri_native_gc_hash_remove(block);
    void *result=realloc(block->base,actual);
    if(!result)eri_fault("out of memory");
    eri_native_gc_live_bytes-=block->size;
    eri_native_gc_live_bytes=eri_native_gc_add_size(eri_native_gc_live_bytes,actual);
    if(eri_native_gc_live_bytes>eri_native_gc_peak_bytes)eri_native_gc_peak_bytes=eri_native_gc_live_bytes;
    block->base=(unsigned char*)result;
    block->size=actual;
    eri_native_gc_hash_insert(block);
    eri_native_gc_allocations_since_collection=eri_native_gc_add_size(eri_native_gc_allocations_since_collection,1);
    return result;
}

static bool eri_native_gc_mark_block(eri_native_gc_block *block){
    if(!block||block->marked)return false;
    block->marked=true;
    return true;
}

static bool eri_native_gc_mark_pointer(const void *pointer){return eri_native_gc_mark_block(eri_native_gc_find_exact(pointer));}

static void eri_native_gc_queue_value(eri_native_gc_value_queue *queue,ev_value value){
    if(queue->count==queue->capacity){
        size_t capacity=queue->capacity?queue->capacity*2:64;
        if(capacity<queue->capacity||capacity>SIZE_MAX/sizeof(ev_value))eri_native_gc_overflow();
        ev_value *items=(ev_value*)realloc(queue->items,capacity*sizeof(ev_value));
        if(!items)eri_fault("out of memory");
        queue->items=items;queue->capacity=capacity;
    }
    queue->items[queue->count++]=value;
}

static void eri_native_gc_mark_text(eri_text text){if(text.data)eri_native_gc_mark_pointer(text.data);}

static void eri_native_gc_mark_resource(eri_file *resource){
    if(!resource)return;
    eri_native_gc_block *block=eri_native_gc_find_exact(resource);
    bool fresh=eri_native_gc_mark_block(block);
    if(!fresh&&block&&block->traced)return;
    if(block)block->traced=true;
    eri_native_gc_mark_text(resource->path);
    if(resource->c_path)eri_native_gc_mark_pointer(resource->c_path);
}

static void eri_native_gc_mark_object(ev_object *object,eri_native_gc_value_queue *queue){
    if(!object)return;
    eri_native_gc_block *block=eri_native_gc_find_exact(object);
    bool fresh=eri_native_gc_mark_block(block);
    if(!fresh&&block&&block->traced)return;
    if(block)block->traced=true;
    if(object->data){
        eri_native_gc_mark_pointer(object->data);
        for(size_t index=0;index<object->count;index++)eri_native_gc_queue_value(queue,object->data[index]);
    }
}

static void eri_native_gc_mark_value(ev_value value,eri_native_gc_value_queue *queue){
    int kind=value.type;
    if(value.type>5)kind=ev_types[value.type].kind;
    if(kind==4){eri_native_gc_mark_text(value.text);return;}
    if(kind==10){eri_native_gc_mark_resource(value.resource);return;}
    if(kind==12){eri_native_gc_mark_text(value.view.text);return;}
    if(kind==6||kind==7||kind==8||kind==9||kind==11){eri_native_gc_mark_object(value.object,queue);return;}
}

static void eri_native_gc_mark_failure_payload(const char *type,void *payload,eri_native_gc_value_queue *queue){
    if(!payload)return;
    eri_native_gc_block *block=eri_native_gc_find_exact(payload);
    if(block)eri_native_gc_mark_block(block);
    if(type&&strcmp(type,"std.files.FileError")==0){
        eri_file_error *error=(eri_file_error*)payload;
        eri_native_gc_mark_text(error->f_message);
        eri_native_gc_mark_text(error->f_path);
    }else{
        eri_native_gc_queue_value(queue,*(ev_value*)payload);
    }
}

static void eri_native_gc_mark_failure(eri_failure_value *failure,eri_native_gc_value_queue *queue,bool owned){
    if(!failure)return;
    if(owned){
        eri_native_gc_block *block=eri_native_gc_find_exact(failure);
        if(block)eri_native_gc_mark_block(block);
    }
    if(!failure->type)return;
    eri_native_gc_mark_text(failure->message);
    eri_native_gc_mark_failure_payload(failure->type,failure->payload,queue);
    eri_secondary_failure *secondary=failure->secondary;
    while(secondary){
        eri_native_gc_block *block=eri_native_gc_find_exact(secondary);
        if(block&&block->traced)break;
        if(block){eri_native_gc_mark_block(block);block->traced=true;}
        eri_native_gc_mark_text(secondary->message);
        eri_native_gc_mark_failure_payload(secondary->type,secondary->payload,queue);
        secondary=secondary->next;
    }
}

static void eri_native_gc_prepare_weak_indexes(void){
    for(eri_native_gc_block *block=eri_native_gc_blocks;block;block=block->next){block->marked=false;block->traced=false;block->weak_index=false;}
    for(size_t bucket=0;bucket<sizeof(eri_text_append_buckets)/sizeof(eri_text_append_buckets[0]);bucket++)
        for(eri_text_append_buffer *cursor=eri_text_append_buckets[bucket];cursor;cursor=cursor->next){
            eri_native_gc_block *block=eri_native_gc_find_exact(cursor);
            if(block)block->weak_index=true;
        }
}

static void eri_native_gc_mark_roots(eri_native_gc_value_queue *queue,const ev_value *temporary_value,const eri_failure_value *temporary_failure){
    for(ev_slot_node *slot=ev_slots;slot;slot=slot->next){eri_native_gc_mark_pointer(slot);eri_native_gc_queue_value(queue,slot->value);}
    for(ev_scope *scope=ev_scopes;scope;scope=scope->previous){
        eri_native_gc_mark_pointer(scope);
        if(scope->roots&&scope->classes){
            for(size_t index=0;index<scope->root_count;index++){
                uintptr_t key=0;memcpy(&key,scope->roots+index*sizeof(key),sizeof(key));
                if(!key)continue;
                if(scope->classes[index]==1){
                    eri_native_gc_block *owner=eri_native_gc_find_value_owner((void*)key);
                    if(owner){eri_native_gc_mark_block(owner);eri_native_gc_queue_value(queue,*(ev_value*)key);}
                }else if(scope->classes[index]==5){
                    eri_native_gc_mark_failure((eri_failure_value*)key,queue,true);
                }else if(scope->classes[index]==4||scope->classes[index]==6){
                    eri_native_gc_mark_pointer((void*)key);
                }
            }
        }
    }
    for(eri_handler_frame *frame=eri_handler_top;frame;frame=frame->prev)eri_native_gc_mark_pointer(frame);
    eri_native_gc_mark_failure(&eri_failure,queue,false);
    if(temporary_value){
        eri_native_gc_block *owner=eri_native_gc_find_value_owner(temporary_value);
        if(owner){eri_native_gc_mark_block(owner);eri_native_gc_queue_value(queue,*temporary_value);}
    }
    if(temporary_failure)eri_native_gc_mark_failure((eri_failure_value*)temporary_failure,queue,false);
}

static void eri_native_gc_keep_live_prefix_indexes(void){
    size_t buckets=sizeof(eri_text_append_buckets)/sizeof(eri_text_append_buckets[0]);
    for(size_t bucket=0;bucket<buckets;bucket++){
        eri_text_append_buffer *cursor=eri_text_append_buckets[bucket];
        eri_text_append_buffer **tail=&eri_text_append_buckets[bucket];
        while(cursor){
            eri_text_append_buffer *next=cursor->next;
            eri_native_gc_block *data=eri_native_gc_find_exact(cursor->data);
            eri_native_gc_block *index=eri_native_gc_find_exact(cursor);
            if(data&&data->marked&&index){
                eri_native_gc_mark_block(index);
                *tail=cursor;tail=&cursor->next;
            }
            cursor=next;
        }
        *tail=NULL;
    }
}

static void eri_native_gc_sweep(void){
    eri_native_gc_block *block=eri_native_gc_blocks;
    while(block){
        eri_native_gc_block *next=block->next;
        if(!block->marked){
            size_t bytes=block->size;
            eri_native_gc_unlink(block);
            eri_native_gc_live_blocks--;
            eri_native_gc_live_bytes-=bytes;
            eri_native_gc_reclaimed_blocks=eri_native_gc_add_size(eri_native_gc_reclaimed_blocks,1);
            eri_native_gc_reclaimed_bytes=eri_native_gc_add_size(eri_native_gc_reclaimed_bytes,bytes);
            free(block->base);free(block);
        }else{block->marked=false;block->traced=false;block->weak_index=false;}
        block=next;
    }
}

static void eri_native_gc_collect(const ev_value *temporary_value,const eri_failure_value *temporary_failure){
    if(eri_native_gc_collecting)return;
    eri_native_gc_collecting=true;
    eri_native_gc_prepare_weak_indexes();
    eri_native_gc_value_queue queue={0};
    eri_native_gc_mark_roots(&queue,temporary_value,temporary_failure);
    size_t cursor=0;
    while(cursor<queue.count)eri_native_gc_mark_value(queue.items[cursor++],&queue);
    eri_native_gc_keep_live_prefix_indexes();
    eri_native_gc_release_range_index();
    eri_native_gc_sweep();
    free(queue.items);
    eri_native_gc_allocations_since_collection=0;
    eri_native_gc_next_collection=ERIST_HEAP_GC_INTERVAL;
#if ERIST_HEAP_GC_INTERVAL > 1
    size_t growth=eri_native_gc_live_blocks;
    if(growth>SIZE_MAX/4)growth=SIZE_MAX;else growth*=4;
    if(growth>eri_native_gc_next_collection)eri_native_gc_next_collection=growth;
#endif
    eri_native_gc_collections=eri_native_gc_add_size(eri_native_gc_collections,1);
    eri_native_gc_collecting=false;
}

static void eri_native_gc_safe_point(const ev_value *temporary_value,const eri_failure_value *temporary_failure){
    if(eri_native_gc_allocations_since_collection>=eri_native_gc_next_collection)
        eri_native_gc_collect(temporary_value,temporary_failure);
}

/* Private hardening/test hooks. They are runtime implementation details, not
   source-language functions and not a stable public ABI. */
void eri_native_heap_collect(void){eri_native_gc_collect(NULL,NULL);}
size_t eri_native_heap_live_blocks(void){return eri_native_gc_live_blocks;}
size_t eri_native_heap_live_bytes(void){return eri_native_gc_live_bytes;}
size_t eri_native_heap_peak_bytes(void){return eri_native_gc_peak_bytes;}
size_t eri_native_heap_collections(void){return eri_native_gc_collections;}
size_t eri_native_heap_reclaimed_blocks(void){return eri_native_gc_reclaimed_blocks;}
size_t eri_native_heap_reclaimed_bytes(void){return eri_native_gc_reclaimed_bytes;}

/* Safe-point wrappers. Object storage is zeroed before its first possible
   collection so partially initialized aggregate construction is traceable. */
ev_scope *evn_scope_enter(void){ev_scope *result=eri_gc_base_scope_enter();eri_native_gc_safe_point(NULL,NULL);return result;}
ev_value *evn_scope_leave(ev_scope *scope,ev_value *value){ev_value *result=eri_gc_base_scope_leave(scope,value);eri_native_gc_safe_point(NULL,NULL);return result;}
ev_value *evn_void(void){ev_value *result=eri_gc_base_void();eri_native_gc_safe_point(NULL,NULL);return result;}
ev_value *evn_copy(ev_value *value){ev_value *result=eri_gc_base_copy(value);eri_native_gc_safe_point(NULL,NULL);return result;}
ev_value *evn_int(int64_t value){ev_value *result=eri_gc_base_int(value);eri_native_gc_safe_point(NULL,NULL);return result;}
ev_value *evn_float(const char *text){ev_value *result=eri_gc_base_float(text);eri_native_gc_safe_point(NULL,NULL);return result;}
ev_value *evn_bool(int64_t value){ev_value *result=eri_gc_base_bool(value);eri_native_gc_safe_point(NULL,NULL);return result;}
ev_value *evn_text(const unsigned char *text,size_t count){ev_value *result=eri_gc_base_text(text,count);eri_native_gc_safe_point(NULL,NULL);return result;}
ev_value *evn_unary(int op,ev_value *value){ev_value *result=eri_gc_base_unary(op,value);eri_native_gc_safe_point(NULL,NULL);return result;}
ev_value *evn_binary(int op,ev_value *first,ev_value *second){ev_value *result=eri_gc_base_binary(op,first,second);eri_native_gc_safe_point(NULL,NULL);return result;}
ev_value *evn_object(int type,size_t count){ev_value *result=eri_gc_base_object(type,count);if(result->object&&result->object->data)memset(result->object->data,0,count*sizeof(ev_value));eri_native_gc_safe_point(NULL,NULL);return result;}
ev_value *evn_member(ev_value *value,int field){ev_value *result=eri_gc_base_member(value,field);eri_native_gc_safe_point(NULL,NULL);return result;}
ev_value *evn_index(ev_value *value,int64_t index){ev_value *result=eri_gc_base_index(value,index);eri_native_gc_safe_point(NULL,NULL);return result;}
ev_value *evn_count(ev_value *value){ev_value *result=eri_gc_base_count(value);eri_native_gc_safe_point(NULL,NULL);return result;}
void evn_add(ev_value *target,ev_value *value){eri_gc_base_add(target,value);eri_native_gc_safe_point(target,NULL);}
ev_value *evn_wrap(int type,ev_value *value){ev_value *result=eri_gc_base_wrap(type,value);eri_native_gc_safe_point(NULL,NULL);return result;}
ev_value *evn_none(int type){ev_value *result=eri_gc_base_none(type);eri_native_gc_safe_point(NULL,NULL);return result;}
ev_value *evn_get(ev_value *value){ev_value *result=eri_gc_base_get(value);eri_native_gc_safe_point(NULL,NULL);return result;}
ev_value *evn_view(int type,ev_value *value){ev_value *result=eri_gc_base_view(type,value);eri_native_gc_safe_point(NULL,NULL);return result;}
ev_value *evn_builtin0(const char *name,int type){ev_value *result=eri_gc_base_builtin0(name,type);eri_native_gc_safe_point(NULL,NULL);return result;}
ev_value *evn_builtin1(const char *name,int type,ev_value *first){ev_value *result=eri_gc_base_builtin1(name,type,first);eri_native_gc_safe_point(NULL,NULL);return result;}
ev_value *evn_builtin2(const char *name,int type,ev_value *first,ev_value *second){ev_value *result=eri_gc_base_builtin2(name,type,first,second);eri_native_gc_safe_point(NULL,NULL);return result;}
eri_handler_frame *evn_frame(void){eri_handler_frame *result=eri_gc_base_frame();eri_native_gc_safe_point(NULL,NULL);return result;}
void evn_pop(eri_handler_frame *frame){eri_gc_base_pop(frame);eri_native_gc_safe_point(NULL,NULL);}
ev_value *evn_error(eri_failure_value *failure,int type){ev_value *result=eri_gc_base_error(failure,type);eri_native_gc_safe_point(NULL,NULL);return result;}
