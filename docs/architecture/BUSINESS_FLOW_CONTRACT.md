# End-to-End Business Flow Contract

[← Documentation Index](../INDEX.md) · [Dependency Map](DEPENDENCY_MAP.md) · [Customer lifecycle](../workflows/WF_11_CUSTOMER_LIFECYCLE.md) · [Cross-module acceptance](../testing/CROSS_MODULE_ACCEPTANCE.md)

Tài liệu này quản lý contract chuyển tiếp dữ liệu và điều hướng xuyên module. Feature files chỉ liên kết tới contract tương ứng, không sao chép quy tắc. Ký hiệu: **AS-IS** là source tại `a7534e7`; **TO-BE** là yêu cầu mục tiêu; **GAP** là phần chưa có hoặc chưa chứng minh; **Evidence** không đồng nghĩa runtime acceptance.

## Nguyên tắc chung

1. Source record và destination record giữ ID thật; route/query chỉ là phương tiện vận chuyển context, Save mới là persistence boundary.
2. Không yêu cầu chọn lại customer, Deal hoặc source record đã xác định và còn hợp lệ. Chỉ hỏi khi có nhiều lựa chọn hợp lệ, thiếu dữ liệu, xung đột identity hoặc người dùng chủ động đổi context.
3. Backend phải kiểm quyền source, quyền tạo/sửa destination, tính hợp lệ của mọi link và field permission. Ẩn nút hoặc route guard không đủ.
4. Không sao chép `DoubleT Message`, `Communication`, `DoubleT Call Log` hay Activity sang hồ sơ khác để tạo timeline. Màn hình hồ sơ dùng permission-scoped projection trên source of truth và provenance link.
5. Sau Save/Reload, destination phải giữ source link và snapshot được quy định; thay đổi master data không được âm thầm thay snapshot lịch sử.

<a id="bf-rt-01--inbound-chat--inboxthread-realtime"></a>
## BF-RT-01 — Inbound chat → Inbox/thread realtime

| Nội dung | Contract |
| --- | --- |
| Source | Authenticated MOCK inbound `zalo_oa.receive_mock_text`; tương lai là verified Zalo OA LIVE webhook. |
| Trigger | Inbound Message được insert hoặc replay; reconnect/tải thêm lịch sử ở client. |
| Destination | `/contact-center/inbox`; conversation list và thread đang mở. |
| Context | `conversation`, deterministic `message.name`, `external_message_id`, direction, `sent_at`; event chỉ được gửi tới user còn quyền đọc thread. |
| Prefill | Không áp dụng; client merge theo `message.name`, không append mù. |
| Validation | Backend permission hook cho Conversation/Message; event không được làm lộ ID/preview thread ngoài scope. Sau reconnect phải fetch lại permission-scoped state. |
| Persistence | `DoubleT Conversation` + `DoubleT Message` là nguồn chuẩn. UI dedupe giữa event, reconnect, refresh và load-older bằng stable ID. |
| Exception | Event lặp, event đến trước response, mất socket, quyền bị thu hồi, thread resolved/reopened, same message identity khác payload. |
| Acceptance | [RT-01…RT-06](../testing/CROSS_MODULE_ACCEPTANCE.md#realtime-and-duplicate-inbound). |

**AS-IS:** Frappe socket được khởi tạo toàn app, nhưng Zalo backend không `publish_realtime` và `ZaloInbox.vue`/`ZaloConversationThread.vue` không subscribe/poll. Inbox chỉ reload khi mở trang, bấm Refresh hoặc sau thao tác local. Pagination prepend dùng message `name` làm key nhưng chưa có merge-dedupe cho realtime/reconnect. MOCK persistence và deterministic IDs đã có; Zalo LIVE chưa có.

**TO-BE:** ưu tiên Frappe realtime sau transaction commit với payload tối thiểu (`conversation`, `message`, change type), rồi client refetch qua API permission-scoped. Có bounded polling/focus refresh làm fallback khi socket mất; không coi polling là Zalo LIVE.

**GAP:** chưa có event contract, permission-safe publish/subscription, reconnect cursor/refresh hoặc client merge-dedupe. Map: `R2-01`, `R2-02`, `R2-06`, `EXT-19`, `CC-03`; xem [Workflow Gaps](../tracking/WORKFLOW_GAPS.md#realtime-communication).

<a id="bf-01--inbox--leadcontact-và-customer-record"></a>
## BF-01 — Inbox → Lead/Contact và customer record

| Nội dung | Contract |
| --- | --- |
| Source | Zalo Inbox conversation chưa định danh hoặc đã link; `ZaloCustomerDetails`. |
| Trigger | `Create Lead`, `Link Customer`, hoặc mở link Lead/Contact/Company/Deal. |
| Destination | `DoubleT Lead` hoặc `DoubleT Contact`; route `LeadDetail`/`ContactDetail`; converted Company/Deal chỉ hiển thị khi caller đọc được. |
| Context | Conversation ID, OA ID, external user ID, existing `lead`/`contact`, source `Zalo OA`; không copy Message. |
| Prefill | AS-IS Create Lead chỉ nhận tên và backend đặt `status=NEW`, `source=Zalo OA`; TO-BE: link hồ sơ khi có đúng một match hợp lệ; tạo Lead khi identity đủ rõ và không có match. |
| Validation | Create/read permission; unique/match policy; existing link/change link cần reason/manager theo workflow; Company không được suy ra chỉ từ tên hoặc Contact mơ hồ. |
| Persistence | Conversation lưu link Lead hoặc Contact; Lead conversion lưu converted links; record tab truy vấn lại cùng Conversation/Message. |
| Exception | Không đủ identity, nhiều match, link sai khách, permission denied, stale version, external identity xung đột. |
| Acceptance | [ID-01…ID-06](../testing/CROSS_MODULE_ACCEPTANCE.md#customer-identity-and-conversion). |

**AS-IS:** `receive_mock_text` tạo Conversation/Message chưa định danh. `Create Lead`/`Link Customer` là thao tác người dùng trong `zalo_workflow`; `get_customer_details` và record links cho phép mở Lead/Contact/Company/Deal có quyền. Historical site evidence từng ghi inbound gắn/tái dùng Lead, nhưng baseline hiện tại không tự tạo Lead khi inbound.

**TO-BE:** nhận diện nguồn đủ chắc và chưa có hồ sơ thì tạo Lead idempotent; ambiguous/conflict đi hàng chờ xác nhận. Khách đã tồn tại phải link, không tạo Lead trùng. Sau conversion mở Contact/Company và tiếp tục xem cùng conversation.

**GAP:** chưa có durable external identity map/match policy, automatic Lead rule hoặc ambiguous identity queue. Map: `R2-03`, `NEW-03`, `CRM-06`, `EXT-03`, `EXT-04`.

<a id="bf-02--lead--contactcompanydeal"></a>
## BF-02 — Lead → Contact/Company/Deal

| Nội dung | Contract |
| --- | --- |
| Source | Lead detail; `DoubleT Lead` Qualified/chưa converted. |
| Trigger | Existing conversion action/controller `convert_lead`. |
| Destination | Personal: Contact; Company: Company + Contact đại diện. Deal chỉ được tạo trong conversion khi chọn `create_deal`; nếu không, có thể tạo Deal sau. |
| Context | Lead identity, customer type, selected/reused Contact/Company, owner/source. |
| Prefill | Dùng dữ liệu Lead và lựa chọn đã xác nhận; không bắt nhập lại customer type/identity. |
| Validation | Lead write + destination create/read, duplicate conversion guard, Contact–Company consistency. Không tự gắn Company khi match mơ hồ. |
| Persistence | `converted_contact`, `converted_company`, `converted_deal`, `converted_on`; `converted_deal` có thể rỗng. Nếu tạo Deal, Deal giữ `source_lead`, `contact`, `company`. Conversation tiếp tục truy theo Lead/converted links. |
| Exception | Convert lặp bị từ chối khi Lead đã converted; không tạo bản ghi thứ hai. Existing customer conflict, thiếu Company, Contact thuộc Company khác, permission denied. |
| Acceptance | Personal, Company, existing customer, retry và denied-role trong [Cross-module acceptance](../testing/CROSS_MODULE_ACCEPTANCE.md). |

**AS-IS:** controller và converted links có; Deal là tùy chọn (`create_deal=0` mặc định); UI có link mở Contact/Company/Deal nếu tồn tại. Quan hệ Contact chỉ có một `company`.

<a id="bf-03--contactcompany--deal"></a>
## BF-03 — Contact/Company → Deal

| Nội dung | Contract |
| --- | --- |
| Source | Contact/Company detail. |
| Trigger | TO-BE `Create Deal`; AS-IS chỉ có danh sách và link mở Deal đã liên kết. |
| Destination | TO-BE: màn hình tạo Deal theo entry point đã xác minh (không giả định route `DealCreate` tồn tại); Deal detail sau Save. |
| Context | Contact ID; Company ID; customer type; với Company chỉ prefill Contact khi có đúng một Contact hợp lệ hoặc người dùng chọn. |
| Prefill | Personal → Contact; Company → Company và optional representative Contact. |
| Validation | Source read, Deal create, Contact–Company match và no restricted label leakage. |
| Persistence | Deal `deal_type`, `contact`, `company`; customer pages reload từ persisted links. |
| Exception | Nhiều Contact đại diện, Contact không thuộc Company, source bị xóa/không đọc được. |
| Acceptance | [NAV-03](../testing/CROSS_MODULE_ACCEPTANCE.md#context-aware-navigation). |

**GAP:** Contact/Company pages hiện list linked Deals nhưng chưa có verified create-with-context entry point. Map: `CRM-04`, `CRM-09`, `EXT-01`, `EXT-02`; cần quyết định UX và representative rule.

<a id="bf-04--leaddeal--quotation"></a>
## BF-04 — Lead/Deal → Quotation

| Nội dung | Contract |
| --- | --- |
| Source | Qualified/Converted Lead hoặc Deal; Lead/Deal UI action. |
| Trigger | `Create Quotation`; route `QuotationCreate?lead=<id>&deal=<id>`. |
| Destination | New Quotation form, rồi saved `DoubleT Quotation`. |
| Context | `lead_name`, `deal_name`, exact source chain, customer type, Contact/Company, interested products. |
| Prefill | `get_quotation_draft_context` returns Deal/customer/source Lead, resolved current price list and editable item suggestions. Một Deal hợp lệ dùng trực tiếp; nhiều Deal buộc chọn. |
| Validation | Quotation create; source records readable; Deal belongs to Lead; Personal/Company completeness; Contact–Company match; Product/pricing access. |
| Persistence | Save stores `deal`, customer context and Quotation Item snapshot; draft API never inserts or converts Lead. |
| Exception | Lead chưa Qualified/chưa convert, không có Deal, nhiều Deal, restricted Deal/Product, price resolution error. |
| Acceptance | [SALE-01…SALE-04](../testing/CROSS_MODULE_ACCEPTANCE.md#sales-lifecycle). |

**AS-IS:** implemented in `sales_completion.get_quotation_draft_context`, `FrappeLead.vue`, `QuotationForm.vue` and quotation utilities; acceptance on exact baseline pending.

<a id="bf-05--accepted-quotation--order"></a>
## BF-05 — Accepted Quotation → Order

| Nội dung | Contract |
| --- | --- |
| Source | Saved Quotation detail. |
| Trigger | `Create Order`. |
| Destination | Existing or new `OrderDetail`. |
| Context/Prefill | Quotation ID; customer/deal/currency and item pricing snapshots copied server-side. |
| Validation | Quotation read; dưới row lock kiểm Order hiện có trước. Nếu có, chỉ trả Order khi caller có quyền đọc. Nếu chưa có, yêu cầu source status exactly `Accepted`, Order create và stored totals valid; unique quotation. |
| Persistence | One `DoubleT Order.quotation`; Order Items preserve snapshot. Retry returns existing readable Order. |
| Exception | Draft/Sent/Rejected bị từ chối khi tạo mới; corrupt totals, concurrent request, existing Order not readable. Order đã có không phụ thuộc trạng thái hiện tại của Quotation hoặc quyền tạo Order mới. |
| Acceptance | [SALE-05…SALE-07](../testing/CROSS_MODULE_ACCEPTANCE.md#sales-lifecycle). |

**AS-IS:** implemented by `create_order_from_quotation`; only `Accepted` creates a new Order.

<a id="bf-06--customer-record--tasknoteappointment"></a>
## BF-06 — Customer record → Task/Note/Appointment

| Nội dung | Contract |
| --- | --- |
| Source | Lead/Deal/Contact/Company detail and Activity header. |
| Trigger | `Task`, `Note`, `Appointment`. |
| Destination | Modal or `/appointments/new`; saved activity and source tab. |
| Context/Prefill | Exact source DocType/name into Task `reference_docname`, Note `reference_name`, Appointment `reference_docname`. |
| Validation | Source read; activity create; controller allowlist of four CRM DocTypes; assignee/reminder validation. |
| Persistence | Dynamic Link persists; reload query filters by both reference fields. No cross-Deal projection merely because customer is shared. |
| Exception | Source switch while request pending, unsupported DocType, restricted source, reminder after due/start. |
| Acceptance | [HIST-01…HIST-05](../testing/CROSS_MODULE_ACCEPTANCE.md#customer-history-continuity). |

**AS-IS:** Activity header/modal and appointment query prefill exist. `get_linked_tasks`, `get_linked_notes`, `get_activities` response shapes are compatibility contracts; see feature files.

<a id="bf-07--missed-call--callback-task"></a>
## BF-07 — Missed Call → Callback Task

| Nội dung | Contract |
| --- | --- |
| Source | Missed incoming `DoubleT Call Log` in Calls queue. |
| Trigger | Assign/accept and create/open callback. |
| Destination | Unique `DoubleT Task`, then Call detail from Task. |
| Context/Prefill | `callback_call_log`, current Lead/Contact reference, due date, assignee. |
| Validation | Call scope/handler, missed incoming status, linked-record read, callback uniqueness. |
| Persistence | Task keeps call link; relink through Contact Center updates Task reference under lock; result/history retained. |
| Exception | Ambiguous caller, unrelated user, repeated create, relink conflict, resolved call. |
| Acceptance | [CALL-01…CALL-04](../testing/CROSS_MODULE_ACCEPTANCE.md#call-context-and-follow-up). |

<a id="bf-08--ai-summary--reviewed-note"></a>
## BF-08 — AI Summary → reviewed Note

| Nội dung | Contract |
| --- | --- |
| Source | Authorized DEMO or LIVE Call AI Summary. |
| Trigger | User reviews and selects Save next steps. |
| Destination | One `DoubleT Note` linked to original customer context. |
| Context/Prefill | `source_call_log`, reviewed next steps, original readable Lead/Contact reference. |
| Validation | Call, summary, recording/File and Note permissions; version/stale guard. DEMO never calls provider. |
| Persistence | Unique immutable `source_call_log`; retry same content returns existing Note; no automatic unreviewed publish. |
| Exception | Missing/ambiguous recording, provider error, customer relink, Note stale/denied. |
| Acceptance | [CALL-05…CALL-07](../testing/CROSS_MODULE_ACCEPTANCE.md#call-context-and-follow-up). |

<a id="bf-09--reportsmart-insight--source-or-follow-up-task"></a>
## BF-09 — Report/Smart Insight → source or Follow-up Task

| Nội dung | Contract |
| --- | --- |
| Source | Permission-scoped report drill-down or current Smart Insight alert. |
| Trigger | Source link or explicit Create follow-up. |
| Destination | Lead/Deal/Quotation/Order/Call/Task/Appointment/Inbox route, hoặc one active `DoubleT Task`. |
| Context/Prefill | Exact source ID; follow-up resolves supported Lead/Deal/Contact/Company reference and embeds stable alert marker. |
| Validation | Aggregate and drill-down same authorized population; source still current; Task create; reference read; active assignee. |
| Persistence | Task stores source-compatible reference; lock + marker prevents duplicate active Task. |
| Exception | Stale/resolved alert, restricted row, unsupported Quotation without readable Deal, concurrent create. |
| Acceptance | [REP-01…REP-04](../testing/CROSS_MODULE_ACCEPTANCE.md#reports-and-smart-insights). |

**AS-IS:** report links and explicit Smart Insights follow-up are implemented. Automatic `NEW-02` and REP-13 AI interpretation remain target/gap.

## Customer history continuity

| History | Source of truth | Projection rule |
| --- | --- | --- |
| Chat | Conversation + Message | Lead/Contact direct link hoặc converted Lead chain; never duplicate Message. |
| Email | `Communication` | Exact `reference_doctype/reference_name` and thread rules; customer-wide merge is not implied. |
| Calls | Call Log | Exact allowed Lead/Contact link; Deal context is not stored AS-IS. |
| Task/Note/Appointment | Their own Dynamic Link | Exact referenced record only; customer aggregation must preserve source label and permission. |
| Deal/Quotation/Order | Persisted Links and snapshots | Contact/Company views may project readable linked records; do not infer records through same customer when Deal-specific context matters. |

Customer 360 TO-BE may aggregate these sources, but every row must expose provenance, restricted/unknown state and source route. It must not blend activities between two Deals of one customer without an explicit customer-level mode.

## Call customer-context decision boundary

AS-IS Call Log has no independent `customer_type` or participant/contact-role model. `reference_doctype` is a Link to DocType but controller allowlist is exactly `DoubleT Lead` and `DoubleT Contact`; phone auto-match scans only those two. The actual participant is represented only by direction plus `from_number`/`to_number`, agent and optional Lead/Contact link.

Before extending, decide whether Company is (a) derived through Contact, (b) stored as a separate business-account context while participant remains Contact, or (c) directly linkable. Do not add all DocTypes to the Dynamic Link. Any target model must distinguish customer type, linked-record type, participant and related Company/Deal, with migration and permission rules.
