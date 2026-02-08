#!/usr/bin/env python3
"""
Single Task Dispatcher for Sequential Orchestration

Dispatches a single task to codeagent-wrapper with tmux visibility.
Synchronously waits for completion and returns result.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from codeagent_utils import resolve_codeagent_wrapper, tmux_enabled, looks_like_tmux_error


# Skill protocol for agent self-judgment
# Uses psychological framing from "using-superpowers" pattern
SKILL_PROTOCOL = """
<SKILL-PROTOCOL>
## [MANDATORY] Skill Check Before ANY Action

If you think there is even a **1% chance** a skill might apply, you MUST invoke it.
This is not negotiable. This is not optional.

### Available Skills
- **test-driven-development**: For ANY code changes (RED->GREEN->REFACTOR)

### Red Flags - STOP if you think:
| Thought | Reality |
|---------|---------|
| "This is simple, no skill needed" | Simple becomes complex. Use skill. |
| "Let me write code first" | TDD means test BEFORE code. |
| "I'll add tests later" | Later = never. RED->GREEN->REFACTOR. |

### Skill Types
**Rigid** (TDD): Follow exactly. No shortcuts. No adaptation.
**Flexible** (patterns): Adapt principles to context.

If writing production code -> TDD is RIGID. No exceptions.
</SKILL-PROTOCOL>
""".strip()


# Agent backend mapping
AGENT_TO_BACKEND = {
    "codex": "codex",
    "gemini": "gemini",
    "codex-review": "codex",
}


def _safe_relpath(path: str, base_dir: Optional[str]) -> str:
    p = Path(path).resolve()
    if base_dir:
        b = Path(base_dir).resolve()
        try:
            return p.relative_to(b).as_posix()
        except ValueError:
            pass
    return p.as_posix()


def _json_from_text(text: str) -> Any:
    decoder = json.JSONDecoder()
    for i, ch in enumerate(text or ""):
        if ch != "{":
            continue
        try:
            obj, _end = decoder.raw_decode(text[i:])
            return obj
        except json.JSONDecodeError:
            continue
    raise ValueError("No JSON object found in output")


def _resolve_timeout_seconds(default_seconds: int) -> int:
    raw = (os.environ.get("CODEX_TIMEOUT") or "").strip()
    if not raw:
        return default_seconds
    try:
        ms = int(raw)
        if ms <= 0:
            return default_seconds
        return max(1, ms // 1000)
    except ValueError:
        return default_seconds


def build_bulk_assignment_prompt(tasks_md_path: str, dispatch_unit_ids: List[str]) -> str:
    """
    Build prompt for sub-agent to assign dispatch units.

    Instead of embedding task details in prompt (which causes confusion),
    we simply provide the tasks.md path and let AI read it directly.

    Args:
        tasks_md_path: Absolute path to tasks.md file
        dispatch_unit_ids: List of dispatch unit task IDs to assign

    Returns:
        Assignment prompt string
    """
    units_list = "\n".join(f"- {tid}" for tid in dispatch_unit_ids)

    return f"""You are assigning dispatch units for sequential orchestration.

## Input

Read the tasks file: @{tasks_md_path}

Dispatch units to assign:
{units_list}

## Rules
- Analyze each task's description and details to determine:
  - **type**: Infer from task semantics:
    - code -> Backend logic, API, database, scripts, algorithms
    - ui -> Frontend, React/Vue components, CSS, pages, forms, styling
    - review -> Code review, audit, property testing
  - **owner_agent**: Based on type:
    - codex -> code tasks
    - gemini -> ui tasks
    - codex-review -> review tasks

## Output

Respond with JSON only:
```json
{{
  "assignments": [
    {{"task_id": "1", "type": "code", "owner_agent": "codex"}},
    {{"task_id": "2", "type": "ui", "owner_agent": "gemini"}}
  ]
}}
```
"""


def ensure_assignments(
    tasks_md_path: str,
    dispatch_unit_ids: List[str],
    state: Dict[str, Any],
    assign_backend: str = "codex",
    assign_opencode_agent: str = "gawain",
    workdir: Optional[str] = None,
) -> Dict[str, Dict[str, str]]:
    """
    Ensure all dispatch units have assignments. Calls LLM once for bulk assignment.
    
    Args:
        tasks_md_path: Absolute path to tasks.md file
        dispatch_unit_ids: List of dispatch unit task IDs
        state: Current state dict (may contain existing assignments)
        assign_backend: Backend for assignment LLM call
        workdir: Working directory
        
    Returns:
        Dict mapping task_id -> {type, owner_agent}
    """
    # Check if assignments already exist in state
    existing = state.get("assignments", {})
    if not isinstance(existing, dict):
        existing = {}
    missing = [tid for tid in dispatch_unit_ids if tid not in existing]
    if not missing:
        return existing
    
    try:
        wrapper_bin = resolve_codeagent_wrapper()
    except FileNotFoundError:
        # Fallback: assign all as code/codex
        for tid in missing:
            existing[tid] = {"type": "code", "owner_agent": "codex"}
        return existing
    
    cwd = workdir or os.getcwd()
    tasks_ref = _safe_relpath(tasks_md_path, cwd)
    prompt = build_bulk_assignment_prompt(tasks_ref, missing)
    env = os.environ.copy()
    if sys.platform.startswith("win") and "CODEAGENT_NO_TMUX" not in env:
        env["CODEAGENT_NO_TMUX"] = "1"
    if assign_backend == "opencode":
        env["CODEAGENT_OPENCODE_AGENT"] = assign_opencode_agent
    
    try:
        result = subprocess.run(
            [wrapper_bin, "--backend", assign_backend, "-"],
            input=prompt,
            capture_output=True,
            text=True,
            cwd=cwd,
            env=env,
            timeout=180,
        )
    except Exception:
        for tid in missing:
            existing[tid] = {"type": "code", "owner_agent": "codex"}
        return existing
    
    if result.returncode != 0:
        for tid in missing:
            existing[tid] = {"type": "code", "owner_agent": "codex"}
        return existing
    
    # Parse JSON from output
    try:
        obj = _json_from_text(result.stdout or "")
        for entry in obj.get("assignments", []):
            task_id = entry.get("task_id")
            if not task_id:
                continue
            existing[task_id] = {
                "type": entry.get("type", "code"),
                "owner_agent": entry.get("owner_agent", "codex"),
            }
    except Exception:
        for tid in missing:
            existing[tid] = {"type": "code", "owner_agent": "codex"}
        return existing
    
    # Fallback for any missing dispatch units
    for tid in missing:
        if tid not in existing:
            existing[tid] = {"type": "code", "owner_agent": "codex"}
    
    return existing


def get_backend_for_agent(owner_agent: str, default: str = "opencode") -> str:
    """
    Get backend for a given owner_agent.
    
    Args:
        owner_agent: Agent name (codex, gemini, codex-review)
        default: Default backend if agent not mapped
        
    Returns:
        Backend name
    """
    return AGENT_TO_BACKEND.get(owner_agent, default)


@dataclass
class DispatchResult:
    """Result of dispatching a task."""
    success: bool
    completed: bool  # Task marked complete
    halted: bool     # Task requested halt
    message: str
    output: str = ""


def build_task_prompt(
    task_id: str,
    description: str,
    details: List[str],
    spec_path: str,
    state_file: str,
    progress_file: str,
    subtasks: Optional[List[Tuple[str, str]]] = None,
) -> str:
    """
    Build the prompt to send to the agent.
    
    Args:
        task_id: Task identifier
        description: Task description
        details: Task detail lines
        spec_path: Path to spec directory
        state_file: Path to state JSON file
        progress_file: Path to progress file
        subtasks: Optional list of (subtask_id, subtask_description) tuples
        
    Returns:
        Formatted prompt string
    """
    lines = [
        "# Sequential Dispatch Unit",
        "",
        "You are executing ONE dispatch unit from a spec.",
        "",
        "## Your Task",
        "",
        f"**Task ID:** {task_id}",
        f"**Description:** {description}",
        "",
    ]
    
    # Show subtasks if this is a parent task
    if subtasks:
        lines.extend([
            "**Subtasks to Complete:**",
            "",
        ])
        for sub_id, sub_desc in subtasks:
            lines.append(f"- {sub_id}: {sub_desc}")
    
    if details:
        lines.append("**Details:**")
        for detail in details:
            lines.append(f"- {detail}")
        lines.append("")
    
    lines.extend([
        "## Inputs",
        "",
        f"- @{spec_path}/requirements.md",
        f"- @{spec_path}/design.md",
        f"- @{spec_path}/tasks.md",
        f"- @{state_file}",
        f"- @{progress_file}",
        "",
        "## Instructions",
        "",
        "1. Read the inputs to understand context",
    ])
    
    if subtasks:
        lines.append("2. Implement **ALL subtasks** listed above (do not skip)")
    else:
        lines.append("2. Implement this **single task** completely")
    
    lines.extend([
        "3. Run quality checks (typecheck, lint, test)",
        "4. Fix any issues",
        "5. Commit if your workflow requires it",
        "",
        "## Completion Signal",
        "",
        "When you have **successfully completed** this task, include this exact string in your response:",
        "",
        "```",
        "<promise>TASK_DONE</promise>",
        "```",
        "",
        "If you **cannot proceed** (missing dependency, unclear requirement, blocked), include:",
        "",
        "```",
        "<promise>HALT</promise>",
        "```",
        "",
        "## Critical Rules",
        "",
    ])
    
    if subtasks:
        lines.extend([
            f"- Complete **ALL {len(subtasks)} subtasks** before signaling TASK_DONE",
            "- Do NOT signal completion until ALL subtasks are done",
        ])
    else:
        lines.append("- Work on **this ONE task only**")
    
    lines.extend([
        "- Do NOT start other tasks",
        "- Do NOT commit broken code",
        "",
        "If you write production code, use test-driven-development (RED->GREEN->REFACTOR) and run tests.",
    ])
    
    return "\n".join(lines)


def dispatch_task(
    task_id: str,
    description: str,
    details: List[str],
    spec_path: str,
    state_file: str,
    progress_file: str,
    backend: str = "opencode",
    workdir: Optional[str] = None,
    timeout_seconds: int = 7200,
    subtasks: Optional[List[Tuple[str, str]]] = None,
    tmux_session: Optional[str] = None,
) -> DispatchResult:
    """
    Dispatch a single task to codeagent-wrapper.
    
    Creates a tmux window (if enabled) and runs the task synchronously.
    
    Args:
        task_id: Task identifier
        description: Task description
        details: Task detail lines
        spec_path: Path to spec directory
        state_file: Path to state JSON file
        progress_file: Path to progress file
        backend: Agent backend (opencode, codex, claude, gemini)
        workdir: Working directory for execution
        timeout_seconds: Timeout for task execution
        subtasks: Optional list of (subtask_id, subtask_description) for parent tasks
        
    Returns:
        DispatchResult with success/completion status
    """
    try:
        wrapper_bin = resolve_codeagent_wrapper()
    except FileNotFoundError as e:
        return DispatchResult(
            success=False,
            completed=False,
            halted=False,
            message=str(e),
        )
    
    cwd = workdir or os.getcwd()
    rel_spec = _safe_relpath(spec_path, cwd)
    rel_state = _safe_relpath(state_file, cwd)
    rel_progress = _safe_relpath(progress_file, cwd)

    prompt = build_task_prompt(
        task_id=task_id,
        description=description,
        details=details,
        spec_path=rel_spec,
        state_file=rel_state,
        progress_file=rel_progress,
        subtasks=subtasks,
    )

    wrapper_task_id = f"task-{task_id}"
    heredoc_input = "\n".join([
        "---TASK---",
        f"id: {wrapper_task_id}",
        f"backend: {backend}",
        f"workdir: {cwd}",
        f"target_window: {wrapper_task_id}",
        "---CONTENT---",
        prompt.rstrip(),
        "",
    ])

    use_tmux = tmux_enabled() and not sys.platform.startswith("win") and shutil.which("tmux") is not None
    session_name = (tmux_session or "sequential").strip() if use_tmux else ""

    base_cmd = [wrapper_bin, "--parallel", "--full-output"]
    cmd_no_tmux = base_cmd
    cmd = cmd_no_tmux
    if session_name:
        cmd = base_cmd + ["--tmux-session", session_name, "--tmux-no-main-window"]

    env = os.environ.copy()
    if sys.platform.startswith("win") and "CODEAGENT_NO_TMUX" not in env:
        env["CODEAGENT_NO_TMUX"] = "1"

    effective_timeout = _resolve_timeout_seconds(timeout_seconds)

    print(f"[dispatch] Task {task_id}: {description}")
    print(f"[dispatch] Backend: {backend}")
    if session_name:
        print(f"[dispatch] Tmux: session={session_name} window={wrapper_task_id}")

    try:
        result = subprocess.run(
            cmd,
            input=heredoc_input,
            capture_output=True,
            text=True,
            cwd=cwd,
            env=env,
            timeout=effective_timeout,
        )
        if session_name and result.returncode != 0:
            combined = (result.stderr or "") + "\n" + (result.stdout or "")
            if looks_like_tmux_error(combined):
                result = subprocess.run(
                    cmd_no_tmux,
                    input=heredoc_input,
                    capture_output=True,
                    text=True,
                    cwd=cwd,
                    env=env,
                    timeout=effective_timeout,
                )
    except subprocess.TimeoutExpired:
        return DispatchResult(
            success=False,
            completed=False,
            halted=False,
            message=f"Task {task_id} timed out after {effective_timeout}s",
        )
    except Exception as e:
        return DispatchResult(
            success=False,
            completed=False,
            halted=False,
            message=f"Dispatch failed: {e}",
        )

    stdout = result.stdout or ""
    stderr = result.stderr or ""

    try:
        report = _json_from_text(stdout)
    except Exception:
        return DispatchResult(
            success=False,
            completed=False,
            halted=False,
            message=f"Task {task_id} failed (exit {result.returncode}): {stderr.strip() or stdout.strip()}",
            output=stdout,
        )

    task_results = report.get("task_results") or report.get("tasks") or []
    if not isinstance(task_results, list) or not task_results:
        return DispatchResult(
            success=False,
            completed=False,
            halted=False,
            message=f"Task {task_id}: invalid execution report (no task_results)",
            output=stdout,
        )

    tr = next((r for r in task_results if isinstance(r, dict) and r.get("task_id") == wrapper_task_id), None)
    if tr is None:
        tr = task_results[0] if isinstance(task_results[0], dict) else {}

    message_text = tr.get("message", "") if isinstance(tr, dict) else ""
    err_text = tr.get("error", "") if isinstance(tr, dict) else ""
    exit_code = tr.get("exit_code", result.returncode) if isinstance(tr, dict) else result.returncode

    completed = "<promise>TASK_DONE</promise>" in message_text or "<promise>COMPLETE</promise>" in message_text
    halted = "<promise>HALT</promise>" in message_text

    if halted:
        return DispatchResult(
            success=True,
            completed=False,
            halted=True,
            message=f"Task {task_id} halted - human input required",
            output=message_text,
        )

    if completed or exit_code == 0:
        return DispatchResult(
            success=True,
            completed=True,
            halted=False,
            message=f"Task {task_id} completed successfully",
            output=message_text,
        )

    return DispatchResult(
        success=False,
        completed=False,
        halted=False,
        message=f"Task {task_id} failed (exit {exit_code}): {err_text.strip() or stderr.strip()}",
        output=message_text,
    )


if __name__ == "__main__":
    # Simple test
    result = dispatch_task(
        task_id="test",
        description="Test task",
        details=["Detail 1", "Detail 2"],
        spec_path=".",
        state_file="state.json",
        progress_file="progress.txt",
    )
    print(f"Result: {result}")
