---
name: antigravity-cli
description: "Delegate coding, review, research, and validation work to Google Antigravity CLI (`agy`) and its subagents."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Antigravity, Google, Subagents, PTY, Automation, Code-Review]
    related_skills: [autonomous-coding-agents, codex, claude-code, hermes-agent]
    official_docs: https://antigravity.google/docs/cli-overview
    docs_read_at: "2026-06-17"
---

# Antigravity CLI (`agy`) — Hermes Orchestration Guide

Use this when Hermes should delegate bounded work to Google Antigravity CLI. The executable is `agy`. Treat it like Codex/Claude Code: useful as a child coding agent, but Hermes remains responsible for scope, diff review, and validation.

Official docs covered for this skill: all Markdown pages under `https://antigravity.google/assets/docs/cli/` as of 2026-06-17. See `references/official-cli-docs-digest.md` for the page list and extracted facts.

## When to use

- Repository investigation, code review, implementation, refactoring, or test-writing where an autonomous coding agent helps.
- A long multi-file task that benefits from Antigravity artifacts, plans, background tasks, or subagents.
- Parallel read-only sweeps or independent worktree lanes.
- Remote/SSH or tmux-first workflows where a lightweight TUI is better than a desktop IDE.

Do **not** use it as proof of completion. Its summaries and artifacts are evidence to inspect, not final verification.

## Prerequisites

1. Check availability and the local flag surface first:
   ```bash
   command -v agy && agy --help
   ```
2. Install if missing:
   - macOS/Linux: `curl -fsSL https://antigravity.google/cli/install.sh | bash`
   - Windows PowerShell: `irm https://antigravity.google/cli/install.ps1 | iex`
   - Windows CMD: `curl -fsSL https://antigravity.google/cli/install.cmd -o install.cmd && install.cmd && del install.cmd`
3. Authentication uses the OS keyring when possible. First launch may open a browser; SSH sessions use a printed URL + code loop.
4. Run inside the intended project directory. Antigravity scopes conversations to the current working directory.
5. For code changes, start from a clean git status and usually an isolated branch/worktree.

## Mode selection

### Mode 1 — Print mode (`-p` / `--print`): preferred for automation

Use for one-shot review, bounded implementation, or validation tasks. It exits and returns text, so Hermes can capture output directly.

```python
terminal(
  command="agy -p 'Review the current git diff for correctness and list only actionable bugs. Do not edit files.'",
  workdir="/path/to/repo",
  timeout=600,
)
```

For write tasks with unknown duration, prefer the interactive tmux/TUI mode below. If print mode is still appropriate, give explicit scope and validation but do **not** add `--print-timeout`; Hermes should monitor the background process, Antigravity logs, file diffs, and validation progress instead of imposing an arbitrary child-agent deadline:

```python
terminal(
  command="agy -p 'Implement the smallest fix for the failing parser test. Do not commit. Run npm test -- parser.test.ts and report changed files plus exact test output.' --sandbox",
  workdir="/path/to/repo",
  background=True,
  notify_on_complete=True,
)
```

Notes:
- Prefer Hermes `workdir` over relying on `agy --cwd`. Official docs show `--cwd`, but the local `agy --help` checked on 2026-06-17 did **not** list it. Verify before using any flag in automation.
- For print mode, prefer the short flag form with the prompt immediately after `-p`: `agy -p "$(cat /tmp/prompt.md)" --sandbox`. In Hermes shell wrapping, `agy --sandbox --print "$(cat file)"` can mis-deliver or truncate the prompt because flag parsing and shell quoting interact poorly; verify prompt delivery in the CLI log before waiting a long time.
- Do **not** add `--print-timeout` in Hermes subagent launches. A fixed child-agent timeout can kill useful long-running work while it is still making progress. The parent agent must monitor progress with `process.poll`, newest `~/.gemini/antigravity-cli/log/cli-*.log`, `git diff --stat`, and test output, then decide whether to keep waiting, steer, or kill.
- If the installed `agy` enforces an implicit print-mode timeout and the task is not bounded enough to fit it, switch to Mode 2 interactive TUI/tmux instead of raising the timeout.
- Use `background=true, notify_on_complete=true` for bounded tasks exceeding Hermes foreground limits.

### Mode 2 — Interactive TUI in tmux: preferred for multi-turn work

Use tmux for long interactive sessions, artifact review, permission prompts, `/agents`, `/tasks`, and follow-up steering.

```python
terminal(command="tmux new-session -d -s agy-feature -x 140 -y 40", timeout=10)
terminal(command="tmux send-keys -t agy-feature 'cd /path/to/repo && agy --sandbox' Enter", timeout=10)
terminal(command="sleep 5 && tmux capture-pane -t agy-feature -p -S -80", timeout=10)
terminal(command="tmux send-keys -t agy-feature 'Explore, plan, then implement the smallest safe fix for <task>. Do not commit or push. Run <test command> and summarize changed files.' Enter", timeout=10)
terminal(command="sleep 30 && tmux capture-pane -t agy-feature -p -S -120", timeout=10)
```

Keep polling with `tmux capture-pane`. If the TUI asks for trust, permission, or artifact approval, inspect the visible prompt before sending `y`, `n`, `Enter`, or `Esc`.

### Mode 3 — Antigravity subagents inside the TUI

Ask Antigravity’s primary agent to spawn subagents for independent lanes:

```text
Use parallel subagents only for independent read-only investigation first:
1. @subagent A: inspect API boundary and list candidate files.
2. @subagent B: inspect tests and reproduce command.
3. @subagent C: inspect docs/config constraints.
Do not write files until the parent presents a consolidated plan.
After plan approval, make the smallest edit and run the named validation.
```

Monitor:
- `/agents` — opens Agent Manager for active/completed/killed/error subagents.
- `/tasks` — tracks background shell tasks and stdout logs.
- `Alt+J` — teleports to the next subagent awaiting confirmation (the official subagents page heading says `Ctrl+J`, but the body and reference table specify `Alt+J`).
- `Ctrl+K` — fast-approves the pending subagent action shown in the status alert. Use only when the action is clearly safe and in scope.

## Safe delegation workflow

1. **Verify live state before launch**
   ```bash
   git status --short
   git branch --show-current
   git rev-parse --show-toplevel
   ```
   Also identify the required test/build command and any project rules. `AGENTS.md` and `GEMINI.md` are automatically parsed by Antigravity when present.

2. **Isolate write work**
   - Use a separate git branch/worktree for implementation lanes.
   - Do not run multiple write-enabled `agy` agents in the same dirty tree.
   - `/fork` clones the conversation thread, **not** the filesystem checkout. It is not a substitute for git worktrees.

3. **Prompt with phases**
   - Explore first: locate interfaces and explain current behavior.
   - Plan second: list files, intended edits, tests, and non-goals.
   - Execute only after the plan is bounded.
   - Validate with the cheapest command that catches the likely failure.

4. **Review artifacts and diffs**
   - `Ctrl+R` opens the Artifact Review panel when `/artifact to review` appears.
   - Use `p` preview, `Enter` open, `y` approve, `n` reject, `Shift+A` approve all only after inspection.
   - Use `/diff` or external `git diff` before trusting edits.

5. **Parent verifies**
   After Antigravity exits or reports done, Hermes must inspect:
   ```bash
   git status --short
   git diff --check
   git diff --stat
   ```
   Then run the relevant tests/build outside the child agent. Do not report success from the child summary alone.

## Prompt template

```text
You are an Antigravity CLI subagent working in: <absolute repo path>

Task: <one concrete task>

Hard constraints:
- Keep the change minimal; preserve existing behavior except for the requested fix.
- Do not commit, push, open PRs, change credentials, buy credits, or edit global settings.
- Stay inside this repo/worktree unless explicitly told otherwise.
- Read AGENTS.md/GEMINI.md and follow project rules.
- If required context is missing, stop and report the specific blocker.

Required phases:
1. Explore: identify relevant files and current behavior; no writes.
2. Plan: list exact intended files, tests, and non-goals.
3. Execute: apply the smallest edit.
4. Validate: run <exact test/build command>.

Final output format:
STATUS: done | blocked | partial
CHANGED FILES: <paths>
VALIDATION: <commands and exact result>
RISKS: <remaining uncertainty>
NEXT: <only if blocked or partial>
```

## Permissions and sandbox policy

Antigravity settings live at:

```text
~/.gemini/antigravity-cli/settings.json
```

Use command-line overrides for a session when possible; avoid mutating global settings unless the user asked.

Recommended bounded automation profile:

```json
{
  "toolPermission": "proceed-in-sandbox",
  "enableTerminalSandbox": true,
  "permissions": {
    "deny": [
      "command(rm -rf)",
      "command(sudo)",
      "write_file(.git/)",
      "write_file(/home/user/.ssh)"
    ],
    "ask": ["command(*)", "execute_url(*)", "mcp(*)"]
  }
}
```

Facts from official docs:
- Permission resources use `action(target)`.
- Supported actions: `read_file`, `write_file`, `read_url`, `execute_url`, `command`, `unsandboxed`, `mcp`.
- Precedence is `deny > ask > allow`.
- Workspace file read/write is auto-allowed by default.
- Web, MCP, terminal commands, and non-workspace files default to Ask unless configured.
- Sandbox uses native isolation: Linux `nsjail`, macOS `sandbox-exec`, Windows `AppContainer`.
- `--dangerously-skip-permissions` exists in local help but should be reserved for disposable, isolated worktrees with explicit user authorization.

## Conversation and recovery commands

- `/resume` — picker for workspace-scoped conversations.
- `agy --continue` — resume the most recent session for the current workspace.
- `agy --conversation <uuid>` — resume a specific session.
- `/fork` or `/branch` — branch the conversation only; use git for file isolation.
- `/rewind` or `/undo` — roll back conversation history after a bad turn.
- `Esc` — global escape hatch; halts active turn or closes panels.
- `/clear` — clear current conversation context.
- `/logout` — purge keyring auth tokens.

On exit, preserve any resume command or conversation ID printed by `agy` if future continuation matters.

## Parallel worktree pattern

```bash
git worktree add -b agy/task-a /tmp/agy-task-a main
git worktree add -b agy/task-b /tmp/agy-task-b main
```

Then launch one `agy` print/TUI process per worktree. Require each lane to report changed files and validation output. Reconcile in the parent repo after inspecting diffs.

## Troubleshooting checklist

For a concrete print-mode timeout/misdelivered-prompt diagnostic loop, see `references/antigravity-print-mode-diagnostics.md`.
For macOS/Hermes PTY auth behavior and partial print-mode recovery, see `references/antigravity-pty-auth-and-print-mode.md`.
For the Hermes/macOS case where print mode times out reading Keychain but `--prompt-interactive` authenticates successfully, see `references/hermes-keyring-prompt-interactive.md`.

- `agy: command not found`: ensure `~/.local/bin` is on `PATH` on macOS/Linux; Windows installer adds a user-local bin path.
- Keyring prompts or failures: local launches use OS keyring; SSH uses URL + code. On macOS headless or Hermes sessions, first run a tiny `agy -p "auth probe: reply OK only"` in the same worktree and inspect the newest `~/.gemini/antigravity-cli/log/cli-*.log`. If print mode logs `keyringAuth: timed out` and triggers OAuth, do not mark Antigravity unavailable and do not switch tools silently; relaunch the same task with `agy --prompt-interactive "$(cat /tmp/task-prompt.md)" --sandbox` under Hermes PTY/background monitoring. A desktop login or previous successful run does not prove the current print-mode process can read Keychain credentials fast enough; prompt-interactive mode may still use the macOS keyring successfully when `agy -p` cannot.
- Silent or apparently hung print mode: inspect the newest `~/.gemini/antigravity-cli/log/cli-*.log` before assuming no work is happening. Useful signals include `promptLength=...`, `Forwarding user message`, `streamGenerateContent`, `tool_confirmation`, and `Print mode: timed out`. If the process writes a partial diff but stops producing log lines until timeout, kill or wait to timeout, then parent-verify the partial diff instead of trusting the missing final summary.
- Do not leave package-manager stores or other binary caches untracked inside an Antigravity worktree. For pnpm installs in isolated worktrees, prefer an external `--store-dir` (for example under `/tmp`) or remove the repo-local store before review/continuation; otherwise Antigravity may waste time trying to diff binary cache files or log non-UTF8 patch errors.
- Transient model capacity errors such as `UNAVAILABLE ... No capacity available` can recover mid-run. Wait only while the log still advances; if the log stops for several minutes and no files/tests change, treat the run as stalled.
- Transient model capacity errors such as `UNAVAILABLE ... No capacity available` can recover mid-run. Wait only while the log still advances; if the log stops for several minutes and no files/tests change, treat the run as stalled.
- Clipboard media over SSH may fail unless the terminal supports graphical clipboard forwarding; attach screenshots only when transport supports it.
- `Shift+Enter` may not work in Apple Terminal; use `Option+Enter` with “Use Option as Meta key”, `Ctrl+J`, or trailing `\` + Enter.
- If a subagent waits for approval, use `/agents`, `Alt+J`, or inspect statusline before approving.
- Print-mode timeouts can still leave useful partial diffs or a nearly complete summary file at the requested output path. Do not trust the process exit, missing final stdout, or summary alone: inspect the real `git diff`, read the summary file if present, remove any generated/untracked package-store artifacts, then parent-run validation before deciding whether to continue, switch to another coding agent, review, or discard.
- If a worktree needs dependencies before an Antigravity lane, prefer an external package store such as `CI=true pnpm install --frozen-lockfile --store-dir /tmp/<lane-store>` over a repo-local `.pnpm-store/`. Antigravity may try to diff untracked binary package-store files and log invalid-UTF8 patch errors.
- If local docs and `agy --help` disagree, trust the installed binary for automation and update this skill if the discrepancy changes.

## Common pitfalls

1. Trusting Antigravity’s final summary without inspecting `git diff` and rerunning tests.
2. Using `/fork` for parallel implementation and assuming files are isolated. They are not.
3. Enabling `always-proceed` or `--dangerously-skip-permissions` in a non-disposable tree.
4. Approving all artifacts with `Shift+A` before reading the plan/diff.
5. Letting multiple write-enabled subagents edit overlapping files.
6. Depending on undocumented or version-drifting flags like `--cwd` without checking `agy --help`.

## Verification checklist

- [ ] `agy --help` checked for the local version and required flags.
- [ ] Workdir/repo/branch/status verified before launch.
- [ ] Prompt included scope, non-goals, validation, and “do not commit/push/PR” unless authorized.
- [ ] Write work was isolated by git branch/worktree.
- [ ] Artifacts/diffs inspected by Hermes.
- [ ] Parent ran the relevant validation outside Antigravity.
- [ ] Final report includes changed paths, exact validation output, and remaining uncertainty.
