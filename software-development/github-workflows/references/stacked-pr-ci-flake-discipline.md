# Stacked PR required-CI flake discipline

Use this note during large stacked-PR cleanup when the PR diff is honest, but the required pull_request gate fails in an unrelated test or file.

## Classification

Before any rerun or merge decision, prove which case you have:

1. Confirm the run is the current pull_request run for the remote PR head SHA and current base.
2. Read the failing job log, not just the GitHub summary.
3. Compare the failing file/test with `git diff origin/<base>...HEAD`.
4. If the failing test is outside the PR diff, run that exact test locally in the PR worktree.

Do not call it an unrelated flake until steps 1-4 are done.

## Allowed response

- If the exact failing test passes locally and the failure is outside the PR diff, one pull_request rerun is reasonable.
- If the rerun passes, merge only after the full required job set is green on the same head/base.
- If the rerun fails again, stop rerunning blindly. The current blocker is now required-CI instability, even if the PR diff is clean.

## Blocker handling

When rerun fails again:

1. Keep the PR unmerged.
2. Stabilize the failing test or create a small unblocker PR on the default branch.
3. Validate the stability fix with the exact failing test and the cheapest relevant suite.
4. Merge the unblocker only through a fresh green pull_request gate.
5. Rebase/restack the original PR on the updated default branch and restart its fresh pull_request gate.

## What not to do

- Do not merge a PR with a red required gate because the failure is "unrelated".
- Do not use local full-suite success as a substitute for required GitHub pull_request CI.
- Do not keep rerunning the same red gate indefinitely; repeated unrelated failures are evidence that CI itself must be fixed first.
- Do not push child PRs based on local preprocessed heads after parent/master changes without rebase, diff audit, and fresh CI.

## Useful handoff details

When stopping at this blocker, record:

- PR number, current head SHA, base ref.
- Failed run id and attempt number.
- Failed job name and exact test name/path.
- Local reproduction command and result.
- Whether a rerun was attempted and its result.
- Which local child heads are only preprocessed and must not be treated as remote truth.
