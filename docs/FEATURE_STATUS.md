# DoubleT CRM — Feature status

Updated: 2026-11-05. Status is based on uploaded 2026-10-31 source, 2026-11-04 Task patch, current checkout inspection, and user's manual test reports. **Runtime changes still require target-environment validation.**

Legend: `MANUAL PASS` user tested; `SOURCE PRESENT` code exists but functionality not fully verified; `IN PROGRESS`; `PLANNED`; `NOT TESTED`.

| Area | Current status | Evidence / caveat | Next focus |
|---|---|---|---|
| Lead | SOURCE PRESENT | Views/detail and DoubleT Lead DocType in ZIP; user reports earlier development | Regression after shared component changes |
| Deal | SOURCE PRESENT | Deal views, detail, stage model, tests in ZIP | Regression for sidebar/stage/tasks |
| Contact | SOURCE PRESENT | List/detail/data panel and Doctype in ZIP | Regression; Tasks tab integration |
| Company | SOURCE PRESENT | List/detail/DoubleTEntityDetail and Doctype in ZIP | Tasks section integration |
| Standalone Tasks MVP | MANUAL PASS | User tested Create/Edit/Delete, My Tasks, status/priority/due/assign, date filters, linked records and navigation after patch | Preserve behavior, test permissions later |
| Task inside record detail | IN PROGRESS | Existing tabs/sections and shared Activities; legacy `CRM Task` handlers and data-shape concerns | `docs/CURRENT_TASK.md` |
| Notes | IN PROGRESS — LEAD MANUAL PASS | Backend 6/6; Lead detail manually verified; shared component covers four detail views and centralized `/notes`; production build passes. Central page and remaining detail views not manually tested | Manually validate centralized search/filter/CRUD/navigation and remaining detail views |
| Task Kanban | PLANNED | Standalone MVP patch uses list, not Kanban | Defer until CRM Core integration stable |
| Smart Reminder | PLANNED | Not validated as DoubleT functionality | Defer |
| Recurring Task | PLANNED | Not validated as DoubleT functionality | Defer |
| Products / Categories | PLANNED | User's roadmap; implementation not verified | Separate feature spec |
| Quotations / Orders | PLANNED | User's roadmap; implementation not verified | Separate feature spec |
| Messaging / Zalo OA / Contact Center | RESEARCH | Direction discussed, not implemented here | Defer |
| Build / permissions / regression | NOT TESTED | Manual Task tests are not substitutes for automated and role-based tests | Focused regression before merge |

## Completion criteria
A feature is `DONE` only if its required behavior is demonstrable on the target environment, tests are recorded, there are no critical regressions, and changes are committed (or explicitly ready for review). Do not mark a feature done solely because code exists.

## Working cadence
1. Finish `docs/CURRENT_TASK.md` only.
2. Record file diff, test evidence, outstanding issues.
3. Request user review; commit only when authorized.
4. Update this table and swap to the next CURRENT_TASK in a separate request.
