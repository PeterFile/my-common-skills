#!/usr/bin/env python3
"""
Batch Dispatch Script

Dispatches ready tasks to worker agents via codeagent-wrapper --parallel.
- Collects tasks with no unmet dependencies
- Builds task config for codeagent-wrapper
- Invokes codeagent-wrapper synchronously
- Processes Execution Report
- Detects file conflicts and partitions tasks into safe batches
- Dispatches parent tasks (dispatch units) with their subtasks
- Expands parent task dependencies to subtasks
- Uses strict dependency completion (only 'completed' status satisfies dependencies)

Requirements: 1.1, 1.2, 1.3, 1.4, 1.6, 1.7, 2.3, 2.4, 2.5, 2.6, 2.7, 9.1, 9.3, 9.4, 9.10, 13.1, 13.3, 13.4
"""

import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Any, Set

# Add script directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import update_parent_statuses for parent status aggregation (Req 1.3, 1.4, 1.5)
from init_orchestration import update_parent_statuses

# Import task filtering and dependency expansion from spec_parser (Req 1.1, 1.2, 1.6, 1.7)
from spec_parser import (
    is_leaf_task,
    is_dispatch_unit,
    get_dispatchable_units,
    expand_dependencies,
    Task,
)

# Import fix loop processing (Req 3.1, 4.6)
from fix_loop import process_fix_loop, get_fix_required_tasks, on_fix_task_complete, rollback_fix_dispatch

# Import codeagent-wrapper helpers (PATH/local bin resolution; tmux fallback)
from codeagent_wrapper_utils import resolve_codex_timeout_seconds, resolve_codeagent_wrapper, looks_like_tmux_missing

# Configure logging
logger = logging.getLogger(__name__)


# Agent backend mapping
AGENT_TO_BACKEND = {
    "codex": "codex",
    "gemini": "gemini",
    "codex-review": "codex",
}

# Skill protocol for agent self-judgment
# Uses psychological framing from "using-superpowers" pattern
SKILL_PROTOCOL = """
<SKILL-PROTOCOL>
## [MANDATORY] Skill Check Before ANY Action

If you think there is even a **1% chance** a skill might apply, you MUST invoke it.
This is not negotiable. This is not optional.

### Available Skills
- **test-driven-development**: For ANY code changes (RED→GREEN→REFACTOR)

### Red Flags - STOP if you think:
| Thought | Reality |
|---------|---------|
| "This is simple, no skill needed" | Simple becomes complex. Use skill. |
| "Let me write code first" | TDD means test BEFORE code. |
| "I'll add tests later" | Later = never. RED→GREEN→REFACTOR. |

### Skill Types
**Rigid** (TDD): Follow exactly. No shortcuts. No adaptation.
**Flexible** (patterns): Adapt principles to context.

If writing production code → TDD is RIGID. No exceptions.
</SKILL-PROTOCOL>
""".strip()


@dataclass
class FileConflict:
    """
    Represents a file conflict between two tasks.
    
    Requirements: 2.3, 2.4
    """
    task_a: str
    task_b: str
    files: List[str]
    conflict_type: str  # "write-write"
    
    def __str__(self) -> str:
        return f"FileConflict({self.task_a} <-> {self.task_b}: {', '.join(self.files)})"


@dataclass
class SubtaskInfo:
    """Information about a subtask within a dispatch unit."""
    task_id: str
    description: str
    details: List[str] = field(default_factory=list)
    is_optional: bool = False


@dataclass
class DispatchPayload:
    """Payload for dispatching a task group to an agent."""
    dispatch_unit_id: str
    description: str
    subtasks: List[SubtaskInfo]
    spec_path: str
    metadata: Dict[str, Any] = field(default_factory=dict)


def _task_id_sort_key(task_id: str) -> List[Any]:
    """Sort key for task IDs like '1.2.3' using numeric ordering."""
    key: List[Any] = []
    for part in task_id.split("."):
        if part.isdigit():
            key.append(int(part))
        else:
            key.append(part)
    return key


def build_dispatch_payload(
    dispatch_unit: Dict[str, Any],
    all_tasks: List[Dict[str, Any]],
    spec_path: str
) -> DispatchPayload:
    """
    Build dispatch payload for a dispatch unit.

    For parent tasks: includes all subtasks in order.
    For standalone tasks: includes the task as a single-item work unit.

    Requirements: 5.1, 5.2, 5.3
    """
    task_id = dispatch_unit["task_id"]
    subtask_ids = dispatch_unit.get("subtasks", [])

    task_map = {t.get("task_id"): t for t in all_tasks}
    subtasks: List[SubtaskInfo] = []

    if subtask_ids:
        for sid in sorted(subtask_ids, key=_task_id_sort_key):
            st = task_map.get(sid)
            if not st:
                continue
            subtasks.append(SubtaskInfo(
                task_id=st.get("task_id", ""),
                description=st.get("description", ""),
                details=st.get("details", []),
                is_optional=st.get("is_optional", False),
            ))
    else:
        subtasks.append(SubtaskInfo(
            task_id=task_id,
            description=dispatch_unit.get("description", ""),
            details=dispatch_unit.get("details", []),
            is_optional=dispatch_unit.get("is_optional", False),
        ))

    return DispatchPayload(
        dispatch_unit_id=task_id,
        description=dispatch_unit.get("description", ""),
        subtasks=subtasks,
        spec_path=spec_path,
        metadata={
            "criticality": dispatch_unit.get("criticality"),
            "writes": dispatch_unit.get("writes", []),
            "reads": dispatch_unit.get("reads", []),
        }
    )


def has_file_manifest(task: Dict[str, Any]) -> bool:
    """
    Check if task has a file manifest (writes or reads declared).
    
    Requirements: 2.5
    """
    return bool(task.get("writes")) or bool(task.get("reads"))


def detect_file_conflicts(tasks: List[Dict[str, Any]]) -> List[FileConflict]:
    """
    Detect file write conflicts between tasks.
    
    Returns list of conflicts that would occur if tasks run in parallel.
    Only detects write-write conflicts (two tasks writing to same file).
    
    Requirements: 2.3, 2.4
    
    Args:
        tasks: List of task dictionaries with optional 'writes' field
        
    Returns:
        List of FileConflict objects describing detected conflicts
    """
    conflicts = []
    
    for i, task_a in enumerate(tasks):
        writes_a = set(task_a.get("writes") or [])
        
        for task_b in tasks[i+1:]:
            writes_b = set(task_b.get("writes") or [])
            
            # Check write-write conflicts
            shared_writes = writes_a & writes_b
            if shared_writes:
                conflicts.append(FileConflict(
                    task_a=task_a["task_id"],
                    task_b=task_b["task_id"],
                    files=list(shared_writes),
                    conflict_type="write-write"
                ))
    
    return conflicts


def partition_by_conflicts(
    tasks: List[Dict[str, Any]],
    log: Optional[logging.Logger] = None
) -> List[List[Dict[str, Any]]]:
    """
    Partition tasks into conflict-free batches.
    
    Rules:
    - Tasks with write-write conflicts are placed in separate batches
    - Tasks without ANY file manifest (no writes AND no reads) are executed serially
    - Tasks with only reads (no writes) can be batched with non-conflicting write tasks
    - Tasks with non-conflicting writes can be batched together
    
    Batches are guaranteed to run sequentially (batch N completes before batch N+1 starts).
    
    Requirements: 2.3, 2.4, 2.5, 2.6, 2.7
    
    Args:
        tasks: List of task dictionaries
        log: Optional logger for warnings
        
    Returns:
        List of batches, where each batch is a list of tasks safe to run in parallel
    """
    if log is None:
        log = logger
    
    # Categorize tasks
    no_manifest_tasks = []      # No writes AND no reads - serial for safety
    safe_tasks = []             # Has reads only OR has writes - can check conflicts
    
    for task in tasks:
        if not task.get("writes") and not task.get("reads"):
            no_manifest_tasks.append(task)
        else:
            safe_tasks.append(task)
    
    batches: List[List[Dict[str, Any]]] = []
    
    # Safe tasks (with manifest): partition by write conflicts
    if safe_tasks:
        # Only tasks with writes can have conflicts
        write_tasks = [t for t in safe_tasks if t.get("writes")]
        read_only_tasks = [t for t in safe_tasks if not t.get("writes")]
        
        conflicts = detect_file_conflicts(write_tasks)
        conflict_pairs: Set[tuple] = {(c.task_a, c.task_b) for c in conflicts}
        conflict_pairs.update({(c.task_b, c.task_a) for c in conflicts})
        
        # Log warnings for conflicts (Req 2.7)
        if conflicts and log:
            for conflict in conflicts:
                log.warning(
                    f"File conflict detected between {conflict.task_a} and {conflict.task_b}: "
                    f"{', '.join(conflict.files)}. Tasks will be serialized."
                )
        
        # Greedy coloring to partition write tasks into non-conflicting batches
        assigned: Set[str] = set()
        
        for task in write_tasks:
            task_id = task["task_id"]
            if task_id in assigned:
                continue
            
            # Find a batch where this task has no conflicts
            placed = False
            for batch in batches:
                batch_ids = {t["task_id"] for t in batch}
                if not any((task_id, bid) in conflict_pairs for bid in batch_ids):
                    batch.append(task)
                    assigned.add(task_id)
                    placed = True
                    break
            
            if not placed:
                batches.append([task])
                assigned.add(task_id)
        
        # Read-only tasks can be added to any batch (no write conflicts)
        # Add them to the first batch for maximum parallelism (Req 2.6)
        if read_only_tasks:
            if batches:
                batches[0].extend(read_only_tasks)
            else:
                batches.append(read_only_tasks)
    
    # No-manifest tasks run serially (each in own batch) - conservative default (Req 2.5)
    for task in no_manifest_tasks:
        if log:
            log.info(f"Task {task['task_id']} has no file manifest, executing serially for safety.")
        batches.append([task])
    
    return batches


@dataclass
class TaskConfig:
    """
    Task configuration for codeagent-wrapper.
    
    Supports two dispatch modes:
    1. Dispatch Unit Mode: Parent task with subtasks - agent executes all subtasks sequentially
    2. Standalone Mode: Single task without subtasks - traditional dispatch
    
    Requirements: 5.3
    """
    task_id: str
    backend: str
    workdir: str
    content: str
    dependencies: List[str] = field(default_factory=list)
    target_window: str = ""
    # Dispatch unit fields (Requirement 5.3)
    subtasks: List[str] = field(default_factory=list)
    is_dispatch_unit: bool = False
    
    def to_heredoc(self) -> str:
        """
        Convert to heredoc format for codeagent-wrapper.
        
        For dispatch units (parent tasks with subtasks), includes:
        - is_dispatch_unit: true
        - subtasks: comma-separated list of subtask IDs
        
        For standalone tasks, maintains backward compatibility with existing format.
        
        Requirements: 5.3
        """
        lines = [
            "---TASK---",
            f"id: {self.task_id}",
            f"backend: {self.backend}",
            f"workdir: {self.workdir}",
        ]
        if self.dependencies:
            lines.append(f"dependencies: {','.join(self.dependencies)}")
        if self.target_window:
            lines.append(f"target_window: {self.target_window}")
        
        # Add dispatch unit fields if this is a parent task dispatch
        if self.is_dispatch_unit:
            lines.append("is_dispatch_unit: true")
            if self.subtasks:
                lines.append(f"subtasks: {','.join(self.subtasks)}")
        
        lines.append("---CONTENT---")
        lines.append(self.content)
        return "\n".join(lines)


@dataclass
class ExecutionReport:
    """Execution report from codeagent-wrapper"""
    success: bool
    tasks_completed: int
    tasks_failed: int
    task_results: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class DispatchResult:
    """Result of batch dispatch"""
    success: bool
    message: str
    tasks_dispatched: int = 0
    execution_report: Optional[ExecutionReport] = None
    errors: List[str] = field(default_factory=list)


def load_agent_state(state_file: str) -> Dict[str, Any]:
    """Load AGENT_STATE.json"""
    with open(state_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_agent_state(state_file: str, state: Dict[str, Any]) -> None:
    """Save AGENT_STATE.json atomically"""
    tmp_file = state_file + ".tmp"
    with open(tmp_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)
    os.replace(tmp_file, state_file)


def get_completed_task_ids(state: Dict[str, Any], strict: bool = True) -> Set[str]:
    """
    Get set of task IDs that satisfy dependencies.
    
    Args:
        state: The AGENT_STATE dictionary
        strict: If True (default), only 'completed' status satisfies dependencies.
                If False, also includes 'pending_review', 'under_review', 'final_review'.
    
    Returns:
        Set of task IDs that are considered "complete" for dependency purposes.
    
    Requirements: 13.1, 13.3, 13.4
    
    Rationale for strict=True default:
    - Prevents downstream tasks from starting before review passes
    - If a task enters fix_required, downstream tasks haven't started yet
    - Ensures fix loop doesn't cause cascading issues with already-started tasks
    - More conservative approach that maintains correctness
    
    When strict=False might be used:
    - Legacy compatibility
    - When review is expected to always pass (low-risk changes)
    - When parallelism is more important than strict correctness
    """
    completed = set()
    for task in state.get("tasks", []):
        status = task.get("status", "")
        if strict:
            # Only 'completed' status satisfies dependencies (Req 13.3)
            if status == "completed":
                completed.add(task["task_id"])
        else:
            # Legacy behavior: review states also satisfy dependencies
            if status in ["completed", "pending_review", "under_review", "final_review"]:
                completed.add(task["task_id"])
    return completed


def _dict_to_task_like(task_dict: Dict[str, Any]) -> Any:
    """
    Convert a task dictionary to a Task-like object for use with spec_parser functions.
    
    This creates a simple object with the attributes needed by is_leaf_task() and
    expand_dependencies() without requiring a full Task dataclass.
    """
    class TaskLike:
        def __init__(self, d: Dict[str, Any]):
            self.task_id = d.get("task_id", "")
            self.subtasks = d.get("subtasks", [])
            self.dependencies = d.get("dependencies", [])
            self.status = d.get("status", "not_started")
            self.is_optional = d.get("is_optional", False)
            self.parent_id = d.get("parent_id")
    return TaskLike(task_dict)


def get_ready_tasks(state: Dict[str, Any], strict_dependencies: bool = True) -> List[Dict[str, Any]]:
    """
    Get leaf tasks ready for execution (no unmet dependencies).
    
    Rules:
    1. Task must be a leaf task (no subtasks) - Req 1.1, 1.2
    2. Task must not be completed or in progress
    3. All dependencies must be satisfied (including expanded parent deps) - Req 1.6, 1.7
    4. Optional tasks are skipped
    
    Args:
        state: The AGENT_STATE dictionary
        strict_dependencies: If True (default), only 'completed' status satisfies dependencies.
                            If False, also includes review states (legacy behavior).
    
    Requirements: 1.1, 1.2, 1.3, 1.6, 1.7, 13.3, 13.4
    """
    completed = get_completed_task_ids(state, strict=strict_dependencies)
    ready = []
    
    # Build task map for dependency expansion
    task_map = {}
    for task_dict in state.get("tasks", []):
        task_like = _dict_to_task_like(task_dict)
        task_map[task_like.task_id] = task_like
    
    for task_dict in state.get("tasks", []):
        task_like = _dict_to_task_like(task_dict)
        
        # Skip parent tasks (they have subtasks) - Req 1.1, 1.2
        if not is_leaf_task(task_like):
            continue
        
        # Skip non-startable tasks
        if task_dict.get("status") != "not_started":
            continue
        
        # Skip optional tasks (marked with is_optional)
        if task_dict.get("is_optional", False):
            continue
        
        # Expand and check dependencies - Req 1.6, 1.7
        dependencies = task_dict.get("dependencies", [])
        expanded_deps = expand_dependencies(dependencies, task_map)
        
        if all(dep in completed for dep in expanded_deps):
            ready.append(task_dict)
    
    return ready


def get_dispatchable_units_from_state(
    state: Dict[str, Any],
    strict_dependencies: bool = True
) -> List[Dict[str, Any]]:
    """
    Get dispatch units ready for execution (no unmet dependencies).

    Dispatch units are:
    - Parent tasks (have subtasks), OR
    - Standalone tasks (no parent, no subtasks)

    Leaf tasks with parents are excluded.

    Args:
        state: The AGENT_STATE dictionary
        strict_dependencies: If True (default), only 'completed' status satisfies
                             dependencies. If False, includes review states.

    Returns:
        List of dispatchable task dictionaries ready to execute.

    Requirements: 1.1, 1.2, 1.3, 4.1, 4.3, 4.4, 13.3, 13.4
    """
    completed = get_completed_task_ids(state, strict=strict_dependencies)

    # Build task map for dependency expansion
    task_like_map = {}
    for task_dict in state.get("tasks", []):
        task_like = _dict_to_task_like(task_dict)
        task_like_map[task_like.task_id] = task_like

    dispatchable = get_dispatchable_units(list(task_like_map.values()), completed)
    dispatchable_ids = {t.task_id for t in dispatchable}

    ready_units = []
    for task_dict in state.get("tasks", []):
        task_id = task_dict.get("task_id")
        if task_id not in dispatchable_ids:
            continue
        # Skip optional tasks
        if task_dict.get("is_optional", False):
            continue
        # Ensure task is not_started (guard against string status mismatch)
        if task_dict.get("status") != "not_started":
            continue
        ready_units.append(task_dict)

    return ready_units


def allocate_windows(
    dispatch_units: List[Dict[str, Any]],
    max_windows: int = 9,
    existing_mapping: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """
    Allocate tmux windows for dispatch units.

    Returns mapping of dispatch_unit_id -> window_name.
    Each dispatch unit gets exactly one window.

    Requirements: 6.1, 6.3
    """
    window_mapping: Dict[str, str] = {}
    existing_mapping = existing_mapping or {}

    for unit in dispatch_units:
        task_id = unit.get("task_id", "")
        if not task_id or task_id in window_mapping:
            continue
        if len(window_mapping) >= max_windows:
            break
        window_name = existing_mapping.get(task_id) or f"task-{task_id}"
        window_mapping[task_id] = window_name

    return window_mapping


def apply_window_allocation(
    state: Dict[str, Any],
    dispatch_units: List[Dict[str, Any]],
    max_windows: int = 9
) -> Dict[str, str]:
    """
    Ensure dispatch units have target_window assigned.

    Uses existing state window_mapping when available, otherwise assigns
    task-{task_id}. Does NOT assign windows for non-dispatch units.
    """
    existing_mapping = state.get("window_mapping", {}) if state else {}
    window_mapping = allocate_windows(
        dispatch_units,
        max_windows=max_windows,
        existing_mapping=existing_mapping
    )

    for task in dispatch_units:
        task_id = task.get("task_id", "")
        if not task_id:
            continue
        if not task.get("target_window") and task_id in window_mapping:
            task["target_window"] = window_mapping[task_id]

    return window_mapping


def find_missing_dispatch_fields(tasks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Identify tasks missing required dispatch fields.

    Codex must set owner_agent and target_window before dispatch.
    """
    missing: Dict[str, List[str]] = {}
    for task in tasks:
        # Only enforce dispatch fields for dispatch units
        task_like = _dict_to_task_like(task)
        if not is_dispatch_unit(task_like):
            continue
        fields = []
        if not task.get("owner_agent"):
            fields.append("owner_agent")
        if not task.get("target_window"):
            fields.append("target_window")
        if fields:
            missing[task.get("task_id", "unknown")] = fields
    return missing


def build_task_content(
    task: Dict[str, Any],
    spec_path: str,
    all_tasks: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Build task content/prompt for the worker agent.
    
    Supports two dispatch modes:
    1. Dispatch Unit Mode (parent task with subtasks): Generates a comprehensive prompt
       with parent task overview, ordered subtask list, and sequential execution instructions.
    2. Standalone Mode (leaf task or no subtasks): Generates a simple task prompt.
    
    Requirements: 2.1, 2.2, 5.3
    
    Args:
        task: Task dictionary with task_id, description, subtasks, details, etc.
        spec_path: Path to spec directory containing requirements.md and design.md
        all_tasks: Optional list of all tasks for looking up subtask details.
                   Required for dispatch unit mode with subtasks.
    
    Returns:
        Formatted task content/prompt string for the worker agent.
    """
    subtask_ids = task.get("subtasks", [])
    
    # Check if this is a dispatch unit with subtasks (parent task dispatch)
    if subtask_ids and all_tasks:
        return _build_dispatch_unit_content(task, spec_path, all_tasks)
    
    # Standalone task or leaf task - use simple format
    return _build_standalone_task_content(task, spec_path)


def _build_skill_protocol_section(task: Dict[str, Any]) -> str:
    """
    Build skill protocol section for task prompt.
    
    Instructs agent to self-judge whether to apply skills.
    Agent decides based on task context, not orchestrator.
    
    Args:
        task: Task dictionary
        
    Returns:
        Skill protocol section string
    """
    # Always include - Agent decides whether TDD applies
    return "\n" + SKILL_PROTOCOL + "\n"


def _build_standalone_task_content(task: Dict[str, Any], spec_path: str) -> str:
    """
    Build task content for a standalone task (no subtasks).
    
    This is the original format for backward compatibility.
    
    Args:
        task: Task dictionary
        spec_path: Path to spec directory
        
    Returns:
        Formatted task content string
    """
    lines = [
        f"Task: {task['description']}",
        "",
        f"Task ID: {task['task_id']}",
        f"Type: {task.get('type', 'code')}",
        "",
        "Reference Documents:",
        f"- Requirements: {spec_path}/requirements.md",
        f"- Design: {spec_path}/design.md",
        "",
    ]
    
    # Add task details if available
    details = task.get("details", [])
    if details:
        lines.append("Details:")
        for detail in details:
            lines.append(f"- {detail}")
        lines.append("")
    
    # Add skill protocol for agent self-judgment
    lines.append(_build_skill_protocol_section(task))
    
    return "\n".join(lines)


def _build_dispatch_unit_content(
    task: Dict[str, Any],
    spec_path: str,
    all_tasks: List[Dict[str, Any]]
) -> str:
    """
    Build task content for a dispatch unit (parent task with subtasks).
    
    Generates a comprehensive prompt with:
    - Parent task overview
    - Ordered subtask list with step numbers
    - Instructions for sequential execution
    
    Requirements: 2.1, 2.2
    
    Args:
        task: Parent task dictionary with subtasks list
        spec_path: Path to spec directory
        all_tasks: List of all tasks for looking up subtask details
        
    Returns:
        Formatted dispatch unit content string
    """
    # Build task map for subtask lookup
    task_map = {t["task_id"]: t for t in all_tasks}
    
    # Get subtask IDs and sort them for consistent ordering
    subtask_ids = sorted(task.get("subtasks", []), key=_task_id_sort_key)
    
    lines = [
        f"# Task Group: {task['task_id']}",
        "",
        "## Overview",
        task['description'],
        "",
    ]
    
    # Add parent task details if available
    parent_details = task.get("details", [])
    if parent_details:
        lines.append("### Context")
        for detail in parent_details:
            lines.append(f"- {detail}")
        lines.append("")
    
    # Add subtasks section with step numbers
    lines.append("## Subtasks (Execute in Order)")
    lines.append("")

    for step_num, subtask_id in enumerate(subtask_ids, start=1):
        subtask = task_map.get(subtask_id, {})
        subtask_desc = subtask.get("description", f"Subtask {subtask_id}")      
        is_optional = subtask.get("is_optional", False)
        subtask_status = subtask.get("status", "not_started")
        
        # Format step header
        optional_marker = " (Optional)" if is_optional else ""
        lines.append(f"### Step {step_num}: {subtask_id} - {subtask_desc}{optional_marker}")
        lines.append("")
        
        # Add subtask details
        subtask_details = subtask.get("details", [])
        if subtask_details:
            for detail in subtask_details:
                lines.append(f"- {detail}")
            lines.append("")
        else:
            lines.append("(No additional details)")
            lines.append("")

        lines.append(f"Status: {subtask_status}")
        lines.append("")

    # Resume guidance (skip already completed subtasks)
    completed_subtasks = [
        sid for sid in subtask_ids
        if task_map.get(sid, {}).get("status") == "completed"
    ]
    resume_subtask_id = None
    for sid in subtask_ids:
        status = task_map.get(sid, {}).get("status", "not_started")
        if status != "completed":
            resume_subtask_id = sid
            break

    if completed_subtasks or resume_subtask_id is not None:
        lines.append("## Resume Guidance")
        if completed_subtasks:
            lines.append(f"- Completed subtasks: {', '.join(completed_subtasks)}")
        if resume_subtask_id is not None:
            resume_step = subtask_ids.index(resume_subtask_id) + 1
            lines.append(f"- Resume from Step {resume_step}: {resume_subtask_id}")
            lines.append("- Skip already completed subtasks.")
        else:
            lines.append("- All subtasks are completed. Only proceed if rework is required.")
        lines.append("")
    
    # Add reference documents section
    lines.append("## Reference Documents")
    lines.append(f"- Requirements: {spec_path}/requirements.md")
    lines.append(f"- Design: {spec_path}/design.md")
    lines.append("")
    
    # Add execution instructions
    lines.append("## Instructions")
    instructions = [
        "Execute each subtask in order (Step 1, Step 2, etc.)",
        "After completing each subtask, report its status",
        "Maintain context from previous subtasks within this task group",
        "If a subtask fails, stop and report the failure - do not proceed to subsequent subtasks",
        "If resuming after a blocked subtask, start from the first incomplete subtask and do not redo completed work",
    ]
    if any(task_map.get(sid, {}).get("is_optional", False) for sid in subtask_ids):
        instructions.append("Optional subtasks may be skipped if not critical to the task group")
    for idx, instruction in enumerate(instructions, start=1):
        lines.append(f"{idx}. {instruction}")
    lines.append("")
    
    # Add skill protocol for agent self-judgment
    lines.append(_build_skill_protocol_section(task))
    
    return "\n".join(lines)


def build_task_configs(
    tasks: List[Dict[str, Any]],
    spec_path: str,
    workdir: str = ".",
    all_tasks: Optional[List[Dict[str, Any]]] = None
) -> List[TaskConfig]:
    """
    Build task configurations for codeagent-wrapper.
    
    Requirement 1.3, 1.4, 2.1, 2.2, 5.3: Build task config for dispatch.
    Expects Codex-provided owner_agent and target_window on each task.
    
    Args:
        tasks: List of tasks to build configs for
        spec_path: Path to spec directory
        workdir: Working directory for tasks
        all_tasks: Optional list of all tasks for dispatch unit mode.
                   If provided, enables parent task dispatch with subtask details.
                   If None, falls back to standalone task mode.
    
    Returns:
        List of TaskConfig objects ready for codeagent-wrapper
    """
    configs = []
    
    # Use all_tasks for subtask lookup, or fall back to tasks list
    task_lookup = all_tasks if all_tasks is not None else tasks
    
    for task in tasks:
        owner_agent = task.get("owner_agent")
        if not owner_agent:
            raise ValueError(f"Task {task.get('task_id', 'unknown')} missing owner_agent")
        backend = AGENT_TO_BACKEND.get(owner_agent)
        if not backend:
            raise ValueError(f"Task {task.get('task_id', 'unknown')} has unsupported owner_agent: {owner_agent}")
        target_window = task.get("target_window")
        if not target_window:
            raise ValueError(f"Task {task.get('task_id', 'unknown')} missing target_window")
        
        # Determine if this is a dispatch unit (parent task with subtasks)
        subtask_ids = task.get("subtasks", [])
        is_dispatch_unit = bool(subtask_ids)
        
        config = TaskConfig(
            task_id=task["task_id"],
            backend=backend,
            workdir=workdir,
            content=build_task_content(task, spec_path, task_lookup),
            dependencies=task.get("dependencies", []),
            target_window=target_window,
            subtasks=sorted(subtask_ids, key=_task_id_sort_key) if subtask_ids else [],
            is_dispatch_unit=is_dispatch_unit,
        )
        configs.append(config)
    
    return configs


def build_heredoc_input(configs: List[TaskConfig]) -> str:
    """Build heredoc-style input for codeagent-wrapper --parallel"""
    return "\n\n".join(config.to_heredoc() for config in configs)


def _looks_like_tmux_connect_error(output: str) -> bool:
    """Detect tmux socket connection failures that can be fixed via TMUX_TMPDIR."""
    if not output:
        return False
    text = output.lower()
    if "tmux" not in text:
        return False
    return (
        "error connecting to /tmp/tmux" in text
        or "failed to connect to /tmp/tmux" in text
        or "operation not permitted" in text
        or "permission denied" in text
    )


def _ensure_tmux_tmpdir(env: Dict[str, str]) -> Optional[str]:
    """Ensure TMUX_TMPDIR is set to a writable user directory."""
    current = env.get("TMUX_TMPDIR", "").strip()
    if current:
        return current
    tmpdir = os.path.join(os.path.expanduser("~"), ".tmux-tmp")
    try:
        os.makedirs(tmpdir, exist_ok=True)
        try:
            os.chmod(tmpdir, 0o700)
        except OSError:
            pass
    except OSError:
        return None
    env["TMUX_TMPDIR"] = tmpdir
    os.environ.setdefault("TMUX_TMPDIR", tmpdir)
    return tmpdir


def invoke_codeagent_wrapper(
    configs: List[TaskConfig],
    session_name: str,
    state_file: str,
    dry_run: bool = False
) -> ExecutionReport:
    """
    Invoke codeagent-wrapper --parallel synchronously.
    
    Requirement 9.1, 9.3: Dispatch via codeagent-wrapper, wait for completion
    """
    heredoc_input = build_heredoc_input(configs)
    
    if dry_run:
        print("DRY RUN - Would invoke codeagent-wrapper with:")
        print("-" * 40)
        print(heredoc_input)
        print("-" * 40)
        return ExecutionReport(
            success=True,
            tasks_completed=len(configs),
            tasks_failed=0,
            task_results=[{"task_id": c.task_id, "status": "dry_run"} for c in configs]
        )
    
    # Build command (allow disabling tmux in restricted environments)
    use_tmux = os.environ.get("CODEAGENT_NO_TMUX", "").strip().lower() not in {"1", "true", "yes"}
    full_output = os.environ.get("CODEAGENT_FULL_OUTPUT", "").strip().lower() in {"1", "true", "yes"}
    cmd_env = os.environ.copy()

    try:
        wrapper_bin = resolve_codeagent_wrapper()
    except FileNotFoundError:
        return ExecutionReport(
            success=False,
            tasks_completed=0,
            tasks_failed=len(configs),
            errors=["codeagent-wrapper not found (set CODEAGENT_WRAPPER or add it to PATH)"],
        )

    base_cmd = [wrapper_bin, "--parallel"]
    if full_output:
        base_cmd.append("--full-output")

    cmd_no_tmux = base_cmd + ["--state-file", state_file]
    cmd = cmd_no_tmux
    if use_tmux:
        cmd = base_cmd + ["--tmux-session", session_name, "--tmux-no-main-window", "--state-file", state_file]

    timeout_seconds = resolve_codex_timeout_seconds()

    try:
        result = subprocess.run(
            cmd,
            input=heredoc_input,
            capture_output=True,
            text=True,
            env=cmd_env,
            timeout=timeout_seconds,
        )
        if use_tmux and result.returncode != 0:
            combined = (result.stderr or "") + "\n" + (result.stdout or "")
            if looks_like_tmux_missing(combined):
                logger.warning("tmux not available; retrying without tmux (set CODEAGENT_NO_TMUX=1 to disable)")
                result = subprocess.run(
                    cmd_no_tmux,
                    input=heredoc_input,
                    capture_output=True,
                    text=True,
                    env=cmd_env,
                    timeout=timeout_seconds,
                )
            elif _looks_like_tmux_connect_error(combined):
                tmpdir = _ensure_tmux_tmpdir(cmd_env)
                if tmpdir:
                    logger.warning("tmux connect failed; retrying with TMUX_TMPDIR=%s", tmpdir)
                    result = subprocess.run(
                        cmd,
                        input=heredoc_input,
                        capture_output=True,
                        text=True,
                        env=cmd_env,
                        timeout=timeout_seconds,
                    )
                    if result.returncode != 0:
                        combined = (result.stderr or "") + "\n" + (result.stdout or "")
                        if _looks_like_tmux_connect_error(combined):
                            logger.warning("tmux still failing; retrying without tmux (set CODEAGENT_NO_TMUX=1 to disable)")
                            result = subprocess.run(
                                cmd_no_tmux,
                                input=heredoc_input,
                                capture_output=True,
                                text=True,
                                env=cmd_env,
                                timeout=timeout_seconds,
                            )

        # Parse output as JSON if possible
        try:
            report_data = json.loads(result.stdout)
            return ExecutionReport(
                success=result.returncode == 0,
                tasks_completed=report_data.get("tasks_completed", 0),
                tasks_failed=report_data.get("tasks_failed", 0),
                task_results=report_data.get("task_results", []),
                errors=report_data.get("errors", [])
            )
        except json.JSONDecodeError:
            # Non-JSON output
            return ExecutionReport(
                success=result.returncode == 0,
                tasks_completed=len(configs) if result.returncode == 0 else 0,
                tasks_failed=0 if result.returncode == 0 else len(configs),
                errors=[result.stderr] if result.stderr else []
            )
            
    except subprocess.TimeoutExpired:
        return ExecutionReport(
            success=False,
            tasks_completed=0,
            tasks_failed=len(configs),
            errors=[f"Execution timed out after {timeout_seconds} seconds"]
        )
    except FileNotFoundError:
        return ExecutionReport(
            success=False,
            tasks_completed=0,
            tasks_failed=len(configs),
            errors=["codeagent-wrapper not found (set CODEAGENT_WRAPPER or add it to PATH)"],
        )
    except Exception as e:
        return ExecutionReport(
            success=False,
            tasks_completed=0,
            tasks_failed=len(configs),
            errors=[str(e)]
        )


def update_task_statuses(
    state: Dict[str, Any],
    task_ids: List[str],
    new_status: str
) -> None:
    """Update task statuses in state"""
    for task in state.get("tasks", []):
        if task["task_id"] in task_ids:
            task["status"] = new_status


def rollback_batch_tasks(state: Dict[str, Any], task_ids: List[str]) -> None:
    """Reset any in-progress tasks in a failed batch back to not_started."""
    for task in state.get("tasks", []):
        if task["task_id"] in task_ids and task.get("status") == "in_progress":
            task["status"] = "not_started"
            for field in ["window_id", "pane_id", "exit_code", "output", "error", "completed_at"]:
                task.pop(field, None)


def handle_partial_completion(
    state: Dict[str, Any],
    dispatch_unit_id: str,
    completed_subtasks: List[str],
    failed_subtask: str,
    error: str
) -> None:
    """Handle partial completion when a subtask fails."""
    task_map = {t["task_id"]: t for t in state.get("tasks", [])}

    # Mark completed subtasks
    for sid in completed_subtasks:
        if sid in task_map:
            task_map[sid]["status"] = "completed"

    # Mark failed subtask
    if failed_subtask and failed_subtask in task_map:
        task_map[failed_subtask]["status"] = "blocked"
        if error:
            task_map[failed_subtask]["blocked_reason"] = error

    # Mark parent as blocked
    if dispatch_unit_id in task_map:
        task_map[dispatch_unit_id]["status"] = "blocked"
        if failed_subtask:
            task_map[dispatch_unit_id]["blocked_by"] = failed_subtask
        if error:
            task_map[dispatch_unit_id]["blocked_reason"] = error


def process_execution_report(
    state: Dict[str, Any],
    report: ExecutionReport
) -> None:
    """
    Process execution report and update state.
    
    Requirement 9.4: Process Execution Report
    """
    task_map = {t["task_id"]: t for t in state.get("tasks", [])}

    for result in report.task_results:
        task_id = result.get("task_id")
        if not task_id:
            continue

        # Find and update task
        task = task_map.get(task_id)
        if not task:
            continue

        completed_subtasks = result.get("completed_subtasks", []) or []
        failed_subtask = result.get("failed_subtask") or result.get("blocked_by")

        if failed_subtask:
            # Handle partial completion (subtask failure)
            handle_partial_completion(
                state,
                dispatch_unit_id=task_id,
                completed_subtasks=completed_subtasks,
                failed_subtask=failed_subtask,
                error=result.get("error", "")
            )
        else:
            # Update status based on result
            if result.get("status") == "completed" or result.get("exit_code", 1) == 0:
                task["status"] = "pending_review"
                # If this is a dispatch unit, mark untouched subtasks as pending_review
                subtask_ids = task.get("subtasks", [])
                if subtask_ids:
                    for sid in subtask_ids:
                        subtask = task_map.get(sid)
                        if subtask and subtask.get("status") == "not_started":
                            subtask["status"] = "pending_review"
            elif result.get("status") == "blocked":
                task["status"] = "blocked"

        # Copy result fields
        for field in ["exit_code", "output", "error", "files_changed",
                     "coverage", "coverage_num", "tests_passed", "tests_failed",
                     "window_id", "pane_id"]:
            if field in result:
                task[field] = result[field]

        task["completed_at"] = datetime.now(timezone.utc).isoformat()


def dispatch_batch(
    state_file: str,
    workdir: str = ".",
    dry_run: bool = False
) -> DispatchResult:
    """
    Dispatch ready tasks to worker agents with file conflict detection.
    
    Tasks are partitioned into conflict-free batches and dispatched sequentially.
    Each batch completes before the next batch starts, ensuring no file conflicts.
    
    Also processes fix_required tasks through the fix loop before getting ready tasks.
    
    Args:
        state_file: Path to AGENT_STATE.json
        workdir: Working directory for tasks
        dry_run: If True, don't actually invoke codeagent-wrapper
    
    Returns:
        DispatchResult with execution details
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.6, 1.7, 2.3, 2.4, 2.5, 2.6, 2.7, 3.1, 4.6, 9.1, 9.3, 9.4, 9.10
    
    Note: Tasks are only marked in_progress after successful dispatch.
          On failure, tasks are rolled back to not_started to allow retry.
    """
    # Load state
    try:
        state = load_agent_state(state_file)
    except Exception as e:
        return DispatchResult(
            success=False,
            message=f"Failed to load state file: {e}",
            errors=[str(e)]
        )
    
    # Process fix loop first (Req 3.1, 4.6)
    # This handles fix_required tasks and returns fix requests to dispatch
    fix_requests = process_fix_loop(state)
    fix_tasks_dispatched = 0
    fix_dispatch_failures = 0
    total_dispatched = 0
    total_completed = 0
    total_failed = 0
    all_errors: List[str] = []
    all_task_results: List[Dict[str, Any]] = []
    overall_success = True
    has_execution_report = False
    
    if fix_requests:
        logger.info(f"Processing {len(fix_requests)} fix requests from fix loop")
        
        # Dispatch fix requests
        for fix_req in fix_requests:
            task_id = fix_req["task_id"]
            backend = fix_req["backend"]
            prompt = fix_req["prompt"]
            
            # Build a single task config for the fix request
            fix_config = TaskConfig(
                task_id=task_id,
                backend=backend,
                workdir=workdir,
                content=prompt,
                dependencies=[],
            )
            
            if not dry_run:
                # Invoke codeagent-wrapper for fix task
                session_name = state.get("session_name", "roundtable")
                report = invoke_codeagent_wrapper(
                    [fix_config],
                    session_name,
                    state_file,
                    dry_run=False
                )
                
                has_execution_report = True
                total_completed += report.tasks_completed
                total_failed += report.tasks_failed
                all_errors.extend(report.errors)
                all_task_results.extend(report.task_results)
                
                if report.success:
                    fix_tasks_dispatched += 1
                    # Process the fix task result
                    process_execution_report(state, report)
                    # Call on_fix_task_complete to increment fix_attempts and transition to pending_review (Req 7.1, 7.2, 7.3)
                    on_fix_task_complete(state, task_id)
                else:
                    overall_success = False
                    fix_dispatch_failures += 1
                    # Fix task dispatch failed - rollback status to fix_required (Req 7.4, 7.5)
                    rollback_fix_dispatch(state, task_id)
                    logger.warning(f"Fix task {task_id} dispatch failed, rolled back to fix_required")
                    logger.error(f"Fix task {task_id} dispatch failed: {report.errors}")
                    if not report.errors:
                        all_errors.append(f"Fix task {task_id} dispatch failed")
            else:
                fix_tasks_dispatched += 1
                print(f"DRY RUN - Would dispatch fix task: {task_id}")
        
        # Save state after fix loop processing
        if not dry_run:
            save_agent_state(state_file, state)
    
    # Get ready dispatch units (parent or standalone tasks with satisfied dependencies)
    ready_tasks = get_dispatchable_units_from_state(state)
    
    if not ready_tasks:
        # No new tasks ready, but we may have dispatched fix tasks
        # Always update parent statuses before returning (Req 8.1, 8.2, 8.3)
        if not dry_run:
            update_parent_statuses(state)
            save_agent_state(state_file, state)
        
        combined_report = None
        if has_execution_report:
            combined_report = ExecutionReport(
                success=overall_success,
                tasks_completed=total_completed,
                tasks_failed=total_failed,
                task_results=all_task_results,
                errors=all_errors
            )
        
        if fix_dispatch_failures > 0:
            if fix_tasks_dispatched > 0:
                message = (
                    f"Fix task dispatch failed: {fix_dispatch_failures} failed, "
                    f"{fix_tasks_dispatched} dispatched"
                )
            else:
                message = f"Fix task dispatch failed: {fix_dispatch_failures} failed"
            return DispatchResult(
                success=False,
                message=message,
                tasks_dispatched=fix_tasks_dispatched,
                execution_report=combined_report,
                errors=all_errors
            )
        
        if fix_tasks_dispatched > 0:
            return DispatchResult(
                success=True,
                message=f"Dispatched {fix_tasks_dispatched} fix task(s), no new tasks ready",
                tasks_dispatched=fix_tasks_dispatched,
                execution_report=combined_report
            )
        return DispatchResult(
            success=True,
            message="No tasks ready for dispatch",
            tasks_dispatched=0
        )

    # Assign target windows for dispatch units if missing (Req 6.1)
    apply_window_allocation(state, ready_tasks)

    # Validate Codex-provided dispatch fields before proceeding
    missing_fields = find_missing_dispatch_fields(ready_tasks)
    if missing_fields:
        missing_messages = [
            f"{task_id}: missing {', '.join(fields)}"
            for task_id, fields in missing_fields.items()
        ]
        return DispatchResult(
            success=False,
            message="Missing required dispatch fields. Populate owner_agent and target_window before dispatch.",
            tasks_dispatched=0,
            errors=missing_messages
        )
    
    # Partition tasks into conflict-free batches (Req 2.3, 2.4, 2.5, 2.6, 2.7)
    batches = partition_by_conflicts(ready_tasks, logger)
    
    if len(batches) > 1:
        logger.info(f"Partitioned {len(ready_tasks)} tasks into {len(batches)} conflict-free batches")
    
    spec_path = state.get("spec_path", ".")
    session_name = state.get("session_name", "roundtable")
    
    # Get all tasks from state for dispatch unit mode (subtask lookup)
    all_tasks = state.get("tasks", [])
    
    # Dispatch batches sequentially (Req 2.3, 2.4)
    for batch_idx, batch in enumerate(batches):
        batch_task_ids = [t["task_id"] for t in batch]
        
        if len(batches) > 1:
            logger.info(f"Dispatching batch {batch_idx + 1}/{len(batches)} with {len(batch)} tasks: {batch_task_ids}")
        
        # Build task configs for this batch (pass all_tasks for dispatch unit mode)
        configs = build_task_configs(batch, spec_path, workdir, all_tasks)
        
        # Invoke codeagent-wrapper for this batch
        try:
            report = invoke_codeagent_wrapper(
                configs,
                session_name,
                state_file,
                dry_run=dry_run
            )
        except Exception as e:
            overall_success = False
            err_text = str(e)
            logger.error(f"Batch {batch_idx + 1} failed with exception: {err_text}")
            all_errors.append(err_text)
            if not dry_run:
                rollback_batch_tasks(state, batch_task_ids)
                update_parent_statuses(state)
                save_agent_state(state_file, state)
            continue
        
        has_execution_report = True
        total_dispatched += len(configs)
        total_completed += report.tasks_completed
        total_failed += report.tasks_failed
        all_errors.extend(report.errors)
        all_task_results.extend(report.task_results)
        
        # Process results for this batch
        if not dry_run:
            if report.success:
                # Dispatch succeeded - update tasks to in_progress first
                update_task_statuses(state, batch_task_ids, "in_progress")
                # Then process individual task results
                process_execution_report(state, report)
            else:
                overall_success = False
                # Dispatch failed - ensure tasks remain in not_started for retry
                tasks_with_results = {r.get("task_id") for r in report.task_results if r.get("task_id")}
                
                # Process any partial results we did get
                if report.task_results:
                    update_task_statuses(state, list(tasks_with_results), "in_progress")
                    process_execution_report(state, report)
                rollback_batch_tasks(state, batch_task_ids)
                
                # Log batch failure
                logger.error(f"Batch {batch_idx + 1} failed: {report.errors}")
            
            # Update parent statuses after each batch (Req 1.3, 1.4, 1.5)
            update_parent_statuses(state)
            
            # Save state after each batch
            save_agent_state(state_file, state)
        
        # If batch failed, we might want to stop (but continue for now to process all batches)
        # Future enhancement: add option to stop on first failure
    
    # Build combined execution report
    combined_report = ExecutionReport(
        success=overall_success,
        tasks_completed=total_completed,
        tasks_failed=total_failed,
        task_results=all_task_results,
        errors=all_errors
    )
    
    # Build message including fix tasks info
    total_all_dispatched = total_dispatched + fix_tasks_dispatched
    message_parts = []
    
    if fix_tasks_dispatched > 0:
        message_parts.append(f"{fix_tasks_dispatched} fix task(s)")
    
    if total_dispatched > 0:
        message_parts.append(f"{total_dispatched} new task(s) in {len(batches)} batch(es)")
    
    if message_parts:
        message = f"Dispatched {', '.join(message_parts)}"
    else:
        message = "No tasks dispatched"
    
    if not overall_success:
        message = f"Dispatch partially failed: {total_completed} completed, {total_failed} failed"
    
    return DispatchResult(
        success=overall_success,
        message=message,
        tasks_dispatched=total_all_dispatched,
        execution_report=combined_report,
        errors=all_errors
    )


def main():
    """Command line entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Dispatch ready tasks to worker agents"
    )
    parser.add_argument(
        "state_file",
        help="Path to AGENT_STATE.json"
    )
    parser.add_argument(
        "--workdir", "-w",
        default=".",
        help="Working directory for tasks (default: current directory)"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Show what would be dispatched without executing"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON"
    )
    
    args = parser.parse_args()
    
    result = dispatch_batch(
        args.state_file,
        workdir=args.workdir,
        dry_run=args.dry_run
    )
    
    if args.json:
        output = {
            "success": result.success,
            "message": result.message,
            "tasks_dispatched": result.tasks_dispatched,
            "errors": result.errors
        }
        if result.execution_report:
            output["execution_report"] = {
                "tasks_completed": result.execution_report.tasks_completed,
                "tasks_failed": result.execution_report.tasks_failed,
            }
        print(json.dumps(output, indent=2))
    else:
        if result.success:
            print(f"✅ {result.message}")
            if result.execution_report:
                print(f"   Completed: {result.execution_report.tasks_completed}")
                print(f"   Failed: {result.execution_report.tasks_failed}")
        else:
            print(f"❌ {result.message}")
            for error in result.errors:
                print(f"   - {error}")
            sys.exit(1)


if __name__ == "__main__":
    main()
