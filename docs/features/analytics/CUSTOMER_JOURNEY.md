# Customer Journey & Funnel

[← analytics index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-rep-06"></a>
- `REP-06` — Customer Journey: Lead → Deal → Quotation → Order
<a id="feature-ext-14"></a>
- `EXT-14` — Funnel theo nhóm Lead cùng kỳ

## Mục đích nghiệp vụ

Customer Journey: Lead → Deal → Quotation → Order; Funnel theo nhóm Lead cùng kỳ. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| REP-06 | Customer Journey: Lead → Deal → Quotation → Order | R1 · Reports | P0 | 25/11 · PR #33 đã merge main 319ee10 (feature 5980359). Customer Journey mở rộng cohort Lead theo nguồn; drill-down các Deal/Quotation/Order, phân biệt Order trực tiếp và qua Quotation, deduplicate. | Đề xuất 22/11 · HubSpot funnel · BA UC-01 · ORD-02 |
| EXT-14 | Funnel theo nhóm Lead cùng kỳ | Nâng cấp · Báo cáo | P2 | 25/11 · PR #33 đã merge main 319ee10 (feature 5980359). Cohort theo ngày tạo Lead/nguồn; đếm Lead duy nhất chuyển Deal/Won, drill-down nhiều Deal/Quotation/Order theo liên kết thực. | CRM CORE &APP A173:A175 · Future |

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
| REP-06 | reports.py · CustomerJourneyReport.vue · test_reports.py | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. Customer Journey drill-down; cần kiểm dữ liệu/owner. |
| EXT-14 | reports.py · CustomerJourneyReport.vue · test_reports.py | 25/11 · PR #33 đã merge main 319ee10 (feature 5980359). Source get_customer_journey và Lead to Won Rate; Codex báo Reports backend 51 PASS; Smart Insights/export 25 PASS; Pipeline frontend 5 PASS; Smart Insights frontend 4 PASS; compile/diff check PASS. Chưa nghiệm thu browser/role trên bản cuối. |

## Upstream Dependencies

- Business source of truth và date/filter contract.
- [Lead Conversion](../crm/LEAD_CONVERSION.md)
- [Customer](../crm/CUSTOMER.md)

## Downstream Impact

- Dashboard, management decision, Smart Insights và follow-up.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 01 INDIVIDUAL SALES](../../workflows/WF_01_INDIVIDUAL_SALES.md)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| REP-06 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| EXT-14 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| REP-06 | Kiểm cohort nhiều hồ sơ, link từng loại, mẫu số và quyền/CSV thực tế. |
| EXT-14 | Đối chiếu cohort và mẫu số với dữ liệu mẫu, nhiều hồ sơ liên kết, quyền và CSV. |

## Known Limitations

- **REP-06:** Source có nhưng vẫn phải theo acceptance status.
- **EXT-14:** Source có nhưng vẫn phải theo acceptance status.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
