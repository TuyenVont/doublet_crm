# Lead Conversion

[← crm index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-crm-02"></a>
- `CRM-02` — Lead → Deal cho cá nhân và doanh nghiệp

## Mục đích nghiệp vụ

Lead → Deal cho cá nhân và doanh nghiệp. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| CRM-02 | Lead → Deal cho cá nhân và doanh nghiệp | R1 · CRM lõi | P0 | Controller có convert_lead, dùng Contact/Company đã có hoặc tạo mới và lưu liên kết chuyển đổi. | BA SCP-01, FR-04–05 |

## Data Model

`DoubleT Lead`, `DoubleT Contact`, `DoubleT Company`, `DoubleT Deal`, `DoubleT Deal Stage` và các Link/Dynamic Link liên quan.

Xem [Data Model](../../architecture/DATA_MODEL.md) và [Data Ownership](../../architecture/DATA_OWNERSHIP.md).

## Business Rules

Quy tắc dùng chung được quản lý tại [Deal & Pipeline](DEAL_PIPELINE.md#business-rules); file này chỉ bổ sung validation nêu trong checklist/source mapping bên dưới.

## Workflow và State Transitions

Dữ liệu đi từ prospect/interaction đến customer master, Deal và các projection downstream; trạng thái chỉ thay đổi qua controller/API có kiểm quyền.

Contract chuyển tiếp và dữ liệu kế thừa được quản lý tại [BF-02 Lead → Contact/Company/Deal](../../architecture/BUSINESS_FLOW_CONTRACT.md#bf-02--lead--contactcompanydeal). Converted links và Deal `source_lead` phải còn sau reload; Conversation đã link Lead tiếp tục được truy qua converted chain mà không copy Message. Contact đại diện Company phải được xác nhận, không suy ra khi ambiguous.

Chi tiết end-to-end nằm ở mục Related Workflows; state không được suy ra từ nhãn UI nếu controller/schema quy định khác.

## Permissions

DocPerm và backend read/write checks; owner/assignee field không tự tạo record scope nếu thiếu permission hook.

Contract chung: [Permission Model](../../architecture/PERMISSION_MODEL.md).

## Source Mapping

| ID | Source reference | Bằng chứng mới trong checklist |
| --- | --- | --- |
| CRM-02 | doublet_lead.py | 18/11 · 7105984 · convert_lead có code cho Personal/Company. Chưa chạy lại luồng. |

## Upstream Dependencies

- Lead source, customer identity và Frappe permission infrastructure.
- [Lead](LEAD.md)
- [Customer](CUSTOMER.md)
- [Deal](DEAL_PIPELINE.md)

## Downstream Impact

- Pricing, Quotation, Order, Activities, Contact Center và Reports.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 01 INDIVIDUAL SALES](../../workflows/WF_01_INDIVIDUAL_SALES.md)
- [WF 02 COMPANY SALES](../../workflows/WF_02_COMPANY_SALES.md)
- [WF 11 CUSTOMER LIFECYCLE](../../workflows/WF_11_CUSTOMER_LIFECYCLE.md)
- [Identity/conversion acceptance](../../testing/CROSS_MODULE_ACCEPTANCE.md#customer-identity-and-conversion)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| CRM-02 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| CRM-02 | Thử Personal và Company, mở lại hồ sơ liên kết và xác nhận convert lặp giữ đúng một Deal. |

## Known Limitations

- **CRM-02:** Source có nhưng vẫn phải theo acceptance status.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
