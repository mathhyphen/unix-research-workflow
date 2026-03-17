# Unix Research Workflow

一个专为 ML/DL 科研工作者设计的**意图驱动**实验管理系统，配备 **Claude Code Skill** AI 助手、**MLflow** 可视化整合和**GPU 调度**功能。

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🎯 **Intent-First** | 每个实验从清晰的 `intent.yaml` 开始，记录目标、假设和成功标准 |
| 🤖 **AI 驱动** | Claude Code Skill 深度集成，语音控制实验管理 |
| 📊 **MLflow 整合** | 训练过程可视化、模型注册、远程协作 |
| 📝 **自动报告** | 从 metrics 自动生成 Markdown/JSON/HTML 报告 |
| 🎮 **GPU 调度** | 自动等待空闲 GPU、多任务锁定、显存监控 |
| 🔒 **本地优先** | 数据留在本地，敏感研究不出院 |

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 基础功能
pip install pyyaml

# 完整功能（推荐）
pip install pyyaml mlflow pillow
```

### 2. 创建第一个实验

**使用 Claude Code（推荐）**：
```
帮我创建一个实验，叫 unet-baseline
```

**手动创建**：
```bash
git worktree add -b expl/unet-baseline .claude/worktrees/unet-baseline
python scripts/new_exp.py --name unet-baseline
# 编辑 .claude/worktrees/unet-baseline/intent.yaml
python scripts/validate_intent.py .claude/worktrees/unet-baseline/intent.yaml
```

### 3. 在训练代码中整合

```python
from pathlib import Path
from scripts.log_hook import LogHook
from scripts.mlflow_integration import MlflowHook

workspace = Path(__file__).parent
log = LogHook(workspace)
mlflow = MlflowHook(workspace, experiment_name="unet-baseline")

mlflow.start_run(log_params={"lr": 0.001, "batch_size": 4})
log.log_environment()

for epoch in range(epochs):
    train_loss = train_one_epoch()
    val_dice = evaluate()
    log.log_epoch(epoch, {"loss": train_loss, "dice": val_dice}, phase="val")
    mlflow.log_epoch(epoch, {"loss": train_loss, "dice": val_dice}, phase="val")

mlflow.end_run()
```

### 4. 等待 GPU 并运行训练

```bash
python scripts/gpu_scheduler.py --min-memory 8000 train.py --lr 0.001
python scripts/gpu_scheduler.py --list-gpus  # 查看 GPU 状态
```

### 5. 生成报告

```bash
python scripts/summarize.py unet-baseline
mlflow ui --backend-store-uri workspace/unet-baseline/mlruns
```

---

## 📁 目录结构

```
Unix_workflow/
├── scripts/
│   ├── new_exp.py               # 创建实验
│   ├── list_exp.py              # 列出实验
│   ├── validate_intent.py       # 验证 intent
│   ├── log_hook.py              # JSONL 日志记录
│   ├── mlflow_integration.py    # MLflow 整合
│   ├── gpu_scheduler.py         # GPU 调度
│   ├── summarize.py             # 生成报告
│   ├── compare_exp.py           # 对比实验
│   └── rm_exp.py                # 删除实验
├── templates/intent.yaml        # Intent 模板
├── workspace/                   # 实验数据（.gitignore 忽略）
│   └── <name>/
│       ├── intent.yaml
│       ├── logs/metrics.jsonl
│       ├── findings/report.md
│       └── mlruns/
├── SKILL.md                     # Claude Code Skill 定义
└── GPU_SCHEDULER.md             # GPU 调度指南
```

---

## 📋 命令参考

| 命令 | 用法 | 说明 |
|------|------|------|
| `new_exp.py` | `--name <name>` | 创建实验 |
| `list_exp.py` | `[-f table|json]` | 列出实验（状态：I/M/R） |
| `show_exp.py` | `<name>` | 显示详情 |
| `validate_intent.py` | `<path>` | 验证 intent.yaml |
| `summarize.py` | `<name> [-F format]` | 生成报告 (md/json/html) |
| `compare_exp.py` | `<name1> <name2>` | 对比实验 |
| `export_csv.py` | `<name> [-o output]` | 导出 CSV |
| `rm_exp.py` | `<name> [--force]` | 删除实验 |
| `gpu_scheduler.py` | `[选项] script.py` | GPU 调度 |

**状态码**: I=Initialized, M=Metrics, R=Report

---

## 🎯 Intent 模板

```yaml
experiment: unet-baseline
branch: expl/unet-baseline
objective: |
  在 BraTS2020 数据集上训练 3D U-Net 作为基线模型
  验证数据预处理流程是否正确
hypothesis: |
  基线 U-Net 应该达到：
  - 整体肿瘤 Dice > 0.85
  - 肿瘤核心 Dice > 0.80
success_criteria:
  metrics:
    - name: dice_WT
      threshold: 0.85
      direction: higher_is_better
constraints:
  max_runtime_hours: 48
  gpu: "RTX 4090"
```

---

## 🤖 Claude Code Skill

将项目链接到 Claude Code 技能目录：

```bash
# Linux/Mac
ln -s /path/to/Unix_workflow ~/.claude/skills/unix-research-workflow

# Windows (管理员)
mklink /J "%USERPROFILE%\.claude\skills\unix-research-workflow" "D:\apps\Unix_workflow"
```

触发关键词："创建实验 xxx"、"看看有哪些实验"、"生成报告"、"对比实验"

---

## 📊 MLflow 整合

### 本地查看
```bash
mlflow ui --backend-store-uri workspace/<exp-name>/mlruns
# http://localhost:5000
```

### 远程服务器
```bash
# 服务器端
mlflow ui --host 0.0.0.0 --port 5000 --backend-store-uri /path/to/mlruns
# 本地浏览器访问 http://<server-ip>:5000
```

---

## 🛠️ 故障排除

**Worktree 问题**:
```bash
git worktree list          # 查看现有 worktrees
git worktree remove <path> # 删除 worktree
```

**Intent 验证失败**: objective 至少 20 字符

**找不到 metrics.jsonl**: 训练代码需添加 `LogHook`

---

## 📝 隐私和安全

- ✅ **无云端依赖**: 所有数据存储在本地
- ✅ **敏感数据保护**: `.gitignore` 自动忽略 `workspace/`、`mlruns/`、`.env`
- ✅ **医院内网友好**: MLflow 可部署在内网服务器

---

## 📄 License

MIT License
