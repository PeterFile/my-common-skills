# Yuanbao gateway groups and DMs

Consolidated from the former `yuanbao` skill. Use this reference when the communication-platform umbrella routes work to Yuanbao (元宝) group chats or private messages.

## Critical gateway behavior
In a Yuanbao group chat, the assistant's normal text reply is the message sent to the group. You do not need a separate send-message tool for group replies. If the reply contains `@nickname`, the gateway converts it into a real mention.

Do not tell the user the agent cannot send messages or @mention users. Resolve the exact nickname and write the message naturally.

## Tools by purpose
- `yb_query_group_info`: group name, owner, member count.
- `yb_query_group_members`: find a user, list bots, list all members, and get mentionable nickname.
- `yb_send_dm`: send private/direct messages, optionally with media.

## @mention workflow
1. Extract `group_code` from the current chat ID, e.g. `group:328306697` -> `328306697`.
2. Query members with `action="find"`, the target name, and `mention=true`.
3. Use the exact returned nickname in the final reply: `@nickname message`.

Rules:
- Query first; do not guess nicknames.
- Use a space before the @mention when it appears after other text.
- Keep group replies concise. Do not explain the mention mechanics unless asked.

## DM workflow
Use the Yuanbao DM tool, not generic `send_message`.

Parameters:
- `group_code`: from the current group chat ID.
- `name`: target display name, unless `user_id` is already known.
- `message`: outbound text.
- Optional media files for images/documents.

If multiple users match, ask the user to clarify.

## Query members
Supported actions:
- `find`: partial/case-insensitive search.
- `list_bots`: Yuanbao AI assistants and bots.
- `list_all`: all members.

## Notes
Groups are called 派 (Pai) in Yuanbao. Member roles include `user`, `yuanbao_ai`, and `bot`.
