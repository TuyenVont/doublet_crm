# Activity & Contact Center Report

[← analytics index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-rep-03"></a>
- `REP-03` — Activity & Contact Center Reports theo nhân viên/kỳ

## Mục đích nghiệp vụ

Activity & Contact Center Reports theo nhân viên/kỳ. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| REP-03 | Activity & Contact Center Reports theo nhân viên/kỳ | R1 · Báo cáo | P1 | 25/11 · PR #33 đã merge main 319ee10 (feature 5980359). Có lọc kênh Call/Task/Email/Zalo, thời gian, Agent/Assignee; Email/Zalo chưa hỗ trợ lọc nhân viên đầy đủ. CSV và saved filters. | BA FR-26 |

## Data Model

Permission-scoped query trên Deal, Order, Quotation, Activity, Conversation và Call; không tạo nguồn KPI song song.

Xem [Data Model](../../architecture/DATA_MODEL.md) và [Data Ownership](../../architecture/DATA_OWNERSHIP.md).

## Business Rules

Quy tắc dùng chung được quản lý tại [Report Platform](REPORT_PLATFORM.md#business-rules); file này chỉ bổ sung validation nêu trong checklist/source mapping bên dưới.

## Workflow và State Transitions

Filter/cohort → authorized query → aggregate/chart/table → export/drill-down trên cùng dataset.

Chi tiết end-to-end nằm ở mục Related Workflows; state không được suy ra từ nhãn UI nếu controller/schema quy định khác.

## Permissions

Aggregate, export và drill-down phải cùng record scope; unknown không được ép thành 0.

Contract chung: [Permission Model](../../architecture/PERMISSION_MODEL.md).

## Source Mapping

| ID | Source reference | Bằng chứng mới trong checklist |
| --- | --- | --- |
| REP-03 | reports.py · ActivityContactCenterReport.vue · report_tools.py · test_activity_reports.py | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. Activity report thêm Appointment/Reminder; giới hạn attribution Email/Zalo vẫn còn. |

## Upstream Dependencies

- Business source of truth và date/filter contract.
- [Tasks](../activities/TASKS.md)
- [Inbox](../contact-center/INBOX.md)
- [Calls](../contact-center/CALLS.md)

## Downstream Impact

- Dashboard, management decision, Smart Insights và follow-up.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 04 ZALO CARE](../../workflows/WF_04_ZALO_CARE.md)
- [WF 05 MISSED CALL CALLBACK](../../workflows/WF_05_MISSED_CALL_CALLBACK.md)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| REP-03 | Có một phần | Cần kiểm | Checklist: Có một phần; Cần kiểm. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| REP-03 | Kiểm lọc từng kênh, link nguồn, đối chiếu số liệu và quyền 3 role; giữ rõ giới hạn Email/Zalo. |

## Known Limitations

- **REP-03:** 25/11 · PR #33 đã merge main 319ee10 (feature 5980359). Có lọc kênh Call/Task/Email/Zalo, thời gian, Agent/Assignee; Email/Zalo chưa hỗ trợ lọc nhân viên đầy đủ. CSV và saved filters.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
