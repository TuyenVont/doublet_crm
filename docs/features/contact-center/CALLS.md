# Call Management & AI Summary

[← contact-center index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-call-01"></a>
- `CALL-01` — Call Logs, thống kê và phân trang
<a id="feature-call-02"></a>
- `CALL-02` — Xác minh AI Summary cho Call Logs
<a id="feature-cc-09"></a>
- `CC-09` — Tích hợp tổng đài thật qua SIP/PBX
<a id="feature-cc-10"></a>
- `CC-10` — Tạo việc gọi lại từ cuộc gọi nhỡ

## Mục đích nghiệp vụ

Call Logs, thống kê và phân trang; Xác minh AI Summary cho Call Logs; Tích hợp tổng đài thật qua SIP/PBX; Tạo việc gọi lại từ cuộc gọi nhỡ. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| CALL-01 | Call Logs, thống kê và phân trang | R1 · Cuộc gọi | P0 | 23/11 · PR #27 (218cdef) bổ sung ContactCenterCalls.vue và contact_center_calls.py: hàng đợi Waiting/In Progress/Resolved, filter, assignee, quyền quản lý, log Call Event và luồng Call Log. Test_contact_center_calls có trong main; chưa có kết quả browser end-to-end đợt này. | CHECKLIST cũ #36 · Audit 18/11 |
| CALL-02 | Xác minh AI Summary cho Call Logs | R1 · Cuộc gọi | P1 | 23/11 · PR #27 (218cdef) thêm call_log/ai_summary.py, Doctype DoubleT Call AI Summary, giao diện Generate/Regenerate và test. Ghi âm private, transcript, summary, customer needs, next steps; sử dụng BeeKnoee theo cấu hình, job queue. Chưa có bằng chứng chạy thành công với API thực tế trên site. | CHECKLIST cũ #36 · Rà GitHub |
| CC-09 | Tích hợp tổng đài thật qua SIP/PBX | Sau mốc · Tổng đài | P2 | Call Center hiện đã quản lý cuộc gọi, nhưng PR #27 không phải kết nối tổng đài SIP/PBX thật. Hạng mục này vẫn chờ môi trường và phạm vi tích hợp được chốt. | Bitrix24 · SIP connector |
| CC-10 | Tạo việc gọi lại từ cuộc gọi nhỡ | Sau mốc · Tổng đài | P2 | 23/11 · PR #27 (218cdef) bổ sung Callback Task gắn missed Call Log, kết quả gọi lại, bảo vệ quyền sửa callback và test_callback_task_permissions.py. Có chức năng trong source; chưa kiểm điện thoại/tổng đài SIP/PBX thật. | Bitrix24 · Xử lý cuộc gọi nhỡ |

## Data Model

`Communication`, `Conversation`, `Message`, `Conversation Event`, `Call Log`, `Call Event`, `Call AI Summary`, private `File`.

Xem [Data Model](../../architecture/DATA_MODEL.md) và [Data Ownership](../../architecture/DATA_OWNERSHIP.md).

## Business Rules

Quy tắc dùng chung được quản lý tại [Inbox shared handling rules](INBOX.md#business-rules); file này chỉ bổ sung validation nêu trong checklist/source mapping bên dưới.

## Workflow và State Transitions

Inbound/outbound event → link customer → assign/handle → resolve; derived Task/Note giữ link về nguồn.

Chi tiết end-to-end nằm ở mục Related Workflows; state không được suy ra từ nhãn UI nếu controller/schema quy định khác.

## Permissions

Permission hooks theo assignment/manager/API principal; attachment và linked customer phải kiểm quyền.

Contract chung: [Permission Model](../../architecture/PERMISSION_MODEL.md).

## Source Mapping

| ID | Source reference | Bằng chứng mới trong checklist |
| --- | --- | --- |
| CALL-01 | api.py:790, 820 | 22/11 · PR #27 merged main 218cdef. Diff contact_center_calls.py, DoubleT Call Event, Call Log schema, permissions.py, CallLogDetails.vue và test_contact_center_calls.py. Runtime cuối chưa kiểm. |
| CALL-02 | CallLogs.vue:366 | 21/11 · commit 1318641; 22/11 · PR #27 → main 218cdef. Diff call_log/ai_summary.py, DoubleT Call AI Summary, CallLogAISummary.vue, test_doublet_call_ai_summary.py. Chưa xác minh chạy thực tế. |
| CC-09 | router.js | 22/11 · PR #27 → main 218cdef xây Call Center Calls nội bộ; chưa có bằng chứng adapter SIP/FusionPBX hoặc call qua tổng đài thật. |
| CC-10 | api.py | 22/11 · PR #27 → main 218cdef. doublet_crm/contact_center_calls.py, doublet_task.py/json, test_callback_task_permissions.py và TaskArea.vue. Có code/test; runtime chưa xác nhận. |

## Upstream Dependencies

- Email/Zalo/telephony provider và customer identity.
- [Tasks](../activities/TASKS.md)
- [Notes](../activities/NOTES_TIMELINE.md)
- [Activity report](../analytics/ACTIVITY_CONTACT_CENTER.md)

## Downstream Impact

- Customer history, Activities và Contact Center analytics.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 05 MISSED CALL CALLBACK](../../workflows/WF_05_MISSED_CALL_CALLBACK.md)
- [WF 06 CALL AI NOTE](../../workflows/WF_06_CALL_AI_NOTE.md)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| CALL-01 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| CALL-02 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| CC-09 | Cần chốt | Cần chốt | Checklist: Cần chốt; Cần chốt. Không suy ra runtime PASS. |
| CC-10 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| CALL-01 | Chạy test_contact_center_calls; browser bằng Manager/Sales: lọc assigned/unassigned, Waiting→In Progress→Resolved, phân công/reassign, xem recording và không lộ Call Log người khác. |
| CALL-02 | Cấu hình BeeKnoee bằng secret môi trường test; gắn recording private hợp lệ rồi chạy Generate/Regenerate; kiểm transcript/summary/needs/next steps, worker queue, quyền role, ca lỗi và rate limit. |
| CC-09 | Sau khi nhóm chốt phạm vi, thử một cuộc gọi vào và một cuộc gọi ra bằng môi trường test. Gắn vào hồ sơ đúng khách qua module của Thư. |
| CC-10 | Thử một missed call mẫu, tạo/đi tới Callback Task và đánh dấu gọi lại; xác nhận không tạo trùng, liên kết Call Log 2 chiều, quyền Sales/Manager; tách rõ test mock với PBX thật. |

## Known Limitations

- **CALL-01:** Source có nhưng vẫn phải theo acceptance status.
- **CALL-02:** Source có nhưng vẫn phải theo acceptance status.
- **CC-09:** Call Center hiện đã quản lý cuộc gọi, nhưng PR #27 không phải kết nối tổng đài SIP/PBX thật. Hạng mục này vẫn chờ môi trường và phạm vi tích hợp được chốt.
- **CC-10:** Source có nhưng vẫn phải theo acceptance status.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
