# Follow-up Automation

[← automation index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-new-02"></a>
- `NEW-02` — Nhắc follow-up Deal và báo giá sắp hết hạn

## Mục đích nghiệp vụ

Nhắc follow-up Deal và báo giá sắp hết hạn. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| NEW-02 | Nhắc follow-up Deal và báo giá sắp hết hạn | Đề xuất sau khi lõi đạt | P2 | Dashboard có danh sách follow-up, Tasks có ngày đến hạn. REP-09 đề xuất hiển thị cảnh báo hành động ngay trên Reports; mục NEW-02 riêng cho tự tạo Task/nhắc tự động, tránh triển khai trùng. | Đề xuất từ review code · BA SC-07 |

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
| NEW-02 | dashboard.py | Chưa có bằng chứng mới |

## Upstream Dependencies

- Lead/Deal/Insight events và configuration.
- [Smart Insights](../analytics/SMART_INSIGHTS.md)
- [Tasks](../activities/TASKS.md)

## Downstream Impact

- Assignment, Task, notification và integration.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 09 SMART INSIGHTS FOLLOW UP](../../workflows/WF_09_SMART_INSIGHTS_FOLLOW_UP.md)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| NEW-02 | Đề xuất | Đề xuất | Checklist: Đề xuất; Đề xuất. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| NEW-02 | Khi Smart Insights (REP-09) có cảnh báo, bổ sung tự tạo một Task đúng owner vào mốc tới hạn, chống lặp khi chạy workflow và cho mở lại hồ sơ nguồn. |

## Known Limitations

- **NEW-02:** Dashboard có danh sách follow-up, Tasks có ngày đến hạn. REP-09 đề xuất hiển thị cảnh báo hành động ngay trên Reports; mục NEW-02 riêng cho tự tạo Task/nhắc tự động, tránh triển khai trùng.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
