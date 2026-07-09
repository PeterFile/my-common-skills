# CI, validation, review, and duplicate-check playbook

Load when: choosing validation commands, running Codex review, triaging GitHub checks, duplicate `push`/`pull_request` runs, browser smoke CI failures, or avoiding full-gate loops.
Keywords: Layer A, Layer B, Layer C, review, P0, P1, P2, full gate, browser smoke, duplicate CI, same-SHA, push, pull_request, Graphite, merge queue.

## 1. Correct local loop

Preferred order:
1. implement smallest scoped change
2. run Layer A focused validation
3. run independent review immediately
4. classify review findings P0/P1/P2
5. fix P0/P1 in batch
6. rerun only impacted Layer A
7. re-review the changed area
8. run Layer B once when candidate-ready
9. push/open PR or submit stack
10. let GitHub/Graphite/merge queue handle required heavy gates
11. Layer C runs async/nightly/post-merge

Do not run long full gates before review by default. That creates the slow loop: long gate -> review blocker -> small fix -> long gate again.

## 2. Validation layers

### Layer A — local fast loop
Purpose:
- implementation iteration
- review blocker repair
- smallest semantic proof

Budget target: usually under 5 minutes.

Allowed examples:
- touched backend test
- touched Vitest file/case
- focused App/DetailsPanel/projector test
- single Playwright grep/file when the change touches real browser keyboard/request/runtime behavior
- `web:typecheck` only when touched TypeScript contracts justify it

Forbidden defaults:
- no default `pnpm test:all` before review
- no default dual browser smoke for small selector/test/copy changes
- no full-gate escalation just because one focused test changed

### Layer B — required PR gate
Purpose:
- minimum credible pre-merge validation

Target budget after CI optimization: 10-15 minutes.

Recommended shape:
- `pnpm backend:test`
- `pnpm web:test`
- `pnpm web:typecheck`
- `pnpm web:build`
- one canonical browser smoke path

Default canonical browser smoke should usually be preview because it is closer to production output. If dev smoke is empirically higher signal for a touched harness/proxy path, justify that explicitly.

If both preview and dev smoke remain required, split them into parallel jobs. Do not serialize them in one long job.

### Layer C — async full gate
Purpose:
- full regression
- second browser-smoke mode
- extended smoke
- nightly/post-merge/merge queue synthetic merge validation
- environment drift detection

Layer C protects completeness. It should not synchronously block every tiny PR edit.

## 3. Independent review policy

Run review after Layer A, before expensive gates.

Review output must classify findings:
- `P0 merge blocker`
- `P1 should-fix-in-PR`
- `P2 follow-up`

### P0
Examples:
- acceptance not met
- correctness/security/data-loss issue
- widened request surface
- changed surface validation red
- stale base/head SHA
- hot-file sibling merged but branch not rebased
- diff no longer slice-pure

P0 blocks current PR.

### P1
Examples:
- bounded current-scope quality/test/a11y issue
- missing regression directly tied to this PR
- small maintainability issue likely to break the current surface

P1 normally blocks current PR unless fixing it would materially expand scope; then explicitly downgrade or split.

### P2
Examples:
- adjacent cleanup
- broader hardening
- unrelated baseline red
- future CI optimization
- nice-to-have refactor

P2 does not block the current PR. Create Linear follow-up or PR comment. Do not spend full-gate budget on P2.

Do not trust a reviewer's severity label mechanically. If a finding is labeled P2 but describes current-scope correctness, API/write-boundary compatibility, evidence/provenance validation, stale-vs-live truthfulness, request-surface widening, or a regression against inputs the store/UI already accepts, promote it to P1 for the current PR. Fix it with a focused regression, rerun impacted Layer A, and re-review before push/PR-ready.

## 4. Full-gate rerun budget

Default budget per PR:
- candidate-ready Layer B: 1 run
- after P0/P1 fixes: at most 1 Layer B rerun
- GitHub failed duplicate job/run rerun: at most 1 before deeper triage

If the budget is exhausted and new blockers keep appearing:
- rescope the slice
- split P2/follow-up work
- create separate unblocker for unrelated baseline red
- ask for explicit override if the risk is strategic

Do not stay in an unbounded heavy rerun loop.

### Vitest full-suite timing failures

For `pnpm web:test` / full Vitest failures that are timeouts in a long `App.test.tsx` case:
1. rerun the exact failing `-t "..."` selector on the feature worktree
2. rerun the same exact selector on clean current `master`
3. if both exact runs pass and the failure is outside the slice diff, classify the full-suite red as a timing/full-suite-load anomaly, not a proven branch regression
4. still do not call Layer B green until a rerun of the required Layer B command passes, or a separate minimal baseline/unblocker is cut and landed
5. do not patch feature code just to appease one unconfirmed full-suite timeout
6. if cutting a test-only timeout unblocker, make the diff boring and auditable: add a local per-test timeout only to the proven long `it(...)` cases, do not change assertions, fixtures, helper logic, request expectations, or product code
7. be careful delegating mechanical timeout edits to Codex: it can over-apply `, 10000` to unrelated object/function closures when the prompt says “add third argument to these tests”. Always inspect `git diff` before validation/commit; if any non-`it(...)` block changed, kill/reset and apply a surgical patch manually or with exact old-string context.
8. for a fresh unblocker worktree, verify package binaries before interpreting test results. `ERR_PNPM_RECURSIVE_EXEC_FIRST_FAIL Command "vitest" not found` usually means the worktree lacks linked/installed `node_modules`, not that the timeout fix failed; fix dependencies first, then rerun the same focused selectors and full `pnpm web:test`.

Record in PR body / controller:
- Layer A commands/results
- review verdict
- P0/P1 status
- P2 follow-ups
- Layer B run count
- current head SHA
- exact next action if red

## 5. CI optimization priorities for metaverse-office-web

Immediate throughput fixes:
1. remove duplicate PR branch work from `push` + `pull_request` where possible
2. split the single CI job into parallel jobs
3. keep only one canonical browser smoke in PR-required Layer B if feasible
4. move the second smoke mode to nightly/post-merge/merge queue Layer C
5. if both smoke modes remain required, run them in parallel

Cost reduction:
1. reuse `web:build` artifacts; do not rebuild preview inside smoke wrapper when CI already built
2. split smoke into `core` vs `extended`
3. start Playwright concurrency with `workers: 2`; measure flake before increasing
4. upload Playwright artifacts and print exact repro commands on failure

Future improvements:
- path filters
- flake telemetry
- historical CI duration dashboard
- bounded automatic failed-job rerun policy

## 6. Duplicate CI and same-SHA triage

Common pattern: the same PR head SHA has both `push` and `pull_request` runs.

Rules:
- do not classify the PR from aggregate status alone if duplicate runs disagree
- inspect current PR head SHA first
- inspect job/step metadata for both duplicate runs
- if one sibling duplicate is still in progress, wait for it to settle before rerunning or rewriting code
- if PR-relevant run is green and only duplicate push run is red, treat as flake candidate; rerun the failed duplicate job/run
- if push succeeds but pull_request fails, reproduce the exact failing local test before changing code
- if both fail on unrelated changed surfaces and local exact repro is green, treat as flake candidate and rerun failed jobs/runs once
- if restack/rebase/force-push changes the head SHA, ignore old SHA checks completely

Use GitHub job/check-run details, not stale combined status, as the decision source.

## 7. Graphite / merge queue heavy gate

For stacked PRs:
- every PR needs Layer A evidence and review
- Layer B should be required at PR/stack readiness
- Layer C or old `pnpm test:all` belongs at merge queue / synthetic merge / nightly level when available
- after a lower stack PR merges, restack/rebase remaining PRs and wait only on the new head SHA

Queue red classification:
- changed-surface red -> return to the responsible PR
- unrelated baseline red -> freeze queue and create an unblocker slice
- flake -> rerun failed job/run once with evidence

Do not contaminate unrelated PRs with baseline/unblocker fixes.