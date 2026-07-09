# Stacked UI conflict: older root vs newer merged child

Use this when a stacked UI PR is still open after later adjacent slices have already been merged into the default branch. Cherry-picking the older PR can conflict with newer merged semantics even when both were originally valid.

## Pattern

Symptoms:
- PR A is an older root or sibling, still open.
- PR B touched the same UI/test region and has already been squash-merged to `master`.
- Replaying PR A onto current `master` conflicts in large React/test files.
- One side removes or hides UI that the newer merged branch deliberately exposed behind a disclosure, popover, or compact surface.

## Safe resolution

1. Treat the old PR as a patch to current `master`, not as authority over the entire conflicted block.
2. Identify the current merged semantics from `master` before editing the conflict.
3. Preserve newer merged behavior unless the user explicitly asked to revert it.
4. Apply only the old PR's still-missing behavior as an incremental change.
5. For UI compacting conflicts, prefer composition over deletion:
   - keep the compact summary/triage behavior from the old PR if still desired;
   - keep newer explicit disclosure/detail affordances from `master` if already merged;
   - ensure hidden/default-closed detail remains testable by expanding it before asserting contents.
6. Update tests to match the combined behavior, not either historical side verbatim.
7. Search for conflict markers, run `git diff --check`, finish the cherry-pick/rebase, then run the lane gate.
8. If browser-smoke specs changed, run a local smoke grep when feasible before push; CI smoke is still required after push.

## Test adjustment examples

Bad after combining with a default-closed disclosure:

```ts
expect(within(inspectPeek).queryByRole('region', { name: 'Selected agent source matrix peek' })).not.toBeInTheDocument();
```

Better:

```ts
const closedSourceMatrix = within(inspectPeek).queryByRole('region', {
  name: 'Selected agent source matrix peek'
});
expect(closedSourceMatrix).not.toBeNull();
expect(closedSourceMatrix).not.toBeVisible();
await user.click(within(inspectPeek).getByText('Source details'));
const sourceMatrix = await within(inspectPeek).findByRole('region', {
  name: 'Selected agent source matrix peek'
});
expect(within(sourceMatrix).getByText('Workspace file · Observed')).toBeVisible();
```

## Why

This avoids silently reverting a newer merged user-visible affordance while still landing the older PR's useful compacting/CTA/read-surface behavior. In stacked cleanup, correctness is the diff against current `master`, not fidelity to stale conflict sides.
