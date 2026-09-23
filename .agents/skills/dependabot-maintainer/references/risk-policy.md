# Dependabot Risk and Decision Policy

Use this policy to assess two independent dimensions:

- **Security priority**: how urgently the vulnerability should be addressed.
- **Change risk**: how likely the proposed update is to cause a regression or compromise the development pipeline.

High security priority never lowers verification requirements. Low change risk never proves that an alert is exploitable or urgent.

## Security priority

Raise priority when evidence shows runtime scope, reachable vulnerable behavior, critical or high severity, known exploitation, high EPSS, exposure to untrusted input, network reachability, or a broad confidentiality/integrity/availability impact.

Lower priority, without dismissing the alert, when the dependency is development-only, the vulnerable code is demonstrably unreachable in this repository, exploitation requires absent conditions, or compensating controls materially reduce exposure.

Record the evidence. Do not infer reachability solely from dependency scope or severity.

## Change risk

Classify the proposed change by the highest matching category.

### Low

All of these must hold:

- One package is updated by a SemVer patch or equivalent minimal secure change.
- The dependency graph remains compatible and the manifest constraint needs no material expansion.
- The diff contains no package-manager, language/runtime, CI permission, workflow behavior, generated protocol, or application-code change.
- The lockfile change is narrow, with no unexplained new package source, lifecycle behavior, downgrade, or unrelated package churn.
- The affected surface has meaningful automated coverage and all relevant local and required GitHub checks pass.
- No concrete regression, compatibility warning, or migration requirement is present.

The following are never Low in this repository: GitHub Actions updates and web runtime dependency updates, because Actions execute in a privileged CI path and the web application currently lacks automated UI tests.

### Medium

Use Medium for any of:

- A minor update, grouped update, runtime dependency patch, parent-dependency change, or meaningful transitive re-resolution.
- A web dependency update that needs manual UI smoke testing.
- A development tool update that can change generated output, lint rules, builds, or test behavior.
- A GitHub Action update that does not otherwise meet High criteria.
- Incomplete coverage, a broad lockfile diff, or uncertainty that can be resolved with targeted review or testing.

### High

Use High for any of:

- A major update, breaking change, migration, or language/package-manager/runtime baseline change.
- Changes to authentication, authorization, cryptography, network boundaries, serialization, persistence, build/release behavior, action permissions, or secret handling.
- A GitHub Actions change that alters workflow logic, permissions, triggers, downloaded executables, or trust boundaries.
- New or changed install/lifecycle scripts, dependency sources, registries, or unpinned executable content.
- A required test/security-check bypass, unresolved incompatibility, unexplained generated-code change, or concrete regression.
- Insufficient evidence to bound a potentially material production or supply-chain impact.

## Repository verification gates

### Python API

Run `scripts/verify-update.sh api`. It must complete:

- deterministic Poetry synchronization;
- Ruff;
- mypy;
- the complete pytest suite, including the integration smoke test.

Inspect `services/api/pyproject.toml` and `services/api/poetry.lock`. Runtime dependency changes are at least Medium unless the evidence and coverage justify a stricter case-by-case exception; such an exception still requires human review.

### JavaScript web app

Run `scripts/verify-update.sh web`. It must complete deterministic pnpm installation, lint, generated-type build, TypeScript compilation, and the Vite build.

The web app has no automated UI test suite. Any runtime dependency change therefore requires a manual smoke test and is at least Medium. Build-tool and type-tool updates require review of generated files and build output.

### GitHub Actions

Run `scripts/verify-update.sh actions`, inspect the workflow diff and action release notes, and require the hosted CI run to pass. Treat changes to action ownership, reference style, permissions, triggers, or executed commands as High.

### Security evidence

The repository's `pip-audit`, Bandit, and `pnpm audit` CI steps currently downgrade findings to warnings. A green security job is therefore not evidence that those scanners found nothing. Read their logs and treat any finding as evidence until the CI policy is hardened.

## Decision gates

### Merge candidate

Recommend `MERGE_CANDIDATE` only when:

- the PR is precisely correlated to the alert or is a clearly scoped version update;
- the secure version is actually selected in the resolved dependency graph;
- change risk is Low under this policy;
- local verification and every required GitHub check pass;
- the PR is current, mergeable, and free of unexplained changes;
- no manual check remains outstanding.

This classification is a recommendation, not permission to merge.

### Hold or remediate

Use `HOLD` for Medium/High risk, incomplete evidence, outstanding manual tests, conflicts, or failed checks. Use `REMEDIATE` when a concrete, bounded change can make the current fix viable. Keep the PR open while the issue is actionable.

### Close candidate

Recommend closure only with concrete evidence of one of these:

- another named PR or commit supersedes it and covers the same package, manifest, and secure version;
- it duplicates another active PR and retaining both adds no value;
- the default branch no longer contains the vulnerable dependency/version and GitHub confirms the alert is fixed or inapplicable;
- the PR targets obsolete repository content and cannot apply.

Failed tests, high change risk, lack of maintainer time, or absence of a safe fix are not closure criteria. Link the replacement or evidence in any closure comment.

### Dismiss candidate

Alert dismissal is exceptional. Require human approval, a precise rationale, and a revisit condition or compensating control. Prefer fixing the default branch so GitHub resolves the alert automatically. Never dismiss solely to reduce alert count.

## External mutation boundary

These operations all require the mutation gate in `SKILL.md`: pushing branches, editing or commenting on PRs, submitting reviews, changing labels, enabling auto-merge, merging, closing or reopening PRs, and updating or dismissing alerts.

If this skill is later run in CI, keep analysis separate from deterministic merge enforcement, use trusted triggers, grant least-privilege token permissions, and do not expose write credentials to untrusted pull-request code.
