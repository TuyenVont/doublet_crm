# Ranh giới module: Core và Apps

[← Documentation Index](../INDEX.md) · [Kiến trúc](SYSTEM_ARCHITECTURE.md) · [Dependency Map](DEPENDENCY_MAP.md)

| Nhóm | Thành phần | Ranh giới trách nhiệm |
| --- | --- | --- |
| Frappe infrastructure | User/Role/DocPerm/Custom DocPerm, ORM, Communication, File, Notification Log, Email Queue, Redis/queue/scheduler, Version/Comment | Tái sử dụng; không fork/sửa core. |
| DoubleT CRM Core | Lead, Contact, Company, Deal, Deal Stage, Task, Note, shared Activities, permission helpers | Hồ sơ, pipeline và hoạt động CRM. |
| DoubleT business | Product/Category/Variant, Price List/Settings, Quotation/Template/Approval, Order | Catalog-to-cash và snapshot thương mại. |
| Integration | Zalo adapter/inbox, quotation email, Call Log ingestion, BeeKnoee client | Biên provider; không nhúng logic provider vào core entity. |
| Automation | Reminder scheduler, Smart Insights follow-up, future webhook/n8n | Trigger có idempotency và audit; không tạo nguồn dữ liệu song song. |
| Analytics | Dashboard, Reports, export/saved filters, Stage Aging/Health | Chỉ aggregate tập record đã được permission engine cho phép. |

Đây là các module nghiệp vụ trong **một Frappe app** `doublet_crm`, không phải đề xuất tách thành nhiều Frappe app/repository. Chỉ cân nhắc tách vật lý khi có lifecycle/deployment/ownership độc lập đã được xác nhận.

## Ánh xạ 14 module nghiệp vụ vào cây tài liệu

Tám thư mục `features/` là nhóm điều hướng; 14 module dưới đây vẫn là ranh giới nghiệp vụ và checklist logic, không phải 14 Frappe app độc lập.

| Module | Trách nhiệm | Tài liệu chính |
| --- | --- | --- |
| M01 — CRM Core | Lead, conversion, Deal, pipeline | [CRM](../features/crm/README.md) |
| M02 — Customer Management | Contact, Company, Customer 360, identity | [Customer](../features/crm/CUSTOMER.md) |
| M03 — User & Permission | Role, record/field scope | [Permissions](../features/crm/PERMISSIONS.md) |
| M04 — Product Catalog | Category, Standard, Template, Variant | [Product Catalog](../features/sales/PRODUCT_CATALOG.md) |
| M05 — Pricing | Price List, settings, resolution | [Pricing](../features/sales/PRICING.md) |
| M06 — Quotation Management | Draft-to-acceptance, snapshot, approval, email | [Quotation](../features/sales/QUOTATION.md) |
| M07 — Order Management | Manual/conversion Order và lifecycle | [Order](../features/sales/ORDER.md) |
| M08 — Sales Activities | Task, Note, Appointment, Reminder | [Activities](../features/activities/README.md) |
| M09 — Contact Center & Communication | Email, Inbox, Conversation/Message | [Contact Center](../features/contact-center/README.md) |
| M10 — Call Management | Call queue, recording, AI summary, callback | [Calls](../features/contact-center/CALLS.md) |
| M11 — Dashboard & Reports | KPI, analytics, export, insights | [Analytics](../features/analytics/README.md) |
| M12 — Integration & Automation | Woo, webhook/n8n, external channel, assignment | [Integration](../features/integration/README.md) và [Automation](../features/automation/README.md) |
| M13 — Advanced CRM | Stage requirements, playbook, multi-pipeline, recurrence | [Advanced CRM](../features/crm/ADVANCED_CRM.md) |
| M14 — Platform & Quality | Standalone, UX, extensibility, QA/deployment | [Platform](../features/platform/README.md) |
