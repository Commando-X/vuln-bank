# Task: Create Shared AI Learnings & Process Suggestions Doc

**Status:** Queued
**Created:** March 6, 2026
**Priority:** Medium
**Scope:** Moderate
**Depends on:** 01 (workflow setup must be merged first)
**Parallel safe with:** 02
**Executed by:** --
**Completed:**
**PR:**

---

## What

Create a living document in the repo that both AI models (Claude Code and Cursor) can read and contribute to. This doc captures:
1. Things learned through the multi-model collaboration process
2. Suggestions for process changes that would make life easier for the AI models
3. Friction points, workarounds, and coordination improvements

## Why

AI models encounter process friction that humans don't always see — index update timing, branch conflicts, ambiguous task ownership, etc. Having a shared doc where both models can log these observations creates a feedback loop that improves the workflow over time. It also gives the human operators visibility into what's working and what isn't from the AI perspective.

## Acceptance Criteria

- [ ] Doc has clear sections: Learnings, Process Suggestions, Friction Points, Resolved Items
- [ ] Both models know to check and update it (referenced in CLAUDE.md and .cursorrules)
- [ ] Format supports appending entries without merge conflicts (each entry is self-contained with date and model attribution)
- [ ] Initial entries seeded from what we've already learned in this setup session

## Files to Edit

- `.workflow/ai-learnings.md` (new)
- `CLAUDE.md` (add reference to the learnings doc)
- `.cursorrules` (add reference to the learnings doc)

## Notes

- Structure entries as: date, model name, category (Learning / Suggestion / Friction), description
- Keep entries short and actionable
- Either model can propose process changes here; human operators review and decide whether to adopt them

---

*When complete: update STATUS.md, tasks/index.md.*
