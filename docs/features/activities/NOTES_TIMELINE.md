# Notes & Activity Timeline

[← activities index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-act-02"></a>
- `ACT-02` — Notes và Activities

## Mục đích nghiệp vụ

Notes và Activities. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| ACT-02 | Notes và Activities | R1 · Công việc | P0 | 23/11 · PR #28 (21aabe4, test 123fc4b) bổ sung regression giữ lịch sử Call Log liên kết Deal kiểu cũ, không lộ sang Lead khác; note/timeline có test trong main. Chưa có kết quả chạy lại test trên site bàn giao. | BA SCP-02 · Báo cáo 08–14/11 |

## Data Model

`DoubleT Task`, `DoubleT Note`, `DoubleT Appointment`, Dynamic Link tới Lead/Deal/Contact/Company và `Notification Log`.

Xem [Data Model](../../architecture/DATA_MODEL.md) và [Data Ownership](../../architecture/DATA_OWNERSHIP.md).

## Business Rules

Các validation riêng được xác định từ source/checklist trong bảng dưới đây; quy tắc xuyên module được quản lý tại [Data Ownership](../../architecture/DATA_OWNERSHIP.md) và [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Workflow và State Transitions

Tạo/assign activity → lifecycle → reminder/notification hoặc projection lên timeline.

Chi tiết end-to-end nằm ở mục Related Workflows; state không được suy ra từ nhãn UI nếu controller/schema quy định khác.

## Permissions

Owner/assignee/share và linked-record permission phải được kiểm ở backend.

Contract chung: [Permission Model](../../architecture/PERMISSION_MODEL.md).

## Source Mapping

| ID | Source reference | Bằng chứng mới trong checklist |
| --- | --- | --- |
| ACT-02 | SharedNotes.vue | 18/11 · 7105984 · SharedNotes.vue:293. Chưa test Sales User và timeline. |

## Upstream Dependencies

- CRM record, Call/Insight hoặc thao tác người dùng.
- [Calls](../contact-center/CALLS.md)
- [Customer](../crm/CUSTOMER.md)

## Downstream Impact

- Timeline, work queue, Notification và activity reports.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 06 CALL AI NOTE](../../workflows/WF_06_CALL_AI_NOTE.md)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| ACT-02 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| ACT-02 | Chạy test_doublet_note và UI Timeline ở Lead/Deal/Contact/Company bằng 2 Sales User; kiểm bản ghi Call Log Deal cũ, quyền, Notes CRUD và không trộn lịch sử khách khác. |

## Known Limitations

- **ACT-02:** Source có nhưng vẫn phải theo acceptance status.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
