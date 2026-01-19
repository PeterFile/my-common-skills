# Phase 2: Design Document Creation

Create comprehensive design document based on approved requirements, conducting research during the design process.

> **Note**: Design documents should be thorough. Avoid over-applying "minimal" philosophy to documentation—designs need sufficient depth for implementation clarity.

## Prerequisites

- Ensure requirements.md exists at `.kiro/specs/{feature-name}/requirements.md`
- Requirements must be approved before design phase

## Research Phase

1. **Identify Research Needs**
   - What technologies/patterns need investigation?
   - What existing solutions can inform the design?

2. **Conduct Research**
   - Use available resources (web search, documentation, MCP tools)
   - Build context in conversation thread
   - Summarize key findings with source links
   - **Don't create separate research files**
   - Cite sources with relevant links

---

## Design Document Structure

Create `.kiro/specs/{feature-name}/design.md` with the following sections.

### 1. Overview

- High-level approach and rationale (WHY this design)
- Key architectural decisions with trade-offs considered
- Technology stack choices with justifications

### 2. Architecture

- Component relationship diagram (Mermaid, ASCII, or other)
- Data flow between components
- External integrations and dependencies
- Deployment topology (if applicable)

### 3. Components and Interfaces

**For each component, document:**

- **Purpose**: What problem it solves
- **Responsibilities**: What it does and does not do
- **Interface contract**: Methods/functions it exposes (use language appropriate to the project)
- **Dependencies**: What it requires from other components
- **Design rationale**: Why this approach was chosen

**Depth Anchor**: Interfaces should be complete enough that another developer could implement the component without asking clarifying questions.

### 4. Data Models

- Entity definitions with all attributes
- Relationships between entities
- State transitions and lifecycle rules
- Validation constraints
- Persistence strategy (where data lives)

### 5. Correctness Properties

**What is a Property?**

A property is a **universal statement** about system behavior—an invariant that must always be true regardless of inputs.

**Property Format:**

```markdown
### Property N: [Descriptive Name]

_For any_ [quantified inputs], [precondition clause], [system] SHALL [expected behavior].

**Validates: Requirement X.Y**
```

**Extraction Process:**

1. Read each EARS acceptance criterion
2. Transform to universal form using `_For any_`
3. Link to source requirement number

**Coverage Targets:**

- Every testable AC should map to a property
- Include properties for error conditions
- Include properties for state transition rules
- Include properties for data integrity

### 6. Error Handling

**First Principle**: Ask "What can go wrong?" for every component, data flow, and user interaction in this system.

**Thought Process:**

1. **Trace every input** — Where does data enter the system? What if it's invalid, missing, malformed, or malicious?

2. **Trace every dependency** — What external systems, services, or resources does this depend on? What if they fail, timeout, return unexpected data, or are unavailable?

3. **Trace every state transition** — What if the system is in an unexpected state? What if operations happen out of order or concurrently?

4. **Trace every output** — What if the operation partially succeeds? What should the user see? What state should be preserved?

**Documentation Approach:**

Document error handling in whatever format best serves THIS system:
- For APIs: Error codes, status codes, response structures
- For frontends: User-facing messages, recovery UI, degraded states
- For distributed systems: Actor behaviors, retry strategies, circuit breakers
- For data pipelines: Validation failures, partial processing, rollback strategies

The format should emerge from the system's nature, not from a template.

**Quality Check:**

- [ ] Every external call has failure handling
- [ ] Every user input has validation
- [ ] Partial failure scenarios are addressed
- [ ] Recovery paths are documented
- [ ] The user experience during errors is considered

### 7. Testing Strategy

- **Unit Tests**: Key components/functions to test
- **Integration Tests**: End-to-end flows to verify
- **Property-Based Tests**: Link to Correctness Properties
- Performance testing considerations

---

## Review & Iteration

After creating/updating design:
- Ask: "Does the design look good? If so, we can move on to the implementation plan."
- Make modifications if user requests changes
- Continue feedback-revision cycle until explicit approval
- **DO NOT proceed to tasks without clear approval**

## Quality Principles

- **Comprehensive over minimal** — Designs need depth for implementation
- **Language appropriate** — Use idioms fitting the project's stack
- **Visual when helpful** — Diagrams for complex flows
- **Explain WHY** — Rationale for design decisions
- **Correctness first** — Properties derived from requirements
