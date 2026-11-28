# Order Management

[← sales index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-ord-01"></a>
- `ORD-01` — Danh sách, chi tiết và tạo/sửa Order thủ công
<a id="feature-ord-02"></a>
- `ORD-02` — Tạo một Order từ Quotation và giữ dữ liệu giá đã lưu
<a id="feature-ord-03"></a>
- `ORD-03` — Hoàn tất hoặc hủy Order khi báo giá nguồn thay đổi
<a id="feature-ord-04"></a>
- `ORD-04` — Lọc Deal theo Customer Type và Contact/Company
<a id="feature-ord-05"></a>
- `ORD-05` — Quy tắc trạng thái Quotation được phép tạo Order
<a id="feature-ord-06"></a>
- `ORD-06` — Quyền xem và sửa Order của Sales và quản lý
<a id="feature-ord-07"></a>
- `ORD-07` — Nghiệm thu Order trên bản main đã gộp

## Mục đích nghiệp vụ

Danh sách, chi tiết và tạo/sửa Order thủ công; Tạo một Order từ Quotation và giữ dữ liệu giá đã lưu; Hoàn tất hoặc hủy Order khi báo giá nguồn thay đổi; Lọc Deal theo Customer Type và Contact/Company; Quy tắc trạng thái Quotation được phép tạo Order; Quyền xem và sửa Order của Sales và quản lý; Nghiệm thu Order trên bản main đã gộp. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| ORD-01 | Danh sách, chi tiết và tạo/sửa Order thủ công | R1 · Đơn hàng | P0 | main f5b91c3 có menu, danh sách, chi tiết và tạo/sửa Draft. Danh sách có tìm mã, lọc trạng thái và tải thêm. | Rà nhánh Order 17/11 · SALE-01–03, SALE-05 |
| ORD-02 | Tạo một Order từ Quotation và giữ dữ liệu giá đã lưu | R1 · Đơn hàng | P0 | main có bản sao từng dòng giá/chiết khấu, đối chiếu tổng khi tạo đơn. API khóa Quotation và trả Order cũ khi đã tạo. | Rà nhánh Order 17/11 · SALE-05, SALE-06 |
| ORD-03 | Hoàn tất hoặc hủy Order khi báo giá nguồn thay đổi | R1 · Đơn hàng | P0 | Kiểm Quotation nguồn khi tạo Order; chuyển trạng thái về sau giữ snapshot. | Rà nhánh Order 17/11 · SALE-06 |
| ORD-04 | Lọc Deal theo Customer Type và Contact/Company | R1 · Đơn hàng | P0 | Order lọc Contact/Deal theo khách, xóa Deal không hợp lệ, backend validate. | Rà nhánh Order 17/11 · SALE-04 |
| ORD-05 | Quy tắc trạng thái Quotation được phép tạo Order | R1 · Đơn hàng | P0 | Chỉ Quotation Accepted được tạo Order mới; giữ Order đã liên kết, khóa chống trùng và kiểm snapshot. | Rà nhánh Order 17/11 · SALE-06 |
| ORD-06 | Quyền xem và sửa Order của Sales và quản lý | R1 · Đơn hàng | P0 | Có Delete Draft theo quyền và ẩn menu nếu không có read; quyền theo owner còn cần chốt. | Rà nhánh Order 17/11 · CRM-07, EXT-27 |
| ORD-07 | Nghiệm thu Order trên bản main đã gộp | R1 · Đơn hàng | P0 | Đã build/migrate bản tích hợp; user báo review UI xong, chưa có log E2E từng role. | Rà nhánh Order 17/11 · QA-01, QA-02 |

## Data Model

Product/Category/Variant, Price List/Settings, Quotation/Items/Approval và Order/Items; item thương mại lưu snapshot.

Xem [Data Model](../../architecture/DATA_MODEL.md) và [Data Ownership](../../architecture/DATA_OWNERSHIP.md).

## Business Rules

**Tài liệu quản lý chính cho nhóm quy tắc này:** file hiện tại.

`Draft→Confirmed→Completed`, Draft/Confirmed→Cancelled; Completed/Cancelled terminal. Accepted Quotation mới tạo Order; unique quotation + row lock ngăn trùng và retry trả existing readable Order. Sau Draft khóa snapshot; chỉ Draft được xóa.

## Workflow và State Transitions

Catalog → price resolution → Deal/Quotation → Accepted Quotation hoặc manual Order → lifecycle Order.

Chi tiết end-to-end nằm ở mục Related Workflows; state không được suy ra từ nhãn UI nếu controller/schema quy định khác.

## Permissions

Backend DocPerm, linked-record read checks và action-specific validation; frontend gating chỉ là UX.

Contract chung: [Permission Model](../../architecture/PERMISSION_MODEL.md).

## Source Mapping

| ID | Source reference | Bằng chứng mới trong checklist |
| --- | --- | --- |
| ORD-01 | OrderForm.vue | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. Order list search/filter/load more và form responsive được cải tiến. |
| ORD-02 | doublet_order.py | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. Accepted-only, snapshot và khóa chống tạo trùng. |
| ORD-03 | doublet_order.py | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. |
| ORD-04 | OrderForm.vue | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. |
| ORD-05 | QuotationForm.vue | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. |
| ORD-06 | doublet_order.json | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. |
| ORD-07 | test_doublet_order.py | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. |

## Upstream Dependencies

- Customer, Deal, Product và Pricing.
- [Quotation](QUOTATION.md)
- [Customer](../crm/CUSTOMER.md)
- [Sales Performance](../analytics/SALES_PERFORMANCE.md)

## Downstream Impact

- Email/PDF, Order và sales analytics.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 01 INDIVIDUAL SALES](../../workflows/WF_01_INDIVIDUAL_SALES.md)
- [WF 02 COMPANY SALES](../../workflows/WF_02_COMPANY_SALES.md)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| ORD-01 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| ORD-02 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| ORD-03 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| ORD-04 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| ORD-05 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| ORD-06 | Có một phần | Cần kiểm | Checklist: Có một phần; Cần kiểm. Không suy ra runtime PASS. |
| ORD-07 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| ORD-01 | Tạo/sửa Draft cho Personal và Company. Kiểm giá, chiết khấu, tổng sau khi tải lại. Thử tìm/lọc, hơn 20 đơn và màn hình hẹp. |
| ORD-02 | Đổi bảng giá sau khi lưu báo giá nhiều dòng rồi tạo Order. So từng dòng, chiết khấu và tổng. Bấm nhanh hoặc tạo từ hai phiên, kết quả chỉ có một mã Order. |
| ORD-03 | Thử đổi khách nguồn rồi Confirm/Complete/Cancel; đối chiếu snapshot. |
| ORD-04 | Thử Personal/Company, đổi khách và API sai liên kết. |
| ORD-05 | Kiểm UI/API cả bốn trạng thái và tạo đồng thời. |
| ORD-06 | Kiểm 2 Sales, Manager, System Manager, Guest và phạm vi owner. |
| ORD-07 | Kiểm ORD-01–06 và Lead → Deal → Quotation → Order theo role. |

## Known Limitations

- **ORD-01:** Source có nhưng vẫn phải theo acceptance status.
- **ORD-02:** Source có nhưng vẫn phải theo acceptance status.
- **ORD-03:** Source có nhưng vẫn phải theo acceptance status.
- **ORD-04:** Source có nhưng vẫn phải theo acceptance status.
- **ORD-05:** Source có nhưng vẫn phải theo acceptance status.
- **ORD-06:** Có Delete Draft theo quyền và ẩn menu nếu không có read; quyền theo owner còn cần chốt.
- **ORD-07:** Source có nhưng vẫn phải theo acceptance status.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
