# Legacy workflow archive index

Purpose: keep large historical delivery workflows searchable without making them the default execution path.

Read this index before loading any legacy archive. The current operating path is `SKILL.md` plus the current references named in its Reference Loading Map.

## Primary current references

- `delivery-operating-model-v2.md` — current mode selector, dynamic rate control, workgroup cadence, and Definition of Done.
- `ci-validation-and-duplicate-checks-2026-04.md` — current validation layer and CI duplicate-handling policy.
- `closeout-pm-truth-and-worktree-rescue-2026-04.md` — current merge truth, closeout, and dirty/stale worktree rescue policy.
- `workflow-optimization-addendum-2026-04.md` — current controller-artifact, background-process, and continuation rules.

## Legacy archives

| File | Status | Load only when |
| --- | --- | --- |
| `legacy-linear-slack-worktree-delivery-loop-skill.md` | superseded v2 workflow source | You need a historical Slack/Linear/workgroup edge case not covered by current references. |
| `legacy-parallel-worktree-codex-review-loop-skill.md` | superseded parallel-worktree source | You need a historical Codex/worktree/review loop detail not covered by current references. |
| `legacy-linear-slack-full-pre-refactor-2026-04-25.md` | full verbatim pre-refactor archive | You need provenance, exact old wording, or a rare edge case; do not use as the primary operating path. |

## Rules for using legacy material

1. Do not promote an archived rule over current `SKILL.md` unless the current skill is missing a real reusable edge case.
2. If a legacy archive contains a still-valid rule, migrate the compact rule into `SKILL.md` or a current reference instead of repeatedly loading the full archive.
3. Keep progress logs, transient PR numbers, and one-off run narratives out of this skill. Only preserve reusable workflow policy.
4. When a legacy rule conflicts with current dynamic rate control, validation layering, closeout truth, or controller-state discipline, the current rule wins.
