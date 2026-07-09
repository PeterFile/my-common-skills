---
name: dense-multi-agent-worktree-delivery
description: Coordinate dense multi-agent software delivery with isolated worktrees, scoreable lanes, stacked PRs, fast validation, and truthful Slack/Linear/GitHub closeout.
version: 1.2.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [multi-agent, codex, worktrees, stacked-prs, ci, github, linear, slack, delivery]
    related_skills:
      - codex
      - github-workflows
      - software-delivery-workflows
      - task-pr-flow
      - skill-library-maintenance
---

# Dense Multi-Agent Worktree Delivery

## Core Rule

Use this workflow when the user wants substantial project advancement through many coordinated agents, isolated worktrees, scoreable lanes, stacked PRs, fast validation feedback, and external status sinks.

Preserve this as a standalone operating model. Generic delivery skills may support it, but must not collapse it into a project router, a three-agent fallback, or a vague "parallel work" note. Dense means controlled throughput with evidence, not uncontrolled WIP.

## Mode Selector

Choose exactly one mode before acting:

1. **Batch mode** — default for new dense product progress. Use adaptive workgroups, scoreable lanes, stacked PRs, and status sinks.
2. **Single-slice mode** — use when the user names one issue, PR, bug, CI failure, or hotfix. Do not add swarm overhead unless adjacent low-overlap work can safely continue.
3. **Closeout/audit mode** — use when PRs, CI, dirty worktrees, controller state, Slack/Linear state, or sibling branch rebases are already in flight.

Closeout/audit debt must be owned before new implementation, but it is not a global stop sign. Hermes may keep low-overlap development moving when live PR/CI/review capacity exists and each lane has an explicit closeout owner and next action.

## Truth Sources

When signals disagree, prefer current verifiable state in this order:

1. local git/worktree state and locally rerun validation
2. GitHub/Graphite PR head, diff base, reviews, and required `pull_request` checks for the current SHA
3. repo-local controller state and handoff artifacts
4. Linear or equivalent lifecycle tracker
5. Slack/chat/status messages
6. remembered summaries or subagent reports

Slack is never merge truth. Linear `Done` is never merge truth. A subagent report is a lead, not proof.

## Non-Negotiables

1. Verify live state before planning: repo path, realpath, default branch, `git status`, recent commits, worktree list, branches/remotes, open PR stack, CI state, dirty files, controller state, issue state, and relevant chat/status trail.
2. Prove required status sinks before write-heavy work: GitHub PR read/write, Slack, Linear, issue comments, Graphite/merge queue, or the repo's equivalents. Prefer read-only probes first. If a required sink is unavailable, stop before side effects or get explicit fallback authorization.
3. Select a mode before spawning agents.
4. Dense does not mean blind, but there is no fixed default upper limit. Hermes controls development rate dynamically from live evidence: agent availability, worktree isolation, hot-file overlap, review capacity, CI throughput, PR backlog, local machine load, user urgency, and rollback risk. Scale up until a measured bottleneck appears; slow down only for a specific, named risk.
5. Start batch mode with a multi-agent planning/review council. Include product/vision, operator/user, architecture/runtime, UX, QA/replay, security/cost, red-team, and delivery/stack roles when relevant.
6. Convert strategy into scoreable lanes. Each lane needs a slug, goal, file scope, no-touch areas, dependencies, stack parent, PR size cap, checklist, scoring rubric, fastest validation command, and first-feedback timebox.
7. Use isolated implementation worktrees or equivalent isolation for every write-enabled lane. Do not let a Hermes delegate concurrency cap limit a Codex CLI swarm; use delegates for synthesis/review and separate Codex sessions for implementation.
8. Keep PRs small. Use stacked branches for dependent slices. Split oversized worker output before opening PRs.
9. Validate quickly and repeatedly: narrow checks first, broader gates only after credible diff + review.
10. Commit intended files only. The controller inspects diffs, reruns tests, verifies PR/CI state, and reconciles only deliberate changes.
11. Keep transient progress in controller state, Slack, Linear, GitHub comments, or equivalent trackers. Update durable markdown only when product/API/storage/runtime/UI semantics or persistent operating policy changes.
12. Never claim delivery complete until code, review, validation, PR/CI, tracker state, controller state, and required status updates are reconciled.

## Minimum Preflight

Before launching implementation, record these facts in the controller or handoff surface:

- target repo path and canonical realpath
- default branch and current HEAD
- dirty files and untracked files
- worktree inventory, including stale/prunable entries
- open PRs, target bases, current head SHAs, required checks, and reviews
- current CI health and known baseline-red tests
- active background processes or external agents
- controller/handoff exact next actions
- Slack/Linear/GitHub/Graphite availability or explicit degraded-mode authorization
- selected mode and dynamic rate-control decision: current bottleneck, allowed concurrency, and why that rate is safe now

If preflight reveals closeout debt, switch to closeout/audit mode.

## Planning Contract

Run a planning pass before write-enabled batch implementation:

- Re-read the latest repo-authoritative vision/product/progress sources.
- Check whether recent commits advanced product/runtime capability or only optimized workflow/test mechanics.
- Ask planning agents to independently inspect current truth, propose route candidates, challenge weak/redundant work, and identify hot-file overlap.
- Score routes before launch using a 100-point rubric: product value, scope discipline, contract correctness, test evidence, docs discipline, reviewability, CI cost, and delivery risk.
- Prefer enough lanes to saturate safe throughput for the real project shape. Hermes, not a fixed numeric cap, chooses the rate from overlap risk, review capacity, CI capacity, PR backlog, machine capacity, and user urgency.
- Do not let workflow/CI-only optimization dominate consecutive product batches unless delivery is actually blocked.

## Lane Prompt Contract

Give every implementation agent a self-contained prompt with:

- repo path and exact worktree path
- branch, base branch, stack parent, and intended PR base
- allowed files and explicit no-touch files
- goal, non-goals, acceptance checks, and score target
- dependency/hot-file notes and expected sibling rebase order
- fastest Layer-A validation command
- PR size budget and split trigger
- instruction not to commit, push, open PRs, or post Slack/Linear unless authorized
- required output: changed paths, validation output, review concerns, blockers, risk notes, and exact next action

Use Codex CLI agents for code-writing lanes when requested. Use Hermes delegates for planning, review, synthesis, and audit when they reduce controller context load.

## Execution Loop

For each iteration:

1. Launch or resume lanes from live state, not stale summaries.
2. Poll running agents and inspect worktrees directly.
3. Run the lane's fastest validation as soon as a plausible diff exists.
4. Review the diff for scope, correctness, tests, security, docs, user-surface behavior, and PR size.
5. Fix or send back only the smallest necessary change.
6. Promote a lane only after controller-verified validation and review.
7. Commit intended files only, then push/open the correctly based PR.
8. Update Slack/Linear/GitHub/controller state with facts, URLs/IDs, current SHA, and exact next action.
9. Re-score after each feedback cycle and decide whether to merge, split, restack, continue, pause, or kill the lane.

Long-running bounded commands should use background execution with completion notification and recorded session IDs. Notification is only a wake-up signal; controller state remains the continuation truth.

## Validation And Review Policy

Default local loop:

1. implement the smallest scoped change
2. run Layer-A focused validation
3. run independent review before expensive gates
4. classify findings as P0/P1/P2
5. fix P0/P1 in batch
6. rerun impacted Layer-A checks and re-review
7. run Layer-B only when candidate-ready
8. push/open PR and let required CI/merge queue provide the final broad gate

Definitions:

- **Layer A**: fastest semantic proof for the touched surface, usually under 5 minutes.
- **Layer B**: required PR-ready gate for credible pre-merge validation.
- **Layer C**: async/nightly/post-merge full regression or expensive drift detection.

Do not run long full gates before review by default. That creates the slow loop: full gate, review blocker, small fix, full gate again.

## Stack Governance

Use stacked delivery when dependencies exist:

- Root durable-docs or contract PR may target the default branch.
- Implementation PRs target the previous branch in the stack.
- Verify every PR diff against its intended base before opening.
- If a branch carries stale parent history or an oversized diff, restack or cherry-pick the true child delta into a fresh branch.
- If remote PR backlog is large, pause new work and cluster existing PRs by route, file overlap, status, and supersession before adding more.
- If sibling PRs touch hot files, close them sequentially: merge one, fast-forward default branch, rebase/restack siblings, rerun required validation on the rebased head, then update PRs.
- Never merge on stale local assumptions. Verify the current head SHA, review requirement, and required `pull_request` CI gate for that SHA.

## Documentation And Status

Use durable markdown sparingly:

- Update existing docs when behavior, architecture, API, storage, runtime, UI semantics, or persistent operating policy changes.
- Do not create new markdown for temporary progress, raw lane logs, or transient checklists unless the repo explicitly treats it as a durable controller artifact.
- Keep ephemeral state in Slack, Linear, GitHub comments, controller files, or equivalent trackers.
- When creating durable docs, state why the knowledge is persistent.

Status updates must separate:

- implementation complete
- review complete
- local validation complete
- PR open / waiting for CI
- merged
- delivery-chain complete, including tracker/controller cleanup

## Closeout Contract

Before reporting completion:

- Re-check default branch, current HEAD, and worktree cleanliness.
- List merged PRs, open PRs, dirty lanes, blocked lanes, abandoned lanes, and still-running processes.
- Confirm Slack/Linear/GitHub/controller state matches reality.
- Separate verified facts from inference.
- Record exact validation commands and results.
- Preserve handoff context only where future work needs it.

After a squash merge, local branch deletion may require force delete because the branch tip is not an ancestor of the new default-branch commit. Only do that after GitHub merge and local fast-forward are verified.

## Cross-Runtime Metadata

- `agents/openai.yaml` provides Codex/OpenAI-style interface metadata. Hermes does not expose it through `linked_files`; inspect it directly when porting or auditing cross-runtime behavior.
- Keep Hermes support material under `references/`, `templates/`, `scripts/`, or `assets/` when it needs `skill_manage` support.

## Reference Loading Map

Load references only when the specific decision requires them:

- `references/delivery-operating-model-v2.md`: mode selector, dynamic rate control, workgroup operating model, batch cadence.
- `references/ci-validation-and-duplicate-checks-2026-04.md`: validation layers, review severity, duplicate CI, PR gate discipline.
- `references/closeout-pm-truth-and-worktree-rescue-2026-04.md`: merge truth, stale worktrees, sibling closeout, controller rescue.
- `references/workflow-optimization-addendum-2026-04.md`: controller artifacts, exact next action, background-process continuation, dense conveyor refinements.
- `references/product-strategy-kernel-notion-research-council.md`: product/vision council and route scoring.
- `references/ux-qa-delivery-captain-council-2026-06.md`: UX/QA/Delivery captain council pattern for planning-only dense Codex/worktree waves with PR stack boundaries, scoring, fast feedback cadence, Slack/Linear update points, and documentation discipline.
- `references/public-label-ci-feedback-loop-2026-06.md`: dense-wave CI feedback pattern for public-safe label/source-kind vocabulary changes where focused leak-sentinel tests pass but broad App integration assertions still need exact-head PR triage and narrow `App.test.tsx -t` reproduction.
- `references/playwright-ui-regression-pitfalls-index-2026-04.md`: browser/UI regression pitfalls.
- `references/legacy-index.md`: index for archived legacy workflows. Read this before loading any large legacy archive.
- `references/legacy-linear-slack-worktree-delivery-loop-skill.md`: legacy high-throughput Slack/Linear/worktree/Graphite workflow. Historical edge cases only.
- `references/legacy-parallel-worktree-codex-review-loop-skill.md`: legacy parallel Codex worktree and review/revalidate workflow. Historical edge cases only.
- `references/legacy-linear-slack-full-pre-refactor-2026-04-25.md`: full pre-refactor archive. Provenance/search only; not the primary operating path.
