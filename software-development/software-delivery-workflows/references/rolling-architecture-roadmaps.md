# Rolling architecture roadmaps

Use this reference when a project direction document starts acting like a parking lot for one subsystem.

## Signals

- User says work is stuck in one direction or not advancing the broader vision.
- The roadmap names one milestone as the whole project direction.
- Agents keep producing green PRs that harden infrastructure but do not ship product-route progress.
- Seed/demo entities are being treated as the product limit instead of a fallback.

## Durable-document pattern

Patch the existing durable direction document instead of creating a new temporary roadmap file.

Required shape:

1. State the product vision in runtime terms: what the product should reflect from the live system.
2. Convert the single milestone into an architecture route table.
3. Define one primary route plus at least two secondary routes for the next delivery wave.
4. Add exit/rotation rules: rotate after a merged validated slice or a concrete blocker; repeat the same primary route only with an explicit exception.
5. Demote foundation/infrastructure hardening to a support route unless it unblocks a product route or fixes a release-blocking regression.
6. Keep progress status in Slack/Linear/controller systems; keep only durable boundaries and route targets in markdown.

## Cadence rule

Do not invent fixed calendar windows when the user is using fast agent development. Use delivery waves tied to validated slices, CI, and blockers.

## Runtime-discovery rule

If the system has a live runtime population, the roadmap should say runtime discovery owns the current shape. Seed data, fixture rosters, and canonical demo actors are compatibility scaffolds or empty-state fallback, not the product ceiling.

Example wording:

> Planning cadence follows agent delivery speed, not a fixed calendar window. Each implementation wave selects one primary route plus at least two secondary routes, then rotates as soon as the selected route has a merged, validated slice or a concrete blocker.

> The world should reflect the company actually running now. Agent count, identities, active rooms, and team shape come from live runtime discovery where available; seeded rosters are fallback only.
