# Deployment

> Source: https://github.com/SalesforceCommerceCloud/b2c-developer-tooling/tree/main/skills/storefront-next/skills/sfnext-deployment

**Mental model:** Build locally with Vite, push bundle to MRT via `sfnext` CLI. Env vars configured in MRT dashboard per environment. Page Designer cartridge deployed separately to Commerce Cloud. Bundle size enforced pre-deploy.

## Build and Deploy

```bash
# Production build (compiles TS, bundles client/server, minifies, generates PD registry)
pnpm build

# Push to MRT
pnpm push
# Or with options:
pnpm sfnext push -m "Release v1.2.0"
pnpm sfnext push --environment staging --wait
```

Flow: `pnpm build → pnpm push → MRT receives bundle → Deployed to environment`

## MRT Deployment Variables

```bash
# Project slug (required for push)
MRT_PROJECT=my-project-slug

# Target environment (optional — if omitted, bundle uploaded but not deployed)
MRT_TARGET=development
```

## Environment Configuration (MRT Dashboard)

```bash
# Set per environment in MRT Dashboard
PUBLIC__app__commerce__api__clientId=prod-client-id
PUBLIC__app__commerce__api__organizationId=prod-org-id
PUBLIC__app__commerce__api__shortCode=prod-short-code
```

- `PUBLIC__` variables baked into app at build time
- `.env` files are local dev only (not deployed)
- Server-only secrets set without `PUBLIC__` prefix

## Page Designer Cartridge

Deployed separately to Commerce Cloud (not MRT):

```bash
pnpm generate:cartridge        # Generate metadata JSON
pnpm deploy:cartridge          # Deploy to B2C instance
pnpm deploy:cartridge:clean    # Remove old + deploy fresh
pnpm validate:cartridge        # Validate structure
```

Cartridge metadata also auto-generated during `pnpm build`.

## Pre-Deployment Checklist

1. `pnpm test` — all tests pass
2. `pnpm bundlesize:test` — bundle within limits
3. Verify environment variables set in target environment
4. `pnpm build` — completes without errors
5. Verify SCAPI credentials match target environment

## Development Commands

```bash
pnpm dev              # Dev server with HMR
pnpm build            # Production build
pnpm push             # Deploy to MRT
pnpm test             # Run tests
pnpm typecheck        # TypeScript check
pnpm lint             # ESLint
pnpm storybook        # Component dev
pnpm bundlesize:test  # Check bundle limits
pnpm lighthouse:ci    # Lighthouse audit
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Build fails | TypeScript errors | Fix type errors; `pnpm typecheck` |
| Push rejected | Auth issue | Verify sfnext CLI credentials |
| 500 after deploy | Missing env vars | Check required vars in MRT dashboard |
| Stale PD components | Cartridge not deployed | Re-deploy cartridge |
