# SkyTurn Agent PTY Session Delivery

Use this reference when planning or delivering SkyTurn work that adds an embedded terminal / PTY transport for agents.

## Product framing

- The goal is a SkyTurn-owned PTY session runtime, not embedding Warp as the product foundation.
- Terminal UI is an inspect/takeover surface: default hidden, session-scoped, and compact.
- SkyTurn remains canvas-first. Do not add a global terminal dashboard, file tabs, or an IDE-like terminal workspace.
- Node cards must stay compact. Do not stream logs/prompts/config/code inside nodes.
- Node modal content tabs remain exactly `Output`, `Changes`, and `Context`.

## Architecture rule

Treat PTY as a transport, not the source of truth.

Correct flow:

```text
PTY / CLI output
  -> agent-bridge lifecycle + parser
  -> RunEvent / RunEvidence / WorkflowIntent
  -> workflow-kernel projection
  -> Canvas UI
```

Forbidden shortcut:

```text
terminal text says "done"
  -> node completed
```

Completion evidence must still come from process lifecycle, structured events where available, git status/diff, tests, artifacts, workflow events, and delivery gates.

## Hermes vs Codex transport split

- Hermes planner is the primary candidate for a long-lived PTY/native session: one SkyTurn `CanvasSession` can bind to one Hermes native session/PTY, with follow-up user input sent to the same session when available.
- Codex executor lanes should keep `codex exec --json` as the default automation path because it is structured and good for evidence. Add PTY for inspect/takeover/debug/interactive fallback, not as the first replacement.
- Preserve resume/continue handles only when the CLI exposes stable identity. If only process-level continuity is known, say so and record degraded/recovery metadata rather than claiming semantic continuity.

## PR slicing pattern

Prefer 6-7 reviewable slices, usually stacked where contract changes are shared:

1. **Contracts and flags**: `project-core` / `agent-runtime` transport kinds, lifecycle states, terminal session ids, adapter capabilities, disabled-by-default feature gate.
2. **Bridge runtime**: `agent-bridge` PTY session manager with injectable PTY factory, lifecycle events, scrollback/ring buffer, stdin, resize, cancel, timeout, redaction, tests. Do not alter existing exec defaults.
3. **Electron IPC seam**: desktop main/preload terminal IPC contracts, disabled unsupported/degraded behavior, input validation, safe renderer API. Renderer still cannot run shell/git/fs/SQLite.
4. **Hermes planner PTY transport**: command builder, resume/continue handling, same-session user input, lifecycle/output events, honest degraded behavior, no second planner root.
5. **Hidden Terminal Inspector UI**: session-scoped default-hidden drawer/popover, read-only first, shows lifecycle and buffer, no node-card logs and no node-modal tab changes. Do not use `CanvasSession.id` as `terminalSessionId`; require an explicit terminal-session binding (or show an honest unbound state without calling snapshot).
6. **Session integration**: bind `CanvasSession` to Hermes terminal session under feature gate; append input to same PTY when active; fallback/degraded path explicit; existing headless path unchanged.
7. **Acceptance/docs**: native dependency/Electron ABI notes if any, disabled/enabled acceptance, redaction, no completion from terminal text, README/docs clearly mark PTY as experimental interactive transport.

## Validation focus

- Existing headless `demo:mvp` / exec-json paths must still pass or be explicitly reported blocked by local credentials.
- Feature disabled path must be unchanged.
- Feature enabled path must show terminal lifecycle and buffer evidence, but not mark nodes complete from terminal prose.
- Bridge PTY manager review must stress asynchronous ordering and teardown, not just happy-path fake PTY behavior: queue terminal events per session, drain already-enqueued output before final lifecycle, suppress late output after finalization, make kill/termination best-effort, and clear SIGKILL escalation if the PTY exits after SIGTERM.
- PTY manager tests should cover async event sink ordering, non-zero exit -> failed evidence, scrollback byte cap / ring eviction, kill throwing, timeout kill escalation, and duplicate close/output suppression.
- Treat terminal observer/IPC callbacks as non-authoritative: metadata/progress observer rejection must not make a PTY `startSession` fail after the process has already spawned. Wrap observer emissions best-effort or route them through the same guarded event queue.
- For cancel/terminate/timeout intent, make the intended final lifecycle/evidence sticky before process teardown when the PTY abstraction can synchronously emit `onExit` from `kill("SIGTERM")`; otherwise user cancel/timeout can be overwritten by a process-exit failure.
- Guard `startSession` async gaps: if an async `starting` event sink allows the PTY to exit before `running` is set, do not overwrite the final status with `running` or start a timeout on a finalized session.
- If `node-pty` or another native dependency is introduced, rebuild Electron native dependencies and verify Node/Electron ABI-sensitive tests separately.
- Run relevant package tests for `project-core`, `agent-runtime`, `agent-bridge`, `desktop`, and `ui-canvas`, plus root build before claiming integration complete.
- For `ui-canvas` terminal-inspector slices, require a browser-safe build check: local source imports need `.js` suffixes, test files must not be emitted into `dist`, original test suites must be preserved when adding source-level tests, and React effects that subscribe to terminal resources must depend on the actual `terminalSessionId`, not just the canvas session id.

## Pitfalls

- Do not embed Warp as the first implementation seam. Warp is a full product; SkyTurn needs a thin backend PTY seam and renderer display surface.
- Do not parse terminal prose as durable status. Parsers may emit progress/output, but evidence must be reconciled independently.
- Do not trust synchronous fake PTY tests as proof of lifecycle correctness. A real event sink may persist or broadcast asynchronously, so final lifecycle can overtake output unless the manager serializes and drains events deliberately.
- Do not let PTY kill paths throw through cancel/timeout or timer callbacks. Native PTYs can already be gone; kill and escalation must be best-effort and audited through lifecycle/evidence instead.
- Do not let renderer import backend PTY libraries or gain shell execution capability.
- Do not silently swap Codex automation from `exec --json` to PTY; that weakens structured evidence.
- Do not claim native Hermes session continuity unless resume/session identity is actually available and stored.
