# CLAUDE.md

This is a Salesforce Storefront Next storefront: a full-stack React commerce app built on React Router 7 (framework mode), React 19, Vite, TypeScript, Tailwind CSS v4, and shadcn/ui, deployed on Managed Runtime (MRT), fetching commerce data via SCAPI.

## Rendering Model

- Every initial request is server-rendered (SSR) with streaming from MRT.
- After hydration, navigation is client-side via React Router — only data requests hit the server (loaders re-invoke server-side).
- Prefer **sync loaders** returning promises (enables streaming SSR). Only `await` data that is SEO-critical or needed for the page shell.
- Non-critical data is returned as unresolved Promises from loaders and streamed via `<Suspense>` + `<Await>`.
- HTML documents are never cached; static assets are immutable at the edge.

## Data Flow

- Route loader → `createApiClients(context)` → SCAPI → B2C Commerce API. All SCAPI calls server-side only.
- Configuration from `config.server.ts`, accessed via `getConfig(context)` (server) or `useConfig()` (client).
- Auth tokens live only in server middleware (`auth.server.ts`); client receives non-sensitive `PublicSessionData` via `useAuth()`.
- Basket state: cookie snapshot via middleware → lazy hydration client-side via `useBasket()`.
- Interactive data (post-page-load): `useScapiFetcher` hook calls SCAPI via server resource route.

## Hard Rules

- **TypeScript only** — `.ts`/`.tsx` files exclusively. No `.js`/`.jsx`/`.mjs`/`.cjs` (ESLint blocks them).
- Never fetch in `useEffect` or client-side code when a loader can do it.
- Never use `clientLoader` or `clientAction` — server-only data retrieval is enforced.
- Never put secrets in `PUBLIC__` env vars or any client-reachable code.
- Never import `config.server.ts` directly — use `getConfig()` or `useConfig()`.
- Never hand-roll UI primitives that exist in `src/components/ui/` (shadcn/ui). Add via `npx shadcn@latest add <component>`.
- Never hardcode Tailwind color utilities (`bg-red-500`) — use semantic tokens (`bg-primary`, `text-destructive`). ESLint blocks this.
- Never use CSS modules, inline styles, or separate CSS files — Tailwind CSS v4 only.
- Never compose promises in a component body — breaks Suspense identity (infinite fallback).
- Never share a single `<Suspense>` boundary across multiple deferred promises.
- Never return `Response.json()` from actions — use `data()` from `react-router`.
- Never return error data with HTTP 200 — throw a `Response` with the correct status code.
- Never call SCAPI directly from client components — all API calls route through server loaders/actions.
- Never use sequential `await` for independent SCAPI calls — parallelize with concurrent promises.
- Never create Zod schemas with `t()` at module level — use factory pattern `createSchema(t)`.

## Repo Conventions

```
src/routes/          → Pages and resource routes (flat routes convention)
src/components/      → Reusable UI (components/ui/ = shadcn primitives)
src/lib/             → Non-React utilities, API clients (api-clients.ts), business logic
src/hooks/           → Custom React hooks
src/providers/       → React context providers
src/middlewares/     → Request middleware (*.server.ts = server-only)
src/extensions/      → Feature extensions (ISV/partner add-ons)
src/locales/         → i18n translation files (one dir per locale)
src/theme/           → Global CSS, tokens, overrides
src/test-utils/      → Shared test mocks, providers, config
config.server.ts     → All app/commerce/feature configuration
```

- Routes: `product.$productId.tsx`, `action.cart-item-add.tsx`, `resource.stores.ts`
- Components: folder per component with `index.tsx` entry + `index.test.tsx` + `stories/`. Use `cn()` for all className composition.
- New pages: `src/routes/_app.<page-name>.tsx` (nests under main layout). Wrap with `createPage()` HOC.
- Resource routes (API endpoints): export only `loader`/`action`, no default component.
- Tests colocated with source (`index.test.tsx` beside `index.tsx`).
- SCAPI access in loaders/actions: always `createApiClients(context)` from `@/lib/api-clients`.

## Verification

Run before declaring work done:

```bash
pnpm typecheck && pnpm lint && pnpm test
```

Fix all errors. Do not skip or suppress warnings without justification. Also run `pnpm bundlesize:test` before deployment.

## Skill Reference

Detailed Storefront Next reference lives in the `storefront-next` skill. Consult it before implementing anything touching baskets, caching, sessions, i18n, multisite, SEO, adapters, extensions, action hooks, server routes, images, shopper context, security headers, Page Designer, hybrid storefronts, testing, or deployment.
