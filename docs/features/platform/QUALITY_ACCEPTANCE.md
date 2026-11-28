# Quality, Deployment & Business Acceptance

[← platform index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-qa-01"></a>
- `QA-01` — Hồi quy browser và quyền trên build cuối
<a id="feature-qa-02"></a>
- `QA-02` — Cài sạch, nâng cấp dữ liệu và đồng bộ asset
<a id="feature-qa-03"></a>
- `QA-03` — Hướng dẫn cài đặt, demo và minh chứng khóa luận
<a id="feature-qa-04"></a>
- `QA-04` — Tổng hợp số đo đạt mục tiêu BA

## Mục đích nghiệp vụ

Hồi quy browser và quyền trên build cuối; Cài sạch, nâng cấp dữ liệu và đồng bộ asset; Hướng dẫn cài đặt, demo và minh chứng khóa luận; Tổng hợp số đo đạt mục tiêu BA. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| QA-01 | Hồi quy browser và quyền trên build cuối | Bàn giao · Kiểm thử | P0 | 23/11 · main 4d835a9 có các test mới: frontend/tests/reportsHub.test.mjs (PR #29), test_doublet_note (PR #28), test_doublet_call_ai_summary, test_contact_center_calls, test_callback_task_permissions (PR #27), Quotation pricing/snapshot (PR #26). Đây là sự hiện diện của test trong source, CHƯA phải log test PASS trên site bàn giao. | BA QD-09, SM-01–06 · FEATURE_STATUS |
| QA-02 | Cài sạch, nâng cấp dữ liệu và đồng bộ asset | Bàn giao · Dữ liệu | P0 | 23/11 · main 4d835a9 có patches PR #27 cho Call queue (backfill_call_queue), lịch sử Call Event và AI Summary cũ (archive/recover_legacy_call_ai_notes, protect_call_case_history). Chưa có log migrate/cài sạch trên bản main hiện tại. | QUY TẮC · Hướng dẫn cài đặt DoubleT |
| QA-03 | Hướng dẫn cài đặt, demo và minh chứng khóa luận | Bàn giao · Tài liệu | P0 | 23/11 · main đã đổi Reports Hub, Contact Center/AI Summary và Deal Kanban ở các PR #27–29. Hướng dẫn/slide demo cũ có nguy cơ lệch chức năng; chưa có commit xác nhận cập nhật tài liệu bàn giao theo main 4d835a9. | Hướng dẫn DoubleT · BA SM-01–06 |
| QA-04 | Tổng hợp số đo đạt mục tiêu BA | Bàn giao · Đo lường | P1 | BA có SM-01 đến SM-06. Chưa có bảng nghiệm thu bản cuối cho các tiêu chí áp dụng trong phần được rà. | BA 3.5, SM-01–06 |

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
| QA-01 | FEATURE_STATUS.md | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. Đã kiểm conflict, frontend và build; chưa chạy lại backend regression và role matrix. |
| QA-02 | patches.txt | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. Migration site hiện tại PASS sau bổ sung controller; cài sạch chưa thử. |
| QA-03 | ARCHITECTURE.md | Chưa có bằng chứng mới |
| QA-04 | FEATURE_STATUS.md | Chưa có bằng chứng mới |

## Upstream Dependencies

- Frappe Framework và repository configuration.
- [Testing](../../testing/README.md)
- [Deployment](../../deployment/README.md)

## Downstream Impact

- Toàn bộ module nghiệp vụ.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- Xem [workflow index](../../workflows/README.md); chưa có workflow riêng cho mục này.

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| QA-01 | Cần xác minh | Cần kiểm | Checklist: Cần xác minh; Cần kiểm. Không suy ra runtime PASS. |
| QA-02 | Cần xác minh | Cần kiểm | Checklist: Cần xác minh; Cần kiểm. Không suy ra runtime PASS. |
| QA-03 | Có một phần | Cần làm | Checklist: Có một phần; Cần làm. Không suy ra runtime PASS. |
| QA-04 | Cần xác minh | Cần kiểm | Checklist: Cần xác minh; Cần kiểm. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| QA-01 | Chạy npm test/build và bench run-tests trên main 4d835a9; ghi số PASS/FAIL và log. Browser: Admin/Sales/Manager ở CRM → Quotation → Order và Contact Center, Reports placeholder, mobile 375px. |
| QA-02 | Backup site, thử cài sạch frappe+doublet_crm và nâng cấp site cũ ở test; chạy bench migrate/build, kiểm Call Log/Callback/AI Summary dữ liệu trước–sau và asset frontend, ghi log. |
| QA-03 | Cập nhật hướng dẫn cài đặt và nghiệp vụ theo main 4d835a9, kèm ảnh/video demo và test evidence; mô tả rõ OA mock, AI cần BeeKnoee config, Reports Hub chỉ là khung. |
| QA-04 | Đếm ca sync đúng, match đúng và tự động hóa đúng. Ghi số thao tác trước/sau và kịch bản truy vết trong phạm vi được giao. |

## Known Limitations

- **QA-01:** 23/11 · main 4d835a9 có các test mới: frontend/tests/reportsHub.test.mjs (PR #29), test_doublet_note (PR #28), test_doublet_call_ai_summary, test_contact_center_calls, test_callback_task_permissions (PR #27), Quotation pricing/snapshot (PR #26). Đây là sự hiện diện của test trong source, CHƯA phải log test PASS trên site bàn giao.
- **QA-02:** 23/11 · main 4d835a9 có patches PR #27 cho Call queue (backfill_call_queue), lịch sử Call Event và AI Summary cũ (archive/recover_legacy_call_ai_notes, protect_call_case_history). Chưa có log migrate/cài sạch trên bản main hiện tại.
- **QA-03:** 23/11 · main đã đổi Reports Hub, Contact Center/AI Summary và Deal Kanban ở các PR #27–29. Hướng dẫn/slide demo cũ có nguy cơ lệch chức năng; chưa có commit xác nhận cập nhật tài liệu bàn giao theo main 4d835a9.
- **QA-04:** BA có SM-01 đến SM-06. Chưa có bảng nghiệm thu bản cuối cho các tiêu chí áp dụng trong phần được rà.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
