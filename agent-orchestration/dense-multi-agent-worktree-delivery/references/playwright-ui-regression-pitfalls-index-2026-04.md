# Playwright, UI, request-scope, and pivot regression pitfall index

Load when: touching metaverse-office-web Hub/DetailsPanel/App browser smoke, request-scope assertions, accessible names, pivot/correlation behavior, viewport geometry, or browser-smoke fixtures.
Keywords: Playwright, browser-smoke, request-scope, DetailsPanel, Hub, App.test, accessible name, correlation, selectedCorrelationId, null, undefined, viewport, route, fixture.

This file is an index and distilled guardrail set. For full historical detail, search the legacy archive:
`references/legacy/SKILL-2026-04-25-full-pre-refactor.md`.

## 1. Browser-smoke command discipline

For real smoke validation, prefer the project wrapper:
- `pnpm --filter @metaverse-office/web test:browser-smoke -- --grep "..."`
- or inside `apps/web`: `node ./scripts/run-browser-smoke.mjs -- --grep "..."`

Do not treat direct `playwright test` as authoritative if the project wrapper provisions backend/proxy/frontend lifecycle differently.

## 2. Request-scope assertions

Bad patterns:
- asserting network shape immediately after a DOM assertion
- using a frozen request log with `expect.poll`
- relying on `networkidle` or fixed timeouts as proof
- filtering only GET requests and then claiming no non-GET happened

Good patterns:
- arm `page.waitForRequest` / `page.waitForResponse` before the pivot/action
- use `expect.poll` on the live request log for positive required requests
- start forbidden-request capture only at the action boundary being claimed
- wait for a short stable sample before negative assertions
- record all same-origin methods, then assert non-GET set is empty if that is the contract

## 3. Route matching

Prefer semantic route gating:
- parse `new URL(route.request().url())`
- match pathname and meaningful query parameters
- explicitly exclude other request classes such as `agent_id`, `state`, or `limit` only when relevant

Avoid brittle exact query-string matches when param order or harmless additions may change.

If a route override only needs one synthetic JSON row, direct `route.fulfill({ status, contentType, body })` can be safer than `route.fetch().json()` against proxied paths that may return HTML under harness conditions.

## 4. Fixture discipline

Do not copy assumptions from `App.test.tsx` into Playwright smoke.
Inspect `apps/web/scripts/browser-smoke-backend.mjs` or the live fixture path first.

Examples of historically risky assumptions:
- actor/counterparty identities differ between jsdom and browser-smoke fixtures
- default selected correlations differ by entry path
- seeded collector/workflow/accountability records may reorder replay rows or selected correlation behavior

Prefer test-local narrow route overrides over mutating the shared browser-smoke backend fixture for one new canary.

## 5. Accessible names and strict locators

When a surface gains buttons inside rows previously asserted as plain text:
- assert container text with `toHaveTextContent(...)`
- separately assert the button accessible name
- include row-local context in aria-labels when repeated agents/correlations/events can occur

Avoid generic labels like:
- `Open workflow correlation <id>`
- `Select incident feed counterparty agent <agent>`
- `Select collector supervision watcher <agent>`

Use context-rich labels:
- `Open workflow interaction correlation from interaction <interaction_id> <correlation_id>`
- `Select incident feed counterparty agent from incident <incident_id> <agent_id>`
- `Select watch topology source agent from <watch_mode> edge <from_agent_id> <to_agent_id>`

## 6. Correlation carry semantics

Do not collapse `undefined` and `null` correlation semantics.

Safe mental model:
- `undefined` means existing auto-selection path
- explicit `null` means intentionally preserve no-correlation path only when the callsite has opted into that meaning
- non-null correlation carries active scope

Do not globally preserve null from every pivot. Some callsites need auto-correlation while async sources are still loading.

For correlation buttons:
- default-correlation reselect may stay auto only when the clicked correlation is already active, equals computed default, and current mode is auto
- manual/preserved paths must remain explicit when intended
- rerun workflow/accountability carry canaries after changing shared handlers

## 7. Viewport and geometry smokes

When testing viewport drag/reachability:
- account for Hub overlays and selected-watch overlays intercepting pointer events
- close Hub if the contract is post-Hub steady state
- use host-level/synthetic pointer dispatch only when testing host listeners under overlay conditions
- assert against actual `.aitown-world__host` size when inspector dimensions matter
- avoid over-tight subpixel tolerances; use established geometry budgets

## 8. Hub/OpenHub first-fold visual smoke pattern

When turning Hub/OpenHub UX research into a product slice, do not start by adding more right-rail content. First add a real browser geometry canary, prove RED on current behavior, then make the smallest IA/layout change.

Reusable pattern from the Hub first-fold slice:
- create a dedicated Playwright spec such as `apps/web/e2e/operator-shell.layout-visual.smoke.spec.ts`
- run it through the project wrapper, not bare Playwright, for RED/GREEN proof: `pnpm --filter @metaverse-office/web test:browser-smoke -- e2e/operator-shell.layout-visual.smoke.spec.ts --grep "..."`
- assert first-fold visibility with real `getBoundingClientRect()` against the Hub scrollport, not with text-only DOM assertions; require priority objects like `Crew Overview`, `Active Queue`, and the first active queue action to fit without scrolling
- compute overlay obstruction from rectangle intersection and keep the Hub as a side sheet; also define a primary world drag lane and assert the Hub does not intersect it
- close the Hub and perform an actual canvas/viewport drag to prove the world remains usable after the overlay path
- if the RED failure proves the priority section is below the fold, prefer moving that exact section earlier over shrinking fonts, weakening assertions, or adding another menu
- when a new smoke file is intended as a default gate, update `apps/web/scripts/run-browser-smoke.mjs` and `apps/web/scripts/run-browser-smoke.test.ts` in the same slice; otherwise CI will not run it
- after a new geometry smoke passes once, run a small repeat check (`--repeat-each=3` via Playwright is acceptable as a reliability probe, but the project wrapper remains the authoritative smoke command)
- record the design rule in an ADR when it encodes product direction, e.g. reject long right rails / large routine modals / stacked popups / fake game metrics, and prefer compact HUD, inspect peeks, tabbed drilldowns, or map overlays

Do not over-tighten geometry thresholds. Use product-level budgets such as first-fold containment, side-sheet obstruction ratio, and primary drag-lane clearance rather than pixel-perfect screenshots.

## 9. Browser-smoke / App-test flake triage

If full smoke fails but targeted wrapper command passes:
- rerun the exact failed smoke once in isolation
- classify likely flake only with fresh evidence
- if a new test hits default 30s timeout under whole-suite load but passes targeted wrappers, prefer per-test `test.slow()` or narrow timeout adjustment, not global timeout changes

For `App.test.tsx` / RTL tests that assert "no polling after Hub close":
- first reproduce the exact selector on the feature worktree and on clean current `master`
- if clean `master` is also red, classify it as a baseline canary blocker and cut a minimal unblocker from `master` instead of contaminating the feature PR
- beware `user.click(Close Hub)` in timing-sensitive tests with a shortened poll interval such as `__AITOWN_POLL_INTERVAL_MS__ = 1000`; user-event can spend enough async time in the click sequence for an already-scheduled poll to fire before the close state commits, creating a false extra `/correlations/<id>?limit=10&window=60m` request
- when the product control is a plain `<button onClick={closeHub}>` and `closeHub` only does synchronous `setHubOpen(false)`, it is acceptable for this specific timing canary to trigger the close with `await act(async () => { screen.getByRole('button', { name: 'Close Hub' }).click(); });` before waiting past the poll interval
- keep separate `user.click` tests for the real Hub close/accessibility path; do not globally replace user-event interactions with DOM `.click()`

## 9. Where to find full history

The full pre-refactor pitfall ledger remains in:
- `references/legacy/SKILL-2026-04-25-full-pre-refactor.md`

Search it for MYC-specific incidents before touching sensitive surfaces:
- selected-agent replay/supervision stale data
- current operation request scope
- incident feed lifecycle semantics
- collector tmux stable refs
- world viewport clamp/reachability
- duplicate CI and hot-file sibling closeout