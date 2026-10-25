#include <assert.h>
#define ERIST_NATIVE_RUNTIME
#define ERIST_SLOT_GC_INTERVAL 1
#define ERIST_HEAP_GC_INTERVAL 1
#define main runtime_application_main
#include "runtime/native_gc_runtime.c"
#undef main

static const int box_fields[]={4};
static const int node_fields[]={7};
static const int error_fields[]={4,1};
const ev_type ev_types[]={
    {0,0,"",0,NULL},{1,0,"Int",0,NULL},{2,0,"Float",0,NULL},
    {3,0,"Bool",0,NULL},{4,0,"Text",0,NULL},{5,0,"void",0,NULL},
    {6,0,"Node",1,node_fields},
    {9,6,"identity Node",0,NULL},
    {6,0,"Box",1,box_fields},
    {7,1,"List Int",0,NULL},
    {8,6,"maybe Node",0,NULL},
    {6,0,"Expected",2,error_fields},
    {11,0,"Error",1,NULL},
    {12,4,"bytes",0,NULL}
};
ev_value *erist_entry(void){return NULL;}

static size_t prefix_nodes(void){
    size_t result=0;
    for(size_t bucket=0;bucket<sizeof(eri_text_append_buckets)/sizeof(eri_text_append_buckets[0]);bucket++)
        for(eri_text_append_buffer *cursor=eri_text_append_buckets[bucket];cursor;cursor=cursor->next)result++;
    return result;
}

static void clear_slots(void){
    ev_collect_slots();
    eri_native_heap_collect();
}

static void reachable_values_and_weak_prefixes(void){
    ev_scope *scope=evn_scope_enter();
    uintptr_t roots[5]={0};
    unsigned char classes[5]={1,1,1,1,5};
    evn_bind_roots(scope,roots,classes,5);

    ev_value *box=evn_object(8,1);roots[0]=(uintptr_t)box;
    ev_value *message=evn_text((const unsigned char*)"alive",5);roots[1]=(uintptr_t)message;
    evn_init(box,0,message);
    eri_native_heap_collect();
    assert(box->object->data[0].text.len==5);
    assert(memcmp(box->object->data[0].text.data,"alive",5)==0);

    ev_value *first=evn_text((const unsigned char*)"a",1);roots[1]=(uintptr_t)first;
    ev_value *second=evn_text((const unsigned char*)"b",1);roots[2]=(uintptr_t)second;
    ev_value *joined=evn_binary(0,first,second);roots[3]=(uintptr_t)joined;
    assert(joined->text.len==2&&memcmp(joined->text.data,"ab",2)==0);
    assert(prefix_nodes()>0);
    roots[1]=roots[2]=0;
    clear_slots();
    assert(joined->text.len==2&&memcmp(joined->text.data,"ab",2)==0);
    assert(prefix_nodes()>0);

    roots[3]=0;
    clear_slots();
    assert(prefix_nodes()==0);

    ev_scope_leave(scope,ev_void());
    eri_native_heap_collect();
}

static void list_maybe_and_text_view_survive_collection(void){
    ev_scope *scope=evn_scope_enter();
    uintptr_t roots[4]={0};unsigned char classes[4]={1,1,1,1};
    evn_bind_roots(scope,roots,classes,4);

    ev_value *list=evn_object(9,2);roots[0]=(uintptr_t)list;
    ev_value *one=evn_int(1);roots[1]=(uintptr_t)one;
    ev_value *two=evn_int(2);roots[2]=(uintptr_t)two;
    evn_init(list,0,one);evn_init(list,1,two);
    roots[1]=roots[2]=0;
    clear_slots();
    assert(list->object->count==2);
    assert(list->object->data[0].i==1&&list->object->data[1].i==2);

    ev_value *node=evn_object(6,1);roots[1]=(uintptr_t)node;
    ev_value *identity=evn_wrap(7,node);roots[2]=(uintptr_t)identity;
    evn_init(node,0,identity);
    ev_value *optional=evn_wrap(10,node);roots[3]=(uintptr_t)optional;
    roots[1]=roots[2]=0;
    clear_slots();
    assert(optional->object&&optional->object->data[0].type==6);
    assert(optional->object->data[0].object->data[0].type==7);

    roots[0]=roots[3]=0;
    clear_slots();

    ev_value *text=evn_text((const unsigned char*)"view",4);roots[0]=(uintptr_t)text;
    ev_value *view=evn_view(13,text);roots[1]=(uintptr_t)view;
    roots[0]=0;
    clear_slots();
    assert(view->view.text.len==4);
    assert(memcmp(view->view.text.data,"view",4)==0);

    roots[1]=0;
    clear_slots();
    ev_scope_leave(scope,ev_void());
    eri_native_heap_collect();
}

static void unreachable_identity_cycle(void){
    ev_scope *scope=evn_scope_enter();
    uintptr_t roots[2]={0};unsigned char classes[2]={1,1};
    evn_bind_roots(scope,roots,classes,2);
    size_t baseline=eri_native_heap_live_blocks();

    ev_value *node=evn_object(6,1);roots[0]=(uintptr_t)node;
    ev_value *identity=evn_wrap(7,node);roots[1]=(uintptr_t)identity;
    evn_init(node,0,identity);
    eri_native_heap_collect();
    size_t with_cycle=eri_native_heap_live_blocks();
    assert(with_cycle>baseline);

    roots[0]=roots[1]=0;
    clear_slots();
    assert(eri_native_heap_live_blocks()<with_cycle);

    ev_scope_leave(scope,ev_void());
    eri_native_heap_collect();
}

static void saved_failure_survives_collection(void){
    ev_scope *scope=evn_scope_enter();
    uintptr_t roots[4]={0};unsigned char classes[4]={1,1,1,5};
    evn_bind_roots(scope,roots,classes,4);

    ev_value *error=evn_object(11,2);roots[0]=(uintptr_t)error;
    ev_value *message=evn_text((const unsigned char*)"expected",8);roots[1]=(uintptr_t)message;
    ev_value *number=evn_int(42);roots[2]=(uintptr_t)number;
    evn_init(error,0,message);evn_init(error,1,number);

    eri_handler_frame *frame=evn_frame();
    if(setjmp(frame->env)==0){evn_fail(error,0);abort();}
    evn_pop(frame);
    eri_failure_value *saved=evn_saved();roots[3]=(uintptr_t)saved;
    ev_value *caught=evn_error(saved,11);roots[0]=(uintptr_t)caught;
    eri_native_heap_collect();
    assert(caught->object->data[0].text.len==8);
    assert(caught->object->data[1].i==42);

    roots[0]=roots[1]=roots[2]=roots[3]=0;
    eri_failure=(eri_failure_value){0};
    clear_slots();
    ev_scope_leave(scope,ev_void());
    eri_native_heap_collect();
}

static void long_running_allocation_plateaus(void){
    ev_scope *scope=evn_scope_enter();
    uintptr_t roots[1]={0};unsigned char classes[1]={1};
    evn_bind_roots(scope,roots,classes,1);
    size_t start_reclaimed=eri_native_heap_reclaimed_blocks();
    for(int i=0;i<10000;i++){
        ev_value *text=evn_text((const unsigned char*)"temporary",9);
        (void)text;
        ev_value *object=evn_object(8,1);
        (void)object;
    }
    clear_slots();
    assert(eri_native_heap_collections()>1000);
    assert(eri_native_heap_reclaimed_blocks()>start_reclaimed+10000);
    assert(eri_native_heap_live_bytes()<65536);
    assert(eri_native_heap_peak_bytes()<262144);
    ev_scope_leave(scope,ev_void());
    eri_native_heap_collect();
}

int main(void){
    reachable_values_and_weak_prefixes();
    list_maybe_and_text_view_survive_collection();
    unreachable_identity_cycle();
    saved_failure_survives_collection();
    long_running_allocation_plateaus();
    eri_failure=(eri_failure_value){0};
    eri_native_heap_collect();
    assert(eri_native_heap_live_blocks()==0);
    assert(eri_native_heap_live_bytes()==0);
    assert(prefix_nodes()==0);
    return 0;
}
