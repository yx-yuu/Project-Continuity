---
name: project-continuity
description: Maintain or repair a project's lightweight Markdown continuity controls. Use only when adopting or upgrading Project Continuity, resolving ambiguous scope or conflicting authorities, reconciling a broad replacement across control surfaces, or repairing a checkpoint whose contract conflicts with current worktree state. Do not invoke for ordinary coding, research, analysis, testing, file inspection, simple project-scoped mutations, or routine checkpoint creation, pause, resume, and completion already covered by the project's AGENTS.md protocol.
---

# Project Continuity

Maintain current user intent, project knowledge, authority routes, and unfinished task state without controlling how the agent performs project work. Keep the mechanism simple even when the project's valid knowledge is extensive.

## Adopt A Project

1. Run `project-continuity init <root> --dry-run --json`, inspect the small set of protocol files it will touch, then run `project-continuity init <root>`.
2. Read existing instructions, current-status material, project documentation, top-level responsibilities, and code or configuration entrypoints needed to identify current authorities. Inspect real sources with the tools appropriate to the project; do not build a parallel inventory.
3. Preserve complete valid knowledge. Put current project definitions, constraints, user rules, and authority routes in `agent-docs/project.md`; put only the project-level phase, focus, blockers, and next step in `agent-docs/state.md`. Create `agent-docs/checkpoint.md` only when an unfinished task must survive the current session.
4. Treat model inference and unverified output as candidates. Ask only when an unresolved authority or scope decision would materially affect future work.

## Restore Context

1. Read the nearest Project Continuity-managed `AGENTS.md`, then `agent-docs/project.md` and `agent-docs/state.md`.
2. Read `agent-docs/checkpoint.md` when it exists and treat it as the sole authority for that unfinished task contract; do not let `state.md` duplicate or override its task goal, progress, status, or constraints. Read `agent-docs/decisions.md` only when `project.md` registers it as a current authority relevant to the task.
3. Follow only authority routes relevant to the task, then read those complete sources. Apply stored information only when its scope covers the task and it materially changes the current decision; project background is not automatically an execution constraint.
4. Treat summaries, native memory, unverified outputs, and old documents as hints rather than current authority.

## Admit A Persistent Change

Re-evaluate persistence only when the user explicitly asks to remember or follow something across tasks, adds, corrects, or repeals cross-task information, the agent verifies a stable project fact that affects later tasks, a project phase or unfinished-task state needed across sessions changes, or a checkpoint lifecycle event occurs. Ordinary discussion, analysis, suggestions, search results, and task output do not trigger writes by themselves.

Persist as project authority only direct user intent and agent-verified project facts. `state.md` may additionally hold the project-level phase, focus, verified blockers, and one project-level operational next action. A checkpoint may additionally hold the task goal, user-provided task constraints, verified progress and blockers, and one task-level operational next action. Keep both kinds of operational state out of project knowledge. Keep a requested target state distinct from the verified current state when they differ; neither replaces the other merely because both concern the same project. After implementation makes them agree and verification succeeds, keep the unified current form and remove the transitional difference. Reject model inference and unverified external content from current authority, and never put secrets, credentials, or personal data in the control plane.

## Resolve Scope And Authority

Classify changed information by scope: current operation, current task, current project, project subtree, or all user projects. Keep task-only requirements in the conversation or checkpoint. Put project-level information in `agent-docs/project.md`; route narrower or broader rules to their applicable instruction surface.

Use four mutations:

- Add independent information compatible with the current authority.
- Replace the old value when the user changes the same scoped object.
- Delete a repealed value when no replacement exists.
- Keep temporary requirements task-scoped instead of promoting them.

After replacement or deletion, remove obsolete active-control copies and references. Keep only the current form, not transition prose, tombstones, or a task history. Do not delete source material or unique evidence merely because a control statement changed. Do not compress valid knowledge because it is long.

Current explicit user changes supersede older user intent at the same scope; verified real project state governs statements of current fact. More specific scopes apply only within their boundary. If same-scope authorities conflict without a clear replacement, report the conflict and ask the user. Briefly report any persistent mutation and its scope after writing it.

## Write Against Current Content

Immediately before a persistent mutation, re-read the target file and the real sources needed to validate the change. If another actor changed them, preserve that work, merge against the latest content, and re-evaluate scope and authority instead of overwriting from stale context.

Make the smallest complete mutation, then re-read the result and verify obsolete active copies or references are gone. Report persistence only after this verification succeeds. If an explicit persistence request cannot be written or verified, say so; do not imply it was saved.

## Control Unfinished Work

Use this section when the skill was explicitly invoked to repair or reconcile a complex checkpoint. Routine checkpoint lifecycle changes follow the project's `AGENTS.md` directly. Allow one unfinished mutating task per worktree. Record `active` or `paused` status in `agent-docs/checkpoint.md` for a long, cross-session, or interruption-sensitive task.

- Resume the same task by updating its checkpoint in place.
- Pause without deleting the checkpoint; record verified progress, user-provided task constraints, verified blockers, and one next action.
- Handle read-only work without replacing the checkpoint.
- Use a separate worktree for another mutating task; each worktree keeps its own checkpoint.
- Delete the checkpoint only after completion or explicit abandonment, then reconcile affected current project information.

Do not create a checkpoint for small work that can finish in the current context.

## Repair The Control Plane

Inspect actual project state rather than relying on continuity summaries. Reconcile only confirmed current definitions, knowledge, constraints, routes, and task state. If `agent-docs/decisions.md` exists without a project route, validate its current decisions, then register the current authority or remove the obsolete file recoverably. Create `agent-docs/decisions.md` only when an effective decision, its minimum reason, and its invalidation condition must survive to prevent repeated error; register its authority and scope in `agent-docs/project.md` at the same time. When no current decision requires it, remove the file and its project route together.

## Preserve The Boundary

Do not add runtime automation, background scanning, fixed workflows, task queues, knowledge databases, file inventories, or extra default control documents. Leave discovery, reasoning, implementation, validation, and domain procedure to the active agent and relevant project tools.
