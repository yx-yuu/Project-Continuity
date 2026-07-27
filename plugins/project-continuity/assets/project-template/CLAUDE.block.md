## Claude Code 适配

- 以项目内 `AGENTS.md`、`agent-docs/project.md` 和 `agent-docs/state.md` 为当前权威入口，不在 auto memory 中重复保存这些内容或压缩完整项目知识。
- auto memory 中与项目当前权威信息冲突、已被替换或已经废止的内容不再有效；忽略该内容，并在可安全控制时清理对应副本。
