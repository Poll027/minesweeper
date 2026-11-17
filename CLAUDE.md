# Project instructions

Read `PROJECT_CONTEXT.md` (status, decisions, working conventions) and `WORK_LOG.md`
(chronological record of every change) at the start of each session.

## Working log rule

After every change to the repo (file created/edited/deleted, dataset pulled, script run
that produced output, decision made in chat), append an entry to `WORK_LOG.md` before
ending the turn. Newest entry at the bottom. Format:

```
## YYYY-MM-DD — short title
- **What:** what changed (files, commands, outputs)
- **Why:** the reasoning / decision, and who made it
- **State after:** what now works / what is still open
```

Record decisions and findings as well as code changes. Keep entries factual; no
speculation. `WORK_LOG.md` is meant to be pasted into a fresh chat to restore full
context, so each entry must make sense on its own.

## Conventions

- Design: follow the vibe-wise process (ask for Folajuwon's approach first, discuss
  tradeoffs, he decides when ready).
- Code in `detector/` and `training/`: default is segment by segment. Show the code in
  chat with explanations; Folajuwon types it out himself. Do not write those files
  unless he explicitly says to for a specific task. He can override per scenario.
- Full details: "Working conventions" in `PROJECT_CONTEXT.md`.
