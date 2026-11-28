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
- **Record-level:** `permission_query_conditions` + `has_permission` cho Conversation, Message, Call Log, Call Event, Task và Appointment. Sales User chỉ thấy Conversation/Message được giao; Sales Manager/System Manager quản lý toàn hàng đợi. Appointment theo owner/assignee/share. Lead/Deal/Contact/Company chưa có hook owner/team tổng quát ở baseline.
- **Owner/assignee:** `owner`, `lead_owner`, `deal_owner`, `contact_owner`, `company_owner`, `assigned_to` không đồng nghĩa tự động giới hạn record nếu thiếu DocPerm/hook tương ứng.
- **Field-level:** `permlevel`, `read_only` và `has_field_permission`; backend phải kiểm tra khi trả field nhạy cảm. Ẩn nút frontend chỉ là UX.
- **API:** endpoint phải `check_permission`/`has_permission`, validate linked record và dùng `frappe.get_list` permission-scoped; Guest bị từ chối ở nghiệp vụ.
- **Private attachment:** Call recording/Quotation attachment phải là `File.is_private=1` khi nhạy cảm; API chỉ trả pointer sau khi kiểm quyền Call/Quotation/File. Không công khai `/private/files` bằng URL đoán được.

### Contact Center scope

- `DoubleT Conversation` và `DoubleT Message` có read DocPerm cho Sales roles nhưng permission hooks mới quyết định record thực tế: Sales User chỉ đọc thread được gán; manager roles đọc/quản lý toàn hàng đợi.
- Assign/transfer/list assignees chỉ dành cho Administrator, System Manager hoặc Sales Manager. Sales User được giao phải Accept trước khi reply; Resolved không reply cho đến khi inbound mới reopen.
- `DoubleT Conversation Event` mặc định chỉ System Manager đọc qua generic DocType. API `get_conversation_info` trả handling history sau khi đã kiểm quyền Conversation và chỉ lộ customer link mà caller đọc được.
- Realtime chat hiện chưa có event contract. Khi triển khai, publish/subscription không được thay HTTP authorization: payload tối thiểu, sau event client refetch qua API permission-scoped; transfer/revoke phải khiến user cũ ngừng nhận và đóng thread. Không publish preview/customer label vào room toàn cục.
- Cấu hình channel/team membership chưa có; danh sách assignee hiện lấy enabled System User mang một trong các role System Manager, Sales Manager hoặc Sales User.
- Call AI Summary tái kiểm quyền Call/assignee ở API và worker; lưu next steps còn cần quyền Note và quyền đọc customer/reference.

## 5.3 Permission risks

Rủi ro chính là nhầm default DocPerm với site policy, coi frontend gating là authorization, aggregate report vượt record scope, hoặc trả link/label của record không đọc được. Mọi nghiệm thu quyền cần tối thiểu Administrator, Sales Manager, hai Sales User khác owner/assignee và Guest/API principal phù hợp.

Các điểm kiểm quyền ở ranh giới điều hướng/create-from-record được quản lý tại [Business Flow Contract](BUSINESS_FLOW_CONTRACT.md); test denied-role tại [Cross-module Acceptance](../testing/CROSS_MODULE_ACCEPTANCE.md).
