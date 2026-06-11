# Testing

> Source: https://github.com/SalesforceCommerceCloud/b2c-developer-tooling/tree/main/skills/storefront-next/skills/sfnext-testing

**Mental model:** Vitest for unit/integration tests (colocated with source), Storybook for component stories + interaction tests + a11y. Tests live next to source files. Coverage thresholds enforced. Use `@testing-library/react` patterns.

## Test Organization

```
src/components/product-tile/
├── index.tsx              # Component
├── index.test.tsx         # Vitest unit tests
└── stories/
    └── index.stories.tsx  # Storybook stories

src/routes/
├── _app.product.$productId.tsx
└── _app.product.$productId.test.tsx
```

## Commands

```bash
pnpm test                # Run all tests with coverage
pnpm test:ui             # Interactive Vitest UI
pnpm test:watch          # Watch mode
pnpm storybook           # Dev server (port 6006)
pnpm build-storybook     # Build static Storybook
pnpm test-storybook:interaction    # Interaction tests
pnpm test-storybook:a11y           # Accessibility tests
pnpm test-storybook:snapshot       # Snapshot tests
pnpm bundlesize:test     # Verify bundle limits
```

## Coverage Thresholds (vitest.thresholds.ts)

| Metric | Minimum |
|--------|---------|
| Lines | 73% |
| Statements | 73% |
| Functions | 72% |
| Branches | 67% |

## Unit Test Pattern

```typescript
// src/components/product-card/index.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProductCard } from './index';
import { mockProduct } from '@/test-utils/mocks';

describe('ProductCard', () => {
  it('renders product name', () => {
    render(<ProductCard product={mockProduct} />);
    expect(screen.getByText(mockProduct.productName)).toBeInTheDocument();
  });
});
```

## Route Testing

Mock loaders, actions, and React Router context:

```typescript
// src/routes/_app.product.$productId.test.tsx
import { describe, test, expect, vi } from 'vitest';
import { render } from '@testing-library/react';

vi.mock('@/components/product-view', () => ({
  default: ({ product }: any) => (
    <div data-testid="product-view">
      <div data-testid="product-name">{product?.name}</div>
    </div>
  ),
}));
```

## Storybook Story Pattern

```typescript
// src/components/product-card/stories/index.stories.tsx
import type { Meta, StoryObj } from '@storybook/react-vite';
import { within, expect } from 'storybook/test';
import { ProductCard } from '../index';
import { ConfigProvider } from '@/config/context';
import { mockConfig } from '@/test-utils/config';
import { mockProduct } from '@/test-utils/mocks';

const meta: Meta<typeof ProductCard> = {
  title: 'Components/ProductCard',
  component: ProductCard,
  tags: ['autodocs', 'interaction'],
  decorators: [
    (Story) => (
      <ConfigProvider config={mockConfig}>
        <Story />
      </ConfigProvider>
    ),
  ],
};
export default meta;
type Story = StoryObj<typeof ProductCard>;

export const Default: Story = {
  args: { product: mockProduct },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText(mockProduct.productName)).toBeInTheDocument();
  },
};
```

### Story Tags

| Tag | Purpose |
|-----|---------|
| `autodocs` | Enable automatic documentation |
| `interaction` | Include in interaction test runs |
| `skip-a11y` | Exclude from a11y tests (use sparingly) |

## Test Utilities (`src/test-utils/`)

- `config.ts` — Mock configuration objects and ConfigProvider wrappers
- `context-provider-utils.ts` — Context provider helpers
- `context-provider.tsx` — Test context providers
- `mocks/` — Shared mock data

## Testing Libraries

| Library | Purpose |
|---------|---------|
| `@testing-library/react` | Component rendering and queries |
| `@testing-library/jest-dom` | Custom DOM matchers |
| `@testing-library/user-event` | User interaction simulation |
| `@vitest/coverage-v8` | Code coverage |
| `@vitest/ui` | Interactive test UI |

## Rules

- Colocate tests next to source files (`.test.tsx` beside `index.tsx`)
- Use `vi.mock()` for API clients and context providers
- Use `@testing-library/user-event` for interaction testing
- Create stories for Default, Loading, Error states
- Multiple story variants per component
- Never skip a11y tests without documented reason
