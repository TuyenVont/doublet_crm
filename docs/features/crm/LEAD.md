# Lead Management

[← crm index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-crm-01"></a>
- `CRM-01` — Danh sách, tạo và cập nhật Lead

## Mục đích nghiệp vụ

Danh sách, tạo và cập nhật Lead. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| CRM-01 | Danh sách, tạo và cập nhật Lead | R1 · CRM lõi | P0 | Có trang danh sách, chi tiết, trạng thái và nguồn Lead. | BA SCP-01, FR-01–05 |

## Data Model

`DoubleT Lead`, `DoubleT Contact`, `DoubleT Company`, `DoubleT Deal`, `DoubleT Deal Stage` và các Link/Dynamic Link liên quan.

Xem [Data Model](../../architecture/DATA_MODEL.md) và [Data Ownership](../../architecture/DATA_OWNERSHIP.md).

## Business Rules

Quy tắc dùng chung được quản lý tại [Deal & Pipeline](DEAL_PIPELINE.md#business-rules); file này chỉ bổ sung validation nêu trong checklist/source mapping bên dưới.

## Workflow và State Transitions

Dữ liệu đi từ prospect/interaction đến customer master, Deal và các projection downstream; trạng thái chỉ thay đổi qua controller/API có kiểm quyền.

Chi tiết end-to-end nằm ở mục Related Workflows; state không được suy ra từ nhãn UI nếu controller/schema quy định khác.

## Permissions

DocPerm và backend read/write checks; owner/assignee field không tự tạo record scope nếu thiếu permission hook.

Contract chung: [Permission Model](../../architecture/PERMISSION_MODEL.md).

## Source Mapping

| ID | Source reference | Bằng chứng mới trong checklist |
| --- | --- | --- |
| CRM-01 | FrappeLead.vue | 18/11 · 7105984 · Lead có list/detail và controller. Quyền mặc định xem CRM-07. Runtime chưa kiểm. |

## Upstream Dependencies

- Lead source, customer identity và Frappe permission infrastructure.
- [Lead Conversion](LEAD_CONVERSION.md)
- [Permission Model](../../architecture/PERMISSION_MODEL.md)

## Downstream Impact

- Pricing, Quotation, Order, Activities, Contact Center và Reports.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 01 INDIVIDUAL SALES](../../workflows/WF_01_INDIVIDUAL_SALES.md)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| CRM-01 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| CRM-01 | Chạy lại bằng Sales User. Tạo, tìm, lọc và sửa Lead mẫu đúng quyền. |

## Known Limitations

- **CRM-01:** Source có nhưng vẫn phải theo acceptance status.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
