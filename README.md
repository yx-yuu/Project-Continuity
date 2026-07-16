# Research Harness

一套面向单个科研项目、可供不同 coding agent 共用的轻量项目控制协议。它维护当前研究定义、项目级约束、当前状态、必要决策、证据关系、任务边界和变更影响，并让 compact 或新会话能够从固定入口恢复。

它不会为所有项目预装同一套文献、方法、实验或审稿流程。具体任务由用户和按需 skill 执行，但必须服从 harness 管理的项目约束、证据门禁、范围、完成条件和验证边界。

## 快速开始

```bash
cd /path/to/research-harness

# 只读查看候选结构
./bin/research-harness scan /path/to/project

# 初始化或迁移项目控制面
./bin/research-harness init /path/to/project

# 检查外部文件变化
./bin/research-harness sync /path/to/project

# 完成影响审查和上下文更新后接受新基线
./bin/research-harness sync /path/to/project --accept

# compact 或新会话后恢复
./bin/research-harness resume /path/to/project

# 检查结构、项目就绪状态、任务契约和恢复预算
./bin/research-harness doctor /path/to/project
```

## 项目结构

```text
project/
├── AGENTS.md
├── CLAUDE.md              # 导入 AGENTS.md，不复制协议
├── .research-harness.json
├── .research-harness/
│   └── snapshot.json      # 文件增量基线，不进入默认上下文
└── agent-docs/
    ├── index.md
    ├── project.md
    ├── state.md
    ├── decisions.md
    └── checkpoint.md      # 仅在受控任务存在时创建
```

## 单一任务契约与 checkpoint

关键、长程、跨阶段或需要跨会话恢复的任务使用一个可覆盖 checkpoint：

```bash
./bin/research-harness checkpoint save --path /path/to/project \
  --goal "当前要完成的结果" \
  --scope "允许修改的范围和明确非目标" \
  --done "可以核验的完成条件" \
  --validation "与风险匹配的检查及预算" \
  --impact "可能受影响的代码、实验、结果或论文对象" \
  --current "已经核验的进展" \
  --next "下一步唯一动作" \
  --fact "已确认事实" \
  --decision "用户决定" \
  --risk "尚未解决的风险" \
  --ref "src/current.py"
```

每次保存覆盖旧内容，不形成任务历史。存在未确认文件变化时，普通 `checkpoint clear` 会拒绝清理；完成影响审查和 `sync --accept` 后再清理。只有明确放弃任务时才使用 `--force`。

## 控制边界

- harness 管理：当前项目定义与约束、状态、证据来源、任务边界、变更影响、恢复与信息生命周期。
- 按需 skill 管理：文献检索、方法设计、编码、实验、统计和审稿的具体执行步骤。
- task skill 不得绕过：项目约束、证据门禁、完成条件、验证边界和当前权威来源。
- 自动扫描、compact 摘要、模型推断和任务输出始终只是 candidate。
- 同一对象只保留一个当前权威来源；默认不保存任务 archive。
- `doctor` 同时检查默认恢复包总字节预算，避免通过长单行或多个核心文件绕过行数限制。

## Agent 适配

`init` 在 `AGENTS.md` 中维护共享控制协议，并在 `CLAUDE.md` 中写入 `@AGENTS.md`。Codex 读取前者，Claude Code 按[官方 import 机制](https://code.claude.com/docs/en/memory#agents-md)读取同一内容；两个入口都会保留原有用户规则。

### Codex

```bash
codex plugin marketplace add /path/to/research-harness
codex plugin add codex-research-harness@personal
```

### Claude Code

```bash
mkdir -p ~/.claude/skills
ln -s /path/to/research-harness/plugins/codex-research-harness/skills/research-harness \
  ~/.claude/skills/research-harness
```

如果希望在 harness 项目中完全关闭 Claude auto memory，可在项目 `.claude/settings.json` 设置 `"autoMemoryEnabled": false`。

协议版本：`0.4.0`。
