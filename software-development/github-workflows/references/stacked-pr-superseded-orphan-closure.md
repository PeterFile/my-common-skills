# Stacked PR superseded/orphan closure notes

Use this when an open PR is based on an old stack base that is no longer open, and the PR title or diff appears to overlap work already squash-merged into the default branch.

## Safe decision path

1. Rebuild the live open-PR inventory first. Identify whether the PR's `base.ref` is neither the default branch nor the `head.ref` of another open PR. Treat that as an orphaned stack base, not as mergeable state.
2. Check whether the feature is already present on the current default branch using multiple cheap signals:
   - `git log origin/<default> --grep='<feature title terms>' --regexp-ignore-case`
   - search the current files for the route/API/component/test names added by the old PR
   - compare the old PR changed-file list against current default-branch implementation shape
3. If default already contains an evolved implementation, do not merge or restack the stale PR. Closing is safer than reintroducing outdated contract text, test expectations, or old parent-stack commits.
4. Leave a concise PR comment with evidence: the default-branch commit or current files/routes/tests that supersede it, and why merging the stale diff would be dishonest or regressive.
5. Close the PR through the issue/PR API.
6. Before deleting the remote head branch, re-query open PRs whose `base.ref` equals that head ref. Delete only when the child list is empty.
7. Clean local restack worktrees/branches only after the remote PR is closed and remote head cleanup is safe.

## Pitfalls

- A same-title commit on `master` is not enough by itself. Verify current code/tests/docs still contain the relevant behavior.
- Do not close a PR merely because its old parent PR was squash-merged; if the child delta is still missing, rebuild the child delta onto the correct base instead.
- Do not delete a head branch that still has open children; retarget/restack children first.
- Do not merge a stale orphan PR to get it out of the queue. That can silently restore obsolete contract shapes or duplicate already-merged parent work.

## Good closeout comment shape

```
Closing as superseded by the current default-branch implementation. `origin/<default>` already contains <commit/title> and the current <routes/files/tests> are present. This PR is still based on old stack base `<base-ref>` and would reintroduce stale <contract/test/docs> shape rather than the evolved current implementation.
```
