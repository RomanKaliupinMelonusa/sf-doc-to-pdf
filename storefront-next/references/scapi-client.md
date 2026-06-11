# SCAPI Client

> Source: https://developer.salesforce.com/docs/commerce/pwa-kit-managed-runtime/guide/sfnext-api-integration.html

**Mental model:** Type-safe SCAPI client at `@salesforce/storefront-next-runtime/scapi`. Built on openapi-fetch (near-zero overhead). Wraps all Shopper APIs with semantic names, auto-injected `organizationId`/`siteId`, and stateless auth helpers. Auth is stateless — you manage token storage.

## Creating Clients

```typescript
import { createCommerceApiClients } from '@salesforce/storefront-next-runtime/scapi';

const clients = createCommerceApiClients({
  baseUrl: 'https://shortcode.api.commercecloud.salesforce.com',
  organizationId: 'f_ecom_xxx',
  siteId: 'RefArch',
  clientId: 'your-slas-client-id',
  redirectUri: 'https://yoursite.com/callback',
  locale: 'en-US',                              // optional
  clientSecret: process.env.COMMERCE_API_SLAS_SECRET, // optional, enables private SLAS
});
```

- No `clientSecret` → public SLAS with PKCE
- With `clientSecret` → private SLAS (server-side only, enables passwordless login)

## Authentication (stateless)

```typescript
// Guest
const tokens = await clients.auth.loginAsGuest();

// Registered
const tokens = await clients.auth.loginWithCredentials({ username, password });

// Refresh
const newTokens = await clients.auth.refreshToken({ refreshToken });

// Logout
await clients.auth.logout({ accessToken, refreshToken });

// Social login
const { url, codeVerifier } = await clients.auth.social.getAuthorizationUrl({ hint: 'google' });
const tokens = await clients.auth.social.exchangeCode({ code, codeVerifier, redirectUri });
```

### Adding Token to Requests

```typescript
import { SLAS_AUTH_ENDPOINTS } from '@salesforce/storefront-next-runtime/scapi';

clients.use({
  onRequest({ request }) {
    const url = new URL(request.url);
    if (SLAS_AUTH_ENDPOINTS.some(path => url.pathname.includes(path))) return request;
    request.headers.set('Authorization', `Bearer ${accessToken}`);
    return request;
  },
});
```

## Fetching Data

```typescript
// Product
const { data: product } = await clients.shopperProducts.getProduct({
  params: { path: { id: 'product-123' }, query: { expand: ['availability', 'prices', 'variations', 'images'] } },
});

// Search
const { data } = await clients.shopperSearch.productSearch({
  params: { query: { q: 'shoes', limit: 24, offset: 0, sort: 'best-matches' } },
});

// Category
const { data } = await clients.shopperProducts.getCategory({
  params: { path: { id: 'mens-clothing' }, query: { levels: 2 } },
});
```

## Mutations

```typescript
// Add to basket
const { data } = await clients.shopperBasketsV2.addItemToBasket({
  params: { path: { basketId: 'basket-123' } },
  body: [{ productId: 'product-456', quantity: 2 }],
});
```

## Available Clients

`shopperProducts`, `shopperSearch`, `shopperBasketsV2`, `shopperCustomers`, `shopperOrders`, `shopperLogin`, `shopperPromotions`, `shopperContext`, `shopperStores`, `shopperExperience`, `shopperAvailability`, `shopperGiftCertificates`, `shopperSeo`, `shopperConsents`, `auth`

## TypeScript Types

```typescript
import type { ShopperProducts, ShopperSearch } from '@salesforce/storefront-next-runtime/scapi';
type Product = ShopperProducts.schemas['Product'];
type SearchParams = ShopperSearch.operations['productSearch']['parameters']['query'];
```

## Error Handling

```typescript
import { ApiError } from '@salesforce/storefront-next-runtime/scapi';
// Properties: status, statusText, body, rawBody, headers, url, method
```

## Middleware

```typescript
clients.use({ onRequest({ request }) { ... }, onResponse({ response }) { ... } });
clients.shopperProducts.use(specificMiddleware); // per-client
```

## Gotchas

- Custom SCAPI endpoints NOT supported by this client — use native `fetch`
- Auth helpers are stateless: they don't store tokens. You manage storage (cookies/session).
- All responses return `{ data, response }` — use `response` for headers/etag
