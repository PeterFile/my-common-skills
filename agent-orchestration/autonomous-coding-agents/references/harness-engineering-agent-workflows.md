# Harness Engineering Lessons for Coding-Agent Workflows

Source pattern from the OpenAI article `Harness engineering: leveraging Codex in an agent-first world` and this session's analysis. Use this as a compact reference when improving Codex/Antigravity/Hermes delivery loops.

## Core Shift

Do not optimize only for "more agents". Optimize the harness so agents can see, verify, and correct the system themselves.

The useful abstraction is:

```text
Humans steer. Agents execute. The harness supplies legibility, constraints, and feedback loops.
```

## Practical Upgrades

1. **Application legibility for UI lanes**
   - Per worktree, launch a real app instance.
   - Clear console and capture before evidence.
   - Drive the intended UI path through browser/devtools automation.
   - Capture after evidence plus console/runtime events.
   - Apply the fix, restart, and re-run the identical path until clean.
   - Require evidence artifacts, not only a child-agent summary.

2. **Observability legibility for runtime lanes**
   - Give each worktree isolated logs/metrics/traces where practical.
   - Start simple: per-worktree structured logs and query scripts are better than no observability.
   - Mature path: Vector fan-out to log/metric/trace stores with agent-queryable APIs (LogQL/PromQL/TraceQL or local equivalents).
   - Make performance/reliability prompts executable: e.g. startup time, slow spans, failed journeys.

3. **Repository knowledge as system of record**
   - Keep `AGENTS.md` short: table of contents plus hard rules, not an encyclopedia.
   - Put durable architecture, product, reliability, security, quality, and execution-plan knowledge in repo-local docs.
   - Chat/Slack/Google Docs decisions that agents cannot read should be promoted into repo-local artifacts when durable.
   - Add CI/lint checks for broken links, stale docs, and missing cross-links when docs become operational inputs.

4. **Mechanical architecture and taste constraints**
   - Prefer custom lint/structural tests over prose rules for recurring agent mistakes.
   - Good constraints: import/layer direction, boundary parsing, structured logging fields, schema/type naming, file-size limits, no ad-hoc duplicate helpers.
   - Write lint errors as remediation prompts for agents.

5. **Continuous garbage collection**
   - Agents replicate existing patterns, including bad ones.
   - Run recurring small cleanup lanes for stale docs, duplicated helpers, architecture drift, flaky tests, slow checks, and quality score updates.
   - Keep cleanup PRs small enough for fast review/merge; do not accumulate a weekly/manual "AI slop" cleanup pile.

## Cautions

- Do not copy the "zero manually-written code" constraint as dogma. It was an experimental constraint; the transferable lesson is harness design.
- Do not relax merge gates just because agent throughput is high. Lightweight gates are safe only after app legibility, rollback, observability, and cleanup loops exist.
- A child agent saying it reviewed itself is not proof. Parent/controller still verifies diff and reruns targeted checks.

## Lane Prompt Additions

For UI work, add:

```text
Required evidence: before screenshot/DOM snapshot, after screenshot/DOM snapshot, console/runtime error summary, exact route and interaction path, and the validation command/output used after restart.
```

For runtime/performance work, add:

```text
Required evidence: per-worktree log/metric/trace query or local structured-log query showing before/after behavior for the named workload.
```

For architecture work, add:

```text
If the rule is durable and recurring, prefer a lint/structural test with agent-readable remediation text over another prose instruction.
```
