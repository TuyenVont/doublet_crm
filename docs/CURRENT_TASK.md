
# CURRENT TASK: Shared Notes

## Objective
Implement generic Notes for DoubleT CRM using Frappe.

## Scope
- Create DoubleT Note DocType.
- Fields: title, content, reference_doctype, reference_name.
- Support CRUD: Create, Read, Update, Delete.
- Attach Notes to Lead, Deal, Contact, Company.
- Use one shared Notes component.
- Persist data in Frappe database.
- Reload must preserve Notes.
- Notes must remain isolated by reference record.

## Implementation
1. Inspect ARCHITECTURE.md and FEATURE_STATUS.md.
2. Reuse existing DocType, API, and frontend patterns.
3. Implement backend first.
4. Implement frontend after backend validation.
5. Test CRUD, reload persistence, and record isolation.

## Constraints
- Minimal code changes.
- No unrelated refactoring.
- No new dependencies.
- Do not modify Tasks or Activities.
- Do not use subagents.
- Do not run build or migrate without approval.
- Keep existing UI conventions.

## Completion
- Update FEATURE_STATUS.md when verified.
- Record completed work and remaining issues here.
- Summarize changed files and test results.

## Progress — 2026-11-05
- Added backend source for the `DoubleT Note` DocType with `title`, `content`,
  `reference_doctype`, and `reference_name`.
- Restricted references to DoubleT Lead, Deal, Contact, and Company, and validate
  that the referenced record exists and is readable by the current user.
- Added `doublet_crm.api.get_linked_notes` for permission-checked, record-isolated
  note reads. Standard Frappe document APIs provide create, update, and delete.
- Static metadata contract, JSON parsing, Python syntax, and diff checks: **PASS**.
- Migration completed by the user. Focused backend tests on `doublet.localhost`:
  **PASS** — 5 tests covering CRUD/delete, database reload persistence, all four
  supported reference types, record isolation, and Administrator/Guest permissions.
- Test command: `bench --site doublet.localhost run-tests --module
  doublet_crm.doublet_crm.doctype.doublet_note.test_doublet_note`.
- No DoubleT Note production bug was confirmed during backend validation.
- Added one reusable `SharedNotes.vue` frontend component with create, edit,
  delete, loading, empty, retry, and mutation-error states.
- Integrated the component into the existing Notes tabs for Lead, Deal, and
  Contact, plus the Company detail page, using each record's actual DoubleT
  DocType and route-derived record name.
- The component clears notes immediately when the reference changes and ignores
  out-of-order responses, preventing a previous record's notes from rendering.
- Frontend production build: **PASS** on 2026-11-05. Vite emitted only its
  large-chunk size warning.
- Browser CRUD, page-reload persistence, and rapid record-switch isolation:
  **NOT TESTED**.
- Lead detail Shared Notes create/edit/delete and reload behavior: **MANUAL PASS**
  (user verified).
- Replaced the `/notes` placeholder with centralized Notes management using the
  same `SharedNotes.vue` CRUD logic in management mode.
- Centralized Notes supports listing, search, reference-type filtering,
  create/edit/delete, and navigation to linked Lead, Deal, Contact, or Company.
- Added permission-checked `get_notes` listing support. Focused backend tests:
  **PASS — 6/6**, including centralized search/filter and Guest denial.
- Centralized Notes frontend production build: **PASS**. Browser behavior:
  **NOT TESTED**.

## Remaining
- Manually verify Notes create/edit/delete and reload persistence on Lead, Deal,
  Contact, and Company detail pages.
- Switch directly between two records while Notes is loading and confirm no
  stale note cards appear.
- Manually verify centralized Notes search, filtering, CRUD, and linked-record
  navigation at `/doublet-crm/notes`.
