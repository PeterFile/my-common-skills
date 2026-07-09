# Himalaya message composition with MML

Consolidated support file from the former `himalaya` skill.

Himalaya composes messages with headers plus a body, optionally using MML (MIME Meta Language) for multipart bodies and attachments.

## Basic message
```text
From: sender@example.com
To: recipient@example.com
Subject: Hello World

This is the message body.
```

## Common headers
- `From`
- `To`
- `Cc`
- `Bcc`
- `Subject`
- `Reply-To`
- `In-Reply-To`

Address examples:
```text
To: user@example.com
To: John Doe <john@example.com>
To: "John Doe" <john@example.com>
To: user1@example.com, user2@example.com, "Jane" <jane@example.com>
```

## Multipart alternative
```text
From: alice@localhost
To: bob@localhost
Subject: Multipart Example

<#multipart type=alternative>
This is the plain text version.
<#part type=text/html>
<html><body><h1>This is the HTML version</h1></body></html>
<#/multipart>
```

## Attachments
```text
<#part filename=/path/to/document.pdf><#/part>
<#part filename=/path/to/file.pdf name=report.pdf><#/part>
```

## Inline image
```text
<#multipart type=related>
<#part type=text/html>
<html><body><img src="cid:image1"></body></html>
<#part disposition=inline id=image1 filename=/path/to/image.png><#/part>
<#/multipart>
```

## Mixed content
```text
<#multipart type=mixed>
<#part type=text/plain>
Please find the attached files.
<#part filename=/path/to/file1.pdf><#/part>
<#part filename=/path/to/file2.zip><#/part>
<#/multipart>
```

## CLI composition
Interactive editor:
```bash
himalaya message write
himalaya message reply 42 --all
himalaya message forward 42
```

Agent-preferred stdin send:
```bash
cat message.txt | himalaya template send
```

Header-prefill:
```bash
himalaya message write -H "To:recipient@example.com" -H "Subject:Quick Message" "Message body here"
```

Use `himalaya message export --full` to inspect raw MIME.
