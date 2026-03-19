---
name: unix-research-workflow
description: Research experiment workflow for local ML/DL repositories that use git worktrees, intent.yaml, JSONL metrics, and generated reports. Use when Codex needs to create, validate, inspect, compare, summarize, or clean up experiments in this repository, especially for diffusion, flow matching, MRI, CT, or other medical imaging generation work.
---

# Unix Research Workflow

Use this skill to operate the experiment workflow in this repository.

## Core Workflow

1. Create or locate the experiment worktree.
2. Create `intent.yaml` with `python scripts/new_exp.py --name <name>`.
3. Fill the objective, hypothesis, and `success_criteria.metrics`.
4. Validate the intent with `python scripts/validate_intent.py <path-to-intent.yaml>`.
5. Run training with `LogHook` enabled and use `gpu_scheduler.py` when GPU scheduling matters.
6. Generate or inspect reports with `summarize.py`, `show_exp.py`, `list_exp.py`, and `compare_exp.py`.

## Guardrails

- Treat `intent.yaml` as mandatory before training.
- Prefer the repository workflow helpers over ad hoc shell scripts when managing experiments.
- Search for experiments in all supported workspaces: `workspace/`, project `.claude/worktrees/`, and home `.claude/worktrees/`.
- Keep experiment artifacts local; do not commit `workspace/`, `mlruns/`, or private datasets.
- If the task mentions MRI, CT, diffusion, flow matching, synthesis, or modality translation, read [references/medical-imaging.md](./references/medical-imaging.md) before editing the intent or evaluation plan.

## Read These References When Needed

- Read [references/workflow.md](./references/workflow.md) for command-level usage, status meanings, and common troubleshooting.
- Read [references/medical-imaging.md](./references/medical-imaging.md) for medical imaging generation conventions, suggested intent fields, and evaluation advice.

## Typical Requests

- "Create an experiment for a new MRI-to-CT baseline."
- "List my current experiments and show which ones have reports."
- "Validate this intent before I start training."
- "Summarize the latest diffusion run and compare it with the flow matching baseline."
- "Clean up an experiment worktree after the report is generated."
