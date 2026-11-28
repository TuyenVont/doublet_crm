# Task & Work Queue

[← activities index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-act-01"></a>
- `ACT-01` — Tasks và phân công
<a id="feature-ext-10"></a>
- `EXT-10` — Bộ lọc Task theo ngày đến hạn
<a id="feature-ext-12"></a>
- `EXT-12` — Hàng đợi việc cần xử lý cho Sales
<a id="feature-ext-34"></a>
- `EXT-34` — Bộ đếm Task quá hạn trên thẻ Deal

## Mục đích nghiệp vụ

Tasks và phân công; Bộ lọc Task theo ngày đến hạn; Hàng đợi việc cần xử lý cho Sales; Bộ đếm Task quá hạn trên thẻ Deal. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| ACT-01 | Tasks và phân công | R1 · Công việc | P0 | 23/11 · PR #27 (218cdef) bổ sung callback_call_log trên Task, Callback Task liên kết Call Log và test quyền cập nhật callback. Tasks CRUD/My Tasks có từ trước; chưa chứng minh test mới đã chạy trên môi trường bàn giao. | BA SCP-02 · Báo cáo 08–14/11 |
| EXT-10 | Bộ lọc Task theo ngày đến hạn | R1 · Hoạt động | P1 | Tasks.vue đã có Overdue, Due Today và Upcoming, lọc theo ngày đến hạn. | CRM CORE &APP A128:A131 · MVP |
| EXT-12 | Hàng đợi việc cần xử lý cho Sales | Nâng cấp · Hoạt động | P2 | My Tasks có lọc. Chưa thấy hàng đợi để xử lý lần lượt nhiều bản ghi. | HubSpot · Liên quan ACT-01, NEW-02 |
| EXT-34 | Bộ đếm Task quá hạn trên thẻ Deal | Nâng cấp · Hoạt động | P2 | Tasks có lọc quá hạn. Kanban Deal chưa thấy bộ đếm hoạt động đến hạn theo từng thẻ. | Bitrix24 · Nối ACT-01 và CRM-03 |

## Data Model

`DoubleT Task`, `DoubleT Note`, `DoubleT Appointment`, Dynamic Link tới Lead/Deal/Contact/Company và `Notification Log`.

Xem [Data Model](../../architecture/DATA_MODEL.md) và [Data Ownership](../../architecture/DATA_OWNERSHIP.md).

## Business Rules

Quy tắc dùng chung được quản lý tại [Appointment & Reminder](APPOINTMENTS_REMINDERS.md#business-rules); file này chỉ bổ sung validation nêu trong checklist/source mapping bên dưới.

## Workflow và State Transitions

Tạo/assign activity → lifecycle → reminder/notification hoặc projection lên timeline.

Chi tiết end-to-end nằm ở mục Related Workflows; state không được suy ra từ nhãn UI nếu controller/schema quy định khác.

## Permissions

Owner/assignee/share và linked-record permission phải được kiểm ở backend.

Contract chung: [Permission Model](../../architecture/PERMISSION_MODEL.md).

## Source Mapping

| ID | Source reference | Bằng chứng mới trong checklist |
| --- | --- | --- |
| ACT-01 | Tasks.vue | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. Task có reminder_at, reminder_sent_at và preset/custom. |
| EXT-10 | Tasks.vue | Chưa có bằng chứng mới |
| EXT-12 | Tasks.vue | Chưa có bằng chứng mới |
| EXT-34 | DoubleTDealKanban.vue | Chưa có bằng chứng mới |

## Upstream Dependencies

- CRM record, Call/Insight hoặc thao tác người dùng.
- [Calls](../contact-center/CALLS.md)
- [Follow-up](../automation/FOLLOW_UP.md)
- [Appointment](APPOINTMENTS_REMINDERS.md)

## Downstream Impact

- Timeline, work queue, Notification và activity reports.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 05 MISSED CALL CALLBACK](../../workflows/WF_05_MISSED_CALL_CALLBACK.md)
- [WF 08 ACTIVITY REMINDER](../../workflows/WF_08_ACTIVITY_REMINDER.md)
- [WF 09 SMART INSIGHTS FOLLOW UP](../../workflows/WF_09_SMART_INSIGHTS_FOLLOW_UP.md)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| ACT-01 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| EXT-10 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| EXT-12 | Có một phần | Đề xuất | Checklist: Có một phần; Đề xuất. Không suy ra runtime PASS. |
| EXT-34 | Chưa thấy | Đề xuất | Checklist: Chưa thấy; Đề xuất. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| ACT-01 | Chạy test_callback_task_permissions và test Task; kiểm tạo/giao/Done, công việc gọi lại từ missed call, liên kết từ Task ↔ Call Log, quyền Sales/Manager. |
| EXT-10 | Kiểm ba nhóm với dữ liệu mẫu, gồm thời điểm đổi ngày và Task Done/Canceled. |
| EXT-12 | Gom việc hôm nay, quá hạn và Deal cần theo dõi. Mở mục kế tiếp sau khi đóng việc và lọc được theo owner. |
| EXT-34 | Trên một Deal có Task quá hạn, thấy bộ đếm và mở đúng danh sách. Đóng Task thì số giảm. |

## Known Limitations

- **ACT-01:** Source có nhưng vẫn phải theo acceptance status.
- **EXT-10:** Source có nhưng vẫn phải theo acceptance status.
- **EXT-12:** My Tasks có lọc. Chưa thấy hàng đợi để xử lý lần lượt nhiều bản ghi.
- **EXT-34:** Tasks có lọc quá hạn. Kanban Deal chưa thấy bộ đếm hoạt động đến hạn theo từng thẻ.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
