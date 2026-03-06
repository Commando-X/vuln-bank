# Vuln Bank — Decision Log

## Project Metadata

| Field | Value |
|-------|-------|
| **Project Name** | Vuln Bank |
| **Repository** | https://github.com/hrpatel/vuln-bank |
| **Live URL** | N/A (local Docker) |
| **Tech Stack** | Python, Flask, SQLite, HTML/CSS/JS |
| **Started** | March 2026 |
| **Status** | Active |
| **Primary AI Tools** | Claude Code, Cursor |

---

## Entries

### Getting Organized

**Summary:** Setting up workflow and coordination for multi-model collaboration
**Sessions:** 1
**AI Tools:** Claude Code

---

#### Multi-Model Coordination Protocol
- **Type:** Decision
- **Category:** Process
- **Context:** Two AI models (Claude Code and Cursor) need to work on the same repo in parallel without stepping on each other.
- **What happened:** Adopted a task-index-based coordination protocol with file-level conflict detection, branch isolation per model, and status signaling in the shared task index.
- **Alternatives considered:** (1) Domain separation (backend vs frontend ownership) — too rigid. (2) Sequential turns — too slow, kills parallelism. (3) Forking the repo per model — too much overhead to sync.
- **Why this path:** Uses existing task tracking infrastructure. File-level conflict detection is simple and sufficient. Branch prefixes make ownership visible. The task index is the single coordination point.
- **Outcome:** [pending — first session]

#### Workflow Documentation in Repo
- **Type:** Decision
- **Category:** Process
- **Context:** Both models need access to the workflow system. Cursor reads from the repo; Claude Code reads from CLAUDE.md and repo files.
- **What happened:** Added `.workflow/` directory with adapted workflow docs, `.cursorrules` for Cursor, and `CLAUDE.md` for Claude Code. Both point to the same underlying workflow.
- **Why this path:** Each model has its own entry point (`.cursorrules` vs `CLAUDE.md`) but shares the same workflow docs. No duplication of process rules.
- **Outcome:** [pending — first session]

---

## Appendix: Glossary

| Term | Meaning |
|------|---------|
| Vuln Bank | The deliberately vulnerable banking app |
| Claude Code | AI model operated via CLI by Michael |
| Cursor | AI model operated via IDE by coworker |
| Task Index | `tasks/index.md` — the coordination point for parallel work |

---

*For use with the Meta Tracker app (meta.jynaxxapps.com)*
