# SkyTurn Kiro-style Plan pages

Use this when implementing or reviewing SkyTurn Plan-mode UX that resembles Kiro/spec-driven workflows.

## Durable lesson
Plan mode should not be treated as three markdown sections on one page. The product expectation is a gated workflow:

```text
Requirements page -> explicit approval -> Design page -> explicit approval -> Tasks page -> explicit approval -> Convert to Canvas
```

This is a UX/state-machine requirement, not just copy.

## Implementation checklist
- Requirements, Design, and Tasks render as separate pages/states.
- Requirements is the only initially accessible page.
- Design is disabled until Requirements is approved.
- Tasks is disabled until Design is approved.
- `Convert to Canvas` is disabled until all three pages are approved.
- Editing an approved page invalidates that page and all downstream approvals.
- Approval handlers must not rely on state that was just scheduled with React `setState`; if approval should advance immediately, set the active page directly or compute the next approval state locally.
- Seed content should guide Kiro-style artifacts:
  - Requirements: introduction, glossary, EARS acceptance criteria.
  - Design: architecture/components, correctness properties, testing strategy.
  - Tasks: implementation checklist with requirement references.

## Review and validation
- Add tests that lock the gating behavior: disabled downstream pages, disabled Convert, invalidation after edits, and immediate approve-and-advance.
- Browser-smoke each page state. A source test proving strings exist is not enough for visual gating.
- Do not collapse this into file tabs or a full editor; SkyTurn remains canvas-first and Plan is pre-canvas planning state.

## Common pitfall
In React, this is wrong for immediate navigation:

```ts
setApprovals((prev) => ({ ...prev, requirements: true }));
changeActiveSection("design"); // may read old approvals and refuse navigation
```

Prefer setting the next active section directly after approval, or computing `nextApprovals` before checking access.
