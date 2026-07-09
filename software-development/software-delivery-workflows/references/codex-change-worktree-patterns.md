# Codex Change and Worktree Patterns

Use this when a SkyTurn/workflow task asks to model code-change evidence or branch/worktree behavior after OpenAI Codex.

Source inspected: `openai/codex` shallow clone at commit `21a599f`.

## Durable Findings

- Codex treats code changes as protocol evidence, not assistant prose. Relevant structures are `PatchApplyBeginEvent`, `PatchApplyUpdatedEvent`, `PatchApplyEndEvent`, `FileChangeItem`, and `TurnDiffEvent`.
- `FileChange` is structured as `Add { content }`, `Delete { content }`, or `Update { unified_diff, move_path }`.
- `TurnDiffTracker` tracks the net per-turn diff from committed `apply_patch` deltas without rereading the workspace. If the delta is not exact, it invalidates rather than pretending precision.
- Patch lifecycle emits a completed `FileChangeItem` and then emits `TurnDiffEvent` when the tracked net diff changes, including net-zero updates.
- For baseline-style diffing, Codex uses Git tree/blob comparison in `git-utils/src/baseline.rs` to produce `GitBaselineDiff { changes, unified_diff }`.
- Codex local CLI does **not** generally auto-create worktree branches. Main-path `git worktree add` occurrences were tests/config support, not a local orchestration primitive.
- Codex model instructions explicitly say not to create new branches or commits unless requested. Branch mutation is treated as unsafe; read-only `git branch` forms are allowed separately.
- Codex Cloud task creation passes a branch/ref to the remote backend. Local apply fetches a diff and uses `git apply --check` / `git apply --3way`; it does not create a local worktree branch.
- Codex TUI can parse hidden `::git-create-branch{cwd="..." branch="..."}` assistant directives to refresh UI branch metadata after an action, but the directive is notification/UX metadata, not proof of branch creation.

## Application to SkyTurn-like Systems

- Make changes first-class backend/run events: `file_change.begin`, `file_change.updated`, `file_change.end`, and `turn_diff`/`run_diff`; UI should render these, not infer them from agent text.
- Keep final changeset evidence Git-backed. A final `git diff`/`git status` pass should verify event-derived change state.
- If the product needs isolated lanes, it is acceptable to be stronger than Codex CLI and create managed worktrees, but the creator must live in backend/Electron-main/process code, be idempotent, validate branch/base refs, record created/failed events, and reconcile candidate identity against path, gitdir, base, and current HEAD. Branch name may be absent for detached candidates and should not be the only identity.
- Do not let renderer/UI synthesize branch, base/head, or changeset truth. It can request and display evidence only.

## SkyTurn Product Decision Captured

When translating Codex patterns into SkyTurn product design, do **not** default sessions to isolated worktrees. The default execution target is the current project worktree on a user-selected branch. `New worktree` is an explicit New Session option.

The New Session input should be modeled as two separate controls:

1. Execution target:
   - `Current branch` — default; run in the selected branch/current project worktree.
   - `New worktree` — explicit opt-in; create a candidate worktree from the selected base.
2. Branch selector:
   - In `Current branch` mode, this is the development branch.
   - In `New worktree` mode, this is the base branch/ref for the candidate worktree.

Candidate worktrees are not user-facing project branches until accepted. On acceptance, SkyTurn may create a formal branch, commit, merge/cherry-pick, or PR. On rejection, clean the candidate after checking no runs target it.

For Changes UI, use a two-layer source model:

- Live layer: structured adapter events, especially Codex patch/file-change/turn-diff events. Codex TUI renders summaries from structured `FileChange`, not assistant prose.
- Reconcile layer: git-backed final changeset against the session start branch state or the worktree base ref. If structured events and git reconciliation disagree, surface the mismatch rather than silently choosing one.
