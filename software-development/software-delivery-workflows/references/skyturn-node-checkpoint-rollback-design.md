# SkyTurn node checkpoint and rollback design

Use this when designing SkyTurn node selection, node-level adjustment, fork/variant flows, repair lanes, or rollback semantics.

## Upstream mechanisms checked

### Hermes Agent checkpoints

Hermes checkpoints are filesystem safety nets, not workflow graph semantics.

- Opt-in via `hermes chat --checkpoints` or `checkpoints.enabled: true`.
- Before file-mutating tools or destructive terminal commands, Hermes snapshots the working directory at most once per conversation turn.
- Storage is an internal shared shadow git store under `~/.hermes/checkpoints/store/` with per-project refs and indexes; the user's project `.git` is not touched.
- `/rollback diff <N>` previews changes from a checkpoint.
- `/rollback <N>` restores tracked files from the shadow store and first creates a pre-rollback snapshot so the undo can itself be undone.
- Good lesson for SkyTurn: use filesystem checkpointing as a lower-level safety net, but do not expose tool-call-level snapshots as the main product model.

### OpenAI Codex rollback/backtrack

Codex rollback is thread/history rollback, not filesystem rollback.

- `ThreadRollback { num_turns }` drops the last N user turns from in-memory/persisted thread context.
- Codex protocol explicitly says it does not revert local filesystem changes; clients are responsible for undoing disk edits.
- The TUI backtrack flow stages a rollback request, waits for core success, and only then trims the local transcript. This prevents UI state from getting ahead of authoritative thread state.
- Codex also supports thread fork: a new thread can be forked from existing thread history with cwd, sandbox, runtime workspace roots, model/provider, and other config.
- Good lesson for SkyTurn: separate graph rollback, agent-thread rollback/fork, and filesystem/worktree rollback. Do not pretend one mechanism covers all three.

## SkyTurn product model

User-visible checkpoint granularity should be the node/run boundary, not individual tool calls.

Each node/run should expose two durable checkpoint concepts:

- `beforeCheckpoint`: state before the node starts, including upstream completed evidence, base commit/worktree, selected execution target, agent thread/session start, and input context.
- `afterCheckpoint`: state after the node finishes, including run evidence, changeset/reconciliation, validation evidence, local commit evidence, and any delivery evidence.

## Node selection interaction

Selecting a card should not open the modal. It should select the node as the composer target.

- The node modal/details should move behind a small More button in the card's top-right corner.
- The composer should show a selected-node pill with status and title.
- Do not drop users into a bare ambiguous input. Present explicit node actions first, then specialize the input placeholder.

Recommended action choices:

- `Repair this node`: starts from `afterCheckpoint` and asks an agent to fix or refine the current result.
- `Try another version`: starts from `beforeCheckpoint` and creates a sibling/variant node from the previous stable state.
- `Rollback this node`: rolls back the selected node and eligible downstream nodes at the workflow graph level.

## Rollback semantics

A SkyTurn rollback should preserve audit history. It should not delete events, run output, changesets, or evidence.

Default behavior:

1. Mark the selected node as rolled back/rejected.
2. Automatically cascade graph rollback to downstream nodes that depend on it.
3. Mark downstream nodes as `rolled_back_by_ancestor` or equivalent inactive/stale state.
4. Remove rolled-back nodes from scheduling/active path, but keep them visible/auditable.
5. If a new attempt is desired, fork a variant node from the selected node's `beforeCheckpoint`.

## External side-effect boundary

Do not automatically roll back nodes that have crossed a remote side-effect boundary.

For SkyTurn, remote side effects are the hard stop:

- pushed branch
- created PR
- merged PR
- synced main or equivalent remote/default-branch delivery

If a selected node or any downstream node has crossed this boundary, do not perform rollback on that node. Show that it has left the rollback-safe zone and route the user to a repair/revert PR flow instead.

Local commit handling can be more permissive:

- A local SkyTurn-created commit that has not been pushed may be handled if exact evidence proves the target commit and worktree state.
- In a managed worktree, if HEAD exactly matches the recorded local commit and there are no later changes, reset/restore to the `beforeCheckpoint` is acceptable after confirmation.
- On current branch, dirty worktrees, or HEAD mismatch, do not reset. Prefer a repair/revert lane.

## Implementation hardening checklist

For SkyTurn contract/kernel slices, do not start downstream backend/UI work until the contract slice has passed parent-side tests and review-only approval. Repeated review `BLOCK` findings are useful evidence; feed the exact findings back to the owning worker and rerun focused tests before stacking dependent branches.

When implementing node checkpoint rollback contracts:

- Keep `NodeStatus` stable unless every typed UI/backend mapping is updated in the same slice. Prefer a separate `NodeRollbackStatus` plus canonical mapping helper from lane status to rollback status so materializers do not guess.
- Rollback authorization must use explicit, auditable checkpoint fields. Defaults may be useful for display, but missing `phase`, `executionTarget`, lane/node identity, or restore target must not authorize rollback.
- Eligibility should return the resolved checkpoint and restore target, not force backend/UI callers to rederive `headCommit ?? baseCommit` independently.
- Duplicate checkpoint events should preserve immutable first-known identity/commit/worktree/run boundaries, fill missing fields from later authoritative events, and merge `evidenceRefs` additively. Never let `evidenceRefs: []` erase existing audit refs without an explicit tombstone contract.
- `rollback_requested` should record intent/eligibility only; `rollback_applied` is the state-mutating event and must re-check remote side effects, local rollback safety, checkpoint ownership, and restore target.
- Rollback-derived repair/variant/fork successors must be order-insensitive. If rollback is applied before the successor intent arrives, the intent should be able to restore the trusted successor subgraph from inactive to schedulable state; generic downstream nodes stay inactive.
- If both `successorLaneId` and `successorSemanticKey` are present, require both to match the same lane. Only fall back to single-field matching when only one field exists.
- Remote side effects must block both requested and applied paths, including session-wide events with no lane id.

## Design pitfall

Do not conflate these layers:

- workflow graph rollback: which nodes are active, stale, rejected, or rescheduled;
- agent thread rollback/fork: what conversation/history the agent continues from;
- filesystem/worktree rollback: what files and commits exist on disk;
- remote delivery rollback: PR/revert/merge-management, which is not automatic rollback.

If the design cannot state which layer an action mutates, it is too vague to implement safely.

## Contract/kernel implementation review lessons

When implementing this model in browser-safe contracts and workflow-kernel code, enforce these invariants before downstream UI/backend slices stack on the contract:

- Treat `rollback_requested` and `rollback_applied` as distinct events. A request records intent/eligibility only; only an applied event with valid backend evidence may mutate lane/node active state.
- Validate checkpoint identity before mutation. Rollback should resolve the authoritative target from a matching `before` checkpoint; do not treat arbitrary `nodeId` as `laneId`, and reject wrong-phase, wrong-lane, missing, or stale checkpoint references.
- Make explicit safety failures hard blockers. `localRollbackSafe === false` and remote side effects must reject both request and applied paths; a remote side effect arriving between request and apply must still block apply.
- Preserve audit history while preventing resurrection. Late segment/evidence/commit/PR-check events may still be retained, but must not change `rolled_back`, `inactive`, or `rejected` lanes back to running/completed.
- Represent remote side effects without guessing. Support `affectedLaneIds`; if a remote side-effect event has no lane identity, treat it as session-wide and surface that in the eligibility/ref shape.
- Keep checkpoint upsert conservative. Duplicate or partial checkpoint events must not erase evidence refs or flip phase/source through defaults.
- Define scheduling for derived follow-up lanes narrowly. Generic dependencies on rolled-back lanes are not satisfied; only repair/variant/fork lanes that can prove they derive from the corresponding checkpoint/intent may proceed.
- Run review-only before starting dependent slices. A contract review block is not paperwork: fix it and re-run focused package tests/typechecks before creating backend/UI worktrees stacked on the contract.

## Integration closeout review lessons

When integrating SkyTurn node checkpoint/rollback slices, run a fresh review-only pass on the integrated diff after demo/runtime validation, not just on child branches. Final review should inspect the real merged projection/IPC/UI path and can expose gaps that slice tests miss.

Hardening points from integration review:

- Production run boundaries must emit checkpoints. Do not rely on hand-written test `workflow.node.checkpoint_recorded` events. The scheduler should record a `before` checkpoint when a lane/run starts, and run-result persistence should record an `after` checkpoint with run/segment/evidence/changeset/artifact refs.
- Repair and variant are not rollback actions. A repair successor from an `afterCheckpoint` and a variant/fork successor from a `beforeCheckpoint` must be schedulable without first applying rollback. Keep a guard that checkpoint successors need explicit incoming dependency edges, but do not gate them on `rollbackStatus === rolled_back`.
- Preserve rollback-cascade semantics separately. A successor depending on a rolled-back lane is schedulable only when it is a trusted checkpoint successor for that lane; generic downstream nodes must remain inactive/stale after cascade.
- Selected-node instructions must reach the executor. It is not enough to persist `instruction` in repair/variant/rollback events and projection intents; the materialized successor node context or prompt input must carry the instruction into the Codex/Hermes run.
- Do not elevate commit permissions from display text. Commit-lane sandbox/prompt policy must use trusted canonical lane metadata such as `laneKind`/runtime policy, not title regexes like `/commit/`, because titles are user/model-influenced display text.
- Do not use prompt text as a security boundary. If a trusted workflow projection says a lane is `read-only`, renderer/runtime helpers must not upgrade browser/screenshot/validation/review lanes to `danger-full-access` based on title text. Artifact-writing lanes should get an explicit kernel/runtime policy such as `workspace-write`; `danger-full-access` is reserved for explicit commit/delivery lanes that need git metadata writes.
- Production checkpoints must reflect actual run/worktree identity, not session target placeholders. Do not record `worktreePath: "."`, branch names, or selected refs as rollback-authorizing checkpoint facts for `new_worktree` runs. Use the real managed worktree path/id/gitdir and full HEAD SHA when available; when unavailable, omit the optional fields rather than forging display-friendly values. Exact-head rollback gates depend on these fields being authoritative.
- Treat `demo:mvp` failures where all lanes exit 0 but acceptance is false as product evidence, not flaky output. Inspect the acceptance predicate and generated run evidence; prompt policy, dirty temp repos, screenshot parse failures, checkpoint identity drift, and graph hygiene are common integration bugs.
