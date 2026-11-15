# vuln-bank — Consolidated Security Audit Report

**Target:** `/home/rafael/vuln-bank` — intentionally-vulnerable Flask banking app running on `http://localhost:5000`  
**Date:** 2026-08-23  
**Scope:** Full source tree (Python, templates, JS, Dockerfile, CI workflows, GraphQL)  
**Author:** Combined SAST scan — Semgrep OSS 1.174.0 + OCR (LLM via MiniMax-M3) + Frieren DAST-AI

---

## Executive Summary

### Headline numbers

| Tool | Type | Files scanned | Findings | Notable outcome |
|---|---|---|---|---|
| **Semgrep OSS 1.174.0** | Static AST | 8 | **47** (37 ERROR / 10 WARNING) | 33 SQLi sinks confirmed across 3 files |
| **OCR (open-code-review 1.9.10)** + MiniMax-M3 | LLM code review | 6 Python | **67** (23 critical / 17 high / 22 medium / 5 low) | PCI, JWT alg=none, race conditions, IDOR, plaintext passwords |
| **Frieren DAST-AI** | Runtime black-box | 17 endpoints crawled | **0** (could not authenticate) | needs `--auth-url/--username/--password` to be useful |
| **ggshield** | Secret detection | n/a | n/a | deferred — auth not completed |

### The 6 vulnerabilities that actually matter

Ranked by real-world impact, not by tool confidence. Each is corroborated by source-code evidence (Semgrep), logic analysis (OCR), or both.

1. **`merchant_payments.py` returns full PAN + CVV in 4 API endpoints** *(OCR, critical)* — violates PCI-DSS requirement 3.2. Any merchant calling these endpoints exfiltrates customer card data to their logs.
2. **`auth.py` accepts JWT `alg=none` tokens** *(OCR, critical)* — combined with the hardcoded secret `"secret123"` and the `verify_signature=False` fallback at L47, any attacker can forge admin tokens. CVSS-effective ~9.8.
3. **`auth.py` transfer has a TOCTOU race condition** *(OCR, high)* — SELECT balance then UPDATE in separate statements (L185/L190). Concurrent requests can each pass the balance check and collectively overdraw the account.
4. **`merchant_payments.py` API key derived from a 4-digit code with `random.choices`** *(OCR, critical)* — only 10,000 possibilities; an attacker who knows the derivation can enumerate all valid merchant API keys offline.
5. **33 SQL injection sinks via f-string concatenation** *(Semgrep + OCR, critical)* — `username`, `password`, `account_number`, `card_id`, `merchant_id`, `api_key`, `email` are concatenated directly into SQL strings. Auth bypass via `admin' --` on login is trivial.
6. **`app.py:2496` runs Flask with `host=0.0.0.0, debug=True`** *(Semgrep + OCR, high)* — Werkzeug interactive debugger reachable from any network the container is on. Historically used for unauthenticated RCE.

---

## 1. Methodology

| Tool | Version | Configuration | What it covers |
|---|---|---|---|
| Semgrep OSS | 1.174.0 | `p/python p/owasp-top-ten p/security-audit p/secrets p/flask p/jwt p/sql-injection p/command-injection p/insecure-transport p/cwe-top-25` | AST-based static analysis with CWE mapping |
| OCR | 1.9.10 | Provider `minimax`, model `MiniMax-M3`, endpoint `https://api.minimax.io/v1` | LLM code review, scoped to Python files only |
| Frieren DAST-AI | main @ 1.0.0 | `AI_PROVIDER=openai`, `OPENAI_BASE_URL=https://api.minimax.io/v1` | Black-box runtime scan via Playwright + 8 LLM-driven attack agents |
| ggshield | 1.45.0 | n/a (auth incomplete) | Sends file contents to GitGuardian cloud |

### Important caveats

- **OCR was scoped to Python files.** It did not review Jinja2 templates, static JavaScript, Dockerfile, or CI workflows. Findings in those areas come from Semgrep only.
- **Frieren ran without credentials.** Every login/register/api-docs endpoint was marked `attack_skip: no_injectable_parameters`. Its 0 findings reflect a coverage gap, not a clean app.
- **ggshield was not run.** It needs `ggshield auth login` to complete interactively before any scan will run.

---

## 2. Vulnerability Classes — Combined Cross-Tool View

| # | Vulnerability Class | CWE | Semgrep hits | OCR hits | Where |
|---|---|---|---|---|---|
| 1 | SQL Injection (f-string concatenation) | CWE-89 | 33 | 10 | `app.py`, `auth.py`, `merchant_payments.py`, `transaction_graphql.py` |
| 2 | Hardcoded credentials | CWE-798 | 1 | 4 | `auth.py:29` JWT secret; `database.py` DB password fallback; admin seed `admin123` |
| 3 | JWT signature bypass / `alg=none` | CWE-347 | 1 | 2 | `auth.py:47` `verify_signature=False`; alg-allowlist includes `none` |
| 4 | Cryptographically-insecure random | CWE-338 | 0 | 2 | `random.choices` for card numbers, CVVs, account numbers, API keys |
| 5 | Race condition / TOCTOU | CWE-362 | 0 | 3 | `auth.py` transfer; `merchant_payments.py` charge; `app.py` rate-limit check |
| 6 | Stored XSS via Jinja2 `\|safe` | CWE-79 | 3 | 0 | `templates/dashboard.html:81,166`; `templates/admin.html:219` |
| 7 | Sensitive info in responses (incl. PCI) | CWE-200 / CWE-312 | 0 | 4 | Login echoes account_number + IP + UA; merchant `/me` echoes API key; charge/list returns full PAN+CVV |
| 8 | IDOR / BOLA | CWE-639 | 0 | 3 | `/api/v1/payments/<merchant_id>` cross-merchant; `/virtual_cards/<id>` no ownership check |
| 9 | Missing token expiration | CWE-613 | 0 | 2 | User JWT and merchant JWT both issued without `exp` |
| 10 | Insecure TLS validation | CWE-295 | 1 | 1 | `app.py:707` `verify=False` on image proxy |
| 11 | Debug mode + bind 0.0.0.0 | CWE-489 | 2 | 1 | `app.py:2496` `app.run(host=0.0.0.0, debug=True)` |
| 12 | Mutable CI action tag (supply chain) | CWE-829 | 3 | 0 | `.github/workflows/deploy.yml:20,23`; `.github/workflows/reset.yml:36` |
| 13 | Missing container USER | CWE-250 | 1 | 0 | `Dockerfile:29` no `USER` directive |
| 14 | Insecure cookie attributes | CWE-614 | 1 | 0 | `app.py:430` cookie without `Secure` or `SameSite` |
| 15 | Plaintext password storage | CWE-256 | 0 | 2 | `merchant_payments.py` registration + login compare verbatim |
| 16 | No idempotency / replay protection | CWE-863 | 0 | 1 | `merchant_payments.py` charge re-processes on `merchant_order_id` reuse |
| 17 | Loss of traceback (`raise e`) | CWE-754 | 0 | 4 | `database.py` (4 sites) |
| 18 | Bare `except:` swallowing SystemExit | CWE-396 | 0 | 2 | `app.py`, `auth.py` |

---

## 3. Findings by File

Each file section shows Semgrep findings as a compact table and OCR findings as a compact list. Full code-context snippets for every finding are in `OCR_FINDINGS.md` and `SEMGREP_REPORT.md`.

### `.github/workflows/deploy.yml`  —  Semgrep 2 · OCR 0

<details><summary><strong>Semgrep findings (2)</strong></summary>

| Line | Sev | Rule | CWE | Message |
|---|---|---|---|---|
| 20 | WARNING | `github-actions-mutable-action-tag` | CWE-1357: Reliance on Insufficiently Trustworthy Component, CWE-353: Missing Support for Integrity Check | GitHub Actions step uses a mutable tag or branch reference. Tags and branch names can be silently repointed by the actio… |
| 23 | WARNING | `github-actions-mutable-action-tag` | CWE-1357: Reliance on Insufficiently Trustworthy Component, CWE-353: Missing Support for Integrity Check | GitHub Actions step uses a mutable tag or branch reference. Tags and branch names can be silently repointed by the actio… |

</details>


### `.github/workflows/reset.yml`  —  Semgrep 1 · OCR 0

<details><summary><strong>Semgrep findings (1)</strong></summary>

| Line | Sev | Rule | CWE | Message |
|---|---|---|---|---|
| 36 | WARNING | `github-actions-mutable-action-tag` | CWE-1357: Reliance on Insufficiently Trustworthy Component, CWE-353: Missing Support for Integrity Check | GitHub Actions step uses a mutable tag or branch reference. Tags and branch names can be silently repointed by the actio… |

</details>


### `Dockerfile`  —  Semgrep 1 · OCR 0

<details><summary><strong>Semgrep findings (1)</strong></summary>

| Line | Sev | Rule | CWE | Message |
|---|---|---|---|---|
| 29 | ERROR | `missing-user` | CWE-250: Execution with Unnecessary Privileges | By not specifying a USER, a program in the container may run as 'root'. This is a security hazard. If an attacker can co… |

</details>


### `ai_agent_deepseek.py`  —  Semgrep 0 · OCR 2

<details><summary><strong>OCR findings (2)</strong></summary>

- **[HIGH/bug]** The `except` clause only catches `requests.exceptions.RequestException`, but the success branch performs unguarded dict/list access on the response JSON. If the API returns HTTP 200 with malformed JSON (`response.json()` raises `json.JSONDecodeError`), with `choices` missing or empty (`KeyError`/`IndexError`), or with a different schema, the except...
- **[MEDIUM/security]** Even though the SQL parameter is bound, the `%` wildcards are inserted inside the parameter value (`f"%{word}%"`), so any `%` or `_` characters in the user-controlled `word` from `message.split()` are interpreted as SQL LIKE wildcards. An attacker can supply `%` (match all) or `_` (match single char) to enumerate usernames far more efficiently than...

</details>


### `app.py`  —  Semgrep 23 · OCR 10

<details><summary><strong>Semgrep findings (23)</strong></summary>

| Line | Sev | Rule | CWE | Message |
|---|---|---|---|---|
| 395 | ERROR | `tainted-sql-string` | CWE-704: Incorrect Type Conversion or Cast | Detected user input used to manually construct a SQL string. This is usually bad practice because manual construction co… |
| 430 | WARNING | `secure-set-cookie` | CWE-614: Sensitive Cookie in HTTPS Session Without 'Secure' Attribute | Found a Flask cookie with insecurely configured properties.  By default the secure, httponly and samesite ar configured … |
| 506 | ERROR | `tainted-sql-string` | CWE-704: Incorrect Type Conversion or Cast | Detected user input used to manually construct a SQL string. This is usually bad practice because manual construction co… |
| 600 | ERROR | `tainted-sql-string` | CWE-704: Incorrect Type Conversion or Cast | Detected user input used to manually construct a SQL string. This is usually bad practice because manual construction co… |
| 707 | ERROR | `disabled-cert-validation` | CWE-295: Improper Certificate Validation | Certificate verification has been explicitly disabled. This permits insecure connections to insecure servers. Re-enable … |
| 1147 | ERROR | `tainted-sql-string` | CWE-704: Incorrect Type Conversion or Cast | Detected user input used to manually construct a SQL string. This is usually bad practice because manual construction co… |
| 1174 | ERROR | `tainted-sql-string` | CWE-704: Incorrect Type Conversion or Cast | Detected user input used to manually construct a SQL string. This is usually bad practice because manual construction co… |
| 1273 | ERROR | `tainted-sql-string` | CWE-704: Incorrect Type Conversion or Cast | Detected user input used to manually construct a SQL string. This is usually bad practice because manual construction co… |
| 1323 | ERROR | `tainted-sql-string` | CWE-704: Incorrect Type Conversion or Cast | Detected user input used to manually construct a SQL string. This is usually bad practice because manual construction co… |
| 1371 | ERROR | `tainted-sql-string` | CWE-704: Incorrect Type Conversion or Cast | Detected user input used to manually construct a SQL string. This is usually bad practice because manual construction co… |
| 1601 | ERROR | `tainted-sql-string` | CWE-704: Incorrect Type Conversion or Cast | Detected user input used to manually construct a SQL string. This is usually bad practice because manual construction co… |
| 1651 | ERROR | `tainted-sql-string` | CWE-704: Incorrect Type Conversion or Cast | Detected user input used to manually construct a SQL string. This is usually bad practice because manual construction co… |
| 1696 | ERROR | `tainted-sql-string` | CWE-704: Incorrect Type Conversion or Cast | Detected user input used to manually construct a SQL string. This is usually bad practice because manual construction co… |
| 1748 | ERROR | `tainted-sql-string` | CWE-704: Incorrect Type Conversion or Cast | Detected user input used to manually construct a SQL string. This is usually bad practice because manual construction co… |
| 1780 | ERROR | `tainted-sql-string` | CWE-704: Incorrect Type Conversion or Cast | Detected user input used to manually construct a SQL string. This is usually bad practice because manual construction co… |
| 1839 | ERROR | `tainted-sql-string` | CWE-704: Incorrect Type Conversion or Cast | Detected user input used to manually construct a SQL string. This is usually bad practice because manual construction co… |
| 2041 | ERROR | `tainted-sql-string` | CWE-704: Incorrect Type Conversion or Cast | Detected user input used to manually construct a SQL string. This is usually bad practice because manual construction co… |
| 2078 | ERROR | `tainted-sql-string` | CWE-704: Incorrect Type Conversion or Cast | Detected user input used to manually construct a SQL string. This is usually bad practice because manual construction co… |
| 2085 | ERROR | `tainted-sql-string` | CWE-704: Incorrect Type Conversion or Cast | Detected user input used to manually construct a SQL string. This is usually bad practice because manual construction co… |
| 2117 | ERROR | `tainted-sql-string` | CWE-704: Incorrect Type Conversion or Cast | Detected user input used to manually construct a SQL string. This is usually bad practice because manual construction co… |
| 2231 | ERROR | `tainted-sql-string` | CWE-704: Incorrect Type Conversion or Cast | Detected user input used to manually construct a SQL string. This is usually bad practice because manual construction co… |
| 2496 | WARNING | `avoid_app_run_with_bad_host` | CWE-668: Exposure of Resource to Wrong Sphere | Running flask app with host 0.0.0.0 could expose the server publicly.… |
| 2496 | WARNING | `debug-enabled` | CWE-489: Active Debug Code | Detected Flask app with debug=True. Do not deploy to production with this flag enabled as it will leak sensitive informa… |

</details>

<details><summary><strong>OCR findings (10)</strong></summary>

- **[CRITICAL/security]** Hardcoded secret key violates CWE-798. The Flask secret_key should be loaded from a secure environment variable or secrets manager; baking it into source code allows session/JWT forgery if the source is leaked, and applies to every deployment using this image.
- **[CRITICAL/security]** `random.choices` is not cryptographically secure (CWE-338). Card numbers, CVVs and account numbers are security-sensitive identifiers and must be generated with the `secrets` module; otherwise an attacker who observes a few outputs can predict subsequent values and forge valid payment instruments or accounts.
- **[CRITICAL/security]** The `/internal/secret` route trusts `request.remote_addr == '127.0.0.1'` to gate exposure of `app.secret_key`, `auth.JWT_SECRET` and DB credentials, but the SSRF in `/upload_profile_picture_url` (no scheme/host allowlist, redirects enabled, `verify=False`) lets any authenticated user make the server issue a request to itself. The chained effect is ...
- **[CRITICAL/security]** Running with `debug=True` while listening on `0.0.0.0` exposes the Werkzeug interactive debugger, which has historically been a vector for arbitrary code execution via debugger PIN brute force / PIN leak (CWE-489). For any non-local deployment this is unsafe regardless of the rest of the application posture.
- **[HIGH/security]** Module-level mutable `defaultdict` used as rate-limit storage is racy and not thread/process safe. The `check_rate_limit` function performs a TOCTOU (sum -> compare -> append) without any lock; concurrent requests can each pass the limit check and append simultaneously, and `defaultdict` itself is not thread-safe for the read-and-create pattern. Un...
- **[HIGH/security]** Plaintext JWT printed to stdout (CWE-532). Anyone with log access (or an attacker that triggers a log disclosure) can replay the token until it expires. Remove the debug print; if logging is required, log only a short prefix and never the full token.
- **[HIGH/security]** `verify=False` disables TLS certificate validation for the URL fetcher (CWE-295). This silently downgrades the SSRF surface to allow MITM-injected responses and bypasses any host-validation done later; even for a learning endpoint, this should be `True` (with a custom CA bundle if needed) so the behavior reflects what a deployed version would do.
- **[MEDIUM/maintainability]** `generate_account_number` also uses `random.choices`. Account numbers are persistent identifiers used in URLs and DB lookups and should be unpredictable and collision-resistant; switch to `secrets` and consider enforcing uniqueness at the database layer.
- **[MEDIUM/security]** Bare `except:` swallows `KeyboardInterrupt` and `SystemExit` and hides the real failure (e.g. a malformed JWT, expired token, or `verify_token` bug) behind a silent fallthrough to the unauthenticated branch. Narrow to `except Exception` and log the cause, otherwise an invalid token gives an attacker access to the lower-rate-limit branch as if they ...
- **[LOW/maintainability]** `import html` is unused; the module never calls `html.escape`. Drop the import to keep the surface minimal and avoid implying XSS sanitization is performed (the `/update_bio` route, in particular, stores raw HTML and would mislead a future reviewer who notices the import).

</details>


### `auth.py`  —  Semgrep 9 · OCR 21

**Pattern:** 7 SQL-injection sinks, all f-string style like `f"...WHERE x='VAR'..."`. The codebase has `# Vulnerability: SQL Injection possible` comments next to every one. Fix: replace with `cursor.execute("... WHERE x=?", (x,))` parameter binding.

| Line | Sink preview |
|---|---|
| 120 | `>>>  120 |         query = f"SELECT * FROM users WHERE username='{auth.get('username')}' AND password='{auth.get('password')}'"` |
| 153 | `>>>  153 |         account_number = request.args.get('account_number')` |
| 157 | `>>>  157 |         c.execute(f"SELECT username, balance FROM users WHERE account_number='{account_number}'")` |
| 185 | `>>>  185 |         c.execute(f"SELECT balance FROM users WHERE id={current_user['user_id']}")` |
| 190 | `>>>  190 |             c.execute(f"UPDATE users SET balance = balance - {amount} WHERE id={current_user['user_id']}")` |
| 191 | `>>>  191 |             c.execute(f"UPDATE users SET balance = balance + {amount} WHERE account_number='{to_account}'")` |
| 195 | `>>>  195 |             c.execute(f"SELECT username, balance FROM users WHERE account_number='{to_account}'")` |

Other Semgrep findings in this file:
- L29 [ERROR] `jwt-python-hardcoded-secret` — Hardcoded JWT secret or private key is used. This is a Insufficiently Protected Credentials weakness: https://cwe.mitre.org/data/definitions
- L47 [ERROR] `unverified-jwt-decode` — Detected JWT token decoded with 'verify=False'. This bypasses any integrity checks for the token which means the token could be tampered wit

**OCR findings (21):**

- **[CRITICAL/security]** Including 'none' in the accepted algorithm list lets an attacker forge tokens with no signature, bypassing authentication entirely (CWE-347). Restrict the allow-list to the algorithm you actually use (e.g., ['HS256']) and never accept 'none'.
- **[CRITICAL/security]** Critical auth bypass: on InvalidSignatureError the code re-decodes the token with verify_signature=False and still returns the payload. Any attacker who modifies a token (or submits a 'none'-signed token) is treated as authenticated (CWE-347). Remove the fallback entirely; an invalid signature must reject the token.
- **[CRITICAL/security]** SQL injection in login: username and password are interpolated directly into the SQL string via f-string (CWE-89). A password like "x' OR '1'='1" bypasses authentication. Use parameterized queries and never store/compare plaintext passwords (hash with bcrypt/argon2).
- **[CRITICAL/security]** SQL injection in check_balance: account_number from the query string is interpolated into SQL (CWE-89). An attacker can dump arbitrary rows or break out of the WHERE clause. Use a parameterized query.
- **[CRITICAL/security]** SQL injection in transfer: the balance read is built with f-string interpolation of current_user['user_id'] (CWE-89). Even though the value comes from the token, treating it as trusted SQL is a footgun (e.g., if the token is forged via the 'none' bug above). Use parameter binding.
- **[CRITICAL/security]** SQL injection in transfer UPDATE: both the debit (id) and credit (account_number) statements are constructed via f-strings (CWE-89). account_number comes directly from the request body and is fully attacker-controlled. Use parameter binding and an atomic UPDATE guarded by the balance check.
- **[HIGH/security]** JWT signing secret is a trivially guessable hard-coded literal ("secret123"). An attacker who guesses the source can forge tokens for any user. Load the secret from an environment variable or secret manager and use a high-entropy value (CWE-798, CWE-326).
- **[HIGH/security]** Tokens are issued without an 'exp' (expiration) claim, so any leaked or stolen token grants permanent access (CWE-613). Add an 'exp' set to a short, sensible lifetime (e.g., 15–60 minutes) and pair with a refresh-token flow.
- **[HIGH/security]** Insecure direct object reference (IDOR): any authenticated user can query any account_number with no ownership check (CWE-639). Authorize that current_user is allowed to read the requested account (e.g., compare account_number against current_user's own account, or enforce role-based access).
- **[HIGH/security]** TOCTOU race condition on funds transfer: the balance is read and then the UPDATE happens in a separate statement; concurrent requests can both pass the balance check and collectively overdraw the account (CWE-362). Wrap the debit in a single conditional UPDATE (e.g., `... WHERE id=? AND balance >= ?`) inside a transaction with the row locked, and r...
- **[HIGH/bug]** No amount validation: negative or zero amounts, NaN, or non-finite values flow straight into SQL and could credit the sender or perform a no-op transfer. Validate amount > 0 (and consider rejecting values over a daily cap). Also, decimal.Decimal is preferable to float for currency.
- **[MEDIUM/bug]** Bare 'except:' catches BaseException including KeyboardInterrupt and SystemExit, and silently swallows every error from the inner decode (CWE-396). Catch jwt exceptions explicitly and let system exceptions propagate.
- **[MEDIUM/security]** Printing exception text from token decoding can leak internal details (key material fragments, library internals) to logs/stderr and provide attackers with reconnaissance (CWE-209). Log via the logging module and either drop the message or keep it generic.
- **[MEDIUM/security]** Accepting the token from query string, form body, and cookies (in addition to Authorization) significantly increases leakage risk: URLs end up in proxy logs, browser history, Referer headers, and accidental copy-pastes (CWE-598). Restrict tokens to the Authorization header (or a Secure/HttpOnly cookie with SameSite=Strict) and never accept them in ...
- **[MEDIUM/security]** The 401 response echoes the raw exception text in 'details', which can disclose internal error information to callers (CWE-209). Return a generic message and log the real cause server-side.
- **[MEDIUM/security]** Login response leaks account_number, is_admin, and a debug_info block (login time, remote IP, User-Agent) to the client (CWE-200). Don't return internal identifiers or client metadata that an attacker doesn't need; never include IP/UA as "debug" data in a public response.
- **[MEDIUM/security]** Information disclosure in transfer response: returns recipient username and full new_balance to the caller (CWE-200). A legitimate user should only see their own new balance; revealing the recipient's balance aids reconnaissance and social engineering.
- **[MEDIUM/bug]** No self-transfer guard: a user can transfer to their own account_number, which (with the missing amount validation) is one half of a double-spend primitive. Reject transfers where to_account matches the sender's own account.
- **[LOW/bug]** 'Bearer' is matched with a substring test, so headers like 'XBearer abc' or 'NotBearer foo' are accepted as Bearer tokens (and 'abc def' is treated as a raw token). Use startswith('Bearer ') with a length check.
- **[LOW/bug]** SQLite connections are opened and closed manually; an exception between connect() and close() leaks the connection and the underlying file handle. Use a context manager (e.g., `with sqlite3.connect('bank.db') as conn:`) in every route and combine with explicit transactions.
- **[LOW/maintainability]** Suspended-account check uses positional indices (len(user) > 9 and user[9]) that depend on an undocumented schema column order. If the schema changes, this silently breaks or returns wrong data. Name columns explicitly in the SELECT (e.g., `SELECT id, username, account_number, is_admin, suspended FROM users ...`) and access by key.


### `database.py`  —  Semgrep 0 · OCR 9

<details><summary><strong>OCR findings (9)</strong></summary>

- **[HIGH/security]** Hardcoded default password: `os.getenv('DB_PASSWORD', 'postgres')` falls back to a literal credential in source. If the environment variable is unset (e.g., in production misconfiguration), the application silently authenticates with a publicly known password. Refuse to start when `DB_PASSWORD` is unset rather than providing a default.
- **[HIGH/security]** Hardcoded secrets in seed data: The admin account is created with plaintext password 'admin123', and merchants are seeded with plaintext passwords and API keys. These credentials are committed in source and would be live if init_db runs on a fresh database. Use randomized secrets generated at first install, or load them from a secrets manager.
- **[MEDIUM/error]** Original traceback lost: `raise e` re-raises the caught exception object but breaks the chain so the original traceback is discarded. Use bare `raise` (or `raise ... from e`) so the actual exception location is preserved in logs.
- **[MEDIUM/error]** Silent exception swallow hides schema errors: `except Exception: pass` discards both the "column already exists" case (expected) and real migration failures (e.g., permission errors, syntax errors with newer Postgres). At minimum log the exception; better, narrow to `psycopg2.errors.DuplicateColumn` or check `information_schema.columns` first.
- **[MEDIUM/error]** Silent exception swallow on critical migrations: Three ALTER TYPE statements are guarded by a single bare `except Exception: pass`, so if the first conversion fails the others are skipped silently. This can leave the schema half-migrated with no diagnostics. Log the exception or split each ALTER into its own guarded block.
- **[MEDIUM/error]** Original traceback lost on init failure: `raise e` discards the underlying exception's traceback, making startup failures hard to diagnose. Use bare `raise`.
- **[MEDIUM/error]** Original traceback lost in execute_query: `raise e` after rollback breaks the traceback chain, which complicates debugging at call sites. Use bare `raise`.
- **[MEDIUM/error]** Original traceback lost in execute_transaction: `raise e` after rollback discards the chained traceback. Use bare `raise`.
- **[LOW/maintainability]** Unused import: `datetime` is imported but never referenced anywhere in this module. Remove the import to keep dependencies minimal.

</details>


### `merchant_payments.py`  —  Semgrep 8 · OCR 21

**Pattern:** 8 SQL-injection sinks, all f-string style like `f"...WHERE x='VAR'..."`. The codebase has `# Vulnerability: SQL Injection possible` comments next to every one. Fix: replace with `cursor.execute("... WHERE x=?", (x,))` parameter binding.

| Line | Sink preview |
|---|---|
| 61 | `>>>   61 |         query = f"""` |
| 76 | `>>>   76 |             query = f"""` |
| 160 | `>>>  160 |             query = f"""` |
| 209 | `>>>  209 |             query = f"""` |
| 266 | `>>>  266 |             card_query = f"""` |
| 436 | `>>>  436 |             query = f"""` |
| 501 | `>>>  501 |             query = f"""` |
| 554 | `>>>  554 |             query = f"""` |

**OCR findings (21):**

- **[CRITICAL/security]** SQL injection: `api_key` comes from the `X-Merchant-Api-Key` request header (attacker-controlled) and is interpolated into the query via f-string. Use parameterized queries (`%s` placeholder) instead.
- **[CRITICAL/security]** SQL injection: `merchant_id` from the decoded JWT payload is interpolated directly. If `verify_token` ever accepts an `alg: none` token or weak secret, this becomes arbitrary SQL. Use a parameterized query.
- **[CRITICAL/security]** SQL injection on registration: `name`, `email`, and `password` are user-controlled request fields interpolated into the INSERT via f-string. Use parameterized queries.
- **[CRITICAL/security]** Plaintext password storage: passwords are inserted verbatim and compared verbatim in `login_merchant`. Hash with a slow algorithm (bcrypt/argon2) and verify via constant-time comparison. Also note that returning the raw password in `debug_info` leaks it.
- **[CRITICAL/security]** SQL injection on merchant login: `email` and `password` are attacker-controlled JSON fields interpolated via f-string. Use parameterized queries, and store/verify passwords as hashes.
- **[CRITICAL/security]** Predictable / weak API key: derived from a 4-digit code (10,000 possibilities) using `random` (not `secrets`), so trivially brute-forceable by enumerating all `vk_<sha256(0000..9999)>` hashes. Use `secrets.token_urlsafe(32)` or `secrets.token_hex(32)`.
- **[CRITICAL/security]** SQL injection on charge: `card_number` is user-controlled (from the charge request body) and is interpolated via f-string into the card lookup. Use parameterized queries.
- **[CRITICAL/security]** PCI / data-handling violation: the charge response includes the full PAN (`card_number`) and CVV of the customer card. CVV must never be stored or returned after authorization. PAN must be masked. Strip these fields from the response.
- **[CRITICAL/security]** PCI violation: GET `/api/v1/payments/<id>` returns full PAN and CVV of the customer's card. Never return CVV, and mask PAN to last4.
- **[CRITICAL/security]** PCI violation: list endpoints also leak full PAN (`card_number`) for every transaction. Mask to last4 across `list_merchant_payments` and `list_payments_by_merchant_id`.
- **[CRITICAL/security]** IDOR / authorization bypass: any authenticated merchant can list all payments of any other merchant by passing their `merchant_id` in the URL. The `@merchant_required` decorator only verifies the caller is a merchant, not that they own the resource. Enforce `merchant_id == current_merchant['id']` (or admin check) and reject otherwise.
- **[HIGH/security]** Information disclosure: the registration response echoes the user's plaintext password (and full raw request) back to the client in `debug_info`. Drop debug fields entirely from production responses.
- **[HIGH/security]** Predictable authorization code: `time.time()` seconds + 3 random digits is trivially guessable. Use `secrets.token_urlsafe`/`secrets.token_hex` instead.
- **[HIGH/security]** Race condition / non-atomic charge: SELECT (balance check), UPDATE (debit), and INSERT (transaction record) are three separate statements with no transaction wrapper. Two concurrent charges can both pass the balance check and both debit, producing a negative balance. Wrap in a single DB transaction and use a conditional `UPDATE ... WHERE current_ba...
- **[HIGH/security]** Information disclosure: the `/merchants/me` response includes the merchant's API key in `debug_info`. The API key is a long-lived secret and should never be returned after the initial registration/issuance.
- **[MEDIUM/security]** JWT has no `exp` claim and uses `datetime.utcnow()` (deprecated). Tokens never expire until the secret rotates, so a leaked merchant JWT is permanently valid. Add an `exp` (and optionally `nbf`) claim, and use `datetime.now(timezone.utc)`.
- **[MEDIUM/bug]** Raw exception text returned in error responses (`str(e)`) leaks internal details (stack-trace fragments, SQL errors, schema info). Return a generic message and log the exception server-side.
- **[MEDIUM/bug]** No idempotency / replay protection: a merchant can re-submit the same `merchant_order_id` and the card will be charged again. Add a unique constraint on `(merchant_id, merchant_order_id)` and either reject duplicates or store an idempotency key (e.g. request hash) per call.
- **[MEDIUM/bug]** Float used for monetary amounts (`float(data.get('amount'))` and `float(card_balance)`). Use `decimal.Decimal` for money to avoid precision loss and to safely compare/accumulate balances.
- **[MEDIUM/bug]** Missing input validation: `amount` is not required to be positive, `currency` is not validated, `cvv`/`expiry_date` are accepted as strings without length/format checks. Validate and reject early with 400.
- **[MEDIUM/bug]** Currency mismatch not checked: the card's currency (`card_currency`) is read but never compared with the requested `currency`. Charges may be processed in a different currency than the merchant intended, leading to incorrect amounts or FX exposure. Reject if they differ or convert explicitly.


### `templates/admin.html`  —  Semgrep 1 · OCR 0

<details><summary><strong>Semgrep findings (1)</strong></summary>

| Line | Sev | Rule | CWE | Message |
|---|---|---|---|---|
| 219 | WARNING | `template-unescaped-with-safe` | CWE-79: Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting') | Detected a segment of a Flask template where autoescaping is explicitly disabled with '\| safe' filter. This allows rende… |

</details>


### `templates/dashboard.html`  —  Semgrep 2 · OCR 0

<details><summary><strong>Semgrep findings (2)</strong></summary>

| Line | Sev | Rule | CWE | Message |
|---|---|---|---|---|
| 81 | WARNING | `template-unescaped-with-safe` | CWE-79: Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting') | Detected a segment of a Flask template where autoescaping is explicitly disabled with '\| safe' filter. This allows rende… |
| 166 | WARNING | `template-unescaped-with-safe` | CWE-79: Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting') | Detected a segment of a Flask template where autoescaping is explicitly disabled with '\| safe' filter. This allows rende… |

</details>


### `transaction_graphql.py`  —  Semgrep 0 · OCR 4

<details><summary><strong>OCR findings (4)</strong></summary>

- **[CRITICAL/security]** SQL injection: `account_number` is a GraphQL string argument controlled by the client and is interpolated directly into the SQL query. An attacker can supply input like `' OR '1'='1` to bypass the lookup or inject arbitrary SQL. Use parameterized queries (e.g., `execute_query("... WHERE account_number = %s", (account_number,))`) and rely on the dat...
- **[CRITICAL/security]** SQL injection: `scoped_account_number` originates from the GraphQL `account_number` argument (passed via `_resolve_scope`) and is interpolated directly into the query. An attacker can break out of the string literal to read/destroy data (e.g., `'; DROP TABLE transactions; --`). Use parameterized queries.
- **[HIGH/security]** SQL injection / defense-in-depth: `user_id` is sourced from `current_user['user_id']` in the request context. If the auth pipeline ever forwards untrusted input (e.g., from a header or query string) into this value, an attacker can inject SQL here as well. Even when trusted, building SQL by interpolation is a brittle pattern — switch to parameteriz...
- **[HIGH/security]** SQL injection: `scoped_user_id` is interpolated into both queries via f-strings. While it typically originates from integer DB columns today, this pattern is fragile and will become exploitable if upstream code ever allows a string value (e.g., via a tampered account lookup). Use parameterized queries for both the loan and bill_payments queries.

</details>


---

## 4. Tool Complementarity — what each missed

### Findings only OCR caught

Real vulnerabilities in vuln-bank that the Semgrep rulesets I used did not flag. These are **logic-level or design-level** flaws that AST cannot see:

- **PCI: full PAN+CVV returned in merchant payment endpoints** — most severe real-world issue. AST has no concept of "field should never leave the server".
- **Predictable 4-digit API key derivation** — needs understanding of the math (10,000 keyspace), not the syntax.
- **JWT `alg=none` acceptance** — algorithmic vulnerability, not a syntactic one.
- **Race conditions (3 separate sites)** — TOCTOU requires understanding transaction boundaries, not just call sequences.
- **IDOR / BOLA in `/api/v1/payments/<merchant_id>`** — needs authorization-model reasoning.
- **Plaintext password storage in `merchant_payments.py`** — needs semantic rule about password column handling.
- **Default password fallback `os.getenv('DB_PASSWORD', 'postgres')`** — heuristic, not syntactic.
- **Hardcoded seed credentials (`admin/admin123`, merchant API keys)** — only visible when reading schema/seed code, not in handlers.
- **SQLi in GraphQL resolvers (`transaction_graphql.py`)** — Semgrep's GraphQL ruleset was not in my config; coverage gap on my side.
- **`raise e` discarding traceback** — repeated 4× in `database.py`. Pythonic but easy to miss.
- **Bare `except:` swallowing `KeyboardInterrupt`/`SystemExit`** — subtle; most scanners don't distinguish `except:` from `except Exception:`.
- **No idempotency / replay protection** — needs business-logic understanding.
- **`random.choices` for security-sensitive values** — Semgrep has this in its secrets pack but doesn't catch the call site at API-key-derivation functions.

### Findings only Semgrep caught

Two categories:

1. **OCR scope:** it was pointed only at Python files, so it never saw `templates/*.html`, `.github/workflows/*.yml`, `Dockerfile`, or `static/*.js`. All stored-XSS, CI supply-chain, and container-security findings come from Semgrep.
2. **OCR blind spots:** a few specific items like `app.py:430` (cookie missing `Secure`) and `app.py:2496` (`debug=True` + `0.0.0.0`) — Semgrep has purpose-built rules that emit at the exact line.

---

## 5. Frieren DAST-AI Result

Run with:
```bash
uv run dast-ai scan --target http://localhost:5000 --max-depth 3 --max-pages 30 --workers 2 --iterations 2 --confidence 0.7 --output-dir /tmp/frieren-results
```

Crawled 17 endpoints in 133 seconds and then exited. **Every login/register/forgot-password/api-docs/merchant-login endpoint was skipped with `attack_skip: no_injectable_parameters`** because Frieren had no authenticated session to attack protected routes from.

### What this means

Frieren is not useless here — it just needs auth. The static findings already confirm the runtime vulnerabilities are real (SQLi sinks, SSRF endpoint, LLM-injection target in `ai_agent_deepseek.py`); running Frieren again with credentials would let it actually exploit them and produce proof-of-concept attack traces.

### To complete the DAST pass

```bash
cd /tmp/frieren && uv run dast-ai scan \
  --target http://localhost:5000 \
  --auth-url http://localhost:5000/login \
  --username admin --password admin123 \
  --max-depth 5 --max-pages 100 --workers 2 \
  --output-dir /tmp/frieren-results-auth
```

(Default vuln-bank admin: `admin / admin123` per `database.py` seed data.)

---

## 6. Recommendations

### Immediate (within 1 day)

1. Replace the JWT secret in `auth.py:29` with `os.environ["JWT_SECRET"]`; refuse to start if unset.
2. Remove the `verify_signature=False` fallback in `auth.py:47` — an invalid signature must return 401.
3. Restrict JWT `algorithms=["HS256"]` to remove `alg=none` from the allow-list.
4. Wrap all 33 SQL query sites in parameterised queries.
5. Strip PAN and CVV from every response in `merchant_payments.py`; mask PAN to last-4.
6. Stop `app.run(host="0.0.0.0", debug=True)` in `app.py:2496` — bind 127.0.0.1, set `debug=os.getenv("FLASK_DEBUG","0")=="1"`.

### Short-term (within 1 week)

7. Replace `random.choices` with `secrets.choice` for card numbers, CVVs, account numbers, and merchant API keys. Increase API key length to ≥32 bytes.
8. Add `exp` claim (15-minute lifetime) and refresh-token flow to both user and merchant JWTs.
9. Wrap the transfer debit in a single conditional UPDATE: `UPDATE users SET balance = balance - ? WHERE id=? AND balance >= ?` — eliminates TOCTOU.
10. Hash merchant passwords with `bcrypt` / `argon2`; remove `debug_info` echoes from all responses.
11. Pin GitHub Actions to commit SHAs (not tags): `actions/checkout@<sha>`, `webfactory/ssh-agent@<sha>`.
12. Add `USER nonroot` in `Dockerfile` before `CMD`.
13. Replace `verify=False` in `app.py:707` with `verify=True` (or a custom CA bundle).
14. Add ownership checks to `/api/v1/payments/<merchant_id>` and all `/virtual_cards/<id>` endpoints.
15. Add idempotency key on merchant `/charge` (unique constraint on `(merchant_id, merchant_order_id)`).

### Tooling pipeline going forward

| Stage | Tool | Purpose |
|---|---|---|
| Pre-commit | ggshield (once authed) | catch accidentally-committed secrets |
| PR gate | Semgrep | fast AST scan, fails build on ERROR-severity findings |
| Nightly | OCR + MiniMax-M3 | deep LLM review of changed Python files |
| Pre-deploy | Frieren DAST with auth | runtime exploitation, produces PoC traces |

---

## 7. Appendix: Raw output locations

- **Semgrep full JSON:** `/tmp/semgrep-vulnbank.json` (47 findings)
- **OCR detailed findings (per-finding):** `/home/rafael/vuln-bank/OCR_FINDINGS.md` (67 findings)
- **OCR raw session log:** `/home/rafael/.opencodereview/sessions/home-rafael-vuln-bank/4a506184-*.jsonl`
- **Frieren crawl trace:** `/tmp/frieren-results/dast-audit_20260823-193027.jsonl`
- **Detailed Semgrep walk-through (per-line code context):** `/home/rafael/vuln-bank/SEMGREP_REPORT.md`
