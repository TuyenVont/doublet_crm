
# DoubleT CRM — Architecture map

## Evidence and freshness

- The original architecture map was verified against GitHub `main` at `26feef6`, the merge of PR #20 on 2026-11-12. The subsequent source review at `44bc805` confirmed the Dashboard route and the merge of PR #21 for quotation email delivery.
- On 2026-11-16, the local `doublet.localhost` build showed the standalone Zalo OA Inbox with two mock inbound messages, one mock reply, and a link that opened the matching Lead. See [FEATURE_STATUS.md](FEATURE_STATUS.md) for the recorded results.
- The Zalo OA chat tabs inside Lead, Deal, Contact and Company are in scope for Task 24B. See [CURRENT_TASK.md](CURRENT_TASK.md) for implementation and acceptance criteria.
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
| Product catalog | `DoubleT Product` uses `product_kind` (`Standard`, `Template`, `Variant`), `variant_of`, `variant_attributes`, `sku`, `price`, and `is_active`. `category` is the primary category, and `categories` contains category assignments. |
| Pricing | Contact and Company can link to `DoubleT Price List`. `doublet_crm/pricing.py` resolves pricing from an explicit list, then Company, Contact, or the default in `DoubleT Pricing Settings`. It falls back to the Product price when the selected list has no matching item. |
| Quotation | `DoubleT Quotation` links to a Deal and its customer. `DoubleT Quotation Item` stores product details, unit price, quantity, discount type and value, and line total. The controller validates and calculates totals. `quotation_pdf.py` renders the PDF. The Quotation form can send the PDF by email. |
| Call Log | `doublet_crm.api.create_call_log` accepts authenticated integration events and uses `external_call_id` for duplicate detection. The controller can match a unique Lead or Contact by phone. Reported local WSL changes add explicit Deal references and use `frappe.client.get` for call details. Verify the active checkout before relying on those changes. |
| Dashboard | `doublet_crm/dashboard.py` defines native Frappe Desk cards and charts and is wired to `after_migrate`. The custom CRM route renders `Dashboard.vue`, which calls `doublet_crm.dashboard.get_overview` for permission-scoped data. |
| Zalo OA inbound | `doublet_crm.zalo_oa.receive_mock_text` receives simulated text through an authenticated request. A `DoubleT Conversation` is identified by source, OA ID, and external user ID. A `DoubleT Message` is identified by source, OA ID, and external message ID. Replaying a message returns the existing message and conversation. |
| Zalo OA Lead linking | `DoubleT Conversation.lead` links to `DoubleT Lead`. The inbound flow creates a Lead with source `Zalo OA` and status `NEW` when the conversation first needs a Lead. Later messages reuse that link. A previously saved mock conversation can acquire the link when its message is replayed. The response can include the converted Contact when the caller has read access. |
| Zalo OA Inbox | `doublet_crm.zalo_inbox` builds latest-message summaries from permission-filtered conversations/messages, applies customer/user search plus OA and reply-state filters before pagination, and orders by latest activity with conversation name as the stable tie-breaker. A mock reply is stored as a `DoubleT Message` with outbound direction and the simulation flag set. |
| Zalo OA chat in record details | Task 24B adds a chat tab inside Lead, Deal, Contact and Company detail pages. `ZaloConversationThread.vue` provides the shared history/composer used by the record tab and standalone Inbox; `ZaloRecordChat.vue` resolves and selects record conversations. `doublet_crm.zalo_inbox` exposes permission-checked record list/history/reply APIs. |

## Task and Notes contracts

- `get_linked_tasks(doctype, docname)` queries `DoubleT Task` and returns `[[], [], [], tasks, []]`. With `include_pagination=1`, index 3 contains `{tasks, has_more, limit_start, limit_page_length}`. Check existing consumers before changing this response shape.
- `get_linked_notes` filters on both reference fields after checking access to the record. `get_notes` provides the centralized, permission-checked listing.
- `Tasks.vue` provides standalone management, My Tasks, filters, assignment, and navigation to linked records. The shared `Activities.vue` and `AllModals.vue` use `DoubleT Task` for linked tasks.
- `SharedNotes.vue` handles CRUD for the Notes page and the four record detail views. It discards stale responses when the active record changes.
- Task statuses are `Backlog`, `Todo`, `In Progress`, `Done`, and `Canceled`. Priorities are `Low`, `Medium`, `High`, and `Urgent`.

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
| `/notes` | `Notes` | `Notes.vue` |

Task 24B uses the existing Lead, Deal, Contact and Company detail routes. The chat is exposed through the `Zalo OA` tab on those pages.

## Architecture boundaries

- Keep DoubleT business logic and DocTypes in the DoubleT CRM app. Reuse Frappe Framework permissions and APIs and existing frappe-ui components. The application runs on Frappe Framework with no dependency on Frappe CRM or ERPNext.
- Keep aggregation and authorization on the backend. Dashboard data, record links, Inbox queries, and chat replies follow the current user's effective permissions.
- The base DocType definitions grant Lead, Task and Note CRUD to `System Manager`. `Sales User` and `Sales Manager` have read access to Deal in the base schema. Verify effective permissions on the target site because role overrides and document sharing may apply.
- Keep Zalo transport and provider-specific logic in the integration layer. The shared conversation and message data belongs to DoubleT CRM.
- Quotation stages are `Draft`, `Sent`, `Accepted`, and `Rejected`. The form supports PDF export and email sending. `Mark as Sent` records the status manually for a quotation delivered through another channel.
```
