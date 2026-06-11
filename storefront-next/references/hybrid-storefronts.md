# Hybrid Storefronts

> Source: https://github.com/SalesforceCommerceCloud/b2c-developer-tooling/tree/main/skills/storefront-next/skills/sfnext-hybrid-storefronts

**Mental model:** Split traffic between Storefront Next (MRT) and SFRA/SiteGenesis (B2C instance). CDN routes by URL pattern in production; Vite proxy simulates locally. Session bridging via shared cookies (`dwsid`, `cc-*`) ensures auth/cart continuity across both.

## Architecture

```
Customer Request → CDN/eCDN (Cloudflare) → routes by URL pattern
                         ↓                         ↓
               Storefront Next (MRT)    SFRA/SiteGenesis (B2C Instance)
                         ↕ Session Bridge (shared cookies) ↕
```

- **Production:** Cloudflare eCDN origin rules route between storefronts
- **Local dev:** Vite plugin (`hybridProxyPlugin`) proxies non-matching requests to SFCC sandbox

## Configuration

### Application Config (all environments)

```bash
# Enable hybrid mode
PUBLIC__app__hybrid__enabled=true

# Routes belonging to SFRA — <Link> clicks trigger full-page loads
PUBLIC__app__hybrid__legacyRoutes='["/cart", "/checkout", "/product/:id"]'
```

### Proxy Plugin Config (local dev only)

```bash
HYBRID_PROXY_ENABLED=true
SFCC_ORIGIN=https://zzrf-001.dx.commercecloud.salesforce.com

# Cloudflare expression format: paths matching → Storefront Next; not matching → SFCC
HYBRID_ROUTING_RULES='(http.request.uri.path matches "^/$" or http.request.uri.path matches "^/product.*" or http.request.uri.path matches "^/category.*" or http.request.uri.path matches "^/resource.*" or http.request.uri.path matches "^/action/.*")'

# Optional: locale for SFRA path transformation
HYBRID_PROXY_LOCALE=en-GB
```

## Client-Side Navigation Middleware

`legacy-routes.client.ts` intercepts client-side navigation to SFRA-owned routes:

1. User clicks `<Link to="/checkout">`
2. React Router begins client navigation
3. Middleware checks if path matches `legacyRoutes` pattern
4. If yes → forces full-page navigation (CDN/proxy routes to SFRA)
5. If no → continues normal client-side rendering

## Session Bridging

Both storefronts share cookies (`dwsid`, `cc-*`) on a common domain:

**Storefront Next → SFRA:**
- Shared `dwsid` cookie maintains session
- Full-page navigation triggered by legacy-routes middleware
- CDN routes request to SFCC origin

**SFRA → Storefront Next:**
- SFRA provides session credentials (dwsgst/dwsrst tokens)
- Storefront Next exchanges bridge token for SLAS tokens
- Normal SLAS cookie-based auth resumes

## Traffic Routing: Gradual Migration

1. **Phase 1** — Homepage, product, category on Storefront Next
2. **Phase 2** — Account and search
3. **Phase 3** — Cart and checkout
4. **Phase 4** — Full migration, remove SFRA

### Required Routing Rules (always Storefront Next)

| Pattern | Why |
|---------|-----|
| `^/resource.*` | React Router resource routes (data endpoints) |
| `^/action/.*` | React Router actions (form submissions) |

### Keep Rules in Sync

`HYBRID_ROUTING_RULES` (what SF Next owns) and `PUBLIC__app__hybrid__legacyRoutes` (what SFRA owns) are complementary. Any path not in routing rules that could be a `<Link>` target should be in `legacyRoutes`.

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Lost session crossing storefronts | Cookie domain mismatch | Ensure shared parent domain |
| Cart items disappear | Basket not synced | Verify session bridge cookies (`dwsid`, `cc-*`) |
| Redirect loops | Conflicting rules | Check eCDN rules and `legacyRoutes` consistency |
| 404 on SFRA pages (local dev) | Missing from routing rules | Add path to `HYBRID_ROUTING_RULES` |
| React Router 404 on legacy route | Missing from legacyRoutes | Add to `PUBLIC__app__hybrid__legacyRoutes` |

## Rules

- Cookie domains must match across both storefronts
- Update eCDN origin rules as pages migrate
- Maintain URL structure for SEO continuity
- `/resource/*` and `/action/*` must ALWAYS route to Storefront Next
