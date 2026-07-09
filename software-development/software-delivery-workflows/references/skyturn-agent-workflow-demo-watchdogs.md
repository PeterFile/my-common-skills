# SkyTurn agent workflow demo watchdogs

## Trigger
Use this when validating SkyTurn's real Hermes→Codex desktop workflow demo or similar agent workflow acceptance scripts that start local CLI adapters and wait for terminal run evidence.

## Lesson
An outer demo wait timeout is not the same thing as adapter terminal evidence. If the foreground command, CI job, or acceptance harness kills the demo before the agent adapter watchdog fires, the run can be left with only `progress` events and no terminal `status`/`RunEvidence`. That is not acceptable completion evidence.

## Durable pattern
1. Treat `pnpm --filter @skyturn/desktop run demo:mvp` as a real long-running acceptance path, not a mock or unit test.
2. Configure Hermes/Codex adapter watchdogs to expire before the harness wait timeout, leaving a small buffer for `evidence` and final `status` events to flush.
3. If the demo times out, inspect the temporary `skyturn-react-demo-*` project before summarizing:
   - `git status --short --branch` in the temp repo.
   - `.devflow/runs/*/events.ndjson` last event per run.
   - `.devflow/tasks/*/output.md` for lane-specific evidence.
   - Screenshot artifact size/existence and verification script result.
4. Distinguish partial real progress from full acceptance:
   - Hermes planner succeeded.
   - Codex implementation/validation/screenshot lanes succeeded.
   - Review or commit lane hung/no terminal evidence.
   These are useful facts, but they are not `ok: true`.
5. Do not call the direction complete until final demo JSON or reconstructed evidence proves all required lanes reached terminal status and acceptance predicates passed.

## Pitfall
A foreground 600s tool timeout can kill a demo before the repo's default 30-minute agent watchdog emits `timed-out`. The fix is not to record "demo is flaky"; the fix is to make demo adapter watchdogs shorter than the demo wait timeout and test that timeout relationship.
