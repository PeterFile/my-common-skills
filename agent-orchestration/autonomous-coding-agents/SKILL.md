---
name: autonomous-coding-agents
description: "Use when delegating coding work to Codex CLI, Claude Code, OpenCode, Hermes subagents, or a Kanban implementation lane."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [autonomous-agents, codex, claude-code, opencode, delegation, kanban]
    related_skills: [subagent-driven-development]
---

# Autonomous Coding Agents

## Overview
Use this umbrella when another agent or agent CLI should implement, review, or investigate code. Hermes remains accountable for scope, reconciliation, and verification. Child agent summaries are not proof of completion.

## When to Use
- Delegating to Codex CLI, Claude Code, OpenCode, or `delegate_task`.
- Running an isolated implementation lane from a Kanban worker.
- Parallelizing independent code tasks.

## Shared Delegation Pattern
1. Verify live state before launching: repo path/branch/status, recent commits, open PR stack, worktrees, and required status sinks such as Slack/Linear when the user requires them.
2. Use planning/review agents first to define scoreable route goals: checklist, file scope, non-goals, fastest validation, PR size cap, score rubric, and first-feedback timebox.
3. Write a self-contained prompt with repo path, branch rules, files, acceptance criteria, tests, constraints, and “do not commit/push/PR/post status” unless explicitly authorized.
4. Use isolation such as a separate worktree, branch, or session. For large Codex clusters, do not let Hermes delegate concurrency cap the swarm size; use delegates for synthesis/review and many isolated Codex CLI worktrees for implementation.
5. Require verifiable outputs such as changed paths, test output, commit hash, PR URL, or a lane output file.
6. Inspect diff and run tests yourself.
   - Match review scope to the actual artifact state. If the worker's changes are still uncommitted, tell review-only agents to inspect `git diff`/`git diff --stat`, not `<base>..HEAD`; if the review prompt is based on `<base>..HEAD`, commit the candidate first or the reviewer will correctly see an empty PR diff.
   - For stacked PRs, review and validate against the intended stack base (`parent-branch..HEAD`), not always `origin/main..HEAD`.
   - If review-only returns `BLOCK`, do not launch dependent implementation worktrees. Feed the exact findings back to the responsible worker, rerun the focused package tests/typechecks, then rerun review-only on the same slice before stacking downstream branches.
7. Reconcile only intended changes.
   - When two otherwise independent slices both need the same narrow public contract/type file, stack the later slice on the earlier one before opening PRs. This keeps the PR diff honest and avoids two parallel PRs racing on the same hot file.
8. Keep transient progress in Slack/Linear/controller systems. Update existing durable markdown only when project/product/API/runtime semantics change; avoid creating progress-log documents.

For larger Codex swarms with stacked worktrees, use `references/codex-worktree-cluster-delivery.md`. In that mode, do not cap the implementation swarm at Hermes delegate concurrency; use delegates for planning/review synthesis and many isolated Codex CLI worktrees for implementation, each with scoreable goals, PR size caps, and parent-run validation. Before launching a write-enabled swarm, use `references/dense-swarm-preflight-and-stack-governance.md` to verify required status sinks, detect oversized remote PR-stack backlog, and decide whether to freeze/cluster existing PRs instead of opening more work. When resuming or closing out a budget-interrupted swarm, also use `references/dense-cluster-continuation-closeout.md` for the handoff-verification, UI-details, path-overlap, and Slack/Linear closeout checklist.

For agent-first workflow optimization, use `references/harness-engineering-agent-workflows.md`: prioritize application/observability legibility, repo-local knowledge as system of record, mechanical architecture constraints, and recurring cleanup lanes before simply increasing agent count.

## Agent-Specific Notes

The legacy standalone CLI skills were consolidated into this umbrella. Keep class-level instructions here, and keep detailed provider manuals as references:

- `references/codex-cli-legacy.md`
- `references/claude-code-cli-legacy.md`
- `references/opencode-cli-legacy.md`

### Codex CLI
Best for code edits, refactors, PR review, and batch issue fixing in a git repo. Provide exact working directory and test commands.

Hermes defaults:
- Use `pty=true`; Codex is interactive and can hang without a PTY.
- Codex refuses to run outside a git repo. For scratch tasks, create a temp directory and `git init` before launch.
- The standalone CLI may use `~/.codex/auth.json`; a missing `OPENAI_API_KEY` alone does not prove auth is missing.
- In Hermes gateway/service contexts, workspace-write sandboxing can fail with bubblewrap/user-namespace errors. Prefer `--sandbox danger-full-access` only inside a clean, scoped worktree, then inspect diffs and run tests yourself.
- Check current flag scope with `codex exec --help`; approval-policy flags can move between top-level and subcommand positions.
- For merge conflicts, poll for real progress (`git status`, conflict marker count, changed files). If logs repeat the same hunk across polls, stop the worker and resolve deterministically.
- Treat late/background completion as new evidence only after inspecting the worktree and running the exact gates.

Pitfall: on codex-cli 0.136.0, `codex exec` may reject `-a never` / `--ask-for-approval never` even though help text lists the flag. For non-interactive worktree agents, use `codex exec -C <worktree> -s workspace-write -o <summary-file> < prompt.txt` unless the installed version is verified to accept approval flags.

### Claude Code
Good for larger feature implementation or repository-scale reasoning. Keep deliverables bounded.

Hermes defaults:
- Prefer print mode for one-shot automation: `claude -p "<task>" --max-turns N`.
- Use tmux for interactive sessions so Hermes can `send-keys` and `capture-pane` reliably.
- Workspace trust usually accepts with Enter, but the `--dangerously-skip-permissions` warning defaults to "No, exit"; send Down then Enter only when permission bypass is deliberately chosen.
- Use `--max-turns`, `--max-budget-usd`, and `--allowedTools` in print mode to bound cost and scope.
- Clean up tmux sessions after completion.

### OpenCode
Use for implementation and PR review, but verify its summary through diffs and tests.

Hermes defaults:
- Prefer `opencode run "<task>"` for bounded automation; it does not need PTY.
- Use background TUI sessions only for iterative work, with `pty=true`.
- `/exit` is not a valid OpenCode exit command and opens an agent selector. Exit with Ctrl+C (`\x03`) or kill the process.
- PATH mismatches can select a different OpenCode binary. Check `which -a opencode` and `opencode --version`; pin `$HOME/.opencode/bin/opencode` if needed.
- Avoid sharing one working directory across parallel OpenCode sessions.

### Antigravity CLI (`agy`)
Use for UI-focused implementation when the user prefers it or when renderer/UI changes are the task. Keep the prompt narrow and make Hermes verify the resulting diff.

Hermes defaults:
- Launch `agy` in the intended isolated worktree and capture output with `tee`; unset provider/base-url environment variables if the task requires the default configured route.
- `agy --prompt-interactive` requires the prompt as an argument; do not pipe the prompt on stdin to that flag. For one-shot UI work, prefer `agy --print "$(cat prompt.txt)"` or pass the prompt string directly to `--prompt-interactive`.
- `agy` may emit little or no stdout, time out waiting for response, or leave helper/PTY noise such as `tcsetattr: Inappropriate ioctl for device` after it has already written a useful diff. Treat this like any hung child agent: inspect `git status --short`, `git diff --stat`, and untracked intended files, run parent-side tests, and kill the stuck process only after preserving the artifact.
- For UI-only slices, explicitly forbid backend/Electron/Node edits in the prompt; if `agy` still touches only the intended UI files and validation passes, the lack of a clean agent exit is not itself a blocker.
- If a small UI fix is mechanical but the user mandated `agy`, use a tiny prompt for that exact edit, then verify with the relevant test/typecheck/diff-check rather than hand-editing.
- When an agent edits or renames tests, compare total test counts and diff stats against the previous validated run. A green run with fewer tests is a blocker: restore the original suite and append the new assertions rather than accepting a replacement.

### Kanban Lane
A worker may run a coding CLI, but the worker still owns lifecycle, acceptance checks, and reconciliation.

## Common Pitfalls
1. Delegating without enough context.
2. Letting child agents commit, push, or merge outside scope.
3. Trusting a child agent's test claim without output.
4. Mixing multiple agents in one dirty tree.
5. Continuing to plan or launch a swarm after the user narrows scope to open-PR closeout. Stop new development, cancel pending implementation lanes, verify the live PR stack, and drain/merge only already-open work that has fresh exact-head/base CI.
6. Hand-editing product code after the user explicitly says coding agents should write code. In that mode, keep Hermes as parent/operator: write prompts, inspect diffs, run validations, and rerun review-only agents; delegate each code fix back to the coding agent unless the user changes the instruction.
7. Treating a hung/timeout child-agent process as equivalent to no work. Some agent CLIs can apply a valid diff before their stdout or MCP helper process hangs. If the process stops producing output, inspect the worktree and output file, run parent-side validation, and kill the stuck process only after preserving the diff state. Conversely, do not treat a child-agent timeout as success without diff/test evidence. If a timed-out TDD-oriented child leaves only failing tests or contract assertions with no production implementation, treat that as an incomplete red phase: either finish the smallest production implementation yourself or send the exact failing test diff back to a worker; do not report the slice as implemented. If validation failure belongs to an upstream/base slice rather than the child slice, fix and validate the base slice first, commit that base fix, then merge it into the stacked child worktree before continuing.
8. Reacting to stale background process notifications as fresh blockers. Hermes can deliver `process.kill`/SIGTERM notices for earlier agent runs after their diffs were already validated, committed, or superseded. Reconcile the process id and prompt/output path against the current active lane and git state before acting. If the killed process was intentionally terminated after preserving/validating its diff, state that it is non-blocking and continue the current lane; do not restart or rework the stale task.
9. Treating repeated review-only `BLOCK` results as churn rather than signal. For contract/kernel slices, keep the dependency graph stopped, feed each exact finding back to the owning implementation agent, rerun the focused tests/typechecks, and require a fresh review-only `APPROVE` before creating stacked downstream worktrees.

## Verification Checklist
- [ ] Prompt included context and acceptance criteria.
- [ ] Agent returned verifiable handles.
- [ ] Parent inspected diff and ran tests.
