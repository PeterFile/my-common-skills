#!/usr/bin/env python3
"""
Sequential Orchestration Loop

Main orchestration runner for sequential (serial) task execution.
Executes tasks one at a time with tmux visibility.

Usage:
    python sequential_loop.py --spec .kiro/specs/my-feature [--delay 5] [--max-iterations 50]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add script directory to path
sys.path.insert(0, str(Path(__file__).parent))

from spec_parser import parse_tasks_md, get_next_incomplete_task, all_tasks_complete, Task, get_subtask_list
from dispatch_task import dispatch_task, DispatchResult, ensure_assignments, get_backend_for_agent


def _sanitize_tmux_session(name: str) -> str:
    name = (name or "").strip()
    if not name:
        return "sequential"
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")
    sanitized = "".join(ch if ch in allowed else "-" for ch in name)
    sanitized = sanitized.strip("-")
    return sanitized or "sequential"


def load_state(state_file: Path) -> Dict[str, Any]:
    """Load state from JSON file."""
    if not state_file.exists():
        return {"completed": [], "halted": False, "started_at": None}
    return json.loads(state_file.read_text(encoding="utf-8"))


def save_state(state_file: Path, state: Dict[str, Any]) -> None:
    """Save state to JSON file atomically."""
    tmp_file = state_file.with_suffix(".tmp")
    tmp_file.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp_file.replace(state_file)


def append_progress(progress_file: Path, iteration: int, task: Task, result: DispatchResult) -> None:
    """Append progress entry to progress file."""
    timestamp = datetime.now(timezone.utc).isoformat()
    
    status = "Completed" if result.completed else ("Halted" if result.halted else "Failed")
    
    entry = f"""
## Iteration {iteration}
- **Task:** {task.task_id} - {task.description}
- **Status:** {status}
- **Time:** {timestamp}
- **Message:** {result.message}
"""
    
    with open(progress_file, "a", encoding="utf-8") as f:
        f.write(entry)


def initialize_progress(progress_file: Path, spec_path: str) -> None:
    """Initialize progress file with header."""
    timestamp = datetime.now(timezone.utc).isoformat()
    
    header = f"""# Sequential Execution Progress

**Spec:** {spec_path}
**Started:** {timestamp}

---
"""
    
    progress_file.write_text(header, encoding="utf-8")


def run_sequential_loop(
    spec_path: str,
    max_iterations: int = 50,
    delay: float = 5.0,
    backend: str = "opencode",
    workdir: Optional[str] = None,
    assign_backend: Optional[str] = None,
    assign_opencode_agent: str = "gawain",
    tmux_session: Optional[str] = None,
) -> int:
    """
    Run the sequential orchestration loop.
    
    Args:
        spec_path: Path to spec directory containing requirements.md, design.md, tasks.md
        max_iterations: Maximum number of iterations
        delay: Seconds to wait between iterations
        backend: Agent backend to use
        workdir: Working directory for task execution
        
    Returns:
        Exit code: 0 = complete, 1 = max iterations, 2 = halted
    """
    spec_dir = Path(spec_path).resolve()
    
    # Validate spec directory
    tasks_md = spec_dir / "tasks.md"
    if not tasks_md.exists():
        print(f"[sequential] ERROR: tasks.md not found at {tasks_md}")
        return 1
    
    # State files in parent directory (like multi-agent)
    parent_dir = spec_dir.parent
    state_file = parent_dir / "SEQUENTIAL_STATE.json"
    progress_file = parent_dir / "SEQUENTIAL_PROGRESS.md"
    
    # Parse tasks
    try:
        tasks = parse_tasks_md(str(tasks_md))
    except Exception as e:
        print(f"[sequential] ERROR: Failed to parse tasks.md: {e}")
        return 1
    
    print()
    print("[sequential] Sequential Orchestration")
    print(f"[sequential] spec={spec_dir}")
    print(f"[sequential] state_file={state_file}")
    print(f"[sequential] progress_file={progress_file}")
    print(f"[sequential] tasks_total={len(tasks)}")
    print(f"[sequential] max_iterations={max_iterations} delay={delay}s backend={backend}")
    print()
    
    # Load or initialize state
    state = load_state(state_file)
    if not state.get("started_at"):
        state["started_at"] = datetime.now(timezone.utc).isoformat()
        save_state(state_file, state)
        initialize_progress(progress_file, str(spec_dir))
    
    raw_completed = state.get("completed", [])
    if not isinstance(raw_completed, list):
        raw_completed = []
    completed_ids: List[str] = []
    completed_set = set()
    for raw_id in raw_completed:
        tid = str(raw_id)
        if tid in completed_set:
            continue
        completed_set.add(tid)
        completed_ids.append(tid)

    assignments = state.get("assignments", {})
    if not isinstance(assignments, dict):
        assignments = {}
    state["assignments"] = assignments

    if workdir:
        effective_workdir = workdir
    else:
        # Spec dir is typically: <repo>/.kiro/specs/<name>
        if spec_dir.parent.name == "specs" and spec_dir.parent.parent.name == ".kiro":
            effective_workdir = str(spec_dir.parent.parent.parent)
        else:
            effective_workdir = str(spec_dir.parent.parent) if len(spec_dir.parents) > 1 else str(spec_dir.parent)
    effective_assign_backend = assign_backend or backend
    session_name = _sanitize_tmux_session(tmux_session or f"sequential-{spec_dir.name}")

    print(f"[sequential] workdir={effective_workdir}")
    print(f"[sequential] assign_backend={effective_assign_backend} assign_opencode_agent={assign_opencode_agent}")
    print(f"[sequential] tmux_session={session_name}")
    print()
    
    # Main loop
    for iteration in range(1, max_iterations + 1):
        print()
        print("===========================================================")
        print(f"  Iteration {iteration} of {max_iterations}")
        print("===========================================================")
        
        # Check if all done
        if all_tasks_complete(tasks, completed_ids):
            print()
            print("[sequential] All tasks completed!")
            
            # Update progress
            timestamp = datetime.now(timezone.utc).isoformat()
            with open(progress_file, "a", encoding="utf-8") as f:
                f.write(f"\n---\n\n**Completed:** {timestamp}\n")
            
            state["completed_at"] = timestamp
            save_state(state_file, state)
            return 0
        
        # Find next task
        next_task = get_next_incomplete_task(tasks, completed_ids)
        
        if not next_task:
            print("[sequential] No executable tasks found. All remaining tasks may be blocked.")
            return 2
        
        print(f"[sequential] Next task: {next_task.task_id} - {next_task.description}")
        
        # Build subtask list if this is a parent task
        task_map = {t.task_id: t for t in tasks}
        subtask_objs = get_subtask_list(next_task, task_map)
        subtasks = [(s.task_id, s.description) for s in subtask_objs] if subtask_objs else None
        
        if subtasks:
            print(f"[sequential] Parent task with {len(subtasks)} subtasks: {[s[0] for s in subtasks]}")
        
        # Ensure assignment exists for this dispatch unit (Gawain-style)
        if next_task.task_id not in assignments:
            assignments = ensure_assignments(
                tasks_md_path=str(tasks_md),
                dispatch_unit_ids=[next_task.task_id],
                state=state,
                assign_backend=effective_assign_backend,
                assign_opencode_agent=assign_opencode_agent,
                workdir=effective_workdir,
            )
            state["assignments"] = assignments
            save_state(state_file, state)

        # Look up assignment from state
        task_assignment = assignments.get(next_task.task_id, {"type": "code", "owner_agent": "codex"})
        task_type = task_assignment.get("type", "code")
        owner_agent = task_assignment.get("owner_agent", "codex")
        effective_backend = get_backend_for_agent(owner_agent, default=backend)
        print(f"[sequential] Assignment: type={task_type}, agent={owner_agent} -> backend={effective_backend}")
        
        # Dispatch task
        result = dispatch_task(
            task_id=next_task.task_id,
            description=next_task.description,
            details=next_task.details,
            spec_path=str(spec_dir),
            state_file=str(state_file),
            progress_file=str(progress_file),
            backend=effective_backend,
            workdir=effective_workdir,  # Go up to project root
            subtasks=subtasks,
            tmux_session=session_name,
        )
        
        # Log progress
        append_progress(progress_file, iteration, next_task, result)
        
        # Handle result
        if result.halted:
            print()
            print("[sequential] HALT - human input required")
            state["halted"] = True
            state["halted_at"] = datetime.now(timezone.utc).isoformat()
            state["halted_task"] = next_task.task_id
            save_state(state_file, state)
            return 2
        
        if result.completed:
            prefix = f"{next_task.task_id}."
            done_ids = [
                t.task_id for t in tasks
                if t.task_id == next_task.task_id or t.task_id.startswith(prefix)
            ]
            for tid in done_ids:
                if tid in completed_set:
                    continue
                completed_set.add(tid)
                completed_ids.append(tid)
            state["completed"] = completed_ids
            save_state(state_file, state)
            print(f"[sequential] Task {next_task.task_id} completed")
        else:
            print(f"[sequential] Task {next_task.task_id} failed: {result.message}")
            # Continue to next iteration anyway - agent might have made progress
        
        # Check if all done after this task
        if all_tasks_complete(tasks, completed_ids):
            print()
            print("[sequential] All tasks completed!")
            timestamp = datetime.now(timezone.utc).isoformat()
            state["completed_at"] = timestamp
            save_state(state_file, state)
            return 0
        
        # Delay before next iteration
        if delay > 0:
            print(f"[sequential] Sleeping {delay}s before next iteration...")
            time.sleep(delay)
    
    print()
    print(f"[sequential] Reached max iterations ({max_iterations}) without completing all tasks.")
    print(f"   Check {state_file} for remaining tasks.")
    return 1


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Sequential Orchestration - Execute tasks one at a time with tmux visibility"
    )
    parser.add_argument(
        "--spec",
        required=True,
        help="Path to spec directory (containing requirements.md, design.md, tasks.md)",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=50,
        help="Maximum number of iterations (default: 50)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=5.0,
        help="Seconds to wait between iterations (default: 5)",
    )
    parser.add_argument(
        "--backend",
        default="opencode",
        choices=["opencode", "codex", "claude", "gemini"],
        help="Agent backend to use (default: opencode)",
    )
    parser.add_argument(
        "--assign-backend",
        choices=["opencode", "codex", "claude", "gemini"],
        help="Backend used for assignment (default: same as --backend)",
    )
    parser.add_argument(
        "--assign-opencode-agent",
        default="gawain",
        help="OpenCode agent for assignment when --assign-backend=opencode (default: gawain)",
    )
    parser.add_argument(
        "--tmux-session",
        help="tmux session name for visibility (default: sequential-<spec_dir_name>)",
    )
    parser.add_argument(
        "--workdir",
        help="Working directory for task execution (default: inferred repo root)",
    )
    
    args = parser.parse_args(argv)
    
    return run_sequential_loop(
        spec_path=args.spec,
        max_iterations=args.max_iterations,
        delay=args.delay,
        backend=args.backend,
        workdir=args.workdir,
        assign_backend=args.assign_backend,
        assign_opencode_agent=args.assign_opencode_agent,
        tmux_session=args.tmux_session,
    )


if __name__ == "__main__":
    sys.exit(main())
