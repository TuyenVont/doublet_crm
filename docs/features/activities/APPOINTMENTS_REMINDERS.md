# Appointment & Reminder

[← activities index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-ext-11"></a>
- `EXT-11` — Lịch hẹn và cuộc gặp gắn hồ sơ

## Mục đích nghiệp vụ

Lịch hẹn và cuộc gặp gắn hồ sơ. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| EXT-11 | Lịch hẹn và cuộc gặp gắn hồ sơ | R1 · Hoạt động | P1 | Appointment có lịch bắt đầu/kết thúc, liên kết hồ sơ, người phụ trách, trạng thái, danh sách và Reminder cho Appointment/Task. | Odoo · CRM CORE &APP A133 · MVP |

## Data Model

`DoubleT Task`, `DoubleT Note`, `DoubleT Appointment`, Dynamic Link tới Lead/Deal/Contact/Company và `Notification Log`.

Xem [Data Model](../../architecture/DATA_MODEL.md) và [Data Ownership](../../architecture/DATA_OWNERSHIP.md).

## Business Rules

**Tài liệu quản lý chính cho nhóm quy tắc này:** file hiện tại.

Task: `Backlog/Todo/In Progress/Done/Canceled`; Appointment: `Scheduled/Completed/Cancelled`. Dynamic Link chỉ Lead/Deal/Contact/Company. end ≥ start, reminder ≤ due/start. Thay schedule/assignee/status/reminder reset marker; scheduler khóa record và gửi Notification đúng một lần.

## Workflow và State Transitions

Tạo/assign activity → lifecycle → reminder/notification hoặc projection lên timeline.

Activity header route `AppointmentCreate` truyền `reference_doctype/reference_docname`; `AppointmentsView` prefill query này, backend vẫn phải validate source/allowlist. Save/reload phải giữ exact reference. Xem [BF-06](../../architecture/BUSINESS_FLOW_CONTRACT.md#bf-06--customer-record--tasknoteappointment).

Chi tiết end-to-end nằm ở mục Related Workflows; state không được suy ra từ nhãn UI nếu controller/schema quy định khác.

## Permissions

Owner/assignee/share và linked-record permission phải được kiểm ở backend.

Contract chung: [Permission Model](../../architecture/PERMISSION_MODEL.md).

## Source Mapping

| ID | Source reference | Bằng chứng mới trong checklist |
| --- | --- | --- |
| EXT-11 | doublet_task.json | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. |

## Upstream Dependencies

- CRM record, Call/Insight hoặc thao tác người dùng.
- [Tasks](TASKS.md)
- [Activity report](../analytics/ACTIVITY_CONTACT_CENTER.md)

## Downstream Impact

- Timeline, work queue, Notification và activity reports.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 08 ACTIVITY REMINDER](../../workflows/WF_08_ACTIVITY_REMINDER.md)
- [WF 11 CUSTOMER LIFECYCLE](../../workflows/WF_11_CUSTOMER_LIFECYCLE.md)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| EXT-11 | Có | Cần kiểm | Appointment/Reminder source tồn tại; checklist reference cũ; runtime acceptance pending. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| EXT-11 | Kiểm tạo/đổi/hủy lịch, quyền và scheduler gửi đúng một thông báo. |

## Known Limitations

- **EXT-11:** Source có nhưng vẫn phải theo acceptance status.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
