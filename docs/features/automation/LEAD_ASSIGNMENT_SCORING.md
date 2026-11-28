# Lead Assignment & Scoring

[← automation index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-r3-02"></a>
- `R3-02` — Chấm điểm Lead và tạo Task theo dõi
<a id="feature-ext-23"></a>
- `EXT-23` — Tự gán Lead theo nguồn hoặc nhóm

## Mục đích nghiệp vụ

Chấm điểm Lead và tạo Task theo dõi; Tự gán Lead theo nguồn hoặc nhóm. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| R3-02 | Chấm điểm Lead và tạo Task theo dõi | R3 · n8n | P1 | Có Lead và Task thủ công. Chưa có bằng chứng luồng chấm điểm/tạo Task tự động của DoubleT hiện tại. | Đề cương · BA SC-07, SM-06 |
| EXT-23 | Tự gán Lead theo nguồn hoặc nhóm | Nâng cấp · Tự động hóa | P2 | Có owner và API người phụ trách. Chưa thấy rule phân Lead tự động trên DoubleT. | Odoo · CRM CORE &APP A16, A256 · Future |

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
| R3-02 | doublet_lead.json | Chưa có bằng chứng mới |
| EXT-23 | api.py | Chưa có bằng chứng mới |

## Upstream Dependencies

- Lead/Deal/Insight events và configuration.
- [Lead](../crm/LEAD.md)
- [Permissions](../crm/PERMISSIONS.md)

## Downstream Impact

- Assignment, Task, notification và integration.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- Xem [workflow index](../../workflows/README.md); chưa có workflow riêng cho mục này.

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| R3-02 | Chưa thấy | Cần làm | Checklist: Chưa thấy; Cần làm. Không suy ra runtime PASS. |
| EXT-23 | Có một phần | Đề xuất | Checklist: Có một phần; Đề xuất. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| R3-02 | Chọn quy tắc scoring có thể giải thích, tạo Task theo điều kiện phù hợp và lưu lý do. Chạy hai ca đạt/không đạt. |
| EXT-23 | Tạo Lead từ nguồn đã chọn và xem được gán đúng người. Có người dự phòng và cho đổi lại. |

## Known Limitations

- **R3-02:** Có Lead và Task thủ công. Chưa có bằng chứng luồng chấm điểm/tạo Task tự động của DoubleT hiện tại.
- **EXT-23:** Có owner và API người phụ trách. Chưa thấy rule phân Lead tự động trên DoubleT.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
