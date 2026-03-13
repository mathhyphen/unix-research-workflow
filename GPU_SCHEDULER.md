# GPU 调度与 Worktree 使用指南

## 问题 1：Worktree 目录结构修复

### 问题描述

之前创建实验时，worktree 文件夹有时没有放到正确的位置，需要手动修正目录结构。

### 原因分析

旧代码的执行顺序：
1. 创建 `workspace/<name>/` 目录
2. 创建 `logs/`、`findings/` 子目录
3. **最后**尝试创建 git worktree

问题：git worktree 会接管整个目录，可能导致已创建的子目录结构混乱。

### 解决方案（已修复）

新的执行顺序：
1. 检查是否是 git 仓库
2. **首先**创建 git worktree（这会创建目录）
3. **然后**在 worktree 内创建子目录结构

### 修复后的行为

```bash
# 创建实验
python scripts/new_exp.py --name unet-baseline

# 输出示例：
Creating experiment 'unet-baseline'...
  [OK] Git worktree: created (branch: expl/unet-baseline)
  [OK] Created directory structure
  [OK] Copied intent template

Done: D:\apps\Unix_workflow\workspace\unet-baseline

Next steps:
  1. Edit: D:\apps\Unix_workflow\workspace\unet-baseline/intent.yaml
  2. Validate: python scripts/validate_intent.py .../intent.yaml
  3. Git: cd .../unet-baseline && git add . && git commit -m 'Add unet-baseline'
```

### 目录结构保证

```
workspace/unet-baseline/       ← worktree 根目录
├── .git                       ← worktree 元数据（自动创建）
├── intent.yaml                ← 实验意图
├── logs/                      ← 日志目录
│   └── .gitkeep
├── findings/                  ← 报告目录
│   └── .gitkeep
└── checkpoints/               ← 模型检查点
    └── .gitkeep
```

---

## 问题 2：GPU 调度管理

### 使用场景

在多用户/多任务的服务器上：
- 需要等待空闲 GPU
- 避免多个任务抢占同一 GPU
- 自动检测 GPU 可用性
- 训练完成后自动释放 GPU

### 基本用法

```bash
# 最简单的用法 - 自动等待 1 个可用 GPU
python scripts/gpu_scheduler.py train.py --lr 0.001 --epochs 100

# 指定需要 2 个 GPU
python scripts/gpu_scheduler.py --gpus 2 train.py

# 指定最小显存（16GB）
python scripts/gpu_scheduler.py --min-memory 16000 train.py

# 最长等待 2 小时
python scripts/gpu_scheduler.py --wait-time 7200 train.py
```

### 完整参数

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--gpus` | `-g` | 1 | 需要的 GPU 数量 |
| `--min-memory` | `-m` | 8000 | 最小空闲显存 (MB) |
| `--max-util` | | 10 | 最大利用率 (%) |
| `--wait-time` | `-w` | 3600 | 最长等待时间 (秒) |
| `--check-interval` | | 30 | 检查间隔 (秒) |
| `--python` | | 当前 Python | 指定 Python 解释器 |

### 实用命令

```bash
# 查看当前 GPU 状态
python scripts/gpu_scheduler.py --list-gpus

# 输出示例：
# ======================================================================
# GPU Status
# ======================================================================
# GPU  | Name                      | Free       | Used       | Util
# ----------------------------------------------------------------------
# 0    | NVIDIA GeForce RTX 3090   |    24000MB |     1000MB |    5%
# 1    | NVIDIA GeForce RTX 3090   |     8500MB |    16500MB |   80%   🔒
# 2    | NVIDIA GeForce RTX 3090   |    23000MB |     2000MB |   12%
# 3    | NVIDIA GeForce RTX 3090   |     1000MB |    24000MB |   95%   🔒
# ======================================================================
#
# Locked GPUs:
#   GPU 1: job_12345 (1800s ago)
#   GPU 3: job_12346 (300s ago)

# 清理过期的 GPU 锁
python scripts/gpu_scheduler.py --clean-locks
```

---

## 完整训练流程示例

### 示例 1：单卡训练

```bash
# 等待 1 个 GPU 空闲（最少 8GB 显存），然后运行训练
python scripts/gpu_scheduler.py \
    --min-memory 8000 \
    --wait-time 3600 \
    train.py --config configs/unet_baseline.yaml
```

### 示例 2：多卡训练

```bash
# 等待 2 个 GPU 空闲（每个最少 16GB 显存）
python scripts/gpu_scheduler.py \
    --gpus 2 \
    --min-memory 16000 \
    --wait-time 7200 \
    train.py --config configs/unet_ddp.yaml
```

### 示例 3：大模型训练

```bash
# A100/H100 大模型：需要 4 个 GPU，每个 40GB+ 空闲显存
python scripts/gpu_scheduler.py \
    --gpus 4 \
    --min-memory 40000 \
    --max-util 5 \
    --wait-time 14400 \
    train.py --config configs/vision_transformer.yaml
```

---

## 在你的训练代码中整合

### 最简单的整合

```python
#!/usr/bin/env python3
"""训练脚本 - 与 GPU Scheduler 兼容"""

import os
import torch
from pathlib import Path
from scripts.log_hook import LogHook
from scripts.mlflow_integration import MlflowHook

def main():
    # CUDA_VISIBLE_DEVICES 由 gpu_scheduler 自动设置
    device = torch.device(f"cuda")

    # 初始化工作空间
    exp_name = os.environ.get("EXP_NAME", "default-exp")
    workspace = Path(f"workspace/{exp_name}")

    # 初始化日志
    log = LogHook(workspace)
    mlflow = MlflowHook(workspace, experiment_name=exp_name)
    mlflow.start_run()

    # 你的训练代码...
    model = create_model().to(device)

    for epoch in range(100):
        train_loss = train_one_epoch(model)
        val_dice = evaluate(model)

        log.log_epoch(epoch, {"loss": train_loss, "dice": val_dice}, phase="val")
        mlflow.log_epoch(epoch, {"loss": train_loss, "dice": val_dice}, phase="val")

    mlflow.end_run()

if __name__ == "__main__":
    main()
```

### 运行方式

```bash
# 方式 1：直接运行（单卡）
python train.py

# 方式 2：通过 GPU Scheduler（自动等待 GPU）
python scripts/gpu_scheduler.py train.py --gpus 1 --min-memory 8000

# 方式 3：多卡
python scripts/gpu_scheduler.py --gpus 4 train.py
```

---

## 完整工作流：从创建实验到训练

```bash
# 步骤 1：创建实验
python scripts/new_exp.py --name unet-brats-baseline

# 步骤 2：编辑 intent.yaml
# 编辑 workspace/unet-brats-baseline/intent.yaml

# 步骤 3：验证 intent
python scripts/validate_intent.py workspace/unet-brats-baseline/intent.yaml

# 步骤 4：等待 GPU 并运行训练
python scripts/gpu_scheduler.py \
    --gpus 1 \
    --min-memory 8000 \
    --wait-time 3600 \
    workspace/unet-brats-baseline/train.py

# 步骤 5：训练完成后生成报告
python scripts/summarize.py unet-brats-baseline
```

---

## GPU 锁机制说明

### 锁文件位置

```
~/.unix_workflow/gpu_locks/
├── gpu_0.lock
├── gpu_1.lock
└── gpu_2.lock
```

### 锁文件格式

```json
{
  "job_id": "job_12345_20260313143000",
  "timestamp": "2026-03-13T14:30:00",
  "pid": 12345
}
```

### 自动过期

- 默认锁超时时间：30 分钟
- 超过时间后自动释放
- 可用 `--clean-locks` 手动清理

### 手动释放

如果进程异常退出，锁可能未释放：

```bash
# 清理所有过期锁
python scripts/gpu_scheduler.py --clean-locks

# 或者手动删除
rm ~/.unix_workflow/gpu_locks/gpu_*.lock
```

---

## 常见问题

### Q: gpu_scheduler 如何知道哪些 GPU 可用？

A: 使用 `nvidia-smi` 命令检测：
- 空闲显存 > `--min-memory`
- 利用率 < `--max-util`
- 没有被其他任务锁定

### Q: 如果服务器没有 nvidia-smi 怎么办？

A: 脚本会检测到并提示，但无法自动调度 GPU。需要手动设置 `CUDA_VISIBLE_DEVICES`。

### Q: 多个用户同时运行怎么办？

A: GPU 锁机制确保同一 GPU 不会被多个任务抢占。锁文件使用独占创建 (`O_EXCL`) 防止竞争。

### Q: 训练脚本崩溃了 GPU 锁会释放吗？

A: 不会自动释放。需要：
1. 等待 30 分钟自动过期
2. 或运行 `--clean-locks` 清理
3. 或手动删除锁文件

### Q: 可以在 Slurm/PBS 等调度系统上使用吗？

A: 可以，但建议：
- 在 Slurm 分配的资源内运行
- 或者只用 `--list-gpus` 查看状态
- 让 Slurm 处理调度，不使用 gpu_scheduler 的等待功能

---

## 进阶用法

### 与 wandb 整合

```bash
python scripts/gpu_scheduler.py \
    --gpus 2 \
    train.py \
    --use_wandb \
    --wandb_project my-project
```

### 后台运行（nohup）

```bash
nohup python scripts/gpu_scheduler.py \
    --wait-time 86400 \
    train.py > train.log 2>&1 &

# 查看日志
tail -f train.log
```

### 定时检查脚本

```bash
#!/bin/bash
# check_gpu.sh - 定期检查 GPU 状态

while true; do
    echo "=== $(date) ==="
    python scripts/gpu_scheduler.py --list-gpus
    sleep 300  # 每 5 分钟检查一次
done
```

---

## 总结

| 功能 | 命令 |
|------|------|
| 创建实验 | `python scripts/new_exp.py --name <name>` |
| 等待 GPU | `python scripts/gpu_scheduler.py train.py` |
| 查看 GPU | `python scripts/gpu_scheduler.py --list-gpus` |
| 清理锁 | `python scripts/gpu_scheduler.py --clean-locks` |
| 生成报告 | `python scripts/summarize.py <name>` |
