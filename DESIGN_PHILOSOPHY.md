# Design Philosophy

## Purpose

This document is the governing design charter for Eristavi.

It guides syntax, semantics, the type system, memory management, compiler architecture, runtime behavior, the standard library, tooling, portability, and future evolution.

When implementation convenience conflicts with these principles, the default response should be to change the implementation rather than weaken the language model.

The language should grow deliberately. New features must justify their permanent complexity.

---

## 1. Core identity

Eristavi should combine:

- **readability**;
- **native performance**;
- **universal portability**;
- **controlled simplicity**;
- **safety by default**;
- **low-level power when explicitly requested**.

The central idea is:

> **Complexity belongs in the compiler and runtime, not in the programmer's code.**

The language should be approachable without becoming simplistic, and powerful without forcing ordinary programmers to manage unnecessary complexity.

---

## 2. Small, stable vocabulary

The core language vocabulary should remain intentionally small.

Keywords describe program structure and semantics, not every operation a program can perform. Text processing, sorting, JSON, networking, encryption, image processing, databases, and similar capabilities normally belong in types, the standard library, or external libraries.

### Rule

> **Do not add a keyword when a type, library, operator, or existing construct can express the concept clearly.**

---

## 3. One obvious way

Fundamental concepts should normally have one preferred form.

Avoid accumulating multiple equivalent syntaxes merely for familiarity or convenience. In particular, avoid overlapping variable declarations, several unrelated function forms, redundant loop constructs, and legacy aliases that permanently increase cognitive load.

### Rule

> **New syntax must reduce complexity, not merely move it.**

---

## 4. Readable, but precise

The language should read naturally without trying to imitate unrestricted English.

```eri
let total be price * quantity;

if total > 100 {
    print total;
}
```

The goal is immediate human comprehension while preserving deterministic grammar and unambiguous parsing.

### Rule

> **Prefer concise natural readability over verbose natural-language imitation.**

---

## 5. Safe and predictable by default

The language should avoid surprising implicit behavior.

Implicit conversions should be limited to cases that are unquestionably safe and unsurprising. For example, Eristavi should not silently choose whether:

```eri
"5" + 5
```

means numeric addition or text concatenation.

### Rule

> **If reasonable programmers could interpret an operation differently, require explicit intent.**

---

## 6. Strong types without excessive ceremony

The type system should provide strong static guarantees while allowing concise everyday code.

```eri
let age be 44;
let name be "Revaz";
```

Explicit types remain available where contracts, public APIs, documentation, or safety benefit from them.

### Rule

> **Infer what is obvious; require what is important.**

---

## 7. Rich standard library, small language

The standard library should provide a coherent foundation so routine work does not require unnecessary third-party dependencies.

Likely domains include Text, Collections, Math, Time, Files, JSON, Networking, Processes, Concurrency, Randomness, Encoding, and System interaction.

### Rule

> **Grow capability through libraries before growing grammar.**

---

## 8. Automatic memory management

Ordinary programmers should not manually allocate and free general-purpose memory.

The compiler should avoid heap allocation where possible through register allocation, value optimization, escape analysis, stack allocation, object elimination, and related techniques. Values that genuinely require dynamic shared lifetime may use managed heap storage.

### Rule

> **Programmers express lifetime through program structure; the compiler/runtime handles memory lifetime.**

---

## 9. Deterministic resource management

Memory and external resources are different problems.

Files, sockets, database connections, locks, OS handles, transactions, and similar resources require predictable scoped cleanup.

The locked Eristavi model uses `with`:

```eri
with file be try files.open("data.txt") {
    let contents be try file.readText();
    print contents;
}
```

### Rule

> **Memory may be managed automatically; scarce external resources must be released predictably.**

---

## 10. Explicit low-level power

Eristavi should not prevent systems-level or performance-critical programming.

Low-level capabilities may eventually include raw memory, custom allocators, foreign-function interfaces, direct buffers, SIMD, platform APIs, and hardware-specific operations.

Code that bypasses normal guarantees must be explicitly marked.

### Rule

> **Powerful operations are allowed, but dangerous behavior must never look ordinary.**

---

## 11. Universal, machine-neutral intermediate representation

The compiler should have its own machine-independent intermediate representation.

```text
Source
  ↓
Frontend
  ↓
Typed representation
  ↓
Eristavi IR
  ↓
Backends
```

Source semantics must not depend on x86, ARM, RISC-V, WebAssembly, or any other target architecture.

### Rule

> **The language describes computation; target backends describe machines.**

---

## 12. Native and portable compilation

Native compilation remains a core goal:

```text
Source
  ↓
Eristavi IR
  ↓
Target backend
  ↓
Native machine code
```

The compiler architecture may also support portable execution formats and non-native targets. The currently selected long-term target set is documented in `TARGETS.md` and includes native machine code, C, JavaScript, and WebAssembly.

The internal Eristavi IR must not be treated as a permanently frozen public bytecode merely because portable execution may later be useful.

### Rule

> **Portability must not require sacrificing true native compilation.**

---

## 13. CPU and operating-system independence

Core language semantics should not change with the operating system or processor architecture.

Platform-specific behavior belongs behind target backends, runtime abstractions, platform libraries, or explicitly platform-specific APIs.

### Rule

> **New machines should require new backends, not a new language.**

---

## 14. Excellent compiler diagnostics

Compiler errors are part of the language experience.

Diagnostics should identify the actual problem, show relevant source, explain why it is invalid, and suggest likely corrections when confidence is high.

```text
Unknown name "costumer".

7 | print costumer;
          ^^^^^^^^

Did you mean "customer"?
```

### Rule

> **An error message should help the programmer fix the program, not merely report that compilation failed.**

---

## 15. Performance transparency

High-level syntax should not mean opaque performance.

Tooling should eventually be able to explain stack versus heap allocation, eliminated allocations, inlining, escape behavior, bounds-check removal, vectorization, generated target instructions, and memory pressure.

Conceptually:

```text
erist explain memory app.eri
erist explain optimize app.eri
```

### Rule

> **The compiler may automate performance decisions, but programmers should be able to inspect them.**

---

## 16. Avoid historical baggage

Eristavi starts without legacy constraints. That opportunity should be protected.

Do not copy a feature merely because another language has it. Every feature should answer:

1. What problem does it solve?
2. Is that problem common enough for the language itself?
3. Can the standard library solve it instead?
4. Does an existing construct already solve it?
5. Does it create another way to do something already supported?
6. Will the decision still make sense ten years later?

### Rule

> **Familiarity is useful, but coherence is more important.**

---

## 17. Deliberate evolution

The project follows this order:

> **Philosophy → Semantics → Architecture → Implementation**

Syntax should not be finalized before semantics are understood. Implementation convenience must not define language semantics accidentally. Optimizations preserve semantics rather than reshape them.

### Rule

> **Design the meaning first, then the mechanism.**

---

# Decision test

Before accepting a new language, compiler, runtime, or library feature, evaluate it against the following questions.

## Necessity

- What real problem does it solve?
- Is the problem common enough to justify permanent complexity?
- Can a library solve it instead?

## Simplicity

- Does it add a new concept?
- Does it duplicate an existing concept?
- Can the current language express it without becoming awkward?

## Readability

- Is its meaning obvious on first encounter?
- Is the syntax concise?
- Is it unambiguous?

## Safety

- Can ordinary use create surprising behavior?
- Are implicit conversions predictable?
- Does dangerous behavior require explicit intent?

## Portability

- Does the feature depend on one CPU or OS?
- Can it be represented cleanly in the Eristavi IR?
- Can future backends implement it without changing source semantics?

## Performance

- Can the compiler optimize it effectively?
- Does it force unnecessary runtime cost?
- Can the programmer inspect relevant performance decisions?

## Long-term cost

- Will the feature make future evolution harder?
- Does it create syntax or semantics we may regret supporting permanently?
- Does it make the language easier to learn, or merely more familiar?

---

# Governing principle

When in doubt, prefer the design that keeps the programmer's mental model smaller while preserving capability.

> **Small language. Rich libraries. Powerful compiler. Predictable runtime. Universal architecture.**

This document is the project's design constitution and should remain the baseline for future Eristavi decisions.
