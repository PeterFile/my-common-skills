# OpenAI Harness Engineering Article Extraction Notes

Use this when a public OpenAI article is Cloudflare/JS gated and the user asks for complete article analysis including figures.

## Working Pattern Observed

- Direct `web_extract()` may falsely report a private/internal network blocker.
- Direct browser navigation may stop at Cloudflare challenge.
- Plain Python `urllib` to `https://openai.com/...` may return 403.
- Jina Reader with the original **HTTP** URL worked where HTTPS did not:

```text
https://r.jina.ai/http://http://openai.com/index/harness-engineering/
```

- Jina Reader with `Accept: application/json` can expose metadata including OpenGraph image URLs, but its `content` may omit inline figures.
- OpenAI sitemap endpoints can be reachable and useful for lastmod/alternate URL discovery, e.g. `https://openai.com/sitemap.xml` then category sitemap entries.
- Search snippets for exact diagram titles can confirm that figures are part of the original OpenAI page, even when reader output drops images.

## Figure Recovery Pattern

1. Extract full text through the reader endpoint.
2. Query exact phrases from the article and diagram titles, for example:
   - `"Codex drives the app with Chrome DevTools MCP"`
   - `"Giving Codex a full observability stack"`
   - `"Layered domain architecture with explicit cross-cutting boundaries"`
3. Prefer mirrors that preserve original image assets or raw GitHub copies of secondary writeups.
4. Download recovered images locally and run vision analysis; clearly label provenance as recovered/mirrored if the asset did not come directly from the original page.
5. Separately fetch the OpenGraph/SEO image from metadata if needed; it is usually a cover image, not the article diagrams.

## Provenance Language

When reporting results, separate:

- **Original article text**: from reader extraction of the OpenAI URL.
- **Original-page figure existence**: confirmed by search snippets/exact titles or page metadata.
- **Figure pixels**: recovered from mirror/raw secondary source, not necessarily OpenAI's original asset URL.

Do not claim direct original asset retrieval unless the image URL was actually from OpenAI/Contentful and was downloaded successfully.
