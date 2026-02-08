# Spawn Review Prompt

## Description

Spawn a Review Codex instance to audit completed task implementation.

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| task_id | Yes | Task identifier to review (e.g., "task-001") |
| criticality | No | Override criticality level (standard, complex, security-sensitive) |

## Instructions

When spawning a review, follow these steps:

### Step 1: Validate Task Status
1. Read AGENT_STATE.json
2. Verify task is in "pending_review" status
3. If not pending_review, report current status and abort

### Step 2: Determine Review Count
| Criticality | Review Count | Notes |
|-------------|--------------|-------|
| standard | 1 | Single reviewer |
| complex | 2+ | Multiple parallel reviewers |
| security-sensitive | 2+ | Security-focused reviewers |

### Step 3: Gather Review Context
1. Get task description from tasks.md
2. Get implementation changes from task output
3. Get relevant requirements from requirements.md
4. Get design constraints from design.md

### Step 4: Build Review Task Configuration
```
---TASK---
id: review-<task_id>
backend: codex
workdir: .
dependencies: <task_id>
---CONTENT---
Review task <task_id>:

## Implementation Summary
<files_changed>
<code_changes_summary>

## Requirements to Verify
<relevant_requirements>

## Review Checklist
- [ ] Code correctness
- [ ] Error handling
- [ ] Test coverage
- [ ] Security considerations
- [ ] Performance implications

Produce a Review Finding with severity: critical, major, minor, or none.
```

### Step 5: Invoke codeagent-wrapper
```bash
python skills/multi-agent-orchestration/scripts/dispatch_reviews.py AGENT_STATE.json --task-id <task_id>
```

Or directly:
```bash
codeagent-wrapper --parallel \
  --tmux-session roundtable \
  --tmux-no-main-window \
  --state-file AGENT_STATE.json \
  <<'EOF'
<review_task_configuration>
EOF
```

### Step 6: Update State
1. Task status transitions to "under_review"
2. Review pane created in task's window
3. Review finding recorded when complete

## Example Usage

### Natural Language
"Spawn review for task-001"
"Start code review for the authentication implementation"

### Script
```bash
python skills/multi-agent-orchestration/scripts/dispatch_reviews.py AGENT_STATE.json --task-id task-001
```

### Programmatic
```python
from skills.multi_agent_orchestrator.scripts.dispatch_reviews import spawn_review
spawn_review("AGENT_STATE.json", "task-001")
```

## Review Finding Format

```json
{
  "task_id": "task-001",
  "reviewer": "codex-review-1",
  "severity": "minor",
  "summary": "Implementation correct with minor suggestions",
  "details": "Consider adding input validation for edge cases...",
  "created_at": "2026-01-06T10:30:00Z"
}
```

## Severity Levels

| Severity | Description | Action |
|----------|-------------|--------|
| critical | Blocking issues, security vulnerabilities | Must fix before completion |
| major | Significant problems, missing functionality | Should fix before completion |
| minor | Style issues, minor improvements | Can defer to later |
| none | No issues found | Proceed to completion |

## State Transitions

```
pending_review → under_review (on review spawn)
under_review → final_review (when all reviews complete)
final_review → completed (when final report produced)
```

## Error Handling

| Error | Action |
|-------|--------|
| Task not in pending_review | Report current status, suggest waiting |
| Review already in progress | Report existing review, suggest waiting |
| Codex unavailable | Report error, suggest manual review |
