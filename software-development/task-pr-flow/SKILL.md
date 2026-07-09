---
name: task-pr-flow
description: Plan and manage fast, safe software delivery through small task slices, short-lived branches, PR sequencing, stacked PRs, feature flags, CI tiering, merge queues, and agent coordination. Use when Codex needs to split a feature into implementation tasks or PRs, design a Git/GitHub PR workflow, unblock dependent PRs, reduce CI wait time, handle merge conflicts, coordinate multiple coding agents, or answer Chinese/English questions about 任务拆解, PR 管理, stacked PR, merge queue, CI pipeline, or branch strategy.
---

# Task PR Flow

## Overview

Use this skill to turn a vague feature or delivery problem into a concrete PR flow. Optimize for small diffs, short-lived branches, stable `main`, fast feedback, and no hidden breakage.

Do not recommend bypassing review, tests, or CI as the speed solution. Make the work smaller and the validation smarter.

## When to Use

Use this skill when the user needs to:

- Turn a feature, bugfix batch, or vague delivery request into small PRs.
- Decide whether work should be independent PRs, stacked PRs, or a mixed flow.
- Sequence contract, implementation, integration, rollout, and cleanup work.
- Reduce PR review size, CI wait time, merge conflicts, or stalled dependent PRs.
- Coordinate multiple coding agents without overlapping hot files or shared contracts.
- Explain or compare branch strategy, merge queue usage, CI tiering, or PR gating.

Do not use it as a shortcut around repository inspection, code review, tests, or CI. If the user asks for implementation, inspect the repo and implement the smallest safe first slice instead of planning a large speculative batch.

## Core Rules

- Keep `main` releasable.
- Use one short-lived branch per task slice.
- Keep each PR reviewable; target 300-500 effective changed lines unless the repo has a different norm.
- Put incomplete user-facing behavior behind feature flags or disabled config.
- Split contracts before implementations when work has dependencies.
- Prefer merge queues for busy repos.
- Keep stacked PRs shallow; 2-3 layers is the practical ceiling.
- Isolate formatting, renames, migrations, and broad refactors into their own PRs.
- Do not let multiple agents modify the same hot file, schema, or shared abstraction at the same time.

## Workflow

### 1. Establish Boundaries

Determine:

- Goal and non-goals.
- Modules touched.
- User-visible behavior.
- Data/schema/API contracts.
- Existing tests and CI tiers.
- Risk: low, medium, or high.

If the request is only planning, do not edit files. If the request includes implementation, implement only the smallest valid first slice unless the user explicitly asks for more.

### 2. Build the Dependency Map

Classify each dependency:

- Contract dependency: types, API shape, route, event, schema, interface.
- Implementation dependency: backend logic, UI wiring, migration, worker, integration.
- Validation dependency: test fixture, mock, e2e path, CI job.
- Rollout dependency: feature flag, config, migration rollout, cleanup.

Prefer this order:

```text
contract -> parallel implementation -> integration -> rollout -> cleanup
```

Do not serialize independent work just because one large PR was written first.

### 3. Slice PRs

Create PR slices that can merge safely:

```text
PR 1: contract/types/route skeleton/test fixture
PR 2: backend implementation behind flag
PR 3: frontend/client integration using contract or mock
PR 4: integration tests and wiring
PR 5: enable flag for limited scope
PR 6: remove old path after rollout
```

For each PR define:

- Title.
- Scope.
- Base branch.
- Files/modules expected to change.
- Validation command.
- Review owner if known.
- Merge dependency.
- Feature flag or rollback path if user-visible.

### 4. Choose Branch Topology

Use independent PRs when slices can merge independently:

```text
main
  ├─ pr-a-contract
  ├─ pr-b-backend
  └─ pr-c-ui
```

Use stacked PRs only when the diff must depend on unmerged code:

```text
main
  └─ pr-1-contract
       └─ pr-2-backend
            └─ pr-3-ui
```

After a lower PR merges, rebase the next PR onto updated `main`, retarget its base to `main`, then push with `--force-with-lease`.

Do not use a long-lived integration branch unless the team explicitly accepts delayed integration and extra conflict cost.

### 5. Define CI Tiers

Separate fast feedback from full confidence:

```text
PR blocking CI:
  lint, typecheck, unit tests, affected package tests, touched package build

Merge queue CI:
  integration tests, critical e2e, migration checks, compatibility checks

Nightly CI:
  full e2e matrix, slow cross-platform jobs, stress/perf, flaky detection

Release CI:
  full validation and deployment checks
```

Aim for PR blocking CI in 5-10 minutes. If it takes 40 minutes, recommend affected-test selection, caching, parallelism, or moving slow jobs to merge queue/nightly.

### 6. Plan Agent Work

Assign agents by module boundary, not by vague feature name:

```text
Agent 1: contract/types only
Agent 2: backend service only
Agent 3: frontend UI only
Agent 4: integration tests only
Agent 5: cleanup only
```

Each agent task must include:

- Allowed paths.
- Forbidden paths.
- Expected tests.
- PR title.
- Maximum scope.
- Whether behavior must stay behind a flag.

Reject tasks like "implement the whole feature" unless the feature is trivially small.

## Conflict Control

Use these rules before coding:

- Rebase from `main` before starting and before final push.
- Avoid shared config churn.
- Do not mix formatting with behavior changes.
- Do not mix rename/move with logic changes.
- Do not let generated files dominate review unless they are required.
- Prefer stable public contracts over temporary cross-branch imports.
- Use `git push --force-with-lease`, never plain `--force`, after rebasing a reviewed branch.

## Security and Risk

For credentials, permissions, production data, deployment, or destructive Git operations:

- Warn explicitly.
- Prefer read-only or dry-run first.
- Use least privilege.
- Include rollback steps.
- Do not hide risky changes inside a routine PR.

For experimental APIs or unstable tooling:

- Label them experimental.
- State instability risks: breaking changes, rate limits, missing guarantees.
- Provide a fallback path.

## Output Format

For planning tasks, output:

```md
## Delivery Plan

### PR Slices

| PR | Base | Scope | Depends On | Validation | Risk |
|----|------|-------|------------|------------|------|
| 1  | main | ...   | none       | ...        | low  |

### Branch Strategy

Independent PRs / stacked PRs / mixed. Explain why in one sentence.

### CI Plan

- PR blocking:
- Merge queue:
- Nightly:

### Agent Allocation

- Agent/task:
- Allowed paths:
- Forbidden paths:
- Validation:

### Conflict Plan

- Rebase points:
- Files likely to conflict:
- Isolation rules:
```

For implementation tasks, also include changed files and validation results in the final response.

## Common Pitfalls

1. **Oversized PR slices.** If a PR needs unrelated reviewers, touches unrelated modules, or cannot be summarized in one sentence, split it.
2. **Deep stacks.** More than 2-3 stacked PRs usually hides review state and increases rebase cost. Flatten independent work onto `main` instead.
3. **Contract drift.** Backend, frontend, tests, and generated clients must share the same contract source. Do not let each PR invent its own temporary shape.
4. **Wrong merge gate.** Do not treat a same-head push job, stale check, or unrelated lane as the authoritative PR gate. Identify the repository's real blocking checks.
5. **Mixed refactor and behavior.** Formatting, renames, migrations, and broad cleanup belong in separate PRs unless they are mechanically required for the slice.
6. **Feature flag theater.** A flag only helps if the incomplete path is truly unreachable by default and has a rollback or disable path.
7. **Agent collision.** Parallel agents must not edit the same hot file, schema, config, migration chain, or shared abstraction without an explicit owner.
8. **Unverified dependency unblock.** After a lower PR merges, rebase/retarget the dependent PR and rerun the relevant validation before calling it unblocked.

## Verification Checklist

Before finalizing, verify:

- [ ] Maintainability: each PR has one reason to exist and a reviewable diff size.
- [ ] Dependency order: contracts, implementations, tests, rollout, and cleanup are sequenced correctly.
- [ ] Branch topology: independent work is not unnecessarily stacked; required stacks are shallow and have rebase/retarget points.
- [ ] CI plan: PR-blocking checks are fast and relevant; slow confidence checks are assigned to merge queue, nightly, or release lanes.
- [ ] Conflict plan: hot files, schemas, generated files, migrations, and shared configs have clear ownership.
- [ ] Security: risky operations are isolated, warned, dry-run where possible, and include rollback.
- [ ] Style/consistency: branch names, PR titles, review owners, and validation commands match repo norms.
- [ ] Backward compatibility: `main` remains releasable and unfinished user-visible behavior is hidden behind a real flag or disabled config.
