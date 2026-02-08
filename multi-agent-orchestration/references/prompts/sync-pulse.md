# Sync Pulse Prompt

## Description

Synchronize AGENT_STATE.json to PROJECT_PULSE.md, updating the human-readable status dashboard.

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| state_file | No | Path to AGENT_STATE.json (default: ./AGENT_STATE.json) |
| pulse_file | No | Path to PROJECT_PULSE.md (default: ./PROJECT_PULSE.md) |

## Instructions

When syncing state to PULSE, follow these steps:

### Step 1: Read Current State
```bash
python skills/multi-agent-orchestration/scripts/sync_pulse.py AGENT_STATE.json PROJECT_PULSE.md --dry-run
```

### Step 2: Update Mental Model Section
1. Extract architecture summary from design.md
2. Update component status based on completed tasks
3. Highlight active work areas

```markdown
## Mental Model

### Architecture
- [x] Authentication module (task-001 completed)
- [ ] User management (task-002 in progress)
- [ ] API gateway (task-003 not started)

### Current Focus
Active implementation of user management module.
```

### Step 3: Update Narrative Delta Section
1. List recently completed tasks (last 24h)
2. Summarize key changes and decisions
3. Note any blockers resolved

```markdown
## Narrative Delta

### Recent Completions
- **task-001**: Authentication module implemented
  - Added JWT token generation
  - Integrated with user database
  - Review completed with no issues

### Key Decisions
- Chose bcrypt for password hashing (security requirement)
```

### Step 4: Update Risks & Debt Section
1. List blocked items from AGENT_STATE.json
2. List pending decisions requiring human input
3. Escalate items pending > 24 hours
4. List deferred fixes

```markdown
## Risks & Debt

### Blocked Items
- **task-005**: Waiting for API specification
  - Blocked since: 2026-01-05
  - Required: API schema from backend team

### Pending Decisions ⚠️ ESCALATED
- **decision-001**: Database choice (pending 26h)
  - Options: PostgreSQL, MongoDB
  - Context: Need to decide before task-006

### Deferred Fixes
- Minor: Add input validation to login form (task-001)
```

### Step 5: Update Semantic Anchors Section
1. Map key code locations from completed tasks
2. Update file references
3. Note important interfaces

```markdown
## Semantic Anchors

### Key Files
- `src/auth/jwt.py` - JWT token handling (task-001)
- `src/auth/password.py` - Password hashing (task-001)

### Interfaces
- `AuthService.authenticate(username, password) -> Token`
- `AuthService.validate_token(token) -> User`
```

### Step 6: Write Updated PULSE
```bash
python skills/multi-agent-orchestration/scripts/sync_pulse.py AGENT_STATE.json PROJECT_PULSE.md
```

## Example Usage

### Natural Language
"Sync state to PULSE document"
"Update the project status dashboard"

### Script
```bash
python skills/multi-agent-orchestration/scripts/sync_pulse.py AGENT_STATE.json PROJECT_PULSE.md
```

### Programmatic
```python
from skills.multi_agent_orchestrator.scripts.sync_pulse import sync_pulse
sync_pulse("AGENT_STATE.json", "PROJECT_PULSE.md")
```

## PULSE Document Structure

```markdown
# PROJECT_PULSE.md

## Mental Model
[Architecture overview and component status]

## Narrative Delta
[Recent changes and decisions]

## Risks & Debt
[Blocked items, pending decisions, deferred fixes]

## Semantic Anchors
[Key code locations and interfaces]

---
Last synced: 2026-01-06T10:30:00Z
```

## Escalation Rules

| Condition | Action |
|-----------|--------|
| Pending decision > 24h | Add ⚠️ ESCALATED marker |
| Blocked item > 48h | Move to top of Risks section |
| Critical review finding | Add to Risks section |
| Multiple blockers on same dependency | Highlight dependency |

## Sync Frequency

| Trigger | Action |
|---------|--------|
| Task completion | Auto-sync |
| Review completion | Auto-sync |
| Blocker added | Auto-sync |
| Manual request | Immediate sync |
| Periodic | Every 30 minutes |

## Error Handling

| Error | Action |
|-------|--------|
| State file not found | Report error, suggest initialization |
| PULSE file not found | Create new PULSE from template |
| Invalid state JSON | Report validation errors |
| Write permission denied | Report error, suggest permissions fix |
