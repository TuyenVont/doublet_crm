# Single Source of Truth & Data Ownership

[← Documentation Index](../INDEX.md) · [Data Model](DATA_MODEL.md) · [Dependency Map](DEPENDENCY_MAP.md)

| Nghiệp vụ | Source of truth | Không được dùng thay thế |
| --- | --- | --- |
| Cá nhân/doanh nghiệp | `DoubleT Contact`, `DoubleT Company` | Lead, Conversation hoặc integration payload như hồ sơ khách song song. |
| Prospect | `DoubleT Lead`; provenance ở `source` | Tạo Contact/Company ngầm khi chưa đủ căn cứ. |
| Cơ hội/pipeline | `DoubleT Deal` + `DoubleT Deal Stage.stage_type` | UI column label hoặc Dashboard cache. |
| Catalog | `DoubleT Product`/Category/Variant | Quotation snapshot làm giá hiện hành. |
| Giá hiện hành | Price resolution: explicit → Company → Contact → default → Product fallback | Reprice Quotation/Order đã lưu. |
| Báo giá | `DoubleT Quotation` + Items snapshot | Product/Price List sau thời điểm lưu. |
| Đơn hàng | `DoubleT Order` + Items snapshot | Quotation thay đổi sau tạo Order. |
| Email | Frappe `Communication`/`Email Queue` | Conversation/Message Zalo. |
| Hội thoại OA | `DoubleT Conversation` + `DoubleT Message`; Event là audit | Lead timeline copy hoặc UI local state. |
| Cuộc gọi | `DoubleT Call Log`; Event/AI Summary/Task/Note là dữ liệu dẫn xuất có link | File recording hoặc callback Task như call record chính. |
| Activity | Task/Note/Appointment/Communication/Call riêng; Activities là projection | Một bảng timeline song song. |
| Reports | Permission-scoped queries trên business source ở trên | Mock KPI, cached frontend totals hoặc unknown = 0. |

## Provenance và dữ liệu kế thừa

- Route/query context không phải source of truth. Destination chỉ sở hữu dữ liệu sau khi backend validate và Save; source link/snapshot phải còn sau reload.
- External OA identity (`source + oa_id + external_user_id`) xác định Conversation, chưa tự chứng minh một Lead/Contact. Automatic identity mapping là TO-BE và cần policy/audit riêng.
- Lead conversion sở hữu converted links; customer record không được ghi đè lịch sử Lead/Conversation. Deal sở hữu sales context; Quotation/Order sở hữu snapshot thương mại.
- Customer-history view chỉ projection Chat/Email/Call/Activity/Sales records được phép đọc. Không tạo bảng timeline song song và không suy diễn customer-level activity thành Deal-specific activity.

Xem [Business Flow Contract](BUSINESS_FLOW_CONTRACT.md) cho quy tắc Source/Context/Prefill/Persistence.
