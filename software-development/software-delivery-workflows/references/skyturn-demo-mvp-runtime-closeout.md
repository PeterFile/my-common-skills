# SkyTurn demo:mvp runtime closeout

Use this when validating SkyTurn's real Hermes→Codex MVP loop with `pnpm --filter @skyturn/desktop run demo:mvp`.

## Pattern
1. Sync and validate the repo first when the user wants closeout: `git pull --ff-only` only after checking the worktree is clean, then run the normal gates in project order.
2. Before real desktop workflow testing, run `pnpm --filter @skyturn/desktop run rebuild:native` so `better-sqlite3` matches the Electron ABI.
3. Treat `demo:mvp` as long-running real acceptance. Do not rely on a foreground `terminal()` with a 600s cap for final evidence. Start it as a managed background process with completion notification, then poll/wait until the process exits.
4. If a foreground run times out or is killed, do not call the product failed just from the shell timeout. Inspect the temp repo and run events first. Current script creates `/var/folders/.../skyturn-react-demo-*`; run evidence lives under `.devflow/runs/*/events.ndjson`.
5. While waiting, inspect latest `events.ndjson` tail per run to distinguish real stuck state from normal slow Hermes/Codex lanes. Useful milestones: planner succeeded, implementation succeeded, command validation succeeded, browser screenshot succeeded, evidence review succeeded, verified commit succeeded.
6. Only accept the demo from the final JSON/process exit: `ok: true`, exit code 0, connected graph, all cards completed, `testExitCode: 0`, screenshot bytes > threshold, commit count > 1, changed files match the expected app files, and temp repo git status is clean.
7. After Electron ABI testing, restore Node ABI for Node-side tests with `pnpm --filter @skyturn/persistence rebuild better-sqlite3`. Verify from the package context, e.g. `pnpm --filter @skyturn/persistence exec node -e 'require("better-sqlite3"); console.log(process.versions.modules)'`, then run a targeted persistence test.

## Pitfalls
- A 600s foreground timeout can kill a nearly successful commit lane. The lesson is to use a managed background process and inspect `.devflow` evidence, not to rerun blindly or report failure.
- `better-sqlite3` may be rebuilt for Electron ABI during demo validation. Restore Node ABI afterward before trusting Node/Vitest persistence checks.
- `require("better-sqlite3")` from the monorepo root can fail due to package resolution; verify it through `@skyturn/persistence` package context instead.
