# 当前状态

> 这是项目级当前阶段的启动入口，只保存阶段、焦点、已核验阻塞、当前阶段完成条件、支撑当前阶段判断所需的已核验证据和一个项目级操作性下一步；不追加历史日志，也不复制 checkpoint 中的任务契约。

- 更新时间：`2026-09-21T14:39:54+08:00`
- 当前阶段：`0.11.0 release candidate`
- 当前焦点：正式运行时 `AGENTS.md` harness 已采用分层新版结构并保留强信息保真约束；本地 CLI 与插件已重新构建、安装和核验。

## 下一步

检查本次 `main` 推送触发的远端 CI；通过后按发布意图创建 `v0.11.0` release。

## 当前阻塞与待决策

- 当前无已核验阻塞。

## 当前阶段完成条件

- 若发布新版本，远端受支持平台 CI 通过，tag、发行产物和版本元数据一致。

## 当前证据

- Python 3.13.9 下 47 项单元测试通过；`git diff --check` 通过。
- 正式模板在 managed marker 后直接进入 `## 开始任务`，不含产品名或总标题；新版分层明确了 checkpoint 任务身份与当前用户要求的优先关系、信息准入与放置、按需文件生命周期、无 checkpoint 的任务结算、持久化安全和并发约束，同时保留不得因篇幅摘要、压缩、截断或删除有效信息的强约束。
- 四文件路由明确区分项目级长期知识、项目级操作状态、跨会话任务契约和跨任务当前决定；项目级下一步与任务级下一步不得重复记录，已有真实权威来源的信息优先登记路由。
- 官方 Skill 与 plugin 校验通过；插件 cachebuster 为 `0.11.0+codex.20260920171400`。
- `0.11.0` sdist、wheel 和 standalone zipapp 已在仓库 `dist/` 中重新构建；wheel 校验、zipapp 和已安装 CLI 的新项目注入均通过，生成的 managed block 与正式模板逐字一致，第二次 dry-run 零写入。
- SemGuard 已完成语义清理：`AGENTS.md` 只保留一份与正式模板逐字一致的 managed block；`index.md` 已改用 `current-decisions.md` 路由，`state.md` 已去除“简洁当前证据”措辞。清理后检测到并保留了 SemGuard `project.md`、`state.md` 和活动 `checkpoint.md` 的并发更新，`CLAUDE.md` 未变；最新版本第二次 dry-run 为零写入。清理备份保留在 `/tmp/semguard-semantic-cleanup-backup.OPZzAh/`。
- 本机 CLI 已从本次 wheel 强制重装，版本为 `project-continuity 0.11.0`；插件在 `personal` marketplace 中以 `0.11.0+codex.20260920171400` installed、enabled。Codex App Server 通过 `skills/list` 强制刷新后发现并启用了该版本 Skill，插件 ID、缓存路径与 cachebuster 一致，且无加载错误。
