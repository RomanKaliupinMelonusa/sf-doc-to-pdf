# Extensions

> Source: https://github.com/SalesforceCommerceCloud/storefront-next-template/blob/main/src/extensions/README.md

**Mental model:** Extensions are modular feature add-ons in `src/extensions/`. Each is self-contained with its own components, routes, hooks, locales, and config. Integration with core app uses comment markers. Extensions register via `config.json` and target the app via `target-config.json`. For ISVs/partners — NOT for template customization.

## Structure

```
src/extensions/
  config.json                    # Extension registry
  my-extension/
    index.ts
    target-config.json           # UI targets, context providers, action hooks
    config.ts                    # Client-side config defaults
    components/
    routes/                      # Auto-processed as new routes
    hooks/
    locales/<locale>/translations.json
```

## UI Targets (Components)

Insert components into target points marked with `<UITarget targetId="...">`:

```json
// target-config.json
{
  "components": [{
    "targetId": "header.before.cart",
    "path": "extensions/store-locator/components/header/store-locator-badge.tsx",
    "order": 0
  }]
}
```

Multiple components targeting same `targetId` render in ascending `order`.

## Context Providers

```json
{ "contextProviders": [{ "path": "extensions/store-locator/providers/store-locator.tsx", "order": 0 }] }
```

Inserted at application root (`root.tsx`).

## Routes

Files under `src/extensions/<name>/routes/` are automatically processed as new routes.

## Integration Markers

Code changes to core app are marked:
- Single line: `/** @sfdc-extension-line SFDC_EXT_STORE_LOCATOR */`
- Block: `{/* @sfdc-extension-block-start SFDC_EXT_STORE_LOCATOR */}` ... `{/* @sfdc-extension-block-end */}`
- Entire file: `/** @sfdc-extension-file SFDC_EXT_STORE_LOCATOR */`

## Extension Configuration (client-side)

```typescript
// src/extensions/loqate-address-verification/config.ts
export default { apiKey: '', cacheTTL: 900000 };
```

Namespaced by camelCase of folder: `config.app.extension.loqateAddressVerification`

Access:
```typescript
// Client: useConfig().app.extension?.loqateAddressVerification?.apiKey
// Server: getConfig().app.extension?.loqateAddressVerification?.apiKey
```

Merchant override: `PUBLIC__app__extension__loqateAddressVerification__apiKey=123456`

**Rules for config.ts:** Plain object (no `as const`), JSON-serializable values only, don't import core config, folder name must be letters/digits/hyphens starting with letter.

## Extension i18n

Translations auto-namespaced as `extMyExtension` (PascalCase of folder):
```typescript
const { t } = useTranslation('extMyExtension');
```

## Action Hooks

Server-side hooks at checkout flow points:

```json
// target-config.json
{
  "actionHooks": [{
    "hookId": "sfcc.checkout.fraud.afterSubmitContactInfo",
    "handler": "extensions/my-extension/hooks/fraud-check.ts",
    "order": 0
  }]
}
```

### Handler Pattern

```typescript
import type { ActionHookContext } from '@/targets/action-hook.server';
import { ActionHookError } from '@/targets/action-hook.server';

export default async function handler(context: ActionHookContext) {
  const { data, actionContext } = context;
  if (shouldBlock) throw new ActionHookError('Message', hookId, 'fieldName');
  return context; // pass through or modify data
}
```

### Hook Classification

| Type | Behavior on unexpected error |
|------|-----|
| **Blocking** (`beforePlace`, `beforePlaceOrder`) | Action fails |
| **Non-blocking** (all others) | Error logged, action continues |

`ActionHookError` always aborts (both types). Distinction only affects unexpected errors.

### Available Hook IDs

| hookId | Action | Blocking |
|--------|--------|----------|
| `sfcc.checkout.fraud.afterSubmitContactInfo` | submit-contact-info | No |
| `sfcc.checkout.addressVerification.afterSubmitShippingAddress` | submit-shipping-address | No |
| `sfcc.checkout.shipping.afterMethodsFetch` | submit-shipping-address | No |
| `sfcc.checkout.shipping.afterMethodSelect` | submit-shipping-options | No |
| `sfcc.checkout.payments.afterSubmitPayment` | submit-payment | No |
| `sfcc.checkout.fraud.beforePlace` | place-order | Yes |
| `sfcc.checkout.payments.beforePlaceOrder` | place-order | Yes |
| `sfcc.checkout.payments.afterPlaceOrder` | place-order | No |

### Constraints

- 5-second timeout per handler
- Handlers run in series (waterfall), ordered by `order`
- Non-blocking: failing handler skipped, next gets last successful context
- Blocking: any failure aborts entire waterfall
- Build-time optimized via Vite plugin (`virtual:action-hooks`) — no handlers = no bundle impact

## config.json Schema

```json
{
  "SFDC_EXT_PRODUCT_REVIEW": {
    "name": "Product Review",
    "description": "Product review allows users to see and create reviews.",
    "installationInstructions": "instructions/install-product-review.mdc",
    "uninstallationInstructions": "instructions/uninstall-product-review.mdc",
    "folder": "product-review"
  }
}
```

## Generate Install/Uninstall Instructions

```bash
npx @salesforce/storefront-next-dev create-instructions \
  -d /path/to/project \
  -c /path/to/src/extensions/config.json \
  -e SFDC_EXT_STORE_LOCATOR \
  -f /path/to/src/extensions/your-extension
```
