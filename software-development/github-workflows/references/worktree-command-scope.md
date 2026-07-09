# Worktree command-scope pitfall

When restacking PRs in isolated worktrees, command working directory is part of correctness. A common mistake is to run:

```sh
git worktree add -b <branch> <path> origin/master && git cherry-pick <sha>
```

from the main repository. The `git cherry-pick` runs in the original working directory, not in the new worktree, and can dirty or conflict the default branch.

Safe pattern:

1. Create the worktree as a standalone command.
2. Run `git status --short --branch` in the target worktree path.
3. Run cherry-pick/rebase/commit commands with `workdir=<new-worktree-path>` or `git -C <new-worktree-path> ...`.
4. If the wrong worktree is accidentally dirtied by a cherry-pick/rebase, stop and run the matching abort command there (`git cherry-pick --abort` / `git rebase --abort`), then verify its status is clean before continuing in the intended worktree.

This is not a Git bug; it is shell command scope. Do not hide worktree creation and mutation in one chained command during PR restacks.