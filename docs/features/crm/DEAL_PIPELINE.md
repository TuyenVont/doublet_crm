# Deal & Pipeline

[← crm index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-crm-03"></a>
- `CRM-03` — Quản lý cơ hội và pipeline
<a id="feature-crm-09"></a>
- `CRM-09` — Điều hướng hai chiều giữa hồ sơ và cơ hội

## Mục đích nghiệp vụ

Quản lý cơ hội và pipeline; Điều hướng hai chiều giữa hồ sơ và cơ hội. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| CRM-03 | Quản lý cơ hội và pipeline | R1 · CRM lõi | P0 | PR #37 sửa tải danh sách Deal: filter reactive theo lifecycle/stage/owner/ngày tạo, reload giữ filter, phân trang giữ tập lọc và nạp nhãn Contact/Company. Kanban stage transition từ PR #28 vẫn là contract hiện hành. | BA SCP-01, FR-25 |
| CRM-09 | Điều hướng hai chiều giữa hồ sơ và cơ hội | R1 · Hồ sơ khách | P1 | Lead lưu converted_contact/company/deal và Deal có source_lead. Cần đối chiếu màn Contact/Company có đủ danh sách Lead/Deal cùng khách. | BA FR-04–05 · UC-01 |

## Data Model

`DoubleT Lead`, `DoubleT Contact`, `DoubleT Company`, `DoubleT Deal`, `DoubleT Deal Stage` và các Link/Dynamic Link liên quan.

Xem [Data Model](../../architecture/DATA_MODEL.md) và [Data Ownership](../../architecture/DATA_OWNERSHIP.md).

## Business Rules

**Tài liệu quản lý chính cho nhóm quy tắc này:** file hiện tại.

Lead/Deal canonical rules: Lead status `NEW/CONTACTED/NURTURE/QUALIFIED/CONVERTED/UNQUALIFIED/JUNK`; conversion phải idempotent; `Deal Stage.stage_type` là `OPEN/WON/LOST`; LOST cần `lost_reason`; Deal probability ưu tiên Stage, blank là unknown và `0` hợp lệ; stage evidence do server ghi.

## Workflow và State Transitions

Dữ liệu đi từ prospect/interaction đến customer master, Deal và các projection downstream; trạng thái chỉ thay đổi qua controller/API có kiểm quyền.

Lead/customer → Deal và Deal → Quotation phải giữ source/customer context theo [Business Flow Contract](../../architecture/BUSINESS_FLOW_CONTRACT.md#bf-04--leaddeal--quotation). Customer page create-with-context vẫn là GAP; Deal/Lead → Quotation đã có implementation.

Chi tiết end-to-end nằm ở mục Related Workflows; state không được suy ra từ nhãn UI nếu controller/schema quy định khác.

## Permissions

DocPerm và backend read/write checks; owner/assignee field không tự tạo record scope nếu thiếu permission hook.

Contract chung: [Permission Model](../../architecture/PERMISSION_MODEL.md).

## Source Mapping

| ID | Source reference | Bằng chứng mới trong checklist |
| --- | --- | --- |
| CRM-03 | `frontend/src/composables/useDoubleTDeals.js`; `frontend/src/pages/DealsView.vue`; `frontend/tests/dealsResource.test.mjs`; stage APIs/controllers | Historical docs ghi Deal pipeline source present, cần demo-role và Dashboard comparison. PR #37 bổ sung source/focused test cho filter/reload/pagination/labels; test không chạy lại trong task tài liệu. |
| CRM-09 | DoubleTEntityDetail.vue | 18/11 · 7105984 · Company có Contacts/Deals/Converted Leads. Còn kiểm điều hướng và báo giá theo khách. |

## Upstream Dependencies

- Lead source, customer identity và Frappe permission infrastructure.
- [Customer](CUSTOMER.md)
- [Product](../sales/PRODUCT_CATALOG.md)
- [Quotation](../sales/QUOTATION.md)
- [Pipeline Analytics](../analytics/PIPELINE_ANALYTICS.md)

## Downstream Impact

- Pricing, Quotation, Order, Activities, Contact Center và Reports.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 01 INDIVIDUAL SALES](../../workflows/WF_01_INDIVIDUAL_SALES.md)
- [WF 02 COMPANY SALES](../../workflows/WF_02_COMPANY_SALES.md)
- [WF 11 CUSTOMER LIFECYCLE](../../workflows/WF_11_CUSTOMER_LIFECYCLE.md)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| CRM-03 | Có | Cần kiểm | Source verified tại `a7534e7`: list resource tải sau khi stage sẵn sàng, reset `start=0` khi filter đổi, reload/pagination giữ filters và resolve nhãn Contact/Company. Browser/role và test execution trên baseline vẫn pending. |
| CRM-09 | Có một phần | Cần làm | Checklist: Có một phần; Cần làm. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| CRM-03 | Kiểm trên Chrome bằng Sales User/Manager: kéo Open → Won/Lost, xác nhận/huỷ, reload giữ stage và tổng; kiểm khi API lỗi rollback đúng; lịch sử cuộc gọi Deal cũ vẫn hiển thị đúng quyền. |
| CRM-09 | Từ Contact/Company tìm lại Lead, Deal đang mở và báo giá liên kết. Kiểm danh sách đúng hồ sơ và đúng role. |

## Known Limitations

- **CRM-03:** Source và automated test case có, nhưng task này không chạy test/browser. Search cục bộ trong `DealsView.vue` vẫn lọc trên dữ liệu đã tải; không thay thế server filters/pagination.
- **CRM-09:** Lead lưu converted_contact/company/deal và Deal có source_lead. Cần đối chiếu màn Contact/Company có đủ danh sách Lead/Deal cùng khách.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
