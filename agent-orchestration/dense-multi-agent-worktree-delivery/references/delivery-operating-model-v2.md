# Delivery operating model v2

Load when: starting or resuming metaverse-office-web delivery; choosing between workgroup/Graphite, single-slice, or closeout mode; optimizing throughput.
Keywords: workgroup, Graphite, mode selector, WIP, batch cadence, controller, handoff, Definition of Done, Linear, Slack, GitHub, local truth.

## 1. Intent

This is the durable high-throughput operating model for metaverse-office-web delivery.
The default posture is no longer `one tiny slice -> one worktree -> full gate -> review -> rerun full gate`.
The default posture is:
- adaptive parallel workgroups
- theme worktrees
- Graphite or ordered PR stacks where useful
- layered validation
- independent review before expensive gates
- exact continuation state in repo-local controller files
- truthful Linear/Slack/GitHub closeout

The goal is large-company delivery discipline: fast local loops, narrow review loops, small PRs, strong merge discipline, and no uncontrolled validation churn.

## 2. Mode selector

Choose exactly one mode before acting.

### Mode A — Workgroup / Graphite batch mode (default)
Use when:
- the user asks to continue product progress without naming a single hotfix
- no unowned urgent closeout backlog is hiding merge/rebase/CI truth
- multiple adjacent slices can move in parallel across themes without unmanaged hot-file collisions

Rules:
- worktree = theme/workgroup boundary
- Graphite stack or ordered branches = dependent slices inside that theme
- one Linear issue per slice
- Slack sends batch start / PR-ready digest / merge-done digest, not noisy internal chatter
- each lane has one exact next action in controller state
- WIP rate is intentionally controlled by Hermes from live throughput evidence, not by a fixed default cap

Typical themes:
- world-runtime
- supervision-accountability
- ops-replay-workflow
- hotfix-closeout when needed

### Mode B — Single-slice mode
Use when:
- the user names one issue, PR, bug, CI failure, or hotfix
- the change is intentionally isolated
- Graphite/workgroup setup would add overhead

Rules:
- still use Linear-first tracking unless doing truthful audit/backfill
- still use Layer A -> review -> P0/P1 fix -> Layer B
- single-slice mode is not the default for ongoing product throughput

### Mode C — Closeout / audit mode
Use when:
- open PRs, pending CI, sibling rebase needs, stale worktrees, or premature Linear/Slack states exist
- the user says continue/finish/close out and there is already work in flight

Rules:
- do not open new implementation before auditing existing delivery state
- GitHub PR merged state + actual master commit is merge truth
- local worktree state and current PR head SHA are stronger than remembered chat/process IDs
- correct premature Linear Done / Slack merge-done if GitHub/master disagree
- assign closeout backlog an owner and exact next action before expanding WIP; do not require a global stop when low-overlap capacity is available

## 3. Dynamic rate control

There is no fixed default upper limit for active workgroups, worktrees, stacked slices, open PRs, or local-only shadow work. Hermes owns the rate decision.

At each batch start and closeout checkpoint, choose the highest safe development rate from live evidence:
- available implementation agents and isolated worktree capacity
- review capacity and controller attention
- CI queue depth, required `pull_request` gate health, and known flaky lanes
- hot-file overlap and sibling rebase cost
- PR backlog, merge queue behavior, and required reviewer latency
- local machine load, dependency install cost, and background process count
- user urgency and rollback risk

Scale up until a measured bottleneck appears. Slow down only when a specific risk is named and assigned an owner, for example:
- direct PR gate is red or untriaged
- multiple siblings collide on hot files with no sequential closeout owner
- controller state no longer identifies exact next action per lane
- review backlog is hiding P0/P1 findings
- local machine or CI capacity is causing false failures/timeouts
- status sinks are unavailable and no degraded-mode authorization exists

CI-wait throughput rule:
- Waiting on one PR's `pull_request` gate does not automatically block new work.
- New work may continue if it is low-overlap, starts from current `origin/master`, has an isolated worktree, and is labeled with its exact merge dependency.
- Do not merge from same-head `push` results. Inspect the direct PR run/job; use only the fresh direct `pull_request` lane as merge gate.
- If Red Team/Delivery recommends slowing down but the user wants throughput, prefer local-only shadow lanes over stopping entirely. Do not push/open those lanes until their dependency chain is rebased, reviewed, and validated.

Hot-file rule:
- if multiple PRs touch the same hot file, close them sequentially
- after one sibling merges, rebase/restack each remaining sibling onto current master
- rerun required validation on the rebased head
- force-push/update PR
- ignore old SHA checks after a new head is pushed

## 4. Batch cadence

### Batch start
1. audit master, open PRs, worktrees, controller state
2. pick as many breadth-first slices across distinct themes as current Hermes rate control can safely drive
3. create/confirm Linear issues
4. post one Slack batch-start message
5. create or reuse theme worktrees
6. record exact next action per workgroup/lane

### Inner loop
1. implement with Codex or assigned agent
2. write/confirm RED proof when appropriate
3. run Layer A only
4. run independent review early
5. classify findings P0/P1/P2
6. batch-fix P0/P1
7. rerun impacted Layer A and re-review

### PR-ready loop
1. run Layer B only when candidate-ready
2. push branch / submit Graphite stack / open PR
3. update Linear to In Review
4. post PR-ready Slack digest or truthful degraded note

### Closeout loop
1. wait on current head SHA checks only
2. triage duplicate CI before modifying code
3. merge in dependency order
4. fast-forward local master
5. clean worktrees and branches
6. mark Linear Done
7. send Slack merge-done/backfill/correction
8. update controller state

### Batch finish
- all stack PRs merged, blocked, or explicitly deferred
- no stale controller action remains
- no stale worktree/branch remains
- next batch seeded if conveyor is empty and user has asked for continued advancement

## 5. Controller artifacts

Use repo-local controller artifacts under `.hermes/orchestrator/`.

Minimum fields per lane/workgroup:
- Linear id / slice title
- theme/workgroup name
- worktree path
- active branch / stack top
- owner agent
- lifecycle state (`Todo`, `In Progress`, `In Review`, `Blocked`, `Done`)
- local health (`running`, `waiting`, `no-op`, `stalled`, `degraded`, `baseline-red`, etc.)
- active process session id if any
- strongest evidence
- exact next action

Rules:
- every lane must have one exact next action
- `notify_on_complete` is a signal, not orchestration
- after starting a long background process, immediately record session id and successor action
- near session/context limits, write handoff first, then fresh continuation

## 6. Truth-source hierarchy

When signals disagree:
1. local git/worktree + local reruns
2. GitHub/Graphite PR head, stack order, checks, merged state
3. Linear lifecycle
4. Slack messages

Slack never owns truth.
Linear owns lifecycle only, not transient CI health.
Graphite/GitHub own code dependency and merge truth.
Controller files own execution continuation truth.

## 7. Definition of Done hierarchy

### Slice-local done
- scope implemented
- diff narrow and slice-pure
- Layer A green
- independent review complete
- P0/P1 fixed or explicitly scoped out
- evidence recorded in controller/Linear comment

### PR-ready
- branch or stack pushed
- PR opened with Conventional Commit title
- Linear issue linked in PR body
- validation summary present
- independent review verdict/comment present
- Layer B started or green according to repo policy
- Linear is `In Review`

### Merge-ready
- PR head SHA is current
- required checks green for that head or queue SHA
- review requirement satisfied
- no stale sibling/hot-file rebase remains
- no known P0/P1 blocker

### Delivery done
- PR merged into master
- local master fast-forwarded to merge commit
- worktree removed/pruned
- local/remote branch cleaned
- Linear `Done` with truthful note
- Slack merge-done/backfill/correction posted or degradation recorded
- controller lane marked done with evidence

### Layer C done
- async/nightly/post-merge full regression observed or scheduled
- failures are triaged into unblockers/follow-ups, not hidden or folded into unrelated PRs

## 8. Big-tech throughput rules

- Prefer trunk-stable, short-lived PRs, and Hermes-controlled adaptive WIP.
- Review early while the diff is cheap to change.
- Keep PRs small but not atomized into useless test-only churn.
- Preserve breadth-first product progress: each batch should cover world/runtime, supervision/accountability, and ops/replay/workflow when possible.
- Do not let hardening-only slices consume the whole conveyor unless master is actually blocked.
- Separate implementation complete from delivery-chain complete.
- Stop uncontrolled loops; when a slice burns its gate/review budget, split, defer, or rescope.