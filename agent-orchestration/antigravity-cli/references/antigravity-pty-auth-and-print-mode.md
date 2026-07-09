# Antigravity CLI PTY auth and print-mode recovery

Use this when `agy -p` automation behaves differently between Hermes terminal modes, especially on macOS.

## Durable pattern

- `agy` authentication may be available through OS keyring only when launched with a PTY. A non-PTY background print-mode launch can still print an OAuth URL and time out even after the user has logged in elsewhere.
- Before launching long write lanes, run a tiny PTY auth probe from the same Hermes session and user account:

```bash
agy -p "auth probe: reply OK only"
```

Run it with Hermes `terminal(..., pty=true)`. If it returns `OK`, launch the real `agy -p` lane with `pty=true` as well.

## Launch guidance

For bounded write lanes where print mode is still desired:

```python
terminal(
  command='agy -p "$(cat /tmp/prompt.txt)" 2>&1 | tee /tmp/lane.agy.log',
  workdir='/path/to/worktree',
  background=True,
  notify_on_complete=True,
  pty=True,
)
```

Do not assume a successful desktop Antigravity login means non-PTY CLI automation is authenticated. Verify with the auth probe.

## Recovery when print mode times out after writing files

If the process prints `Error: timed out waiting for response` or exits without a useful final summary:

1. Kill or stop the stale `agy` process if it is still running.
2. Inspect the real `git status`, `git diff --name-only`, and `git diff --stat` in the worktree.
3. Parent-run validation outside Antigravity.
4. If validation passes, run an independent review-only agent or manual review before committing.
5. If validation fails, repair the diff in the same worktree or restart a scoped `agy` run; never trust the partial child summary.

## Notes

- In macOS git worktrees, `agy` logs may warn that the git event watcher cannot handle `worktreeconfig`. Treat that as a watcher limitation, not evidence that file edits failed; use parent `git diff` as source of truth.
- When multiple `agy` launches race for OAuth, serialize them. First prove one PTY auth probe works, then launch write lanes. If one lane still prompts for OAuth, stop that lane rather than letting it burn timeout while another writes files.
