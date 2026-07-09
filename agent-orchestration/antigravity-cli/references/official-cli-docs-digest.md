# Antigravity CLI official docs digest

Read on: 2026-06-17
Source root: `https://antigravity.google/assets/docs/cli/`
Entry page: `https://antigravity.google/docs/cli-overview`

## Pages read

1. `cli-overview.md` — CLI overview, shared agent harness, settings sync, conversation export.
2. `cli-getting-started.md` — install path, first launch, workspace trust, first task.
3. `cli-install.md` — install scripts, install flags, keyring/browser auth, SSH OAuth URL+code, `/logout`.
4. `cli-tutorial.md` — create demo project, launch `agy`, generate code, review artifact, run verification, exit.
5. `cli-using.md` — settings file, `/config`, overrides, quick tips, keybindings.
6. `cli-features.md` — plugins, terminal sandbox, slash commands, settings, subagents, `/agents`.
7. `gcli-migration.md` — `agy plugin import gemini`, context/rules, skills path migration, MCP `serverUrl` schema.
8. `cli-prompting.md` — prompt box, `Esc`, multiline input, `$EDITOR`, media paste.
9. `cli-artifacts.md` — artifact picker/detail viewer, approval/rejection, line comments, Mermaid rendering.
10. `cli-conversations.md` — cwd-scoped histories, `/resume`, desktop import, `--continue`, `--conversation`, `/fork` limitations.
11. `cli-subagents.md` — async subagents/background tasks, `/agents`, `/tasks`, detail view, approval shortcuts.
12. `cli-permissions.md` — permission resource schema, deny/ask/allow precedence, action types, defaults, examples.
13. `cli-sandbox.md` — native OS sandboxing, `enableTerminalSandbox`, sandbox approval choices.
14. `cli-settings.md` — `settings.json`, command-line overrides, alt-screen/inline modes, keybindings.
15. `cli-credits.md` — credits/quota statusline, `/credits`, Use G1 Credits setting.
16. `cli-plugins.md` — plugin layout, plugin commands, `.agents/skills`, global skills, hooks, MCP config.
17. `cli-statusline.md` — `/statusline`, statusLine command scripts, JSON state fields including subagents/background tasks.
18. `cli-title.md` — `/title`, title command scripts, JSON state payload.
19. `cli-best-practices.md` — verification loops, explore-plan-execute, `@` paths, media, AGENTS/GEMINI rules, permissions, `/rewind`, `/fork`, `agy -p`, parallel subagents.
20. `cli-troubleshooting.md` — PATH, keyring, clipboard forwarding, updater locks/failures.
21. `cli-reference.md` — slash commands, default keybindings, configuration keys.

## High-value facts for Hermes orchestration

- The command is `agy`; the CLI is a keyboard-driven TUI sharing Antigravity's agent harness.
- Official install path on macOS/Linux: `~/.local/bin/agy`.
- Print mode: `agy -p "..."` / `agy --print "..."` for non-interactive one-shot work. Official best-practice example shows `agy -p "Review this git diff and draft a conventional commit message" --cwd $(pwd)`.
- Local binary checked on 2026-06-17 exposed `--print`, `--print-timeout`, `--prompt-interactive`, `--continue`, `--conversation`, `--sandbox`, `--dangerously-skip-permissions`, but did not list `--cwd`. Use Hermes `workdir` unless `agy --help` confirms `--cwd`.
- TUI sessions should be run under tmux for orchestration and capture.
- Conversations are scoped to current working directory. `/fork` clones conversation history only; it does not isolate git files.
- `AGENTS.md` and `GEMINI.md` at workspace root are parsed as codebase rule files. Global developer context may live at `~/.gemini/GEMINI.md`.
- Local workspace Antigravity skills live in `.agents/skills/*.md`; global skills live in `~/.gemini/antigravity-cli/skills/`.
- Plugins live under `~/.gemini/antigravity-cli/plugins/<plugin_name>/` and may contain `plugin.json`, `mcp_config.json`, `hooks.json`, `skills/`, `agents/`, `rules/`.
- MCP global config: `~/.gemini/antigravity-cli/mcp_config.json`; workspace local config: `.agents/mcp_config.json`; remote MCP uses `serverUrl`, not legacy `url` or `httpUrl`.
- Settings path: `~/.gemini/antigravity-cli/settings.json`; keybindings path: `~/.gemini/antigravity-cli/keybindings.json`.
- Important settings: `toolPermission`, `artifactReviewPolicy`, `allowNonWorkspaceAccess`, `enableTerminalSandbox`, `notifications`, `verbosity`, `altScreenMode`.
- Permission resources are `action(target)`: `read_file`, `write_file`, `read_url`, `execute_url`, `command`, `unsandboxed`, `mcp`.
- Permission precedence: `deny > ask > allow`; workspace read/write auto-allowed; web/MCP/commands/non-workspace default to Ask.
- Sandbox backends: Linux `nsjail`, macOS `sandbox-exec`, Windows `AppContainer`.
- Artifact review is explicit: `Ctrl+R` opens review panel, `p` preview, `Enter` open, `y` approve, `n` reject, `Shift+A` approve all, `Esc` returns.
- Subagent/task monitoring: `/agents` for agent hierarchy, `/tasks` for background shell tasks; statusline JSON includes `subagents`, `background_tasks`, `tool_confirmation_pending`.
- Approval shortcuts: official reference table uses `Alt+J` for teleport to pending subagent confirmation and `Ctrl+K` for fast approve. The subagents page has a heading typo saying `Ctrl+J` for teleport, while its body says `Alt+J`.
- Recovery: `Esc` halts active turn/closes panels; `/rewind` or `/undo` rolls back conversation history; `/clear` resets context; `/resume`, `agy --continue`, and `agy --conversation <uuid>` resume.
- Multiline prompt input: `Shift+Enter`, `Ctrl+J`, Apple Terminal `Option+Enter` with Meta enabled, or trailing `\` + Enter.
- Troubleshooting: PATH issues, keyring authorization, SSH clipboard/media forwarding, and updater locks are common blockers.

## Best-practice distillation

1. Establish a local verification loop before asking for code changes.
2. Use explore -> plan -> execute -> validate, especially for complex edits.
3. Include target file paths with `@` path completion or explicit absolute paths.
4. Put durable codebase constraints in `AGENTS.md` or `GEMINI.md`.
5. Prefer `proceed-in-sandbox` + `enableTerminalSandbox` for autonomous runs.
6. Use print mode for automation; use tmux TUI for artifact/subagent/manual approval workflows.
7. Use git worktrees for filesystem isolation; do not confuse `/fork` with worktree isolation.
8. Parent orchestrator must inspect diffs and rerun validation outside Antigravity.
