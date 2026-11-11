# File acquisition development evidence — 9 November 2026

**Partial implementation only. Whole-Function File ownership/cleanup is unfinished.**
Base: `328f03ef6b7ef2a57d9cdf630fc0b98668c3cb9b` on draft PR #111.
Final relevant source hashes are recorded in `source-hashes.json`.

Local Linux x86-64, GCC 13.3.0, Python 3.12, project-pinned
regex 2026.9.29 and unicodedata2 17.0.0. No custom CFLAGS.

Final exact-source command:
`PYTHONPATH=.:tests python -m unittest test_u2_file_acquire_native -v`
**2/2 PASS**, 13.683 seconds. Native read-only File acquisition succeeds for
an existing file and returns a typed saved failure for a missing path. Each
outcome survives explicit slot/Text collection; the acquired File is closed
through the existing cleanup accumulator. Scope retirement and the existing
resource FINISH observer verify reclamation. The static native executables
have no loader, undefined symbols or executable stack, and run with an
unavailable PATH. An unknown same-length acquisition symbol refuses before
assembler output. Generation uses the bootstrap C compiler; no new owned-
generator equivalence, sanitizer, allocator-fault or cross-platform claim.

Related command (before the final carrier-alias admission guard and test-only
same-length symbol refinement):
`PYTHONPATH=.:tests python -m unittest test_u2_file_acquire_native test_u2_scoped_owners test_u2_native_cleanup -v`
**14 run / 13 passed / 0 failed / 1 intentional opt-in skip**, 58.973 seconds.
This is related-regression evidence, not an exact-source final full suite.
The changed bridge was rerun by the final command above. Raw logs retained.

Initial fixture attempts failed because the bootstrap metadata specialization
was absent and the acquisition signature (with its path parameter) was used
where a zero-parameter outcome signature was required. A test assertion also
compared byte output with strings. Those attempts are not green evidence;
the final source fixes them without deleting tests or raising watchdogs.

New tests join the existing one-platform smoke selection. Hosted smoke and
four-platform qualification are not claimed by this local report. #111 stays
draft/unmerged, #74 open. Production/default compiler and runtime unchanged.

Next: use this bridge in original whole-Function SSA/native dispatch together
with the existing close/cleanup implementation, retaining exact pending primary
and ordered secondary context, owner moves, roots and every exit. See
`docs/architecture/UIR_U2_FILE_ACQUIRE_BRIDGE.md` for the ABI and limitations.
