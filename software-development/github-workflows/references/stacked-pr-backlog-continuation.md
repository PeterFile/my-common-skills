# Stacked PR backlog continuation notes

Use this when a stacked GitHub PR cleanup spans multiple agent sessions or hits an iteration/tool budget boundary.

## Resume sequence

1. Treat previous-session summaries as leads, not proof. Re-confirm live state before mutations:
   - `git fetch origin --prune`
   - repo/default branch/current HEAD
   - `git status --short --branch`
   - open PR inventory: number, base ref, head ref, head SHA, title
   - local worktrees/branches that may hold an unfinished restack
2. Resume the smallest unfinished lifecycle step. Do not restart completed PRs.
3. If an unfinished restack worktree exists, inspect it before recreating anything:
   - status and branch tracking
   - `git diff --check origin/master...HEAD`
   - whether validation already ran after the final commit
4. For each PR, keep the gate strict:
   - push with `--force-with-lease=<head-ref>:<old-remote-sha>`
   - retarget to `master` only after the branch contains an honest diff against current `origin/master`
   - wait for a fresh `pull_request` run for the exact head SHA
   - require the full expected job set, not just a green push run
5. After merge, cleanup is conditional:
   - delete the merged PR head only after checking no open PR still has `base.ref == <merged-head-ref>`
   - keep parent head branches while children still target them
   - delete local restack worktrees/branches after merge or confirmed abandonment

## Budget-boundary handoff format

When forced to stop mid-backlog, write a handoff with these fields, and avoid narrative noise:

- repo, local path, default branch
- current `origin/master` SHA if verified
- PRs merged this window: number, title, exact head SHA, CI run id, merge SHA, cleanup performed
- PRs closed as superseded: evidence and cleanup performed
- current in-progress PR: worktree path, branch, old remote SHA, new local SHA, conflicts resolved, validation command/result, and the next exact command-class step (push, retarget, poll CI, merge, cleanup)
- retained branches and why, especially parent branches kept for open children
- remaining open PR inventory or explicitly mark it stale if not reprinted

## Pitfalls

- A passing local lane is not a merge gate. It only permits pushing/restacking; GitHub still needs a fresh exact-head `pull_request` run.
- A merged parent does not make its old branch deletable if a child still targets it.
- Do not delete remote stack branches as cleanup based on memory; query open children first.
- During cleanup, remove only the exact restack worktree/branch created for the completed PR. If a similarly named older worktree exists, especially detached or dirty with conflict markers/unmerged paths, inspect it and report it rather than deleting it as part of the current PR cleanup.
- Do not turn a failed/zero-test targeted command into validation. Rerun the command that executes the intended tests.
- If validation succeeded but you stop before status/push, the next session should verify status/diff first rather than redoing conflict resolution.
