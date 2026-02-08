# Dispatch Task Prompt

## Description

Dispatch a task to the appropriate worker agent (codex for code, gemini for UI, codex-review for review).

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| task_id | Yes | Task identifier to dispatch (e.g., "task-001") |
| force | No | Force dispatch even if dependencies not satisfied (default: false) |

## Instructions

When dispatching a task, follow these steps:

### Step 1: Load State
```bash
python skills/multi-agent-orchestration/scripts/dispatch_batch.py AGENT_STATE.json --task-id <task_id> --dry-run
```

### Step 2: Validate Dependencies
1. Read AGENT_STATE.json to get task details
2. Check all dependencies are in "completed" status
3. If dependencies not satisfied and force=false, report blocked status

### Step 3: Determine Agent Type
| Task Type | Agent | Backend Flag |
|-----------|-------|--------------|
| Code implementation | codex | `--backend codex` |
| UI/Frontend | Gemini | `--backend gemini` |
| Review | codex-review | `--backend codex` |

### Step 4: Build Task Configuration
```
---TASK---
id: <task_id>
backend: <agent_backend>
workdir: .
dependencies: <comma_separated_deps>
---CONTENT---
<task_description_from_tasks.md>
```

### Step 5: Invoke codeagent-wrapper
```bash
codeagent-wrapper --parallel \
  --tmux-session roundtable \
  --tmux-no-main-window \
  --state-file AGENT_STATE.json \
  <<'EOF'
<task_configuration>
EOF
```

### Step 6: Update State
1. Task status transitions to "in_progress"
2. Window/pane mapping recorded in AGENT_STATE.json
3. PROJECT_PULSE.md updated via sync_pulse.py

## Example Usage

### Natural Language
"Dispatch task-001 to the appropriate worker"

### Script
```bash
python skills/multi-agent-orchestration/scripts/dispatch_batch.py AGENT_STATE.json --task-id task-001
```

### Programmatic
```python
from skills.multi_agent_orchestrator.scripts.dispatch_batch import dispatch_task
dispatch_task("AGENT_STATE.json", "task-001")
```

## Error Handling

| Error | Action |
|-------|--------|
| Task not found | Report error, list available tasks |
| Dependencies not satisfied | Report blocked dependencies, suggest --force |
| Agent unavailable | Report error, suggest manual intervention |
| Tmux session error | Create new session or report error |

## State Transitions

```
not_started → in_progress (on dispatch)
blocked → in_progress (when blocker resolved)
```
