# START HERE

**Read this file first. Every session. No exceptions.**

---

## The Rules

1. **Work quietly.** Don't narrate intermediate steps. Surface results, blockers, and decisions only.
2. **Humans merge.** AI models never merge PRs. They create them, review them, flag them as ready.
3. **Tasks are sequential unless marked parallel-safe.** Parallel tasks touching the same files can revert each other.
4. **Ask before acting on anything destructive or ambiguous.** When in doubt, ask.
5. **Check for conflicts before starting.** Read `tasks/index.md` and verify no in-progress task from the other model touches your files.
6. **Claim your work.** Update the task index status when you start and finish a task.

## Before You Build

When approaching any implementation task, don't default to the obvious solution. Before writing code, ask:

- Is there a better pattern for this? Research best-in-class approaches for the problem type.
- Are there established libraries or utilities already in the stack that handle this well?
- What do leading products do for this same problem?
- Is there a simpler solution that achieves the same outcome with less code?

A few minutes of research before implementing saves multiple iteration cycles after.

## How to Start a Session

1. Read this file (you're doing it now).
2. Read `CLAUDE.md` (if you're Claude Code) or `.cursorrules` (if you're Cursor) for model-specific instructions.
3. Check `STATUS.md` for current project state.
4. Check `tasks/index.md`. If there are queued tasks, pick the next one that doesn't conflict with any in-progress work.
5. If no tasks are queued, ask your operator what to work on.

## Task Workflow

- Tasks live in `tasks/` as individual `.md` files.
- `tasks/index.md` lists all tasks at a glance with status and ownership.
- When you finish a task, mark it Done in the index and move the task file to `tasks/done/`.
- Update `STATUS.md`, `decisions.md`, and `metrics.md` as part of completing any task that warrants it.

## Task Dependencies & Parallel Work

Every task file must include these fields in its header:

- **Depends on:** List any task numbers that must be completed first. Use `None` if independent.
- **Parallel safe with:** List task numbers that can safely run at the same time, or `Any non-overlapping` if it doesn't touch shared files.
- **Files to Edit:** List all files this task will modify — this enables conflict detection.

**How to assess parallel safety:** Two tasks conflict if they modify the same file. Check the "Files to Edit" section of all In Progress tasks before starting yours.

## Creating New Tasks

1. **Number it sequentially.** Check the index for the next available number. Use `{##}-{slug}.md` format.
2. **List files touched.** Every task must have a "Files to Edit" section.
3. **Check for dependencies.** Scan all open tasks. If any open task touches the same files, note the dependency.
4. **Fill all header fields.** Status, Created, Priority, Depends on, Parallel safe with, Executed by, Completed, PR.

## Task Completion Checklist

1. **Task file updated** — status set to Done, acceptance criteria checked off.
2. **Index updated** — task marked Done in `tasks/index.md`.
3. **Task file moved** — from `tasks/` to `tasks/done/`.
4. **Metrics updated** — if code was shipped, update `metrics.md`.
5. **Decisions updated** — if a significant decision was made, update `decisions.md`.
6. **STATUS.md updated** — reflect the current project state.

## Review Cadence

**After every 2-3 merges**, do a quick review pass:

1. **Build check** — verify the application runs correctly.
2. **Data integrity** — check for mismatched references or broken functionality.
3. **Bug logging** — any issues found get logged in `metrics.md`.
4. **Flag for review** — note anything for the human operators to check.

## Key References

| Doc | Location | When to Read |
|-----|----------|-------------|
| **STATUS.md** | Repo root | Every session |
| **How We Work** | `.workflow/` | When you need process details |
| **Tips & Lessons** | `.workflow/` | When you hit a technical snag |
| **decisions.md** | Repo root | When you need project history |
| **metrics.md** | Repo root | When updating tracking data |
| **tasks/index.md** | `tasks/` | Before starting any work |

---

*Adapt these guidelines to your workflow. Last updated: March 6, 2026.*
