# SEO and Metadata

> Source: https://developer.salesforce.com/docs/commerce/pwa-kit-managed-runtime/guide/sfnext-seo-metadata.html

**Mental model:** Three SEO systems: (1) hreflang + canonical generated centrally in root.tsx via `buildSeoMetaDescriptors()`; (2) per-page `<SeoMeta>` component for title/description/OG/Twitter; (3) structured data (JSON-LD) per route. All rendered server-side for crawlers.

## Hreflang Alternate Links

Generated in `src/utils/seo.ts`, returned from root `meta` export. Automatic from `site.supportedLocales`.

Output per page:
- `<link rel="canonical" href="...">`
- `<link rel="alternate" hreflang="en-GB" href="...">` per locale
- `<link rel="alternate" hreflang="x-default" href="...">` (default locale)

Self-referencing tag included (Google requires it). Locale aliases respected. Query params follow canonical normalization.

## Canonical URLs

Built in `src/utils/canonical-url.ts`. Three normalizations:
1. **Allowlisted query params only** — everything else stripped
2. **Sorted alphabetically** — deterministic
3. **Trailing slash removed** (non-root paths)

### Default Allowlist (`CONTENT_PARAMS`)

| Param | Purpose |
|-------|---------|
| `q` | Search query |
| `offset` | Pagination |
| `sort` | Sort order |
| `refine` | Filter refinements |
| `pid` | Product variant ID |

To add a param: add to `CONTENT_PARAMS` set in `src/utils/canonical-url.ts`. Don't add params that don't change page content (analytics, modals, UI prefs).

## SeoMeta Component

```tsx
import { SeoMeta } from '@/components/seo-meta';

<SeoMeta
  title="Classic Jacket"
  description="A premium leather jacket."
  openGraph={{ type: 'product', url: '...', image: '...' }}
/>
// Renders: <title>Classic Jacket | Storefront Next: Market Street</title>
```

### Props

| Prop | Type | Description |
|------|------|-------------|
| `title` | string | Page title (suffixed with `| {siteName}` by default) |
| `rawTitle` | boolean | Render title without suffix |
| `description` | string | Meta description + OG/Twitter description |
| `noIndex` | boolean | Adds `<meta name="robots" content="noindex">` |
| `siteName` | string | Override site name |
| `openGraph` | object | `type`, `url`, `image` |
| `twitter` | object | `cardType`, `image` |

### Title Modes

| Mode | Props | Output |
|------|-------|--------|
| Suffixed (default) | `title="My Page"` | `My Page | My Store` |
| Raw | `title="Custom" rawTitle` | `Custom` |

When `openGraph` provided without `twitter`, Twitter Card tags auto-derived from OG values.

## Rules

- Never manually add hreflang tags in route components — use centralized root-level generation
- Always throw 404 Response for missing resources (not return 200 with error) — SEO depends on correct status codes
- Use `SeoMeta` in every route that should be indexed
- `noIndex` on account pages, cart, checkout, search with no results
- Canonical + hreflang are NOT rendered by SeoMeta — they're root-level only
- React hoists `<title>` and `<meta>` to `<head>` automatically from any component position
