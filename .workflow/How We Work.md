# How We Work — Multi-Model Collaboration

## Team Structure

### Human Operators
- **Operator A** — uses Claude Code (CLI)
- **Operator B** — uses Cursor

Both operators:
- Assign tasks to their respective AI models
- Review and merge PRs (AI models never merge)
- Make product and priority decisions
- Coordinate via their own communication channels

### AI Models
- **Claude Code** — works via CLI, creates branches and PRs
- **Cursor** — works via IDE, creates branches and PRs

Both models:
- Read the workflow docs at session start
- Check for conflicts before starting work
- Claim tasks in the index before working on them
- Create PRs for all code changes
- Never merge, never push directly to main

## Coordination Protocol

### The Task Index is the Source of Truth

`tasks/index.md` is where both models check for work and signal what they're doing. The status column tells everyone what's happening:

| Status | Meaning |
|--------|---------|
| `Queued` | Available for either model to pick up |
| `In Progress (Claude Code)` | Claude Code is actively working on this |
| `In Progress (Cursor)` | Cursor is actively working on this |
| `In Review` | PR created, waiting for human review/merge |
| `Done` | Merged and complete |

### Before Starting a Task

1. Read `tasks/index.md`
2. Find a `Queued` task (or create one if your operator gives you new work)
3. Check its "Files to Edit" against all `In Progress` tasks from the other model
4. If there's a file overlap → pick a different task or wait
5. If no overlap → update the index to claim the task, then start working

### Branch Naming

Use a consistent pattern so it's clear who's working on what:
- Claude Code: `claude/{##}-{task-slug}`
- Cursor: `cursor/{##}-{task-slug}`

Example: `claude/03-add-xss-scenario`, `cursor/04-update-auth-tests`

### Handling Conflicts

If both models accidentally start tasks that touch the same files:
1. The model that started **second** (later timestamp in the index) yields
2. That model stashes or shelves its work
3. Wait for the first model's PR to merge
4. Rebase and continue

If a merge conflict arises in a PR, the model that created the PR resolves it.

## Workflow

1. Operator describes what they want
2. AI model asks clarifying questions if needed
3. AI model checks the task index for conflicts
4. AI model creates a task file (if one doesn't exist) and claims it in the index
5. AI model works on a feature branch
6. AI model creates a PR
7. **Human merges** the PR
8. AI model updates the task index, STATUS.md, and other tracking docs

## Communication Style

### Keep It Quiet
- **DO:** Report outcomes ("PR created, ready to merge")
- **DO:** Surface blockers and decisions that need input
- **DON'T:** Narrate intermediate steps
- **DON'T:** Describe what you're about to do before doing it

## Code Review

### Every PR Gets Reviewed Before Merge
The creating model should review its own diff before flagging the PR as ready. Check for:
- No unintended file changes
- No hardcoded secrets or credentials
- Existing functionality isn't broken
- Changes match the task description

### Review Priority

| Change Type | Review Level |
|-------------|-------------|
| Config, docs, templates | Quick scan — low risk |
| Single-file changes | Read the diff — medium risk |
| Multi-file features | Careful review — higher risk |
| Security-related changes | Extra scrutiny — this is a security project |

## Decision Tracking

Every significant decision gets logged in `decisions.md`. This creates a record of how the project evolved, useful for both models and both operators.

## Iteration Patterns

1. **Small, targeted PRs** — one concern per PR
2. **Branch isolation** — each model on its own branch
3. **Task ownership** — claimed in the index, no ambiguity
4. **File-level conflict detection** — "Files to Edit" is the mechanism
5. **Sequential within chains, parallel across chains** — dependency chains are respected; independent tasks run simultaneously
6. **Research before building** — don't default to the first approach; find the best one

---

*Last updated: March 6, 2026*
