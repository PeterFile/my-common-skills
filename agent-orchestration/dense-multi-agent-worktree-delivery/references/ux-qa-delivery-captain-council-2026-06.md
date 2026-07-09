# UX/QA/Delivery Captain Council Pattern (2026-06)

Use this reference when a user asks for a dense worktree/Codex cluster plan rather than immediate implementation, especially when UX, QA, PR stack boundaries, Slack/Linear updates, and documentation discipline are all part of the deliverable.

## Pattern

1. Treat the request as **batch planning mode** unless the user explicitly asks to launch agents.
2. Still perform live preflight before giving the plan:
   - repo path / realpath
   - current branch and head
   - `git status --short --branch`
   - worktree inventory size and detached/stale risk
   - open GitHub PR list
   - current route/direction docs if present
   - available fast validation and PR-size commands
   - Slack/Linear availability when those status sinks are part of done
3. Produce a council-style plan with clear roles:
   - UX captain: user-visible flow, hot UI files, visual smoke expectations
   - QA captain: Layer-A gates, browser/regression smoke, failure triage
   - Delivery captain: stack topology, PR size cap, status sinks, closeout truth
4. Prefer **more than three implementation lanes** when the repo is clean and PR backlog is low; start around six write-enabled Codex lanes plus read-only review/audit lanes, then scale by evidence instead of a fixed cap.
5. Assign each lane a branch/worktree slug, goal, owner/hot files, allowed files, forbidden files, fastest Layer-A gate, and PR split trigger.
6. Separate independent PRs from true stacks:
   - independent product lanes target default branch
   - dependent contract/client/projection lanes target their parent branch
   - keep stacks shallow and verify diff against intended base before PR creation
7. Build the cadence into the plan:
   - T+0 launch/status table
   - T+12 first changed-path poll
   - T+18 kill/re-prompt scope-drifting lanes
   - T+20 Layer-A validation and re-score
   - T+30 Slack/Linear/controller update
   - repeat every ~30 minutes while work is active
8. Make documentation discipline explicit:
   - no temporary markdown progress logs
   - status/progress/blockers go to Slack, Linear, controller/runtime state, or GitHub comments
   - durable docs update only for API/storage/runtime/UI semantics, route/focus changes, or persistent operating policy

## Output shape

A good final response has:

- verified facts from preflight
- selected mode and dynamic concurrency decision
- lane table with PR stack boundaries and hot-file ownership
- scoring rubric and hard-fail gates
- fast feedback cadence
- Slack/Linear update points
- documentation discipline
- exact external updates performed, if any
- explicit statement whether repo files were changed

## Pitfalls

- Do not let a planning-only council request silently become implementation.
- Do not call Slack or Linear merge truth; they are status sinks only.
- Do not create new markdown status files for transient lane progress.
- Do not use a flat “3 agents” default when the user asked for a dense cluster and live preflight shows safe capacity.
- Do not launch write-heavy agents before checking required status sink availability when the requested deliverable includes Slack/Linear updates.
