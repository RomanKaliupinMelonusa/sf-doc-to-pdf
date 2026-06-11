# Loading States

> Source: https://developer.salesforce.com/docs/commerce/pwa-kit-managed-runtime/guide/sfnext-suspense.html

**Mental model:** Declarative loading = `<Suspense>` boundaries catching unresolved promises from loaders. Imperative loading = `useNavigation()` and `useFetcher().state` for transition/mutation feedback. Each deferred promise needs its own Suspense boundary to avoid fallback thrashing.

## Declarative: Suspense + Await

Preferred pattern — `<Await>` resolves inline, co-locates error handling:

```tsx
<Suspense fallback={<Skeleton />}>
  <Await resolve={nonCritical} errorElement={<ErrorFallback />}>
    {(data) => <Content data={data} />}
  </Await>
</Suspense>
```

Alternative — React 19 `use()` (requires separate component):

```tsx
function Wrapper({ promise }: { promise: Promise<Data> }) {
  const data = use(promise);
  return <Content data={data} />;
}
<Suspense fallback={<Skeleton />}>
  <Wrapper promise={nonCritical} />
</Suspense>
```

## Critical Rule: One Promise Per Boundary

Each deferred promise **must** have its own `<Suspense>` boundary.

```tsx
// ✅ Correct
<Suspense fallback={<SkeletonA />}>
  <Await resolve={promiseA}>{(d) => <A data={d} />}</Await>
</Suspense>
<Suspense fallback={<SkeletonB />}>
  <Await resolve={promiseB}>{(d) => <B data={d} />}</Await>
</Suspense>
```

### Anti-patterns (cause fallback thrashing / CLS)

1. Multiple `<Await>` sharing one `<Suspense>` boundary
2. Multiple `use()` calls in one component (same boundary)
3. Nested `<Await>` inside one boundary (artificial waterfall)

**Exception:** Truly dependent promises (detail after list) can share a boundary — they're one logical unit.

## Promise Identity

`<Suspense>` tracks promises by reference. Same logical operation must produce same promise object across renders.

- Loader promises: identity-stable (React Router preserves them per route match)
- `Promise.all`, `.then()`, any composition in component body: **creates new reference each render → infinite fallback**
- Never compose promises in the component body; do it in the loader

## Imperative: useNavigation / useFetcher

```tsx
const navigation = useNavigation();
// navigation.state: 'idle' | 'loading' | 'submitting'

const fetcher = useFetcher();
// fetcher.state: 'idle' | 'loading' | 'submitting'
```

Use for global spinners, skeleton overlays during navigation, and per-component mutation feedback.
