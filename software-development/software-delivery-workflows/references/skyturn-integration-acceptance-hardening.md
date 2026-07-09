# SkyTurn integration acceptance hardening

Use this when closing a multi-slice SkyTurn integration branch after stacked PR slices have been parent-validated.

## Review scope

- Integration review must inspect both committed integration history (`base..HEAD`) and any uncommitted post-review fixes in the worktree.
- If a review-only agent returns `BLOCK`, treat it as a real signal until disproven by code inspection. Do not open the integration PR with a known P0/P1 block.
- After every post-review fix, rerun targeted validation, then rerun review-only on the actual current artifact before committing or opening the PR.

## Merge gate consistency

Delivery merge readiness is a cross-layer invariant, not just a renderer affordance.

- UI, Electron IPC, git-worktree helpers, workflow-kernel projection, scheduler gating, and next-action selection must agree.
- Exact-head checks are necessary but not sufficient for merge readiness.
- Merge requires known non-blocking review evidence. Accepted review states are `approved` and `pending`.
- `changes_requested`, `unknown`, and missing review evidence must not produce `merge_ready` and must not produce a `merge_pull_request` next action.
- Backend merge calls should fail closed even if UI/kernel projection regresses.

## Native ABI sequencing

`demo:mvp` may require Electron native modules, while Node package tests require Node native modules.

- Before real desktop demo validation, run the desktop native rebuild so `better-sqlite3` matches the Electron ABI.
- After Electron-native demo validation, switch back to Node ABI before running Node/Vitest tests that load `better-sqlite3`.
- Verify from the consuming package cwd, not the repo root. The repo root may not be able to `require("better-sqlite3")` if the dependency is package-scoped.
- A useful check from `packages/persistence` is:
  - `node -p 'process.version + " modules=" + process.versions.modules'`
  - `node -e 'require("better-sqlite3"); console.log("better-sqlite3 require ok")'`
  - `corepack pnpm --filter @skyturn/persistence run test`

## Parent/operator role

If the user says coding agents should write code, keep Hermes as the parent operator:

- Delegate every post-review code fix to a coding agent with exact file scope and tests.
- Hermes may write prompts and PR bodies, inspect diffs, run validation, and run review-only agents.
- Hermes should not hand-edit product code unless the user changes that instruction.
