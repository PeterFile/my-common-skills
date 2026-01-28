# Phase 3: Implementation Task List

## Tasks Phase

Convert approved design into actionable, test-driven implementation tasks.

### Prerequisites

- Ensure `design.md` exists and is approved
- Requirements and design provide context for tasks

### Task Generation Instructions

**Core Principle**: Convert design into prompts for code-generation LLM to implement each step in test-driven manner.

**Focus**:

- Incremental progress with early testing
- Build on previous tasks - no orphaned code
- ONLY tasks involving writing, modifying, or testing code
- No big jumps in complexity

**Exclude**:

- User acceptance testing or feedback gathering
- Deployment to production/staging
- Performance metrics gathering
- Running application for manual testing (but OK to write automated end-to-end tests)
- User training or documentation creation
- Business process changes
- Marketing or communication activities

### Pre-Task Verification Gate

Before generating tasks, verify design feasibility to prevent AI hallucination:

**Existence Check** (prevent referencing non-existent APIs):

- [ ] **Dependencies**: Verify all libraries exist in package registry
  - npm: `npm view <package> version`
  - Go: `go list -m <module>@latest`
  - Python: `pip index versions <package>`
- [ ] **API Signatures**: Confirm method signatures against official docs
  - Use MCP tools or direct doc retrieval when available

**Feasibility Check** (prevent logically impossible architectures):

- [ ] **Data Flow**: Can data actually flow as designed?
- [ ] **Interface Compatibility**: Do interfaces align between components?
- [ ] **Constraint Satisfaction**: Are all EARS requirements achievable?

**Gate Decision**:

- ✅ All checks pass → Proceed to task generation
- ❌ Any check fails → Return to Design phase with specific findings

**Bidirectional Feedback**: If verification reveals issues, update design.md with:

```markdown
## Verification Findings

- [Issue description]
- [Recommended fix]
```

### Task Format

Create `.kiro/specs/{feature-name}/tasks.md` with:

```markdown
# Implementation Plan: [Feature Name]

## Overview

[Brief description of the implementation approach. Explain the order of tasks and any key decisions about how work is structured.]

## Tasks

- [ ] 1. Set up project structure and core interfaces
  - Create directory structure for models, services, repositories
  - Define interfaces that establish system boundaries
  - _Requirements: 1.1_
  - _writes: src/types/index.ts, src/interfaces/repository.ts_

- [ ] 2. Implement data models and validation
  - [ ] 2.1 Create core data model interfaces and types
    - Write TypeScript interfaces for all data models
    - Implement validation functions for data integrity
    - _Requirements: 2.1, 3.3, 1.2_
    - _writes: src/models/user.ts, src/models/index.ts_

  - [ ] 2.2 Implement User model with validation
    - Write User class with validation methods
    - Create unit tests for User model validation
    - _Requirements: 1.2_
    - _writes: src/models/user.ts, src/models/**tests**/user.test.ts_

- [ ] 3. Create storage mechanism
  - [ ] 3.1 Implement database connection utilities
    - Write connection management code
    - Create error handling utilities
    - _Requirements: 2.1, 3.3_
    - _writes: src/db/connection.ts, src/db/errors.ts_

[Additional tasks...]

## Notes

- Each task includes `_writes:` manifest for file conflict detection
- [Any additional implementation notes or constraints]
```

### Task Requirements

**Structure**:

- Maximum two-level hierarchy (tasks and sub-tasks)
- Use decimal notation for sub-tasks (1.1, 1.2, 2.1)
- Each item must be a checkbox
- Simple structure preferred

**Each Task Must Include**:

- Clear objective involving code (writing, modifying, testing)
- Additional info as sub-bullets
- Specific requirement references (granular sub-requirements, not just user stories)

**Quality Standards**:

- Discrete, manageable coding steps
- Incremental builds on previous steps
- Test-driven development prioritized
- Covers all design aspects implementable through code
- Validates core functionality early

### Review & Iteration

3. **Ask for Approval**
   - After creating/updating tasks
   - Ask: "Do the tasks look good?"
     - Make modifications if user requests changes
   - Continue feedback-revision cycle until explicit approval
   - **Stop once approved - do not proceed to implementation**

### Completion

**Important**: This workflow is ONLY for creating planning artifacts.

- DO NOT implement the feature as part of this workflow
- Inform user they can execute tasks by:
  - Opening tasks.md
  - Clicking "Start task" next to items
  - Or asking you to execute specific tasks
