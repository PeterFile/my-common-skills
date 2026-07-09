# UI Canvas Visual Validation Notes

Use this when validating interactive canvas UI changes, especially React Flow / xyflow node-card or edge styling work.

## Durable lesson
A browser smoke test can mutate the state being validated. In SkyTurn-like apps, a mock runner or interval may auto-advance node status after a session opens, so a seeded five-state design exploration can quickly stop displaying the intended Pending / Running / Retrying / Completed / Failed matrix.

## Recommended workflow
1. Verify the seed/model data first with unit tests or direct factory assertions.
2. For visual validation, ensure the runtime cannot auto-advance the state you are trying to inspect. Good options:
   - add an explicit demo/design-preview mode that freezes seeded states;
   - skip mock advancement for nodes carrying design-preview display/runtime metadata;
   - or make the smoke test capture immediately before timers advance, if the app design allows that.
3. For multi-branch UI delivery, run the served app from the exact worktree/branch under review, preferably on a dedicated port per slice. Do not let a screenshot from one branch stand in for another branch's visual validation.
4. Validate the actual complained-about interaction, not just initial render. Examples: open the custom dropdown and inspect overlap/coordinates; approve a gated page and confirm it advances; select a canvas node and confirm the composer does not cover node/status text.
5. For non-overlap claims, pair the screenshot with DOM geometry. Inspect `getBoundingClientRect()` for the selected node, composer dock, composer shell/input, and ReactFlow viewport, then explicitly check rectangle intersections. A visually plausible screenshot can still hide a 10-20px overlap at card edges.
6. Treat absolute-positioned overlays plus canvas padding as suspect for selected-node composers. If the requirement is “do not cover information,” prefer reserved layout space (for example, stage grid rows with ReactFlow above and composer below) over an overlay. Also ensure the graph refits after entering that layout: single-node canvases may skip normal `fitView` paths if `shouldAutoFitCanvas(nodes)` returns false, so selected-node state may need to be part of the viewport signature or fit trigger.
7. Do not treat unit/type/build success as enough after changing React Flow node selection or `useNodesState` synchronization. Exercise the real selected-node click path and capture runtime errors. React error #185 / `forceStoreRerender` / `@xyflow/react setNodes` after selection usually means an update loop between local node state and the React Flow store. Check effects like `setFlowNodes((current) => mergeFlowNodeState(current, nodesSource))`; the merge helper must return the existing `current` array when nothing semantically changed, and selected-node layout/fit changes must not create fresh node objects on every render.
8. For selected-node composer validation, the acceptance gate is all of: no white screen after click, no console/runtime exception, `selectedCount === 1`, and no rectangle overlap between the selected node and composer dock/shell/input. If any one fails, the slice is not PR-ready even if tests pass.
9. Treat a successful render with mutated statuses or an unexercised interaction as partial validation only: layout and mounting are verified, but the requested state or interaction is not.
10. Report the distinction clearly: seed correctness, build/type correctness, and live visual state are separate evidence. If tool budget stops before one interaction screenshot or DOM overlap check, say that slice is not visually complete and do not claim PR-ready visual acceptance.

## What not to persist as a rule
Do not encode one-off port conflicts, missing node_modules, or local dev-server setup failures as durable constraints. Capture the validation-state freeze pattern, not transient setup state.