# End-to-End Business Workflows

[← Documentation Index](../INDEX.md) · [Dependency Map](../architecture/DEPENDENCY_MAP.md)

Các luồng dưới đây phân biệt implementation hiện tại, partial, target và acceptance pending. Quy tắc nghiệp vụ thuộc feature được liên kết thay vì lặp lại tại workflow.

| Workflow | Kịch bản |
| --- | --- |
| WF-01 | [Bán hàng cho khách cá nhân](WF_01_INDIVIDUAL_SALES.md) |
| WF-02 | [Bán hàng cho khách doanh nghiệp](WF_02_COMPANY_SALES.md) |
| WF-03 | [Gửi/nhận Email và báo giá PDF](WF_03_QUOTATION_EMAIL.md) |
| WF-04 | [Tiếp nhận và chăm sóc qua Zalo OA](WF_04_ZALO_CARE.md) |
| WF-05 | [Cuộc gọi nhỡ và Callback Task](WF_05_MISSED_CALL_CALLBACK.md) |
| WF-06 | [Recording → AI Call Summary → Note](WF_06_CALL_AI_NOTE.md) |
| WF-07 | [Đồng bộ WooCommerce](WF_07_WOOCOMMERCE_SYNC.md) |
| WF-08 | [Task/Appointment → Reminder → Notification](WF_08_ACTIVITY_REMINDER.md) |
| WF-09 | [Smart Insights → Follow-up Task](WF_09_SMART_INSIGHTS_FOLLOW_UP.md) |
| WF-10 | [CRM Event → Webhook → n8n → Action → Execution Log](WF_10_N8N_AUTOMATION.md) |
