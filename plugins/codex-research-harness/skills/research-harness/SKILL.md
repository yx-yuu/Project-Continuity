---
name: research-harness
description: Maintain a lightweight, agent-driven control plane for one research project. Use when adopting or refreshing a project; restoring current context; applying project constraints and directory responsibilities; starting, switching, resuming, or completing a critical or cross-stage task; reconciling verified changes across methods, experiments, results, and paper; or removing stale project context. Keep file discovery, Git inspection, validation, and domain work under agent judgment rather than a harness file tracker.
---

# Research Harness

Maintain current project intent, stable constraints, directory responsibilities, current state, and one optional task contract. Let the active agent inspect the real project and choose task procedures; do not build a parallel file inventory, snapshot, or task database.

## Adopt A Project

1. Run `research-harness init <root> --dry-run --json`, inspect the small set of protocol files it will touch, then run `research-harness init <root>`.
2. Read existing instructions, README files, current-status material, top-level directories, code/config entrypoints, experiment outputs, and paper sources relevant to understanding the project. Use Git or other repository tools when useful; do not enumerate large datasets or generated trees merely to populate harness documents.
3. Reconcile stable, confirmed information into `agent-docs/project.md` and the current focus into `state.md`. Record directory responsibilities and downstream checks at directory granularity.
4. Preserve existing material and user rules. Treat inferred research meaning as candidate and ask only questions that materially change the project definition or constraints.
5. Review legacy files reported by `init`. Extract still-current information before removing obsolete control files with a recoverable deletion mechanism.
6. Report the current authorities, unresolved user decisions, and whether the project is ready.

## Restore Context

1. Locate the nearest project `AGENTS.md` containing the Research Harness managed block.
2. Read `AGENTS.md`, `agent-docs/project.md`, and `state.md`. Read `checkpoint.md` only when it exists; read `decisions.md` only when a current decision is relevant.
3. Follow the directory responsibilities in `project.md` to inspect only sources relevant to the request.
4. Treat conversation summaries, unverified outputs, and old documents as hints rather than current authority.

## Control One Task

Allow only one active mutating task per worktree.

- If an existing checkpoint matches the request, update it in place and continue.
- If a new request is read-only, handle it without replacing the active checkpoint.
- If a new mutating request differs from the active checkpoint, report the conflict before writing. Finish or abandon the old task, or use a separate worktree; never silently overwrite or mix task contracts.

For a critical, long-running, cross-stage, or compact-sensitive task, create or replace `agent-docs/checkpoint.md` directly with: goal, scope, done conditions, validation boundary, expected impacts, verified progress, facts, decisions, risks, necessary references, and one next action. Do not create a checkpoint for a small local task.

## Reconcile Work

1. Inspect actual changes with the tools appropriate to the repository and task. Use Git status/diff when available, but do not rely on harness-maintained file state.
2. Verify the task's done conditions, project constraints, and evidence gates. Identify affected directories and downstream research objects.
3. Replace outdated current information at its authoritative source. Update `project.md` only for durable definitions, constraints, or directory responsibilities; update `state.md` when the current phase, focus, blocker, or next step changes.
4. Create `decisions.md` only when forgetting a decision would likely cause repeated error. Keep the current decision, minimum reason, and invalidation condition.
5. Remove the completed checkpoint with a recoverable deletion mechanism after verifying the work and its impacts. Keep no task archive by default.

## Keep It Light

- Maintain current information, not a timeline.
- Track directory responsibilities, not file inventories.
- Link to canonical research sources instead of copying them.
- Keep detailed domain procedures in optional skills.
- Do not add runtime automation, background scanning, task queues, or extra control documents.

Read [protocol.md](references/protocol.md) before changing durable responsibilities. Read [lifecycle.md](references/lifecycle.md) when migrating an older project or deciding whether to replace, retain, or delete context.
