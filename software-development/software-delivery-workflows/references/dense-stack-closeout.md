# Dense stack closeout after context loss

Use this when resuming a multi-worktree/stacked-PR software delivery run after compaction, tool budget exhaustion, or child-agent execution.

## Live-state recovery
1. Re-check the main worktree: branch, HEAD, remote, clean/dirty status, and recent commits.
2. Enumerate relevant worktrees and branches. For each lane, record dirty files, HEAD commit, upstream remote branch, and whether it has an open PR.
3. Query PR state from the actual repository owner/remote, not a remembered owner. If an MCP call returns `Not Found`, inspect `git remote -v` and retry with the real owner/repo.
4. For CI, match workflow runs by PR head SHA. Old failing runs on previous SHAs are not evidence after a push; old green runs are not evidence for a newer head either.
5. Treat child/Codex summaries as leads only. Parent must inspect diffs and run at least the fastest targeted validation that exercises the intended assertion.

## Dense feedback loop
- Prefer exact narrow tests first, then the lane quick gate. This shortens feedback without claiming narrow tests replace required CI.
- If a UI/Pixi test drives ticker/motion, wait for the rendered object or inspector state that proves the component effect has populated sprites/containers before ticking. `ready` text or a shell caption alone may precede the render effect that creates motion state.
- When API/PR status scripts need nested quotes or f-strings, write a temporary script file and run it. Shell heredoc quoting mistakes can produce misleading Python `NameError`/parse failures and waste the feedback loop.

## Post-merge validation discipline
- After stacked PRs merge, fast-forward the local default branch before claiming closeout; verify open PR count again from the actual remote owner/repo.
- After merging one of several sibling PRs that target the same default branch, treat the remaining siblings' old CI as stale even if `gh pr checks` still shows green. Run `gh pr update-branch <pr>`, fetch the branch, record the new `headRefOid`, wait for a fresh pull_request check on that exact head, then merge with `--match-head-commit`. `mergeStateStatus: UNKNOWN` after a base merge is a prompt to refresh/recheck, not permission to merge.
- If `pnpm install` in a non-interactive closeout shell fails with `ERR_PNPM_ABORTED_REMOVE_MODULES_DIR_NO_TTY`, rerun with `CI=true pnpm install ...`; this is pnpm refusing an unattended node_modules replacement, not code failure. Prefer `--offline --frozen-lockfile --store-dir <warmed-store>` when the store is already populated, then run the real build/lint/test/typecheck gate.
- If `pnpm run test` or React/Vitest suites fail broadly with `TypeError: React.act is not a function`, first check for `NODE_ENV=production` shell pollution. Rerun validation with `env -u NODE_ENV ...` before treating it as a code regression.
- Long browser smoke suites can exceed foreground or tool-call limits even when healthy. Run them as tracked background processes with `notify_on_complete=true`, poll/wait until natural exit, and report the real final count/exit code. A tool timeout/SIGTERM from the harness is not a test failure; a process exit code is.

## Handoff shape when stopping
Separate these buckets explicitly:
- verified PRs and their exact head SHA/CI state;
- pushed branches with fresh CI pending;
- parent-validated but unpushed or uncommitted dirty lanes;
- dirty/not-reviewed lanes;
- external status sinks already updated;
- exact next commands to continue.

Do not create temporary markdown progress logs for this state unless it changes durable product/API/storage/runtime/UI semantics; use Slack/Linear/controller state instead.