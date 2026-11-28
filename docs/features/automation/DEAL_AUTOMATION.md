# Deal Event Automation

[← automation index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-ext-29"></a>
- `EXT-29` — Tạo hoạt động khi Deal vào stage

## Mục đích nghiệp vụ

Tạo hoạt động khi Deal vào stage. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| EXT-29 | Tạo hoạt động khi Deal vào stage | Nâng cấp · Tự động hóa | P2 | Đã có đổi stage và Tasks. Chưa thấy rule tạo hoạt động một lần khi đổi stage. | Bitrix24 · CRM CORE &APP A252:A257 · sau n8n nền |

## Data Model

CRM event/evidence, configurable rule, deterministic idempotency key, action result và audit log.

Xem [Data Model](../../architecture/DATA_MODEL.md) và [Data Ownership](../../architecture/DATA_OWNERSHIP.md).

## Business Rules

Các validation riêng được xác định từ source/checklist trong bảng dưới đây; quy tắc xuyên module được quản lý tại [Data Ownership](../../architecture/DATA_OWNERSHIP.md) và [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Workflow và State Transitions

Event → rule evaluation → authorized action → execution result/retry.

Chi tiết end-to-end nằm ở mục Related Workflows; state không được suy ra từ nhãn UI nếu controller/schema quy định khác.

## Permissions

Rule configuration theo Manager; action principal không bypass permission.

Contract chung: [Permission Model](../../architecture/PERMISSION_MODEL.md).

## Source Mapping

| ID | Source reference | Bằng chứng mới trong checklist |
| --- | --- | --- |
| EXT-29 | hooks.py | Chưa có bằng chứng mới |

## Upstream Dependencies

- Lead/Deal/Insight events và configuration.
- [Deal](../crm/DEAL_PIPELINE.md)
- [Webhook/n8n](../integration/WEBHOOK_N8N.md)

## Downstream Impact

- Assignment, Task, notification và integration.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 10 N8N AUTOMATION](../../workflows/WF_10_N8N_AUTOMATION.md)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| EXT-29 | Chưa thấy | Đề xuất | Checklist: Chưa thấy; Đề xuất. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| EXT-29 | Vào stage đã chọn thì tạo đúng một Task. Gửi lại cùng event và đối chiếu log xử lý. |

## Known Limitations

- **EXT-29:** Đã có đổi stage và Tasks. Chưa thấy rule tạo hoạt động một lần khi đổi stage.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
