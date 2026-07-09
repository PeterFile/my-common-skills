# Parallel code simplification review

Consolidated from the former `simplify-code` skill. Use this reference from `software-delivery-workflows` when the user explicitly asks to simplify, review, or clean up recent code changes with parallel reviewers.

## Trigger
Use only on explicit requests such as:
- "simplify my changes"
- "review my recent changes"
- "clean up my changes"
- "/simplify"

Honor modifiers:
- Focus: `reuse`, `quality`, or `efficiency`.
- Dry run: report only, apply nothing.
- Scope: staged changes, last commit, branch, or named files.

## Phase 1: identify the diff
Default order:
```bash
git diff
git diff HEAD
git diff --staged
git diff HEAD~1
git diff main...HEAD
git diff -- src/foo.py
```

If the diff is huge (roughly >2000 changed lines), warn that three subagents will be token-heavy and offer to scope down.

## Phase 2: run three reviewers in parallel
Use `delegate_task` batch mode with the complete diff and absolute repo path for every reviewer. Give children terminal/file/search toolsets. Require each reviewer to search the codebase for evidence and report `file:line -> problem -> suggested fix`, ranked high/medium/low confidence.

### Reviewer 1: reuse
Find duplicated functionality, hand-rolled logic, missed helpers/constants/patterns, and existing utilities that should be reused.

### Reviewer 2: quality
Find redundant state, parameter sprawl, copy-paste-with-variation, leaky abstractions, stringly typed code, and abstraction boundaries that got weaker.

### Reviewer 3: efficiency
Find redundant computation, repeated file reads/API calls, N+1 access patterns, missed concurrency, hot-path bloat, TOCTOU pre-checks, leaks, and overly broad reads.

## Phase 3: aggregate and apply
1. Dedupe findings.
2. Drop false positives and style-only nits.
3. Resolve conflicts in this order: correctness > user's stated focus > readability/reuse > micro-performance.
4. Apply only scoped fixes unless dry run.
5. Run targeted tests/lint/type checks for touched files.
6. Summarize applied fixes and skipped findings.

## Pitfalls
- Do not fan out beyond about three reviewers.
- Give every reviewer the whole diff; splitting hides cross-file issues.
- Drop reuse findings without concrete existing utility evidence.
- Keep edits scoped to the user's changes.
- Fold AGENTS.md/CLAUDE.md/HERMES.md conventions into reviewer prompts.
