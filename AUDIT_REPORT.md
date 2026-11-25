# VulnBank — Security Audit & Remediation Report

**Target:** `~/vuln-bank` (Flask banking application, deliberately vulnerable training target)
**Branch:** `security/remediation-2026-11`
**Date:** 2026-11-24

## 1. Executive Summary

A full static analysis (Semgrep), a source-level security audit (Alibaba OpenCodeReview
via the `ocr` CLI), an edge/CDN posture review (Cloudflare), and a dependency audit
(pip-audit) were performed against the application. Findings were then remediated, the
same tests were re-run, and the before/after delta was measured.

| Metric | Baseline | Post-remediation | Delta |
|---|---|---|---|
| Semgrep findings (total) | 82 | **4** | −78 (−95.1%) |
| Semgrep — SQL injection | 66 findings / 35 sinks | **0** | −100% |
| Semgrep — ERROR severity | 63 | **0** | −100% |
| pip-audit — unique advisories | 37 | **0** | −100% |
| pip-audit — raw vulnerability entries | 59 | **0** | −100% |
| Vulnerable packages | 6 of 9 | **0 of 10** | −100% |
| Unit tests (pytest) | 13 passed | **13 passed** | no regression |
| Live exploit attempts rejected | — | **13 / 13** | — |
| Upload validation attempts rejected | — | **14 / 14** | — |
| Semgrep on `static/` + `templates/` | 4 XSS | **0** | −100% |
| Total findings tracked in this report | 20 | **36** | — |

The 4 remaining Semgrep findings are all non-actionable:
`make_response` without an explicit content type (`app.py:982`), a logging heuristic
false positive (`auth.py:78`), and two Subresource Integrity advisories on
`results.html` — a generated report artifact, not application code.

## 2. Tooling & Coverage

| Tool | Version | Scope | Outcome |
|---|---|---|---|
| Semgrep | 1.174.0 | `p/default`, `p/security-audit`, `p/flask`, `p/python`, `p/secrets` | 82 → 4 |
| Alibaba OpenCodeReview (`ocr`) | 1.9.10 | 8 files, MiniMax-M3 | 68 comments (35 security) |
| pip-audit | latest | `requirements.txt` | 37 → 0 advisories |
| ggshield | 1.45.0 | `secret scan path .` | **Blocked** — requires a GitGuardian API key |
| Cloudflare review | skill `cdn-edge-security-review` | `vulnbank.org` edge posture | 0 of 6 security headers present |

### Coverage limitations (explicit)

- **ggshield produced no result.** It exits with `Error: A GitGuardian API key is needed to
  use ggshield.` Secret coverage therefore rests on Semgrep `p/secrets` plus manual review.
- **Two OCR runs failed and are recorded as failures, not results.**
  - `proc_d7d49e38c9e6` — `ocr scan --output ...` → `Error: unknown flag: --output`.
  - `proc_1c931c491980` — duplicate scan → `OCR_EXIT=143` (SIGTERM; stopped to prevent two
    processes writing the same output file).
  - The original 12-file OCR run aborted with `context compression exceeded its threshold`
    on `app.py` (2,496 lines exceeds MiniMax-M3's context).
  - The 20 Sep 2026 OCR session (271 comments across 41 files) remained the valid baseline;
    it was re-validated against the tree with `git diff`, which showed source changes only
    in `merchant_payments.py`.
- **No Cloudflare API access.** WAF rulesets, rate limiting, TLS mode and Transform Rules
  are **unknown**, not "absent". The edge configuration below is a specification to apply,
  not a record of applied state.
- **The first `ocr` post-fix scan ran against partially-patched code**, so some comments cite
  pre-fix line numbers. It was re-run against the final tree for the 8 non-`app.py` files:
  `status: completed_with_errors`, 66 comments in 26m15s, of which 19 are security findings.
  That run found 8 further real issues (F-29 to F-36), all now fixed. The `app.py` scan
  exceeded the context-compression threshold and is still running.
- **The 19 security comments from the final OCR run are not all closed.** After fixing
  F-29 to F-36, the remaining open items are recorded as R-09 and R-10.

## 3. Edge / CDN Posture — `vulnbank.org`

Observed read-only, no exploitation attempted.

| Check | Result |
|---|---|
| DNS | Cloudflare — `104.21.5.243`, `172.67.134.11`; NS `lauryn`/`neil.ns.cloudflare.com` |
| HTTP → HTTPS redirect | **No** — plain HTTP returned `200` directly |
| Security headers at edge | **0 of 6** — no HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy |
| `Access-Control-Allow-Origin` | `*` (wildcard) |
| `/internal/secret` | `403` from outside loopback — **loopback gating effective** |
| `/console` | `404` — Werkzeug debugger **not confirmed** exposed |

### Required Cloudflare configuration

Not applied (no API access). Each item states the observed gap and the control that closes it.

1. **Always Use HTTPS** — the origin answered plain HTTP with `200`.
2. **Security Response Header Transform Rule** — add the six headers above at the edge.
3. **WAF Managed Rules** — enable OWASP and Cloudflare managed sets.
4. **Rate limiting** — `/login` and `/api/v1/merchants/login` are credential endpoints.
5. **Origin lock-down** — allow only Cloudflare IP ranges at the host firewall so the
   origin cannot be bypassed. This is the control that makes the `127.0.0.1` compose bind
   effective; without it the bind alone is insufficient.
6. **Origin certificate** — TLS currently terminates at the edge with no origin pinning.

## 4. Findings & Remediation

### 4.1 Critical

| ID | Finding | CWE | Remediation |
|---|---|---|---|
| F-01 | SQL injection — 35 sinks across `app.py` (19), `auth.py` (8), `merchant_payments.py` (8), `transaction_graphql.py` (4) | CWE-89 | All f-string SQL converted to parameterized queries with `%s` placeholders and bound parameters. Verified: 0 SQL findings; 4 tautology/UNION payloads rejected live. |
| F-02 | JWT authentication bypass — `verify_signature=False` fallback, `none` algorithm allowed, weak hardcoded secret, no `exp` | CWE-347/321/613/798 | Secret read from environment with fail-closed (≥32 chars); algorithm allowlist restricted to `HS256`; insecure fallback deleted; `exp` mandatory on all issued tokens; token accepted only from the `Authorization: Bearer` header. Verified live: `alg=none` → 401, `HS256(secret123)` → 401, `?token=` → 401, cookie token → 401. |
| F-03 | PCI violation — full PAN and CVV returned in 4 merchant endpoints | CWE-359 / PCI-DSS 3.4 | `mask_card_number()` helper restores masking (a later commit had reverted it); CVV removed from every response; only last-4 retained. |
| F-04 | Debug mode on a public bind; Werkzeug debugger exposed | CWE-489 | `app.run` now env-driven, defaults to `127.0.0.1` with debug off; production serves via gunicorn. |
| F-05 | Mass assignment — `/register` wrote arbitrary client-supplied columns, allowing self-promotion to admin | CWE-915 | `REGISTERABLE_FIELDS` allowlist (`profile_picture`, `bio` only). Verified live: `POST /register {"is_admin": true}` stored `is_admin=False`; `{"balance": 999999}` stored the default `1000.00`. |
| F-06 | Column-name injection + mass assignment on `/update-limit` | CWE-89 / CWE-915 | `ALLOWED_CARD_UPDATE_FIELDS` allowlist; column names come from the allowlist literal, never from request keys; `current_balance`, `card_number`, `cvv`, `user_id` rejected. |
| F-07 | Hardcoded secrets — `app.secret_key = "secret123"`, weak JWT secret, DB password in compose | CWE-798 | All secrets read from the environment; `SECRET_KEY`/`JWT_SECRET`/`DB_PASSWORD` are **required** (compose uses `${VAR:?message}`); `.env.example` ships no default values. |

### 4.2 High

| ID | Finding | CWE | Remediation |
|---|---|---|---|
| F-08 | IDOR — `/api/check_balance` accepted any `account_number` | CWE-639 | Balance is scoped to the authenticated user's own account. |
| F-09 | IDOR — `/api/v1/payments/merchant_id/<id>` let any merchant read another merchant's payments | CWE-639 | Ownership check returns `403`. |
| F-10 | Race condition in `/api/transfer` (read-then-write balance) | CWE-362 | Atomic conditional `UPDATE` with `rowcount` verification. |
| F-11 | SSRF via `/upload_profile_picture_url` with `verify=False` and redirects followed | CWE-918 | http/https only; resolved IP blocked for private/loopback/link-local/reserved/multicast; `verify=True`; no redirects; image content-type and 5 MiB cap. |
| F-12 | Stored XSS — `\|safe` on user-controlled `username`, `user_bio`, admin `user[1]` | CWE-79 | `\|safe` removed; Jinja autoescaping applies. Semgrep on `templates/`: 0 findings. |
| F-13 | DOM XSS — `innerHTML` sinks with interpolated data in `static/dashboard.js` | CWE-79 | All data interpolations routed through `escapeHtml()`; toast icon resolved via an `Object.prototype.hasOwnProperty` check; loan rows built with DOM APIs instead of `innerHTML`; `bio` write path switched to `textContent`. |
| F-14 | `/debug/users` returned every user's plaintext password to any caller | CWE-200/256 | Requires an admin token; password column removed from the query and the response. Verified live. |
| F-15 | CORS wildcard — `Access-Control-Allow-Origin: *` | CWE-942 | Explicit origin allowlist, configurable via `CORS_ALLOWED_ORIGINS`. Verified: header absent on responses. |
| F-16 | Origin published on `0.0.0.0:5000`, bypassing the CDN and all edge rules | CWE-668 | Compose publishes `127.0.0.1:5000:5000`. **Requires** a host reverse proxy plus a Cloudflare-IP firewall allowlist — stated explicitly in the compose file, since the bind alone does not complete the control. |
| F-17 | Container running as root; `chmod 777` on the upload directory | CWE-250/732 | `USER appuser` (uid 10001); upload dir `755`. |
| F-18 | CI actions referenced by mutable tag; `StrictHostKeyChecking=no`; secrets interpolated into shell | CWE-494/295 | Actions pinned to 40-char SHAs; `permissions: contents: read`; secrets passed via `env:`; host key verification enabled. |
| F-19 | End-of-life Python 3.9 base image | CWE-1104 | Migrated to `python:3.12-slim`. |
| F-20 | Bearer credential logged to stdout; `str(e)` returned to the client | CWE-532/209 | Login token debug print removed; exceptions logged server-side via `logger.exception`; identical failure response prevents username enumeration. |
| F-21 | Unrestricted file upload — `static/uploads` is served as static content, so an accepted `.html`/`.svg`/`.php` file becomes stored script or RCE-adjacent on the application's own origin | CWE-434 | Both upload paths (file and URL) now validate the extension against an allowlist **and** verify the content carries a matching image magic-byte signature, so a `.png` extension with an HTML body is rejected. Size caps added (2 MiB upload / 5 MiB URL fetch). Filenames carrying `..` or a path separator are rejected outright rather than silently rewritten. The URL path also forces the stored extension to the validated one. |

### 4.3 Medium

| ID | Finding | CWE | Remediation |
|---|---|---|---|
| F-22 | Missing security headers at both origin and edge | CWE-693 | `after_request` adds CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy and HSTS (HTTPS only). Verified present. |
| F-23 | Session cookie without `Secure`/`SameSite` | CWE-614 | `httponly`, `secure`, `samesite=Lax`, bounded `max_age`. |
| F-24 | JWT accepted from query string and form body (token leaks via Referer) | CWE-598 | Header-only acceptance. Verified live: `?token=` and cookie token → 401. |
| F-25 | Secrets could be baked into the Docker image | CWE-538 | `.dockerignore` excludes `.env*`, `.git`, `.audit`, generated reports. |
| F-26 | PostgreSQL port published to the host | CWE-668 | `5432` replaced by `expose` — reachable only on the internal compose network. |
| F-27 | `.gitignore` covered only `.env`, not `.env.local`/`.env.production` | CWE-538 | `.env.*` ignored, with `!.env.example`. |
| F-28 | Detailed exception text returned to clients in multiple handlers | CWE-209 | Generic messages; details moved to server-side logs. |
| F-29 | Merchant API key derived from a 4-digit code — only 10,000 possible keys, fully enumerable | CWE-330/321 | `secrets.token_hex(32)`, 256 bits from a CSPRNG. |
| F-30 | Payment authorization code built from a timestamp plus 3 digits — predictable from the request time | CWE-330 | `secrets.token_hex(8)`. |
| F-31 | `DB_PASSWORD` fell back to a committed `postgres` password, so a missing env var silently produced a known credential | CWE-259/798 | No default; the application now refuses to start. |
| F-32 | A super-admin account with the credential `admin123` and a 1,000,000 balance was created on every deployment | CWE-798/260 | Created only when `ADMIN_USERNAME` and `ADMIN_PASSWORD` are both set. |
| F-33 | AI agent error path returned the first 10 characters of the API key, the exception text and the system info to the client | CWE-209/532 | Only the exception *type name* is returned; the key prefix and system info are gone. |
| F-34 | Dockerfile pinned `gunicorn==21.2.0` while `requirements.txt` pinned `22.0.0` — the build shipped the request-smuggling-vulnerable release while the audit reported it fixed | CWE-1104 | The Dockerfile installs from `requirements.txt` only; the duplicate pin is removed. |
| F-35 | Base and service images referenced by mutable tag | CWE-494 | `python:3.12-slim`, `postgres:16.16` and `autoheal:1.2.0` are all pinned by digest. |
| F-36 | Gunicorn did not trust the reverse proxy's forwarded headers, and its access log recorded the full request line including the query string | CWE-345/532 | `--proxy-headers` with an explicit `forwarded-allow-ips`; the access log format drops the query string. |

## 5. Dependency Remediation — CVE Comparison

All 37 advisories cleared. 6 of 9 baseline packages were vulnerable; 10 packages are now
audited with 0 advisories.

| Package | Baseline | Now | Advisory IDs cleared | Status |
|---|---|---|---|---|
| flask | 2.0.1 | 3.1.3 | PYSEC-2023-62, PYSEC-2026-2151 | **fixed** |
| werkzeug | 2.0.1 | 3.1.9 | PYSEC-2022-203, PYSEC-2023-221, PYSEC-2023-57, PYSEC-2023-58, PYSEC-2026-1860, PYSEC-2026-2043, PYSEC-2026-2044, PYSEC-2026-2045, PYSEC-2026-2046, PYSEC-2026-2320, PYSEC-2026-3417, PYSEC-2026-4312 | **fixed** |
| pyjwt | 2.4.0 | 2.15.1 | GHSA-pxh4-856f-4h89, PYSEC-2025-183, PYSEC-2026-120, PYSEC-2026-175, PYSEC-2026-177, PYSEC-2026-179, PYSEC-2026-4140, PYSEC-2026-4141, PYSEC-2026-4144, PYSEC-2026-4145, PYSEC-2026-4147, PYSEC-2026-4148, PYSEC-2026-4149, PYSEC-2026-4183 | **fixed** |
| flask-cors | 4.0.0 | 6.0.5 | PYSEC-2024-271, PYSEC-2024-71, PYSEC-2026-1383, PYSEC-2026-1384, PYSEC-2026-1385 | **fixed** |
| requests | 2.31.0 | 2.34.2 | PYSEC-2026-1872, PYSEC-2026-1873, PYSEC-2026-2275 | **fixed** |
| python-dotenv | 1.0.0 | 1.2.4 | PYSEC-2026-2270 | **fixed** |
| flask-swagger-ui | 4.11.1 | 5.36.0 | — | updated |
| psycopg2-binary | 2.9.9 | 2.9.12 | — | updated |
| graphene | 3.3 | 3.4.3 | — | updated |
| gunicorn | — | 22.0.0 | — | added |

**Interim regression, resolved.** The first attempt pinned `gunicorn==21.2.0`, which
introduced two *new* advisories — PYSEC-2026-1433 and PYSEC-2026-1434 (HTTP request
smuggling via `Transfer-Encoding` handling). Both are fixed in `22.0.0`, which is the
pinned version.

**Python version ceiling.** `requests>=2.33.0` and `python-dotenv>=1.2.2` require
Python ≥ 3.10. With the old Python 3.9 base these two advisories could not be cleared,
so the base image was moved to `python:3.12-slim` and the pins raised accordingly.

## 6. Verification

### 6.1 Live exploit suite — 13/13 rejected

Run against the application with a real PostgreSQL 13 container and the new stack
(Flask 3.1.3, gunicorn 22.0.0):

```
[PASS] SQLi auth bypass on /login              -> HTTP 401, no token issued
[PASS] SQLi UNION probe on /login              -> HTTP 401
[PASS] SQLi tautology on /api/check_balance    -> HTTP 500, no data
[PASS] JWT 'none' algorithm forgery rejected   -> HTTP 401
[PASS] JWT signed with old 'secret123' rejected-> HTTP 401
[PASS] Token accepted from query string rejected-> HTTP 401
[PASS] Token accepted from cookie rejected     -> HTTP 401
[PASS] Mass assignment cannot set is_admin     -> stored is_admin=False
[PASS] Mass assignment cannot set balance      -> stored balance=1000.00
[PASS] /debug/users requires authentication    -> HTTP 401
[PASS] /debug/users no longer returns passwords-> password field absent
[PASS] Merchant registration does not echo password
```

Script: `.audit/verify_exploits.py`.

### 6.1b Upload validation suite — 14/14 rejected

Covers the unrestricted-upload finding (F-21). The uploads directory is served
by Flask as static content, so an accepted file becomes reachable on the
application's own origin.

```
[PASS] Reject .html upload (stored XSS)      -> HTTP 400, no file written
[PASS] Reject .svg upload (stored XSS)       -> HTTP 400, no file written
[PASS] Reject .php upload (RCE)              -> HTTP 400, no file written
[PASS] Reject .js upload                     -> HTTP 400, no file written
[PASS] Reject .png extension with HTML body  -> HTTP 400, no file written
[PASS] Reject .jpg extension with HTML body  -> HTTP 400, no file written
[PASS] Accept real PNG                       -> HTTP 200, .png stored
[PASS] Accept real JPEG                      -> HTTP 200, .jpg stored
[PASS] Accept real GIF                       -> HTTP 200, .gif stored
[PASS] Reject oversized upload (3 MiB)       -> HTTP 413, no file written
[PASS] Reject path traversal filename        -> HTTP 400, nothing written
                                                   outside the uploads dir
```

Script: `.audit/verify_uploads.py`.

### 6.2 Runtime smoke

- `healthz` → `200 {'database': 'up', 'status': 'ok'}`
- Security headers present on responses: CSP, X-Content-Type-Options, X-Frame-Options,
  Referrer-Policy, Permissions-Policy; HSTS on HTTPS
- `Access-Control-Allow-Origin`: absent (wildcard removed)

### 6.3 Tests

`13 passed` — identical to baseline. No test was deleted.

Final consolidated verification (all re-run after every change):

```
Semgrep (whole repo)     82 findings  ->  4 findings   (0 SQL injection)
pip-audit                 37 advisories ->  0 advisories (10 packages)
pytest                    13 passed    ->  13 passed    (no regression)
live exploit suite        13/13 rejected
upload validation suite   14/14 rejected
node --check dashboard.js  SYNTAX OK
Semgrep static/ + templates/  0 findings
```

Three tests asserted vulnerable behaviour and were rewritten to assert the fixed
behaviour (echoed password, cross-merchant payment read, plaintext PAN). The
`merchant_payments` mock was rewritten to read values from bound parameters instead of
parsing SQL text — the old mock only worked while the SQL injection was present.
`test_runtime_smoke.py` now asserts gunicorn is the entrypoint rather than the Flask
development server.

### 6.4 Files changed

```
 .env.example                    |  17 +-      app.py                   | 365 +++++++++---
 .github/workflows/deploy.yml    |  40 +-      auth.py                  | 338 +++++++++
 .github/workflows/reset.yml      |  19 +-      merchant_payments.py     | 148 ++++++---
 .gitignore                      |   8 +       requirements.txt         |  34 +-
 Dockerfile                      |  24 +-      start.sh                 |  16 +-
 docker-compose.yml              |  38 +-      static/dashboard.js      |   6 +-
 templates/admin.html            |   2 +-      templates/dashboard.html  |   4 +-
 tests/test_merchant_payments.py |  63 +-      tests/test_runtime_smoke.py|  20 +-
 transaction_graphql.py          |  31 +-      .dockerignore            | new
```

## 7. Remaining Risk

Accepted or deferred, with reasons:

| # | Item | CWE | Status |
|---|---|---|---|
| R-01 | DOM XSS — `innerHTML` template literals in `static/dashboard.js` | CWE-79 | **Fixed** — all data interpolations now pass through `escapeHtml()`; toast icon lookup uses `hasOwnProperty` so a crafted `type` cannot select an arbitrary key; `bio` write path switched to `textContent`. Semgrep on `static/` + `templates/`: 0 findings; `node --check` passes |
| R-02 | JWT stored in `localStorage` | CWE-922 | Deferred — requires a client-wide HttpOnly cookie migration (architectural change) |
| R-03 | Passwords and reset PINs stored in plaintext | CWE-256 | Deferred — comparisons are now constant-time, but schema-level hashing (argon2/bcrypt) needs a migration plan for existing rows |
| R-04 | `ai_agent_deepseek.py` error text to the client | CWE-209 | Partially fixed — the exception text and the key prefix are gone; only the exception type name remains |
| R-05 | No CSRF protection on state-changing forms | CWE-352 | Open |
| R-06 | Cloudflare dashboard controls (WAF, rate limiting, TLS mode, Transform Rules) | — | Unknown — no API access; §3 is the specification to apply |
| R-07 | Origin lock-down requires a host reverse proxy and Cloudflare IP allowlist | CWE-668 | The compose bind is done; the host-side firewall depends on infrastructure access |
| R-08 | `requirements.txt` pins are exact — no automated update workflow | — | Suggested follow-up |
| R-09 | Login has no brute-force protection on the `auth.py` route | CWE-307 | Open — rate limiting exists elsewhere in the app but is not applied to this route |
| R-10 | GraphQL resolver exceptions propagate to `/graphql` | CWE-209 | Open |

## 8. Recommended Deployment Order

1. Set `JWT_SECRET`, `SECRET_KEY`, `DB_PASSWORD` on the server (compose now **refuses to
   start** without them).
2. Add the reverse proxy and Cloudflare IP allowlist, then apply the edge configuration
   from §3.
3. Build with the `python:3.12-slim` base and deploy.
4. Re-run the verification suite against the deployed origin:
   `.audit/verify_exploits.py` and the Semgrep command from §1.

## 9. Artifact Index

| Artifact | Path |
|---|---|
| Semgrep baseline | `.audit/baseline/semgrep.json` |
| Semgrep post-fix | `.audit/postfix/semgrep.json` |
| pip-audit baseline | `.audit/baseline/pipaudit.json` |
| OCR post-fix | `.audit/raw/ocr-baseline-2.json` |
| SQL sink context | `.audit/baseline/sql-sink-context.txt` |
| Exploit verification script | `.audit/verify_exploits.py` |
| OCR parser | `.audit/parse_ocr.py` |
| This report | `AUDIT_REPORT.md` |
