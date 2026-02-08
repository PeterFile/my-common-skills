#!/usr/bin/env python3
"""
Spec Parser for Multi-Agent Orchestration

Parses tasks.md to extract task definitions for orchestration.
Agent will read requirements.md and design.md directly when executing tasks.

Requirements: 1.2, 11.2, 11.3
"""

import re
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from enum import Enum


class TaskType(Enum):
    """Task type enumeration for backend routing"""
    CODE = "code"
    UI = "ui"
    REVIEW = "review"


class TaskStatus(Enum):
    """Task status enumeration"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    UNDER_REVIEW = "under_review"
    FIX_REQUIRED = "fix_required"  # NEW: Task needs fixes after review
    FINAL_REVIEW = "final_review"
    COMPLETED = "completed"
    BLOCKED = "blocked"


# Valid state transitions for task status
# Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
VALID_TRANSITIONS = {
    "not_started": ["in_progress", "blocked"],
    "in_progress": ["pending_review", "blocked"],
    "pending_review": ["under_review", "blocked"],
    "under_review": ["final_review", "fix_required", "blocked"],  # NEW: fix_required
    "fix_required": ["in_progress", "blocked"],  # NEW: can retry or block
    "final_review": ["completed", "blocked"],
    "completed": [],
    "blocked": ["not_started", "in_progress", "fix_required"],  # NEW: can go to fix_required
}


def validate_transition(from_status: str, to_status: str) -> bool:
    """
    Validate state transition.
    
    Requirements: 4.5
    
    Args:
        from_status: Current status
        to_status: Target status
        
    Returns:
        True if transition is valid, False otherwise
    """
    valid_targets = VALID_TRANSITIONS.get(from_status, [])
    return to_status in valid_targets


@dataclass
class Task:
    """
    Represents a parsed task from tasks.md
    
    Extended with fix loop fields for Requirements 3.10
    """
    task_id: str
    description: str
    task_type: TaskType = TaskType.CODE
    status: TaskStatus = TaskStatus.NOT_STARTED
    dependencies: List[str] = field(default_factory=list)
    is_optional: bool = False
    parent_id: Optional[str] = None
    subtasks: List[str] = field(default_factory=list)
    details: List[str] = field(default_factory=list)
    # File manifest fields for conflict detection (Requirement 2.1)
    writes: List[str] = field(default_factory=list)
    reads: List[str] = field(default_factory=list)
    
    # Fix loop fields (Requirement 3.10)
    fix_attempts: int = 0
    max_fix_attempts: int = 3
    escalated: bool = False
    escalated_at: Optional[str] = None
    original_agent: Optional[str] = None
    last_review_severity: Optional[str] = None
    review_history: List[Dict] = field(default_factory=list)
    blocked_reason: Optional[str] = None
    blocked_by: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "task_id": self.task_id,
            "description": self.description,
            "type": self.task_type.value,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "is_optional": self.is_optional,
            "parent_id": self.parent_id,
            "subtasks": self.subtasks,
            "details": self.details,
            "writes": self.writes,
            "reads": self.reads,
            # Fix loop fields
            "fix_attempts": self.fix_attempts,
            "max_fix_attempts": self.max_fix_attempts,
            "escalated": self.escalated,
            "escalated_at": self.escalated_at,
            "original_agent": self.original_agent,
            "last_review_severity": self.last_review_severity,
            "review_history": self.review_history,
            "blocked_reason": self.blocked_reason,
            "blocked_by": self.blocked_by,
        }


@dataclass
class ParseError:
    """Parse error information"""
    file: str
    line: int
    message: str


@dataclass
class TasksParseResult:
    """Result of parsing tasks.md"""
    success: bool
    tasks: List[Task] = field(default_factory=list)
    errors: List[ParseError] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of spec directory validation"""
    valid: bool
    spec_path: str = ""
    missing_files: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class DependencyGraph:
    """Represents a task dependency graph"""
    nodes: Set[str] = field(default_factory=set)
    edges: Dict[str, List[str]] = field(default_factory=dict)
    
    def add_task(self, task_id: str, dependencies: List[str] = None):
        """Add a task node with its dependencies"""
        self.nodes.add(task_id)
        self.edges[task_id] = dependencies or []
        for dep in (dependencies or []):
            self.nodes.add(dep)
    
    def get_dependencies(self, task_id: str) -> List[str]:
        """Get direct dependencies of a task"""
        return self.edges.get(task_id, [])
    
    def get_dependents(self, task_id: str) -> List[str]:
        """Get tasks that depend on this task"""
        return [tid for tid, deps in self.edges.items() if task_id in deps]


@dataclass
class CircularDependencyError:
    """Represents a circular dependency error"""
    cycle: List[str]
    
    def __str__(self):
        return f"Circular dependency: {' -> '.join(self.cycle)}"


@dataclass
class MissingDependencyError:
    """Represents a missing dependency error"""
    task_id: str
    missing: List[str]
    
    def __str__(self):
        return f"Task {self.task_id} has missing dependencies: {', '.join(self.missing)}"


@dataclass
class DependencyResult:
    """Result of dependency extraction"""
    graph: DependencyGraph
    circular_dependencies: List[CircularDependencyError] = field(default_factory=list)
    missing_dependencies: Dict[str, List[str]] = field(default_factory=dict)
    
    @property
    def valid(self) -> bool:
        """Valid if no circular dependencies AND no missing dependencies"""
        return len(self.circular_dependencies) == 0 and len(self.missing_dependencies) == 0
    
    def get_missing_dependency_errors(self) -> List[MissingDependencyError]:
        """Convert missing_dependencies dict to list of MissingDependencyError"""
        return [MissingDependencyError(task_id=tid, missing=deps) 
                for tid, deps in self.missing_dependencies.items()]


# Task status markers in tasks.md
STATUS_MARKERS = {
    "[ ]": TaskStatus.NOT_STARTED,
    "[x]": TaskStatus.COMPLETED,
    "[X]": TaskStatus.COMPLETED,
    "[-]": TaskStatus.IN_PROGRESS,
    "[~]": TaskStatus.BLOCKED,
}

# Task type detection removed - Codex assigns type via Step 1b of SKILL.md
# TaskType enum and Task.task_type field retained for backward compatibility


def _parse_task_line(line: str) -> Tuple[Optional[str], TaskStatus, bool, str]:
    """Parse a task line to extract task ID, status, optional flag, and description.
    
    Supports nested task IDs of any depth (e.g., 1, 1.1, 1.1.1, 1.1.1.1).
    """
    # Pattern supports task IDs like: 1, 1.1, 1.1.1, 1.1.1.1, etc.
    pattern = r'^[-*]\s*\[([xX\s~-])\](\*)?\s*(\d+(?:\.\d+)*)(?:\.)?\s+(.+)$'
    match = re.match(pattern, line.strip())
    
    if not match:
        return None, TaskStatus.NOT_STARTED, False, ""
    
    status_char = match.group(1)
    is_optional = match.group(2) == "*"
    task_id = match.group(3).rstrip('.')
    description = match.group(4).strip()
    
    status_key = f"[{status_char}]"
    status = STATUS_MARKERS.get(status_key, TaskStatus.NOT_STARTED)
    
    return task_id, status, is_optional, description


def parse_tasks(content: str) -> TasksParseResult:
    """
    Parse tasks.md content and extract task definitions.
    
    Uses two-pass parsing to handle parent-subtask relationships correctly
    regardless of order in the file (Requirement 14.1, 14.2, 14.3, 14.4).
    
    Pass 1: Collect all tasks with their basic properties
    Pass 2: Build parent-subtask relationships
    
    Args:
        content: Markdown content of tasks.md
        
    Returns:
        TasksParseResult: Parsed tasks and any errors
    """
    tasks: List[Task] = []
    errors: List[ParseError] = []
    
    lines = content.split('\n')
    current_task: Optional[Task] = None
    current_details: List[str] = []
    line_num = 0
    
    # ========================================================================
    # Pass 1: Collect all tasks with basic properties
    # ========================================================================
    for line in lines:
        line_num += 1
        stripped = line.strip()
        
        if not stripped or stripped.startswith('#'):
            continue
        
        if re.match(r'^[-*]\s*\[[xX\s~-]\]', stripped):
            # Save previous task
            if current_task:
                current_task.details = current_details
                # task_type defaults to CODE; Codex assigns type via Step 1b
                # Extract file manifest from details (Requirement 2.2)
                writes, reads = _extract_file_manifest(current_details)
                current_task.writes = writes
                current_task.reads = reads
                tasks.append(current_task)
                current_details = []
            
            # Parse new task
            task_id, status, is_optional, description = _parse_task_line(stripped)
            
            if task_id is None:
                errors.append(ParseError("tasks.md", line_num, f"Invalid task format: {stripped}"))
                continue
            
            current_task = Task(
                task_id=task_id,
                description=description,
                status=status,
                is_optional=is_optional,
            )
            
            # Set parent_id for subtasks (e.g., 1.1 -> parent is 1, 1.1.1 -> parent is 1.1)
            # Note: We only set parent_id here, subtasks list is built in Pass 2
            if '.' in task_id:
                # Find the immediate parent (e.g., 1.1.1 -> 1.1, 1.1 -> 1)
                parts = task_id.rsplit('.', 1)
                current_task.parent_id = parts[0]
        
        elif current_task and stripped.startswith('-'):
            current_details.append(stripped[1:].strip())
        
        elif current_task and stripped:
            current_details.append(stripped)
    
    # Don't forget the last task
    if current_task:
        current_task.details = current_details
        # task_type defaults to CODE; Codex assigns type via Step 1b
        # Extract file manifest from details (Requirement 2.2)
        writes, reads = _extract_file_manifest(current_details)
        current_task.writes = writes
        current_task.reads = reads
        tasks.append(current_task)
    
    # ========================================================================
    # Pass 2: Build parent-subtask relationships (order-independent)
    # Requirement 14.1, 14.2, 14.3, 14.4
    # ========================================================================
    _build_parent_subtask_relationships(tasks)
    
    return TasksParseResult(success=len(errors) == 0, tasks=tasks, errors=errors)


def _build_parent_subtask_relationships(tasks: List[Task]) -> None:
    """
    Build parent-subtask relationships from parsed tasks.
    
    This is a post-processing step that links subtasks to their parents
    regardless of the order they appear in tasks.md.
    
    Handles nested subtasks (e.g., 1.1.1 is a subtask of 1.1, which is a subtask of 1).
    
    Requirements: 14.1, 14.2, 14.3, 14.4
    
    Args:
        tasks: List of parsed Task objects (modified in place)
    """
    # Build task_id -> Task mapping
    task_map: Dict[str, Task] = {t.task_id: t for t in tasks}
    
    # Clear any existing subtasks lists (in case of re-processing)
    for task in tasks:
        task.subtasks = []
    
    # For each task with a parent_id, add it to the parent's subtasks list
    for task in tasks:
        if task.parent_id:
            parent = task_map.get(task.parent_id)
            if parent:
                parent.subtasks.append(task.task_id)


def validate_spec_directory(spec_path: str) -> ValidationResult:
    """
    Validate that all required spec files exist.
    
    Args:
        spec_path: Path to spec directory
        
    Returns:
        ValidationResult with spec_path for reference
    """
    required_files = ["requirements.md", "design.md", "tasks.md"]
    missing_files: List[str] = []
    
    if not os.path.isdir(spec_path):
        return ValidationResult(
            valid=False,
            spec_path=spec_path,
            errors=[f"Spec directory does not exist: {spec_path}"]
        )
    
    for filename in required_files:
        if not os.path.isfile(os.path.join(spec_path, filename)):
            missing_files.append(filename)
    
    return ValidationResult(
        valid=len(missing_files) == 0,
        spec_path=spec_path,
        missing_files=missing_files,
        errors=[f"Missing: {', '.join(missing_files)}"] if missing_files else []
    )


def _extract_dependencies_from_details(details: List[str]) -> List[str]:
    """Extract dependency references from task details."""
    dependencies = []
    
    for detail in details:
        detail_lower = detail.lower()
        
        # Pattern: dependencies: 1, 2 or depends on: 1.1
        for pattern in [r'dependenc(?:y|ies)[:\s]+([^\n]+)', r'depends?\s+on[:\s]+([^\n]+)']:
            match = re.search(pattern, detail_lower)
            if match:
                task_ids = re.findall(r'(?:task[-_])?(\d+(?:\.\d+)?)', match.group(1))
                dependencies.extend(task_ids)
    
    return list(dict.fromkeys(dependencies))


def _extract_file_manifest(details: List[str]) -> Tuple[List[str], List[str]]:
    """
    Extract file manifest (writes and reads) from task details.
    
    Parses _writes: and _reads: markers from task details to determine
    which files a task will modify or read.
    
    Format in tasks.md:
        - _writes: file1.py, file2.py
        - _reads: config.json, data.csv
    
    Requirements: 2.2
    
    Args:
        details: List of detail strings from task
        
    Returns:
        Tuple of (writes, reads) - lists of file paths
    """
    writes: List[str] = []
    reads: List[str] = []
    
    for detail in details:
        detail_stripped = detail.strip()
        
        # Parse _writes: marker
        if detail_stripped.lower().startswith('_writes:'):
            # Extract file list after the marker
            files_str = detail_stripped[8:].strip()  # len('_writes:') = 8
            if files_str:
                # Split by comma and clean up each file path
                files = [f.strip() for f in files_str.split(',')]
                writes.extend([f for f in files if f])
        
        # Parse _reads: marker
        elif detail_stripped.lower().startswith('_reads:'):
            # Extract file list after the marker
            files_str = detail_stripped[7:].strip()  # len('_reads:') = 7
            if files_str:
                # Split by comma and clean up each file path
                files = [f.strip() for f in files_str.split(',')]
                reads.extend([f for f in files if f])
    
    # Remove duplicates while preserving order
    writes = list(dict.fromkeys(writes))
    reads = list(dict.fromkeys(reads))
    
    return writes, reads


def _detect_circular_dependencies(graph: DependencyGraph) -> List[CircularDependencyError]:
    """Detect circular dependencies using DFS."""
    cycles = []
    visited = set()
    rec_stack = set()
    path = []
    
    def dfs(node: str) -> bool:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for dep in graph.get_dependencies(node):
            if dep not in visited:
                if dfs(dep):
                    return True
            elif dep in rec_stack:
                cycle_start = path.index(dep)
                cycles.append(CircularDependencyError(cycle=path[cycle_start:] + [dep]))
                return True
        
        path.pop()
        rec_stack.remove(node)
        return False
    
    for node in graph.nodes:
        if node not in visited:
            dfs(node)
    
    return cycles


def extract_dependencies(tasks: List[Task]) -> DependencyResult:
    """
    Extract dependencies from tasks and build dependency graph.
    
    Args:
        tasks: List of parsed Task objects
        
    Returns:
        DependencyResult with graph and any errors
    """
    graph = DependencyGraph()
    task_ids = {t.task_id for t in tasks}
    missing_deps: Dict[str, List[str]] = {}
    
    for task in tasks:
        deps = _extract_dependencies_from_details(task.details)
        task.dependencies = deps
        
        missing = [d for d in deps if d not in task_ids]
        if missing:
            missing_deps[task.task_id] = missing
        
        valid_deps = [d for d in deps if d in task_ids]
        graph.add_task(task.task_id, valid_deps)
    
    circular = _detect_circular_dependencies(graph)
    
    return DependencyResult(
        graph=graph,
        circular_dependencies=circular,
        missing_dependencies=missing_deps
    )


def expand_dependencies(dependencies: List[str], task_map: Dict[str, 'Task']) -> List[str]:
    """
    Expand parent task dependencies to their subtasks.
    
    If a dependency is a parent task, replace it with all its subtasks.
    This ensures dependent tasks wait for ALL subtasks to complete.
    
    Handles nested subtasks (e.g., 1.1.1) correctly through recursive expansion.
    
    Requirements: 1.6, 1.7, 5.1, 5.2, 5.4
    
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


def is_dispatch_unit(task: Task) -> bool:
    """
    Check if task is a dispatch unit (can be dispatched independently).

    A task is a dispatch unit if:
    - It has subtasks (parent task), OR
    - It has no subtasks AND no parent (standalone task)

    Leaf tasks with parents are NOT dispatch units.

    Requirements: 1.1, 1.2, 1.3
    """
    if task.subtasks:
        return True
    if task.parent_id is None:
        return True
    return False


def get_dispatchable_units(tasks: List[Task], completed_ids: Set[str]) -> List[Task]:
    """
    Get dispatch units ready for execution.

    Returns parent tasks and standalone tasks whose dependencies are satisfied.
    Does NOT return leaf tasks that belong to a parent.

    Requirements: 1.1, 1.2, 1.3, 4.3
    """
    ready = []
    task_map = {t.task_id: t for t in tasks}

    for task in tasks:
        # Only consider dispatch units
        if not is_dispatch_unit(task):
            continue

        # Skip completed or non-startable
        status_value = task.status
        if isinstance(status_value, TaskStatus):
            status_value = status_value.value
        if task.task_id in completed_ids or status_value != TaskStatus.NOT_STARTED.value:
            continue

        # Check dependencies (expand parent deps to subtasks)
        expanded_deps = expand_dependencies(task.dependencies, task_map)
        if all(dep in completed_ids for dep in expanded_deps):
            ready.append(task)

    return ready


def is_leaf_task(task: Task) -> bool:
    """
    Check if task is a leaf task (has no subtasks).
    
    A leaf task is the only type of task that can be dispatched for execution.
    Parent tasks act as containers and their status is derived from subtasks.
    
    Requirements: 1.1, 1.2
    """
    return len(task.subtasks) == 0


def get_ready_tasks(tasks: List[Task], completed_ids: Set[str]) -> List[Task]:
    """
    Get leaf tasks ready to execute (all dependencies satisfied).
    
    Rules:
    1. Task must be a leaf task (no subtasks) - Req 1.1, 1.2
    2. Task must not be completed
    3. All dependencies must be satisfied (including expanded parent deps) - Req 1.6, 1.7
    
    Requirements: 1.1, 1.2, 1.6, 1.7, 5.1, 5.2, 5.4
    """
    ready = []
    task_map = {t.task_id: t for t in tasks}
    
    for task in tasks:
        # Skip parent tasks (they have subtasks) - Req 1.1, 1.2
        if not is_leaf_task(task):
            continue
        
        # Skip completed tasks
        if task.task_id in completed_ids or task.status == TaskStatus.COMPLETED:
            continue
        
        # Expand and check dependencies - Req 1.6, 1.7, 5.1, 5.2
        expanded_deps = expand_dependencies(task.dependencies, task_map)
        if all(dep in completed_ids for dep in expanded_deps):
            ready.append(task)
    return ready


def topological_sort(tasks: List[Task]) -> Tuple[List[Task], List[CircularDependencyError], List[MissingDependencyError]]:
    """
    Sort tasks in topological order based on dependencies.
    
    Returns:
        Tuple of (sorted_tasks, circular_errors, missing_errors)
        - If any errors exist, sorted_tasks will be empty
    """
    dep_result = extract_dependencies(tasks)
    
    # Fail fast on invalid dependencies (circular or missing)
    if not dep_result.valid:
        return [], dep_result.circular_dependencies, dep_result.get_missing_dependency_errors()
    
    task_map = {t.task_id: t for t in tasks}
    in_degree = {t.task_id: len(t.dependencies) for t in tasks}
    
    queue = [tid for tid, degree in in_degree.items() if degree == 0]
    sorted_tasks = []
    
    while queue:
        queue.sort()
        current = queue.pop(0)
        if current in task_map:
            sorted_tasks.append(task_map[current])
        
        for task in tasks:
            if current in task.dependencies:
                in_degree[task.task_id] -= 1
                if in_degree[task.task_id] == 0:
                    queue.append(task.task_id)
    
    return sorted_tasks, [], []


def load_tasks_from_spec(spec_path: str) -> Tuple[TasksParseResult, ValidationResult]:
    """
    Load and parse tasks from a spec directory.
    
    Args:
        spec_path: Path to spec directory
        
    Returns:
        Tuple of (tasks_result, validation_result)
    """
    validation = validate_spec_directory(spec_path)
    if not validation.valid:
        return TasksParseResult(success=False, errors=[]), validation
    
    tasks_path = os.path.join(spec_path, "tasks.md")
    with open(tasks_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tasks_result = parse_tasks(content)
    
    # Extract dependencies
    if tasks_result.success:
        extract_dependencies(tasks_result.tasks)
    
    return tasks_result, validation


if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: spec_parser.py <spec_directory>")
        print("       spec_parser.py <tasks.md>")
        sys.exit(1)
    
    path = sys.argv[1]
    
    if os.path.isdir(path):
        tasks_result, validation = load_tasks_from_spec(path)
        
        if not validation.valid:
            print(f"❌ Validation failed: {validation.errors}")
            sys.exit(1)
        
        print(f"✅ Spec directory: {path}")
        print(f"   Tasks: {len(tasks_result.tasks)}")
        print(f"   Reference docs: requirements.md, design.md")
        
        if "--json" in sys.argv:
            print(json.dumps({"tasks": [t.to_dict() for t in tasks_result.tasks]}, indent=2))
    
    elif path.endswith("tasks.md"):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        result = parse_tasks(content)
        extract_dependencies(result.tasks)
        
        print(f"Parsed {len(result.tasks)} tasks:")
        for task in result.tasks:
            icon = "✅" if task.status == TaskStatus.COMPLETED else "⬜"
            opt = " (optional)" if task.is_optional else ""
            deps = f" [deps: {task.dependencies}]" if task.dependencies else ""
            print(f"  {icon} {task.task_id}: {task.description[:50]}...{opt}{deps}")
    
    else:
        print(f"Unknown: {path}")
        sys.exit(1)
