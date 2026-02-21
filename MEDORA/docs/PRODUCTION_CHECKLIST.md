# MEDORA – Production readiness checklist

## What’s in place

- **Error boundary** – React ErrorBoundary wraps the app; unhandled render errors show a fallback and “Try again”.
- **API client** – 60s timeout, `AbortController`, clear messages for timeout/network errors.
- **CORS** – Backend reads `CORS_ORIGINS` (comma-separated) from env; defaults to localhost for dev.
- **Trust / legal** – Disclaimer, “Powered by AI”, “Your data is private”, “Emergency? Call 911”.
- **UI** – Some `aria-label` and `role` usage; responsive layout and bottom nav on mobile.

## Before going to production

### Must-have

1. **Auth** – Backend has no auth. Add auth (e.g. JWT or session) if users or PII are involved.
2. **CORS** – Set `CORS_ORIGINS` to your real frontend origin(s), e.g. `https://app.medora.example.com`.
3. **API URL** – Set `VITE_API_BASE_URL` in the frontend build to your backend URL.
4. **Secrets** – No API keys in frontend; keep `GEMINI_API_KEY` and similar only in backend env.
5. **HTTPS** – Serve frontend and backend over HTTPS in production.

### Should-have

6. **Rate limiting** – Add backend rate limiting (e.g. per IP or per user) to protect LLM endpoints.
7. **Input validation** – Backend already uses Pydantic; tighten limits (e.g. `query` length, `context` size, image size).
8. **Logging / monitoring** – Backend logs; add error tracking (e.g. Sentry) and health/uptime checks.
9. **Accessibility** – Run an a11y audit (e.g. axe, Lighthouse) and fix to WCAG AA where required.
10. **Tests** – Add at least: API client + key user flows (e.g. chat send); backend route tests.

### Nice-to-have

11. **Request IDs** – Correlate frontend requests with backend logs.
12. **Analytics** – Privacy-preserving usage/errors if needed for product.
13. **Feature flags** – For gradual rollout or A/B tests.
14. **E2E tests** – Playwright/Cypress for critical paths.

## Summary

The app is **suitable for demos and internal use**. For **public production** (real users, health-related use), add auth, tighten CORS/env, add rate limiting and validation, then monitoring and tests.
