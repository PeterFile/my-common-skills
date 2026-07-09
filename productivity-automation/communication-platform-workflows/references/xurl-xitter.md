# xitter / x-cli fallback reference

Consolidated from the older xitter skill that used the third-party `x-cli` terminal client. Prefer official `xurl` for new X/Twitter work; use this only when a user explicitly has `x-cli` configured or needs historical workflow details.

## Install
```bash
uv tool install git+https://github.com/Infatoshi/x-cli.git
uv tool upgrade x-cli
x-cli --help
```

## Credentials
`x-cli` expects five X Developer values, usually in `~/.config/x-cli/.env`:
- `X_API_KEY`
- `X_API_SECRET`
- `X_BEARER_TOKEN`
- `X_ACCESS_TOKEN`
- `X_ACCESS_TOKEN_SECRET`

Do not ask the user to paste these into chat. They must create or link the file themselves.

If the user already maintains X credentials in `~/.hermes/.env`, they can run outside the agent:
```bash
mkdir -p ~/.config/x-cli
ln -sf ~/.hermes/.env ~/.config/x-cli/.env
```

## Verification
```bash
x-cli user get openai
x-cli tweet search "from:NousResearch" --max 3
x-cli me mentions --max 5
```

## Common commands
```bash
x-cli tweet post "hello world"
x-cli tweet get https://x.com/user/status/1234567890
x-cli tweet delete 1234567890
x-cli tweet reply 1234567890 "nice post"
x-cli tweet quote 1234567890 "worth reading"
x-cli tweet search "AI agents" --max 20
x-cli tweet metrics 1234567890
x-cli user get openai
x-cli user timeline openai --max 10
x-cli user followers openai --max 50
x-cli user following openai --max 50
x-cli me mentions --max 20
x-cli me bookmarks --max 20
x-cli me bookmark 1234567890
x-cli me unbookmark 1234567890
x-cli like 1234567890
x-cli retweet 1234567890
```

Use `-j` for machine-readable output. Write actions still require explicit confirmation.

## Pitfalls
- X API access is often paid or quota-limited.
- `403 oauth1-permissions`: regenerate the access token after enabling read/write permissions.
- Programmatic replies are often restricted; quote posts can be more reliable.
- Credential drift occurs if linked `.env` files no longer point at current secrets.
