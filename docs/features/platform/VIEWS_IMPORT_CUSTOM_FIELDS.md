# Saved Views, Import/Export & Custom Fields

[← platform index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-ext-25"></a>
- `EXT-25` — Lưu bộ lọc dùng lại trên Lead và Deal
<a id="feature-ext-26"></a>
- `EXT-26` — Nhập Lead/Contact và xuất danh sách đã lọc
<a id="feature-ext-28"></a>
- `EXT-28` — Admin thêm trường nghiệp vụ ngoài core

## Mục đích nghiệp vụ

Lưu bộ lọc dùng lại trên Lead và Deal; Nhập Lead/Contact và xuất danh sách đã lọc; Admin thêm trường nghiệp vụ ngoài core. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| EXT-25 | Lưu bộ lọc dùng lại trên Lead và Deal | Nâng cấp · Danh sách | P2 | ViewControls có thao tác View. LeadsView/DealsView dùng bộ lọc riêng, chưa thấy chức năng lưu ở hai trang này. | HubSpot · Ứng viên nâng cấp giao diện |
| EXT-26 | Nhập Lead/Contact và xuất danh sách đã lọc | R1 · Dữ liệu | P1 | ViewControls có Import/Export dùng chung. Chưa xác minh đường vào trên giao diện DoubleT và quyền. | HubSpot · RESEARCH A108:A109 · Platform |
| EXT-28 | Admin thêm trường nghiệp vụ ngoài core | R1 · Nền tảng | P1 | Bảng dự án xếp Custom Fields là Platform MVP. Code form Vue có tập trường cố định, chưa xác minh hiển thị field mới. | HubSpot · CRM CORE &APP A194:A197 · Platform |

## Data Model

Frappe app metadata/hooks, Vue assets/routes, translation/preferences, test/deployment evidence.

Xem [Data Model](../../architecture/DATA_MODEL.md) và [Data Ownership](../../architecture/DATA_OWNERSHIP.md).

## Business Rules

Các validation riêng được xác định từ source/checklist trong bảng dưới đây; quy tắc xuyên module được quản lý tại [Data Ownership](../../architecture/DATA_OWNERSHIP.md) và [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Workflow và State Transitions

Cấu hình/phát hành → migrate/build/verify → role/browser/business acceptance; task docs không chạy các bước runtime.

Chi tiết end-to-end nằm ở mục Related Workflows; state không được suy ra từ nhãn UI nếu controller/schema quy định khác.

## Permissions

Platform utility không được bypass DocPerm/record scope; secrets không nằm trong source/evidence.

Contract chung: [Permission Model](../../architecture/PERMISSION_MODEL.md).

## Source Mapping

| ID | Source reference | Bằng chứng mới trong checklist |
| --- | --- | --- |
| EXT-25 | ViewControls.vue | Chưa có bằng chứng mới |
| EXT-26 | ViewControls.vue | Chưa có bằng chứng mới |
| EXT-28 | FrappeLead.vue | Chưa có bằng chứng mới |

## Upstream Dependencies

- Frappe Framework và repository configuration.
- [Report Platform](../analytics/REPORT_PLATFORM.md)
- [Permissions](../crm/PERMISSIONS.md)

## Downstream Impact

- Toàn bộ module nghiệp vụ.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- Xem [workflow index](../../workflows/README.md); chưa có workflow riêng cho mục này.

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| EXT-25 | Có một phần | Đề xuất | Checklist: Có một phần; Đề xuất. Không suy ra runtime PASS. |
| EXT-26 | Cần xác minh | Cần kiểm | Checklist: Cần xác minh; Cần kiểm. Không suy ra runtime PASS. |
| EXT-28 | Cần xác minh | Cần kiểm | Checklist: Cần xác minh; Cần kiểm. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| EXT-25 | Lưu một view Lead và một view Deal. Mở lại vẫn áp đúng bộ lọc, người dùng khác xem theo quyền. |
| EXT-26 | Nhập file mẫu kèm lỗi theo dòng và kiểm trùng. Xuất đúng số bản ghi sau lọc bằng role được phép. |
| EXT-28 | Thêm một field mẫu cho Lead hoặc Deal theo cách nhóm chọn. Kiểm nhập/lưu, quyền và nâng cấp. |

## Known Limitations

- **EXT-25:** ViewControls có thao tác View. LeadsView/DealsView dùng bộ lọc riêng, chưa thấy chức năng lưu ở hai trang này.
- **EXT-26:** ViewControls có Import/Export dùng chung. Chưa xác minh đường vào trên giao diện DoubleT và quyền.
- **EXT-28:** Bảng dự án xếp Custom Fields là Platform MVP. Code form Vue có tập trường cố định, chưa xác minh hiển thị field mới.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
