# Cross-module Workflow Gaps

[← Documentation Index](../INDEX.md) · [Known Gaps](KNOWN_GAPS.md) · [Business Flow Contract](../architecture/BUSINESS_FLOW_CONTRACT.md)

Đây là backlog review theo workflow, không thay Master Checklist và không tự nâng trạng thái. `Proposed ID` chỉ là nhãn tạm để thảo luận.

## Customer Identity & Conversion

| Gap | Ưu tiên đề xuất | Checklist / Proposed ID | Source evidence | AS-IS | TO-BE | Module ảnh hưởng | Acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Durable channel identity map | P0 | `CRM-06`, `R2-03`, `NEW-03`; Proposed `WF-ID-01` | `receive_mock_text`, Conversation `oa_id/external_user_id`; manual workflow | Conversation identity có, customer identity map chưa có | unique match link existing; new sufficient identity creates Lead; conflict waits review | Contact Center, CRM, Reports | ID-01, ID-03–ID-05 |
| Preserve conversion continuity | P0 | `CRM-02`, `CRM-05`, `EXT-03` | converted fields; `get_customer_details`; record chat lookup | Manual link + converted-chain projection có một phần | mở converted record và giữ Conversation/provenance | CRM, Contact Center, Activities | ID-01/02, HIST-03 |
| Company representative rule | P1 | `EXT-01`, `EXT-02`; Proposed `WF-ID-02` | one `Contact.company`; Deal validates membership | Một Contact–Company, một Deal Contact | explicit primary/role/multiple-company decision | CRM, Sales, Calls | ID-02, NAV-03, CALL-02 |

## Context Navigation

| Gap | Ưu tiên đề xuất | Checklist / Proposed ID | Source evidence | AS-IS | TO-BE | Module ảnh hưởng | Acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Contact/Company → Create Deal context | P1 | `CRM-04`, `CRM-09`; Proposed `WF-NAV-01` | customer pages only list linked Deals | Không có verified create entry | prefill exact customer; ask only on multiple contacts | CRM, Sales | NAV-03 |
| Consistent source-return context | P2 | `CRM-09`, `CRM-05`; Proposed `WF-NAV-02` | mixed route/query/hash conventions | Nhiều route link riêng | destination/return link contract thống nhất | All UI modules | NAV-01…NAV-06 |

## Sales Lifecycle

| Gap | Ưu tiên đề xuất | Checklist / Proposed ID | Source evidence | AS-IS | TO-BE | Module ảnh hưởng | Acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Baseline E2E evidence | P0 | `EXT-06`, `ORD-07`, `QA-01` | draft/order APIs + tests exist | Source implemented, acceptance pending | role/browser/concurrency persistence evidence | CRM, Sales, Reports | SALE-01…SALE-07 |
| Customer-wide Quote/Order history | P1 | `CRM-05`, `EXT-31` | Deal Quotations and customer related lists incomplete | Deal-specific views | readable customer projection with provenance | CRM, Sales | HIST-04 |

## Realtime Communication

| Gap | Ưu tiên đề xuất | Checklist / Proposed ID | Source evidence | AS-IS | TO-BE | Module ảnh hưởng | Acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Permission-safe chat realtime | P0 | `R2-02`, `EXT-19`, `CC-03`; Proposed `WF-RT-01` | global socket exists; no Zalo publish/subscription | Manual/local refresh only | after-commit event + permission-scoped refetch | Contact Center, Platform | RT-01, RT-04, RT-05 |
| Client dedupe/reconnect | P0 | `R2-06`; Proposed `WF-RT-02` | deterministic message ID; load older prepends | No realtime merge contract | merge stable IDs across event/history/reconnect | Contact Center | RT-02–RT-04 |
| LIVE provider boundary | P0 | `R2-01`, `R2-02` | MOCK API/replies only | MOCK | signed webhook, outbound delivery/reconciliation | Integration, Contact Center | RT-06 + provider suite |

## Customer History

| Gap | Ưu tiên đề xuất | Checklist / Proposed ID | Source evidence | AS-IS | TO-BE | Module ảnh hưởng | Acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Unified permission-scoped history | P1 | `CRM-05`, `EXT-31`; Proposed `WF-HIST-01` | separate Activity/Zalo/related tabs | Nguồn rời, một số projection | one view with source/scope/completeness | CRM, Activities, Contact Center, Sales | HIST-01…HIST-05 |
| Deal vs customer scope | P0 | `ACT-02`, `CRM-05`; Proposed `WF-HIST-02` | exact Dynamic Links; same customer may have many Deals | Exact source is safe, aggregation undefined | explicit scope prevents cross-Deal blend | CRM, Activities, Reports | HIST-02 |

## Permissions & Data Integrity

| Gap | Ưu tiên đề xuất | Checklist / Proposed ID | Source evidence | AS-IS | TO-BE | Module ảnh hưởng | Acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Realtime authorization parity | P0 | `CRM-07`, `EXT-27`, `CC-03`; Proposed `WF-PERM-01` | HTTP hooks exist; no event channel contract | HTTP permission-scoped | event/list/detail/export same population | Platform, Contact Center | RT-05, HIST-05 |
| Call participant/customer model | P1 | `CALL-01`, `CC-10`; Proposed `WF-CALL-01` | allowlist Lead/Contact; number + agent | No customer type/Company/Deal context fields | decide participant, customer, Company/Deal relationships | Calls, CRM, Activities | CALL-01/02/04 |
| Same message ID, changed payload | P0 | `R2-06`; Proposed `WF-IDEMP-01` | duplicate checks conversation/direction only | content/timestamp conflict not compared | reject/audit approved payload conflict policy | Contact Center, Integration | RT-02 plus changed-payload negative case |

## Quyết định cần người dùng xác nhận

1. Tiêu chí “external identity đủ rõ” để automatic Lead và nguồn nào được tin cậy.
2. Company trong Call là customer context dẫn xuất qua Contact hay link độc lập; Deal có cần context riêng không.
3. Realtime fallback: chu kỳ polling/focus refresh, retention/cursor và payload tối thiểu.
4. Customer-history mặc định theo customer hay theo current Deal; cách hiển thị restricted/unknown rows.
5. UX `Contact/Company → Create Deal` và rule chọn Contact đại diện khi có nhiều hồ sơ.
