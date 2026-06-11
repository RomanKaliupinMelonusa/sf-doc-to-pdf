# Content Caching

> Source: https://developer.salesforce.com/docs/commerce/pwa-kit-managed-runtime/guide/sfnext-caching-content.html

**Mental model:** Multi-tier caching: Browser → eCDN (Cloudflare) → MRT (metadata) → B2C Commerce → SCAPI response cache. Static content is immutable at edge (>99% hit ratio). HTML documents are NOT cached (personalization). SCAPI caching is per-unique-URL (including full query string).

## Tiers

| Layer | What's Cached | Cache Type |
|-------|--------------|------------|
| Browser | Static assets (JS bundles, images) | Immutable, long-lived |
| eCDN (Cloudflare) | Static content | Edge, globally distributed |
| MRT | Site/page metadata | Application-level |
| SCAPI | API response data | Per-unique-request-URL |

## Rules

- HTML documents are never cached (supports personalization)
- Only request necessary SCAPI expansions — `availability` expansion has short TTL, drastically reduces cache hit rate
- If no `expand` parameter specified, ALL expansions are selected (worse for caching)
- Each unique query string = separate SCAPI cache entry
- Short-TTL fields mixed with long-TTL data pull entire response to shorter schedule
- Fetch short-TTL data (inventory, real-time pricing) as separate non-critical deferred loader calls

## Reference

See [Server-Side Web-Tier Caching](https://developer.salesforce.com/docs/commerce/commerce-api/guide/server-side-web-tier-caching.html) for SCAPI caching details.
