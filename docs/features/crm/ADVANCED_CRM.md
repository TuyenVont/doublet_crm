# Advanced CRM

[← crm index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-ext-16"></a>
- `EXT-16` — Điều kiện bắt buộc khi chuyển stage
<a id="feature-ext-17"></a>
- `EXT-17` — Playbook bán hàng theo từng stage
<a id="feature-ext-18"></a>
- `EXT-18` — Nhiều pipeline theo loại hình bán
<a id="feature-ext-30"></a>
- `EXT-30` — Tạo Deal định kỳ cho khách gia hạn

## Mục đích nghiệp vụ

Điều kiện bắt buộc khi chuyển stage; Playbook bán hàng theo từng stage; Nhiều pipeline theo loại hình bán; Tạo Deal định kỳ cho khách gia hạn. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| EXT-16 | Điều kiện bắt buộc khi chuyển stage | Nâng cấp · Pipeline | P2 | Có kiểm stage và yêu cầu lý do khi Lost. Chưa thấy danh sách trường bắt buộc theo từng stage. | HubSpot · Liên quan CRM-03 |
| EXT-17 | Playbook bán hàng theo từng stage | Nâng cấp · Pipeline | P2 | Có Task thủ công và Deal stage. Chưa thấy kế hoạch các bước ứng với mỗi stage. | SAP · Ứng viên nâng cấp · ACT-01 |
| EXT-18 | Nhiều pipeline theo loại hình bán | Nâng cấp · Pipeline | P2 | Có một bộ Deal Stage, trên Deal phân Personal/Company. Chưa thấy model pipeline độc lập. | Bitrix24 · CRM CORE &APP A57:A59 · Future |
| EXT-30 | Tạo Deal định kỳ cho khách gia hạn | Nâng cấp · Pipeline | P2 | Có Deal tạo thủ công, chưa thấy scheduler hoặc cấu hình Deal định kỳ. | Bitrix24 · CRM CORE &APP A60 · Future |

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
| EXT-16 | doublet_deal.py | Chưa có bằng chứng mới |
| EXT-17 | DealDetailView.vue | Chưa có bằng chứng mới |
| EXT-18 | doublet_deal_stage.json | Chưa có bằng chứng mới |
| EXT-30 | hooks.py | Chưa có bằng chứng mới |

## Upstream Dependencies

- Lead source, customer identity và Frappe permission infrastructure.
- [Deal](DEAL_PIPELINE.md)
- [Deal Automation](../automation/DEAL_AUTOMATION.md)

## Downstream Impact

- Pricing, Quotation, Order, Activities, Contact Center và Reports.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- Xem [workflow index](../../workflows/README.md); chưa có workflow riêng cho mục này.

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| EXT-16 | Có một phần | Đề xuất | Checklist: Có một phần; Đề xuất. Không suy ra runtime PASS. |
| EXT-17 | Chưa thấy | Đề xuất | Checklist: Chưa thấy; Đề xuất. Không suy ra runtime PASS. |
| EXT-18 | Chưa thấy | Đề xuất | Checklist: Chưa thấy; Đề xuất. Không suy ra runtime PASS. |
| EXT-30 | Chưa thấy | Đề xuất | Checklist: Chưa thấy; Đề xuất. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| EXT-16 | Thử một rule trước stage báo giá cần có khách và ngày dự kiến chốt. Kiểm form, Kanban và backend. |
| EXT-17 | Chọn hai stage và hiện 2–3 bước gợi ý. Dùng Task hiện có để ghi bước đã hoàn thành. |
| EXT-18 | Cấu hình hai pipeline riêng với stage riêng, lọc và giữ lịch sử chuyển nếu nhóm chọn làm. |
| EXT-30 | Cấu hình chu kỳ test. Sinh Deal mới cùng khách, tham chiếu kỳ trước và chạy lại không nhân đôi. |

## Known Limitations

- **EXT-16:** Có kiểm stage và yêu cầu lý do khi Lost. Chưa thấy danh sách trường bắt buộc theo từng stage.
- **EXT-17:** Có Task thủ công và Deal stage. Chưa thấy kế hoạch các bước ứng với mỗi stage.
- **EXT-18:** Có một bộ Deal Stage, trên Deal phân Personal/Company. Chưa thấy model pipeline độc lập.
- **EXT-30:** Có Deal tạo thủ công, chưa thấy scheduler hoặc cấu hình Deal định kỳ.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
