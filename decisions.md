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

## How to Log Decisions

Each entry uses a structured format that feeds into Meta Tracker's decision tree. The key fields:

| Field | Values | When to Use |
|-------|--------|-------------|
| **Type** | decision · event · dead-end · discovery · pivot | What kind of entry this is |
| **Category** | technical · functional · ux-design · process | What domain it belongs to |
| **Chosen path** | Free text | What we actually did (decisions/pivots only) |
| **Alternatives** | List | What else we considered (decisions/pivots only) |
| **Failure reason** | Free text | Why it didn't work (dead-ends only) |

Both models should log decisions — not just the model that made them. If Cursor discovers something important, log it here.

---

## Entries

### Getting Organized

**Summary:** Setting up workflow and coordination for multi-model collaboration
**Sessions:** 1
**Phase:** Spec
**AI Tools:** Claude Code

---

#### Multi-Model Coordination Protocol
- **Type:** decision
- **Category:** process
- **Context:** Two AI models (Claude Code and Cursor) need to work on the same repo in parallel without stepping on each other.
- **Chosen path:** Task index coordination with branch prefixes and file-level conflict detection
- **Alternatives:** (1) Domain separation (backend vs frontend ownership) — too rigid. (2) Sequential turns — too slow, kills parallelism. (3) Forking the repo per model — too much overhead to sync.
- **Why this path:** Uses existing task tracking infrastructure. File-level conflict detection is simple and sufficient. Branch prefixes make ownership visible. The task index is the single coordination point.
- **Outcome:** Implemented in PR #1

#### Workflow Documentation in Repo
- **Type:** decision
- **Category:** process
- **Context:** Both models need access to the workflow system. Cursor reads from the repo; Claude Code reads from CLAUDE.md and repo files.
- **Chosen path:** Shared .workflow/ docs with model-specific entry points (.cursorrules, CLAUDE.md)
- **Alternatives:** (1) External docs only. (2) Single shared config file.
- **Why this path:** Each model has its own entry point (`.cursorrules` vs `CLAUDE.md`) but shares the same workflow docs. No duplication of process rules.
- **Outcome:** Implemented in PR #1

---

## Appendix: Entry Types

| Type | Use When |
|------|----------|
| **decision** | A deliberate choice between alternatives |
| **event** | Something noteworthy happened (milestone, external change) |
| **dead-end** | An approach was tried and abandoned |
| **discovery** | Something was learned that changed understanding |
| **pivot** | Direction changed mid-task |

## Appendix: Glossary

| Term | Meaning |
|------|---------|
| Vuln Bank | The deliberately vulnerable banking app |
| Claude Code | AI model operated via CLI by Michael |
| Cursor | AI model operated via IDE by coworker |
| Task Index | `tasks/index.md` — the coordination point for parallel work |
| Meta Tracker | Dashboard that visualizes project decisions and metrics (meta.jynaxxapps.com) |

---

*For use with the Meta Tracker app (meta.jynaxxapps.com)*
