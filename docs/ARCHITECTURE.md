DoubleT CRM — Architecture map
Evidence and freshness
- Verified against GitHub main at 26feef6, the merge of PR #20 on 2026-11-12. Status and test evidence are in [FEATURE_STATUS.md](FEATURE_STATUS.md).
- WSL and Docker can contain newer or uncommitted changes. Check the branch, commit, working tree, and running build before editing or testing. Paths below are relative to apps/doublet_crm/.
- The local Dashboard draft and the user's local Call Log changes are work in progress. Use [CURRENT_TASK.md](CURRENT_TASK.md) for the Dashboard scope.
Deployment topology
Windows / VS Code → WSL checkout → Docker container crm-frappe-1
                                     ├─ Frappe Bench / site doublet.localhost
                                     ├─ DoubleT CRM Python and DocTypes
                                     └─ Vue / Vite frontend assets
Other containers: crm-mariadb-1, crm-redis-1
- Previously observed Bench directory: /home/frappe/frappe-bench. Confirm the container, site and mounted checkout before running Bench there. The WSL-local Bench previously lacked env/bin/frappe.
- Browser routes use createWebHistory('/doublet-crm'). The Vite build writes assets under doublet_crm/public/frontend/ and updates doublet_crm/www/doublet_crm.html. Deploy the HTML and assets from the same build.
- doublet_crm/patches.txt runs the legacy category backfill and Retail/Wholesale seed after model sync. Verify both clean installation and upgrade when preparing a release.
Backend and data model
Area	Main entry points and relationships
Lead conversion	doublet_crm/doublet_crm/doctype/doublet_lead/doublet_lead.py creates or links a Contact, optional Company, and Deal. Lead stores converted_contact, converted_company, converted_deal, and converted_on. Deal stores source_lead, contact, company, deal_owner, stage, amount, won_on, and lost_on.
Deal pipeline	doublet_crm.api.update_deal_stage checks write permission and updates the stage. DoubleT Deal Stage supplies the stage label, order and lifecycle type (OPEN, WON, LOST).
Task and Notes	Both support Lead, Deal, Contact and Company references. Task uses reference_doctype + reference_docname; Note uses reference_doctype + reference_name.
Activities	doublet_crm.api.get_activities returns [versions, calls, notes, tasks, attachments] after checking access to the reference. add_activity_comment handles comments. Some WhatsApp paths still reference crm.api.whatsapp.*; the Call Area on main still references a Frappe CRM call detail method.
Product catalog	DoubleT Product uses product_kind (Standard, Template, Variant), variant_of, variant_attributes, sku, price, and is_active. category is the primary category; categories contains category assignments.
Pricing	Contact and Company can link to DoubleT Price List. doublet_crm/pricing.py resolves an explicit list, then Company, Contact or the default in DoubleT Pricing Settings, with fallback to the Product price when a matching list item is absent.
Quotation	DoubleT Quotation links to a Deal and its customer. DoubleT Quotation Item stores product details, unit price, quantity, discount type/value and line total. The controller validates and calculates totals. quotation_pdf.py renders the PDF.
Call Log	doublet_crm.api.create_call_log accepts authenticated integration events and uses external_call_id for duplicate detection. The controller can match a unique Lead or Contact by phone. Local WSL changes reported by the user add explicit Deal references and use frappe.client.get for details.
Dashboard	doublet_crm/dashboard.py defines native Frappe Desk cards/charts and is wired to after_migrate. The custom CRM route serves a placeholder on main. The local draft connects the route to Dashboard.vue and adds doublet_crm.dashboard.get_overview.


Task and Notes contracts
- get_linked_tasks(doctype, docname) queries DoubleT Task and returns [[], [], [], tasks, []]. With include_pagination=1, index 3 contains {tasks, has_more, limit_start, limit_page_length}. Check consumers before changing the shape.
- get_linked_notes filters on both reference fields after checking record access. get_notes provides the centralized, permission-checked listing.
- Tasks.vue provides standalone management, My Tasks, filters, assignment and linked navigation. The shared Activities.vue and AllModals.vue use DoubleT Task for linked tasks.
- SharedNotes.vue handles CRUD for the Notes page and the four record detail views. It discards stale responses when the active record changes.
- Task statuses are Backlog, Todo, In Progress, Done, and Canceled. Priorities are Low, Medium, High, and Urgent.
Frontend routes
Paths below are relative to /doublet-crm and declared in frontend/src/router.js.
Path	Route name	Component
/dashboard	Dashboard	PlaceholderView.vue on main; Dashboard.vue in the local draft
/leads	Leads	LeadsView.vue
/leads/:leadId	LeadDetail	FrappeLead.vue
/deals	Deals	DealsView.vue
/deals/:dealId	DealDetail	DealDetailView.vue
/contacts/:contactId	ContactDetail	ContactDetailView.vue
/companies/:companyId	CompanyDetail	CompanyDetailView.vue
/products	Products	ProductsView.vue
/products/categories	ProductCategories	ProductCategoriesView.vue
/price-lists	PriceLists	PriceListsView.vue
/quotations	Quotations	QuotationsView.vue
/quotations/new	QuotationCreate	QuotationForm.vue
/quotations/:quotationId	QuotationDetail	QuotationForm.vue
/call-logs	Call Logs	CallLogs.vue
/tasks	Tasks	Tasks.vue
/notes	Notes	Notes.vue


Architecture boundaries
- Own DoubleT business logic and DocTypes in this app. Reuse Frappe Framework permissions and APIs and existing frappe-ui components. Keep changes out of Frappe core and avoid adding dependencies on Frappe CRM or ERPNext.
- Keep aggregation and authorization on the backend. A Dashboard count, chart, list or deep link must respect the current user's effective read access.
- The base DocType definitions grant Lead, Task and Note CRUD to System Manager. Sales User and Sales Manager have read access to Deal in the base schema. Check effective permissions on the target site, which may include role overrides and document sharing.
- Quotation stages are Draft, Sent, Accepted and Rejected. Mark as Sent records status manually. The current flow exports a PDF for external delivery; the Quotation form has no email-send action.