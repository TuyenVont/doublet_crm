# Email & Quotation Delivery

[← contact-center index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-r2-04"></a>
- `R2-04` — Lượt 1 · Email báo giá trên Lead, Deal và Quotation
<a id="feature-ext-22"></a>
- `EXT-22` — Mẫu email bán hàng dùng lại
<a id="feature-cc-01"></a>
- `CC-01` — Lượt 2 · Kênh Email trong Inbox của Contact Center

## Mục đích nghiệp vụ

Lượt 1 · Email báo giá trên Lead, Deal và Quotation; Mẫu email bán hàng dùng lại; Lượt 2 · Kênh Email trong Inbox của Contact Center. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| R2-04 | Lượt 1 · Email báo giá trên Lead, Deal và Quotation | R2 · Email | P0 | Đã triển khai Lead, Deal và Quotation dùng chung Communication. PASS backend 8/8, quyền đọc, chống trùng, hai Deal cùng khách và production build. | BA SCP-07, FR-03, FR-31 |
| EXT-22 | Mẫu email bán hàng dùng lại | Nâng cấp · Email | P2 | Form báo giá có soạn nội dung gửi, chưa thấy thư viện mẫu chọn theo tình huống. | HubSpot · Nối SALE-07 |
| CC-01 | Lượt 2 · Kênh Email trong Inbox của Contact Center | Contact Center · Open Channels | P1 | Inbox trên main hiện xử lý Zalo OA mock. Email báo giá đã hiện trên hồ sơ và Quotation ở R2-04. Email trong Inbox chung còn cần bổ sung. | Bitrix24 · Open Channels |

## Data Model

`Communication`, `Conversation`, `Message`, `Conversation Event`, `Call Log`, `Call Event`, `Call AI Summary`, private `File`.

Xem [Data Model](../../architecture/DATA_MODEL.md) và [Data Ownership](../../architecture/DATA_OWNERSHIP.md).

## Business Rules

Các validation riêng được xác định từ source/checklist trong bảng dưới đây; quy tắc xuyên module được quản lý tại [Data Ownership](../../architecture/DATA_OWNERSHIP.md) và [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Workflow và State Transitions

Inbound/outbound event → link customer → assign/handle → resolve; derived Task/Note giữ link về nguồn.

### Quotation Email API compatibility

- `get_quotation_email_context(name, search)` kiểm Quotation read, ưu tiên readable Contact rồi Company và chỉ search Contact có email trong cùng Company.
- `get_quotation_emails(name)` kiểm Quotation, Communication và File read; Communication state ưu tiên Email Queue, thiếu evidence giữ `Unknown`.
- `send_quotation_email` yêu cầu read/write + matching `modified`; expiry cần explicit confirmation; tạo một Communication/Email Queue và queue job có dedupe.
- `reply_quotation_email` chỉ reply Received Email cùng Quotation; recipient lấy từ inbound sender, caller không được đổi. PDF delivery không tự đổi lifecycle.

Email history giữ exact Communication reference/thread; customer-wide view không được trộn email của hai Deal chỉ vì cùng customer. Xem [Customer history continuity](../../architecture/BUSINESS_FLOW_CONTRACT.md#customer-history-continuity).

Chi tiết end-to-end nằm ở mục Related Workflows; state không được suy ra từ nhãn UI nếu controller/schema quy định khác.

## Permissions

Permission hooks theo assignment/manager/API principal; attachment và linked customer phải kiểm quyền.

Contract chung: [Permission Model](../../architecture/PERMISSION_MODEL.md).

## Source Mapping

| ID | Source reference | Bằng chứng mới trong checklist |
| --- | --- | --- |
| R2-04 | QuotationEmails.vue:192 | 17/11 PASS · CRM-NEW-LEAD-01<br>Received, 1 bản ghi sau pull lại.<br>QUO-00005: 4 thư mỗi scope API.<br>Browser: NOT TESTED.<br>18/11 · 7105984 có luồng đọc Communication theo hồ sơ và báo giá. Chưa test browser. |
| EXT-22 | QuotationForm.vue | Chưa có bằng chứng mới |
| CC-01 | router.js | Ca nghiệm thu: CRM-NEW-LEAD-01 → tạo/gắn Lead → View Lead → Emails. Kiểm thêm reply QUO-00005 và hồi quy tab Zalo OA. |

## Upstream Dependencies

- Email/Zalo/telephony provider và customer identity.
- [Quotation](../sales/QUOTATION.md)
- [Inbox](INBOX.md)
- [Customer](../crm/CUSTOMER.md)

## Downstream Impact

- Customer history, Activities và Contact Center analytics.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 03 QUOTATION EMAIL](../../workflows/WF_03_QUOTATION_EMAIL.md)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| R2-04 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| EXT-22 | Chưa thấy | Đề xuất | Checklist: Chưa thấy; Đề xuất. Không suy ra runtime PASS. |
| CC-01 | Chưa thấy | Cần làm | Checklist: Chưa thấy; Cần làm. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| R2-04 | Kiểm trên browser bằng Sales User: mở QUO-00005, Deal và Lead nguồn. Cả ba tab Emails hiện đúng 4 thư gửi/nhận, mã QUO bấm được và Deal khác cùng khách không lẫn thư. |
| EXT-22 | Chọn mẫu báo giá hoặc nhắc phản hồi. Điền tên/số báo giá và cho sửa trước khi gửi. |
| CC-01 | Lọc All / Unlinked / Linked. Mở chuỗi, reply và mở Lead/Deal/Quotation được liên kết. Thư mới: Create Lead điền sẵn tên/email/nguồn hoặc Link to existing Lead. Kiểm quyền, không trùng và thấy thư trong Lead → Emails. |

## Known Limitations

- **R2-04:** Source có nhưng vẫn phải theo acceptance status.
- **EXT-22:** Form báo giá có soạn nội dung gửi, chưa thấy thư viện mẫu chọn theo tình huống.
- **CC-01:** Inbox trên main hiện xử lý Zalo OA mock. Email báo giá đã hiện trên hồ sơ và Quotation ở R2-04. Email trong Inbox chung còn cần bổ sung.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
