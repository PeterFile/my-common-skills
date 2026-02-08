"""
Multi-Agent Orchestrator Scripts

Parses tasks.md for orchestration. Agent reads requirements.md and design.md directly.
Provides initialization, batch dispatch, and review dispatch functionality.
"""

from .spec_parser import (
    Task,
    TaskType,
    TaskStatus,
    ParseError,
    TasksParseResult,
    ValidationResult,
    DependencyGraph,
    DependencyResult,
    CircularDependencyError,
    MissingDependencyError,
    parse_tasks,
    validate_spec_directory,
    extract_dependencies,
    get_ready_tasks,
    topological_sort,
    load_tasks_from_spec,
    # New dispatch unit functions
    is_dispatch_unit,
    get_dispatchable_units,
)

from .init_orchestration import (
    TaskEntry,
    AgentState,
    InitResult,
    initialize_orchestration,
    assign_owner_agent,
    determine_criticality,
    convert_task_to_entry,
)

from .dispatch_batch import (
    TaskConfig,
    ExecutionReport,
    DispatchResult,
    dispatch_batch,
    get_ready_tasks as get_ready_tasks_from_state,
    build_task_configs,
    # New dispatch unit types and functions
    SubtaskInfo,
    DispatchPayload,
    build_dispatch_payload,
    get_dispatchable_units_from_state,
    handle_partial_completion,
)

from .dispatch_reviews import (
    ReviewTaskConfig,
    ReviewReport,
    ReviewDispatchResult,
    dispatch_reviews,
    get_tasks_pending_review,
    get_review_count,
    build_review_configs,
)

__all__ = [
    # spec_parser
    "Task",
    "TaskType",
    "TaskStatus",
    "ParseError",
    "TasksParseResult",
    "ValidationResult",
    "DependencyGraph",
    "DependencyResult",
    "CircularDependencyError",
    "MissingDependencyError",
    "parse_tasks",
    "validate_spec_directory",
    "extract_dependencies",
    "get_ready_tasks",
    "topological_sort",
    "load_tasks_from_spec",
    # spec_parser - dispatch unit functions
    "is_dispatch_unit",
    "get_dispatchable_units",
    # init_orchestration
    "TaskEntry",
    "AgentState",
    "InitResult",
    "initialize_orchestration",
    "assign_owner_agent",
    "determine_criticality",
    "convert_task_to_entry",
    # dispatch_batch
    "TaskConfig",
    "ExecutionReport",
    "DispatchResult",
    "dispatch_batch",
    "get_ready_tasks_from_state",
    "build_task_configs",
    # dispatch_batch - dispatch unit types and functions
    "SubtaskInfo",
    "DispatchPayload",
    "build_dispatch_payload",
    "get_dispatchable_units_from_state",
    "handle_partial_completion",
    # dispatch_reviews
    "ReviewTaskConfig",
    "ReviewReport",
    "ReviewDispatchResult",
    "dispatch_reviews",
    "get_tasks_pending_review",
    "get_review_count",
    "build_review_configs",
]
