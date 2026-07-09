# Closeout, PM truth, and worktree rescue playbook

Load when: closing PRs, auditing Linear/Slack/GitHub disagreement, handling stale worktrees, sequential sibling PR merges, duplicate CI closeout, or resuming from a handoff/cron.
Keywords: closeout, GitHub merged, master, Linear Done, Slack, audit correction, backfill, worktree prune, stale worktree, sibling rebase, current SHA, controller, cron.

## 1. Merge truth

A slice is merged only when GitHub PR state and master state agree.

Hard rule:
- GitHub PR `merged=true` plus actual merge/squash commit on master is merge truth.
- Slack merge-done text is not merge truth.
- Linear `Done` is not merge truth.
- A helper script's expectation that merge should soon succeed is not merge truth.

If Linear/Slack say Done but GitHub/master show the PR is still open:
1. treat GitHub/master as truth
2. restore Linear to `In Review`
3. post a truthful audit-correction note
4. continue closeout from real PR state
5. later, after actual merge, restore Done and post audit-resolution

## 2. Closeout sequence

Before merge:
- confirm current PR head SHA
- confirm required checks for that SHA/queue SHA
- confirm review requirement
- confirm no stale sibling rebase is needed
- confirm P0/P1 blockers are clear

After merge:
1. fast-forward local master
2. verify local HEAD is the merge commit or newer expected master
3. remove/prune worktree
4. delete local branch only after merge is verified
5. delete remote branch if appropriate
6. mark Linear Done with merge SHA/PR URL
7. send Slack merge-done or audit/backfill note
8. update controller lane evidence and exact next action/done state

After squash merge, `git branch -D` may be valid because the slice branch tip is not an ancestor of master. Use it only after PR merge and local master fast-forward are verified.

## 3. Backfill and audit wording

If the current run did not perform a merge or closeout step, do not word messages as if it did.
Use explicit labels:
- audit/backfill
- audit correction
- audit resolution
- closeout continuation

If a Linear issue did not exist for already-started work, create a backfill issue with truthful wording. Map branch/PR/SHA to that issue and set state to the real current phase.

## 4. Resumed run audit

On every resumed/handoff/cron run, inspect live truth before acting:
- `git status -sb`
- `git rev-parse HEAD`
- `git worktree list --porcelain`
- open/merged PRs and current head SHAs
- Linear state
- recent Slack trail if relevant
- controller/handoff exact next action

If remembered process IDs return `not_found`, do not assume failure. Another pass may already have completed the work.

If a remembered worktree path is missing, audit PR/master/Linear first. It may already be merged and cleaned.

## 5. Stale worktree safety

A leftover `.worktrees/<slug>` directory can exist even after it is no longer a registered worktree.
Do not trust `git -C <path>` until you verify:
- path appears in `git worktree list`
- path has a `.git` file or valid worktree metadata
- `git rev-parse --show-toplevel` equals the expected path
- workspace manifest files exist where expected

If `git worktree list` reports a prunable entry, run `git worktree prune` before deleting the local branch.

If the directory is stale debris and PR is already merged, remove the directory only after verifying master/PR state.

## 6. Sibling PR sequential closeout

When several sibling PRs touch the same hot file:
1. merge only one green sibling at a time
2. fast-forward local master
3. rebase/restack each remaining sibling onto new master
4. rerun required validation on the rebased local head
5. force-push/update PR
6. wait only on the new PR head SHA
7. ignore old SHA CI once new head is pushed

Do not keep waiting on obsolete old SHA checks after a sibling merge.

## 7. Transport and API flakes

Git SSH transport can flake. If fetch/push fails with connection-closed style errors:
- retry briefly
- fall back to HTTPS + auth header/token for that operation when available
- do not classify it as repo-state failure without evidence

GitHub/Linear/Slack API helpers should handle:
- transient 5xx/429/network TLS errors with bounded retry
- REST `204 No Content` as success, not JSON parse failure
- GraphQL schema differences by using known working query shapes

## 8. Slack degradation

Slack is required for delivery communication when available, but not a truth source.

If Slack delivery fails:
1. retry the known working target form once
2. try direct Slack API if configured
3. if still unavailable, record degraded Slack state in Linear/final report
4. do not claim Slack was sent
5. do not block code closeout solely on Slack transport if GitHub/local/Linear truth is complete and the degradation is recorded

## 9. Closeout is not implementation

Report state precisely:
- implementation complete: code/validation/review done
- PR-ready: branch pushed and PR opened with required evidence
- delivery complete: merge/master cleanup/Linear/Slack/controller all done
- closeout-only continuation: no new implementation; only finishing delivery chain

Never collapse those into one vague Done.