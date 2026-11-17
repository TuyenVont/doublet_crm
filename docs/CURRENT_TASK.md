# CURRENT TASK — Quotation Emails and threaded replies

Status — COMPLETION PASS IMPLEMENTED in the current WSL worktree. Automated/API/build verification passes; browser and live-mail verification remain for Tuyền. Preserve the existing Order, Call Log, Zalo OA and generated-asset changes.

## Completion pass — recipient, layout and automatic delivery

1. Resolve the initial PDF recipient from the readable Quotation Contact, then Company email; expose readable Contacts from the same Company for name/email search while preserving manual entry and clearing state between quotations.
2. Use the available page width, keep product-table overflow local, widen the Send and Reply composers, and distinguish Outgoing/Received direction from Queued/Sent/Failed/Unknown delivery state.
3. Build mail with the configured CRM outgoing account as From and its receiving inbox as Reply-To. Enqueue the newly committed Email Queue immediately with a deduplicated background job instead of waiting for the scheduler's next `all` tick.
4. Poll queued mail for a bounded interval, prefer Communication delivery state when Queue records have been cleaned up, and retain manual Refresh.
5. Only allow Reply to a Received Communication. Warn and require explicit confirmation when sending a PDF after the site's `valid_until` date; Reply remains available.

## Objective

Add an Emails tab to saved `DoubleT Quotation` records so Sales can read inbound and outbound Frappe `Communication` history, see real Email Queue delivery status and attachments, and reply in the same email thread without leaving DoubleT CRM.

## Implementation scope

1. Reuse the existing email presentation/editor patterns where compatible, but expose quotation-specific, permission-checked DoubleT APIs.
2. Load Communications linked to the quotation, including inbound mail such as `CRM-INBOUND-01`; show sender, recipients, subject, timestamp, content, attachments, loading, empty and error states.
3. Send quotation PDFs through the existing Email Queue while creating exactly one outbound Communication linked to the quotation. Show Queued, Sent or Failed from the actual queue state. Preserve the existing quotation lifecycle and manual `Mark as Sent` behavior.
4. Reply to a selected Communication with recipients prefilled, Frappe threading metadata preserved and the outbound Communication linked to the same quotation. Prevent duplicate submission and retain the draft after errors.
5. Require quotation read permission for history, quotation write permission for send/reply, verify that the replied-to Communication belongs to the quotation, and preserve normal File permissions.
6. Keep Deal email, automatic Contact/Lead association and a global Inbox outside this task.

## Acceptance checks

| Case | Expected result |
|---|---|
| Existing inbound | Opening `QUO-00005` → Emails shows `CRM-INBOUND-01` immediately from its saved Communication link. |
| PDF delivery | One Send action creates one outbound Communication and one queued email with the quotation PDF; the tab reports Queued / Sent / Failed from Email Queue. |
| Threaded reply | Reply prefills the original counterparty, uses Frappe reply/thread headers, links the outbound Communication to the quotation and resists double clicks. A failed attempt keeps the draft. |
| Permissions | Users without quotation read access cannot fetch history or attachments; users without quotation write access cannot send or reply; a Communication from another record cannot be used as the reply source. |
| Regression | PDF export, quotation status transitions and manual `Mark as Sent` retain their current behavior. Production build and focused backend tests pass. |

## Verification record — 2026-11-17

- PASS — `get_quotation_emails("QUO-00005")` returned the Received Communication with subject `Re: Quotation QUO-00005` and content containing `CRM-INBOUND-01`.
- PASS — `get_quotation_email_context("QUO-00005")` resolved Contact `Đỗ Hoa <dohoa@gmail.com>`, listed that Contact under the linked Company, and reported `valid_until=2026-11-15` as expired on the site date.
- PASS — focused Quotation Email suite: 7/7. Coverage includes Contact/Company/no-email recipient resolution and same-company search, linked inbound history, private attachment filtering, Guest/read-only denial, one Communication and one queue job per send call, scheduler-compatible queue locking, PDF attachment, Communication-first/Unknown status, expired confirmation, Received-only threaded Reply and cross-quotation rejection.
- PASS — production build completed for 2,461 modules with only the existing large-chunk warning. Python compile and `git diff --check` pass.
- PASS — queue diagnosis for `k1v4krnns6`: it changed from Not Sent to Sent after about four minutes; scheduler and worker were online. The wait was the scheduler's `all` interval, not an observed SMTP failure. The completion pass now enqueues that queue's `send` method after commit.
- PARTIAL — the existing Quotation regression suite passed 18/19. The remaining test compares Decimal totals before reload with float totals after reload; no quotation email file participates in that conversion.
- NOT TESTED — authenticated browser opening `QUO-00005` → Emails, visual content/attachment behavior, responsive layout and refresh.
- NOT TESTED — real PDF delivery through the completion-pass path, resulting automatic Queued → Sent/Failed transition, corrected live From/Reply-To headers, and a real reply grouped in the recipient mailbox thread.

---

# Previous task — Zalo OA Inbox and reply experience

Status — Task 24C implemented in the current WSL worktree. Backend regression, production build and API acceptance on `doublet.localhost` pass; interactive browser checks remain pending.

## Task 24C objective

Upgrade the standalone Inbox with global search, OA and reply-state filters, latest-message previews and stable activity ordering. Add a permission-aware Customer details panel and improve the shared composer used by Inbox and the four record tabs.

## Task 24C implementation verification — 2026-11-16

- PASS — Inbox filtering and pagination are server-side across the full permission-filtered conversation set. Six backend tests cover search outside page one, OA filtering, stable latest activity, Needs reply/Replied transitions, future-dated inbound handling, deep links and restricted users.
- PASS — `doublet.localhost` has two acceptance conversations across `mock-oa-01` and `mock-oa-02`. Searching `task24c-user-02` and filtering `mock-oa-02 / Needs reply` returned the expected conversation.
- PASS — saving a mock reply changed the `mock-oa-02` conversation to Replied, updated its preview and made the reply its latest activity. Customer details returned the readable Lead with source and status.
- PASS — production build completed with only the existing large-chunk warning.
- NOT TESTED — interactive browser behavior for the responsive Customer details panel, filter controls, Enter/Shift+Enter and Vietnamese IME in Inbox and all four record tabs. Restricted-user API behavior passes automated coverage; restricted-user browser behavior is not tested.

## Task 24B baseline — record chat

Status — Implemented in the current WSL worktree; automated backend and production-build checks pass. Browser verification of the four record tabs remains pending. Mock inbound and Lead linking passed the reported Postman cases on `doublet.localhost`. The standalone Inbox was observed in the browser with two inbound messages, a mock reply and navigation to the linked Lead.

## Objective

Add a `Zalo OA` tab to Lead, Deal, Contact and Company details. Users can select a linked conversation, read its history and save a mock reply from the record detail page.

## Implementation scope

1. Read root and frontend Graphify before inspecting source. Verify the WSL branch, local changes, routes and APIs against the running checkout.
2. Add the tab to the existing detail navigation. Adapt the Company detail layout to expose the same chat functionality.
3. Reuse Inbox message history and reply behavior. Show sender context, timestamps, message direction, mock labels and older messages. Keep an optional deep link to the selected conversation in Inbox.
4. Resolve records through `Conversation.lead`, `Deal.source_lead`, and the Lead conversion fields `converted_deal`, `converted_contact` and `converted_company`, as appropriate to the record being viewed.
5. Enforce backend permissions and verify record-to-conversation membership on record-scoped requests. Handle empty, loading, error and restricted states. Clear stale results when changing records or conversations.
6. Preserve the standalone Inbox and existing detail workflows. Live OA webhook and live outbound delivery remain pending OA access.

## Acceptance checks

| Case | Expected result |
|---|---|
| Lead with Zalo history | The Zalo OA tab on `Zalo user mock-user-01` shows its two inbound messages and the saved mock reply. |
| Reply from the record | Saving a mock reply in the tab adds one outbound message to the same thread. The message remains after refresh and appears in Inbox. |
| Deal, Contact and Company | Related records show the conversation reached through their saved Lead relationships. A record without a linked conversation shows an empty state. |
| Access and record isolation | A user lacking access cannot read or reply. Changing the record or conversation ID never returns another record's history through the record-scoped API. |
| Inbox navigation | Open in Inbox selects the correct conversation, including conversations outside the first list page. |
| Regression | Existing tabs work, the tab is reachable at narrow widths, and existing Postman responses retain their behavior. |

Record the tested commit, site and role with PASS / FAIL / NOT TESTED. Record build results and browser results independently.

## Implementation verification — 2026-11-16

- PASS — `npm run build`; Vite completed with only the existing large-chunk warning.
- PASS — `test_zalo_inbox`: 4 tests, including Lead/Deal/Contact/Company relationship resolution, record/conversation isolation, mock reply persistence, whitelist validation and restricted-role behavior.
- PASS — `doublet.localhost` record-scoped APIs returned the `mock-user-01` conversation with two mock inbound messages and one saved mock reply. Direct conversation lookup for Inbox deep-linking also passed.
- PASS — replaying `mock-message-01` and `mock-message-02` returned `duplicate: true` with the existing conversation, messages and Lead.
- NOT TESTED — interactive Lead/Deal/Contact/Company tabs, narrow viewport, reply submission from the browser and refresh into Inbox. The site Lead currently has no converted Deal/Contact/Company, so those browser paths need linked acceptance data.
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
