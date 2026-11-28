# WooCommerce Integration

[← integration index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-r2-05"></a>
- `R2-05` — Đồng bộ Product/SKU/Variant với WooCommerce

## Mục đích nghiệp vụ

Đồng bộ Product/SKU/Variant với WooCommerce. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| R2-05 | Đồng bộ Product/SKU/Variant với WooCommerce | R2 · Tích hợp Catalog | P1 | Catalog nội bộ có source. Checklist cũ #19 ghi còn thiếu đồng bộ sản phẩm WordPress. Main chưa thấy code tích hợp Catalog này. | Đề cương · CHECKLIST cũ #19 |

## Data Model

Target/source IDs, signed request/event envelope, idempotency key và execution/audit record; business entity vẫn là source of truth.

Xem [Data Model](../../architecture/DATA_MODEL.md) và [Data Ownership](../../architecture/DATA_OWNERSHIP.md).

## Business Rules

Các validation riêng được xác định từ source/checklist trong bảng dưới đây; quy tắc xuyên module được quản lý tại [Data Ownership](../../architecture/DATA_OWNERSHIP.md) và [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Workflow và State Transitions

Authenticate/verify → deduplicate → map identity → upsert/action → log/retry/DLQ.

Chi tiết end-to-end nằm ở mục Related Workflows; state không được suy ra từ nhãn UI nếu controller/schema quy định khác.

## Permissions

Least-privilege integration principal, protected secrets, signature và action-level backend checks.

Contract chung: [Permission Model](../../architecture/PERMISSION_MODEL.md).

## Source Mapping

| ID | Source reference | Bằng chứng mới trong checklist |
| --- | --- | --- |
| R2-05 | ProductsView.vue | Chưa có bằng chứng mới |

## Upstream Dependencies

- External provider và integration configuration.
- [Customer Identity](../crm/IDENTITY_DUPLICATES.md)
- [Order](../sales/ORDER.md)

## Downstream Impact

- Customer/Lead/Order, notification và automation.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 07 WOOCOMMERCE SYNC](../../workflows/WF_07_WOOCOMMERCE_SYNC.md)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| R2-05 | Chưa thấy | Cần làm | Checklist: Chưa thấy; Cần làm. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| R2-05 | Chốt chiều đồng bộ và nguồn giá. Đối chiếu một SKU và một biến thể giữa Woo và CRM, kiểm cập nhật lặp. |

## Known Limitations

- **R2-05:** Catalog nội bộ có source. Checklist cũ #19 ghi còn thiếu đồng bộ sản phẩm WordPress. Main chưa thấy code tích hợp Catalog này.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
