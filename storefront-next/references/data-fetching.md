# Data Fetching

> Source: https://developer.salesforce.com/docs/commerce/pwa-kit-managed-runtime/guide/sfnext-data-loading.html

**Mental model:** Server-load everything. MRT is the data orchestration layer, not a proxy. All SCAPI calls execute on the server via route loaders. Initial request is SSR with streaming; subsequent navigations are client-side but still invoke server loaders for data. No client-side data fetching for initial loads.

## Dependencies

| Package | Version |
|---------|---------|
| `react-router` | 7.12.0 |
| `react` | 19.2.0 |

## Core Paradigms

1. **Server-load everything** — All API requests execute on MRT (server). Loaders aggregate parallel/sequential SCAPI requests into a single request to MRT, streamed to client.
2. **Route-level data fetching** — Loaders are the only mechanism guaranteeing data before component render on server. Never use `useEffect`/`fetch` for initial page data.

## Data Classification

| Type | Behavior | Example |
|------|----------|---------|
| **Critical** | `await` in loader before return. Blocks render. Required for SEO, LCP, correct HTTP status. | Product title, meta, prices |
| **Non-critical** | Return Promise (don't await). Streamed via `<Suspense>`. | Recommendations, reviews |
| **Interaction-driven** | Fetched on user action via fetchers. | Add-to-cart response |

## API Client Access

Always use `createApiClients(context)` in loaders and actions:

```typescript
import { createApiClients } from '@/lib/api-clients';

export function loader({ context }: LoaderFunctionArgs) {
  const clients = createApiClients(context);
  clients.shopperProducts.getProduct({...});
  clients.shopperSearch.productSearch({...});
  clients.shopperBasketsV2.getBasket({...});
  clients.shopperCustomers.getCustomer({...});
}
```

## Loaders

Loader arguments: `request` (Request), `params` (object), `context` (RouterContextProvider from middleware).

### Sync Loader (Full Streaming — Preferred)

Returns promises directly. Shell renders immediately; data streams in progressively. Best when all data renders progressively:

```typescript
export function loader({ params, context }: LoaderFunctionArgs): ProductPageData {
  const clients = createApiClients(context);
  return {
    product: clients.shopperProducts.getProduct({
      params: { path: { id: params.productId } }
    }).then(({ data }) => data),
    reviews: clients.shopperProducts.getReviews({
      params: { path: { id: params.productId } }
    }).then(({ data }) => data),
  };
}
```

### Async Loader (Await Critical Data)

Use when data is required for SEO or the page shell (e.g., category name in breadcrumbs):

```typescript
export async function loader({ params, context }: LoaderFunctionArgs): Promise<CategoryPageData> {
  const clients = createApiClients(context);
  // Await critical data needed for page shell/SEO
  const category = await clients.shopperProducts.getCategory({
    params: { path: { id: params.categoryId } }
  }).then(({ data }) => data);

  return {
    category,  // Resolved immediately
    products: clients.shopperSearch.productSearch({
      params: { query: { q: '', refine: { cgid: params.categoryId } } }
    }).then(({ data }) => data),  // Streamed
  };
}
```

### When to Use Each

| Pattern | When | Example |
|---------|------|--------|
| Sync (full streaming) | All data can render progressively | Product page with reviews |
| Async (await critical) | SEO-critical data needed for page shell | Category page (needs name) |
| Mixed | Some data critical, some deferrable | Category name (await) + grid (stream) |
```

### Consuming Loader Data

```tsx
// Props pattern
export default function Page({ loaderData: { product, reviews } }: { loaderData: PageData }) {
  return (
    <>
      <h1>{product.name}</h1>
      <Suspense fallback={<Skeleton />}>
        <Await resolve={reviews}>{(data) => <Reviews data={data} />}</Await>
      </Suspense>
    </>
  );
}

// Or useLoaderData hook
const loaderData = useLoaderData<PageData>();
```

### 404 Handling

Throw `Response` for missing resources — never return error data with 200:

```typescript
throw new Response("Product not found", { status: 404 });
```

Caught by nearest `ErrorBoundary` in route hierarchy.

### SCAPI Request Shape

- Audit each loader: only request fields the route renders (payload size → TTFB)
- Each unique query string = separate SCAPI cache entry
- Short-TTL fields (inventory, pricing) pull entire response to shorter schedule. Fetch them separately as non-critical deferred data.

## Actions

Handle mutations (POST/PUT/DELETE). Always return `data(payload, init?)` from `react-router` — never `Response.json(...)`.

```typescript
import { data } from 'react-router';

export type ExampleResponse = { success: boolean; error?: ActionError };

export async function action({ request, context }: Route.ActionArgs): Promise<ReturnType<typeof data<ExampleResponse>>> {
  // mutation logic
  return data({ success: true }, { status: 200 });
}
```

- Annotate with explicit return type for type inference via `useFetcher<typeof action>()`
- After action completes, React Router auto-revalidates all active loaders

## Fetchers

`useFetcher()` calls loaders (reads) or actions (writes) without navigation. Each fetcher has independent lifecycle (`fetcher.state`, `fetcher.data`).

## useScapiFetcher (Interactive Data Fetching)

For on-demand data fetching triggered by user interactions (after page load):

```typescript
import { useScapiFetcher } from '@/hooks/use-scapi-fetcher';

export function useSearchSuggestions({ q, limit, currency }) {
  const parameters = useMemo(
    () => ({ params: { query: { q, limit, currency } } }),
    [q, limit, currency]
  );

  const fetcher = useScapiFetcher('shopperSearch', 'getSearchSuggestions', parameters);

  const refetch = useCallback(async () => {
    await fetcher.load();
  }, [fetcher]);

  return { data: fetcher.data, isLoading: fetcher.state === 'loading', refetch };
}
```

## Middlewares

Run in pipeline before loaders/actions. Populate typed context for downstream consumption. Not React Context — runs in request lifecycle.

```typescript
export const middleware: MiddlewareFunction[] = [authMiddleware, i18nMiddleware, basketMiddleware];
```

## Rules

- Never use `clientLoader` or `clientAction` — server-only data retrieval is enforced
- Never fetch in `useEffect` when a loader can do it
- Never mix short-TTL SCAPI fields into critical long-cacheable payloads
- Always throw Response with non-200 status for errors (not return with 200)
- Use `data()` from react-router for action returns, not `Response.json()`

## Gotchas

- Unresolved promises in loader return trigger `<Suspense>` — must wrap each in its own `<Suspense>` boundary
- Promise identity matters: never compose promises in component body (creates new object each render → infinite fallback flicker)
- Promises from `useLoaderData` are identity-stable for the route match lifetime
