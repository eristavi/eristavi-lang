# U1b narrow scalar types — initial identity and SSA foundation

Status: draft; not qualified or merged. Agreed U1 contract and frozen Eristavi semantics remain governing.

Internal TypeId 4=i8, 5=i16, 6=i32; pred=1, i64=2, f64=3 unchanged. The independent verifier and builder accept the narrow types as distinct function and block parameters, return values and private scalar-cell types, with no implicit widening. A negative verifier test changes an i8 parameter to i64 and requires rejection. A second test carries a mutable i8 cell across a diamond and compares direct and promoted SSA execution at signed 8-bit boundary values.

This first slice does not add narrow integer constants/arithmetic, signedness-specific operations, immutable aggregates, U2 managed values or U3 production integration. It creates no additional public Eristavi numeric types and changes no runtime ABI or existing production compiler.

Before merging, require the four-platform ordinary CI and full completed-batch qualification on the exact head. Reconcile any concurrent U1a verifier changes and requalify the combined tree. Historical full owned compiler self-build remains out of scope.
