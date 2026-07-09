# Public-label CI feedback loop (2026-06)

Use this reference when a dense stacked PR wave changes public-safe UI labels, source-kind labels, or leak-sentinel helpers.

## Durable lesson

Focused lane validation can pass while the full PR `web:test` fails in a broad integration file such as `App.test.tsx` because older assertions still expect the previous public labels. Treat label/vocabulary changes as cross-cutting public-surface changes even when the product code delta is small.

## Required controller loop

1. Keep the lane small and under `pr:size`, but expand validation just enough for the public surface:
   - run the lane's focused tests;
   - additionally run exact App/integration tests that assert the changed label surface, using `vitest run src/App.test.tsx -t "..."` rather than the whole large file first.
2. If exact-head `pull_request` CI fails, read the failing job and reproduce only the named failed tests locally.
3. Fix stale assertions or public-surface regressions in the same PR scope only.
4. Re-run:
   - the exact failed `App.test.tsx -t ...` slice;
   - the original lane focused `verify:quick` command.
5. Commit the fix normally and push. Prefer normal push for additive test fixes; do not force-push unless restacking requires it.
6. Comment on the PR with: failed run id, failing surface, new head SHA, local validation commands, and that the merge gate is the new exact-head `pull_request` CI.

## Example trigger

A label-firewall PR changed source matrix labels from raw-ish terms such as `Workspace file` / `Tmux observation` to public-safe `Workspace evidence` / `Runtime evidence`. Focused source-matrix and sentinel tests passed, but full `web:test` failed in three `App.test.tsx` assertions still expecting the old labels. The correct fix was updating only those stale App assertions, rerunning the exact three-test slice plus the original focused lane validation, then pushing a normal follow-up commit.

## Pitfall

Do not treat a green focused leak-sentinel test as proof that broad UI integration assertions are aligned. Leak-sentinel coverage proves the new vocabulary is safe; App/DetailsPanel/WorldScene integration assertions prove the visible shell still matches that vocabulary.

## Stuck GitHub Actions jobs

When one exact-head `pull_request` job stays `in_progress` for far longer than sibling shards and GitHub says logs are unavailable because the job is still running, treat it as CI-runner debt, not product evidence. Verify job-level state first. If a specific job cannot be rerun while in progress, cancel that stuck workflow run and rerun the same head/attempt through GitHub Actions. Record that the rerun was operational CI handling; do not change code, force-push, or merge based on the cancelled run.