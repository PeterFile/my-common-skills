---
name: research-intelligence-workflows
description: "Use when gathering, monitoring, or synthesizing external information from arXiv, feeds, YouTube, market data, LLM wikis, or academic paper workflows."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [research, arxiv, feeds, youtube, market-data, papers]
    related_skills: []
---

# Research Intelligence Workflows

## Overview
Use this umbrella for finding, monitoring, extracting, and synthesizing external information. Prefer source-grounded outputs with URLs, timestamps, and extracted evidence.

## When to Use
- arXiv searches by keyword, author, category, or ID.
- Blog/RSS/Atom monitoring.
- YouTube transcript extraction and summaries.
- Polymarket or market-data queries.
- LLM Wiki style markdown knowledge bases.
- Academic or ML paper writing.

## Workflow
1. Define the question and inclusion criteria.
2. Search relevant sources and record URLs/IDs/dates.
3. Extract primary content, not only snippets.
4. Synthesize with citations and uncertainty.
5. For monitoring, store query/feed and last-seen state.

## Source Notes
- arXiv: capture title, authors, abstract, category, date, ID, PDF.
- Feeds: maintain read/seen state.
- YouTube: use transcripts and distinguish creator claims.
- Markets: record slug, price, liquidity, close date, timestamp.
- Papers: tie claims to experiments, figures, and related work.

## SPA / Static Docs Extraction
When a documentation site is a single-page app and page extraction fails or returns empty:
1. Fetch the HTML with a real User-Agent and handle gzip/encoding explicitly.
2. Inspect script/link assets for route tables or `DOCS_STRUCTURE`-style metadata.
3. Prefer original markdown/assets endpoints (for example `/assets/docs/<section>/<slug>.md`) over rendered HTML.
4. Record the discovered slug list and source URL for each page before translation/synthesis.
5. For large translation jobs, split files into stable batches, write outputs to disk, then verify file count, frontmatter/source fields, Markdown fence balance, and README/local links.

## Blocked Article + Figure Recovery
For Cloudflare/JS-blocked public articles where the user needs full text plus figures:
1. Try Jina Reader from a terminal HTTP client (`https://r.jina.ai/http://https://...`) when `web_extract()` is empty or falsely blocks nested reader URLs.
2. Verify figures separately; reader/Markdown output often drops images, code captions, and chart alt text.
3. For Next.js/RSC pages, inspect archived HTML/WARC payloads and `?_rsc=` responses for image URLs, `altText`, captions, and code blocks.
4. Download figure assets locally and run vision analysis on the files; for SVGs that fail ImageMagick due embedded data URLs, convert with macOS `sips`.
5. Report provenance explicitly: original page for article claims, reader/archive/WARC for recovered text/assets.

Detailed recipes:
- `references/blocked-spa-article-extraction.md`
- `references/openai-harness-engineering-extraction.md` for the OpenAI harness-engineering article pattern: use Jina Reader against the original `http://` URL when HTTPS is Cloudflare-blocked, recover diagrams separately, and label mirror/asset provenance precisely.

## Common Pitfalls
1. Summarizing snippets as full sources.
2. Omitting dates for volatile markets/news.
3. Losing provenance during synthesis.
4. Trusting SPA-rendered navigation without checking the underlying route/source asset list.

## Verification Checklist
- [ ] Primary sources extracted or blocker stated.
- [ ] URLs/IDs/timestamps captured.
- [ ] Output format matches request.
