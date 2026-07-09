---
name: oss-issue-scout
description: Analyze a user-provided Git repository and GitHub issues to confirm contribution rules (CONTRIBUTING, CLA/DCO, templates) and shortlist high-value, maintainer-friendly issues likely to be accepted. Use when a user wants help selecting open-source issues to contribute to, or when triaging a GitHub repo for good first contributions.
---

# OSS Issue Scout

## Overview

Identify contribution rules and surface a small set of high-value, maintainer-friendly issues for a given GitHub repository.

## Workflow

### 1) Confirm inputs

- Ask for the repo URL or a local repo path and whether GitHub access is available.
- Ask for constraints: language/stack familiarity, time budget, desired impact, preferred work type (bug/doc/test/feature), and skill level.
- Ask if the user can run tests and open PRs.

### 2) Read contribution rules and signals

- Check repo docs locally or via GitHub: CONTRIBUTING.md, README, CODE_OF_CONDUCT, SECURITY.md, LICENSE, GOVERNANCE, MAINTAINERS, issue/PR templates, .github/ folder, CI configs.
- Note CLA/DCO requirements, branch naming, commit rules, test expectations, and required checks.
- If any open-source or GitHub practice is unclear, use Context7 to refresh before advising.

### 3) Pull issues via GitHub MCP

- Discover available GitHub MCP resources/templates and use them to list open issues with labels, assignees, milestones, and last activity.
- Prefer issues labeled good first issue/help wanted/bug/docs/tests and those with clear acceptance criteria.
- Filter out: stale/needs info, blocked, huge refactors, security-sensitive items, no reproduction steps, or already assigned issues.
- Cross-check for linked PRs, duplicates, or active discussions that indicate ongoing work.

### 4) Score and shortlist

- Use `references/issue-scoring.md` to score value, acceptance likelihood, clarity, and effort fit.
- Select 3-7 issues with the best balance of impact and low acceptance risk; keep scope aligned to user constraints.

### 5) Report back

- Provide a concise list of recommended issues with links, labels, last activity, estimated effort, and why they are good picks.
- Summarize contribution rules and any blockers.
- Ask targeted questions if key info is missing or if all candidate issues are low quality.

## Output format

- Recommended issues
- Contribution rules and constraints
- Risks/unknowns
- Questions for the user
- Suggested next actions

## References

- Read `references/issue-scoring.md` when scoring or filtering issues.
