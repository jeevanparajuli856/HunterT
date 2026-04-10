# HunterT Agent Guide

This file defines repository-specific guidance for coding agents working in HunterT.

## Project Direction

HunterT is a research-to-product repository for language-model-guided directory enumeration.

Current state:
- The working implementation is Python-first.
- `lstm_pipeline/` is the primary maintained model path and the source of truth for current training, evaluation, and model-backed attack simulation logic.
- `transformer_pipeline/` and `transformer_pipelineV2/` are preserved research branches. They are useful reference material, but they are not the primary product direction.

Near-term product direction:
- build a Go CLI front end named `huntert`
- keep Python as the model/runtime backend during the first migration phase
- preserve research assets while making the repo easier to operate as a product codebase

## Environment

- Repository root: `/home/jeevan/HunterT`
- Shell: `bash`
- Python environment: root `.venv`
- Always use `python3`, never `python`
- Activate Python tools with:

```bash
source .venv/bin/activate
```

## Current Repo Map

- `lstm_pipeline/`: active LSTM training, evaluation, plotting, and reusable attack logic
- `transformer_pipeline/`: first transformer research branch
- `transformer_pipelineV2/`: second transformer research branch
- `LSTM_Research/`: datasets, notebooks, and wordlists from the AISec'24 reproduction work
- `infra/`, `infra_T_V100/`: GCP infra and runbooks
- `scripts/`: utility scripts
- `docs/`: lightweight project notes and placeholders
- `.claude/`, `.codex/`: local agent role definitions

## Working Rules

- Treat `lstm_pipeline/` as the primary implementation unless the user explicitly asks to work on transformer research.
- Preserve research artifacts, experiment logs, notebooks, and papers unless the user explicitly asks to remove or archive them.
- If you change structure or paths, update related docs in the same task.
- Prefer small, reversible migration steps over sweeping rewrites that break reproducibility.
- Do not invent product capabilities that are not backed by code yet. If the Go CLI or Python backend does not exist yet, describe it as planned or in-progress, not current.
- Keep commands and documentation Linux/bash-oriented.
- When you find copied guidance from another codebase, replace it fully with HunterT-specific instructions rather than trying to patch around it.

## Primary Commands

LSTM pipeline:

```bash
cd lstm_pipeline
python3 main.py train
python3 main.py evaluate
python3 plot_tables.py
```

Transformer research:

```bash
cd transformer_pipeline
python3 main.py train
python3 main.py evaluate

cd ../transformer_pipelineV2
python3 main.py train-diagnostic
python3 main.py evaluate
```

## Agent Expectations

- Planner-style work should focus on repo layout, migration sequencing, CLI/backend boundaries, and documentation clarity.
- Executor-style work should implement code and docs directly in the repo with minimal ceremony.
- Tester-style work should prefer smoke tests, import checks, CLI help checks, and targeted regression checks over invented process.
- Critic-style work should focus on factual review findings: broken paths, misleading docs, reproducibility risks, and interface drift.

## User-Preferred Rules

- Use `python3` instead of `python` in all commands.
- Use the root `.venv` for Python dependencies instead of system Python.
- If you find discrepancies between code and markdown, update the markdown and mention it briefly in the final response.
- If the user says a workflow or convention is not good, reflect the corrected rule in this file or `CLAUDE.md` when relevant.
