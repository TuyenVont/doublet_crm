# Website Lead, Telegram & AI Agent

[← integration index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-r3-03"></a>
- `R3-03` — Thông báo Telegram từ workflow
<a id="feature-r3-04"></a>
- `R3-04` — AI hỗ trợ một tình huống tư vấn/chăm sóc
<a id="feature-ext-24"></a>
- `EXT-24` — Nhận Lead từ form website

## Mục đích nghiệp vụ

Thông báo Telegram từ workflow; AI hỗ trợ một tình huống tư vấn/chăm sóc; Nhận Lead từ form website. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| R3-03 | Thông báo Telegram từ workflow | R3 · Thông báo | P1 | BA xếp trong R3. Chưa thấy triển khai Telegram trong main. | BA SCP-09, R3 |
| R3-04 | AI hỗ trợ một tình huống tư vấn/chăm sóc | R3 · AI Agent | P1 | Đề cương và BA phạm vi đưa AI Agent vào hướng tích hợp. BA phần ưu tiên ghi mức thấp/tùy chọn. Chưa thấy luồng AI có thể xác minh trên main. | Đề cương · BA SCP-13, R3, mục 8.3 |
| EXT-24 | Nhận Lead từ form website | Nâng cấp · Nguồn Lead | P2 | Có Lead Source và form trong CRM. Chưa thấy web form ghi Lead website trong snapshot. | Odoo · CRM CORE &APP A14 · Future |

## Data Model

Target/source IDs, signed request/event envelope, idempotency key và execution/audit record; business entity vẫn là source of truth.

Xem [Data Model](../../architecture/DATA_MODEL.md) và [Data Ownership](../../architecture/DATA_OWNERSHIP.md).

## Business Rules

Các validation riêng được xác định từ source/checklist trong bảng dưới đây; quy tắc xuyên module được quản lý tại [Data Ownership](../../architecture/DATA_OWNERSHIP.md) và [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Workflow và State Transitions

Authenticate/verify → deduplicate → map identity → upsert/action → log/retry/DLQ.

Chi tiết end-to-end nằm ở mục Related Workflows; state không được suy ra từ nhãn UI nếu controller/schema quy định khác.

## Permissions

Least-privilege integration principal, protected secrets, signature và action-level backend checks.

Contract chung: [Permission Model](../../architecture/PERMISSION_MODEL.md).

## Source Mapping

| ID | Source reference | Bằng chứng mới trong checklist |
| --- | --- | --- |
| R3-03 | hooks.py | Chưa có bằng chứng mới |
| R3-04 | hooks.py | Chưa có bằng chứng mới |
| EXT-24 | hooks.py | Chưa có bằng chứng mới |

## Upstream Dependencies

- External provider và integration configuration.
- [Webhook/n8n](WEBHOOK_N8N.md)
- [Lead](../crm/LEAD.md)

## Downstream Impact

- Customer/Lead/Order, notification và automation.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 10 N8N AUTOMATION](../../workflows/WF_10_N8N_AUTOMATION.md)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| R3-03 | Chưa thấy | Cần làm | Checklist: Chưa thấy; Cần làm. Không suy ra runtime PASS. |
| R3-04 | Chưa thấy | Cần chốt | Checklist: Chưa thấy; Cần chốt. Không suy ra runtime PASS. |
| EXT-24 | Chưa thấy | Đề xuất | Checklist: Chưa thấy; Đề xuất. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| R3-03 | Chọn một sự kiện demo, gửi qua bot test và kiểm đích nhận, liên kết hồ sơ, hành vi khi workflow chạy lặp. |
| R3-04 | Chốt mức demo dựa trên BA, chọn một kịch bản nhỏ như gợi ý trả lời OA có nhân viên duyệt. Ghi dữ liệu đầu vào và cách đánh giá kết quả. |
| EXT-24 | Gửi form demo, tạo Lead kèm nguồn. Thử thiếu thông tin và gửi trùng theo quy tắc định danh. |

## Known Limitations

- **R3-03:** BA xếp trong R3. Chưa thấy triển khai Telegram trong main.
- **R3-04:** Đề cương và BA phạm vi đưa AI Agent vào hướng tích hợp. BA phần ưu tiên ghi mức thấp/tùy chọn. Chưa thấy luồng AI có thể xác minh trên main.
- **EXT-24:** Có Lead Source và form trong CRM. Chưa thấy web form ghi Lead website trong snapshot.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
