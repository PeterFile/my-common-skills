# Stacked PR CI failure triage notes

Use this when cleaning a stacked PR backlog and a fresh pull_request CI run fails after a force-pushed restack.

## Pattern

1. Confirm the failing run belongs to the current remote PR head SHA and `pull_request` event. Ignore older green or red runs after any force-push or base advance.
2. Fetch the failing job metadata and check-run annotations before rerunning. A single annotation often points to the exact stale expectation or test file.
3. Fix only the current PR scope. For label/text changes, search for the old public string across the relevant app/e2e tree and update stale assertions in the same PR instead of widening product behavior.
4. Reproduce the failing shard/test locally with the narrowest command available, for example a Playwright/browser-smoke grep that targets the failed test title.
5. Clean generated artifacts from local smoke runs (`playwright-report/`, test-results, screenshots) before amending.
6. Amend the single PR commit, push the exact amended commit with `--force-with-lease=refs/heads/<head-ref>:<old-head-sha>`, then wait for a new fresh `pull_request` gate.
7. Do not push or merge prepared child PRs while the parent PR is still waiting or red; parent merge will advance `master` and stale the children.

## Evidence from metaverse-office-web cleanup

A label-only UI PR changed `Workspace evidence` to `Local evidence`. Unit tests and typecheck passed, but GitHub browser smoke failed in `operator-shell.layout-visual.smoke.spec.ts` because one e2e assertion still expected the old label. The correct recovery was:

- Read the failing job annotations; they named the exact spec line and expected substring.
- Search the e2e tree for the old label; only one stale assertion remained.
- Patch that assertion to `Local evidence`.
- Run the focused browser smoke grep locally.
- Remove generated `apps/web/playwright-report/`.
- Amend and force-push with a lease; wait for a fresh PR run.

A stacked UI model PR later had a fresh pull_request `test` job fail twice in `WorldScene.test.tsx`, a file outside the PR diff. The correct recovery was not to bury unrelated test stabilization inside the feature PR. Treat it as a separate unblocker when all of these are true: annotations point outside the PR diff, the failure reproduces as a known timing/assertion-settle gap or CI-only flake, and the fix is test-only or otherwise independent of the feature. Safe sequence:

- Confirm the current PR diff is honest and does not touch the failing file.
- Read check-run annotations to identify the exact failing test and line.
- Run the failing test locally multiple times; if it passes locally but CI fails, inspect for missing `waitFor`/microtask/layout settle before user simulation.
- Create a small default-branch unblocker PR with only the stabilization fix.
- Validate the narrow failing tests, the full affected test file, typecheck, and `git diff --check`.
- Wait for the unblocker PR fresh pull_request CI and merge it first.
- Rebase the original feature PR onto the new default branch and require a new fresh pull_request CI before merging.

Do not record PR numbers as durable procedure; the reusable parts are annotation-first triage, keeping unrelated flake fixes out of feature PRs, and using a small validated unblocker PR when the failing file is outside the current diff.

## Playwright / browser-smoke patterns from compact UI PRs

When a restacked UI PR changes compact disclosure/card layout, GitHub `test` and browser-smoke failures often expose stale exact assertions rather than product regressions. Handle them narrowly:

- If a hidden `<details>` panel is intentionally closed by default, do not assert absence with container `toContainText`; DOM `textContent` includes hidden disclosure content. Assert user-visible state instead, e.g. `getByRole(...).toHaveCount(0)` for hidden accessible regions or `getByText(...).toBeHidden()` for closed disclosure rows, then separately test expansion when needed.
- Keep exact API read guards exact. If the current UI legitimately issues a new read-only GET for an already-modeled facet, add the exact method+path+query to the allowlist and route fixture; also add nearby rejected permutations with reordered query/raw/write variants so the test is not accidentally widened.
- When CI annotations point to stale CSS contract tests, compare the CSS rule in `styles.css` before editing. Update the test to the current intentional contract only when the product CSS is already the desired compact/scroll-bounded behavior.
- When a UI PR changes a compact HUD/chip from an old exact status label to a derived state model, browser-smoke failures may be stale accessible-name and text assertions rather than runtime failures. Patch all coupled assertions together: role/name (`aria-label`), visible chip copy, and HUD summary/topline copy. Then run the exact failing smoke grep in both modes (`test:browser-smoke:dev -- --grep ...` and `test:browser-smoke -- --grep ...`) before amending.
- If Playwright `.click()` on a compact `<summary>` times out because a neighboring action group/source-details summary intercepts the pointer, first reproduce the exact smoke locally and inspect screenshot/error context. If the assertion only needs disclosure expansion for geometry/visibility and keyboard access is acceptable, use `press('Enter')` on the summary instead of force-clicking; do not add ineffective z-index/pointer-event CSS just to satisfy the test.
- If a pushed PR first fails browser smoke on a stale visible/ARIA label and you fix that assertion, the next exact-head run may expose a different `test` job failure before smoke shards even start. Treat the skipped smoke jobs as downstream of the failed prerequisite, not as missing CI. Read the new test-job annotations, compare the failing file against the final PR diff, and do not merge or bury unrelated stabilization into the current PR just to get the stack moving.
- Always remove generated `apps/web/playwright-report/` and `apps/web/test-results/` before amending, then rerun the focused failing smoke plus `git diff --check` and the relevant type/style/unit check before force-pushing with a lease.
