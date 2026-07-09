# SkyTurn UI Slice Integration Closeout

Use when several already-validated SkyTurn UI slices touch overlapping `packages/ui-canvas` / planner files and the user asks for an integration PR.

## Pattern
1. Verify live state first: `main`, open PRs, each slice head SHA, base branch, mergeability, and exact-head CI. Treat earlier child-agent or parent summaries as leads only.
2. Create a fresh integration worktree/branch from `origin/main`; do not mutate the main worktree.
3. Merge sibling slice heads in explicit order with `--no-ff` so the integration PR preserves audit history. Resolve conflicts only inside the expected overlap files.
4. In a new worktree, run `corepack pnpm install --frozen-lockfile` before root gates if `node_modules` is absent; missing `turbo` is setup state, not a code failure.
5. Run root gates from the integration worktree, in SkyTurn order: `git diff --check origin/main...HEAD`, `corepack pnpm run build`, `corepack pnpm run test`, `corepack pnpm run lint`, `corepack pnpm run typecheck`.
6. For UI changes, run a real browser smoke against the integrated branch, not just the individual slices. Cover every combined behavior that can interact:
   - new-session controls render as styled app controls, not native selects;
   - Plan starts on Requirements, keeps Convert disabled, gates Design/Tasks, and approve advances to Design;
   - selected-node composer does not white-screen and its rects do not overlap the selected node/dock/shell/input.
7. Push the integration branch and open one integration PR that explicitly lists absorbed PRs. Keep the original slice PRs open for audit until the integration PR merges; closing or merging them is a separate explicit closeout action.
8. Stop after opening/validating the integration PR unless the user explicitly authorizes merge and sibling PR cleanup.

## React Flow selected-node pitfall
Do not drive React Flow's internal `selected` state from app-level selected composer state while also listening to React Flow selection. That can form a `setNodes` feedback loop and trigger React error #185 / white-screen. Prefer app-owned node data such as `composerSelected`, stop propagation from node-card clicks, and make merge helpers return the current node array when nothing semantically changed.

## Evidence to report
- Integration PR URL, head SHA, exact-head CI state.
- Root gate commands and pass/fail summaries.
- Browser smoke facts, including no JS errors and `nodeDockOverlap/nodeShellOverlap/nodeInputOverlap: false` for selected-node composer work.
- Which sibling PRs are absorbed and still open.