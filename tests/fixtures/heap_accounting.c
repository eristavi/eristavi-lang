#include <assert.h>
#include <stdalign.h>
#define ERIST_NATIVE_RUNTIME
#define main runtime_application_main
#include "runtime/value_runtime.c"
#undef main

static const int record_fields[]={1},error_fields[]={4,1};
const ev_type ev_types[]={
    {0,0,"",0,NULL},{1,0,"Int",0,NULL},{2,0,"Float",0,NULL},
    {3,0,"Bool",0,NULL},{4,0,"Text",0,NULL},{5,0,"void",0,NULL},
    {6,0,"Record",1,record_fields},{7,1,"List",0,NULL},{10,0,"Expected",2,error_fields}
};
ev_value *erist_entry(void){return NULL;}

/* Test teardown only: every application value is dead here. This is not GC. */
static void finish(void){
    memset(eri_text_append_buckets,0,sizeof(eri_text_append_buckets));
    eri_failure=(eri_failure_value){0};
    while(eri_heap_blocks)eri_free(eri_heap_blocks+1);
    assert(eri_heap_check() && eri_heap_total.live_allocations==0 && eri_heap_total.live_bytes==0);
    eri_heap_write_stats(stdout);
}
static void accounting(void){
    unsigned char *a=eri_alloc_kind(8,ERI_HEAP_TEXT),*b=eri_alloc_kind(16,ERI_HEAP_OBJECT_DATA);
    unsigned char *zero=eri_alloc(0),*d=eri_realloc_kind(NULL,3,ERI_HEAP_OBJECT_DATA);
    assert((uintptr_t)a%alignof(max_align_t)==0 && (uintptr_t)b%alignof(max_align_t)==0);
    memset(a,7,8);memset(b,9,16);zero[0]=0;
    a=eri_realloc(a,4096);assert(a[0]==7 && a[7]==7 && eri_heap_check());
    b=eri_realloc(b,4);assert(b[0]==9 && b[3]==9 && eri_heap_check());
    zero=eri_realloc(zero,0);zero[0]=1;assert(eri_heap_check());
    assert(eri_heap_total.live_bytes==4103 && eri_heap_total.requested_bytes==4127);
    assert(eri_heap_categories[ERI_HEAP_TEXT].live_bytes==4096);
    assert(eri_heap_categories[ERI_HEAP_OBJECT_DATA].live_bytes==7);
    eri_heap_write_stats(stdout);
    eri_free(NULL);eri_free(b);eri_free(a);eri_free(zero);eri_free(d);
    assert(eri_heap_total.allocations==4 && eri_heap_total.reallocations==3 && eri_heap_total.frees==4);
    finish();
}
static void batch(void){
    ev_scope *scope=ev_scope_enter();
    for(volatile int i=0;i<100;i++){
        ev_value record=ev_object_value(6,1);record.object->data[0]=ev_int(i);
        ev_value list=ev_object_value(7,1);list.object->data[0]=record.object->data[0];
        ev_value snapshot=list;ev_add(&list,ev_int(42));
        assert(snapshot.object->count==1 && snapshot.object->data[0].i==i && list.object->count==2);
        eri_text before=eri_text_from_cstr("a"),after=eri_text_add(before,eri_text_from_cstr("b"));
        assert(before.len==1 && before.data[0]=='a' && after.len==2);
        eri_text normalized=eri_unicode_normalizeNfc(eri_text_from_cstr("e\xcc\x81"));
        assert(normalized.len==2);
        ev_value error=ev_object_value(8,2);error.object->data[0]=ev_text(before);error.object->data[1]=ev_int(i);
        eri_handler_frame *frame=evn_frame();
        if(setjmp(frame->env)==0){ev_fail_message(error,0);abort();}
        evn_pop(frame);
        eri_failure_value *saved=evn_saved();ev_value *caught=evn_error(saved,8);
        assert(caught->object->data[1].i==i);
        eri_attach_secondary(saved,(eri_failure_value){"cleanup",NULL,after,NULL});
        assert(saved->secondary && saved->secondary->message.len==2);
    }
    ev_scope_leave(scope,ev_void());
    assert(eri_heap_check());
    assert(eri_heap_categories[ERI_HEAP_SLOT].live_allocations==0);
    assert(eri_heap_categories[ERI_HEAP_SCOPE].live_allocations==0);
    assert(eri_heap_categories[ERI_HEAP_HANDLER].live_allocations==0);
    assert(eri_heap_categories[ERI_HEAP_UNICODE].live_allocations==0);
    eri_heap_write_stats(stdout);
}
int main(int argc,char **argv){
    assert(argc==2);
    if(strcmp(argv[1],"accounting")==0)accounting();
    else if(strcmp(argv[1],"stress")==0){batch();batch();finish();}
    else if(strcmp(argv[1],"overflow")==0)(void)eri_alloc_kind(SIZE_MAX,ERI_HEAP_TEXT);
    else if(strcmp(argv[1],"resize-overflow")==0)(void)eri_realloc(eri_alloc(8),SIZE_MAX);
    else abort();
    return 0;
}
