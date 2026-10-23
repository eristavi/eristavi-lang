# Design Philosophy

## Purpose

This document is the governing design charter for Eristavi.

It defines the principles that should guide decisions about syntax, semantics, the type system, memory management, the compiler, runtime, standard library, tooling, portability, and future evolution.

When an implementation choice conflicts with these principles, the default response should be to change the implementation rather than weaken the philosophy for convenience.

The language should grow deliberately. New features must justify their complexity.

---

## 1. Core Identity

Eristavi should combine:

- **Readability**
- **Native performance**
- **Universal portability**
- **Controlled simplicity**
- **Safety by default**
- **Low-level power when explicitly requested**

The central idea is:

> **Complexity belongs in the compiler and runtime, not in the programmer's code.**

The language should be approachable without becoming simplistic, and powerful without forcing ordinary programmers to manage unnecessary complexity.

---

## 2. Small, Stable Vocabulary

The core language vocabulary should remain intentionally small.

Keywords exist to describe the structure and semantics of programs, not every operation a program can perform.

Operations such as text reversal, sorting, JSON parsing, networking, encryption, image processing, and database access belong in types, the standard library, or external libraries.

### Rule

> **Do not add a keyword when a type, library, operator, or existing construct can express the concept clearly.**

---

## 3. One Obvious Way

Fundamental concepts should normally have one preferred form.

Avoid accumulating multiple equivalent syntaxes merely for convenience, familiarity, or compatibility with other languages.

Examples of what to avoid:

- several variable-declaration keywords with overlapping meaning;
- multiple unrelated function syntaxes;
- several ways to express the same loop;
- legacy aliases that permanently increase cognitive load.

### Rule

> **New syntax must reduce complexity, not merely move it.**

---

## 4. Readable, but Precise

The language should read naturally, but it should not attempt to imitate unrestricted English.

Example:

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

## 5. Safe and Predictable by Default

The language should avoid surprising implicit behavior.

Implicit conversions should be limited to cases that are unquestionably safe and unsurprising.

For example, the language should not silently choose whether:

```eri
"5" + 5
```

means numeric addition or text concatenation.

Conversions should be explicit when meaning could be ambiguous.

### Rule

> **If reasonable programmers could interpret an operation differently, require explicit intent.**

---

## 6. Strong Types Without Excessive Ceremony

The type system should provide strong static guarantees while allowing concise everyday code.

Type inference should handle obvious cases:

```eri
let age be 44;
let name be "Revaz";
```

Explicit types should remain available where contracts, public APIs, documentation, or safety benefit from them.

The type system should help the programmer rather than dominate the source code.

### Rule

> **Infer what is obvious; require what is important.**

---

## 7. Rich Standard Library, Small Language

The standard library should provide a coherent and useful foundation so programmers do not need third-party dependencies for routine work.

Likely standard-library domains include:

- Text
- Collections
- Math
- Time
- Files
- JSON
- Networking
- Processes
- Concurrency
- Randomness
- Encoding
- System interaction

APIs should remain internally consistent.

### Rule

> **Grow capability through libraries before growing grammar.**

---

## 8. Automatic Memory Management

Ordinary programmers should not manually allocate and free general-purpose memory.

The compiler should attempt to avoid heap allocation where possible through:

- register allocation;
- value optimization;
- escape analysis;
- stack allocation;
- object elimination.

Objects that genuinely require dynamic shared lifetime may use a managed heap.

### Rule

> **Programmers express object lifetime through program structure; the compiler/runtime handles memory lifetime.**

---

## 9. Deterministic Resource Management

Memory and external resources are different problems.

Resources such as files, sockets, database connections, locks, OS handles, and GPU resources should support deterministic scoped cleanup.

Conceptually:

```eri
using file be open("data.txt");
let contents be file.read();
```

### Rule

> **Memory may be managed automatically; scarce external resources must be released predictably.**

---

## 10. Explicit Low-Level Power

The language should not prevent systems-level or performance-critical programming.

Low-level capabilities may eventually include raw memory, custom allocators, foreign-function interfaces, direct buffers, SIMD, platform APIs, and hardware-specific operations.

Code that bypasses normal guarantees must be explicitly marked.

### Rule

> **Powerful operations are allowed, but dangerous behavior must never look ordinary.**

---

## 11. Universal, Machine-Neutral Intermediate Representation

The compiler should have its own machine-independent intermediate representation.

The IR is the architectural center of the compiler. Source-language semantics must not depend on x86, ARM, RISC-V, or any current CPU.

Conceptually:

```text
Source
  ↓
Frontend
  ↓
Typed representation
  ↓
Universal IR
  ↓
Backends
```

### Rule

> **The language describes computation; target backends describe machines.**

---

## 12. Native and Portable Compilation

The architecture should eventually support two complementary execution models.

### Native

```text
Source
  ↓
Universal IR
  ↓
Target backend
  ↓
Native machine code
```

### Portable

```text
Source
  ↓
Universal IR
  ↓
Stable portable bytecode
  ↓
Runtime
```

The internal compiler IR and the public portable bytecode format should not be assumed to be the same representation.

### Rule

> **Portability must not require sacrificing the possibility of true native compilation.**

---

## 13. CPU and Operating-System Independence

Core language semantics should not change depending on operating system or processor architecture.

Platform-specific behavior should live behind target backends, runtime abstractions, platform libraries, or explicitly platform-specific APIs.

### Rule

> **New machines should require new backends, not a new language.**

---

## 14. Excellent Compiler Diagnostics

Compiler errors are part of the language experience.

Diagnostics should identify the actual problem, show the relevant source, explain why it is invalid, and suggest likely corrections when confidence is high.

Example:

```text
Unknown name "costumer".

7 | print costumer;
          ^^^^^^^^

Did you mean "customer"?
```

### Rule

> **An error message should help the programmer fix the program, not merely report that compilation failed.**

---

## 15. Performance Transparency

High-level syntax should not mean opaque performance.

Tooling should eventually be able to explain decisions such as stack vs heap allocation, eliminated allocations, inlining, object escape, bounds-check removal, vectorization, generated target instructions, and memory pressure.

Conceptually:

```text
erist explain memory app.eri
erist explain optimize app.eri
```

### Rule

> **The compiler may automate performance decisions, but programmers should be able to inspect them.**

---

## 16. Avoid Historical Baggage

Eristavi starts without legacy constraints. That opportunity should be protected.

Do not copy a feature merely because another language has it.

Every feature should answer:

1. What problem does it solve?
2. Is that problem common enough for the language itself?
3. Can the standard library solve it instead?
4. Does an existing construct already solve it?
5. Does it introduce another way to do something already supported?
6. Will programmers still understand this decision ten years later?

### Rule

> **Familiarity is useful, but coherence is more important.**

---

## 17. Deliberate Evolution

The project should follow this order:

> **Philosophy → Semantics → Architecture → Implementation**

Syntax should not be finalized before semantics are understood. Implementation convenience should not define language semantics accidentally. Optimizations should preserve semantics rather than reshape them.

### Rule

> **Design the meaning first, then the mechanism.**

---

# Decision Test

Before accepting a new language, compiler, runtime, or library feature, evaluate it against these questions.

## Necessity

- What real problem does it solve?
- Is the problem common enough to justify permanent complexity?
- Can a library solve it instead?

## Simplicity

- Does it add a new concept?
- Does it duplicate an existing concept?
- Can the current language express it without becoming awkward?

## Readability

- Is its meaning obvious when encountered for the first time?
- Is the syntax concise?
- Is it unambiguous?

## Safety

- Can ordinary use create surprising behavior?
- Are implicit conversions predictable?
- Does dangerous behavior require explicit intent?

## Portability

- Does the feature depend on one CPU or OS?
- Can it be represented cleanly in the universal IR?
- Can future backends implement it without changing source semantics?

## Performance

- Can the compiler optimize it effectively?
- Does it force unnecessary runtime cost?
- Can the programmer inspect relevant performance decisions?

## Long-Term Cost

- Will this feature make future evolution harder?
- Does it create syntax or semantics we may regret supporting permanently?
- Does it make the language easier to learn, or merely more familiar?

---

# Governing Principle

When in doubt, prefer the design that keeps the programmer's mental model smaller while preserving capability.

> **Small language. Rich libraries. Powerful compiler. Predictable runtime. Universal architecture.**

This document is the project's design constitution and should be used as the baseline for future Eristavi decisions.
