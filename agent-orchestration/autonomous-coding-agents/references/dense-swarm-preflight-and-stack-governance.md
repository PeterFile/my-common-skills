# Dense swarm preflight and stack governance

Use this reference when a user asks for a large Codex/worktree cluster with external status reporting and many parallel lanes.

## Preflight before write-enabled swarm

Before launching write-enabled Codex agents, verify the sinks the user requires for progress/status updates. If the user requires Slack + Linear, both must be proven usable before side effects.

Minimum checks:
- Live repo state: top-level path, branch, clean/dirty status, recent commits, remotes, worktree list.
- Momentum check: inspect the latest commits/merged PRs against the current direction doc or milestone and state whether recent work is advancing the target, merely refactoring, or creating backlog.
- Agent/tool path: Codex CLI availability and exact invocation supported by installed version.
- GitHub path: either `gh` or authenticated API/MCP for PRs/checks.
- Issue tracker: target team/issue/project exists and write-back can return a URL or ID.
- Chat/status sink: exact Slack/Discord/Telegram target or token/channel is available and a test/read-back is possible.

If a required sink is missing:
- Do not launch write-enabled swarm.
- It is still valid to run read-only planning/review agents.
- Write a blocker to the available authoritative tracker if one is available and the user requested status feedback.
- If issue creation is blocked by tracker limits (for example Linear active-issue limits), do not create progress markdown or invent a new tracker. Find the existing authoritative project/umbrella issue and add a status comment there; include the returned comment URL as the write proof.
- Offer explicit alternatives: connect the missing sink, or user authorizes Linear-only / Discord / Telegram fallback.
- Do not claim Slack delivery when only Discord/Telegram targets exist or only Linear succeeded.

## Remote stack governance before expanding

A large open remote PR stack changes the task from “open more worktrees” to “govern the stack” unless the user explicitly accepts more backlog.

Red flags:
- Many open `stack/*` PRs already exist.
- Local Graphite view only shows `master` or otherwise does not reflect remote PR DAG.
- Latest worktrees/branches appear stale or numerous.
- Existing PRs span evidence, storage, API, UI, verification, and smoke lanes.

Rules:
1. Treat remote GitHub PR data as authoritative when local stack tooling is stale or incomplete.
2. Freeze ordinary new stack PRs until the existing stack is triaged. Exceptions: CI/test unblockers, conflict fixups, security/public-leak fixes, and consolidation/replacement PRs.
3. If a scoreable stack already exists, use the dense Codex swarm as a review/score/repair swarm on those existing PR worktrees before creating new branches. Launch one lane per existing PR/worktree, require no commit/push/post from workers, collect score/test output, and let the parent decide whether any local fix is worth keeping. "More agents" does not have to mean "more PRs" when backlog is already review-bound.
4. Cluster open PRs by semantic route, not by creation time alone: read-only evidence, route/verify helpers, controller/API, storage/runtime, public leak safety, UI interaction/smoke.
5. For each cluster, check changed-file overlap, base/head dependency, duplicate helpers/contracts, CI status, and whether a later PR supersedes an earlier one.
6. Merge or close in checkpoint batches. After each cluster checkpoint, update/rebase/retarget downstream PRs and close superseded PRs.
7. Do not solve stack chaos by creating a mega-PR. Keep normal PR caps and split by semantic boundary.

## Status update shape

When blocked before implementation, status should be factual and non-narrative:

```text
Preflight result:
- Repo HEAD/status:
- Recent work is/is not advancing target milestone because:
- GitHub/PR state:
- Codex/tool state:
- Linear state:
- Slack/chat state:
Decision:
- Write-enabled swarm started: yes/no
- If no: blocker and minimal unblock condition
Planning output:
- route lanes proposed
- governance recommendation
Next safe action:
```

Always include returned handles for external writes, such as Linear comment URL or GitHub PR URL. Do not report chat sync for channels that were not verified.