# Project Map

## Purpose
Thesis system: detect indirect prompt injection in text an AI coding agent reads (GitHub PR/issue/comment text, MCP tool output) before the agent processes it.

## Requirements
- Two tiers: Tier 1 deterministic regex, Tier 2 distilled DistilBERT (planned, per PROJECT_CONTEXT.md).
- Surfaces: GitHub Action CI gate plus Claude Code hooks (planned).
- Final Defence (21-25 Jun 2027) needs a working demo; Mini Defence 27 Nov-4 Dec 2026 needs chapters 1-2 only.

## Components
- `training/data/raw/injecagent/` - four raw InjecAgent JSON files (dh/ds x base/enhanced). Exists.
- `training/scripts/mine_negatives.py` - gh-CLI miner for benign GitHub text, incl. email-bearing rows. Exists, tested on 4 repos.
- `detector/` - removed; to be rewritten by the learner. Not present.
- `PROJECT_CONTEXT.md`, `WORK_LOG.md`, `CLAUDE.md` - status, change log, session instructions.

## Main Flow
Data stage (current): InjecAgent ds raw -> [chosen, not implemented] sanitize mined emails (both classes) -> pool (+amy.watson) -> seeded shuffle -> round-robin assign -> augmented rows + manifest -> grouped split (?) ; GitHub miner -> benign negatives -> (?) ; both -> Tier 2 training (not started) -> Tier 1 -> Tier 2 pipeline, Action, hooks (not started).

## Data and Trust Boundaries
Mined GitHub text is assumed benign, not verified, and contains real people's emails (keep local). Injection data is public benchmark text.

## Build and Deployment
No build files currently; requirements, Dockerfile, action.yml were deleted. Miner run: `python3 training/scripts/mine_negatives.py --out <path>` (needs authenticated `gh`).

## Unknowns
Augmentation and grouped-split code (agreed specs only), AgentDyn pull, negatives full run, Tier 2 training setup, long-input handling, deployment files.
