# CURRENT TASK — End-to-End Business Workflow documentation

## Active objective

Chuẩn hóa tài liệu modular theo business workflow xuyên module trên baseline PR #38; phân biệt AS-IS, TO-BE, GAP và Acceptance Evidence. Trạng thái: hoàn tất tài liệu và static verification, chờ review.

## Baseline

- Commit/HEAD/origin main: `a7534e74090f46498f5cbfcd30e0fcf77d882f2e` (PR #38).
- Branch: `docs/reconcile-baseline-20261128`.
- Checkout: `/home/tuyen/frappe-crm/frappe-bench/apps/doublet_crm`.
- Graphify: snapshot 25/11/2026 từ `809089aa`, stale so với baseline; chỉ dùng định vị, không rebuild.
- Checklist: giữ nguyên 110 unique IDs và trạng thái đã đối chiếu ngày 28/11/2026.

## Feature IDs

Giữ đủ 110 checklist IDs. Trọng tâm: `CRM-02`–`CRM-06`, `CRM-09`, `R2-01`–`R2-03`, `R2-06`, `EXT-01`–`EXT-04`, `EXT-19`, `CC-03`, `CALL-01`, `CALL-02`, `ORD-02`, `ORD-05`, `REP-09`, `REP-13` và các ID Activity liên quan.

## Scope

- Business Flow Contract, customer lifecycle, cross-module acceptance và workflow gaps.
- Feature specs, Data Model/Ownership, Permission/Dependency và workflow liên quan.
- Bảo toàn 110 checklist IDs, historical evidence và API compatibility contracts còn hiệu lực.
- Xuất toàn bộ docs diff so với HEAD ra `~/doublet-docs-review-v2.diff`.

## Out of scope

Source code nghiệp vụ, schema, frontend assets, database, Graphify, build, migration, runtime/browser/live tests, Google Sheets, commit, push và merge.

## Dependencies

Source/schema/API/permission/frontend/test tại baseline; checklist cập nhật; Graphify stale dùng để định vị; tài liệu modular hiện tại.

## Acceptance criteria

- 110/110 checklist IDs duy nhất; không tự nâng trạng thái.
- Mọi luồng trọng tâm có context/prefill/validation/persistence/exception contract.
- AS-IS, TO-BE, GAP rõ ràng; MOCK/DEMO không được mô tả là LIVE.
- Relative links hợp lệ; không dẫn tới tài liệu đã xóa.
- `git diff --check` PASS; thay đổi do task chỉ gồm Markdown.
- Báo cáo file thay đổi/xóa và nội dung chưa thể xác minh.

## Verification commands

```bash
git status --short --untracked-files=all
git diff --check -- '*.md'
# Read-only coverage, link/anchor, source-reference and Markdown checks
```

Không chạy build, migrate, runtime tests hoặc browser automation.

## Stop conditions

Dừng sau khi cập nhật và verification tài liệu; không commit/push/merge, không tự chọn feature tiếp theo.

## Latest result

Hoàn tất bốn tài liệu workflow mới và đồng bộ feature/architecture/tracking liên quan. Static verification: 110/110 checklist IDs duy nhất, 0 relative link/anchor lỗi, `git diff --check` PASS và task diff chỉ có Markdown. Runtime test/build/migration/browser/live integration **NOT RUN**. Full docs diff đã xuất tại `~/doublet-docs-review-v2.diff`; chưa commit/push/merge.
