# Iteration Playbook

Use this process for each rules-module development round.

## Round Shape
Each round should fit in a small PR:

- One behavior category.
- One protocol or state shape change at most.
- Focused server tests first or alongside implementation.
- Minimal UI affordance only when needed to exercise the behavior.
- Documentation update in this directory and `docs/agent-context.md`.

## Before Coding
Write a short round brief:

- Goal.
- Files expected to change.
- Source constraints and content boundaries.
- Command/event changes.
- Test cases.
- Manual verification steps.
- Known shortcuts.

Do not paste protected rule prose into issues, docs, tests, fixtures, or commit messages. Convert reference material into original acceptance criteria and invented fixture names.

## Recommended Order Inside a Round
1. Add or update schema/protocol definitions when needed.
2. Add backend state and validation tests.
3. Implement the server-authoritative behavior.
4. Generate protocol types.
5. Add narrow UI support if required.
6. Run API tests and web build.
7. Update roadmap/context docs.

## Acceptance Criteria Template
Use this structure for each phase:

```md
Goal:

Server behavior:

Events emitted:

Client behavior:

Tests:

Out of scope:

Content boundary:
```

## Review Checklist
- Does the client send intent instead of deciding the result?
- Does the server emit enough events to replay the outcome?
- Are random rolls server-side and auditable?
- Does `HELLO` include enough snapshot state for reconnect?
- Are reaction/pending-choice windows explicit?
- Are protected names, prose, examples, boards, scenarios, and profiles absent?
- Can the behavior be tested with invented fixtures?
- Did docs stay aligned with code?

## Documentation Discipline
- Keep roadmap files strategic, not rulebook-like.
- Document mechanics as software responsibilities and state transitions.
- Use invented examples for fixtures and tests.
- Update `docs/protocol.md` and `docs/data-model.md` when the protocol or data model changes.
- Update `docs/agent-context.md` at the end of every behavior-changing round.

