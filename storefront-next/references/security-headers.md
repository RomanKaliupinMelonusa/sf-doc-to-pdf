# Security Response Headers

> Source: https://developer.salesforce.com/docs/commerce/pwa-kit-managed-runtime/guide/sfnext-security-headers.html

**Mental model:** Security headers ship from `@salesforce/storefront-next-runtime` package by default. Extend via `config.server.ts` by spreading `defaultCspDirectives` and appending origins. Never replace defaults wholesale.

## Default Headers

| Header | Default Value |
|--------|--------------|
| `Content-Security-Policy` | See directives below |
| `Strict-Transport-Security` | `max-age=15552000; includeSubDomains` (MRT only, suppressed locally) |
| `X-Frame-Options` | `SAMEORIGIN` |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` |

## CSP Directives

| Directive | Default |
|-----------|---------|
| `default-src` | `'self'` |
| `script-src` | `'self' https://challenges.cloudflare.com 'nonce-<per-request>'` |
| `style-src` | `'self' 'unsafe-inline'` (Tailwind requires it) |
| `img-src` | `'self' data: https://*.commercecloud.salesforce.com https://*.demandware.net` |
| `font-src` | `'self' data:` |
| `connect-src` | `'self' https://*.commercecloud.salesforce.com https://*.demandware.net https://challenges.cloudflare.com` |
| `frame-src` | `https://challenges.cloudflare.com` |
| `frame-ancestors` | `'self'` |
| `form-action` | `'self'` |
| `base-uri` | `'self'` |
| `object-src` | `'none'` |

## Extending CSP for Integrations

```typescript
// config.server.ts
import { defaultCspDirectives } from '@salesforce/storefront-next-runtime/security';

export default defineConfig({
  app: {
    security: {
      headers: {
        csp: {
          directives: {
            ...defaultCspDirectives,
            'script-src': [...defaultCspDirectives['script-src']!, 'https://cdn.example.com'],
            'connect-src': [...defaultCspDirectives['connect-src']!, 'https://api.example.com'],
          },
        },
      },
    },
  },
});
```

## Env Var Override

```bash
PUBLIC__app__security__headers__csp__reportOnly=true    # report-only mode
PUBLIC__app__security__headers__hsts=false               # disable HSTS
# Full directives map (replaces ALL defaults):
PUBLIC__app__security__headers__csp__directives='{"default-src":["self"],...}'
```

## Rules

- Always spread `defaultCspDirectives` when adding origins — each set directive replaces default entirely
- Don't use `reportOnly: true` in production (provides no protection)
- For social login providers, extend `connect-src` with provider origins
- Env var override replaces the ENTIRE directives map — prefer `config.server.ts` edits
- Headers apply to rendered pages only, not health checks, SCAPI proxy, or static assets
