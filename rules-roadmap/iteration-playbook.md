# Implementation Iteration Playbook

## Before coding

1. Read `docs/agent-context.md`, then this directory's README and the selected Pxx package.
2. Check working tree/branch and preserve unrelated changes. Confirm which prerequisite slices actually landed; a plan entry is not implementation evidence.
3. Select one small slice and its Rxx requirements. Reopen the source pages, diagrams, sidebars, and applicable corrections. Check the decision register; do not invent faction data or resolve a blocked rule from memory.
4. Write a short implementation brief using the template below. Keep current protocol documentation distinct from planned contracts.

```text
Slice: Pxx.n
Outcome visible to players:
Requirements: Rxx, Ryy
Prerequisites and current implementation evidence:
Source ID/pages/corrections:
Selected decisions and unresolved questions:
Expected files/modules:
Commands, events, choices, and snapshot change:
State invariants and failure/rollback behavior:
Required tests (positive, rejection, timing/boundary, reconnect/replay):
Minimal UI and manual demonstration:
Compatibility/migration:
Known limitations and release impact:
```

If source material is missing, implement only independently justified infrastructure or synthetic test fixtures; mark the affected content `source_blocked`. Keep fixtures nonselectable. A question does not block unrelated work.

## Implementation order

1. Add focused domain tests for the intended behavior and edge cases; use original arrangements, not copied published examples.
2. Evolve domain types and schema where necessary. Specify actor/phase/choice permissions and rejection codes.
3. Implement server decision/reduction, transaction/RNG/choice checkpoints, and invariants. No rules authority in the browser.
4. Generate both protocol languages from the schema. Never hand-edit generated files.
5. Add the minimal UI to exercise the behavior, including opponent prompts, illegal-action feedback, and snapshot/resync handling.
6. Run focused tests and then appropriate repository checks; see validation guide. Check version compatibility and replay where state changes.
7. Demonstrate with two clients when the slice affects player interaction. Verify the nonactive player can answer its own choices but cannot act outside them.
8. Update requirement status with actual code/test paths, package progress, and the next slice. Update `docs/agent-context.md` snapshot, next tasks, and risks. Update `docs/protocol.md` and `docs/data-model.md` for actual contract/model changes.

## Completion checks for every slice

- Client sends intent, not dice totals, derived legality, casualties inflicted, or winner.
- Ownership and current choice/phase are enforced server-side; connection order does not confer authority.
- Duplicate and stale commands cannot reroll, spend twice, or resolve a choice twice.
- Rejected proposals leave authoritative state unchanged; rule-driven cancellation retains already paid costs and resolved reactions as required.
- Every random outcome and choice needed for replay is recorded; snapshots contain the complete pending resolution.
- Effects expire at the correct boundary; no implicit clearing of fatigue or retained dice.
- Content is source-backed, version-pinned, original in expression, and outside generic core.
- Tests are meaningful behavioral checks, not copies of implementation branches. UI/backend/schema remain aligned.
- No new source question is hidden by a default value. Record a limitation precisely and keep unsupported content unavailable.

## Handoff record

End each slice with: what changed and why; validation commands/results; relevant Rxx tests; migration/compatibility notes; unresolved source questions; and exact next Pxx.n. Keep status truthful. Passing lint/build alone is not evidence that a rules interaction works.

Commit only the intended slice files. Keep local source PDFs, OCR, rendered pages, credentials, generated caches, and unrelated working-tree changes out of commits. Use neutral development language in documentation and commit messages.
