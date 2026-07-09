---
name: living-documentation
description: Sync spec files with code changes. Triggers when modifying code that affects .kiro/specs/*/requirements.md or .kiro/specs/*/design.md. Use after implementing features, fixing bugs, or refactoring that changes behavior documented in specs.
---

# Living Documentation

Spec guides generation. Code changes update spec.

## When Triggered

- Modifying code that implements behavior defined in `requirements.md`
- Changing architecture/interfaces described in `design.md`
- Discovering edge cases or patterns not yet documented

## Lifecycle

| Phase    | Authority   | Action                      |
| -------- | ----------- | --------------------------- |
| Generate | Spec → Code | Follow spec as contract     |
| Modify   | Code → Spec | Update spec to reflect code |

## Sync Protocol

After completing code change:

1. **Identify Affected Specs**
   - Check task's `_writes:` manifest
   - Map to spec sections: which requirements/design does this touch?

2. **Update Spec Content**
   - Remove obsolete descriptions
   - Document actual implementation approach
   - Add discovered edge cases as new ACs
   - Keep spec readable without code

3. **Add Traceability**

   ```markdown
   <!-- impl: path/to/file.ts#FunctionName -->
   ```

4. **Commit Together**
   - Spec changes in same commit as code changes

## What to Update

| Code Change           | Spec Update                       |
| --------------------- | --------------------------------- |
| New function/module   | Add to `design.md#Components`     |
| Behavior change       | Update ACs in `requirements.md`   |
| Edge case handling    | Add AC with EARS format           |
| Architecture decision | Document rationale in `design.md` |
| Removed feature       | Delete from both specs            |

## Quality Check

- [ ] Spec describes current reality, not original plan
- [ ] No stale sections left
- [ ] New reader understands system from spec alone
- [ ] Traceability links added
