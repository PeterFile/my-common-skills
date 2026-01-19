# Phase 4: Task Execution

## Execute Phase

Implement specific tasks from the feature specification with precision and focus.

### Prerequisites

**ALWAYS read spec files first**:
- `.kiro/specs/{feature-name}/requirements.md`
- `.kiro/specs/{feature-name}/design.md`
- `.kiro/specs/{feature-name}/tasks.md`

Never execute tasks without understanding full context.

### Execution Process

1. **Task Selection**
   - If task number/description provided: Focus on that specific task
   - If no task specified: Review task list and recommend next logical task
   - If task has sub-tasks: Always complete sub-tasks first

2. **Implementation**
   - **ONE task at a time** - Never implement multiple without approval
   - **Minimal code** - Write only what's necessary for current task
   - **Follow the design** - Adhere to architecture decisions
   - **Verify requirements** - Ensure implementation meets specifications

3. **Completion Protocol**
   - Once task complete, STOP and inform user
   - DO NOT proceed to next task automatically
   - Wait for user review and approval
   - Only run tests if explicitly requested

### Efficiency Principles

- **Parallel operations**: Execute independent operations simultaneously
- **Batch edits**: Use MultiEdit for multiple changes to same file
- **Minimize steps**: Complete tasks in fewest operations
- **Check your work**: Verify implementation meets requirements

### Response Patterns

**For implementation requests**:
1. Read relevant spec files
2. Identify the specific task
3. Implement with minimal code
4. Stop and await review

**For information requests**:
- Answer directly without starting implementation
- Examples: "What's the next task?", "What tasks are remaining?"

### Key Behaviors

- Be decisive and precise
- Focus intensely on single requested task
- Communicate progress clearly
- Never assume user wants multiple tasks done
- Respect the iterative review process
