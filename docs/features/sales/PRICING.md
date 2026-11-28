# Price List & Price Resolution

[← sales index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-sale-03"></a>
- `SALE-03` — Bảng giá theo khách và giá dự phòng

## Mục đích nghiệp vụ

Bảng giá theo khách và giá dự phòng. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| SALE-03 | Bảng giá theo khách và giá dự phòng | R1 · Bảng giá | P0 | Có Price List mặc định/riêng với thứ tự chọn rõ → Company → Contact → mặc định. Rơi về giá Product nếu bảng thiếu SKU. | Báo cáo 08–14/11 |

## Data Model

Product/Category/Variant, Price List/Settings, Quotation/Items/Approval và Order/Items; item thương mại lưu snapshot.

Xem [Data Model](../../architecture/DATA_MODEL.md) và [Data Ownership](../../architecture/DATA_OWNERSHIP.md).

## Business Rules

Quy tắc dùng chung được quản lý tại [Product Catalog](PRODUCT_CATALOG.md#business-rules); file này chỉ bổ sung validation nêu trong checklist/source mapping bên dưới.

## Workflow và State Transitions

Catalog → price resolution → Deal/Quotation → Accepted Quotation hoặc manual Order → lifecycle Order.

Chi tiết end-to-end nằm ở mục Related Workflows; state không được suy ra từ nhãn UI nếu controller/schema quy định khác.

## Permissions

Backend DocPerm, linked-record read checks và action-specific validation; frontend gating chỉ là UX.

Contract chung: [Permission Model](../../architecture/PERMISSION_MODEL.md).

## Source Mapping

| ID | Source reference | Bằng chứng mới trong checklist |
| --- | --- | --- |
| SALE-03 | pricing.py | 22/11 · PR #26 → main 082ba52. Bổ sung test ưu tiên Price List: explicit > Company > Contact > mặc định và fallback. Đây là test được thêm vào source, chưa có kết quả chạy suite trên site cuối. |

## Upstream Dependencies

- Customer, Deal, Product và Pricing.
- [Customer](../crm/CUSTOMER.md)
- [Product](PRODUCT_CATALOG.md)
- [Quotation](QUOTATION.md)

## Downstream Impact

- Email/PDF, Order và sales analytics.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 01 INDIVIDUAL SALES](../../workflows/WF_01_INDIVIDUAL_SALES.md)
- [WF 02 COMPANY SALES](../../workflows/WF_02_COMPANY_SALES.md)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| SALE-03 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| SALE-03 | Kiểm một SKU có giá riêng và một SKU fallback. Xác nhận bảng giá theo khách và so ca role bán hàng. |

## Known Limitations

- **SALE-03:** Source có nhưng vẫn phải theo acceptance status.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
