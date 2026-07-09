# Stacked PR governance notes

Use this when a repository already has a large remote stack/backlog and the task is to merge, close, restack, or repair many PRs.

## Safe order
1. Build a live remote inventory from GitHub, not from local stack state alone: PR number, base ref, head ref, head SHA, mergeable state, CI conclusion, and changed files.
2. Model dependency order by `base.ref`: default-branch roots first, then direct children, then leaves.
3. For each root, choose one action: merge if fresh CI is green and diff is still intended; close if superseded; fix if conflict/red CI is in-scope.
4. Before deleting or merging away a parent branch, retarget/rebase direct children. Verify each child branch after the push.
5. Work in small checkpoint batches. Re-inventory after each batch because GitHub mergeability, CI, and base refs change asynchronously.

## Rebase/restack correctness checks
After any scripted rebase or cherry-pick, verify the remote PR head, not just the local commit:

- expected old head SHA was captured before the force push
- force push used `--force-with-lease=refs/heads/<head-ref>:<old-sha>`
- PR `base.ref` is the intended new base
- PR `head.sha` equals the rebased commit you intended to publish
- `git diff origin/<base>...<head>` contains only that PR's intended diff
- a fresh pull_request CI run started after the push and is the merge gate

## Detached HEAD / no-op push pitfall
A common scripted failure is:

1. add worktree from `origin/<pr-head>`
2. rebase/cherry-pick to create the correct commit while detached
3. checkout the old local branch again
4. push `<branch>:refs/heads/<head-ref>`

That can update the PR base while leaving the remote head unchanged, producing a misleading no-op push. Fix by pushing the exact rebased commit SHA to the PR head ref with a lease against the captured old SHA, then re-read the PR and confirm `head.sha` changed.

## Fresh CI gate discipline
For stacked PR cleanup, CI success is only a valid merge gate when it belongs to the current remote PR head and intended base after the latest restack. Do not reuse an older green run after any of these events:

- default branch advanced because a parent/root PR merged
- the PR was retargeted to a new base
- the head was force-pushed, even if the diff looks identical
- duplicate/stale workflow runs were canceled

After merging a parent PR, immediately restack direct children, push their exact new heads with leases, then wait for new pull_request CI. Treat `cancelled`, `skipped`, missing checks, and green runs attached to an old SHA/base as blockers, not success. If a repo has multiple required jobs or smoke shards, confirm the full expected set succeeded before merging; one successful job is not the whole gate.

When API status is unavailable, rate-limited, or returns only `pending` with no useful checks, use another read-only source rather than relaxing the gate. Acceptable fallbacks include the GitHub checks page for the PR/head SHA or locally reduced API payloads saved by the tool. On the checks page, separate `push` from `pull_request`; only the current-head `pull_request` suite with the expected jobs green is sufficient. If the snapshot collapses suites or omits icons, inspect DOM text/links for job names and icon aria labels such as succeeded/failed/in progress, then record the run id and job set in the handoff.

## Required-CI flake discipline during large PR cleanup

When a current-head pull_request gate fails in files outside the PR diff, do not assume it is safe and do not merge around it. First prove scope: read the failed job log, compare the failing file/test to the PR diff, and run the specific failing test locally if possible. A single rerun is acceptable when the local isolated test passes and the failure is plausibly unrelated flake. If rerun fails again, stop rerunning blindly: treat the flaky required check as the current blocker, stabilize the test or create/merge a small unblocker PR, then resume the stack. Local full-suite success is useful evidence for diagnosis but never replaces the required fresh pull_request gate.

Detailed notes: see `references/stacked-pr-ci-flake-discipline.md`.

## Replacement PR fallback for dishonest child diffs

When a parent PR was squash-merged, a child PR may still be based on the parent branch or on an older ancestor. If the child branch is rebuilt cleanly on the default branch but the existing PR cannot be retargeted with the available toolset, do not merge the old PR with a misleading diff.

Safe fallback:

1. Identify the child commit's true single-PR patch, usually `git diff HEAD^..HEAD`, and verify it excludes already-merged parent work.
2. Reset a dedicated worktree to `origin/<default-branch>` and cherry-pick/apply only that patch.
3. Run the smallest relevant local gate.
4. Force-push the clean commit to the child head branch with a lease against the old head SHA.
5. Open a replacement PR from the same clean head to the default branch.
6. Comment on and close the old PR as superseded, linking the replacement and explaining the diff honesty issue.
7. Do not delete the child head branch until the replacement PR is merged and no open PR depends on it.

This preserves reviewability and avoids merging stale parent changes twice.

## Continuation after handoff drift

When resuming a long PR cleanup from a previous-session handoff, treat the handoff as a lead, not live truth. The named "next PR" may already have been merged, closed, retargeted, or superseded by an external actor or a later partial run. First rebuild the current open-PR DAG from GitHub and compare it to the handoff before acting. If the handoff's next PR is no longer open, do not try to resurrect or repeat it; mark that step complete by live state and choose the next safest default-branch root.

For root selection during a large backlog, prefer low-risk roots first when the user did not specify a semantic priority: default-branch PRs with no open children, small/contained diffs, and local validation commands that are cheap and specific. This reduces retarget churn before taking on roots that require immediate child restacking.

## Post-merge cleanup discipline

After a successful squash merge, separate read-only verification from destructive cleanup. First re-read open PRs whose base is the merged head branch; only delete the remote head branch if there are no open children depending on it. If a destructive cleanup command is denied by the runtime approval layer, stop and report the exact completed merge SHA plus the unperformed cleanup steps. Do not retry the same deletion through another route without user approval.

## Budget-boundary and compaction handoff discipline

Large PR cleanups often stop mid-PR because of tool/iteration budgets or context compaction. Treat any local-only restack as unsafe until the next session re-verifies it. In the handoff, explicitly separate remote facts from local preparation:

- PR number, title, base ref, head ref, and old remote head SHA captured before local work
- local worktree path and local branch name for any in-progress restack
- local new head SHA only if it was actually created
- changed files and diff honesty result relative to the intended base
- local validation already run, with exact command and pass/fail result
- whether the new head was pushed; if not pushed, say so plainly and do not describe it as PR state
- whether a fresh pull_request CI run exists for that exact remote head; if not, the PR is not mergeable
- cleanup that was intentionally skipped or denied, separated from merge correctness

On resume, first rebuild live GitHub state and compare it to the handoff. If the local worktree still exists, re-check `git status`, `HEAD`, and `git diff origin/<base>...HEAD` before validating or pushing. If default branch advanced since the local-only rebase, rebase again before running CI or force-pushing.

## Status reporting
For large governance runs, status updates should separate:

- merged PRs with merge SHAs
- closed/superseded PRs and why they were not merged
- replacement PRs created to preserve honest diffs, including old/new PR numbers and clean head SHA
- restacked PRs with old/new head SHAs, clearly marking local-only heads versus pushed remote heads
- blocked PRs with the exact blocker: conflict, red CI, missing fresh CI, stale diff, dependency not merged, or cleanup denied after merge
- local/background validation process IDs only as transient handoff detail, not durable documentation

