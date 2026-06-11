# Basket Management

> Source: https://developer.salesforce.com/docs/commerce/pwa-kit-managed-runtime/guide/sfnext-basket-management.html

**Mental model:** Cookie snapshot (basketId + counts) persists across requests via middleware. Full basket hydration is lazy by default — triggered client-side only when `useBasket()` is called. Server actions mutate basket via SCAPI, then call `updateBasketResource()` to sync the middleware state.

## Architecture Flow

1. Middleware reads `__sfdc_basket` cookie → parses snapshot into context
2. Root loader passes snapshot to `BasketProvider` (no full hydration)
3. Client components call `useBasket()` → triggers lazy fetch if snapshot has basketId
4. After loaders/actions, middleware writes updated cookie snapshot

## Basket Middleware

```typescript
// root.tsx
import createBasketMiddleware from '@/middlewares/basket.server';
export const middleware = [/* ...other */, createBasketMiddleware()];
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `mode` | `'lazy'` | `'lazy'` or `'eager'` hydration |
| `cookieName` | `'__sfdc_basket'` | Cookie name |
| `cookieDurationRegistered` | ECOM default | TTL for registered shoppers |
| `cookieDurationGuest` | ECOM default | TTL for guest shoppers |
| `currency` | — | Currency for basket creation |
| `calculateBasketSnapshot` | — | Add custom fields to cookie |

### Server-Side Helpers (loaders/actions)

```typescript
import {
  getBasket,
  getBasketSnapshot,
  ensureBasketId,
  updateBasketResource,
  destroyBasket
} from '@/middlewares/basket.server';

// In loader:
const snapshot = getBasketSnapshot(context);
const basketResource = await getBasket(context, { ensureBasket: true });

// In action:
const basketId = await ensureBasketId(context);
// ...SCAPI mutation...
updateBasketResource(context, (current) => ({
  ...current,
  basketId: basketId ?? current?.basketId,
}));
```

## Client-Side: BasketProvider + Hooks

```typescript
// Root provides snapshot only (no eager creation)
<BasketProvider snapshot={basketSnapshot}>

// Read basket (triggers lazy hydration)
import { useBasket } from '@/providers/basket';
const basket = useBasket();

// Update after mutation
import { useBasketUpdater, useBasketReset } from '@/providers/basket';
const setBasket = useBasketUpdater();
const resetBasket = useBasketReset();

setBasket(updatedBasketData);  // After add/remove item
resetBasket();                 // After order completion
```

## Provider State Shape

- `snapshot`: Cookie-safe summary (basketId, totalItemCount, uniqueProductCount)
- `current`: Full basket payload (when hydrated)
- `hydrated`: Whether hydration attempted
- `error`: Hydration error info

## Rules

- Root loader passes only `basketSnapshot` — never eagerly creates basket
- Use `useBasketUpdater()` after mutations — updates aren't auto-inferred from loaders due to lazy mode
- Cookie TTL should match your ECOM instance settings
- `destroyBasket(context)` clears basket state (use after checkout)

## Gotchas

- `useBasket()` triggers fetch only when snapshot has basketId and no full basket in context
- In lazy mode, full basket data isn't available during SSR — design components to handle `null`
