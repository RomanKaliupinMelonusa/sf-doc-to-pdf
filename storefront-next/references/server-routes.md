# Server API Routes (Resource Routes)

> Source: https://developer.salesforce.com/docs/commerce/pwa-kit-managed-runtime/guide/sfnext-server-routes.html

**Mental model:** Backend-For-Frontend pattern. All data flows through server endpoints (resource routes = route files with only `loader`/`action`, no default component). Client calls these endpoints via `useFetcher()` or `useScapiFetcher()`. Keeps credentials secure, reduces client bundle.

## Route Types

| Type | File pattern | HTTP method |
|------|-------------|-------------|
| Loader (GET) | `resource.*.ts` | GET |
| Action (mutations) | `action.*.ts` | POST/PUT/DELETE |
| Dynamic | `resource.auth.$operation.ts` | Any (param-based dispatch) |

## Loader Route Example

```typescript
// src/extensions/store-locator/routes/resource.stores.ts
import { data, type LoaderFunctionArgs } from 'react-router';
import { createApiClients } from '@/lib/api-clients';

export async function loader({ request, context }: LoaderFunctionArgs) {
  const url = new URL(request.url);
  const postalCode = url.searchParams.get('postalCode') ?? undefined;
  const clients = createApiClients(context);
  const { data: stores } = await clients.shopperStores.searchStores({
    params: { query: { postalCode } },
  });
  return Response.json({ success: true, stores });
}
```

## Action Route Example

```typescript
// src/routes/action.set-locale.ts
import { data, type ActionFunction } from 'react-router';
import { localeCookie } from '@/middlewares/i18next.server';

export const action: ActionFunction = async ({ request }) => {
  const formData = await request.formData();
  const locale = formData.get('locale') as string;
  if (!locale) throw new Response('Locale is required', { status: 400 });
  return data({ success: true }, { headers: { 'Set-Cookie': await localeCookie.serialize(locale) } });
};
```

## useScapiFetcher Hook

Generic hook that pairs with a server route to call any SCAPI method from components — keeps API communication on server.

```typescript
import { useScapiFetcher } from '@/hooks/use-scapi-fetcher';
```

You don't interact with the underlying route directly.

## Naming Conventions

- `resource.*` → `/resource/...` endpoints
- `action.*` → `/action/...` endpoints
- `loader.*` → `/loader/...` endpoints
- `_empty.*` → bypasses parent layouts (e.g., logout action that redirects)

## Rules

- Always use server `loader`/`action` — `clientLoader`/`clientAction` expose security risks
- Resource routes export only data functions (no default component export)
- Use `data()` helper for responses that need status codes with typed payloads
- Validate all inputs from `request.url` / `formData` in actions
- Keep API credentials server-side — never expose in client bundle
