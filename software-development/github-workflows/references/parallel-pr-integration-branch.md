# Parallel PR integration branch pattern

Use when several independently green PR/worktree branches overlap heavily enough that sequential squash merges would be risky or misleading.

## Trigger
- Multiple open PRs share a base branch and touch the same contracts, IPC surfaces, package exports, generated lockfile, or UI/runtime boundaries.
- Each PR is locally green in isolation, but the combined product path depends on all of them.
- Mergeability from GitHub is unknown/stale (`mergeable: null`) or too coarse to expose API drift between PRs.

## Procedure
1. Keep the default branch clean. Create a dedicated integration worktree/branch from the current remote default branch, e.g. `git worktree add -b feature/<topic>-integration <path> origin/main`.
2. Fetch PR heads explicitly (`refs/pull/*/head:refs/remotes/origin/pr/*`) and merge them into the integration branch in dependency order, not PR-number order. Typical order: shared contracts/kernel -> ledger/persistence -> backend services -> evidence/services -> UI -> desktop IPC.
3. On conflicts, preserve additive behavior from both sides. Do not resolve by deleting one feature slice just to satisfy TypeScript. Common conflict classes:
   - add/add Node-only service files: combine service interfaces/tests into one Node-only module;
   - renderer-facing API types: keep legacy UI compatibility plus the newer narrow API surface;
   - Electron preload/main IPC: preserve both old call names used by current UI and new grouped workflow APIs;
   - duplicated helpers from two branches: keep one implementation and update all call sites.
4. After each conflict-resolved merge, finish the merge commit with `GIT_EDITOR=true git merge --continue` to avoid editor hangs in non-interactive sessions.
5. Verify every original PR head is included: `git merge-base --is-ancestor origin/pr/<n> HEAD`.
6. Run the full integration validation on the integration branch before merging anything to default. For pnpm monorepos on external disks, if the default store hits symlink/permission problems, use a temporary store (`pnpm install --frozen-lockfile --store-dir /tmp/<repo>-pnpm-store`) and record that this is an environment workaround, not a source change.
7. Prefer opening/merging one integration PR after validation over squashing overlapping PRs one by one. The original PRs can then be closed as superseded or left linked as absorbed; do not pretend their isolated checks prove the combined result.
8. If the integration PR is opened while a long acceptance command is still running, treat the PR body as provisional. After the background command exits, update the PR body or add a status comment with the final result; do not leave stale text such as “still being monitored” after acceptance is known.

## Validation shape
- Install exactly as requested, then build before lint if the repo uses TypeScript project references.
- Run the package-level tests named by the user plus any acceptance/demo command that exercises the combined product path.
- If a command fails from conflict residue, fix the residue and rerun the exact failed command before moving on.
- If a combined monorepo test run fails from resource pressure rather than an assertion (for example a process killed with exit 137), rerun the affected package directly to separate real failures from scheduler pressure. If the package passes alone, rerun the integration suite with the build tool's concurrency control (for Turbo, `pnpm exec turbo run test --concurrency=1`), not by appending unknown flags through `pnpm run test -- ...` where they may be forwarded to Vitest.
- Test-only stabilization can belong on the integration branch when the combined workload exposes too-narrow test timeouts or polling windows. Keep those changes minimal and explicit: increase the specific test timeout or helper wait bound; do not change production/runtime behavior just to satisfy integration load.
- For UI-impacting integration, build the browser/desktop artifact before smoke testing so the runtime consumes the integrated workspace package dist.

## Pitfalls
- `git merge --continue` may open an editor and hang under tool execution. Use `GIT_EDITOR=true git merge --continue` when the default merge message is acceptable.
- Adjacent source-validation tests from two UI PRs often conflict textually while being semantically additive. Preserve both sides, delete conflict markers, and run the parser/tests before assuming the manual splice is balanced.
- Do not use remote `mergeable`/`mergeable_state` as sufficient evidence for a multi-PR integration; it does not catch cross-PR API drift until the branches are actually combined.
- Do not let a long-running agent loop indefinitely on the same conflict hunk. If logs repeat and no files change, kill the agent, inspect `git status` and conflict markers, then resolve deterministically in the integration worktree.
- Avoid duplicate renderer API keys when preserving legacy and new preload wrappers. Keep legacy top-level names for current UI and put newer grouped APIs under a distinct object such as `workflow`.
- After a squash merge of the integration PR, the original PR head SHAs will not be ancestors of `main`. Do not use `merge-base --is-ancestor origin/pr/<n> origin/main` as the absorption check after squash; it will report false even when the content was integrated. Use the integration PR body/merge commit and the earlier pre-merge inclusion check as evidence, then comment and close the absorbed standalone PRs as superseded rather than merging them again.
