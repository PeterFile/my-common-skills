# SkyTurn Electron native workflow blocker pattern

Use when SkyTurn real desktop workflow testing fails around `better-sqlite3`, Electron IPC, planner-root startup, a blank desktop dev renderer, or agent terminal run evidence not reaching the SQLite workflow fact source.

## Native ABI discipline
- `better-sqlite3` is a native module with different ABI builds for Node and Electron.
- Before real Electron desktop workflow testing, run:
  ```sh
  pnpm --filter @skyturn/desktop run rebuild:native
  ```
- Verify the Electron ABI import from the same cwd required by the acceptance command. If the command runs from the repo root, package resolution must work from the repo root too:
  ```sh
  ELECTRON_RUN_AS_NODE=1 apps/desktop/node_modules/.bin/electron -e "import('@skyturn/persistence/workflow-store').then(()=>console.log('ok'))"
  ```
- If that exact repo-root command cannot resolve `@skyturn/persistence`, the app may still work from `apps/desktop` but the acceptance command is not satisfied. The minimal fix can be a root `devDependencies` workspace link such as `"@skyturn/persistence": "workspace:*"`, with lockfile update.
- After rebuilding for Electron, Node-side persistence tests may fail with a `NODE_MODULE_VERSION` mismatch. Rebuild back to Node ABI before Node tests:
  ```sh
  pnpm --filter @skyturn/persistence rebuild better-sqlite3
  pnpm --filter @skyturn/persistence run test
  ```
- Treat ABI as local native artifact state, not source breakage, as long as the correct rebuild for the target runtime passes.

## Planner-root run:start guard
- Do not remove or weaken the generic `run:start` projection guard.
- The safe fallback is narrow: when a node is missing from `FlowProjection.projectionNodes` but workflow events exist, allow only the SQLite-materialized Hermes planner root from `materializeCanvasSession(sessionId)`.
- Required checks: input `nodeId` equals `canvasSession.plannerNodeId`, the canvas node exists, `agent === "hermes"`, not `user_decision`, not `executable:false`, not `runtimePolicy.executable:false`, and status is `running` or `retrying`.
- Keep non-planner missing nodes rejected.

## Desktop dev blank renderer / React refresh
- SkyTurn desktop dev imports browser workspace packages from their built `dist` via package exports. Build `packages/ui-canvas` before browser/Electron smoke when the app imports it from `dist`.
- Start the renderer from the correct package cwd (`apps/desktop`) or via the package dev script so Vite loads `apps/desktop/vite.config.ts`. Starting Vite from the repo root can bypass the desktop config and create misleading blank-page failures.
- If the renderer is blank and a dynamic import or console probe shows `ReferenceError: $RefreshSig$ is not defined` in a workspace `dist/*.js` module such as `packages/ui-canvas/dist/DecryptedText.js`, suspect Vite React-refresh transform without a preamble.
- A minimal dev-only fix is to ensure the desktop Vite HTML initializes the React refresh preamble before `/src/main.tsx`. One working pattern is a `serve`-only Vite plugin in `apps/desktop/vite.config.ts` that injects:
  ```js
  import { injectIntoGlobalHook } from "/@react-refresh";
  injectIntoGlobalHook(window);
  window.$RefreshReg$ = () => {};
  window.$RefreshSig$ = () => (type) => type;
  ```
  via `transformIndexHtml` with `injectTo: "head-prepend"`.
- Add a package-level test that calls `createServer({ root: apps/desktop, configFile: apps/desktop/vite.config.ts, server: { middlewareMode: true } })`, runs `server.transformIndexHtml("/", html)`, and asserts `window.$RefreshSig$` appears before `src="/src/main.tsx"`.
- Verify the fix with a real browser/CDP import probe, not just by reading source. A useful probe is importing a transformed workspace module that previously failed, e.g. `packages/ui-canvas/dist/DecryptedText.js`, and confirming it returns `{ ok: true }`.

## Terminal RunEvidence must persist workflow facts
- In the real desktop loop, `startAgentRun` starts the child process; it does not mean the agent has completed. Do not rely on the immediate `startAgentRun -> getRunEvents/getRunEvidence` read to contain final output or evidence.
- A common failure shape is: `.devflow/runs/<run>/events.ndjson` contains final Hermes `WorkflowIntent`, `evidence` exit 0, and `status:succeeded`, while SQLite still only has `hermes_session_started` and `workflow.user_input`. The UI may show the planner node completed, but `workflow.intent.accepted` and lane declarations never appear.
- The correct fix is to persist after terminal run evidence/status arrives through the run-event stream. In the renderer, the event listener may call existing Electron IPC APIs, but SQLite remains owned by Electron main/persistence.
- Use concrete terminal evidence, not agent text: for Hermes, only parse/apply the `WorkflowIntent` after a successful terminal run from the trusted planner root. Do not key this on `agent === "hermes"` alone.
- Non-planner Hermes flow-kernel lanes, such as review/verifier lanes, are ordinary executable workflow lanes for persistence purposes. They must record terminal `RunEvidence` through the same `recordWorkflowRunResult` + `scheduleWorkflowReadyLanes` path as Codex/validation lanes, not attempt to parse or apply planner `WorkflowIntent` JSON.
- In renderer fallback/local projection paths, apply Hermes WorkflowIntent output only for the planner root (`session.plannerNodeId`); a Hermes review lane that prints JSON-shaped text must not be allowed to declare lanes or mutate the graph.
- Add a de-duplication guard keyed by `runId` (or equivalent terminal-event key) so repeated final events do not double-apply the same intent or double-schedule lanes. If a persistence attempt returns no terminal evidence yet, release the claim so a later terminal event can retry.
- Tests should cover the exact timing bug: immediate post-start evidence is still `running` and must not call `applyWorkflowIntent`; after a terminal event/evidence arrives, `applyWorkflowIntent` and `scheduleWorkflowReadyLanes` are called exactly once. Also cover non-planner Hermes review/verifier lanes recording `RunEvidence` without invoking `applyWorkflowIntent`.
- Add a de-duplication guard keyed by `runId` (or equivalent terminal-event key) so repeated final events do not double-apply the same intent or double-schedule lanes. If a persistence attempt returns no terminal evidence yet, release the claim so a later terminal event can retry.
- Tests should cover the exact timing bug: immediate post-start evidence is still `running` and must not call `applyWorkflowIntent`; after a terminal event/evidence arrives, `applyWorkflowIntent` and `scheduleWorkflowReadyLanes` are called exactly once.
- Tests should also cover non-planner Hermes lanes: a terminal Hermes review/verifier lane calls `recordWorkflowRunResult` + `scheduleWorkflowReadyLanes` and does not call `applyWorkflowIntent`; non-planner Hermes output that looks like JSON WorkflowIntent must not leak new lanes into local projection.

## Delivery / PR shape
- If multiple defects are discovered in the same real desktop workflow acceptance chain, it is usually safer to deliver one atomic PR that makes the full real path pass than to split into intermediate PRs that cannot independently satisfy acceptance.
- If the user explicitly expects one PR per blocker/component, ask or split before merge. Otherwise, state why a single PR is atomic: each fix is required for the same real Electron workflow to complete.
- For final closeout, an opened PR is not the end state when the user asks to finish delivery or sync `main`: wait for exact-head CI, squash merge if requested/expected, verify the PR is merged, then fast-forward local `main` from `origin/main`.

## Clean desktop dev startup / stale artifact avoidance
- When the user asks to clear application cache and start SkyTurn dev from latest code, make the runtime state explicit: current git branch/status, build artifacts, Vite/Turbo caches, Electron `userData`, generated `dist`, and active dev processes are separate layers.
- Clear only targeted project/dev artifacts unless the user explicitly asks for broader deletion: `apps/desktop/dist`, `apps/desktop/dist-electron`, `packages/ui-canvas/dist`, project/package `.turbo`, Vite caches such as `node_modules/.vite` and `apps/desktop/node_modules/.vite`, plus a disposable Electron profile under `/tmp` (for example `/tmp/skyturn-userdata-fresh`). Do not delete normal user Electron state when an isolated `--user-data-dir` will prove freshness.
- Rebuild from source after clearing: run root `pnpm run build` so workspace `dist` packages, especially `@skyturn/ui-canvas`, are regenerated before dev smoke. Then run `pnpm --filter @skyturn/desktop run rebuild:native` before Electron testing.
- Start the renderer from `apps/desktop` using `scripts/devServer.mjs` to choose the port instead of hard-coding `5173`, then launch Electron with `VITE_DEV_SERVER_URL=<chosen-url>` and `--user-data-dir=<fresh-profile>`.
- Verify the running artifact, not just process existence: `curl -I <renderer-url>` should return `200`, the served HTML should include the desktop React-refresh preamble before `/src/main.tsx`, browser smoke should mount the SkyTurn shell, and browser console should have no JavaScript errors.

## Real desktop validation notes
- For real UI validation, isolate Electron `userData` with `--user-data-dir` so workspace state does not pollute the user's normal Electron profile.
- When the immediate goal is “clear caches and start latest dev artifacts”, remove stale build/dev artifacts (`apps/desktop/dist`, `apps/desktop/dist-electron`, browser workspace `dist` such as `packages/ui-canvas/dist`, Turbo/Vite caches) before rebuilding, then run the relevant build so the dev server cannot serve stale workspace `dist` output.
- Treat a background `watch_patterns` match such as “renderer ready” as a progress signal, not proof the dev environment is still alive. After the match, poll the managed process and hit the renderer URL; if Electron and Vite were launched in one shell with a `trap`, an Electron exit can kill Vite even after readiness printed.
- For easier diagnosis and recovery, prefer running Vite and Electron as separate managed background processes when manually bringing up SkyTurn desktop dev. Verify Vite with `curl`/browser smoke, then start Electron with `VITE_DEV_SERVER_URL` pointing at that URL and poll Electron separately. This avoids losing the renderer when Electron exits and gives separate logs/process handles.
- A preseeded `workspace.json` can avoid GUI file-picker automation while still exercising Electron IPC, SQLite workflow store, and real agent run startup.
- If GUI automation is unavailable, use Electron `--remote-debugging-port` and Chrome DevTools Protocol to submit the renderer form and inspect DOM/console state.
- If a CDP helper reports no selector but a screenshot shows the input, first dump raw `Runtime.evaluate` responses against the target page; the issue may be the automation script, not the app.
- Do not claim full UI acceptance without concrete evidence: `.devflow` run events, SQLite workflow events, run evidence, and screenshot/output when requested.
- Do not hard-code lane ids in acceptance watchdogs. Hermes may choose semantically equivalent ids across runs (for example `lane-review-static-site` vs `lane-review-requirements`). Poll SQLite for terminal workflow facts by event kind/status and the actual declared lanes, or derive the lane ids from `workflow.lane.declared` before waiting for `workflow.segment.finished`.
