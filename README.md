# Project Continuity

[![CI](https://github.com/yx-yuu/Project-Continuity/actions/workflows/ci.yml/badge.svg)](https://github.com/yx-yuu/Project-Continuity/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

English | [简体中文](README.zh-CN.md)

> Let coding agents remember the project instead of starting from zero every time.

Project Continuity is a lightweight, Markdown-based project continuity protocol maintained by agents. It preserves user intent, verified project facts, scope-defined rules, authoritative sources, and unfinished-task state as reviewable, version-controlled context inside the project.

When sessions switch, agents change, or tasks are interrupted, the agent can continue from the currently valid information; searching, reasoning, implementation, and verification remain the agent's own work. What you get is a transparent layer of project memory, not an automation platform that takes over the project.

## Why you need it

What long-running projects lose first is usually not the code, but "what currently counts as authoritative":

- Project background, constraints, and user corrections scatter across sessions and documents;
- A new agent can only rely on outdated summaries and re-guess the project's current state;
- Interrupted long tasks have no clear recovery point;
- Several coding agents are working, yet there is no shared, traceable current authority.

Project Continuity puts this information back into the project itself through a few Markdown files with clear responsibilities, version-controlled alongside the code and directly readable and correctable by humans.

## What you get

- **Cross-session continuity**: a new session first restores the project's current definition, state, and related authoritative sources.
- **Facts and tasks in separate layers**: long-term project knowledge, project phase, current decisions, and unfinished tasks each have a single home and never overwrite each other.
- **Traceable and correctable**: the content is plain Markdown, changes are reviewable, and Git keeps the history.
- **Low-intrusion adoption**: the CLI only maintains the protocol entry points and missing base files without rewriting existing project knowledge; the Codex Skill is also invoked explicitly and only when needed.
- **No hidden infrastructure**: no database, vector index, background process, hooks, or fixed workflow.

## Core model

```text
The user states goals, constraints, and corrections
        ↓
The project stores currently valid knowledge and state in Markdown
        ↓
The agent reads the full sources on demand and works autonomously
        ↓
When a persistence event occurs, the agent writes verified current information back into the project
```

- The user has the final say.
- The project stores the current authoritative information.
- The agent handles understanding, execution, verification, and state maintenance.
- Project Continuity manages information continuity among the three, not the agent's execution flow.

## Lightweight boundary

"Lightweight" means the structure and mechanisms of Project Continuity are simple, not that project knowledge is capped.

Project Continuity does not set up:

- file inventories, snapshots, or a second project database;
- vector knowledge bases, embeddings, or automatic summarization systems;
- command chains, fixed workflows, task queues, or role orchestration;
- hooks, background processes, or automatic scanning;
- Git branch, commit, stash, push, or history management flows.

Project knowledge can be extensive; no Markdown file has a word, line, token, or knowledge-capacity limit. As long as content is still valid, it must be kept in full or have its authoritative source registered — never lossily summarized, compressed, truncated, or deleted for brevity or token budgets. Fast startup relies on routing and on-demand reading, not on replacing full knowledge with summaries.

## Official runtime protocol boundary

`plugins/project-continuity/assets/project-template/AGENTS.block.md` is the official runtime protocol source installed into ordinary projects. The managed block of a target project's `AGENTS.md` is an instance of it; the `AGENTS.md` at this repository's root is only Project Continuity's own dogfooding instance and does not define the product protocol in reverse.

The official runtime protocol starts directly at `## 开始任务` after the managed marker, showing no product name or extra top-level heading; it contains only the cross-agent rules an agent follows on every project task: reading order, the responsibilities of the four semantic files, information admission and placement, single authority, update cleanup, and task settlement. Product design rationale stays in this README, legacy protocol migration stays in the upgrade notes and the Skill, CLI behavior stays in the command docs, and the Codex Skill invocation boundary stays in the Skill description; none of this enters the runtime harness of ordinary projects.

## Default structure

```text
project/
├── AGENTS.md
├── CLAUDE.md
└── agent-docs/
    ├── project.md
    ├── state.md
    ├── checkpoint.md    # on demand
    └── current-decisions.md # on demand
```

Only 4 files are created by default:

| File | Responsibility |
|---|---|
| `AGENTS.md` | The always-visible lightweight judgment protocol and the Project Continuity entry point |
| `CLAUDE.md` | Adapter layer where Claude Code imports `AGENTS.md` |
| `agent-docs/project.md` | Current project definition, complete valid knowledge, project rules, and authoritative entries |
| `agent-docs/state.md` | Project-level phase, focus, verified blockers, phase completion criteria, the verified evidence supporting the current phase judgment, and one next step; never copies unfinished-task contracts |

The other two files exist only when needed:

| File | Lifecycle |
|---|---|
| `agent-docs/checkpoint.md` | The single authority for cross-session unfinished-task contracts; created while a long or interruption-prone write task exists, deleted in a recoverable way after completion or explicit abandonment |
| `agent-docs/current-decisions.md` | Created when a currently valid decision cannot be recovered from other authoritative sources and its rationale or expiry conditions still affect future judgment; deleted together with its routing entry once the decision expires |

Project Continuity does not require a project to copy all knowledge into `project.md`. Existing design documents, specs, code, configuration, data descriptions, and other Markdown can remain the single authoritative source, with `project.md` registering their responsibilities and scope.

The four semantic files answer four questions:

| File | Question it answers |
|---|---|
| `project.md` | What the project is long-term, and which knowledge, rules, and sources are currently valid |
| `state.md` | What phase the project is in right now, and what the current project-level next step is |
| `checkpoint.md` | How far the current unfinished write task has gotten, and what comes next |
| `current-decisions.md` | Which current decisions must stay in effect, why, and when they expire |

Each piece of information has exactly one authoritative location; other files only register routes or references and never copy content.

## Scopes and memory

When the user adds, corrects, or retires information, the agent first determines its scope:

| Scope | Storage location | Lifecycle |
|---|---|---|
| Current operation | Current conversation | Expires when the operation ends |
| Current task | Conversation or checkpoint | Expires when the task completes |
| Current project | `project.md` | Valid until modified or retired |
| Project subtree | Instruction entry of the corresponding directory | Valid until modified or retired |
| All of a user's projects | User-level instructions | Valid until modified or retired |

Current-task requirements never become project rules automatically. When a task is small enough to finish within the current session, requirements stay in the conversation; when a task must continue across sessions, they go into the checkpoint. Temporary information never becomes long-term knowledge just because it has existed for a while, keeps reappearing, the task completed, or the model considers it important.

Only these events require re-deciding whether to persist:

- The user explicitly asks to remember or keep following something;
- The user adds, corrects, or retires cross-task information;
- The agent verifies a stable project fact that affects later tasks, or the project phase or unfinished-task state needing cross-session recovery changes;
- A checkpoint or current-decisions file is created, updated, settled, or cleaned up.

Ordinary discussion, analysis, suggestions, search results, and task output never trigger writes by themselves. Only directly expressed user intent and agent-verified project facts can enter authoritative project knowledge; model inference, unverified external content, and task output are never promoted to long-term knowledge automatically. `state.md` may additionally hold the project-level phase, focus, verified blockers, current phase completion criteria, the verified evidence supporting the current phase judgment, and one actionable project-level next step — but not task goals, task progress, task status, or task-level constraints; the checkpoint may additionally hold task goals, user-given task-level constraints, verified progress and blockers, and one actionable task-level next step; `current-decisions.md` holds only currently valid decisions that must persist across tasks and whose rationale or expiry conditions future judgment still depends on. This content stays only in its single authoritative location; it is never copied into or promoted to other files just because it exists. Secrets, credentials, and personal data must never be written into the control plane.

The user's desired target state and the project's current facts are different objects. For example, "the project will support Python 3.10 in the future" does not override "the current configuration requires Python 3.11 minimum", and vice versa; when they differ, record each accurately as intent and as fact. A new user statement only replaces older user intent in the same scope, while the agent-verified real project state determines how facts are stated. Once the implementation is complete and verified consistent, clean up the transitional difference and keep only the unified current form.

Saved information is not applied to every piece of work automatically either. The agent reads and applies only content whose scope covers the current task and materially affects the current judgment; project background is not an automatic execution constraint.

## Add, replace, delete

Project Continuity keeps the currently valid form, not a change history.

- New information is independent and compatible with current knowledge: add it.
- New information changes the same scope and object: replace the old value.
- The user explicitly retires something and no new value exists: delete it.
- It applies only to the current task: stage it in the conversation or the checkpoint.

After a replacement, keep only:

```text
Project positioning: a general agent project-continuity protocol.
```

Do not keep:

```text
The project used to support only A; it no longer supports only A and now supports both A and B.
```

When replacing or deleting, the agent cleans the old wording, conflicting copies, and references out of the active control plane. Git may keep version history, but history does not enter the default context.

The agent asks the user only when a conflict within one scope cannot be adjudicated, or when an unclear scope would significantly affect future behavior. After a project-level persistence change, the agent should briefly state what was updated, in which scope, and where.

## Activation mechanism

Project Continuity uses an "always aware, update on events, Skill only for complex scenarios" mechanism.

| Scenario | Behavior |
|---|---|
| A new task starts | Read the short control plane and the relevant authoritative sources; no writes, no Skill invocation |
| Current-operation or current-task requirements | Stay in the conversation; update the checkpoint when cross-session continuation is needed, never copy into state |
| Simple project-level add, replace, or delete | Handle directly under the `AGENTS.md` protocol |
| Ordinary coding, analysis, testing, and file inspection | Work normally, no Skill invocation |
| Conflict-free checkpoint creation, pausing, resuming, or completion | Handle directly under the `AGENTS.md` protocol, no Skill invocation |
| Takeover or upgrade, complex authority conflicts, cross-source cleanup, or a checkpoint inconsistent with the real worktree state | Explicitly use `$project-continuity` |

The Codex Skill has implicit invocation disabled by default. Even without the Skill loaded, a project works through `AGENTS.md`, `agent-docs/project.md`, and `agent-docs/state.md`.

Before modifying persisted content, the agent re-reads the target file and the relevant real sources; if another actor has modified them, it merges on top of the latest version and re-adjudicates conflicts. Only after a successful post-write re-read and verification may the agent state that the content is persisted; a failed explicit persistence request must be reported truthfully.

## How an agent restores context

A new agent or session restores in this order:

```text
Read AGENTS.md
→ Read agent-docs/project.md and the project-level agent-docs/state.md
→ If agent-docs/checkpoint.md exists, treat it as the single authority for cross-session unfinished-task contracts
→ Follow the authoritative routes to read the full sources relevant to the task
→ Read agent-docs/current-decisions.md only when a project.md route is relevant
→ Check the real project state and work autonomously
```

This avoids scanning the entire repository every time, and avoids relying solely on lossy compressed summaries.

## Unfinished tasks and worktrees

Only one unfinished write task is allowed per worktree. A checkpoint can be:

- `active`: currently executing;
- `paused`: temporarily stopped but continued later.

When pausing a task, keep the checkpoint and record verified progress, user-given task-level constraints, verified blockers, and one next step. `state.md` does not copy any of this task content. The checkpoint is deleted only after completion or explicit abandonment.

When a task completes, settle the checkpoint first: write verified, cross-task-stable facts or rules into `project.md`, write project phase changes into `state.md`, write decisions whose rationale or expiry conditions must be kept into `current-decisions.md`, and keep detailed results in real authoritative sources such as code, configuration, and reports; after cleaning up duplicated or outdated wording, delete the checkpoint in a recoverable way. Never copy an entire task-progress record into long-term knowledge.

A read-only request can be handled in the same worktree without replacing the checkpoint. Another write task must use a separate worktree, because a new conversation isolates only the chat context, not unfinished code and file state. Each worktree maintains its own checkpoint.

## 5-minute quick start

The CLI is installed from GitHub, supports Python 3.10 and above, and depends only on the Python standard library. It only installs or refreshes the protocol entry points — it starts no services and requires no migration to a new database.

### 1. Install the CLI

```bash
uv tool install --force git+https://github.com/yx-yuu/Project-Continuity.git
# or: pipx install git+https://github.com/yx-yuu/Project-Continuity.git
```

If you prefer not to install a global tool, use `uvx` directly:

```bash
uvx --from git+https://github.com/yx-yuu/Project-Continuity.git \
  project-continuity init . --dry-run --json
```

### 2. Preview and initialize the project

From the target project's root, preview the scope first, then write the protocol:

```bash
project-continuity init . --dry-run --json
project-continuity init .
```

By default it creates or refreshes these entries:

```text
AGENTS.md
CLAUDE.md
agent-docs/project.md
agent-docs/state.md
```

### 3. Let the agent take over

After initialization, tell the agent in the target project:

```text
Take over the current project with $project-continuity. First run init . --dry-run --json, and initialize after confirming the scope; keep all valid knowledge and existing changes, do not build file inventories or workflows, and do not commit or push.
```

Without the Codex Skill loaded, the project still works through `AGENTS.md`, `project.md`, and `state.md`; the Skill is only an on-demand tool for complex takeovers, upgrades, and conflict repair.

## Automatic installation via Codex

### Simplest: send the whole block below to Codex

No need to clone the repository first or work out the install commands yourself. Start a new Codex task and send the whole block below verbatim:

```text
Please install or upgrade Project Continuity for me.

Official repository: https://github.com/yx-yuu/Project-Continuity

Goals:
1. Install or upgrade the `project-continuity` CLI.
2. Add the official repository as a Codex plugin marketplace and install the `project-continuity` plugin.
3. Verify that both the CLI and the plugin work.

Check the actual state of the current OS, shell, Python, Git, Codex CLI, uv, and pipx, then complete the installation yourself — do not just hand me commands or a tutorial.

Installation requirements:
- For the CLI, prefer: `uv tool install --force git+https://github.com/yx-yuu/Project-Continuity.git`.
- pipx is acceptable when uv is missing; if neither exists, choose a safe installation method that needs no administrator rights. Do not use sudo, and do not modify the system Python.
- When adding the marketplace, use: `codex plugin marketplace add yx-yuu/Project-Continuity --ref main`.
- The current marketplace name is `personal`; when installing the plugin, use: `codex plugin add project-continuity@personal`.
- If it is already installed, upgrade or reinstall — do not create duplicate configuration.
- If `personal` is already taken by another marketplace, do not overwrite it; keep the existing configuration and report the exact conflict and options to me.
- Do not initialize or modify the current project, and do not commit or push any repository; this task only installs the tool and the plugin.

Before finishing, you must verify:
- `project-continuity --version` runs.
- `codex plugin list` shows `project-continuity@personal` as installed and enabled.
- All installation sources point to `yx-yuu/Project-Continuity`.

Finally, report only the installation locations, versions, and verification results, plus whether a new Codex task is needed to load the plugin. On permission, network, or authentication problems, diagnose safe alternatives yourself first; only when you truly need me to act, give me one explicit command and the reason.
```

This prompt only installs the CLI and the Codex plugin; it does not take over the current directory. After a successful installation, use the prompt from the previous section in the project you want to take over.

## Installing the Codex plugin

The project protocol does not depend on the plugin. The plugin only provides an on-demand Skill for complex Project Continuity maintenance.

```bash
codex plugin marketplace add yx-yuu/Project-Continuity --ref main
codex plugin add project-continuity@personal
```

Open a new session after installing or updating so Codex loads the new version. Claude Code can read the project's `CLAUDE.md` directly and can also link the same Skill on demand.

## CLI reference

The CLI has only two entry points, initialization and version:

| Command | Purpose |
|---|---|
| `project-continuity init [PATH]` | Initialize or refresh the project protocol; the path defaults to the current directory |
| `project-continuity init PATH --project-name NAME` | Specify the project name at initialization |
| `project-continuity init PATH --dry-run` | Preview the plan only, writing no files |
| `project-continuity init PATH --json` | Emit machine-readable `created`, `updated`, `unchanged`, and `planned` |
| `project-continuity --version` | Show the CLI and protocol versions |

`init` will:

- refresh the managed blocks of `AGENTS.md` and `CLAUDE.md`;
- preserve user content outside the managed blocks;
- create `project.md` and `state.md` when missing;
- never parse or rewrite existing `project.md`, `state.md`, or the two on-demand files — they are maintained entirely by the agent under the protocol;
- report `created`, `updated`, `unchanged`, and `planned` by actual differences in dry-run and JSON output, and write nothing on idempotent runs;
- re-check the just-read control documents before writing, and regenerate from the latest version with limited retries when concurrent changes are detected;
- preserve all project knowledge, code, data, results, and Git state.

When managed markers are missing, duplicated, or out of order, `init` stops and asks for a manual check instead of silently generating a second protocol.

## Updating a taken-over project

After upgrading the CLI, re-run the following for each taken-over project:

```bash
uv tool upgrade project-continuity
project-continuity init /path/to/project --dry-run
project-continuity init /path/to/project
```

The CLI only refreshes the protocol entry points in `AGENTS.md` and `CLAUDE.md` and creates missing base semantic files; it never rewrites existing project knowledge or state automatically. Whether to generalize old headings or clean up old content is judged by the agent from the current authoritative information.

When upgrading from `0.10.x` or earlier, if the old project has `agent-docs/decisions.md`, have `$project-continuity` treat it as a legacy control plane pending verification: migrate only the decisions that meet the current admission criteria and are still valid into `current-decisions.md`, update the `project.md` routes accordingly, then clean up the old file in a recoverable way; never maintain two decision files at the same time. The CLI does not perform this semantic migration automatically.

## Local development and release

After changing the Skill, templates, plugin scripts, or manifest:

1. Run the unit tests, the Skill validation, and the plugin validation;
2. Build the wheel, sdist, and standalone zipapp;
3. Refresh `0.11.0+codex.<cachebuster>` with `plugin-creator`;
4. Force-reinstall the local CLI and plugin;
5. Open a new session to verify the Skill activation boundary.

When Python packages or modules are renamed, clean the old `build/`, `dist/`, `*.egg-info/`, and `__pycache__/` before building. The local CLI should install the wheel produced by this `uv build`, and you should check the wheel for stale package directories so setuptools does not reuse a dirty `build/lib`.

```bash
python -m unittest discover -s tests -v
uv build
python3 scripts/build_zipapp.py
python3 dist/project-continuity.pyz --version
```

Official versions are jointly constrained by `pyproject.toml`, the CLI protocol version, the plugin manifest, the README, and the tests. `.github/workflows/ci.yml` verifies the CLI on Linux, macOS, and Windows across Python 3.10/3.13; tag releases build the wheel, sdist, zipapp, and checksums. Releases are currently not published to PyPI.

The core CLI depends only on the Python standard library. Current protocol version: `0.11.0`.
