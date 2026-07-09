# Stacked PR remote branch cleanup discipline

Use this after a stacked PR has been squash-merged and its head branch may be deletable.

## Rule

Do not bundle destructive cleanup with required non-destructive progress steps. Fetching, fast-forwarding `master`, and re-inventorying PRs are safe status updates; remote branch deletion and forced worktree removal are cleanup. Run them as separate steps so a safety denial or user veto on deletion does not block live-state recovery.

## Safe sequence

1. Non-destructive refresh first:
   - `git fetch origin --prune`
   - fast-forward the local default branch if needed
   - re-read the open PR inventory
2. For every candidate head branch, query open PRs whose `base.ref` equals that head ref.
3. Print or record the exact candidate refs and their child lists.
4. Delete a remote head branch only when the child list is empty and the PR using that head is already merged/closed.
5. Remove local restack worktrees/branches separately from remote deletion.
6. If a tool or user blocks the destructive cleanup, stop that cleanup. Do not retry the same deletion through another tool. Leave a handoff with exact refs that still need cleanup and continue only if the user explicitly authorizes a non-destructive path or the cleanup later. Treat the already-completed non-destructive/merge work as done; do not relabel the whole PR lifecycle as failed just because cleanup was blocked.

## Pitfalls

- A single shell command that does fetch + PR inventory + `git push origin :refs/heads/...` can be blocked as destructive before the useful read-only work happens. Split it.
- Do not delete an old parent head merely because its PR merged; children can still target that branch until restacked.
- Do not treat local worktree removal and remote branch deletion as the same risk class. Local cleanup is reversible-ish; remote branch deletion affects collaborators and stacked PR bases.
