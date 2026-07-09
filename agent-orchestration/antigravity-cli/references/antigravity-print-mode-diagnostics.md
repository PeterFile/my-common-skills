# Antigravity print-mode diagnostics from SkyTurn UI delegation

Context: Hermes parent delegated UI work to Antigravity CLI in a dirty single implementation worktree while Codex owned backend/contracts. One Antigravity print run timed out without stdout; log inspection showed the prompt was effectively mis-delivered (`promptLength=15`) when using `agy --sandbox --print ... "$(cat prompt.md)"` with awkward flag ordering.

## Reliable launch pattern

Use the short print flag and put the expanded prompt immediately after it. Do not add `--print-timeout` from Hermes prompts; the parent agent should monitor progress instead of assigning an arbitrary duration to a child-agent task:

```bash
agy -p "$(cat /tmp/task-prompt.md)" --sandbox
```

Run as a managed background process from Hermes for long UI jobs:

```text
terminal(command='agy -p "$(cat /tmp/task-prompt.md)" --sandbox', workdir='<repo>', background=true, notify_on_complete=true)
```

If the installed `agy` still exits due to its implicit print-mode timeout and the task is unknown-duration implementation work, relaunch in interactive TUI/tmux mode rather than increasing a print timeout.

## Diagnostic loop

1. Find the newest log: `~/.gemini/antigravity-cli/log/cli-*.log`.
2. Check early lines for prompt delivery and auth:
   - `Print mode: starting (promptLength=...)` should be plausibly large for a full task prompt.
   - `Forwarding user message` confirms the prompt entered the conversation.
3. Check progress lines:
   - `streamGenerateContent` means the model is responding.
   - `tool_confirmation ... Bash` means it is executing commands.
   - new `git diff --name-only` output confirms actual file writes.
4. If model capacity errors appear, wait only while log lines keep advancing. If logs stop for several minutes and file diffs/tests stop changing, treat as stalled.
5. If print mode times out after writing files, do not trust the missing final summary. Parent must inspect `git diff`, run targeted tests, and either accept the partial diff or launch a narrow cleanup run.

## Delivery lesson

For architect-delegated sessions, Antigravity partial output can still be useful but is not completion evidence. The parent should keep responsibility for diff review, style cleanup, and final verification gates.