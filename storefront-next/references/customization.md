# Customization and Upgrades

> Source: https://developer.salesforce.com/docs/commerce/pwa-kit-managed-runtime/guide/sfnext-customize.html, https://developer.salesforce.com/docs/commerce/pwa-kit-managed-runtime/guide/sfnext-component-extend-upgrade.html

**Mental model:** New pages = new route files in `src/routes/`. New components = new folders in `src/components/`. For upgrading customized components after Salesforce releases updates: either merge directly (minimal customizations) or maintain separate copies with Vite aliasing (extensive customizations).

## createPage HOC

`createPage` provides standardized Suspense wrappers, page key management, and loading states:

```typescript
import { createPage, type RouteComponentProps } from '@/components/create-page';

function ProductView({ loaderData }: RouteComponentProps<ProductPageData>) {
  return (/* ... */);
}

export default createPage<ProductPageData>({
  component: ProductView,
  fallback: <ProductSkeleton />,
});
```

Use `createPage` for all new page routes to ensure consistent loading states and error handling.

## Adding a Custom Page

1. Create component in `src/components/<name>/index.tsx`
2. Create route file in `src/routes/_app.<page-name>.tsx`

The `_app.` prefix nests under the `_app.tsx` layout (header/footer). Without a loader, the page renders immediately.

### Route File Pattern

```tsx
// src/routes/_app.custom-page.tsx
import { type ReactElement } from 'react';
import { createPage, type RouteComponentProps } from '@/components/create-page';
import CustomBanner from '@/components/custom-banner';

export type CustomPageData = Record<string, never>;

function CustomPageView({}: RouteComponentProps<CustomPageData>): ReactElement {
  return (
    <div className="pb-16">
      <CustomBanner title="Welcome to the Custom Collection!" />
    </div>
  );
}

export default createPage<CustomPageData>({ component: CustomPageView });
```

`createPage` wraps with Suspense and loading handling.

### Component Pattern

```tsx
// src/components/custom-banner/index.tsx
export interface CustomBannerProps {
  title: string;
  subtitle?: string;
  className?: string;
}

export default function CustomBanner({ title, subtitle, className }: CustomBannerProps): ReactElement {
  return (
    <div className={`w-full bg-primary text-primary-foreground py-12 md:py-16 lg:py-20 ${className || ''}`}>
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold mb-4">{title}</h1>
          {subtitle && <p className="text-lg sm:text-xl text-primary-foreground/90">{subtitle}</p>}
        </div>
      </div>
    </div>
  );
}
```

## Upgrade Strategy: Method 1 — Merge Directly

Use when: minimal customizations, straightforward conflicts, want single version.

Supervised Git merge of upstream updates. Review all changes to preserve customizations.

## Upgrade Strategy: Method 2 — Vite Aliasing

Use when: extensive customizations, complex conflicts, want explicit control over adoption timing.

1. Create `/customizations/` directory
2. Copy component to customize
3. Modify your copy
4. Configure Vite alias:

```typescript
// vite.config.ts
import path from 'path';

export default defineConfig({
  plugins: [reactRouter(), tailwindcss(), tsconfigPaths(), storefrontNextPlugin()],
  resolve: {
    alias: {
      '@/components/ProductCard': path.resolve(__dirname, './customizations/ProductCard'),
    },
  },
});
```

Original stays untouched. You manually adopt upstream changes at your pace.

## Rules

- UI Extensions (`<UITarget>`, `target-config.json`) are for ISVs/partners, NOT for template customization
- Use Vite aliasing (Method 2) or direct merge (Method 1) for component customization
- `_app.` prefix = nested under main layout with header/footer
- Use `createPage` wrapper for consistent loading states and error handling
- After creating/modifying routes: `pnpm run build && pnpm run dev`
