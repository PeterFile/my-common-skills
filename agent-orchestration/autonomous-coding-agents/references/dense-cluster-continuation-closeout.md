# Dense cluster continuation closeout notes

Use this as a compact reference when resuming a large Codex/worktree cluster after a Hermes budget or context cutoff.

## Resume from handoff without replaying completed work

1. Treat the handoff as a lead, not evidence.
2. Verify the live main repo and each named worktree before touching code:
   - branch and HEAD
   - upstream/tracking state
   - `git status --short --branch`
   - diff stat and changed paths for dirty lanes
3. If the handoff contains a file-mutation verifier warning, check the actual worktree path directly. A failed patch warning may be stale or may point at a path typo; do not assume either completion or loss.
4. Resume at the smallest unfinished lifecycle step: run the missing validation, fix only the failing assertion/boundary, commit, push, PR, or status-sync.
5. If context compaction or a tool-call ceiling interrupts immediately after a parent-side patch, treat that lane as dirty/unverified even when the patch is narrow and obviously targeted. On the next turn, start with `git status --short --branch`, review the exact diff, then rerun the narrowest focused validation before scoring, committing, or reporting completion.
6. If an active todo list survives compaction, use it only as a lifecycle pointer. Reconfirm live worktree/process state before deciding whether a lane is still running, ready for validation, or already obsolete.

## Parent-side validation before PR

For each lane:
- Review the actual diff before staging.
- Run the cheapest command that proves the touched behavior, then a typecheck/build gate when relevant.
- Confirm the intended tests actually ran; skipped-by-filter output is not validation unless the intended subset also passed.
- Commit only the lane files.
- Compare branch diff against the intended stack base, not against the default branch.
- If the lane is an oversized dirty scratch result from a killed/late worker, split it before PR: export path-scoped patches, create fresh stack branches from the right base, apply with index, commit small slices, validate each slice, and keep the original scratch lane clearly marked not-ready until deliberately cleaned.

## UI density/details pattern

When a UI density lane hides detailed content behind native `<details>`:
- Closed `<details>` content remains in the DOM.
- Tests should assert `not.toBeVisible()` for closed detail content, then click the `summary` before content assertions.
- `not.toBeInTheDocument()` is the wrong assertion for closed details content.

## Broad UI file overlap check

Before opening a UI PR that touches broad files such as `App.tsx`, `App.test.tsx`, or global CSS:
- List changed files for sibling stack PRs against the same base.
- If paths overlap, restack or split before PR.
- If paths do not overlap, record that the overlap check was clean.

## Status closeout

After the final dirty lane is resolved:
- Verify all run worktrees are clean.
- Treat a killed/terminated cluster runner (`exit -15`, missing one lane exit file, or a stopped wrapper process) as process state only. It is not evidence that every lane failed or succeeded. Reconcile using live worktree status, lane commits, PR heads, and validation output.
- Post one concise status update to Slack and Linear with PR URLs, validation commands/results, no-op lanes, and remaining caveats. If the tracker cannot create a new issue because of usage limits, update the existing umbrella issue with a comment and return the comment URL; do not create a transient markdown status file just to work around tracker limits.
- If GitHub status API returns `state: pending` with `total_count: 0` and empty statuses, report it as "no checks returned", not CI success.
- When status API is empty, query GitHub Actions by PR `head_sha` and prefer the latest `pull_request` run over push runs. A green push run does not replace the PR gate. Poll briefly if useful, but stop and report an external CI queue blocker rather than waiting blindly.
- Never merge a child PR into its parent branch to make progress. Child PR success only means the child head is validated against its current base; it is still blocked until the parent chain is merged/restacked. Merge only PRs whose intended target is the default branch and whose `pull_request` gate is green.
- Do not create progress markdown for transient run status; use existing durable direction/spec docs only when product/API/runtime/UI semantics changed.
