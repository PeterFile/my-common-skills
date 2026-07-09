# SkyTurn stacked slice delivery notes

Use this when orchestrating a multi-slice SkyTurn delivery with child coding agents and stacked PRs.

## Durable workflow

1. Treat parent agent summaries as untrusted until parent verification has read the diff and run the relevant tests/typecheck/build.
2. Only push/open PRs for slices that are all three: locally committed, parent-validated, and review-only approved.
3. If the user asks to open completed slice PRs before continuing, do it immediately for those approved slices with the correct stacked base. Do not wait for integration.
4. Keep unfinished slices dirty/local and do not include them in PRs.
5. For stacked PR bases, use the slice dependency graph, not chronological order:
   - contract/kernel root -> `main`.
   - backend/IPC depending on contracts -> contracts branch.
   - renderer helpers depending on backend contracts -> backend branch.
   - docs that depend on contract wording -> contracts branch.
6. PR creation is not completion. Integration still needs a fresh integration branch, merge/cherry-pick of approved slices, full gates, and a final PR.

## UI-only slice guardrail

For UI-only slices, do not fake durable workflow behavior by stuffing typed action fields into a generic text/user-input path if the backend ledger drops them. Either:
- show the selection/action affordance as disabled or pending backend wiring; or
- move the typed persistence/IPC change into the correct backend slice.

This prevents the UI from claiming repair/variant/rollback semantics that are not replayable from the ledger.

## Integration PR closeout after sibling slice PRs

When independent SkyTurn slice PRs are opened for review and a final integration PR cherry-picks them together:

1. Treat the integration PR as the only delivery PR. Before merging, verify it is `CLEAN` and has a green current `pull_request` CI check.
2. Squash-merge the integration PR with the cleaned integration PR body, then re-query the PR by number. `gh pr merge` may print little or nothing; `gh pr view <n> --json state,mergedAt,mergeCommit` is the evidence.
3. If the user instead asks to merge the whole opened stack sequentially, merge the root PR first, fast-forward local `main`, retarget direct children to `main`, and require a fresh exact-head `pull_request` check after every retarget/update. When `gh pr update-branch` conflicts after a parent squash merge, do not merge the stale branch: create a fresh worktree from current `origin/main`, cherry-pick only the intended child delta commit, run the slice validation, then update the PR head with `--force-with-lease` and wait for a fresh check.
4. For join/integration PRs after sibling slices have landed, restack only the final integration delta commit on current `main`; the earlier sibling commits should already be absorbed by their squash merges and must not be reintroduced into the PR diff.
5. Close the sibling slice PRs as superseded by the integration PR. Include a short comment such as “Integrated and delivered through #<integration>.”
6. Do not rely on `gh pr close --delete-branch` when local worktrees still use those branch names. It can close the PR and then fail on local branch deletion. After any such partial failure, first verify the PR state, then continue cleanup explicitly.
5. Before deleting remote heads, verify no open PR uses each ref as either `headRefName` or `baseRefName`.
6. Delete remote temporary branches one at a time with `git push origin --delete <branch>` so each destructive mutation has a visible audit boundary.
7. Fast-forward local `main` to the squash commit, remove temporary worktrees, then delete local slice/integration branches. Use `git branch -D` for local cleanup after a squash merge because the original slice commits are intentionally not ancestors of `main`.

## Review lessons

- Review-only agents should inspect the actual integrated/worktree diff, not child summaries.
- Re-run review after every material fix; repeated BLOCK is a signal to narrow the repair further, not to commit anyway.
- Accessibility review should catch nested interactive controls: if a node card has a More button, keep the selectable target and the More button as distinct controls with clear labels and consistent visual selection state.
