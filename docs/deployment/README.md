# Deployment & Migration

[← Documentation Index](../INDEX.md) · [Standalone](../features/platform/STANDALONE.md) · [Testing](../testing/README.md)

Prerequisites: supported Frappe Bench/Python/Node/Yarn, MariaDB, Redis/queue/scheduler; Docker/WSL optional. The app declares `phonenumbers` and bench-managed Frappe, not Frappe CRM/ERPNext.

```bash
cd /path/to/frappe-bench
bench get-app https://github.com/TuyenVont/doublet_crm --branch main
bench --site <site> install-app doublet_crm
bench --site <site> migrate
cd apps/doublet_crm/frontend
yarn install --frozen-lockfile
yarn build
```

Các lệnh là hướng dẫn tham chiếu và **không được chạy trong task này**. Trên môi trường Docker đã ghi nhận, chạy bench trong container/bench path thực tế sau khi xác minh mount/site.

`patches.txt` post-model-sync gồm category backfill, default Price Lists, Zalo Lead Source, call queue, bảo vệ lịch sử Call case và archive/recover legacy AI notes. Trước upgrade: backup DB + public/private files + protected site config, ghi commit/assets, pause scheduler/mute email trên QA. Sau migrate: kiểm row counts/link/unique constraints/private attachments, queue/worker/scheduler và HTML/asset hash. Rollback phải dùng database, files, source và frontend assets cùng revision; dữ liệu phát sinh sau cutover phải được bảo toàn/reconcile trước restore.

Clean-install acceptance bắt buộc vì còn inherited `crm.*`, `crm.fcrm.*`, WhatsApp/telephony/ViewControls và optional ERPNext references. Không tuyên bố standalone production-ready trước khi luồng core trên site chỉ có Frappe + DoubleT vượt qua.
