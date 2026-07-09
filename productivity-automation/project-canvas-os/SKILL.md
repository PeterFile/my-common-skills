---
name: project-canvas-os
description: "Use when operating a best-practice Project Canvas OS: project documents as the Agent knowledge layer, README.md as project contract, Obsidian Project.canvas as the human cognition map, Evidence cards as truth handles, and a zero-dependency CLI as the safe mutation/audit layer. Trigger on Project Canvas OS, Project.canvas, Obsidian Canvas project map, documentation hygiene, Heptabase-style project map, evidence-driven project state, or requests to reduce human understanding cost without losing project docs."
version: 2.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [project-management, documentation, obsidian, canvas, json-canvas, evidence, software-delivery, cli]
    related_skills: [json-canvas, obsidian-markdown, obsidian-cli, software-delivery-workflows, task-pr-flow]
---

# Project Canvas OS

## Purpose

Operate projects with two complementary layers:

```text
Agent knowledge layer: README.md + current project docs
Human cognition layer: Project.canvas
Truth layer: Git/CI/tests/artifacts/evidence
Mutation/audit layer: scripts/project_canvas_os.py
```

The important correction: **Canvas does not replace documentation**.

- Project documents remain the best way for agents to understand the system deeply: architecture, domain model, API contracts, runbooks, testing strategy, ADRs, protocols, setup notes.
- `Project.canvas` is primarily for humans: it lowers understanding cost by showing goals, modules, current work, risks, decisions, and evidence relationships spatially.
- README is the project contract and index: it should point to the important docs and the Canvas.
- The CLI validates Canvas and audits documentation hygiene so docs stay current, discoverable, and non-redundant.

## Required Companion Skills

Load as needed:

1. `json-canvas` — required before direct `.canvas` JSON work.
2. `obsidian-markdown` — required before writing Obsidian-facing Markdown.
3. `obsidian-cli` — optional; only when interacting with a running Obsidian vault.
4. `software-delivery-workflows` or `task-pr-flow` — when the Canvas/docs update is tied to code delivery, branches, PRs, or validation gates.

Default: use the bundled CLI first for Canvas/status/evidence operations. Direct JSON edits are allowed only when the CLI cannot express the operation.

## Hard Rules

1. Do not discard useful project documentation. Keep relevant docs current when code, architecture, run/validation, API contracts, or operational procedures change.
2. Do not create redundant or ephemeral status-document sprawl. Temporary progress/status/handoff docs are allowed only when explicitly canonical for that project or requested by the user.
3. README must be a contract and doc index, not a long progress log.
4. `Project.canvas` is the human-facing cognition map, not the sole source of project knowledge.
5. Every completion claim needs concrete evidence: command output, CI link, commit, screenshot, trace, benchmark, or manual observation.
6. Agent may transition tasks to `Verify`; agent may not transition to `Done` without a concrete Evidence Card and explicit gate text from a human or named verification script.
7. Prefer CLI operations over hand-editing Canvas JSON:
   ```bash
   python3 <skill>/scripts/project_canvas_os.py status <repo>
   python3 <skill>/scripts/project_canvas_os.py docs <repo>
   python3 <skill>/scripts/project_canvas_os.py add-task <repo> --title "..."
   python3 <skill>/scripts/project_canvas_os.py add-evidence <repo> --task "..." --test "..." --set-task-verify
   python3 <skill>/scripts/project_canvas_os.py transition <repo> --task "..." --state Done --gate "human confirmed"
   ```
8. Canvas and relevant docs should be committed with code when the code changes project understanding.

## Documentation Layer

Docs are allowed and expected when they help agents understand or operate the project.

Good docs:

```text
README.md
AGENTS.md / CLAUDE.md / .agents/*.md
docs/architecture.md
docs/domain.md
docs/api.md
docs/testing.md
docs/runbook.md
docs/adr/*.md
docs/protocols/*.md
```

Bad docs:

```text
duplicate summaries
stale implementation notes
unowned progress logs
status files that contradict Project.canvas
handoffs with no durable facts
```

Rule: if a document describes durable project knowledge, keep it current. If it only describes transient state, prefer `Project.canvas` + Evidence.

## Best-Practice Operating Loop

### Start of work

1. Read `README.md` as the contract/index.
2. Read the relevant docs linked from README or discovered by:
   ```bash
   python3 <skill>/scripts/project_canvas_os.py docs <repo>
   ```
3. Inspect the human map:
   ```bash
   python3 <skill>/scripts/project_canvas_os.py status <repo>
   python3 <skill>/scripts/project_canvas_os.py validate <repo> --strict
   ```
4. Pick a task from `Active`, or propose a small `Proposed` task.
5. Check dependencies, docs, risk, and evidence edges before coding.

### End of work

1. Run the real validation for the code/workflow.
2. Update relevant docs if the change affects architecture, domain terms, public API, setup, validation, runbooks, or agent rules.
3. Add/update an Evidence Card with exact result text:
   ```bash
   python3 <skill>/scripts/project_canvas_os.py add-evidence <repo> \
     --title "<short evidence>" \
     --task "<task title/id>" \
     --test "<command + result>" \
     --artifact "<path/url or none>" \
     --set-task-verify
   ```
4. Add Risk Card if anything is unverified, flaky, blocked, undocumented, or assumed.
5. Update Module/Decision cards for human comprehension when durable relationships changed.
6. Audit docs and Canvas:
   ```bash
   python3 <skill>/scripts/project_canvas_os.py audit <repo> --strict --docs-strict
   ```
7. Report changed code, docs, Canvas state, validation output, and remaining uncertainty.

## Canvas Role

Canvas is for fast human orientation. Keep it spatial, short, and connected.

Use five stable regions:

| Region | Purpose |
|---|---|
| Goal | intent and success condition |
| System Structure | module/data/agent relationships; link key docs as file nodes when useful |
| Current Work | Proposed/Active/Verify/Blocked/Done tasks |
| Evidence | concrete proof handles |
| Risks & Decisions | open uncertainty and durable choices |

Do not put long explanations in Canvas. Put durable explanations in docs and link them from README/Canvas.

## Card Types

Use only these six text-card types unless the user explicitly extends the protocol:

| Card | Purpose |
|---|---|
| Goal | objective and success condition |
| Module | system module, data flow, agent flow, major interface |
| Task | executable work item |
| Evidence | hard proof for task/module/decision |
| Risk | uncertainty, blocker, missing proof, missing docs, operational risk |
| Decision | durable choice with rationale and impact |

Use Canvas `file` nodes for important docs when a visual link improves human comprehension; do not invent a separate Document Card type unless the project explicitly needs it.

## State Model

| State | Meaning | Agent can set? | Color |
|---|---|---:|---|
| Proposed | suggested, not approved | yes | `"6"` |
| Active | approved/current work | yes, if instructed or already active | `"5"` |
| Verify | implementation claims complete, evidence attached | yes | `"3"` |
| Done | accepted by human or named verification gate | only with explicit gate | `"4"` |
| Blocked | dependency, evidence, or required-doc update missing | yes | `"1"` |

`Done` requires both:

```text
concrete Evidence Card
Gate: <human/script confirmation>
```

## CLI First

Primary script:

```text
scripts/project_canvas_os.py
```

Useful commands:

```bash
python3 <skill>/scripts/project_canvas_os.py init <repo> --name "<Project>" --goal "<Goal>"
python3 <skill>/scripts/project_canvas_os.py docs <repo>
python3 <skill>/scripts/project_canvas_os.py audit <repo> --strict --docs-strict --list-docs
python3 <skill>/scripts/project_canvas_os.py validate <repo> --strict
python3 <skill>/scripts/project_canvas_os.py status <repo>
```

Compatibility validator:

```text
scripts/validate_project_canvas.py
```

Use `references/cli-reference.md` for full commands.

## Initialization

For a repo without this system:

```bash
python3 <skill>/scripts/project_canvas_os.py init <repo> --name "<Project>" --goal "<Goal>"
python3 <skill>/scripts/project_canvas_os.py audit <repo> --strict --list-docs
```

This creates:

```text
README.md
Project.canvas
.agents/canvas-protocol.md
```

Then keep or create only docs that are useful to agents and link key docs from README.

## Scaling Rules

Escalate only when the file-level system is insufficient:

1. Native Markdown docs + Canvas + CLI — default.
2. Sub-canvas/file nodes — when one canvas exceeds roughly 50 cards or one module needs its own map.
3. Obsidian Advanced Canvas — when folding/focus/navigation becomes the bottleneck.
4. Bases — only for hidden indexes like all `Verify` tasks, open risks, or docs inventory; not the daily entrypoint.
5. MCP/REST — only when multiple independent agents need concurrent vault access with policy enforcement.

## Validation Gate

Before final response after any Canvas/docs change:

```bash
python3 <skill>/scripts/project_canvas_os.py validate <repo> --strict
python3 <skill>/scripts/project_canvas_os.py audit <repo> --strict --docs-strict
python3 -m json.tool <repo>/Project.canvas >/dev/null
git -C <repo> diff --check
python3 <skill>/scripts/test_project_canvas_os.py -v   # when editing the skill itself
```

For codebase sessions with an external coding gate, also run the cheapest relevant repository script that can see the checkout, usually lint/typecheck/test.

Checks include:

- JSON parses.
- Node/edge IDs unique.
- Edges reference real nodes.
- Task states are valid.
- `Verify`/`Done` tasks have concrete evidence.
- `Done` has explicit gate text when transitioned through CLI.
- Markdown docs are inventoried and classified as contract/knowledge/other/state.
- Stale/deprecated doc markers are reported; `--docs-strict` fails on them.
- Key knowledge docs not referenced by README or Canvas are reported as discoverability warnings.

## Linked Files

- `scripts/project_canvas_os.py` — primary zero-dependency CLI.
- `scripts/validate_project_canvas.py` — validation compatibility wrapper.
- `scripts/test_project_canvas_os.py` — skill self-tests.
- `templates/README.md` — minimal project contract and docs index template.
- `templates/Project.canvas` — five-region starter canvas.
- `references/canvas-protocol.md` — repo-local agent protocol for `.agents/canvas-protocol.md`.
- `references/operating-model.md` — full operating model and escalation rules.
- `references/cli-reference.md` — command reference and examples.
- `references/adoption-checklist.md` — checklist for converting an existing repo.
- `references/documentation-hygiene.md` — rules for current, non-redundant Agent knowledge docs.

## When Not To Use

Do not use this skill for:

- Replacing GitHub/Linear lifecycle systems.
- Long-form research notes unrelated to a project.
- General wiki design with no project execution loop.
- Projects where the user explicitly wants conventional documentation only.
- Obsidian plugin development itself; use Obsidian-specific skills directly.
