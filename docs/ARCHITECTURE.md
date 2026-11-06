# DoubleT CRM — Architecture map

## Evidence and freshness
- **Verified in uploaded source ZIP** `doublet_crm-main (2)(4).zip` (snapshot 2026-10-31), plus uploaded `DoubleT_Task_MVP_patch.zip` (2026-11-04).
- The user's actual WSL/Docker checkout may differ. Agent **must verify current code** before edits. Paths here are relative to Frappe app root `apps/doublet_crm/`.
- User has manually tested standalone Task MVP operations on the live environment, but **integration into every record page is not yet confirmed**.

## Deployment topology
```text
Windows/VS Code → WSL checkout → Docker container crm-frappe-1
                                     ├─ Frappe Bench / site doublet.localhost
                                     ├─ DoubleT CRM Python / DocTypes
                                     └─ Vue/Vite frontend assets
Other containers: crm-mariadb-1, crm-redis-1
```
- Browser route base: `/doublet-crm` via `createWebHistory('/doublet-crm')`.
- `frontend/package.json` build script: `vite build --base=/assets/doublet_crm/frontend/`.
- Docker bench path previously observed: `/home/frappe/frappe-bench`. Check current container before running.
- Avoid running local WSL `bench`: local `env/bin/frappe` was missing while container bench worked.

## Backend
- `doublet_crm/api.py`: whitelisted `get_linked_tasks(doctype, docname)`, `get_linked_notes(doctype, docname)`, permission-checked `get_notes(search, reference_doctype)`, and `update_deal_stage(...)`.
- `doublet_crm/doublet_crm/doctype/`: business DocType JSON/Python definitions.
- New Task patch: `doublet_crm/doublet_crm/doctype/doublet_task/` (`doublet_task.json`, `doublet_task.py`, `__init__.py`).
- Shared Notes backend: `doublet_crm/doublet_crm/doctype/doublet_note/`; references use `reference_doctype` plus `reference_name` and are limited to the four DoubleT entities.
- `get_linked_tasks` accepts four entity doctypes and returns legacy-shaped `[[], [], [], tasks, []]`; patch changed its query from `CRM Task` to `DoubleT Task`. Verify permission behavior and consumers before altering response shape.
- `get_linked_notes` checks read access to the referenced record and filters by both reference fields. Backend CRUD, persistence, four-entity references, record isolation, and Administrator/Guest permissions passed focused tests on 2026-11-05.

| DocType | Important fields verified in uploaded source |
|---|---|
| `DoubleT Lead` | `first_name`, `last_name`, `status`, `lead_owner`, `converted_contact`, `converted_company`, `converted_deal` |
| `DoubleT Deal` | `deal_title`, `deal_owner`, `source_lead`, `contact`, `company`, `stage` |
| `DoubleT Contact` | `first_name`, `last_name`, `contact_owner`, `company` |
| `DoubleT Company` | `company_name`, `company_owner` |
| `DoubleT Task` (patch) | `title`, `description`, `status`, `priority`, `due_date`, `assigned_to`, `reference_doctype`, `reference_docname` |
| `DoubleT Note` | `title`, `content`, `reference_doctype`, `reference_name` |

`DoubleT Task` status options: `Backlog`, `Todo`, `In Progress`, `Done`, `Canceled`. Priority options: `Low`, `Medium`, `High`, `Urgent`. `reference_docname` is a Dynamic Link whose doctype comes from `reference_doctype`.

**Permission risk**: Uploaded Task JSON grants CRUD to `System Manager`; no other roles confirmed. Test with a non-admin user before claiming multi-user readiness.

## Frontend routes
Defined in `frontend/src/router.js`:

| URL | Route name | Component |
|---|---|---|
| `/leads` | `Leads` | `LeadsView.vue` |
| `/leads/:leadId` | `LeadDetail` | `FrappeLead.vue` |
| `/deals` | `Deals` | `DealsView.vue` |
| `/deals/:dealId` | `DealDetail` | `DealDetailView.vue` |
| `/contacts/:contactId` | `ContactDetail` | `ContactDetailView.vue` |
| `/companies/:companyId` | `CompanyDetail` | `CompanyDetailView.vue` |
| `/tasks` | `Tasks` | `Tasks.vue` |
| `/notes` | `Notes` | `PlaceholderView.vue` in snapshot; verify live state |

Avoid guessing route names such as `Lead`, `Deal`, `Company` that are not declared above.

## Shared Notes frontend
- `frontend/src/components/Notes/SharedNotes.vue` owns linked-note loading and
  create/edit/delete UI using the Notes APIs and standard Frappe document APIs.
- `/notes` renders the same component in management mode for centralized
  listing, search, type filtering, reference selection, and linked navigation.
- Lead, Deal, and Contact render it from their existing Notes tabs. Company
  renders the same component in `DoubleTEntityDetail.vue`.
- Inputs are `referenceDoctype` and `referenceName`. A request sequence guard
  clears state on record changes and ignores stale responses.
- Production build passed on 2026-11-05; browser behavior remains to be manually
  verified on all four detail pages.

## Where Task integration already exists
- `frontend/src/pages/FrappeLead.vue`: **Tasks tab exists** and uses shared `Activities` with `doctype="DoubleT Lead"`.
- `frontend/src/pages/DealDetailView.vue`: **Tasks tab exists** and uses shared `Activities` with `doctype="DoubleT Deal"`.
- `frontend/src/pages/ContactDetailView.vue`: **Tasks tab exists** and uses `Activities` with `doctype="DoubleT Contact"`.
- `frontend/src/pages/CompanyDetailView.vue` delegates to `DoubleTEntityDetail.vue`, which **renders Tasks section** using `Activities` with computed `doctype="DoubleT Company"`.
- `frontend/src/components/Activities/Activities.vue`: `linkedTasks` resource requests `doublet_crm.api.get_linked_tasks`; shared `TaskArea.vue` renders individual tasks.
- `frontend/src/components/Activities/ActivityHeader.vue`: New Task action calls `modalRef.showTask()`.
- `frontend/src/components/Activities/AllModals.vue`: **snapshot still uses `CRM Task` in show/delete/update status**. This may be why a tab can display but not create/edit correctly. Do not globally replace other CRM-related doctypes.
- `frontend/src/components/Activities/Activities.vue`: verify actual `linkedTasks` data shape and computed `activities` behavior; `linkedTasks.transform` returns `{tasks: [...]}` but the Tasks branch in snapshot passes `linkedTasks.data` directly to `sortByModified`. **Investigate, do not assume.**
- `frontend/src/components/Activities/TaskArea.vue`: uses `modalRef` for editing, status updates, delete.
- Legacy `crm.api.activities.get_activities` is referenced for other activity types; outside Task scope unless the Task tab is demonstrably blocked by it.

## Task page (November 4 patch)
- `frontend/src/pages/Tasks.vue`: standalone CRUD, My Tasks, status and due filters, assigned user, dynamic reference to four DoubleT types, navigation to related detail routes.
- Manual testing reported working for standalone list/Create/Edit/Delete, date and status filters, assignment and links. This is **user-reported**, not automated coverage.

## Architectural boundaries
- Task domain state and UI must remain independent of Frappe CRM / ERPNext.
- Reuse a single `DoubleT Task` DocType; avoid introducing a parallel Task schema.
- Preserve server permissions and check record access before showing linked tasks.
- Distinguish `Customer/Contact/Company` concepts: no assumption of an existing many-to-many contact-company model.
- Route, field names and existing code take precedence over speculative docs.
