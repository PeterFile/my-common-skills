# SkyTurn delegated slice PR verification

Use this when Hermes is acting as parent/operator while Codex or Antigravity CLI implement small SkyTurn slices in separate worktrees.

## Pattern
1. Create or reuse integration branches for the large direction, then create one child branch/worktree per small slice.
2. Give each child agent a narrow prompt with: exact worktree, base branch, allowed files, non-goals, validation commands, and a ban on commit/push/PR unless explicitly delegated.
3. Treat child summaries as leads only. Parent must inspect `git diff`, run `git diff --check`, and run the smallest relevant tests/typechecks in the child worktree.
4. If parent finds a bug, send a narrow repair prompt to the same child worktree instead of broad manual rewrites.
5. After every post-review edit or whitespace cleanup, rerun the relevant verification in the exact worktree before committing.
6. Commit only after the worktree is clean except intended files and verification is fresh.
7. Push slice branches and open PRs against the integration branch, not `main`, unless the user explicitly asks for direct-to-main.
8. After opening PRs, read them back with GitHub and post the parent verification evidence as a PR comment. Do not merge unless asked.

## Pitfalls
- A shell command can print successful push/PR URLs and still exit non-zero because of later cleanup/parsing. Read back branch/PR state before reporting success.
- `git diff --check` without a revision checks working-tree diff; after committing, use `git diff --check HEAD~1..HEAD` for committed whitespace evidence.
- If a system or user asks for fresh verification after a commit, rerun the actual commands; do not cite prior verification output.
- For UI visual slices, style tests/typechecks prove contracts only. They do not prove the user likes the visual result; separate automated evidence from visual approval.
