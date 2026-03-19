# Workflow Reference

## Lifecycle

Use the repository as an intent-driven experiment manager:

1. Create a git worktree or experiment directory.
2. Run `python scripts/new_exp.py --name <name>`.
3. Edit `intent.yaml`.
4. Run `python scripts/validate_intent.py <path-to-intent.yaml>`.
5. Train with `LogHook` enabled.
6. Run `python scripts/summarize.py <name>`.

## Directory Layout

Experiments are searched in:

- `workspace/`
- `.claude/worktrees/`
- `~/.claude/worktrees/`

Each experiment should look like:

```text
<experiment>/
|- intent.yaml
|- logs/
|  `- metrics.jsonl
|- findings/
|  `- report.md|report.json|report.html
`- checkpoints/
```

## Script Selection

- Use `new_exp.py` when creating a new experiment scaffold.
- Use `list_exp.py` to enumerate known experiments.
- Use `show_exp.py` to inspect one experiment quickly.
- Use `validate_intent.py` before training starts.
- Use `gpu_scheduler.py` when a run should wait for free GPU memory.
- Use `summarize.py` after logging exists.
- Use `compare_exp.py` and `export_csv.py` when the user asks for comparisons or tabular export.
- Use `rm_exp.py` only when the user explicitly wants cleanup.

## Status Expectations

- `I` means initialized only.
- `M` means metrics exist.
- `R` means at least one report artifact exists.

## Logging Expectations

- `LogHook.log_epoch()` writes flat metrics with `epoch` and `phase`.
- Nested `{"metrics": {...}}` payloads are also supported.
- Reports summarize numeric metrics and separate them by phase when present.
