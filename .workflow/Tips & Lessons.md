# Tips & Lessons Learned

Hard-won knowledge from AI-assisted development. Add new entries as you discover them.

---

## Multi-Model Coordination

- **The task index is the lock.** Before starting any work, read `tasks/index.md`. If another model has an In Progress task touching the same files, pick something else.
- **Branch naming signals ownership.** Use `claude/` or `cursor/` prefixes so it's obvious who's working where.
- **File-level granularity is enough.** You don't need line-level locking — if two tasks touch the same file, they conflict. Keep tasks scoped to avoid this.
- **Update the index immediately.** Claim your task before you start coding, not after. The gap between "I decided to work on this" and "I updated the index" is where collisions happen.

## AI Code Generation

- **Be extremely specific in prompts:** Exact file paths, exact code patterns, exact replacements. Tell the tool what NOT to change.
- **Sequential tasks within dependency chains.** Parallel tasks touching the same files can revert each other's changes.
- **Check diffs carefully.** AI tools sometimes touch more files than asked. Always review the full diff before committing.

## Security Testing Context

- **This is a deliberately vulnerable app.** Vulnerabilities are features, not bugs. Don't "fix" intentional vulnerabilities unless explicitly asked to.
- **Document each vulnerability clearly.** Include: what the vulnerability is, where it lives, how to exploit it, and how a real app would fix it.
- **Separate intentional vulns from real bugs.** If you find an actual bug (not an intentional vulnerability), log it in `metrics.md`.

## GitHub & PRs

- **All changes through PRs.** No direct pushes to main.
- **Keep PRs focused.** One task per PR makes review easier and rollback safer.
- **PAT tokens:** Never hardcode tokens in committed files.

## Code Review

- **Deep review via source analysis:** For large PRs, read the full source file, not just the diff.
- **Parity checks:** When adding a second way to do something, verify the new path matches the existing one in behavior.

## Session Management

- **Living docs over session notes.** STATUS.md is always current — no versioned passoff documents needed.
- **Update tracking docs as part of the work**, not as a separate ritual at the end.

---

*Add new entries as they're discovered. Keep it practical — this is a reference, not a journal.*
