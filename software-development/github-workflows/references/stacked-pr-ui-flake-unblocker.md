# Stacked PR UI flake unblocker pattern

Use when a stacked PR's exact-head `pull_request` gate fails in UI tests outside the PR diff, especially after a local focused reproduction passes.

## Signal

- The PR diff is backend/docs or otherwise unrelated to the failing UI test.
- The first failed required job names a UI test outside the PR diff.
- A local focused rerun of that exact test passes.
- A single rerun of failed jobs fails again, especially on a different unrelated UI test.

At that point, stop blind reruns. The required gate is still red, but repeated reruns are noise, not evidence.

## Safe response

1. Preserve the blocked PR as-is if its own local lane is green.
2. Create a separate test-only unblocker branch from current `origin/master`.
3. Stabilize only the flaky test harness/expectation, not product behavior:
   - For async focus assertions, wait for focus to settle before checking `document.activeElement`.
   - For Pixi/AI-town scene timing, wait for the specific rendered sprite/pin/layer precondition before ticking or asserting movement. Do not assert on objects that may not have been created yet.
4. Validate the unblocker locally with the exact failing focused tests, then the smallest broader lane that covers the edited test files, plus typecheck when TypeScript changed.
5. Open/merge the unblocker only after its own exact-head `pull_request` gate is green.
6. Rebase/restack the blocked PR onto the new default branch, rerun its in-scope local validation, force-push with a lease, and require a new exact-head `pull_request` gate.

## Pitfalls

- Do not merge the blocked PR because local backend validation passed; the required PR gate is still red.
- Do not keep rerunning after two unrelated UI flakes. Treat it as a CI stability blocker and fix the test class.
- Do not contaminate the backend/docs PR with unrelated UI test stabilization unless the user explicitly asks for that trade-off. A separate unblocker keeps diffs honest.
- Do not commit a speculative test stabilization that fails focused validation. Revert or refine it first.
