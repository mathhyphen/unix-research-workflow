---
name: unix-research-workflow
description: Intent-driven ML experiment workflow for local research repositories. Use when Codex needs to create, validate, track, summarize, compare, or clean up experiments with this repository's scripts, especially for iterative research such as MRI or CT synthesis, diffusion models, flow matching, segmentation baselines, and other GPU-based training workflows.
---

# Unix Research Workflow

Use this skill to operate the repository's experiment lifecycle instead of inventing ad hoc folders, YAML files, or reporting scripts.

## Follow The Built-In Workflow

1. Create or locate the experiment worktree or workspace directory.
2. Initialize the experiment with `python -m scripts.new_exp --name <name>`.
3. Fill in `intent.yaml` before training.
4. Validate with `python -m scripts.validate_intent <path-to-intent.yaml>`.
5. Log metrics with `scripts.log_hook.LogHook` during training.
6. Generate reports with `python -m scripts.summarize <name>`.

Search for experiments in these roots:
- `workspace/`
- `.claude/worktrees/`
- `~/.claude/worktrees/`

Invoke CLI modules from the repository root with `python -m scripts.<module>`.

## Use The Existing Scripts

Prefer the repository scripts over handwritten one-off commands:

- `scripts/new_exp.py` for experiment scaffolding
- `scripts/list_exp.py` for experiment discovery
- `scripts/show_exp.py <name>` for quick inspection
- `scripts/validate_intent.py <path>` for intent checks
- `scripts/summarize.py <name>` for report generation
- `scripts/compare_exp.py <name1> <name2>` for comparisons
- `scripts/export_csv.py <name>` for CSV export
- `scripts/rm_exp.py <name>` for cleanup
- `scripts/gpu_scheduler.py ...` for GPU waiting and launch control

Do not replace these with new wrappers unless the user explicitly asks for a workflow change.

## Write Intent Before Training

Treat `intent.yaml` as the contract for the experiment. The validator currently requires:

- `branch`
- `objective`
- `hypothesis`
- `success_criteria.metrics`

Read `references/intent-schema.md` when you need field guidance or example intents.

## Keep Logging And Reports Consistent

- Use `LogHook` so metrics land in `logs/metrics.jsonl`.
- Keep metrics numeric and phase-aware when possible.
- Use `summarize.py` to generate reports instead of manually summarizing JSONL logs.
- Prefer updating the existing reporting flow over introducing a second reporting format.

## Medical Imaging Guidance

For MRI, CT, diffusion, or flow-matching experiments:

- Capture modality and task details in the intent, even when they are not validator-required.
- Record dataset, split, preprocessing, spacing, normalization, and conditioning choices.
- Make success criteria explicit for generation tasks, for example `mae`, `ssim`, `psnr`, or downstream segmentation quality.
- Keep experiment names short and stable so comparisons and report generation remain easy.
- Read `references/medical-imaging.md` when the user is working on modality translation, diffusion baselines, flow matching, or clinical-image-specific evaluation.

## Read References Only When Needed

- Read `references/workflow.md` for lifecycle, directory layout, and command selection.
- Read `references/intent-schema.md` for required fields, recommended fields, and example intents.
- Read `references/medical-imaging.md` for MRI, CT, and other medical imaging generation conventions.
