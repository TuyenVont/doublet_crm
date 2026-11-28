# DoubleT CRM

DoubleT CRM là ứng dụng CRM độc lập trên Frappe Framework, phục vụ quản lý Lead, khách hàng, Deal, Catalog/Pricing, Quotation/Order, hoạt động bán hàng, Contact Center, Calls, Dashboard và Reports. Hệ thống tái sử dụng hạ tầng Frappe nhưng không yêu cầu Frappe CRM hoặc ERPNext.

Đặc tả đầy đủ, trạng thái 110 checklist IDs, dependency và workflow bắt đầu tại [docs/INDEX.md](docs/INDEX.md).

## Kiến trúc tóm tắt

- Backend: Frappe application `doublet_crm`, DocType/controller/whitelisted API, permission hooks, scheduler và background queue.
- Frontend: Vue 3, Vite và frappe-ui, phục vụ dưới `/doublet-crm`.
- Data: MariaDB DocTypes; Redis cho cache/queue; Frappe Communication/File/Notification Log cho hạ tầng dùng chung.
- Integration hiện tại: Email, Zalo OA MOCK, Call ingestion và optional AI call provider. WooCommerce, Zalo LIVE, PBX/SIP, n8n/Telegram và AI Business Insights vẫn là gap/target.

## Nhóm tính năng

CRM & Customer · Product/Pricing · Quotation/Order · Activities · Contact Center/Calls · Analytics · Integration/Automation · Platform/Quality.

## Prerequisites

- Frappe Bench tương thích, Python/Node/Yarn theo phiên bản bench.
- MariaDB, Redis, queue workers và scheduler.
- Docker/WSL là tùy chọn; xác minh site/container/path thực tế trước khi chạy lệnh.

## Installation

```bash
cd /path/to/frappe-bench
bench get-app https://github.com/TuyenVont/doublet_crm --branch main
bench --site <site> install-app doublet_crm
```

Clean installation chỉ có Frappe + DoubleT CRM chưa được nghiệm thu trên baseline hiện tại; xem [Known Gaps](docs/tracking/KNOWN_GAPS.md).

## Migration

Sao lưu database, public/private files và protected site config trước khi nâng cấp, sau đó:

```bash
bench --site <site> migrate
```

Chi tiết patch, hậu kiểm và rollback: [Deployment & Migration](docs/deployment/README.md).

## Frontend build

```bash
cd apps/doublet_crm/frontend
yarn install --frozen-lockfile
yarn build
```

Giữ HTML và assets cùng revision. Các lệnh trên là hướng dẫn, không phải bằng chứng đã chạy cho baseline tài liệu.

## Development workflow

1. Kiểm tra branch/worktree và local changes.
2. Đọc [AGENTS.md](AGENTS.md), [CURRENT_TASK.md](docs/CURRENT_TASK.md), feature file liên quan và dependency được link.
3. Tra Graphify hiện có trước; nếu stale thì đối chiếu source liên quan. Không tự rebuild Graphify.
4. Thay đổi trong scope, kiểm quyền backend, chạy focused verification được phép và cập nhật tài liệu bị ảnh hưởng.
5. Review diff; không commit/push/merge nếu chưa được yêu cầu.

## Documentation

- [Documentation Index](docs/INDEX.md)
- [Feature Index — 110/110](docs/tracking/FEATURE_INDEX.md)
- [Feature Status](docs/tracking/FEATURE_STATUS.md)
- [Known Gaps](docs/tracking/KNOWN_GAPS.md)
- [Testing & Acceptance](docs/testing/README.md)

## Known limitations

Customer 360/identity merge, owner/team record scope, Email Inbox chung, Zalo LIVE, PBX/SIP, WooCommerce, n8n/Telegram, AI Business Insights, localization và clean standalone install chưa được nghiệm thu đầy đủ.

## License

MIT.
