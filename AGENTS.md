# DoubleT CRM — Agent working agreement

> This file applies to agents working in this repository. Be conservative: preserve working CRM features and existing uncommitted changes.

## Product and stack
- Build **DoubleT CRM**, a standalone CRM application on **Frappe Framework + Vue 3 + Vite + frappe-ui**.
- **Do not install or depend on Frappe CRM or ERPNext**. The source snapshot contains inherited `crm.*`, `CRM Task`, and `FCRM Note` references: treat these as potential migration debt, **not** proof that those applications are installed.
- Core entities: `DoubleT Lead`, `DoubleT Deal`, `DoubleT Contact`, `DoubleT Company`, `DoubleT Task`.
- Environment reported by developer: Windows + WSL + Docker, backend container `crm-frappe-1`, site `doublet.localhost`, web `http://doublet.localhost:8000/doublet-crm`.
- Local WSL bench executable is **not** the runnable Frappe environment. When execution is authorized, use `docker exec` with the Frappe container. Verify paths in the active environment before running commands.

## Context, read on demand
- Start with Git status and Graphify (root and frontend when relevant), then inspect the actual source. If the graph is missing or stale, report that and continue.
- Read only the active task and relevant sections; do not load historical evidence wholesale.
1. `docs/CURRENT_TASK.md`: active objective, acceptance criteria, scope and stop conditions.
2. `docs/ARCHITECTURE.md`: routes, doctypes and important coupling points.
3. `docs/FEATURE_STATUS.md`: verified progress vs unverified assumptions.

Do **not** reread every file on every turn. Read the relevant sections; inspect actual repository code first when the documents and code disagree. The live checkout is authoritative.

## Rules
1. Start by checking `git status --short` and the current branch. **Never** reset, restore, checkout over, clean, force-push, or discard user changes.
2. Work on **one bounded work package** per run (related checklist items may share a pass only when CURRENT_TASK explicitly groups them). Summarize a short plan; then implement only files required by `CURRENT_TASK.md`.
3. Reuse existing components, resources, routes, APIs and patterns. **Search before creating** a new tab, component, endpoint or DocType.
4. Minimize diff size. Preserve existing public UI workflows, field names, and tests. Avoid unrelated refactors, generated assets, lock files or dependency changes.
5. Prefer `frappe.get_list` / `frappe.get_doc` with appropriate user permissions; do not bypass Frappe permission checks or expose task data between users. Validate dynamic-link doctype against the four allowed DoubleT entities.
6. Never invent `crm.*` API assumptions. Identify each inherited dependency and replace only what the current task needs.
7. Do not execute database writes, fixtures, migrations, data deletion, package installation, or destructive tests without explicit approval. Read-only inspection and builds are permitted when safe.
8. Do not expose API keys, site config secrets, personal data or credentials in chat, commits or logs.
9. Mark tests as PASS only when actually executed and observed. Use `NOT TESTED` when blocked.
10. Do not auto-commit or push unless the user asks. Suggest an isolated commit after approval.

## Branch and review workflow
- Use a feature branch/worktree based on verified origin/main; never edit the deploy branch for feature work. Preserve any existing generated local changes and stashes; verify actual status rather than assuming the historical count.
- Keep successive fixes within the same active Reports work package on the same branch; do not reuse a merged PR as a draft; batch commits and push only when requested for review; reuse a draft PR where applicable.
- Implement and run focused tests in the same pass. Use an isolated test site for database-mutating tests, with explicit approval. Do not mutate the running demo site without approval.
- Record commit, site, roles, commands, PASS/FAIL/NOT TESTED and browser evidence separately. Never infer acceptance from build or test-file existence.
- Read the actual diff before review. Use current repo package manager/lockfile (Yarn was used successfully on 24 Nov). Keep deploy HTML/assets matched; do not commit incidental build outputs unless release policy requires them.

## Workflow / stop rule
- Inspect `CURRENT_TASK.md`, current `git status`, and just the relevant code.
- List impacted files and risks in 3–6 lines.
- Make the smallest compatible code change; verify with focused tests/build (no database mutation unless approved).
- Summarize: modified files, PASS/FAIL/NOT TESTED, compatibility concerns, next step. **Stop**. Do not self-assign the next feature or run unbounded fix loops.

## Repository-specific note
The October 31 source snapshot already has Tasks UI in Lead/Deal/Contact and Company detail, yet some of their shared handlers still reference `CRM Task`. The November 4 Task MVP patch replaces the standalone Tasks page with `DoubleT Task`. **First reconcile this integration rather than rebuilding the tabs.**
## Contact Center and record chat

- Contact Center uses `DoubleT Conversation` and `DoubleT Message` as the shared conversation history. The standalone Inbox and record-level Zalo OA tabs use the same history and reply logic.
- Reuse the existing detail tabs, route names and frontend components. Record chat applies to `DoubleT Lead`, `DoubleT Deal`, `DoubleT Contact` and `DoubleT Company`.
- Resolve relationships on the backend using stored CRM links. For record-scoped history and replies, check access to the record and verify that the selected conversation belongs to it. Apply the existing conversation and message permissions.
- Keep the mock reply label visible in the UI. Record mock and live Zalo OA test results as distinct acceptance items.
- Use the user's existing WSL checkout and Docker site for verification. Preserve local changes during source edits and builds.
## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- Use existing Graphify queries before exploring source.
Do not run graphify update or rebuild graphs.
The user handles Graphify updates manually.
If the graph is stale, inspect relevant source directly.
- In focused review-repair passes, stop after source/tests/docs; leave every Graphify rebuild and post-update query to the user, even when code changed.
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.
## Frontend consistency

- Use the Frappe CRM reference screenshots as a visual guide. Before changing a screen, follow the Graphify rules below and inspect the closest existing DoubleT CRM screen of the same type. Implement the change with the repository's existing Vue and frappe-ui stack.
- Reuse existing layout, theme tokens and components for page headers, buttons, forms, tables, tabs and loading, empty and error states. Search for an existing component or variant before adding one.
- For list views, place the breadcrumb and primary action in the page header, with search and filters above the table. Follow the reference screen's conventions for row actions, status indicators and pagination.
- For record detail views, keep the record name and primary action in the header and place tabs below it. Use a side summary when users need record information alongside the active tab. On narrow screens, let that summary collapse or stack below the main content.
- For forms and dialogs, follow existing conventions for labels, required fields, validation and save actions. Give wide content such as quotation items and email composition enough room. Keep the primary action visible and confine horizontal scrolling to the table when needed.
- Match the existing UI language and naming conventions. Keep visual changes within the current task's scope and preserve existing navigation, permissions and workflows.
- Verify changed screens at desktop and narrow widths when authorized and available; in quota-saving mode, provide a short manual browser checklist instead of repeated agent browser runs. Record unperformed checks as NOT TESTED. Check the primary action, filters or tabs as applicable, and any fields or columns affected by layout changes. In the handoff, name the reference screen and reused components, and record checks that could not be run as `NOT TESTED`.
## Reports and Dashboard
- Reports and Dashboard are separate views. Preserve existing Dashboard KPI contract and navigation; an explicitly scoped REP-14 pass may add a shared Smart Insights summary without redesigning existing KPIs.
- Use permission-scoped aggregation, including field-level restrictions and linked-record drill-down. Distinguish Deal creation, won_on, lost_on and order_date; never equate Won Deal Value or Booked Sales with paid revenue.
- Reuse ReportsFilters.vue and existing chart/UI patterns. No placeholder or mock metric may count as accepted.

- Quota-saving mode: use focused Graphify queries and source reads, avoid repeated repo-wide scans, unnecessary subagents and long browser automation. Run relevant automated checks once per coherent change; rerun failing focused checks after fixes. Human browser acceptance is separate. Never claim a test was run if it was not.
- Keep rule-based alerts, health scores, forecasts and AI explanations distinct. Never invent stage history, activity timestamps or probabilities. Use explicit business definitions, field/record permissions and source links; unknown or unauthorized data is not zero.
- Export only the current user’s authorized filtered report; prevent spreadsheet formula injection. Keep personal saved filters isolated by authenticated user and report.
