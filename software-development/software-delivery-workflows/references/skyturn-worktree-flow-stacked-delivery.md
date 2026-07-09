# SkyTurn worktree-flow stacked delivery notes

Use these notes when delivering SkyTurn workflow/worktree changes across multiple small PRs with coding agents.

## Review scope must match artifact state

- If a worker branch is dirty/uncommitted, review-only agents must inspect `git diff`, `git diff --stat`, and the changed files directly.
- Do not ask a reviewer to inspect `<base>..HEAD` until the candidate changes are committed; the reviewer will correctly see an empty PR diff and block.
- After committing or amending, rerun the review prompt against the intended stack base (`parent-branch..HEAD`), not blindly against `origin/main`.

## Stack when narrow contract files overlap

- If two otherwise independent slices both need the same narrow public type/contract file, stack the later slice on the earlier one before opening PRs.
- Example pattern: A changes a `WorkflowApi` create-worktree return contract; C changes the same interface for user-decision write-through. Keep C based on A so each PR diff is honest and avoids racing the same hot file.

## Worktree run-path binding needs end-to-end path checks

When fixing SkyTurn `new_worktree` run binding, verify all three layers:

1. Renderer/runtime calls the narrow Electron IPC to create/recover the managed worktree and passes the returned absolute path to `startAgentRun`.
2. Electron persists the session target (`new_worktree`, selected branch/base ref) in `workflow:createSession`; otherwise materialization/reload can silently turn the session back into `current_branch`.
3. Agent adapters actually honor `StartAgentRunInput.worktreePath`. In this session, Codex already did, but Hermes adapter originally used `projectRoot` as cwd and needed adapter-level coverage.

## Adopt/clean safety checks

For real managed worktree adopt/clean wiring:

- A cherry-pick/merge preview must not leave the target checkout dirty. Prefer a temporary worktree. If previewing in the target checkout, record pre-preview HEAD, require an explicitly clean worktree including untracked files (`git status --porcelain=v1 --untracked-files=all --`), and restore with only `merge/cherry-pick --abort` plus `reset --hard <head>`. Do **not** run broad `git clean -fd` in preview cleanup; it can delete unrelated untracked user files.
- Before applying adoption, verify target branch HEAD still equals the declared base commit. Drift or wrong target branch must record `workflow.variant.adopt_failed` and fail before checkout/merge side effects proceed.
- Treat persisted SQLite worktree identities as untrusted at IPC boundaries. Before adopt/clean service calls, validate the selected created worktree identity belongs to the current opened project: real `repoRoot` equals the current project root and real worktree path is inside that project’s managed `.worktrees` root. On boundary failure, write the terminal failure event, broadcast the projection, and reject. The lookup for a created identity must itself be inside the audited failure path; missing/non-created `worktreeId` is also a terminal failure, not a bare thrown exception.
- Cleanup early failures should still be auditable. Running-task guard failures, stale/missing created events, identity/reconcile mismatches, repo/path boundary failures, unsafe branch names, and delete-branch preflight failures should record `workflow.worktree.clean_failed`; not only post-`git worktree remove` failures. Keep boundary checks before any git side effects, but after enough store/event-sink setup exists to write the failure event.
- For `deleteBranch: true`, validate branch safety before `git worktree remove`. If branch deletion could fail after worktree removal, either preflight it first or record a truthful cleaned event before separate branch-delete failure evidence. Do not leave projection believing a removed worktree still exists.
- Renderer worktree lifecycle UI must not invent dangerous side-effect facts. Adopt should be disabled or error when trusted metadata such as `worktreeId`, `variantId`, `baseCommit`, `headCommit`, or target branch is missing; do not fall back to string values like `HEAD` or `main`. Use stable adoption IDs derived from existing worktree/head identity rather than `Date.now()`.
- Clean UI must send the full `WorkflowWorktreeIdentity` expected by the desktop API, not raw `CanvasNode.worktree` if it lacks fields. In current projections that means adding `parentLaneId: node.id` and disabling Clean unless `worktreeId`, `variantId`, `realPath`, `gitdir`, `repoRoot`, `branchName`, `baseCommit`, and `headCommit` are present. If the user cancels the delete-branch confirmation after confirming clean, still call clean with `deleteBranch: false` rather than aborting the safe cleanup path.
- Public workflow contracts must match terminal behavior. If IPC now returns `adopted`/`failed` or `cleaned`, update `WorkflowApi` and `FlowEventKind`/projection contracts in the same slice; do not leave browser-facing types saying `status: "requested"`.

## Scheduler parallelism slices

For SkyTurn worktree-aware scheduling, keep the policy centralized in `packages/ui-canvas/src/workflowRuntime.ts` and treat `allowedParallelism` only as a safe upper bound; Flow Kernel dependency/scope gates still decide the actual runnable lanes.

- Current-branch write lanes must stay conservative/serial; if a shared write is already running, new shared writes should not be scheduled.
- Trusted read-only validation/review lanes may raise the bound, but only when runtime policy is trusted and executable/read-only.
- New-worktree write lanes may run concurrently only with a real managed worktree identity: `worktreeId`, absolute `realPath`, `gitdir`, and distinct real paths. Placeholder `new_worktree` metadata, missing `realPath/gitdir`, duplicate worktree identity, or unknown runtime policy must fall back safe.
- Tests should include positive and negative cases: current-branch writes remain serial, read-only lanes can parallelize, distinct managed worktrees can parallelize, placeholders/missing identity/duplicate identity do not.

## Validation pattern

- Parent must rerun the relevant package tests after child-agent claims, especially after review-blocker fixes.
- For fresh worktrees with missing dependencies, install with an explicit external store such as `CI=true pnpm install --frozen-lockfile --store-dir /tmp/<lane-store>` rather than polluting the worktree with a `.pnpm-store/` that agents/reviewers may try to diff.
- SkyTurn UI package tests in a fresh worktree can fail before exercising the slice when browser-consumed workspace package `dist` entries are missing. Build the exact upstream workspace packages reported by resolver errors (commonly `@skyturn/project-core`, `@skyturn/workflow-kernel`, `@skyturn/orchestrator`, `@skyturn/planner`, `@skyturn/persistence`) and then rerun the same UI test/typecheck command; do not treat resolver setup failures as product failures.
- Passing UI tests is not enough for delivery UI slices: run `pnpm --filter @skyturn/ui-canvas run typecheck` after tests. Typecheck can catch projection/type boundary mismatches that source-text tests miss, such as persistence-only lane kinds (`pull_request`) not being in the browser-facing `CanvasNode.laneKind` union.
- For Antigravity UI agents that time out after writing a partial diff, stop the process, inspect `git diff` directly, and send a narrow repair prompt for concrete blockers (for example inline styles, `@ts-ignore`, unsafe fallback values, or backend-contract mismatches). Treat the partial diff as untrusted until parent validation and review-only pass.
- For safety-sensitive IPC PRs, do not stop after the first review approval if subsequent fixes changed early-failure or boundary behavior; rerun review-only on the exact artifact state until the latest diff is APPROVE.

## Stacked PR integration closeout

When SkyTurn slice PRs are stacked and child PRs have no fresh `pull_request` checks for their current base, prefer a dedicated integration worktree over blind one-by-one squash merges.

1. Start from `origin/main` in `feature/worktree-flow-integration`.
2. Merge accepted slice heads in dependency order.
3. Run the full integration gate: root `pnpm run build`, `lint`, `typecheck`, `test`, affected package tests/typechecks, `pnpm --filter @skyturn/desktop run rebuild:native`, `git diff --check`, and `demo:mvp` when credentials are available.
4. Open one integration PR against `main`; wait for a fresh exact-head `Build and test` success before merging.
5. After the integration PR is merged, close superseded slice PRs with a comment and do not delete remote branches unless explicitly doing branch cleanup.

## `demo:mvp` acceptance discipline

- A foreground tool timeout is not a product failure and not success evidence. If `demo:mvp` may exceed the foreground limit, rerun it as a tracked background process and tee stdout to a file, then parse the final JSON.
- Treat `demo:mvp` as green only when the JSON has `ok: true`, all run evidence statuses succeeded, graph connectivity/root-dependency checks pass, git reconciliation/commit evidence is present, and screenshot bytes are non-trivial.
- If an intermediate lane reports missing app dependencies, inspect later run events before calling the demo failed: a commit/repair lane may install dependencies, generate screenshot evidence, and complete successfully. The durable lesson is to follow structured run events and final JSON, not a single lane's prose.

## Desktop Electron build refresh PRs

For tiny SkyTurn desktop build fixes that touch `apps/desktop/package.json` and `apps/desktop/scripts/dev.test.mjs`:

- If Electron main output can be stale or missing, prefer `tsc -b tsconfig.electron.json --force` over `tsc -p tsconfig.electron.json` when the Electron tsconfig is composite and uses a `.tsbuildinfo` file. This forces rebuild of `dist-electron/electron/main.js` instead of trusting stale incremental state.
- Add a narrow script-string regression test in `apps/desktop/scripts/dev.test.mjs` to keep `build:electron` from drifting back to the stale incremental command.
- When an old small PR is behind a much newer `main`, refresh it in an isolated worktree by merging `origin/main`, then verify that the PR diff against `origin/main` is still only the intended files before pushing. Do not infer the large merge output is part of the PR diff; check `git diff --stat origin/main...HEAD`.
- Fresh worktrees need dependencies before desktop tests. Install with an external store such as `CI=true pnpm install --frozen-lockfile --store-dir /tmp/<lane-store>`; a missing `vite` or `typescript` in a new worktree is setup state, not a product failure.
- Relevant validation for this class: `pnpm --filter @skyturn/desktop run test`, `typecheck`, `build:electron`, confirm `apps/desktop/dist-electron/electron/main.js` exists, and `git diff --check origin/main...HEAD --` before waiting for fresh exact-head CI.

## Delivery commit backend safety

For backend-first commit/push delivery actions:

- Validate the workflow/session context before any Git side effect. A stale or unknown `sessionId` must fail before `HEAD` changes, otherwise IPC can return failure after creating a commit with no workflow evidence event.
- Validate the commit lane before any Git side effect. Resolve `laneId` from the workflow projection, require `laneKind === "commit"`, and keep Flow Kernel projection logic from treating `workflow.commit.created` as completion for unknown or non-commit lanes.
- Do not trust renderer-supplied `worktreePath` for delivery. Derive or validate it server-side against the `CanvasSession` node/lane stored worktree (`realPath` when present, otherwise the project root/current branch path); reject mismatches before importing/calling the Git service.
- Stage and commit only the caller's verified file list. Do not rely on a preflight followed by bare `git commit`; hooks or concurrent commands can add staged files between checks. Use a path-limited commit such as `git commit --only -- <files>` and then verify the actual committed file set with `git diff-tree --name-only` before returning evidence.
- Treat Git pathspec magic as hostile input. Reject file paths beginning with `:` (including `:!foo`, `:^foo`, `:/`, and `:(...)`) or prove literal-pathspec handling; add regressions showing the index remains unchanged on rejection.
- Reject empty file lists, duplicate/ambiguous paths, unchanged/missing files, paths outside the selected worktree, and symlink traversal through an in-worktree path to outside storage. Add temp-git-repo regressions for these cases.
- For remote delivery PR creation, proving that a remote branch exists is not enough. Before `gh pr create`, parse `git ls-remote --exit-code --heads <remote> <headBranch>` and reject unless the remote SHA exactly equals the verified delivery `commitSha`; add a stale-remote-head regression that proves `gh pr create` is not called for the wrong commit.
- If adding new workflow delivery events such as pushed/PR-created, do not invent a new lane completion semantic unless the canonical lane kind exists in `project-core` and tests cover it. It is valid for those events to be recorded without completing a lane.
- If the UI allows committing a `mismatch` reconciliation, make the exception explicit end-to-end: require user confirmation in UI, send an explicit flag such as `acceptMismatch: true`, and allow `reconciliationStatus === "mismatch"` in the backend only when that flag is present. Otherwise keep mismatch commits disabled; do not prompt the user for an action the backend will reject.
- Keep UI wiring separate from backend delivery logic. First land Node/Electron/preload contracts and backend tests; then let a UI-focused agent wire the narrow renderer caller without introducing renderer-side Git, filesystem, SQLite, or process execution.


## Delivery remote UI safety

When wiring delivery Push/Create PR controls into the Changes tab:

- Keep the UI renderer-side only: no git, shell, filesystem, SQLite, or backend contract changes in the UI slice. Call the narrow desktop workflow API and let Electron/main/backend validate session, lane, worktree, and commit evidence.
- Do not require renderer-visible commit evidence after reload. `workflow:events` may expose redacted `workflow.commit.created` events: match by top-level `event.laneId` first, optionally fallback to `payload.laneId`, and treat a matching redacted event as a persisted commit marker. Do not fabricate `commitSha`, `branch`, or `worktreePath`; send only `sessionId` + commit `laneId` plus optional fields that are actually visible, and let the backend resolve stored evidence.
- Reset delivery UI state on node/session/project identity changes. Clear `commitEvidence`, `pushStatus`, `prStatus`, `prUrl`, and `deliveryStatus` when `node.id`, `session.id`, or `projectRoot` changes; also clear commit evidence when `getEvents` is unavailable or no matching commit event exists. Otherwise modal reuse can leak Push/PR gating across lanes.
- PR base must come only from explicit base metadata such as `node.worktree.baseRef` or `session.target.baseRef`. Do not use `selectedBranch`, `baselineRef`, or hardcoded `main`; current-branch persistence may set `baselineRef` from the development branch. Re-check the user-confirmed base after prompt: trim it, require non-empty, and require `base !== deliveryBranch` before calling the API.
- Create PR must use a real dependent `pull_request` lane as `laneId` and the current commit lane as `commitLaneId`; never send the commit lane as both. Keep Create PR disabled until push succeeded, the dependent PR lane exists, explicit base is known, and delivery branch is known.
- Tests should cover the source-level trust boundaries above: persisted redacted event marker, top-level `laneId`, no selectedBranch/baselineRef/main base fallback, prompt base revalidation, dependent PR lane use, and state reset on identity change.

## Worktree lifecycle UI safety

When wiring compare/adopt/clean into the node modal:

- Put lifecycle controls in the existing `Context` or `Changes` modal content, never in compact node cards, and keep exactly the three modal tabs (`Output`, `Changes`, `Context`).
- Renderer UI may display worktree identity and request a narrow IPC action, but must not fabricate adoption identity or dangerous git facts. Do not default missing `targetBranchName` to `main`, missing `headCommit` to `HEAD`, or synthesize adoption IDs/strategies from `Date.now()` unless the backend contract explicitly asks for a client nonce. Disable the action or show an error when trusted projection/worktree metadata is incomplete.
- Current-branch nodes must not show adopt-as-candidate controls. Only show lifecycle actions for real managed worktree identities with `worktreeId`, path/realPath, branch/base/head facts where required.
- Tests and typecheck passing are not enough for these UI slices: parent review must inspect the diff for trust-boundary violations and misleading confirmations before starting review-only or committing.

## Stacked UI integration conflict pattern

When merging SkyTurn UI slices that both append `App.test.ts` source-validation blocks, conflict resolution should usually preserve both test groups. Remove conflict markers, add the missing `});` between adjacent `it(...)` blocks, and verify the final `describe(...)` closure before running tests. Do not delete one slice's tests just because both branches edited the same validation section.

## Delivery remote UI wiring safety

When wiring Push / Create PR into SkyTurn's Changes tab on top of backend delivery actions:

- Treat renderer-visible workflow events as sanitized/redacted. `workflow.getEvents()` returns an object with `events`, and workflow event identity is `kind`, not `type`. Do not require `payload.evidence` from a persisted `workflow.commit.created` event; use a matching commit event as a persisted commit marker and let Electron/backend resolve trusted commit evidence from the store.
- Keep renderer-supplied push payload minimal. If commit evidence came from the current component's `createDeliveryCommit` response, optional `commitSha`/`branch`/`worktreePath` may be sent. If evidence is only a persisted marker, send trusted identifiers (`sessionId`, commit `laneId`) and let the backend find the commit evidence; never fabricate redacted fields in the UI.
- PR creation must target a real dependent `pull_request` lane. Do not call the PR IPC with the commit lane as both `laneId` and `commitLaneId`; find a downstream lane whose runtime/projection kind is `pull_request`, pass that as `laneId`, and pass the current commit lane as `commitLaneId`.
- PR base must come only from explicit base metadata such as `node.worktree.baseRef` or `session.target.baseRef`. Do not use `selectedBranch`, `baselineRef`, or a hardcoded `main` fallback: current-branch projections may set those to the development/head branch, which can make base=head.
- Revalidate the final user-edited base branch prompt after trimming. It must be non-empty and different from the delivery/head branch immediately before `createPullRequest`; checking only the derived default is insufficient.
- Empty/clean changeset views must not hide remote delivery actions when persisted commit evidence exists. Keep the empty evidence message if needed, but still render the same Push/PR toolbar for a commit lane with known local or persisted commit evidence. Do not enable local Commit without git evidence.
- Source-level tests are useful for this UI class, but review-only should still inspect the actual diff for trust-boundary regressions: no inline styles, no `@ts-ignore`, no renderer git/fs/shell/SQLite, no merge button, and no UI claim that push/PR success means CI passed.
