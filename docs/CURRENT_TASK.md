# CURRENT TASK — Sales Completion Phase 1

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
