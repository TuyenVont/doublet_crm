# Smart Insights

[← analytics index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-rep-09"></a>
- `REP-09` — Smart Insights: cảnh báo có lý do và thao tác
<a id="feature-rep-10"></a>
- `REP-10` — Deal Health Score: điểm rủi ro cơ hội minh bạch

## Mục đích nghiệp vụ

Smart Insights: cảnh báo có lý do và thao tác; Deal Health Score: điểm rủi ro cơ hội minh bạch. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| REP-09 | Smart Insights: cảnh báo có lý do và thao tác | R1 · Reports | P0 | 25/11 · PR #33 đã merge main 319ee10 (feature 5980359). Engine Smart Insights cảnh báo Deal ít cập nhật, quá ngày dự kiến, Quotation sắp hết hạn, Task quá hạn và prolonged_stage. Có lý do/link, tạo follow-up Task chống trùng. | Đề xuất đột phá 22/11 · Salesforce/Dynamics · NEW-02 |
| REP-10 | Deal Health Score: điểm rủi ro cơ hội minh bạch | R2 · Reports nâng cao | P1 | 25/11 · PR #33 đã merge main 319ee10 (feature 5980359). Health Score rule-based, lý do, phân loại và coverage; nguồn không đọc được hoặc thiếu dữ liệu không được coi là 0/healthy. | Đề xuất đột phá 22/11 · Dynamics Relationship Analytics |

## Data Model

Permission-scoped query trên Deal, Order, Quotation, Activity, Conversation và Call; không tạo nguồn KPI song song.

Xem [Data Model](../../architecture/DATA_MODEL.md) và [Data Ownership](../../architecture/DATA_OWNERSHIP.md).

## Business Rules

Quy tắc dùng chung được quản lý tại [Report Platform](REPORT_PLATFORM.md#business-rules); file này chỉ bổ sung validation nêu trong checklist/source mapping bên dưới.

## Workflow và State Transitions

Filter/cohort → authorized query → aggregate/chart/table → export/drill-down trên cùng dataset.

Source links và explicit follow-up tuân theo [BF-09](../../architecture/BUSINESS_FLOW_CONTRACT.md#bf-09--reportsmart-insight--source-or-follow-up-task): alert phải còn current/readable; Quotation chỉ tạo Task qua readable Deal hợp lệ; lock + active marker chống duplicate. Đây không phải automatic `NEW-02`.

Chi tiết end-to-end nằm ở mục Related Workflows; state không được suy ra từ nhãn UI nếu controller/schema quy định khác.

## Permissions

Aggregate, export và drill-down phải cùng record scope; unknown không được ép thành 0.

Contract chung: [Permission Model](../../architecture/PERMISSION_MODEL.md).

## Source Mapping

| ID | Source reference | Bằng chứng mới trong checklist |
| --- | --- | --- |
| REP-09 | smart_insights.py · SmartInsightsReport.vue · test_smart_insights.py | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. Smart Insights cải tiến severity/load more; cần đối chiếu Dashboard. |
| REP-10 | smart_insights.py · SmartInsightsReport.vue · test_smart_insights.py | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. Health Score rule-based; chưa nghiệm thu role. |

## Upstream Dependencies

- Business source of truth và date/filter contract.
- [Pipeline](PIPELINE_ANALYTICS.md)
- [Follow-up](../automation/FOLLOW_UP.md)

## Downstream Impact

- Dashboard, management decision, Smart Insights và follow-up.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 09 SMART INSIGHTS FOLLOW UP](../../workflows/WF_09_SMART_INSIGHTS_FOLLOW_UP.md)
- [Report/Insight acceptance](../../testing/CROSS_MODULE_ACCEPTANCE.md#reports-and-smart-insights)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| REP-09 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| REP-10 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| REP-09 | Kiểm ngưỡng, link, quyền từng role và chống tạo Task trùng khi gọi đồng thời; đối chiếu Dashboard. |
| REP-10 | Kiểm Deal tốt/rủi ro/thiếu dữ liệu, điểm và quyền; đối chiếu CSV theo role. |

## Known Limitations

- **REP-09:** Source có nhưng vẫn phải theo acceptance status.
- **REP-10:** Source có nhưng vẫn phải theo acceptance status.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
