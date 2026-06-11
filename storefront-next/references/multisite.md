# Multisite Configuration

> Source: https://developer.salesforce.com/docs/commerce/pwa-kit-managed-runtime/guide/sfnext-multi-site.html

**Mental model:** Single deployment serves multiple B2C Commerce sites and locales. URL pattern (prefix/query params) is configurable. Middleware resolves site + locale from URL, cookies, or headers (configurable priority). Works for single-site too — middleware always runs.

## Site Definition

```typescript
// config.server.ts → app.commerce
commerce: {
  sites: [
    {
      id: 'RefArchGlobal',        // Must match Business Manager site ID
      defaultLocale: 'en-GB',
      defaultCurrency: 'GBP',
      supportedLocales: [
        { id: 'en-GB', preferredCurrency: 'GBP' },
        { id: 'fr-FR', preferredCurrency: 'EUR' },
      ],
      supportedCurrencies: ['EUR', 'GBP'],
    },
  ],
}
```

`app.defaultSiteId` determines fallback on first visit.

## URL Pattern

```typescript
// config.server.ts → app.url
url: {
  prefix: '/:siteId/:localeId',           // Path segments prepended
  search: '?lng=:localeId',               // Query params appended
  excludeRoutes: ['/resource/**', '/action/**'],  // Skip prefixing
}
```

Both `prefix` and `search` are optional. Use `:siteId` and `:localeId` placeholders.

**Protected:** `url.prefix` and `url.excludeRoutes` cannot be overridden via env vars (require rebuild).

## Alias Maps (clean URLs)

```typescript
app: {
  siteAliasMap: { RefArchGlobal: 'global', RefArch: 'us' },
  localeAliasMap: { 'en-US': 'us', 'en-GB': 'gb' },
}
```

Result: `/global/gb/product/123` instead of `/RefArchGlobal/en-GB/product/123`

## Detection Config

```typescript
siteDetectionConfig: {
  order: ['path', 'querystring', 'cookie', 'header'],
  lookupFromPathIndex: 0,    // First path segment
  lookupQuerystring: 'site',
  lookupCookie: 'site_id',
  lookupHeader: 'X-Site-Id',
  caches: ['cookie'],
}
localeDetectionConfig: {
  order: ['path', 'querystring', 'cookie', 'header'],
  lookupFromPathIndex: 1,    // Second path segment
  lookupQuerystring: 'lng',  // Must be 'lng' to match i18next
  lookupCookie: 'lng',
  lookupHeader: 'Accept-Language',
  caches: ['cookie'],
}
```

## Site-Context Cookies

```typescript
app: {
  siteContext: {
    currencyCookieName: 'currency',
    cookieOptions: { httpOnly: true, secure: true, sameSite: 'lax', maxAge: 604800 },
  },
}
```

## Default Behavior

- Homepage (`/`): resolves from `site_id` cookie (no prefix)
- Subpages: include site/locale prefix (shareable, deterministic)
- `Link` component and `buildUrlFromContext` skip prefixing for `/` by default

## Rules

- Keep `i18n.supportedLngs` in sync with all `commerce.sites[].supportedLocales[].id` values
- Locale query param key MUST be `lng` (matches i18next cookie key)
- Each locale must have corresponding translation directory under `src/locales/`
- Detection `order` and URL config must stay in sync (path index matches prefix segment position)
