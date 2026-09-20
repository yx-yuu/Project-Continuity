# Project Continuity

[![CI](https://github.com/yx-yuu/Project-Continuity/actions/workflows/ci.yml/badge.svg)](https://github.com/yx-yuu/Project-Continuity/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

[English](README.md) | 简体中文

> 让 coding agent 记住项目，而不是每次从零开始。

Project Continuity 是一套基于 Markdown、由 agent 维护的轻量项目连续性协议。它把用户意图、已核验的项目事实、作用域明确的规则、权威来源和未完成任务状态，保存为项目中可审阅、可版本控制的上下文。

当会话切换、agent 更换或任务被中断时，agent 可以从当前有效信息继续工作；搜索、推理、实现和验证仍由 agent 自主完成。你得到的是一层透明的项目记忆，而不是一个接管项目的自动化平台。

## 为什么需要它

长期项目最容易丢失的，往往不是代码，而是“现在到底以什么为准”：

- 项目背景、约束和用户纠正散落在不同会话与文档里；
- 新 agent 只能依赖过时摘要，重新猜测项目当前状态；
- 被中断的长任务没有清晰的恢复点；
- 多个 coding agent 都在工作，却没有一份共同、可追溯的当前权威。

Project Continuity 用少量职责清晰的 Markdown 文件把这些信息放回项目本身，让它们跟着代码一起版本控制，也能被人直接阅读和修正。

## 你会得到什么

- **跨会话连续性**：新会话先恢复项目当前定义、状态和相关权威来源。
- **事实与任务分层**：项目长期知识、项目阶段、当前决定和未完成任务各有唯一位置，不互相覆盖。
- **可追溯、可修正**：内容是普通 Markdown，变更可以审阅，Git 可以保留历史。
- **低侵入接入**：CLI 只维护协议入口和缺失的基础文件，不改写已有项目知识；Codex Skill 也只在需要时显式调用。
- **没有隐形基础设施**：不需要数据库、向量索引、后台进程、hooks 或固定工作流。

## 核心模型

```text
用户提出目标、约束和纠正
        ↓
项目用 Markdown 保存当前有效知识与状态
        ↓
agent 按需读取完整来源并自主完成工作
        ↓
持久化事件发生时，agent 将核验后的当前信息写回项目
```

- 用户拥有最终决定权。
- 项目保存当前权威信息。
- agent 负责理解、执行、核验和维护状态。
- Project Continuity 管理三者之间的信息连续性，不管理 agent 的执行流程。

## 轻量边界

“轻量”指 Project Continuity 的结构和机制简单，不是限制项目知识规模。

Project Continuity 不建立：

- 文件清单、快照或第二套项目数据库；
- 向量知识库、embedding 或自动摘要系统；
- 命令链、固定工作流、任务队列或角色编排；
- hooks、后台进程或自动扫描；
- Git branch、commit、stash、push 或历史管理流程。

项目知识可以很多，任何 Markdown 都没有字数、行数、token 数或知识容量上限。只要内容仍然有效，就应完整保存或登记其权威来源，不能为了篇幅或 token 预算做有损摘要、压缩、截断或删除。快速启动依靠路由和按需读取，而不是用摘要替代完整知识。

## 正式运行时协议边界

`plugins/project-continuity/assets/project-template/AGENTS.block.md` 是安装到普通项目中的正式运行时协议源码。目标项目的 `AGENTS.md` managed block 是它的实例；本仓库根目录的 `AGENTS.md` 只是 Project Continuity 自身的 dogfooding 实例，不反向定义产品协议。

正式运行时协议在 managed marker 后直接从 `## 开始任务` 开始，不显示产品名称或额外总标题；只包含 agent 每次项目工作需要执行的跨 agent 规则：读取顺序、四类语义文件职责、信息准入与放置、唯一权威、更新清理和任务结算。产品设计理由保留在 README，旧协议迁移保留在升级说明和 Skill，CLI 行为保留在命令文档，Codex Skill 的调用边界保留在 Skill 描述；这些内容不进入普通项目的运行时 harness。

## 默认结构

```text
project/
├── AGENTS.md
├── CLAUDE.md
└── agent-docs/
    ├── project.md
    ├── state.md
    ├── checkpoint.md    # 按需
    └── current-decisions.md # 按需
```

默认只创建 4 个文件：

| 文件 | 职责 |
|---|---|
| `AGENTS.md` | 始终可见的轻量判断协议和 Project Continuity 入口 |
| `CLAUDE.md` | Claude Code 导入 `AGENTS.md` 的适配层 |
| `agent-docs/project.md` | 当前项目定义、完整有效知识、项目规则和权威入口 |
| `agent-docs/state.md` | 项目级阶段、焦点、已核验阻塞、阶段完成条件、支撑当前阶段判断所需的已核验证据和一个下一步，不复制未完成任务契约 |

另外两个文件只在需要时存在：

| 文件 | 生命周期 |
|---|---|
| `agent-docs/checkpoint.md` | 跨会话未完成任务契约的唯一权威；长任务或易中断写任务存在时创建，完成或明确放弃后用可恢复方式删除 |
| `agent-docs/current-decisions.md` | 当前有效决定无法从其他权威来源恢复，且其理由或失效条件会影响未来判断时创建；决定失效后与对应路由一起删除 |

Project Continuity 不要求项目把所有知识复制进 `project.md`。现有设计文档、规范、代码、配置、数据说明和其他 Markdown 可以继续作为唯一权威来源，由 `project.md` 登记其职责和适用范围。

四类语义文件分别回答四个问题：

| 文件 | 回答的问题 |
|---|---|
| `project.md` | 项目长期是什么，哪些知识、规则和来源当前有效 |
| `state.md` | 项目现在处于什么阶段，当前项目级下一步是什么 |
| `checkpoint.md` | 当前未完成写任务做到哪里，接下来做什么 |
| `current-decisions.md` | 哪些当前决定必须继续生效，为什么，以及何时失效 |

同一信息只保留一个权威位置，其他文件只登记路由或引用，不复制内容。

## 作用域与记忆

用户添加、纠正或废止信息时，agent 先判断作用域：

| 作用域 | 保存位置 | 生命周期 |
|---|---|---|
| 当前操作 | 当前对话 | 操作结束后失效 |
| 当前任务 | 对话或 checkpoint | 任务完成后失效 |
| 当前项目 | `project.md` | 被修改或废止前持续有效 |
| 项目子树 | 对应目录的指令入口 | 被修改或废止前持续有效 |
| 用户所有项目 | 用户级指令 | 被修改或废止前持续有效 |

当前任务要求不会自动升级为项目规则。任务很小且能在当前会话完成时，要求留在对话；任务需要跨会话继续时，写入 checkpoint。临时信息也不会因为存在时间长、重复出现、任务完成或模型认为重要而自动变成长期知识。

只有以下事件需要重新判断是否持久化：

- 用户明确要求记住或长期遵循某项内容；
- 用户添加、纠正或废止跨任务信息；
- agent 核验出会影响后续任务的稳定项目事实，或需要跨会话恢复的项目阶段、未完成任务状态发生变化；
- checkpoint 或 current-decisions 被创建、更新、结算或清理。

普通讨论、分析、建议、搜索结果和任务输出本身不触发写入。只有用户直接表达的意图和 agent 已核验的项目事实可以进入项目权威知识；模型推断、未核验外部内容和任务输出不能自动晋升为长期知识。`state.md` 可以额外保存项目级阶段、焦点、已核验阻塞、当前阶段完成条件、支撑当前阶段判断所需的已核验证据和一个项目级操作性下一步，但不能包含任务目标、任务进度、任务状态或任务级约束；checkpoint 可以额外保存任务目标、用户给出的任务级约束、已核验进度与阻塞和一个任务级操作性下一步；current-decisions 只保存必须跨任务保留且未来判断仍依赖其理由或失效条件的当前决定。这些内容只留在各自的唯一权威位置，不因存在而复制或升级到其他文件。秘密、凭据和个人数据不能写入控制面。

用户期望的目标状态和项目当前事实是不同对象。例如，“项目以后支持 Python 3.10”不能覆盖“当前配置最低为 Python 3.11”，反之亦然；两者存在差异时，应分别准确记录为意图和事实。用户的新表述只替换同一作用域的旧用户意图，agent 核验的真实项目状态决定事实表述。实现完成并核验一致后，清理过渡差异，只保留统一的当前形式。

保存的信息也不会自动应用到每项工作。agent 只读取和应用作用域覆盖当前任务、并且会实质影响当前判断的内容；项目背景不是自动执行约束。

## 添加、替换与删除

Project Continuity 保存的是当前有效形式，不是变更历史。

- 新信息独立且与当前知识兼容：添加。
- 新信息改变同一作用域和对象：替换旧值。
- 用户明确废止且没有新值：删除。
- 只适用于当前任务：暂存在对话或 checkpoint。

替换后只保留：

```text
项目定位：通用的 agent 项目连续性协议。
```

不要保留：

```text
项目以前只支持 A，现在不再只支持 A，而是同时支持 A 和 B。
```

替换或删除时，agent 清理活动控制面中的旧表述、冲突副本和引用。Git 可以保留版本历史，但历史不进入默认上下文。

同一作用域出现无法判断的冲突，或作用域不明确且会显著影响未来行为时，agent 才询问用户。发生项目级持久化修改后，agent 应简短说明更新内容、作用域和位置。

## 激活机制

Project Continuity 采用“始终感知、按事件更新、复杂场景才使用 Skill”的机制。

| 场景 | 行为 |
|---|---|
| 新任务开始 | 读取短控制面和相关权威来源，不写入，不调用 Skill |
| 当前操作或当前任务要求 | 留在对话；需要跨会话时更新 checkpoint，不复制到 state |
| 简单的项目级添加、替换或删除 | 直接按 `AGENTS.md` 协议处理 |
| 普通编码、分析、测试和文件检查 | 正常工作，不调用 Skill |
| 无冲突的 checkpoint 创建、暂停、恢复或完成 | 直接按 `AGENTS.md` 协议处理，不调用 Skill |
| 接管或升级、复杂权威冲突、跨来源清理，或 checkpoint 与真实 worktree 状态不一致 | 显式使用 `$project-continuity` |

Codex Skill 默认关闭隐式调用。项目即使没有加载 Skill，仍可通过 `AGENTS.md`、`agent-docs/project.md` 和 `agent-docs/state.md` 正常工作。

修改持久化内容前，agent 重新读取目标文件和相关真实来源；发现其他 actor 已修改时，基于最新版合并并重新判断冲突。只有写入后重新读取核验成功，才能说明内容已持久化；明确的持久化请求失败时必须如实报告。

## Agent 如何恢复上下文

新 agent 或新会话按以下顺序恢复：

```text
读取 AGENTS.md
→ 读取 agent-docs/project.md 和项目级 agent-docs/state.md
→ 存在 agent-docs/checkpoint.md 时，以它作为跨会话未完成任务契约的唯一权威
→ 按权威路由读取与任务有关的完整来源
→ 仅在 project.md 路由相关时读取 agent-docs/current-decisions.md
→ 检查真实项目状态并自主工作
```

这避免每次扫描整个仓库，也避免只依赖失真的压缩摘要。

## 未完成任务与 worktree

同一 worktree 只允许一个未完成写任务。checkpoint 可以是：

- `active`：当前正在执行；
- `paused`：暂时停止，但以后继续。

暂停任务时保留 checkpoint，记录已核验进度、用户给出的任务级约束、已核验阻塞和一个下一步。`state.md` 不复制这些任务内容。只有完成或明确放弃后才删除 checkpoint。

任务完成时先结算 checkpoint：把已核验且跨任务稳定的事实或规则写入 `project.md`，把项目阶段变化写入 `state.md`，把仍需保留理由或失效条件的决定写入 `current-decisions.md`，详细结果保留在代码、配置、报告等真实权威来源中；清理重复或过时表述后，再用可恢复方式删除 checkpoint。不能把整份任务进度复制成长期知识。

新请求是只读任务时，可以在同一 worktree 处理而不替换 checkpoint。另一项写任务必须使用独立 worktree，因为新对话只能隔离聊天上下文，不能隔离未完成的代码和文件状态。每个 worktree 维护自己的 checkpoint。

## 5 分钟上手

CLI 当前从 GitHub 安装，支持 Python 3.10 及以上，只依赖 Python 标准库。它只负责安装或刷新协议入口，不启动服务，也不要求项目迁移到新的数据库。

### 1. 安装 CLI

```bash
uv tool install --force git+https://github.com/yx-yuu/Project-Continuity.git
# 或：pipx install git+https://github.com/yx-yuu/Project-Continuity.git
```

不想安装全局工具时，可以直接使用 `uvx`：

```bash
uvx --from git+https://github.com/yx-yuu/Project-Continuity.git \
  project-continuity init . --dry-run --json
```

### 2. 预览并初始化项目

在目标项目根目录先预览范围，再写入协议：

```bash
project-continuity init . --dry-run --json
project-continuity init .
```

默认会创建或刷新以下入口：

```text
AGENTS.md
CLAUDE.md
agent-docs/project.md
agent-docs/state.md
```

### 3. 让 agent 接管

初始化完成后，在目标项目中告诉 agent：

```text
使用 $project-continuity 接管当前项目。先运行 init . --dry-run --json，确认范围后初始化；保留完整有效知识和已有改动，不建立文件清单或工作流，不提交或推送。
```

没有加载 Codex Skill 时，项目仍可依靠 `AGENTS.md`、`project.md` 和 `state.md` 工作；Skill 只是复杂接管、升级和冲突修复时的按需工具。

## 通过 Codex 自动安装

### 最简单：把下面整段发给 Codex

不需要先克隆仓库，也不需要自己判断安装命令。新建一个 Codex 任务，把下面整段原样发给它：

```text
请帮我安装或升级 Project Continuity。

官方仓库：https://github.com/yx-yuu/Project-Continuity

目标：
1. 安装或升级 `project-continuity` CLI。
2. 把官方仓库添加为 Codex plugin marketplace，并安装 `project-continuity` 插件。
3. 验证 CLI 和插件都能正常使用。

请直接检查当前操作系统、Shell、Python、Git、Codex CLI、uv 和 pipx 的实际状态，然后完成安装，不要只给我命令或教程。

安装要求：
- CLI 优先使用：`uv tool install --force git+https://github.com/yx-yuu/Project-Continuity.git`。
- 没有 uv 时可以使用 pipx；如果两者都没有，选择不需要管理员权限的安全安装方式。不要使用 sudo，也不要修改系统 Python。
- 添加 marketplace 时使用：`codex plugin marketplace add yx-yuu/Project-Continuity --ref main`。
- 当前 marketplace 名称是 `personal`，安装插件时使用：`codex plugin add project-continuity@personal`。
- 如果已经安装，执行升级或重装，不要创建重复配置。
- 如果 `personal` 已被另一个 marketplace 占用，不要覆盖它；保留已有配置并告诉我准确的冲突和解决选项。
- 不要初始化或修改当前项目，不要提交或推送任何仓库；这次只安装工具和插件。

完成前必须验证：
- `project-continuity --version` 可以执行。
- `codex plugin list` 中 `project-continuity@personal` 是 installed、enabled。
- 所有安装来源都指向 `yx-yuu/Project-Continuity`。

最后只向我汇报安装位置、版本、验证结果，以及是否需要新建 Codex 任务来加载插件。遇到权限、网络或认证问题时，先自行诊断安全的替代方案；确实需要我操作时，再给出一条明确命令和原因。
```

这段提示词只安装 CLI 和 Codex 插件，不会接管当前目录。安装成功后，在需要接管的项目中使用上一节的提示词。

## 安装 Codex 插件

项目协议不依赖插件。插件只为复杂的 Project Continuity 维护提供按需 Skill。

```bash
codex plugin marketplace add yx-yuu/Project-Continuity --ref main
codex plugin add project-continuity@personal
```

安装或更新后请新开会话，Codex 才会加载新版本。Claude Code 可以直接读取项目中的 `CLAUDE.md`，也可以按需链接同一个 Skill。

## CLI 参考

CLI 只有初始化和版本查询两个入口：

| 命令 | 用途 |
|---|---|
| `project-continuity init [PATH]` | 初始化或刷新项目协议，默认路径为当前目录 |
| `project-continuity init PATH --project-name NAME` | 初始化时指定项目名称 |
| `project-continuity init PATH --dry-run` | 只预览计划，不写文件 |
| `project-continuity init PATH --json` | 输出机器可读的 `created`、`updated`、`unchanged` 和 `planned` |
| `project-continuity --version` | 查看 CLI 与协议版本 |

`init` 会：

- 刷新 `AGENTS.md` 和 `CLAUDE.md` 的 managed block；
- 保留 managed block 外的用户内容；
- 在缺失时创建 `project.md` 和 `state.md`；
- 不解析或改写已有 `project.md`、`state.md` 及两个按需文件，它们完全由 agent 按协议维护；
- 在 dry-run 和 JSON 中按实际差异报告 `created`、`updated`、`unchanged` 与 `planned`，幂等执行不写文件；
- 写入前核对刚读取的控制文档，检测到并发变化时基于最新版重新生成并有限重试；
- 保留完整项目知识、代码、数据、结果和 Git 状态。

managed marker 缺失、重复或顺序损坏时，`init` 会停止并要求人工检查，不会静默生成第二套协议。

## 更新已接管项目

升级 CLI 后，对每个已接管项目重新执行：

```bash
uv tool upgrade project-continuity
project-continuity init /path/to/project --dry-run
project-continuity init /path/to/project
```

CLI 只刷新 `AGENTS.md`、`CLAUDE.md` 的协议入口，并创建缺失的基础语义文件，不自动改写任何已有项目知识或状态。是否需要通用化旧标题或清理旧内容，由 agent 根据当前权威信息判断。
从 `0.10.x` 或更早版本升级时，若旧项目存在 `agent-docs/decisions.md`，让 `$project-continuity` 将其视为待核验的旧控制面：只把符合当前准入条件且仍有效的决定迁移到 `current-decisions.md`，同步更新 `project.md` 路由，再用可恢复方式清理旧文件；不要同时维护两份决定文件。CLI 不自动执行这种语义迁移。

## 本地开发与发布

修改 Skill、模板、插件脚本或 manifest 后：

1. 运行单元测试、Skill 校验和 plugin 校验；
2. 构建 wheel、sdist 和 standalone zipapp；
3. 使用 `plugin-creator` 刷新 `0.11.0+codex.<cachebuster>`；
4. 强制重装本地 CLI 和插件；
5. 新开会话验证 Skill 激活边界。

Python 包或模块发生重命名时，构建前先清理旧的 `build/`、`dist/`、`*.egg-info/` 和 `__pycache__/`。本地 CLI 应安装本次 `uv build` 生成的 wheel，并检查 wheel 中没有旧包目录，避免 setuptools 复用脏 `build/lib`。

```bash
python -m unittest discover -s tests -v
uv build
python3 scripts/build_zipapp.py
python3 dist/project-continuity.pyz --version
```

正式版本由 `pyproject.toml`、CLI 协议版本、插件 manifest、README 和测试共同约束。`.github/workflows/ci.yml` 在 Linux、macOS、Windows 和 Python 3.10/3.13 上验证 CLI；tag release 构建 wheel、sdist、zipapp 和校验和。当前 release 不发布到 PyPI。

核心 CLI 只依赖 Python 标准库。当前协议版本：`0.11.0`。
