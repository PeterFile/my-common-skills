# Issue Scoring and Filtering

Use this rubric to identify issues that are both high value and likely to be accepted by maintainers.

## Quick filter checklist

- Open, unassigned, and updated within the last 30-90 days.
- Clear reproduction steps or acceptance criteria.
- Labels indicate maintainers want help (good first issue, help wanted, bug, docs, tests, chore).
- Active maintainer involvement (recent comments or triage).
- Scope fits user constraints (1-5 focused PRs, minimal API changes).

## Scoring rubric (0-5 each)

Score each category, then compute: total = value + acceptance + clarity + effort_fit - risk.

- Value: User impact, bug severity, or documentation/testing benefit.
- Acceptance likelihood: Maintainer interest, labels, responsiveness, no conflicting work.
- Clarity: Reproduction steps, acceptance criteria, clear scope.
- Effort fit: Matches user time/skill; not a deep refactor.
- Risk (penalty): Breaking changes, security sensitivity, architectural changes, or unclear scope.

## Red flags (avoid unless explicitly requested)

- Needs design/consensus or major refactor.
- Security vulnerabilities or sensitive disclosures.
- Stale issues with no maintainer response.
- Duplicate issues or already active PRs.
- Missing reproduction steps or ambiguous scope.

## Tiebreakers

- Issues with a maintainer comment outlining expectations.
- Issues tied to a milestone, project board, or release.
- Issues with a clear test plan or suggested fix.

## Suggested output fields

- Link and title
- Labels and last activity date
- Effort estimate (S/M/L)
- Why this is high value
- Acceptance risks or unknowns
