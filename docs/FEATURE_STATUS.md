# DoubleT CRM — Feature status
Updated 2026-11-26. Sales Completion is based on verified main `319ee10`; older Reports/deployment evidence below retains its original baseline and date. Source present, automated tests and observed acceptance are distinct.

## Sales Completion Phase 1 — 2026-11-26

| ID | Status | Evidence and next check |
|---|---|---|
| EXT-05 | IMPLEMENTED; MOCKED PASS; MIGRATION/BROWSER PENDING | Deal Products tab, sellable Catalog multi-select, quantity/remove/save, persistent child schema, duplicate/SKU and quantity validation, permission-aware current reference pricing, and Deal-to-Quotation draft suggestions are implemented. Backend focused suite is included in the 11/11 Phase 1 pass; frontend focused files pass. Run migration, then verify persistence, roles, current Price List values and no Deal Amount/status or historical Quotation changes. |
| EXT-06 | IMPLEMENTED; MOCKED PASS; MIGRATION/BROWSER PENDING | Qualified/Converted Lead backend eligibility, conversion/Deal guidance, exact `source_lead` relationship, one/multiple Deal handling, Quotation create and linked-record permission checks are implemented without automatic conversion or duplicate record creation. Verify live roles, conversion paths and browser messages after migration. |

The Phase 1 implementation is acceptance pending and is not marked Done. No Reports or AI Foundation source was changed in this worktree.

## Current Reports / deployment evidence

| ID | Status | Evidence and next check |
|---|---|---|
| REP-01 | Cần kiểm | PR #31 Admin Dashboard regression recorded 19 Leads, 17 Open Deals, 2 Won Deals, 7 Draft Quotations; Dashboard unchanged in PR #32. Role browser, KPI navigation and forced states pending. |
| REP-02 | Cần kiểm | Live Sales Performance with event-date/Booked Sales/owner metrics; PR #31 tests/API/browser evidence below; PR #32 regression reported. Role/browser and seeded acceptance pending. |
| REP-03 | IMPLEMENTED; AUTOMATED PASS; BROWSER PENDING | Call/Task/Email/Zalo filter added; Agent/Assignee applies only to Calls/Tasks and Email/Zalo attribution limitation is explicit. Activity mocked suite 8/8; role/browser evidence pending. |
| REP-04 | Cần kiểm | Active worktree has six live groups including Smart Insights. Existing five-group regression plus new source tests pass; browser acceptance pending. |
| REP-05 | Cần kiểm — partial | Shared dates/presets/owner and four-group previous-period comparison. Team unsupported; Activity comparison absent, Email/Zalo employee attribution unsupported. Check empty periods/owner changes/roles and agree limits. |
| REP-06 | IMPLEMENTED; AUTOMATED PASS; BROWSER PENDING | Journey exposes all permission-scoped linked Deals/Quotations/Orders, deduplicates IDs and labels direct Deal vs quotation Order links. Role/browser evidence pending. |
| REP-07 | Cần kiểm | Pipeline current-stage creation cohort, Lost Reason by lost_on, expected-close overdue, 30-day modified stale and links present. Verify exact numbers, boundaries and roles. |
| REP-08 | IMPLEMENTED; AUTOMATED PASS; BROWSER PENDING | Preserves all-quotation conversion and adds current Accepted-only denominator/exact linked booked-order numerator, deduplication, zero handling, definition and drill-down. |
| REP-09 | IMPLEMENTED; AUTOMATED PASS; SITE ACTION PENDING | Shared permission-scoped engine, current as-of alerts, centralized 7/3-day thresholds, source routes and explicit duplicate-locked follow-up Task endpoint added. Live role/action/concurrency acceptance pending. |
| REP-10 | IMPLEMENTED; AUTOMATED PASS; BROWSER PENDING | Deterministic 0–100 score with centralized 25-point factors, normalized known-evidence coverage, Unknown states, readable Call/Email recency and labelled `modified` fallback. Not a probability. |
| REP-11 | Cần kiểm — partial | Six report views have source links and responsive local overflow patterns; full Journey links are implemented. Role/empty/error/375px release checks remain pending. |
| REP-12 | IMPLEMENTED; AUTOMATED PASS; SITE/BROWSER PENDING | Backend reruns allowlisted authorized report for BOM CSV and formula neutralization; personal named filters use per-user `__UserSettings`. Excel download and cross-user live acceptance pending. |
| REP-13 | Đề xuất | AI interpretation not implemented; deferred until verified data. |
| REP-14 | IMPLEMENTED; AUTOMATED PASS; BROWSER PENDING | Existing KPI paths preserved; compact Needs Attention uses shared Smart Insights summary with source links and View All. Dashboard role/visual regression pending. |
| EXT-13 | Đã xong (checklist) | Won Deal Value by won_on; keep regression, not paid revenue. |
| EXT-14 | IMPLEMENTED; AUTOMATED PASS; BROWSER PENDING | Lead Source filter plus unique Lead→Deal and Lead-with-Won-Deal counts/rates use Lead cohort denominator and disclose current-outcome limitation. |
| EXT-15 | Đề xuất | Expected close and amount fields exist; no configured probability. Forecast deferred. |
| EXT-32 | Đã xong (checklist) | Lost Reason count/value/share and missing reason by lost_on; keep regression. |
| EXT-33 | Đề xuất | Stage-entry timestamp not present in Deal schema; capture real transitions in later package. |

- SOURCE VERIFIED: main ed76ba1, all five report components mounted, related APIs and tests present. GitHub main unchanged from ed76ba1 at 25 Nov review. No fresh CI/browser/local execution claimed here.
- REPORTED (24 Nov, CHECKLIST PR #32 evidence): Codex 42/42 Reports and 6/6 Activity tests PASS; user reported local functionality OK. These are reported results, not independently rerun in this docs update; detailed release browser acceptance remains pending.
- Historical observed PR #31 evidence follows; do not relabel it as PR #32 testing. Isolated seeded acceptance, interactive Sales Manager/Sales User/restricted-user browser and forced error/retry not tested in that pass.

### Active A–E implementation evidence — 2026-11-25

- Checkout: `feat/reports-completion` at `acf1d7a`, tree-identical to reference merge `ed76ba1` but one commit behind it. Changes are uncommitted; no push/merge.
- PASS: backend `doublet_crm.test_reports` 44/44, `test_activity_reports` 8/8, `test_smart_insights` 9/9. Frontend `node --test frontend/tests/*.test.mjs` passed 13/14 files initially; the only failure was the intentional old five-section count, and the focused updated `reportsHub.test.mjs` then passed. Python compileall and `git diff --check` passed.
- PASS: Yarn production build transformed 2,480 modules in 74.28s and synchronized deploy HTML/assets; existing chunk-size warning only. Root/frontend Graphify AST updates completed; frontend reports 3,281 nodes / 5,853 edges.
- NOT TESTED: persisted seeded data, read-only API role matrix for the new endpoints, interactive Admin/Sales Manager/Sales User/restricted user, desktop/375 px, forced empty/error/retry, Excel-opened CSV, cross-user saved filters and live follow-up duplicate concurrency. No schema/migration exists or was run.

## Historical Pass 1 verification (PR #31 baseline) — 2026-11-24

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


## Historical feature evidence — through 2026-11-17

| Area | Status | Evidence and next check |
|---|---|---|
| Lead → Contact / Company → Deal | SOURCE PRESENT | Conversion logic and tests exist. Verify personal and company flows, record links, role permissions and duplicate conversion handling on the target site. |
| Deal pipeline | SOURCE PRESENT | Stage updates and Won/Lost rules are in source. Verify with demo roles and compare the visible pipeline with Dashboard totals. |
| Task | HISTORICAL MANUAL PASS; REGRESSION PENDING | The user tested standalone CRUD, My Tasks, filters, assignment and links on the earlier MVP. Linked Tasks are wired into the four record types in current source. Recheck CRUD, navigation and permissions across Lead, Deal, Contact and Company. |
| Notes | HISTORICAL LEAD MANUAL PASS; REGRESSION PENDING | Focused backend tests were reported 6/6 on 2026-11-05. Lead detail CRUD and reload were manually verified then. Recheck centralized Notes and the four record views, including record switching and access control. |
| Product, Category and Variant | USD/UI FIX IMPLEMENTED; VISUAL REGRESSION PENDING | Product price is USD with cents. The Categories menu now has an opaque surface, viewport collision/scroll handling and retains primary/secondary selection rules. Desktop/narrow browser interaction is CHƯA TEST. |
| Price List | USD/UI FIX IMPLEMENTED; VISUAL REGRESSION PENDING | The dialog is approximately 900 px on desktop, viewport constrained and responsive; Product remains widest and Price (USD)/remove stay visible. Build passes; New/Edit visual checks, long names and multiple rows are CHƯA TEST. |
| Quotation and Discount | IMPLEMENTED; AUTOMATED PARTIAL PASS; BROWSER PENDING | Customer-scoped Deal filtering, Amount/Percentage UI, en-US USD cents, backend decimal calculations and English USD PDF are implemented. On 2026-11-17 the 19-test module passed 18/19; the remaining historical-total assertion compares Decimal values before reload with floats after reload and is outside the email files changed here. Preview arithmetic and production build pass. Browser and downloaded-PDF comparison remain CHƯA TEST. |
| Lead → send Quotation | IMPLEMENTED; DELIVERY PENDING | `Mark as Sent` now requires confirmation that external delivery already occurred and explicitly performs no send. Full Lead → Deal → Quotation browser regression and delivery through an agreed channel/recipient are CHƯA TEST. |
| Activities and Call Log | SOURCE PRESENT; REGRESSION PENDING | DoubleT timeline API, Call Log listing and ingestion exist. Check Sales permissions, detail and recording playback, and the reported local Deal-linked Call Log changes. |
| Dashboard | IMPLEMENTED; DATA/API PASS; VISUAL CHECK PENDING | On `doublet.localhost`, commit `09bb5163`, Administrator and Sales User authenticated HTTP/API checks pass. Rollback-backed regression passes Lead source reconciliation, Open→Won KPI/stage/list counts, Draft→Sent→Accepted, expired Sent exclusion, Draft filter, labels and linked-record permissions. Build and referenced JS/CSS pass. Restricted backend state returns null rather than zero. Interactive card/row clicks, empty/retry rendering and narrow viewport remain CHƯA TEST. Dashboard test module is 5/7; two unrelated timeline Version assertions fail under the test runner. |
| Zalo OA inbound mock — Task 23 | PASS — POSTMAN | On `doublet.localhost`, the first request returned `200 OK` with `duplicate: false`. Repeating it returned `duplicate: true` with the same message and conversation IDs. |
| Zalo OA Lead linking — Task 25 | PASS — POSTMAN | Replaying `mock-message-01` linked Lead `j26jv05gmb`. Sending `mock-message-02` created a new message and reused the same Lead and conversation. |
| Zalo OA standalone Inbox — Task 24 | OBSERVED — BROWSER | The browser showed two inbound messages and one mock reply in the same conversation. The linked Lead opened with source `Zalo OA`. Persistence after refresh and restricted-role coverage still need recorded results. |
| Zalo OA chat in record details — Task 24B | PASS — USER TESTED | The user confirmed Task 24B works on the current WSL checkout. Shared history/composer, four record tabs, record-scoped permission/membership checks and Inbox deep links remain covered by backend regression. |
| Zalo OA Inbox experience — Task 24C | IMPLEMENTED; API/AUTOMATED PASS; BROWSER PENDING | Global search, OA and Needs reply/Replied filters, latest previews/order, Customer details and IME-safe keyboard sending are implemented. Six backend tests, production build and two-conversation API acceptance pass. Responsive/filter/IME browser checks remain pending. |
| Quotation automatic PDF email | AUTOMATED PASS; CURRENT LIVE RETEST PENDING | The 7/7 focused suite verifies one Communication, one Email Queue lookup, one PDF attachment, one deduplicated after-commit send job per click, and a scheduler-compatible row lock. Diagnosis of `k1v4krnns6` found a roughly four-minute wait for the scheduler `all` tick, not an observed SMTP failure. A real delivery and automatic Queued → Sent/Failed transition through the changed path are NOT TESTED. |
| Quotation inbound receive and link | PASS — SITE DATA/API | On 2026-11-17, `QUO-00005` had one Received Communication (`Re: Quotation QUO-00005`) linked by `reference_doctype/reference_name`; the new read API returned that same Communication. |
| Quotation Emails tab | IMPLEMENTED; API/BUILD PASS; BROWSER PENDING | The current API returned the linked inbound Communication containing `CRM-INBOUND-01` for `QUO-00005`; recipient context resolved its linked Contact; and the 2,461-module production build passed. Full-width layout, Line Total visibility, dialog sizing, polling and visual attachment access are NOT TESTED in a browser. |
| Quotation threaded Reply | AUTOMATED PASS; LIVE/BROWSER PENDING | The focused suite verifies Received-only Reply, `in_reply_to`, immutable original-sender recipient, same-quotation isolation and read-only send denial. The built frontend blocks duplicate submission and retains a failed draft. A real reply and resulting mail-client thread are NOT TESTED. |
| Quotation CRM sender and Reply-To | CODE/AUTOMATED PASS; LIVE HEADER PENDING | The implementation selects Frappe's configured outgoing Email Account for From and its enabled incoming inbox for Reply-To. Existing queue `k1v4krnns6` still records the historical bad `admin@example.com` headers; no new real message was sent, so corrected stored/raw headers remain NOT TESTED. |
| Live Zalo OA integration | PENDING OA ACCESS | Verify live webhook ingestion and outbound delivery after OA access is available. |
| WooCommerce integration | EXTERNAL VERIFICATION PENDING | Track implementation and target-site evidence separately from Zalo OA. |
| Telephony and external integrations | FUTURE OR EXTERNAL VERIFICATION | Call Log ingestion is present. End-to-end telephony and external integrations need separate evidence. This was the historical scope; Contact Center Calls is now merged, current runtime verification remains separate. |
| Deployment | CURRENT WORKTREE BUILD PASS; CLEAN RELEASE PENDING | On 2026-11-17, the current WSL worktree built successfully for 2,461 modules and generated HTML references `index-DItmvQ-r.js` and `index-CdVcU4hb.css`. Vite reported only the existing large-chunk warning. A clean-checkout release remains pending. |


## Completion criteria
Mark a feature done once the target-site behavior, tested roles and test results are recorded, blocking regressions are resolved, and the change is ready for review. Record the build or commit tested so older results remain distinguishable from current results.
## Working cadence
Use [CURRENT_TASK.md](CURRENT_TASK.md) for the active implementation. Record coding-agent results, relevant file changes, retest evidence and remaining work here as they become available.
