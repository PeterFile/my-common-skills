# Documentation State Audit Pattern

Use this when asked to audit whether project docs match the real code and to update docs when they do not.

## Pattern
1. Verify live state first: repo root, branch, status, default branch, remotes, recent commits, and existing worktrees. Do not rely on session-start snapshots.
2. Read the authoritative direction/spec docs and package/test scripts before delegating. Identify which docs are current authority and which are historical archives.
3. Use subagents only for bounded, read-only lanes. Broad “whole project” audits can time out and produce no usable output. Prefer focused prompts such as:
   - docs/current-direction + README/spec consistency
   - backend/API/storage implementation vs contract
   - frontend/API-client/UI route consumption vs contract
4. Treat child summaries as leads. Parent must re-read exact code/doc lines for every claimed mismatch before editing.
5. When docs are stale, make a docs-only branch/worktree. Patch current authoritative docs, not historical archive text, unless the archive itself is actively misleading despite an archive notice.
6. For active ADRs with stale route catalogs, prefer pointing them at living route catalogs (`README`, API contract) instead of trying to keep an exhaustive list in the ADR.
7. For milestone or roadmap docs, distinguish:
   - already implemented/hardening guardrails
   - remaining milestone work
   - non-goals/control-plane boundaries
   - target/landing-plan text that should stay as forward direction even when some pieces are now implemented
8. When an active design doc mixes goals, current state, and implementation plan, update only the explicit current-state/code-fact sections. Add a short reading rule if needed: requirements/landing-plan/acceptance sections are product direction, while “current state” sections are code facts. Do not delete forward direction just because code caught up with part of it.
9. When summarizing a project after recent PRs, build a capability map from live `main`, recent merged PRs, and implementation/test paths. Explicitly call out documentation debt separately from product gaps; stale statements like “not yet implemented” can become false after a merged hardening slice.
10. For systems with node/detail/evidence UI already in place, avoid inventing new panels or dashboards just to expose proof. First audit the existing detail surfaces and state whether they already carry the required evidence, then plan only the missing source-of-truth or product-path work.
11. For historical scaffold or early verification docs that are stale but still useful, add a clear status banner pointing to current authoritative docs/code paths instead of rewriting the whole archive as if it were current.
12. Validate docs-only changes with the repo’s narrow docs lane and whitespace/conflict checks. For whole-repo audits or capability summaries, run the relevant full gates when feasible. If a forced Turbo run fails with exit 137 under high concurrency, rerun with low concurrency (for example `turbo run test typecheck lint --force --concurrency=1`) before treating it as a code failure.
13. If creating a PR, include evidence checked, docs-only scope, and exact validation commands. Do not merge unless explicitly asked.
14. When a design doc's old “implementation order” has become a stale checklist, replace it with a current capability map: “landed/main path”, “partial/needs convergence”, “next priorities”, and “future modification points”. Keep the existing product goals and acceptance text intact unless it is factually wrong.
15. Treat root-level `/goal` prompts, implementation prompts, and milestone goal files as high-risk drift sources. If the milestone has landed or evolved, add an archive/status banner or retarget them to the current capability map so future agents do not execute stale requirements as active work.
16. For runtime/support docs, verify both implementation and contract types. Drift can be split: the implementation may already support a behavior while docs or public types still describe an older narrower model, such as auth readiness sources, watchdog behavior, or support-level boundaries.
17. For user-facing summaries after a documentation audit, respect concise-answer requests: group findings by severity and current authority, report only the top actionable drifts, and avoid a doc-by-doc inventory unless the user asked for exhaustive output.
18. After opening a docs-only PR, verify the PR head SHA and CI/check rollup for that exact head. Report PR-open, CI-green, and merge-ready as separate facts; do not imply merge completion.
19. After adding archive/status banners, run a targeted stale-phrase grep for phrases that caused the drift (for example old click behavior, obsolete “current issue” headings, unimplemented prompts, or outdated support claims). If the grep still returns matches in historical files, either rewrite the sentence as explicitly historical or ensure the local surrounding text cannot be misread as current behavior.

## Pitfalls
- Do not treat stale historical plan docs as current roadmap when current-direction/spec docs explicitly supersede them.
- Do not trust a timed-out subagent as evidence.
- Do not let documentation updates accidentally imply new runtime/control-plane behavior.
- Do not say a route is consumed by the UI unless you have checked both the API client helper and the UI call site/gating.
- Do not leave the exact stale wording in place just because a file has a historical banner; future search-based agents may still lift the bad sentence out of context.
- Do not add a new evidence panel/dashboard during a docs-state audit just because the docs mention evidence. First inspect existing node details, modals, composer scopes, and delivery surfaces.
