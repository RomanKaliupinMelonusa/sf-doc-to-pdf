# UI Styling

> Source: https://developer.salesforce.com/docs/commerce/pwa-kit-managed-runtime/guide/sfnext-ui-styling.html

**Mental model:** Tailwind CSS v4 utility-first + shadcn/ui component pattern (Radix primitives + CVA variants + `cn()` helper). Semantic color tokens in CSS variables. No hardcoded color utilities allowed (ESLint enforced).

## Stack

| Dependency | Purpose |
|-----------|---------|
| tailwindcss 4.x | Utility-first CSS |
| @radix-ui/* | Headless accessible primitives |
| class-variance-authority | Component variant management (CVA) |
| clsx | Conditional class composition |
| tailwind-merge | Tailwind class conflict resolution |

## Theme Location

`src/theme/index.css` (entry point) → `src/theme/tokens/` (CSS variables) → `src/theme/base.css` (resets, component classes) → `src/theme/overrides/`

CSS variables in `:root`: `--background`, `--foreground`, `--primary`, `--primary-foreground`, `--secondary`, `--muted`, `--accent`, `--destructive`, `--border`, `--ring`, `--radius`

## cn() Utility

```typescript
// src/lib/utils.ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)); }
```

## Component Patterns

### Variant-Based (CVA pattern in shadcn/ui)

```tsx
// src/components/ui/button.tsx
const variantClasses: Record<ButtonVariant, string> = {
  default: 'bg-primary text-primary-foreground hover:bg-primary/90',
  outline: 'border bg-background hover:bg-accent',
};
function Button({ variant = 'default', size = 'default', className, ...props }) {
  return <button className={cn(baseClasses, variantClasses[variant], sizeClasses[size], className)} {...props} />;
}
```

### Compound Components

Multi-part components as separate functions: `Card`, `CardHeader`, `CardContent`, etc.

## Color Enforcement

**Hardcoded Tailwind colors (`bg-red`, `text-green`) are blocked via ESLint.** Use semantic tokens: `bg-primary`, `text-foreground`, `bg-destructive`, etc.

## Reuse Decision

| Condition | Use |
|-----------|-----|
| Has markup structure, props, logic, children | React component |
| Pure layout/styling, no logic, applied to many elements | `@layer components` CSS class |

```css
/* src/theme/base.css */
@layer components {
  .section-container { @apply px-4 sm:px-8 lg:px-16 max-w-screen-2xl mx-auto; }
}
```

Don't use `@utility` for multi-property compositions — utility layer has highest specificity, overrides won't work.

## Rules

- Never hand-roll UI primitives that exist in shadcn/ui (`src/components/ui/`)
- Always use `cn()` for className composition (handles conflicts)
- Use semantic color tokens, never hardcoded colors
- Responsive: use Tailwind prefix modifiers (`sm:`, `md:`, `lg:`)
- Components accept `className` prop for override capability
