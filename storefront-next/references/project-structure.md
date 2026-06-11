# Project Structure and Configuration

> Source: https://developer.salesforce.com/docs/commerce/pwa-kit-managed-runtime/guide/sfnext-project-structure.html, https://developer.salesforce.com/docs/commerce/pwa-kit-managed-runtime/guide/sfnext-project-config.html

**Mental model:** React Router 7 framework mode + Vite. `src/` holds app code, `config.server.ts` at root is the single source of truth for all configuration. Client accesses config via `useConfig()`; server via `getConfig(context)`. Environment variables with `PUBLIC__` prefix override any config path at deploy time using `__` separators.

## Directory Layout

```text
src/
├── routes/              # File-based routing (flat routes convention)
├── components/          # Reusable UI (components/ui/ = shadcn primitives)
├── lib/                 # Non-React utilities, API clients, business logic
├── hooks/               # Custom React hooks
├── providers/           # React context providers
├── middlewares/         # Request middleware (*.server.ts = server-only)
├── extensions/          # Modular feature extensions
├── locales/             # i18n translation files per locale
├── theme/               # Global CSS, tokens, base resets, overrides
├── root.tsx             # App shell: middleware chain, root loader, Layout, App
├── routes.ts            # flatRoutes() auto-generates route config
config.server.ts         # All commerce/site/feature config (never import directly)
vite.config.ts           # Build config
react-router.config.ts   # React Router settings
```

## Route File Naming

| Pattern | Example | URL |
|---------|---------|-----|
| `_index.tsx` | `_index.tsx` | `/` (index at parent) |
| `name.tsx` | `cart.tsx` | `/cart` |
| `$param` | `product.$productId.tsx` | `/product/:productId` |
| `$.tsx` | `category.$.tsx` | `/category/*` (splat) |
| `parent.child.tsx` | `account.orders.tsx` | `/account/orders` |
| `action.*` | `action.cart-item-add.tsx` | Server action (no page) |
| `resource.*` | `resource.stores.ts` | API endpoint (no component) |
| `_empty.*` | `_empty.logout.tsx` | Bypasses parent layout |

`routes.ts` uses `flatRoutes()` — rarely needs modification.

## root.tsx Exports

| Export | Purpose |
|--------|---------|
| `middleware` | Server middleware chain (auth, locale, basket, etc.) |
| `clientMiddleware` | Client middleware (runs on client navigation) |
| `loader` | Root data loader (session, config, basket snapshot) |
| `Layout` | `<html>`, `<head>`, `<body>` structure |
| `default` (App) | Header + `<Outlet />` + Footer |

## Configuration Access

```typescript
// Server (loaders, actions, middleware)
import { getConfig } from '@/config';
export function loader({ context }: LoaderFunctionArgs) {
  const config = getConfig(context);
}

// Client (components)
import { useConfig } from '@/config';
function MyComponent() {
  const config = useConfig();
}
```

## Environment Variable Overrides

- Prefix: `PUBLIC__` (safe for browser) or none (server-only secret)
- Path separator: `__` → nested config path: `PUBLIC__app__commerce__api__clientId`
- Auto-parsed types: numbers, booleans, JSON arrays/objects
- Deep-merged into `config.server.ts` defaults
- Case-insensitive

## Minimum Required Env Vars

```bash
PUBLIC__app__commerce__api__clientId=your-client-id
PUBLIC__app__commerce__api__organizationId=your-org-id
PUBLIC__app__commerce__api__shortCode=your-short-code
# Private SLAS (optional):
PUBLIC__app__commerce__api__privateKeyEnabled=true
COMMERCE_API_SLAS_SECRET=your-secret  # NEVER use PUBLIC__ prefix
```

## Rules

- Never import `config.server.ts` directly — always use `getConfig()` or `useConfig()`
- Never put secrets in `PUBLIC__` variables — they're bundled to browser JS
- `runtime.ssrOnly` accepts glob patterns for server-only files
- `url.prefix` and `url.excludeRoutes` cannot be overridden via env vars (require rebuild)
