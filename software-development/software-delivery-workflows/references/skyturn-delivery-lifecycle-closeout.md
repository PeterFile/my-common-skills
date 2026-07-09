# SkyTurn delivery lifecycle closeout

Use this when closing a multi-slice SkyTurn delivery lifecycle integration branch after commit/push/PR/check/merge/sync/cleanup work.

## Durable lessons

1. Treat final review as invalidated by any later edit.
   - If you patch docs, contracts, or tests after a review-only APPROVE, rerun the final review before committing or opening the PR.
   - Do not rationalize a prior APPROVE over a changed diff.

2. Keep renderer event redaction compatible with UI hydration.
   - Electron `workflow:events` may redact raw payloads for safety.
   - If renderer UI must restore lifecycle state from the ledger, expose a narrow renderer-safe payload such as `payload.delivery` with only commit/push/PR/check/merge/sync facts.
   - Do not make UI hydration depend on raw `payload.evidence` if the real IPC strips it.

3. Validate lane kinds end to end, not just in tests.
   - If UI/Electron guards depend on a semantic lane kind like `pull_request`, it must exist in `WorkflowLaneKind`, `WORKFLOW_LANE_KINDS`, workflow-kernel `isWorkflowLaneKind`, normalization tests, and real projection materialization.
   - A test helper using `kind: "pull_request"` can hide that runtime normalization falls back to `implementation`.

4. Backend gates must match UI gates.
   - UI disabling a button is not enough.
   - IPC handlers for high-privilege actions such as merge/sync/cleanup must re-check recorded evidence server-side: PR number, expected head SHA, passed exact-head checks, and same PR/head merge evidence where applicable.
   - Review evidence policy must be enforced end-to-end: UI, Electron IPC, backend git helpers, workflow-kernel projection/scheduler/next-action, and persistence replay fixtures. Unknown or missing review evidence is not merge-ready; only `approved` and explicitly allowed `pending` review states may advance a merge gate.

5. Scope review findings precisely.
   - “Worktree adopt UI must default to merge and not expose cherry-pick” does not necessarily mean removing an existing backend compatibility path for cherry-pick.
   - Fix product-scope violations, but do not break public contracts unless the user asked for a contract removal.

6. Read-only review sandboxes can produce false validation failures.
   - Codex review-only may try to run Vitest and fail on temp/cache writes (`EPERM`, Vite SSR cache, localhost listen). Treat that as “review validation unavailable,” not as a product test failure, and rely on parent-run validations from a writable shell.

7. Real acceptance can invalidate an approved diff.
   - If `demo:mvp` or another real acceptance path exposes a root-cause issue after final review, fix the issue, run affected tests, rebuild any compiled workspace package consumed by the acceptance script, rerun the acceptance, and then rerun final review over the new diff.
   - Do not push/open the integration PR from a state where the latest real acceptance timed out, was killed, or ended with a known blocker. Earlier green logs are historical evidence, not proof of the current diff.

8. Tool-budget handoff must separate committed, dirty, and unverified state.
   - If forced to stop before PR creation, state whether the integration commit exists, which files are still dirty, which validations are current for the dirty diff, which acceptance runs are historical versus latest, and which external disposable PRs/branches remain open for manual cleanup.

## Minimum closeout loop

1. Verify live integration worktree status and diff.
2. Run affected package tests/typechecks after each root-cause fix.
3. Run real acceptance after fixes that affect runtime/demo behavior; if it imports compiled workspace packages, rebuild those packages first.
4. Run final review-only over the exact current diff.
5. If review finds P1/P0, fix only that root cause and go back to step 2.
6. After the final post-edit APPROVE and current real acceptance evidence, commit, push, and open PR.
7. Do not merge, close disposable smoke PRs, delete remote branches, or cleanup worktrees unless explicitly authorized.
