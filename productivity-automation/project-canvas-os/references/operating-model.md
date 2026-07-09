# Project Canvas OS Operating Model

## Architecture

Project Canvas OS has four layers:

```text
README.md + docs          Agent knowledge layer
Project.canvas            human cognition map
project_canvas_os.py      safe mutation + audit layer
Git/CI/tests/artifacts    fact source
```

The Canvas is not a replacement for documentation, GitHub, Linear, or CI. It is the human orientation layer that links goals, architecture, current work, evidence, risks, and decisions.

## Why this works

Agents need text docs for deep understanding. Humans need a compact spatial map to avoid reading every doc before making a decision.

```text
Docs explain durable knowledge.
Canvas shows current shape and relationships.
Evidence proves claims.
```

A good task chain looks like:

```text
Doc/Module -> Task -> Evidence -> Risk/Decision
```

## Read paths

### Agent read path

1. `README.md` for goal, commands, constraints, and doc index.
2. Relevant docs: architecture, domain, API, testing, runbook, ADRs, agent rules.
3. `Project.canvas` for current state and human-priority context.
4. Code/tests for live truth.

### Human read path

1. Goal region.
2. System Structure region and key doc file nodes.
3. Current Work region.
4. Evidence region.
5. Risks & Decisions region.

## Agent Work Cycle

### Before coding

```bash
python3 <skill>/scripts/project_canvas_os.py docs <repo>
python3 <skill>/scripts/project_canvas_os.py status <repo>
python3 <skill>/scripts/project_canvas_os.py validate <repo> --strict
```

Then read the relevant docs and select one slice unless the orchestrator explicitly coordinates parallel work.

### During coding

- Do not create narrative progress dumps.
- If new information changes durable project knowledge, update the relevant doc.
- If the change affects human orientation, update Module/Risk/Decision cards.
- If validation is not yet available, keep the task `Active` or `Blocked`.

### After coding

1. Run the relevant validation.
2. Update docs if durable knowledge changed.
3. Add concrete Evidence.
4. Move task to `Verify`.
5. Add Risk if validation/docs are incomplete.
6. Validate Canvas and audit docs.
7. Commit code, relevant docs, and Canvas together when applicable.

## Evidence Quality

Strong evidence:

- exact test/build command and pass/fail result
- CI URL and conclusion
- commit SHA
- screenshot/video path for visual/UI checks
- benchmark output
- manual observation with exact environment and result

Weak evidence:

- "implemented"
- "should work"
- model self-report
- unchecked assumptions
- missing command output

Weak evidence cannot justify `Done`.

## Done Gate

`Done` is a gate, not an agent mood.

Allowed gate examples:

```text
Gate: human confirmed in review
Gate: scripts/verify-release.sh passed
Gate: pull_request CI success at <url>
Gate: browser smoke screenshot accepted by human
```

Disallowed:

```text
Gate: agent says complete
Gate: looks okay
Gate: tests probably pass
```

## Multi-Agent / Worktree Use

For parallel implementation:

1. Orchestrator owns `Project.canvas` writes or explicitly assigns Canvas write ownership.
2. Coding agents read docs and Canvas; if they modify durable knowledge, they update docs in their worktree.
3. If multiple agents edit Canvas, they must use the CLI and merge by card ID, not by rewriting the whole file.
4. Code, docs, and Canvas diffs should be reviewed together.

## Existing Repo Adoption

Use:

```bash
python3 <skill>/scripts/project_canvas_os.py init <repo> --name "<Project>" --goal "<Goal>"
python3 <skill>/scripts/project_canvas_os.py audit <repo> --strict --list-docs
```

Then keep live truth:

- existing useful docs
- one Goal card
- key Module cards
- current Active/Blocked/Verify tasks
- evidence for recently completed work
- open risks and durable decisions

Do not bulk-import old narrative progress logs into Canvas. Link or preserve only docs containing durable facts.

## Scaling and Escalation

Stay file-first until it hurts.

| Need | Escalation |
|---|---|
| deep agent context | Markdown docs |
| human overview | Native Canvas + CLI |
| map too large | sub-canvas via file nodes |
| need fold/focus/navigation | Advanced Canvas |
| need table/index views | Obsidian Bases as hidden index |
| many agents writing concurrently | MCP/REST with policy layer |

If docs disappear, agents get dumber. If Canvas becomes the only source of truth, humans get a pretty but shallow dashboard.

## Failure Modes

- Canvas replaces docs: restore docs as the Agent knowledge layer.
- Docs become stale: update, link replacement, archive, or delete.
- Canvas becomes a Kanban board only: restore Module/Evidence/Risk/Decision links.
- Evidence becomes prose: require command/artifact/CI output.
- Too many cards: split into sub-canvas by module, keep top-level map shallow.
- Done inflation: enforce `Done` gate with concrete evidence.
