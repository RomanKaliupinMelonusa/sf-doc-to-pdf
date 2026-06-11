---
name: storefront-next
description: Salesforce Storefront Next development reference (React Router 7 framework mode on Managed Runtime, SCAPI, B2C Commerce). Use this skill whenever writing, reviewing, or debugging ANY code in this storefront — routes, loaders, actions, basket logic, SCAPI calls, caching, sessions, shopper context, server API routes, styling, images, SEO, i18n, multisite, adapters, extensions, action hooks, customization, component upgrades, security headers, Page Designer, testing, Storybook, deployment, hybrid storefronts, performance — even if the user doesn't mention Storefront Next by name.
---

# Storefront Next Reference

Read ONLY the reference files relevant to the current task:

| Task involves… | Read |
| --- | --- |
| Project layout, directory conventions, file naming, routes.ts, root.tsx | references/project-structure.md |
| Fetching data in routes, loaders, actions, streaming, createApiClients, useScapiFetcher | references/data-fetching.md |
| Suspense boundaries, deferred promises, skeleton patterns, promise identity | references/loading-states.md |
| State management, useLoaderData, useFetcher, URL state, optimistic UI, Zustand stores | references/state-management.md |
| Cart, add/remove items, basket middleware, BasketProvider, useBasket, checkout state | references/basket-management.md |
| Calling SCAPI, commerce API client creation, auth flows, token handling, TypeScript types | references/scapi-client.md |
| Authentication, login/logout, session cookies, token refresh, 401 recovery, useAuth | references/sessions-auth.md |
| Caching strategy, SCAPI cache behavior, expand parameters, TTL impact | references/caching.md |
| Shopper context, qualifiers, source codes, personalization, useShopperContext | references/shopper-context.md |
| Resource routes, BFF pattern, server actions, useScapiFetcher, dynamic endpoints | references/server-routes.md |
| Tailwind, shadcn/ui, cn(), CVA variants, theming, CSS variables, color tokens, responsive | references/ui-styling.md |
| Images, DIS, DynamicImage component, responsive widths, preloading, PLP image filtering | references/images.md |
| SEO, metadata, canonical URLs, hreflang, SeoMeta component, robots, Open Graph | references/seo-metadata.md |
| Multisite, URL patterns, site/locale detection, aliases, site-context cookies | references/multisite.md |
| Internationalization, translations, useTranslation, getTranslation, Zod factory, locale switching | references/i18n.md |
| Analytics, Einstein, Active Data, engagement adapters, sendEvent, consent | references/adapters.md |
| Security headers, CSP, extending directives, HSTS, Permissions-Policy | references/security-headers.md |
| Extensions, UITarget, action hooks, extension config, extension i18n, target-config.json | references/extensions.md |
| Adding pages, new components, createPage HOC, Vite aliasing, upgrade strategy | references/customization.md |
| Page Designer, decorators, component registry, Region, fetchPageFromLoader, cartridge deploy | references/page-designer.md |
| Vitest unit tests, Storybook stories, interaction tests, a11y, coverage thresholds | references/testing.md |
| Bundle size, DynamicImage perf, parallel fetching, sync loaders, Lighthouse, metrics | references/performance.md |
| Build, deploy to MRT, sfnext push, env vars per environment, pre-deploy checklist | references/deployment.md |
| Hybrid with SFRA/SiteGenesis, proxy config, session bridging, gradual migration | references/hybrid-storefronts.md |
