# CURRENT TASK — Reports & Analytics completion

Updated 2026-11-24. Status: ACTIVE PASS 1 IMPLEMENTED AND VERIFIED WITH AUTOMATED, READ-ONLY API AND BROWSER EVIDENCE; isolated seeded-site acceptance remains pending.
Planning baseline: `4d835a9` (23 Nov). Verified main/local baseline: `015251f` (PR #31). Fetch and verify before editing. Active branch to create/reuse: `feat/reports-completion`. Keep deploy/main-20261123 and its generated changes intact.

## Weekly objective (23–30 Nov)
Deliver five Reports groups with real permission-scoped system data, filters, charts and links to underlying records; preserve Dashboard's existing KPIs. Checklist: REP-01, REP-02, REP-04, REP-05, REP-06, REP-07, REP-11, EXT-13, EXT-32. REP-03 and REP-08 are related dependencies for five-group coverage, not additional accepted items by default.

## Active pass only — Sales Performance & Pipeline Analytics
Model: GPT-5.6 or GPT-6 if available; High reasoning.

Read root and frontend Graphify first, then AGENTS.md and relevant architecture/status sections. Inspect reports.py, test_reports.py, SalesPerformanceReport.vue, PipelineAnalyticsReport.vue, ReportsFilters.vue, reportFilters.js, Deal/Stage/Order schemas and actual list routes. Check git status, worktrees, and current runtime. Report stale/missing graph and proceed with source. Preserve existing functionality.

### Scope
- REP-02 / EXT-13: retain Booked Sales, Order Count and Average Order Value; add Won/Lost counts, Won Deal Value by won_on, win rate Won/(Won+Lost), average close duration for valid Won records, employee breakdown and drill-down. Won/Lost use their own event dates; explicitly label all denominators and units. Do not equate booked orders or Deal value with paid revenue.
- REP-07 / EXT-32: retain current-stage analytics by creation; add Lost Reason counts, value and percentages by lost_on, including missing reasons; flag open deals overdue against expected_close_date, and stale deals only with an explicit supported definition. No invented stage history.
- REP-05: reuse shared filters; date ranges, month/quarter presets, employee, team only if supported by real schema, prior-period comparison with clear definition, reset and synchronized KPI/chart/table. Handle empty and invalid ranges. No page reload needed. Scope filters by each metric's date field.
- REP-11 (partial): accessible charts, tooltips, exact drill-down, loading/empty/error/retry and responsive behavior. No new dependency without necessity. English labels, USD cents, respect actual currency schema.
- Backend authorization for records and fields; no permission bypass, mock metrics, core modifications or unrelated changes to Order/Quotation/Contact Center. Dashboard remains unchanged except an explicitly justified regression fix.

### Acceptance (run in same pass)
1. Seeded cases with creation in prior month and won_on/lost_on in selected month yield exact counts/amounts, win rate and duration; existing booked-order results stay correct.
2. Date, employee and comparison filters update all related output, handle zero denominators and invalid ranges; team support is implemented or explicitly documented as blocked.
3. Lost Reason shares reconcile to total (rounding explained), overdue Open deals are correct, and drill-down results match aggregate scope.
4. Admin/Manager/Sales User and restricted users see only authorized records and fields; direct APIs and drill-down cannot leak restricted data.
5. Focused backend/frontend tests, Yarn build and applicable migration checks; browser desktop/375px and Dashboard regression recorded separately. Use isolated authorized test data/site; if unavailable, report NOT TESTED rather than PASS.

## Later passes — do not self-assign
2. Customer Journey and Quotation & Order: trace saved Lead→Deal→Quotation→Order links, distinct entity counts, explicit cohort/denominator, no duplicate inflation; quote/order status, value and conversion, real drill-down. REP-06/04, related REP-08.
3. Activity & Contact Center Reports: permission-scoped Calls, Tasks, Communication and mock/live distinction; coordinate with Thư; reporting only, no changes to transport/Contact Center business workflows. REP-04, related REP-03.
4. Regression and acceptance: all five reports, filters, drill-down, permissions, responsive/empty/error, old Dashboard KPI and links. REP-01/04/05/11. No REP-14 redesign, export or AI insights in this scope.

## Handoff and stop
Implement and test active pass only. Record files changed, metric formulas, commit/worktree, site/role, commands/results, browser evidence and blockers. Update Graphify and relevant docs. Keep same branch across passes. Do not commit/push/merge unless asked; reuse draft PR when review is requested. Do not mark checklist Done without actual acceptance evidence.

## Active Pass 1 verification — 2026-11-24

- Checkout: `feat/reports-completion` at uncommitted `015251f` baseline, verified `0/0` against fetched `origin/main`. The pre-existing documentation, `frontend/components.d.ts`, and source-map changes were preserved. No commit, push or merge was performed.
- PASS — Sales formulas and date scopes: Booked Sales/Order Count/AOV remain Confirmed/Completed Orders by `order_date`; Won/Lost use `won_on`/`lost_on`; Win Rate is `Won / (Won + Lost)`; Won Deal Value uses Deal Amount; close duration is valid `won_on - creation` in days with an explicit denominator. Unit cases include creation in a prior month with events in the selected month, invalid duration exclusion and zero denominators.
- PASS — Pipeline scopes: current-stage metrics remain by Deal `creation`; Lost Reason is by `lost_on`, includes `No reason provided`, count/value shares and two-decimal rounding disclosure; overdue Open Deals use `expected_close_date` in range before the as-of date; stale is explicitly Open and not modified for 30 days as of End Date. Aggregate rows and embedded record drill-down use the same permission-scoped result sets.
- PASS — Shared filters: custom range, 7/30 days, current/previous month, current/previous quarter, Deal Owner, reset, and optional immediately preceding equal-length comparison. All related output reloads without page navigation. Invalid/missing ranges disable Apply and backend validation remains authoritative. Team is explicitly unsupported because `DoubleT Deal` has no team field.
- PASS — focused backend tests: `bench --site doublet.localhost run-tests --app doublet_crm --module doublet_crm.test_reports` → 11/11. Frontend focused tests → 9/9. `python3 -m compileall`, `git diff --check`, and Yarn production build passed; build transformed 2,474 modules in 50.91 seconds with only the existing chunk-size warning.
- PASS — read-only runtime API on `doublet.localhost`: Administrator, `salesmanager@gmail.com` (Sales Manager), and `salesuser@gmail.com` (Sales User) could call both endpoints; Guest received `PermissionError` from both. Administrator data reconciled to one $480 booked Order for 1–24 Nov; Pipeline returned 2 created Deals/$121, one overdue Open Deal/$5, six stale Open Deals/$10,103,257, and equal-length prior-period comparison. No permission bypass or raw SQL is used.
- PASS — browser Administrator desktop: Sales and Pipeline loaded live KPI/chart/table data, exact record links, Team limitation, comparison period and retry/empty-capable UI. Enabling comparison then Apply updated the report in-place to the 30-day prior period (26 Sep–25 Oct). Dashboard regression remained 19 Total Leads, 17 Open Deals, 2 Won Deals and 7 Draft Quotations.
- PASS WITH EXISTING SHELL CONTROL — 375 px: after using the app's existing Collapse control, both reports fit the 375 px document with no document/body horizontal overflow; wide charts/tables scroll locally. With the global sidebar left expanded, the pre-existing shell leaves only a narrow report viewport; no shell or Dashboard behavior was changed in this pass.
- PASS — Graphify was initially missing in this checkout. `graphify update .` created/refreshed root (9,680 nodes/20,860 edges) and frontend (3,141 nodes/5,602 edges) graphs; focused queries locate both report components, shared filters and backend comparison helpers.
- NOT APPLICABLE — migration: no DocType, patch, fixture or schema file changed.
- NOT TESTED — database-seeded exact acceptance on a separate isolated site, because no authorized isolated test site/data-write permission was available. Pure/helper tests cover the specified seeded arithmetic, but this is not presented as persisted-site evidence.
- NOT TESTED — interactive browser sessions for Sales Manager, Sales User and a restricted non-Guest user; their read-only direct API behavior is recorded separately above. Empty/error/retry source and automated coverage exist, but forced browser network/error-state interaction was not performed.

## Baseline verification
PASS: 0/0 commit divergence and Yarn build (72.02s, chunk warning only). NOT TESTED: migration confirmation, focused current Reports tests and interactive browser acceptance. Earlier Quotation/Zalo/Task verification is historical; see FEATURE_STATUS.md and ARCHITECTURE.md.
