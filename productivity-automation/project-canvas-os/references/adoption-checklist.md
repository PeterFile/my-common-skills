# Project Canvas OS Adoption Checklist

Use this when converting an existing repo.

## Install/Load prerequisites

- [ ] `json-canvas` skill installed.
- [ ] `obsidian-markdown` skill installed.
- [ ] `project-canvas-os` skill loaded.

## Initialize

```bash
python3 <skill>/scripts/project_canvas_os.py init <repo> --name "<Project>" --goal "<Goal>"
python3 <skill>/scripts/project_canvas_os.py audit <repo> --strict --list-docs
```

## Preserve and clean docs

- [ ] Keep existing useful docs that explain architecture, domain, API, setup, testing, runbooks, ADRs, or agent workflow.
- [ ] Link key docs from README's Documentation Index.
- [ ] Remove/archive/update stale docs.
- [ ] Do not bulk-delete docs just because Canvas exists.
- [ ] Do not keep duplicate progress dumps unless they are canonical project artifacts.

## Seed Canvas with human-oriented truth

- [ ] One Goal card.
- [ ] 3-8 Module cards for real architecture surfaces.
- [ ] File nodes or short references for the most important docs when useful.
- [ ] Current Active tasks only.
- [ ] Current Blocked tasks only.
- [ ] Verify tasks with concrete evidence.
- [ ] Open risks, including missing docs/proof.
- [ ] Durable decisions.

Do not bulk-import old progress docs into Canvas.

## Repo hygiene

- [ ] README is a contract + doc index.
- [ ] Docs are the Agent knowledge layer.
- [ ] Project.canvas is the human cognition map.
- [ ] Local agent rules live in `.agents/canvas-protocol.md` if needed.
- [ ] Code, relevant docs, and Canvas changes commit together when related.

## Validation gate

Before final response or PR:

```bash
python3 <skill>/scripts/project_canvas_os.py docs <repo>
python3 <skill>/scripts/project_canvas_os.py validate <repo> --strict
python3 <skill>/scripts/project_canvas_os.py audit <repo> --strict --docs-strict
python3 <skill>/scripts/project_canvas_os.py status <repo>
```

For skill changes:

```bash
python3 <skill>/scripts/test_project_canvas_os.py -v
```

## Human review

- [ ] Review Verify tasks by following Task → Evidence edges.
- [ ] Read linked docs only when detail is needed.
- [ ] Move to Done only after evidence is accepted.
- [ ] Add Gate text for every Done transition.
- [ ] Convert unresolved uncertainty into Risk cards.
