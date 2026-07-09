---
name: github-workflows
description: "Use when doing GitHub work end to end including auth, repos, issues, branches, PRs, reviews, CI, releases, and codebase inspection."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [github, git, gh-cli, pull-requests, issues, code-review]
    related_skills: [requesting-code-review]
---

# GitHub Workflows

## Overview
This umbrella covers GitHub work from local repository discovery through issue and PR lifecycle. Use `gh` when authenticated; fall back to git plus REST/MCP tools when needed. Verify repo, branch, remotes, and returned URLs or IDs.

## When to Use
- Authentication, remotes, clone/fork/create, releases.
- Issue creation, triage, labels, assignees, milestones.
- Branches, commits, pull requests, CI checks, merge flow.
- PR review with inline comments or summary reviews.
- Repository language/LOC inspection.

## Workflow Sections
### Authentication
Check `gh auth status` and `git remote -v`. If auth is missing, explain the exact login or token step; never guess secrets.

For local macOS setup, install GitHub CLI with Homebrew when needed (`brew install gh`), set HTTPS unless the user specifically wants SSH (`gh config set git_protocol https --host github.com`), then authenticate with the browser/device flow. In non-interactive or service-like sessions, prefer `GH_PROMPT_DISABLED=1 gh auth login -h github.com --git-protocol https --web --scopes repo,workflow` so the device code and URL are printed directly; open `https://github.com/login/device`, copy the code for the user, wait for authorization, then verify with `gh auth status` and run `gh auth setup-git`. Do not read, print, or store tokens manually.

### Repository Management
Confirm owner, repo, default branch, and local path. Avoid overwriting directories. Verify remotes and current branch after changes.

### Issues
Search for duplicates when likely. Gather title/body/labels/assignees. Return the real issue URL or number from command output.

### Pull Requests
Use isolated branches, check `git status --short`, commit only intended files, create the PR with clear title/body, then monitor CI with `gh pr checks` or status APIs. If `gh` is unavailable but git push/auth and GitHub MCP/API are available, push with git and create/read PRs through the API/MCP; verify returned PR URLs/numbers instead of assuming success.

When the user asks to finish all follow-up delivery actions or to make `main` current, do not stop at an open PR. After exact-head CI is green and the PR is mergeable, perform the requested merge style as a separate auditable mutation, commonly `gh pr merge <n> --squash --subject "type(scope): ..." --body-file ...`; then verify the PR is `MERGED`, fetch/pull local `main` with `--ff-only`, and report the new main SHA. If `gh pr merge` prints a local git checkout/worktree error such as `fatal: 'main' is already used by worktree ...`, immediately re-query `gh pr view <n> --json state,mergedAt,headRefOid` before retrying: GitHub may already have completed the remote merge while only the local checkout step failed. Treat remote head-branch cleanup as a separate optional mutation after confirming no open PRs use that branch as `base.ref`. If the user has already granted broad closeout authority, do not stall on a generic clarification prompt; execute each destructive mutation as its own visible tool call so any required approval is surfaced by the tool boundary. If the user wanted PRs split by blocker or component, clarify/split before merging; otherwise a single atomic PR is acceptable when all fixes are required for one real acceptance path. For the detailed integration-merge, main-sync, smoke-PR, branch, and worktree cleanup sequence, see `references/guarded-delivery-closeout.md`.

For stacked delivery, keep PRs small and explicit: a durable docs/root PR may target the default branch, then implementation PRs target the previous stack branch. When a user explicitly asks to open PRs for completed slices before continuing remaining work, do not wait for the whole integration plan: first identify slices that are committed, parent-validated, and review-approved; push/open only those PRs with the correct stacked base, leave blocked/in-progress slices untouched, and state that PR creation is not merge completion. For SkyTurn-style multi-slice parent orchestration details, UI-only slice pitfalls, and final integration-PR closeout after sibling slice PRs are superseded by a squash merge, see `references/skyturn-stacked-slice-delivery.md`. Before creating each PR, confirm the branch contains only its intended diff relative to its base; otherwise rebase/restack rather than opening a misleading mega-PR. For open-PR stack closeout, merge the root PR first, retarget child PRs to the real default branch, and then verify a fresh `pull_request` CI run for each current child head/base pair before merging. A green run from before the retarget is stale for the new base. If retargeting does not trigger CI, use a scoped tree-identical empty commit plus normal push on that PR branch to refresh the gate; do not use force-push for this. After any sibling PR is merged into the base, repeat the fresh-gate check for remaining siblings whose diff may now interact with the new `master`/`main`: run `gh pr update-branch <pr>`, fetch or re-query until the branch head is the new `headRefOid`, then require a fresh `pull_request` check on that exact head before merging with `--match-head-commit`. A stale green check from before the base update is not merge evidence, and `mergeStateStatus: UNKNOWN` means refresh/recheck rather than merge. In a parallel independent-PR closeout, expect every remaining sibling to become `BEHIND` after each squash merge; process them serially as `update-branch → wait for the new head SHA → fresh exact-head CI success → squash with --match-head-commit`, then sync local main before moving to the next PR. Use `references/parallel-pr-integration-branch.md` for the detailed pattern and pitfalls. When using Git worktrees for restacks, keep worktree creation separate from mutations; see `references/worktree-command-scope.md` for the command-scope pitfall where a chained `git worktree add ... && git cherry-pick ...` dirties the original worktree. If a dirty worker result exceeds the size target, split it into fresh stacked branches before opening PRs and state that the original scratch lane remains not-ready if it is left dirty. If a repo already has a large remote `stack/*` PR backlog, treat that as a governance problem before opening more PRs: fetch/list remote PRs, cluster by semantic route, check changed-file overlap and superseded work, merge/close in checkpoint batches, and do not trust a local stack tool such as Graphite when it only shows `master` or otherwise disagrees with remote GitHub PR data. For large stacked-PR governance, use the detailed checklist in `references/stacked-pr-governance.md`; when the cleanup spans multiple sessions or hits an iteration/tool budget boundary, use `references/stacked-pr-backlog-continuation.md` to resume from verified live state and write precise handoffs; when an orphaned old-stack PR appears already absorbed by an evolved default-branch implementation, use `references/stacked-pr-superseded-orphan-closure.md` before closing or deleting its head; for repeated required-CI flakes during that cleanup, use `references/stacked-pr-ci-flake-discipline.md`. For fresh CI failures after restacks, use `references/stacked-pr-ci-failure-triage.md`: read failing job annotations first, fix only current-PR scope, rerun the narrow failing smoke/test locally, clean generated artifacts, amend, force-push with a lease, and wait for a new pull_request gate. For non-restack additive CI fixes, prefer a normal follow-up push over force-push; record the failed run id, the exact failing test slice, the new head SHA, and wait for the new exact-head `pull_request` gate. For rebase conflicts caused by adjacent stacked test additions, evolved exact-shape contract fields, or child PRs whose parent was squash-merged, use `references/stacked-pr-rebase-conflict-patterns.md`: preserve additive tests, merge current public contract fields into in-scope type/fixture assertions, identify the real old parent cut point from child branch ancestry before `git rebase --onto`, then re-run the lane gate before force-pushing. When a child PR still targets an old parent branch after that parent was squash-merged, use `references/stacked-pr-child-delta-restack.md`: verify ancestry and cherry-pick only the true child delta if `old-base..child-head` would drag stale stack history into the diff. For older UI roots conflicting with newer already-merged UI slices, use `references/stacked-ui-conflict-merge.md`: preserve current `master` semantics and apply only the still-missing old-PR behavior as an incremental patch. When `gh` is unavailable or combined status is incomplete, use `references/stacked-pr-actions-api-polling.md` to poll GitHub Actions by exact head SHA and verify the full pull_request job set. For post-merge remote head cleanup, use `references/stacked-pr-remote-branch-cleanup.md`: split non-destructive refresh/inventory from destructive branch deletion, verify no open children by `base.ref`, and stop rather than reroute if deletion is denied. When Hermes blocks a destructive stacked-PR operation, including force-with-lease push as well as cleanup deletion, use `references/stacked-pr-guard-boundaries.md`: stop on the denied mutation, report the ready local artifact and exact next approval needed, and do not reroute through another command/API for the same outcome. For destructive remote PR actions, also use `references/stacked-pr-destructive-mutation-discipline.md`: broad user authorization lets you proceed, but each force-push, retarget, merge, and branch cleanup still needs a narrow visible boundary with target ref/PR, expected old SHA when applicable, validation state, and explicit out-of-scope actions. Do not bundle force-push, retarget, merge, cleanup, or API PATCH steps inside one shell/Python script. If Hermes needs an approval prompt for an already-authorized destructive git command, issue the single direct command so the user can approve it; do not replace that with a wrapper script or a manual-instruction handoff. If exact `pull_request` runs are missing after a force-push/base-retarget, fall back to all runs plus check-suites/check-runs for that SHA; never merge until a fresh pull_request gate for the current head is visible and green.

If a repo has a PR-size advisory command, run it after committing the candidate branch and before opening the PR; if the advisory reports over-cap, split or compress instead of rationalizing the excess. If validation had a one-time failure followed by targeted isolation and a full passing rerun, disclose that in the PR body/status update and score risk lower than a clean first-pass green run.

When GitHub API/MCP output is too large or status endpoints are rate-limited/incomplete during backlog cleanup, do not guess CI state. Reduce the data locally to the fields needed for governance (number, base ref, head ref/SHA, title, mergeability, changed files), or use the GitHub checks web page as a read-only fallback. On the checks page, verify the current head SHA and the `pull_request` suite specifically; a green `push` suite alone is not a merge gate. If browser snapshots hide expanded jobs, inspect DOM text/links for each expected job name and success/failure icon text before merging.

CI/workflow PRs have a special compatibility constraint: preserve existing required check names and job semantics unless the user explicitly accepts required-check churn. Prefer a tiny concurrency/cancel-stale-runs PR over a broad job-splitting PR when you cannot verify branch protection and required-check wiring.

### Code Review
Fetch PR metadata, files, and diff. Review correctness, security, tests, regressions, and maintainability. Use inline comments only for actionable line-specific issues.

### Codebase Inspection
Use real tools such as pygount/cloc/tokei when available and report generated totals, never mental estimates.

## Common Pitfalls
1. Acting in the wrong repo or branch.
2. Committing unrelated/generated files.
3. Treating push success as CI success.
4. Posting vague review comments.
5. Treating status API `pending` with zero contexts/checks as success; it only means no checks were returned.

## Verification Checklist
- [ ] Owner/repo/default branch confirmed.
- [ ] Working tree checked before side effects.
- [ ] Mutation returned a URL, ID, or status.
- [ ] CI/review state checked when relevant.
