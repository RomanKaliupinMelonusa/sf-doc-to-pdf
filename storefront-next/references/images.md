# Images and Dynamic Imaging Service

> Source: https://developer.salesforce.com/docs/commerce/pwa-kit-managed-runtime/guide/sfnext-images.html

**Mental model:** DIS transforms images at request time (resize, format convert, quality). `<DynamicImage>` generates `<picture>` with responsive `<source>` elements, DIS-powered srcSets, and React 19 `preload()` for high-priority images.

## DIS Configuration

```typescript
// config.server.ts → app.images
images: {
  quality: 70,              // 1-100
  formats: ['webp'],        // Target formats for <source>
  fallbackFormat: 'jpg',    // Format for <img> src
  host: DIS_DEFAULT_HOST,
  enableDis: true,          // false = serve static assets directly
}
```

Override per env: `PUBLIC__app__images__quality=80`, `PUBLIC__app__images__enableDis=false`

## DIS URL Parameters

| Param | Description |
|-------|-------------|
| `sw` | Scale width (px) |
| `sh` | Scale height (preserves aspect if alone) |
| `q` | Quality 1-100 |
| `sfrm` | Source format for transcoding |
| `sm` | Scale mode: `fit` (default) or `cut` |
| `cx,cy,cw,ch` | Crop region (all four required together) |

## DynamicImage Component

```tsx
import { DynamicImage } from '@/components/dynamic-image';

// Basic
<DynamicImage src="https://example.com/image.jpg" alt="Product" widths={[400, 800, 1200]} />

// Placeholder syntax
<DynamicImage src="https://example.com/image.jpg[?sw={width}&sh={height}]" widths={[400, 800]} heights={[300, 600]} />

// Breakpoint object
<DynamicImage src={src} widths={{ base: '100vw', sm: '50vw', md: '680px' }} />

// High priority (preloaded during SSR)
<DynamicImage src={heroImage} widths={[...]} priority="high" loading="eager" />
```

### widths formats

- Array of numbers: `[400, 600, 800]` (px)
- Array of strings: `['100vw', '50vw', '680px']` (mixed units; vw calculated per breakpoint)
- Breakpoint object: `{ base: 400, sm: 600, md: 800, lg: 1000 }` (keys: base/sm/md/lg/xl/2xl; values carried forward)

### heights

Enables `sh` param. Multiplied by DPR (2x → double). Supports same formats as widths.

## PLP Image Filtering

```typescript
// config.server.ts → app.search.products.images
search: {
  products: {
    images: {
      tile: 'medium',     // viewType for product tile hero
      swatch: 'swatch',   // viewType for color thumbnails
    },
  },
}
```

- Derives `imgTypes` query parameter as union of role values
- Setting role to `undefined` opts out; empty `images: {}` disables filtering (full payload)
- If you change the product tile to read a different viewType, update the matching role here

## Rules

- Use `<DynamicImage>` for all commerce images — handles responsive srcSets + preloading
- Use fixed px widths for predetermined containers (carousels); vw for viewport-scaling (grids, heroes)
- Only request SCAPI `expand=images` + `allImages=true` when using `imgTypes` filtering
- Don't over-request image expansions — increases PLP payload dramatically on variant-heavy catalogs
