DoubleT CRM — Feature status
Updated 2026-11-24. Current verified Git baseline: main/local `015251f`. Historical evidence below retains its original dates and scope; it does not establish current acceptance.

## Current Reports / deployment evidence

| ID | Status | Evidence and next check |
|---|---|---|
| REP-01 | PASS — ADMIN REGRESSION; ROLE BROWSER PENDING | Administrator browser still shows 19 Leads, 17 Open Deals, 2 Won Deals and 7 Draft Quotations. Dashboard source was unchanged. Sales Manager/Sales User browser and forced empty/error states remain pending. |
| REP-02 | IMPLEMENTED; AUTOMATED/API/BROWSER PASS; ISOLATED SEED PENDING | Retains Booked Sales/Order Count/AOV and adds Won/Lost, Won Deal Value, Win Rate, valid close duration, owner breakdown and exact record drill-down with explicit date fields and denominators. |
| REP-04 | PARTIAL | Five routes, two live reports, three placeholders on main. |
| REP-05 | IMPLEMENTED; PASS | Custom/7/30/month/quarter ranges, previous month/quarter, Deal Owner, reset and immediately preceding equal-length comparison update the whole report without navigation. Team is documented unsupported by the actual Deal schema. |
| REP-06 | NOT IMPLEMENTED | Customer Journey placeholder; implement linked funnel with deduplication. |
| REP-07 | IMPLEMENTED; AUTOMATED/API/BROWSER PASS; ISOLATED SEED PENDING | Keeps current stage by Creation; adds Lost Reason by Lost On, missing reason, count/value shares, overdue by Expected Close Date, and explicit 30-day modified stale definition with exact record rows. |
| REP-11 | PARTIAL PASS — ACTIVE PASS 1 | Sales/Pipeline provide accessible labels, hover titles, record links, loading/empty/error/retry source and local table scrolling. Desktop and collapsed-shell 375 px pass; later report groups and role-browser/error injection remain pending. |
| EXT-13 | IMPLEMENTED; PASS | Won Deal Value is summed from permission-scoped Deal Amount by `won_on`, explicitly not paid revenue. |
| EXT-32 | IMPLEMENTED; PASS | Lost Reason counts/value/count-share/value-share use `lost_on`, include missing reasons and disclose two-decimal rounding. |

- PASS (observed 2026-11-24): branch baseline and origin/main parity 0/0; backend Reports 11/11; frontend Reports 9/9; production build 2,474 modules in 50.91s with chunk warning only; read-only APIs pass Administrator/Sales Manager/Sales User and deny Guest; desktop plus collapsed-shell 375 px browser checks pass.
- SOURCE PRESENT: Product multi-category/variants `c025247`, Contact Center Calls merge `218cdef`, Reports PRs #29–31. No new feature acceptance inferred.
- NOT TESTED: persisted seeded acceptance on an authorized isolated site; Sales Manager/Sales User/restricted non-Guest interactive browser sessions; forced browser empty/error/retry. Migration is not applicable because this pass changes no schema/patch/fixture.

## Historical feature evidence — through 2026-11-17

Area	Status	Evidence and next check
Lead → Contact / Company → Deal	SOURCE PRESENT	Conversion logic and tests exist. Verify personal and company flows, record links, role permissions and duplicate conversion handling on the target site.
Deal pipeline	SOURCE PRESENT	Stage updates and Won/Lost rules are in source. Verify with demo roles and compare the visible pipeline with Dashboard totals.
Task	HISTORICAL MANUAL PASS; REGRESSION PENDING	The user tested standalone CRUD, My Tasks, filters, assignment and links on the earlier MVP. Linked Tasks are wired into the four record types in current source. Recheck CRUD, navigation and permissions across Lead, Deal, Contact and Company.
Notes	HISTORICAL LEAD MANUAL PASS; REGRESSION PENDING	Focused backend tests were reported 6/6 on 2026-11-05. Lead detail CRUD and reload were manually verified then. Recheck centralized Notes and the four record views, including record switching and access control.
Product, Category and Variant	USD/UI FIX IMPLEMENTED; VISUAL REGRESSION PENDING	Product price is USD with cents. The Categories menu now has an opaque surface, viewport collision/scroll handling and retains primary/secondary selection rules. Desktop/narrow browser interaction is CHƯA TEST.
Price List	USD/UI FIX IMPLEMENTED; VISUAL REGRESSION PENDING	The dialog is approximately 900 px on desktop, viewport constrained and responsive; Product remains widest and Price (USD)/remove stay visible. Build passes; New/Edit visual checks, long names and multiple rows are CHƯA TEST.
Quotation and Discount	IMPLEMENTED; AUTOMATED PARTIAL PASS; BROWSER PENDING	Customer-scoped Deal filtering, Amount/Percentage UI, en-US USD cents, backend decimal calculations and English USD PDF are implemented. On 2026-11-17 the 19-test module passed 18/19; the remaining historical-total assertion compares Decimal values before reload with floats after reload and is outside the email files changed here. Preview arithmetic and production build pass. Browser and downloaded-PDF comparison remain CHƯA TEST.
Lead → send Quotation	IMPLEMENTED; DELIVERY PENDING	`Mark as Sent` now requires confirmation that external delivery already occurred and explicitly performs no send. Full Lead → Deal → Quotation browser regression and delivery through an agreed channel/recipient are CHƯA TEST.
Activities and Call Log	SOURCE PRESENT; REGRESSION PENDING	DoubleT timeline API, Call Log listing and ingestion exist. Check Sales permissions, detail and recording playback, and the reported local Deal-linked Call Log changes.
Dashboard	IMPLEMENTED; DATA/API PASS; VISUAL CHECK PENDING	On `doublet.localhost`, commit `09bb5163`, Administrator and Sales User authenticated HTTP/API checks pass. Rollback-backed regression passes Lead source reconciliation, Open→Won KPI/stage/list counts, Draft→Sent→Accepted, expired Sent exclusion, Draft filter, labels and linked-record permissions. Build and referenced JS/CSS pass. Restricted backend state returns null rather than zero. Interactive card/row clicks, empty/retry rendering and narrow viewport remain CHƯA TEST. Dashboard test module is 5/7; two unrelated timeline Version assertions fail under the test runner.
| Area | Status | Evidence and next check |
|---|---|---|
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
| WooCommerce integration | EXTERNAL VERIFICATION PENDING | Track implementation and target-site evidence separately from Zalo OA. |FUTURE OR EXTERNAL VERIFICATION	Call Log ingestion is present. End-to-end telephony and external integrations need separate evidence. This was the historical scope; Contact Center Calls is now merged, current runtime verification remains separate.
Deployment	CURRENT WORKTREE BUILD PASS; CLEAN RELEASE PENDING	On 2026-11-17, the current WSL worktree built successfully for 2,461 modules and generated HTML references `index-DItmvQ-r.js` and `index-CdVcU4hb.css`. Vite reported only the existing large-chunk warning. A clean-checkout release remains pending.


Completion criteria
Mark a feature done once the target-site behavior, tested roles and test results are recorded, blocking regressions are resolved, and the change is ready for review. Record the build or commit tested so older results remain distinguishable from current results.
Working cadence
Use [CURRENT_TASK.md](CURRENT_TASK.md) for the active implementation. Record Anti's results, relevant file changes, retest evidence and remaining work here as they become available.
