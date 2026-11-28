# Customer Identity & Duplicate Handling

[← crm index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-crm-06"></a>
- `CRM-06` — Phát hiện và xử lý hồ sơ trùng
<a id="feature-ext-04"></a>
- `EXT-04` — Gộp hồ sơ trùng có người duyệt

## Mục đích nghiệp vụ

Phát hiện và xử lý hồ sơ trùng; Gộp hồ sơ trùng có người duyệt. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| CRM-06 | Phát hiện và xử lý hồ sơ trùng | R1 · Dữ liệu khách | P0 | Có cảnh báo trùng Lead/Contact theo email/điện thoại. Chưa thấy luồng đối chiếu và quyết định liên kết đa nguồn. | BA UC-04, FR-11, FR-17–23, FR-30–32 |
| EXT-04 | Gộp hồ sơ trùng có người duyệt | Nâng cấp · Dữ liệu khách | P2 | Có cảnh báo trùng trên form Contact. Chưa thấy màn chọn bản ghi chính và chuyển liên kết. | Odoo · CRM CORE &APP A34:A35 · Merge ghi Future |

## Data Model

`DoubleT Lead`, `DoubleT Contact`, `DoubleT Company`, `DoubleT Deal`, `DoubleT Deal Stage` và các Link/Dynamic Link liên quan.

Xem [Data Model](../../architecture/DATA_MODEL.md) và [Data Ownership](../../architecture/DATA_OWNERSHIP.md).

## Business Rules

Các validation riêng được xác định từ source/checklist trong bảng dưới đây; quy tắc xuyên module được quản lý tại [Data Ownership](../../architecture/DATA_OWNERSHIP.md) và [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Workflow và State Transitions

Dữ liệu đi từ prospect/interaction đến customer master, Deal và các projection downstream; trạng thái chỉ thay đổi qua controller/API có kiểm quyền.

Chi tiết end-to-end nằm ở mục Related Workflows; state không được suy ra từ nhãn UI nếu controller/schema quy định khác.

## Permissions

DocPerm và backend read/write checks; owner/assignee field không tự tạo record scope nếu thiếu permission hook.

Contract chung: [Permission Model](../../architecture/PERMISSION_MODEL.md).

## Source Mapping

| ID | Source reference | Bằng chứng mới trong checklist |
| --- | --- | --- |
| CRM-06 | doublet_lead.py | Chưa có bằng chứng mới |
| EXT-04 | DoubleTContactDataPanel.vue | Chưa có bằng chứng mới |

## Upstream Dependencies

- Lead source, customer identity và Frappe permission infrastructure.
- [Customer](CUSTOMER.md)
- [External Channels](../integration/EXTERNAL_CHANNELS.md)

## Downstream Impact

- Pricing, Quotation, Order, Activities, Contact Center và Reports.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 04 ZALO CARE](../../workflows/WF_04_ZALO_CARE.md)
- [WF 07 WOOCOMMERCE SYNC](../../workflows/WF_07_WOOCOMMERCE_SYNC.md)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| CRM-06 | Có một phần | Cần làm | Checklist: Có một phần; Cần làm. Không suy ra runtime PASS. |
| EXT-04 | Chưa thấy | Đề xuất | Checklist: Chưa thấy; Đề xuất. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| CRM-06 | Chốt quy tắc định danh. Có ca trùng chắc chắn, nghi vấn và giữ riêng. Lưu ID nguồn và quyết định của người được phân quyền. |
| EXT-04 | Quản lý chọn các trường giữ lại và kiểm lại Lead/Deal/Notes sau khi gộp. Có log quyết định. |

## Known Limitations

- **CRM-06:** Có cảnh báo trùng Lead/Contact theo email/điện thoại. Chưa thấy luồng đối chiếu và quyết định liên kết đa nguồn.
- **EXT-04:** Có cảnh báo trùng trên form Contact. Chưa thấy màn chọn bản ghi chính và chuyển liên kết.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
