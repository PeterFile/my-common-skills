# Himalaya email CLI

Consolidated from the former `himalaya` skill. Use this reference when the communication-platform umbrella routes email work to the external Himalaya CLI.

## Purpose
Himalaya manages mailboxes from the terminal using IMAP, SMTP, Notmuch, or Sendmail backends. It is separate from the Hermes email gateway adapter: the gateway lets people email the agent; Himalaya lets the agent operate a mailbox.

## Prerequisites
- `himalaya --version`
- Config at `~/.config/himalaya/config.toml`
- IMAP/SMTP credentials configured through a password command, keyring, or other secure store.

## Install
```bash
curl -sSL https://raw.githubusercontent.com/pimalaya/himalaya/master/install.sh | PREFIX=~/.local sh
brew install himalaya
cargo install himalaya --locked
```

## Agent usage
- Use `--output json` for structured parsing.
- Prefer piped templates over `$EDITOR` flows.
- Use PTY only for the interactive account configuration wizard.
- Message IDs are relative to the current folder; re-list after folder changes.

## Common commands
```bash
himalaya folder list
himalaya envelope list --page 1 --page-size 20
himalaya envelope list --folder "Sent" --output json
himalaya message read 42
himalaya message export 42 --full
himalaya message move 42 "Archive"
himalaya message copy 42 "Important"
himalaya message delete 42
himalaya flag add 42 --flag seen
himalaya attachment download 42 --dir ~/Downloads
himalaya --account work envelope list
```

## Non-interactive send/reply patterns
```bash
cat <<'EOF' | himalaya template send
From: you@example.com
To: recipient@example.com
Subject: Test Message

Hello from Himalaya.
EOF
```

Reply:
```bash
himalaya template reply 42 | <safe template edit step> | himalaya template send
```

Forward:
```bash
himalaya template forward 42 | <safe template edit step> | himalaya template send
```

## Critical pitfall
For Gmail and other providers whose folder names differ from Himalaya's canonical folder names, configure `folder.aliases.*`. If save-to-Sent fails after SMTP delivery, a naive retry can duplicate-send the email.
