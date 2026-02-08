#!/usr/bin/env python3
"""
PULSE Synchronization Script for Multi-Agent Orchestration

Synchronizes AGENT_STATE.json to PROJECT_PULSE.md:
- Updates Mental Model section (if architecture changed)
- Updates Narrative Delta with recent completions
- Updates Risks & Debt with blocked items and pending decisions
- Escalates 24h+ pending decisions

Requirements: 6.1, 6.3, 6.4, 6.6
"""

import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple

# Add script directory to path
sys.path.insert(0, str(Path(__file__).parent))


@dataclass
class SyncResult:
    """Result of sync operation"""
    success: bool
    message: str
    pulse_updated: bool = False
    errors: List[str] = field(default_factory=list)


@dataclass
class MentalModel:
    """Mental Model section data"""
    description: str
    mermaid_diagram: str


@dataclass
class RisksAndDebt:
    """Risks & Debt section data"""
    cognitive_warnings: List[str] = field(default_factory=list)
    technical_debt: List[str] = field(default_factory=list)
    pending_decisions: List[str] = field(default_factory=list)


@dataclass
class SemanticAnchor:
    """Semantic anchor entry"""
    module: str
    path: str
    symbol: str


@dataclass
class PulseDocument:
    """Complete PULSE document structure"""
    mental_model: MentalModel
    narrative_delta: str
    risks_and_debt: RisksAndDebt
    semantic_anchors: List[SemanticAnchor]


# Section header patterns
SECTION_PATTERNS = {
    'mental_model': r'^##\s*🟢?\s*Mental\s*Model',
    'narrative_delta': r'^##\s*🟡?\s*Narrative\s*Delta',
    'risks_and_debt': r'^##\s*🔴?\s*Risks\s*[&＆]\s*Debt',
    'semantic_anchors': r'^##\s*🔗?\s*Semantic\s*Anchors',
}


def parse_datetime(dt_str: str) -> Optional[datetime]:
    """Parse ISO datetime string to datetime object"""
    if not dt_str:
        return None
    try:
        # Handle various ISO formats
        dt_str = dt_str.replace('Z', '+00:00')
        if '.' in dt_str:
            # Handle microseconds
            return datetime.fromisoformat(dt_str)
        else:
            return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        return None


def is_older_than_24h(dt_str: str) -> bool:
    """Check if datetime string is older than 24 hours"""
    dt = parse_datetime(dt_str)
    if not dt:
        return False
    
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return (now - dt) > timedelta(hours=24)


def _find_sections(content: str) -> Dict[str, str]:
    """Find positions and content of each section in the document"""
    lines = content.split('\n')
    sections = {}
    current_section = None
    current_lines = []
    
    for line in lines:
        found_section = None
        for section_name, pattern in SECTION_PATTERNS.items():
            if re.match(pattern, line, re.IGNORECASE):
                found_section = section_name
                break
        
        if found_section:
            if current_section:
                sections[current_section] = '\n'.join(current_lines)
            current_section = found_section
            current_lines = [line]
        elif current_section:
            current_lines.append(line)
    
    if current_section:
        sections[current_section] = '\n'.join(current_lines)
    
    return sections


def _parse_mental_model(content: str) -> MentalModel:
    """Parse Mental Model section"""
    # Extract Mermaid diagram
    mermaid_match = re.search(r'```mermaid\s*(.*?)```', content, re.DOTALL)
    mermaid_diagram = mermaid_match.group(1).strip() if mermaid_match else ''
    
    # Extract description (text before mermaid, excluding header)
    lines_before = content.split('```mermaid')[0] if '```mermaid' in content else content
    description_lines = []
    for line in lines_before.split('\n'):
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('<!--'):
            if '-->' not in line:
                description_lines.append(line)
    
    description = ' '.join(description_lines).strip()
    return MentalModel(description=description, mermaid_diagram=mermaid_diagram)


def _parse_narrative_delta(content: str) -> str:
    """Parse Narrative Delta section"""
    lines = []
    for line in content.split('\n'):
        if not re.match(r'^##', line):
            lines.append(line)
    return '\n'.join(lines).strip()


def _parse_risks_and_debt(content: str) -> RisksAndDebt:
    """Parse Risks & Debt section"""
    cognitive_warnings = []
    technical_debt = []
    pending_decisions = []
    
    current_subsection = None
    
    for line in content.split('\n'):
        line_stripped = line.strip()
        line_lower = line_stripped.lower()
        
        if line_stripped.startswith('###') or line_stripped.startswith('**'):
            if 'cognitive' in line_lower:
                current_subsection = 'cognitive'
                continue
            elif 'technical debt' in line_lower:
                current_subsection = 'debt'
                continue
            elif 'pending' in line_lower:
                current_subsection = 'pending'
                continue
        
        list_match = re.match(r'^[-*]\s+(.+)', line_stripped)
        if list_match and current_subsection:
            item = list_match.group(1).strip()
            if item.lower() == 'none':
                continue
            if current_subsection == 'cognitive':
                cognitive_warnings.append(item)
            elif current_subsection == 'debt':
                technical_debt.append(item)
            elif current_subsection == 'pending':
                pending_decisions.append(item)
    
    return RisksAndDebt(
        cognitive_warnings=cognitive_warnings,
        technical_debt=technical_debt,
        pending_decisions=pending_decisions
    )


def _parse_semantic_anchors(content: str) -> List[SemanticAnchor]:
    """Parse Semantic Anchors section"""
    anchors = []
    anchor_pattern = r'\[([^\]]+)\]\s*`?([^`\s]+)`?\s*->\s*`?([^`\s]+)`?'
    
    for line in content.split('\n'):
        if line.strip().startswith('-') or line.strip().startswith('*'):
            match = re.search(anchor_pattern, line)
            if match:
                anchors.append(SemanticAnchor(
                    module=match.group(1).strip(),
                    path=match.group(2).strip(),
                    symbol=match.group(3).strip()
                ))
    
    return anchors


def parse_pulse(content: str) -> Optional[PulseDocument]:
    """Parse PULSE document from markdown content"""
    sections = _find_sections(content)
    
    required = ['mental_model', 'narrative_delta', 'risks_and_debt', 'semantic_anchors']
    for section in required:
        if section not in sections:
            return None
    
    return PulseDocument(
        mental_model=_parse_mental_model(sections['mental_model']),
        narrative_delta=_parse_narrative_delta(sections['narrative_delta']),
        risks_and_debt=_parse_risks_and_debt(sections['risks_and_debt']),
        semantic_anchors=_parse_semantic_anchors(sections['semantic_anchors'])
    )


def generate_pulse(document: PulseDocument) -> str:
    """Generate PULSE document markdown from structured data"""
    lines = ['# PROJECT_PULSE', '']
    
    # Mental Model
    lines.append('## 🟢 Mental Model')
    lines.append('')
    if document.mental_model.description:
        lines.append(document.mental_model.description)
        lines.append('')
    if document.mental_model.mermaid_diagram:
        lines.append('```mermaid')
        lines.append(document.mental_model.mermaid_diagram)
        lines.append('```')
        lines.append('')
    
    # Narrative Delta
    lines.append('## 🟡 Narrative Delta')
    lines.append('')
    if document.narrative_delta:
        lines.append(document.narrative_delta)
    lines.append('')
    
    # Risks & Debt
    lines.append('## 🔴 Risks & Debt')
    lines.append('')
    
    lines.append('### Cognitive Load Warnings')
    if document.risks_and_debt.cognitive_warnings:
        for warning in document.risks_and_debt.cognitive_warnings:
            lines.append(f'- {warning}')
    else:
        lines.append('- None')
    lines.append('')
    
    lines.append('### Technical Debt')
    if document.risks_and_debt.technical_debt:
        for debt in document.risks_and_debt.technical_debt:
            lines.append(f'- {debt}')
    else:
        lines.append('- None')
    lines.append('')
    
    lines.append('### Pending Decisions')
    if document.risks_and_debt.pending_decisions:
        for decision in document.risks_and_debt.pending_decisions:
            lines.append(f'- {decision}')
    else:
        lines.append('- None')
    lines.append('')
    
    # Semantic Anchors
    lines.append('## 🔗 Semantic Anchors')
    lines.append('')
    if document.semantic_anchors:
        for anchor in document.semantic_anchors:
            lines.append(f'- [{anchor.module}] `{anchor.path}` -> `{anchor.symbol}`')
    else:
        lines.append('- None')
    
    return '\n'.join(lines)



def format_blocked_item(item: Dict[str, Any]) -> str:
    """Format blocked item for PULSE display"""
    task_id = item.get("task_id", "unknown")
    reason = item.get("blocking_reason", "No reason provided")
    resolution = item.get("required_resolution", "")
    
    result = f"[{task_id}] {reason}"
    if resolution:
        result += f" (Resolution: {resolution})"
    return result


def format_pending_decision(decision: Dict[str, Any], escalated: bool = False) -> str:
    """Format pending decision for PULSE display"""
    decision_id = decision.get("id", "unknown")
    task_id = decision.get("task_id", "unknown")
    context = decision.get("context", "No context provided")
    options = decision.get("options", [])
    
    prefix = "⚠️ ESCALATED: " if escalated else ""
    result = f"{prefix}[{decision_id}] {context} (task: {task_id})"
    
    if options:
        options_text = ", ".join(str(o)[:30] for o in options[:3])
        if len(options) > 3:
            options_text += f" (+{len(options) - 3} more)"
        result += f" Options: {options_text}"
    
    return result


def format_deferred_fix(fix: Dict[str, Any]) -> str:
    """Format deferred fix for PULSE display"""
    task_id = fix.get("task_id", "unknown")
    description = fix.get("description", "No description")
    severity = fix.get("severity", "unknown")
    
    return f"[{task_id}] {description} (severity: {severity})"


def get_completed_tasks(agent_state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get list of completed tasks from agent state"""
    tasks = agent_state.get("tasks", [])
    return [t for t in tasks if t.get("status") == "completed"]


def get_in_progress_tasks(agent_state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get list of in-progress tasks from agent state"""
    tasks = agent_state.get("tasks", [])
    return [t for t in tasks if t.get("status") == "in_progress"]


def get_blocked_tasks(agent_state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get list of blocked tasks from agent state"""
    tasks = agent_state.get("tasks", [])
    return [t for t in tasks if t.get("status") == "blocked"]


def build_narrative_delta(agent_state: Dict[str, Any], existing_narrative: str) -> str:
    """
    Build updated Narrative Delta section.
    
    Requirement 6.1: Update Narrative Delta with recent completions
    """
    lines = []
    
    # Get task statistics
    tasks = agent_state.get("tasks", [])
    total = len(tasks)
    completed = len([t for t in tasks if t.get("status") == "completed"])
    in_progress = len([t for t in tasks if t.get("status") == "in_progress"])
    blocked = len([t for t in tasks if t.get("status") == "blocked"])
    pending_review = len([t for t in tasks if t.get("status") == "pending_review"])
    
    # Add spec path info
    spec_path = agent_state.get("spec_path", "unknown")
    lines.append(f"**Orchestration spec:** `{spec_path}`")
    lines.append("")
    
    # Add progress summary
    lines.append("**Progress Summary:**")
    lines.append(f"- Total tasks: {total}")
    lines.append(f"- Completed: {completed}")
    lines.append(f"- In progress: {in_progress}")
    lines.append(f"- Pending review: {pending_review}")
    lines.append(f"- Blocked: {blocked}")
    lines.append("")
    
    # Add recent completions
    completed_tasks = get_completed_tasks(agent_state)
    if completed_tasks:
        lines.append("**Recent Completions:**")
        # Sort by completed_at if available, take last 5
        sorted_tasks = sorted(
            completed_tasks,
            key=lambda t: t.get("completed_at", ""),
            reverse=True
        )[:5]
        for task in sorted_tasks:
            task_id = task.get("task_id", "unknown")
            desc = task.get("description", "")[:50]
            lines.append(f"- ✅ {task_id}: {desc}")
        lines.append("")
    
    # Add in-progress tasks
    in_progress_tasks = get_in_progress_tasks(agent_state)
    if in_progress_tasks:
        lines.append("**Currently In Progress:**")
        for task in in_progress_tasks[:5]:
            task_id = task.get("task_id", "unknown")
            desc = task.get("description", "")[:50]
            owner = task.get("owner_agent", "unknown")
            lines.append(f"- 🔄 {task_id}: {desc} ({owner})")
        lines.append("")
    
    return '\n'.join(lines)


def build_risks_and_debt(
    agent_state: Dict[str, Any],
    existing_risks: RisksAndDebt
) -> RisksAndDebt:
    """
    Build updated Risks & Debt section.
    
    Requirements:
    - 6.1: Update Risks & Debt with blocked items and pending decisions
    - 6.6: Escalate 24h+ pending decisions
    """
    cognitive_warnings = list(existing_risks.cognitive_warnings)
    technical_debt = list(existing_risks.technical_debt)
    pending_decisions = []
    
    # Add blocked items as cognitive warnings
    blocked_items = agent_state.get("blocked_items", [])
    blocked_task_ids = {item.get("task_id") for item in blocked_items}
    
    for item in blocked_items:
        formatted = format_blocked_item(item)
        if formatted not in cognitive_warnings:
            cognitive_warnings.append(f"🚫 BLOCKED: {formatted}")
    
    # Also check tasks with blocked status that might not have blocked_items entry
    blocked_tasks = get_blocked_tasks(agent_state)
    for task in blocked_tasks:
        task_id = task.get("task_id")
        if task_id and task_id not in blocked_task_ids:
            desc = task.get("description", "")[:50]
            warning = f"🚫 BLOCKED: [{task_id}] {desc}"
            if warning not in cognitive_warnings:
                cognitive_warnings.append(warning)
    
    # Add deferred fixes as technical debt
    deferred_fixes = agent_state.get("deferred_fixes", [])
    for fix in deferred_fixes:
        formatted = format_deferred_fix(fix)
        if formatted not in technical_debt:
            technical_debt.append(formatted)
    
    # Add pending decisions with escalation for 24h+ items
    pending = agent_state.get("pending_decisions", [])
    for decision in pending:
        created_at = decision.get("created_at", "")
        escalated = is_older_than_24h(created_at)
        formatted = format_pending_decision(decision, escalated=escalated)
        pending_decisions.append(formatted)
    
    return RisksAndDebt(
        cognitive_warnings=cognitive_warnings,
        technical_debt=technical_debt,
        pending_decisions=pending_decisions
    )


def build_semantic_anchors(
    agent_state: Dict[str, Any],
    existing_anchors: List[SemanticAnchor]
) -> List[SemanticAnchor]:
    """
    Build updated Semantic Anchors section.
    
    Adds anchors for files changed by completed tasks.
    """
    anchors = list(existing_anchors)
    existing_paths = {a.path for a in anchors}
    
    # Add anchors for files changed in completed tasks
    completed_tasks = get_completed_tasks(agent_state)
    for task in completed_tasks:
        files_changed = task.get("files_changed", [])
        task_id = task.get("task_id", "unknown")
        
        for file_path in files_changed:
            if file_path not in existing_paths:
                # Determine module from path
                parts = file_path.split('/')
                module = parts[0] if len(parts) > 1 else "Root"
                
                anchors.append(SemanticAnchor(
                    module=module,
                    path=file_path,
                    symbol=task_id
                ))
                existing_paths.add(file_path)
    
    return anchors


def build_mental_model(
    agent_state: Dict[str, Any],
    existing_model: MentalModel
) -> MentalModel:
    """
    Build updated Mental Model section from agent state.
    
    Updates the mental model description and diagram based on:
    - Spec path information
    - Task completion status
    - Architecture information from design.md (if available)
    
    Requirement 6.1: Update Mental Model if architecture changed
    """
    spec_path = agent_state.get("spec_path", "")
    session_name = agent_state.get("session_name", "roundtable")
    tasks = agent_state.get("tasks", [])
    
    # Build description from state
    total_tasks = len(tasks)
    completed = len([t for t in tasks if t.get("status") == "completed"])
    in_progress = len([t for t in tasks if t.get("status") == "in_progress"])
    
    # Get unique agents involved
    agents = set()
    for task in tasks:
        owner = task.get("owner_agent", "")
        if owner:
            agents.add(owner)
    
    agents_str = ", ".join(sorted(agents)) if agents else "none assigned"
    
    description = (
        f"Multi-agent orchestration for spec: {spec_path}. "
        f"Session: {session_name}. "
        f"Tasks: {completed}/{total_tasks} completed. "
        f"Agents: {agents_str}."
    )
    
    # Build mermaid diagram showing task flow
    mermaid_lines = ["flowchart TB"]
    
    # Add orchestrator node
    mermaid_lines.append("    Orchestrator[Codex Orchestrator]")
    
    # Group tasks by status
    task_groups = {
        "completed": [],
        "in_progress": [],
        "pending_review": [],
        "blocked": [],
        "not_started": [],
    }
    
    for task in tasks[:10]:  # Limit to 10 tasks for readability
        status = task.get("status", "not_started")
        task_id = task.get("task_id", "unknown")
        if status in task_groups:
            task_groups[status].append(task_id)
    
    # Add task nodes by status
    if task_groups["completed"]:
        for tid in task_groups["completed"][:3]:
            safe_id = tid.replace("-", "_").replace(".", "_")
            mermaid_lines.append(f"    {safe_id}[{tid} ✅]")
            mermaid_lines.append(f"    Orchestrator --> {safe_id}")
    
    if task_groups["in_progress"]:
        for tid in task_groups["in_progress"][:3]:
            safe_id = tid.replace("-", "_").replace(".", "_")
            mermaid_lines.append(f"    {safe_id}[{tid} 🔄]")
            mermaid_lines.append(f"    Orchestrator --> {safe_id}")
    
    if task_groups["blocked"]:
        for tid in task_groups["blocked"][:2]:
            safe_id = tid.replace("-", "_").replace(".", "_")
            mermaid_lines.append(f"    {safe_id}[{tid} 🚫]")
            mermaid_lines.append(f"    Orchestrator --> {safe_id}")
    
    mermaid_diagram = "\n".join(mermaid_lines)
    
    return MentalModel(
        description=description,
        mermaid_diagram=mermaid_diagram
    )


def sync_pulse_from_state(
    pulse_content: str,
    agent_state: Dict[str, Any],
    update_mental_model: bool = False
) -> Tuple[str, bool]:
    """
    Synchronize PULSE document from agent state.
    
    Args:
        pulse_content: Current PULSE document content
        agent_state: AGENT_STATE.json data
        update_mental_model: Whether to update mental model section
    
    Returns:
        Tuple of (updated_content, was_updated)
    
    Requirements: 6.1, 6.3, 6.4, 6.6
    """
    # Parse existing PULSE document
    document = parse_pulse(pulse_content)
    if not document:
        return pulse_content, False
    
    # Update Mental Model if requested (Requirement 6.1)
    if update_mental_model:
        new_mental_model = build_mental_model(agent_state, document.mental_model)
    else:
        new_mental_model = document.mental_model
    
    # Update Narrative Delta (Requirement 6.1)
    new_narrative = build_narrative_delta(agent_state, document.narrative_delta)
    
    # Update Risks & Debt (Requirements 6.1, 6.6)
    new_risks = build_risks_and_debt(agent_state, document.risks_and_debt)
    
    # Update Semantic Anchors
    new_anchors = build_semantic_anchors(agent_state, document.semantic_anchors)
    
    # Create updated document
    updated_document = PulseDocument(
        mental_model=new_mental_model,
        narrative_delta=new_narrative,
        risks_and_debt=new_risks,
        semantic_anchors=new_anchors
    )
    
    # Generate updated content
    updated_content = generate_pulse(updated_document)
    
    return updated_content, True



def sync_pulse_files(
    state_file_path: str,
    pulse_file_path: str,
    output_path: Optional[str] = None,
    update_mental_model: bool = False
) -> SyncResult:
    """
    Synchronize PULSE document from state file.
    
    Args:
        state_file_path: Path to AGENT_STATE.json
        pulse_file_path: Path to PROJECT_PULSE.md
        output_path: Output path (default: overwrite pulse_file_path)
        update_mental_model: Whether to update mental model section
    
    Returns:
        SyncResult with success status
    
    Requirements: 6.1, 6.3, 6.4, 6.6
    """
    errors = []
    
    # Read AGENT_STATE.json
    try:
        with open(state_file_path, 'r', encoding='utf-8') as f:
            agent_state = json.load(f)
    except FileNotFoundError:
        return SyncResult(
            success=False,
            message=f"State file not found: {state_file_path}",
            errors=[f"File not found: {state_file_path}"]
        )
    except json.JSONDecodeError as e:
        return SyncResult(
            success=False,
            message=f"Invalid JSON in state file: {e}",
            errors=[str(e)]
        )
    except Exception as e:
        return SyncResult(
            success=False,
            message=f"Failed to read state file: {e}",
            errors=[str(e)]
        )
    
    # Read PROJECT_PULSE.md
    try:
        with open(pulse_file_path, 'r', encoding='utf-8') as f:
            pulse_content = f.read()
    except FileNotFoundError:
        return SyncResult(
            success=False,
            message=f"PULSE file not found: {pulse_file_path}",
            errors=[f"File not found: {pulse_file_path}"]
        )
    except Exception as e:
        return SyncResult(
            success=False,
            message=f"Failed to read PULSE file: {e}",
            errors=[str(e)]
        )
    
    # Sync
    updated_content, was_updated = sync_pulse_from_state(
        pulse_content, agent_state, update_mental_model=update_mental_model
    )
    
    if not was_updated:
        return SyncResult(
            success=False,
            message="Failed to parse PULSE document",
            errors=["Could not parse PULSE document structure"]
        )
    
    # Write output
    output_file = output_path or pulse_file_path
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
    except Exception as e:
        return SyncResult(
            success=False,
            message=f"Failed to write output file: {e}",
            errors=[str(e)]
        )
    
    return SyncResult(
        success=True,
        message=f"Successfully synchronized PULSE document to {output_file}",
        pulse_updated=True
    )


def sync_pulse(
    agent_state: Dict[str, Any],
    pulse_document: PulseDocument,
    update_mental_model: bool = False
) -> PulseDocument:
    """
    Sync agent state to PULSE document (in-memory).
    
    This is the core sync function used by other components.
    
    Args:
        agent_state: AGENT_STATE.json data
        pulse_document: Existing PULSE document
        update_mental_model: Whether to update mental model section
    
    Returns:
        Updated PulseDocument
    
    Requirements: 6.1, 6.3, 6.4, 6.6
    """
    # Update Mental Model if requested (Requirement 6.1)
    if update_mental_model:
        new_mental_model = build_mental_model(agent_state, pulse_document.mental_model)
    else:
        new_mental_model = pulse_document.mental_model
    
    # Update Narrative Delta
    new_narrative = build_narrative_delta(agent_state, pulse_document.narrative_delta)
    
    # Update Risks & Debt
    new_risks = build_risks_and_debt(agent_state, pulse_document.risks_and_debt)
    
    # Update Semantic Anchors
    new_anchors = build_semantic_anchors(agent_state, pulse_document.semantic_anchors)
    
    return PulseDocument(
        mental_model=new_mental_model,
        narrative_delta=new_narrative,
        risks_and_debt=new_risks,
        semantic_anchors=new_anchors
    )


def main():
    """Command line entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Synchronize PROJECT_PULSE.md with AGENT_STATE.json"
    )
    parser.add_argument(
        "state_file",
        help="Path to AGENT_STATE.json"
    )
    parser.add_argument(
        "pulse_file",
        help="Path to PROJECT_PULSE.md"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: overwrite pulse_file)"
    )
    parser.add_argument(
        "--update-mental-model",
        action="store_true",
        help="Update the Mental Model section from agent state"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON"
    )
    
    args = parser.parse_args()
    
    result = sync_pulse_files(
        args.state_file,
        args.pulse_file,
        args.output,
        update_mental_model=args.update_mental_model
    )
    
    if args.json:
        output = {
            "success": result.success,
            "message": result.message,
            "pulse_updated": result.pulse_updated,
            "errors": result.errors
        }
        print(json.dumps(output, indent=2))
    else:
        if result.success:
            print(f"✅ {result.message}")
        else:
            print(f"❌ {result.message}")
            for error in result.errors:
                print(f"   - {error}")
            sys.exit(1)


if __name__ == "__main__":
    main()
