/* Acceptance-only observer for disposable Linux x86-64 output assembly.
 * No allocation, no GC roots, and no change to production allocator/GC policy.
 * Capacity is read from successful allocations, never inferred from field counts.
 */
#include <stdint.h>
#include <stddef.h>
typedef uint64_t U;
#define MAP_SIZE (1u << 19)
#define MAX_IDS 512
#define TAGS 64
#define CATS 11
#ifndef OUTPUT_FD
#error OUTPUT_FD is required
#endif
enum { MASK_LIST=1, WORD_BODY, WORD_IDENTITY, MASK_ACCESS, CLASSES,
       FLOW_BODY, FLOW_WRAPPER, SHARED_TABLES, OTHER_VERIFY, SHARED_RUNTIME };
struct Stat { U allocations, traffic, live, peak, frees, freed, failures, reserved; };
struct Meta { U pass, kind, function, r, b, w, n; };
struct Record {
    U magic, event, id, pass, kind, function, r, b, w, n, sequence, errors;
    U total_live, total_peak, map_live, max_probe;
    U semantic[CATS][2]; /* actual capacity bytes / distinct graph allocations */
    struct Stat stats[TAGS];
};
_Static_assert(sizeof(struct Record)==4400,"observer record ABI");
_Static_assert(sizeof(struct Stat)==64,"observer stat ABI");
struct Type { int32_t kind, inner; U name, fields, descriptor; };
extern struct Type ev_types[];
extern void *erist_rt_graph_find(void *);
/* Hook-visible observer state. None of these pointer arrays is a runtime root. */
U st_active, st_sid, st_category, st_kind, st_tracked_live;
static U keys[MAP_SIZE], tags[MAP_SIZE], sizes[MAP_SIZE], seen[MAP_SIZE];
static struct Stat stats[MAX_IDS*TAGS];
static struct Meta meta[MAX_IDS];
static U next_id, pass_id, sequence, errors, max_probe, semantic_epoch;
static struct Record record;

static long write_fd(const void *p, U n) {
    long r;
    __asm__ volatile("syscall" : "=a"(r) : "a"(1L), "D"((long)OUTPUT_FD),
                     "S"(p), "d"(n) : "rcx", "r11", "memory");
    return r;
}
static void write_record(void) {
    const char *p=(const char *)&record; U n=sizeof(record);
    while(n) { long r=write_fd(p,n); if(r==-4)continue; if(r<=0) {
        __asm__ volatile("syscall"::"a"(60L),"D"(126L):"rcx","r11","memory");
        __builtin_unreachable();
    } p+=r; n-=(U)r; }
}
static void emit(U event,U id) {
    struct Meta *m=&meta[id];
    record.magic=0x53544f5241474531ULL; record.event=event; record.id=id;
    record.pass=m->pass; record.kind=m->kind; record.function=m->function;
    record.r=m->r; record.b=m->b; record.w=m->w; record.n=m->n;
    record.sequence=++sequence; record.errors=errors;
    record.total_live=stats[0].live; record.total_peak=stats[0].peak;
    record.map_live=st_tracked_live; record.max_probe=max_probe;
    for(U i=0;i<TAGS;i++)record.stats[i]=stats[id*TAGS+i];
    write_record();
}
static void clear_semantic(void) {
    for(U i=0;i<CATS;i++)for(U j=0;j<2;j++)record.semantic[i][j]=0;
}
static void fail_at(U line) {
    errors=line; clear_semantic(); emit(99,st_sid);
    __asm__ volatile("syscall"::"a"(60L),"D"(125L):"rcx","r11","memory");
    __builtin_unreachable();
}
#define fail() fail_at(__LINE__)
static U mix(U p) { p>>=4; p^=p>>30; p*=0xbf58476d1ce4e5b9ULL;
    p^=p>>27; p*=0x94d049bb133111ebULL; return (p^(p>>31))&(MAP_SIZE-1); }
static U locate(U p,int insert) {
    U at=mix(p), hole=MAP_SIZE;
    for(U n=1;n<=MAP_SIZE;n++,at=(at+1)&(MAP_SIZE-1)) {
        if(n>max_probe)max_probe=n;
        if(keys[at]==p)return at;
        if(keys[at]==1 && hole==MAP_SIZE)hole=at;
        if(keys[at]==0)return insert?(hole==MAP_SIZE?at:hole):MAP_SIZE;
    } fail(); return MAP_SIZE;
}
static void add(struct Stat *s,U size) {
    ++s->allocations; s->traffic+=size; s->live+=size;
    if(s->live>s->peak)s->peak=s->live;
    if(s->live>s->traffic)fail();
}
static void drop(struct Stat *s,U size) {
    if(s->live<size)fail(); s->live-=size; ++s->frees; s->freed+=size;
}
void st_allocated(void *pointer) {
    if(!st_active)return;
    U tag=st_sid*TAGS+st_category*3+st_kind;
    if(!st_category || st_category>=CATS || st_kind>2 || tag>=MAX_IDS*TAGS)fail();
    if(!pointer) { ++stats[tag].failures; ++stats[0].failures; return; }
    if(st_tracked_live>=MAP_SIZE*3/4)fail();
    U p=(U)pointer, at=locate(p,1);
    if(keys[at]==p)fail();
    U capacity=(((U *)pointer)[-4]&~15ULL)+32;
    if(capacity<48 || capacity&15)fail();
    keys[at]=p; tags[at]=tag; sizes[at]=capacity; seen[at]=0;
    ++st_tracked_live; add(&stats[tag],capacity); add(&stats[0],capacity);
    if(st_sid)add(&stats[st_sid*TAGS],capacity);
}
void st_freed(void *pointer) {
    if(!pointer || !st_tracked_live)return;
    U at=locate((U)pointer,0); if(at==MAP_SIZE)return;
    drop(&stats[tags[at]],sizes[at]); drop(&stats[0],sizes[at]);
    U owner=tags[at]/TAGS; if(owner)drop(&stats[owner*TAGS],sizes[at]);
    keys[at]=1; tags[at]=0; sizes[at]=0; seen[at]=0; --st_tracked_live;
}
/* Derive semantic categories from the emitted descriptor table, not guessed IDs. */
static U descriptor_category(U type) {
    if(type==WORD_TYPE)return WORD_BODY;
    if(type==WORD_ID_TYPE)return WORD_IDENTITY;
    if(type==MASK_LIST_TYPE)return MASK_LIST;
    if(type==FLOW_TYPE)return FLOW_BODY;
    if(type==FLOW_ID_TYPE || type==FLOW_MAYBE_TYPE)return FLOW_WRAPPER;
    if(type==INT_LIST_TYPE && meta[st_sid].kind==2)return CLASSES;
    return st_category;
}
void st_select_type(U type) { st_category=descriptor_category(type); }
void st_select_value(const U *cell) { if(cell)st_category=descriptor_category(cell[0]); }
void st_select_graph(void) { st_kind=1; }
void st_select_slot(void) { st_kind=2; }
void st_select_shared(void) { st_sid=0; st_category=SHARED_RUNTIME; }

static U *graph(U p) {
    if(!p || erist_rt_graph_find((void *)p)!=(void *)p)fail();
    return (U *)p;
}
static void include(U p) {
    U at=locate(p,0); if(at==MAP_SIZE || (tags[at]%TAGS)%3!=1)fail();
    if(tags[at]/TAGS!=st_sid)fail();
    if(seen[at]==semantic_epoch)return;
    seen[at]=semantic_epoch;
    U cat=(tags[at]%TAGS)/3;
    record.semantic[cat][0]+=sizes[at]; ++record.semantic[cat][1];
}
/* Follow only backing ownership, never arbitrary graph fields. */
static U *owned_graph(U p) {
    U *g=graph(p), *current=g;
    for(U depth=0;;depth++) {
        if(depth>8)fail(); include((U)current);
        if(!current[7])break;
        current=graph(current[7]);
    } return g;
}
static U *record_cell(const U *cell,U wanted,int own) {
    for(U depth=0;depth<8;depth++) {
        U type=cell[0]; if(type>TYPE_MAX)fail();
        int kind=ev_types[type].kind;
        if(kind==8 || kind==9) {
            if(!cell[1])return 0;
            U *g=own?owned_graph(cell[1]):graph(cell[1]);
            if(g[0]!=1 || !g[1])fail(); cell=(const U *)g[1];
        } else {
            if(type!=wanted || kind!=6)fail();
            U *g=own?owned_graph(cell[1]):graph(cell[1]);
            if(g[0]!=ev_types[type].fields || !g[1])fail(); return (U *)g[1];
        }
    } fail(); return 0;
}
static U *list(const U *cell,U type) {
    if(!cell || cell[0]!=type || ev_types[type].kind!=7)fail();
    U *g=owned_graph(cell[1]);
    if(g[0]>1000000 || (g[0] && !g[1]))fail(); return g;
}
void st_begin_verify(void) {
    if(st_active || next_id+1>=MAX_IDS)fail();
    st_active=1; st_sid=++next_id; st_category=SHARED_TABLES; st_kind=0;
    meta[st_sid].pass=++pass_id; meta[st_sid].kind=1; meta[st_sid].function=(U)-2;
}
void st_begin_routine(const U *routine) {
    if(!st_active || next_id+1>=MAX_IDS)fail();
    st_sid=++next_id; st_category=OTHER_VERIFY; st_kind=0;
    meta[st_sid].pass=pass_id; meta[st_sid].kind=2;
    U *body=record_cell(routine,FUNCTION_TYPE,0);
    /* Current emitted nominal fields are in reverse declaration order. */
    if(!body || body[5*4]!=1)fail(); meta[st_sid].function=body[5*4+1];
}
/* The three arguments are live source locals, copied read-only by an ASM hook. */
void st_snapshot(const U *classes,const U *masks,const U *flows,U event) {
    if(!st_active || !st_sid || meta[st_sid].kind!=2)fail();
    clear_semantic(); if(++semantic_epoch==0)fail();
    U *c=list(classes,INT_LIST_TYPE); U r=c[0];
    U *m=list(masks,MASK_LIST_TYPE); U n=m[0];
    const U *items=(const U *)m[1];
    for(U i=0;i<n;i++) {
        if(items[i*4]!=WORD_ID_TYPE)fail();
        U *word=record_cell(items+i*4,WORD_TYPE,1);
        if(!word || word[0]!=1)fail();
    }
    U b=0; const U *cursor=flows;
    while(cursor) {
        U *f=record_cell(cursor,FLOW_TYPE,1); if(!f)break;
        if(++b>1000000)fail();
        /* Include cached successor wrappers, but do not recurse into the CFG. */
        (void)record_cell(f+2*4,FLOW_TYPE,1);
        (void)record_cell(f+1*4,FLOW_TYPE,1);
        cursor=f;
    }
    U words=(r+61)/62;
    if(n!=(2*b+1)*words || !b)fail();
    struct Meta *me=&meta[st_sid];me->r=r;me->b=b;me->w=words;me->n=n;
    if(record.semantic[WORD_IDENTITY][1]!=n || record.semantic[WORD_BODY][1]!=n)fail();
    emit(event,st_sid);
}
void st_end_verify(void) { clear_semantic(); emit(3,st_sid); }
void st_dump_all(U event) {
    clear_semantic();
    for(U id=0;id<=next_id;id++)emit(event,id);
}
