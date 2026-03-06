# Task: Create Generic Multi-Model Bootstrap Template

**Status:** Queued
**Created:** March 6, 2026
**Priority:** Medium
**Scope:** Moderate
**Depends on:** 01 (workflow setup must be merged first)
**Parallel safe with:** 03
**Executed by:** --
**Completed:**
**PR:**

---

## What

Create a generic, reusable bootstrap document that captures the process for setting up multi-model AI collaboration on any new repo. This is a template — not specific to Vuln Bank — so that the next time we want two (or more) AI models working on the same codebase, we can follow a checklist instead of figuring it out from scratch.

## Why

We just went through this setup process for the first time (Claude Code + Cursor on vuln-bank). The steps — creating entry points for each model, coordination protocols, task tracking, conflict avoidance — should be captured as a repeatable playbook.

## Acceptance Criteria

- [ ] Bootstrap doc covers: repo setup checklist, model entry point files to create, coordination protocol setup, task index structure, branch naming conventions
- [ ] Generic enough to work for any repo, any pair of AI models (not just Claude Code + Cursor)
- [ ] Lives in `.workflow/` so both models can reference it
- [ ] Also copied to the local `_Shared/` folder for use on future projects

## Files to Edit

- `.workflow/bootstrap-multi-model.md` (new)
- Local: `_Shared/Decision Framework/bootstrap-multi-model.md` (new)

## Notes

- Draw from what we did in the workflow-setup PR as the source material
- Include gotchas we hit (PAT permissions, file-level conflict detection, index as coordination bottleneck)
- Keep it practical — checklist format, not essay format

---

*When complete: update STATUS.md, tasks/index.md.*
