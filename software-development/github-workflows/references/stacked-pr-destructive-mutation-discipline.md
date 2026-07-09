# Stacked PR destructive mutation discipline

Use this when cleaning up or restacking a large PR backlog where force-push, PR retarget, squash merge, or branch deletion may be needed.

## Rule

Destructive remote PR mutations must be auditable, narrow, and sequential. Do not hide them inside a multi-action shell/Python script.

A single approved mutation should state:

- PR number and title when relevant.
- Target ref or PR metadata field.
- Expected old SHA / lease for force pushes.
- New local SHA for force pushes.
- Validation already completed.
- What is explicitly out of scope: no retarget, no merge, no cleanup, etc.

Then execute only that mutation. Verify the result read-only before the next mutation.

## Safe sequence

1. Restack locally in an isolated worktree.
2. Run the relevant local validation.
3. Read remote head SHA and local head SHA.
4. Force-push only with `--force-with-lease=<ref>:<old_sha>`.
5. Read remote head again and confirm it equals local head.
6. Separately retarget PR base if needed.
7. Wait for fresh exact-head `pull_request` CI; a green same-SHA `push` run is not a merge gate.
8. Separately squash merge only after the exact-head `pull_request` run is green.
9. Separately consider branch cleanup only after confirming no open children by `base.ref`.

## Missing pull_request run recovery

If a pushed/retargeted PR shows only a same-head `push` run and no `pull_request` run:

1. Wait for the push run to complete only as a diagnostic; still do not merge from it.
2. Confirm no `pull_request` run exists for the exact head SHA.
3. Create a tree-identical commit (`git commit --amend --no-edit`).
4. Verify old tree and new tree are identical.
5. Force-push with a lease from the current remote head.
6. Poll the new exact-head `pull_request` run.

If the `push` run fails but the fresh exact-head `pull_request` run later completes successfully with the full expected job set, use the `pull_request` run as the merge gate and report the ignored push-run failure explicitly.

## Pitfalls

- Do not combine force-push, PR PATCH, CI polling, merge, and cleanup in one script. It is technically convenient and operationally wrong.
- Do not retry a mutation through another API after Hermes guard blocks it. If the user has already granted the operation but Hermes needs an interactive approval prompt, issue the exact single destructive command directly so the approval can be granted; do not wrap it in scripts, compound shell pipelines, or manual-instruction detours. If there is no visible approval path and the user asks to stop the recurring blocker, pause the GitHub workflow and fix the Hermes approval configuration in the active profile, then return to the same single-command mutation boundary.
- Do not treat a previous broad user authorization as permission to make an opaque bundled mutation. Broad authorization lets you proceed; it does not remove the need for narrow visible mutation boundaries.
- Do not chain `git worktree add ... && git cherry-pick ...` from the parent repository when the cherry-pick is meant to run inside the new worktree. Create the worktree first, then run subsequent git commands with an explicit `workdir` set to that worktree. Otherwise a successful worktree creation can be followed by an accidental cherry-pick in the original checkout.
