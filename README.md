# A Distilled Two-Tier Classifier for Prompt-Injection Detection in GitHub Coding-Agent Pipelines

Final-year thesis project (Covenant University, CIS). The repo folder is called "Minesweeper" but has nothing to do with the game.

The goal is to detect indirect prompt injection in text an AI coding agent reads (PR/issue/comment text, tool output) before the agent acts on it.

- **Tier 1:** deterministic regex rules.
- **Tier 2:** a distilled DistilBERT classifier.
- **Surfaces:** a GitHub Action gate and Claude Code PreToolUse/PostToolUse hooks.

## Status

Early. Data pipeline in progress; the detector, training, Action and hooks are not built yet. See `PROJECT_CONTEXT.md` for decisions and `WORK_LOG.md` for the full change history.

## Layout

| Path | What |
|---|---|
| `training/data/raw/injecagent/` | Raw InjecAgent benchmark files (injection examples) |
| `training/scripts/mine_negatives.py` | Mines benign GitHub text with the `gh` CLI |
| `training/scripts/sanitize_emails.py` | Replaces real emails with fake ones on reserved TLDs |
| `.github/workflows/` | Toy PR keyword gate (learning exercise) |
| `.claude/` | Toy Claude Code hook (learning exercise) |

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
```

The scripts use only the standard library. The miner also needs an authenticated [`gh`](https://cli.github.com/) CLI:

```bash
python3 training/scripts/mine_negatives.py --out <path>
```

## Data note

The mined negatives (`training/data/raw/github_negatives/`) contain real people's text and emails. They are git-ignored and must not be published.
