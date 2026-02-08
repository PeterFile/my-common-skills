"""
Spec Parser for Sequential Orchestration

Parses tasks.md files to extract task list.
Simplified version - no dispatch unit or dependency expansion logic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Task:
    """Represents a single task from tasks.md."""
    task_id: str
    description: str
    details: List[str] = field(default_factory=list)
    parent_id: Optional[str] = None
    subtasks: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    is_optional: bool = False


def parse_tasks_md(tasks_md_path: str) -> List[Task]:
    """
    Parse tasks.md file to extract task list.
    
    Supports formats:
    - Numbered list: 1. Task description
    - Nested tasks: 1.1 Subtask description
    - Details: Indented lines after task
    - Optional marker: [optional] in description
    - Dependencies: depends on: 1, 2
    
    Args:
        tasks_md_path: Path to tasks.md file
        
    Returns:
        List of Task objects
    """
    path = Path(tasks_md_path)
    if not path.exists():
        raise FileNotFoundError(f"tasks.md not found: {tasks_md_path}")
    
    content = path.read_text(encoding="utf-8")
    return _parse_tasks_content(content)


def _parse_tasks_content(content: str) -> List[Task]:
    """Parse task content from markdown string."""
    tasks: List[Task] = []
    task_map: Dict[str, Task] = {}
    
    lines = content.split("\n")
    current_task: Optional[Task] = None
    
    # Pattern for task lines: "1." or "1.1" or "- [ ]" etc.
    task_pattern = re.compile(r'^(\d+(?:\.\d+)*)\.\s+(.+)$')
    checkbox_pattern = re.compile(r'^-\s+\[[ x]\]\s+(?:\*\*)?(\d+(?:\.\d+)*)[.:]?\*?\*?\s*(.+)$', re.IGNORECASE)
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines and headers
        if not stripped or stripped.startswith("#"):
            continue
        
        # Try numbered format: "1. Task description"
        match = task_pattern.match(stripped)
        if match:
            task_id = match.group(1)
            description = match.group(2).strip()
            current_task = _create_task(task_id, description, task_map)
            tasks.append(current_task)
            task_map[task_id] = current_task
            continue
        
        # Try checkbox format: "- [ ] **1.** Description" or "- [x] 1. Description"
        match = checkbox_pattern.match(stripped)
        if match:
            task_id = match.group(1)
            description = match.group(2).strip()
            # Remove trailing ** if present
            description = re.sub(r'\*\*$', '', description).strip()
            current_task = _create_task(task_id, description, task_map)
            tasks.append(current_task)
            task_map[task_id] = current_task
            continue
        
        # Detail line (indented or starting with -)
        if current_task and (line.startswith("  ") or line.startswith("\t") or stripped.startswith("-")):
            detail = stripped.lstrip("- ").strip()
            if detail and not detail.startswith("["):
                # Check for dependencies
                dep_match = re.match(r'depends?\s+on:?\s*(.+)', detail, re.IGNORECASE)
                if dep_match:
                    deps = [d.strip() for d in dep_match.group(1).split(",")]
                    current_task.dependencies.extend(deps)
                else:
                    current_task.details.append(detail)
    
    return tasks


def _create_task(task_id: str, description: str, task_map: Dict[str, Task]) -> Task:
    """Create a Task object and set up parent-child relationships."""
    # Check for optional marker
    is_optional = "[optional]" in description.lower()
    description = re.sub(r'\[optional\]', '', description, flags=re.IGNORECASE).strip()
    
    # Determine parent_id for nested tasks (e.g., "1.2" -> parent "1")
    parent_id = None
    if "." in task_id:
        parts = task_id.rsplit(".", 1)
        parent_id = parts[0]
        # Update parent's subtasks list
        if parent_id in task_map:
            task_map[parent_id].subtasks.append(task_id)
    
    return Task(
        task_id=task_id,
        description=description,
        parent_id=parent_id,
        is_optional=is_optional,
    )


def is_dispatch_unit(task: Task) -> bool:
    """
    Check if task is a dispatch unit (can be dispatched independently).

    A task is a dispatch unit if:
    - It has subtasks (parent task), OR
    - It has no subtasks AND no parent (standalone task)

    Leaf tasks with parents are NOT dispatch units - they are executed
    as part of their parent's dispatch.

    This matches multi-agent-orchestration behavior.
    """
    if task.subtasks:
        return True
    if task.parent_id is None:
        return True
    return False


def expand_dependencies(dependencies: List[str], task_map: Dict[str, Task]) -> List[str]:
    """
    Expand parent task dependencies to their subtasks.

    If a dependency is a parent task, replace it with all its subtasks.
    This ensures dependent tasks wait for ALL subtasks to complete.

    Args:
        dependencies: List of task IDs that are dependencies
        task_map: Dictionary mapping task_id to Task object

    Returns:
        List of expanded dependency IDs (leaf tasks only)
    """
    expanded = []

    for dep_id in dependencies:
        dep_task = task_map.get(dep_id)

        if dep_task and dep_task.subtasks:
            # Parent task: expand to all subtasks (recursively)
            for subtask_id in dep_task.subtasks:
                expanded.extend(expand_dependencies([subtask_id], task_map))
        else:
            # Leaf task or unknown: keep as-is
            expanded.append(dep_id)

    # Remove duplicates while preserving order
    return list(dict.fromkeys(expanded))


def get_next_dispatch_unit(
    tasks: List[Task],
    completed_ids: List[str]
) -> Optional[Task]:
    """
    Get the next dispatch unit to execute.

    A dispatch unit is either:
    - A parent task (has subtasks) - agent executes all subtasks
    - A standalone task (no subtasks and no parent)

    Leaf tasks with parents are NOT dispatch units.

    Rules:
    - Skip already completed tasks
    - Skip optional tasks
    - Execute in order (by task_id)
    - Check dependencies are satisfied

    Args:
        tasks: List of all tasks
        completed_ids: List of completed task IDs

    Returns:
        Next dispatch unit to execute, or None if all complete
    """
    completed_set = set(completed_ids)
    task_map = {t.task_id: t for t in tasks}

    # Sort tasks by task_id for consistent ordering
    sorted_tasks = sorted(tasks, key=lambda t: _task_id_sort_key(t.task_id))

    for task in sorted_tasks:
        # Only consider dispatch units
        if not is_dispatch_unit(task):
            continue

        # Skip completed
        if task.task_id in completed_set:
            continue

        # Skip optional
        if task.is_optional:
            continue

        # Check dependencies (expand parent deps to subtasks)
        if task.dependencies:
            expanded_deps = expand_dependencies(task.dependencies, task_map)
            if not all(dep in completed_set for dep in expanded_deps):
                continue

        return task

    return None


# Backward compatibility alias
def get_next_incomplete_task(
    tasks: List[Task],
    completed_ids: List[str]
) -> Optional[Task]:
    """Backward compatibility alias for get_next_dispatch_unit."""
    return get_next_dispatch_unit(tasks, completed_ids)


def _task_id_sort_key(task_id: str) -> List[Any]:
    """Sort key for task IDs like '1.2.3' using numeric ordering."""
    key: List[Any] = []
    for part in task_id.split("."):
        if part.isdigit():
            key.append(int(part))
        else:
            key.append(part)
    return key


def all_tasks_complete(tasks: List[Task], completed_ids: List[str]) -> bool:
    """Check if all non-optional dispatch units are complete."""
    completed_set = set(completed_ids)

    for task in tasks:
        # Skip optional
        if task.is_optional:
            continue

        # Only check dispatch units (parent or standalone tasks)
        if not is_dispatch_unit(task):
            continue

        if task.task_id not in completed_set:
            return False

    return True


def get_subtask_list(task: Task, task_map: Dict[str, Task]) -> List[Task]:
    """
    Get all subtasks of a dispatch unit recursively.

    Args:
        task: The parent task
        task_map: Dictionary mapping task_id to Task object

    Returns:
        List of subtask Task objects (leaf tasks only)
    """
    if not task.subtasks:
        return []

    result = []
    for subtask_id in task.subtasks:
        subtask = task_map.get(subtask_id)
        if subtask:
            if subtask.subtasks:
                # Nested parent: recurse
                result.extend(get_subtask_list(subtask, task_map))
            else:
                # Leaf task
                result.append(subtask)
    return result

