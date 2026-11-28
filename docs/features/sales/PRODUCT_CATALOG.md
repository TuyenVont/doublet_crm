# Product Catalog

[← sales index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-sale-01"></a>
- `SALE-01` — Category chính/phụ và Product Standard
<a id="feature-sale-02"></a>
- `SALE-02` — Template và Product Variant
<a id="feature-sale-08"></a>
- `SALE-08` — Ảnh sản phẩm và chế độ List/Grid
<a id="feature-sale-09"></a>
- `SALE-09` — Trang chi tiết Product và danh sách Variant

## Mục đích nghiệp vụ

Category chính/phụ và Product Standard; Template và Product Variant; Ảnh sản phẩm và chế độ List/Grid; Trang chi tiết Product và danh sách Variant. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| SALE-01 | Category chính/phụ và Product Standard | R1 · Catalog | P0 | Controller kiểm danh mục và có sản phẩm Standard. Giao diện có tìm theo tên/SKU, lọc danh mục/trạng thái. | Đề cương · Báo cáo 08–14/11 |
| SALE-02 | Template và Product Variant | R1 · Catalog | P0 | 23/11 · PR #26 (082ba52) bổ sung/chỉnh fixture test Product Template/Variant (mặc định tham số có thể override); mã nguồn và test có trong main 4d835a9. Chưa có kết quả chạy lại bộ test hoặc thao tác browser của lượt cập nhật. | Đề cương · Báo cáo 08–14/11 |
| SALE-08 | Ảnh sản phẩm và chế độ List/Grid | Nâng cấp · Catalog | P1 | Có ảnh đại diện, thumbnail, List/Grid và lọc Category chính/phụ trước phân trang. Variant dùng ảnh riêng, ảnh Template hoặc ảnh mặc định. | Đợt 1 · Tham khảo Odoo Products · SALE-01/02 |
| SALE-09 | Trang chi tiết Product và danh sách Variant | Nâng cấp · Catalog | P1 | Có trang chi tiết Product từ List/Grid, bảng Variant theo Template, liên kết hai chiều và nút Edit theo quyền ghi. | Đợt 2 · Tham khảo Odoo Products · SALE-02 |

## Data Model

Product/Category/Variant, Price List/Settings, Quotation/Items/Approval và Order/Items; item thương mại lưu snapshot.

Xem [Data Model](../../architecture/DATA_MODEL.md) và [Data Ownership](../../architecture/DATA_OWNERSHIP.md).

## Business Rules

**Tài liệu quản lý chính cho nhóm quy tắc này:** file hiện tại.

SKU unique, trim và không đổi sau creation. `Standard` không có variant fields; `Template` không sellable; `Variant` cần Template, attributes và unique `variant_key`. Product sellable khi active và không phải Template. Category chính luôn thuộc child assignments.

## Workflow và State Transitions

Catalog → price resolution → Deal/Quotation → Accepted Quotation hoặc manual Order → lifecycle Order.

Chi tiết end-to-end nằm ở mục Related Workflows; state không được suy ra từ nhãn UI nếu controller/schema quy định khác.

## Permissions

Backend DocPerm, linked-record read checks và action-specific validation; frontend gating chỉ là UX.

Contract chung: [Permission Model](../../architecture/PERMISSION_MODEL.md).

## Source Mapping

| ID | Source reference | Bằng chứng mới trong checklist |
| --- | --- | --- |
| SALE-01 | doublet_product.py | 18/11 · 7105984 · Có CRUD Product/Category và controller. UI và thao tác chưa kiểm lại. |
| SALE-02 | doublet_product.py | 18/11 · 7105984 · Kiểm controller Product. Chưa thử tạo Variant trên browser. |
| SALE-08 | ProductsView.vue | 19/11 · PR #25 → main c2edcb6. Chrome PASS lọc Category phụ Vận hành và giữ kết quả khi đổi List → Grid → List. Thao tác ảnh và kế thừa chưa test trên site. |
| SALE-09 | ProductDetailView.vue | 19/11 · PR #25 → main c2edcb6. Chrome PASS điều hướng Template → Variant → Template. Query Variant và test quyền backend PASS. Ảnh có dữ liệu và quyền Edit thực tế còn cần kiểm Chrome. |

## Upstream Dependencies

- Customer, Deal, Product và Pricing.
- [Deal](../crm/DEAL_PIPELINE.md)
- [Pricing](PRICING.md)
- [Quotation](QUOTATION.md)
- [Order](ORDER.md)

## Downstream Impact

- Email/PDF, Order và sales analytics.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 01 INDIVIDUAL SALES](../../workflows/WF_01_INDIVIDUAL_SALES.md)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| SALE-01 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| SALE-02 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| SALE-08 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| SALE-09 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| SALE-01 | Tạo và sửa sản phẩm mẫu. Chọn nhiều Category, bỏ Category phụ và xác nhận Category chính giữ đúng. |
| SALE-02 | Chạy test_doublet_product trên site target; tạo Template và 2 Variant, thử trùng tổ hợp/SKU, ảnh kế thừa và chọn Variant được phép bán vào Quotation bằng Sales User. |
| SALE-08 | Trên site đã migrate field image, kiểm thêm/thay/gỡ ảnh của sản phẩm QA, ảnh kế thừa và ảnh riêng của Variant trên List/Grid. Kiểm hiển thị màn hẹp và Load More. |
| SALE-09 | Kiểm trang chi tiết bằng tài khoản chỉ đọc và sản phẩm có ảnh. Thử Edit với tài khoản có quyền và kiểm Template chưa có Variant. |

## Known Limitations

- **SALE-01:** Source có nhưng vẫn phải theo acceptance status.
- **SALE-02:** Source có nhưng vẫn phải theo acceptance status.
- **SALE-08:** Source có nhưng vẫn phải theo acceptance status.
- **SALE-09:** Source có nhưng vẫn phải theo acceptance status.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
