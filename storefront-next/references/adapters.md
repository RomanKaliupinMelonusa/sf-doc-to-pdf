# Engagement Adapter Pattern

> Source: https://developer.salesforce.com/docs/commerce/pwa-kit-managed-runtime/guide/sfnext-adapters.html

**Mental model:** Components call a generic `sendEvent()` interface. The adapter store dispatches to registered vendor implementations (Einstein, Active Data). Adapters are lazily initialized via dynamic import (code-split, not in initial bundle).

## Architecture

```
Component → sendEvent(event) → Adapter Store (Map) → Vendor Implementation (Einstein/ActiveData)
```

## File Structure

```
src/lib/adapters/engagement/
├── types.ts          # EngagementAdapter interface
├── store.ts          # addAdapter, getAdapter, getAllAdapters, removeAdapter
├── einstein.ts       # createEinsteinAdapter factory
├── active-data.ts    # createActiveDataAdapter factory
├── register.ts       # initializeEngagementAdapters (reads config, registers)
├── initialize.ts     # ensureAdaptersInitialized (lazy, idempotent)
└── utils.ts          # hasConsent helper
```

## Interface

```typescript
export interface EngagementAdapter extends EventAdapter {
  name: string;
  sendEvent?: (event: AnalyticsEvent, siteInfo?: EventSiteInfo, consentPreferences?: ConsentPreferences) => Promise<unknown>;
  send?: (url: string, options?: RequestInit) => Promise<Response>;
}
```

## Store API

```typescript
addAdapter('einstein', adapter);
getAdapter('einstein');
getAllAdapters();
removeAdapter('einstein');
```

## Configuration

```typescript
// config.server.ts → app.engagement.adapters
engagement: {
  adapters: {
    einstein: {
      enabled: true,
      host: 'https://api.cquotient.com',
      einsteinId: '<id>',
      siteId: '<site>',
      realm: '<realm>',
      isProduction: false,
      consentCategory: 'C0004',
      eventToggles: { view_product: true, cart_item_add: true },
    },
    activeData: { enabled: true, host: '<host>', siteUUID: '<uuid>', consentCategory: 'C0002' },
  },
}
```

If `enabled: false`, adapter isn't registered.

## Adding a Custom Adapter

1. Create `src/lib/adapters/engagement/your-adapter.ts` (factory → `EngagementAdapter`)
2. Register in `register.ts` inside `initializeEngagementAdapters()`
3. Add config under `engagement.adapters.yourAdapter`

## Testing

```typescript
const mockAdapter = { name: 'mock-einstein', sendEvent: vi.fn().mockResolvedValue(undefined) };
beforeEach(() => addAdapter('einstein', mockAdapter));
afterEach(() => removeAdapter('einstein'));

// Reset lazy init for clean state
import { resetAdaptersInitialization } from '@/lib/adapters/engagement/initialize';
afterEach(() => resetAdaptersInitialization());
```

## Gotchas

- Adapters are code-split via dynamic `import()` — not in initial bundle
- `ensureAdaptersInitialized()` is idempotent — safe to call multiple times
- Consent checking is per-adapter via `consentCategory` — events skipped if no consent
