# GPU 调度与 Worktree 使用指南

## Worktree 集成

Claude Code 创建实验时自动执行：
```bash
git worktree add -b expl/<name> .claude/worktrees/<name>
python scripts/new_exp.py --name <name>
```

目录结构：
```
.claude/worktrees/<name>/
├── intent.yaml       # 实验意图
├── logs/             # 日志
├── findings/         # 报告
└── checkpoints/      # 检查点
```

---

## GPU 调度管理

### 基本用法

```bash
# 自动等待 1 个可用 GPU
python scripts/gpu_scheduler.py train.py --lr 0.001

# 指定 2 个 GPU，最小 16GB 显存
python scripts/gpu_scheduler.py --gpus 2 --min-memory 16000 train.py

# 最长等待 2 小时
python scripts/gpu_scheduler.py --wait-time 7200 train.py
```

### 参数表

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--gpus` | `-g` | 1 | 需要的 GPU 数量 |
| `--min-memory` | `-m` | 8000 | 最小空闲显存 (MB) |
| `--max-util` | | 10 | 最大利用率 (%) |
| `--wait-time` | `-w` | 3600 | 最长等待时间 (秒) |
| `--check-interval` | | 30 | 检查间隔 (秒) |

### 实用命令

```bash
# 查看 GPU 状态
python scripts/gpu_scheduler.py --list-gpus

# 清理过期锁
python scripts/gpu_scheduler.py --clean-locks
```

### 锁机制

- 锁文件：`~/.unix_workflow/gpu_locks/gpu_*.lock`
- 默认超时：30 分钟
- 进程异常退出需手动清理：`--clean-locks`

---

## 完整工作流

```bash
# 1. 创建实验
python scripts/new_exp.py --name unet-brats-baseline

# 2. 验证 intent
python scripts/validate_intent.py workspace/unet-brats-baseline/intent.yaml

# 3. 等待 GPU 并训练
python scripts/gpu_scheduler.py --gpus 1 --min-memory 8000 workspace/unet-brats-baseline/train.py

# 4. 生成报告
python scripts/summarize.py unet-brats-baseline
```
