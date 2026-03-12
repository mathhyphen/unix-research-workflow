---
name: unix-research-workflow
description: Intent-driven ML experiment management with automated logging and reporting. Use when starting experiments, validating intent, tracking metrics, or enforcing reproducible research workflows.
triggers:
  - "create/start/run experiment"
  - "list/show experiments"
  - "experiment status/progress"
  - "generate report/summary"
  - "compare experiments"
  - "export metrics"
  - "remove/delete experiment"
  - "reproducible workflow"
  - "training code modification"
---

# Unix Research Workflow

This skill provides an automated pipeline for managing research experiments with strict workflow enforcement.

## Core Principles

1. **Intent-First** - No experiment starts without an `intent.yaml`
2. **Validate Before Run** - Always validate intent before training scripts
3. **Log Everything** - All metrics must use `log_hook.py`
4. **Auto-Summarize** - Generate reports from logs, never manually

## Quick Start

```bash
# Create new experiment
python scripts/new_exp.py --name <experiment-name>

# List all experiments
python scripts/list_exp.py

# Validate intent before running
python scripts/validate_intent.py workspace/<name>/intent.yaml

# Generate report after experiment
python scripts/summarize.py <experiment-name>
```

## Workflow

### 1. Start New Experiment

```bash
python scripts/new_exp.py --name my-experiment
```

This creates:
- `workspace/my-experiment/` directory
- `logs/` and `findings/` subdirectories
- `intent.yaml` template with experiment name
- Git worktree on branch `expl/my-experiment`

### 2. Fill Intent

Edit `workspace/<name>/intent.yaml`:

```yaml
experiment: my-experiment
branch: expl/my-experiment
objective: |
  Describe what you want to achieve (min 20 chars).
hypothesis: |
  Describe what you expect to happen (min 20 chars).
success_criteria:
  metrics:
    - name: val_loss
      threshold: 0.1
      direction: lower_is_better
constraints:
  max_runtime_hours: 24
```

### 3. Validate Intent

```bash
python scripts/validate_intent.py workspace/<name>/intent.yaml
```

### 4. Run Experiment with Logging

In your training loop, use the log hook:

```python
from pathlib import Path
from scripts.log_hook import LogHook

def train(num_epochs: int):
    """Example training loop with logging."""
    workspace = Path("workspace/my-experiment")
    log = LogHook(workspace)
    log.log_environment()

    for epoch in range(num_epochs):
        train_loss = train_one_epoch()
        val_loss = evaluate()

        log.log_epoch(epoch, {
            "train_loss": train_loss,
            "val_loss": val_loss
        }, phase="val")

        print(f"Epoch {epoch}: train={train_loss:.4f}, val={val_loss:.4f}")

    return workspace

if __name__ == "__main__":
    train(num_epochs=10)
```

### 5. Generate Report

```bash
python scripts/summarize.py <name>
```

Generates `workspace/<name>/findings/report.md`

## Experiment Status Codes

| Code | Meaning |
|------|---------|
| `I` | Initialized (intent only) |
| `M` | Metrics logged |
| `R` | Report ready |

## Commands Reference

| Script | Usage | Description |
|--------|-------|-------------|
| `new_exp.py` | `--name <name>` | Create new experiment |
| `list_exp.py` | (none) | List all experiments with status |
| `show_exp.py` | `<name>` | Show experiment details |
| `validate_intent.py` | `<path>` | Validate intent.yaml |
| `log_hook.py` | (import as module) | Log metrics to JSONL |
| `summarize.py` | `<name>` | Generate Markdown report |
| `export_csv.py` | `<name> [-o output]` | Export metrics to CSV |
| `compare_exp.py` | `<name1> <name2> ... [-m metric]` | Compare experiments |
| `rm_exp.py` | `<name> [--force]` | Remove experiment |

## When to Use This Skill

| Scenario | AI Action |
|----------|-----------|
| User wants to start a new ML experiment | Create experiment with `new_exp.py`, guide intent填写 |
| User needs reproducible workflow | Enforce intent-first, log-everything discipline |
| User is managing multiple experiments | Use `list_exp.py`, `compare_exp.py` for overview |
| User finished training | Auto-generate report with `summarize.py` |
| User asks about experiment progress | Check `list_exp.py` status, show metrics |
| User modifies training code | Remind to add `LogHook` for auto-logging |
| User wants to export/share results | Use `export_csv.py` or `summarize.py` for clean output |

## When NOT to Use This Skill

| Scenario | Alternative |
|----------|-------------|
| Quick prototype / debugging | Skip experiment manager, just run script |
| User has W&B/MLflow/Neptune | Use existing tracking system |
| Non-ML tasks (web, system, etc.) | This skill is ML-experiment specific |
| One-off data exploration | No need for intent/experiment structure |

## Files Structure

```
Unix_workflow/
├── scripts/
│   ├── __init__.py           # Package exports
│   ├── new_exp.py            # Experiment creation
│   ├── list_exp.py           # List experiments
│   ├── show_exp.py           # Show experiment details
│   ├── validate_intent.py    # Intent validation
│   ├── log_hook.py           # Metrics logging
│   ├── summarize.py          # Report generation
│   ├── export_csv.py         # Export to CSV
│   ├── compare_exp.py        # Compare experiments
│   └── rm_exp.py             # Experiment removal
├── templates/
│   └── intent.yaml           # Intent template
├── workspace/                # Experiment directory
│   └── <name>/
│       ├── intent.yaml
│       ├── logs/
│       │   └── metrics.jsonl
│       └── findings/
│           └── report.md
└── rules/
    └── research_protocol.md  # Guardian protocol
```

## Automatic Triggers

Claude Code should **automatically invoke** this skill in the following scenarios:

### 🟢 High Priority Triggers (immediately invoke skill)

| User says / does | AI Action |
|------------------|-----------|
| "创建实验" / "create experiment" / "start experiment" | Run `new_exp.py --name <name>` → Create intent template → Ask user to fill objective/hypothesis |
| "看看有哪些实验" / "list experiments" / "experiment status" | Run `list_exp.py` → Display table → Explain status codes (I/M/R) |
| "exp-001 怎么样" / "show exp-001" / "experiment details" | Run `show_exp.py exp-001` → Display intent + metrics count + git branch |
| "实验跑完了" / "experiment done" / "generate report" | Run `summarize.py <name>` → Generate report.md → Show summary |
| "对比 exp-001 和 exp-002" / "compare experiments" | Run `compare_exp.py exp-001 exp-002 [-m metric]` → Display comparison table |
| "删除实验 xxx" / "remove experiment" | Run `rm_exp.py <name>` → Confirm before deletion |
| "导出 metrics" / "export to csv" | Run `export_csv.py <name>` → Generate CSV file |
| User creates/modifies `workspace/*/intent.yaml` | Suggest: `validate_intent.py` |
| User modifies training code (detects `train`, `model.fit`, etc.) | Remind: Add `LogHook` to training loop |
| User opens `logs/metrics.jsonl` or asks about metrics | Suggest: Run `summarize.py` for pretty report |

### 🟡 Medium Priority Triggers (suggest or remind)

| User says / does | AI Reminder |
|------------------|-------------|
| User talks about running training | "Remember to use `log_hook.py` for metrics tracking" |
| User asks "how to track experiments" | Explain intent-first workflow + demonstrate `new_exp.py` |
| User creates Python files with "train" in name | Suggest: Set up experiment structure first |
| User asks about reproducibility | Explain: intent.yaml + log_hook + summarize workflow |

### 🔴 Never Trigger This Skill When

- User is doing quick one-off tests (prototyping, debugging)
- User already has W&B/MLflow/Neptune configured
- Non-ML tasks (web dev, system admin, etc.)
- User explicitly says "don't use experiment manager"

---

## AI Behavior Guidelines

### When Creating New Experiment

```
1. Run: python scripts/new_exp.py --name <user-provided-name>
2. Open created intent.yaml for user
3. Ask user to fill in:
   - objective (what you want to achieve)
   - hypothesis (what you expect)
   - success_criteria (metrics + thresholds)
4. Run: python scripts/validate_intent.py workspace/<name>/intent.yaml
5. Remind user to add LogHook to training code
```

### When Experiment Completes

```
1. Run: python scripts/summarize.py <name>
2. Read generated report.md
3. Present key metrics to user
4. Optionally: Run compare_exp.py if there are other experiments
```

### When User Asks About Experiments

```
1. Run: python scripts/list_exp.py
2. Parse output table
3. Explain status codes:
   - I = Just intent, no training yet
   - M = Has metrics, training in progress
   - R = Report generated, ready for review
4. Offer follow-up actions (show/summarize/compare)
```

## Related Files

- **Protocol Rules**: See `rules/research_protocol.md` for guardian protocol
- **Settings**: See `.claude/settings.local.json` for local configuration

---

## AI Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│          UNIX RESEARCH WORKFLOW - AI CHEAT SHEET               │
├─────────────────────────────────────────────────────────────────┤
│  USER SAYS...              →  AI RUNS                          │
├─────────────────────────────────────────────────────────────────┤
│  "创建实验 foo"            →  new_exp.py --name foo           │
│  "有哪些实验"              →  list_exp.py                      │
│  "exp-001 怎么样"          →  show_exp.py exp-001             │
│  "实验跑完了"              →  summarize.py <name>              │
│  "对比 exp-001 和 002"     →  compare_exp.py exp-001 exp-002  │
│  "删除 exp-001"            →  rm_exp.py exp-001               │
│  "导出 metrics"            →  export_csv.py <name>            │
│  修改训练代码              →  Remind: add LogHook             │
│  修改 intent.yaml          →  validate_intent.py <path>       │
├─────────────────────────────────────────────────────────────────┤
│  STATUS CODES: I=Intent only | M=Has metrics | R=Report ready  │
│  WORKFLOW: new → intent → validate → train (log) → summarize   │
└─────────────────────────────────────────────────────────────────┘
```
