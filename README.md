# Research Harness

一套由 AI agent 维护的轻量科研项目协议。它让不同 coding agent 从固定入口理解当前研究问题、稳定约束、目录职责、项目状态和未完成任务，但不建立文件数据库，不扫描数据集，也不编排具体研究步骤。

Research Harness 的核心是项目内少量 Markdown 文件。CLI 只负责幂等安装和刷新协议；阅读、判断、验证和研究工作由 agent 完成。

## 适用边界

Research Harness 负责：

- 当前研究定义、范围和稳定约束；
- 目录职责和需要检查的下游对象；
- 当前阶段、焦点、阻塞、下一步和证据门禁；
- 一个可选的长任务契约，以及必要的长期决策。

Research Harness 不负责：

- 文件清单、文件快照、数据集扫描或 manifest；
- hooks、后台进程、任务队列或自动工作流；
- 具体的代码、实验、统计、论文或审稿步骤；
- Git commit、branch、stash、push 或历史重写。

这些工作由 agent、仓库工具或按需加载的领域 skill 判断和执行。

## 快速开始

### 懒人版：直接交给 Agent

在目标项目根目录打开 Codex、Claude Code 或其他能够执行命令的 coding agent，把下面这段话完整发送给它：

```text
请在当前项目中部署并接管 Research Harness，安装源为：
https://github.com/yx-yuu/research-harness.git

要求：
1. 先确认当前工作目录确实是目标项目根目录，并读取已有的 AGENTS.md、CLAUDE.md、README 和用户规则。
2. 优先使用 uvx 临时运行 CLI，不修改全局 Python 环境。先执行 init . --dry-run --json；核对目标目录、计划写入文件和保留内容无误后，再执行 init .。
3. 保留已有规则和未提交改动；不要移动或删除项目文件，不执行 Git commit、push、branch、stash 或历史改写。
4. 初始化后，按照 Research Harness 协议读取项目说明、主要目录、代码/配置入口、当前结果和论文材料，把确认过的稳定信息整理到 agent-docs/project.md，把当前阶段、焦点、阻塞、证据门禁和下一步整理到 agent-docs/state.md。
5. 不建立文件清单，不扫描大型数据集或生成目录。推断内容先作为候选；只有会改变项目定义、约束或使用方式的问题才向我确认。
6. 最后报告实际创建或修改的协议文件、当前权威来源、仍待确认的决定，以及项目是否已经可以继续工作。不要提交或推送改动。
```

Agent 可以直接使用下面的临时命令完成初始化，无需用户预先安装 CLI：

```bash
uvx --from git+https://github.com/yx-yuu/research-harness.git \
  research-harness init . --dry-run --json
uvx --from git+https://github.com/yx-yuu/research-harness.git \
  research-harness init .
```

这一步部署的是项目内协议。安装 Codex 插件属于可选增强；插件安装后需要新开会话才能加载，项目接管不必等待插件安装。

### 只临时使用 CLI

```bash
cd /path/to/project
uvx --from git+https://github.com/yx-yuu/research-harness.git research-harness init .
```

### 安装全局 CLI

```bash
uv tool install git+https://github.com/yx-yuu/research-harness.git
# 或：pipx install git+https://github.com/yx-yuu/research-harness.git
research-harness init /path/to/project
```

建议先预览初始化范围：

```bash
research-harness init /path/to/project --dry-run --json
research-harness init /path/to/project
```

然后在项目中告诉 agent：

```text
使用 research-harness 接管当前项目。
```

Agent 会阅读现有说明、README、主要目录、代码和研究材料，把确认过的稳定信息整理到控制文档中。用户不需要维护文件清单、运行同步命令或手工填写模板。

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

默认只创建 `AGENTS.md`、`CLAUDE.md`、`project.md` 和 `state.md`。`checkpoint.md` 与 `decisions.md` 由 agent 按需创建，完成或失效后删除。

## 接管项目

### 新项目

1. 运行 `init --dry-run --json`，确认只会处理协议入口文件。
2. 运行 `research-harness init <root>`。
3. 让 agent 读取项目材料，确认研究定义、目录职责、稳定约束和当前状态。
4. 对仍不确定且会改变项目范围或规则的问题作出选择。

### 已有项目

`init` 会保留已有用户内容，只追加或刷新受管理区块，不会移动、删除或扫描其他项目文件。已有规则文件可以：

- 集中到 `agent-docs/project.md`，旧文件改为指针或在确认后清理；
- 继续作为唯一权威来源，由 `project.md` 登记来源和适用范围。

规则来源、适用范围或内容发生冲突时，agent 必须报告冲突，不能自行猜测唯一权威版本。复杂老项目可以使用：

```text
使用 research-harness 接管当前项目。保留现有规则文件和权威来源；先识别职责、适用范围、重复和冲突，未经确认不移动或删除，不复制完整规则。
```

旧版 harness 的 `.research-harness.json`、`.research-harness/`、`agent-docs/index.md`、`bootstrap.md`、`claims.md` 和 `tasks/` 只会被报告为审查候选。先提取仍有效的信息，再使用可恢复方式清理。

## 硬规则和当前事实

按生命周期放置规则：

| 内容                                   | 权威位置                     |
| -------------------------------------- | ---------------------------- |
| 所有 agent 都必须遵守的短协议          | `AGENTS.md`                |
| 研究定义、范围、稳定约束、目录职责     | `agent-docs/project.md`    |
| 当前阶段、焦点、阻塞、下一步、证据门禁 | `agent-docs/state.md`      |
| 一个长任务的范围、完成条件和恢复信息   | `agent-docs/checkpoint.md` |
| 忘记后可能重复犯错的关键决定           | `agent-docs/decisions.md`  |

候选结果、模型推断、外部材料和旧对话在核验前都不是当前事实。agent 应检查相关目录和下游对象后，替换权威位置中的过时内容，不建立历史流水或第二套真相。

## 日常使用和跨会话恢复

恢复项目时，agent 默认读取：

1. 最近的 `AGENTS.md`；
2. `agent-docs/project.md`；
3. `agent-docs/state.md`；
4. 只有存在且与当前任务相关时才读取 `checkpoint.md` 或 `decisions.md`。

小型局部任务不需要 checkpoint。关键、长期、跨阶段或容易因上下文压缩中断的写任务需要创建 checkpoint，至少记录目标、范围、完成条件、验证边界、事实、决定、风险和下一步。

同一 worktree 同时只允许一个活动写任务：

- 新会话继续同一任务时，读取并更新原 checkpoint；
- 新请求是只读任务时，不替换活动 checkpoint；
- 新请求是不同的写任务时，先完成、放弃或隔离旧任务，不能静默覆盖或混合；
- 需要并行写任务时，使用不同 worktree。

任务完成后，agent 应核验实际变更、测试和下游影响，更新 `project.md` 或 `state.md`，再用可恢复方式删除 checkpoint。默认不保留任务历史档案。

## CLI

CLI 只保留初始化和版本查询：

```bash
# 预览会触及的协议文件
research-harness init /path/to/project --dry-run

# JSON 预览，适合自动核验
research-harness init /path/to/project --dry-run --json

# 安装或刷新协议
research-harness init /path/to/project

# 查看版本
research-harness --version
```

`init` 只维护 `AGENTS.md`、`CLAUDE.md` 的受管理区块，并在缺失时创建 `project.md`、`state.md`。它不会扫描、移动或删除其他项目文件，不执行 Git 操作，也不生成 manifest、snapshot 或任务数据库。没有 `sync`、`doctor`、`resume`、`checkpoint` 等旧版命令。

## 更新已接管的项目

升级本机 CLI 后，已经接管过的每个项目都应重新运行一次：

```bash
uv tool upgrade research-harness
research-harness init /path/to/project --dry-run
research-harness init /path/to/project
```

如果 CLI 是从本地仓库或指定 tag 安装的，使用强制安装可以避免继续使用旧环境：

```bash
uv tool install --force --no-cache \
  "git+https://github.com/yx-yuu/research-harness.git@<tag>"
```

CLI 更新不会自动改写项目状态；`init` 只刷新协议入口并补齐缺失文件，仍由 agent 判断是否需要更新 `project.md` 和 `state.md`。

## 更新 Codex 插件

Codex 插件和全局 CLI 是两个独立安装面。

| 修改内容                                    | 更新全局 CLI | 更新 Codex 插件        | 对已有项目重新运行`init` |
| ------------------------------------------- | ------------ | ---------------------- | -------------------------- |
| README、测试、CI                            | 否           | 否                     | 否                         |
| skill 或插件 manifest                       | 否           | 是，并新开会话         | 否                         |
| CLI 实现                                    | 是           | 插件内脚本同时变化时是 | 否                         |
| `AGENTS.md`、`CLAUDE.md` 或项目文档模板 | 是           | 是                     | 是                         |
| 正式版本发布                                | 是           | 是，并新开会话         | 协议或模板变化时是         |

### 本地开发迭代

修改 skill、模板、插件脚本或 manifest 后：

1. 运行测试和 plugin/skill 校验；
2. 使用 `plugin-creator` 的 `update_plugin_cachebuster.py` 更新 `0.6.0+codex.<时间戳>` 后缀；
3. 从本地 marketplace 重装插件；
4. 新开 Codex 会话验证。

可以直接告诉 Codex：

```text
使用 plugin-creator 刷新 research-harness 的 cachebuster，校验并重装本地插件；不修改 marketplace 配置，不提交、不推送。
```

```bash
codex plugin add codex-research-harness@personal
```

只执行 `plugin add` 而不刷新同一基础版本的 cachebuster，Codex 可能继续使用旧缓存。只修改 README、测试或 CI 时，不需要更新插件。

同步更新本机 CLI：

```bash
uv tool install --force --no-cache .
```

### 新机器安装 Codex 插件

当前插件通过仓库内的本地 marketplace 提供：

```bash
git clone https://github.com/yx-yuu/research-harness.git
codex plugin marketplace add /path/to/research-harness
codex plugin add codex-research-harness@personal
```

`codex plugin marketplace add` 会在 Codex 配置中登记稳定的仓库根路径，例如 `source = "/path/to/research-harness"`；这里不保存插件版本。`codex plugin add` 才会根据插件 manifest 把具体版本复制到 Codex 缓存。不要手工维护 `last_updated`，也不要把 prompt 或项目文档绑定到版本化缓存路径。

同一机器上如果已经注册了另一个同名 `personal` marketplace，应先解决 marketplace 名称冲突，不要手工修改 Codex 缓存目录。安装或重装后应新开会话。

### Claude Code 和其他 agent

Claude Code 可以直接读取项目中的 `CLAUDE.md`，也可以安装同一 skill：

```bash
mkdir -p ~/.claude/skills
ln -s /path/to/research-harness/plugins/codex-research-harness/skills/research-harness \
  ~/.claude/skills/research-harness
```

其他 agent 至少需要能够读取项目根目录的 `AGENTS.md` 和 `agent-docs/`。没有插件缓存时，项目内协议仍是恢复入口；插件只提供更方便的按需 skill，不是项目事实的唯一存储。

## 正式发布

当前正式版本由 `pyproject.toml`、`harness_core.py`、插件 manifest、README 和测试共同约束。发布新版本时必须同步基础版本号，例如从 `0.6.0` 升级到 `0.6.1` 或 `0.7.0`，再刷新插件 cachebuster。

发布前至少运行：

下面两个校验脚本由 Codex 的 `skill-creator` 和 `plugin-creator` 技能提供，路径按本机安装位置替换；如果只使用 Python CLI，至少运行单元测试和构建检查。

```bash
python -m unittest discover -s tests -v
python3 <skill-creator>/scripts/quick_validate.py \
  plugins/codex-research-harness/skills/research-harness
python3 <plugin-creator>/scripts/validate_plugin.py \
  plugins/codex-research-harness
uv build
python3 scripts/build_zipapp.py
python3 dist/research-harness.pyz --version
```

审查并提交版本变更后，创建并推送对应 tag：

```bash
git tag v0.7.0
git push origin main
git push origin v0.7.0
```

`.github/workflows/release.yml` 会在 `v*` tag 上运行测试，构建 wheel、源码包和 standalone zipapp，生成 `SHA256SUMS`，并创建 GitHub Release。当前 workflow 不发布到 PyPI；用户从 GitHub tag 安装即可：

```bash
uv tool install --force \
  "git+https://github.com/yx-yuu/research-harness.git@v0.7.0"
```

发布前要确认 tag、`pyproject.toml`、CLI 协议版本和插件基础版本一致。`+codex.<时间戳>` 只是 Codex 本地缓存刷新标记，不应替代正式 semver 版本。

## 故障排查

### Agent 没有读取最新 skill

新开会话；然后检查：

```bash
codex plugin list
```

如果插件版本没变化，重新刷新 cachebuster 并运行 `codex plugin add codex-research-harness@personal`。不要直接删除或手工改写 Codex 缓存目录。

### CLI 仍显示旧版本

检查命令来源和版本：

```bash
command -v research-harness
research-harness --version
```

确认安装源后使用 `uv tool install --force --no-cache` 重新安装。CLI 更新后，对目标项目重新执行 `init`。

### `init` 报告旧版控制文件

这不是自动删除请求。让 agent 先从候选文件提取仍有效的研究定义、约束、状态和决策，再用可恢复方式清理；数据集、结果和代码不会被 `init` 扫描或删除。

### 两个任务互相覆盖

检查 `agent-docs/checkpoint.md`。同一 worktree 只允许一个活动写任务；完成、放弃或改用独立 worktree 后再开始新的写任务。

### 项目规则和新请求冲突

agent 应报告规则来源、适用范围、冲突内容和影响，等待用户确认权威版本，不能为了完成请求而静默绕过硬规则。

## 维护命令

```bash
python -m unittest discover -s tests -v
uv build
python3 scripts/build_zipapp.py
```

核心 CLI 只依赖 Python 标准库。当前协议版本：`0.6.0`。
