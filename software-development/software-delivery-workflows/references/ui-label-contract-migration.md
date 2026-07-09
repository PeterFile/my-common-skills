# UI Label Contract Migration

Use this when a UI helper changes raw enum/source/status/role values into human-safe display labels and tests begin failing across component and integration suites.

## Pattern
1. Identify the render path before editing assertions.
   - Helper-backed UI can assert human-safe labels.
   - Raw provenance, checkpoint proof, source-kind aggregation, storage/API contracts, and debug evidence dumps may intentionally remain raw enum strings.
2. Patch the label allowlist/helper first, not fixtures or broad call sites.
   - Add explicit allowed mappings for known safe enum values.
   - Keep unknown/unsafe fallback bounded, usually `Unknown`.
   - Do not globally title-case arbitrary strings; that can render hostile or secret-like values.
3. Update tests only after proving the assertion observes helper output.
   - Component tests usually reveal the intended local contract.
   - Integration tests often mix helper-backed visible labels with raw proof strings in the same panel; inspect nearby component code before changing expected text.
4. When a test times out after label changes, suspect a stale `findByText`/`waitFor` string before increasing timeout.
   - Run the single named test.
   - Read the nearby assertions and rendered label path.
   - Only increase timeout after proving the wait condition is correct and the test is inherently slow.

## Validation ladder
- `git diff --check origin/<base>...HEAD`
- Focused component suites that cover the helper and immediate consumers.
- Targeted integration tests for each changed visible label path.
- Full file integration suite if the file contains many mixed helper/raw contracts.
- Browser/e2e smoke greps for the same visible label path in every served mode that CI runs, commonly preview/build and dev. Stale raw-label assertions can survive unit/App tests and fail only in Playwright smoke.
- Typecheck after the final test edits, not just before them.

## Pitfalls
- Global search/replace of raw enum strings breaks proof/source aggregation contracts.
- Treating every stale test as product failure hides the real distinction between display labels and raw accountability evidence.
- Secret/canary strings in tests are often negative assertions. Do not copy them into summaries; refer to them as `[REDACTED]`.
- A Playwright smoke assertion may intentionally keep raw proof type tokens while expecting human-safe helper labels around them. Update only the helper-backed label segments and preserve raw proof identifiers such as event/type names when those are the accountability contract.
