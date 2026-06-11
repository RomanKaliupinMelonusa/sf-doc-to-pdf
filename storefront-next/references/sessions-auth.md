# Sessions and Authentication

> Source: https://developer.salesforce.com/docs/commerce/pwa-kit-managed-runtime/guide/sfnext-storage-sessions.html

**Mental model:** Server-only auth. All SLAS token management happens in `auth.server.ts` middleware on every request. Tokens never reach browser. Client gets non-sensitive `PublicSessionData` via `useAuth()`. Cookie-based, per-request JWT validation, automatic refresh/guest-login.

## Architecture

1. **Server middleware** (`middlewares/auth.server.ts`) — runs every request, reads/validates/refreshes auth cookies, writes `Set-Cookie`
2. **React context** (`providers/auth.tsx`) — exposes `PublicSessionData` (no tokens) via `useAuth()`

Route modules use only server `loader`/`action` — **never** `clientLoader`/`clientAction`.

## Cookie Architecture

All auth cookies are `HttpOnly`. Client JS cannot access them.

| Cookie | Purpose | User Type | Expiry |
|--------|---------|-----------|--------|
| `cc-nx-g` | Guest refresh token | Guest | 30 days max |
| `cc-nx` | Registered refresh token | Registered | 90 days max |
| `cc-at` | Access token | Both | JWT `exp` |
| `usid` | User session ID | Both | Refresh expiry |
| `enc_user_id` | Encoded user ID | Registered | Refresh expiry |
| `dw_dnt` | Tracking consent | Both | Session |
| `dwsid` | Hybrid session bridge | Both | Session |
| `cc-cv` | PKCE code verifier | Both | 5 min |
| `cc-auth-recover` | 401-recovery loop guard | Both | 30 sec |

Key decisions:
- Only one of `cc-nx-g`/`cc-nx` exists at a time (mutual exclusion on user-type transition)
- `userType` derived from JWT (registered tokens have `rcid` claim), never stored in cookie
- Cookies namespaced with `siteId` (e.g., `cc-nx_RefArch`) except `dwsid`/`dw_dnt`
- Cookie domain configurable via `cookies.domain` in site config

## Accessing Session Data

### Server (loaders, actions, middleware)
```typescript
import { getAuth } from '@/middlewares/auth.server';

export async function loader({ context }: LoaderFunctionArgs) {
  const auth = getAuth(context);
  // auth.accessToken, auth.customerId, auth.userType, auth.usid
}
```

### Client (components)
```typescript
import { useAuth } from '@/providers/auth';

function Component() {
  const auth = useAuth(); // PublicSessionData | undefined
  // auth.userType, auth.customerId — NO tokens
}
```

## Updating Auth (Login)

```typescript
import { updateAuth, loginRegisteredUser } from '@/middlewares/auth.server';

export async function action({ request, context }: ActionFunctionArgs) {
  const tokenResponse = await loginRegisteredUser(context, email, password);
  updateAuth(context, tokenResponse);
  return redirect('/account');
}
```

## Destroying Auth (Logout)

```typescript
import { destroyAuth } from '@/middlewares/auth.server';
destroyAuth(context); // clears all auth cookies on response
return redirect('/');
```

## 401 Recovery

When SCAPI returns 401 (non-SLAS endpoint), middleware catches `AuthTokenInvalidError`, clears stale state, re-runs refresh/guest flow, issues 307 redirect with `x-sfnext-auth-recovery: 1` header. Guard cookie prevents loops (30s TTL).

## Configuration

```bash
PUBLIC_COMMERCE_API_GUEST_REFRESH_TOKEN_EXPIRY_SECONDS=2592000      # max 30 days
PUBLIC_COMMERCE_API_REGISTERED_REFRESH_TOKEN_EXPIRY_SECONDS=7776000 # max 90 days
```

Cookie domain (share across subdomains):
```typescript
// config.server.ts → app.commerce.sites
sites: [{ id: 'RefArch', cookies: { domain: '.example.com' }, ... }]
```

## Rules

- Never expose tokens to client — use `useAuth()` for non-sensitive data only
- Route-level auth checks go in server `loader`, not client guards
- `customerId` is derived per-request from JWT, not stored in cookie
- For auth-gated routes, branch inside loader: `if (auth.userType !== 'registered') throw redirect('/login')`
