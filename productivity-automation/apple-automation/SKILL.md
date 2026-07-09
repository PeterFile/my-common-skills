---
name: apple-automation
description: "Use when automating Apple and macOS personal apps including Notes, Reminders, Messages, Find My, and desktop computer use."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [apple, macos, notes, reminders, imessage, findmy]
    related_skills: []
---

# Apple/macOS Automation

## Overview
Use this umbrella for Apple ecosystem tasks on macOS. Verify the host and required local CLI, perform the action with the app-specific tool, then read back or otherwise verify the result.

## When to Use
- Apple Notes create/search/edit work.
- Apple Reminders add/list/complete work.
- iMessage or SMS send/read flows.
- Find My device or AirTag lookup.
- macOS desktop automation when no direct API exists.

## App Playbooks
### Notes
Use local `memo` tooling when installed. Search before creating duplicates. Verify by reading/searching the note title or changed content.

### Reminders
Use `remindctl` when installed. Include list, due date, and priority when supplied. List matching reminders before completing an ambiguous one.

### iMessage/SMS
Use `imsg` when installed. Resolve recipient ambiguity before sending. Report real command status rather than fabricated message history.

### Find My
Use FindMy.app-backed local tooling. Report timestamp and freshness because locations can be stale.

### macOS Computer Use
Prefer direct APIs first. If using GUI automation, take screenshots, click minimally, and verify visible state.

## Common Pitfalls
1. Assuming Apple tools exist on non-macOS hosts.
2. Creating duplicate notes or reminders without searching.
3. Sending messages to ambiguous recipients.
4. Reporting stale Find My locations without timestamp context.

## Verification Checklist
- [ ] Correct app/tool selected.
- [ ] Ambiguous targets resolved before side effects.
- [ ] Result verified by command output, read-back, or visible state.
