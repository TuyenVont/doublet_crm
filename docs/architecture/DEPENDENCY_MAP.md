# Cross-module Dependency Map

[← Documentation Index](../INDEX.md) · [Module Boundaries](MODULE_BOUNDARIES.md) · [Business Flow Contract](BUSINESS_FLOW_CONTRACT.md) · [Workflows](../workflows/README.md)

| Module nguồn | Module đích | Dữ liệu truyền | Quy tắc liên kết / trạng thái | Rủi ro khi thay đổi | Regression cần kiểm |
| --- | --- | --- | --- | --- | --- |
| M01 Lead | M02 Contact/Company | identity và converted links | Idempotent conversion; **đã có code** | Trùng khách, mất trace | Personal/Company, convert lặp |
| M01 Lead | M01 Deal | `source_lead`, customer context | Một conversion giữ đúng Deal; **đã có code** | Funnel sai, duplicate Deal | conversion + Journey |
| M02 Customer | M05 Pricing | Contact/Company `price_list` | Company trước Contact; **đã có code** | Báo sai giá | explicit/company/contact/default/fallback |
| M04 Product | M01 Deal | Product, qty, reference price | Current suggestion only; **đã có code** | Deal Amount/snapshot bị đổi | inactive/template/duplicate SKU |
| M04 Product | M06 Quotation | Product snapshot + live resolved price khi thêm mới | Template không bán; **đã có code** | Reprice lịch sử | save/reopen sau đổi Catalog |
| M04 Product | M07 Order | Product/item snapshot | New manual rows validate sellable; linked Order phải khớp Quote; **đã có code** | Order lệch Quote | manual và conversion |
| M01 Deal | M06 Quotation | customer, Deal products, source Lead | Link phải khớp customer; **đã có code** | Báo giá sai khách | Deal/list/Lead entry |
| M06 Quotation | M07 Order | Accepted snapshot | Unique Quotation; row lock; **đã có code** | Double order/race | concurrent create, totals |
| M09 Email | M01/M06 | Communication reference/thread | Exact reference and recipient; **đã có code một phần** | Email lẫn Deal/Quote | two Deals same customer, reply |
| M09 Conversation | M01/M02 | explicit Lead/Contact link | Create/Link/Change có permission, reason/audit; **đã có code MOCK** | Lộ hội thoại/sai khách | record membership, stale link, transfer |
| M09 Conversation | M01 Lead conversion | Conversation `lead` → converted customer links | Record chat truy theo Lead/converted chain; auto-create Lead **chưa triển khai** | Trùng Lead hoặc đứt lịch sử | new/returning/ambiguous identity, convert/reload |
| M09 Message | Inbox UI | deterministic Message ID, Conversation activity | Persistence có; realtime publish/subscription/merge **chưa triển khai** | Tin trùng, chậm, lộ event | duplicate/reconnect/load-more/transfer permission |
| M09 Conversation | M12 Integration audit | Message external ID, Conversation Event/request hash | Idempotent trong Zalo MOCK; inbound same-identity payload chưa được hash; **có một phần**, chưa phải sync log đa kênh | Replay sai payload, tưởng audit cục bộ là integration log | duplicate inbound/action, same ID khác identity/content |
| M10 Call | M02/M08 | Lead/Contact link, participant number, callback Task, next-steps Note | Chỉ Lead/Contact; DEMO/LIVE tách; `source_call_log` unique; **đã có code** | Nhân đôi follow-up, nhầm Company/Deal hoặc gửi DEMO ra provider | ambiguous phone, callback/relink, demo no-queue, live permission, stale Note |
| M08 Activity | M01/M02 | Dynamic reference | Chỉ 4 CRM entity; **đã có code** | Cross-record leak | two users/two records |
| M08 Task/Appointment | Frappe Notification | reminder payload | Row lock + sent marker; **đã có code** | Gửi lặp/bỏ sót | reschedule/terminal/concurrency |
| M01 Deal/M07 Order | M11 Reports | values and event dates | `won_on`, `lost_on`, `order_date`; **đã có code** | Metric semantic drift | aggregate=drill-down |
| M11 Smart Insights | M08 Task | alert source/reason | Explicit authorized action, active marker; **đã có code** | Task spam | concurrent create + stale alert |
| M02 Customer | M01 Deal | Contact/Company context | Related Deal list có; create-with-prefill **chưa có verified entry point** | Bắt nhập lại hoặc gắn sai Contact đại diện | Personal/Company/multiple contacts/denied role |
| M01/M02/M09/M10 | Customer history | exact source IDs và provenance | Các tab/projection có một phần; unified history **mục tiêu** | Trộn hai Deal, copy dữ liệu, lộ restricted row | two Deals/same customer, conversion, two roles |
| M12 Integration | M02 Identity | external ID/payload | Explicit mapping + audit; **kiến trúc mục tiêu** | Duplicate/mis-link | replay/ambiguous identity |
| M12 WooCommerce | M04/M07 | SKU, Variant, Customer, Order | Direction/source chưa chốt; **chưa triển khai** | Hai nguồn giá/order | repeat event/conflict |
| M12 n8n/Webhook | All | event/action/execution log | Signed, idempotent, retryable; **chưa triển khai** | Loop/duplicate action | event→action→log replay |
| M09 Contact Center | M11 Reports | Message/Conversation/first-response/waiting metrics | Metrics có source; SLA threshold và Email/Zalo attribution còn giới hạn; **có một phần** | KPI/SLA sai owner hoặc ép unknown thành 0 | future/missing timestamp, threshold, role scope |
| M03 Permission | All modules | authorized population/fields | Backend source of truth; **có một phần** | Data leak | list/detail/export/API parity |
