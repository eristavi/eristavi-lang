# Eristavi module loading, import resolution, and dependency architecture
Date: 2026-10-29
Status: Revised architecture and phased milestone plan agreed on 2026-10-29. Implementation and validation remain pending; numerical regression budgets remain provisional until the baseline is established. Filesystem decision FS-001 is explicitly separate and pending.
UIR linkage clarification: added during the pending UIR review. New UIR contract/version details and the separate generic-artifact gate below remain proposals until that review is agreed; the previously agreed M1 scope is unchanged.
Baseline: PR 57 head 8af0ffe3350c737550c3ab0e6c3fa89f60f6f091, confirmed unchanged during this review.

## Recommendation
Long-term direction: one request-scoped owner for immutable inputs and explicitly owned stage results, a module/dependency graph, compatible module-contract views, and stage-specific caching. This is an architectural map, not one implementation milestone. Do not share mutable analyzers or live inference state as a shortcut to session reuse.

Preserve Eristavi's current module language. Improve processing, identity, validation, and invalidation without introducing new import syntax or reopening source semantics. Separate the compiler's consumption of resolved dependencies from future package fetching/version resolution.

## 0. Scope and milestone boundaries
The earlier nine-item summary grouped independent workstreams too broadly. The first milestone is limited to input reuse and cache correctness, with two independently reviewable slices:

| Slice | Included work | Explicit boundaries |
|---|---|---|
| M0: baseline | Fixed benchmark fixture, action/read/parse counters, cold/warm measurements | Measurement plan only until implementation is authorized |
| M1a: cache correctness | Compiler implementation fingerprint; validated hits; complete-generation publication; regression coverage | Retain existing interface/object formats and module language; no session refactor required |
| M1b: immutable input reuse | One snapshot/parse per module revision within a request; pass those inputs to import discovery, checking, and object production | Mutable semantic work remains stage/attempt-owned; no global analyzer cache, parallel scheduler, or persistent daemon |
| M2: graph/lookup representation | Dense ModuleIds, explicit edges, optional lookup/metadata indices | Separate change; profile lookup time, visit counts, and scaling before prioritizing performance work |
| M3: filesystem adapter | Centralize host path operations while preserving accepted behavior | Separate change; symlink containment tightening is excluded and requires FS-001 |
| Later contract adapters | Unify read access to already existing contracts where useful | A minimal adapter need not wait for UIR, but it does not block M1 |
| UIR-dependent work (original item 8) | Redesign serialized implementation material and generic body templates | Concrete implementation artifacts wait for agreed typed UIR contracts. New generic-template artifacts additionally wait for their separate artifact/profile design. Preserve existing adapters; neither blocks M1 |

The original summary's items 1, 3, and 5 define M1's broad theme; they must not turn M1 into an all-at-once shared-state rewrite. Full action-index/CAS separation, fine-grained dependencies, concurrency, package resolution, and native artifact redesign are later work. M1a can use immutable generation directories and a committed manifest without implementing a general-purpose storage service.

## 1. Current strengths to retain
One .eri file is one module, with logical identity derived from its source-root-relative path. Imports use dotted names, optionally aliased; public visibility controls imported access. Modules are private by default. The std root is reserved. Cyclic imports are compile-time errors. Imported modules are declaration-only and run no implicit initialization. An executable explicitly selects one entry source, with no required main function or filename.

The bootstrap already supports deterministic versioned interfaces, Universal-IR implementation artifacts, checking without dependency source, source-independent linking, reusable inferred-generic templates, and a basic incremental artifact cache. These behaviors have dedicated tests and must survive migration.

Third-party package root naming, dependency version resolution, and registry behavior are explicitly postponed in LANGUAGE_SEMANTICS.md. This proposal creates a boundary for those tools without implementing or freezing them now.

## 2. Concrete findings
| Finding | Code evidence | Consequence |
|---|---|---|
| Self-hosted module lookup scans a linked module chain | semantic_project.load | Repeated path comparisons as imports grow |
| Import/declaration lookup is linear; layout lookup recursively traverses imports | semantic_model.imported/declaration; semantic.layout | Repeated graph traversal; shared dependencies may be revisited |
| Loading, parsing, recursive dependency processing, and analysis are tightly coupled | semantic_project; project.ProjectCompiler | Harder to reuse intermediate results and define independent stage lifetimes |
| Bootstrap artifact misses create fresh project sessions repeatedly | build_cache._imports, compile_module, compile_module_object | Import discovery parses a file, then analysis and object production reopen/reprocess project inputs |
| Cache key omits compiler implementation identity | build_cache fingerprint fields | Changed compiler behavior can reuse an old result while artifact schemas remain unchanged |
| A cache hit only checks existence of two files | cached_interface.exists and cached_object.exists | Corrupt or mixed-generation cache entries can be copied as hits |
| Interface and implementation files are written separately | build_cache miss/publication paths | Interrupted/concurrent writes can expose incomplete pairs |
| Self-hosted path handling uses slash-specific Text routines; imported paths do not receive the same canonical containment check as the entry | semantic_project | Platform handling and root-policy enforcement need one defined implementation boundary |
| Generic artifact payloads currently embed source | object_artifact; direct_project._template_module | A source-independent build may still re-lex, parse, and analyze an embedded template |

These are source-level findings. No new runtime tests or performance benchmarks were run for this proposal. Existing phase times do not isolate the cost of module lookup or repeated analysis. The existence of linked scans is not evidence that they dominate compilation. Measure lookup counts, time, and graph-size scaling; preserve a simple implementation unless evidence warrants additional indices. Recursive repeated transitive searches are a separate scaling hypothesis, also requiring measurement.

## 3. Component boundaries
| Component | Responsibility |
|---|---|
| BuildRequest | Entry/library role, declared roots, target/profile, output request, cache policy |
| SourceManager | Immutable source bytes, SourceIds, content digests, source maps |
| ModuleRegistry | ModuleKeys, ModuleIds, provider selection, per-stage state |
| DependencyGraph | Ordered import edges, reverse edges, cycle paths, dependency scheduling |
| ModuleContract provider | Common read interface for source-generated, serialized, and standard-library contracts |
| Name tables | Import qualifiers and public export membership |
| ArtifactStore | Bounded decoding, integrity/compatibility checks, immutable artifact generations |
| BuildScheduler | Stage reuse, explicit inputs, invalidation, deterministic diagnostic commitment |
| Filesystem adapter | Host path representation, canonicalization, containment, atomic publication primitives |

Logical boundaries do not require an independently allocated object or runtime-polymorphic interface for every operation. Use direct internal calls and compact records where practical.

## 4. Identity
Separate logical identity, physical file location, and artifact content identity.

A ModuleKey is the declared root namespace plus an NFC-normalized, case-sensitive sequence of logical path segments. Today the namespaces are the configured project root and reserved standard-library provider. Future package bindings can provide additional namespaces under separately agreed rules.

A 32-bit ModuleId indexes a session-local dense registry; reserve zero and check exhaustion. ModuleIds, SymbolIds, and AST IDs are not serialized as permanent identities. Dense IDs primarily make ownership and references explicit; they are not a measured speedup and do not by themselves make processing deterministic. Determinism comes from specified traversal, serialization, and diagnostic rules.

Physical paths are used for I/O and diagnostic display. Host absolute checkout paths, timestamps, and module visitation order must not accidentally define portable nominal type identity or cache identity. Artifact records carry logical owner identities and remap serialized names/references into current-session IDs.

A module's source digest is an input revision, not its logical identity. A private edit must not rename every nominal type in that local module.

Different logical module names that happen to reach one physical file must not automatically be merged: canonical nominal identity depends on the logical owner. Initially process each distinct ModuleKey under the declared rules; sharing source bytes is an optional implementation detail and does not equate modules.

## 5. Resolution and filesystem policy
Resolve imports against declared roots/providers. Preserve current workspace-source preference and source-independent artifact fallback through a compatibility adapter. An explicit precompiled dependency binding chooses its pinned artifact generation, rather than whatever neighboring files happen to exist.

The filesystem adapter centralizes host path operations and preserves existing accepted resolution behavior during the infrastructure migration. Enforcing canonical containment for every imported symlink would change accepted projects and is not approved by accepting the infrastructure architecture. The proposed tightening is isolated in decision FS-001 below, with its own migration requirements.

Preserve NFC, case-sensitive logical names across hosts. Do not globally case-fold module IDs or blindly rewrite physical filenames to NFC. The long-term adapter needs defined canonical-equivalence and collision behavior. Any new rejection or resolution change is a separate compatibility policy, not an incidental M1 behavior change. A later portability check can flag module layouts that cannot be represented on another selected host filesystem, such as conflicting case-only names.

Handle Windows drive/UNC paths and host-specific separators in the adapter. These are host filesystem concerns; the CPU target selected for generated code does not determine how source files are opened.

Exact entry filename validity, unusual root-relative names, and legacy symlink edge cases must be covered by compatibility tests. Do not impose a new source identifier restriction on entry filenames incidentally.

## 6. Source snapshots and one session
Read each required source into one immutable byte snapshot per module revision. Hash and compile those same bytes. Reuse the parsed AST for import extraction, semantic analysis, interface generation, and implementation production. Helpers receive session/module handles instead of reopening files and starting new ProjectCompilers.

The request owner is a lifetime boundary and immutable-input registry. It is not a globally mutable Analyzer. Current Analyzer objects contain scopes, mutable TypeVars, specialization maps, expression facts, and visiting states; simply sharing them across stages is not safe. M1b reuses source/tokens/AST inputs first. A semantic result may be reused only through an immutable product with a defined complete context key; otherwise its analysis context remains exclusively owned by its stage attempt.

Use this stage-attempt state contract: absent -> running(attempt ID) -> ready(immutable result) on successful completion. A failure records a diagnostic for that attempt; cancellation records cancellation for that attempt. Neither is a ready result. Cleanup removes active ownership and dependency wait state. A later request or retry can execute the same key with a fresh attempt; an old failure/cancellation must not poison it.

Each attempt owns its builders, inference variables, scratch storage, temporary outputs, and locks. Generic template instantiation creates fresh caller-local inference variables; cached contracts cannot contain mutable unification state shared with a caller. Publish a ready product only after its required checks finish and its reachable mutable construction state is frozen, copied, or transferred exclusively.

Cancellation is checked at stage boundaries and bounded long-loop safe points. Once observed, stop starting dependent work; discard unfinished products and uncommitted generations; release locks and temporary storage on every exit path. Already committed valid cache generations remain valid. A cancelled generation cannot become visible through a late commit: check cancellation and attempt validity at the publication gate under the same ownership/commit guard. A commit that completed before cancellation remains a completed result.

Keep the initial scheduler serial and request-scoped. Dispose the request owner after success, failure, or cancellation. Cross-request retention of live semantic contexts and background execution are outside M1. Add fault-injection coverage for cancellation before/after each publication boundary, analysis failure after a dependency succeeds, retry after failure, and independent generic instantiations after an interrupted attempt.

At most one result is produced for a given stage and its full context key within a session. New generic type-argument specializations remain legitimate distinct work items.

An immutable snapshot guarantees consistency for that input. It does not claim that all project files were captured at one instant. A build publication policy may detect concurrent input changes and restart; regardless, emitted artifacts must describe the exact snapshots consumed, never a fingerprint from one read attached to output from another.

## 7. Graph and scheduling
Use dense module records and ordered contiguous import-edge ranges, with a ModuleKey-to-ModuleId exact lookup index and reverse dependencies. Each import edge retains its source span, target ModuleId, alias SymbolId, and source order. Repeated aliases/imports retain the language's existing validation behavior; do not silently collapse bindings.

Use an explicit DFS work stack and visiting/finished states for graph traversal. This supports deep graphs without relying on native recursive loading. Cycles report the full import chain and relevant edge locations.

Track per-stage states such as unrequested, active, ready, and failed. Do not conflate interface availability with verified implementation availability.

Separate discovery and semantic APIs. Define default module-layer diagnostic order operationally, following the owned source-loading path:
1. Preserve the selected command driver's setup-error order. On entering a source module, finish its read/UTF-8/lex/parse sequence before traversing any of its imports. An entry parse error therefore precedes errors in dependencies that its successfully parsed form would import.
2. Visit source import occurrences in textual order. Perform the existing edge-local checks at that occurrence, then recursively finish the dependency before considering the next import. A previously completed module is reused; an active module reached again reports the cycle at the closing edge.
3. After dependencies finish, run that module's semantic stages in their existing deterministic phase and traversal order. Preserve demand-driven callee checking. In the owned checker, the prepended declaration list means some type/function checks occur in reverse declaration order; M1 does not silently switch these to source order.
4. An artifact provider visits dependencies in its format-defined stored order (including the legacy interface's sorted order). Never use hash-map iteration order as a replacement. Retain this rule when source is unavailable.
5. Select the first error encountered by this serial reference traversal. Future ahead-of-order workers may compute results, but may commit a diagnostic only when earlier reference positions are known not to fail. No parallel diagnostic scheduling is part of M1.

This is depth-first dependency completion with explicit phase order, not a global sort by filename, source offset, or topological rank. The Python and owned implementations already differ on some duplicate-import and declaration-check ordering; preserve each migration path's baseline and record discrepancies as explicit compatibility decisions. Do not claim they already share identical error priority. The later semantic redesign may propose a new local order separately.

Required ordering fixtures include: an entry parse error after import text versus an imported semantic error; first dependency semantic failure versus second dependency parse failure; a shared failing dependency reached along two paths; duplicate qualifiers with a failing target; and two bad function declarations exercising the owned checker's reverse traversal.

Graph traversal is O(V+E), excluding parsing, semantic analysis, hashing, filesystem work, and expected hash-index costs. Body-dependent function result inference remains semantic work, not a reason to traverse imports again.

Future parallel execution may schedule independent work, but it must retain deterministic output/error ordering. Concurrency is not required for the initial replacement.

## 8. Name lookup and structural metadata
Use per-module alias SymbolId-to-ModuleId tables and export SymbolId-to-declaration/contract tables. Retain source-ordered arrays separately for diagnostics and deterministic emission.

Resolve an imported symbol through its qualifier and the target's public export table. Importing a module does not automatically expose its dependencies or private declarations. Preserve current resolution precedence, including module members whose names also occur on List or Text.

Replace recursive semantic.layout searches with a canonical structural-metadata registry keyed by the resolved nominal type identity. A direct metadata lookup may access compiler-visible private layout information needed to validate public contracts, without making that type or name source-addressable.

Do not repeatedly copy the full transitive structure map into each module analyzer. Register canonical entries once, verify duplicates for consistency, and reference them by identity. Public export visibility and compiler-required structural metadata are distinct views.

Lexical scopes, binding identity, type inference, failure checking, and resource semantics remain the next semantic-analysis design scope.

## 9. One contract interface, several providers
Source modules, serialized interfaces, and standard-library modules expose the same logical contract operations:
- export lookup and visibility;
- function parameter/result relationships and checked failures;
- nominal/error metadata, field order, fixed constraints, and dependency identities;
- compatibility/profile information.

A source provider derives contracts from semantic results. An artifact provider validates and decodes them. A standard-library provider supplies the pinned sysroot contract and target/runtime bindings. This replaces scattered special cases without implying every standard-library operation has an ordinary source implementation.

Check-only operations can use a valid interface without an implementation object. Executable linkage requires a compatible implementation. An interface-only module cannot become the executable entry.

Treat compiler-private storage access as part of the explicit build-capability context agreed earlier. Importing a specially named file cannot grant that capability.

## 10. Interfaces and implementations
Keep three distinct dependency-relevant products:
1. Contract metadata: what a consumer needs for semantic checking.
2. Implementation material: verified typed Universal IR and reusable specialization bodies.
3. Native products: target-specific machine objects and final links.

Canonical interface encoding includes all semantically required public relationships and reachable structural metadata. Exclude unrelated private definitions where safe, but never discard hidden structure needed for equality, fixed eligibility, resource checks, or public type layout.

Preserve field order, parameter order, and any other semantically ordered sequence. Deterministic serialization does not mean alphabetically reordering every list.

Existing JSON interface/object formats remain a migration/interchange path. A compact indexed binary encoding can be designed later, after the new UIR and artifact contracts are stable. No new extension is selected here.

Dependency gate for the original nine-item summary's item 8: concrete implementation-artifact redesign consumes the typed UIR operation, type, ownership, and verification contracts. Its generic-artifact replacement additionally consumes a separately reviewed generic-template profile/specialization design, which is deferred from UIR U0-U4. Existing embedded-source/JSON generic adapters remain supported until a replacement passes compatibility validation. A minimal module-contract reader and M1a/M1b do not wait for either replacement. The typed UIR proposal carries the same gate.

## 11. Correct dependency fingerprints
Track what each stage actually consumes.

| Change | Required consequence |
|---|---|
| Module source changes | Recompute that module's affected products |
| Dependency contract changes | Recheck dependent semantic consumers and regenerate affected implementations |
| Dependency private body changes, unchanged contract, ordinary out-of-line call | Rebuild dependency implementation and relink; importer semantic result can remain reusable |
| Dependency body is consumed for specialization, inlining, or cross-module optimization | Regenerate affected implementation consumers even when the public contract is unchanged |
| Compiler behavior, Unicode profile, verifier/IR format, or relevant options change | Invalidate incompatible stage results |
| Target, ABI, runtime, SDK, or linker input changes | Invalidate the stages that consume those inputs |

The existing rule that importers depend only on public interface digests is useful for semantic checking, but is not sufficient for every future code-generation dependency. Start conservatively with module-level implementation/template digests when bodies are consumed. Fine-grained per-definition tracking can follow measurements.

Every final link depends on the implementation content it includes. Reusing an importer's check result must never imply retaining an executable containing an obsolete dependency body.

## 12. Cache structure and integrity
Use stage-specific keys over canonical descriptions of actual inputs. Include:
- compiler build/implementation identity, not just human version or unchanged file schemas;
- language, Unicode, IR, artifact, and verification profiles as relevant;
- for UIR-producing/consuming actions: encoding/schema version, exact semantic/legality profile versions, canonical required operation/extension contract versions, verification-policy version, and applicable runtime-import/ABI contract versions;
- exact source snapshot digest;
- logical module and entry/library role where relevant;
- resolved dependency bindings and consumed contract/implementation fingerprints;
- semantic/codegen options and target/ABI/runtime/SDK inputs at the stages where they matter.

Use a conservative compiler build fingerprint that covers behavior-changing implementation/configuration, including dirty/generated build inputs. Refine granularity only with evidence.

UIR contract versions also appear in the committed manifest and are validated on consumption. They supplement compiler build identity, not replace it. Version only the inputs consumed by a stage: changing a backend legality profile need not invalidate a check-only contract action that does not consume it. The new UIR schemas/profiles remain proposed until their architectural review is complete.

Separate an action-key-to-output-manifest index from content-addressed immutable payloads. Keep SHA-256 initially, matching the existing artifact digests. This describes a local offline cache; a remote cache is not required.

A cache hit validates the committed manifest, requested action key, expected module identities, sizes/digests, supported schema/profile, interface/object relationship, and consumed dependency contracts. Bounded decoders reject malformed counts, references, duplicate/conflicting definitions, and invalid names.

A bad local derived-cache entry can be treated as a miss and rebuilt. A corrupt explicit dependency with no source must produce an actionable error. Preserve mandatory Universal IR verification when implementation material is consumed; matching hashes prove byte identity, not semantic validity.

Add independent invalidation fixtures for each relevant UIR schema/profile/extension/verifier/runtime-contract version: with source, compiler build, and other options fixed, the changed consumed version must change the affected action key and miss. Unsupported explicit precompiled contracts must diagnose. Preserve hits for unchanged eligible actions and retain the separate real compiler-build A/B regression. These fixtures specify future validation; none were run during document review.

## 13. Transactional publication
Write outputs into a private generation directory, validate the complete generation, and publish one committed manifest/reference through the host's supported atomic replacement mechanism on the same filesystem. Readers consume only committed generations.

Do not claim that independently renaming an interface and object makes the pair atomic. Coordinate writers per action key; release locks and temporary state on failure/cancellation. If same-key writers produce different payload digests, report a determinism failure rather than silently choosing a result.

Legacy adjacent artifacts may remain explicit exports. If a reader sees an incomplete or mismatched legacy pair, reject it rather than treating it as a valid generation.

Atomic visibility and crash durability are different guarantees. Define required flush/commit behavior in the filesystem adapter rather than assuming identical rename behavior on every host.

## 14. Reusable inferred generics
Retain source-independent specialization. The current embedded-source template is a compatibility mechanism; it is not the desired permanent representation.

Once the new typed Universal IR supports the necessary inferred-generic relationships, serialize verified reusable body templates with explicit declaration/type references and their constraints. Include private helpers required by the body while preserving source visibility. This must not create an independent redundant Typed IR merely for packaging.

Cache specializations by template/body identity, concrete type arguments, relevant dependency fingerprints, toolchain/profile, and target inputs where required. Keep emitted symbols and serialization stable under unrelated session-ID changes.

The detailed generic template operation set belongs to the UIR/semantic design. Until it is agreed, preserve existing template behavior rather than pretending the new representation already exists.

## 15. Offline dependency boundary
The compiler consumes a resolved local dependency/provider map and available artifacts. Ordinary compilation performs no implicit network resolution.

A future package tool can fetch, verify, pin, and bind dependencies before compilation. Package manifest extension, registry protocol, version-solving policy, and lockfile schema remain separate decisions, as required by the current language scope. No new source import form is introduced.

## 16. Diagnostics, observability, and acceptance
Diagnostics identify the import span, logical target, selected provider/root, and a cycle chain or artifact compatibility reason as appropriate. Preserve existing error categories and selection order during migration; explicitly review deliberate filesystem-policy changes.

Record source reads, parses, module stage runs, graph visits, artifact decodes, cache hit/miss reasons, bytes hashed, and phase time. Keep trace output separate from normal diagnostics and products.

Acceptance checks:
- Diamond and shared-dependency graphs process each stage/context once.
- Deep graphs and cycles terminate safely with deterministic errors.
- Alias, privacy, no-shadowing integration, std reservation, import ordering, declaration-only imports, and explicit entry rules remain correct.
- Source, interface-only checking, source-independent linking, and generic specialization preserve existing behavior.
- M1 preserves existing path behavior. Later imported-path containment, symlink, Unicode filename, case-collision, relocated-workspace, and Windows-path tests apply only to the separately agreed adapter/policy scope.
- Compiler implementation changes invalidate results even when artifact schema numbers stay unchanged.
- Private ordinary-call edits reuse valid importer semantic checks while relinking updated dependency code.
- Generic/inlining body changes invalidate consumers even with unchanged public signatures.
- Corruption, truncated generations, mismatched interface/object pairs, interrupted publication, and concurrent writers cannot create accepted false hits.
- Cache loads remap serialized names into current IDs and preserve mandatory verification.
- Cold, warm, private-edit, public-edit, and body-consuming incremental builds report comparable time, memory, I/O, and action counts.

The milestone order is defined in section 0: baseline, isolated cache correctness, then immutable-input reuse. Graph/lookup representation and filesystem adapters are separate changes. Serialized implementation/template redesign waits for UIR. Minimal existing-contract adapters are optional and do not block M1.

### Concrete M1 success metrics — proposed gates
Freeze a deterministic 32-module declaration-only benchmark fixture before implementation. Include a shared-dependency diamond, fan-out, nominal types, checked failures, and an inferred-generic export. Compile its root library into the same requested reusable artifacts in baseline and candidate. Record its source digest, graph, expected module/action counts, and build command. Use the existing full frontend project only as a later representative qualification workload; do not launch expensive self-builds to establish these small-fixture metrics.

Measure baseline and candidate in the same runtime tier, toolchain settings, target, host, and output mode. Do not compare a Python baseline against a native candidate. Use fresh processes for every timed run, five paired repetitions, empty dedicated cache directories for cold runs, and independently prepopulated caches for warm runs. Record cache state separately from OS page-cache state; an empty artifact cache is not a claim of cold physical disk I/O. Report medians and spread, with source reads/parses, semantic/lowering action counts, bytes hashed, validated hits, and peak RSS.

| Metric | Proposed acceptance gate |
|---|---|
| Cold root-artifact build median | At most 1.05 times baseline median |
| Unchanged warm root-artifact rebuild median | At most 1.05 times baseline warm median |
| Peak RSS on the fixture | At most 1.10 times baseline for the corresponding mode |
| Warm artifact-action hit rate | 100% of eligible unchanged module-artifact actions, reported as hits/eligible actions |
| Warm unchanged semantic/lowering actions | Zero for modules covered by valid artifact hits; hashing, decoding, verification, and any required parsing remain separately counted |
| Source reads/parses within a cold M1b request | At most one snapshot read and one parse per distinct module revision/context |
| False accepted hits, mixed-generation products, leaked ready state after cancelled attempts | Zero in the specified fault tests |

The 5% time and 10% memory budgets are proposed engineering regression limits, not observed performance or promised speedups. Establish absolute baseline seconds/bytes before implementation; if noise exceeds a budget, mark the timing result inconclusive and improve measurement rather than declaring a pass. A correctness fix must not be discarded to meet a speed budget; report its cost and decide the tradeoff explicitly. M1 targets correctness and duplicate-work removal; no arbitrary percentage speedup is promised.

Also record private-body and public-contract edit rebuild times and affected-action counts. For an ordinary out-of-line private-body edit with an unchanged interface, the dependency implementation must change, unchanged importer contract consumers may hit, and any final executable must relink updated code. For a public-contract edit, every affected semantic consumer must miss. For a consumed generic body edit, the affected specialization/code-generation action must miss even if the contract digest is unchanged. Attribute each action to its declared inputs instead of requiring every importer artifact to hit in every backend mode.

### Required compiler-build invalidation regression
Use one unchanged source/dependency fixture, identical options, Unicode profile, and artifact schema/IR versions, and a shared cache:
1. Build with compiler build A. Require a miss and a completed A generation.
2. Repeat with A in a fresh process. Require a validated hit.
3. Build with a distinct compiler build B without changing fixture inputs or artifact schema numbers. Require a different action key, a miss, and actual B compilation work; the A payload must not be copied as B output.
4. Repeat with B. Require a validated B hit.
5. Return to A. Its separate valid generation may hit; B must not overwrite it under A's key.

Test the real build-fingerprint derivation as well as key plumbing: a compiler implementation change, including a dirty/generated implementation input where supported, must change the fingerprint without relying on a manually bumped schema. A unit test that injects a different identity string is useful, but alone does not establish this end-to-end property. Artifact provenance and stage events establish which compiler action actually ran. No new builds were run while writing this regression specification.

## Decision FS-001: imported symlinks crossing a declared root
Status: separate proposed behavior change; not approved and not part of M1 or a behavior-preserving adapter refactor.

Current behavior: imported targets do not consistently receive the entry path's canonical containment check. Some projects may successfully import a symlink whose target is outside the configured source root.

Proposed future rule: permit symlinks resolving within the declared root; require an explicitly configured external root/provider binding for targets outside it. Continue distinguishing logical module identity from physical file identity.

Compatibility example: src/lib.eri points to ../vendor/lib.eri outside the configured src root. A currently accepted import may fail under the proposed rule. The infrastructure milestone must continue accepting it unless this separate policy is explicitly selected.

Migration prerequisites: document and inspect existing resolution behavior; identify affected projects; design and ship the explicit external binding mechanism before enforcing the restriction; provide a migration diagnostic identifying the importing span and resolved target; version the policy and include it in relevant cache keys. No flag, command, manifest syntax, or provider capability is claimed to exist already. Package/root-binding design remains separate from source import syntax.

Decision required later: retain current behavior or adopt the tightened rule with the migration mechanism. Do not infer approval of FS-001 from approval of cache/session architecture.

No production source changes, new workflows, tests, or benchmarks were started during this review.

## References
Rust and Bazel are precedents for individual techniques, not evidence that the full design fits Eristavi. Eristavi-specific justification comes from the call paths and state mutations identified in section 2, the ownership/error contracts above, and the proposed local measurements and regressions. Source inspection establishes repeated operations and missing key inputs; it does not establish their percentage of compile time.
Repository baseline: https://github.com/eristavi/eristavi-lang/tree/8af0ffe3350c737550c3ab0e6c3fa89f60f6f091
Language rules: LANGUAGE_SEMANTICS.md, section 11.
Implementation: src/compiler/semantic_project.eri; semantic_model.eri; semantic.eri; compiler/erist/project.py; build_cache.py; interface.py; object_artifact.py; direct_project.py.
Contracts/tests: MODULE_INTERFACES.md; tests/test_project.py; test_interfaces.py; test_build_cache.py; test_object_artifacts.py; test_module_member_precedence.py.
Rust metadata documentation illustrates separate check/link products and compiler/dependency compatibility: https://rustc-dev-guide.rust-lang.org/backend/libs-and-metadata.html
Rust incremental documentation explains explicit dependencies and stable cross-session representations: https://rustc-dev-guide.rust-lang.org/queries/incremental-compilation-in-detail.html
Bazel cache documentation illustrates declared action inputs and action-manifest/content-store separation: https://bazel.build/remote/caching

