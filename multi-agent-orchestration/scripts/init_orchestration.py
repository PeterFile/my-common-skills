#!/usr/bin/env python3
"""
Orchestration Initialization Script

Initializes multi-agent orchestration from a Kiro spec directory.
- Parses tasks.md and validates spec files
- Creates AGENT_STATE.json scaffold (no agent decisions by default)
- Writes TASKS_PARSED.json for Codex to consume
- Creates PROJECT_PULSE.md template (legacy mode can generate a filled PULSE)

Requirements: 11.2, 11.4, 11.5, 11.6, 11.8
"""

import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Any

# Add script directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from spec_parser import (
    Task,
    TaskType,
    TaskStatus,
    parse_tasks,
    validate_spec_directory,
    extract_dependencies,
    load_tasks_from_spec,
)


# Legacy agent mapping removed - Codex assigns owner_agent via Step 1b of SKILL.md

# Legacy keywords for criticality detection (Requirement 11.6)
SECURITY_KEYWORDS = ["security", "auth", "password", "token", "encrypt", "credential", "secret"]
COMPLEX_KEYWORDS = ["refactor", "migration", "integration", "architecture"]


@dataclass
class TaskEntry:
    """
    Task entry for AGENT_STATE.json
    
    Extended to include subtasks, parent_id, writes, reads for:
    - Parent status aggregation (Req 1.3, 1.4, 1.5)
    - File conflict detection (Req 2.1, 2.2)
    """
    task_id: str
    description: str
    type: str
    status: str
    dependencies: List[str]
    is_optional: bool
    created_at: str
    owner_agent: Optional[str] = None
    criticality: Optional[str] = None
    # Parent-subtask relationship fields (Req 1.3, 1.4, 1.5)
    subtasks: List[str] = field(default_factory=list)
    parent_id: Optional[str] = None
    # File manifest fields (Req 2.1, 2.2)
    writes: List[str] = field(default_factory=list)
    reads: List[str] = field(default_factory=list)
    # Fix loop fields (Req 3.10)
    fix_attempts: int = 0
    max_fix_attempts: int = 3
    escalated: bool = False
    escalated_at: Optional[str] = None
    original_agent: Optional[str] = None
    last_review_severity: Optional[str] = None
    review_history: List[Dict[str, Any]] = field(default_factory=list)
    blocked_reason: Optional[str] = None
    blocked_by: Optional[str] = None
    # Task details for prompt building
    details: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return {key: value for key, value in data.items() if value is not None}


@dataclass
class AgentState:
    """Full AGENT_STATE.json structure"""
    spec_path: str
    session_name: str
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    review_findings: List[Dict[str, Any]] = field(default_factory=list)
    final_reports: List[Dict[str, Any]] = field(default_factory=list)
    blocked_items: List[Dict[str, Any]] = field(default_factory=list)
    pending_decisions: List[Dict[str, Any]] = field(default_factory=list)
    deferred_fixes: List[Dict[str, Any]] = field(default_factory=list)
    window_mapping: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InitResult:
    """Result of initialization"""
    success: bool
    message: str
    tasks_file: Optional[str] = None
    state_file: Optional[str] = None
    pulse_file: Optional[str] = None
    errors: List[str] = field(default_factory=list)


def determine_criticality(task: Task) -> str:
    """
    Determine task criticality based on description and details.
    
    Legacy behavior: Codex should determine criticality in the orchestration phase.

    Requirement 11.6: Set initial criticality based on task markers
    - * for optional
    - security keywords for security-sensitive
    - complex keywords for complex
    """
    text = (task.description + " " + " ".join(task.details)).lower()
    
    # Check for security-sensitive keywords
    for keyword in SECURITY_KEYWORDS:
        if keyword in text:
            return "security-sensitive"
    
    # Check for complex keywords
    for keyword in COMPLEX_KEYWORDS:
        if keyword in text:
            return "complex"
    
    return "standard"


def assign_owner_agent(task: Task) -> str:
    """Legacy fallback. Codex assigns owner_agent via Step 1b of SKILL.md."""
    return "codex"


def convert_task_to_entry(task: Task, include_decisions: bool = False) -> TaskEntry:
    """
    Convert parsed Task to TaskEntry for AGENT_STATE.json.
    
    Preserves all Task fields including:
    - subtasks, parent_id for parent status aggregation (Req 1.3, 1.4, 1.5)
    - writes, reads for file conflict detection (Req 2.1, 2.2)
    - fix loop fields for retry mechanism (Req 3.10)
    """
    owner_agent = assign_owner_agent(task) if include_decisions else None
    criticality = determine_criticality(task) if include_decisions else None

    return TaskEntry(
        task_id=task.task_id,
        description=task.description,
        type=task.task_type.value,
        status=task.status.value,
        dependencies=task.dependencies,
        is_optional=task.is_optional,
        created_at=datetime.now(timezone.utc).isoformat(),
        owner_agent=owner_agent,
        criticality=criticality,
        # Parent-subtask relationship fields (Req 1.3, 1.4, 1.5)
        subtasks=task.subtasks,
        parent_id=task.parent_id,
        # File manifest fields (Req 2.1, 2.2)
        writes=task.writes,
        reads=task.reads,
        # Fix loop fields (Req 3.10)
        fix_attempts=task.fix_attempts,
        max_fix_attempts=task.max_fix_attempts,
        escalated=task.escalated,
        escalated_at=task.escalated_at,
        original_agent=task.original_agent,
        last_review_severity=task.last_review_severity,
        review_history=task.review_history,
        blocked_reason=task.blocked_reason,
        blocked_by=task.blocked_by,
        # Task details for prompt building
        details=task.details,
    )


def update_parent_statuses(state: Dict[str, Any]) -> None:
    """
    Update parent task statuses based on subtask completion.
    
    This function derives parent task status from the statuses of its subtasks.
    It should be called after each batch completion to keep parent statuses in sync.
    
    Rules (in priority order):
    - All subtasks completed → parent completed
    - Any subtask blocked → parent blocked
    - Any subtask fix_required → parent fix_required
    - Any subtask in_progress/pending_review/under_review/final_review → parent in_progress
    - Otherwise → parent not_started
    
    Requirements: 1.3, 1.4, 1.5
    
    Args:
        state: The AGENT_STATE dictionary containing tasks
    """
    # Build task map for quick lookup
    task_map = {t["task_id"]: t for t in state.get("tasks", [])}
    
    # Process tasks in reverse order to handle nested hierarchies
    # (children before parents)
    for task in reversed(state.get("tasks", [])):
        subtask_ids = task.get("subtasks", [])
        if not subtask_ids:
            continue  # Leaf task, skip
        
        # Get subtask statuses
        subtask_statuses = []
        for sid in subtask_ids:
            if sid in task_map:
                subtask_statuses.append(task_map[sid].get("status", "not_started"))
        
        if not subtask_statuses:
            continue  # No valid subtasks found
        
        # Determine parent status from subtask statuses (Req 1.3, 1.4, 1.5)
        if all(s == "completed" for s in subtask_statuses):
            # All subtasks completed → parent completed (Req 1.3)
            task["status"] = "completed"
        elif any(s == "blocked" for s in subtask_statuses):
            # Any subtask blocked → parent blocked (Req 1.5)
            task["status"] = "blocked"
        elif any(s == "fix_required" for s in subtask_statuses):
            # Any subtask fix_required → parent fix_required
            task["status"] = "fix_required"
        elif any(s in ["in_progress", "pending_review", "under_review", "final_review"] 
                 for s in subtask_statuses):
            # Any subtask in progress → parent in_progress (Req 1.4)
            task["status"] = "in_progress"
        else:
            # Otherwise → parent not_started
            task["status"] = "not_started"


def extract_mental_model_from_design(design_path: str) -> Dict[str, str]:
    """
    Extract mental model from design.md for PROJECT_PULSE.md.
    
    Requirement 11.8: Initialize PROJECT_PULSE.md with Mental Model from design.md
    """
    try:
        with open(design_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return {
            "description": "Multi-agent orchestration system",
            "diagram": ""
        }
    
    # Extract overview section for description
    description = ""
    overview_match = re.search(r'## Overview\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
    if overview_match:
        overview_text = overview_match.group(1).strip()
        # Get first paragraph
        paragraphs = overview_text.split('\n\n')
        if paragraphs:
            description = paragraphs[0].strip()
    
    # Extract first mermaid diagram
    diagram = ""
    mermaid_match = re.search(r'```mermaid\s*\n(.*?)```', content, re.DOTALL)
    if mermaid_match:
        diagram = mermaid_match.group(1).strip()
    
    return {
        "description": description or "Multi-agent orchestration system",
        "diagram": diagram
    }


def generate_pulse_document(
    spec_path: str,
    mental_model: Dict[str, str],
    tasks: List[Dict[str, Any]]
) -> str:
    """
    Generate PROJECT_PULSE.md content.
    
    Requirement 11.8: Initialize PROJECT_PULSE.md with Mental Model from design.md
    """
    # Count tasks by status
    total_tasks = len(tasks)
    not_started = sum(1 for t in tasks if t.get("status") == "not_started")
    
    pulse_content = f"""# PROJECT_PULSE.md

## 🟢 Mental Model

{mental_model['description']}

"""
    
    if mental_model['diagram']:
        pulse_content += f"""```mermaid
{mental_model['diagram']}
```

"""
    
    pulse_content += f"""## 🟡 Narrative Delta

**Orchestration initialized from spec:** `{spec_path}`

- Total tasks: {total_tasks}
- Ready to start: {not_started}

## 🔴 Risks & Debt

### Cognitive Load Warnings
- None identified

### Technical Debt
- None identified

### Pending Decisions
- None pending

## 🔗 Semantic Anchors

- [Spec] {spec_path}/requirements.md -> Requirements
- [Spec] {spec_path}/design.md -> Design
- [Spec] {spec_path}/tasks.md -> Tasks
"""
    
    return pulse_content


def generate_pulse_template(spec_path: str) -> str:
    """
    Generate PROJECT_PULSE.md template without AI decisions.
    
    This keeps the document parsable by sync_pulse.py while delegating
    content generation to Codex.
    """
    return f"""# PROJECT_PULSE

## Mental Model

<!-- Codex: Summarize the system mental model using design.md -->

## Narrative Delta

**Orchestration spec:** `{spec_path}`

<!-- Codex: Add progress summary and recent completions -->

## Risks & Debt

### Cognitive Load Warnings
- None

### Technical Debt
- None

### Pending Decisions
- None

## Semantic Anchors
- None
"""


def initialize_orchestration(
    spec_path: str,
    session_name: Optional[str] = None,
    output_dir: Optional[str] = None,
    mode: str = "codex"
) -> InitResult:
    """
    Initialize orchestration from spec directory.
    
    Args:
        spec_path: Path to spec directory containing requirements.md, design.md, tasks.md
        session_name: Tmux session name (default: derived from spec path)
        output_dir: Output directory for state files (default: spec_path parent)
        mode: "codex" (scaffold) or "legacy" (script-driven decisions)
    
    Returns:
        InitResult with success status and file paths
    
    Requirements: 11.2, 11.4, 11.5, 11.6, 11.8
    """
    errors = []
    
    # Validate spec directory (Requirement 11.2)
    validation = validate_spec_directory(spec_path)
    if not validation.valid:
        return InitResult(
            success=False,
            message=f"Invalid spec directory: {spec_path}",
            errors=validation.errors
        )
    
    # Parse tasks.md (Requirement 11.3, 11.4)
    tasks_result, _ = load_tasks_from_spec(spec_path)
    if not tasks_result.success:
        return InitResult(
            success=False,
            message="Failed to parse tasks.md",
            errors=[str(e) for e in tasks_result.errors]
        )
    
    # Convert tasks to entries (Requirement 11.4, 11.5, 11.6)
    include_decisions = mode == "legacy"
    task_entries = [
        convert_task_to_entry(t, include_decisions=include_decisions)
        for t in tasks_result.tasks
    ]
    
    # Determine session name
    if not session_name:
        spec_name = Path(spec_path).name
        session_name = f"orch-{spec_name}"
    
    # Create AGENT_STATE.json (scaffold by default)
    agent_state = AgentState(
        spec_path=os.path.abspath(spec_path),
        session_name=session_name,
        tasks=[t.to_dict() for t in task_entries],
    )
    
    # Determine output directory
    if output_dir:
        out_path = Path(output_dir)
    else:
        out_path = Path(spec_path).parent
    
    out_path.mkdir(parents=True, exist_ok=True)
    
    # Write TASKS_PARSED.json for Codex consumption
    tasks_file = out_path / "TASKS_PARSED.json"
    try:
        with open(tasks_file, 'w', encoding='utf-8') as f:
            json.dump(
                {
                    "spec_path": os.path.abspath(spec_path),
                    "tasks": [t.to_dict() for t in task_entries],
                },
                f,
                indent=2
            )
    except Exception as e:
        errors.append(f"Failed to write TASKS_PARSED.json: {e}")
    
    # Write AGENT_STATE.json
    state_file = out_path / "AGENT_STATE.json"
    try:
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(agent_state.to_dict(), f, indent=2)
    except Exception as e:
        errors.append(f"Failed to write AGENT_STATE.json: {e}")
    
    # Generate and write PROJECT_PULSE.md
    if mode == "legacy":
        # Extract mental model from design.md (Requirement 11.8)
        design_path = os.path.join(spec_path, "design.md")
        mental_model = extract_mental_model_from_design(design_path)
        pulse_content = generate_pulse_document(
            spec_path,
            mental_model,
            [t.to_dict() for t in task_entries]
        )
    else:
        pulse_content = generate_pulse_template(spec_path)
    pulse_file = out_path / "PROJECT_PULSE.md"
    try:
        with open(pulse_file, 'w', encoding='utf-8') as f:
            f.write(pulse_content)
    except Exception as e:
        errors.append(f"Failed to write PROJECT_PULSE.md: {e}")
    
    if errors:
        return InitResult(
            success=False,
            message="Initialization completed with errors",
            tasks_file=str(tasks_file),
            state_file=str(state_file),
            pulse_file=str(pulse_file),
            errors=errors
        )
    
    return InitResult(
        success=True,
        message=f"Orchestration initialized successfully",
        tasks_file=str(tasks_file),
        state_file=str(state_file),
        pulse_file=str(pulse_file)
    )


def main():
    """Command line entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Initialize multi-agent orchestration from spec directory"
    )
    parser.add_argument(
        "spec_path",
        help="Path to spec directory (containing requirements.md, design.md, tasks.md)"
    )
    parser.add_argument(
        "--session", "-s",
        help="Tmux session name (default: derived from spec path)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output directory for state files (default: spec parent directory)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON"
    )
    parser.add_argument(
        "--mode",
        choices=["codex", "legacy"],
        default="codex",
        help="Initialization mode: codex (scaffold) or legacy (script-driven)"
    )
    
    args = parser.parse_args()
    
    result = initialize_orchestration(
        args.spec_path,
        session_name=args.session,
        output_dir=args.output,
        mode=args.mode
    )
    
    if args.json:
        output = {
            "success": result.success,
            "message": result.message,
            "tasks_file": result.tasks_file,
            "state_file": result.state_file,
            "pulse_file": result.pulse_file,
            "errors": result.errors
        }
        print(json.dumps(output, indent=2))
    else:
        if result.success:
            print(f"✅ {result.message}")
            print(f"   State file: {result.state_file}")
            if result.tasks_file:
                print(f"   Tasks file: {result.tasks_file}")
            print(f"   PULSE file: {result.pulse_file}")
        else:
            print(f"❌ {result.message}")
            for error in result.errors:
                print(f"   - {error}")
            sys.exit(1)


if __name__ == "__main__":
    main()
