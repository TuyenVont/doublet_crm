# CURRENT TASK — PR #35 integration (27 Nov 2026)

- Integrate PR #34 (EXT-05/06) with PR #35 (Reports, Sales Completion and Sales Activities).
- Before integration: 197/197 backend tests reported by Codex; migration and production build confirmed by user. These are not post-integration results.
- Integration conflict resolution prepared; post-integration build, migration, runtime tests and browser acceptance pending. Keep PR draft until verified.
- REP-13 remains out of scope.

## Historical implementation records (not current task instructions)

## Historical task — Sales Completion Phase 3: Quotation Fixes & Order Management (EXT-09, ORD-03..06)

Updated 2026-11-27. Finalized EXT-09 and Order Management (ORD-03..06), then added Appointment and in-app Reminder management. Migration (`bench migrate`), runtime role tests, production build, and browser acceptance remain pending until final verification.

## Implemented in Phase 3 (27 Nov)

- **EXT-09 Fixes**:
  - `DoubleTQuotation.validate` now evaluates `validate_items_and_calculate` and `sync_discount_approval_state` before checking `ensure_quotation_can_send(self)` on `Draft -> Sent`, preventing financial edits + `Sent` in the same save from bypassing approval.
  - `send_quotation_email` and `Mark as Sent` share `ensure_quotation_can_send`.
  - Removed `write: 1` for `Sales Manager` on `DoubleT Pricing Settings` (`doublet_pricing_settings.json`); `update_discount_approval_settings` restricts `Sales Manager` to the 3 discount approval fields only.
  - Controlled sends now re-evaluate the current financial data against current thresholds and require a matching approved snapshot when approval is currently required. Approval and email-send paths lock the Quotation row to prevent races.
- **ORD-03 (Order Lifecycle & Snapshot)**:
  - `DoubleTOrder.validate_quotation` validates Quotation consistency only at creation (`not previous`), so later source Quotation changes do not block `Confirm`, `Complete`, or `Cancel` on existing Orders.
- **ORD-04 (Customer & Deal Filtering)**:
  - `OrderForm.vue` reuses `contactsForCustomer` and `dealsForCustomer`, clears ineligible Deals on customer change, and does not overwrite customer fields when selecting a Deal.
- **ORD-05 (Quotation to Order)**:
  - Only `Accepted` Quotations can create a new linked Order through either conversion or direct insert. Direct inserts must exactly match the accepted item/customer/currency snapshot. Current approval thresholds are intentionally not applied retroactively after acceptance. Existing linked Orders remain openable.
- **ORD-06 (Permissions & Order UI)**:
  - Added `Delete` Draft Order action with confirmation in `OrderForm.vue` (gated by `canDelete` and `status === 'Draft'`), and hid `Orders` in `AppSidebar.vue` when `DoubleT Order` read permission is absent.

## Sales Activities added (27 Nov)

- **Appointment**: added `DoubleT Appointment` with Scheduled/Completed/Cancelled lifecycle, start/end validation, assignee, meeting type/location, optional Lead/Deal/Contact/Company reference, list search/time/status/assignee filters, upcoming view, navigation, permission-scoped ownership/assignment/sharing, and creation from record activity actions.
- **Reminder**: added `reminder_at`/`reminder_sent_at` to Appointment and `DoubleT Task`; validation prevents reminders after start/due time. A minute scheduler creates an assignee-only Frappe `Notification Log`, links back to the activity, locks the source row, and persists a sent marker for idempotency. Schedule, assignee, status, or reminder changes reset the marker; completed/cancelled activities are skipped.
- **Architecture decision**: Frappe Event was inspected but not used because its Public/Private participant permission model and Calendar/email/Google behavior do not match the CRM assignee/reference contract. Frappe User, Dynamic Link, Notification Log, scheduler, realtime notification, and existing Activity UI are reused.
- **Migration required**: create `DoubleT Appointment` and add Task reminder fields.

## Verification in finalization pass (27 Nov)

- PASS: Order controller focused suite `21/21`.
- PASS: Appointment/Task reminder validation and reminder idempotency suite `5/5`.
- PASS: current-threshold discount approval pure suite `3/3`.
- PASS: frontend quotation + activity-permission tests (`2` files); Python compile/JSON validation; `git diff --check`.
- PASS: `yarn build` (`2,486` modules); existing large-chunk warning only.
- BLOCKED / NOT RUN after migration: persisted Quotation suite and live Appointment/Reminder role/scheduler checks. The current site has not migrated the already-pending EXT-08/09 schema, so the attempted Quotation module produced missing DocType/field failures; this is not recorded as a product test pass.
- NOT RUN: browser acceptance and full regression, per focused-test scope.

---


Updated 2026-11-27. Implemented EXT-07, EXT-08, and EXT-09 source changes and focused unit tests. Migration (`bench migrate`), frontend production build, and live site/browser acceptance remain pending.

## Implemented in this pass (27 Nov)

### EXT-07 — Expired Quotations
- Added centralized `is_quotation_expired` and `get_site_today` in `doublet_quotation.py` using site date (`nowdate()`), keeping `Accepted` and `Rejected` terminal states intact.
- Synchronized `quotation_email.py`, `frontend/src/utils/quotation.js`, `QuotationsView.vue`, `QuotationForm.vue`, and `DealQuotations.vue` to display the `Expired` badge and filter (`Expired` / `Not Expired`) without mutating saved status or snapshots.

### EXT-08 — Quotation Templates
- Added `DoubleT Quotation Template` and `DoubleT Quotation Template Item` DocTypes (template name, description, product/service group, active flag, terms, sellable products, default quantities — no default unit price).
- Added `get_quotation_template_payload` in `doublet_quotation_template.py` to load active template items and terms into a Quotation Draft, resolving current customer/Price List prices via `pricing.py`.
- Added `QuotationTemplatesView.vue`, `QuotationTemplateModal.vue`, router `/quotation-templates`, sidebar navigation, and Draft template picker in `QuotationForm.vue` with overwrite confirmation when items already exist.

### EXT-09 — Discount Approval
- Extended `DoubleT Pricing Settings` (`enable_discount_approval`, `discount_approval_threshold_percent`, `discount_approval_threshold_amount`, `Sales Manager` write access) and `DoubleT Quotation` (`approval_status`, `approval_requested_by/on`, `approved_by/on`, `rejection_reason`, `approval_snapshot_hash`).
- Implemented backend threshold evaluation, self-approval prevention, manager-only approve/reject, financial snapshot re-evaluation on Draft edits, and blocking `Draft -> Sent` / `send_quotation_email` when unapproved.
- Added `DiscountApprovalSettingsModal.vue`, approval filter/column in `QuotationsView.vue`, and approval banner/actions in `QuotationForm.vue`.

## Verification status (27 Nov)
- `node --test frontend/tests/quotation.test.mjs`: PASS (12/12).
- `git diff --check`: PASS.
- `bench --site doublet.localhost migrate`, backend `run-tests`, production frontend build, and browser acceptance: NOT RUN (pending).

---


Updated 2026-11-26. Planning baseline `4d835a9` (23 Nov); last verified GitHub main `319ee10` (PR #33). Local/deploy parity not verified. User prioritizes missing capabilities over auditing existing code. No new Done status.

## Active work package — Phase 1 only
Model: GPT-5.6 Sol. Reasoning: High. Quota-saving mode.

Read AGENTS.md and focused existing root/frontend Graphify queries before inspecting relevant source. If missing/stale, report and inspect source directly. Verify git status, origin/main and worktrees; use isolated `feat/sales-completion` worktree, or reuse the existing branch for this exact scope. Preserve dirty Reports and `/tmp/doublet-crm-rep13` worktrees. Keep later Sales phases on this same branch. Do not overwrite user changes.

### EXT-05 — Interested products on Deal
- Inspect Deal schema/controller/detail UI, existing Product selection and Quotation creation flow. Reuse equivalent fields/components if present; do not rebuild Catalog or Pricing.
- Allow authorized users to add/remove Standard or active Variant products and positive quantities on Deal. Reject Template, inactive or unauthorized products when selecting new lines. Handle duplicate selection explicitly and consistently; preserve existing Deal records and permissions.
- When creating a new Quotation from Deal, allow loading interested products as editable draft suggestions. Resolve current prices through existing customer/Price List precedence and fallback; preserve manual price/discount and saved quotation snapshots. Do not implicitly change Deal Amount or existing quotations.
- Add minimal schema only if needed; document migration. Backend validates the same rules regardless of client.

### EXT-06 — Quotation from Qualified Lead
- Inspect FrappeLead.vue, existing Lead conversion, stored converted customer/Deal links and QuotationForm. Add a clear action for eligible Qualified Leads using the existing authorized conversion/Deal flow.
- Reuse the existing linked Deal/customer where valid; if conversion is required, require explicit user action and use existing conversion service. Do not silently create duplicate customers or Deals, bypass qualification or invent customer mappings.
- Open a new Quotation draft with correct Personal/Company context, linked Deal and traceable source Lead. Repeated clicks must not duplicate conversion or silently save quotations. Existing entry from Deal/list continues working.
- Enforce eligibility and relevant read/create/write permissions on backend; handle missing/restricted/stale links clearly.

## Acceptance — implement and focused-test in one pass
1. Authorized user can save interested Standard and Variant products with quantities; invalid/unauthorized products and quantities are rejected.
2. New Quotation from Deal loads editable suggestions with correct customer prices/fallback, without repricing saved quotations or modifying unrelated Deal data.
3. Qualified Lead action opens correct draft via existing conversion/linked Deal; source Lead traceable, nonqualified/unauthorized paths denied, no duplicate conversion.
4. Existing Deal/list Quotation flows and pricing contracts remain intact. Run relevant safe pure/mocked tests; record exact PASS/FAIL/NOT TESTED and manual acceptance steps.
5. Document any schema/migration requirements and preserve existing data. No claim of runtime acceptance without evidence.

## Weekly scope — 19 codes (23–30 Nov)
Goal: correct customer, product, price and discounts; PDF matches saved total; saved prices do not silently change; narrow screen usable. Master CHECKLIST tab `KLTN · Đối chiếu bản cuối` read 26 Nov: 12 Cần kiểm, 4 Cần làm, 3 Đề xuất. User now prioritizes new feature development.

| Phase | Codes | Boundary |
|---|---|---|
| 1 New Quotation flows | EXT-05, EXT-06 | Active only; implement missing Deal products and Qualified Lead entry. |
| 2 Quotation lifecycle | EXT-07, NEW-01 | Later: expiry badge/filter, revision preserving original. |
| 3 Advanced Quotation | EXT-08, EXT-09 | Later: business templates and discount approval. |
| 4 Localization | UX-02 | Later: scoped Vietnamese UI. |
| Separate acceptance | SALE-01, SALE-02, SALE-03, SALE-04, SALE-05, SALE-06, SALE-07, SALE-08, SALE-09, SALE-10, SALE-11, UX-01 | Existing code / Cần kiểm. Do not audit or reimplement independently now; targeted regression only where directly affected. |

Do not self-assign later phases or Order Management. Proposed phases require user instruction.

## Stop / exclusions
- No Graphify update/rebuild/post-update query, yarn/npm/bench build, migration, package install, fixture, DB-mutating tests, full suite or browser automation without explicit approval.
- No commit/push/merge/PR/deploy or generated assets; no unrelated refactors, actual AI API calls or changes to parked Reports/AI worktrees.
- Handoff by checklist code: implemented behavior, files, exact focused test results, schema/migration needs, pending role/browser checks and blockers. Update relevant docs without marking Done; stop after EXT-05/06.

## Parked work packages — preserve separately (26 Nov)

- `feat/reports-forecast-stage-aging`: uncommitted EXT-15/33 completion in the original WSL checkout, as reported by Codex. Deal/Stage probability configuration and stage-entry timestamp/actor added; Reports 55/55, Smart Insights 26/26 and focused frontend test reported PASS. Migration, lifecycle/Kanban DB tests, build and browser acceptance pending. Review risks: unset vs 0% after persistence; probability field read/write permissions; every transition path and server-controlled actor/timestamp; CSV with missing probability. Do not resume in Sales worktree.
- `feat/ai-business-insights`: uncommitted REP-13 Phase 1 in `/tmp/doublet-crm-rep13`, baseline `319ee10`. AI Settings, Password field, shared Beeknoee service and durable usage/reservation reported implemented. Backend mocked 11/11 and frontend 3/3 reported PASS. No live API call, migration, build or browser acceptance. Review risks: GET vs frontend call method, real MariaDB concurrency, duplicate requests, transaction commit isolation, key removal, and mock teardown. Later AI phases (data context, business insights, Dashboard integration) are not implemented. Do not resume in Sales worktree.
- Both packages are **not merged** and not Done. Preserve their dirty files and worktrees; do not assume their schemas or assets exist on main. No fresh tests were run for this documentation update.

## Historical worktree evidence — 2026-11-25 (not release acceptance)

- Branch/commit: `feat/reports-completion` at `acf1d7a`; it is one merge commit behind reference `ed76ba1`, with no tree difference between those commits. At that checkpoint A–E changes were uncommitted; subsequently merged in PR #33.
- Implemented: REP-03/06/08/09/10/11/12/14 and EXT-14 source changes described above. At this historical checkpoint REP-13, EXT-15 and EXT-33 were not implemented; final main now contains partial EXT-15/33 source. Existing Sales/Pipeline KPI formulas and the Pipeline 30-day stale definition were not changed.
- PASS: Reports backend 44/44; Activity backend 8/8; Smart Insights/export safety backend 9/9; frontend suite 14/14 files after the intentional six-section regression update; Python compileall; `git diff --check`; production Yarn build (2,480 modules, 74.28s, existing large-chunk warning only).
- PASS: root/frontend Graphify updated AST-only; frontend rebuilt to 3,281 nodes / 5,853 edges. Root follow-up found no tracked code changes after its completed rebuild.
- NOT TESTED: persisted seeded data reconciliation, Admin/Sales Manager/Sales User/restricted-user interactive browser acceptance, 375 px visual acceptance, forced empty/error/retry, export download opened in Excel, cross-user saved-filter behavior on site, Task creation/duplicate concurrency against live Redis/site permissions. No migration is required because no DocType/patch/fixture/schema changed.
- No migration, fixture, package install, site-data write, browser automation, commit, push or merge was performed.

Historical focused repair (25 Nov): backend mocked/read-only 66/66 PASS, frontend 5/5 files PASS, Python compile and diff check PASS. Production build/browser/migration/site writes/Graphify rebuild not run in that repair. These are reported historical results, not verification of final merge.

26 Nov documentation-only update: source review against `319ee10`; no code changes, Graphify, build, test, migration or Git mutations performed.


---

## Historical task — Sales Completion Phase 1

Updated 2026-11-26. Status: **EXT-05 and EXT-06 implemented; focused automated tests pass; migration and site/browser acceptance pending.** Do not mark the checklist Done yet.

- Verified main reference: `319ee10b48d0dff61268ffbdeb3964b39d5a16ba`.
- Planning baseline: `4d835a9`.
- Branch: `feat/sales-completion`.
- Worktree: `/tmp/doublet-crm-sales`.
- Reports and AI worktrees were left unchanged. Keep this Sales Completion branch for later phases.

## Phase 1 implementation

### EXT-05 — Deal interested products

- Deal Detail has a Products tab with loading, empty and error states, the shared sellable Product Catalog, multi-select, editable quantity, remove, explicit Save and stale-document protection.
- `DoubleT Deal Product` stores Product, name/SKU snapshots, Variant attributes, quantity and reference price under `DoubleT Deal.interested_products`.
- Deal validation checks positive finite quantity, Product read permission, active Standard/Variant sellability through the existing pricing service, and duplicate Product/SKU. Template and inactive Products are rejected.
- Reference prices use `doublet_crm/pricing.py`. Saving products does not update Deal Amount or lifecycle state.
- Creating a Quotation from a Deal asks the backend for a fresh draft context. It copies the customer, Deal, interested products and quantities, and resolves current prices at that moment. The draft remains editable and no Quotation is inserted or sent automatically.

### EXT-06 — Qualified Lead to Quotation Draft

- The actual Lead schema status `QUALIFIED` was verified. The backend accepts `QUALIFIED`, plus `CONVERTED` only so a Lead can continue after the existing conversion changes its status.
- Qualified Leads without a linked Deal receive conversion guidance. Converted Leads without a Deal receive explicit Deal guidance; no Contact, Company or Deal is created automatically.
- One readable source Deal opens the draft; multiple readable source Deals require an explicit selection. Every selected Deal must retain `source_lead`, which provides the saved Lead trace through `Quotation.deal -> Deal.source_lead`.
- The backend enforces Lead/Deal/Product/customer reads, Deal write for interested-product changes, Deal customer-field permlevel access, and Quotation create permission. Frontend visibility is not the security boundary.

## Schema and migration

This phase adds one child DocType and one Table field. After review/deployment, run `bench --site <site> migrate`. No migration was run in this implementation pass.

## Automated evidence

- PASS — backend pure/mocked focused suite: 11/11.
- PASS — frontend focused files: `salesCompletion.test.mjs`, `quotation.test.mjs`, `productCatalog.test.mjs`.
- PASS — Vue parse/compile-script check for `DealInterestedProducts.vue`, `DealDetailView.vue`, `FrappeLead.vue`, and `QuotationForm.vue`.
- PASS — Python compile, DocType JSON parsing and `git diff --check`.
- NOT TESTED — migration, persisted reload, live role matrix, browser interaction/responsive states, current site pricing data, production build and full suite. These were excluded by scope.

## Manual acceptance after migration

1. As an authorized Deal writer, add one active Standard and one active Variant, save, reload, edit quantity and remove a row. Confirm Template, inactive Product, invalid quantity and duplicate SKU are rejected and Deal Amount/stage stay unchanged.
2. Create a Quotation from that Deal. Confirm customer/Deal/items/quantities load, prices match the current effective Price List, lines remain editable, and an older saved Quotation does not change.
3. From a Qualified Lead, verify conversion guidance when records are missing. After normal conversion, create a draft from its linked Deal; with multiple source Deals, choose one and verify the saved Quotation traces back through `Deal.source_lead`.
4. Repeat with System Manager, applicable Sales roles and a restricted user to verify read/write/create denials and clear error states.

Stop after EXT-05 and EXT-06. Do not begin later Sales Completion phases from this task.
