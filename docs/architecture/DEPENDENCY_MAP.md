# Cross-module Dependency Map

[← Documentation Index](../INDEX.md) · [Module Boundaries](MODULE_BOUNDARIES.md) · [Workflows](../workflows/README.md)

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
| M09 Conversation | M01/M02 | explicit Lead/Contact link | No ambiguous auto-link; **đã có code MOCK** | Lộ hội thoại/sai khách | record membership, transfer |
| M10 Call | M02/M08 | Dynamic customer link, callback Task, next-steps Note | Unique callback/note; **đã có code** | Nhân đôi follow-up | missed call retry/relink |
| M08 Activity | M01/M02 | Dynamic reference | Chỉ 4 CRM entity; **đã có code** | Cross-record leak | two users/two records |
| M08 Task/Appointment | Frappe Notification | reminder payload | Row lock + sent marker; **đã có code** | Gửi lặp/bỏ sót | reschedule/terminal/concurrency |
| M01 Deal/M07 Order | M11 Reports | values and event dates | `won_on`, `lost_on`, `order_date`; **đã có code** | Metric semantic drift | aggregate=drill-down |
| M11 Smart Insights | M08 Task | alert source/reason | Explicit authorized action, active marker; **đã có code** | Task spam | concurrent create + stale alert |
| M12 Integration | M02 Identity | external ID/payload | Explicit mapping + audit; **kiến trúc mục tiêu** | Duplicate/mis-link | replay/ambiguous identity |
| M12 WooCommerce | M04/M07 | SKU, Variant, Customer, Order | Direction/source chưa chốt; **chưa triển khai** | Hai nguồn giá/order | repeat event/conflict |
| M12 n8n/Webhook | All | event/action/execution log | Signed, idempotent, retryable; **chưa triển khai** | Loop/duplicate action | event→action→log replay |
| M09 Contact Center | M11 Reports | Message/Conversation/response metrics | Email/Zalo agent attribution giới hạn; **có một phần** | KPI sai owner | unknown vs zero, role scope |
| M03 Permission | All modules | authorized population/fields | Backend source of truth; **có một phần** | Data leak | list/detail/export/API parity |
