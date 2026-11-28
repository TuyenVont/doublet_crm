# Testing & Acceptance

[← Documentation Index](../INDEX.md) · [Feature Status](../tracking/FEATURE_STATUS.md) · [Quality feature](../features/platform/QUALITY_ACCEPTANCE.md)

Scenario chi tiết cho Calls/Zalo MOCK và điều kiện LIVE: [Contact Center QA & Integration Acceptance](CONTACT_CENTER_ACCEPTANCE.md).

Scenario xuyên module cho identity, realtime, navigation, sales lifecycle, history và permission: [Cross-module End-to-End Acceptance](CROSS_MODULE_ACCEPTANCE.md).

| Layer | Meaning | Baseline status in this docs task |
| --- | --- | --- |
| Source verified | Schema/controller/API/UI path inspected | PASS for documented core; gaps explicitly marked. |
| Automated test exists | Test file/case present in repository | PASS for many core/sales/contact-center/reports paths; existence is not execution. |
| Automated test executed | Command/log on exact `a7534e7` | NOT RUN by documentation-only constraint. |
| Migration verified | Clean/upgrade site migrated exact baseline | NOT RUN; historical PR #35 logs do not prove PR #38. |
| Build verified | Frontend production build exact baseline | NOT RUN; historical build evidence is pre-baseline. |
| Browser verified | Desktop/narrow and route actions | NOT RUN on baseline. |
| Role acceptance | Admin/Manager/two Sales/Guest/API | NOT RUN on baseline. |
| Live integration | SMTP/Zalo/PBX/Woo/n8n/Telegram/AI provider | Email has older evidence; all require baseline-specific verification; most are pending. |

### Focused source/test reconciliation — 28/11/2026

| Scope | Source/test evidence at `a7534e7` | Execution in this task |
| --- | --- | --- |
| CRM-03 | `useDoubleTDeals.js`, `DealsView.vue`, `dealsResource.test.mjs` cover reactive filters, reload, pagination and Contact/Company labels | NOT RUN |
| R2-02/R2-06/NEW-03/EXT-20/EXT-21/CC-02/CC-03 | Zalo workflow/inbox/OA, Conversation/Event/Message schemas, permission hooks and `test_zalo_inbox.py` cover MOCK lifecycle, scope, metrics, linking and idempotency | NOT RUN |
| CALL-02 | `call_log/ai_summary.py`, Note schema and `test_doublet_call_ai_summary.py` cover DEMO/LIVE separation, worker permission and unique next-steps Note | NOT RUN |

### Historical evidence retained

- 17/11: Quotation PDF email/inbound Communication evidence on earlier code; not baseline acceptance.
- 19/11 PR #25: Product Catalog/Quotation frontend focused evidence; save/reopen/role gaps remained.
- 24–25/11 PR #31–33: Reports focused tests/build/browser evidence; exact counts tied to earlier commits/data.
- 27/11 PR #35: reported frontend/build/migration and pre/post integration test evidence; backend full suite was not rerun after all integration according to checklist.
- 28/11 baseline `a7534e7` includes PR #36 Contact Center, PR #37 Deals fix và PR #38 modular docs; no runtime evidence was created in this documentation pass.

### Cross-module release test suites

1. Lead → Contact/Company/Deal → Quotation → Accepted Order with two customer types and two Sales users.
2. Product/Price precedence/zero/missing → Quotation snapshot → Catalog price change → Order snapshot.
3. Quotation approval → PDF/email queue → inbound Communication/reply/attachment permission.
4. Zalo MOCK duplicate → assign/transfer/accept/reply/resolve/reopen → record tab → response metric.
5. Missed Call → assignment → callback uniqueness/result → AI demo/live state → reviewed Note.
6. Task/Appointment reminder validation/idempotency/Notification Log.
7. Dashboard/Reports aggregate↔drill-down/export parity under restricted roles and unknown data.
8. Clean install/upgrade/rollback including DocTypes, patches, private files and matching assets.
9. Customer lifecycle: khách mới/cũ, Personal/Company, inbound duplicate/ambiguous, denied role và history không trộn giữa hai Deal.
