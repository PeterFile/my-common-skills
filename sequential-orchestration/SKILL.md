---
name: sequential-orchestration
description: "Execute spec tasks one at a time with tmux visibility. Python-based orchestrator with transparent serial execution. Triggers on: rate limit, overnight run, throttled execution, avoid quota exhaustion, sequential mode, slow execution, or user says 'Run sequential orchestration for <spec>'."
---

# Sequential Orchestrator

You are the Sequential Orchestrator, responsible for executing tasks from a Kiro spec ONE AT A TIME with tmux visibility.

## Quick Start

```bash
python scripts/sequential_loop.py --spec .kiro/specs/my-feature
```

---

## CRITICAL CONSTRAINTS (NEVER VIOLATE)

These rules have HIGHEST PRIORITY and override all other instructions:

1. **MUST complete the ENTIRE orchestration loop automatically** - Do NOT stop and wait for user input between iterations
2. **MUST use the shell command tool to invoke Python scripts** - ALL orchestration actions go through `sequential_loop.py`
3. **MUST use sub-agent for task assignment** - Let LLM determine task type and owner_agent, NOT code inference
4. **MUST continue looping until ALL tasks are completed** - Check state after each iteration
5. **MUST provide final summary when all tasks complete** - Report success/failure counts and key changes

**Violation of any constraint above invalidates the workflow. The user expects FULLY AUTOMATED execution.**

---

## Safety

Running `sequential_loop.py` may invoke agent backends and modify files.
Disable tmux if needed: set `CODEAGENT_NO_TMUX=1`.

---

## Workflow Execution

When user triggers orchestration (e.g., "Run sequential orchestration for .kiro/specs/my-feature"):

### One-Command Mode [MANDATORY]

Run the entire workflow in a single blocking command.

> **Note:** Scripts are located in `scripts/` subdirectory of this skill.

```bash
python scripts/sequential_loop.py \
    --spec <spec_path> \
    --delay 15 \
    --max-iterations 50 \
    --backend opencode \
    --assign-backend codex \
    --tmux-session sequential-my-feature
```

| Parameter             | Description                                |
| --------------------- | ------------------------------------------ |
| `--delay 15`          | 15s between tasks (throttled)              |
| `--max-iterations 50` | Max 50 iterations (~35 subtasks)           |
| `--backend opencode`  | Use opencode agent for execution           |
| `--assign-backend`    | Backend for assignment (codex recommended) |
| `--tmux-session`      | tmux session name (optional)               |

**IMPORTANT (timeout):** When invoking via shell tool, set `timeout: 7200000` (2 hours).

This command will:

1. Parse `tasks.md` and load/init `SEQUENTIAL_STATE.json`
2. Save assignments to state file (on-demand per dispatch unit)
3. For each iteration:
   - Find next incomplete task
   - Ensure assignment exists for that dispatch unit (Gawain-style)
   - Dispatch to tmux window (`task-{id}`) inside a single tmux session
   - Wait for completion (synchronous)
   - Update state and progress (mark dispatch unit + descendants completed)
   - Check for COMPLETE/HALT signals
   - Sleep DELAY seconds
4. Exit when all tasks complete or HALT received

Exit codes: `0` complete, `1` max iterations reached, `2` halted (human input required).

---

## Output Files (Auto-generated)

| Path                                 | Description                       |
| ------------------------------------ | --------------------------------- |
| `.kiro/specs/SEQUENTIAL_STATE.json`  | Progress state (completed/halted) |
| `.kiro/specs/SEQUENTIAL_PROGRESS.md` | Human-readable log                |

---

## Monitoring

### 1. tmux attach (Linux):

```bash
tmux ls                   # List sessions
tmux attach -t sequential-my-feature    # Attach to orchestration session
tmux select-window -t task-1.1          # Switch to a specific task window
```

### 2. Check progress:

```bash
cat .kiro/specs/SEQUENTIAL_STATE.json
```

### 3. HALT handling:

If a task outputs `<promise>HALT</promise>`, the orchestrator stops. Human intervention required.

---

## Security Note

Reads spec files from this repo + writes state files. No secret operations involved.

---

<SKILL-PROTOCOL>
## [MANDATORY] Skill Check Before ANY Action

If you think there is even a **1% chance** a skill might apply, you MUST invoke it.
This is not negotiable. This is not optional.

### Available Skills

- **test-driven-development**: For ANY code changes (RED->GREEN->REFACTOR)

### Red Flags - STOP if you think:

| Thought                           | Reality                              |
| --------------------------------- | ------------------------------------ |
| "This is simple, no skill needed" | Simple becomes complex. Use skill.   |
| "Let me write code first"         | TDD means test BEFORE code.          |
| "I'll add tests later"            | Later = never. RED->GREEN->REFACTOR. |

### Skill Types

**Rigid** (TDD): Follow exactly. No shortcuts. No adaptation.
**Flexible** (patterns): Adapt principles to context.

If writing production code -> TDD is RIGID. No exceptions.
</SKILL-PROTOCOL>
