# DoubleT CRM — Architecture map

## Integration baseline — 2026-11-27

PR #35 (`45bcb3f`) integrates with main (`7221e0e`, PR #34). Preserve Phase 1 and later Sales/Reports/Activities contracts. Prior 197/197 backend tests are reported evidence before integration; migration and build were confirmed by the user before integration. Post-integration build, migration and acceptance remain pending. Historical sections below retain their original scope.

## Sales Completion Phase 1 — implemented, acceptance pending

- Worktree `/tmp/doublet-crm-sales`, branch `feat/sales-completion`, verified baseline `319ee10b48d0dff61268ffbdeb3964b39d5a16ba`.
- `DoubleT Deal.interested_products` is a Table of `DoubleT Deal Product`. Each row stores the Product link plus display snapshots, Variant attributes, quantity and a current reference price. The Deal controller revalidates Product read access, active Standard/Variant sellability, quantity and unique SKU, then resolves price through `doublet_crm/pricing.py`; it does not derive or update Deal Amount.
- `doublet_crm.sales_completion` is the permission boundary for reading/saving Deal products and preparing a Quotation Draft. It checks Deal read/write and customer-field permlevels, linked Product/Contact/Company/Lead reads, exact `Deal.source_lead` relationships and Quotation create permission. The API returns only draft data and never inserts a Quotation or converts a Lead.
- Deal-first draft creation resolves prices at request time and copies suggestions into editable new Quotation rows. Saved Quotations retain their existing snapshots and are never synchronized from Deal products.
- Lead-first creation uses the verified `QUALIFIED` status and continues from `CONVERTED` because the existing conversion flow changes the status. Missing records are handled by guidance to the existing conversion/Deal workflow; one source Deal is used directly and multiple source Deals require selection. Traceability uses the persisted `Quotation.deal -> DoubleT Deal.source_lead` chain.
- Schema sync is required after deployment. Automated evidence is pure/mocked only; persisted-site and browser acceptance remain pending.

## Historical Reports baseline — 2026-11-25

- GitHub `main` verified at `319ee10` (PR #33, merged 25 Nov; feature head `5980359`). PR #32 (`ed76ba1`, feature `acf1d7a`) is historical. The earlier planning baseline was `4d835a9` (PR #29); PR #30 synchronized deployment assets and PR #31 (`015251f`) added Sales and Pipeline analytics. Local WSL/deploy parity with `319ee10`, migration and current browser acceptance have not been independently verified in this review.
- Historical local evidence at `015251f`: deploy/main-20261123 was 0/0 against origin/main, Yarn build passed with chunk-size warnings, and two generated files differed locally. Recheck actual status before editing; preserve local changes/stashes.
- Product multi-category/variants `c025247` and Contact Center Calls merge `218cdef` are earlier in main. Historical sections below are context, not current acceptance.
- PR #33 merged A–E plus Forecast and Stage Aging source. Six report sections are mounted. Source review is not runtime acceptance. Active package is Sales Completion Phase 1. Separate unmerged Reports and AI worktrees are parked; see below.

## Sales architecture — source inspected at main `319ee10`

| Area | Existing contract / entry point |
|---|---|
| Product & Category (SALE-01/02) | `doublet_crm/doublet_crm/doctype/doublet_product/doublet_product.py`: primary category plus child category assignments, Standard/Template/Variant validation, normalized variant signature/key and duplicate detection. Template is not sellable; active Variant is independent of Template activity. Verify SKU and permissions rather than rebuilding. |
| Catalog (SALE-08) | `frontend/src/pages/ProductsView.vue` and `useDoubleTProducts`: search, category/status filters, pagination, List/Grid and image thumbnails; `productCatalog` utilities resolve own/Template/fallback image. |
| Detail (SALE-09) | `frontend/src/pages/ProductDetailView.vue`: supporting categories/templates, linked variants and attributes, permission-based edit, request guards and loading/error states. |
| Pricing (SALE-03) | `doublet_crm/pricing.py`: permission-checked documents, explicit > Company > Contact > default Price List, missing SKU fallback to Product price, reject inactive list and non-sellable product. `doublet_crm/test_pricing.py` contains tests for precedence, fallback, discounts, snapshots and Sales User access; existence is not fresh execution evidence. |
| Quotation (later phases) | `QuotationForm.vue`, `doublet_quotation.py`, `quotation_pdf.py`, `quotation_email.py`: reuse existing customer context, Catalog selector, discounts, saved snapshots, PDF/email and lifecycle. Later extensions must preserve existing contracts. |

Phase 1 implements the missing EXT-05/06 flows below. Existing catalog/pricing and quotation components are integration dependencies, not standalone audit tasks. Full browser/role/DB acceptance of the twelve Cần kiểm items is deferred. The exact 19-code scope and phase boundaries are in CURRENT_TASK.md.

### Historical Phase 1 plan (implemented by PR #34; acceptance pending)
- EXT-05: add a minimal Deal interested-products child table if no equivalent exists; store sellable Product references and positive quantities. Reuse pricing.py and QuotationForm to prefill a new Draft using the current authorized customer price context. Do not change saved quotations or Deal Amount implicitly.
- EXT-06: add a Qualified Lead quotation entry via the existing permission-checked conversion/linked Deal flow. Reuse stored customer and source Lead links; never silently create duplicate customers or Deals, or bypass qualification/permissions. If conversion is required, make it explicit. Preserve existing Deal/list quotation entry points.
- New schema, if needed, requires later migration; no migration or runtime acceptance is claimed.

## Historical parked work packages (26 Nov; Reports now in PR #35)

- `feat/reports-forecast-stage-aging`: uncommitted EXT-15/33 completion in the original WSL checkout, as reported by Codex. Deal/Stage probability configuration and stage-entry timestamp/actor added; Reports 55/55, Smart Insights 26/26 and focused frontend test reported PASS. Migration, lifecycle/Kanban DB tests, build and browser acceptance pending. Review risks: unset vs 0% after persistence; probability field read/write permissions; every transition path and server-controlled actor/timestamp; CSV with missing probability. Do not resume in Sales worktree.
- `feat/ai-business-insights`: uncommitted REP-13 Phase 1 in `/tmp/doublet-crm-rep13`, baseline `319ee10`. AI Settings, Password field, shared Beeknoee service and durable usage/reservation reported implemented. Backend mocked 11/11 and frontend 3/3 reported PASS. No live API call, migration, build or browser acceptance. Review risks: GET vs frontend call method, real MariaDB concurrency, duplicate requests, transaction commit isolation, key removal, and mock teardown. Later AI phases (data context, business insights, Dashboard integration) are not implemented. Do not resume in Sales worktree.
- Both packages are **not merged** and not Done. Preserve their dirty files and worktrees; do not assume their schemas or assets exist on main. No fresh tests were run for this documentation update.

## Reports architecture — current source at 319ee10

| Area | Current source contract |
|---|---|
| Reports Hub | `frontend/src/pages/ReportsPage.vue`, `frontend/src/utils/reports.js`, router; main has six live sections, adding Smart Insights to the five baseline reports. |
| Sales | `doublet_crm/reports.py:get_sales_performance`: Confirmed/Completed Orders by `order_date`, Won by `won_on`, Lost by `lost_on`, owner breakdown and drill-down. Booked Sales is not paid revenue. |
| Pipeline | `get_pipeline_analytics`: current stage of Deals created in period (not historical stage snapshots), Lost Reason by `lost_on`, overdue by `expected_close_date`, stale by a 30-day `modified` definition. |
| Forecast (EXT-15) | `reports.py:_sales_forecast`, `_summarize_forecast`; PipelineAnalyticsReport.vue renders monthly Open Deal value by expected_close_date, selected-period drill-down, missing-date/overdue counts and conditional weighted forecast. Probability is read from a permitted numeric Deal or Stage field if available; no invented default. Configuration and acceptance pending. |
| Stage Aging (EXT-33) | `stage_aging.py:stage_aging_for_deals`, `summarize_stage_aging`; PipelineAnalyticsReport.vue displays average current-stage days, buckets, history coverage and drill-down. Reads permission-scoped Version transitions; prolonged-stage alert uses 30 days. Current tracking flag and empty history do not independently prove historical completeness; verify legacy/actor/transition handling. |
| Journey | `get_customer_journey`: Lead creation cohort with Lead Owner and Source filters; unique Lead→Deal and Lead-with-Won-Deal rates; permission-scoped, deduplicated Deal/Quotation/Order rows distinguish quotation-linked and direct-Deal Orders. Won is current linked outcome, not historical cohort state. |
| Quotation & Order | `get_quotation_order`: preserves all-quotation conversion and adds current Accepted Quotation→Booked Order conversion. Denominator is unique currently Accepted quotations dated in range; exact Confirmed/Completed `Order.quotation` links form the deduplicated numerator irrespective of Order Date. |
| Activity | `get_activity_contact_center`: permission-scoped Calls, Tasks, CRM Communication, Zalo Conversation/Message plus Call/Task/Email/Zalo filter. Employee applies only to Call Agent/Task Assignee; Email/Zalo attribution remains explicitly unavailable. |
| Smart Insights / Health | `doublet_crm/smart_insights.py`: current as-of alerts for 7-day unchanged Open Deals, past expected close, Sent Quotation expiry within 3 days/expired, overdue unfinished Tasks and prolonged current Stage (30 days) when history is known. Deterministic health normalizes documented 25-point factors over known evidence only; readable linked Call/Email timestamps take precedence over explicitly labelled CRM `modified` fallback. It is not Won probability. |
| Export / preferences | `doublet_crm/report_tools.py` reruns allowlisted permission-scoped reports for UTF-8 BOM CSV, neutralizes spreadsheet formulas, and stores named per-user/report filters in Frappe `__UserSettings`; no customer rows are stored and no schema is added for saved filters. |
| Filters | `ReportsFilters.vue`, `ReportActions.vue`, `reportFilters.js`: dates/presets, supported owner/employee/source/channel filters, prior-period comparison where supported, CSV export, and personal saved filters. No Team field on Deal. |
| Tests | `doublet_crm/test_reports.py`, `doublet_crm/test_activity_reports.py`, frontend report tests. See FEATURE_STATUS for observed vs reported execution. |
| Dashboard | `doublet_crm/dashboard.py:get_overview()` preserves existing KPI contract and adds a compact permission-scoped Needs Attention payload from the shared Smart Insights engine; Dashboard UI provides alert links and View All to Smart Insights. |

Report aggregates and drill-down must share the same permission-scoped population. Distinguish missing/unauthorized data from zero. Do not infer paid revenue, historical snapshots, or ownership when the schema does not support them.

## Merged Reports architecture — acceptance pending

- Existing report services/components were extended; Contact Center transport/workflows were not changed. Pipeline's existing 30-day stale metric remains separate from Smart Insights' labelled 7-day alert.
- The shared permission-scoped Smart Insights service supplies Reports and Dashboard. Follow-up Task creation is an explicit authenticated endpoint, validates the current authorized alert/reference/assignee, and uses a Redis source lock plus active marker lookup to prevent concurrent duplicates.
- Export and saved filters reuse the report/filter contract, validate allowlisted inputs on the backend, require read/export permissions, and isolate preferences by authenticated user. CSV is delivered; XLSX was not added because no existing dependency supports it without churn.
- Deal schema currently has `expected_close_date`, `stage`, `won_on`, `lost_on`, and `lost_reason`, but no dedicated stage-entry timestamp or configured probability. Deal Stage has `stage_type` (OPEN/WON/LOST) and `sort_order`, not a probability. Forecast and Version-based Stage Aging already exist in main; explicit probability configuration and transition evidence were implemented in a separate parked worktree, not in main. Never invent historical backfill or weights. REP-13 Phase 1 exists in a separate parked worktree; AI interpretation and Dashboard integration remain unimplemented.
- Task reference DoTypes are Lead, Deal, Contact and Company. A Quotation alert may link to its readable Deal for a follow-up task only when valid; never insert an unsupported reference type. See CURRENT_TASK for the active scope.

## Evidence and freshness (historical)

- The original architecture map was verified against GitHub `main` at `26feef6`, the merge of PR #20 on 2026-11-12. The subsequent source review at `44bc805` confirmed the Dashboard route and the merge of PR #21 for quotation email delivery.
- On 2026-11-16, the local `doublet.localhost` build showed the standalone Zalo OA Inbox with two mock inbound messages, one mock reply, and a link that opened the matching Lead. See [FEATURE_STATUS.md](FEATURE_STATUS.md) for the recorded results.
- On 2026-11-17, the Quotation Emails completion pass was verified against branch `feat/zalo-oa-inbox` at `4b7f673` plus the current worktree. The focused email tests pass 7/7; the site API returns `CRM-INBOUND-01`, resolves the quotation Contact for `QUO-00005`, and reports that quotation as expired. Browser and live-send/reply checks remain pending.
- The Zalo OA chat tabs inside Lead, Deal, Contact and Company were in historical Task 24B; not part of the active Sales package.
- WSL and Docker can contain newer or uncommitted changes. Check the branch, commit, working tree and running build before editing or testing. Repository paths below are relative to `apps/doublet_crm/`.

## Deployment topology

```text
Windows / VS Code
  → WSL checkout
    → Docker container crm-frappe-1
      → Frappe Bench / site doublet.localhost
      → DoubleT CRM Python and DocTypes
      → Vue / Vite frontend assets

Other containers: crm-mariadb-1, crm-redis-1
```

- The previously observed Bench directory in the container is `/home/frappe/frappe-bench`. Confirm the container, site and mounted checkout before running Bench commands. The WSL-local Bench previously lacked `env/bin/frappe`.
- Browser routes use `createWebHistory('/doublet-crm')`. A Vite build writes assets to `doublet_crm/public/frontend/` and updates `doublet_crm/www/doublet_crm.html`. Deploy the HTML and assets from the same build.
- `doublet_crm/patches.txt` runs post-model-sync patches. These include the legacy product category backfill, the Retail and Wholesale Price List seed, and the `Zalo OA` Lead Source seed in the local Zalo implementation. Verify clean installation and upgrade behavior when preparing a release.

## Backend and data model

| Area | Main entry points and relationships |
|---|---|
| Lead conversion | `doublet_crm/doublet_crm/doctype/doublet_lead/doublet_lead.py` creates or links a Contact, an optional Company, and a Deal. Lead stores `converted_contact`, `converted_company`, `converted_deal`, and `converted_on`. Deal stores `source_lead`, `contact`, `company`, `deal_owner`, `stage`, `amount`, `won_on`, and `lost_on`. |
| Deal pipeline | `doublet_crm.api.update_deal_stage` checks write permission and updates the stage. `DoubleT Deal Stage` supplies the stage label, order, and lifecycle type (`OPEN`, `WON`, `LOST`). |
| Tasks and Notes | Both support references to Lead, Deal, Contact and Company. Task uses `reference_doctype` and `reference_docname`. Note uses `reference_doctype` and `reference_name`. |
| Activities | `doublet_crm.api.get_activities` returns `[versions, calls, notes, tasks, attachments]` after checking access to the reference. `add_activity_comment` handles comments. Some inherited WhatsApp paths reference `crm.api.whatsapp.*`. The reviewed GitHub baseline also has an inherited Frappe CRM call-detail reference in `CallArea.vue`. |
| Appointments | `DoubleT Appointment` stores the sales meeting snapshot, assignee, Scheduled/Completed/Cancelled state, meeting location/type, and one validated Lead/Deal/Contact/Company Dynamic Link. List visibility is manager-wide or owner/assignee/share scoped. `get_activities` adds readable linked appointments to the existing versions stream without changing its five-part response shape. |
| Reminders | Appointment and `DoubleT Task` store `reminder_at` plus the internal `reminder_sent_at` marker. `doublet_crm.reminders.send_due_reminders` runs each minute, locks due rows and inserts an assignee-only Frappe `Notification Log`. Terminal activities and inaccessible records are skipped; changed schedules reset the marker. |
| Product catalog | `DoubleT Product` uses `product_kind` (`Standard`, `Template`, `Variant`), `variant_of`, `variant_attributes`, `sku`, `price`, and `is_active`. `category` is the primary category, and `categories` contains category assignments. |
| Pricing | Contact and Company can link to `DoubleT Price List`. `doublet_crm/pricing.py` resolves pricing from an explicit list, then Company, Contact, or the default in `DoubleT Pricing Settings`. It falls back to the Product price when the selected list has no matching item. |
| Quotation | `DoubleT Quotation` links to a Deal and its customer. `DoubleT Quotation Item` stores product details, unit price, quantity, discount type and value, and line total. The controller validates and calculates totals. `quotation_pdf.py` renders the PDF. `quotation_email.py` provides permission-checked Communication history, PDF delivery and threaded replies. |
| Call Log | `doublet_crm.api.create_call_log` accepts authenticated integration events and uses `external_call_id` for duplicate detection. The controller can match a unique Lead or Contact by phone. Reported local WSL changes add explicit Deal references and use `frappe.client.get` for call details. Verify the active checkout before relying on those changes. |
| Dashboard | `doublet_crm/dashboard.py` defines native Frappe Desk cards and charts and is wired to `after_migrate`. The custom CRM route renders `Dashboard.vue`, which calls `doublet_crm.dashboard.get_overview` for permission-scoped data. |
| Zalo OA inbound | `doublet_crm.zalo_oa.receive_mock_text` receives simulated text through an authenticated request. A `DoubleT Conversation` is identified by source, OA ID, and external user ID. A `DoubleT Message` is identified by source, OA ID, and external message ID. Replaying a message returns the existing message and conversation. |
| Zalo OA Lead linking | `DoubleT Conversation.lead` links to `DoubleT Lead`. New Zalo conversations start unidentified. Inbox users with CRM permissions can link an exact Lead or Contact, or create a Lead with source `Zalo OA` and status `NEW`. Later messages and replays retain the link. The response can include the converted Contact when the caller has read access. |
| Zalo OA Inbox | `doublet_crm.zalo_inbox` builds latest-message summaries from permission-filtered conversations/messages, applies customer/user search plus OA and reply-state filters before pagination, and orders by latest activity with conversation name as the stable tie-breaker. A mock reply is stored as a `DoubleT Message` with outbound direction and the simulation flag set. |
| Zalo OA chat in record details | Task 24B adds a chat tab inside Lead, Deal, Contact and Company detail pages. `ZaloConversationThread.vue` provides the shared history/composer used by the record tab and standalone Inbox; `ZaloRecordChat.vue` resolves and selects record conversations. `doublet_crm.zalo_inbox` exposes permission-checked record list/history/reply APIs. |

## Task and Notes contracts

- `get_linked_tasks(doctype, docname)` queries `DoubleT Task` and returns `[[], [], [], tasks, []]`. With `include_pagination=1`, index 3 contains `{tasks, has_more, limit_start, limit_page_length}`. Check existing consumers before changing this response shape.
- `get_linked_notes` filters on both reference fields after checking access to the record. `get_notes` provides the centralized, permission-checked listing.
- `Tasks.vue` provides standalone management, My Tasks, filters, assignment, and navigation to linked records. The shared `Activities.vue` and `AllModals.vue` use `DoubleT Task` for linked tasks.
- `SharedNotes.vue` handles CRUD for the Notes page and the four record detail views. It discards stale responses when the active record changes.
- Task statuses are `Backlog`, `Todo`, `In Progress`, `Done`, and `Canceled`. Priorities are `Low`, `Medium`, `High`, and `Urgent`.
- Reminder time must be at or before Task due time. Appointment reminder time must be at or before its start. The Notification Log `link` points to `/doublet-crm/tasks` or the Appointment detail route.

## Quotation email contract

- `QuotationForm.vue` exposes full-width Details and Emails tabs for a saved quotation. Product-table overflow remains local on narrow viewports. `QuotationEmails.vue` loads the quotation-specific history and reuses `EmailContent.vue` and `AttachmentItem.vue` for message bodies and permitted files. Loading, empty and error states are rendered; direction is Outgoing/Received and delivery is Queued/Sent/Failed/Unknown. Queued rows poll for at most 30 seconds and manual Refresh remains available.
- `get_quotation_email_context(name, search)` requires quotation read access. It suggests the readable quotation Contact first and the readable Company second, and uses permission-filtered `frappe.get_list` to search email-bearing Contacts of that same Company by first name, last name or email. The frontend resets this state whenever the quotation route changes.
- `get_quotation_emails(name)` requires read access to the `DoubleT Quotation`, checks read access to each linked `Communication`, and only includes attached `File` records readable by the current user. Communication delivery state takes precedence over the linked `Email Queue`, so history remains meaningful after queue cleanup; absent evidence is Unknown rather than an assumed success.
- `send_quotation_email` requires read and write access to the current Draft and its matching `modified` value. An expired `valid_until` requires explicit confirmation in both frontend and backend. After these explicit DoubleT checks, it calls Frappe's internal Communication creation once and lets `Communication.send_email` produce exactly one linked Email Queue. The configured outgoing CRM Email Account supplies From, and its incoming inbox supplies Reply-To. An after-commit, queue-ID-specific background job sends the new queue immediately; job deduplication and Frappe queue-state locking make this safe alongside the scheduler. The compatibility endpoint in `quotation_pdf.py` delegates to this implementation.
- `reply_quotation_email` requires quotation write access and Communication read access, then verifies the original Communication is a Received Email linked to the same quotation. The recipient is derived from the inbound sender saved by Frappe and cannot be changed by the caller. Frappe `in_reply_to` points at the original Communication, allowing the queue builder to emit the original message ID as the email `In-Reply-To` header.
- PDF delivery does not change the quotation lifecycle. `Mark as Sent` remains a separate manual confirmation. Legacy Email Queue rows without a Communication are not synthesized as history and do not prevent linked inbound Communications from loading.

## Zalo OA record chat contract

This section defines the target behavior for Task 24B.

| Record | How to resolve linked conversations |
|---|---|
| Lead | Use `DoubleT Conversation.lead` for the Lead being viewed. |
| Deal | Use `DoubleT Deal.source_lead`. Check `DoubleT Lead.converted_deal` for records linked through the existing conversion flow. |
| Contact | Use Leads whose `converted_contact` points to the Contact being viewed. |
| Company | Use Leads whose `converted_company` points to the Company being viewed. |

- Resolve relationships on the backend using stored identifiers. The record-scoped API accepts only `DoubleT Lead`, `DoubleT Deal`, `DoubleT Contact`, and `DoubleT Company`.
- Record-scoped history and replies require permission to read the record and access its conversation and messages. The backend verifies that the selected conversation belongs to the record. Saving a reply also requires the applicable write and message creation permissions.
- The `Zalo OA` tab displays history inside the detail page and lets the user save a mock reply there. If several conversations match, the user can select one. Show loading, empty, error, and restricted states.
- The tab and standalone Inbox use the same message records. A reply saved from a detail page appears in the standalone Inbox when reloaded. `Open in Inbox` opens the selected conversation directly, including when it is outside the first page of the Inbox list.
- Record-scoped reads and replies call `list_record_conversations`, `get_record_messages` and `save_record_mock_reply`. Each request validates the reference doctype, checks record/conversation/message permissions and revalidates that the conversation resolves through the record's saved Lead relationship. Inbox deep links use `get_conversation_info` and the `conversation` query parameter instead of relying on the first list page.
- The current test flow covers simulated inbound and outbound messages. Live webhook ingestion and live outbound delivery require OA access and separate acceptance testing.

## Zalo OA Inbox contract — Task 24C

See the [Contact Center QA and integration guide](CONTACT_CENTER.md) for handling, recording demos and release verification.

- `list_conversations(start, search, oa_id, reply_status)` applies search and filters to the complete permission-filtered set before slicing a page. It returns latest-message preview, direction, timestamp, reply state, total count and available OA values.
- Needs reply means the latest message is inbound; Replied means it is outbound. Conversations without messages appear only in All. Reading or refreshing does not mutate this state.
- A newly saved reply is timestamped after the latest stored message, including when the inbound provider timestamp is ahead of the application clock, so a successful reply becomes the latest activity.
- `get_customer_details` checks access separately for Lead, Contact, Deal and Company. The UI only renders routes for readable linked records.
- `ZaloCustomerDetails.vue` provides the responsive customer panel. `ZaloConversationThread.vue` handles Enter to send, Shift+Enter for a newline, composition/IME safety, duplicate-submit prevention and draft retention on errors for Inbox and record tabs.

## Frontend routes

Paths below are relative to `/doublet-crm` and declared in `frontend/src/router.js`.

| Path | Route name | Component |
|---|---|---|
| `/dashboard` | `Dashboard` | `Dashboard.vue` |
| `/leads` | `Leads` | `LeadsView.vue` |
| `/leads/:leadId` | `LeadDetail` | `FrappeLead.vue` |
| `/deals` | `Deals` | `DealsView.vue` |
| `/deals/:dealId` | `DealDetail` | `DealDetailView.vue` |
| `/contacts` | `Contacts` | `ContactsView.vue` |
| `/contacts/:contactId` | `ContactDetail` | `ContactDetailView.vue` |
| `/companies` | `Companies` | `CompaniesView.vue` |
| `/companies/:companyId` | `CompanyDetail` | `CompanyDetailView.vue`, which delegates to `DoubleTEntityDetail.vue` |
| `/products` | `Products` | `ProductsView.vue` |
| `/products/categories` | `ProductCategories` | `ProductCategoriesView.vue` |
| `/price-lists` | `PriceLists` | `PriceListsView.vue` |
| `/quotations` | `Quotations` | `QuotationsView.vue` |
| `/quotations/new` | `QuotationCreate` | `QuotationForm.vue` |
| `/quotations/:quotationId` | `QuotationDetail` | `QuotationForm.vue` |
| `/contact-center/inbox` | `Inbox` | `ZaloInbox.vue` in the local Zalo build |
| `/call-logs` | `Call Logs` | `CallLogs.vue` |
| `/tasks` | `Tasks` | `Tasks.vue` |
| `/appointments`, `/appointments/new`, `/appointments/:appointmentId` | `Appointments`, `AppointmentCreate`, `AppointmentDetail` | `AppointmentsView.vue` + `AppointmentModal.vue` |
| `/notes` | `Notes` | `Notes.vue` |

Task 24B uses the existing Lead, Deal, Contact and Company detail routes. The chat is exposed through the `Zalo OA` tab on those pages.

## Architecture boundaries

- Keep DoubleT business logic and DocTypes in the DoubleT CRM app. Reuse Frappe Framework permissions and APIs and existing frappe-ui components. The application runs on Frappe Framework with no dependency on Frappe CRM or ERPNext.
- Keep aggregation and authorization on the backend. Dashboard data, record links, Inbox queries, and chat replies follow the current user's effective permissions.
- The base DocType definitions grant Lead, Task and Note CRUD to `System Manager`. `Sales User` and `Sales Manager` have read access to Deal in the base schema. Verify effective permissions on the target site because role overrides and document sharing may apply.
- Keep Zalo transport and provider-specific logic in the integration layer. The shared conversation and message data belongs to DoubleT CRM.
- Quotation stages are `Draft`, `Sent`, `Accepted`, and `Rejected`. The form supports PDF export and email sending. `Mark as Sent` records the status manually for a quotation delivered through another channel.
