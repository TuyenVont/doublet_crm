# CURRENT TASK — Reports completion & Smart Insights

Updated 2026-11-25. Status: IMPLEMENTED IN ACTIVE WORKTREE; focused automated checks pass, but role/browser/site-data acceptance remains incomplete and no checklist item is marked Done.
Planning baseline: `4d835a9` (23 Nov). Verified GitHub main: `ed76ba1` (PR #32). Verify local checkout, remote and worktrees before editing. Use a new `feat/reports-smart-insights` branch based on verified main, or reuse an existing unmerged branch for this exact scope. Preserve deploy branch, local changes and stashes.

## Weekly objective (23–30 Nov)
Complete reports for quotations, orders and customer-care activity; add actionable alerts, opportunity assessment, forecasting and export. Checklist: REP-03, REP-08, REP-09, REP-10, REP-12, REP-13, REP-14, EXT-14, EXT-15, EXT-33. Previous REP-06/11 drill-down gaps are related fixes; REP-05 filter limits remain explicitly documented. Mark Done only with recorded acceptance evidence.

## Active work package — implement and focused-test in one pass
Model: GPT-6.2 if available in Codex; otherwise strongest available coding model. Reasoning: High. Quota-saving mode.

Read AGENTS.md and root/frontend Graphify before source exploration (query first when graph.json exists). Verify current git status, main and runtime; inspect relevant reports.py helpers, report components, filters, dashboard, task APIs, permissions and schemas. If graph missing/stale, report and continue. Do not rebuild existing reports. Brief plan (3–6 lines); work through A–E in order. If a blocker prevents a group, keep earlier completed code stable and report the gap. No unbounded retry loops.

### A. Existing reports — REP-03, REP-08, EXT-14 (+ related REP-06/11)
- Activity: add channel filter Call/Task/Email/Zalo with clear applicability. Preserve permission-scoped existing data and mock/live labels. Employee filter means Agent/Assignee for Calls/Tasks; disclose Email/Zalo attribution limitation rather than inventing ownership. Reporting only; no Contact Center workflow/transport changes. Verify existing routes and permissions.
- Quotation & Order: preserve current all-quotation conversion and add Accepted Quotation → Booked Order conversion. Denominator = unique currently Accepted quotations dated in selected range; numerator = those with at least one exact linked Confirmed/Completed Order regardless of Order date. Deduplicate multiple Orders; exclude standalone Orders; zero denominator handled explicitly; disclose this is current status, not a historical acceptance event. Expose matching drill-down and definition.
- Journey: extend existing Lead creation cohort with source filter and unique Lead → Deal / Lead with Won Deal counts and rates (explicit denominators and current-outcome limitation). Use saved links, not contact-name guesses. Add permission-scoped drill-down for all linked Deals/Quotations/Orders; distinguish direct Deal Orders vs quotation-linked Orders, deduplicate entity IDs and avoid leaking hidden records. Reuse current routes; preserve existing metrics.
- Retain date/owner filters and prior-period comparison where supported. Do not fabricate Team or unsupported Activity comparisons; document remaining REP-05 limits.

### B. Smart Insights — REP-09
- Shared backend rule engine with current, explicit as-of date. Open Deal stale by `modified`, Open Deal past expected close, Sent Quotation approaching/after `valid_until`, unfinished Task past `due_date` (exclude Done/Canceled). Proposed new alert defaults: 7 days unchanged and 3 days until expiry; centralize and label thresholds, do not silently change existing Pipeline 30-day metric.
- Return only authorized alerts and readable source fields: type, severity, reason, relevant dates/days, owner when available, stable source ID and route. No hidden related-record inference. Missing date/permission is unknown, not a false zero. Use the existing permission-aware query patterns; keep queries bounded/batched.
- Add Smart Insights report section; support relevant filters and source links. Define current-alert vs period-report semantics explicitly. Follow-up Task creation is an authenticated explicit action, not an automatic job: reuse existing Task API/controller; validate source and supported reference (Lead/Deal/Contact/Company only), record read and Task create permissions, allowed assignee and active duplicate prevention including concurrent submissions. Quotation may reference readable linked Deal if valid; otherwise link only. No mutation during read.

### C. Deal Health Score — REP-10
- Deterministic score 0–100, centralized documented factors/weights and category thresholds; no AI. Use trustworthy linked interaction timestamps, overdue Tasks, expected close, and linked Quotation status/expiry. If only modified time exists, label it as update recency, not customer interaction. Missing or restricted input must not expose hidden data or be treated as positive/negative evidence; show Unknown or transparent coverage. Avoid treating scores as Won probability.
- Show score, Healthy/Needs Attention/At Risk (or Unknown), per-factor explanation and authorized source links in existing Pipeline/Smart Insights UI. Preserve existing metrics.

### D. Dashboard — REP-14
- Preserve current KPI, charts, links and layout contract. Add compact Needs Attention summary, totals, prioritised alerts and authorized source/action links. Use the same Smart Insights engine as Reports; View All navigates to Smart Insights. No redesign of unrelated pages. Loading/empty/error/retry and narrow layout.

### E. Export and saved filters — REP-12
- Shared export for live Reports: CSV UTF-8 BOM (Excel-compatible); XLSX only if existing safe dependency supports it without new dependency churn. Export complete authorized filtered result, not page slice; preserve displayed column semantics, units, report name, applied period and generation time. Neutralize formula-injection strings. Backend validates allowlisted report/filter parameters and read/export/field permissions; never trust frontend-supplied records or user IDs. No raw unfiltered data export.
- Named personal saved filters per authenticated user/report; save/apply/delete, validate filters on restore. Reuse existing preference mechanism if suitable; otherwise minimal justified schema with migration documented. Do not store customer records in preferences.

## Acceptance (same pass; no fabricated evidence)
1. Reports: focused tests for Accepted-only denominator, duplicate/standalone orders, source/Won cohort, multi-record links, date/owner/channel filters and missing/unauthorized sources. Existing KPI formulas unchanged.
2. Alerts and score: test exact date boundaries, closed records, unknown data, rule arithmetic and source permission restrictions; unauthorized callers denied; follow-up action authorized and duplicate-safe.
3. Dashboard: old KPI contracts still pass regression; summary matches shared alert engine; links/actions and loading/empty/error/retry available.
4. Export/preferences: data reconciles to authorized applied filters, unicode/USD and formula injection safe, no cross-user filter access or export permission escalation.
5. Run relevant existing and new backend/frontend tests, `git diff --check`, production Yarn build; document migration requirements. Do not execute DB-mutating tests, migrations, fixtures, installs or writes on any site without explicit authorization. Use pure/mocked focused tests and safe read-only checks where possible. Record blocked commands as NOT TESTED. Provide a short manual browser checklist (Admin, Sales Manager, Sales User, restricted user, desktop/375px, empty/error/retry); no long agent browser acceptance runs.

## Later package — do not self-assign
- EXT-15: forecast open Deal value by expected_close_date; add weighted forecast only with explicit configured probabilities and a defined denominator; no arbitrary stage probability or Health Score proxy.
- EXT-33: capture actual stage entry and actor on transition; legacy stage-entry unknown unless reliable history can be proven. Schema/migration and permission tests required.
- REP-13: AI only explains verified KPI snapshots and source/period/limitations, with human review. No fabricated calculations, external transfer of customer data or unapproved provider calls. If no AI configured, disclose blocker; deterministic text is not AI acceptance.

## Active worktree evidence — 2026-11-25 (not release acceptance)

- Branch/commit: `feat/reports-completion` at `acf1d7a`; it is one merge commit behind reference `ed76ba1`, with no tree difference between those commits. All A–E changes remain uncommitted on this one branch.
- Implemented: REP-03/06/08/09/10/11/12/14 and EXT-14 source changes described above. REP-13, EXT-15 and EXT-33 were not implemented. Existing Sales/Pipeline KPI formulas and the Pipeline 30-day stale definition were not changed.
- PASS: Reports backend 44/44; Activity backend 8/8; Smart Insights/export safety backend 9/9; frontend suite 14/14 files after the intentional six-section regression update; Python compileall; `git diff --check`; production Yarn build (2,480 modules, 74.28s, existing large-chunk warning only).
- PASS: root/frontend Graphify updated AST-only; frontend rebuilt to 3,281 nodes / 5,853 edges. Root follow-up found no tracked code changes after its completed rebuild.
- NOT TESTED: persisted seeded data reconciliation, Admin/Sales Manager/Sales User/restricted-user interactive browser acceptance, 375 px visual acceptance, forced empty/error/retry, export download opened in Excel, cross-user saved-filter behavior on site, Task creation/duplicate concurrency against live Redis/site permissions. No migration is required because no DocType/patch/fixture/schema changed.
- No migration, fixture, package install, site-data write, browser automation, commit, push or merge was performed.

## Handoff and stop
Update only relevant docs. Do not run Graphify update or rebuild commands; the user handles Graphify updates manually.

Focused review repair (2026-11-25): Graphify rebuild, update and post-update queries remain explicitly assigned to the user. This repair pass must not replace the prior graph artifacts or claim they reflect the repaired source.

- Repair evidence: focused backend mocked/read-only suite 66/66 PASS; focused frontend files 5/5 PASS; Python compile and `git diff --check` PASS.
- Not run in this repair pass: production build, browser automation, migration, site-data mutation and Graphify update/rebuild/post-update query.

Record exact branch/commit, changed files, formulas, actual commands/results, pending browser checks and blockers by checklist code.

Do not commit/push/merge unless asked. Keep this package's fixes on the same branch. Reuse the draft PR when applicable. Preserve old evidence in FEATURE_STATUS; don't mark checklist Done based solely on code/build.
