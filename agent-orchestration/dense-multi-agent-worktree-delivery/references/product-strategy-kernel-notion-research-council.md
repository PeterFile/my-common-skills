# Product strategy kernel, Notion map, and research council

Load when: deciding what metaverse-office-web should build next, creating a batch, judging whether work advances the vision, designing UI/world/game-like surfaces, or preventing autonomous agents from optimizing the workflow instead of the product.
Keywords: Notion, capability map, strategy, vision, product council, subagents, research brief, UI design, game UI, spatial UI, agent observability, anti-stagnation, roadmap.

## 1. Problem this solves

The main Hermes agent must not decide product direction from its own intuition.
When humans do not participate in the development loop, the project needs an explicit product strategy kernel:
- a Notion map for vision/capability/decision/research relationships
- a multi-agent product council for proposal/challenge/scoring
- a research loop that learns from current external UI/game/spatial/observability sources
- anti-stagnation metrics that prove product capability moved, not just tests/workflow

Delivery workflow answers: "how do we ship?"
This kernel answers: "what should we ship, and why is it vision progress?"

## 2. Notion's role

Notion owns product/strategy map truth only.

Notion should track:
- vision and outcomes
- personas / operator jobs-to-be-done
- capability map
- decisions and rationale
- research evidence and source quality
- assumptions / risks
- external references to Linear/GitHub/Graphite/Slack/controller/repo docs
- capability delta ledger

Notion must not replace:
- Linear lifecycle truth
- GitHub code/review/test truth
- Graphite stack topology
- Slack communication truth
- controller execution state
- repo append-only/event/read-model truth

Truth split:
1. Git/local/GitHub/Graphite own implementation and merge truth
2. Linear owns execution lifecycle
3. Notion owns strategy/capability/research/decision map
4. Slack broadcasts only

Current setup note: `NOTION_API_KEY` is not configured in `~/.hermes/.env` as of 2026-04-25 inspection, so real Notion database creation requires setup first.

### Activation checklist

When the user asks how to enable the Notion map, give executable setup steps and verify credentials before claiming sync:
1. Create a Notion internal integration at `https://notion.so/my-integrations` with read/insert/update content permissions.
2. Store the token locally, never in chat: add `NOTION_API_KEY=ntn_...` (or `secret_...`) to `~/.hermes/.env` or export it in the shell.
3. Create a root Notion page such as `Metaverse Office Map`.
4. Share/connect that root page to the integration via Notion UI `... -> Connect to -> <integration name>`; without this, the API key cannot see the page.
5. Verify access with a Notion search/read call before creating databases.
6. Create the required MO databases under the shared root page and migrate active controller/council artifacts into them.
7. Record only strategy/capability/decision/research/delta truth in Notion; do not use it as execution or merge truth.

If the API key or page sharing is missing, say exactly that and keep outputs in controller/skill artifacts as a temporary map. Do not claim Notion sync happened.

## 3. Required Notion databases

### MO Vision & Outcomes
Purpose: north-star, non-goals, product principles, success signals.
Key properties:
- Name
- Map ID
- Kind: North Star / Product Outcome / Principle / Non-goal / Metric
- Horizon: Phase 1 / Phase 2 / Quarterly / Long-term
- Strategic State: Draft / Active / Revisit / Archived
- Related Capabilities
- Related Decisions
- Supporting Research
- Success Signals
- Non-goals

Seed principles:
- engineering-focused AI Metaverse Office / Company OS
- real operation, supervision, replay, accountability
- no flashy dashboard/demo
- no manual task assignment / human orchestration as product core
- UI must not outrun event/state/storage/query architecture

### MO Personas & JTBD
Purpose: operator/user jobs-to-be-done.
Key personas:
- internal team lead/operator
- observed employee agent
- engineering maintainer/operator
- future external user

### MO Capability Map
Purpose: capability tree and dependencies.
Key properties:
- Capability ID
- Level: L0 Product / L1 Domain / L2 Capability / L3 Sub-capability / Technical Enabler
- Product Area: World/Runtime, Supervision/Attention, Accountability/Evidence, Replay/Causality, Runtime Ops, Platform/CI
- Map State: Candidate / Defined / Validated / Deprecated / Out of Scope
- Strategic Priority
- Parent / Child / Depends On / Enables
- Related Outcomes / Personas / Decisions / Research / External Refs
- API Surface
- Code Anchors
- Linear / GitHub / Graphite refs
- Drift Flag

Core lanes:
- World / Runtime
- Supervision / Attention
- Accountability / Evidence
- Replay / Causality
- Runtime / Company Ops
- Platform / CI

### MO Decisions
Purpose: product/design/architecture/process decisions and rationale.
Key properties:
- Decision ID
- Decision Type: Product / UX / Architecture / Data Model / Workflow / Scope / Integration
- Decision State: Proposed / Accepted / Rejected / Superseded
- Context
- Options Considered
- Decision
- Consequences
- Reversibility
- Related Capabilities / Research / External Refs
- Repo Anchor Required / Present
- Drift Flag

Repo-affecting decisions must link ADR/spec/PR/code anchor.

### MO Research & Evidence
Purpose: external/user/market/technical/design research.
Key properties:
- Research Question
- Hypothesis
- Finding Summary
- Recommendation: Adopt / Explore / Reject / Monitor / No Action
- Evidence Grade: A Strong / B Useful / C Anecdotal / D Unverified
- Confidence
- Source Refs
- Supports / Challenges Capabilities
- Supports / Challenges Decisions
- Stale After
- Action Needed

No source refs means confidence cannot be High.

### MO External References
Purpose: links to Linear, GitHub, Graphite, Slack, repo paths, API routes, controller artifacts.
Rule: snapshot only; never authoritative status.

### MO Capability Delta Ledger
Purpose: anti-stagnation proof.
Each batch records:
- before capability
- after capability
- operator value
- evidence/replay/accountability delta
- proof links: PR/API/test/demo/research
- demo-drift risk

If a batch cannot fill this ledger with a real product delta, it is maintenance, not product progress.

## 4. Multi-agent product council

The main agent is not the product decider. It acts as facilitator/scribe/router.

Required council roles:
- Vision Steward: guards north-star and anti-goals
- Operator/User Advocate: defends operator jobs-to-be-done
- Product Strategy: assembles coherent batch thesis
- Runtime/Evidence Architect: checks event/state/evidence/replay fit
- Backend/API Agent: checks route/store/projection feasibility
- Frontend/World UX Agent: checks spatial/operator shell design
- QA/Replay Agent: defines test/replay/smoke proof
- Security/Privacy/Cost Agent: checks permissions, data exposure, dependencies, cost
- Red Team/Anti-Demo Agent: attacks dashboard/demo/fake-liveness/manual-assignment drift
- Delivery/Graphite Captain: turns selected proposals into stacks/PR order

Main agent duties:
- prepare context pack
- launch subagents
- collect independent proposals/challenges/scores
- record decision in Notion
- create Linear/Graphite execution objects
- never silently replace council judgment with its own intuition

## 5. Council agenda

### Context pack
Before proposal generation, provide:
- current master/open PR/worktree/controller state
- recent merged PR product delta log
- current Notion capability map gaps
- relevant external research briefs
- current blockers and constraints
- anti-goals and Phase 1 frozen decisions

### Independent proposal round
Each role returns at most 1-2 proposal cards:
- title
- product hypothesis
- operator problem
- capability delta
- evidence source
- affected surfaces
- no-go boundaries
- acceptance checks
- likely slices
- risks/unknowns

### Challenge round
Every shortlisted proposal must receive challenge cards from at least two non-proposer agents and the Red Team:
- challenge type: vision / architecture / evidence / UX / risk / scope
- objection
- failure scenario
- required mitigation
- severity 1-5
- hard veto candidate

### Revision round
Proposers revise by shrinking scope, adding evidence path/tests, or deleting dashboard-only parts.

### Scoring round
Roles score independently before seeing others' scores.

Scoring dimensions:
- Vision alignment
- Evidence/replay/accountability delta
- Operator leverage
- Non-dashboard capability delta
- Architecture fit / reversibility
- Feasibility / batch size
- Testability
- Learning value
- UX clarity
- Security/cost/permission

Hard veto if the proposal:
- centers manual task assignment / orchestration as the product loop
- fabricates liveness, progress, severity, or location
- shows fact-like status with no evidence source
- becomes a dashboard/demo without supervision/replay/accountability gain
- adds write paths/events/storage without ADR/spec rationale
- cannot define acceptance checks

### Batch assembly
Batch should usually contain:
- one product-facing capability slice
- one evidence/replay/accountability slice
- one verification/supporting slice
- optional CI/workflow work only if it unblocks throughput

Breadth-first default:
- world/runtime
- supervision/accountability
- ops/replay/workflow

## 6. External research loop

Agents must learn from external sources before design/product slices when relevant.

Research sources are graded:
- A: standards/platform/research sources (WCAG, Apple HIG, Material Design, OpenTelemetry, NN/g)
- B: mature product/vendor docs (LangSmith, Langfuse, Phoenix, Gather, platform spatial UI docs)
- C: case libraries and visual references (Game UI Database, AI Town, screenshots)
- D: trends/listicles/social posts

Rules:
- at least one A source or two B sources are required before turning a design/architecture trend into a slice
- C/D sources can inspire patterns but cannot alone justify implementation
- every design brief must say what it rejects
- do not copy fashionable visuals; extract principles and map them to operator tasks and data contracts

Research brief fields:
- research question
- operator scenario
- project constraints
- source list and grades
- extracted principles
- rejected trends
- benchmark comparison
- proposed slices
- review gate result

Benchmark dimensions:
- operator outcome
- spatial fit
- evidence fit
- visual/typography quality
- observability fit
- implementation risk

## 7. Research domains for this project

### UI / typography / accessibility
Use for readable evidence, hierarchy, focus, keyboard, density.
Useful source families:
- WCAG 2.2
- Apple HIG typography/layout
- Material Design 3
- NN/g usability research
- curated design systems such as Linear/Vercel/Notion/Sentry only as references, not as visual copying

### Game UI / simulation UI
Use for glanceability, spatial HUD, attention signals, map overlays.
Useful references:
- colony sim / strategy UI principles
- Game UI Database
- RimWorld-like information layering
- AI Town / Gather-style spatial social office patterns

Do not import game mechanics like XP bars, fake productivity scores, leaderboards, or decorative animation.

### Spatial UI
Use for stable spatial anchors, readable overlays, comfort, not for Phase 1 3D/XR scope expansion.
References can include Apple/Meta/Microsoft/Android XR spatial layout guidance, translated into 2D office constraints.

### AI agent observability
Use for trace/session/span/evaluation mental models.
References can include OpenTelemetry GenAI conventions, LangSmith, Langfuse, Phoenix, Braintrust/OpenLLMetry.
Translate to local concepts:
- correlation_id as trace spine
- timeline / incidents / workflow / memory artifacts as spans/evidence
- replayability and provenance as primary UX

## 8. Anti-stagnation controls

### Product delta rule
Every batch must produce at least one Capability Delta Ledger entry.
If the after-state is only "more tests", "cleaner workflow", or "prettier UI", classify as maintenance.

### Maintenance cap
A batch may contain at most one workflow/CI/test-only slice unless master or the delivery chain is blocked.

### Product-facing ratio
Across any two consecutive batches, product-facing capability PRs should be at least 50%; target 2/3.
If not, next batch must be strategy-corrective and product-facing.

### No-op gate
Reject proposals that cannot answer:
- what new operator/system capability exists after this?
- what evidence/replay/accountability chain got stronger?
- why is this not a dashboard/demo?
- how is it tested?

### Drift alarm
Trigger corrective planning when:
- UI changes repeatedly add no evidence/replay capability
- refactors merge without operator capability delta
- states are shown without provenance
- many Linear issues close but no Notion capability moves
- Graphite PR count rises while product delta ledger stays flat

### Phase-stagnation diagnostic

When the user asks why the project is still in Phase 1 or progress feels slow, audit and report these separately:
- repo-defined phase truth: `README.md`, `specs/phase1-spec.md`, ADRs, and whether a Phase 2 spec/ADR/exit criteria exists
- merge truth: current master SHA, clean/dirty state, merged PRs, open PRs, stale/dirty worktrees
- strategy truth: whether Notion capability map and Capability Delta Ledger are live; if not, PR count cannot prove phase graduation
- validation throughput: CI trigger shape, serial jobs, duplicate push+pull_request runs, browser-smoke count, Playwright worker/concurrency, repeated full-gate reruns
- semantic blockers: lifecycle/evidence/replay/accountability correctness issues that must not be rushed because wrong truth is worse than no feature
- scope creep: Phase 1 slices repeatedly adding capabilities without a frozen exit gate

Use this conclusion pattern:
- Fact: what is verified in repo/GitHub/controller.
- Inference: why velocity is slow or phase is sticky.
- Corrective gate: define Phase 1 exit criteria, enable Notion map, close current open PRs, freeze new Phase 1 scope, move non-critical ideas to Phase 2.

Do not equate "many PRs merged" with phase progress unless a Capability Delta Ledger entry shows a product capability moved. Do not call workflow/CI/test-only work product progress unless it unblocks delivery or strengthens evidence/replay/accountability in a user-visible way.

## 9. Linear / Graphite / Notion integration

Notion:
- strategy/capability/research/decision map
- proposal/challenge/scorecard/batch decision/capability delta ledger

Linear:
- execution lifecycle only
- issue cannot enter selected/ready state without Notion decision/scorecard link when strategy work is involved

Graphite:
- implementation stack only after batch decision
- PRs link Notion decision, Linear issue, acceptance checks, evidence/replay impact

Slack:
- batch-start / PR-ready / merge-done / audit-correction broadcast only

## 10. Minimal viable rollout

If Notion is not configured yet:
1. maintain the council outputs in skill/controller text temporarily
2. do not pretend Notion sync happened
3. once `NOTION_API_KEY` is configured and pages/databases are shared with the integration, create the databases and migrate the active strategy map

First live rollout should create:
- MO Vision & Outcomes
- MO Capability Map
- MO Decisions
- MO Research & Evidence
- MO External References
- MO Capability Delta Ledger

Then use the council flow before selecting the next product batch.