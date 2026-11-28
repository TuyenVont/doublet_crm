# User, Role & Record Scope

[← crm index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-crm-07"></a>
- `CRM-07` — Role và phạm vi xem/sửa hồ sơ
<a id="feature-ext-27"></a>
- `EXT-27` — Quyền theo người phụ trách và nhóm

## Mục đích nghiệp vụ

Role và phạm vi xem/sửa hồ sơ; Quyền theo người phụ trách và nhóm. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| CRM-07 | Role và phạm vi xem/sửa hồ sơ | R1 · Phân quyền | P0 | Đã sửa tên phiên ở sidebar và kiểm quyền hiện nút Create/Edit/Delete trên Contact, New Task và Add Note trên Lead. Phạm vi đọc/ghi hồ sơ theo Sales và owner còn cần xác nhận. | BA SCP-03, FR-29–30 |
| EXT-27 | Quyền theo người phụ trách và nhóm | R1 · Phân quyền | P1 | Có quyền DocType và giao hồ sơ. Quyền theo owner/team trên site cần kiểm. Bảng dự án xếp quyền quản lý theo nhóm vào Future. | CRM CORE &APP A183:A186 · Own Items MVP |

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
| CRM-07 | ContactDetailView.vue | 19/11 · PR #25 → main c2edcb6. Build và test frontend PASS. Chờ Chrome retest bằng role Sales và kiểm phạm vi hồ sơ. |
| EXT-27 | doublet_deal.json | 18/11 · 7105984 · Schema kiểm theo DocType. Phạm vi owner/team trên site chưa kiểm. |

## Upstream Dependencies

- Lead source, customer identity và Frappe permission infrastructure.
- [Permission Model](../../architecture/PERMISSION_MODEL.md)
- [Report Platform](../analytics/REPORT_PLATFORM.md)

## Downstream Impact

- Pricing, Quotation, Order, Activities, Contact Center và Reports.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- Xem [workflow index](../../workflows/README.md); chưa có workflow riêng cho mục này.

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| CRM-07 | Có một phần | Cần kiểm | Checklist: Có một phần; Cần kiểm. Không suy ra runtime PASS. |
| EXT-27 | Cần xác minh | Cần kiểm | Checklist: Cần xác minh; Cần kiểm. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| CRM-07 | Retest bằng Sales User và Sales Manager. Kiểm tên phiên, quyền Contact, mở form Task/Note và phạm vi dữ liệu giữa hai Sales cùng role nhưng khác owner. |
| EXT-27 | Thử hai Sales khác owner và một quản lý. Kiểm list, chi tiết, xuất và KPI. Ưu tiên nghiệm thu quyền theo owner. |

## Known Limitations

- **CRM-07:** Đã sửa tên phiên ở sidebar và kiểm quyền hiện nút Create/Edit/Delete trên Contact, New Task và Add Note trên Lead. Phạm vi đọc/ghi hồ sơ theo Sales và owner còn cần xác nhận.
- **EXT-27:** Có quyền DocType và giao hồ sơ. Quyền theo owner/team trên site cần kiểm. Bảng dự án xếp quyền quản lý theo nhóm vào Future.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
