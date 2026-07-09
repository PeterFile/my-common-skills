# Guarded delivery closeout after integration PRs

Use this when a user asks to finish a validated integration PR, merge it, sync main, and clean delivery artifacts.

## Preconditions

- Re-query the live PR immediately before merging: `gh pr view <n> --json state,headRefOid,mergeStateStatus,statusCheckRollup`.
- Verify exact-head CI is green for the current `headRefOid`; stale green checks do not count.
- Verify the local worktree is clean before mutation.
- If the user has already granted broad closeout authority, do not ask again with a generic clarification prompt. Execute each destructive mutation as its own visible, auditable tool command so Hermes can surface any required approval.

## Merge sequence

1. Save or prepare the squash body from the PR body.
2. Run a single direct merge command, for example:
   `gh pr merge <n> --squash --subject "type(scope): summary" --body-file <body.md>`.
3. Re-query the PR after merge. If the command reports a local checkout/worktree error, still check remote PR state before retrying; GitHub may already have merged it.
4. `git fetch origin` and verify `origin/main` moved to the merge commit.
5. In the real main worktree, run `git pull --ff-only origin main` and verify `HEAD == origin/main`.

## Cleanup sequence

- If the user says "cleanup" while the final validated PR is still open, finish that PR first: re-query its exact-head check, squash merge it, fetch, and fast-forward local default branch. Cleanup only starts after all intended delivery PRs are `MERGED`.
- First confirm there are no open PRs depending on the branches you plan to delete: `gh pr list --state open --json number,baseRefName,headRefName,title,url`.
- Close disposable smoke PRs instead of merging them. If cleanup is authorized, use `gh pr close <n> --delete-branch --comment ...`.
- Delete integration remote branches explicitly, for example: `git push origin --delete integration/<name>`. For a multi-branch stack, delete remote heads one ref at a time after confirming no open PR uses that ref as `baseRefName` or `headRefName`.
- Run `git fetch --prune origin` and verify remote-tracking refs disappeared.
- Remove local worktrees before deleting their branches: `git worktree remove <path>`.
- After worktree removal, delete local slice branches. For squash-integrated slice branches, `git branch -D <branch>` is expected because Git cannot prove the squash merge ancestry.
- Final verification: `git status --short --branch`, `HEAD == origin/<default>`, `git worktree list --porcelain`, relevant `git branch --list`, relevant `git branch -r`, and `gh pr list --state open`.

## Pitfalls

- Do not treat a killed or stale background validation process as the final result if a later run produced a verified pass. Report which log/run is authoritative.
- Do not bundle merge, PR close, remote branch deletion, worktree deletion, and local branch deletion inside one opaque script. Keep each high-impact mutation separately visible.
- `gh pr close --delete-branch` can successfully close the PR but still exit non-zero when the local branch is checked out by another worktree. Treat the PR-close side effect and local cleanup as separate facts: re-query open PRs, close any remaining absorbed PRs without `--delete-branch` if needed, then delete remote branches and remove local worktrees/branches in explicit cleanup steps.
- If a branch deletion command says it skipped local branch deletion because the current directory is not a git repository, distinguish that from remote deletion; verify the remote branch separately with `git fetch --prune`.
