---
name: project-continuity
description: Maintain or repair a project's lightweight Markdown continuity controls. Use only when adopting or upgrading Project Continuity, resolving ambiguous scope or conflicting authorities, reconciling a broad replacement across control surfaces, migrating legacy continuity context, or pausing, resuming, switching, or completing a checkpointed mutating task. Do not invoke for ordinary coding, research, analysis, testing, file inspection, or simple project-scoped additions, replacements, and deletions already covered by the project's AGENTS.md protocol.
---

# Project Continuity

Maintain current user intent, project knowledge, authority routes, and unfinished task state without controlling how the agent performs project work. Keep the mechanism simple even when the project's valid knowledge is extensive.

## Adopt A Project

1. Run `project-continuity init <root> --dry-run --json`, inspect the small set of protocol files it will touch, then run `project-continuity init <root>`.
2. Read existing instructions, current-status material, project documentation, top-level responsibilities, and code or configuration entrypoints needed to identify current authorities. Inspect real sources with the tools appropriate to the project; do not build a parallel inventory.
3. Preserve complete valid knowledge. Put current project definitions, constraints, user rules, and authority routes in `agent-docs/project.md`; put the active task and state in `agent-docs/state.md`.
4. Treat model inference and unverified output as candidates. Ask only when an unresolved authority or scope decision would materially affect future work.
5. Review legacy candidates reported by `init`, reconcile still-current information, and remove obsolete control files only with a recoverable mechanism.

## Restore Context

1. Read the nearest Project Continuity-managed `AGENTS.md`, then `agent-docs/project.md` and `agent-docs/state.md`.
2. Read `agent-docs/checkpoint.md` when it exists. Read `agent-docs/decisions.md` only when `project.md` registers it as a current authority relevant to the task.
3. Follow authority routes to read complete sources relevant to the task. Treat summaries, native memory, unverified outputs, and old documents as hints rather than current authority.

## Resolve Scope And Authority

Classify changed information by scope: current operation, current task, current project, project subtree, or all user projects. Keep task-only requirements in the conversation or checkpoint. Put project-level information in `agent-docs/project.md`; route narrower or broader rules to their applicable instruction surface.

Use four mutations:

- Add independent information compatible with the current authority.
- Replace the old value when the user changes the same scoped object.
- Delete a repealed value when no replacement exists.
- Keep temporary requirements task-scoped instead of promoting them.

After replacement or deletion, remove obsolete active-control copies and references. Keep only the current form, not transition prose, tombstones, or a task history. Do not delete source material or unique evidence merely because a control statement changed. Do not compress valid knowledge because it is long.

Current explicit user changes supersede older project wording. More specific scopes apply only within their boundary. If same-scope authorities conflict without a clear replacement, report the conflict and ask the user. Briefly report any persistent mutation and its scope after writing it.

## Control Unfinished Work

Allow one unfinished mutating task per worktree. Record `active` or `paused` status in `agent-docs/checkpoint.md` for a long, cross-session, or interruption-sensitive task.

- Resume the same task by updating its checkpoint in place.
- Pause without deleting the checkpoint; record verified progress, temporary constraints, risks, and one next action.
- Handle read-only work without replacing the checkpoint.
- Use a separate worktree for another mutating task; each worktree keeps its own checkpoint.
- Delete the checkpoint only after completion or explicit abandonment, then reconcile affected current project information.

Do not create a checkpoint for small work that can finish in the current context.

## Repair The Control Plane

Inspect actual project state rather than relying on continuity summaries. Reconcile only confirmed current definitions, knowledge, constraints, routes, and task state. Treat an existing `agent-docs/decisions.md` without a project route as a legacy candidate: validate its current decisions, then register the current authority or remove the obsolete file recoverably. Create `agent-docs/decisions.md` only when an effective decision, its minimum reason, and its invalidation condition must survive to prevent repeated error; register its authority and scope in `agent-docs/project.md` at the same time. When no current decision requires it, remove the file and its project route together.

## Preserve The Boundary

Do not add runtime automation, background scanning, fixed workflows, task queues, knowledge databases, file inventories, or extra default control documents. Leave discovery, reasoning, implementation, validation, and domain procedure to the active agent and relevant project tools.
