# 当前状态

> 这是项目级当前阶段的启动入口，只保存阶段、焦点、已核验阻塞、当前阶段完成条件、支撑当前阶段判断所需的已核验证据和一个项目级操作性下一步；不追加历史日志，也不复制 checkpoint 中的任务契约。

- 更新时间：`2026-08-13T02:54:56+08:00`
- 当前阶段：`0.11.0 release candidate`
- 当前焦点：正式运行时 `AGENTS.md` 协议已完成复审，且 SemGuard 实例的旧无 marker 协议、旧决定路由和旧状态措辞已完成语义清理。

## 下一步

新开 Codex 会话验证 `0.11.0+codex.20260812182047` Skill 已加载，再按发布意图运行远端 CI 和创建 `v0.11.0` release。

## 当前阻塞与待决策

- 当前无已核验阻塞。

## 当前阶段完成条件

- 新会话加载已安装的 `0.11.0` Skill，显式激活边界与仓库定义一致。
- 若发布新版本，远端受支持平台 CI 通过，tag、发行产物和版本元数据一致。

## 当前证据

- Python 3.13.9 下 47 项单元测试通过；`git diff --check` 通过。
- 正式模板在 managed marker 后直接进入 `## 开始任务`，不含产品名或总标题，也不含产品设计、升级、CLI、Skill、RAG、索引、日志或后台机制；回归测试同时核验真实生成区块与模板逐字一致。
- 四文件路由已明确区分项目级长期知识、项目级操作状态、跨会话任务契约和跨任务当前决定；临时信息转化、checkpoint 更新与结算、current-decisions 准入和有效内容完整保留均有显式规则。
- 官方 Skill 与 plugin 校验通过；插件 cachebuster 为 `0.11.0+codex.20260812182047`。
- `0.11.0` sdist、wheel 和 standalone zipapp 已在 `/tmp/project-continuity-agents-final.H1OeL4` 构建并校验；zipapp 和已安装 CLI 的新项目样本均只默认创建四个入口文件，生成的 managed block 与正式模板逐字一致，第二次 dry-run 零写入。
- SemGuard 已完成语义清理：`AGENTS.md` 只保留一份与正式模板逐字一致的 managed block；`index.md` 已改用 `current-decisions.md` 路由，`state.md` 已去除“简洁当前证据”措辞。清理后检测到并保留了 SemGuard `project.md`、`state.md` 和活动 `checkpoint.md` 的并发更新，`CLAUDE.md` 未变；最新版本第二次 dry-run 为零写入。清理备份保留在 `/tmp/semguard-semantic-cleanup-backup.OPZzAh/`。
- 本机 CLI 为 `project-continuity 0.11.0`；插件在 `personal` marketplace 中为 installed、enabled。当前会话早于重装，需新会话加载新 Skill。
