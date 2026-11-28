# Tổng quan hệ thống

[← Documentation Index](../INDEX.md) · [Kiến trúc](SYSTEM_ARCHITECTURE.md) · [Ranh giới module](MODULE_BOUNDARIES.md)

<a id="document-control"></a>
## Kiểm soát tài liệu

| Thuộc tính | Giá trị |
| --- | --- |
| Baseline source | `a7534e74090f46498f5cbfcd30e0fcf77d882f2e` — merge PR #38, remote `origin/main` xác minh ngày 28/11/2026 |
| Branch tài liệu | `docs/reconcile-baseline-20261128` |
| Master Checklist | Google Sheets `KLTN · Đối chiếu bản cuối`, 110 mã, đọc ngày 28/11/2026 |
| Nguồn nghiệp vụ | Business Analysis ngày 24/10/2026; Development Rules; NOTES; source và tài liệu repository |
| Graphify | Root/frontend tạo ngày 25/11/2026; hữu ích để định vị, nhưng có generated/minified nodes và cũ hơn baseline nên mọi kết luận được đối chiếu source |
| Mức xác minh | Documentation-only: source verified; không chạy test, build, migration, browser hoặc live integration trong lượt này |

Quy ước trạng thái:

- **Implemented — source verified**: có schema/controller/API/UI tương ứng tại baseline; chưa đồng nghĩa đã nghiệm thu runtime.
- **Partial**: có một phần contract hoặc luồng, còn thiếu thành phần cần thiết.
- **Target architecture**: yêu cầu đã xác định nhưng chưa có implementation tại baseline.
- **Not implemented**: không tìm thấy implementation có thể xác minh.
- **Acceptance pending**: thiếu bằng chứng chạy trên baseline/role/browser/site/live integration.
- **Historical evidence**: bằng chứng có commit, PR hoặc ngày nhưng không được dùng để khẳng định baseline hiện tại PASS.

## Bối cảnh và phạm vi

DoubleT CRM là custom Frappe application độc lập phục vụ bán hàng và chăm sóc khách hàng đa kênh. Vấn đề nghiệp vụ gốc là thông tin của cùng một khách hàng nằm rời rạc giữa CRM, Zalo OA, Email, WooCommerce và quy trình thủ công; người dùng phải nhập lại, đối chiếu và chuyển ứng dụng để theo dõi hành trình khách hàng.

Hệ thống hướng tới một hồ sơ CRM có thể truy vết từ tương tác ban đầu đến `DoubleT Lead`, `DoubleT Contact`/`DoubleT Company`, `DoubleT Deal`, `DoubleT Quotation` và `DoubleT Order`; Frappe cung cấp identity, permission, ORM, Communication, File, queue, scheduler và Notification.

Chuỗi trên được chuẩn hóa bằng [End-to-End Business Flow Contract](BUSINESS_FLOW_CONTRACT.md): mỗi chuyển tiếp phải nêu Source, Trigger, Destination, Context, Prefill, Validation, Persistence, Exception và Acceptance; AS-IS không được trộn với TO-BE/GAP.

**Người dùng chính:** Administrator, System Manager, Sales Manager, Sales User; các integration principal như `Call Log API`; người quản lý xem Dashboard/Reports. Khách hàng không đăng nhập CRM nhưng tương tác qua Email/Zalo/call/commerce.

**Phạm vi hiện tại đã có source:** CRM core, Catalog/Pricing, Quotation/Order, Task/Note/Appointment/Reminder, Email theo Communication, Zalo OA MOCK Inbox và record chat, Calls queue/Callback/AI Call Assistant, Dashboard và sáu Reports.

**Phạm vi chưa hoàn chỉnh:** Customer 360 xuyên kênh, identity mapping/merge, Email Inbox chung, record scope toàn bộ CRM, localization và clean standalone install acceptance.

**Phạm vi mục tiêu/chưa có live verification:** Zalo OA LIVE, WooCommerce, PBX/SIP, n8n/Webhook platform, Telegram, website Lead, AI Business Insights và AI Agent. Các mục này không được mô tả như đang vận hành thực tế.


## Mục tiêu nghiệp vụ và phạm vi

## 2.1 Nguồn Business Analysis và mục tiêu

Business Analysis xác định năm mục tiêu:

| ID | Business Objective | Success Metric |
| --- | --- | --- |
| BO-01 | Tập trung thông tin khách hàng thuộc scope vào hồ sơ CRM truy xuất thống nhất. | SM-01: thông tin thuộc test scenario truy xuất từ CRM. |
| BO-02 | Đồng bộ và liên kết đúng dữ liệu kênh ngoài với khách hàng. | SM-02/03: 100% valid test case sync và match đúng. |
| BO-03 | Giảm nhập lại/đối chiếu thủ công. | SM-04: giảm số bước so với As-Is. |
| BO-04 | Truy vết Interaction → Lead → Deal → Order. | SM-05: 100% scenario thuộc scope truy vết được. |
| BO-05 | Tạo nền dữ liệu/workflow nhất quán cho automation. | SM-06: 100% valid automation test case thực thi đúng. |

Các mục tiêu trên là yêu cầu ban đầu; mức đạt phải được chứng minh bằng test scenario, không suy ra từ việc có file source.

## 2.2 Functional Requirements BA

BA có 32 `FR`: FR-01–06 hồ sơ/lịch sử khách hàng; FR-07–12 Zalo OA và Lead; FR-13–16 WooCommerce Order; FR-17–23 duplicate/identity mapping; FR-24–28 Dashboard/pipeline/drill-down; FR-29–32 permission, source provenance và audit trail. Checklist 110 mã là lớp phân rã triển khai/đề xuất chi tiết hơn, không thay thế mã FR.

## 2.3 Release và scope reconciliation

| Release BA | Nội dung | Hiện trạng baseline |
| --- | --- | --- |
| R1 — Core CRM | Contact, Lead, Deal, Task/Activity, Permission, Dashboard | Source rộng hơn R1: có Catalog, Pricing, Quotation, Order, Reports; acceptance role/browser chưa đầy đủ. |
| R2 — External Integration | Zalo OA, WooCommerce, Email | Email theo hồ sơ/báo giá và Zalo MOCK có source; Email Inbox, Zalo LIVE, WooCommerce chưa hoàn chỉnh. |
| R3 — Workflow Automation | n8n, trigger/API, Telegram, AI Agent | Smart Insights rule-based và reminder có source; integration platform/Telegram/AI Agent chưa triển khai. |
| Future Increment | Contact Center/FusionPBX | Internal Calls/Contact Center đã có source sau BA; PBX/SIP thật vẫn là target. |

BA có mâu thuẫn cần giữ nguyên để chốt phạm vi: `SCP-13 AI Agent` vừa được ghi In Scope/R3, vừa được xếp Future/Optional; `SCP-12 Contact Center` từng là Future nhưng source hiện đã có internal Contact Center. Tài liệu này không tự quyết định hai điểm đó.

## 2.4 In/Out/Future

- In scope đã xác định: `SCP-01` CRM, `SCP-02` Activity, `SCP-03` Permission, `SCP-04` Dashboard/Reporting, `SCP-05` Zalo, `SCP-06` WooCommerce, `SCP-07` Email, `SCP-08` n8n, `SCP-09` Telegram và AI tùy quyết định phạm vi.
- Out of scope: sửa Frappe core; thay thế Zalo OA/WooCommerce; bắt buộc phụ thuộc Frappe CRM/ERPNext.
- Chưa xác nhận: AI Agent bắt buộc hay optional; live provider/môi trường; rule identity/merge; team scope; paid revenue source; clean-install release gate.
