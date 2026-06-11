# State Management

> Source: https://developer.salesforce.com/docs/commerce/pwa-kit-managed-runtime/guide/sfnext-state-management.html

**Mental model:** React Router replaces global state libraries for remote state. `loader` → `useLoaderData` handles fetch+sync. `action` auto-revalidates all loaders. No Redux/React Query needed for server data. Use React primitives only for client-only UI state.

## State Types and Tools

| State Type | Tool |
|-----------|------|
| Server/remote data | `loader` + `useLoaderData` |
| Mutations | `action` + `<Form>` |
| Mutations without navigation | `useFetcher` |
| Cross-route data | `useRouteLoaderData("routeId")` |
| Middleware context | `context.set` / `context.get` (request-scoped, not React Context) |
| Navigation state | `useNavigation()` |
| URL state | `useSearchParams`, `useParams` |
| Persistent (cookies) | `createCookie`, `createCookieSessionStorage` |
| Optimistic | `fetcher.formData`, `useOptimistic` |
| Error state | `useRouteError` + `ErrorBoundary` |
| Local UI | `useState`, `useReducer`, Context API |

## Key Patterns

### Cross-Route Data
```tsx
const rootData = useRouteLoaderData<typeof rootLoader>("root");
```
Returns `undefined` if target route isn't active. Route ID must match route config.

### URL State
Use `useSearchParams` over `useState` when state should: survive refresh, be shareable via URL, be accessible to loaders.

### Optimistic UI
- **Simple:** `fetcher.formData` — read pending values directly
- **URL-driven:** `navigation.location` — read target search params while navigating
- **Complex transforms:** `useOptimistic()` (React 19) — temporary state auto-reverts on settle

### Cookies vs Sessions vs URL

| Criterion | Cookies | Sessions | URL |
|-----------|---------|----------|-----|
| Survives refresh | Yes | Yes | Yes |
| Shareable via link | No | No | Yes |
| Available in loaders | Yes | Yes | Yes (via request.url) |
| Works without JS | Yes | Yes | Only with `<Form>` |
| Security (httpOnly) | Yes | Yes | No |

## Zustand (Feature-Level Client State)

For complex extension-specific UI state (e.g., store locator modal), use Zustand:

```typescript
// src/extensions/store-locator/stores/store-locator-store.ts
import { createStore } from 'zustand/vanilla';

type StoreLocatorState = {
  isOpen: boolean;
  mode: 'input' | 'device';
  selectedStoreInfo: SelectedStoreInfo | null;
};

type StoreLocatorActions = {
  open: () => void;
  close: () => void;
  setSelectedStoreInfo: (info: SelectedStoreInfo) => void;
};

export const createStoreLocatorStore = (init?: Partial<StoreLocatorState>) => {
  return createStore<StoreLocatorState & StoreLocatorActions>()((set) => ({
    isOpen: false,
    mode: 'input',
    selectedStoreInfo: init?.selectedStoreInfo ?? null,
    open: () => set({ isOpen: true }),
    close: () => set({ isOpen: false }),
    setSelectedStoreInfo: (selectedStoreInfo) => set({ selectedStoreInfo }),
  }));
};
```

## Post-Mutation Sync Pattern

Keep mutations on the server; update request-context resources there:

```typescript
import { data } from 'react-router';
import { getBasket, updateBasketResource } from '@/middlewares/basket.server';

export async function action({ request, context }: ActionFunctionArgs) {
  const formData = await request.formData();
  const productId = formData.get('productId') as string;
  const basketResource = await getBasket(context);
  const clients = createApiClients(context);

  const { data: updatedBasket } = await clients.shopperBasketsV2.addItemToBasket({
    params: { path: { basketId: basketResource.current?.basketId ?? '' } },
    body: [{ productId, quantity: 1 }],
  });

  updateBasketResource(context, updatedBasket);
  return data({ success: true, basket: updatedBasket });
}
```

## When to Use Each

| Scenario | Use |
|----------|-----|
| Product data on page load | `loader` |
| Shopping cart badge count | Basket provider (`useBasket`, `useBasketSnapshot`) |
| Complex extension UI workflow | Zustand store |
| Add to cart | Server `action` + `updateBasketResource` |
| Search results | `loader` |

## Rules

- Don't use global state libraries for server data — loaders handle it
- Don't store derived values in `useState` — compute inline or `useMemo`
- Use `useMemo` only for expensive computations or referential stability
- Use `useCallback` only when passing to `memo`-wrapped children
- Context API is for low-frequency shared UI state (locale, preferences), not high-frequency updates
- Middleware context ≠ React Context. Middleware runs in request lifecycle; React Context in render lifecycle.
- Zustand only for feature-local complexity (typically extensions) — not for server data
- Sync basket/auth resources inside `action` handlers after mutations
