# Hermes macOS keyring auth: prefer prompt-interactive when print mode times out

Context: In a SkyTurn multi-worktree delivery session, `agy -p "$(cat prompt)" --sandbox` and a tiny `agy -p 'auth probe...'` both printed an OAuth URL and timed out. The newest `~/.gemini/antigravity-cli/log/cli-*.log` showed `keyringAuth: timed out after 5s, skipping keyring auth` followed by `silent auth failed, triggering OAuth`.

The same environment successfully authenticated with:

```bash
agy --prompt-interactive "$(cat /tmp/task-prompt.md)" --sandbox
```

The log then showed `ChainedAuth: authenticated via keyring` and `Forwarding user message`.

## Durable lesson

For Hermes-launched macOS Antigravity tasks, a working desktop login or past successful print-mode run does not prove the current non-interactive print process can read Keychain fast enough. If print mode shows OAuth/keyring timeout, do not treat Antigravity as unavailable and do not silently switch tools. Relaunch the same task with `--prompt-interactive` in a PTY/background process, monitor logs and `git diff`, and kill only after the agent reports done or progress stops.

## Minimal diagnostic loop

1. Start a tiny probe in the same worktree:
   ```bash
   agy -p 'auth probe: reply OK only; do not use tools'
   ```
2. Inspect the newest Antigravity log for either:
   - success: `ChainedAuth: authenticated via keyring`, `Forwarding user message`; or
   - failure: `keyringAuth: timed out`, `silent auth failed, triggering OAuth`.
3. If print mode fails but auth exists historically, relaunch as:
   ```bash
   agy --prompt-interactive "$(cat /tmp/task-prompt.md)" --sandbox
   ```
4. Parent agent still owns verification: inspect `git diff`, run targeted tests/typecheck/build, and ignore Antigravity's summary as sole proof.

## Cleanup pitfall

When reusing dependencies in isolated pnpm worktrees, temporary `node_modules` symlinks are useful for validation but must be removed before commit/PR. They are local verification scaffolding, not project changes.