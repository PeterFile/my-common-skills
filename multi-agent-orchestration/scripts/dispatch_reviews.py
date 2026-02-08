#!/usr/bin/env python3
"""
Review Dispatch Script

Dispatches review tasks for completed implementation work.
- Identifies tasks in pending_review status
- Builds review task config with codex backend
- Invokes codeagent-wrapper for review batch
- Spawns multiple reviewers for complex/security-sensitive tasks

Requirements: 8.1, 8.2, 8.3, 8.4
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Any, Set

# Add script directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import fix loop functions for review completion handling (Req 3.1, 4.6)
from fix_loop import on_review_complete, should_enter_fix_loop

from codeagent_wrapper_utils import (
    ensure_tmux_tmpdir,
    looks_like_tmux_connect_error,
    looks_like_tmux_missing,
    resolve_codex_timeout_seconds,
    resolve_codeagent_wrapper,
    tmux_enabled,
)


# Review count by criticality (Requirement 8.5, 8.6)
REVIEW_COUNT_BY_CRITICALITY = {
    "standard": 1,
    "complex": 2,
    "security-sensitive": 2,
}


def _task_id_sort_key(task_id: str) -> List[Any]:
    """Sort key for task IDs like '1.2.3' using numeric ordering."""
    key: List[Any] = []
    for part in task_id.split("."):
        if part.isdigit():
            key.append(int(part))
        else:
            key.append(part)
    return key


@dataclass
class ReviewTaskConfig:
    """Review task configuration for codeagent-wrapper"""
    review_id: str
    task_id: str
    backend: str = "codex"
    workdir: str = "."
    content: str = ""
    reviewer_index: int = 1
    dependencies: List[str] = field(default_factory=list)
    
    def to_heredoc(self) -> str:
        """Convert to heredoc format for codeagent-wrapper"""
        lines = [
            "---TASK---",
            f"id: {self.review_id}",
            f"backend: {self.backend}",
            f"workdir: {self.workdir}",
        ]
        if self.dependencies:
            lines.append(f"dependencies: {','.join(self.dependencies)}")
        lines.extend([
            "---CONTENT---",
            self.content,
        ])
        return "\n".join(lines)


@dataclass
class ReviewReport:
    """Review report from codeagent-wrapper"""
    success: bool
    reviews_completed: int
    reviews_failed: int
    review_results: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class ReviewDispatchResult:
    """Result of review dispatch"""
    success: bool
    message: str
    reviews_dispatched: int = 0
    review_report: Optional[ReviewReport] = None
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


def _is_dispatch_unit(task: Dict[str, Any]) -> bool:
    """
    Check if task is a dispatch unit (parent or standalone).
    """
    subtasks = task.get("subtasks", [])
    parent_id = task.get("parent_id")
    if subtasks:
        return True
    if parent_id is None:
        return True
    return False


def get_tasks_pending_review(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get dispatch units pending review.

    - Parent tasks: all subtasks are pending_review
    - Standalone tasks: task itself is pending_review

    Requirement 9.1: Identify dispatch units needing review
    """
    task_map = {t.get("task_id"): t for t in state.get("tasks", [])}
    pending = []

    for task in state.get("tasks", []):
        if not _is_dispatch_unit(task):
            continue

        subtask_ids = task.get("subtasks", [])
        if subtask_ids:
            # Parent task: all subtasks must be pending_review
            if all(task_map.get(sid, {}).get("status") == "pending_review" for sid in subtask_ids):
                pending.append(task)
        else:
            # Standalone task
            if task.get("status") == "pending_review":
                pending.append(task)

    return pending


def get_review_count(task: Dict[str, Any]) -> int:
    """
    Get required review count based on criticality.
    
    Requirement 8.5, 8.6: Review count by criticality
    """
    criticality = task.get("criticality", "standard")
    return REVIEW_COUNT_BY_CRITICALITY.get(criticality, 1)


def build_review_content(
    task: Dict[str, Any],
    spec_path: str,
    reviewer_index: int,
    all_tasks: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Build review task content/prompt.
    
    Requirement 8.3: Review agent audits code changes
    """
    files_changed = task.get("files_changed", [])
    output = task.get("output", "")
    task_map = {t.get("task_id"): t for t in all_tasks} if all_tasks else {}
    
    lines = [
        f"Review Task: {task['task_id']}",
        f"Reviewer: #{reviewer_index}",
        "",
        f"Original Task: {task.get('description', 'No description')}",
        "",
        "## Instructions",
        "",
        "Audit the code changes produced by the worker agent.",
        "Produce a Review_Finding with severity assessment:",
        "- critical: Security vulnerability or data loss risk",
        "- major: Significant bug or design flaw",
        "- minor: Code style or minor improvement",
        "- none: No issues found",
        "",
        "## Reference Documents",
        f"- Requirements: {spec_path}/requirements.md",
        f"- Design: {spec_path}/design.md",
        "",
    ]
    
    subtask_ids = task.get("subtasks", [])
    if subtask_ids and task_map:
        lines.append("## Subtask Outputs")
        for sid in sorted(subtask_ids, key=_task_id_sort_key):
            subtask = task_map.get(sid, {})
            subtask_desc = subtask.get("description", "No description")
            subtask_status = subtask.get("status", "not_started")
            subtask_files = subtask.get("files_changed", [])
            subtask_output = subtask.get("output", "")

            lines.append(f"### {sid} - {subtask_desc}")
            lines.append(f"Status: {subtask_status}")

            if subtask_files:
                lines.append("Files Changed:")
                for f in subtask_files:
                    lines.append(f"- {f}")

            if subtask_output:
                lines.append("Output Summary:")
                lines.append(subtask_output[:500])
            else:
                lines.append("Output Summary: (none)")
            lines.append("")
    else:
        if files_changed:
            lines.append("## Files Changed")
            for f in files_changed:
                lines.append(f"- {f}")
            lines.append("")

        if output:
            lines.append("## Implementation Summary")
            lines.append(output[:500])  # Truncate long output
            lines.append("")
    
    lines.extend([
        "## Output Format",
        "",
        "Provide your review as JSON:",
        "```json",
        "{",
        '  "severity": "critical|major|minor|none",',
        '  "summary": "Brief summary of findings",',
        '  "details": "Detailed explanation",',
        '  "issues": [',
        '    {"description": "Issue description", "severity": "major"}',
        "  ]",
        "}",
        "```",
    ])
    
    return "\n".join(lines)


def build_batch_review_content(
    tasks: List[Dict[str, Any]],
    spec_path: str,
    all_tasks: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Build batch review content for multiple tasks.
    
    Combines all pending review tasks into a single prompt for one agent.
    Reduces API calls from N to 1.
    """
    task_map = {t.get("task_id"): t for t in all_tasks} if all_tasks else {}
    
    lines = [
        "# Batch Code Review",
        "",
        f"Review the following {len(tasks)} tasks.",
        "For each task, provide a review finding with severity assessment.",
        "",
        "## Reference Documents",
        f"- Requirements: {spec_path}/requirements.md",
        f"- Design: {spec_path}/design.md",
        "",
        "---",
        "",
    ]
    
    for idx, task in enumerate(tasks, start=1):
        task_id = task.get("task_id", "unknown")
        description = task.get("description", "No description")
        files_changed = task.get("files_changed", [])
        output = task.get("output", "")
        subtask_ids = task.get("subtasks", [])
        
        lines.append(f"## Task {idx}: {task_id}")
        lines.append(f"**Description**: {description}")
        lines.append("")
        
        if subtask_ids and task_map:
            lines.append("### Subtasks")
            for sid in sorted(subtask_ids, key=_task_id_sort_key):
                subtask = task_map.get(sid, {})
                subtask_desc = subtask.get("description", "No description")
                subtask_files = subtask.get("files_changed", [])
                lines.append(f"- **{sid}**: {subtask_desc}")
                if subtask_files:
                    lines.append(f"  Files: {', '.join(subtask_files)}")
            lines.append("")
        elif files_changed:
            lines.append("### Files Changed")
            for f in files_changed:
                lines.append(f"- {f}")
            lines.append("")
        
        if output:
            lines.append("### Output Summary")
            lines.append(output[:300])
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    lines.extend([
        "## Output Format",
        "",
        "Provide your review as JSON array:",
        "```json",
        "[",
        "  {",
        '    "task_id": "1",',
        '    "severity": "critical|major|minor|none",',
        '    "summary": "Brief summary",',
        '    "issues": []',
        "  }",
        "]",
        "```",
    ])
    
    return "\n".join(lines)


def build_review_configs(
    tasks: List[Dict[str, Any]],
    spec_path: str,
    workdir: str = ".",
    all_tasks: Optional[List[Dict[str, Any]]] = None
) -> List[ReviewTaskConfig]:
    """
    Build review task configurations.
    
    Requirement 8.2, 8.5, 8.6: Create review tasks with correct count
    """
    configs = []
    
    task_lookup = all_tasks or tasks

    for task in tasks:
        task_id = task["task_id"]
        review_count = get_review_count(task)
        
        for i in range(review_count):
            reviewer_index = i + 1
            review_id = f"review-{task_id}-{reviewer_index}"
            
            config = ReviewTaskConfig(
                review_id=review_id,
                task_id=task_id,
                backend="codex",
                workdir=workdir,
                content=build_review_content(task, spec_path, reviewer_index, task_lookup),
                reviewer_index=reviewer_index,
                dependencies=[task_id],
            )
            configs.append(config)
    
    return configs


def build_heredoc_input(configs: List[ReviewTaskConfig]) -> str:
    """Build heredoc-style input for codeagent-wrapper --parallel"""
    return "\n\n".join(config.to_heredoc() for config in configs)


def invoke_codeagent_wrapper(
    configs: List[ReviewTaskConfig],
    session_name: str,
    state_file: str,
    dry_run: bool = False
) -> ReviewReport:
    """
    Invoke codeagent-wrapper --parallel for reviews.
    
    Requirement 8.1, 8.2: Spawn Review_Codex instances
    """
    heredoc_input = build_heredoc_input(configs)
    
    if dry_run:
        print("DRY RUN - Would invoke codeagent-wrapper with:")
        print("-" * 40)
        print(heredoc_input)
        print("-" * 40)
        return ReviewReport(
            success=True,
            reviews_completed=len(configs),
            reviews_failed=0,
            review_results=[{"review_id": c.review_id, "status": "dry_run"} for c in configs]
        )
    
    full_output = os.environ.get("CODEAGENT_FULL_OUTPUT", "").strip().lower() in {"1", "true", "yes"}
    use_tmux = tmux_enabled()
    cmd_env = os.environ.copy()

    try:
        wrapper_bin = resolve_codeagent_wrapper()
    except FileNotFoundError:
        return ReviewReport(
            success=False,
            reviews_completed=0,
            reviews_failed=len(configs),
            errors=["codeagent-wrapper not found (set CODEAGENT_WRAPPER or add it to PATH)"],
        )

    base_cmd = [wrapper_bin, "--parallel"]
    if full_output:
        base_cmd.append("--full-output")

    cmd_no_tmux = base_cmd + ["--state-file", state_file, "--review"]
    cmd = cmd_no_tmux
    if use_tmux:
        cmd = base_cmd + [
            "--tmux-session",
            session_name,
            "--tmux-no-main-window",
            "--state-file",
            state_file,
            "--review",  # Flag to indicate review mode
        ]
    
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
                result = subprocess.run(
                    cmd_no_tmux,
                    input=heredoc_input,
                    capture_output=True,
                    text=True,
                    env=cmd_env,
                    timeout=timeout_seconds,
                )
            elif looks_like_tmux_connect_error(combined):
                tmpdir = ensure_tmux_tmpdir(cmd_env)
                if tmpdir:
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
                        if looks_like_tmux_connect_error(combined):
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
            return ReviewReport(
                success=result.returncode == 0,
                reviews_completed=report_data.get("reviews_completed", 0),
                reviews_failed=report_data.get("reviews_failed", 0),
                review_results=report_data.get("review_results", []),
                errors=report_data.get("errors", [])
            )
        except json.JSONDecodeError:
            return ReviewReport(
                success=result.returncode == 0,
                reviews_completed=len(configs) if result.returncode == 0 else 0,
                reviews_failed=0 if result.returncode == 0 else len(configs),
                errors=[result.stderr] if result.stderr else []
            )
            
    except subprocess.TimeoutExpired:
        return ReviewReport(
            success=False,
            reviews_completed=0,
            reviews_failed=len(configs),
            errors=[f"Review execution timed out after {timeout_seconds} seconds"]
        )
    except FileNotFoundError:
        return ReviewReport(
            success=False,
            reviews_completed=0,
            reviews_failed=len(configs),
            errors=["codeagent-wrapper not found (set CODEAGENT_WRAPPER or add it to PATH)"],
        )
    except Exception as e:
        return ReviewReport(
            success=False,
            reviews_completed=0,
            reviews_failed=len(configs),
            errors=[str(e)]
        )


def update_task_to_under_review(state: Dict[str, Any], task_ids: List[str]) -> None:
    """Update tasks to under_review status"""
    task_map = {t.get("task_id"): t for t in state.get("tasks", [])}
    for task_id in task_ids:
        task = task_map.get(task_id)
        if not task:
            continue
        task["status"] = "under_review"
        for sid in task.get("subtasks", []):
            subtask = task_map.get(sid)
            if subtask and subtask.get("status") == "pending_review":
                subtask["status"] = "under_review"


def rollback_tasks_to_pending_review(state: Dict[str, Any], task_ids: List[str]) -> None:
    """Rollback tasks to pending_review status (for failed dispatch)"""
    task_map = {t.get("task_id"): t for t in state.get("tasks", [])}
    for task_id in task_ids:
        task = task_map.get(task_id)
        if not task:
            continue
        if task.get("status") == "under_review":
            task["status"] = "pending_review"
        for sid in task.get("subtasks", []):
            subtask = task_map.get(sid)
            if subtask and subtask.get("status") == "under_review":
                subtask["status"] = "pending_review"


def add_review_findings(
    state: Dict[str, Any],
    report: ReviewReport
) -> None:
    """
    Add review findings to state.
    
    Requirement 8.7: Update review_findings in AGENT_STATE.json
    """
    for result in report.review_results:
        # Parse review output to extract finding
        finding = {
            "task_id": result.get("task_id", ""),
            "reviewer": result.get("review_id", ""),
            "severity": result.get("severity", "none"),
            "summary": result.get("summary", "Review completed"),
            "details": result.get("details", ""),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        state.setdefault("review_findings", []).append(finding)


def check_all_reviews_complete(state: Dict[str, Any], task_id: str) -> bool:
    """Check if all required reviews are complete for a task"""
    # Find task
    task = None
    for t in state.get("tasks", []):
        if t["task_id"] == task_id:
            task = t
            break
    
    if not task:
        return False
    
    required_count = get_review_count(task)
    
    # Count completed reviews
    completed_count = sum(
        1 for f in state.get("review_findings", [])
        if f.get("task_id") == task_id
    )
    
    return completed_count >= required_count


def update_completed_reviews_to_final(state: Dict[str, Any]) -> List[str]:
    """Update tasks with all reviews complete to final_review status"""
    updated = []

    task_map = {t.get("task_id"): t for t in state.get("tasks", [])}

    for task in state.get("tasks", []):
        if task.get("status") == "under_review":
            if check_all_reviews_complete(state, task["task_id"]):
                task["status"] = "final_review"
                updated.append(task["task_id"])
                # Propagate to subtasks for dispatch units
                for sid in task.get("subtasks", []):
                    subtask = task_map.get(sid)
                    if subtask and subtask.get("status") in ["under_review", "pending_review"]:
                        subtask["status"] = "final_review"

    return updated


def dispatch_reviews(
    state_file: str,
    workdir: str = ".",
    dry_run: bool = False,
    batch: bool = False
) -> ReviewDispatchResult:
    """
    Dispatch review tasks for completed work.
    
    Args:
        state_file: Path to AGENT_STATE.json
        workdir: Working directory for reviews
        dry_run: If True, don't actually invoke codeagent-wrapper
    
    Returns:
        ReviewDispatchResult with execution details
    
    Requirements: 8.1, 8.2, 8.3, 8.4
    
    Note: Tasks are only marked under_review after successful dispatch.
          On failure, tasks are rolled back to pending_review to allow retry.
    """
    # Load state
    try:
        state = load_agent_state(state_file)
    except Exception as e:
        return ReviewDispatchResult(
            success=False,
            message=f"Failed to load state file: {e}",
            errors=[str(e)]
        )
    
    # Get tasks pending review
    pending_tasks = get_tasks_pending_review(state)
    
    if not pending_tasks:
        return ReviewDispatchResult(
            success=True,
            message="No tasks pending review",
            reviews_dispatched=0
        )
    
    # Build review configs
    spec_path = state.get("spec_path", ".")
    session_name = state.get("session_name", "roundtable")
    task_ids = [t["task_id"] for t in pending_tasks]
    
    if batch:
        # Batch mode: single agent reviews all tasks
        batch_content = build_batch_review_content(pending_tasks, spec_path, all_tasks=state.get("tasks", []))
        configs = [ReviewTaskConfig(
            review_id="batch-review",
            task_id="batch",
            backend="codex",
            workdir=workdir,
            content=batch_content,
            reviewer_index=1,
            dependencies=[],
        )]
    else:
        # Standard mode: one agent per task
        configs = build_review_configs(pending_tasks, spec_path, workdir, all_tasks=state.get("tasks", []))
    
    # Invoke codeagent-wrapper (don't update state until we know result)
    report = invoke_codeagent_wrapper(
        configs,
        session_name,
        state_file,
        dry_run=dry_run
    )
    
    # Process results based on success/failure
    if not dry_run:
        if report.success:
            # Dispatch succeeded - update tasks to under_review
            update_task_to_under_review(state, task_ids)
            # Process review findings
            add_review_findings(state, report)
            # Check if any tasks have all reviews complete
            update_completed_reviews_to_final(state)
        else:
            # Dispatch failed - determine which tasks got partial results
            tasks_with_results = set()
            for result in report.review_results:
                # Prefer task_id field if available (more reliable)
                task_id = result.get("task_id")
                if task_id:
                    tasks_with_results.add(task_id)
                else:
                    # Fallback: extract task_id from review_id (format: review-{task_id}-{index})
                    # Use rsplit to handle task_ids containing dashes (e.g., "task-001")
                    review_id = result.get("review_id", "")
                    if review_id.startswith("review-"):
                        # Remove "review-" prefix, then split from right to get task_id
                        remainder = review_id[len("review-"):]
                        parts = remainder.rsplit("-", 1)
                        if len(parts) == 2 and parts[1].isdigit():
                            tasks_with_results.add(parts[0])
            
            # Only update tasks that got at least some results
            if tasks_with_results:
                update_task_to_under_review(state, list(tasks_with_results))
                add_review_findings(state, report)
                update_completed_reviews_to_final(state)
            
            # Tasks without any results stay as pending_review (no change needed
            # since we didn't update them yet)
        
        save_agent_state(state_file, state)
    
    return ReviewDispatchResult(
        success=report.success,
        message=f"Dispatched {len(configs)} reviews for {len(pending_tasks)} tasks" if report.success else f"Review dispatch failed for {len(pending_tasks)} tasks",
        reviews_dispatched=len(configs),
        review_report=report,
        errors=report.errors
    )


def main():
    """Command line entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Dispatch review tasks for completed work"
    )
    parser.add_argument(
        "state_file",
        help="Path to AGENT_STATE.json"
    )
    parser.add_argument(
        "--workdir", "-w",
        default=".",
        help="Working directory for reviews (default: current directory)"
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
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Batch mode: single agent reviews all tasks (reduces API calls)"
    )
    
    args = parser.parse_args()
    
    result = dispatch_reviews(
        args.state_file,
        workdir=args.workdir,
        dry_run=args.dry_run,
        batch=args.batch
    )
    
    if args.json:
        output = {
            "success": result.success,
            "message": result.message,
            "reviews_dispatched": result.reviews_dispatched,
            "errors": result.errors
        }
        if result.review_report:
            output["review_report"] = {
                "reviews_completed": result.review_report.reviews_completed,
                "reviews_failed": result.review_report.reviews_failed,
            }
        print(json.dumps(output, indent=2))
    else:
        if result.success:
            print(f"✅ {result.message}")
            if result.review_report:
                print(f"   Completed: {result.review_report.reviews_completed}")
                print(f"   Failed: {result.review_report.reviews_failed}")
        else:
            print(f"❌ {result.message}")
            for error in result.errors:
                print(f"   - {error}")
            sys.exit(1)


if __name__ == "__main__":
    main()
