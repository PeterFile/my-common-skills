---
name: productivity-api-workflows
description: "Use when operating productivity SaaS and document tools through APIs or CLIs including Airtable, Google Workspace, Linear, Notion, maps, PowerPoint, Teams, and PDFs."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [productivity, api, airtable, google-workspace, linear, notion, documents]
    related_skills: []
---

# Productivity API Workflows

## Overview
Use this umbrella for workplace SaaS, documents, and productivity APIs. Discover schema/context, make the smallest safe mutation, and verify with read-back or returned IDs.

## When to Use
- Airtable records, filters, upserts, and schema-aware updates.
- Google Workspace Gmail, Calendar, Drive, Docs, Sheets.
- Linear issues, projects, and teams.
- Notion pages, databases, and blocks.
- Maps, geocoding, POIs, routes, and timezones.
- PowerPoint deck creation/editing.
- Teams meeting summary pipeline operations.
- PDF edits and document transformations.
- Filesystem-first note-taking workflows such as Obsidian vault search, read, create, append, and wikilink edits. See `references/obsidian-vault.md`.

## API Discipline
1. Resolve credentials and workspace/base/database/team IDs.
2. Read schema or metadata before structured mutations.
3. Use idempotent upserts where appropriate.
4. Verify with fetch/read-back after writes.
5. Return stable handles: record ID, document URL, issue ID, file path, or job ID.

## Common Pitfalls
1. Mutating the wrong workspace/account.
2. Writing fields that do not exist.
3. Treating API success as content correctness.
4. Returning vague done instead of identifiers.

## Verification Checklist
- [ ] Target account/workspace/object identified.
- [ ] Schema or existing object read when needed.
- [ ] Mutation returned a verifiable ID/path/URL.
