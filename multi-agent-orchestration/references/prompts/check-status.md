# Check Status Prompt

## Description

Check and report the current orchestration status from AGENT_STATE.json.

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| state_file | No | Path to AGENT_STATE.json (default: ./AGENT_STATE.json) |
| format | No | Output format: summary, detailed, json (default: summary) |
| task_id | No | Filter to specific task |

## Instructions

When checking status, follow these steps:

### Step 1: Read State File
```bash
cat AGENT_STATE.json | jq '.'
```

### Step 2: Generate Summary Report

#### Task Status Overview
```
Orchestration Status: <session_name>
Spec: <spec_path>

Tasks:
  not_started:    3
  in_progress:    2
  pending_review: 1
  under_review:   0
  completed:      4
  blocked:        1
  ─────────────────
  Total:         11

Progress: 36% (4/11 completed)
```

#### Active Tasks
```
In Progress:
  • task-005: Implement user management (codex)
    Window: task-005, Pane: %3
    Started: 2026-01-06T09:15:00Z
    
  • task-006: Create dashboard UI (gemini)
    Window: task-006, Pane: %5
    Started: 2026-01-06T09:20:00Z

Pending Review:
  • task-004: Authentication module
    Waiting for review spawn
```

#### Blocked Items
```
Blocked:
  • task-007: API integration
    Reason: Waiting for API specification
    Required: Backend team to provide OpenAPI spec
    Blocked since: 2026-01-05T14:00:00Z (20h)
```

#### Pending Decisions
```
Decisions Needed:
  ⚠️ decision-001: Database selection (pending 26h - ESCALATED)
     Options: PostgreSQL, MongoDB
     Context: Affects task-008, task-009
```

### Step 3: Output Format Options

#### Summary (default)
```
Orchestration: roundtable-auth
Progress: 36% (4/11 tasks)
Active: 2 in_progress, 1 pending_review
Blocked: 1 task
Decisions: 1 pending (1 escalated)
```

#### Detailed
Full report with all sections as shown in Step 2.

#### JSON
```json
{
  "session_name": "roundtable-auth",
  "spec_path": ".kiro/specs/auth-feature",
  "summary": {
    "total": 11,
    "completed": 4,
    "in_progress": 2,
    "pending_review": 1,
    "blocked": 1,
    "not_started": 3
  },
  "progress_percent": 36,
  "active_tasks": [...],
  "blocked_items": [...],
  "pending_decisions": [...]
}
```

## Example Usage

### Natural Language
"Show orchestration status"
"What's the current progress?"
"Check status of task-005"

### Script
```bash
# Summary
cat AGENT_STATE.json | jq '{
  total: .tasks | length,
  completed: [.tasks[] | select(.status == "completed")] | length,
  in_progress: [.tasks[] | select(.status == "in_progress")] | length,
  blocked: .blocked_items | length,
  pending_decisions: .pending_decisions | length
}'

# Specific task
cat AGENT_STATE.json | jq '.tasks[] | select(.task_id == "task-005")'
```

### Programmatic
```python
import json

def check_status(state_file: str, format: str = "summary") -> str:
    with open(state_file) as f:
        state = json.load(f)
    
    tasks = state.get("tasks", [])
    by_status = {}
    for task in tasks:
        status = task.get("status", "unknown")
        by_status[status] = by_status.get(status, 0) + 1
    
    completed = by_status.get("completed", 0)
    total = len(tasks)
    progress = (completed / total * 100) if total > 0 else 0
    
    return f"Progress: {progress:.0f}% ({completed}/{total} tasks)"
```

## Status Indicators

| Status | Icon | Description |
|--------|------|-------------|
| not_started | ○ | Task not yet started |
| in_progress | ◐ | Task currently executing |
| pending_review | ◑ | Awaiting review spawn |
| under_review | ◕ | Review in progress |
| final_review | ◔ | Consolidating reviews |
| completed | ● | Task finished |
| blocked | ⊘ | Task blocked |

## Tmux Integration

Check tmux session status:
```bash
# List windows
tmux list-windows -t roundtable

# List panes in task window
tmux list-panes -t roundtable:task-005

# Check if session exists
tmux has-session -t roundtable && echo "Session active"
```

## Health Checks

| Check | Healthy | Warning | Critical |
|-------|---------|---------|----------|
| Progress | > 50% | 25-50% | < 25% |
| Blocked tasks | 0 | 1-2 | > 2 |
| Pending decisions | 0 | 1 (< 24h) | Any > 24h |
| Failed reviews | 0 | 1 minor | Any major/critical |

## Error Handling

| Error | Action |
|-------|--------|
| State file not found | Report error, suggest initialization |
| Invalid JSON | Report parse error with line number |
| Tmux session not found | Report session missing, suggest restart |
| Empty state | Report no tasks, suggest spec parsing |
