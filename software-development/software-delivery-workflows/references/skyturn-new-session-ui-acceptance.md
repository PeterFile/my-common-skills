# SkyTurn New Session UI acceptance

Use this when the user asks whether SkyTurn can complete a real project-building request from the desktop New Session input, without mock-only shortcuts.

## What this validates
This is distinct from `pnpm --filter @skyturn/desktop run demo:mvp`.

- `demo:mvp` seeds a temporary React project and drives the runtime path from a script.
- New Session UI acceptance must exercise the real desktop renderer input: Project Start Page → `textarea[aria-label="New task goal"]` → `button[aria-label="Create"]`.
- Browser-only Vite is insufficient because it lacks `window.devflow` and will use browser/mock fallback. Use Electron with preload IPC.

## Practical pattern
1. Create an isolated temporary real git project, normally a minimal React/Vite app with:
   - `src/App.jsx` and `src/App.css`.
   - `scripts/verify.mjs` that checks the requested visible strings.
   - optional `scripts/capture-screenshot.mjs` that writes `.devflow/acceptance/react-app.png`.
   - an initial git commit.
2. Create an isolated Electron user data directory and pre-seed `workspace.json` with the temporary project as the active project and `activeSessionId: null`.
   - This avoids the native Open Project dialog while still using the real New Session input.
   - `workspace:load` calls `rememberProjectRoots`, so the project becomes a known root for subsequent IPC.
3. Build the live artifacts before launching Electron:
   - `corepack pnpm --filter @skyturn/ui-canvas run build` when the desktop imports workspace `dist`.
   - `corepack pnpm --filter @skyturn/desktop run build:electron`.
   - `corepack pnpm --filter @skyturn/desktop run rebuild:native` before Electron if native SQLite is involved.
4. Launch real Electron with a dev server and remote debugging:
   - Start Vite for `apps/desktop` on a free localhost port.
   - Launch Electron with `VITE_DEV_SERVER_URL`, `--user-data-dir=<tmp-user-data>`, and `--remote-debugging-port=<port>`.
5. Drive the renderer through CDP or another real UI automation mechanism:
   - Wait for `window.devflow` and the New Session textarea.
   - Set the textarea value through the native setter and dispatch an `InputEvent`.
   - Click the `Create` button.
6. Treat success as evidence-backed only after all of these are true:
   - A canvas session exists from `window.devflow.loadWorkspace()`.
   - `window.devflow.workflow.getProjection(projectRoot, sessionId)` shows Hermes planner output and flow-kernel lanes.
   - Real `codex exec --json`/Hermes runs produced `.devflow/runs/*/events.ndjson` and terminal `RunEvidence`.
   - The target app source contains requested visible strings.
   - `node scripts/verify.mjs` exits 0.
   - The verification script itself is still the seeded validation contract. Capture a checksum immediately after seeding the temp project and fail final acceptance if `scripts/verify.mjs` changes; a coding lane can otherwise make the test easier and create a false green.
   - Screenshot artifact exists and is non-trivial size when requested.
   - Commit lane produced a commit when requested; do not count dirty files as completion.
   - Git status is clean and changed files come from the committed delivery diff, not from uncommitted lane output.
   - The committed file set is allowlisted for the requested product change. For the standard temp React acceptance, the commit should contain only `src/App.jsx` and `src/App.css`; fail closed on helper/script changes such as `scripts/verify.mjs`, `scripts/capture-screenshot.mjs`, or `src/main.jsx` unless the acceptance task explicitly allows them.
7. Run the full acceptance as a managed background process when it can exceed the foreground timeout. Poll both the process and the isolated `workspace.json` / temp project state; a foreground timeout can kill the parent while child Electron/Codex work continues or leaves orphaned processes.

## Failure and partial-success reporting
Report the boundary precisely:

- If the New Session input submitted, Hermes planner generated lanes, and Codex modified files, but screenshot/review/commit lanes were not observed to terminal state, say the UI-driven real build path works through implementation/verification but full closed-loop acceptance is not proven.
- Do not call a run complete merely because Codex says it is done. Use projection state, run evidence, git status/commit count, verify command, and artifact size.
- If automation had to pre-seed `workspace.json`, disclose that it bypassed only the native directory picker, not the New Session input or agent runtime path.
- If renderer automation fails before workflow completion, emit a structured final JSON blocker such as `failure.code = RENDERER_AUTOMATION_FAILED`; do not leave only a CDP stack trace on stderr. Keep `projectRoot`, `userData`, and `workspacePath` in the JSON so the parent can inspect partial evidence.
- On current SkyTurn builds, the planner-root card can remain visually `running` after planner `RunEvidence` has succeeded while all Flow Kernel lanes complete. Report that as a UI/projection status gap, not as product-artifact failure, and verify the planner evidence separately.

## Pitfalls
- Running only the Vite page validates browser fallback, not desktop SkyTurn.
- Launch Electron/Codex child processes with `OPENAI_BASE_URL` unset when local Codex requires native auth routing.
- After `rebuild:native` for Electron, restore the Node ABI with `corepack pnpm --filter @skyturn/persistence rebuild better-sqlite3` and run the persistence tests before trusting Node/Vitest again.
- `Open Project` is a native dialog; for automated acceptance, pre-seed isolated userData instead of changing product code or using mock adapters.
- CDP websocket handshakes from Electron may use status text `101 WebSocket Protocol Handshake`, not exactly `101 Switching Protocols`; match `HTTP/1.1 101`.
- If a script bug stops automation before agent completion, classify it as harness failure, not SkyTurn product failure.
- If a managed acceptance process is killed or times out, inspect and terminate orphaned Electron/Vite/agent process groups tied to the isolated `userData` or temp project before rerunning; otherwise stale CDP targets, ports, or child runs can contaminate the next result.
- A visible Codex process such as `codex exec --json --sandbox workspace-write -C <temp-project>` is useful evidence that execution is real, but final acceptance still requires terminal lane evidence and artifact/git checks.
- Do not let a child agent modify the acceptance oracle. In temp projects, protect or checksum seeded validation scripts (`scripts/verify.mjs`) and fail closed if they change, even if the modified script still passes.
- Do not let validation/screenshot lanes repair the harness inside the temp project unless that is explicitly the task. A screenshot lane that edits `scripts/capture-screenshot.mjs` or `src/main.jsx` may produce a green artifact while changing the acceptance object; keep those files fixed and report the blocker instead.
