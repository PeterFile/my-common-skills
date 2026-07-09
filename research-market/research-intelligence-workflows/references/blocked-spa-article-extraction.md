# Blocked SPA/article extraction patterns

Use when a source page is Cloudflare/JS-blocked or normal extraction returns empty, but the user needs full article text plus figures.

## Pattern: source text via Jina Reader

- If `web_extract()` rejects or returns empty for a public article, try Jina Reader from a terminal HTTP client rather than `web_extract`, because some extractors falsely classify nested reader URLs as private/internal.
- Example:
  ```bash
  python3 - <<'PY'
  import urllib.request
  url='https://r.jina.ai/http://https://example.com/path/'
  req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
  with urllib.request.urlopen(req, timeout=120) as r:
      print(r.read().decode('utf-8','replace'))
  PY
  ```
- Treat the reader output as article text, but verify missing images/figures against original HTML or archived assets.

## Pattern: recover figures from Next.js/RSC pages

When Jina/plain Markdown omits figures:

1. Look for archive mirrors only as asset recovery, not as authoritative text if the original is available.
2. If Ghostarchive is available, download the WARC referenced by the replay element, then enumerate WARC records.
3. Extract both the main HTML response and any `?_rsc=` response for the page.
4. Search those payloads for image asset URLs, `altText`, titles, dimensions, code blocks, and captions.
5. Deduplicate Contentful/Image CDN URLs by base URL before resizing/query params.
6. Download the canonical desktop/light images locally and use `vision_analyze()` on local files for chart text.

## SVG pitfall

Some SVGs contain path-only text and embedded `data:` images. If ImageMagick fails with a "File name too long"/data URL error, on macOS use:

```bash
sips -s format png input.svg --out output.png
```

Then analyze the PNG locally.

## Reporting

- State the source chain: original URL, reader/cached text source, archive/WARC source for figures.
- Separate authoritative article claims from inferred figure interpretation.
- Include every figure's title, visible labels, flow/arrows, and role in the argument.
