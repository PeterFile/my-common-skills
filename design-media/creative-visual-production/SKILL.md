---
name: creative-visual-production
description: "Use when creating visual artifacts such as diagrams, Excalidraw files, HTML mockups, design references, p5.js sketches, pixel art, Manim animations, or DESIGN.md specs."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [creative, diagrams, html, svg, excalidraw, p5js, pixel-art, manim]
    related_skills: []
---

# Creative Visual Production

## Overview
Use this umbrella for visual deliverables. Choose the medium, create a real file or renderable output, and verify by opening, exporting, screenshotting, or running the renderer.

## When to Use
- Architecture or infra diagrams in SVG/HTML.
- Hand-drawn diagrams in Excalidraw JSON.
- HTML landing pages, mockups, prototypes, or design explorations.
- p5.js generative art, shaders, interactive, or 3D sketches.
- Pixel art assets with constrained palettes.
- Manim math or algorithm animations.
- DESIGN.md token specifications.

## Medium Selection
- Architecture diagrams: structured SVG/HTML with clear labels.
- Excalidraw: valid `.excalidraw` JSON.
- HTML/CSS mockups: produce variants when comparison helps.
- p5.js: build runnable sketches and verify in browser/local server.
- Pixel art: respect palette, resolution, tile size, and export format.
- Manim: render scenes and inspect the output.
- DESIGN.md: validate token schema and exports.

## Workflow
1. Clarify dimensions, medium, and audience only when material.
2. Generate source files in the workspace.
3. Run renderer, validator, or export where available.
4. Return artifact path or URL and verification result.

## Common Pitfalls
1. Delivering prose instead of a file.
2. Forgetting aspect ratio, palette, or export target.
3. Producing invalid JSON/HTML/JS without running it.

## Verification Checklist
- [ ] Medium selected.
- [ ] Source and viewable/exported artifact produced.
- [ ] Syntax/render/export verified.
