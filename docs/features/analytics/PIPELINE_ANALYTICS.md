# Pipeline Analytics, Forecast & Deal Health

[← analytics index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-rep-07"></a>
- `REP-07` — Pipeline Analytics: giá trị, giai đoạn, cơ hội rủi ro
<a id="feature-ext-15"></a>
- `EXT-15` — Dự báo doanh thu theo ngày dự kiến chốt
<a id="feature-ext-32"></a>
- `EXT-32` — Lost Reason Analytics: lý do mất Deal
<a id="feature-ext-33"></a>
- `EXT-33` — Deal đứng lâu ở một stage

## Mục đích nghiệp vụ

Pipeline Analytics: giá trị, giai đoạn, cơ hội rủi ro; Dự báo doanh thu theo ngày dự kiến chốt; Lost Reason Analytics: lý do mất Deal; Deal đứng lâu ở một stage. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| REP-07 | Pipeline Analytics: giá trị, giai đoạn, cơ hội rủi ro | R1 · Reports | P0 | 25/11 · PR #33 đã merge main 319ee10 (feature 5980359). Giữ Pipeline/Lost Reason/risk hiện hữu; bổ sung Sales Forecast và Stage Aging, phân biệt inactivity với thời gian nằm stage. | Đề xuất 22/11 · Odoo Pipeline · Salesforce pipeline inspection |
| EXT-15 | Dự báo doanh thu theo ngày dự kiến chốt | Nâng cấp · Báo cáo | P2 | Probability tùy chọn ở Deal/Stage, phân biệt chưa cấu hình và 0%; weighted forecast và CSV. | Odoo · CRM CORE &APP A176 · Future |
| EXT-32 | Lost Reason Analytics: lý do mất Deal | R1 · Báo cáo | P1 | 24/11 · PR #32 merge main ed76ba1 (feature acf1d7a). Lost Reason Analytics nhóm theo lost_on/lost_reason, count/value/share, gồm lý do trống; có xử lý mẫu số 0, làm tròn và drill-down. | Odoo · CORE A170 · NOTES |
| EXT-33 | Deal đứng lâu ở một stage | Nâng cấp · Báo cáo | P2 | Stage Aging dùng stage_entered_on/by và lịch sử Version; phân biệt Unknown, không dùng modified. | HubSpot · CORE A173:A175 · Future |

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
| REP-07 | reports.py · stage_aging.py · PipelineAnalyticsReport.vue | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. Forecast và Stage Aging hoàn thiện code. |
| EXT-15 | reports.py · PipelineAnalyticsReport.vue · report_tools.py · test_reports.py | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. |
| EXT-32 | doublet_crm/reports.py · PipelineAnalyticsReport.vue · test_reports.py | 24/11 · PR #32 merge main ed76ba1 (feature acf1d7a). Test lost reason reconciliation và risk/lost drill-down; Codex báo 42/42 Reports + 6/6 Activity PASS; Tuyền xác nhận chức năng OK trên local.  |
| EXT-33 | stage_aging.py · reports.py · smart_insights.py · PipelineAnalyticsReport.vue | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. |

## Upstream Dependencies

- Business source of truth và date/filter contract.
- [Deal](../crm/DEAL_PIPELINE.md)
- [Smart Insights](SMART_INSIGHTS.md)
- [Tasks](../activities/TASKS.md)

## Downstream Impact

- Dashboard, management decision, Smart Insights và follow-up.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 09 SMART INSIGHTS FOLLOW UP](../../workflows/WF_09_SMART_INSIGHTS_FOLLOW_UP.md)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| REP-07 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| EXT-15 | Có | Cần kiểm | Stage Aging source tồn tại ở baseline; acceptance pending. |
| EXT-32 | Có | Đã xong | Checklist: Có; Đã xong. Không suy ra runtime PASS. |
| EXT-33 | Có | Cần kiểm | Deal Health/analytics source tồn tại ở baseline; acceptance pending. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| REP-07 | Đối chiếu dữ liệu, date/owner, drill-down, forecast/aging và quyền 3 role; xem EXT-15/EXT-33. |
| EXT-15 | Kiểm persistence, quyền trường, 0/Unknown và CSV. |
| EXT-32 | Duy trì regression; kiểm quyền browser cùng REP-07. |
| EXT-33 | Kiểm mọi đường chuyển stage, actor/timestamp và dữ liệu legacy. |

## Known Limitations

- **REP-07:** Source có nhưng vẫn phải theo acceptance status.
- **EXT-15:** Source có nhưng vẫn phải theo acceptance status.
- **EXT-32:** Source có nhưng vẫn phải theo acceptance status.
- **EXT-33:** Source có nhưng vẫn phải theo acceptance status.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
