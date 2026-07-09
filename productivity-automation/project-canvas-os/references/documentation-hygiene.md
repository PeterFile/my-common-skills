# Documentation Hygiene

Project Canvas OS does not remove project documentation. It separates durable knowledge from transient state.

## Canonical roles

```text
README.md         contract + documentation index
Project.canvas    human cognition map
Docs              Agent knowledge layer
Evidence cards    proof handles
Git/CI/tests      fact source
```

## Keep docs when they help agents

Good project docs include:

- architecture and module boundaries
- domain model / terminology
- API contracts / schemas
- setup and environment notes
- validation/test strategy
- runbooks and operational procedures
- ADRs / durable decisions
- agent rules and workflow protocols

These are not clutter. They are usually the best way for agents to understand the project.

## Avoid doc rot

A doc is harmful when it is:

- redundant with another canonical doc
- stale or contradicted by code/tests/Canvas
- unlinked and undiscoverable
- a one-off progress dump with no durable facts
- a handoff that survives after the state moved on

## Update rules

When code changes, update docs if the change affects:

- public commands or setup
- architecture/module ownership
- API shape, schemas, or data contracts
- validation/testing instructions
- operational behavior or runbooks
- domain terms
- agent workflow rules

Do not update docs just to narrate that work happened. Use Evidence Cards for completion facts.

## Discoverability rules

Important docs should be reachable from at least one of:

- `README.md`
- `Project.canvas` as a file node or referenced in a Module/Decision/Risk card
- `.agents/canvas-protocol.md` for agent-specific rules

The CLI warns when knowledge docs are not referenced from README or Canvas.

## Status docs

Status/progress docs are not banned. They are risky.

Keep them only if the project explicitly treats them as canonical operational artifacts, for example:

- a controller `latest-status.md` consumed by automation
- timestamped cycle logs required by a runbook
- release notes with durable user-facing facts

Otherwise prefer:

```text
Project.canvas task state + Evidence Card + Git/CI artifact
```

## Archiving

If a doc is no longer current:

1. Update it to point to the replacement, or
2. Move it under an archive path, or
3. Delete it if no durable fact remains.

Do not leave stale docs in active discovery paths.

## Audit commands

```bash
python3 <skill>/scripts/project_canvas_os.py docs <repo>
python3 <skill>/scripts/project_canvas_os.py audit <repo> --strict --docs-strict --list-docs
```

`--docs-strict` fails on explicit stale/deprecated markers. It does not fail just because docs exist.
