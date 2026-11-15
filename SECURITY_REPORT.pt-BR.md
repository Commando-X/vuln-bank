# vuln-bank — Relatório Consolidado de Auditoria de Segurança

**Alvo:** `/home/rafael/vuln-bank` — aplicação Flask bancária intencionalmente vulnerável rodando em `http://localhost:5000`  
**Data:** 2026-08-23  
**Escopo:** árvore de código-fonte completa (Python, templates, JS, Dockerfile, workflows CI, GraphQL)  
**Autoria:** varredura SAST combinada — Semgrep OSS 1.174.0 + OCR (LLM via MiniMax-M3) + Frieren DAST-AI

---

## Resumo Executivo

### Números gerais

| Ferramenta | Tipo | Arquivos | Achados | Resultado notável |
|---|---|---|---|---|
| **Semgrep OSS 1.174.0** | AST estático | 8 | **47** (37 ERROR / 10 WARNING) | 33 sinks de SQLi confirmados em 3 arquivos |
| **OCR (open-code-review 1.9.10)** + MiniMax-M3 | revisão LLM | 6 Python | **67** (23 críticos / 17 altos / 22 médios / 5 baixos) | violações PCI, JWT alg=none, race conditions, IDOR, senhas em texto puro |
| **Frieren DAST-AI** | runtime black-box | 17 endpoints rastreados | **0** (sem autenticação) | precisa de `--auth-url/--username/--password` para ser útil |
| **ggshield** | detecção de segredos | n/a | n/a | adiado — autenticação não completada |

### As 6 vulnerabilidades que realmente importam

Ordenadas por impacto no mundo real, não pela confiança da ferramenta. Cada uma é corroborada por evidência no código-fonte (Semgrep), análise lógica (OCR), ou ambos.

1. **`merchant_payments.py` retorna PAN + CVV completos em 4 endpoints de API** *(OCR, crítico)* — viola o requisito 3.2 do PCI-DSS: "Nunca armazene o CVV após a autorização". Qualquer merchant que chamar esses endpoints exfiltra dados de cartão dos clientes para seus próprios logs.
2. **`auth.py` aceita tokens JWT com `alg=none`** *(OCR, crítico)* — combinado com o segredo hardcoded `"secret123"` e o fallback `verify_signature=False` na L47, qualquer atacante pode forjar tokens de admin. CVSS efetivo ~9.8.
3. **`auth.py` tem race condition TOCTOU na transferência** *(OCR, alto)* — SELECT do saldo seguido de UPDATE em statements separados (L185/L190). Requisições concorrentes podem cada uma passar na verificação de saldo e coletivamente sacar a conta a valores negativos.
4. **`merchant_payments.py` deriva a API key de um código de 4 dígitos com `random.choices`** *(OCR, crítico)* — apenas 10.000 possibilidades; um atacante que conheça a derivação pode enumerar offline todas as API keys merchant válidas.
5. **33 sinks de SQL injection via concatenação em f-string** *(Semgrep + OCR, crítico)* — `username`, `password`, `account_number`, `card_id`, `merchant_id`, `api_key`, `email` são concatenados diretamente em strings SQL. Bypass de autenticação via `admin' --` no login é trivial.
6. **`app.py:2496` executa o Flask com `host=0.0.0.0, debug=True`** *(Semgrep + OCR, alto)* — o debugger interativo do Werkzeug fica acessível a partir de qualquer rede onde o container esteja. Historicamente usado para RCE não autenticado.

---

## Metodologia

| Ferramenta | Versão | Configuração | O que cobre |
|---|---|---|---|
| Semgrep OSS | 1.174.0 | `p/python p/owasp-top-ten p/security-audit p/secrets p/flask p/jwt p/sql-injection p/command-injection p/insecure-transport p/cwe-top-25` | análise estática AST com mapeamento CWE |
| OCR | 1.9.10 | Provider `minimax`, modelo `MiniMax-M3`, endpoint `https://api.minimax.io/v1` | revisão de código via LLM, restrita aos arquivos Python |
| Frieren DAST-AI | main @ 1.0.0 | `AI_PROVIDER=openai`, `OPENAI_BASE_URL=https://api.minimax.io/v1` | varredura runtime black-box via Playwright + 8 agentes de ataque LLM-driven |
| ggshield | 1.45.0 | n/a (autenticação incompleta) | envia conteúdo dos arquivos para a nuvem do GitGuardian |

### Ressalvas importantes

- **OCR foi restrito aos arquivos Python.** Ele não revisou templates Jinja2, JavaScript estático, Dockerfile, ou workflows CI. Achados nessas áreas vêm exclusivamente do Semgrep.
- **Frieren rodou sem credenciais.** Cada endpoint em /login, /register, /api-docs foi marcado como `attack_skip: no_injectable_parameters`. Seus 0 achados refletem uma lacuna de cobertura, não uma aplicação limpa.
- **ggshield não foi executado.** Precisa que `ggshield auth login` seja completado interativamente antes de qualquer varredura rodar.

---

## Classes de Vulnerabilidade — Visão Combinada entre Ferramentas

| # | Classe de Vulnerabilidade | CWE | Achados Semgrep | Achados OCR | Onde |
|---|---|---|---|---|---|
| 1 | SQL Injection (concatenação em f-string) | CWE-89 | 33 | 10 | `app.py`, `auth.py`, `merchant_payments.py`, `transaction_graphql.py` |
| 2 | Credenciais hardcoded | CWE-798 | 1 | 4 | `auth.py:29` segredo JWT; `database.py` fallback de senha do DB; seed admin `admin123` |
| 3 | Bypass de assinatura JWT / `alg=none` | CWE-347 | 1 | 2 | `auth.py:47` `verify_signature=False`; allowlist de alg inclui `none` |
| 4 | Aleatoriedade criptograficamente insegura | CWE-338 | 0 | 2 | `random.choices` para números de cartão, CVVs, account numbers, API keys |
| 5 | Race condition / TOCTOU | CWE-362 | 0 | 3 | `auth.py` transferência; `merchant_payments.py` cobrança; `app.py` verificação de rate-limit |
| 6 | XSS armazenado via Jinja2 `\|safe` | CWE-79 | 3 | 0 | `templates/dashboard.html:81,166`; `templates/admin.html:219` |
| 7 | Informações sensíveis em respostas (incl. PCI) | CWE-200 / CWE-312 | 0 | 4 | Login ecoa account_number + IP + UA; merchant `/me` ecoa API key; charge/list retorna PAN+CVV completos |
| 8 | IDOR / BOLA | CWE-639 | 0 | 3 | `/api/v1/payments/<merchant_id>` cross-merchant; `/virtual_cards/<id>` sem checagem de propriedade |
| 9 | Ausência de expiração do token | CWE-613 | 0 | 2 | JWT de usuário e de merchant emitidos sem `exp` |
| 10 | Validação TLS insegura | CWE-295 | 1 | 1 | `app.py:707` `verify=False` no proxy de imagens |
| 11 | Modo debug + bind 0.0.0.0 | CWE-489 | 2 | 1 | `app.py:2496` `app.run(host=0.0.0.0, debug=True)` |
| 12 | Tag mutável de action CI (supply chain) | CWE-829 | 3 | 0 | `.github/workflows/deploy.yml:20,23`; `.github/workflows/reset.yml:36` |
| 13 | Ausência de USER no container | CWE-250 | 1 | 0 | `Dockerfile:29` sem diretiva `USER` |
| 14 | Atributos inseguros de cookie | CWE-614 | 1 | 0 | `app.py:430` cookie sem `Secure` nem `SameSite` |
| 15 | Armazenamento de senha em texto puro | CWE-256 | 0 | 2 | `merchant_payments.py` registro e login comparam verbatim |
| 16 | Sem idempotência / proteção contra replay | CWE-863 | 0 | 1 | `merchant_payments.py` cobrança reprocessa ao reutilizar `merchant_order_id` |
| 17 | Perda de traceback (`raise e`) | CWE-754 | 0 | 4 | `database.py` (4 ocorrências) |
| 18 | `except:` nu engolindo SystemExit | CWE-396 | 0 | 2 | `app.py`, `auth.py` |

---

## Achados por Arquivo

Cada seção de arquivo mostra os achados do Semgrep como tabela compacta e os do OCR como lista compacta. Snippets de código completos para cada achado estão em `OCR_FINDINGS.md` e `SEMGREP_REPORT.md`.

### `.github/workflows/deploy.yml`  —  Semgrep 2 · OCR 0

**▼ Achados do Semgrep (2)**

| Linha | Sev | Regra | CWE | Mensagem |
|---|---|---|---|---|
| 20 | WARNING | `github-actions-mutable-action-tag` | CWE-1357: Reliance on Insufficiently Trustworthy Component, CWE-353: Missing Support for Integrity Check | GitHub Actions step uses a mutable tag or branch reference. Tags and branch names can be silently repointed by the actio… |
| 23 | WARNING | `github-actions-mutable-action-tag` | CWE-1357: Reliance on Insufficiently Trustworthy Component, CWE-353: Missing Support for Integrity Check | GitHub Actions step uses a mutable tag or branch reference. Tags and branch names can be silently repointed by the actio… |




### `.github/workflows/reset.yml`  —  Semgrep 1 · OCR 0

**▼ Achados do Semgrep (1)**

| Linha | Sev | Regra | CWE | Mensagem |
|---|---|---|---|---|
| 36 | WARNING | `github-actions-mutable-action-tag` | CWE-1357: Reliance on Insufficiently Trustworthy Component, CWE-353: Missing Support for Integrity Check | GitHub Actions step uses a mutable tag or branch reference. Tags and branch names can be silently repointed by the actio… |




### `Dockerfile`  —  Semgrep 1 · OCR 0

**▼ Achados do Semgrep (1)**

| Linha | Sev | Regra | CWE | Mensagem |
|---|---|---|---|---|
| 29 | ERROR | `missing-user` | CWE-250: Execution with Unnecessary Privileges | By not specifying a USER, a program in the container may run as 'root'. This is a security hazard. If an attacker can co… |




### `ai_agent_deepseek.py`  —  Semgrep 0 · OCR 2

**▼ Achados do OCR (2)**

- **[HIGH/bug]** The `except` clause only catches `requests.exceptions.RequestException`, but the success branch performs unguarded dict/list access on the response JSON. If the API returns HTTP 200 with malformed JSON (`response.json()` raises `json.JSONDecodeError`), with `choices` missing or empty (`KeyError`/`IndexError`), or with a different schema, the except...
- **[MEDIUM/security]** Even though the SQL parameter is bound, the `%` wildcards are inserted inside the parameter value (`f"%{word}%"`), so any `%` or `_` characters in the user-controlled `word` from `message.split()` are interpreted as SQL LIKE wildcards. An attacker can supply `%` (match all) or `_` (match single char) to enumerate usernames far more efficiently than...




### `app.py`  —  Semgrep 23 · OCR 10

**▼ Achados do Semgrep (23)**

| Linha | Sev | Regra | CWE | Mensagem |
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



**▼ Achados do OCR (10)**

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




### `auth.py`  —  Semgrep 9 · OCR 21

**Padrão:** 7 sinks de SQL-injection, todos no estilo f-string `f"...WHERE x='VAR'..."`. O código-fonte tem comentários `# Vulnerability: SQL Injection possible` ao lado de cada um. Correção: substituir por `cursor.execute("... WHERE x=?", (x,))` com bind de parâmetros.

| Linha | Preview do sink |
|---|---|
| 120 | `>>>  120 |         query = f"SELECT * FROM users WHERE username='{auth.get('username')}' AND password='{auth.get('password')}'"` |
| 153 | `>>>  153 |         account_number = request.args.get('account_number')` |
| 157 | `>>>  157 |         c.execute(f"SELECT username, balance FROM users WHERE account_number='{account_number}'")` |
| 185 | `>>>  185 |         c.execute(f"SELECT balance FROM users WHERE id={current_user['user_id']}")` |
| 190 | `>>>  190 |             c.execute(f"UPDATE users SET balance = balance - {amount} WHERE id={current_user['user_id']}")` |
| 191 | `>>>  191 |             c.execute(f"UPDATE users SET balance = balance + {amount} WHERE account_number='{to_account}'")` |
| 195 | `>>>  195 |             c.execute(f"SELECT username, balance FROM users WHERE account_number='{to_account}'")` |

Outros achados do Semgrep neste arquivo:
- L29 [ERROR] `jwt-python-hardcoded-secret` — Hardcoded JWT secret or private key is used. This is a Insufficiently Protected Credentials weakness: https://cwe.mitre.org/data/definitions
- L47 [ERROR] `unverified-jwt-decode` — Detected JWT token decoded with 'verify=False'. This bypasses any integrity checks for the token which means the token could be tampered wit

**Achados do OCR (21):**

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

**▼ Achados do OCR (9)**

- **[HIGH/security]** Hardcoded default password: `os.getenv('DB_PASSWORD', 'postgres')` falls back to a literal credential in source. If the environment variable is unset (e.g., in production misconfiguration), the application silently authenticates with a publicly known password. Refuse to start when `DB_PASSWORD` is unset rather than providing a default.
- **[HIGH/security]** Hardcoded secrets in seed data: The admin account is created with plaintext password 'admin123', and merchants are seeded with plaintext passwords and API keys. These credentials are committed in source and would be live if init_db runs on a fresh database. Use randomized secrets generated at first install, or load them from a secrets manager.
- **[MEDIUM/error]** Original traceback lost: `raise e` re-raises the caught exception object but breaks the chain so the original traceback is discarded. Use bare `raise` (or `raise ... from e`) so the actual exception location is preserved in logs.
- **[MEDIUM/error]** Silent exception swallow hides schema errors: `except Exception: pass` discards both the "column already exists" case (expected) and real migration failures (e.g., permission errors, syntax errors with newer Postgres). At minimum log the exception; better, narrow to `psycopg2.errors.DuplicateColumn` or check `information_schema.columns` first.
- **[MEDIUM/error]** Silent exception swallow on critical migrations: Three ALTER TYPE statements are guarded by a single bare `except Exception: pass`, so if the first conversion fails the others are skipped silently. This can leave the schema half-migrated with no diagnostics. Log the exception or split each ALTER into its own guarded block.
- **[MEDIUM/error]** Original traceback lost on init failure: `raise e` discards the underlying exception's traceback, making startup failures hard to diagnose. Use bare `raise`.
- **[MEDIUM/error]** Original traceback lost in execute_query: `raise e` after rollback breaks the traceback chain, which complicates debugging at call sites. Use bare `raise`.
- **[MEDIUM/error]** Original traceback lost in execute_transaction: `raise e` after rollback discards the chained traceback. Use bare `raise`.
- **[LOW/maintainability]** Unused import: `datetime` is imported but never referenced anywhere in this module. Remove the import to keep dependencies minimal.




### `merchant_payments.py`  —  Semgrep 8 · OCR 21

**Padrão:** 8 sinks de SQL-injection, todos no estilo f-string `f"...WHERE x='VAR'..."`. O código-fonte tem comentários `# Vulnerability: SQL Injection possible` ao lado de cada um. Correção: substituir por `cursor.execute("... WHERE x=?", (x,))` com bind de parâmetros.

| Linha | Preview do sink |
|---|---|
| 61 | `>>>   61 |         query = f"""` |
| 76 | `>>>   76 |             query = f"""` |
| 160 | `>>>  160 |             query = f"""` |
| 209 | `>>>  209 |             query = f"""` |
| 266 | `>>>  266 |             card_query = f"""` |
| 436 | `>>>  436 |             query = f"""` |
| 501 | `>>>  501 |             query = f"""` |
| 554 | `>>>  554 |             query = f"""` |

**Achados do OCR (21):**

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

**▼ Achados do Semgrep (1)**

| Linha | Sev | Regra | CWE | Mensagem |
|---|---|---|---|---|
| 219 | WARNING | `template-unescaped-with-safe` | CWE-79: Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting') | Detected a segment of a Flask template where autoescaping is explicitly disabled with '\| safe' filter. This allows rende… |




### `templates/dashboard.html`  —  Semgrep 2 · OCR 0

**▼ Achados do Semgrep (2)**

| Linha | Sev | Regra | CWE | Mensagem |
|---|---|---|---|---|
| 81 | WARNING | `template-unescaped-with-safe` | CWE-79: Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting') | Detected a segment of a Flask template where autoescaping is explicitly disabled with '\| safe' filter. This allows rende… |
| 166 | WARNING | `template-unescaped-with-safe` | CWE-79: Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting') | Detected a segment of a Flask template where autoescaping is explicitly disabled with '\| safe' filter. This allows rende… |




### `transaction_graphql.py`  —  Semgrep 0 · OCR 4

**▼ Achados do OCR (4)**

- **[CRITICAL/security]** SQL injection: `account_number` is a GraphQL string argument controlled by the client and is interpolated directly into the SQL query. An attacker can supply input like `' OR '1'='1` to bypass the lookup or inject arbitrary SQL. Use parameterized queries (e.g., `execute_query("... WHERE account_number = %s", (account_number,))`) and rely on the dat...
- **[CRITICAL/security]** SQL injection: `scoped_account_number` originates from the GraphQL `account_number` argument (passed via `_resolve_scope`) and is interpolated directly into the query. An attacker can break out of the string literal to read/destroy data (e.g., `'; DROP TABLE transactions; --`). Use parameterized queries.
- **[HIGH/security]** SQL injection / defense-in-depth: `user_id` is sourced from `current_user['user_id']` in the request context. If the auth pipeline ever forwards untrusted input (e.g., from a header or query string) into this value, an attacker can inject SQL here as well. Even when trusted, building SQL by interpolation is a brittle pattern — switch to parameteriz...
- **[HIGH/security]** SQL injection: `scoped_user_id` is interpolated into both queries via f-strings. While it typically originates from integer DB columns today, this pattern is fragile and will become exploitable if upstream code ever allows a string value (e.g., via a tampered account lookup). Use parameterized queries for both the loan and bill_payments queries.




---

## Complementaridade entre Ferramentas — o que cada uma deixou passar

### Achados que só o OCR capturou

Vulnerabilidades reais do vuln-bank que os rulepacks do Semgrep que eu utilizei não sinalizaram. Estas são falhas de **nível lógico ou de design** que análise AST não enxerga:

- **PCI: PAN+CVV completos retornados nos endpoints de pagamento merchant** — o problema mais severo no mundo real. AST não tem noção de "campo que nunca deveria sair do servidor".
- **Derivação previsível de API key de 4 dígitos** — exige entender a matemática (keyspace de 10.000), não a sintaxe.
- **Aceitação de JWT `alg=none`** — vulnerabilidade algorítmica, não sintática.
- **Race conditions (3 ocorrências distintas)** — TOCTOU exige entender os limites transacionais, não apenas a sequência de chamadas.
- **IDOR / BOLA em `/api/v1/payments/<merchant_id>`** — exige raciocínio sobre o modelo de autorização.
- **Armazenamento de senha em texto puro em `merchant_payments.py`** — exige regra semântica sobre tratamento da coluna de senha.
- **Fallback de senha padrão `os.getenv('DB_PASSWORD', 'postgres')`** — heurística, não sintaxe.
- **Credenciais hardcoded no seed (`admin/admin123`, API keys de merchant)** — só visíveis ao ler o código de schema/seed, não nos handlers.
- **SQLi em resolvers GraphQL (`transaction_graphql.py`)** — o rulepack GraphQL do Semgrep não estava na minha configuração; lacuna de cobertura do meu lado.
- **`raise e` descartando o traceback** — repetido 4× em `database.py`. Pythônico mas fácil de escapar.
- **`except:` nu engolindo `KeyboardInterrupt`/`SystemExit`** — sutil; a maioria dos scanners não distingue `except:` de `except Exception:`.
- **Sem idempotência / proteção contra replay** — exige entendimento da lógica de negócio.
- **`random.choices` em valores sensíveis de segurança** — o Semgrep tem isso no seu pack de segredos mas não captura o call site nas funções de derivação de API key.

### Achados que só o Semgrep capturou

Duas categorias:

1. **Escopo do OCR:** ele foi apontado apenas para os arquivos Python, então nunca viu `templates/*.html`, `.github/workflows/*.yml`, `Dockerfile`, nem `static/*.js`. Todos os achados de stored-XSS, supply chain CI e segurança de container vêm do Semgrep.
2. **Pontos cegos do OCR:** alguns itens específicos como `app.py:430` (cookie sem `Secure`) e `app.py:2496` (`debug=True` + `0.0.0.0`) — o Semgrep tem regras dedicadas que emitem na linha exata.

---

## Resultado do Frieren DAST-AI

Executado com:
```bash
uv run dast-ai scan --target http://localhost:5000 --max-depth 3 --max-pages 30 --workers 2 --iterations 2 --confidence 0.7 --output-dir /tmp/frieren-results
```

Rastreou 17 endpoints em 133 segundos e então saiu. **Cada endpoint /login, /register, /forgot-password, /api-docs, /merchant-login foi pulado com `attack_skip: no_injectable_parameters`** porque o Frieren não tinha sessão autenticada de onde atacar as rotas protegidas.

### O que isso significa

Frieren não é inútil aqui — só precisa de autenticação. Os achados estáticos já confirmam que as vulnerabilidades runtime são reais (sinks de SQLi, endpoint de SSRF, alvo de LLM-injection em `ai_agent_deepseek.py`); rodar o Frieren novamente com credenciais permitiria explorá-las de fato e produzir traces de prova de conceito.

### Para completar a varredura DAST

```bash
cd /tmp/frieren && uv run dast-ai scan \
  --target http://localhost:5000 \
  --auth-url http://localhost:5000/login \
  --username admin --password admin123 \
  --max-depth 5 --max-pages 100 --workers 2 \
  --output-dir /tmp/frieren-results-auth
```

(Admin padrão do vuln-bank: `admin / admin123`, conforme dados de seed em `database.py`.)

---

## Recomendações

### Imediato (em até 1 dia)

1. Substituir o segredo JWT em `auth.py:29` por `os.environ["JWT_SECRET"]`; recusar inicialização se não estiver definido.
2. Remover o fallback `verify_signature=False` em `auth.py:47` — uma assinatura inválida deve retornar 401.
3. Restringir `algorithms=["HS256"]` no JWT para remover `none` da allowlist.
4. Embrulhar todos os 33 sites de query SQL em queries com bind de parâmetros.
5. Remover PAN e CVV de toda resposta em `merchant_payments.py`; mascarar PAN para os últimos 4 dígitos.
6. Parar `app.run(host="0.0.0.0", debug=True)` em `app.py:2496` — bind em 127.0.0.1, setar `debug=os.getenv("FLASK_DEBUG","0")=="1"`.

### Curto prazo (em até 1 semana)

7. Substituir `random.choices` por `secrets.choice` para números de cartão, CVVs, account numbers e API keys de merchant. Aumentar tamanho da API key para ≥32 bytes.
8. Adicionar claim `exp` (tempo de vida de 15 minutos) e fluxo de refresh token tanto para JWTs de usuário quanto de merchant.
9. Embrulhar o débito da transferência em um único UPDATE condicional: `UPDATE users SET balance = balance - ? WHERE id=? AND balance >= ?` — elimina o TOCTOU.
10. Hashear senhas de merchant com `bcrypt` / `argon2`; remover echoes de `debug_info` de todas as respostas.
11. Pinar GitHub Actions por SHA de commit (não por tag): `actions/checkout@<sha>`, `webfactory/ssh-agent@<sha>`.
12. Adicionar `USER nonroot` no `Dockerfile` antes do `CMD`.
13. Substituir `verify=False` em `app.py:707` por `verify=True` (ou um bundle de CA customizado).
14. Adicionar checagens de propriedade em `/api/v1/payments/<merchant_id>` e em todos os endpoints `/virtual_cards/<id>`.
15. Adicionar chave de idempotência no `/charge` de merchant (constraint UNIQUE em `(merchant_id, merchant_order_id)`).

### Pipeline de tooling daqui pra frente

| Estágio | Ferramenta | Propósito |
|---|---|---|
| Pre-commit | ggshield (após autenticar) | capturar segredos acidentalmente commitados |
| PR gate | Semgrep | varredura AST rápida; falha o build em achados ERROR |
| Noturno | OCR + MiniMax-M3 | revisão LLM profunda dos arquivos Python alterados |
| Pré-deploy | Frieren DAST com auth | exploração runtime; produz traces de PoC |

---

## Apêndice: Localização dos outputs brutos

- **Semgrep JSON completo:** `/tmp/semgrep-vulnbank.json` (47 achados)
- **Achados detalhados do OCR (por achado):** `/home/rafael/vuln-bank/OCR_FINDINGS.md` (67 achados)
- **Log bruto da sessão OCR:** `/home/rafael/.opencodereview/sessions/home-rafael-vuln-bank/4a506184-*.jsonl`
- **Trace de rastreamento do Frieren:** `/tmp/frieren-results/dast-audit_20260823-193027.jsonl`
- **Walk-through detalhado do Semgrep (contexto de código por linha):** `/home/rafael/vuln-bank/SEMGREP_REPORT.md`
