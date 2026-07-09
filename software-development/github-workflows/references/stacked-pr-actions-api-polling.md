# Stacked PR Actions API polling notes

Use this during large stacked-PR cleanup when `gh` is unavailable or too noisy and GitHub MCP combined status does not expose check-run jobs.

## Why

GitHub's combined status endpoint may return `pending` with zero statuses for a pull request head even while GitHub Actions checks are running. That is not a merge gate. For this repo class, the real gate is the fresh `pull_request` workflow run for the current `head.sha`, with the expected job set:

- `test`
- `Browser smoke (preview, shard 1-of-2)`
- `Browser smoke (preview, shard 2-of-2)`
- `Browser smoke (dev, shard 1-of-2)`
- `Browser smoke (dev, shard 2-of-2)`

## Polling pattern

1. Confirm the PR's remote `head.sha` and `base.ref` after any force-push or base retarget.
2. Query Actions runs by exact head SHA:
   `GET /repos/{owner}/{repo}/actions/runs?head_sha=<sha>&per_page=20`
3. Filter runs to `event == "pull_request"`. Ignore `push` runs as merge gates.
4. For the newest pull_request run, query jobs:
   `GET /repos/{owner}/{repo}/actions/runs/{run_id}/jobs?per_page=100`
5. Merge only when the run is `completed/success` and every expected job completed successfully.
6. If polling from Python, use `python3 -u` or otherwise flush output for long waits; buffered stdout can hide useful progress until a command timeout.
7. Use an authenticated token when available, but never print it. Unauthenticated REST polling can hit rate limits during large cleanup runs.

## Minimal Python skeleton

```python
import json, os, time, urllib.request

base = "https://api.github.com/repos/OWNER/REPO"
sha = "CURRENT_HEAD_SHA"
token = os.environ.get("GITHUB_PAT_TOKEN")
headers = {"Accept": "application/vnd.github+json", "User-Agent": "hermes-agent"}
if token:
    headers["Authorization"] = "Bearer " + token

def get(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

for _ in range(40):
    runs = get(f"{base}/actions/runs?head_sha={sha}&per_page=20").get("workflow_runs", [])
    pr_runs = [r for r in runs if r["event"] == "pull_request"]
    if pr_runs:
        run = pr_runs[0]
        jobs = get(f"{base}/actions/runs/{run['id']}/jobs?per_page=100").get("jobs", [])
        for job in jobs:
            print(job["name"], job["status"], job["conclusion"], flush=True)
        if run["status"] == "completed":
            break
    time.sleep(30)
```

## Missing or stale PR run recovery

Sometimes a force-pushed restack produces a green `push` run for the exact head SHA but no `pull_request` run, even after base retargeting. Also, after a root stacked PR is squash-merged and children are retargeted from the old parent branch to the default branch, GitHub may keep showing the old exact-SHA `pull_request` run from the pre-retarget base. Do not reuse that stale base-context run as the merge gate.

Minimal safe recovery:

1. Confirm the PR head ref, exact SHA, and current base are correct.
2. Confirm whether the newest exact-head `pull_request` run was created after the force-push/base-retarget. If it predates the base-retarget or no `pull_request` run exists, treat it as stale/missing even if green.
3. In the restack worktree, create a tree-identical new commit, e.g. `git commit --amend --no-edit`.
4. Verify old and new tree IDs match with `git rev-parse '<old>^{tree}'` and `git rev-parse 'HEAD^{tree}'` before pushing.
5. Force-push with a lease from the old remote SHA to the same head ref, then wait for the new exact-head `pull_request` gate on the current base.

This is a CI trigger workaround, not a code change. Report the old/new commit SHAs and identical tree ID.

## Pitfalls

- Do not treat a green `push` run as the PR gate.
- Do not treat combined status `pending` with zero contexts as either failure or success; inspect Actions runs.
- Do not stop at the first successful job; browser smoke shards can start only after `test` completes and may run much longer.
- A single terminal polling call can time out while the exact-head `pull_request` run is still healthy and in progress. Treat that as an incomplete observation, not a CI failure: rerun the poller against the same head SHA/run, keep the previous run id in view, and continue until the run reaches `completed` with the full expected job set.
- GitHub can expose duplicate same-head-SHA `pull_request` workflow runs, including a cancelled placeholder/matrix run next to the real in-progress run. Do not fail the gate just because the first returned run is `cancelled` if another same-SHA PR run is active or non-cancelled. Rank runs by non-cancelled/active status, then newest id, and evaluate the expected job set on that selected run.
- After force-pushing, GitHub's pull request endpoint can lag behind the remote ref. If the PR still reports the old head SHA, verify `git ls-remote origin refs/heads/<head-ref>`, wait briefly, then re-read the PR before polling CI.
- After creating an additional late PR during closeout, refresh the poll target list before reporting status. A hard-coded PR list from before the late PR will silently omit its CI state.
- After merging any root PR, prior prepared child heads are stale until rebased onto the new default branch and revalidated.
- When embedding Python polling scripts in a `zsh -lc '...'` command, avoid single quotes inside the shell-quoted heredoc body (for example `r['id']` inside an f-string). Use double-quoted keys or assign `run_id = run.get("id")`; otherwise zsh can terminate the outer string and the script may query a bogus Actions jobs URL.
- If heredoc quoting keeps breaking a polling script (for example f-string key lookups become `NameError`, or escaped quotes inside f-string expressions become `SyntaxError`), stop retrying inline shell. Write the Python poller to a temporary file under the worktree (for example `.tmp/poll-ci.py`) and execute `python3 -u .tmp/poll-ci.py`; keep that file uncommitted or remove it before amending.
- In zsh, quote Git revspecs containing braces in shell commands, e.g. `git rev-parse "HEAD^{tree}"`; unquoted `HEAD^{tree}` can be treated as a glob and fail before the Git check runs.

