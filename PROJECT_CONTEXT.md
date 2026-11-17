# Project Context

This file exists so any Claude Code session picking up this repo has context without
re-deriving it. It records status and decisions Folajuwon has actually made — it does
not prescribe implementation. Keep it updated as stages close out; don't let it drift.

## Project

**Thesis title:** A Distilled Two-Tier Classifier for Prompt-Injection Detection in
GitHub Coding-Agent Pipelines.

**Architecture (as planned, not yet (re)implemented):** Tier 1 (pattern/regex rules)
catches obvious payloads cheaply. Tier 2 (a distilled DistilBERT classifier) catches
"instruction-like phrasing" that needs semantic understanding rather than a pattern
match. Deployed as a GitHub Action CI/CD gate plus Claude Code hooks. Two target
surfaces: GitHub PR/issue/comment text, and MCP tool-output content.

**Repo state as of 2026-11-05:** wiped to a clean slate. Only `.claude/` (Claude
Code's own tooling config) and `training/data/raw/injecagent/` (raw dataset, see
below) exist. No detector code, no README, no CI config, no requirements files —
all of that is Folajuwon's to write from scratch himself.

## Departmental context (Covenant University CIS, confirmed from the real 2026/2027
FYP Expectations doc)

- Mini Defence: 27 Nov – 4 Dec 2026. Chapters 1–2 only, no working system required.
  25/100 marks.
- Final Defence: 21–25 June 2027. Chapters 1–5 **and a working system demo**.
  30/100 marks: Introduction 1, SOP/Research Questions 2, Aim and Objectives 2,
  **Results from Objectives 7**, **Implementation/Analysis Process 7**, Write-up
  Quality 1, Comportment+Answers 5, Presentation+Slides 5. Results + Implementation
  = 14/30 (~47%) — working Tier 2 execution matters more than documentation polish.
- Turnitin ≤20%, AI-detection ≤15%, 60% of references within the last 5 years.
- A separate scope document (lit review, reference audit, BERM/DistilBERT
  justification, architecture rationale) is maintained in Claude Docs — this file is
  about data/code status, not a replacement for that doc.

## Working conventions

- **Design** follows the vibe-wise plugin's process (`/vibe-wise:learn`): Claude asks for
  Folajuwon's approach first, examines tradeoffs with him, and he decides when a design is
  ready.
- **Code** is written by Folajuwon himself for `detector/` and `training/` (needed for
  Final Defence defensibility: Comportment+Answers is 5/30, he must explain any line a
  panel points at). Default workflow: work in **segments**; Claude gives the code for
  one segment in chat/terminal with explanations, then Folajuwon types it out himself.
  Claude does not write or edit files under `detector/` or `training/` unless he
  explicitly says so for a specific task (as he did for `training/scripts/mine_negatives.py`).
  Data acquisition scripting Claude may execute directly. He may override this default per
  scenario.
- Nothing in this file should be read as a design decision already made on
  Folajuwon's behalf. Where a technique is described below (e.g. the split
  methodology), it reflects a choice he has actually discussed and agreed, not an
  inherited default.

## Data pipeline — current status (Stage 1: Data)

### Sources

1. **InjecAgent** (github.com/uiuc-kang-lab/injecagent, MIT). Indirect prompt
   injection via tool-output content — same surface as this project's MCP case.
   Primary positive source.
2. **AgentDyn** (github.com/SaFo-Lab/AgentDyn, built on AgentDojo, MIT). Has a
   dedicated GitHub suite plus Slack — 560 injection cases across 6 suites. **Not yet
   pulled.** Independent payload-generation process from InjecAgent — main planned
   source of real phrasing diversity, not just more volume.
3. **Negatives (benign)**: plan is to pull real, current PR/issue/comment text via
   the GitHub REST/GraphQL API from active public repos, not a static dataset dump —
   to match actual deployment-distribution content. **Not started — no benign
   examples exist yet.**
4. **Explicitly excluded**: MCPTox (tool-description/metadata poisoning at
   registration time) — different attack surface than this project's target. Cite as
   related-but-distinct in the lit review; not a training data source.

### InjecAgent — pulled, not yet curated

Raw files in `training/data/raw/injecagent/` (fetched 2026-11-05):
- `test_cases_dh_base.json` — 510 records, 30 distinct `Attacker Instruction`
  payloads (~17 tool-wrapper variants each). Direct-harm, single-stage. Structurally
  diverse across domains — no major template-overfit risk found.
- `test_cases_ds_base.json` — 544 records, 32 distinct payloads (~17 variants each).
  Data-stealing, two-stage. **Finding:** nearly all 32 payloads share one template —
  "retrieve [X data], send to amy.watson@gmail.com" — only the data-type noun varies.
  Real diversity is lower than the raw 30+32=62 count implies.
- `test_cases_dh_enhanced.json`, `test_cases_ds_enhanced.json` — same payloads as
  `_base`, plus an appended override phrase. Don't count toward the distinct-payload
  total — treat as a separate evaluation slice, not new data.

**Key field:** `"Tool Response"` is the fully-assembled injected tool-output text —
the classifier's positive training input. `"Tool Response Template"` (has the
unresolved `<Attacker Instruction>` placeholder) is used as the insertion target for
the augmentation step below, not as training input directly. Discard
`"Expected Achievements"` / `"Thought"` — agent-evaluation artifacts, not classifier
input.

### Email-placeholder augmentation (spec agreed, not yet implemented)

Mitigates the `amy.watson@gmail.com` template-overfit risk in `ds_base`/
`ds_enhanced`. Scope: `ds` files only — `dh`'s one "Amy" reference is semantically
part of that attack, not a repeated artifact. Target: the literal string
`amy.watson@gmail.com` only, not the name "Amy" (several `ds` sentences use pronouns
that would become grammatically inconsistent under a name swap).

1. Build a pool of ~15–20 plausible alternate email addresses.
2. Group the 32 `ds` records by their *original* `Attacker Instruction` text — this
   group key must stay stable and match the train/test split's group key, or the
   split's leakage-prevention guarantee breaks.
3. Deterministically (seeded) assign one pool email per distinct payload group — same
   email for all ~17 wrapper-variants of that payload, and for both `base` and
   `enhanced` versions.
4. Per record: `augmented_instruction = original_instruction.replace(old_email,
   assigned_email)`, then re-render via
   `tool_response_template.replace("<Attacker Instruction>", augmented_instruction)`
   — don't patch the already-assembled `Tool Response` string directly.
5. Row schema:
   ```json
   {
     "text": "<augmented_tool_response>",
     "label": "injection",
     "source": "injecagent_ds_base" | "injecagent_ds_enhanced",
     "payload_group": "<stable id 0-31, from the ORIGINAL instruction text>",
     "attack_type": "<from record>",
     "original_email": "amy.watson@gmail.com",
     "substituted_email": "<assigned_email>"
   }
   ```

### Train/test split methodology (agreed, not yet implemented)

Both `dh_base` and `ds_base` are a cross-product: each distinct payload appears
wrapped in ~17 different tool-response templates. A naive random record-level split
puts near-duplicate copies of the same literal payload text on both sides
(~98% probability per payload given 17 copies and an 80/20 split), letting the model
memorize fixed strings instead of general injection patterns, and silently inflating
reported test accuracy.

**Fix:** group by `Attacker Instruction` identity (same `payload_group` key as the
augmentation step, so augmented and non-augmented copies of one payload stay
together) so no payload straddles the train/test boundary, and stratify those groups
by `Attack Type` for balanced category coverage. Equivalent to scikit-learn's
`GroupKFold`/`GroupShuffleSplit`.

### Label taxonomy

Binary (`injection` / `benign`) as the training label. Each source's attack-category
metadata (InjecAgent's `Attack Type`, AgentDyn's suite name) is kept as a sidecar
field for error-analysis breakdown in the results chapter, not built into the model
as a multi-class head — chosen given the project timeline.

## Stage plan (anchored to real dates)

- **Stage 1 — Data (now → ~Nov 25):** finish InjecAgent curation (augmentation +
  grouped split), pull AgentDyn's GitHub suite, build the GitHub-API negative-mining
  pipeline. *Current position: raw InjecAgent files pulled; curation script, AgentDyn
  pull, and negatives all outstanding.*
- **Stage 2 — Baseline training (weeks 3–5):** fine-tune DistilBERT, single-pass,
  confirm training loop + eval harness (precision/recall/F1, FPR) work end to end.
- **Stage 3 — Context-window handling (weeks 5–6):** long-input handling for
  injections that fall outside DistilBERT's 512-token limit, tested against
  deliberately long adversarial inputs.
- **Stage 4 — Integration (weeks 6–8):** Tier 1 → Tier 2 pipeline, GitHub Action,
  Claude Code hook(s), end-to-end latency benchmark.
- **Stage 5 — Results writeup (weeks 8–10, buffer before Final Defence):** metrics,
  confusion matrices, baseline comparisons.

## Open items

- Reference pool in the scope doc: as of its last audit, 3 of 8 sources were websites
  (37.5%), over the department's ≤10% ceiling. Unrelated to Tier 2 progress — fix
  before any re-evaluation against the cis-fyp-verifier rubric.
- AgentDyn not yet pulled.
- GitHub-API negative-mining not yet started.
- Augmentation and grouped-split logic above are agreed specs, not code — Folajuwon
  is implementing both himself.
