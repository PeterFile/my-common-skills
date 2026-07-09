# SkyTurn node-action UI wiring handoff/recovery

Use for SkyTurn renderer slices that wire selected-node composer actions (repair, variant, rollback) to backend workflow IPC.

## Durable lesson

A child coding agent may time out after writing only tests or partial UI wiring. Treat that as an unfinished red-test state, not a completed implementation.

## Recovery steps

1. Verify the actual worktree, not the child summary:
   - `git status --short --branch`
   - `git diff --stat`
   - inspect changed files.
2. Remove tool/install artifacts that should not be committed, for example a worktree-local `.pnpm-store/` created by an interrupted install.
3. If package tests fail with missing workspace package entries, build the workspace before judging the feature tests:
   - `corepack pnpm install --frozen-lockfile`
   - `corepack pnpm run build`
   - then rerun the focused package test.
4. Use the red test output to identify missing exported helpers and UI contract points. Do not retry the same failing test command unchanged after environment prerequisites are known missing.
5. For renderer-only wiring, keep the renderer on typed preload APIs only. Do not import git/fs/SQLite/Electron-main code into `packages/ui-canvas`.
6. For selected-node rollback UI:
   - hydrate action state from workflow projection plus backend rollback eligibility; do not depend on raw workflow events unless the IPC explicitly returns full payloads;
   - disable rollback for remote side effects and show repair/revert PR flow copy;
   - repair uses the after checkpoint;
   - variant uses the before checkpoint;
   - rollback applies workflow graph state only and must say evidence/history is retained;
   - reload projection/canvas session after successful backend IPC.
7. In the real Electron renderer, `workflow:events` may intentionally redact payloads for safety. A helper that validates full `workflow.lane.declared`, `workflow.edge.declared`, checkpoint, or remote-side-effect payloads will fail closed on that response. Use `workflow.getProjection(...).projection` or add a narrow backend IPC for selected-node action state; add a regression with the redacted event shape.
8. When repair/variant/rollback submissions include user text, carry it as a typed `instruction` end to end: renderer payload -> Electron IPC normalization (accept `instruction`, optionally normalize legacy `text`) -> workflow store event payload -> workflow-kernel checkpoint/rollback intent projection. Do not rely on generic text input or a field that the store normalizer drops. For rollback, validate idempotent retries against `instruction` too, otherwise the same request id can silently reuse a different user rationale.
9. When a previous slice deliberately left action submission disabled because backend wiring was out of scope, the wiring slice must remove that disabled-only guard and make the state explicit through helper availability and backend availability.
10. Add source/unit tests for the renderer contract, but still run package test, typecheck, and `git diff --check` before review-only. If persistence tests consume built workspace `dist`, rebuild upstream contract/kernel packages before judging replay failures.

## Review traps

- Do not pass node-action data through generic `appendWorkflowUserInput` if the persistence layer only stores text; that silently loses typed target/action state.
- Do not hydrate selected-node action availability from redacted `workflow:events`; it will look wired in source tests but stay disabled in the real desktop app.
- Do not add `instruction` only in the renderer. Verify it survives IPC normalization, store event payloads, replay, and kernel projection.
- Do not expose raw JSON, raw paths beyond existing evidence patterns, or git controls in the renderer.
- Do not let More/details behavior regress: node selection and detail inspection remain separate.
- If CSS/visual support marks rolled-back/inactive nodes, use existing `CanvasNode.rollbackStatus`; do not invent renderer-only rollback semantics.
