# Workflow optimization addendum (2026-04-24 / 2026-04-25)

This reference consolidates recent workflow-optimization plans into the durable workflow skill.
Do not treat the original repo-local `.hermes/plans/*.md` files as the authoritative long-term workflow source after this file exists.

Source plans consolidated here:
- `2026-04-24_180454-main-agent-conveyor-plan.md`
- `2026-04-24_182000-graphite-workgroup-operating-model.md`
- `2026-04-25_121257-ci-throughput-validation-reset.md`

## 1. Authoritative rule

If a workflow / CI / gate / continuation rule is expected to be reused in future delivery, it belongs in this skill (SKILL.md or a linked reference like this file), not only in a repo-local `.hermes/plans/...` artifact.

Use `.hermes/plans/...` only for:
- one-off analysis
- draft task breakdowns
- temporary exploration that is not yet an approved reusable operating rule

If a plan produces a durable operating rule, migrate the durable summary into the relevant workflow skill promptly.

## 2. Main control-plane rules

Durable takeaways from `main-agent-conveyor-plan`:

### 2.1 Controller artifacts are the continuation truth source
Do not rely on chat transcript memory as the control plane.
Keep repo-local control artifacts under `.hermes/orchestrator/`.

Minimum durable artifacts:
- `workgroups.json` or equivalent controller state file
- `handoffs/*.md` fresh-continuation summaries

Each live lane/workgroup should record at least:
- worktree path
- active branch / stack top
- owner agent
- current lifecycle state
- local health state
- active background `session_id` if any
- strongest evidence
- exact next action

### 2.2 Every lane gets one exact next action
Never leave a lane with fuzzy text like "continue" or "follow up later".
Use precise successors like:
- rerun exact blocker test
- run independent review
- push rebased head
- wait on PR check for current SHA
- clean up merged worktree

### 2.3 Background commands are signals, not orchestration
For long commands such as Codex runs, browser smoke, full gates, or broad build/typecheck:
- run them in background when appropriate
- use `notify_on_complete=true`
- record `session_id` immediately
- record the successor action immediately

`notify_on_complete` is only a signal.
True continuation still requires controller artifacts and a wake-up path.

### 2.4 60/60 fresh continuation rule
When the session is near practical context/turn limits:
- stop opening new large work
- write a compact handoff summary first
- resume from the handoff + controller state in a fresh continuation

## 3. Workgroup operating model

Durable takeaways from `graphite-workgroup-operating-model`:

### 3.1 Prefer theme worktrees, not infinite micro-worktrees
Do not scale by `1 tiny slice = 1 long-lived worktree` forever.
For this repo, the durable direction is:
- worktree = theme/workgroup boundary
- Graphite stack = ordered dependent slices inside that theme worktree

Typical theme split:
- world-runtime
- supervision-accountability
- ops-replay / workflow

### 3.2 Responsibility split
- Hermes main agent: delivery director / control plane
- theme lead / reviewer agents: technical ownership and review
- Codex: implementation inside assigned worktree/branch
- Linear: lifecycle truth
- Slack: notification / broadcast only
- GitHub / Graphite: code dependency and merge truth
- local controller file: execution continuation truth

### 3.3 Keep lifecycle state tiny; keep health local
Lifecycle states should stay simple and external, e.g.:
- Todo
- In Progress
- In Review
- Blocked
- Done

Execution health stays local and diagnostic, e.g.:
- running
- waiting
- no-op
- stalled
- drifted
- degraded
- baseline-red

Do not pollute project-management state with dozens of transient technical states.

### 3.4 Truth-source order
When signals disagree, prefer:
1. local git/worktree state + local reruns
2. GitHub / Graphite PR head and checks
3. Linear lifecycle status
4. Slack messages

Slack is never the truth source.

## 4. Validation-layer reset

Durable takeaways from `ci-throughput-validation-reset`:

### 4.1 The core problem is unlayered verification
Do not treat every small semantic fix as a full release-grade synchronous gate.
That pattern kills throughput and traps agents in:
- fix one blocker
- wait 30-40 minutes
- get one more blocker
- rerun again

### 4.2 Use three validation layers

#### Layer A — local fast loop
Purpose:
- local iteration
- review-blocker repair
- smallest semantic proof

Budget target:
- usually under 5 minutes

Typical content:
- focused vitest files
- focused selector / App / DetailsPanel / projector tests
- single Playwright file or grep when needed
- targeted typecheck only when touched contracts justify it

Rule:
- do not default to full browser smoke for every small change

#### Layer B — required PR gate
Purpose:
- minimum credible pre-merge gate

Budget target:
- usually under 10-15 minutes

Typical content:
- `backend:test`
- `web:test`
- `web:typecheck`
- `web:build`
- one canonical browser smoke path

Rule:
- if two browser-smoke paths are still required, they must be split into parallel jobs rather than serialized in one long job

#### Layer C — async full gate
Purpose:
- full regression coverage
- second browser-smoke mode
- extended smoke / nightly / post-merge coverage
- slow environment-drift detection

Rule:
- Layer C protects completeness; it should not synchronously block every tiny PR edit

### 4.3 Independent review comes before the expensive full gate
Bad loop:
- run long gate
- then review
- then get blocker
- rerun long gate

Preferred loop:
1. run Layer A
2. do independent review immediately
3. classify findings once
4. fix the blocking findings in batch
5. run Layer B once when the slice is candidate-ready

### 4.4 Review findings must be graded
Use a durable 3-way split:
- `P0 merge blocker`
- `P1 should-fix-in-PR`
- `P2 follow-up`

Rules:
- only P0/P1 block the current PR
- P2 becomes follow-up work, not an excuse to keep rerunning full release-grade gates on the same tiny slice

### 4.5 Full-gate rerun budget
Per slice / per PR, aim for:
- 1 candidate-ready full validation
- at most 1 more full rerun after fixing review blockers

If new blockers keep appearing after that:
- re-scope the slice
- split follow-up work
- or correct the review boundary

Do not stay in an unbounded heavy rerun loop.

### 4.6 Stop conditions for agents
- If the change is only a small selector / test wording / tiny semantic fix, do not auto-upgrade straight to dual full browser smoke.
- If independent review still produces brand-new blockers after repeated repair cycles, treat that as a scope or review-boundary problem, not as a reason to keep brute-forcing full reruns.
- If full-gate cost is far larger than the change cost, shrink the gate or defer the broader coverage to Layer C.

## 5. CI optimization priorities for this repo

Recent verified repo facts behind these rules:
- current CI is serialized in one job
- both `push` and `pull_request` can run on the same PR branch
- Playwright is configured with `fullyParallel: false` and `workers: 1`
- preview smoke rebuilds even after `web:build`
- the browser smoke wrapper currently targets the large smoke bundle directly

Durable optimization priorities:
1. eliminate duplicate `push` + `pull_request` PR work where possible
2. split browser jobs into parallel jobs if both modes still exist
3. prefer one canonical browser-smoke path in required PR gate
4. move the second browser-smoke mode to nightly / post-merge when feasible
5. reuse build artifacts; do not rebuild preview unnecessarily inside the smoke wrapper
6. maintain a `core` vs `extended` smoke split so PR gate stays high-signal and bounded
7. increase Playwright parallelism cautiously (`workers: 2` first, then re-measure)

## 6. Practical usage rule for future workflow changes

When a new workflow-optimization idea appears:
1. inspect live repo facts first
2. decide whether the idea is one-off or durable
3. if durable, update the workflow skill (SKILL.md or a linked reference file)
4. only leave it in `.hermes/plans/...` if it is still draft analysis and not yet approved as durable workflow policy

## 7. What this file does not change

This reference does not itself rewrite repo code or GitHub workflows.
It only upgrades the durable workflow operating guidance so future runs stop depending on repo-local plan files for reusable policy.