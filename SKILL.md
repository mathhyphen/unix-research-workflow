---
name: unix-research-workflow
description: **ALWAYS use for ML experiments.** Intent-driven: git worktree → intent.yaml → validate → train (LogHook) → auto-report.
---

# Unix Research Workflow

**Purpose**: Automated pipeline for ML/DL experiment management.

## Core Principles

1. **Intent-First** — No experiment starts without `intent.yaml`
2. **Validate Before Run** — Always validate intent before training
3. **Log Everything** — All metrics use `LogHook` (JSONL)
4. **Auto-Summarize** — Generate reports from logs

---

## Workflow

### 1. Create Experiment
```bash
git worktree add -b expl/<name> .claude/worktrees/<name>
python scripts/new_exp.py --name <name>
```

### 2. Fill Intent (min 20 chars for objective/hypothesis)
```yaml
experiment: <name>
branch: expl/<name>
objective: |
  Describe objective (min 20 chars)
hypothesis: |
  Describe hypothesis (min 20 chars)
success_criteria:
  metrics:
    - name: val_loss
      threshold: 0.1
      direction: lower_is_better
```

### 3. Validate → Train → Report
```bash
python scripts/validate_intent.py .claude/worktrees/<name>/intent.yaml
python scripts/gpu_scheduler.py --min-memory 8000 train.py
python scripts/summarize.py <name>
```

---

## Commands

| Command | Usage |
|---------|-------|
| `new_exp.py --name <name>` | Create experiment |
| `list_exp.py` | List experiments (I/M/R) |
| `show_exp.py <name>` | Show details |
| `validate_intent.py <path>` | Validate intent |
| `summarize.py <name>` | Generate report |
| `compare_exp.py <n1> <n2>` | Compare |
| `export_csv.py <name>` | Export CSV |
| `rm_exp.py <name>` | Delete |
| `gpu_scheduler.py [opts] script.py` | Wait GPU, run |

**Status**: I=Initialized, M=Metrics, R=Report

---

## Triggers

| User Says | Action |
|-----------|--------|
| "创建实验 xxx" | Create worktree + intent |
| "有哪些实验" | List experiments |
| "生成报告" | Generate report |
| "对比 exp-001 和 002" | Compare |
| "wait for GPU" | gpu_scheduler.py |
