---
name: communication-platform-workflows
description: Use when operating communication platforms from Hermes through CLIs, gateway tools, or platform APIs, including email mailboxes, X/Twitter, Yuanbao groups/DMs, posting, reading, searching, replying, mentions, and safe credential handling.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [communication, email, social-media, messaging, x, twitter, yuanbao, himalaya, cli]
    related_skills: [productivity-api-workflows]
---

# Communication Platform Workflows

## Overview
Use this umbrella for agent-operated communication channels: email mailboxes, social platforms, group chats, direct messages, and platform-specific command-line/API clients. The shared workflow is: identify the account/channel, verify read access cheaply, protect credentials, confirm intent before writes, then return a verifiable result.

## When to use
- Reading, searching, replying to, forwarding, or sending email through a mailbox CLI.
- Posting, searching, reading, liking, replying, quoting, DMing, or uploading media on X/Twitter.
- Yuanbao (元宝) group operations, @mentions, member lookup, group info, and DMs.
- Any communication platform where a Hermes gateway reply is itself the outbound message.

## Universal workflow
1. Resolve the platform, account, workspace/channel/group, and target identity.
2. Verify prerequisites without exposing secrets: version/help command, auth status, account list, group/member lookup, or a cheap read.
3. For write actions, confirm the target and exact action unless the user already provided unambiguous text and target.
4. Use structured output where available and preserve stable identifiers: message ID, post ID, URL, group code, user ID, or command output.
5. Never print credential files, tokens, auth headers, or inline secrets into the conversation.

## Platform subsections

### Himalaya email CLI
Use the external `himalaya` CLI for mailbox operations over IMAP/SMTP/Notmuch/Sendmail. This is separate from Hermes' email gateway adapter. Prefer `--output json` for reads and pipe templates for non-interactive sends/replies. For Gmail, configure folder aliases with `folder.aliases.sent = "[Gmail]/Sent Mail"`; the old singular `folder.alias` form can make SMTP delivery succeed while save-to-Sent fails, causing duplicate emails if retried. See `references/himalaya-cli.md`, `references/himalaya-configuration.md`, and `references/himalaya-message-composition.md`.

### X/Twitter via xurl
Use official `xurl` first for X API work. It supports shortcuts and raw v2 endpoints, with OAuth2 tokens stored under `~/.xurl`. Never read or print `~/.xurl`, never use verbose mode in agent sessions, and never pass inline secret flags. Check `xurl auth status`, then a cheap read like `xurl whoami` before writes. See `references/xurl-cli.md`. The older `x-cli`/xitter backend is preserved only as a fallback reference in `references/xurl-xitter.md`.

### Yuanbao gateway groups and DMs
In Yuanbao group chats, the assistant's normal final reply is the outbound group message. Include `@nickname` after resolving the exact nickname with the Yuanbao member lookup tool; do not claim the agent cannot mention users. Use the Yuanbao DM tool for private messages, not generic send_message. See `references/yuanbao-gateway.md`.

## Common pitfalls
1. Retrying a communication write after a partial-success error without checking whether the first send/post already happened.
2. Reading credential stores (`~/.xurl`, provider `.env` files, app-password files) into LLM context.
3. Using an interactive editor flow when a piped/template send would be deterministic.
4. Guessing social handles, group nicknames, or email recipients instead of resolving them.
5. Forgetting that a gateway final reply may already be the message being sent.

## Verification checklist
- [ ] Platform/account/channel identified.
- [ ] Prerequisites and auth checked without exposing secrets.
- [ ] Target identity resolved before mention/DM/write.
- [ ] Write actions have explicit target and content.
- [ ] Result includes an ID, URL, or command/tool status.
