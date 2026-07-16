---
name: research-harness
description: Maintain a lightweight project control plane for one research project. Use when initializing or migrating a project; starting, resuming, or completing a critical, long-running, or cross-stage task; applying project constraints; detecting external file changes; promoting evidence into current facts; propagating changes across methods, code, experiments, results, and paper; removing stale context; or auditing control-plane health. Use task-specific skills for domain procedures, but keep their execution subject to project constraints, evidence gates, task boundaries, and completion conditions managed here.
---

# Research Harness

Keep one research project's definitions, constraints, state, evidence relationships, task boundaries, and change impacts current and recoverable. Do not preload one universal domain workflow into every project.

## Restore Context

1. Locate `.research-harness.json` from the current directory upward.
2. Run the bundled `python3 <skill-dir>/scripts/harness.py resume <root>`.
3. Read the active agent entrypoint (`AGENTS.md`, or `CLAUDE.md` which imports it), `agent-docs/index.md`, `project.md`, `state.md`, and an existing `checkpoint.md`.
4. Follow `index.md` only to currently registered sources relevant to the user's task.
5. Treat compact summaries and unregistered files as hints, not authority.

If the project is not initialized and the user asks to initialize it, run `scan` first and then `init`. Scanning never promotes files into project facts.

## Establish Task Control

For a critical, long-running, cross-stage, or compact-sensitive task, keep one replaceable task contract:

```bash
python3 <skill-dir>/scripts/harness.py checkpoint save --path <root> \
  --goal "required outcome" --scope "in scope and out of scope" \
  --done "observable completion conditions" \
  --validation "risk-matched checks and budget" \
  --impact "expected downstream object" \
  --current "verified progress" --next "one next action"
```

Do not create a checkpoint for a small local task that does not need recovery or cross-stage control. A task-specific skill may choose the procedure, but it cannot override the current project constraints, evidence gates, scope, or done conditions.

## Reconcile Changes

After a task, rule change, or manual file import:

1. Run `python3 <skill-dir>/scripts/harness.py sync <root>` to see filesystem candidates.
2. Identify which definitions, constraints, evidence, results, paper claims, or other downstream objects are affected.
3. Verify the task contract and project gates, then replace outdated information at its single authoritative location. Do not append a history log.
4. Use `trash` for obsolete material with no reproduction, audit, compliance, or recovery value.
5. Register only confirmed, current sources in `index.md`.
6. Run `sync --accept` only after impact review and context reconciliation.
7. Run `doctor`, address relevant control or budget warnings, then clear the checkpoint. Clearing refuses pending changes unless explicitly forced for an abandoned task.

Read [lifecycle.md](references/lifecycle.md) when migrating v0.1, changing durable rules, or deciding whether to replace, delete, or keep information outside the active context.

## Survive Compaction

For work that must continue across a session or compact boundary, keep one checkpoint:

```bash
python3 <skill-dir>/scripts/harness.py checkpoint save --path <root> \
  --goal "current outcome" --scope "current task boundary" \
  --done "observable completion conditions" --validation "necessary checks" \
  --current "verified progress" --next "one next action"
```

Each save replaces the prior checkpoint. Record only confirmed facts, user decisions, unresolved risks, necessary references, and the next action. Clear it when recovery is no longer needed:

```bash
python3 <skill-dir>/scripts/harness.py checkpoint clear --path <root>
```

Agent adapters may remind the active coding agent to restore context at session start and to checkpoint before compaction. Hooks do not infer or write research facts.

## Keep It Light

- Maintain one current version, not a timeline.
- Link to canonical sources instead of copying their contents.
- Keep no task archive by default.
- Delete `bootstrap.md` and old task documents after migration review.
- Do not create new harness documents when an existing authority can be updated.
- Keep detailed domain procedures in optional skills; keep project-specific constraints and gates in the control plane.

Read [protocol.md](references/protocol.md) before changing core file responsibilities or budgets.
