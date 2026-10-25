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
    {12,4,"bytes",0,NULL},
    {10,0,"std.files.File",0,NULL}
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

static void shared_snapshot_tracing_is_linear(void){
    enum {COUNT=1000};
    ev_value *data=eri_alloc_kind(COUNT*sizeof(*data),ERI_HEAP_OBJECT_DATA);
    for(size_t i=0;i<COUNT;i++)data[i]=ev_text(eri_text_from_cstr("alive"));
    /* Discover successively longer snapshots, then repeat shorter ones. The
       backing storage must expose every live tail without quadratic visits. */
    eri_native_gc_value_queue queue={0};
    for(size_t i=1;i<=COUNT;i++){
        ev_object snapshot={i,data};
        eri_native_gc_mark_object(&snapshot,&queue);
    }
    assert(queue.count==COUNT);
    for(size_t i=COUNT;i>0;i--){
        ev_object snapshot={i,data};
        eri_native_gc_mark_object(&snapshot,&queue);
    }
    assert(queue.count==COUNT);
    for(size_t i=0;i<queue.count;i++)eri_native_gc_mark_value(queue.items[i],&queue);
    eri_native_gc_sweep();
    for(size_t i=0;i<COUNT;i++)assert(data[i].text.len==5&&memcmp(data[i].text.data,"alive",5)==0);
    free(queue.items);
    /* The visited-prefix state must reset for the next collection. */
    queue=(eri_native_gc_value_queue){0};
    ev_object whole={COUNT,data};
    eri_native_gc_mark_object(&whole,&queue);
    assert(queue.count==COUNT);
    free(queue.items);
    eri_native_heap_collect();
    assert(eri_native_heap_live_blocks()==0);
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

static void interior_value_roots_survive_collection(void){
    ev_scope *scope=evn_scope_enter();
    uintptr_t roots[2]={0};unsigned char classes[2]={1,1};
    evn_bind_roots(scope,roots,classes,2);

    ev_value *box=evn_object(8,1);roots[0]=(uintptr_t)box;
    ev_value *text=evn_text((const unsigned char*)"interior",8);roots[1]=(uintptr_t)text;
    evn_init(box,0,text);
    ev_value *field=evn_member_ref(box,0);
    roots[0]=0;roots[1]=(uintptr_t)field;
    ev_collect_slots();
    eri_native_heap_collect();
    assert(field->type==4&&field->text.len==8);
    assert(memcmp(field->text.data,"interior",8)==0);

    roots[1]=0;
    eri_native_heap_collect();

    ev_value *list=evn_object(9,2);roots[0]=(uintptr_t)list;
    ev_value *one=evn_int(17);roots[1]=(uintptr_t)one;evn_init(list,0,one);
    ev_value *two=evn_int(23);roots[1]=(uintptr_t)two;evn_init(list,1,two);
    ev_value *element=evn_index_ref(list,1);
    roots[0]=0;roots[1]=(uintptr_t)element;
    ev_collect_slots();
    eri_native_heap_collect();
    assert(element->type==1&&element->i==23);

    roots[1]=0;
    eri_native_heap_collect();
    ev_scope_leave(scope,ev_void());
    eri_native_heap_collect();
}

static void file_resource_survives_collection(void){
    ev_scope *scope=evn_scope_enter();
    uintptr_t roots[2]={0};unsigned char classes[2]={1,1};
    evn_bind_roots(scope,roots,classes,2);

    const char *path_name="/tmp/eristavi-native-heap-gc-resource.tmp";
    remove(path_name);
    ev_value *path=evn_text((const unsigned char*)path_name,strlen(path_name));roots[0]=(uintptr_t)path;
    ev_value *resource=evn_builtin1("std.files.create",14,path);roots[1]=(uintptr_t)resource;
    roots[0]=0;
    clear_slots();
    assert(resource->resource);
    assert(resource->resource->path.len==strlen(path_name));
    assert(memcmp(resource->resource->path.data,path_name,strlen(path_name))==0);
    assert(resource->resource->c_path);

    eri_failure_value cleanup={0};
    evn_cleanup_accumulate(resource,&cleanup);
    assert(!cleanup.type);
    assert(remove(path_name)==0);

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

static void scalar_administration_does_not_rescan_managed_heap(void){
    ev_scope *scope=evn_scope_enter();
    uintptr_t roots[1]={0};unsigned char classes[1]={1};
    evn_bind_roots(scope,roots,classes,1);
    ev_value *text=evn_text((const unsigned char*)"retained",8);
    roots[0]=(uintptr_t)text;
    eri_native_heap_collect();
    size_t collections=eri_native_heap_collections();
    size_t managed_blocks=eri_native_heap_live_blocks();
    for(int i=0;i<10000;i++){
        eri_handler_frame *frame=evn_frame();
        evn_int(i);
        evn_pop(frame);
        ev_scope *inner=evn_scope_enter();
        evn_bind_roots(inner,roots,classes,1);
        evn_scope_leave(inner,text);
    }
    assert(eri_native_heap_collections()==collections);
    assert(eri_native_heap_live_blocks()==managed_blocks);
    assert(text->text.len==8&&memcmp(text->text.data,"retained",8)==0);
    assert(eri_native_heap_live_bytes()<65536);
    /* Managed allocation must still trigger the interval-one collector. */
    evn_text((const unsigned char*)"transient",9);
    assert(eri_native_heap_collections()>collections);
    roots[0]=0;
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
    shared_snapshot_tracing_is_linear();
    reachable_values_and_weak_prefixes();
    list_maybe_and_text_view_survive_collection();
    interior_value_roots_survive_collection();
    file_resource_survives_collection();
    unreachable_identity_cycle();
    saved_failure_survives_collection();
    scalar_administration_does_not_rescan_managed_heap();
    long_running_allocation_plateaus();
    eri_failure=(eri_failure_value){0};
    eri_native_heap_collect();
    assert(eri_native_heap_live_blocks()==0);
    assert(eri_native_heap_live_bytes()==0);
    assert(prefix_nodes()==0);
    return 0;
}
