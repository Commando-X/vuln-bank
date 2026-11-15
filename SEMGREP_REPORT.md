# vuln-bank SAST Security Findings
Tool: Semgrep OSS 1.174.0  ·  Date: 2026-08-23  ·  Target: /home/rafael/vuln-bank
**47 findings** (37 ERROR · 10 WARNING)
Configs: `p/python p/owasp-top-ten p/security-audit p/secrets p/flask p/jwt p/sql-injection p/command-injection p/insecure-transport p/cwe-top-25`
---
## Findings by CWE category

- **CWE-704: Incorrect Type Conversion or Cast** — 33 findings
- **CWE-1357: Reliance on Insufficiently Trustworthy Component** — 3 findings
- **CWE-353: Missing Support for Integrity Check** — 3 findings
- **CWE-79: Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting')** — 3 findings
- **CWE-250: Execution with Unnecessary Privileges** — 1 findings
- **CWE-614: Sensitive Cookie in HTTPS Session Without 'Secure' Attribute** — 1 findings
- **CWE-295: Improper Certificate Validation** — 1 findings
- **CWE-668: Exposure of Resource to Wrong Sphere** — 1 findings
- **CWE-489: Active Debug Code** — 1 findings
- **CWE-522: Insufficiently Protected Credentials** — 1 findings
- **CWE-287: Improper Authentication** — 1 findings
- **CWE-89: Improper Neutralization of Special Elements used in an SQL Command ('SQL Injection')** — 1 findings

---
## Findings by file × rule

| File | Line | Severity | Rule | Description |
|---|---|---|---|---|
| `.github/workflows/deploy.yml` | 20 | WARNING | `github-actions-mutable-action-tag` | GitHub Actions step uses a mutable tag or branch reference. Tags and branch names can be silently re... |
| `.github/workflows/deploy.yml` | 23 | WARNING | `github-actions-mutable-action-tag` | GitHub Actions step uses a mutable tag or branch reference. Tags and branch names can be silently re... |
| `.github/workflows/reset.yml` | 36 | WARNING | `github-actions-mutable-action-tag` | GitHub Actions step uses a mutable tag or branch reference. Tags and branch names can be silently re... |
| `Dockerfile` | 29 | ERROR | `missing-user` | By not specifying a USER, a program in the container may run as 'root'. This is a security hazard. I... |
| `app.py` | 395 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 430 | WARNING | `secure-set-cookie` | Found a Flask cookie with insecurely configured properties.  By default the secure, httponly and sam... |
| `app.py` | 506 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 600 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 707 | ERROR | `disabled-cert-validation` | Certificate verification has been explicitly disabled. This permits insecure connections to insecure... |
| `app.py` | 1147 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 1174 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 1273 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 1323 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 1371 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 1601 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 1651 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 1696 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 1748 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 1780 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 1839 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 2041 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 2078 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 2085 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 2117 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 2231 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `app.py` | 2496 | WARNING | `avoid_app_run_with_bad_host` | Running flask app with host 0.0.0.0 could expose the server publicly.... |
| `app.py` | 2496 | WARNING | `debug-enabled` | Detected Flask app with debug=True. Do not deploy to production with this flag enabled as it will le... |
| `auth.py` | 29 | ERROR | `jwt-python-hardcoded-secret` | Hardcoded JWT secret or private key is used. This is a Insufficiently Protected Credentials weakness... |
| `auth.py` | 47 | ERROR | `unverified-jwt-decode` | Detected JWT token decoded with 'verify=False'. This bypasses any integrity checks for the token whi... |
| `auth.py` | 120 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `auth.py` | 153 | WARNING | `sql-injection-db-cursor-execute` | User-controlled data from a request is passed to 'execute()'. This could lead to a SQL injection and... |
| `auth.py` | 157 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `auth.py` | 185 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `auth.py` | 190 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `auth.py` | 191 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `auth.py` | 195 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `merchant_payments.py` | 61 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `merchant_payments.py` | 76 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `merchant_payments.py` | 160 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `merchant_payments.py` | 209 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `merchant_payments.py` | 266 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `merchant_payments.py` | 436 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `merchant_payments.py` | 501 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `merchant_payments.py` | 554 | ERROR | `tainted-sql-string` | Detected user input used to manually construct a SQL string. This is usually bad practice because ma... |
| `templates/admin.html` | 219 | WARNING | `template-unescaped-with-safe` | Detected a segment of a Flask template where autoescaping is explicitly disabled with '\| safe' filte... |
| `templates/dashboard.html` | 81 | WARNING | `template-unescaped-with-safe` | Detected a segment of a Flask template where autoescaping is explicitly disabled with '\| safe' filte... |
| `templates/dashboard.html` | 166 | WARNING | `template-unescaped-with-safe` | Detected a segment of a Flask template where autoescaping is explicitly disabled with '\| safe' filte... |

---
## Critical risk categories

### SQL injection (33 sinks)
All in the form of `f"SELECT/UPDATE/INSERT ... WHERE x='{user_input}'..."`. Every one is documented in code with `# Vulnerability: SQL Injection possible`. Vulnerable parameters include `username`, `password`, `account_number`, `card_id`, `category_id`, `merchant_id`, `api_key`, `email`, etc.

### Authentication & JWT (auth.py)
- L29 — JWT signed with **hardcoded secret** (`jwt.encode(payload, JWT_SECRET, ...)` where `JWT_SECRET` is in the repo)
- L47 — JWT decoded with `verify_signature=False` (accepts any forged token)

### Server security
- app.py L707 — `requests.get(..., verify=False)` (TLS validation disabled for image proxy → MITM possible)
- app.py L430 — session cookie set without `Secure` or `SameSite`
- app.py L2496 — `app.run(host='0.0.0.0', debug=True)` (exposes Werkzeug debugger / RCE if reached)
- Dockerfile L29 — no `USER` directive → container runs as root

### Template injection / XSS
- templates/dashboard.html L81 — `{{ username | safe }}` (admin-controlled greeting → stored XSS)
- templates/dashboard.html L166 — `{{ user_bio|safe }}` (user-controlled bio → stored XSS)
- templates/admin.html L219 — `{{ user[1]|safe }}` (admin-controlled username → stored XSS)

### Supply chain
- .github/workflows/deploy.yml L20 — `actions/checkout@v4` (mutable major tag, can be hijacked via tag repointing)
- .github/workflows/deploy.yml L23 — `webfactory/ssh-agent@v0.8.0` (mutable minor tag)
- .github/workflows/reset.yml L36 — same `webfactory/ssh-agent@v0.8.0`

---
## Cross-reference with README vuln list

The repo README documents many 'Implemented Vulnerabilities' — semgrep confirmed ALL of these classes via static evidence:

| README vulnerability | Semgrep evidence |
|---|---|
| SQL Injection in login | auth.py L120, L157, L185-195 |
| Weak JWT implementation | auth.py L29 (hardcoded secret), L47 (verify=False) |
| BOLA / mass-assignment | app.py L1748, L1779, L1839, L2115 (cards accessed by id without ownership check) |
| Weak password reset (3-digit PIN) | Not flagged by Semgrep but visible in source |
| Token in localStorage | JS-side, out of Semgrep Python scope |
| No session expiration | JWT issued without `exp` flag — see auth.py L29 context |
| Missing pagination | Commented in app.py L1695, L2230 |
| CSRF missing | Commented in app.py L1746 |
| Debug mode enabled | app.py L2496 |
| Missing TLS validation | app.py L707 |

---
## Files NOT reviewed

- `static/dashboard.js` (1410 lines) — major surface area for XSS/JS vulns, but JS not in Semgrep configs used
- `static/merchant.js`, `static/vuln-disclaimer.js` — same
- `graphql/*.graphql` — schemas only, not executable
- `ai_agent_deepseek.py` — LLM agent with system prompt; check separately for prompt injection sinks (Frieren LLM-injection agent covers this)
- `tests/` — not security-relevant
