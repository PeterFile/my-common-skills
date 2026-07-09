# Project Name

## Goal

One sentence describing the project objective and success condition.

## Run

```bash
# Replace with the real command.
```

## Validate

```bash
# Replace with the cheapest reliable validation command.
```

## Documentation Index

Keep this index current. Docs are the Agent knowledge layer.

```text
# Add project-specific docs here, for example:
# docs/architecture.md  — module boundaries and system shape
# docs/domain.md        — domain terms and invariants
# docs/api.md           — API/data contracts
# docs/testing.md       — validation strategy
# docs/runbook.md       — operational procedures
# docs/adr/             — durable decisions
```

## Core Constraints

- Project docs are the Agent knowledge layer; keep relevant docs current.
- `Project.canvas` is the human cognition map; keep it short, spatial, and evidence-linked.
- Do not create redundant progress/summary/handoff/status docs unless explicitly canonical or requested.
- Agent task completion lands in `Verify`, not `Done`, unless a named verification gate or human confirmation authorizes `Done`.
- `Done` requires concrete evidence and explicit gate text.
- Code, relevant docs, and Canvas changes should be committed together when related.

## Project Map

Open `Project.canvas` in Obsidian.

Useful operations:

```bash
python3 <project-canvas-os-skill>/scripts/project_canvas_os.py docs .
python3 <project-canvas-os-skill>/scripts/project_canvas_os.py status .
python3 <project-canvas-os-skill>/scripts/project_canvas_os.py validate . --strict
python3 <project-canvas-os-skill>/scripts/project_canvas_os.py audit . --strict --docs-strict
```

Repo-local agent protocol, if present:

```text
.agents/canvas-protocol.md
```
