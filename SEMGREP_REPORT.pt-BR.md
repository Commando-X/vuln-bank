# vuln-bank — Achados SAST do Semgrep

**Ferramenta:** Semgrep OSS 1.174.0  ·  **Data:** 2026-08-23  ·  **Alvo:** /home/rafael/vuln-bank

**47 achados** (37 ERRO · 10 AVISO)

Rulepacks: `p/python p/owasp-top-ten p/security-audit p/secrets p/flask p/jwt p/sql-injection p/command-injection p/insecure-transport p/cwe-top-25`

---

## Achados por categoria CWE


- **CWE-704: Incorrect Type Conversion or Cast** — 33 achados
- **CWE-1357: Reliance on Insufficiently Trustworthy Component** — 3 achados
- **CWE-353: Missing Support for Integrity Check** — 3 achados
- **CWE-79: Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting')** — 3 achados
- **CWE-250: Execution with Unnecessary Privileges** — 1 achados
- **CWE-614: Sensitive Cookie in HTTPS Session Without 'Secure' Attribute** — 1 achados
- **CWE-295: Improper Certificate Validation** — 1 achados
- **CWE-668: Exposure of Resource to Wrong Sphere** — 1 achados
- **CWE-489: Active Debug Code** — 1 achados
- **CWE-522: Insufficiently Protected Credentials** — 1 achados
- **CWE-287: Improper Authentication** — 1 achados
- **CWE-89: Improper Neutralization of Special Elements used in an SQL Command ('SQL Injection')** — 1 achados

---

## Achados por arquivo × regra


| Arquivo | Linha | Severidade | Regra | Descrição |
|---|---|---|---|---|
| `.github/workflows/deploy.yml` | 20 | AVISO | `github-actions-mutable-action-tag` | GitHub Actions step uses a mutable tag or branch reference. Tags and branch names can be silently re... |
| `.github/workflows/deploy.yml` | 23 | AVISO | `github-actions-mutable-action-tag` | GitHub Actions step uses a mutable tag or branch reference. Tags and branch names can be silently re... |
| `.github/workflows/reset.yml` | 36 | AVISO | `github-actions-mutable-action-tag` | GitHub Actions step uses a mutable tag or branch reference. Tags and branch names can be silently re... |
| `Dockerfile` | 29 | ERRO | `missing-user` | By not specifying a USER, a program in the container may run as 'root'. This is a security hazard. I... |
| `app.py` | 395 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 430 | AVISO | `secure-set-cookie` | Found a Flask cookie with insecurely configured properties.  By default the secure, httponly and sam... |
| `app.py` | 506 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 600 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 707 | ERRO | `disabled-cert-validation` | Certificate verification has been explicitly disabled. This permits insecure connections to insecure... |
| `app.py` | 1147 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 1174 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 1273 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 1323 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 1371 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 1601 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 1651 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 1696 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 1748 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 1780 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 1839 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 2041 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 2078 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 2085 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 2117 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 2231 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 2496 | AVISO | `avoid_app_run_with_bad_host` | Running flask app with host 0.0.0.0 could expose the server publicly.... |
| `app.py` | 2496 | AVISO | `debug-enabled` | Detected Flask app with debug=True. Do not deploy to production with this flag enabled as it will le... |
| `auth.py` | 29 | ERRO | `jwt-python-hardcoded-secret` | Hardcoded JWT secret or private key is used. This is a Insufficiently Protected Credentials weakness... |
| `auth.py` | 47 | ERRO | `unverified-jwt-decode` | Detected JWT token decoded with 'verify=False'. This bypasses any integrity checks for the token whi... |
| `auth.py` | 120 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `auth.py` | 153 | AVISO | `sql-injection-db-cursor-execute` | User-controlled data from a request is passed to 'execute()'. This could lead to a SQL injection and... |
| `auth.py` | 157 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `auth.py` | 185 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `auth.py` | 190 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `auth.py` | 191 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `auth.py` | 195 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `merchant_payments.py` | 61 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `merchant_payments.py` | 76 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `merchant_payments.py` | 160 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `merchant_payments.py` | 209 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `merchant_payments.py` | 266 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `merchant_payments.py` | 436 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `merchant_payments.py` | 501 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `merchant_payments.py` | 554 | ERRO | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `templates/admin.html` | 219 | AVISO | `template-unescaped-with-safe` | Detected a segment of a Flask template where autoescaping is explicitly disabled with '\| safe' filte... |
| `templates/dashboard.html` | 81 | AVISO | `template-unescaped-with-safe` | Detected a segment of a Flask template where autoescaping is explicitly disabled with '\| safe' filte... |
| `templates/dashboard.html` | 166 | AVISO | `template-unescaped-with-safe` | Detected a segment of a Flask template where autoescaping is explicitly disabled with '\| safe' filte... |

---

## Categorias de risco críticas


### Injeção de SQL (33 sinks)

Todos no formato `f"SELECT/UPDATE/INSERT ... WHERE x='{user_input}'..."`. Cada um está documentado no código com `# Vulnerability: SQL Injection possible`. Parâmetros vulneráveis incluem `username`, `password`, `account_number`, `card_id`, `category_id`, `merchant_id`, `api_key`, `email`, etc.


### Autenticação & JWT (auth.py)

- L29 — JWT assinado com **segredo hardcoded** (`jwt.encode(payload, JWT_SECRET, ...)` onde `JWT_SECRET` está no repositório)

- L47 — JWT decodificado com `verify_signature=False` (aceita qualquer token forjado)


### Segurança do servidor

- app.py L707 — `requests.get(..., verify=False)` (validação TLS desabilitada para o proxy de imagem → MITM possível)

- app.py L430 — cookie de sessão definido sem `Secure` ou `SameSite`

- app.py L2496 — `app.run(host=0.0.0.0, debug=True)` (expõe o debugger do Werkzeug / RCE se alcançado)

- Dockerfile L29 — sem diretiva `USER` → container roda como root


### Template injection / XSS

- templates/dashboard.html L81 — `{{ username | safe }}` (saudação controlada por admin → stored XSS)

- templates/dashboard.html L166 — `{{ user_bio|safe }}` (bio controlada pelo usuário → stored XSS)

- templates/admin.html L219 — `{{ user[1]|safe }}` (username controlado por admin → stored XSS)


### Supply chain

- .github/workflows/deploy.yml L20 — `actions/checkout@v4` (tag major mutável, pode ser sequestrada via repointing de tag)

- .github/workflows/deploy.yml L23 — `webfactory/ssh-agent@v0.8.0` (tag minor mutável)

- .github/workflows/reset.yml L36 — mesmo `webfactory/ssh-agent@v0.8.0`


---

## Referência cruzada com a lista de vulnerabilidades do README


O README do repositório documenta muitas "Vulnerabilidades Implementadas" — o Semgrep confirmou TODAS essas classes via evidência estática:


| Vulnerabilidade do README | Evidência no Semgrep |
|---|---|
| SQL Injection no login | auth.py L120, L157, L185-195 |
| Implementação fraca de JWT | auth.py L29 (segredo hardcoded), L47 (verify=False) |
| BOLA / mass-assignment | app.py L1748, L1779, L1839, L2115 (cartões acessados por id sem checagem de propriedade) |
| Reset de senha fraco (PIN de 3 dígitos) | Não sinalizado pelo Semgrep mas visível no código-fonte |
| Token em localStorage | Lado JS, fora do escopo Python do Semgrep |
| Sem expiração de sessão | JWT emitido sem claim `exp` — veja contexto de auth.py L29 |
| Paginação ausente | Comentado em app.py L1695, L2230 |
| CSRF ausente | Comentado em app.py L1746 |
| Modo debug habilitado | app.py L2496 |
| Validação TLS ausente | app.py L707 |

---

## Arquivos NÃO revisados


- `static/dashboard.js` (1410 linhas) — superfície importante para XSS/vulns JS, mas JS não está nos configs do Semgrep utilizados

- `static/merchant.js`, `static/vuln-disclaimer.js` — idem

- `graphql/*.graphql` — apenas schemas, não executáveis

- `ai_agent_deepseek.py` — agente LLM com system prompt; checar separadamente sinks de prompt injection (o agente llm_injection do Frieren cobre isso)

- `tests/` — não relevante para segurança
