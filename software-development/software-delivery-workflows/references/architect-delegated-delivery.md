# Architect-delegated software delivery

Use this pattern when the user wants Hermes to act as architect/operator rather than direct implementer.

## Trigger signals
- The user assigns implementation lanes to specific coding agents, e.g. logic/backend to Codex and UI to Antigravity CLI.
- The user says direct Hermes edits pollute context or asks Hermes to coordinate rather than code.
- The task mixes backend/contracts/runtime and visual/UI work in one repo/worktree.

## Operating pattern
1. Stop direct file edits immediately, including in mid-turn if the user corrects the role while tools are running. If Hermes already wrote code, identify the exact touched files and ask whether to revert or keep as a draft. Revert only the Hermes-authored diff the user approves; do not touch unrelated dirty work.
2. Mark the parent task list to reflect the role change: direct implementation becomes stopped/completed only after contamination is handled; subsequent items should be delegation prompts and parent verification, not manual edits.
3. Split by responsibility, not by arbitrary file count:
   - Codex: contracts, persistence, runtime, adapters, IPC/backend APIs, tests.
   - Antigravity CLI: UI layout/copy/components, visual behavior, UI tests.
   - Hermes parent: architecture prompts, sequencing, diff review, and validation.
4. Avoid concurrent write agents in the same worktree. Run Codex first for contracts/API support, inspect its output/diff, then run the UI agent against the settled contract.
5. Parent verification is mandatory. Treat child-agent summaries as leads only; inspect `git status`, `git diff`, and run the relevant tests yourself before reporting completion.
6. If tool-call budget or timeout stops the parent before verification, report the exact verified state and remaining unverified commands. Do not claim the whole delivery is done.

## Prompt requirements for child agents
- Include absolute worktree path, branch/worktree constraint, and "do not commit/push/PR" unless explicitly authorized.
- State ownership boundaries: which files/classes are allowed and which are forbidden.
- Include product invariants and negative constraints from AGENTS.md.
- Require final output with changed files, validation commands/results, risks, and handoff notes for the next lane.

## Pitfalls
- Direct Hermes patches in an architect-only session contaminate the context and may conflict with the user's intended agent split.
- Starting UI before backend contracts are exposed causes speculative UI state and likely rework.
- Letting Codex edit UI copy/layout when the user assigned UI to Antigravity violates lane ownership even if tests pass.
- A successful child build is not a parent-validated delivery; rerun or at least explicitly label validation as child-reported until verified.
- Child agents can time out after writing useful partial diffs. Treat the diff as untrusted input: inspect it, fix only narrow contract gaps if the parent is allowed to edit, and rerun the affected package tests before continuing. For Antigravity CLI UI lanes, do not add explicit `--print-timeout`; if print mode times out after writing files, kill the stale process, inspect `git status`/`git diff`, and relaunch a narrowly scoped repair prompt instead of rerunning the whole UI task.
- `git diff --check` does not cover untracked files. For new files left by child agents, temporarily run `git add -N <path>` before `git diff --check`, then reset the index so the parent does not accidentally stage work.
- In worktree-target workflows, do not silently fall back from an uncreated candidate worktree to the project root. If `new_worktree` has only requested metadata and no real absolute worktree path, fail fast or leave the run unstarted rather than executing against the current branch.

## Parent verification additions
- After a context compaction or tool budget stop, first verify live state: active branch/worktree, dirty and untracked files, background processes, and whether child agents are still running.
- Review the diff for product-boundary regressions, not just test pass/fail: renderer must not gain git/fs/shell/SQLite execution, contract-only packages must stay pure, and prose output must not become evidence truth.
- When the final requirement includes a fixed command list, rerun that exact list after the last parent fix; earlier green child or pre-fix runs are not final evidence.