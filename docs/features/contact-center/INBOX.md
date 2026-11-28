# Contact Center Inbox & Zalo OA

[← contact-center index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-r2-01"></a>
- `R2-01` — Tiếp nhận và lưu tin nhắn OA
<a id="feature-r2-02"></a>
- `R2-02` — Inbox, lịch sử và phản hồi OA
<a id="feature-r2-03"></a>
- `R2-03` — Tạo hoặc cập nhật Lead từ OA
<a id="feature-ext-19"></a>
- `EXT-19` — Conversation/Message dùng chung và OA adapter
<a id="feature-ext-20"></a>
- `EXT-20` — Phân công và bàn giao hội thoại OA
<a id="feature-ext-21"></a>
- `EXT-21` — Đo thời gian phản hồi đầu tiên của OA
<a id="feature-cc-02"></a>
- `CC-02` — Trạng thái xử lý hội thoại
<a id="feature-cc-03"></a>
- `CC-03` — Phân quyền hàng đợi và cấu hình kênh
<a id="feature-cc-04"></a>
- `CC-04` — Tự động phân công hội thoại theo hàng đợi
<a id="feature-cc-05"></a>
- `CC-05` — Giờ làm việc và trả lời ngoài giờ
<a id="feature-cc-06"></a>
- `CC-06` — Mẫu trả lời nhanh trong Inbox
<a id="feature-cc-07"></a>
- `CC-07` — Cảnh báo hội thoại chờ quá lâu
<a id="feature-cc-08"></a>
- `CC-08` — Đánh giá hỗ trợ sau khi đóng hội thoại
<a id="feature-new-03"></a>
- `NEW-03` — Hàng chờ gắn hội thoại chưa rõ khách

## Mục đích nghiệp vụ

Tiếp nhận/lưu tin OA, Inbox dùng chung, định danh customer, phân công, lifecycle và response metrics. Realtime và automatic Lead là target riêng trong [Business Flow Contract](../../architecture/BUSINESS_FLOW_CONTRACT.md), không phải implementation hiện tại.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| R2-01 | Tiếp nhận và lưu tin nhắn OA | R2 · Zalo OA | P0 | R2-01–R2-03: Chưa có Zalo OA để kết nối thật. Chờ kiểm thử nhận/gửi tin và liên kết Lead qua OA thật.<br>Luồng mock đã lưu tin vào đúng hội thoại theo OA và người gửi, có mã tin, nội dung và thời điểm. | BA UC-02 FR-07, FR-31 · NOTES |
| R2-02 | Inbox, lịch sử và phản hồi OA | R2 · Zalo OA | P0 | Zalo MOCK Inbox dùng chung Conversation/Message với tab hồ sơ; có tìm kiếm, OA/reply/handling filters, history, reply simulated và workflow xử lý. Chưa có inbound/outbound Zalo OA LIVE. | Đề cương · BA SCP-05 · NOTES |
| R2-03 | Tạo hoặc cập nhật Lead từ OA | R2 · Zalo OA | P0 | AS-IS: inbound MOCK tạo Conversation/Message chưa định danh; người dùng mới `Create Lead` hoặc `Link Customer`. Historical evidence từng ghi hai inbound dùng lại Lead đã link. TO-BE automatic Lead khi identity đủ chắc; ambiguous/conflict cần xác nhận. | BA FR-08–12, FR-17–23 |
| EXT-19 | Conversation/Message dùng chung và OA adapter | R2 · Kênh giao tiếp | P0 | Main có DoubleT Conversation và DoubleT Message dùng chung cho Inbox và các tab hồ sơ. Zalo mới có adapter mock. Email dùng Communication. | Bitrix24 · CRM CORE &APP A202:A211 · MVP |
| EXT-20 | Phân công và bàn giao hội thoại OA | Nâng cấp · Kênh giao tiếp | P2 | Có Assign/Accept/Transfer, bắt buộc lý do khi bàn giao, optimistic version, request idempotency và Conversation Event history. | Bitrix24 · CRM CORE &APP A264:A265 · Future |
| EXT-21 | Đo thời gian phản hồi đầu tiên của OA | Nâng cấp · Kênh giao tiếp | P2 | Có `first_response_seconds`, `waiting_seconds`, `waiting_since`, Needs reply/Replied và ưu tiên wait đã biết. Chưa có cấu hình ngưỡng SLA hoặc filter “quá SLA”. | Bitrix24 · Nối REP-03 và R2-02 |
| CC-02 | Trạng thái xử lý hội thoại | Contact Center · Open Channels | P1 | Có Waiting → In Progress → Resolved; inbound mới hơn `resolved_at` mở lại Waiting; thay đổi được ghi Conversation Event. | Bitrix24 · Vận hành hội thoại |
| CC-03 | Phân quyền hàng đợi và cấu hình kênh | Contact Center · Open Channels | P1 | Sales User chỉ thấy hội thoại được giao; Sales Manager/System Manager quản lý toàn hàng đợi và thao tác assign. Chưa có cấu hình channel/team scope hoàn chỉnh. | Bitrix24 · Quyền Open Channels |
| CC-04 | Tự động phân công hội thoại theo hàng đợi | Nâng cấp · Contact Center | P2 | EXT-20 có bàn giao thủ công; chưa có rule/config/team queue tự phân công. Tên Master Checklist cũ là `v`, không tự sửa Sheet. | Bitrix24 · Hàng đợi nhân viên |
| CC-05 | Giờ làm việc và trả lời ngoài giờ | Nâng cấp · Contact Center | P2 | Phụ thuộc nhận/gửi OA và trạng thái hội thoại. Dùng cấu hình theo từng kênh. | Bitrix24 · Giờ làm việc |
| CC-06 | Mẫu trả lời nhanh trong Inbox | Nâng cấp · Contact Center | P2 | Mẫu email ở EXT-22. Mục này chỉ áp dụng cho nhân viên nhắn trong Contact Center. | Bitrix24 · Canned responses |
| CC-07 | Cảnh báo hội thoại chờ quá lâu | Nâng cấp · Contact Center | P2 | Dùng thời điểm phản hồi của EXT-21 và số liệu tương tác của REP-03. Tập trung cảnh báo trong hàng đợi. | Bitrix24 · Thống kê hội thoại |
| CC-08 | Đánh giá hỗ trợ sau khi đóng hội thoại | Nâng cấp · Contact Center | P2 | Đề xuất sau khi ổn định trạng thái đóng và kênh gửi khảo sát. | Bitrix24 · Đánh giá hỗ trợ |
| NEW-03 | Hàng chờ gắn hội thoại chưa rõ khách | Đề xuất sau khi lõi đạt | P2 | Zalo workflow có Create Lead và Link/Change Lead hoặc Contact với reason/audit. Chưa có hàng chờ chung Email/Zalo/call cho identity chưa xác định. | Đề xuất UI cho BA UC-04 |

## Data Model

`Communication`, `Conversation`, `Message`, `Conversation Event`, `Call Log`, `Call Event`, `Call AI Summary`, private `File`.

Xem [Data Model](../../architecture/DATA_MODEL.md) và [Data Ownership](../../architecture/DATA_OWNERSHIP.md).

## Business Rules

**Tài liệu quản lý chính cho nhóm quy tắc này:** file hiện tại.

Conversation legacy unset đọc Waiting; Manager assign/transfer, assignee accept; Resolved không reply; inbound mới reopen Waiting. Transfer/relink cần reason và optimistic version. request_id+hash/source identity đảm bảo idempotency. Zalo hiện MOCK (`is_simulated`). Calls có handling riêng và được đặc tả tại CALLS.md.

## Workflow và State Transitions

Inbound/outbound event → link customer → assign/handle → resolve; derived Task/Note giữ link về nguồn.

- **AS-IS realtime:** Zalo backend không publish realtime; Inbox/thread không subscribe hoặc poll. Dữ liệu chỉ refresh khi mount, bấm Refresh hoặc sau thao tác local.
- **TO-BE realtime:** event tối thiểu sau commit → API refetch theo quyền; polling/focus refresh là fallback; merge theo stable Message ID để chống trùng khi reconnect/load older.
- **AS-IS identity:** `receive_mock_text` không tạo Lead. `Create Lead` đặt source `Zalo OA`, status `NEW`; Link chỉ hỗ trợ Lead/Contact.
- **TO-BE identity:** auto-create/link chỉ khi match duy nhất theo policy; ambiguous/conflict vào human review, không tự suy ra Company.

Contract chính: [BF-RT-01](../../architecture/BUSINESS_FLOW_CONTRACT.md#bf-rt-01--inbound-chat--inboxthread-realtime) và [BF-01](../../architecture/BUSINESS_FLOW_CONTRACT.md#bf-01--inbox--leadcontact-và-customer-record).

Chi tiết end-to-end nằm ở mục Related Workflows; state không được suy ra từ nhãn UI nếu controller/schema quy định khác.

## Permissions

Permission hooks theo assignment/manager/API principal; attachment và linked customer phải kiểm quyền.

Contract chung: [Permission Model](../../architecture/PERMISSION_MODEL.md).

## Source Mapping

| ID | Source reference | Bằng chứng mới trong checklist |
| --- | --- | --- |
| R2-01 | zalo_oa.py:86 | 16/11 · Postman: 200 OK cả hai lần. duplicate false → true, cùng ID tin và hội thoại.<br>18/11 · 7105984 có mock inbound. Chưa có Zalo OA để kết nối thật. |
| R2-02 | `doublet_crm/zalo_inbox.py`; `frontend/src/pages/ZaloInbox.vue`; `frontend/src/components/Zalo/`; `test_zalo_inbox.py` | Historical Task 24 browser thấy 2 inbound + 1 mock reply; Task 24C reported 6 backend tests, build và API acceptance PASS nhưng responsive/filter/IME browser pending. Baseline source/test cases có; không chạy lại test/browser ở task này. |
| R2-03 | `zalo_oa.py::receive_mock_text`; `zalo_workflow.py::update_conversation`; `ZaloConversationActions.vue` | Historical 16/11 Postman: tin 01 gắn Lead `j26jv05gmb`, tin 02 dùng lại đúng Lead/hội thoại; 18/11 `7105984` có link Lead. Baseline xác nhận manual Create/Link, không automatic Lead; OA LIVE chưa kiểm. |
| EXT-19 | zalo_inbox.py:364 | 18/11 · 7105984 · Có DocType và API mock. OA thật chờ tài khoản. |
| EXT-20 | `doublet_crm/zalo_workflow.py`; `DoubleT Conversation Event`; `ZaloConversationActions.vue` | Source verified: assign/transfer/accept, reason, event history và request replay guard; runtime role acceptance chưa chạy. |
| EXT-21 | `doublet_crm/zalo_inbox.py::_response_metrics`; `ZaloInbox.vue`; `test_zalo_inbox.py` | Source/test cases có first response, waiting và future/missing timestamp; chưa có SLA threshold filter. |
| CC-02 | `doublet_crm/zalo_workflow.py`; `doublet_crm/zalo_oa.py`; Conversation/Event DocTypes | Source verified lifecycle và reopen; migration/browser/test execution chưa chạy trong task. |
| CC-03 | `doublet_crm/zalo_workflow.py`; `doublet_crm/hooks.py`; Conversation/Message permissions | Source verified record scope theo assignee/manager; thiếu channel/team configuration và role acceptance runtime. |
| CC-04 | api.py | Chưa có bằng chứng mới |
| CC-05 | api.py | Chưa có bằng chứng mới |
| CC-06 | router.js | Chưa có bằng chứng mới |
| CC-07 | dashboard.py | Chưa có bằng chứng mới |
| CC-08 | dashboard.py | Chưa có bằng chứng mới |
| NEW-03 | `doublet_crm/zalo_workflow.py::update_conversation`; `ZaloConversationActions.vue` | Source có Create Lead và Link Customer cho Lead/Contact; unified multi-channel queue chưa có. |

## Upstream Dependencies

- Email/Zalo/telephony provider và customer identity.
- [Customer Identity](../crm/IDENTITY_DUPLICATES.md)
- [Email](EMAIL.md)
- [Activity report](../analytics/ACTIVITY_CONTACT_CENTER.md)

## Downstream Impact

- Customer history, Activities và Contact Center analytics.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 04 ZALO CARE](../../workflows/WF_04_ZALO_CARE.md)
- [WF 11 CUSTOMER LIFECYCLE](../../workflows/WF_11_CUSTOMER_LIFECYCLE.md)
- [Cross-module Acceptance](../../testing/CROSS_MODULE_ACCEPTANCE.md#realtime-and-duplicate-inbound)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| R2-01 | Có một phần | Chờ phụ thuộc | Checklist: Có một phần; Chờ phụ thuộc. Không suy ra runtime PASS. |
| R2-02 | Có một phần | Cần kiểm | Checklist: Có một phần; Cần kiểm. Không suy ra runtime PASS. |
| R2-03 | Có một phần | Chờ phụ thuộc | Checklist: Có một phần; Chờ phụ thuộc. Không suy ra runtime PASS. |
| EXT-19 | Có một phần | Cần làm | Checklist: Có một phần; Cần làm. Không suy ra runtime PASS. |
| EXT-20 | Có | Cần kiểm | Source verified: Assign/Accept/Transfer, handover reason và audit Event; automated test exists, execution/browser/role acceptance pending. |
| EXT-21 | Có một phần | Cần làm | First response/waiting/Needs reply implemented; configurable SLA threshold/filter chưa triển khai. |
| CC-02 | Có | Cần kiểm | Waiting/In Progress/Resolved, inbound reopen và audit implemented; runtime acceptance pending. |
| CC-03 | Có một phần | Cần làm | Assignee/manager permission scope implemented; channel/team configuration chưa hoàn chỉnh. |
| CC-04 | Chưa thấy | Đề xuất | Checklist: Chưa thấy; Đề xuất. Không suy ra runtime PASS. |
| CC-05 | Đề xuất | Đề xuất | Checklist: Đề xuất; Đề xuất. Không suy ra runtime PASS. |
| CC-06 | Đề xuất | Đề xuất | Checklist: Đề xuất; Đề xuất. Không suy ra runtime PASS. |
| CC-07 | Đề xuất | Đề xuất | Checklist: Đề xuất; Đề xuất. Không suy ra runtime PASS. |
| CC-08 | Đề xuất | Đề xuất | Checklist: Đề xuất; Đề xuất. Không suy ra runtime PASS. |
| NEW-03 | Có một phần | Đề xuất | Zalo Create Lead/Link Lead/Contact implemented; unified unresolved-customer queue across channels chưa có. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| R2-01 | Khi có OA thật, kiểm webhook, xác thực và gửi lại cùng sự kiện để đối chiếu chống trùng. |
| R2-02 | Chạy test_zalo_inbox, kiểm Inbox trên desktop/mobile với Sales User, chống trùng và liên kết Lead; cần tài khoản OA để test gửi/nhận thật, không ghi mock là đã tích hợp OA. |
| R2-03 | Đối chiếu định danh và ca xung đột bằng dữ liệu OA thật. Xác nhận liên kết đúng hồ sơ. |
| EXT-19 | Kiểm Inbox và tab hồ sơ cùng đọc một hội thoại, gửi lại tin mock không trùng. Xác minh adapter nhận/gửi khi có OA thật. |
| EXT-20 | Nhận hội thoại từ inbox, chuyển cho người khác, kiểm người phụ trách mới và lịch sử bàn giao. |
| EXT-21 | Tính số phút từ tin khách đầu tiên đến phản hồi nhân viên. Lọc hội thoại đang chờ và quá ngưỡng. |
| CC-02 | Một hội thoại đi qua Chờ xử lý → Đang xử lý → Đã đóng. Có thể mở lại theo quy tắc đã chốt và xem ai đổi trạng thái lúc nào. |
| CC-03 | Nhân viên xử lý hội thoại được giao. Trưởng nhóm xem hàng đợi được cấp quyền. Chỉ quản trị viên cấu hình kênh. Kiểm cả danh sách, chi tiết và thao tác. |
| CC-04 | Thử hai nhân viên và ba hội thoại. Gán theo vòng lần lượt cho người có mặt. Nếu hết người, giữ hội thoại trong hàng chờ và tránh gán lặp. |
| CC-05 | Một tin ngoài giờ nhận đúng một phản hồi báo lịch làm việc. Tin vẫn được lưu và chờ xử lý. Một tin trong giờ đi theo luồng thường. |
| CC-06 | Chọn một mẫu, chèn vào ô soạn, sửa nội dung và xác nhận trước khi gửi. Tin đã gửi lưu vào đúng hội thoại. |
| CC-07 | Chọn một ngưỡng chờ. Hội thoại chưa phản hồi vượt ngưỡng hiện trên hàng đợi ưu tiên và rời nhóm cảnh báo khi đã phản hồi. |
| CC-08 | Thử gửi khảo sát sau khi đóng trên kênh đã hỗ trợ. Lưu tối đa một đánh giá cho mỗi hội thoại và đếm số phản hồi theo kỳ. |
| NEW-03 | Người được cấp quyền thấy hội thoại chưa gắn, chọn hồ sơ hoặc giữ riêng. Có tìm kiếm, lý do và lịch sử xử lý. |

## Known Limitations

- **R2-01:** R2-01–R2-03: Chưa có Zalo OA để kết nối thật. Chờ kiểm thử nhận/gửi tin và liên kết Lead qua OA thật.
Luồng mock đã lưu tin vào đúng hội thoại theo OA và người gửi, có mã tin, nội dung và thời điểm.
- **R2-02:** Chỉ Zalo OA MOCK; không có webhook, credential, token renewal hoặc provider-confirmed outbound delivery LIVE.
- **R2-03:** Historical evidence về Lead đã link được giữ lại, nhưng inbound baseline không tự tạo Lead. External identity map, automatic Lead và ambiguous queue là TO-BE.
- **Realtime:** Inbound không tự xuất hiện trong Inbox/thread; event authorization, reconnect và client merge-dedupe chưa triển khai.
- **EXT-19:** Main có DoubleT Conversation và DoubleT Message dùng chung cho Inbox và các tab hồ sơ. Zalo mới có adapter mock. Email dùng Communication.
- **EXT-20:** Source hoàn chỉnh ở mức MOCK workflow; chưa có browser/role acceptance trên baseline.
- **EXT-21:** Chưa có cấu hình SLA, filter/cảnh báo quá ngưỡng; timestamp thiếu/tương lai phải giữ unknown.
- **CC-02:** Lifecycle có source nhưng migration và thao tác browser chưa được xác minh ở task này.
- **CC-03:** Chưa có channel/team membership/configuration; default DocPerm vẫn phải phân biệt với Custom DocPerm trên site.
- **CC-04:** EXT-20 đã có nhận và bàn giao thủ công. Mục này bổ sung tự phân theo hàng đợi.
- **CC-05:** Phụ thuộc nhận/gửi OA và trạng thái hội thoại. Dùng cấu hình theo từng kênh.
- **CC-06:** Mẫu email ở EXT-22. Mục này chỉ áp dụng cho nhân viên nhắn trong Contact Center.
- **CC-07:** Dùng thời điểm phản hồi của EXT-21 và số liệu tương tác của REP-03. Tập trung cảnh báo trong hàng đợi.
- **CC-08:** Đề xuất sau khi ổn định trạng thái đóng và kênh gửi khảo sát.
- **NEW-03:** Chỉ Zalo có Create/Link workflow; hàng chờ chung cho Email/Zalo/call và xử lý identity ambiguity chưa triển khai.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
