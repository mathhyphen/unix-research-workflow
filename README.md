# Unix Research Workflow

一个专为 ML/DL 科研工作者设计的**意图驱动**实验管理系统，配备 **Claude Code Skill** AI 助手和 **MLflow** 可视化整合。

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🎯 **Intent-First** | 每个实验从清晰的 `intent.yaml` 开始，记录目标、假设和成功标准 |
| 🤖 **AI 驱动** | Claude Code Skill 深度集成，语音控制实验管理 |
| 📊 **MLflow 整合** | 训练过程可视化、模型注册、远程协作 |
| 📝 **自动报告** | 从 metrics 自动生成 Markdown/JSON/HTML 报告 |
| 🔒 **本地优先** | 数据留在本地，敏感研究不出院 |
| 📁 **生命周期管理** | 创建、列表、验证、对比、导出、删除 |

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 基础功能（不需要 MLflow 可视化）
pip install pyyaml

# 完整功能（推荐）
pip install pyyaml mlflow pillow
```

### 2. 创建第一个实验

```bash
# 创建实验目录和 intent 模板
python scripts/new_exp.py --name unet-baseline

# 编辑 intent.yaml 填写实验目的
# workspace/unet-baseline/intent.yaml

# 验证 intent
python scripts/validate_intent.py workspace/unet-baseline/intent.yaml
```

### 3. 在训练代码中整合

```python
from pathlib import Path
from scripts.log_hook import LogHook
from scripts.mlflow_integration import MlflowHook

# 初始化
workspace = Path("workspace/unet-baseline")
log = LogHook(workspace)
mlflow = MlflowHook(workspace, experiment_name="unet-baseline")

mlflow.start_run(log_params={"lr": 0.001, "batch_size": 4})
log.log_environment()

for epoch in range(epochs):
    train_loss = train_one_epoch()
    val_dice = evaluate()

    # 同时记录到 JSONL 和 MLflow
    log.log_epoch(epoch, {"loss": train_loss, "dice": val_dice}, phase="val")
    mlflow.log_epoch(epoch, {"loss": train_loss, "dice": val_dice}, phase="val")

mlflow.end_run()
```

### 4. 生成报告

```bash
# 生成 Markdown 报告
python scripts/summarize.py unet-baseline

# 查看 MLflow UI
mlflow ui --backend-store-uri workspace/unet-baseline/mlruns
# 浏览器打开 http://localhost:5000
```

---

## 📁 目录结构

```
Unix_workflow/
├── scripts/
│   ├── __init__.py              # 包导出
│   ├── new_exp.py               # 创建实验
│   ├── list_exp.py              # 列出实验
│   ├── show_exp.py              # 显示详情
│   ├── validate_intent.py       # 验证 intent
│   ├── log_hook.py              # JSONL 日志记录
│   ├── mlflow_integration.py    # MLflow 整合
│   ├── summarize.py             # 生成报告
│   ├── compare_exp.py           # 对比实验
│   ├── export_csv.py            # 导出 CSV
│   └── rm_exp.py                # 删除实验
├── templates/
│   └── intent.yaml              # Intent 模板
├── workspace/                   # 实验数据目录（.gitignore 忽略）
│   └── <name>/
│       ├── intent.yaml
│       ├── logs/
│       │   └── metrics.jsonl
│       ├── findings/
│       │   └── report.md
│       └── mlruns/              # MLflow 数据
├── rules/
│   └── research_protocol.md     # 研究规范
├── SKILL.md                     # Claude Code Skill 定义
├── .gitignore                   # Git 忽略规则
└── README.md
```

---

## 📋 命令参考

| 命令 | 用法 | 说明 |
|------|------|------|
| `new_exp.py` | `--name <name>` | 创建新实验 |
| `list_exp.py` | `[-f table\|json]` | 列出所有实验（状态码：I/M/R） |
| `show_exp.py` | `<name>` | 显示实验详情 |
| `validate_intent.py` | `<path>` | 验证 intent.yaml |
| `summarize.py` | `<name> [-F format]` | 生成报告 (markdown/json/html) |
| `compare_exp.py` | `<name1> <name2> [-m metric]` | 对比多个实验 |
| `export_csv.py` | `<name> [-o output]` | 导出为 CSV |
| `rm_exp.py` | `<name> [--force]` | 删除实验 |
| `scan_legacy.py` | `[-t target]` | 扫描旧实验目录（迁移工具） |
| `migrate_legacy.py` | `<source> [-n name]` | 迁移旧实验到标准结构 |
| `cleanup_legacy.py` | `archive\|delete` | 批量归档/删除旧目录 |

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
    - name: dice_TC
      threshold: 0.80
      direction: higher_is_better
    - name: hd95
      threshold: 5.0
      direction: lower_is_better
constraints:
  max_runtime_hours: 48
  gpu: "RTX 4090"
  dataset: "BraTS2020"
```

---

## 🤖 Claude Code Skill 集成

这个项目包含一个 **Claude Code Skill**（`SKILL.md`），让 AI 帮你管理实验。

### 触发关键词

当你对 Claude Code 说以下内容时，会自动触发这个 Skill：

- "创建实验 xxx"
- "看看有哪些实验"
- "实验跑完了，生成报告"
- "对比 exp-001 和 exp-002"
- "导出 metrics 到 CSV"
- "训练代码怎么加 logging"

### 使用方式

1. 将项目目录添加到 Claude Code 的技能搜索路径
2. 或者 symlink 到 `~/.claude/skills/unix-research-workflow`

```bash
# Linux/Mac
ln -s /path/to/Unix_workflow ~/.claude/skills/unix-research-workflow

# Windows (管理员权限)
mklink /J "%USERPROFILE%\.claude\skills\unix-research-workflow" "D:\apps\Unix_workflow"
```

---

## 📊 MLflow 整合

### 本地查看

```bash
mlflow ui --backend-store-uri workspace/<exp-name>/mlruns
# 访问 http://localhost:5000
```

### 远程服务器（团队协作）

```bash
# 服务器端
mlflow ui --host 0.0.0.0 --port 5000 --backend-store-uri /path/to/mlruns

# 本地浏览器
http://<server-ip>:5000
```

### 功能对比

| 功能 | 只用 Skill | Skill + MLflow |
|------|-----------|----------------|
| 实验目录管理 | ✅ | ✅ |
| Intent 追踪 | ✅ | ✅ |
| 报告生成 | ✅ | ✅ |
| AI 交互 | ✅ | ✅ |
| 训练曲线可视化 | ❌ | ✅ |
| 多实验对比图 | ❌ | ✅ |
| 模型注册 | ❌ | ✅ |
| 远程协作 | ❌ | ✅ |

---

## 🔧 状态码说明

| 代码 | 含义 | 条件 |
|------|------|------|
| `I` | Initialized | 只有 intent.yaml，未开始训练 |
| `M` | Metrics | 有 `logs/metrics.jsonl`，正在训练 |
| `R` | Report | 有 `findings/report.md`，报告完成 |

---

## 🛠️ 故障排除

### Git worktree 创建失败

```
WARNING: Failed to create git worktree: not a git repository
```

**解决**: 这不是 git 仓库，实验仍可正常使用，只是没有 git 集成功能。

```bash
# 如果想启用 git 集成
git init
git add .
git commit -m "Initial commit"
```

### Intent 验证失败

```
Intent validation failed: Objective must be at least 20 characters
```

**解决**: objective 太短了，写详细一点（至少 20 字符）。

### 找不到 metrics.jsonl

```
No metrics.jsonl found for '<name>'
```

**解决**: 训练代码里还没加 `LogHook`，参考上面的整合示例。

---

## 📝 隐私和安全

- ✅ **无云端依赖**: 所有数据存储在本地
- ✅ **敏感数据保护**: `.gitignore` 自动忽略 `workspace/`、`mlruns/`、`.env` 等
- ✅ **医院内网友好**: MLflow 可部署在内网服务器
- ✅ **API Keys 不提交**: 敏感配置文件已加入 `.gitignore`

---

## 🎓 适用场景

| 场景 | 推荐度 | 说明 |
|------|--------|------|
| 个人科研管理 | ⭐⭐⭐⭐⭐ | 轻量、够用、AI 加持 |
| 小团队 (2-5 人) | ⭐⭐⭐⭐⭐ | 配合 MLflow 服务器效果好 |
| 医学影像 DL | ⭐⭐⭐⭐⭐ | 支持 3D 分割指标、多模态 |
| 大实验室 (10+ 人) | ⭐⭐⭐⭐ | 建议补充 W&B 企业版 |
| 跨机构合作 | ⭐⭐⭐ | 需配置远程 MLflow |

---

## 📄 License

MIT License

---

## 🔗 相关链接

- [SKILL.md](SKILL.md) - Claude Code Skill 详细定义
- [rules/research_protocol.md](rules/research_protocol.md) - 研究规范协议
