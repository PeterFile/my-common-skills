# xurl X/Twitter CLI

Consolidated from the former `xurl` skill. Use this reference when the communication-platform umbrella routes work to X/Twitter via official X API tooling.

## Purpose
`xurl` is the X developer platform's official CLI. It supports shortcut commands and raw curl-style access to X API v2 endpoints. Commands return JSON.

Use it for posting, replying, quoting, deleting posts, searching, timelines, mentions, likes, reposts, bookmarks, follows, blocks, mutes, DMs, media uploads, and raw v2 endpoint access.

## Mandatory secret safety
- Never read, print, parse, summarize, upload, or send `~/.xurl` to LLM context.
- Never ask the user to paste credentials or tokens into chat.
- Never execute auth commands with inline secrets in agent sessions.
- Never use `--verbose` / `-v` in agent sessions; it can expose auth headers.
- Verify credentials only with `xurl auth status`.

Forbidden secret flags: `--bearer-token`, `--consumer-key`, `--consumer-secret`, `--access-token`, `--token-secret`, `--client-id`, `--client-secret`.

## Install
```bash
curl -fsSL https://raw.githubusercontent.com/xdevplatform/xurl/main/install.sh | bash
brew install --cask xdevplatform/tap/xurl
npm install -g @xdevplatform/xurl
go install github.com/xdevplatform/xurl@latest
```

## User-only setup
The user must do this outside the agent because it involves secrets:
```bash
xurl auth apps add my-app --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
xurl auth oauth2 --app my-app
xurl auth default my-app
xurl auth status
xurl whoami
```

If X returns `UsernameNotFound` or 403 on `/2/users/me`, the user can pass the handle explicitly:
```bash
xurl auth oauth2 --app my-app YOUR_USERNAME
```

## Quick reference
```bash
xurl post "Hello world!"
xurl reply POST_ID "Nice post!"
xurl quote POST_ID "My take"
xurl delete POST_ID
xurl read POST_ID
xurl search "QUERY" -n 10
xurl whoami
xurl user @handle
xurl timeline -n 20
xurl mentions -n 10
xurl like POST_ID
xurl unlike POST_ID
xurl repost POST_ID
xurl unrepost POST_ID
xurl bookmark POST_ID
xurl unbookmark POST_ID
xurl follow @handle
xurl unfollow @handle
xurl block @handle
xurl unblock @handle
xurl mute @handle
xurl unmute @handle
xurl dm @handle "message"
xurl dms -n 10
xurl media upload path/to/file.mp4
xurl media status --wait MEDIA_ID
```

## Raw API
```bash
xurl /2/users/me
xurl -X POST /2/tweets -d '{"text":"Hello world!"}'
xurl -X DELETE /2/tweets/1234567890
xurl https://api.x.com/2/users/me
```

## Agent workflow
1. Verify `xurl --help` and `xurl auth status`.
2. Parse auth status: the default app is marked with `▸`. If default has no OAuth2 token but another app does, tell the user to run `xurl auth default <app>`.
3. If auth is missing, stop and give user-only setup instructions.
4. Start with a cheap read (`xurl whoami`, `xurl user @handle`, or `xurl search ... -n 3`).
5. Confirm target and intent before writes.
6. Return IDs/URLs/status from JSON output.

## Troubleshooting
- Auth errors after OAuth: token saved to empty `default` app; rerun OAuth with `--app` and set default.
- `unauthorized_client`: app type is wrong in X dashboard; use web/automated app type.
- `client-forbidden` / `client-not-enrolled`: check developer plan/enrollment.
- `CreditsDepleted`: buy credits.
- Media processing failed on image: pass image category/media type, e.g. `--category tweet_image --media-type image/png`.
