# Performance

> Source: https://github.com/SalesforceCommerceCloud/b2c-developer-tooling/tree/main/skills/storefront-next/skills/sfnext-performance

**Mental model:** Performance comes from: (1) sync loaders returning promises for streaming SSR, (2) parallel SCAPI calls, (3) bundle size enforcement, (4) DynamicImage for responsive WebP, (5) granular Suspense boundaries for progressive rendering.

## Bundle Size Enforcement

```bash
pnpm bundlesize:test      # Verify bundle within limits
pnpm bundlesize:analyze   # Analyze bundle composition
```

Limits configured in `package.json` under `bundlesize`.

## Performance Metrics

```typescript
// config.server.ts
performance: {
  metrics: {
    serverPerformanceMetricsEnabled: true,
    clientPerformanceMetricsEnabled: true,
    serverTimingHeaderEnabled: false,  // Enable for debugging only
  }
}
```

Tracks: SSR operations, SCAPI call timing with parallelization visibility, auth operations, client navigation timing.

## Parallel Data Fetching

```typescript
// ✅ GOOD — Parallel (all requests start at once, stream independently)
export function loader({ context }: LoaderFunctionArgs) {
  const clients = createApiClients(context);
  return {
    product: clients.shopperProducts.getProduct({...}).then(({ data }) => data),
    reviews: clients.shopperProducts.getReviews({...}).then(({ data }) => data),
    recommendations: clients.shopperProducts.getRecommendations({...}).then(({ data }) => data),
  };
}

// ❌ BAD — Sequential (each waits for previous)
export async function loader({ context }: LoaderFunctionArgs) {
  const clients = createApiClients(context);
  const product = await clients.shopperProducts.getProduct({...});  // Waits...
  const reviews = await clients.shopperProducts.getReviews({...});  // Then waits again
  return { product, reviews };
}
```

## Progressive Streaming

Synchronous loaders returning promises enable streaming SSR — the shell renders immediately while data streams in per-Suspense-boundary:

```typescript
// Full streaming (best for pages where all data renders progressively)
export function loader({ params, context }: LoaderFunctionArgs) {
  const clients = createApiClients(context);
  return {
    product: clients.shopperProducts.getProduct({...}).then(({ data }) => data),
    reviews: clients.shopperProducts.getReviews({...}).then(({ data }) => data),
  };
}
```

Combine with granular Suspense boundaries for progressive page rendering.

## Image Optimization

Use `<DynamicImage>` for all commerce images:

```typescript
import { DynamicImage } from '@/components/dynamic-image';

<DynamicImage
  src={product.image.link}
  alt={product.image.alt}
  widths={[400, 800]}
  priority="high"      // Above-the-fold
  loading="eager"
/>
```

- WebP format by default (25-35% smaller)
- Set explicit widths to prevent layout shifts
- Lazy load below-the-fold images (default behavior)
- Use SCAPI image alt text

## Lighthouse

```bash
pnpm lighthouse:ci   # Run Lighthouse CI
```

Key areas: preload critical CSS, WebP images, lazy-load below-fold, optimize fonts, minimize JS bundle.

## Rules

- Use sync loaders (return promises) over async loaders (await) — enables streaming
- Only `await` data that is SEO-critical or needed for the page shell
- Parallelize independent SCAPI calls — never sequential `await` for independent data
- Run `pnpm bundlesize:test` before every deploy
- Use `<DynamicImage>` — never raw `<img>` for commerce images
- Code-split heavy components with `lazy()` + `<Suspense>`

## Gotchas

| Issue | Cause | Solution |
|-------|-------|----------|
| Large bundle | Unused imports or heavy deps | `bundlesize:analyze`; tree-shake or lazy load |
| Slow transitions | Async loaders blocking | Use sync loaders returning promises |
| Layout shifts | Missing image dimensions | Set widths/heights on DynamicImage |
| Slow SCAPI | Sequential API calls | Parallel data fetching |
