/* Exercise runtime administration independently of persistent value buffers. */
#include <assert.h>
#include <stdlib.h>
#include <stddef.h>
#include <string.h>
static size_t live_allocations;
static void *counted_malloc(size_t size) {
    void *result=malloc(size);
    if(result)live_allocations++;
    return result;
}
static void counted_free(void *pointer) {
    if(pointer){assert(live_allocations);live_allocations--;}
    free(pointer);
}
#define malloc counted_malloc
#define free counted_free
#define ERIST_NATIVE_RUNTIME
#define main runtime_entry_main
#include "runtime/value_runtime.c"
#undef main
#undef malloc
#undef free
const ev_type ev_types[]={{0,0,NULL,0,NULL}};
ev_value *erist_entry(void){return NULL;}

static void normal_frames(void) {
    ev_scope *scope=ev_scope_enter();
    ev_value *caller=evn_int(7);
    size_t baseline=live_allocations;
    for(int i=0;i<10000;i++){
        eri_handler_frame *outer=evn_frame();
        if(setjmp(outer->env)!=0)abort();
        (void)evn_frame();(void)evn_frame();
        /* A return across nested resources pops through the outermost frame. */
        evn_pop(outer);
        assert(!eri_handler_top);
        assert(live_allocations==baseline);
    }
    /* Normal pop must preserve values produced by a successful expression. */
    eri_handler_frame *frame=evn_frame();
    if(setjmp(frame->env)!=0)abort();
    ev_value *result=evn_int(42);
    evn_pop(frame);
    assert(result->i==42 && caller->i==7);
    ev_scope_leave(scope,ev_void());
    assert(live_allocations==0);
}

static void failed_calls(void) {
    ev_scope *scope=ev_scope_enter();
    ev_value *caller=evn_int(7);
    ev_slot_node *mark=ev_slots;
    size_t baseline=live_allocations;
    for(volatile int i=0;i<10000;i++){
        eri_handler_frame *frame=evn_frame();
        if(setjmp(frame->env)==0){
            (void)evn_int(10); /* protected expression temporary */
            (void)ev_scope_enter();
            for(int j=0;j<8;j++)(void)evn_int(j);
            (void)ev_scope_enter();
            *caller=ev_int(i); /* caller state survives checked unwinding */
            eri_raise("Expected",NULL,(eri_text){0,NULL});
            abort();
        }
        evn_pop(frame);
        assert(!eri_handler_top && ev_scopes==scope && ev_slots==mark);
        assert(caller->i==i && live_allocations==baseline);
    }
    ev_scope_leave(scope,ev_void());
    assert(live_allocations==0);
}

static void resource_unwind(void) {
    ev_scope *scope=ev_scope_enter();
    static eri_file file;file.handle=tmpfile();assert(file.handle);
    ev_value resource={.type=6,.resource=&file};
    size_t baseline=live_allocations;
    eri_handler_frame *outer=evn_frame();
    if(setjmp(outer->env)==0){
        eri_handler_frame *inner=evn_frame();
        if(setjmp(inner->env)==0){
            (void)ev_scope_enter();(void)evn_int(9);
            eri_raise("Expected",NULL,(eri_text){0,NULL});
            abort();
        }
        evn_unwind(&resource,inner);
        abort();
    }
    evn_pop(outer);
    assert(file.closed && !file.handle && !eri_handler_top);
    assert(ev_scopes==scope && !ev_slots && live_allocations==baseline);
    /* Normal resource completion releases its frame too. */
    eri_handler_frame *normal=evn_frame();
    if(setjmp(normal->env)!=0)abort();
    evn_cleanup_normal(&resource,normal);
    assert(live_allocations==baseline && !eri_handler_top);
    ev_scope_leave(scope,ev_void());
    assert(live_allocations==0);
}

int main(int argc,char **argv) {
    assert(argc==2);
    if(strcmp(argv[1],"normal")==0)normal_frames();
    else if(strcmp(argv[1],"failure")==0)failed_calls();
    else if(strcmp(argv[1],"resource")==0)resource_unwind();
    else abort();
    return 0;
}
