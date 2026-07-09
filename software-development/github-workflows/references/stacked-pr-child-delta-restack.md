# Stacked PR child-delta restack notes

Use this when a parent PR was squash-merged and an open child PR still targets the old parent branch.

## Problem pattern

After retargeting or partially restacking a stack, the child PR head may not be a descendant of the already-restacked parent commit reported by GitHub. A naive `parent..child` diff or rebase can drag in stale stack history and produce a huge misleading diff.

## Safe sequence

1. Fetch the child head branch and its old base branch explicitly.
2. Inspect ancestry before choosing a cut point:
   - `git rev-parse origin/<child-head>`
   - `git rev-parse origin/<old-base>`
   - `git merge-base origin/<child-head> origin/<old-base>`
   - `git log --oneline --reverse origin/<old-base>..origin/<child-head>`
3. If `old-base..child-head` contains stale parent commits or unrelated old stack commits, do not rebase that whole range.
4. Identify the intended child delta commit directly, usually the child head commit:
   - `git show --stat --name-only <child-head>`
   - `git show -s --format=%P <child-head>`
   - `git diff --stat "<child-head>^!"`
5. Create a fresh worktree from current `origin/master`/`origin/main` and cherry-pick only the intended child delta commit.
6. Verify the diff is honest against current default branch before validation:
   - `git diff --stat origin/main...HEAD` or `git diff --stat origin/master...HEAD`
   - `git diff --check`
7. Run the appropriate lane, push with a lease from the old remote child SHA, patch PR base to the default branch, then require a fresh exact-head `pull_request` gate before merging.

## Sequential squash closeout variant

When closing a stack by squash-merging each PR into the default branch:

1. After each parent PR squash merge, fetch and fast-forward the local default branch before touching children.
2. For the next child, retarget the PR to the default branch and try `gh pr update-branch <n>` first. If it succeeds, verify the child diff is still just the intended delta and wait for the fresh exact-head check.
3. If `gh pr update-branch` reports conflicts, restack locally from current `origin/main`/`origin/master` and cherry-pick only the child delta commit. This also applies to integration/join PRs after their sibling slice PRs have already been squash-merged; do not merge the old join branch wholesale.
4. Validate the restacked worktree, then `git push --force-with-lease=refs/heads/<head-ref>:<old-remote-sha> origin HEAD:<head-ref>`.
5. Re-query the PR head SHA, diff, and checks after the force-push. Merge only after the new exact-head `pull_request` check is green.

## Shell and fresh-worktree pitfalls seen in this workflow

- In zsh, a refspec using a variable needs braces: `+refs/heads/${ref}:refs/remotes/origin/${ref}`. Without braces, `$ref:refs` can be parsed as one parameter expansion.
- Avoid `awk '{print $1}'` inside a single-quoted `zsh -lc '...'` wrapper; `$1` can be expanded by the outer shell or break quoting. Prefer `cut -f1` for `git ls-remote` output.
- Do not chain worktree creation and cherry-pick in one parent-repo shell command. `git worktree add ... && git cherry-pick <sha>` runs the cherry-pick in the original shell cwd, not automatically in the new worktree. After creating the worktree, issue the cherry-pick as a separate command with `workdir` set to the new worktree path.
- If an accidental local commit lands in the wrong checkout and has not been pushed, stop and restore that checkout before continuing the remote workflow; do not proceed with a polluted default-branch worktree.
- Quote single-commit revspecs: `git diff --stat "${sha}^!"`.
- In a fresh pnpm worktree, if local deps are absent, install with a command-scoped store path such as `pnpm install --frozen-lockfile --prefer-offline --store-dir /path/to/store`. Do not run `pnpm config set --location project store-dir ...` unless you intend to commit config; it can dirty `pnpm-workspace.yaml` and create unrelated PR noise.
- When a child delta changes public label/render helper semantics, do not trust the original PR's changed hunks as the full test surface. Search both product rendering code and the affected test tree for stale old visible strings (for example raw enum/source labels). If the new helper is meant to centralize display policy, wire every matching product surface through the helper instead of only updating assertions; then update tests to the new public text and run focused tests that cover the helper plus all UI surfaces where that text appears. For large App integration files, first rerun the exact failing `-t` patterns to prove the specific fix, then run the whole file before pushing even if it is slow.

## Why this matters

The merge gate is based on the honest child diff after the parent squash is already in `master`. If the candidate diff contains old parent docs/tests/UI churn, stop and recalculate the child delta instead of resolving conflicts blindly.
