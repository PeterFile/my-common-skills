# Obsidian filesystem vault workflow

Consolidated from the former `obsidian` skill. Use this reference from `productivity-api-workflows` when operating an Obsidian vault through filesystem tools.

## Vault path
Resolve a concrete absolute vault path before calling file tools.

Preferred convention: `OBSIDIAN_VAULT_PATH`, for example from `${HERMES_HOME:-~/.hermes}/.env`. If unset, use `~/Documents/Obsidian Vault`.

File tools do not expand shell variables. Do not pass paths containing `$OBSIDIAN_VAULT_PATH` to `read_file`, `write_file`, `patch`, or `search_files`. Resolve first, especially because vault paths may contain spaces.

If the vault path is unknown, `terminal` is acceptable for resolving `OBSIDIAN_VAULT_PATH` or checking whether the fallback exists. Once known, use file tools.

## Read notes
Use `read_file` with the absolute note path.

## List notes
Use `search_files` with `target: "files"` and the resolved vault path.

Examples:
- All markdown notes: pattern `*.md` under the vault.
- A subfolder: search under that absolute subfolder path.

## Search
Use `search_files`, not shell grep/find/ls.

- Filenames: `target: "files"`.
- Contents: `target: "content"`, regex pattern, and `file_glob: "*.md"`.

## Create notes
Use `write_file` with full markdown content and an absolute path.

## Append or edit notes
Prefer native file tools:
1. Read the note.
2. Use `patch` for anchored edits when stable context exists.
3. Use `write_file` when a whole-note rewrite is clearer.

For a simple append with no stable context, `terminal` can be acceptable, but avoid shell quoting risks when possible.

## Wikilinks
Use Obsidian `[[Note Name]]` links when creating related notes.
