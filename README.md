# my-common-skills

Personal common skills collection. Each skill lives in a same-named folder with `SKILL.md` as the entry point. Supporting materials may appear in `references`, `examples`, or `assets` subfolders.

## Where skills live

### Antigravity

Project scope:
- `<workspace-root>/.agent/skills/<skill-folder>/`

Global scope:
- `~/.gemini/antigravity/skills/<skill-folder>/`

### Codex

Project scope:
- `$CWD/.codex/skills`
- `$CWD/../.codex/skills`
- `$REPO_ROOT/.codex/skills`

Global scope:
- `$CODEX_HOME/skills`

### Claude

Project scope:
- `.claude/skills/`

Global scope:
- `~/.claude/skills/`

### Gemini CLI

Project scope:
- `.gemini/skills/`

Global scope:
- `~/.gemini/skills/`

## Skills introduction source

```
https://code.claude.com/docs/en/skills
```

## Skills

| Name | Description | Directory |
| --- | --- | --- |
| brand-guidelines | Applies Anthropic's official brand colors and typography to any sort of artifact that may benefit from having Anthropic's look-and-feel. Use it when brand colors or style guidelines, visual formatting, or company design standards apply. | `brand-guidelines/` |
| canvas-design | Create beautiful visual art in .png and .pdf documents using design philosophy. You should use this skill when the user asks to create a poster, piece of art, design, or other static piece. Create original visual designs, never copying existing artists' work to avoid copyright violations. | `canvas-design/` |
| commit-assistant | Help create git commits and PRs with properly formatted messages and release notes following CockroachDB conventions. Use when committing changes or creating pull requests. | `commit-assistant/` |
| docs-write | Write documentation following Metabase's conversational, clear, and user-focused style. Use when creating or editing documentation files (markdown, MDX, etc.). | `docs-write/` |
| frontend-design | Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, artifacts, posters, or applications (examples include websites, landing pages, dashboards, React components, HTML/CSS layouts, or when styling/beautifying any web UI). Generates creative, polished code and UI design that avoids generic AI aesthetics. | `frontend-design/` |
| kiro-specs | Spec-driven workflow for Kiro: create or update requirements (EARS), design docs, and implementation task lists, and execute tasks. Use when working with .kiro/specs/* or when asked to draft/iterate feature specs, design documents, or task plans. Triggered by "kiro" or references to .kiro/specs/ directory. | `kiro-specs/` |
| market-sizing-analysis | This skill should be used when the user asks to "calculate TAM", "determine SAM", "estimate SOM", "size the market", "calculate market opportunity", "what's the total addressable market", or requests market sizing analysis for a startup or business opportunity. | `market-sizing-analysis/` |
| typescript-write | Write TypeScript and JavaScript code following Metabase coding standards and best practices. Use when developing or refactoring TypeScript/JavaScript code. | `typescript-write/` |
