# Webhook & n8n Integration Platform

[← integration index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-r2-06"></a>
- `R2-06` — Nguồn dữ liệu, sự kiện lặp và lịch sử đồng bộ
<a id="feature-r3-01"></a>
- `R3-01` — Workflow n8n chạy trên DoubleT
<a id="feature-r3-05"></a>
- `R3-05` — Custom app cấu hình và giám sát Webhook

## Mục đích nghiệp vụ

Nguồn dữ liệu, sự kiện lặp và lịch sử đồng bộ; Workflow n8n chạy trên DoubleT; Custom app cấu hình và giám sát Webhook. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| R2-06 | Nguồn dữ liệu, sự kiện lặp và lịch sử đồng bộ | R2 · Tích hợp chung | P0 | Zalo mock có mã tin nguồn và chống trùng. Còn hoàn thiện nhật ký sự kiện, truy vết lỗi và xử lý gửi lại ở các tích hợp thật. | BA FR-31–32 · Tài liệu Webhook |
| R3-01 | Workflow n8n chạy trên DoubleT | R3 · n8n | P0 | Checklist #29–30 ghi đã nối Frappe qua event/webhook và tìm workflow. Main chưa thấy workflow export có thể đối chiếu. | BA SCP-08, SM-06 · CHECKLIST #29–30 |
| R3-05 | Custom app cấu hình và giám sát Webhook | R3 · Webhook | P1 | Tài liệu kỹ thuật mô tả app riêng gồm cấu hình, retry, log/monitoring, quản trị và test. Mức bắt buộc của toàn bộ app cần đối chiếu phạm vi BA/đề cương. | Tài liệu Webhook · BA QD-02/QD-06 |

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
| R2-06 | hooks.py | 18/11 · 7105984 · zalo_oa.py. Chưa nghiệm thu đồng bộ đa kênh. |
| R3-01 | hooks.py | Chưa có bằng chứng mới |
| R3-05 | hooks.py | Chưa có bằng chứng mới |

## Upstream Dependencies

- External provider và integration configuration.
- [Deal Automation](../automation/DEAL_AUTOMATION.md)
- [External Channels](EXTERNAL_CHANNELS.md)

## Downstream Impact

- Customer/Lead/Order, notification và automation.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 10 N8N AUTOMATION](../../workflows/WF_10_N8N_AUTOMATION.md)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| R2-06 | Có một phần | Cần làm | Checklist: Có một phần; Cần làm. Không suy ra runtime PASS. |
| R3-01 | Bản cũ/ngoài repo | Cần làm | Checklist: Bản cũ/ngoài repo; Cần làm. Không suy ra runtime PASS. |
| R3-05 | Cần chốt | Cần chốt | Checklist: Cần chốt; Cần chốt. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| R2-06 | Có ID nguồn, kết quả xử lý mỗi sự kiện, replay có kiểm soát và log dễ truy khi lỗi. Đối chiếu tài liệu webhook theo phạm vi được chốt. |
| R3-01 | Tìm flow cũ, nối site đích, chạy một sự kiện đã chốt. Lưu trigger, đầu vào, đầu ra và kết quả khi nhận lại sự kiện. |
| R3-05 | Xác nhận với nhóm/giảng viên phần nào phải trình diễn. Trước mắt truy vết một luồng event → n8n có log lỗi và quyền cấu hình. |

## Known Limitations

- **R2-06:** Zalo mock có mã tin nguồn và chống trùng. Còn hoàn thiện nhật ký sự kiện, truy vết lỗi và xử lý gửi lại ở các tích hợp thật.
- **R3-01:** Checklist #29–30 ghi đã nối Frappe qua event/webhook và tìm workflow. Main chưa thấy workflow export có thể đối chiếu.
- **R3-05:** Tài liệu kỹ thuật mô tả app riêng gồm cấu hình, retry, log/monitoring, quản trị và test. Mức bắt buộc của toàn bộ app cần đối chiếu phạm vi BA/đề cương.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
