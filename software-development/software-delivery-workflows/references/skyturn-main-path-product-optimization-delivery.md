# SkyTurn main-path product optimization delivery

Use this note when the user asks Hermes to act as the SkyTurn delivery parent agent for the main path: Open Project → New Session → Current branch → Hermes planning → Codex execution → validation/screenshot/review/commit → evidence display → repair/variant/rollback.

## Parent-agent workflow

1. Keep each slice in its own git worktree and branch. Do not let one coding agent implement all requested slices in one worktree.
2. Start with live state, not summaries: `git status --short --branch`, `git worktree list`, open PR list, and existing branch names.
3. First wave can run low-conflict slices in parallel: acceptance harness, planner-root evidence status, and docs capability map.
4. For evidence UI/data slices, decide stack only if they edit the same public type contract. If `RunEvidence.artifacts` already exists, data capture and UI display can be independent PRs: data populates artifacts, UI displays whatever is present.
5. Parent must verify child-agent output with real diff/tests before commit. Child summaries are leads, not evidence.
6. Commit/push/open PR only after parent validation. Re-query GitHub PR state because `gh pr create` can print a URL while the shell returns non-zero.
7. Never merge, clean worktrees, delete branches, or remote-cleanup in this workflow unless the user explicitly asks.

## New Session UI acceptance hardening

A real desktop acceptance script should:

- Launch Electron + Vite with isolated `userData` and a temporary real git React project.
- Bypass only the native Open Project dialog by pre-seeding workspace state; do not bypass the New Session textarea or Create button.
- Drive `textarea[aria-label="New task goal"]` and `button[aria-label="Create"]` in the real renderer.
- Check Hermes/Codex readiness and report `mockFallback: false` for real evidence.
- Emit final JSON for both success and structured blockers. Do not let CDP/Electron automation failures escape as a raw stack trace.
- Treat long runs as background processes and inspect live `workspace.json` / `.devflow/runs/*/events.ndjson`; a 600s foreground timeout can kill a run that is close to commit.
- On success require: `ok: true`, screenshot path and bytes > 1000, commit count > 1, temp repo clean, all relevant RunEvidence terminal, planner root dependency-free, and only expected changed files.
- Guard against fake evidence: hash fixed validation scripts before/after, prohibit changing `scripts/verify.mjs` and screenshot harnesses, and require committed files to match an allowlist such as `src/App.jsx`/`src/App.css`.
- Watch for JSX/rendering bugs hidden by source-only validation. Example: raw text `Hermes -> Codex` can break JSX parsing/rendering while a source grep verify script passes; browser screenshot lane catches this.

## Artifact evidence pattern

If a lane has a known produced artifact, pass it as structured input rather than parsing agent prose:

- Add/propagate an explicit expected artifact contract such as `expectedArtifacts?: string[]`.
- Adapter records artifacts only after successful process exit.
- Verify the artifact exists, is a non-empty file, is a safe relative path, and is not secret/token/auth/credential-looking.
- Store safe paths in existing `RunEvidence.artifacts`; do not create a second artifact store.
- Keep inference narrow for known lanes, e.g. browser/screenshot lane → `.devflow/acceptance/react-app.png`.

## Node Modal / selected-node evidence UI

For main-path evidence UX:

- Use existing Node Modal tabs (`Output`, `Changes`, `Context`) and selected-node composer. Do not add evidence panels, dashboards, file tabs, or terminal dashboards.
- Context should display structured `RunEvidence`: runId, status, exit code, checks with kind/name/detail, artifacts, and explicit empty state.
- Changes should display structured changeset/delivery facts: status, changed files, diff stat, repo clean/recorded state, and commit evidence when present.
- Failed selected nodes should show failure summary, latest failed check, and action availability in the existing composer and modal.
- Copy must be explicit: repair uses the after checkpoint; variant uses the before checkpoint; rollback affects selected + downstream; remote side effects block rollback and route to repair/revert PR flow.
- Preserve stale async guards: compare `sessionId:nodeId` payload scope and a monotonic action generation token before applying repair/variant/rollback results.

## Verification notes

- For PR1-style real acceptance, record the final JSON fields in the PR body. Mention `experimental-run`/degraded readiness honestly.
- For UI-only PRs, run `@skyturn/ui-canvas` test/typecheck/build and `git diff --check`; run a browser smoke or screenshot when the task is visual. If no focused smoke exists, state the exact blocker and use build as fallback.
- For renderer smoke, trust the actual Vite `Local:` URL printed by the running process, not the requested port. Some package scripts do not forward extra `-- --port ...` args as intended and Vite may choose another free port.
- When a managed background process later reports `SIGTERM`, check whether the parent intentionally killed it during cleanup. Do not reopen a solved blocker from an expected cleanup notification; label it as cleanup and continue from live state.
- If Antigravity print mode times out but leaves a partial diff, parent should inspect the diff and rerun validation. Do not trust missing final summary; switch to Codex or parent edits if needed.
- If pnpm worktree installs hit store/symlink permission issues, use a temporary worktree-local store for the child agent and delete `.pnpm-store` before review/commit.
