# CURRENT TASK — Modular system documentation

## Active objective

Phân tách đặc tả DoubleT CRM từ tài liệu đơn khối thành hệ thống Markdown theo module/feature, bảo toàn checklist, source audit, business rules, dependency, workflow và evidence; trạng thái hiện tại: hoàn tất triển khai tài liệu, chờ người dùng review.

## Baseline

- Commit/HEAD/origin main: `c087d806e16d26701f6a1597bd82ae3ab6a55319` (PR #37), xác minh 28/11/2026.
- Branch/worktree: `docs/system-specification` tại `/tmp/doublet-crm-system-spec`.
- Graphify: snapshot 25/11/2026, dùng để định vị; không rebuild.
- Checklist: tab `KLTN · Đối chiếu bản cuối`, 110 unique IDs.

## Feature IDs

Toàn bộ 110 mã được quản lý đúng một lần tại [FEATURE_INDEX.md](tracking/FEATURE_INDEX.md), thuộc 8 nhóm tài liệu feature: CRM, Sales, Activities, Contact Center, Analytics, Integration, Automation và Platform.

## Scope

- `docs/INDEX.md`, `docs/architecture/`, `docs/features/`, `docs/workflows/`, `docs/testing/`, `docs/deployment/`, `docs/tracking/`.
- Đồng bộ `README.md`, `AGENTS.md` và file này.
- Xóa tài liệu đơn khối/cũ sau khi xác minh nội dung, link và coverage.

## Out of scope

Python/Vue/JavaScript/JSON, database, build, migration, runtime/browser/live test, Graphify rebuild, generated assets, Google Sheets update, commit/push/merge/PR và feature nghiệp vụ mới.

## Dependencies

Master Checklist, Business Analysis, Development Rules, NOTES, Graphify hiện có, source baseline và tài liệu repository trước hợp nhất.

## Acceptance criteria

- AC-01: `FEATURE_INDEX.md` bao phủ 110/110, không thiếu/trùng.
- AC-02: tài liệu tách theo module/feature và bảo toàn nội dung nghiệp vụ.
- AC-03: dependency/downstream/workflow có relative links hợp lệ.
- AC-04: entry-point đồng bộ, không còn reference lỗi thời.
- AC-05: `git diff --check` PASS; diff chỉ gồm Markdown được phép.

## Verification commands

```bash
git status --short
git diff --check
find docs -type f -name '*.md' -print
# Read-only link/anchor, coverage, Mermaid and reference checks
```

Không chạy build, migration, runtime tests hoặc browser automation cho task này.

## Stop conditions

Dừng sau khi verification tài liệu hoàn tất và báo cáo; không commit/push/merge, không chọn feature tiếp theo.

## Latest result

Cấu trúc modular đã được tạo với 36 feature files, 8 feature README, 10 workflow, 110 feature anchors và tracking/architecture/testing/deployment docs. Coverage/link/anchor/Mermaid và `git diff --check` theo phạm vi Markdown đều PASS. Nội dung đã được chuyển nguyên vẹn sang checkout local chính; worktree tạm được giữ lại để review. Runtime acceptance không chạy theo giới hạn documentation-only.
