# Workflow Reference

## Supported Workspaces

The repository resolves experiments from these locations:

- `workspace/`
- project-local `.claude/worktrees/`
- home `.claude/worktrees/`

Use the existing helpers instead of hand-rolled path logic.

## Main Commands

### Create an experiment

```bash
git worktree add -b expl/<name> .claude/worktrees/<name>
python scripts/new_exp.py --name <name>
```

`new_exp.py` writes:

- `intent.yaml`
- `logs/`
- `findings/`
- `checkpoints/`

### Validate the intent

```bash
python scripts/validate_intent.py <path-to-intent.yaml>
```

Validation currently checks:

- `branch`
- `objective`
- `hypothesis`
- `success_criteria.metrics[*].name`
- `success_criteria.metrics[*].threshold`
- `success_criteria.metrics[*].direction`

### Log training metrics

Use `scripts/log_hook.py` from the training script and keep metric names stable across runs.

### Generate reports

```bash
python scripts/summarize.py <name>
python scripts/show_exp.py <name>
python scripts/compare_exp.py <name1> <name2>
```

`summarize.py` emits `last`, `mean`, `min`, and `max` statistics for each logged metric and phase.

## Status Codes

- `I`: initialized
- `M`: metrics present
- `R`: report artifact present (`.md`, `.json`, or `.html`)

## Common Failure Modes

- Missing worktree: create the worktree before `new_exp.py`.
- Invalid intent: fill objective, hypothesis, and success criteria before training.
- Empty report: confirm `logs/metrics.jsonl` exists and contains metric rows.
- Missing report status: run `summarize.py` or check `findings/`.
