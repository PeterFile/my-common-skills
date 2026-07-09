---
name: smart-home-operations
description: Use when controlling smart-home devices, rooms, scenes, lights, and local IoT bridges from Hermes, including Philips Hue/OpenHue workflows, device discovery, safe command confirmation, and scheduled automations.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [smart-home, home-automation, lights, hue, openhue, iot, scenes]
    related_skills: []
---

# Smart Home Operations

## Overview
Use this umbrella for controlling local smart-home devices and automations. Treat device control as a real-world side effect: discover exact device/room names, choose the smallest command, verify state where possible, and avoid surprising occupants.

## When to use
- Turning lights, rooms, zones, plugs, or scenes on/off.
- Adjusting brightness, color, color temperature, or scene presets.
- Running scheduled home automations through cron jobs.
- Pairing or troubleshooting local bridges such as Philips Hue.

## Universal workflow
1. Identify the home system and available CLI/API/tool.
2. List rooms/devices/scenes before using user-provided informal names.
3. For broad or disruptive actions (all lights off, bedroom changes late at night, security devices), confirm scope if the user was ambiguous.
4. Execute the smallest command that matches the intent.
5. Verify by reading state/list output when supported.

## Philips Hue / OpenHue
OpenHue is the current CLI reference for Philips Hue bridges. First-run pairing requires pressing the Hue Bridge button and the bridge must be on the same local network.

Common commands:

```bash
openhue get light
openhue get room
openhue get scene
openhue set light "Bedroom Lamp" --on --brightness 50
openhue set light "Bedroom Lamp" --on --temperature 300
openhue set light "Bedroom Lamp" --on --rgb "#FF5500"
openhue set room "Bedroom" --off
openhue set scene "Relax" --room "Bedroom"
```

Useful presets:

```bash
# Bedtime: dim warm
openhue set room "Bedroom" --on --brightness 20 --temperature 450

# Work mode: bright cool
openhue set room "Office" --on --brightness 100 --temperature 250

# Movie mode: dim
openhue set room "Living Room" --on --brightness 10
```

Install OpenHue:

```bash
# Linux
curl -sL https://github.com/openhue/openhue-cli/releases/latest/download/openhue-linux-amd64 -o ~/.local/bin/openhue && chmod +x ~/.local/bin/openhue

# macOS
brew install openhue/cli/openhue-cli
```

## Common pitfalls
1. Light, room, and scene names may be case-sensitive; list them first.
2. First-run bridge pairing is physical and cannot be completed by the agent alone.
3. Color commands only work on color-capable bulbs.
4. Scheduled automations should be explicit about timezone and recurrence.
5. Do not silently run broad destructive/disruptive actions when the room/device scope is unclear.

## Verification checklist
- [ ] Device/room/scene names resolved.
- [ ] Command scope matches user intent.
- [ ] State read-back or command status checked where supported.
