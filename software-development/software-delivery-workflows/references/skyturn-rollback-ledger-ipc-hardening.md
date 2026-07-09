# SkyTurn rollback ledger / IPC hardening

Use this when implementing or reviewing SkyTurn backend/Electron-side node rollback, repair, variant, checkpoint, and remote delivery gates.

## Durable rollback ordering
- Never let destructive local git operations outrun durable workflow evidence.
- Write `workflow.node.rollback_requested` before `git reset --hard`.
- Write `workflow.node.rollback_applied` only after reset succeeds.
- On local safety or reset failure, write `workflow.node.rollback_rejected` / manual-repair evidence.
- Make crash windows idempotent:
  - If reset already moved HEAD to the restore commit but `rollback_applied` is missing, retry should append the matching applied event instead of rejecting.
  - If crash happened after requested but before reset, retry should reuse the existing matching request rather than generate a second dangling rollback intent.
- Treat renderer-supplied rollback `requestId` as untrusted. If an idempotency key already exists, validate payload identity exactly before reset: lane, checkpoint, optional node, restore commit, local safety, and absence of terminal rollback event.

## Local git safety gates
- Local commit is not a remote side effect, but reset is allowed only under exact managed-worktree evidence.
- Require managed worktree identity, full restore commit SHA, recorded local commit evidence, exact current HEAD, clean/expected worktree, and exact current branch match.
- Verify branch with `git branch --show-current` or equivalent before reset. Detached or different branch means manual repair; do not reset.
- Serialize local commit creation and rollback reset with the same project/session mutation lock. Otherwise `git add/commit` can interleave with reset and corrupt evidence.

## Remote side-effect gates
- Remote operations must persist `workflow.remote_side_effect.requested` before the remote mutation and `completed` after the outcome is known.
- Unknown/ambiguous failures remain blockers. Only clear a failed remote request when `remoteMutationAttempted === false`.
- Before retrying any remote mutation, scan unresolved durable remote requests in the same project/session with overlapping affected lanes or session-wide scope, regardless of event kind.
- PR creation must require durable push evidence for the commit/branch it depends on; unresolved push requests or missing push evidence return typed manual-resolution/blocking responses.
- Push, PR create, PR merge, and main sync must revalidate evidence and rollback status under the same project/session mutation lock before calling remote helpers.
- Do not hide blocked/manual-resolution results behind a success-only IPC type. The public preload/persistence contracts must include typed blocked/manual-resolution result shapes, including `event: null` when no event was appended.

## Repair / variant successor ledger safety
- Before writing successor lane/edge/intent events, enforce checkpoint authority equivalent to workflow-kernel validation:
  - phase must be explicit;
  - repair requires `after` checkpoint;
  - variant requires `before` checkpoint;
  - checkpoint must belong to the target lane/node.
- Do not trust renderer-provided successor identity. Transactionally reject lane id, semantic key, self-loop/source identity, or checkpoint-intent conflicts before writing any event.
- Idempotent retry with the same intent and successor identity should return the existing result without adding new edges from current graph drift.

## Review checklist
- Check event ordering around every destructive or remote side effect.
- Check crash/restart retry behavior, not just happy path.
- Check project/session identity in in-memory locks and durable blockers.
- Check renderer/preload type shapes match every backend response path.
- Prefer focused source tests plus persistence replay tests when live Electron/GitHub smoke is unavailable; label that limitation clearly.