# Dashboard

[← analytics index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-rep-01"></a>
- `REP-01` — Dashboard tổng quan nhanh Lead, Deal và báo giá (giữ nguyên khi xây Reports)
<a id="feature-rep-14"></a>
- `REP-14` — Nâng cấp Dashboard cũ thành trung tâm điều hành hằng ngày

## Mục đích nghiệp vụ

Dashboard tổng quan nhanh Lead, Deal và báo giá (giữ nguyên khi xây Reports); Nâng cấp Dashboard cũ thành trung tâm điều hành hằng ngày. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| REP-01 | Dashboard tổng quan nhanh Lead, Deal và báo giá (giữ nguyên khi xây Reports) | R1 · Báo cáo | P0 | 25/11 · PR #33 đã merge main 319ee10 (feature 5980359). Giữ KPI Dashboard cũ; bổ sung Needs Attention lấy từ engine Smart Insights dùng chung. | BA FR-24–25, FR-28 |
| REP-14 | Nâng cấp Dashboard cũ thành trung tâm điều hành hằng ngày | R1 · Dashboard điều hành | P1 | 25/11 · PR #33 đã merge main 319ee10 (feature 5980359). Dashboard có Needs Attention tái dùng engine Smart Insights, hiển thị cảnh báo và link View All; giữ KPI cũ. | Chốt thiết kế 22/11 · REP-01, REP-05–11, REP-09 · Dashboard vs Reports |

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
| REP-01 | dashboard.py · Dashboard.vue · smart_insights.py | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. Dashboard giữ KPI và thêm Upcoming Activities. |
| REP-14 | dashboard.py · Dashboard.vue · smart_insights.py | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. Dashboard thêm Upcoming Activities và giữ Needs Attention. |

## Upstream Dependencies

- Business source of truth và date/filter contract.
- [Report Platform](REPORT_PLATFORM.md)
- [Sales Performance](SALES_PERFORMANCE.md)
- [Pipeline](PIPELINE_ANALYTICS.md)

## Downstream Impact

- Dashboard, management decision, Smart Insights và follow-up.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- Xem [workflow index](../../workflows/README.md); chưa có workflow riêng cho mục này.

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| REP-01 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| REP-14 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| REP-01 | Kiểm KPI cũ, cảnh báo, link, empty/error/retry theo từng role. |
| REP-14 | Kiểm cảnh báo khớp Smart Insights, quyền, link, empty/error và màn hẹp. |

## Known Limitations

- **REP-01:** Source có nhưng vẫn phải theo acceptance status.
- **REP-14:** Source có nhưng vẫn phải theo acceptance status.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
