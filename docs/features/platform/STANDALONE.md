# Standalone DoubleT CRM Application

[← platform index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-crm-08"></a>
- `CRM-08` — Chạy luồng lõi trên app DoubleT độc lập

## Mục đích nghiệp vụ

Chạy luồng lõi trên app DoubleT độc lập. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| CRM-08 | Chạy luồng lõi trên app DoubleT độc lập | R1 · Vận hành | P0 | 23/11 · main 4d835a9: PR #27 (218cdef) dùng API/Doctype DoubleT cho Contact Center Calls, Call Log, Callback Task; frontend vẫn có kiểm tra tùy chọn khi Frappe CRM được cài. Chưa xác minh cài sạch chỉ có Frappe Framework. | QUY TẮC · AGENTS.md |

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
| CRM-08 | api.py | 22/11 · PR #27 → main 218cdef. Diff frontend/src/components/Activities/CallArea.vue, RecordCallHistory.vue, hooks.py. Chưa chạy browser ở bản main mới. |

## Upstream Dependencies

- Frappe Framework và repository configuration.
- [Architecture](../../architecture/SYSTEM_ARCHITECTURE.md)
- [Deployment](../../deployment/README.md)

## Downstream Impact

- Toàn bộ module nghiệp vụ.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- Xem [workflow index](../../workflows/README.md); chưa có workflow riêng cho mục này.

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| CRM-08 | Có | Cần làm | Standalone app có source nhưng clean install chỉ Frappe chưa xác minh. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| CRM-08 | Dựng site sạch chỉ cài frappe + doublet_crm, chạy migrate/build. Kiểm Lead/Contact Calls, callback, email, file và đường dẫn; nếu còn phụ thuộc Frappe CRM ghi rõ stacktrace và cách xử lý. |

## Known Limitations

- **CRM-08:** Source có nhưng vẫn phải theo acceptance status.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
