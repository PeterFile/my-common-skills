---
name: kanban-operations
description: "Use when operating Hermes Kanban workflows as an orchestrator or worker, including decomposition, lane routing, lifecycle ownership, and reconciliation."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [kanban, orchestration, workers, delegation]
    related_skills: [autonomous-coding-agents]
---

# Hermes Kanban Operations

## Overview
This umbrella covers Kanban orchestrator and worker behavior. The key invariant is ownership: each lane owns its assigned work and verification; orchestrators should route work rather than secretly performing worker tasks.

## When to Use
- Decomposing a project into Kanban tasks.
- Acting as a Kanban orchestrator or worker.
- Routing a task to a coding-agent lane.
- Reconciling worker reports.

## Orchestrator Playbook
- Break work into independently verifiable tasks.
- Assign clear acceptance criteria and dependencies.
- Do not implement details that belong to workers.
- Track blockers and route follow-up work explicitly.

## Worker Playbook
- Read assigned context and acceptance criteria.
- Do only the assigned task and surface scope creep.
- Produce verifiable outputs: files changed, commands run, test results, artifact IDs.
- Mark complete only after validation or explicit blocker reporting.

## Common Pitfalls
1. Orchestrator performs implementation instead of routing.
2. Worker returns narrative without handles.
3. Dependencies between lanes remain implicit.
4. Done is declared before acceptance checks.

## Verification Checklist
- [ ] Task boundaries and dependencies explicit.
- [ ] Lane acceptance criteria present.
- [ ] Worker outputs are verifiable.
