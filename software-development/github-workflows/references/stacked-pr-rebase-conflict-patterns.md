# Stacked PR rebase conflict patterns

Use during large stacked-PR cleanup when a PR is being rebased onto a default branch that has advanced through adjacent PR merges.

## Preserve adjacent test-only additions

Common pattern: two test-only PRs both append cases near the same location in a large test file. Git reports a conflict even though the intended behavior is additive.

Safe resolution:
1. Confirm both sides are test-only or otherwise non-overlapping behavior.
2. Read the full conflict block, not just the marker lines.
3. Keep both tests/helpers as adjacent blocks; do not choose one side just because one is `HEAD`.
4. Run `git diff --check`, search for conflict markers, then continue the rebase.
5. Run the lane-level validation, not only the single conflicted test, because nearby test helpers can share global fixtures.

## Merge evolved contract fields instead of deleting them

Common pattern: a PR tightens a frontend/API exact-shape assertion while `master` has gained a new backend public field. After rebase, the exact-key assertion fails because it does not include the master field.

Safe resolution:
1. Treat the local test failure as evidence that the PR is stale, not that the new master field is wrong.
2. Verify the field is a current public contract field by checking runtime/backend contract code or existing backend tests.
3. If the PR's scope is parity/type/contract coverage for that surface, add the new field to the frontend type, fixtures, and exact-key assertion in the same PR.
4. Use the real reason-code/value names from backend code or tests; do not invent placeholder enum strings.
5. Re-run the focused contract tests and typecheck before force-pushing.

## Restack children after a squash-merged parent

Common pattern: a parent PR was squash-merged into `master`, but direct child PRs still have `base.ref` pointing at the old parent branch and their branch history still contains the original unsquashed parent commits. The parent branch head, the restacked parent commit, and the squash merge commit are different objects.

Safe resolution:
1. Re-read each child PR live: `base.ref`, `base.sha`, `head.ref`, and `head.sha`. Do not trust handoff text or old local branch names.
2. Inspect ancestry before rebasing: compare the child head against the old parent commit(s) with `git merge-base` and `git log --reverse <cut>..<child-head>`. Identify the real old parent cut point in the child branch history.
3. Rebase only the child delta onto current `origin/master`: `git rebase --onto origin/master <old-parent-commit-in-child-history> HEAD`. Do not use the parent squash merge SHA, a restacked parent SHA, or the PR API `base.sha` unless it is actually in the child history.
4. If the child tip's direct parent is the old parent commit, prefer cherry-picking only that child tip onto current `origin/master` instead of replaying the whole stale stack. Verify with `git show -s --format=%P <child-head>` and `git log --oneline --reverse <old-parent>..<child-head>` before doing it.
5. When conflicts are in evolved docs/tests or adjacent helper constants, preserve current `master` semantics first and reapply only the child feature delta. Avoid accepting the child side wholesale; it can silently delete newer already-merged contract text, helper labels, or regression tests.
6. Validate the resulting diff against `origin/master` is the child’s intended scope only. Then run the lane gate, push with a lease against the child’s old remote head SHA, patch the child PR base to `master`, and wait for fresh `pull_request` CI.
7. Delete the old parent branch only after all open PRs using it as `base.ref` have been restacked or closed and a live query returns none.

## Child PRs after squash-merged parents

When a child PR was stacked on a parent that has since been squash-merged, do not replay the whole branch history. Inspect the child PR commit list and cherry-pick only the true child commit(s) onto current `origin/master`. The parent squash already contains the parent behavior under a new SHA. After the child merges, confirm no open PR uses either the old parent head ref or child head ref before deleting branches/worktrees.

For documentation conflicts where current `master` replaced an old bullet-list section with a scored route/objective table, keep the current table shape. Fold the child PR's still-relevant wording into the matching row rather than restoring the obsolete section. Example: a child that expands cross-surface leak-guard canaries should update the existing `Public label firewall` row, not resurrect old scoreable-slice bullets.

For UI child conflicts that add a new detail control after a parent squash, keep the parent semantics from `master` and add only the child extension. Example pattern: preserve existing world-focus evidence behavior while adding a bounded ledger stepper's args/render call; validate with the new helper test plus the UI quick lane.

For UI enum/label helper conflicts, do not blindly keep the old child helper tables. Older stack branches often centralize allowlisted labels while `master` has since evolved the public human-readable labels. Preserve the child’s safety property (allowlist plus `Unknown` fallback), but fold in current `master` labels and grouping semantics before committing. Concrete checks: fixture/tool source kinds may intentionally collapse to generic copy such as `Tool evidence`/`Linked evidence`; ledger surfaces may expect human labels like `Workspace file`, `Runtime observation`, `Agent output`, `Observed`, not raw enum keys like `workspace_file` or `tmux_observation`. Run focused UI tests before pushing; if tests fail on expected visible labels, fix the helper mapping rather than weakening tests.

For backend/schema catalog stacks where adjacent PRs add static read-only schema routes, conflicts often happen in the same docs bullet cluster and route-boundary tests. Preserve every already-merged static schema route and current field list first (for example controller snapshot `append-proof` must stay if it is on `master`), then add the child PR's one new schema route/test as an adjacent block. Do not accept the child side wholesale: old child branches can silently drop newer route names, public field names, or read-only boundary tests. After resolving, search conflict markers, run `git diff --check`, and use the backend lane because route ordering/static-schema purity is shared.

## Force-push discipline after conflict repair

- Amend the repaired rebase result into the PR's single commit when the PR was intended to stay single-commit.
- Push the exact rebased commit with `--force-with-lease=refs/heads/<head-ref>:<old-head-sha>`.
- Re-read the PR to confirm `base.ref`, `base.sha`, and `head.sha` are what you think they are.
- Require a fresh `pull_request` Actions run for that head; a local green gate is not the merge gate.
