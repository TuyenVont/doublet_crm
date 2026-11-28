# Known Gaps

[← Documentation Index](../INDEX.md) · [Feature Status](FEATURE_STATUS.md) · [Dependency Map](../architecture/DEPENDENCY_MAP.md)

| Gap | Source finding | Required completion/evidence |
| --- | --- | --- |
| Customer 360 | Record Activities exist; no unified all-channel customer page | One permission-scoped view with Lead/Deal/Quote/Order/Email/Zalo/Call completeness states. |
| Identity mapping/duplicate | Email/phone warnings only | Approved match rules, ambiguous queue, provenance and audit. |
| Contact↔many Company | Single `Contact.company` | Explicit relationship/role model; preserve primary company. |
| Customer Quote/Order history | Deal quote tab; customer-wide history incomplete | Contact/Company tabs with authorized filter/link. |
| Email Contact Center Inbox | Communication tabs exist; Inbox is Zalo-only | All/linked/unlinked queue, reply/create/link Lead. |
| Zalo LIVE | MOCK only | Provider credentials, signature, token renewal, outbound status and live test. |
| Conversation lifecycle | Checklist CC-02/EXT-20/21 stale; PR #36 source has lifecycle/transfer/metrics | Migration + backend/browser role acceptance; Google Sheet remains unchanged. |
| PBX/SIP | Generic Call ingestion/internal queue only | Vendor adapter and real inbound/outbound/recording tests. |
| WooCommerce | No verified integration code | Direction, identity/SKU conflict, retry/log and provider test. |
| Webhook/n8n/Telegram | No platform/workflow export | Signed dispatch, action scope, execution log and replay. |
| AI Business Insights | REP-13 unmerged historical evidence only | Merge-reviewed source, migration, live provider and grounded KPI acceptance. |
| Record-level CRM permission | Hooks only for Calls/Conversation/Task/Appointment | Decide/enforce Lead/Deal/Contact/Company owner/team scope; test Custom DocPerm. |
| Standalone install | `pyproject` has no Frappe CRM/ERPNext dependency, but inherited `crm.*`/`crm.fcrm.*`/optional ERPNext references remain in frontend | Clean site with only Frappe + DoubleT; remove/gate runtime-breaking inherited calls. |
| Localization | translation boot exists, UI mixed English/Vietnamese | Confirm language scope and browser/PDF verification. |
| Team/report attribution | no Deal team schema; Email/Zalo employee attribution incomplete | Keep unknown/unavailable explicit or add approved model. |

## Checklist IDs chưa có implementation contract phù hợp

Các ID gồm `R2-05`, `R3-01`–`R3-05`, `EXT-24`, `EXT-29`, `EXT-02`–`EXT-04`, `EXT-17`, `EXT-18`, `EXT-30`, `EXT-34`, `EXT-22`, `CC-01`, `CC-04`–`CC-09`, `NEW-01`, `NEW-03` và phần automatic của `NEW-02`. Source reference trong checklist chỉ là điểm tích hợp dự kiến, không phải bằng chứng triển khai.

## Nội dung chưa thể xác minh trong task tài liệu

- Runtime test/build/migration/browser trên exact baseline.
- Custom DocPerm và dữ liệu site thực tế ngoài source default.
- Live SMTP delivery, Zalo OA, PBX/SIP, WooCommerce, n8n, Telegram và AI provider.
- Clean installation chỉ có Frappe + DoubleT CRM.
