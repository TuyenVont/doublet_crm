CURRENT TASK — Lead-to-Quotation workflow and UI fixes
Status — Ready for implementation. Dashboard implementation and target-site API/data regression were reported complete. Remaining Dashboard checks are recorded below.

Working checkout — The reported WSL checkout was fix/regression-task-notes-product at base commit 09bb5163, mounted into crm-frappe-1 for site doublet.localhost. Verify the current branch, commit, working tree and running build before editing. Preserve in-progress changes to Dashboard and Call Log.
Objective
Make Quotation creation predictable from either the Deal page or the Quotations list. Use English labels and USD with cents throughout the pricing flow. Make the Price List and Product dialogs easy to use, then verify the complete path from Lead to sending and recording a Quotation.
Implementation scope
1. Read Graphify first. Open the reports in graphify-out/ and frontend/graphify-out/ where available. Trace the Lead conversion, Deal customer links, Quotation picker and pricing/PDF paths, then verify the relevant fields, routes, permissions and changes against the current source. Continue with source if the graph is missing or stale. Read [ARCHITECTURE.md](ARCHITECTURE.md) and [FEATURE_STATUS.md](FEATURE_STATUS.md).
2. Filter Deals before selection. When creating from Quotations, filter Deals by the selected Customer Type. For Personal, narrow to the selected Contact. For Company, narrow to the selected Company and, when a Contact is selected, require a matching Contact. Restrict results to readable Deals with usable customer information. Keep Deal = None available and show No matching deals when appropriate. Preserve the chosen customer and clear any incompatible selection when the context changes. When creating from an existing Deal, prefill and lock its customer fields. Keep backend validation that the Quotation customer matches the Deal.
3. Use English and USD with cents. Use consistent English labels and en-US USD formatting across Product, Price List, Deal amount where shown in the flow, Quotation preview and saved view, and exported PDF. Align input precision, stored amounts, backend calculation and PDF rendering to two decimal places for monetary amounts. Preserve the numeric values and recorded totals of historical Quotations. Treat previously entered values that were intended as VND as a data review item.
4. Widen New/Edit Price List. Target approximately 900 px on desktop and fit the viewport with side margins on smaller screens. Give Product / Variant the widest column and keep Price (USD) and the remove control visible on desktop without horizontal scrolling. Stack the fields on narrow screens.
5. Fix the Product Categories dropdown. Give the menu an opaque background and correct stacking inside the dialog. Keep it usable near the bottom of the viewport and in a scrolling dialog. Preserve multi-selection, removal of secondary categories and automatic inclusion of the primary category.
Acceptance checks
Case	Expected result
Customer-first Quotation	Personal and Company show only matching Deals. Two customers of the same type do not see each other's Deals in the picker. Switching customer clears stale selections. A customer with zero matching Deals can create a standalone Quotation.
Deal-first Quotation	The correct Deal, Customer Type and Contact/Company are prefilled and the customer fields are locked. Backend validation still rejects a mismatched link. Check with the intended sales role.
USD and discounts	Product and Price List amounts display in USD. Preview, saved Quotation and PDF agree for two units at $19.99 with a $5.00 discount ($34.98) and with a 10% discount ($35.98 with the line discount rounded to cents). Reopen a historical Quotation to verify its saved totals.
Price List and Categories UI	Test New and Edit on desktop and a narrow viewport. Check a long Product/Variant name and multiple price rows. In Product, select multiple categories, remove a secondary category and verify the primary category remains selected.
Lead to delivery	Create a sample Lead with a source → convert to Contact/Company and Deal → create a Quotation from that Deal → select products and Price List → verify discounts and totals → save → export and check the PDF → send through the agreed channel → record the status.
Delivery evidence	Verify delivery separately from the status update. The current workflow exports the PDF and lets the user mark it Sent after sending it externally. Use an agreed test recipient if a live send is part of the test. Record delivery as pending when the channel or recipient is unavailable. An in-CRM email feature requires a separate scope decision.


Use Anti's existing regression evidence where available. Retest confirmed issues on the current build. Record site, checkout, roles, browser or test command, and PASS / FAIL / NOT TESTED for each case. Distinguish build and API results from interactive browser results.
Previous task — Dashboard MVP
Reported on 2026-11-13 on doublet.localhost, with base commit 09bb5163.
- PASS — Administrator and Sales User API/data checks, Lead source totals, Deal Open → Won counts and filters, Draft → Sent → Accepted follow-up and expired Sent exclusion. Restricted-access behavior, build, matching HTML/assets, Python compile, diff check and Graphify refresh were also reported as passing. Test data was rolled back.
- 5/7 in the Dashboard test module — Two timeline Version assertions still fail. Confirm against the base checkout before calling them pre-existing.
- NOT TESTED — Authenticated browser clicks on the Open, Won and Draft cards and follow-up rows, empty/retry states and narrow viewport rendering. Carry these checks into the next browser pass.

Implementation and verification — 2026-11-13

Checkout and site

- Working tree: `fix/regression-task-notes-product`, based on commit `09bb51630b626e31671c2676fe9070d890b56ffe`; the implementation is not committed.
- Runtime target: `doublet.localhost` in `crm-frappe-1`. Existing Dashboard, Call Log and asset changes were preserved.
- Graphify: PASS — read the current root and frontend reports before editing, traced Lead conversion → Deal customer links → Quotation pricing/PDF and refreshed both graphs after the source changes. The refreshed graphs contain 3,135 root nodes and 2,621 frontend nodes.

Implemented

- Customer-first Quotation now loads readable Deal customer fields and filters the picker by Customer Type, Contact and Company. `None` remains available, `No matching deals` is shown for a resolved empty context, and a stale Deal is cleared when customer context changes. Deal-first creation still prefills and locks customer fields; backend customer/Deal matching remains authoritative.
- Quotation now exposes Percentage and Amount discounts. Preview arithmetic uses integer cents with half-up rounding. Product, Price List, Deal amounts, saved Quotation metadata and PDF use English/en-US USD with two decimal places.
- The lifecycle snapshot normalizes numeric types before comparison, so existing non-Draft Quotations do not become editable or fail status transitions merely because metadata precision changed. Existing recorded non-Draft totals continue to be copied from the prior document.
- Price List uses a `4xl` (approximately 896 px) dialog, viewport-constrained scrolling, a wide Product/Variant field, visible USD price/remove controls on desktop and stacked rows on narrow screens.
- Product Categories uses an opaque menu, portal collision handling and viewport-constrained scrolling while retaining primary-category inclusion and secondary-category removal behavior.
- `Mark as Sent` now requires confirmation that the PDF was already delivered through the agreed external channel and explicitly says the action does not send anything.

Acceptance results

| Case | Administrator / System Manager | Sales User | Evidence |
|---|---|---|---|
| Customer-first Deal filtering | PASS (logic/build) / CHƯA TEST (browser) | PASS (permission-backed list design) / CHƯA TEST (browser) | Pure JS check passes Personal, Company, Company+Contact and cross-customer exclusion. Frappe `get_list` remains permission-filtered. Interactive picker and stale-clear behavior need browser verification. |
| Deal-first and mismatch rejection | PASS (backend) / CHƯA TEST (browser) | PASS (backend) / CHƯA TEST (browser) | Quotation module passed the existing Deal/customer mismatch and Sales User readable-Deal creation cases. Prefill/locked fields compiled into the production bundle. |
| `$19.99 × 2`, `$5.00` discount | PASS (preview logic and saved backend) | CHƯA TEST (browser) | JS result: subtotal `$39.98`, discount `$5.00`, total `$34.98`. Backend module passed this saved-value case before the later PDF assertion was added. |
| `$19.99 × 2`, `10%` discount | PASS (preview logic and saved backend) | CHƯA TEST (browser) | JS/backend result: subtotal `$39.98`, rounded discount `$4.00`, total `$35.98`. |
| Historical non-Draft totals | PASS (source and lifecycle regression) / CHƯA TEST (existing site record) | CHƯA TEST | Numeric snapshot normalization fixed a real float/Decimal lifecycle mismatch found by the first test run. Reopening a chosen historical record in browser is still pending. |
| PDF | PASS (template/build) / CHƯA TEST (new HTML assertion and downloaded PDF) | CHƯA TEST | English USD template and two-decimal renderer are implemented. The newly added HTML/PDF-total regression was added after Docker execution permission became unavailable, so it must be rerun; downloaded binary has not been visually checked. |
| Price List and Product Categories UI | PASS (production build) / CHƯA TEST (visual) | CHƯA TEST | Desktop, narrow viewport, long names, multiple rows, menu placement and category interaction require browser verification. |
| Lead → Deal → Quotation → delivery | CHƯA TEST end-to-end | CHƯA TEST end-to-end | No agreed channel or recipient was available. External delivery and only then `Mark as Sent` must be tested together. |

Commands and results

- PASS — `bench --site doublet.localhost migrate`.
- PASS — focused Quotation backend suite, 18/18, after fixing numeric snapshot normalization. Command: `bench --site doublet.localhost run-tests --app doublet_crm --module doublet_crm.doublet_crm.doctype.doublet_quotation.test_doublet_quotation`.
- CHƯA TEST — rerun of the now 19-test suite. The final PDF/historical assertion was added after the 18/18 run, and further Docker execution permission was unavailable.
- PASS — direct JS assertions for Deal filtering and both discount examples.
- PASS — Python compile, `git diff --check`, two production Vite builds, generated HTML asset references and existence of the referenced JS/CSS. Vite only reported its existing large-chunk warning.
- CHƯA TEST — authenticated browser cases. No browser was available in this execution, so no browser case is reported as PASS.

Files changed for this task

- Frontend source: `frontend/src/pages/QuotationForm.vue`, `frontend/src/utils/quotation.js`, `frontend/src/utils/index.js`, `frontend/src/components/Modals/PriceListModal.vue`, `frontend/src/components/Modals/ProductModal.vue`, `frontend/src/components/Modals/DoubleTConvertToDealModal.vue`, `frontend/src/components/DoubleTDealKanban.vue`, `frontend/src/components/Deal/DoubleTDealInfoPanel.vue`, and `frontend/src/components/Deal/DoubleTDealDataPanel.vue`.
- Backend, metadata and tests: `doublet_crm/doublet_crm/doctype/doublet_deal/doublet_deal.json`, Product/Price List/Quotation DocType JSON files, `doublet_quotation.py`, `quotation_pdf.py`, `test_doublet_quotation.py`, and `doublet_crm/templates/quotation_pdf.html`.
- Build/analysis output: `doublet_crm/public/frontend/`, `doublet_crm/www/doublet_crm.html`, `graphify-out/`, and `frontend/graphify-out/`.
