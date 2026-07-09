# Project Canvas OS CLI Reference

Primary command:

```bash
python3 <skill>/scripts/project_canvas_os.py <command> <repo-or-canvas> [options]
```

Compatibility validator:

```bash
python3 <skill>/scripts/validate_project_canvas.py <repo-or-canvas> --strict
```

## Initialize

```bash
python3 <skill>/scripts/project_canvas_os.py init <repo> \
  --name "Fishing Agent" \
  --goal "Open-source BYO-LLM fishing decision app"
```

Creates:

```text
README.md
Project.canvas
.agents/canvas-protocol.md
```

Use `--force` only when intentionally replacing existing files.

## Validate Canvas

```bash
python3 <skill>/scripts/project_canvas_os.py validate <repo> --strict
```

Use before and after any Canvas mutation.

## Audit docs

```bash
python3 <skill>/scripts/project_canvas_os.py docs <repo>
python3 <skill>/scripts/project_canvas_os.py docs <repo> --strict
```

Classifies Markdown docs as:

```text
contract   README.md
knowledge  durable Agent-understanding docs
state      progress/status/handoff-like docs
other      markdown docs not classified by naming/path
```

`--strict` fails only on explicit stale/deprecated markers. It does not fail because docs exist.

## Full audit

```bash
python3 <skill>/scripts/project_canvas_os.py audit <repo> --strict --docs-strict --list-docs
```

- `--strict` applies strict Canvas validation.
- `--docs-strict` fails on stale/deprecated doc markers.
- `--list-docs` prints classified document inventory.

## Status

```bash
python3 <skill>/scripts/project_canvas_os.py status <repo>
```

Shows card counts, task state counts, and Active/Verify/Blocked task summaries.

## List cards

```bash
python3 <skill>/scripts/project_canvas_os.py list <repo>
python3 <skill>/scripts/project_canvas_os.py list <repo> --kind Task
python3 <skill>/scripts/project_canvas_os.py list <repo> --kind Task --state Verify
```

## Add module

```bash
python3 <skill>/scripts/project_canvas_os.py add-module <repo> \
  --title "Provider Runtime" \
  --role "Owns BYO-LLM provider profiles and chat execution" \
  --inputs "provider profile, credential ref, prompt" \
  --outputs "answer, trace, usage, errors"
```

## Add task

```bash
python3 <skill>/scripts/project_canvas_os.py add-task <repo> \
  --title "Wire provider runtime" \
  --state Active \
  --owner Codex \
  --module "Provider Runtime"
```

`add-task` cannot create `Done` tasks.

## Add evidence and move to Verify

```bash
python3 <skill>/scripts/project_canvas_os.py add-evidence <repo> \
  --title "Provider runtime tests" \
  --task "Wire provider runtime" \
  --test "pnpm test passed: 8 tests" \
  --build "pnpm typecheck passed" \
  --artifact "none" \
  --set-task-verify
```

The evidence must be concrete. Placeholder `none` evidence does not satisfy `Verify`/`Done` in strict validation.

## Add risk

```bash
python3 <skill>/scripts/project_canvas_os.py add-risk <repo> \
  --title "No live provider endpoint tested" \
  --task "Wire provider runtime" \
  --impact "Mock tests can pass while real OpenAI-compatible endpoint fails" \
  --mitigation "Run live endpoint smoke with user key"
```

Use Risk cards for missing proof or missing required documentation.

## Add decision

```bash
python3 <skill>/scripts/project_canvas_os.py add-decision <repo> \
  --title "Standalone app owns provider credentials" \
  --rationale "Open-source BYO-LLM app must not send secrets to shared backend" \
  --impact "Credentials stay in OS secure storage"
```

Durable decisions should usually also live in docs/ADRs when they need explanation beyond a short Canvas card.

## Link cards

```bash
python3 <skill>/scripts/project_canvas_os.py link <repo> \
  --from "Provider Runtime" \
  --to "Provider runtime tests" \
  --label "validated by"
```

Queries can be exact IDs or unique title substrings.

## Transition task state

To Verify or Blocked:

```bash
python3 <skill>/scripts/project_canvas_os.py transition <repo> \
  --task "Wire provider runtime" \
  --state Verify \
  --evidence "Provider runtime tests"
```

To Done:

```bash
python3 <skill>/scripts/project_canvas_os.py transition <repo> \
  --task "Wire provider runtime" \
  --state Done \
  --evidence "Provider runtime tests" \
  --gate "human confirmed after reviewing evidence"
```

No `--gate`, no `Done`.
