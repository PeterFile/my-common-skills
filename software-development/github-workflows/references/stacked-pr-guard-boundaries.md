# Stacked PR Guard Boundaries

Use this when a stacked-PR cleanup/merge session hits Hermes' destructive-action guard.

## Durable lesson
Hermes may block more than deletion cleanup. Force-pushes to PR head branches (`git push --force-with-lease`) are also destructive/irreversible enough to be denied by the tool layer. When the guard denies the command, do not retry, rephrase, or route through another API path for the same outcome.

## Correct sequence
1. Separate non-destructive state gathering from destructive mutation:
   - `git status --short --branch`
   - `git diff --stat origin/master...HEAD`
   - conflict marker scan / `git diff --check`
   - local validation commands
   - GitHub PR/API read-only inventory
2. If a PR restack needs a force-push, make the push step explicit and use `--force-with-lease` with the current remote head SHA. Ask for permission on that single mutation before running it; do not bundle force-push with PR retarget, merge, cleanup, or REST/Python API mutations in the same command. A broad chat message such as "I approve" may not satisfy the tool-layer guard; use the tool's explicit approval path when available and keep the command auditable.
3. If Hermes blocks the force-push:
   - stop that specific mutation immediately;
   - report exactly which mutation was blocked and which local artifact is ready;
   - preserve the handoff with worktree path, local branch, candidate SHA, old remote SHA, PR head ref, validation output, and the next exact command class that needs approval;
   - do not proceed to retarget, CI polling, or merge, because they depend on the pushed head.
4. If the user says there is no visible approval option or approvals are blocking every session, treat that as a Hermes setup problem instead of repeatedly asking for approval. In a Hermes troubleshooting pass, verify the live active profile/config and approval mode first. If the user explicitly wants unblock-now behavior, set the approval mode to off/false through the supported Hermes config path, then verify the previously blocked single command succeeds. Keep hardline/destructive command safeguards intact and continue using auditable `--force-with-lease`/retarget/merge boundaries.
5. If only remote/local cleanup deletion is blocked after a merge, defer cleanup and continue non-deletion PR processing when the user's current instruction is to keep merging. Do not let cleanup become a false precondition for independent non-destructive work.

## Handoff fields
Include:
- PR number and title/ref.
- Worktree absolute path and local branch.
- Candidate head SHA and old remote head SHA.
- Validation command and real pass/fail summary.
- Whether base retarget, exact-head `pull_request` CI, and merge have happened.
- Deferred cleanup items, clearly labeled as blocked by guard.

## Pitfall
A prior user authorization in chat does not prove the tool-layer guard will allow the command. The guard result is authoritative for that tool call. Stop on denial.