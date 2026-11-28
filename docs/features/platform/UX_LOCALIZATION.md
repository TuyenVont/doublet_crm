# Localization & Responsive UX

[← platform index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-ux-01"></a>
- `UX-01` — Hiển thị bảng tiền và modal ở cửa sổ hẹp
<a id="feature-ux-02"></a>
- `UX-02` — Việt hóa màn hình ưu tiên

## Mục đích nghiệp vụ

Hiển thị bảng tiền và modal ở cửa sổ hẹp; Việt hóa màn hình ưu tiên. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| UX-01 | Hiển thị bảng tiền và modal ở cửa sổ hẹp | R1 · Hoàn thiện UI | P1 | Ảnh ngày 15/11 cho thấy Line Total bị che. Bảng có min-width 1120px trong QuotationForm. Source đã có cải tiến modal Product/Price List. | Ảnh UI 15/11 · Báo cáo 08–14/11 |
| UX-02 | Việt hóa màn hình ưu tiên | R1 · Hoàn thiện UI | P2 | Có plugin dịch và hook boot. Chưa xác nhận toàn bộ nhãn/thông báo trong luồng demo có bản tiếng Việt. | NOTES · CHECKLIST cũ #7 |

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
| UX-01 | QuotationForm.vue | 18/11 · Audit source. Chưa xác minh UI/màn hẹp bằng browser. |
| UX-02 | main.js | Chưa có bằng chứng mới |

## Upstream Dependencies

- Frappe Framework và repository configuration.
- [Quality](QUALITY_ACCEPTANCE.md)

## Downstream Impact

- Toàn bộ module nghiệp vụ.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- Xem [workflow index](../../workflows/README.md); chưa có workflow riêng cho mục này.

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| UX-01 | Cần xác minh | Cần kiểm | Checklist: Cần xác minh; Cần kiểm. Không suy ra runtime PASS. |
| UX-02 | Có một phần | Cần làm | Checklist: Có một phần; Cần làm. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| UX-01 | Kiểm viewport hẹp, cột tiền, SKU dài, modal Product/Price List và nút lưu/xóa. Rà sidebar và toolbar Company ở 360px. |
| UX-02 | Nếu giữ yêu cầu NOTES, Việt hóa Lead, Deal, báo giá và thông báo chính. Kiểm PDF/ngôn ngữ và USD theo phạm vi chốt. |

## Known Limitations

- **UX-01:** Ảnh ngày 15/11 cho thấy Line Total bị che. Bảng có min-width 1120px trong QuotationForm. Source đã có cải tiến modal Product/Price List.
- **UX-02:** Có plugin dịch và hook boot. Chưa xác nhận toàn bộ nhãn/thông báo trong luồng demo có bản tiếng Việt.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
