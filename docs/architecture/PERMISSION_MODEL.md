# User Roles & Permission Model

[← Documentation Index](../INDEX.md) · [Data Model](DATA_MODEL.md) · [CRM permissions](../features/crm/PERMISSIONS.md)

## 5.1 Role

| Role/principal | Quyền dự kiến và giới hạn source |
| --- | --- |
| Administrator | Bypass quản trị Frappe; vẫn phải dùng cho vận hành có kiểm soát. |
| System Manager | CRUD rộng theo DocPerm; quản lý Calls/Conversations và cấu hình. |
| Sales Manager | Mặc định nhiều CRM master chỉ read; Quotation/Order/Catalog có quyền rộng hơn; được quản lý Calls/Conversations và discount settings qua API hẹp. |
| Sales User | Quyền mặc định không đồng nhất: Product/Quotation/Order có create/write; Lead/Deal/Contact/Company/Task chủ yếu read. Site `Custom DocPerm` có thể thay thế các dòng mặc định. |
| Call Log Viewer | Read Call Log toàn cục theo permission hook. |
| Call Log API | Chỉ create Call Log qua integration contract; không mặc nhiên có read. |

## 5.2 Các lớp kiểm soát

- **DocType permission:** JSON `permissions`; site có thể có `Custom DocPerm`, nên source default và runtime site phải báo cáo riêng.
- **Record-level:** `permission_query_conditions` + `has_permission` cho Conversation, Message, Call Log, Call Event, Task và Appointment. Sales User chỉ thấy conversation/call được giao; Appointment theo owner/assignee/share. Lead/Deal/Contact/Company chưa có hook owner/team tổng quát ở baseline.
- **Owner/assignee:** `owner`, `lead_owner`, `deal_owner`, `contact_owner`, `company_owner`, `assigned_to` không đồng nghĩa tự động giới hạn record nếu thiếu DocPerm/hook tương ứng.
- **Field-level:** `permlevel`, `read_only` và `has_field_permission`; backend phải kiểm tra khi trả field nhạy cảm. Ẩn nút frontend chỉ là UX.
- **API:** endpoint phải `check_permission`/`has_permission`, validate linked record và dùng `frappe.get_list` permission-scoped; Guest bị từ chối ở nghiệp vụ.
- **Private attachment:** Call recording/Quotation attachment phải là `File.is_private=1` khi nhạy cảm; API chỉ trả pointer sau khi kiểm quyền Call/Quotation/File. Không công khai `/private/files` bằng URL đoán được.

## 5.3 Permission risks

Rủi ro chính là nhầm default DocPerm với site policy, coi frontend gating là authorization, aggregate report vượt record scope, hoặc trả link/label của record không đọc được. Mọi nghiệm thu quyền cần tối thiểu Administrator, Sales Manager, hai Sales User khác owner/assignee và Guest/API principal phù hợp.
