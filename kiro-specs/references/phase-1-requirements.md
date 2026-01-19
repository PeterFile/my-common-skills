# Phase 1: Requirements Gathering

Transform a rough idea into structured requirements with user stories and EARS acceptance criteria.

## Process

1. **Generate Initial Requirements**
   - Create `.kiro/specs/{feature-name}/requirements.md`
   - Use kebab-case for feature name (e.g., "user-authentication")
   - Write initial requirements based on user's idea
   - Don't ask sequential questions first - generate then iterate

2. **Requirements Structure**

```markdown
# Requirements Document

## Introduction

[Feature summary - what problem does this solve?]

## Glossary

[Define domain-specific terms. Ensures consistent vocabulary across requirements, design, and tasks.]

- **Term_Name**: Definition and context

## Requirements

### Requirement 1: [Descriptive Title]

**User Story:** As a [role], I want [feature], so that [benefit]

#### Acceptance Criteria

1. WHEN [event] THEN THE [system] SHALL [response]
2. IF [precondition] THEN THE [system] SHALL [response]
3. WHILE [state] THE [system] SHALL [response]
```

## EARS Format

**Easy Approach to Requirements Syntax** - structured acceptance criteria:

| Pattern | Usage |
|---------|-------|
| `WHEN [event] THEN THE [system] SHALL [response]` | Event-driven |
| `IF [condition] THEN THE [system] SHALL [response]` | Conditional |
| `WHILE [state] THE [system] SHALL [response]` | State-driven |
| `WHERE [feature] THE [system] SHALL [response]` | Ubiquitous |
| `THE [system] SHALL [response]` | Unconditional |

## Quality Anchors

Each requirement should have ACs covering:
- **Happy path**: Normal operation
- **Edge cases**: Boundary conditions, empty states
- **Error conditions**: What happens when things fail
- **State transitions**: Before/after behaviors

**Numbering**: Use dot notation (1.1, 1.2) for precise traceability in design.

## Review & Iteration

After creating/updating requirements:
- Ask: "Do the requirements look good? If so, we can move on to the design."
- Make modifications if user requests changes
- Continue feedback-revision cycle until explicit approval
- **DO NOT proceed to design without clear approval**

## Best Practices

- Consider edge cases and technical constraints
- Focus on user experience and success criteria
- Suggest areas needing clarification
- Break down complex requirements into smaller pieces

## Troubleshooting

If clarification stalls:
- Suggest moving to different aspect
- Provide examples or options
- Summarize what's established and identify gaps
- Continue with available information rather than blocking
