# Vuln Bank — Claude Code Instructions

**Read this file first. Every session. No exceptions.**

## Quick Start

1. Read this file (you're doing it now)
2. Read `STATUS.md` for current project state
3. Read `tasks/index.md` for the work queue
4. Check for any tasks marked **In Progress (Cursor)** — avoid file conflicts with those
5. Pick the next available task or ask Michael what to work on

## Multi-Model Coordination

This repo is worked on by **two AI models in parallel**:
- **Claude Code** (CLI) — operated by Michael
- **Cursor** — operated by a coworker

### The Rules

1. **Check before you start.** Before beginning any task, read `tasks/index.md`. If another model has a task In Progress that touches the same files, pick a different task.
2. **Claim your task.** When you start a task, update its status in the index to `In Progress (Claude Code)`.
3. **Branch per task.** Always work on a feature branch, never directly on main.
4. **PRs are the merge point.** Create PRs; humans merge.
5. **Update the index when done.** Mark your task as Done and move the task file to `tasks/done/`.

### Conflict Avoidance

Every task file has a "Files to Edit" section. This is the conflict-detection mechanism:
- If your task touches `app.py` and a Cursor task that's In Progress also touches `app.py`, **don't start yours yet**.
- If there's no file overlap, you're safe to work in parallel.
- When in doubt, ask Michael.

## Workflow Reference

Full workflow documentation is in `.workflow/`:
- `START HERE.md` — session rules and task workflow
- `How We Work.md` — roles, coordination protocol, review process
- `Tips & Lessons.md` — practical knowledge from AI-assisted development
- `task-template.md` — standard format for new task files

## Project Context

This is a deliberately vulnerable banking application for security testing practice. Work involves updating and extending the vulnerability bank — adding new vulnerability scenarios, improving existing ones, and maintaining the application.

## Code Changes

- All changes go through PRs — no direct pushes to main
- Michael or the coworker merges — AI models never merge
- Keep PRs focused: one concern per PR
