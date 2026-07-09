# SkyTurn Loop Engineering Delivery Wave

Use this reference when planning the next SkyTurn delivery wave after the project already has experimental Hermes/Codex execution, delivery lifecycle IPC, and node checkpoint rollback foundations.

## Product direction
SkyTurn should be treated as a long-lived Loop Engineering tool, not a demo shell. The core loop is:

```text
user need -> Hermes planning -> agent execution -> evidence writeback -> validation/CI/PR gate -> delivery -> rollback/repair/variant -> replay and continue
```

The product value is that the harness can answer, from durable evidence:

1. What is the next safe action?
2. Why can we not continue yet?
3. If this went wrong, what can be restored, and what evidence remains?

## Wave shape
Run delivery lifecycle and rollback/checkpoint work in parallel, but keep a small shared contract root. Prefer a mixed topology:

```text
main
  -> feature/loop-engineering-contracts
       -> feature/delivery-review-gates
            -> feature/delivery-next-action-ui
       -> feature/checkpoint-impact-projection
            -> feature/checkpoint-rollback-ui
       -> feature/repair-variant-loop-scheduling
       -> feature/rollback-recovery-idempotency
       -> test/loop-engineering-acceptance
```

Do not let two UI agents both freely edit `packages/ui-canvas/src/App.tsx` at the same time. Put shared projection/types in the contract root first, then stack dependent UI/backend slices on that root.

## Scoreable slices

### Contracts root
- Scope: project-core/workflow-kernel/persistence contracts for loop phase, next safe action, blockers, and recovery state.
- Avoid: UI redesign and new side effects.
- Validate: project-core, workflow-kernel, persistence tests plus typecheck and diff-check.

### Delivery review/gate hardening
- Scope: record PR reviews/checks, block merge on stale head, failing checks, or changes requested, and recover state after restart.
- Keep: PR creation as evidence, not completion; merge/sync/cleanup as separate explicit actions.
- Validate: git-worktree, desktop, persistence, workflow-kernel tests plus typecheck.

### Delivery next-action UI
- Scope: Changes tab displays commit/push/PR/check/review/merge/sync/cleanup state as ready/blocked/done/stale.
- Keep: no global console, no file tabs, no IDE UI; cleanup/delete branch still confirmed separately.
- Validate: ui-canvas tests and typecheck.

### Checkpoint impact projection
- Scope: rollback eligibility returns affected lanes, downstream inactive set, restore commit, remote blockers, and local safety.
- Keep: rollback never closes PRs, deletes branches, merges, syncs main, or hides evidence.
- Validate: workflow-kernel, persistence, desktop tests plus typecheck.

### Checkpoint/rollback UI
- Scope: selected-node composer and node detail affordances show checkpoint phase/source/commit and rollback impact/blockers.
- Keep: selection binds composer only; details still open through More; remote blockers route user toward repair/revert PR flow.
- Validate: ui-canvas tests and typecheck.

### Repair/variant loop scheduling
- Scope: repair from after checkpoint and variant from before checkpoint create schedulable successor lanes with regression/verification follow-up.
- Keep: rolled-back/inactive lanes not schedulable.
- Validate: workflow-kernel, persistence, desktop tests plus typecheck.

### Rollback recovery/idempotency
- Scope: rollback request durably records intent before destructive reset, handles crash/retry/dirty worktree/manual repair, and avoids duplicate state on repeated clicks.
- Keep: local commit rollback requires exact commit evidence and safe worktree identity.
- Validate: git-worktree, persistence, desktop tests plus diff-check.

### Loop acceptance
- Scope: acceptance scenarios for failure -> repair -> regression -> delivery; PR created not done; exact-head checks gate merge; rollback selected+downstream; remote side effects block rollback; replay has no side effects.
- Validate: root build/test/lint/typecheck and desktop `demo:mvp` when credentials are available. Disposable GitHub smoke remains opt-in only.

## Parent gate
Each slice must use an isolated branch/worktree, child agents must not commit/push/PR unless explicitly authorized, and the parent must inspect diff and run the relevant gates. Require review-only approval before stacking dependent implementation branches. Integration closeout must run root gates and the real desktop demo path when credentials permit.

For the contracts root specifically, do not treat a passing projector test as sufficient. Review and test the same safety predicate through every consumer that can advance the workflow:

- loop/next-action projection;
- scheduler dependency completion (`scheduleReadyLanes` / completed-lane sets);
- SQLite replay/persistence projection.

Exact-head PR evidence must block both visible next actions and downstream merge-lane scheduling after a newer push. A stale check lane may remain historically `completed`, but it must not satisfy merge dependencies for current scheduling.

When projecting selected-node rollback state, scope rollback intents to the effective selected lane. Do not let a latest rollback intent from lane A supply checkpoint id, node id, local-safety, or requested/applied status for selected lane B. Add kernel and persistence replay regressions for this class of selection-state leak.
