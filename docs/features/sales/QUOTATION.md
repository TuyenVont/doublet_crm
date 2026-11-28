# Quotation Management

[← sales index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-sale-04"></a>
- `SALE-04` — Lập Quotation từ Deal và danh sách
<a id="feature-sale-05"></a>
- `SALE-05` — Tính chiết khấu %, số tiền và làm tròn
<a id="feature-sale-06"></a>
- `SALE-06` — Snapshot, dữ liệu cũ và trạng thái báo giá
<a id="feature-sale-07"></a>
- `SALE-07` — Xuất và gửi PDF báo giá qua email
<a id="feature-sale-10"></a>
- `SALE-10` — Chọn sản phẩm từ Catalog trong Quotation
<a id="feature-sale-11"></a>
- `SALE-11` — Đơn giản hóa chọn khách, Deal và bảng giá
<a id="feature-ext-05"></a>
- `EXT-05` — Gắn sản phẩm quan tâm ngay trên Deal
<a id="feature-ext-06"></a>
- `EXT-06` — Tạo báo giá từ Lead đã Qualified
<a id="feature-ext-07"></a>
- `EXT-07` — Hiển thị và lọc báo giá hết hạn
<a id="feature-ext-08"></a>
- `EXT-08` — Mẫu báo giá theo nhóm sản phẩm/dịch vụ
<a id="feature-ext-09"></a>
- `EXT-09` — Duyệt chiết khấu vượt ngưỡng
<a id="feature-new-01"></a>
- `NEW-01` — Tạo bản sửa từ báo giá đã gửi

## Mục đích nghiệp vụ

Lập Quotation từ Deal và danh sách; Tính chiết khấu %, số tiền và làm tròn; Snapshot, dữ liệu cũ và trạng thái báo giá; Xuất và gửi PDF báo giá qua email; Chọn sản phẩm từ Catalog trong Quotation; Đơn giản hóa chọn khách, Deal và bảng giá; Gắn sản phẩm quan tâm ngay trên Deal; Tạo báo giá từ Lead đã Qualified; Hiển thị và lọc báo giá hết hạn; Mẫu báo giá theo nhóm sản phẩm/dịch vụ; Duyệt chiết khấu vượt ngưỡng; Tạo bản sửa từ báo giá đã gửi. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| SALE-04 | Lập Quotation từ Deal và danh sách | R1 · Báo giá | P0 | Có QuotationForm, đường dẫn hai điểm vào, lọc Deal theo khách và validate liên kết ở backend. | Đề cương · Báo cáo 08–14/11 |
| SALE-05 | Tính chiết khấu %, số tiền và làm tròn | R1 · Báo giá | P0 | Có preview và bộ tính backend cho USD 2 chữ số, Amount/Percentage và dữ liệu dòng. | Báo cáo 08–14/11 · Test repo |
| SALE-06 | Snapshot, dữ liệu cũ và trạng thái báo giá | R1 · Báo giá | P0 | 23/11 · PR #26 (082ba52, 25f3aea) chỉnh phép kiểm snapshot Quotation/line_total và bổ sung test thay đổi Product/Price List sau Accepted, nhiều dòng giá. Test được commit lên main; chưa xác nhận đã chạy toàn bộ trên site bàn giao. | Báo cáo 08–14/11 · Test repo |
| SALE-07 | Xuất và gửi PDF báo giá qua email | R1 · Báo giá | P0 | Có xuất PDF và Send by Email trên main. Tuyền đã xác nhận nhận một email thử kèm PDF trong trao đổi 13/11. Mark as Sent là thao tác riêng. | Báo cáo 08–14/11 · PR #21 |
| SALE-10 | Chọn sản phẩm từ Catalog trong Quotation | Nâng cấp · Báo giá | P1 | Browse Catalog có ảnh, tìm tên/SKU, lọc Category chính/phụ, chọn nhiều SKU và chỉnh số lượng. Dòng cũ giữ giá tay/chiết khấu; tổng cập nhật khi định giá xong. | Đợt 3 · Tham khảo Odoo Quotation · SALE-03/04 |
| SALE-11 | Đơn giản hóa chọn khách, Deal và bảng giá | R1 · Báo giá | P0 | Form dẫn theo thứ tự Customer Type → Contact/Company → Deal tùy chọn → Price List. Tạo từ Deal tự điền khách. Unlink cho phép đổi khách và lọc lại lựa chọn. | Phản hồi Tuyền 19/11 · SALE-03/04/06 · Làm trước SALE-10 |
| EXT-05 | Gắn sản phẩm quan tâm ngay trên Deal | R1 · Deal | P1 | 26/11 · PR #34 đã merge main 7221e0e. Có Products tab trên Deal, chọn Standard/Variant, lưu số lượng và giá tham khảo; nạp dòng vào Quotation Draft theo giá hiện hành, không đổi Deal Amount/stage. | Odoo · CRM CORE &APP A53, A72 · MVP |
| EXT-06 | Tạo báo giá từ Lead đã Qualified | R1 · Báo giá | P1 | 26/11 · PR #34 đã merge main 7221e0e. Lead QUALIFIED/CONVERTED có Create Quotation; hướng dẫn conversion nếu thiếu hồ sơ, chọn Deal khi có nhiều, truy nguồn qua Deal.source_lead; không tự tạo hồ sơ. | Odoo · CRM CORE &APP A12, A84 · MVP |
| EXT-07 | Hiển thị và lọc báo giá hết hạn | R1 · Báo giá | P1 | Badge/lọc Expired theo ngày site; giữ trạng thái Accepted/Rejected. | RESEARCH A51 · CORE A93:A94 |
| EXT-08 | Mẫu báo giá theo nhóm sản phẩm/dịch vụ | Nâng cấp · Báo giá | P2 | Quotation Template và Template Item; nạp dòng/điều khoản vào Draft, tính giá hiện hành. | Odoo · Roadmap sau MVP |
| EXT-09 | Duyệt chiết khấu vượt ngưỡng | Nâng cấp · Báo giá | P2 | Ngưỡng duyệt chiết khấu cấu hình; approval riêng, kiểm trước gửi email/Mark as Sent, giữ lịch sử Accepted. | SAP · Ứng viên nâng cấp · SALE-05 |
| NEW-01 | Tạo bản sửa từ báo giá đã gửi | Đề xuất sau khi lõi đạt | P2 | Lifecycle hiện khóa trường/dòng sau Draft. Chưa thấy luồng tạo revision có liên kết từ báo giá đã gửi. | Đề xuất từ review UI/code |

## Data Model

Product/Category/Variant, Price List/Settings, Quotation/Items/Approval và Order/Items; item thương mại lưu snapshot.

Xem [Data Model](../../architecture/DATA_MODEL.md) và [Data Ownership](../../architecture/DATA_OWNERSHIP.md).

## Business Rules

**Tài liệu quản lý chính cho nhóm quy tắc này:** file hiện tại.

State `Draft/Sent/Accepted/Rejected`; expiry chỉ derived cho Draft/Sent. Sau Draft khóa snapshot tài chính. Quantity > 0, price ≥ 0, percent 0–100; `0` là giá hợp lệ. Approval chống self-approve và invalid khi tài chính đổi. Email/Mark Sent dùng cùng guard. Revision chưa có model.

## Workflow và State Transitions

Catalog → price resolution → Deal/Quotation → Accepted Quotation hoặc manual Order → lifecycle Order.

Chi tiết end-to-end nằm ở mục Related Workflows; state không được suy ra từ nhãn UI nếu controller/schema quy định khác.

## Permissions

Backend DocPerm, linked-record read checks và action-specific validation; frontend gating chỉ là UX.

Contract chung: [Permission Model](../../architecture/PERMISSION_MODEL.md).

## Source Mapping

| ID | Source reference | Bằng chứng mới trong checklist |
| --- | --- | --- |
| SALE-04 | QuotationForm.vue | 18/11 · 7105984 · QuotationForm + validate backend có code. Chưa chạy browser. |
| SALE-05 | doublet_quotation.py | 22/11 · PR #26 → main 082ba52. Sửa assertion Decimal/float của PDF USD $34.98, thêm kiểm tra chiết khấu và số dòng trong test. Chưa có kết quả chạy test trên site cuối. |
| SALE-06 | doublet_quotation.py | 22/11 · PR #26 → main 082ba52. Diff doublet_quotation.py và test_doublet_quotation.py kiểm snapshot đầy đủ, gồm line_total, giá, discount và tổng. Test mới có trong repo; chưa chứng minh PASS trên site cuối. |
| SALE-07 | quotation_pdf.py | 17/11 · PASS trên site test: PDF QUO-00005 gửi tự động; reply Received gắn đúng báo giá. Còn kiểm build bàn giao theo role.<br>18/11 · Rà source 7105984 xác nhận PDF/Email có code. Chưa gửi lại trong lượt audit. |
| SALE-10 | QuotationForm.vue | 19/11 · PR #25 → main c2edcb6. Chrome PASS trên form chưa lưu: lọc Category phụ, giữ lựa chọn và tên/SKU, đúng Retail/fallback và tổng $57,115.56. Product Catalog 6/6, Quotation 9/9, build PASS. |
| SALE-11 | QuotationForm.vue | 19/11 · PR #25 → main c2edcb6. Chrome PASS với Administrator: điền và khóa khách từ Deal, Unlink rồi đổi Company, dọn và lọc lại Contact/Deal, Automatic dùng Retail. Sales lưu/mở lại chưa kiểm. |
| EXT-05 | sales_completion.py · Deal Products | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. PR #34 + #35: controller Deal Product được bổ sung, migrate PASS; persistence/role cần kiểm. |
| EXT-06 | FrappeLead.vue · Create Quotation | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. PR #34 được bảo toàn khi hợp nhất QuotationForm; kiểm flow từng role. |
| EXT-07 | doublet_quotation.json | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. |
| EXT-08 | quotation_pdf.py | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. |
| EXT-09 | doublet_quotation.py | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. |
| NEW-01 | doublet_quotation.py | Chưa có bằng chứng mới |

## Upstream Dependencies

- Customer, Deal, Product và Pricing.
- [Deal](../crm/DEAL_PIPELINE.md)
- [Product](PRODUCT_CATALOG.md)
- [Pricing](PRICING.md)
- [Order](ORDER.md)
- [Email](../contact-center/EMAIL.md)
- [Analytics](../analytics/QUOTATION_ORDER.md)

## Downstream Impact

- Email/PDF, Order và sales analytics.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 01 INDIVIDUAL SALES](../../workflows/WF_01_INDIVIDUAL_SALES.md)
- [WF 02 COMPANY SALES](../../workflows/WF_02_COMPANY_SALES.md)
- [WF 03 QUOTATION EMAIL](../../workflows/WF_03_QUOTATION_EMAIL.md)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| SALE-04 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| SALE-05 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| SALE-06 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| SALE-07 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| SALE-10 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| SALE-11 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| EXT-05 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| EXT-06 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| EXT-07 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| EXT-08 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| EXT-09 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| NEW-01 | Đề xuất | Đề xuất | Checklist: Đề xuất; Đề xuất. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| SALE-04 | Tạo báo giá từ cả hai điểm vào bằng Sales User. Kiểm hai ngữ cảnh Personal/Company và trường hợp đổi khách. |
| SALE-05 | Từ 2 × $19.99, giảm $5 ra $34.98, giảm 10% ra $35.98. Đối chiếu preview, lưu và PDF. |
| SALE-06 | Chạy test_doublet_quotation + test_pricing; trong browser lưu báo giá nhiều dòng, đổi giá Catalog, chuyển Accepted và đối chiếu snapshot, tổng USD, PDF và quyền chỉnh sửa. |
| SALE-07 | Dùng Sales User gửi PDF trên build bàn giao. So tổng PDF, 1 Communication và 1 mục Email Queue, Queued → Sent/Failed và reply cùng thread. |
| SALE-10 | Dùng Sales User lưu một Quotation Draft QA rồi mở lại. So SKU, số lượng, giá Retail, giá fallback, giá tay, chiết khấu và tổng. So tổng PDF nếu có quyền xuất. |
| SALE-11 | Retest bằng Sales User cho Personal và Company, từ Deal và từ danh sách. Lưu/mở lại báo giá QA, kiểm đổi khách và việc giữ giá đã lưu hoặc giá tay. |
| EXT-05 | Migrate DocType mới; kiểm lưu/reload, vai trò, giá và snapshot. Rà việc validate sản phẩm inactive khi sửa Deal/chuyển stage, response cũ, modified bắt buộc và quyền field. |
| EXT-06 | Kiểm Qualified trước/sau conversion, Personal/Company, nhiều Deal, role và lưu Draft đúng khách; rà giới hạn 100 Deal và quyền field. Không tạo trùng hồ sơ. |
| EXT-07 | Kiểm biên ngày, lọc và trạng thái cuối; user đã thấy bộ lọc trước tích hợp. |
| EXT-08 | Kiểm tạo/sửa mẫu, nạp và ghi đè, giá và quyền. |
| EXT-09 | Kiểm ngưỡng, quyền duyệt, snapshot và gửi thực tế. |
| NEW-01 | Từ báo giá đã gửi, tạo Draft mới tham chiếu bản gốc. Sửa số lượng/giảm giá rồi đối chiếu bản gốc vẫn giữ snapshot. |

## Known Limitations

- **SALE-04:** Source có nhưng vẫn phải theo acceptance status.
- **SALE-05:** Source có nhưng vẫn phải theo acceptance status.
- **SALE-06:** Source có nhưng vẫn phải theo acceptance status.
- **SALE-07:** Source có nhưng vẫn phải theo acceptance status.
- **SALE-10:** Source có nhưng vẫn phải theo acceptance status.
- **SALE-11:** Source có nhưng vẫn phải theo acceptance status.
- **EXT-05:** Source có nhưng vẫn phải theo acceptance status.
- **EXT-06:** Source có nhưng vẫn phải theo acceptance status.
- **EXT-07:** Source có nhưng vẫn phải theo acceptance status.
- **EXT-08:** Source có nhưng vẫn phải theo acceptance status.
- **EXT-09:** Source có nhưng vẫn phải theo acceptance status.
- **NEW-01:** Lifecycle hiện khóa trường/dòng sau Draft. Chưa thấy luồng tạo revision có liên kết từ báo giá đã gửi.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
