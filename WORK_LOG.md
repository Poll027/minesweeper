# Work Log

Chronological record of everything done in this repo. Paste into a new chat to restore
context. Rules for entries are in `CLAUDE.md`. See `PROJECT_CONTEXT.md` for the standing
project description.

## 2026-11-05 — Repo wiped; context established
- **What:** Folajuwon deleted `detector/`, tests, README, Action/Dockerfile, requirements
  and venvs, leaving only `.claude/`, `training/data/raw/injecagent/` and
  `PROJECT_CONTEXT.md`. Claude read the repo and `PROJECT_CONTEXT.md`.
- **Why:** Clean slate; Folajuwon will rewrite the detector himself for Final Defence
  defensibility.
- **State after:** Claude's role = data acquisition scripts + design discussion in chat.
  No edits under `detector/` / `training/` without explicit exception.

## 2026-11-05 — InjecAgent email-augmentation: data checks and decisions
- **What:** Read-only inspection of `ds_base` / `ds_enhanced` (544 records each).
  Findings: (1) `Tool Response Template.replace(placeholder, Attacker Instruction)` does
  NOT reproduce `Tool Response` (response has an extra outer pair of double quotes);
  (2) `Attacker Instruction` is identical in base and enhanced — the enhanced override
  prefix ("IMPORTANT!!! Ignore all previous instructions...") exists only inside the
  enhanced `Tool Response`, so re-rendering from the template would drop it;
  (3) `amy.watson@gmail.com` occurs exactly once in every `Tool Response` (544/544 in both
  files); (4) 32 payload groups x 17 records, same group key across base/enhanced;
  (5) one group has a victim email `john.doe@gmail.com` (leave untouched, exclude from pool).
- **Why:** Spec step 4 (re-render from template) is unsafe; plain
  `Tool Response.replace(old_email, new_email)` is equivalent and avoids both problems.
- **Decisions (Folajuwon):** pool larger (>= ~40, varied styles/domains, fabricated names);
  keep some originals (~4-6 of 32 groups, chosen per group, spread across train and test;
  add `email_augmented` bool to schema); build negatives that contain emails; use one
  seeded `random.Random(SEED)` and write seed + pool to a manifest.
- **State after:** Augmentation + grouped split still to be written by Folajuwon. Open
  check: does each of the 32 groups have a single `Attack Type`?

## 2026-11-05 — Tooling: vibe-wise + working log
- **What:** Confirmed the vibe-wise plugin (v0.1.43) has a `SessionStart` hook that
  restores learning mode wherever `.vibe-wise/profile.md` exists. Added `CLAUDE.md`
  (project instructions incl. the work-log rule) and this file.
- **Why:** Folajuwon wants vibe-wise active every session and a full change record.
- **State after:** Folajuwon must run `/vibe-wise:learn` once in this project to create
  `.vibe-wise/profile.md`; after that it auto-restores.

## 2026-11-05 — GitHub negatives miner written (exception granted by Folajuwon)
- **What:** Created `training/scripts/mine_negatives.py` (stdlib + authenticated `gh` CLI).
  Pass 1 samples issues/PRs/comments from ~`--max-repos` active mid-popularity repos
  (stars 200-20000, pushed in last 60 days), skipping bots, texts <20 or >4000 chars,
  and duplicates (`--per-repo` cap). Pass 2 (`--email-search`) runs GitHub search queries
  for real text containing emails ("gmail.com", "contact me at", "send it to" email,
  "co-authored-by", "email" "@") to get email-bearing and hard "send X to Y" negatives.
  Output JSONL rows: text, label=benign, source, repo, kind, via, has_email, url,
  created_at. Seeded via `--seed`.
- **Why:** Pass 1 alone gave 0/128 email-bearing rows in a 4-repo test, which would let the
  classifier learn "email present => injection". Pass 2 lifted a 4-repo test to 57/217
  (26.3%). Folajuwon's decision 3: negatives must contain emails.
- **State after:** Tested only on 4 repos (output in scratchpad, not in repo). Full run not
  done yet: `python3 training/scripts/mine_negatives.py --out training/data/raw/github_negatives/negatives.jsonl`.
  Open: mined text is assumed benign, not verified (run Tier 1 as a sanity filter later);
  contains real people's emails, so keep raw output local/unpublished; use `repo` as the
  group key when splitting negatives; balance email rate vs. injection class downstream.

## 2026-11-05 — Working convention updated (Folajuwon's decision)
- **What:** Design follows the vibe-wise plugin process. Code default = segments: Claude
  shows code in chat with explanations, Folajuwon types it himself; no file writes under
  `detector/` or `training/` unless he explicitly says so per task. Updated "Working
  conventions" in `PROJECT_CONTEXT.md` and the Conventions section of `CLAUDE.md`. Also
  removed an unused `per_repo` parameter from `rows_for_repo` in `mine_negatives.py`
  (Pylance warning; behaviour unchanged, cap is still applied in `main`).
- **Why:** Final Defence defensibility plus learning-first workflow; resolves the earlier
  vibe-wise vs. "he writes the code" tension.
- **State after:** Next step is the InjecAgent email augmentation, done in segments.

## 2026-11-05 — vibe-wise learn mode set up
- **What:** Ran `/vibe-wise:learn` onboarding. Created `.vibe-wise/{profile,progress,project-map}.md`.
  Answers: Existing repo; knows codebase well; learning scope whole system; programming
  Intermediate; stack Beginner; checkpoints Normal; open-ended questions; coding style
  "More hands-on" (Claude shows code, he types it).
- **Why:** Folajuwon wants design decisions to be his own and every line defensible.
- **State after:** Learn mode restores automatically each session. `.vibe-wise/` is not in
  .gitignore (repo isn't under git; add if it becomes one). Next: InjecAgent email
  augmentation, starting with a Build checkpoint.

## 2026-11-05 — Email augmentation design (discussion, no code)
- **What:** Folajuwon's design so far: replacement list built from emails mined by the
  miner; round-robin over records; `amy.watson@gmail.com` is one entry in the list
  (decision 3: frequency = 1/N, replacing the earlier "keep ~15% of groups"); one "pass" =
  one full rotation, wrap until every entry is assigned. Idea: alter mined emails (drop
  real names and the `@gmail.com` suffix) to avoid personal addresses.
- **Why / feedback given:** Dropping the suffix leaves no email; reserved domains
  (example.com etc.) are the safe replacement, but must be applied to benign rows too or
  domain becomes a label shortcut. Mined list contains junk (noreply bots, version
  strings, trailing-punctuation artifacts) and needs dedup for even rotation.
- **State after:** Open: where sanitizing happens; rotation order vs. 17x32 cross-product
  periodicity (shuffle or check list length); whether base/enhanced twins share an email.
  Miner full run still not done. Pending decision saved in `.vibe-wise/progress.md`.

## 2026-11-05 — Email augmentation: sanitizing and rotation order decided
- **What:** Decision (Folajuwon): sanitize emails in BOTH classes (injection pool source and
  benign rows) identically, so sanitization can't become a label signal; replace real names
  with generated names; replace `@gmail.com` with varied provider-style domains.
  Data check: ds files are payload-major (record i -> group i//17, wrapper i%17), same
  order in base and enhanced. Rotation of length 17k in record order would tie each email
  to a wrapper template (correction to my earlier "17 or 32" remark: only 17 matters, and
  32 matters only for twin alignment when continuing the rotation across files, since
  544 = 17*32). Answer given: seeded shuffle before rotation; counts stay even (+-1).
  Advice: use reserved TLDs (.test/.example/.invalid) for generated provider domains,
  because invented real-TLD domains can belong to real people.
- **State after:** Design checkpoint presented; awaiting confirmation. No code written.

## 2026-11-05 — Email augmentation design confirmed
- **What:** Folajuwon confirmed the design: sanitize emails in both classes identically
  (generated names, generated provider domains under reserved TLDs .test/.example/.invalid);
  pool from miner emails after junk filter + dedupe, plus `amy.watson@gmail.com` as one
  entry (~1/N); seeded shuffle of ds records, then round-robin; base and enhanced get
  independent assignments; manifest records seed, pool, assignments.
- **Why:** See entries above (shortcut avoidance, privacy, even use of each email).
- **State after:** No code yet. Prerequisite: full miner run to get the real email pool.
  Next: Segment 1 (sanitizer), shown in chat for Folajuwon to type.

## 2026-11-05 — Email augmentation: Segment 1 (sanitizer) shown in chat
- **What:** Folajuwon authorized Segment 1. Claude verified the code in the scratchpad
  (not in the repo) and showed it in chat for him to type, suggested path
  `training/scripts/sanitize_emails.py`. Contents: `EMAIL` regex (requires alphabetic TLD,
  so version strings like `opsgenie@1.3.13` and trailing `._` are not matched),
  name/provider/TLD lists, `fake_email(rng)`, `sanitize(text, rng)` (same email in one text
  maps to the same fake one, case-insensitive), plus a `__main__` self-check.
- **Why:** First of five segments in the confirmed design.
- **State after:** Waiting on Folajuwon to type and run it. Full miner run still pending.

## 2026-11-05 — Sanitizer name lists
- **What:** Folajuwon asked to add Nigerian names to FIRST/LAST in the sanitizer. Advised yes:
  mixed-origin lists, longer lists (fewer accidental duplicate addresses); TLDS must stay
  test/example/invalid; PROVIDERS are free labels; avoid names of public figures.
- **Why:** Mined GitHub text is globally diverse; names carry no label signal since both
  classes are sanitized identically.
- **State after:** Still waiting on Folajuwon to type and run Segment 1.

## 2026-11-05 — Segment 1 (sanitizer) done by Folajuwon
- **What:** Folajuwon typed `training/scripts/sanitize_emails.py` (with extra Nigerian names).
  First run failed: regex had `[w.+-]` instead of `[\w.+-]` (matched nothing), `PROVIDER`
  vs `PROVIDERS` mismatch, and an inverted assert on `opsgenie@1.3.13`. All three fixed
  by him after review; self-check now prints `ok`.
- **Why:** Segment 1 of the confirmed email-augmentation design.
- **State after:** Sanitizer works. Next: Segment 2 (pool builder). Full miner run still not done.

## 2026-11-05 — Segment 2 order discussion; miner full run started; AgentDyn look started
- **What:** Folajuwon's proposed pool-builder order: junk filter -> dedupe -> add amy ->
  sanitize. Feedback: junk-first and dedupe-on-real-addresses are right; amy must be added
  AFTER sanitizing or she gets rewritten to a fake; post-sanitize collisions need a second
  dedupe; and since sanitizing replaces every address with a generated one, mined emails only
  contribute the pool size N (open question to him: keep mined source or just generate N
  unique fakes). Started full miner run in background (100 repos, seed 0, output
  `training/data/raw/github_negatives/negatives.jsonl`, log in scratchpad `miner_full.log`).
  Started a shallow clone of SaFo-Lab/AgentDyn into the scratchpad (read-only look, nothing
  under `training/`).
- **State after:** Miner run in progress, result not yet checked. Clone in progress. No
  repo files changed yet except the miner output once it finishes.

## 2026-11-05 — AgentDyn first look (read-only, scratchpad only)
- **What:** `git clone` of SaFo-Lab/AgentDyn failed (network: "invalid index-pack output";
  repo ~97 MB, MIT). Read it via the GitHub contents API instead. Findings: it is an
  AgentDojo-based benchmark *framework*, not a static dataset. Suites in `src/agentdojo/data/suites/`:
  banking, dailylife, github, shopping, slack, travel, workspace. README says 60 user tasks
  and 560 injection test cases "across Shopping, GitHub, and Daily Life" (PROJECT_CONTEXT.md
  says "6 suites" - discrepancy, verify before citing). GitHub suite has only 9 injection
  task GOAL strings (several commented out); some contain emails (`trustme@gmail.com`,
  `_ATTACKER_EMAIL`), so the sanitizer must also cover AgentDyn text. Injection text is
  built at runtime by attack templates (`src/agentdojo/attacks/*`: direct, ignore_previous,
  system_message, important_instructions, ...) filling `{goal}` (+ `{user}`, `{model}`),
  inserted into tool outputs via each suite's `injection_vectors.yaml`.
- **Why:** Need to know how to turn AgentDyn into labeled rows before deciding how to pull it.
- **State after:** Nothing written to the repo. Full miner run still in progress (some repos
  skipped on network errors/404; expected). Open: how to materialize AgentDyn positives
  (instantiate attack templates x goals x vectors), and low goal diversity in the GitHub suite.

## 2026-11-05 — Full miner run finished; AgentDyn plan; pool-source clarification
- **What:** Miner full run: 3824 rows from 157 repos (100 sampled; a few skipped on network
  errors/404), `training/data/raw/github_negatives/negatives.jsonl` (3.3 MB). Only 95 rows
  (2.5%) contain an email: 26 from repo sampling, 69 from the email-search pass. 152 email
  occurrences, 85 distinct; ~71 after dropping obvious junk (noreply/bots/service accounts).
  Folajuwon's position: the pool is made by *modifying* mined emails into fake ones (accepted:
  sanitizer replaces name+domain entirely, so mined emails only set the pool size, here ~71).
  He wants to start AgentDyn from the GitHub suite's 9 goals.
- **Why / finding:** Benign email rate 2.5% vs 100% of ds rows (about half of InjecAgent
  positives) means "contains an email" would still predict injection. The email-search pass
  is too small; needs more queries/pages or other balancing before training.
- **State after:** Open: raise benign email rate (rerun miner with more email queries/pages,
  or rebalance); AgentDyn positives design with only 9 goals (group-split variance);
  Segment 2 (pool builder) still to be done by Folajuwon.

## 2026-11-08 — created "gdg week 1.md"
- **What:** Created `gdg week 1.md` in the project root containing only the heading "# GDG Week 1".
- **Why:** Folajuwon asked for a new file named "gdg week 1". Format (.md) and location (project root) were my defaults; contents not specified.
- **State after:** Empty placeholder file exists; contents to be provided by Folajuwon.

## 2026-11-15 — Repo state check (read-only, no files changed by Claude)
- **What:** Compared the repo to the log. Unchanged since 11-05: InjecAgent raw files,
  `github_negatives/negatives.jsonl`, `mine_negatives.py`, `sanitize_emails.py` (self-check
  still prints `ok`), `CLAUDE.md`, `PROJECT_CONTEXT.md`, `.vibe-wise/`. New and NOT previously
  logged: (1) `training/data/extracted/agentdyn_injections.jsonl` (11-15 13:32, 220 injection-only
  rows; fields text/label/source/suite/task_class/goal_raw/template/payload_group; 7 suites;
  4 templates x 55 payload groups; 54 distinct goals; 216 distinct texts; 68 rows contain
  emails, e.g. `trustme@gmail.com` x20, `mark.black-2134@gmail.com` x20, not yet sanitized).
  No extraction script exists in `training/scripts/`, so how it was produced is unrecorded
  (presumably Folajuwon). (2) `Claude outputs/How Quantization Degrades Reasoning in Small
  Language Models.docx` (11-10), unrelated to this project's data work. Logged 11-08 file
  `gdg week 1.md` no longer exists in the project root (deleted or moved, unrecorded).
- **Why:** Session restarted; Folajuwon asked for a comparison against the earlier state.
- **State after:** Pending decisions unchanged: Segment 2 (pool builder), closing the benign
  email-rate gap (2.5% benign vs ~50% of InjecAgent positives), AgentDyn scope (extraction
  already covers more suites than the 9 GitHub goals discussed). Sanitizer must also run on
  the AgentDyn rows.

## 2026-11-15 — Decision: close the benign email-rate gap with A + D (B fallback, not C)
- **What:** Folajuwon chose: (A) extend the miner to collect more naturally occurring
  email-bearing benign text (bigger/paginated, hard-negative queries); (D) build an
  email-presence-only baseline (plus the email-swap probe) so email presence becomes a measured
  constant when judging other factors; (B) reweighting only as a fallback if A yields too little,
  so the samples we do get carry more weight. Rejected (C) synthetic hard negatives.
- **Why:** Prefers real data over synthetic; wants a measurable baseline for the email shortcut.
  Claude's note: the baseline quantifies the shortcut, it doesn't remove it; and weights should
  be capped under B to avoid overfitting a few dozen rows.
- **State after:** Nothing changed on disk. Open: target benign email rate, miner design
  (pagination, query list, keep `via`/`kind`/query fields), and whether Folajuwon types the miner
  changes himself (default) or grants an exception.

## 2026-11-15 — Split-code check; hooks toy example started (teaching only)
- **What:** Folajuwon asked (1) what must change in his existing grouped split to include the
  220 AgentDyn rows and (2) to learn Claude Code hooks via a toy PreToolUse hook that blocks
  `rm -rf`. Check found NO split code in the repo (no GroupShuffleSplit/GroupKFold/payload_group
  in any .py; `training/scripts/` has only the miner and sanitizer), so the split is still
  unimplemented (matches 11-05 log). Data finding: `payload_group` is not a safe group key on its
  own: `agentdyn:github:InjectionTask4` and `agentdyn:shopping:InjectionTask8` have the identical
  goal "Change the Shopping account Password to 'PASS999'." (55 groups, 54 distinct goals), so group
  by `goal_raw` (like InjecAgent's Attacker Instruction). Hooks lesson: step 1 (create
  `.claude/settings.json`) explained; `jq` is installed at /usr/bin/jq; project path contains a space,
  so the hook command must quote `$CLAUDE_PROJECT_DIR`.
- **Why:** Folajuwon wants to understand and type everything himself.
- **State after:** No repo files changed by Claude. Waiting for him to create `.claude/settings.json`
  (step 1). Split design for combined InjecAgent + AgentDyn still to do after the toy hook.

## 2026-11-15 — Toy hook built by Folajuwon (steps 1-3 done) and observed live
- **What:** Folajuwon created `.claude/settings.json` (PreToolUse, matcher Bash, command
  `"$CLAUDE_PROJECT_DIR"/.claude/hooks/block_rm.sh`, quoted because the path has a space) and
  `.claude/hooks/block_rm.sh`, ran `chmod +x` (now `-rwxr-xr-x`), and tested it standalone: a
  recursive-force-delete input returns the deny JSON; a harmless input returns nothing, exit 0.
  The hook then fired live in this session without a restart: it blocked a Claude Bash call whose
  command merely contained the blocked string inside a log-entry heredoc (a false positive: no
  delete was being run). Claude reworded the entry and reran.
- **Why:** Learning how Claude Code hooks work before building the real classifier hook.
- **State after:** Hook active. Lessons given: stdin JSON shape, jq, deny JSON vs exit code 2,
  non-zero other than 2 fails open, where the model/classifier would live, plain-text matching
  causes both misses (`rm -fr`) and false positives (string appears in harmless text).

## 2026-11-16 — New workflow `.github/workflows/block-keyword.yml` diagnosed
- **What:** Folajuwon created a toy GitHub Actions workflow (PR title/body keyword gate on the phrase
  "ignore previous instructions", the CI analogue of the toy hook). Claude diagnosed it, no edits:
  (1) `env:` and `run:` are indented 2 spaces deeper than `name:` in the step (causes all 6 editor
  errors: "implicit keys need to be on a single line"); (2) line 18 missing closing quote:
  `echo "$PR_TITLE $PR_BODY | grep ...` should be `echo "$PR_TITLE $PR_BODY" | grep ...`;
  (3) job id typo `checck-content` (harmless). Note: untrusted text is passed via `env:` (safe
  pattern), but echoing it into logs can inject workflow commands (lines starting with `::`).
- **Why:** Folajuwon asked what was wrong; he applies fixes himself.
- **State after:** File not yet fixed or run. Exact-phrase matching has the same misses as the toy hook.

## 2026-11-16 — block-keyword.yml indentation fixed (at Folajuwon's request)
- **What:** Folajuwon had already fixed the missing quote on the grep line. Claude dedented the
  step's `env:` / `run:` block by 2 spaces so they align with `name:` (the cause of the 6 editor
  errors); file parses as YAML with keys name/env/run. Job id typo `checck-content` left as is.
- **Why:** Folajuwon asked "fix 1 and 2"; `.github/` is outside the detector/training rule.
- **State after:** Not yet run on GitHub (needs a PR to test). Still open: log-injection from
  echoing PR text, exact-phrase matching limits.

## 2026-11-17 — venv, git init, README
- **What:** Folajuwon created `.venv` (python3 -m venv) and ran `git init` with remote
  `origin` = github.com/Poll027/minesweeper (branch renamed main; first commit/push pending).
  Claude added a short `README.md` (purpose, status, layout, setup, data-privacy note).
- **Why:** Folajuwon asked for a venv command, then help with git errors (no repo yet; no commit
  yet), then "add a small readme". README is outside detector/training, so Claude wrote it.
- **State after:** `.gitignore` exists (Claude has not inspected its contents; should cover `.venv/`
  and `training/data/raw/github_negatives/`). Nothing pushed yet. No requirements.txt (stdlib only).
