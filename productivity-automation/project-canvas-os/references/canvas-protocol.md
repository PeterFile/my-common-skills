# Project Canvas Protocol

Copy this into `.agents/canvas-protocol.md` when a repo uses Project Canvas OS.

## Layer model

```text
README.md + docs       Agent knowledge layer
Project.canvas         human cognition map
Evidence cards         proof handles
Git/CI/tests           fact source
```

Canvas does not replace docs. Keep durable docs current; keep Canvas readable.

## Agent mutation rule

Prefer the Project Canvas OS CLI over hand-editing `.canvas` JSON:

```bash
python3 <skill>/scripts/project_canvas_os.py docs <repo>
python3 <skill>/scripts/project_canvas_os.py status <repo>
python3 <skill>/scripts/project_canvas_os.py validate <repo> --strict
python3 <skill>/scripts/project_canvas_os.py add-task <repo> --title "..."
python3 <skill>/scripts/project_canvas_os.py add-evidence <repo> --task "..." --test "..." --set-task-verify
python3 <skill>/scripts/project_canvas_os.py transition <repo> --task "..." --state Done --evidence "..." --gate "..."
```

Direct JSON edits are allowed only when the CLI cannot express the change, and must still pass strict validation.

## Documentation rules

Do maintain docs when durable project knowledge changes:

- architecture/module ownership
- domain terms
- API/data contracts
- setup/run/validation commands
- testing strategy
- runbooks/operations
- ADRs/durable decisions
- agent workflow rules

Do not create redundant progress/summary/handoff/status docs unless they are explicitly canonical for this repo or the user requests them.

Important docs should be discoverable from README or Canvas.

## Card types

Only use text cards:

```text
Goal
Module
Task
Evidence
Risk
Decision
```

Use Canvas file nodes for important docs when useful for human orientation.

## State model

Only use:

```text
Proposed
Active
Verify
Done
Blocked
```

Rules:

- Agent may set `Verify` when concrete evidence is attached.
- Agent may set `Blocked` when dependency/evidence/required-doc update is missing.
- Agent may not set `Done` without a concrete Evidence Card and explicit `Gate:` text from a human or named verification script.
- Placeholder evidence (`none`, `unknown`, `<...>`) does not count.

## Evidence requirements

Evidence must include at least one concrete proof:

- command + result
- CI URL + conclusion
- commit SHA
- screenshot/video/artifact path
- benchmark output
- manual observation with exact environment/result

No self-reported completion.

## Spatial layout

Preserve five regions:

1. Goal
2. System Structure
3. Current Work
4. Evidence
5. Risks & Decisions

Do not turn the map into a plain Kanban board. The value is dependency/evidence/risk/doc relationships.

## Before work

```bash
python3 <skill>/scripts/project_canvas_os.py docs <repo>
python3 <skill>/scripts/project_canvas_os.py status <repo>
python3 <skill>/scripts/project_canvas_os.py validate <repo> --strict
```

Then read relevant docs and pick one Active task or propose a small task.

## After work

1. Run real validation.
2. Update relevant docs if durable knowledge changed.
3. Add Evidence Card.
4. Move task to Verify.
5. Add Risk if incomplete/unverified/flaky/undocumented.
6. Validate Canvas and audit docs.
7. Commit code, docs, and Canvas together when related.
