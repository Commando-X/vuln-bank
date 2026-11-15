# ggshield Secret Scan — vuln-bank

**Date:** 2026-08-23  ·  **Tool:** ggshield 1.45.0  ·  **Workspace:** 922945  ·  **Target:** /home/rafael/vuln-bank (git history)

---

## Resumo


| Métrica | Valor |
|---|---|
| Commits analisados | 7 |
| Arquivos analisados | 10 |
| **Secrets reportados** | **7** |
| Secrets ignorados (use `--all-secrets`) | 6 |

**Por tipo de detector:**

| # | Tipo |
|---|---|
| 4 | `Generic Password` |
| 2 | `Generic High Entropy Secret` |
| 1 | `DeepSeek API Key` |

**Por arquivo:**

| # | Arquivo |
|---|---|
| 3 | `.env` |
| 2 | `database.py` |
| 2 | `docker-compose.yml` |
| 1 | `.env.example` |
| 1 | `app.py` |
| 1 | `tests/test_merchant_payments.py` |

---

## Findings agrupados por secret SHA-256


Cada SHA-256 representa **um segredo único**; múltiplas ocorrências em arquivos diferentes são consolidadas.


| # | Tipo | Validade | Ocorrências | Arquivos | Incident |
|---|---|---|---|---|---|
| 1 | `Generic Password` | No Checker | 5 | `.env`, `.env.example`, `database.py`, `docker-compose.yml` | [link](https://dashboard.gitguardian.com/workspace/922945/incidents/36532012) |
| 2 | `DeepSeek API Key` | Invalid | 1 | `.env` | [link](https://dashboard.gitguardian.com/workspace/922945/incidents/36532013) |
| 3 | `Generic High Entropy Secret` | No Checker | 8 | `tests/test_merchant_payments.py` | [link](https://dashboard.gitguardian.com/workspace/922945/incidents/36532011) |
| 4 | `Generic High Entropy Secret` | No Checker | 1 | `app.py` | [link](https://dashboard.gitguardian.com/workspace/922945/incidents/36532014) |


---

## Findings detalhados



### Commit `e8b8af3` — (orphan) ((orphan))


**`database.py`** — 0 detected (1 ignored)



### Commit `0279dff` — threatmind-ai[bot] <302590686+threatmind-ai[bot]@users.noreply.github.com> (Thu Jul 23 21:42:49 2026 +0000)


**`docker-compose.yml`** — 0 detected (2 ignored)



### Commit `40bb39b` — Commando-X <badmusbodunrin@gmail.com> (Mon Feb 17 08:11:30 2025 +0100)


**`.env`** — 1 detected


- `Generic Password` — validity: No Checker, occurrences: 1, SHA: `6e0d657eb1f0fbc4…`

**`database.py`** — 1 detected


- `Generic Password` — validity: No Checker, occurrences: 1, SHA: `6e0d657eb1f0fbc4…`

**`docker-compose.yml`** — 1 detected


- `Generic Password` — validity: No Checker, occurrences: 2, SHA: `6e0d657eb1f0fbc4…`


### Commit `b6ba2be` — Badmus <badmusbodunrin@gmail.com> (Sat Jul 5 12:41:09 2025 +0100)


**`.env`** — 1 detected (1 ignored)


- `DeepSeek API Key` — validity: Invalid, occurrences: 1, SHA: `04a07ce0453a4256…`

**`.env.example`** — 1 detected


- `Generic Password` — validity: No Checker, occurrences: 1, SHA: `6e0d657eb1f0fbc4…`


### Commit `27b6f16` — Badmus <badmusbodunrin@gmail.com> (Sat Jul 5 12:44:41 2025 +0100)


**`.env`** — 0 detected (2 ignored)



### Commit `8db8c92` — Badmus <badmusbodunrin@gmail.com> (Sun May 3 17:47:01 2026 +0100)


**`tests/test_merchant_payments.py`** — 1 detected


- `Generic High Entropy Secret` — validity: No Checker, occurrences: 8, SHA: `a588a80ab6677466…`


### Commit `b6fea30` — Badmus <badmusbodunrin@gmail.com> (Mon Oct 13 19:22:32 2025 +0100)


**`app.py`** — 1 detected


- `Generic High Entropy Secret` — validity: No Checker, occurrences: 1, SHA: `0e0ce0a3e33eedb0…`
