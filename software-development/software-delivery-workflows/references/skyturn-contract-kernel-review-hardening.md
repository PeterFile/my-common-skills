# SkyTurn contract/kernel review hardening

Use this when a SkyTurn slice changes browser-safe contracts or workflow-kernel projection semantics, especially before stacking backend/UI work on top of the contract branch.

## Pattern

1. Keep downstream work stopped until the contract/kernel slice has a clean review-only `APPROVE`.
2. Treat repeated review-only `BLOCK` results as design signal, not churn. Feed each exact finding back to the implementation worker and add a targeted regression before broad validation.
3. Run parent-side focused gates after every repair:
   - `corepack pnpm --filter @skyturn/project-core run test`
   - `corepack pnpm --filter @skyturn/workflow-kernel run test`
   - `corepack pnpm --filter @skyturn/project-core run typecheck`
   - `corepack pnpm --filter @skyturn/workflow-kernel run typecheck`
   - `git diff --check`
4. Rerun review-only after every post-review edit. Do not claim the slice is ready from tests alone.

## Durable design lessons

- Do not expand a stable UI/backend-consumed status union with terminal lifecycle states unless every materializer is updated in the same slice. Prefer a stable base status plus an explicit orthogonal field, e.g. `rollbackStatus`, with a canonical projection helper.
- Rejected rollback is an intent outcome, not a terminal lane state. `rejected` must not block scheduling, completion gates, or later lane updates unless the product explicitly models it as terminal.
- Lifecycle events should merge with prior request state by `requestId`/`intentId`. For `applied` events, load prior request fields first, then let explicit payload fields override individual fields; keep mismatch checks and preserve attribution to the requested target.
- If rollback applies to lane ids that are not declared yet, persist tombstones/overrides in projection. Late lane declarations must inherit rollback inactive/rolled-back state unless a trusted successor restore explicitly clears that lane.
- Successor recovery after rollback must be conservative. Restore only explicit repair/variant/fork successor subgraphs, and do not reactivate fan-in descendants whose affected incoming dependencies remain inactive.
- Checkpoint authority matters. Defaults used for display (`phase`, execution target, etc.) are not authorization. Store/export explicitness and require explicit authority for rollback/repair/variant/fork decisions.
- Remote side-effect blocking must inspect both top-level event fields and nested evidence lane ids, and should include negative tests where unrelated side-effect lanes do not block rollback.

## Review prompts

For uncommitted slice diffs, tell review-only agents to inspect `git diff` and `git diff --stat`, not only `<base>...HEAD`, because uncommitted worker diffs otherwise look empty.
