# Contact, Company & Customer 360

[← crm index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-crm-04"></a>
- `CRM-04` — Danh sách, chi tiết Contact và Company
<a id="feature-crm-05"></a>
- `CRM-05` — Hồ sơ khách tập trung và timeline đa kênh
<a id="feature-crm-10"></a>
- `CRM-10` — Hoàn thiện danh sách và chi tiết Company
<a id="feature-ext-01"></a>
- `EXT-01` — Một Contact đại diện nhiều Company
<a id="feature-ext-02"></a>
- `EXT-02` — Vai trò người liên hệ trong Deal
<a id="feature-ext-03"></a>
- `EXT-03` — Đánh dấu khách quay lại
<a id="feature-ext-31"></a>
- `EXT-31` — Lịch sử báo giá trên hồ sơ khách

## Mục đích nghiệp vụ

Danh sách, chi tiết Contact và Company; Hồ sơ khách tập trung và timeline đa kênh; Hoàn thiện danh sách và chi tiết Company; Một Contact đại diện nhiều Company; Vai trò người liên hệ trong Deal; Đánh dấu khách quay lại; Lịch sử báo giá trên hồ sơ khách. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| CRM-04 | Danh sách, chi tiết Contact và Company | R1 · Hồ sơ khách | P0 | Có list/detail Contact và Company. Company detail có hồ sơ liên quan và Tasks, Notes, Zalo OA. Lỗi phân trang và trạng thái UI ở CRM-10. | BA UC-01, FR-01–02 |
| CRM-05 | Hồ sơ khách tập trung và timeline đa kênh | R1 · Hồ sơ khách | P0 | Có hồ sơ và Activity theo từng bản ghi. API đọc Communication, tasks, notes, versions. Chưa thấy một màn tổng hợp quan hệ và hội thoại tất cả kênh theo khách. | BA UC-01, FR-02–05 |
| CRM-10 | Hoàn thiện danh sách và chi tiết Company | R1 · Hồ sơ khách | P1 | PR #24 đã sửa Company search và detail: tìm/lọc qua composable, dữ liệu tải trang và trạng thái loading/error; bổ sung điều hướng đến chi tiết từ danh sách. Cần nghiệm thu dữ liệu lớn và quyền. | Audit 18/11 · CRM-04, CRM-07 |
| EXT-01 | Một Contact đại diện nhiều Company | R1 · Hồ sơ khách | P1 | Contact chỉ có một Company. Quotation đối chiếu Company của Contact. | HubSpot · CRM CORE &APP A31:A33, A54, A86 · MVP |
| EXT-02 | Vai trò người liên hệ trong Deal | Nâng cấp · Hồ sơ khách | P2 | Schema Deal có một Contact, chưa thấy danh sách người tham gia theo vai trò. | SAP · Liên quan CRM-09 |
| EXT-03 | Đánh dấu khách quay lại | Nâng cấp · Dữ liệu khách | P2 | Có kiểm tra trùng và source_lead, chưa thấy nhãn yêu cầu mới của khách cũ. | Bitrix24 · CRM CORE &APP A13 · Future |
| EXT-31 | Lịch sử báo giá trên hồ sơ khách | R1 · Hồ sơ khách | P1 | Deal có tab Quotations. Chưa thấy danh sách báo giá theo khách trên Contact/Company. | CRM CORE &APP A161 · MVP · Nối CRM-05 |

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
| CRM-04 | router.js | 18/11 · 7105984 · router.js, DoubleTEntityDetail.vue. Browser chưa kiểm. |
| CRM-05 | api.py | Chưa có bằng chứng mới |
| CRM-10 | useDoubleTCompanies.js:75 | 22/11 · PR #24 merged vào main b996e72. Diff useDoubleTCompanies.js, CompaniesView.vue, DoubleTEntityDetail.vue và DealsListView.vue. Chưa có browser retest. |
| EXT-01 | doublet_contact.json | Chưa có bằng chứng mới |
| EXT-02 | doublet_deal.json | Chưa có bằng chứng mới |
| EXT-03 | doublet_lead.py | Chưa có bằng chứng mới |
| EXT-31 | DealQuotations.vue | Chưa có bằng chứng mới |

## Upstream Dependencies

- Lead source, customer identity và Frappe permission infrastructure.
- [Identity](IDENTITY_DUPLICATES.md)
- [Pricing](../sales/PRICING.md)
- [Quotation](../sales/QUOTATION.md)
- [Inbox](../contact-center/INBOX.md)

## Downstream Impact

- Pricing, Quotation, Order, Activities, Contact Center và Reports.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 01 INDIVIDUAL SALES](../../workflows/WF_01_INDIVIDUAL_SALES.md)
- [WF 02 COMPANY SALES](../../workflows/WF_02_COMPANY_SALES.md)
- [WF 07 WOOCOMMERCE SYNC](../../workflows/WF_07_WOOCOMMERCE_SYNC.md)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| CRM-04 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| CRM-05 | Có một phần | Cần làm | Checklist: Có một phần; Cần làm. Không suy ra runtime PASS. |
| CRM-10 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| EXT-01 | Có một phần | Cần làm | Checklist: Có một phần; Cần làm. Không suy ra runtime PASS. |
| EXT-02 | Chưa thấy | Đề xuất | Checklist: Chưa thấy; Đề xuất. Không suy ra runtime PASS. |
| EXT-03 | Chưa thấy | Đề xuất | Checklist: Chưa thấy; Đề xuất. Không suy ra runtime PASS. |
| EXT-31 | Có một phần | Cần làm | Checklist: Có một phần; Cần làm. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| CRM-04 | Dùng role dự kiến mở Contact/Company, kiểm bản ghi liên quan và đối chiếu đúng Deal. Chạy riêng ca sửa Company ở CRM-10. |
| CRM-05 | Hoàn thiện một hồ sơ mẫu có liên kết Lead/Deal, Email và Zalo OA theo quyền. Hiển thị tình trạng khi nguồn chưa đồng bộ. |
| CRM-10 | Kiểm tìm kiếm ngành/tên ngoài trang đầu, số kết quả, tải tiếp, lỗi 403/404, nút theo role và bố cục 360px trên main mới. |
| EXT-01 | Gắn hai Company, đặt một công ty chính và chọn đúng công ty mà Contact đại diện trên từng Deal/báo giá. |
| EXT-02 | Trong một Deal doanh nghiệp, gắn người ra quyết định, người vận hành và đầu mối báo giá. Giữ Contact chính. |
| EXT-03 | Gắn một Lead mới với Contact hiện có và mở lại được Deal trước. Không làm mất hai lịch sử. |
| EXT-31 | Từ hồ sơ khách lọc báo giá theo trạng thái/hạn. Bấm đúng mã và kiểm quyền theo hồ sơ. |

## Known Limitations

- **CRM-04:** Source có nhưng vẫn phải theo acceptance status.
- **CRM-05:** Có hồ sơ và Activity theo từng bản ghi. API đọc Communication, tasks, notes, versions. Chưa thấy một màn tổng hợp quan hệ và hội thoại tất cả kênh theo khách.
- **CRM-10:** Source có nhưng vẫn phải theo acceptance status.
- **EXT-01:** Contact chỉ có một Company. Quotation đối chiếu Company của Contact.
- **EXT-02:** Schema Deal có một Contact, chưa thấy danh sách người tham gia theo vai trò.
- **EXT-03:** Có kiểm tra trùng và source_lead, chưa thấy nhãn yêu cầu mới của khách cũ.
- **EXT-31:** Deal có tab Quotations. Chưa thấy danh sách báo giá theo khách trên Contact/Company.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
