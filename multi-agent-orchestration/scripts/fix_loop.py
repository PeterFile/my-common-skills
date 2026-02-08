#!/usr/bin/env python3
"""
Fix Loop Module for Multi-Agent Orchestration

Implements the fix loop workflow for handling failed reviews:
- Fix loop entry and blocking
- Fix loop action evaluation
- Fix request creation and prompt building
- Fix loop scheduling
- Unblock and success handling
- Human fallback

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4.6, 6.1, 6.2, 6.3, 6.4, 6.5
"""

import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

# Add script directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from spec_parser import expand_dependencies, Task


# Constants
MAX_FIX_ATTEMPTS = 3
ESCALATION_THRESHOLD = 2  # Escalate after 2 completed fix attempts


class FixLoopAction(Enum):
    """
    Actions from fix loop evaluation.
    
    Requirements: 3.3, 3.6, 3.7
    """
    PASS = "pass"              # Review passed, continue
    RETRY = "retry"            # Retry with same agent
    ESCALATE = "escalate"      # Switch to Codex and retry
    HUMAN_FALLBACK = "human"   # Max retries, need human


@dataclass
class FixRequest:
    """
    Request to fix a task based on review findings.
    
    Requirements: 3.4, 6.1, 6.2, 6.3, 6.4, 6.5
    """
    task_id: str
    attempt_number: int          # Current attempt (1-indexed for display): completed + 1
    completed_attempts: int      # Number of completed fix attempts before this one
    review_findings: List[Dict]
    original_output: str
    fix_instructions: str
    review_history: List[Dict]   # Full history for escalation
    use_escalation_agent: bool = False


def should_enter_fix_loop(severity: str) -> bool:
    """
    Determine if review severity requires fix loop.
    
    Requirements: 3.1
    
    Args:
        severity: Review severity (critical, major, minor, none)
        
    Returns:
        True if severity requires fix loop entry
    """
    return severity in ["critical", "major"]


def get_all_dependent_task_ids(state: Dict[str, Any], task_id: str) -> Set[str]:
    """
    Get all tasks that depend on the given task (transitive closure).
    
    Includes:
    - Direct dependents (tasks with task_id in their dependencies)
    - Transitive dependents (tasks depending on direct dependents)
    - Tasks depending on parent if task_id is a subtask
    
    Uses BFS to find transitive closure of dependents.
    
    Requirements: 3.2
    
    Args:
        state: The AGENT_STATE dictionary
        task_id: The task ID to find dependents for
        
    Returns:
        Set of task IDs that depend on the given task
    """
    # Build task map for quick lookup
    task_map = {}
    for t in state.get("tasks", []):
        tid = t.get("task_id")
        if tid:
            # Convert dict to Task-like object for expand_dependencies
            task_map[tid] = type('Task', (), {
                'task_id': tid,
                'subtasks': t.get("subtasks", []),
                'dependencies': t.get("dependencies", []),
            })()
    
    # Build reverse dependency map (task -> tasks that depend on it)
    reverse_deps: Dict[str, Set[str]] = {}
    for t in state.get("tasks", []):
        deps = t.get("dependencies", [])
        # Expand dependencies to handle parent-subtask relationships
        expanded_deps = expand_dependencies(deps, task_map)
        for dep in expanded_deps:
            if dep not in reverse_deps:
                reverse_deps[dep] = set()
            reverse_deps[dep].add(t["task_id"])
    
    # Find the parent if this is a subtask
    task = next((t for t in state.get("tasks", []) if t.get("task_id") == task_id), None)
    parent_id = task.get("parent_id") if task else None
    
    # BFS to find transitive closure
    visited: Set[str] = set()
    queue = [task_id]
    
    # Also start from parent if this is a subtask
    if parent_id:
        queue.append(parent_id)
    
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        
        # Add all tasks that depend on current
        for dependent in reverse_deps.get(current, set()):
            if dependent not in visited:
                queue.append(dependent)
    
    # Remove the original task from results
    visited.discard(task_id)
    if parent_id:
        visited.discard(parent_id)
    
    return visited


def block_dependent_tasks(state: Dict[str, Any], task_id: str, reason: str) -> None:
    """
    Block all tasks that depend on the failed task.
    
    Uses expanded dependencies to handle parent-subtask relationships.
    
    Requirements: 3.2
    
    Args:
        state: The AGENT_STATE dictionary
        task_id: The task ID that failed
        reason: Reason for blocking
    """
    dependent_ids = get_all_dependent_task_ids(state, task_id)
    
    for t in state.get("tasks", []):
        if t.get("task_id") in dependent_ids:
            if t.get("status") not in ["completed", "blocked"]:
                t["status"] = "blocked"
                t["blocked_reason"] = reason
                t["blocked_by"] = task_id
    
    # Add to blocked_items
    if "blocked_items" not in state:
        state["blocked_items"] = []
    
    state["blocked_items"].append({
        "task_id": task_id,
        "blocking_reason": reason,
        "dependent_tasks": list(dependent_ids),
        "created_at": datetime.now(timezone.utc).isoformat()
    })


def enter_fix_loop(state: Dict[str, Any], task_id: str, review_findings: List[Dict]) -> None:
    """
    Enter fix loop for a task after review finds critical/major issues.
    
    This function is called when review completes with critical/major severity.
    
    Steps:
    1. Update task status to fix_required
    2. Store review findings in review_history
    3. Block all dependent tasks
    
    Requirements: 3.1, 3.2
    
    Args:
        state: The AGENT_STATE dictionary
        task_id: The task ID that needs fixes
        review_findings: List of review findings (each with severity, summary, details)
    """
    task = next((t for t in state.get("tasks", []) if t.get("task_id") == task_id), None)
    if not task:
        return
    
    # Determine overall severity from findings
    severities = [f.get("severity", "minor") for f in review_findings]
    if "critical" in severities:
        overall_severity = "critical"
    elif "major" in severities:
        overall_severity = "major"
    else:
        overall_severity = "minor"
    
    # Update task state
    task["status"] = "fix_required"
    task["last_review_severity"] = overall_severity
    
    # Calculate the attempt number for this review
    # fix_attempts = completed fix attempts, so:
    # - Initial review failure: fix_attempts = 0, this is review of initial impl (attempt 0)
    # - After 1st fix completes: fix_attempts = 1, this is review of fix attempt 1
    completed_attempts = task.get("fix_attempts", 0)
    
    # Add to review history (structured format for prompt injection)
    if "review_history" not in task:
        task["review_history"] = []
    
    task["review_history"].append({
        "attempt": completed_attempts,  # 0 for initial, 1/2/3 for fix attempts
        "severity": overall_severity,
        "findings": review_findings,  # List of {severity, summary, details}
        "reviewed_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Block dependent tasks (Req 3.2)
    block_dependent_tasks(state, task_id, f"Upstream task {task_id} requires fixes ({overall_severity})")



def evaluate_fix_loop_action(task: Dict[str, Any], severity: str) -> FixLoopAction:
    """
    Determine next action based on review result and completed attempt count.
    
    fix_attempts = number of COMPLETED fix attempts:
    - 0 completed: RETRY with original agent (this will be attempt 1)
    - 1 completed: RETRY with original agent (this will be attempt 2)
    - 2 completed: ESCALATE to Codex (this will be attempt 3)
    - 3 completed: HUMAN_FALLBACK (no more attempts)
    
    Requirements: 3.3, 3.6, 3.7
    
    Args:
        task: Task dictionary
        severity: Review severity (critical, major, minor, none)
        
    Returns:
        FixLoopAction indicating next action
    """
    if not should_enter_fix_loop(severity):
        return FixLoopAction.PASS
    
    # fix_attempts = number of completed fix attempts
    completed_attempts = task.get("fix_attempts", 0)
    
    if completed_attempts >= MAX_FIX_ATTEMPTS:
        return FixLoopAction.HUMAN_FALLBACK
    
    if completed_attempts >= ESCALATION_THRESHOLD:
        return FixLoopAction.ESCALATE
    
    return FixLoopAction.RETRY



def format_review_history(history: List[Dict]) -> str:
    """
    Format review history for inclusion in escalation prompt.
    
    Requirements: 6.5
    
    Args:
        history: List of review history entries
        
    Returns:
        Formatted string representation of review history
    """
    if not history:
        return "No previous attempts."
    
    lines = []
    for entry in history:
        attempt = entry.get("attempt", 0)
        if attempt == 0:
            lines.append("### Initial Implementation Review")
        else:
            lines.append(f"### Fix Attempt {attempt} Review")
        
        lines.append(f"Severity: {entry.get('severity', 'unknown')}")
        
        # Format findings (list of {severity, summary, details} objects)
        findings = entry.get("findings", [])
        if findings:
            lines.append("Findings:")
            for finding in findings:
                if isinstance(finding, dict):
                    sev = finding.get("severity", "unknown")
                    summary = finding.get("summary", "No summary")
                    lines.append(f"  - [{sev.upper()}] {summary}")
                    if finding.get("details"):
                        lines.append(f"    Details: {finding['details']}")
                else:
                    # Fallback for string findings (legacy format)
                    lines.append(f"  - {finding}")
        
        lines.append("")
    return "\n".join(lines)


def create_fix_request(
    state: Dict[str, Any],
    task_id: str,
    findings: List[Dict]
) -> FixRequest:
    """
    Create fix request with review feedback.
    
    Requirements: 3.4, 6.1, 6.2, 6.3, 6.4, 6.5
    
    Args:
        state: The AGENT_STATE dictionary
        task_id: The task ID that needs fixes
        findings: List of review findings
        
    Returns:
        FixRequest with all necessary information for fix prompt
    """
    task = next((t for t in state.get("tasks", []) if t.get("task_id") == task_id), None)
    if not task:
        raise ValueError(f"Task {task_id} not found in state")
    
    completed_attempts = task.get("fix_attempts", 0)
    review_history = task.get("review_history", [])
    
    # Build fix instructions from findings (Req 6.1)
    instructions = []
    for finding in findings:
        severity = finding.get("severity", "unknown")
        if severity in ["critical", "major"]:
            instructions.append(f"- [{severity.upper()}] {finding.get('summary', 'Issue found')}")
            if finding.get("details"):
                instructions.append(f"  Details: {finding['details']}")
    
    # Determine if escalation is needed (after 2 completed attempts)
    use_escalation = completed_attempts >= ESCALATION_THRESHOLD
    
    return FixRequest(
        task_id=task_id,
        attempt_number=completed_attempts + 1,  # Display: 1, 2, or 3
        completed_attempts=completed_attempts,
        review_findings=findings,
        original_output=task.get("output", ""),
        fix_instructions="\n".join(instructions),
        review_history=review_history,
        use_escalation_agent=use_escalation
    )


def build_fix_prompt(fix_request: FixRequest, task: Dict[str, Any]) -> str:
    """
    Build prompt for fix attempt.
    
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
    
    Args:
        fix_request: The fix request with findings and history
        task: The task dictionary
        
    Returns:
        Formatted prompt string for the fix attempt
    """
    # Truncate original output if too long
    original_output = fix_request.original_output
    if len(original_output) > 2000:
        original_output = original_output[:2000] + "..."
    
    base_prompt = f"""## FIX REQUEST - Attempt {fix_request.attempt_number}/{MAX_FIX_ATTEMPTS}

### Original Task
{task.get('description', 'No description')}

### Review Findings (MUST FIX)
{fix_request.fix_instructions}

### Previous Output
{original_output}

### Instructions
1. Review the findings above carefully
2. Fix ALL critical and major issues
3. Ensure the fix doesn't break existing functionality
4. Run tests to verify the fix
"""
    
    # Include full history for escalation (Req 6.5)
    if fix_request.use_escalation_agent and fix_request.review_history:
        history_section = f"""
### Previous Fix Attempts History
{format_review_history(fix_request.review_history)}
"""
        base_prompt += history_section
    
    return base_prompt



def get_fix_required_tasks(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get tasks that need fix loop processing.
    
    Requirements: 4.6
    
    Args:
        state: The AGENT_STATE dictionary
        
    Returns:
        List of tasks in fix_required status
    """
    return [t for t in state.get("tasks", []) if t.get("status") == "fix_required"]


def on_fix_task_complete(state: Dict[str, Any], task_id: str) -> None:
    """
    Called when a fix task completes.
    
    1. Increment fix_attempts (fix attempt completed)
    2. Transition to pending_review
    3. Re-dispatch review (will be picked up by review dispatch logic)
    
    Requirements: 3.5, 7.1, 7.2, 7.3
    
    Args:
        state: The AGENT_STATE dictionary
        task_id: The task ID that completed the fix
    """
    task = next((t for t in state.get("tasks", []) if t.get("task_id") == task_id), None)
    if not task:
        return
    
    # Increment fix_attempts (fix attempt completed)
    task["fix_attempts"] = task.get("fix_attempts", 0) + 1
    
    # Transition to pending_review
    task["status"] = "pending_review"
    
    # The review result will determine if we stay in fix loop or exit
    # Review dispatch logic will pick this up


def rollback_fix_dispatch(state: Dict[str, Any], task_id: str) -> None:
    """
    Rollback task status after fix dispatch failure.
    
    - Transition from in_progress back to fix_required
    - Do NOT increment fix_attempts
    
    Requirements: 7.4, 7.5
    
    Args:
        state: The AGENT_STATE dictionary
        task_id: The task ID that failed to dispatch
    """
    task = next((t for t in state.get("tasks", []) if t.get("task_id") == task_id), None)
    if not task:
        return
    
    # Only rollback if currently in_progress (was set by process_fix_loop)
    if task.get("status") == "in_progress":
        task["status"] = "fix_required"


def on_review_complete(state: Dict[str, Any], task_id: str, review_findings: List[Dict]) -> None:
    """
    Called when a review completes.
    
    Determines whether to:
    - Exit fix loop (review passed)
    - Continue fix loop (review failed)
    
    Note: fix_attempts is incremented in on_fix_task_complete (when fix completes),
    NOT here. This function only evaluates the review result and decides next action.
    
    Requirements: 4.6, 3.5
    
    Args:
        state: The AGENT_STATE dictionary
        task_id: The task ID that was reviewed
        review_findings: List of review findings
    """
    task = next((t for t in state.get("tasks", []) if t.get("task_id") == task_id), None)
    if not task:
        return
    
    # Determine severity
    severities = [f.get("severity", "none") for f in review_findings]
    if "critical" in severities:
        overall_severity = "critical"
    elif "major" in severities:
        overall_severity = "major"
    else:
        overall_severity = "none" if not severities else "minor"
    
    if should_enter_fix_loop(overall_severity):
        # Review failed - enter/continue fix loop
        enter_fix_loop(state, task_id, review_findings)
    else:
        # Review passed - exit fix loop
        handle_fix_loop_success(state, task_id)


def handle_fix_loop_success(state: Dict[str, Any], task_id: str) -> None:
    """
    Handle successful fix loop completion.
    
    - Transition task to final_review/completed
    - Unblock dependent tasks
    
    Requirements: 3.9
    
    Args:
        state: The AGENT_STATE dictionary
        task_id: The task ID that passed review
    """
    task = next((t for t in state.get("tasks", []) if t.get("task_id") == task_id), None)
    if not task:
        return
    
    task["status"] = "final_review"
    
    # Unblock dependents
    unblock_dependent_tasks(state, task_id)


def unblock_dependent_tasks(state: Dict[str, Any], task_id: str) -> None:
    """
    Unblock tasks that were blocked by the given task.
    
    Called when a fix loop succeeds.
    
    Requirements: 3.9
    
    Args:
        state: The AGENT_STATE dictionary
        task_id: The task ID that was blocking others
    """
    for task in state.get("tasks", []):
        if task.get("blocked_by") == task_id:
            task["status"] = "not_started"
            task["blocked_reason"] = None
            task["blocked_by"] = None
    
    # Remove from blocked_items
    state["blocked_items"] = [
        item for item in state.get("blocked_items", [])
        if item.get("task_id") != task_id
    ]


def process_fix_loop(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Process all tasks in fix_required status.
    
    For each fix_required task:
    1. Evaluate action based on COMPLETED attempts (retry, escalate, human_fallback)
    2. Create fix request with feedback
    3. Return list of fix requests to dispatch
    
    Note: fix_attempts is incremented in on_fix_task_complete (when fix completes),
    NOT here. This function only evaluates and creates fix requests.
    
    Requirements: 4.6
    
    Args:
        state: The AGENT_STATE dictionary
        
    Returns:
        List of fix request dictionaries ready for dispatch
    """
    fix_tasks = get_fix_required_tasks(state)
    fix_requests = []
    
    for task in fix_tasks:
        task_id = task["task_id"]
        severity = task.get("last_review_severity", "major")
        
        # Evaluate action based on COMPLETED attempts (before this dispatch)
        completed_attempts = task.get("fix_attempts", 0)
        action = evaluate_fix_loop_action(task, severity)
        
        if action == FixLoopAction.HUMAN_FALLBACK:
            trigger_human_fallback(state, task_id)
            continue
        
        if action == FixLoopAction.PASS:
            # Shouldn't happen for fix_required tasks, but handle gracefully
            continue
        
        # Get findings from latest review history entry
        review_history = task.get("review_history", [])
        latest_findings = review_history[-1].get("findings", []) if review_history else []
        
        try:
            fix_request = create_fix_request(state, task_id, latest_findings)
        except ValueError:
            continue
        
        # Determine backend (escalate to codex if needed)
        use_escalation = action == FixLoopAction.ESCALATE
        owner_agent = task.get("owner_agent")
        if not owner_agent and not use_escalation:
            state.setdefault("pending_decisions", [])
            decision_id = f"missing-owner-agent-{task_id}"
            if not any(d.get("id") == decision_id for d in state["pending_decisions"]):
                state["pending_decisions"].append({
                    "id": decision_id,
                    "task_id": task_id,
                    "priority": "high",
                    "context": (
                        "Fix loop cannot dispatch because owner_agent is missing. "
                        "Codex must set owner_agent before retrying fixes."
                    ),
                    "options": [
                        "Set owner_agent and retry fix loop",
                        "Defer this fix task",
                        "Abort orchestration"
                    ],
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
            continue
        backend = "codex" if use_escalation else owner_agent
        
        if use_escalation and not task.get("escalated"):
            task["escalated"] = True
            task["escalated_at"] = datetime.now(timezone.utc).isoformat()
            task["original_agent"] = task.get("owner_agent")
        
        # Transition to in_progress
        # NOTE: fix_attempts is NOT incremented here - only after fix completes
        task["status"] = "in_progress"
        
        # Build fix prompt
        prompt = build_fix_prompt(fix_request, task)
        
        fix_requests.append({
            "task_id": task_id,
            "backend": backend,
            "prompt": prompt,
            "fix_request": fix_request,
            "use_escalation": use_escalation,
        })
    
    return fix_requests



def trigger_human_fallback(state: Dict[str, Any], task_id: str) -> None:
    """
    Suspend task and request human intervention.
    
    Called when max fix attempts are exceeded.
    
    Requirements: 3.7, 3.8
    
    Args:
        state: The AGENT_STATE dictionary
        task_id: The task ID that needs human intervention
    """
    task = next((t for t in state.get("tasks", []) if t.get("task_id") == task_id), None)
    if not task:
        return
    
    task["status"] = "blocked"
    task["blocked_reason"] = "human_intervention_required"
    
    # Include review history in context
    history_text = format_review_history(task.get("review_history", []))
    
    # Create pending decision entry (Req 3.8)
    if "pending_decisions" not in state:
        state["pending_decisions"] = []
    
    state["pending_decisions"].append({
        "id": f"human-fallback-{task_id}",
        "task_id": task_id,
        "priority": "critical",
        "context": f"""HUMAN INTERVENTION REQUIRED

Task: {task_id} - {task.get('description', 'No description')}
Fix Attempts: {task.get('fix_attempts', 0)}/{MAX_FIX_ATTEMPTS}

Review History:
{history_text}

Action Required:
1. Review the code and findings manually
2. Either fix the issue or adjust requirements
3. Resume orchestration when ready
""",
        "options": [
            "I've fixed it manually - resume",
            "Skip this task - continue without it",
            "Abort orchestration"
        ],
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Block dependent tasks
    block_dependent_tasks(state, task_id, "Upstream task requires human intervention")
