# Workspace Browser Smoke: Runtime Import Path Pitfall

Use this note when validating UI changes in a monorepo/workspace package through a host app.

## Problem
A source edit can typecheck and still not appear in browser smoke if the host app imports the package through its built output (`dist`) instead of the package source. Vite/desktop dev may resolve an internal workspace package via `package.json` `exports`/`main`, so the browser can serve stale `dist/*.js` while `src/*.tsx` contains the fix.

## Debug pattern
1. Inspect the host app import and the package `package.json` exports/main fields.
2. Fetch or inspect the served module path from the dev server when possible.
   - Example signal: `/src/main.tsx` imports `@workspace/ui` from `packages/ui/dist/index.js`.
3. If the host serves `dist`, run the package build before browser smoke.
4. Clear persisted browser/app state if the bug may have already been saved into localStorage or equivalent.
5. Re-run the browser smoke after waiting longer than the relevant timer/async loop.

## Durable rule
Browser smoke validates the live served artifact, not the edited source file. Prove which artifact is live before trusting the result.

## Agent-driven demo acceptance
When a repo acceptance command drives real agents and can exceed foreground tool limits, run it as a managed background process instead of treating a foreground timeout as failure. Use a short, intentionally bounded diagnostic mode only to localize the first stuck lane, then run the full command in the background and inspect its durable run/event artifacts while it is active. For SkyTurn-style demos, `.devflow/runs/*/events.ndjson` and `.devflow/tasks/*/output.md` are evidence: they can show which lane is active, whether a validation blocker is real, and whether a later lane fixed it. Do not claim success until the parent command exits and reports its final structured result (for example `ok: true` plus screenshot/test/graph fields).
