# SkyTurn checkpoint/rollback contract hardening

Use this when implementing or reviewing SkyTurn node/run checkpoint, rollback, repair, variant, or workflow-kernel contract changes.

## Lesson
For checkpoint/rollback work, passing focused tests is not enough if the public contract still lets UI/backend guess. Repeated review-only `BLOCK` findings in this class usually point at real contract ambiguity. Keep downstream slices stopped until the contract review is approved.

## Contract rules that caught bugs

- Keep existing user-facing status unions stable unless every materializer is updated in the same slice. If `FlowLane.status` is consumed directly by UI/backend, do not add rollback terminal values there and expect a helper to save it later. Prefer a separate `rollbackStatus` field plus a canonical projection helper.
- Checkpoint fields used for authorization must distinguish explicit event facts from normalized defaults. Defaults can be useful for display, but rollback eligibility must require explicit authority for fields such as `phase` and `executionTarget`.
- Rollback restore identity must be unambiguous. Do not let a rollback restore ref fall back from `headCommit` to broader metadata such as `baseCommit`; the backend/UI must see the exact restore commit the kernel validated.
- `rollback_applied` should be replay-safe. Always look up the prior request by `requestId`/`intentId`, merge explicit payload fields over the prior request fields, then re-run current eligibility checks. Do not disable fallback just because an applied event contains one target-ish field such as `nodeId`.
- Remote side effects may be represented at top level or under `payload.evidence`. Block rollback if selected or downstream lane ids appear in either location, including `affectedLaneIds`; also test the inverse case where unrelated lane ids do not block rollback.
- Rollback successor lanes must not run on the old graph state. A repair/variant/fork successor is schedulable only after the target lane is actually rolled back, even if the target was previously `completed` or the successor lacks an incoming edge.
- Successor identity and target identity must be explicit. Avoid private semantic-key fallback conventions. Use explicit `successorLaneId` and/or `successorSemanticKey`; if both are present, both must match. A requested repair/variant/fork intent must also resolve to a concrete target `laneId`; lane-less successor intents should be rejected rather than left as inert `requested` records.
- Use discriminated unions for checkpoint intents. Rollback intents and successor intents have different invariants; a single wide interface lets UI/backend guess which fields are required.
- Keep rejected rollback attempts on the intent, not as terminal lane state. Legacy `rollbackStatus: "rejected"` must not block scheduling, completion gates, or later status updates; only `rolled_back` and `inactive` are terminal lane rollback states.
- Rollback cascade must preserve only trusted successor subgraphs and reset stale `running`/`completed` successor state back to a schedulable state. Generic downstream stays inactive/stale. For fan-in descendants, restore only when all affected incoming dependencies are already preserved or explicitly satisfied by the rollback-derived path.
- Persist rollback tombstones for every affected lane id, not only lanes declared at apply time. Late-declared downstream lanes must inherit inactive rollback state; trusted successor restore should clear tombstones only for the restored successor subgraph.
- Late events must not erase audit history. Late `lane.declared`, run/evidence events, or duplicate checkpoints must not clear output/evidence refs, mutate immutable checkpoint identity, or resurrect rollback-terminal lanes.
- Review/commit gates must ignore stale evidence from rolled-back/inactive/rejected lanes. Evidence is retained for audit, not for scheduling new active work after rollback.

## Validation checklist

For this class of slice, include focused tests for:

1. Missing, wrong-phase, wrong-lane, lane-less, and defaulted-authority checkpoints.
2. `rollback_requested` vs `rollback_applied` separation, including applied-by-request-id replay.
3. Remote side-effect blocks for push, PR created, PR merged, main synced, top-level and nested `evidence.affectedLaneIds` shapes.
4. Local rollback unsafe blocks.
5. Duplicate/partial checkpoint upsert: fill missing fields, merge evidence refs, never overwrite explicit commit/worktree/identity fields.
6. Rollback successor scheduling before and after rollback, with and without graph edges, with explicit successor identity, with resolved target lane, and with fan-in dependencies that should stay inactive.
7. Late event replay after rollback: segment/evidence/PR-check/lane-declared cannot resurrect or erase history; late-declared downstream lanes inherit rollback tombstones.
8. Canonical mapping from kernel lane rollback state to `CanvasNode.status` plus `rollbackStatus`, including rejected attempts staying non-terminal.
9. Type-level contracts: discriminated unions reject impossible intent shapes, and package-level typechecks catch cross-package contract drift before backend/UI slices stack on top.
