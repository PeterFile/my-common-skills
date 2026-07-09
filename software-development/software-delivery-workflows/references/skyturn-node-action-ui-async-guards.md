# SkyTurn node action UI async guard hardening

Use this note when wiring selected-node composer actions such as repair, variant, and rollback in SkyTurn UI.

## Durable lesson

A selected-node action is not protected by comparing only `sessionId + nodeId` after an `await`. SkyTurn sessions can reuse node ids such as `node-1`, and a user can switch away and back to the same session/node while an older request is still pending. That old promise can then pass a scope-only guard and overwrite newer composer state.

## Correct guard shape

1. Build action availability from typed workflow projection/checkpoint state, not from generic text input or agent prose.
2. Before calling backend IPC, fail closed unless the action payload matches the current active `sessionId` and selected `nodeId`.
3. Maintain a monotonic action generation/request token:
   - Increment it on selected action scope changes (`sessionId:nodeId`), which also clears text/error/status/busy state.
   - Increment it again on every submit and capture that generation in the async closure.
   - After every `await`, before `applyWorkflowActionResult`, status/text/error writes, and `finally` busy cleanup, require both scope match and generation match.
4. Reset local action-chip state by `sessionId:nodeId`, not only by `selectedNode.id`.
5. Use user-visible fail-closed copy for stale payloads, for example: `Selected node action is stale. Reselect the node and try again.`

## Review/test pitfall

Source-string assertions are useful for contracts in this repo, but they are weak for async ordering bugs. When practical, add a behavior test with a mocked pending workflow promise:

- Submit action A on node X.
- Switch to another node/session, then back to X.
- Optionally start a newer same-node action.
- Resolve/reject the old promise.
- Assert old status/error/text does not appear and newer busy state is not cleared.

If a review-only agent flags this race, do not commit a scope-only guard. Add the generation token first, rerun parent validation, then rerun review-only.