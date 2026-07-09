---
name: linear-slack-worktree-delivery-loop
description: High-throughput metaverse-office-web delivery controller using Linear, Slack, repo-local workgroups, GitHub, and Graphite-style stacked PRs.
version: 2.0.0
author: Hermes Agent
license: MIT
---

# Linear + Slack + workgroup delivery loop v2

> Archive note: this is a superseded source workflow kept for provenance and rare edge cases. Do not use it as the primary operating path. Start from `../SKILL.md` and `references/legacy-index.md`; migrate any still-valid compact rule into the current skill before relying on this archive repeatedly.

Use this skill for `metaverse-office-web` delivery when the user expects real project progress, not just isolated code edits. The default operating model is now high-throughput and bounded-parallel: theme workgroups, layered validation, early review, truthful closeout, and small PRs that do not get trapped in full-gate loops.

This skill replaces the old default of `one tiny slice -> one worktree -> full gate -> review -> full gate again`. That old flow is preserved only as a fallback and as a legacy archive.

## Source of truth for workflow policy

- Durable workflow / CI / gate / continuation rules belong in this skill or its `references/` files, not only in repo-local `.hermes/plans/...` artifacts.
- Treat `.hermes/plans/...` workflow notes as drafts unless migrated here.
- Before changing CI shape, validation policy, continuation policy, or delivery mode, load the relevant reference listed below.
- Full pre-refactor content is archived at `references/legacy/SKILL-2026-04-25-full-pre-refactor.md`; search it for historical edge cases, but do not use it as the primary operating path.

## When to use

Use when:
- repo is `metaverse-office-web`
- user asks to continue, advance, close out, unblock, or ship product work
- Linear / Slack / GitHub / Graphite / repo-local worktree state matters
- you are managing multiple agents, PRs, worktrees, or CI gates

Do not use this as permission to skip user constraints. Keep `master` clean; all code changes still go through branch + PR + review + merge discipline.

## Product strategy kernel

Delivery speed is not product direction. Before starting a new product batch, use the product strategy kernel in `references/product-strategy-kernel-notion-research-council.md`.

Hard rules:
- Notion is the vision/capability/decision/research map, not Linear/GitHub/Graphite execution truth.
- The main agent is facilitator/scribe/router/controller, not the sole product decider or top-down task dispatcher.
- Batch direction must come from a multi-agent council: Vision Steward, Operator Advocate, Product Strategy, Runtime/Evidence Architect, Frontend/World UX, QA/Replay, Security/Cost, Red Team, and Delivery/Graphite Captain as needed.
- A healthy agent team is not just the main agent decomposing and assigning work: subagents should independently inspect current truth, propose candidate slices, challenge weak ideas, score trade-offs, and own execution/review lanes within the controller's guardrails.
- UI/world/design proposals must cite external research or benchmarks when relevant; use source grading and research briefs, not personal taste.
- Every batch must produce a capability delta ledger entry, or be explicitly classified as maintenance.
- Do not let workflow/CI/test-only optimization dominate two consecutive batches unless master/delivery is actually blocked.

Current Notion setup note: `NOTION_API_KEY` is not configured in `~/.hermes/.env` as of 2026-04-25 inspection. Until configured, record the same map/council outputs in controller/skill artifacts without claiming Notion sync.

## Non-negotiable environment facts

- Repo root is normally `/Users/cwp/Projects/metaverse-office-web`, which may realpath to `/Volumes/HDD/MyStorage/Projects/metaverse-office-web`. Always canonicalize with `pwd -P` / `git rev-parse --show-toplevel` before comparing paths.
- Use repo-local worktrees under `.worktrees/`.
- For Codex: always `unset OPENAI_BASE_URL` first.
- For Node/pnpm in non-login shells, load the user's zsh environment or use a wrapper that sources `~/.zprofile` and `~/dotfiles/.zshrc` before invoking pnpm/node.
- If that shell still exposes Node/npm but not `pnpm`/`corepack`, do not waste time debugging the user profile during delivery. Run validation through the pinned package manager with a writable cache, e.g. `npm_config_cache=/tmp/codex-npm-cache npm exec --yes pnpm@10.28.2 -- pnpm <cmd>`. Treat default npm-cache `EPERM`/transient registry `ECONNRESET` as environment transport noise; retry with the temp cache before classifying validation red.
- Stack constraints are hard: React + TypeScript + pnpm.
- Slack project channel: `#metaverse-office`.
- Linear team: `MYC / Mycel`; prefer exact state names `Todo`, `In Progress`, `In Review`, `Done`.
- PR titles and squash merge titles use Conventional Commits. Do not prefix titles with `MYC-xx`; put MYC ids in branch/body/Linear/Slack.

## Mode selector — choose exactly one before acting

### Mode A — Workgroup / Graphite batch mode (default)

Use when the user asks to keep product progress moving and no urgent closeout backlog blocks WIP.

Rules:
- worktree = theme/workgroup boundary, not every micro-slice
- Graphite stack or ordered PRs = dependent slices inside that theme
- one Linear issue per slice
- Slack usually sends batch start / PR-ready digest / merge-done digest, not internal noise for every tiny fix
- each workgroup/lane has one exact next action in controller state

Default breadth-first themes:
- world-runtime
- supervision-accountability
- ops-replay-workflow
- hotfix-closeout only when needed

### Mode B — Single-slice mode

Use when the user names one issue, bug, PR, CI failure, or hotfix.

Rules:
- still create/confirm Linear before new implementation unless doing truthful audit/backfill
- still use Layer A -> review -> P0/P1 fix -> Layer B
- single-slice mode is not the default for ongoing throughput

### Mode C — Closeout / audit mode

Use when open PRs, pending CI, sibling rebase needs, stale worktrees, or premature Linear/Slack states exist.

Rules:
- do not open new implementation before auditing existing delivery state
- GitHub PR merged state + actual master commit is merge truth
- local worktree state and current PR head SHA outrank remembered chat/process IDs
- correct premature Linear Done / Slack merge-done if GitHub/master disagree
- clear closeout backlog before expanding WIP

## WIP limits and cadence

Default limits:
- 2-3 active theme workgroups max
- 1 theme worktree per workgroup
- 2-4 stacked slices per workgroup
- 3-5 open PRs max; use the low end while CI is slow/flaky
- 1 expensive Layer B/full gate per workgroup at a time
- 0 new implementation if closeout backlog exceeds the cap

Single-CI-wait exception:
- If the only closeout backlog is exactly one PR that is implementation-complete/PR-ready, current head is known, direct `pull_request` CI is actively running, and there is no failed required signal yet, you may start one low-overlap WIP slice instead of idling or creating a cron.
- The new WIP must branch from current `master`/`origin/master`, not from the pending PR, unless it is explicitly a draft stack.
- Do not touch hot files owned by the pending PR; map file-overlap risk first. For example, if the pending PR touches `App.tsx` / `DetailsPanel.tsx` and their tests, a safe parallel slice may be API-client/contract-only.
- If the direct `pull_request` lane appears stuck while a same-head duplicate `push` lane succeeds, do not merge from the push lane. First inspect the direct PR run/job state. If it is genuinely stale/stuck with no failing signal, an empty rerun commit on the PR branch is acceptable; record the old stuck run, duplicate push result, rerun head, fresh PR run/job, and PR comment/controller update. The fresh direct `pull_request` lane becomes the only merge gate.
- If council reviewers disagree about whether to start WIP during the CI wait, treat QA/Red-Team/Delivery's “do not expand WIP” recommendation as the safe default. Override it only when the selected slice is demonstrably low-overlap, product/evidence valuable, limited to exactly one WIP lane, and the controller records the dissent plus the rationale for proceeding.
- If Red Team/Delivery says new implementation is risky but the user explicitly wants throughput, the compromise is one local-only shadow worktree: implement/commit/validate locally, but do not push, open a PR, or call it PR-ready until the pending PR merges, local master fast-forwards, the shadow branch rebases onto fresh master, and review is rerun. Slack/Linear/controller wording must say local-only WIP, not delivered work.
- Do not let the new WIP merge before the pending PR if it would change the pending PR's base semantics or conflict with its touched surfaces. Rebase/revalidate after the pending PR lands if needed.
- After the pending PR lands, any WIP opened under this exception must be rebased onto the new `master`, revalidated, re-reviewed if the base changed materially, force-pushed, and must wait only on the fresh direct `pull_request` CI for the new head. Treat old-head CI as obsolete even if it later turns green.
- Record the exception in controller truth: pending PR/run/job/head, why the new slice is low-overlap, any council dissent, its worktree/branch/process id, and exact next action for both lanes.
- Slack/Linear wording must distinguish: pending PR delivery-chain incomplete; new WIP started for throughput only, not as evidence that the pending PR is done.

Hot-file rule:
- if multiple PRs touch the same hot file, close sequentially
- after one sibling merges, rebase/restack remaining siblings onto current master
- rerun required validation on the rebased head
- force-push/update PR
- wait only on the new head SHA; ignore old SHA checks

Batch cadence:
1. audit master, open PRs, worktrees, controller state
2. load/update Notion capability map or its temporary controller equivalent
3. run multi-agent product council for product-facing batches
4. pick 2-3 breadth-first slices across themes from council-scored proposals
5. create/confirm Linear issues
6. post one truthful Slack batch-start message, or record Slack degradation
7. create/reuse theme worktrees
8. implement with Codex/agents
9. run Layer A per slice
10. run independent review early
11. batch-fix P0/P1
12. run Layer B when candidate-ready
13. push/open PR or submit stack
14. close out in dependency order
15. fast-forward/cleanup/Linear/Slack/controller
16. record capability delta and seed next batch only when closeout truth is clean or explicitly deferred

## Controller artifacts and continuation truth

Use repo-local controller artifacts under `.hermes/orchestrator/`.

Each live lane/workgroup should record:
- Linear id / slice title
- theme/workgroup
- worktree path
- active branch / stack top
- owner agent
- lifecycle state: `Todo`, `In Progress`, `In Review`, `Blocked`, `Done`
- local health: `running`, `waiting`, `no-op`, `stalled`, `degraded`, `baseline-red`, etc.
- background `session_id` if any
- strongest evidence
- exact next action

Rules:
- every lane must have exactly one precise next action; never leave `continue` / `follow up later`
- if historical controller lanes used tracker identifiers as local placeholders because Linear previously returned `not found`, and live Linear later creates real issues with those same identifiers, reconcile before updating lifecycle state: mark the old lanes as legacy placeholders, record that they are not the current Linear issue, then create/update separate lanes for the live Linear issues with their real titles/URLs/states. Do not move the new Linear issue to Done or rewrite the old lane just because the numeric identifier matches.
- `notify_on_complete` is only a signal, not the scheduler
- after starting a long background command, record `session_id`, command, success condition, and successor action immediately
- if a foreground/manual continuation takes over work that also has a scheduled cron closeout, pause or remove the cron before it can race the same PR/Linear/Slack cleanup; after successful closeout, delete the obsolete cron and record the action in controller truth
- if GitHub merge, local fast-forward, branch/worktree cleanup, Linear Done, and Slack merge-done are already complete but `.hermes/orchestrator/workgroups.json` still has the closeout lane open, do a controller-only repair: update/add the workgroup entry with `health: done`, `next_action: closed`, `worktree: null`, `active_branch: null`, `active_process: null`, final `head_sha`/`merge_sha`/CI evidence/delivery note; update top-level `closeout` (`open_prs_after_audit`, `local_master`, `origin_master`, `linear_done`, Slack note, capability delta, next-batch); validate JSON; re-check minimal live truth (`git status`, `HEAD == origin/master`, worktree/branch absence, open PR count) before marking the remaining todo complete. Do not rerun product tests for controller-only repair.
- controller-only repairs under `.hermes/` may be ignored by repo-local `.git/info/exclude`, so `git status` and `git diff` can stay clean even after a successful controller mutation. Verify these repairs with `python3 -m json.tool .hermes/orchestrator/workgroups.json`, direct file reads/searches of the affected lane, and live GitHub/local git truth; do not conclude the update failed just because Git shows no diff.
- if the only remaining blocker is a long-running remote PR CI lane and the current session cannot safely wait to completion, create a bounded closeout cron instead of opening new WIP. The cron prompt must name the exact PR, branch, expected head SHA, pull_request run/job ids if known, merge title, no-recursive-cron rule, green/red/already-merged branches, cleanup/Linear/Slack/controller actions, and must distinguish implementation-complete from delivery-chain-complete. Record the cron id/schedule in controller state.
- when waiting/polling from Hermes foreground tools, keep each foreground wait within the tool timeout cap (observed max 600s). Do not issue a foreground `sleep` or poll command with `timeout` above that cap; use shorter bounded polls, a background process with notify/poll, or the bounded closeout cron path.
- near session/context limits or tool-call iteration limits, write handoff/controller truth first, then resume from controller + handoff in a fresh continuation
- closeout budget rule: once a PR is merged and local master is fast-forwarded, the controller update is part of closeout, not an optional afterthought. If budget is getting tight, perform the minimal controller mutation immediately after each irreversible closeout milestone (merge SHA, local fast-forward, worktree/branch cleanup, Linear Done, Slack merge-done) before doing any optional reporting or next-slice work. If the session is interrupted after GitHub/Linear/Slack closeout but before controller repair, the final response must explicitly say: `delivery chain complete; controller stale repair pending` and name the exact lane/file to repair next.
- when a slice reaches PR-ready but the delivery chain is still incomplete and execution budget is low, prioritize durable continuation truth before optional next-slice work: record PR URL/number, head SHA, branch/worktree, validation/review evidence, Linear/Slack actions already performed, exact missing actions (direct `pull_request` CI audit, merge, fast-forward, cleanup, Linear Done, Slack closeout), and any adjacent WIP worktree/Linear ids. Do not rely on a final chat summary as the only handoff.

## Truth-source hierarchy

When signals disagree:
1. local git/worktree + local reruns
2. GitHub/Graphite PR head, stack order, checks, merged state
3. Linear lifecycle
4. Slack messages

Slack never owns truth. Linear owns coarse lifecycle only, not transient CI health. GitHub/Graphite own code/merge truth. Controller files own execution-continuation truth.

## Core workflow by mode

### Workgroup / Graphite mode

1. Audit current truth: master, open PRs, worktrees, controller, Linear, Slack as needed.
2. Load Notion capability/research/decision map, or temporary controller equivalent if Notion is not configured.
3. Run the multi-agent product council for product-facing batches; do not let the main agent choose product direction alone.
4. Choose 2-3 breadth-first slices across distinct themes from council-scored proposals.
5. Create/confirm Linear issues and move started slices to `In Progress`.
6. Post one Slack batch-start message; if Slack degraded, record that truthfully.
7. Create/reuse theme worktrees and Graphite/ordered branches.
8. Implement using Codex with surgical prompts; do not let Codex become the global coordinator.
9. Run Layer A focused validation.
10. Run independent review before expensive gates.
11. Classify findings P0/P1/P2; fix P0/P1 in batch; turn P2 into follow-up.
12. Run Layer B once candidate-ready.
13. Push branches / submit stack / open PRs with evidence.
14. Merge in dependency order; rebase/restack siblings after each hot-file/base merge.
15. Close out GitHub/local/Linear/Slack/controller truth.
16. Record capability delta in Notion/controller and seed the next batch only after closeout backlog is clean or explicitly bounded.

### Single-slice mode

1. Audit main and open PRs first.
2. Create/confirm one Linear issue.
3. Post Slack start if starting now.
4. Create a repo-local worktree/branch.
5. Implement narrowly with Codex or direct edits.
6. Run Layer A.
7. Run independent review.
8. Fix P0/P1; rerun impacted Layer A and re-review.
9. Run Layer B when candidate-ready.
10. Push/open PR, merge when ready, fast-forward, cleanup, Linear Done, Slack closeout.
11. Do not start the next slice unless conveyor is clean and continued advancement is desired.

### Closeout / audit mode

1. Audit GitHub/Graphite PRs and current head SHAs.
2. Audit local master/worktrees/branches.
3. Audit Linear/Slack for premature or missing state.
4. If a PR is stale after sibling merge: rebase/restack, rerun required validation, force-push, wait on new SHA.
5. If duplicate CI disagrees: inspect job metadata and exact failing step before rewriting code.
6. Merge only when current head/queue SHA satisfies required checks and review.
7. Fast-forward local master, cleanup worktree/branches, mark Linear Done, send Slack merge-done/backfill/correction.
8. Update controller and mark exact next action/done state.

## Validation and review policy

### Layer A — local fast loop

Purpose: implementation iteration, review blocker repair, smallest semantic proof.
Budget target: usually under 5 minutes.

Examples:
- touched backend test
- touched Vitest file/case
- focused App/DetailsPanel/projector test
- one Playwright grep/file only when browser behavior is genuinely touched
- targeted typecheck when TypeScript contracts changed

Do not default to full browser smoke or `pnpm test:all` before review.

### Layer B — required PR gate

Purpose: minimum credible pre-merge validation.
Target budget after CI optimization: 10-15 minutes.

Recommended shape:
- `pnpm backend:test`
- `pnpm web:test`
- `pnpm web:typecheck`
- `pnpm web:build`
- one canonical browser smoke path

If two browser-smoke paths remain required, split them into parallel jobs. Do not serialize them in one long job.

### Layer C — async full gate

Purpose: full regression, second smoke mode, extended smoke, nightly/post-merge/merge-queue validation.
Layer C protects completeness; it must not synchronously block every tiny PR edit.

### Review rules

- Run independent review after Layer A and before expensive gates.
- Review output must classify P0/P1/P2.
- P0/P1 block current PR.
- Do not trust the reviewer's severity label mechanically. If a finding is labeled P2 but describes current-scope correctness, contract compatibility, stale-data truthfulness, write-boundary validation, or a regression against existing accepted inputs, promote it to P1 for this PR and fix/re-review before push/PR-ready.
- True P2 becomes Linear follow-up or PR comment and must not trigger heavy rerun loops.
- Per PR, aim for one candidate-ready Layer B and at most one Layer B rerun after P0/P1 repair.
- If blockers keep appearing after budget is exhausted: rescope, split, create unblocker, or ask for explicit override.

## PR, Linear, Slack, and Graphite conventions

Linear:
- one issue per slice
- new implementation should have tracking before coding unless doing audit/backfill
- use exact states when possible: `Todo`, `In Progress`, `In Review`, `Done`
- lifecycle stays coarse; transient health remains local/controller state

Slack:
- broadcast only; never source of truth
- prefer batch start / PR-ready / merge-done / audit correction messages
- if Slack delivery fails, retry once, try direct API when available, or record degraded state truthfully; do not claim Slack was sent

GitHub:
- PR titles and squash titles use Conventional Commits
- MYC id goes in branch/body/Slack/Linear trail
- do not self-approve your own PR; leave COMMENT with independent review result if needed
- GitHub PR merged state + actual master commit is merge truth

Graphite:
- use for ordered dependent slices inside a theme/workgroup
- stack order is dependency truth
- after base/sibling merge, restack/rebase and wait only on the new head SHA
- if Graphite is unavailable or unnecessary, fall back to normal branch PR mode without weakening truth-source rules

## Definition of Done

### Slice-local done
- scope implemented
- diff narrow and slice-pure
- Layer A green
- independent review complete
- P0/P1 fixed or explicitly scoped out
- evidence recorded in controller/Linear comment

### PR-ready
- branch/stack pushed
- PR opened with Conventional Commit title
- Linear issue linked in PR body
- validation summary present
- independent review verdict/comment present
- Layer B started or green according to repo policy
- Linear is `In Review`
- Slack PR-ready digest/backfill sent or degradation recorded

### Merge-ready
- PR head SHA is current
- required checks green for that head or queue SHA
- review requirement satisfied
- no stale sibling/hot-file rebase remains
- no known P0/P1 blocker remains

### Delivery done
- PR merged into master
- local master fast-forwarded to merge commit
- worktree removed/pruned
- local/remote branch cleaned
- Linear `Done` with truthful note
- Slack merge-done/backfill/correction posted or degradation recorded
- controller lane marked done with evidence

### Batch/workgroup done
- all stack PRs merged, blocked, or explicitly deferred
- no stale worktree/branch/controller action remains
- capability delta ledger updated in Notion, or temporary controller equivalent if Notion is not configured
- next batch seeded if conveyor is empty and continued advancement is desired

## Hard anti-loop rules

- Do not let the main agent choose product direction alone; product-facing batches require multi-agent council input.
- Do not start product-facing UI/world/design work from taste alone; require research brief / benchmark / source grading when relevant.
- Do not run expensive gates before review by default.
- Do not rerun full gates after every tiny review comment.
- Do not wait on obsolete SHA checks after rebase/restack/force-push.
- Do not rewrite product code for duplicate same-SHA CI red until job metadata and local focused repro justify it.
- Do not contaminate an unrelated PR with baseline/unblocker fixes.
- Do not let Slack/Linear optimistic Done override GitHub/master truth.
- Do not expand WIP while closeout backlog is unresolved.
- Do not stop at implementation-complete when the delivery chain is incomplete; report the distinction explicitly.

## Minimal message templates

Slack batch start:
- batch started
- Linear ids/URLs
- themes/workgroups
- exact scope and non-goals
- validation/review policy
- degraded integrations, if any

Slack PR-ready:
- PR URL
- Linear id
- scope
- Layer A result
- review verdict
- Layer B/CI state
- current head SHA

Slack merge-done / backfill:
- PR URL and merge SHA
- master fast-forward status
- cleanup status
- Linear state
- whether this run performed the closeout or only audited/backfilled it

## Reference index

Load these as needed:

- `references/product-strategy-kernel-notion-research-council.md`
  - load before selecting a product batch; covers Notion capability map, multi-agent product council, research briefs, source grading, and anti-stagnation controls
- `references/delivery-operating-model-v2.md`
  - load for mode selection, WIP limits, batch cadence, controller/handoff, Definition of Done
- `references/workflow-optimization-addendum-2026-04.md`
  - load for consolidated history of the 2026-04 workflow optimization plans
- `references/ci-validation-and-duplicate-checks-2026-04.md`
  - load for Layer A/B/C details, P0/P1/P2, full-gate budgets, duplicate CI, same-SHA triage
- `references/closeout-pm-truth-and-worktree-rescue-2026-04.md`
  - load for closeout, GitHub/Linear/Slack truth disputes, stale worktrees, sibling sequential merges
- `references/playwright-ui-regression-pitfalls-index-2026-04.md`
  - load before touching Hub/DetailsPanel/App/browser-smoke/request-scope/correlation/viewport tests
- `references/legacy/SKILL-2026-04-25-full-pre-refactor.md`
  - full pre-refactor archive for search/provenance only; do not treat as primary flow

## Legacy note

The old one-slice conveyor, detailed Slack/Linear/GitHub API gotchas, and the full pitfall ledger were not deleted. They were moved behind references and a legacy archive so the main skill can act like a clean operating manual instead of a 100KB incident dump.

Core process preserved: inspect main, track in Linear, announce truthfully in Slack, use repo-local worktrees, implement narrowly, validate, review independently, push/open PR, merge through GitHub/Graphite truth, fast-forward master, cleanup, close Linear/Slack, and seed next work when the conveyor is clean.
