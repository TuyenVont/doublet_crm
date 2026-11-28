# Cross-module End-to-End Acceptance

[← Testing index](README.md) · [Business Flow Contract](../architecture/BUSINESS_FLOW_CONTRACT.md) · [Workflow Gaps](../tracking/WORKFLOW_GAPS.md)

Tất cả scenario dưới đây là test specification. Không scenario nào được coi PASS nếu thiếu commit/site/role/command hoặc browser evidence trên exact baseline.

## Customer identity and conversion

| ID | Scenario | Expected result |
| --- | --- | --- |
| ID-01 | Khách cá nhân mới: inbound đủ identity → Lead → convert | Một Lead, một Contact; một Deal nếu chọn tạo Deal, nếu không `converted_deal` rỗng. Conversation vẫn truy được cùng Message; converted links mở đúng hồ sơ. Automatic Lead là TO-BE cho đến khi triển khai. |
| ID-02 | Khách doanh nghiệp: Lead Company với Contact đại diện | Company/Contact/Deal đúng quan hệ; không tự chọn Contact khi nhiều ứng viên; mở lại giữ context. |
| ID-03 | Khách quay lại nhắn từ external identity đã map | Link hồ sơ hiện có; không tạo Lead/Contact trùng; lịch sử cũ và mới còn provenance. |
| ID-04 | Hai Contact/Lead cùng phone/external identity | Không auto-link; đưa ra xác nhận/queue; không lộ record bị hạn chế. |
| ID-05 | Convert hoặc inbound retry | Replay inbound không nhân đôi Message/Lead. Convert lần hai bị từ chối hoặc không tạo thêm record theo contract hiện hành; giữ đúng converted links. |
| ID-06 | Sales User không có quyền destination | Backend từ chối; không tạo record một phần; Inbox không lộ label/ID. |

## Realtime and duplicate inbound

| ID | Scenario | Expected result |
| --- | --- | --- |
| RT-01 | MOCK inbound khi Inbox đang mở | TO-BE: list và active thread tự cập nhật; AS-IS cần Refresh và phải được báo là GAP. |
| RT-02 | Cùng event phát hai lần | Một Message; list/thread không render trùng. |
| RT-03 | Event tới trong lúc load older history | Merge theo stable ID, giữ thứ tự và scroll; không mất/trùng row. |
| RT-04 | Socket reconnect hoặc tab regain focus | Refetch permission-scoped delta/state; không append lại toàn bộ. |
| RT-05 | Thread được transfer khi Sales User đang mở | User cũ mất access sau refetch/event; nội dung nhạy cảm bị đóng, không tiếp tục nhận preview. |
| RT-06 | Zalo LIVE chưa cấu hình | MOCK realtime (nếu có) vẫn mang nhãn MOCK; không tuyên bố provider delivery. |

## Context-aware navigation

| ID | Scenario | Expected result |
| --- | --- | --- |
| NAV-01 | Inbox → linked Lead/Contact → quay lại Inbox | Route đúng record; conversation query giữ ID; không copy Message. |
| NAV-02 | Lead conversion → mở Contact/Company/Deal | Link đúng converted fields và quyền; reload không mất. |
| NAV-03 | Contact/Company → Create Deal | TO-BE prefill đúng customer; nhiều Contact thì hỏi chọn; AS-IS chưa có verified entry point. |
| NAV-04 | Lead/Deal → Quotation | Customer/items/price context prefill; multiple Deals yêu cầu chọn; Save giữ source link/snapshot. |
| NAV-05 | Accepted Quotation → Order | Một Order; Draft/Sent/Rejected không tạo Order mới; concurrent retry trả cùng Order nếu có quyền đọc. Order đã có vẫn mở được khi source không còn Accepted hoặc caller không có quyền tạo Order mới. |
| NAV-06 | Customer record → Task/Note/Appointment | Exact Dynamic Link được prefill/persist; reload hiện trong đúng record, không record khác. |

## Sales lifecycle

| ID | Scenario | Expected result |
| --- | --- | --- |
| SALE-01 | Qualified Lead chưa convert tạo Quote | Hướng dẫn convert; không insert Quote/Deal ngầm. |
| SALE-02 | Converted Lead có một/nhiều Deal | Một Deal dùng trực tiếp; nhiều Deal hỏi chọn; restricted Deal không lộ. |
| SALE-03 | Deal Personal/Company tạo Quote | Customer consistency và Contact–Company validation; prices là current suggestion. |
| SALE-04 | Đổi Catalog price sau khi lưu Quote | Saved Quotation snapshot không đổi. |
| SALE-05 | Accepted Quote tạo Order | Order copy chính xác customer/items/totals. |
| SALE-06 | Hai request tạo Order đồng thời | Unique quotation + row lock để chỉ một Order. |
| SALE-07 | Thử Draft/Sent/Rejected | Không tạo Order mới khi chưa có Order liên kết; nếu đã có, trả đúng Order có quyền đọc. |

## Call context and follow-up

| ID | Scenario | Expected result |
| --- | --- | --- |
| CALL-01 | Unique phone match Lead/Contact | Call auto-link đúng allowed type; participant number vẫn giữ. |
| CALL-02 | Nhiều phone match hoặc Company-only | Không auto-link; handler chọn Lead/Contact. Company/Deal direct link là decision/GAP. |
| CALL-03 | Missed Call tạo callback hai lần | Một Task với `callback_call_log`; link customer và due date đúng. |
| CALL-04 | Relink Call có callback | Chỉ qua Contact Center; Task reference đổi cùng transaction/audit; denied user bị chặn. |
| CALL-05 | DEMO AI | Không queue/provider; review rồi lưu đúng một Note. |
| CALL-06 | LIVE AI | Private recording/config/provider và permission recheck; lỗi hiển thị riêng. |
| CALL-07 | Relink sau khi đã có Note | Note giữ provenance/source customer ban đầu; UI yêu cầu review trước khi ghi đè context. |

## Customer history continuity

| ID | Scenario | Expected result |
| --- | --- | --- |
| HIST-01 | Một customer có Chat/Email/Call/Task/Note/Appointment | Mỗi row truy tới source of truth; restricted source là unavailable/unknown, không phải zero. |
| HIST-02 | Hai Deal cùng Contact | Activity link Deal A không xuất hiện như activity Deal B; customer-level view phải ghi rõ scope. |
| HIST-03 | Lead converted | Conversation liên kết Lead vẫn hiện qua converted Contact/Company theo permission, không copy Message. |
| HIST-04 | Quotation/Order history | Customer view chỉ hiện readable records và đúng customer link; snapshot không bị reprice. |
| HIST-05 | Hai Sales User khác scope | Aggregate, list, detail, attachment và realtime event cùng population được phép. |

## Reports and Smart Insights

| ID | Scenario | Expected result |
| --- | --- | --- |
| REP-01 | Report aggregate → drill-down | Cùng permission-scoped dataset; link mở đúng Lead/Deal/Quote/Order/Call/Task/Appointment/Inbox. |
| REP-02 | Smart Insight source link | Mở exact source nếu còn quyền; stale/restricted alert không lộ. |
| REP-03 | Create follow-up hai lần/concurrently | Một active Task với supported reference và marker. |
| REP-04 | Unknown/restricted evidence | Không ép 0/healthy; REP-13 AI không được coi implemented từ evidence worktree ngoài baseline. |

## Evidence matrix cần ghi khi chạy

| Evidence | Bắt buộc |
| --- | --- |
| Baseline | Full commit SHA, branch và dirty-state note. |
| Backend | Command, site, role/user, PASS/FAIL counts. |
| Browser | Route, viewport, role, fixture IDs, screenshots/log nếu phù hợp. |
| Realtime | Hai sessions/users, reconnect/duplicate/load-more timing và permission transfer. |
| Integration | MOCK/DEMO hoặc LIVE ghi riêng; provider account/event/delivery evidence nếu LIVE. |
| Persistence | Reload/reopen query và exact source/destination IDs. |
