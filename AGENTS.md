# DoubleT CRM — Agent working agreement

> This file applies to agents working in this repository. Be conservative: preserve working CRM features and existing uncommitted changes.

## Product and stack
- Build **DoubleT CRM**, a standalone CRM application on **Frappe Framework + Vue 3 + Vite + frappe-ui**.
- **Do not install or depend on Frappe CRM or ERPNext**. The source snapshot contains inherited `crm.*`, `CRM Task`, and `FCRM Note` references: treat these as potential migration debt, **not** proof that those applications are installed.
- Core entities: `DoubleT Lead`, `DoubleT Deal`, `DoubleT Contact`, `DoubleT Company`, `DoubleT Task`.
- Environment reported by developer: Windows + WSL + Docker, backend container `crm-frappe-1`, site `doublet.localhost`, web `http://doublet.localhost:8000/doublet-crm`.
- Local WSL bench executable is **not** the runnable Frappe environment. When execution is authorized, use `docker exec` with the Frappe container. Verify paths in the active environment before running commands.

## Context, read on demand
1. `docs/CURRENT_TASK.md`: active objective, acceptance criteria, scope and stop conditions.
2. `docs/ARCHITECTURE.md`: routes, doctypes and important coupling points.
3. `docs/FEATURE_STATUS.md`: verified progress vs unverified assumptions.

Do **not** reread every file on every turn. Read the relevant sections; inspect actual repository code first when the documents and code disagree. The live checkout is authoritative.

## Rules
1. Start by checking `git status --short` and the current branch. **Never** reset, restore, checkout over, clean, force-push, or discard user changes.
2. Work on **one bounded feature** per run. Summarize a short plan; then implement only files required by `CURRENT_TASK.md`.
3. Reuse existing components, resources, routes, APIs and patterns. **Search before creating** a new tab, component, endpoint or DocType.
4. Minimize diff size. Preserve existing public UI workflows, field names, and tests. Avoid unrelated refactors, generated assets, lock files or dependency changes.
5. Prefer `frappe.get_list` / `frappe.get_doc` with appropriate user permissions; do not bypass Frappe permission checks or expose task data between users. Validate dynamic-link doctype against the four allowed DoubleT entities.
6. Never invent `crm.*` API assumptions. Identify each inherited dependency and replace only what the current task needs.
7. Do not execute database writes, fixtures, migrations, data deletion, package installation, or destructive tests without explicit approval. Read-only inspection and builds are permitted when safe.
8. Do not expose API keys, site config secrets, personal data or credentials in chat, commits or logs.
9. Mark tests as PASS only when actually executed and observed. Use `NOT TESTED` when blocked.
10. Do not auto-commit or push unless the user asks. Suggest an isolated commit after approval.

## Workflow / stop rule
- Inspect `CURRENT_TASK.md`, current `git status`, and just the relevant code.
- List impacted files and risks in 3–6 lines.
- Make the smallest compatible code change; verify with focused tests/build (no database mutation unless approved).
- Summarize: modified files, PASS/FAIL/NOT TESTED, compatibility concerns, next step. **Stop**. Do not self-assign the next feature or run unbounded fix loops.

## Repository-specific note
The October 31 source snapshot already has Tasks UI in Lead/Deal/Contact and Company detail, yet some of their shared handlers still reference `CRM Task`. The November 4 Task MVP patch replaces the standalone Tasks page with `DoubleT Task`. **First reconcile this integration rather than rebuilding the tabs.**

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.
