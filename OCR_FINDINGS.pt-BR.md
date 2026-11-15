# OCR (open-code-review) — Achados Detalhados

**Gerado em:** 2026-08-23  ·  **Modelo:** MiniMax-M3 via MiniMax  ·  **Arquivos revisados:** `ai_agent_deepseek.py`, `app.py`, `auth.py`, `database.py`, `merchant_payments.py`, `transaction_graphql.py`

> Texto em inglês preservado quando se refere a mensagens literais do modelo, identificadores de código, ou descrições técnicas de CWE. Severidade e categoria (entre colchetes) traduzidas.


## `ai_agent_deepseek.py` — 2 achados


### [ALTO/bug]


The `except` clause only catches `requests.exceptions.RequestException`, but the success branch performs unguarded dict/list access on the response JSON. If the API returns HTTP 200 with malformed JSON (`response.json()` raises `json.JSONDecodeError`), with `choices` missing or empty (`KeyError`/`IndexError`), or with a different schema, the exception propagates out of `_call_deepseek_api` rather than falling back to the mock as the surrounding flow implies. The outer `chat` catches `Exception` so the program does not crash, but the user-facing error message becomes unhelpful (e.g., `"Error in AI agent: 'choices'..."`) instead of returning a mock response. Wrap the JSON parsing and indexing in its own `try`/broad except and fall back to `_generate_mock_response(prompt)` on any parse/schema error.


---


### [MÉDIO/segurança]


Even though the SQL parameter is bound, the `%` wildcards are inserted inside the parameter value (`f"%{word}%"`), so any `%` or `_` characters in the user-controlled `word` from `message.split()` are interpreted as SQL LIKE wildcards. An attacker can supply `%` (match all) or `_` (match single char) to enumerate usernames far more efficiently than substring matching, and the search semantics for literal usernames containing those characters are silently wrong. Escape LIKE metacharacters in the user input before constructing the pattern.


---



## `app.py` — 10 achados


### [CRÍTICO/segurança]


Hardcoded secret key violates CWE-798. The Flask secret_key should be loaded from a secure environment variable or secrets manager; baking it into source code allows session/JWT forgery if the source is leaked, and applies to every deployment using this image.


---


### [CRÍTICO/segurança]


`random.choices` is not cryptographically secure (CWE-338). Card numbers, CVVs and account numbers are security-sensitive identifiers and must be generated with the `secrets` module; otherwise an attacker who observes a few outputs can predict subsequent values and forge valid payment instruments or accounts.


---


### [CRÍTICO/segurança]


The `/internal/secret` route trusts `request.remote_addr == '127.0.0.1'` to gate exposure of `app.secret_key`, `auth.JWT_SECRET` and DB credentials, but the SSRF in `/upload_profile_picture_url` (no scheme/host allowlist, redirects enabled, `verify=False`) lets any authenticated user make the server issue a request to itself. The chained effect is unauthenticated disclosure of the JWT signing key and app secret. Either bind the internal routes to a separate listener / unix socket, or require a static shared-secret header rather than a network-locality check.


---


### [CRÍTICO/segurança]


Running with `debug=True` while listening on `0.0.0.0` exposes the Werkzeug interactive debugger, which has historically been a vector for arbitrary code execution via debugger PIN brute force / PIN leak (CWE-489). For any non-local deployment this is unsafe regardless of the rest of the application posture.


---


### [ALTO/segurança]


Module-level mutable `defaultdict` used as rate-limit storage is racy and not thread/process safe. The `check_rate_limit` function performs a TOCTOU (sum -> compare -> append) without any lock; concurrent requests can each pass the limit check and append simultaneously, and `defaultdict` itself is not thread-safe for the read-and-create pattern. Under Werkzeug's threaded server (or gunicorn workers) this both weakens the rate limit and can raise `RuntimeError: dictionary changed size during iteration`. Guard state with a `threading.Lock` (and consider an external store such as Redis if multi-process).


---


### [ALTO/segurança]


Plaintext JWT printed to stdout (CWE-532). Anyone with log access (or an attacker that triggers a log disclosure) can replay the token until it expires. Remove the debug print; if logging is required, log only a short prefix and never the full token.


---


### [ALTO/segurança]


`verify=False` disables TLS certificate validation for the URL fetcher (CWE-295). This silently downgrades the SSRF surface to allow MITM-injected responses and bypasses any host-validation done later; even for a learning endpoint, this should be `True` (with a custom CA bundle if needed) so the behavior reflects what a deployed version would do.


---


### [MÉDIO/manutenibilidade]


`generate_account_number` also uses `random.choices`. Account numbers are persistent identifiers used in URLs and DB lookups and should be unpredictable and collision-resistant; switch to `secrets` and consider enforcing uniqueness at the database layer.


---


### [MÉDIO/segurança]


Bare `except:` swallows `KeyboardInterrupt` and `SystemExit` and hides the real failure (e.g. a malformed JWT, expired token, or `verify_token` bug) behind a silent fallthrough to the unauthenticated branch. Narrow to `except Exception` and log the cause, otherwise an invalid token gives an attacker access to the lower-rate-limit branch as if they were anonymous.


---


### [BAIXO/manutenibilidade]


`import html` is unused; the module never calls `html.escape`. Drop the import to keep the surface minimal and avoid implying XSS sanitization is performed (the `/update_bio` route, in particular, stores raw HTML and would mislead a future reviewer who notices the import).


---



## `auth.py` — 21 achados


### [CRÍTICO/segurança]


Including 'none' in the accepted algorithm list lets an attacker forge tokens with no signature, bypassing authentication entirely (CWE-347). Restrict the allow-list to the algorithm you actually use (e.g., ['HS256']) and never accept 'none'.


---


### [CRÍTICO/segurança]


Critical auth bypass: on InvalidSignatureError the code re-decodes the token with verify_signature=False and still returns the payload. Any attacker who modifies a token (or submits a 'none'-signed token) is treated as authenticated (CWE-347). Remove the fallback entirely; an invalid signature must reject the token.


---


### [CRÍTICO/segurança]


SQL injection in login: username and password are interpolated directly into the SQL string via f-string (CWE-89). A password like "x' OR '1'='1" bypasses authentication. Use parameterized queries and never store/compare plaintext passwords (hash with bcrypt/argon2).


---


### [CRÍTICO/segurança]


SQL injection in check_balance: account_number from the query string is interpolated into SQL (CWE-89). An attacker can dump arbitrary rows or break out of the WHERE clause. Use a parameterized query.


---


### [CRÍTICO/segurança]


SQL injection in transfer: the balance read is built with f-string interpolation of current_user['user_id'] (CWE-89). Even though the value comes from the token, treating it as trusted SQL is a footgun (e.g., if the token is forged via the 'none' bug above). Use parameter binding.


---


### [CRÍTICO/segurança]


SQL injection in transfer UPDATE: both the debit (id) and credit (account_number) statements are constructed via f-strings (CWE-89). account_number comes directly from the request body and is fully attacker-controlled. Use parameter binding and an atomic UPDATE guarded by the balance check.


---


### [ALTO/segurança]


JWT signing secret is a trivially guessable hard-coded literal ("secret123"). An attacker who guesses the source can forge tokens for any user. Load the secret from an environment variable or secret manager and use a high-entropy value (CWE-798, CWE-326).


---


### [ALTO/segurança]


Tokens are issued without an 'exp' (expiration) claim, so any leaked or stolen token grants permanent access (CWE-613). Add an 'exp' set to a short, sensible lifetime (e.g., 15–60 minutes) and pair with a refresh-token flow.


---


### [ALTO/segurança]


Insecure direct object reference (IDOR): any authenticated user can query any account_number with no ownership check (CWE-639). Authorize that current_user is allowed to read the requested account (e.g., compare account_number against current_user's own account, or enforce role-based access).


---


### [ALTO/segurança]


TOCTOU race condition on funds transfer: the balance is read and then the UPDATE happens in a separate statement; concurrent requests can both pass the balance check and collectively overdraw the account (CWE-362). Wrap the debit in a single conditional UPDATE (e.g., `... WHERE id=? AND balance >= ?`) inside a transaction with the row locked, and roll back if zero rows are updated.


---


### [ALTO/bug]


No amount validation: negative or zero amounts, NaN, or non-finite values flow straight into SQL and could credit the sender or perform a no-op transfer. Validate amount > 0 (and consider rejecting values over a daily cap). Also, decimal.Decimal is preferable to float for currency.


---


### [MÉDIO/bug]


Bare 'except:' catches BaseException including KeyboardInterrupt and SystemExit, and silently swallows every error from the inner decode (CWE-396). Catch jwt exceptions explicitly and let system exceptions propagate.


---


### [MÉDIO/segurança]


Printing exception text from token decoding can leak internal details (key material fragments, library internals) to logs/stderr and provide attackers with reconnaissance (CWE-209). Log via the logging module and either drop the message or keep it generic.


---


### [MÉDIO/segurança]


Accepting the token from query string, form body, and cookies (in addition to Authorization) significantly increases leakage risk: URLs end up in proxy logs, browser history, Referer headers, and accidental copy-pastes (CWE-598). Restrict tokens to the Authorization header (or a Secure/HttpOnly cookie with SameSite=Strict) and never accept them in URL parameters.


---


### [MÉDIO/segurança]


The 401 response echoes the raw exception text in 'details', which can disclose internal error information to callers (CWE-209). Return a generic message and log the real cause server-side.


---


### [MÉDIO/segurança]


Login response leaks account_number, is_admin, and a debug_info block (login time, remote IP, User-Agent) to the client (CWE-200). Don't return internal identifiers or client metadata that an attacker doesn't need; never include IP/UA as "debug" data in a public response.


---


### [MÉDIO/segurança]


Information disclosure in transfer response: returns recipient username and full new_balance to the caller (CWE-200). A legitimate user should only see their own new balance; revealing the recipient's balance aids reconnaissance and social engineering.


---


### [MÉDIO/bug]


No self-transfer guard: a user can transfer to their own account_number, which (with the missing amount validation) is one half of a double-spend primitive. Reject transfers where to_account matches the sender's own account.


---


### [BAIXO/bug]


'Bearer' is matched with a substring test, so headers like 'XBearer abc' or 'NotBearer foo' are accepted as Bearer tokens (and 'abc def' is treated as a raw token). Use startswith('Bearer ') with a length check.


---


### [BAIXO/bug]


SQLite connections are opened and closed manually; an exception between connect() and close() leaks the connection and the underlying file handle. Use a context manager (e.g., `with sqlite3.connect('bank.db') as conn:`) in every route and combine with explicit transactions.


---


### [BAIXO/manutenibilidade]


Suspended-account check uses positional indices (len(user) > 9 and user[9]) that depend on an undocumented schema column order. If the schema changes, this silently breaks or returns wrong data. Name columns explicitly in the SELECT (e.g., `SELECT id, username, account_number, is_admin, suspended FROM users ...`) and access by key.


---



## `database.py` — 9 achados


### [ALTO/segurança]


Hardcoded default password: `os.getenv('DB_PASSWORD', 'postgres')` falls back to a literal credential in source. If the environment variable is unset (e.g., in production misconfiguration), the application silently authenticates with a publicly known password. Refuse to start when `DB_PASSWORD` is unset rather than providing a default.


---


### [ALTO/segurança]


Hardcoded secrets in seed data: The admin account is created with plaintext password 'admin123', and merchants are seeded with plaintext passwords and API keys. These credentials are committed in source and would be live if init_db runs on a fresh database. Use randomized secrets generated at first install, or load them from a secrets manager.


---


### [MÉDIO/erro]


Original traceback lost: `raise e` re-raises the caught exception object but breaks the chain so the original traceback is discarded. Use bare `raise` (or `raise ... from e`) so the actual exception location is preserved in logs.


---


### [MÉDIO/erro]


Silent exception swallow hides schema errors: `except Exception: pass` discards both the "column already exists" case (expected) and real migration failures (e.g., permission errors, syntax errors with newer Postgres). At minimum log the exception; better, narrow to `psycopg2.errors.DuplicateColumn` or check `information_schema.columns` first.


---


### [MÉDIO/erro]


Silent exception swallow on critical migrations: Three ALTER TYPE statements are guarded by a single bare `except Exception: pass`, so if the first conversion fails the others are skipped silently. This can leave the schema half-migrated with no diagnostics. Log the exception or split each ALTER into its own guarded block.


---


### [MÉDIO/erro]


Original traceback lost on init failure: `raise e` discards the underlying exception's traceback, making startup failures hard to diagnose. Use bare `raise`.


---


### [MÉDIO/erro]


Original traceback lost in execute_query: `raise e` after rollback breaks the traceback chain, which complicates debugging at call sites. Use bare `raise`.


---


### [MÉDIO/erro]


Original traceback lost in execute_transaction: `raise e` after rollback discards the chained traceback. Use bare `raise`.


---


### [BAIXO/manutenibilidade]


Unused import: `datetime` is imported but never referenced anywhere in this module. Remove the import to keep dependencies minimal.


---



## `merchant_payments.py` — 21 achados


### [CRÍTICO/segurança]


SQL injection: `api_key` comes from the `X-Merchant-Api-Key` request header (attacker-controlled) and is interpolated into the query via f-string. Use parameterized queries (`%s` placeholder) instead.


---


### [CRÍTICO/segurança]


SQL injection: `merchant_id` from the decoded JWT payload is interpolated directly. If `verify_token` ever accepts an `alg: none` token or weak secret, this becomes arbitrary SQL. Use a parameterized query.


---


### [CRÍTICO/segurança]


SQL injection on registration: `name`, `email`, and `password` are user-controlled request fields interpolated into the INSERT via f-string. Use parameterized queries.


---


### [CRÍTICO/segurança]


Plaintext password storage: passwords are inserted verbatim and compared verbatim in `login_merchant`. Hash with a slow algorithm (bcrypt/argon2) and verify via constant-time comparison. Also note that returning the raw password in `debug_info` leaks it.


---


### [CRÍTICO/segurança]


SQL injection on merchant login: `email` and `password` are attacker-controlled JSON fields interpolated via f-string. Use parameterized queries, and store/verify passwords as hashes.


---


### [CRÍTICO/segurança]


Predictable / weak API key: derived from a 4-digit code (10,000 possibilities) using `random` (not `secrets`), so trivially brute-forceable by enumerating all `vk_<sha256(0000..9999)>` hashes. Use `secrets.token_urlsafe(32)` or `secrets.token_hex(32)`.


---


### [CRÍTICO/segurança]


SQL injection on charge: `card_number` is user-controlled (from the charge request body) and is interpolated via f-string into the card lookup. Use parameterized queries.


---


### [CRÍTICO/segurança]


PCI / data-handling violation: the charge response includes the full PAN (`card_number`) and CVV of the customer card. CVV must never be stored or returned after authorization. PAN must be masked. Strip these fields from the response.


---


### [CRÍTICO/segurança]


PCI violation: GET `/api/v1/payments/<id>` returns full PAN and CVV of the customer's card. Never return CVV, and mask PAN to last4.


---


### [CRÍTICO/segurança]


PCI violation: list endpoints also leak full PAN (`card_number`) for every transaction. Mask to last4 across `list_merchant_payments` and `list_payments_by_merchant_id`.


---


### [CRÍTICO/segurança]


IDOR / authorization bypass: any authenticated merchant can list all payments of any other merchant by passing their `merchant_id` in the URL. The `@merchant_required` decorator only verifies the caller is a merchant, not that they own the resource. Enforce `merchant_id == current_merchant['id']` (or admin check) and reject otherwise.


---


### [ALTO/segurança]


Information disclosure: the registration response echoes the user's plaintext password (and full raw request) back to the client in `debug_info`. Drop debug fields entirely from production responses.


---


### [ALTO/segurança]


Predictable authorization code: `time.time()` seconds + 3 random digits is trivially guessable. Use `secrets.token_urlsafe`/`secrets.token_hex` instead.


---


### [ALTO/segurança]


Race condition / non-atomic charge: SELECT (balance check), UPDATE (debit), and INSERT (transaction record) are three separate statements with no transaction wrapper. Two concurrent charges can both pass the balance check and both debit, producing a negative balance. Wrap in a single DB transaction and use a conditional `UPDATE ... WHERE current_balance >= %s` plus rowcount check, or `SELECT ... FOR UPDATE`.


---


### [ALTO/segurança]


Information disclosure: the `/merchants/me` response includes the merchant's API key in `debug_info`. The API key is a long-lived secret and should never be returned after the initial registration/issuance.


---


### [MÉDIO/segurança]


JWT has no `exp` claim and uses `datetime.utcnow()` (deprecated). Tokens never expire until the secret rotates, so a leaked merchant JWT is permanently valid. Add an `exp` (and optionally `nbf`) claim, and use `datetime.now(timezone.utc)`.


---


### [MÉDIO/bug]


Raw exception text returned in error responses (`str(e)`) leaks internal details (stack-trace fragments, SQL errors, schema info). Return a generic message and log the exception server-side.


---


### [MÉDIO/bug]


No idempotency / replay protection: a merchant can re-submit the same `merchant_order_id` and the card will be charged again. Add a unique constraint on `(merchant_id, merchant_order_id)` and either reject duplicates or store an idempotency key (e.g. request hash) per call.


---


### [MÉDIO/bug]


Float used for monetary amounts (`float(data.get('amount'))` and `float(card_balance)`). Use `decimal.Decimal` for money to avoid precision loss and to safely compare/accumulate balances.


---


### [MÉDIO/bug]


Missing input validation: `amount` is not required to be positive, `currency` is not validated, `cvv`/`expiry_date` are accepted as strings without length/format checks. Validate and reject early with 400.


---


### [MÉDIO/bug]


Currency mismatch not checked: the card's currency (`card_currency`) is read but never compared with the requested `currency`. Charges may be processed in a different currency than the merchant intended, leading to incorrect amounts or FX exposure. Reject if they differ or convert explicitly.


---



## `transaction_graphql.py` — 4 achados


### [CRÍTICO/segurança]


SQL injection: `account_number` is a GraphQL string argument controlled by the client and is interpolated directly into the SQL query. An attacker can supply input like `' OR '1'='1` to bypass the lookup or inject arbitrary SQL. Use parameterized queries (e.g., `execute_query("... WHERE account_number = %s", (account_number,))`) and rely on the database driver to escape values.


---


### [CRÍTICO/segurança]


SQL injection: `scoped_account_number` originates from the GraphQL `account_number` argument (passed via `_resolve_scope`) and is interpolated directly into the query. An attacker can break out of the string literal to read/destroy data (e.g., `'; DROP TABLE transactions; --`). Use parameterized queries.


---


### [ALTO/segurança]


SQL injection / defense-in-depth: `user_id` is sourced from `current_user['user_id']` in the request context. If the auth pipeline ever forwards untrusted input (e.g., from a header or query string) into this value, an attacker can inject SQL here as well. Even when trusted, building SQL by interpolation is a brittle pattern — switch to parameterized queries and validate that `user_id` is an integer before substitution.


---


### [ALTO/segurança]


SQL injection: `scoped_user_id` is interpolated into both queries via f-strings. While it typically originates from integer DB columns today, this pattern is fragile and will become exploitable if upstream code ever allows a string value (e.g., via a tampered account lookup). Use parameterized queries for both the loan and bill_payments queries.


---

