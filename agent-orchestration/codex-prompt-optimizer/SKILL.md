---
name: codex-prompt-optimizer
description: Use when drafting, rewriting, or launching prompts for OpenAI Codex/Codex CLI. Converts a user request into an outcome-first, scoped, verifiable Codex prompt with explicit constraints, validation, and stopping conditions.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [codex, prompt-engineering, coding-agent, validation, agentic-workflows]
    related_skills: [codex, hermes-agent]
---

# Codex Prompt Optimizer

## Overview

Use this skill to turn a human request into a high-signal prompt for OpenAI Codex or Codex CLI. The goal is not to make prompts longer. The goal is to make them easier for Codex to execute correctly: outcome-first, scoped, grounded in real repo facts, and verifiable.

Source guidance distilled from OpenAI Prompt guidance for GPT-5.5 and Codex prompting docs:

- Prefer shorter, outcome-first prompts over process-heavy prompt stacks.
- Define what good looks like: target outcome, success criteria, constraints, available evidence, final response shape.
- Avoid unnecessary `always` / `never` / `must` rules unless they are true invariants.
- Give Codex enough context and exact validation commands when possible.
- Break complex work into focused tasks; smaller changes are easier to test and review.
- Add explicit stopping conditions and missing-evidence behavior.
- Ask Codex to verify its work with the cheapest relevant check.

## When to Use

Use when:

- The user asks to “use Codex”, “让 Codex 做”, “spawn Codex”, “codex exec”, or “write a prompt for Codex”.
- You are delegating implementation, bug fixing, refactoring, test writing, PR review, or repo exploration to Codex.
- A prior Codex run failed because the prompt was vague, too broad, over-prescribed, lacked validation, or let Codex change unrelated files.
- You need a bounded review-only prompt after code changes are already made.

Do not use for:

- Direct answers that do not involve Codex.
- Tasks where the correct action is to inspect or edit files yourself instead of delegating.
- Broad planning where no repository, artifact, or acceptance criteria exist yet; ask for the smallest missing decision first.

## Prompt Construction Rules

### 1. Inspect real context before writing the prompt

Do not invent repo facts. Before launching Codex, gather only the context needed for the task:

- repo root and target workdir
- branch/worktree state
- relevant files, failing tests, issue/PR numbers, or error output
- package manager and known validation commands, if discoverable
- user constraints: scope, non-goals, style, compatibility, rollout risk

If a fact is missing but not critical, write the prompt with an explicit assumption. If the missing fact changes risk or target behavior, ask one narrow clarification question before launching.

### 2. Lead with the outcome, not a script

Good Codex prompts state the destination and let Codex choose the efficient path.

Prefer:

```text
Fix the regression where <behavior>. Success means <observable behavior>, with no unrelated UI/API changes. Inspect the relevant code and implement the smallest correct fix. Run <focused validation>. If validation cannot run, report the blocker and the next best check.
```

Avoid:

```text
First open A, then open B, then compare every function, then think through all exceptions, then edit C, then run every possible test...
```

Use strict words (`must`, `never`, `only`) only for real invariants: safety, file scope, output schema, backwards compatibility, and destructive/production limits.

### 3. Include scope and non-goals

Tell Codex what it may change and what it must preserve.

Include when relevant:

- Allowed files/packages.
- Files or behavior explicitly out of scope.
- Compatibility requirements: “preserve public API”, “do not change persisted schema”, “do not break userspace”.
- Product constraints: copy tone, UI behavior, accessibility, responsive behavior.
- Security constraints: no credentials, no production writes, least privilege.

### 4. Include validation and stopping conditions

Every implementation prompt should tell Codex how to prove the change.

Validation hierarchy:

1. targeted unit/integration tests for changed behavior
2. typecheck/lint for affected package
3. focused build for affected target
4. minimal smoke test
5. if none can run, explain why and name the next best check

Stopping conditions:

- Stop once the core request is implemented and the cheapest relevant validation passes.
- Do not broaden the task to opportunistic refactors.
- If blocked by missing credentials, unavailable services, flaky infra, or destructive/production risk, stop and report the blocker instead of guessing.
- If the prompt is review-only, do not edit files and do not run broad/slow tests unless explicitly requested.

### 5. Make the final report auditable

Ask Codex to finish with a compact report containing:

- files changed
- behavior changed
- validation run and result
- remaining risks/blockers
- commit hash, if it committed

Do not ask for long reasoning transcripts. They waste context and make review harder.

## Standard Prompt Template

Use this as the default shape. Fill only sections that matter.

```text
Task: <one-sentence outcome>

Context:
- Workdir/repo: <path or repo name>
- Current state: <branch/worktree/status if relevant>
- Relevant files/errors/issues: <concise bullets>

Success criteria:
- <observable requirement 1>
- <observable requirement 2>
- <backwards compatibility / UX / API invariant>

Constraints:
- Make the smallest correct change.
- Preserve existing behavior unless needed for the task.
- Do not change <out-of-scope files/behavior>.
- Do not use credentials or perform production/destructive actions.

Validation:
- Run: <exact focused command if known>
- Also run <typecheck/lint/build> if directly affected and cheap.
- If a validation cannot run, report why and the next best check.

Final response:
- Summarize files changed, behavior changed, validation results, and remaining risks.
- Keep it concise.
```

## Implementation Prompt Pattern

```text
Implement <feature/fix> in <repo/package>.

Success means:
- <user-visible behavior>
- <edge case or regression expectation>
- existing <API/UI/data contract> behavior remains compatible

Use the smallest correct change. Inspect the relevant code before editing. Avoid unrelated refactors, formatting churn, dependency changes, or broad rewrites.

Validation:
- Run <focused test command>.
- Run <typecheck/lint/build command> if affected and cheap.
- If validation is blocked by environment or credentials, stop and report the blocker plus the next best check.

Final report: changed files, behavior change, validation results, remaining risks.
```

## Bugfix Prompt Pattern

```text
Fix this bug: <bug summary>.

Evidence:
- Reproduction: <steps or failing command>
- Expected: <expected behavior>
- Actual: <actual behavior/error>
- Suspected area: <files/modules if known; omit if unknown>

Success means the reproduction passes and no unrelated behavior changes. Find the root cause before editing. Add or update a focused regression test if practical.

Constraints:
- Smallest correct fix.
- Preserve public API and persisted data compatibility.
- Do not mask the error with a generic catch unless that is the actual product requirement.

Validation:
- Run the regression test or reproduction command.
- Run the nearest affected test/typecheck if cheap.

Final report: root cause, changed files, validation results, remaining risks.
```

## Review-Only Prompt Pattern

Use this after a branch/diff already exists and you want Codex to review, not modify.

```text
Review the current diff against <base>. Do not edit files. Do not run broad or slow tests. Inspect only:
- git diff --name-only <base>...HEAD
- git diff --stat <base>...HEAD
- the changed files needed to evaluate correctness

Review for P0/P1 correctness, security, data loss, backwards compatibility, and test coverage issues. Ignore style-only nits unless they hide a real bug.

Output exactly:
Verdict: APPROVE or BLOCK
Findings:
- [severity] <file:line> <issue> <why it matters> <minimal fix>
Validation gaps:
- <missing checks, if any>
```

If reviewing uncommitted work, replace `<base>...HEAD` with the exact working-tree diff command and list the intended changed files.

## Planning Prompt Pattern

Use when the task is too broad for a safe one-shot implementation.

```text
Inspect <repo/package> and propose a minimal implementation plan for <outcome>. Do not edit files.

Plan must include:
- files/modules likely involved
- required behavior changes
- compatibility and migration risks
- focused validation commands
- task slices small enough for separate Codex runs
- open questions that materially change implementation or risk

Keep the plan concise and actionable. Do not propose speculative rewrites.
```

## Frontend/UI Prompt Additions

Add only when the task touches UI:

```text
UI constraints:
- Prioritize first-screen usability and existing design-system patterns.
- Preserve existing interaction semantics unless the task requires a change.
- Avoid generic generated-UI defaults: decorative gradients, nested cards, hero filler, instructional placeholder text, and layout-breaking overflow.
- Check loading, empty, error, and responsive states if the component already supports them.
- If browser validation is available, render and inspect the changed screen for clipping, spacing, missing content, and console errors.
```

## Codex Launch Checklist

Before launching:

- [ ] Prompt starts with the outcome.
- [ ] Scope and non-goals are explicit.
- [ ] Real repo facts are verified or labeled as assumptions.
- [ ] Validation command is exact, focused, and cheap enough.
- [ ] Destructive/production/credential risks are bounded.
- [ ] Final response shape is auditable.
- [ ] Task is small enough for one Codex run; otherwise ask Codex for a plan first.

After Codex exits:

- [ ] Audit `git status` and changed files yourself.
- [ ] Do not trust Codex’s success claim without checking the diff and validation output.
- [ ] Run or rerun the most relevant validation outside Codex when risk justifies it.
- [ ] If Codex produced no diff for an implementation task, treat the run as failed or no-op.

## Bad Prompt Smells

Rewrite before launching if the prompt has any of these:

- “Fix everything”, “clean up the repo”, “make it better” with no success criteria.
- Multiple unrelated tasks in one run.
- No reproduction, failing command, or expected behavior for a bug.
- No validation request.
- Broad permissions like “change anything” without reason.
- Process micromanagement that constrains the solution path without improving safety.
- Review prompts that allow edits or broad tests when only semantic review is needed.
- Prompts that assume package manager, branch, file paths, or test commands not yet verified.

## Minimal Examples

### Good small implementation prompt

```text
Task: Add `--json` output to the `report` CLI command.

Success criteria:
- `report --json` prints valid JSON with the same fields as the text report.
- Existing text output remains unchanged when `--json` is absent.
- Invalid flag combinations keep existing error behavior.

Constraints: smallest correct change; no dependency changes; preserve public CLI behavior.
Validation: run the focused CLI tests for `report`; run typecheck if available.
Final response: changed files, validation results, risks.
```

### Good bounded review prompt

```text
Review `origin/main...HEAD` for correctness only. Do not edit files. Do not run tests.

Focus on P0/P1 issues: data loss, security, backwards compatibility, broken API contracts, missing regression coverage. Ignore style nits.

Output:
Verdict: APPROVE or BLOCK
Findings:
- [severity] file:line issue / impact / minimal fix
Validation gaps:
- gaps or `none`
```
