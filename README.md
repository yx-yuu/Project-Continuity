# Research Harness

一套由 AI agent 维护的轻量科研项目协议。它让不同 coding agent 从固定入口理解当前研究问题、稳定约束、目录职责、项目状态和未完成任务，但不建立文件数据库，不扫描数据集，也不编排具体研究步骤。

Research Harness 的核心是项目内少量 Markdown 文件。CLI 只负责幂等安装和刷新协议；之后的阅读、判断、验证与维护由 agent 完成。

## 快速开始

不安装全局命令时：

```bash
cd /path/to/project
uvx --from git+https://github.com/yx-yuu/research-harness.git research-harness init .
```

长期使用：

```bash
uv tool install git+https://github.com/yx-yuu/research-harness.git
# 或：pipx install git+https://github.com/yx-yuu/research-harness.git
research-harness init /path/to/project
```

随后在项目中告诉 agent：

```text
使用 research-harness 接管当前项目。
```

Agent 会阅读现有项目材料，确认当前研究定义和目录职责，只在研究含义或稳定约束确实需要选择时提问。用户不需要维护文件清单、运行同步命令或手工填写模板。

## 项目结构

```text
project/
├── AGENTS.md
├── CLAUDE.md                 # Claude Code 导入 AGENTS.md 的适配
└── agent-docs/
    ├── project.md            # 当前研究定义、约束和目录职责
    ├── state.md              # 当前阶段、焦点、下一步和阻塞
    ├── checkpoint.md         # 仅在一个跨阶段写任务存在时创建
    └── decisions.md          # 仅在关键决定必须长期记住时创建
```

默认只创建 `project.md` 和 `state.md`。checkpoint 与 decisions 均由 agent 按需创建，完成或失效后删除。

## 工作方式

### 接管项目

Agent 读取现有 README、研究说明、主要目录、代码/实验/结果/论文入口，将稳定信息整理到 `project.md`，将当前进展整理到 `state.md`。目录表只记录职责和变化时需要检查的对象，不枚举目录中的文件。

### 执行任务

具体的代码、实验、统计、论文和审稿流程由 agent 或按需 skill 决定。harness 只要求它们服从当前约束、证据门禁、任务范围和完成条件。

关键、长程或跨阶段任务使用一个可覆盖的 `checkpoint.md`；小型局部任务不创建。一个 worktree 同时只允许一个活动写任务，新写任务不能静默覆盖旧 checkpoint。

### 完成任务

Agent 使用 Git、测试、实验工具或其他领域工具直接检查实际变化和结果，识别受影响目录及下游对象，随后更新当前项目定义或状态。harness 不保存文件快照，也没有 `sync --accept` 之类的第二套文件真相。

## CLI

CLI 只保留初始化命令：

```bash
# 预览会触及的协议文件
research-harness init /path/to/project --dry-run

# 安装或刷新协议
research-harness init /path/to/project

# 查看版本
research-harness --version
```

`init` 只维护 `AGENTS.md`、`CLAUDE.md` 的受管理区块，并在缺失时创建 `project.md`、`state.md`。它不会扫描、移动或删除其他项目文件，不执行 commit、branch、stash 等 Git 操作，也不生成 manifest 或 snapshot。

## 旧版本迁移

升级本机 CLI 后，在每个项目重新运行一次 `init`：

```bash
uv tool upgrade research-harness
research-harness init /path/to/project
```

旧版 `.research-harness.json`、`.research-harness/` 和 `agent-docs/index.md` 会被报告为审查候选，但不会自动删除。让 agent 先提取仍有效的信息，再使用可恢复方式清理。

## Agent 适配

Codex 插件只提供按需加载的 skill，不运行 hook 或后台任务：

```bash
codex plugin marketplace add /path/to/research-harness
codex plugin add codex-research-harness@personal
```

Claude Code 可直接使用项目中的 `CLAUDE.md`，也可安装同一 skill：

```bash
mkdir -p ~/.claude/skills
ln -s /path/to/research-harness/plugins/codex-research-harness/skills/research-harness \
  ~/.claude/skills/research-harness
```

## 维护与发布

```bash
python3 -m unittest discover -s tests -v
uv build
python3 scripts/build_zipapp.py
```

核心 CLI 只依赖 Python 标准库。协议版本：`0.6.0`。
