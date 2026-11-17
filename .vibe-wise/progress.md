# Learning Progress

## Email augmentation (InjecAgent ds files)
- Introduced: reserved email domains (RFC 2606/6761) as the way to make an address non-deliverable; class-consistent sanitizing so domain cannot become a label shortcut.
- Learner decisions: replacement list is built from emails mined by `mine_negatives.py`; round-robin rotation over records, `amy.watson@gmail.com` is one entry in the list (so ~1/N of records keep it); a "pass" = one full rotation, wrapping until all entries are assigned; idea to alter mined emails by dropping real names / the `@gmail.com` suffix.
- Demonstrated understanding: recognized personal-address risk and proposed altering mined emails.
- Learner chose: sanitize both injection and benign emails identically; wanted generated names and varied "mail providers" instead of gmail.
- Claude explained: file order is payload-major (position i -> group i//17, wrapper i%17), so rotation of length 17k in record order ties emails to wrapper templates; shuffle fixes it.
- Design confirmed by learner (Confirm and continue) including Claude's proposed additions: reserved TLDs, junk filter + dedupe, seeded shuffle then rotate, independent emails for base/enhanced twins, manifest with seed/pool/assignments.
- Segment 1 typed and passing by learner. Debugged own typos: missing backslash in `[\w.+-]` (regex matched nothing, text returned unchanged), `PROVIDER` vs `PROVIDERS` name mismatch, an assertion inverted. Read a failing assert/traceback and traced it to the cause with help.
- Needs reinforcement: dropping the suffix alone leaves no valid email; where sanitizing happens so both classes are treated identically; ordering/periodicity risk when list length shares a factor with 17 or 32.

## Pending decision
Benign email-rate gap - learner chose A (bigger targeted benign search) + D (email-presence-only baseline + swap probe), B as fallback, rejected C. Stage: awaiting reasoning on the target benign email rate and miner design before an Implementation checkpoint. Other open items: Segment 2 pool builder; AgentDyn scope (220-row extracted file of unknown origin, 7 suites).
