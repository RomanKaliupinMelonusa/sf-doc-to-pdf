# Shopper Context

> Source: https://developer.salesforce.com/docs/commerce/pwa-kit-managed-runtime/guide/sfnext-shopper-context.html

**Mental model:** Session-level qualifiers (source codes, customer groups, custom/assignment qualifiers) that influence pricing, promotions, and sorting without changing individual API calls. Managed via middleware + cookies + React hook. Disabled by default.

## Feature Flag

```bash
PUBLIC__app__features__shopperContext__enabled=true
```

When off, middleware exits early — no SCAPI calls.

## How It Works

Two entry paths for qualifiers:
1. **URL query params** — middleware extracts on every request (e.g., `?src=spring-sale&deviceType=mobile`)
2. **React hook** — `useShopperContext()` updates from UI interactions

Both merge new qualifiers into cookie state → PUT full merged context to SCAPI (full replace) → write cookies.

## Supported Qualifiers

| API Field | URL Parameter | Notes |
|-----------|---------------|-------|
| `sourceCode` | `src` | Campaign/attribution |
| `couponCodes` | `couponCodes` | Comma-separated |
| `customQualifiers` | `deviceType` | e.g., `?deviceType=mobile` |
| `assignmentQualifiers` | `store` | e.g., `?store=boston` |

`effectiveDateTime`, `customerGroupIds`, `clientIp`, `geoLocation` not enabled by default. Add to `SHOPPER_CONTEXT_SEARCH_PARAMS` constant to enable.

## Cookies

| Cookie | Default Expiry | Purpose |
|--------|---------------|---------|
| `storefront-next-context` | 6 hours | All qualifiers except source code |
| `dwsourcecode` | 30 days | Source code qualifier |

## Client Hook

```typescript
import { useShopperContext } from '@/hooks/use-shopper-context';

function StoreSelector() {
  const { updateQualifiers, isLoading, error, success } = useShopperContext();
  const handleStoreChange = (storeId: string) => {
    updateQualifiers({ store: storeId });
  };
}
```

## Customization

Add qualifiers by editing `SHOPPER_CONTEXT_SEARCH_PARAMS` in `src/lib/shopper-context/constants.ts`. After adding, both URL params and hook support it automatically.

## Gotchas

- API ties context to USID — no notification when backend clears context
- Cookies cleared on logout or auth failure
- New values overwrite existing keys; unmentioned keys preserved (merge, not replace)
- `geoLocation` is a structured object — needs additional handling
