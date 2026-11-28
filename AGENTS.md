# DoubleT CRM — Agent working agreement

## Product boundary

- DoubleT CRM là standalone Frappe application dùng Vue 3, Vite và frappe-ui.
- Không sửa Frappe core; không copy source Frappe CRM.
- Không tạo dependency bắt buộc vào Frappe CRM hoặc ERPNext. Tái sử dụng Frappe infrastructure: ORM, permission, User/Role, Communication, File, queue, scheduler và Notification.
- Phân biệt module nghiệp vụ trong app với một Frappe app/repository độc lập; không tự tách app vật lý.
- Backend là security boundary. Frontend gating không thay DocPerm, record/field permission hoặc API checks.
- Không hard-code business configuration, secret, provider endpoint hoặc rule có thể cấu hình.
- Không tạo nguồn dữ liệu song song khi đã có source of truth; xem [Data Ownership](docs/architecture/DATA_OWNERSHIP.md).
- Không phá feature đang hoạt động; giữ field/status/API route và snapshot contract nếu scope không yêu cầu đổi.

## Safe working rules

1. Kiểm tra `git status --short`, branch, HEAD và remote baseline trước khi làm.
2. Giữ nguyên local changes của người dùng; không reset/restore/clean/overwrite.
3. Dùng branch hoặc worktree tách biệt dựa trên baseline đã xác minh; không sửa deploy branch.
4. Đọc diff trước review. Không commit, push, merge, tạo PR hoặc deploy nếu chưa được yêu cầu.
5. Chỉ chạy test/build/migration/browser/database write khi scope và quyền cho phép. Ghi chính xác command, commit/site/role và PASS/FAIL/NOT TESTED.
6. Không coi test file tồn tại, source tồn tại hoặc evidence trước merge là acceptance PASS.
7. Bảo vệ secret, credentials và dữ liệu cá nhân trong log/evidence.

## Documentation-first workflow

1. Kiểm tra Git status và branch.
2. Đọc `AGENTS.md`.
3. Đọc [CURRENT_TASK.md](docs/CURRENT_TASK.md).
4. Tra Graphify hiện có bằng query/path/explain hoặc wiki index nếu phù hợp.
5. Mở [docs/INDEX.md](docs/INDEX.md) để tìm **feature file liên quan**, không đọc toàn bộ docs.
6. Đọc [Business Flow Contract](docs/architecture/BUSINESS_FLOW_CONTRACT.md), dependency, workflow và permission **được feature file liên kết**; không cần đọc các contract không liên quan.
7. Đối chiếu source code thực tế; source thắng khi docs mâu thuẫn, nhưng phải ghi nhận và sửa docs.
8. Triển khai và chạy focused verification cùng test luồng liên module bị ảnh hưởng trong chính lượt làm việc; nếu scope cấm runtime test thì ghi `NOT RUN`, không suy ra PASS.
9. Cập nhật feature spec, [FEATURE_STATUS](docs/tracking/FEATURE_STATUS.md), dependency/workflow bị ảnh hưởng.
10. Ghi kết quả và dừng; không tự chọn feature tiếp theo.

## Graphify và quota-saving

- Graphify-first khi điều tra code: ưu tiên graph query/path/explain và `graphify-out/wiki/index.md` nếu có.
- Graphify có thể stale; dùng nó để định vị rồi xác minh source liên quan.
- Không tự update/rebuild Graphify hoặc chạy post-update query.
- Không quét lại repository, đọc toàn bộ tài liệu, gọi subagent, build hoặc chạy broad test nếu task hẹp không cần.
- Documentation-only: chỉ sửa Markdown được yêu cầu; không migration, build, runtime test, generated assets, database hoặc dependency install.

## Branch, test và review

- Một bounded work package trên một branch/worktree; không trộn parked/dirty worktree khác.
- Tái sử dụng route/component/API/DocType hiện có; search trước khi tạo mới.
- Focused tests trong cùng pass nếu được phép; DB-mutating test dùng isolated site và cần phê duyệt.
- Nghiệm thu quyền tối thiểu cân nhắc Administrator, Sales Manager, hai Sales User khác owner/assignee và Guest/API principal phù hợp.
- Report aggregate, export và drill-down phải dùng cùng permission-scoped dataset; unknown không phải 0.
- Quotation/Order giữ snapshot; Pricing phân biệt giá `0` với missing; không silently reprice lịch sử.
- Handoff gồm file thay đổi, verification, migration/schema impact, compatibility risk và nội dung chưa kiểm.
- Mọi thay đổi entry point, route, prefill, conversion hoặc create-from-record phải cập nhật contract Source → Trigger → Destination → Context → Validation → Persistence và scenario trong [Cross-module Acceptance](docs/testing/CROSS_MODULE_ACCEPTANCE.md).
