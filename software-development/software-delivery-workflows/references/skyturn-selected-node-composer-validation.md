# SkyTurn selected-node composer validation

Use when changing SkyTurn canvas node selection, React Flow node state, or the bottom selected-node composer.

## Failure pattern observed

A selected-node composer change can pass unit/type/build gates but still fail in a real browser:

- Clicking `.agent-card-select` white-screens the renderer.
- Browser error is React minified error #185, with stack through `@xyflow/react` store `setNodes` / React `forceStoreRerender`.
- The root cause can be a feedback loop between app-controlled selected-node state and React Flow internal `selected` state.

## Stable fix pattern

Keep composer-target state separate from React Flow's internal selection store:

1. Do not drive React Flow visual selection by writing `selected: node.id === selectedNodeId` into controlled `nodes` when the app also handles selection state.
2. Put app-level composer target state into node data, e.g. `data.composerSelected`.
3. Let `AgentNode` render selected styling from `data.composerSelected`, not the `selected` prop from React Flow.
4. On the node card click/key handlers, call `event.stopPropagation()` before `data.onSelect(node.id)` so React Flow pane/selection handlers do not fight app state.
5. Preserve React Flow measured/dragging state in merge helpers, but return the original `current` nodes array when no semantic node fields changed. Recreating node objects on every effect can feed store update loops.
6. If the selected-node composer moves from overlay to reserved layout, include the selected node id in the viewport signature and use enough selected-state fit padding to keep the node fully above the composer row.

## Verification recipe

Static gates are required but insufficient:

```sh
git diff --check origin/main...HEAD
corepack pnpm --filter @skyturn/ui-canvas run test
corepack pnpm --filter @skyturn/ui-canvas run typecheck
corepack pnpm --filter @skyturn/ui-canvas run build
```

Then run a real browser smoke against the served desktop renderer:

1. Create a Fast canvas session.
2. Click `.agent-card-select`.
3. Assert no `window.onerror` entries and no white-screen.
4. Measure rectangles:
   - `.agent-node-shell.selected`
   - `.composer-selected-dock`
   - `.canvas-composer-shell`
   - `.canvas-composer`
   - `.react-flow`
5. Require the selected node not to overlap the dock, shell, or input. A 1px boundary collision is still a visual failure; increase selected-state fit padding or reduce reserved composer height.
6. Capture a screenshot and visually confirm the node title/status/body remain readable.

## Pitfall

A passing React/source-string test that only checks the intended code shape does not prove React Flow selection is safe. The browser click path is the acceptance gate for this class of change.