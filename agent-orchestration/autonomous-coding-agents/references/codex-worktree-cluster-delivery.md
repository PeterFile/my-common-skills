# Codex worktree cluster delivery pattern

Use this when the user asks for a larger autonomous coding push with multiple Codex agents, stacked branches, dense testing, and external status reporting.

## Core pattern

1. Verify the live repo first: `git rev-parse --show-toplevel`, current branch, `git status --short --branch`, recent commits, remotes, and `git worktree list --porcelain`.
2. Check communication/control channels before launching work: messaging targets, issue tracker/API, Codex availability, GitHub/PR path. Treat missing CLIs as setup state; use available APIs/MCP when authenticated.
3. Have planning agents or short analysis lanes propose scoreable goals before code agents write. Do not let a small `delegate_task` concurrency limit define the whole swarm size: use Hermes delegates for planning/review synthesis, and use separate Codex CLI processes in separate worktrees for the larger implementation cluster. For a user explicitly asking for a larger cluster, do not stop at three lanes just because delegation concurrency is three; use the delegates to design/review, then launch as many isolated Codex worktrees as the repo/backlog/test capacity can responsibly support.
4. Turn the planning discussion into scoreable route goals before implementation. Each goal must be objectively gradable and should include:
   - route / lane slug
   - why it advances the current vision or milestone
   - acceptance checklist with observable pass/fail items
   - likely files and explicit non-goals
   - fastest validation command and expected signal
   - PR split boundary and size budget
   - score rubric with pass/fail evidence
   - first-feedback timebox, normally shorter than the full CI path
   - Slack/Linear/status sink for progress updates
5. Write durable goals only into existing current direction/spec/README docs when they change product/API/storage/UI semantics. Do not create markdown progress logs; transient progress belongs in Slack/Linear/controller systems. If the user warns about “文档地狱”, default to updating the existing authoritative direction doc rather than creating new files. If a new markdown file seems useful, first decide whether it will remain authoritative after this run; otherwise do not create it.
6. Create a run namespace and do not reuse stale worktrees:
   - branch: `stack/<run>/<NN>-<slug>`
   - worktree: `.worktrees/<repo>-<run>-<NN>-<slug>`
   - create a small root branch for durable checklist/spec changes when useful, then branch implementation lanes from it.
7. Install dependencies in fresh worktrees before launching agents if the repo needs local node_modules/venv state. Use the project’s known package manager and shared cache/store if available.
8. Launch one Codex process per isolated worktree. Give each prompt: exact worktree, branch, product boundaries, allowed files, acceptance checklist, validation command, size limits, and “do not commit/push/PR/post status”.
9. Capture each Codex final response to a lane-specific output file (`codex exec -o <file>`), then verify in the parent. Child claims are not proof.
10. Parent must inspect each lane’s diff, file count, net LOC, untracked files, test output, and product boundary before considering it ready.
11. Score lanes before PR:
    - product fit
    - scope/size
    - contract/docs integrity
    - tests/verification
    - documentation durability
    - delivery risk

## Useful Codex invocation

For non-interactive worktree agents:

```bash
codex exec -C <worktree> -s workspace-write -o /tmp/<lane>.out < /tmp/<lane>.prompt.txt
```

On codex-cli 0.136.0, `codex exec -a never` may be rejected even though help lists approval flags. Prefer the invocation above unless the installed version is verified to accept the approval option.

## Scoreable goal template

Use this compact shape before launching implementation lanes:

```text
Lane: <NN-slug>
Why now: <route / product risk it advances>
Base -> head: <stack base> -> <branch>
Allowed scope: <paths and explicit non-goals>
Checklist:
- [ ] <observable product/code behavior>
- [ ] <contract/security/UI boundary>
- [ ] <test or proof>
Fast validation: <single cheapest useful command>
Score (100): product fit <n>, scope <n>, tests <n>, risk <n>, docs/status <n>
PR cap: <= <files> files / <= <net LOC> net LOC; split if exceeded
Status sink: <Slack/Linear/controller target>
```

## Process handling

- Start bounded Codex tasks as background processes with completion notification.
- Poll or wait, but do not trust a running process forever.
- Background completion messages can arrive late and out of order after the parent has already reviewed, committed, pushed, or opened PRs. Before acting on a completion notice, compare its command/worktree/lane to the current lifecycle state. If the lane already has a parent-verified commit/PR, treat the notice as stale telemetry and do not rerun or reopen work.
- For stale failure notices from an obsolete invocation pattern, record the durable command fix once, then ignore repeated lane-specific failures from the same bad command. Do not let one batch of delayed failures overwrite later successful parent verification.
- If an agent summary conflicts with parent review, tests, or final PR diff, the parent-verified state wins. Mention the conflict only if it changes risk or review focus.
- If a process runs far beyond lane budget, shows no CPU, and repeats diff/log output without test progress, kill it and perform parent-side validation on the worktree.
- If a Codex process exits via SIGTERM/timebox and the expected `-o` summary file is missing, do not treat the lane as complete or failed by narrative alone. Inspect the dirty worktree: if the diff is small and coherent, parent may take over by reviewing the diff, removing obvious agent artifacts or nonsense selectors, running the narrowest tests that prove the new branches actually executed, then the lane gate. If validation is green, commit the parent-reviewed diff; if not, leave it dirty/not-ready with the exact failing command.
- If using `git stash` during restack on zsh/macOS shells, quote stash refs such as `git stash apply 'stash@{0}'` and `git stash drop 'stash@{0}'`; unquoted refs can fail or no-op because brace syntax is shell-sensitive.
- If a full UI test lane flakes once on a timeout, rerun the exact failed test first. If it passes, retry the full fast lane once; if it fails again, mark the lane not-ready rather than rationalizing it.
- If a Codex worker reports an unrelated failure inside a huge focused-files UI gate, do not accept that narrative blindly. Parent-run the exact newly added/changed test first, then rerun the named allegedly failing old test by exact `-t` pattern. If both pass, score the lane as targeted-proof green but broad-gate timeboxed; keep the broader gate caveat explicit instead of blocking the whole stack on stale/contaminated worker telemetry.
- When a preferred child-agent lane stalls for provider capacity, emits empty output, or loops without useful diff progress, do not keep waiting forever and do not hand-edit the lane in an architect-only session. Inspect the real worktree diff and the child CLI logs, kill the stale process after preserving any artifact, then re-delegate the same bounded prompt to an available coding agent while keeping the original path/scope constraints. Record the fallback in the lane report as degraded agent routing, not as a product blocker.
- In pnpm monorepo worktrees, Codex `workspace-write` may fail `pnpm install` when the configured store is outside the writable worktree (for example a shared `/Volumes/.../pnpm-store`). Do not let the agent loop on install. Parent should either pre-install dependencies in the worktree with an explicitly writable `--store-dir`, or instruct the worker to use a worktree-local store and remove the generated store before PR. Treat missing `node_modules` as an environment blocker until parent-run validation succeeds.
- If the full focused-files UI gate times out because it includes a huge umbrella test file (for example `App.test.tsx`), run the exact new/changed test by name plus any smaller component test file to distinguish product failure from suite runtime. Passing targeted proof is useful scoring evidence, but it is not a replacement for the required lane gate; keep the lane `not-ready` until the full gate, an approved narrower gate, or a split removes the timeout.
- If a delayed/background Codex result arrives after parent closeout, reopen the lane state instead of ignoring it. Do not trust stdout snippets or expected summary files: inspect the real worktree (`git status`, `git diff --shortstat`, `git diff --name-only`, `git diff --check`), then run the exact new/changed tests. If the worker only implemented a lower component layer, parent-fix the missing integration only when the root cause is small and obvious; otherwise keep the lane as dirty draft and report the blocker.
- For React apps that skip lazy/heavy renderers in jsdom, App-level tests may not exercise a child component prop even when the child test passes. Validate both paths: a child/component targeted test for the real renderer behavior and an App/shell targeted test for the fallback or integration path. If the App test stays red because the shell never builds/passes the prop, fix the App integration; if the shell intentionally cannot render the child, move the assertion to the component test and keep the App test focused on the visible fallback contract.
- If a child agent reports a validation blocker such as local browser/permission/sandbox failure, verify the actual parent-run log before accepting the explanation. A later parent run may expose a real product/test assertion failure hidden behind the child narrative. Mark the lane not-ready when parent validation fails, even if the child summary claims the failure is environmental.
- For test-only security/label-firewall lanes, do not add assertions for behavior the current product intentionally still exposes (for example raw refs inside a detailed evidence/debug surface). First identify the exact public surface that is supposed to be bounded, narrow assertions to that surface, and leave broader product-boundary changes for a separate implementation lane.
- For UI density lanes that move detail content behind native `<details>`, remember that closed details content remains in the DOM but is not visible. Tests should assert `not.toBeVisible()` for the closed state, then click the summary before visibility/content assertions; `not.toBeInTheDocument()` is the wrong assertion for this pattern.
- If a lane runs beyond budget but is still producing useful diff/log output, kill it only after recording the state, then take over in the parent: inspect the diff, fix obvious boundary violations, and rerun the narrowest test that proves the fix. Do not promote a killed lane without a parent-side green validation.
- Some Hermes installations clamp `process(action="wait")` to `0s`; if waits return immediately, use a bounded `sleep` plus `process(action="poll")` loop instead of assuming the child finished.
- Parent-side validation timeouts can leave orphaned `pnpm`/`vitest`/test-runner children when a shell or Python wrapper is killed. After any timeout, check live processes for the lane worktree path and terminate leftovers before running another validation, otherwise later results may be contaminated.
- Dense iteration means short score/test loops, not waiting forever for the biggest agent. Timebox each lane’s first feedback, then choose: commit verified small diff, split oversized diff, or leave the lane dirty/not-ready with the exact failing command. Never open a PR for a lane whose parent-run validation catches a regression.
- Before starting long parent-side validation, commit, push, or PR creation late in a dense swarm, check whether you have enough interaction/tool-call budget to poll completion and finish the lifecycle. Do not launch background validations you cannot observe. If budget is tight, either run a smaller foreground gate that can complete now or write an operational handoff that names exact worktrees, branches, running process IDs, untracked files, validation commands already started, and the next safe action.
- Do not get stuck circling one evidence/live-state lane after the user asks for forward progress. If the lane is killed, oversized, or ambiguous, extract the smallest coherent validated slice into a fresh split worktree/branch, open only that small PR, and leave the original dirty worktree explicitly `not-ready` with size/blocker recorded. Report the distinction in Slack/Linear so status consumers do not confuse the split PR with completion of the original lane.
- When a late Codex completion notice arrives for a lane previously marked not-ready, treat it as telemetry until proven. Inspect the original worktree. If it is still dirty and over the PR size target, do not commit/push it directly. Split the diff into coherent patches, create fresh stacked worktrees from the correct current stack base, apply each patch with `git apply --index`, commit each slice separately, install dependencies if the fresh worktree lacks them, run focused validation per slice, and only then push/create PRs. Leave the original scratch lane dirty/not-ready unless you explicitly clean it after confirming the split PRs cover the intended work.

## PR size gates

Default target:
- <= 350 net LOC
- <= 8 files

Hard cap:
- <= 500 net LOC
- <= 12 files

If a lane exceeds the cap, split it. Do not merge unrelated backend, UI, docs, and test sweep changes into one PR.

When the repo has an advisory PR-size script, run it on the committed candidate diff before PR creation, not only on the dirty worktree. Some scripts intentionally compare `<base>..HEAD` and will print an empty diff for uncommitted work; while the lane is dirty, use `git diff --shortstat` / `git diff --name-only` as the provisional size evidence, then rerun the advisory after the candidate commit. If the advisory lane itself exceeds the target cap, compress, amend, or split before opening the PR; a tool that enforces small PRs must not become the first oversized PR. Keep such scripts advisory-only unless the project explicitly asks for a hard CI gate; do not pretend they score product fit, contract correctness, or reviewer judgment.

For CI-feedback lanes, preserve existing required check names and job semantics unless the user explicitly accepts required-check churn. If a worker proposes splitting a monolithic job in a way that renames a required check, narrow the first PR to a safe improvement such as stale-run concurrency/cancellation, then leave job-DAG refactors for a separate reviewed change.

## Continuation after budget/context loss

When resuming a cluster run, verify instead of trusting handoff text. If a tool-call/context limit forces a final response before the run is complete, make the handoff operational rather than narrative: separate verified PRs, parent-validated-but-uncommitted lanes, dirty/not-ready lanes, still-running processes, exact validation commands/results, status-channel updates already sent, and the next safe action for each lane. Do not collapse dirty lanes into "done" just because an agent summary exists.

1. Inspect the main repo and every named worktree: branch, upstream, dirty/untracked files, and recent commits.
2. For dirty implementation lanes, review the diff and untracked files before staging; add generated/new source files only when they are required by the lane.
3. Rerun the lane's fastest validation in the parent session immediately before commit/PR.
4. Commit each lane separately with its own scope; do not squash multiple lanes just because they were generated in one swarm.
5. Push branches and create stacked PRs with the correct base branch. If the GitHub CLI is unavailable, use git for push and GitHub MCP/API for PR creation/status checks.
   - If a stack-root PR is merged before its direct child PRs, those direct children must not keep targeting the old stack-root branch. Retarget them to `master`/the default branch before merge. If the available GitHub toolset cannot edit a PR base, rebase the affected child branch onto the new default-branch head, force-push with lease, close the wrong-base PR with an audit comment, and recreate it against the correct base. Then rebase/force-push downstream stacked branches onto the rewritten parent branch and rerun the cheapest post-restack validation. Do not merge a PR whose base branch is only an already-merged stack root unless the intent is explicitly to update that stack branch, not the default branch.
6. Treat status API results of `pending` with zero contexts as "no checks returned", not a pass. Report that explicitly and do not claim CI success.
7. Close the loop in issue tracker/chat with PR URLs, validation commands, known caveats, and what remains unmerged. If no first-class issue-tracker tool is exposed but a scoped API credential is already present in the environment, use the provider API directly with least privilege and do not print secrets.
8. For lanes rebased/restacked after initial validation, rerun the cheapest relevant parent validation after the rebase before PR. A green pre-rebase test is not evidence for the rebased commit.
9. If a dirty or ready lane overlaps files with another open PR from the same run, restack it onto the overlapping PR rather than leaving it as a parallel child of the root branch. This keeps the PR diff honest and avoids hidden merge conflicts; rerun validation after the restack.
   - For UI lanes touching broad files such as `apps/web/src/App.tsx`, `apps/web/src/App.test.tsx`, or `apps/web/src/styles.css`, explicitly inspect open PR changed files before PR creation. First filter to the same run/same semantic stack when possible; unauthenticated GitHub REST file-by-file scans over many open PRs can hit rate limits before finishing. If the open-PR list is too large, save/filter it locally, use authenticated API/MCP, then check likely UI stack PRs with `get_pull_request_files` or equivalent.
   - After restacking, prefer a post-rebase focused-file gate plus typecheck when a full lane gate already passed before rebase and would cost several minutes; record both pre-restack and post-restack validation separately in the PR/status update.
   - On a clean committed branch, do not assume `verify:quick`'s default `git diff --check` covers the PR diff; run `git diff --check <pr-base>..HEAD --` explicitly before the lane test/typecheck command, especially after restacking.
   - Exception: do not cross-restack independent semantic stacks when doing so would drag another base PR into the diff and create a misleading mega-PR. Roll back the restack, keep the lane on its semantic base, report the file-overlap risk explicitly, and resolve integration conflicts later.
10. Treat test-runner output with all tests skipped as a failed verification attempt, not a pass. For Vitest/Jest `-t` filters, confirm at least one intended test actually ran; if the pattern misses, inspect test names and rerun with the exact name.
11. Leave known-failing lanes dirty/not-ready rather than polishing them into PRs. Record the exact blocker command and failure, then report the required product/test-boundary decision.

## Status reporting

Status updates should include run id, lane, branch/worktree, PR URL, validation command/result, score, blocker/risk, and next action. Do not report a lane as complete until the parent has verified diff and tests. When GitHub status APIs return `pending` with zero contexts/checks, say "no checks returned" rather than "CI passed".