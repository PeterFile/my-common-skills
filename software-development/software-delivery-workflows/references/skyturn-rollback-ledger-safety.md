# SkyTurn rollback ledger and remote-side-effect safety

Use this when implementing or reviewing SkyTurn node/run rollback, checkpoint ledger, Electron IPC, delivery remote operations, or local worktree reset paths.

## Durable ordering rules

1. Remote side effects must get a durable blocker before the remote mutation starts.
   - Before `git push`, PR create, PR merge, or main sync, append a ledger event such as `workflow.remote_side_effect.requested` with operation id, event kind, lane ids or `sessionWide`, and evidence context.
   - On success, append the concrete remote evidence event (`workflow.delivery.pushed`, `workflow.pull_request.created`, `workflow.pull_request.merged`, `workflow.delivery.main_synced`) and then complete the remote-side-effect request.
   - Do not rely only on in-memory in-flight markers. They help same-process races but do not survive restart.

2. Ambiguous remote failures remain rollback blockers.
   - A remote command can mutate the remote and then fail while parsing stdout, writing evidence, broadcasting, or appending ledger state.
   - Only clear a durable remote blocker on `succeeded`, or on `failed` when there is explicit proof the mutation never happened (`remoteMutationAttempted: false` or equivalent).
   - Otherwise keep the request pending or mark it as unknown/manual-repair-required, and make kernel/persistence replay still block rollback.

3. Local filesystem rollback must be ledger-first and exact.
   - Persist `workflow.node.rollback_requested` before running destructive local reset/restore.
   - Run `git reset --hard` only after exact safety checks: managed worktree, SkyTurn-recorded local commit, full commit SHA, HEAD exact match, clean/expected worktree, matching lane and realpath worktree identity, no remote blockers.
   - Persist `workflow.node.rollback_applied` only after reset succeeds.
   - On failure, persist `workflow.node.rollback_rejected` or manual-repair evidence. Do not leave a destructive reset without durable rollback evidence.

4. Recheck after awaits.
   - If rollback evaluates eligibility, awaits async git/worktree checks, and then resets, another IPC may have started a push/PR in the await window.
   - Before writing rollback request and before reset, rematerialize/evaluate remote blockers again.
   - Prefer a small session/affected-lane mutex shared by rollback apply and remote mutation start.

5. Session-wide events must replay as session-wide.
   - If `workflow.delivery.main_synced` is intended to block rollback for the whole session, its durable payload must carry an explicit supported `sessionWide: true` shape, or omit lane identifiers consistently.
   - Add kernel/persistence round-trip tests; in-memory guards alone are not enough.

## Review checklist

- Is there any remote mutation before a durable blocking event?
- Can an ambiguous remote failure clear the blocker?
- Does rollback write request evidence before local reset and applied only after reset?
- Is the reset target a full recorded commit SHA, not `HEAD` or a branch ref?
- Does recorded commit proof require matching lane id and worktree identity/realpath?
- Is there a final blocker recheck after async local safety checks?
- Are repair/variant successor intent retries idempotent, or are conflicting retries rejected before writing extra edges?
- Do tests cover replay/restart behavior, not just live in-memory state?

## Validation pattern

Run focused backend/kernel gates after any such change:

```bash
corepack pnpm --filter @skyturn/workflow-kernel run build
corepack pnpm --filter @skyturn/persistence run test
corepack pnpm --filter @skyturn/desktop run test
corepack pnpm --filter @skyturn/workflow-kernel run test
corepack pnpm --filter @skyturn/persistence run typecheck
corepack pnpm --filter @skyturn/desktop run typecheck
corepack pnpm --filter @skyturn/workflow-kernel run typecheck
git diff --check
```

The workflow-kernel build can be necessary before persistence tests because package exports may read `packages/workflow-kernel/dist` instead of source.