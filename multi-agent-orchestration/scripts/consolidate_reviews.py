#!/usr/bin/env python3
"""
Review Consolidation Script

Consolidates review findings into final reports.
- Collects all review findings for a task
- Generates Final Report with overall severity
- Updates AGENT_STATE.json final_reports

Requirements: 8.9
"""

import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add script directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import fix loop functions for triggering fix loop on critical/major (Req 3.1, 4.6)
from fix_loop import enter_fix_loop, should_enter_fix_loop


# Severity ordering (highest to lowest)
SEVERITY_ORDER = ["critical", "major", "minor", "none"]


@dataclass
class FinalReport:
    """Final consolidated review report for a task"""
    task_id: str
    overall_severity: str
    summary: str
    finding_count: int
    findings: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "task_id": self.task_id,
            "overall_severity": self.overall_severity,
            "summary": self.summary,
            "finding_count": self.finding_count,
            "created_at": self.created_at,
        }


@dataclass
class ConsolidationResult:
    """Result of consolidation operation"""
    success: bool
    message: str
    reports_created: int = 0
    task_ids: List[str] = field(default_factory=list)
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


def get_tasks_in_final_review(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get tasks in final_review status"""
    return [
        task for task in state.get("tasks", [])
        if task.get("status") == "final_review"
    ]


def get_review_findings_for_task(
    state: Dict[str, Any],
    task_id: str
) -> List[Dict[str, Any]]:
    """Get all review findings for a specific task"""
    return [
        finding for finding in state.get("review_findings", [])
        if finding.get("task_id") == task_id
    ]


def determine_overall_severity(findings: List[Dict[str, Any]]) -> str:
    """
    Determine overall severity from multiple findings.
    
    Returns the highest severity found among all findings.
    """
    if not findings:
        return "none"
    
    severities = [f.get("severity", "none") for f in findings]
    
    # Return highest severity
    for severity in SEVERITY_ORDER:
        if severity in severities:
            return severity
    
    return "none"


def generate_summary(findings: List[Dict[str, Any]], task_id: str) -> str:
    """Generate a summary from review findings"""
    if not findings:
        return f"No review findings for task {task_id}"
    
    severity_counts = {}
    for finding in findings:
        severity = finding.get("severity", "none")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    parts = []
    for severity in SEVERITY_ORDER:
        count = severity_counts.get(severity, 0)
        if count > 0:
            parts.append(f"{count} {severity}")
    
    overall = determine_overall_severity(findings)
    
    if overall == "none":
        return f"Task {task_id}: All {len(findings)} review(s) passed with no issues"
    elif overall == "minor":
        return f"Task {task_id}: {len(findings)} review(s) completed with minor issues ({', '.join(parts)})"
    elif overall == "major":
        return f"Task {task_id}: {len(findings)} review(s) found major issues ({', '.join(parts)})"
    else:  # critical
        return f"Task {task_id}: CRITICAL issues found in {len(findings)} review(s) ({', '.join(parts)})"


def consolidate_findings(
    state: Dict[str, Any],
    task_id: str
) -> Optional[FinalReport]:
    """
    Consolidate all review findings for a task into a final report.
    
    Requirement 8.9: Consolidate findings into Final_Report
    """
    findings = get_review_findings_for_task(state, task_id)
    
    if not findings:
        return None
    
    overall_severity = determine_overall_severity(findings)
    summary = generate_summary(findings, task_id)
    
    return FinalReport(
        task_id=task_id,
        overall_severity=overall_severity,
        summary=summary,
        finding_count=len(findings),
        findings=findings,
    )


def has_existing_final_report(state: Dict[str, Any], task_id: str) -> bool:
    """Check if a final report already exists for a task"""
    return any(
        report.get("task_id") == task_id
        for report in state.get("final_reports", [])
    )


def add_final_report(state: Dict[str, Any], report: FinalReport) -> None:
    """Add final report to state"""
    state.setdefault("final_reports", []).append(report.to_dict())


def update_task_to_completed(state: Dict[str, Any], task_id: str) -> None:
    """Update task status to completed"""
    task_map = {t.get("task_id"): t for t in state.get("tasks", [])}
    task = task_map.get(task_id)
    if not task:
        return

    completed_at = datetime.now(timezone.utc).isoformat()
    task["status"] = "completed"
    task["completed_at"] = completed_at

    # Propagate completion to subtasks for dispatch units
    for sid in task.get("subtasks", []):
        subtask = task_map.get(sid)
        if subtask:
            subtask["status"] = "completed"
            subtask["completed_at"] = completed_at


def consolidate_reviews(
    state_file: str,
    task_ids: Optional[List[str]] = None,
    auto_complete: bool = True
) -> ConsolidationResult:
    """
    Consolidate review findings into final reports.
    
    Args:
        state_file: Path to AGENT_STATE.json
        task_ids: Specific task IDs to consolidate (None = all in final_review)
        auto_complete: If True, mark tasks as completed after consolidation
    
    Returns:
        ConsolidationResult with execution details
    
    Requirement 8.9: Consolidate findings into Final_Report
    """
    # Load state
    try:
        state = load_agent_state(state_file)
    except Exception as e:
        return ConsolidationResult(
            success=False,
            message=f"Failed to load state file: {e}",
            errors=[str(e)]
        )
    
    # Determine which tasks to consolidate
    if task_ids is None:
        tasks_to_consolidate = get_tasks_in_final_review(state)
        task_ids = [t["task_id"] for t in tasks_to_consolidate]
    
    if not task_ids:
        return ConsolidationResult(
            success=True,
            message="No tasks to consolidate",
            reports_created=0
        )
    
    # Consolidate each task
    reports_created = 0
    consolidated_task_ids = []
    errors = []
    
    for task_id in task_ids:
        # Skip if already has final report
        if has_existing_final_report(state, task_id):
            continue
        
        # Consolidate findings
        report = consolidate_findings(state, task_id)
        
        if report is None:
            errors.append(f"No review findings found for task {task_id}")
            continue
        
        # Add final report
        add_final_report(state, report)
        reports_created += 1
        consolidated_task_ids.append(task_id)
        
        # Check if fix loop is needed (Req 3.1, 4.6)
        if should_enter_fix_loop(report.overall_severity):
            # Enter fix loop instead of completing
            enter_fix_loop(state, task_id, report.findings)
        elif auto_complete:
            # Only mark as completed if no critical/major issues
            update_task_to_completed(state, task_id)
    
    # Save state
    try:
        save_agent_state(state_file, state)
    except Exception as e:
        return ConsolidationResult(
            success=False,
            message=f"Failed to save state file: {e}",
            reports_created=reports_created,
            task_ids=consolidated_task_ids,
            errors=[str(e)]
        )
    
    return ConsolidationResult(
        success=True,
        message=f"Consolidated {reports_created} final report(s)",
        reports_created=reports_created,
        task_ids=consolidated_task_ids,
        errors=errors
    )


def consolidate_single_task(
    state: Dict[str, Any],
    task_id: str,
    auto_complete: bool = True
) -> Optional[FinalReport]:
    """
    Consolidate reviews for a single task (in-memory operation).
    
    This is the core consolidation function used by other components.
    If critical/major issues are found, enters fix loop instead of completing.
    
    Args:
        state: AGENT_STATE.json data (will be modified in place)
        task_id: Task ID to consolidate
        auto_complete: If True, mark task as completed (unless fix loop needed)
    
    Returns:
        FinalReport if created, None if no findings
    
    Requirements: 8.9, 3.1, 4.6
    """
    # Skip if already has final report
    if has_existing_final_report(state, task_id):
        return None
    
    # Consolidate findings
    report = consolidate_findings(state, task_id)
    
    if report is None:
        return None
    
    # Add final report
    add_final_report(state, report)
    
    # Check if fix loop is needed (Req 3.1, 4.6)
    if should_enter_fix_loop(report.overall_severity):
        # Enter fix loop instead of completing
        enter_fix_loop(state, task_id, report.findings)
    elif auto_complete:
        # Only mark as completed if no critical/major issues
        update_task_to_completed(state, task_id)
    
    return report


def main():
    """Command line entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Consolidate review findings into final reports"
    )
    parser.add_argument(
        "state_file",
        help="Path to AGENT_STATE.json"
    )
    parser.add_argument(
        "--task", "-t",
        action="append",
        dest="task_ids",
        help="Specific task ID to consolidate (can be repeated)"
    )
    parser.add_argument(
        "--no-complete",
        action="store_true",
        help="Don't mark tasks as completed after consolidation"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON"
    )
    
    args = parser.parse_args()
    
    result = consolidate_reviews(
        args.state_file,
        task_ids=args.task_ids,
        auto_complete=not args.no_complete
    )
    
    if args.json:
        output = {
            "success": result.success,
            "message": result.message,
            "reports_created": result.reports_created,
            "task_ids": result.task_ids,
            "errors": result.errors
        }
        print(json.dumps(output, indent=2))
    else:
        if result.success:
            print(f"✅ {result.message}")
            if result.task_ids:
                print(f"   Tasks: {', '.join(result.task_ids)}")
            if result.errors:
                print("   Warnings:")
                for error in result.errors:
                    print(f"   - {error}")
        else:
            print(f"❌ {result.message}")
            for error in result.errors:
                print(f"   - {error}")
            sys.exit(1)


if __name__ == "__main__":
    main()
