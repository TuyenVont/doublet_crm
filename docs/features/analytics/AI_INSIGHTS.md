# AI Business Insights

[← analytics index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-rep-13"></a>
- `REP-13` — AI diễn giải báo cáo dựa trên số liệu đã kiểm chứng

## Mục đích nghiệp vụ

AI diễn giải báo cáo dựa trên số liệu đã kiểm chứng. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| REP-13 | AI diễn giải báo cáo dựa trên số liệu đã kiểm chứng | R3 · AI Reports | P2 | Main 7221e0e chưa có AI diễn giải; Smart Insights vẫn rule-based. 26/11 · Codex báo REP-13 Phase 1 AI Foundation ở worktree /tmp/doublet-crm-rep13: Settings, Beeknoee service, API Key bảo mật, giới hạn request/ngân sách. Chưa thấy branch trên GitHub. | Đề xuất mở rộng 22/11 · Smart Insights · AI Agent roadmap |

## Data Model

Permission-scoped query trên Deal, Order, Quotation, Activity, Conversation và Call; không tạo nguồn KPI song song.

Xem [Data Model](../../architecture/DATA_MODEL.md) và [Data Ownership](../../architecture/DATA_OWNERSHIP.md).

## Business Rules

Quy tắc dùng chung được quản lý tại [Report Platform](REPORT_PLATFORM.md#business-rules); file này chỉ bổ sung validation nêu trong checklist/source mapping bên dưới.

## Workflow và State Transitions

Filter/cohort → authorized query → aggregate/chart/table → export/drill-down trên cùng dataset.

Chi tiết end-to-end nằm ở mục Related Workflows; state không được suy ra từ nhãn UI nếu controller/schema quy định khác.

## Permissions

Aggregate, export và drill-down phải cùng record scope; unknown không được ép thành 0.

Contract chung: [Permission Model](../../architecture/PERMISSION_MODEL.md).

## Source Mapping

| ID | Source reference | Bằng chứng mới trong checklist |
| --- | --- | --- |
| REP-13 | smart_insights.py · reports.py (nguồn dự kiến) | 26/11 · Codex báo backend mocked 11/11, frontend 3/3 PASS; compile/JSON/diff check PASS. Chưa xác minh remote, API thật, migration, build hoặc browser. Phase 1 chưa phải toàn bộ REP-13. |

## Upstream Dependencies

- Business source of truth và date/filter contract.
- [Report Platform](REPORT_PLATFORM.md)
- [Known Gaps](../../tracking/KNOWN_GAPS.md)

## Downstream Impact

- Dashboard, management decision, Smart Insights và follow-up.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- Xem [workflow index](../../workflows/README.md); chưa có workflow riêng cho mục này.

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| REP-13 | Chưa thấy | Đang làm | Không có source baseline; historical unmerged worktree evidence không đủ PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| REP-13 | Lưu branch, sửa các vấn đề review, migrate và test kết nối thật; tiếp tục AI Data Context, Business Insights, Dashboard integration. Chỉ dùng KPI có kiểm chứng, không gửi PII. |

## Known Limitations

- **REP-13:** Main 7221e0e chưa có AI diễn giải; Smart Insights vẫn rule-based. 26/11 · Codex báo REP-13 Phase 1 AI Foundation ở worktree /tmp/doublet-crm-rep13: Settings, Beeknoee service, API Key bảo mật, giới hạn request/ngân sách. Chưa thấy branch trên GitHub.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
