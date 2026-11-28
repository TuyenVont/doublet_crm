# Sales Performance

[← analytics index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-rep-02"></a>
- `REP-02` — Sales Performance: hiệu suất bán hàng theo nhân viên và kỳ
<a id="feature-ext-13"></a>
- `EXT-13` — Giá trị Deal Won theo kỳ (nguồn cho Sales Reports)

## Mục đích nghiệp vụ

Sales Performance: hiệu suất bán hàng theo nhân viên và kỳ; Giá trị Deal Won theo kỳ (nguồn cho Sales Reports). Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| REP-02 | Sales Performance: hiệu suất bán hàng theo nhân viên và kỳ | R1 · Báo cáo | P0 | 25/11 · PR #33 đã merge main 319ee10 (feature 5980359). Sales Performance giữ các công thức Booked Sales/AOV/Won/Lost; có Export CSV và lưu bộ lọc cá nhân. | NOTES · CHECKLIST cũ #6/10/21/25 |
| EXT-13 | Giá trị Deal Won theo kỳ (nguồn cho Sales Reports) | R1 · Báo cáo | P0 | 24/11 · PR #32 merge main ed76ba1 (feature acf1d7a). Won Deal Value cộng Deal Amount theo won_on trong kỳ và quyền đọc; tách khỏi Booked Sales; hỗ trợ lọc owner, drill-down. | Odoo · CRM CORE &APP A167:A172 · NOTES |

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
| REP-02 | reports.py · SalesPerformanceReport.vue · report_tools.py | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. Sales Performance giữ công thức hiện hữu; kiểm đối chiếu số liệu. |
| EXT-13 | doublet_crm/reports.py · SalesPerformanceReport.vue · test_reports.py | 24/11 · PR #32 merge main ed76ba1 (feature acf1d7a). Test cross-month outcomes, event dates, permissions và drill-down; Codex báo 42/42 Reports + 6/6 Activity PASS; Tuyền xác nhận chức năng OK trên local.  |

## Upstream Dependencies

- Business source of truth và date/filter contract.
- [Deal](../crm/DEAL_PIPELINE.md)
- [Order](../sales/ORDER.md)

## Downstream Impact

- Dashboard, management decision, Smart Insights và follow-up.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 01 INDIVIDUAL SALES](../../workflows/WF_01_INDIVIDUAL_SALES.md)
- [WF 02 COMPANY SALES](../../workflows/WF_02_COMPANY_SALES.md)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| REP-02 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| EXT-13 | Có | Đã xong | Checklist: Có; Đã xong. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| REP-02 | Đối chiếu số liệu và export theo kỳ/owner, kiểm từng role. |
| EXT-13 | Duy trì regression khi sửa Sales/Pipeline; kiểm quyền browser cùng REP-02. |

## Known Limitations

- **REP-02:** Source có nhưng vẫn phải theo acceptance status.
- **EXT-13:** Source có nhưng vẫn phải theo acceptance status.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
