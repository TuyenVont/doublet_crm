# Feature Index & Checklist Traceability

[← Documentation Index](../INDEX.md) · [Feature Status](FEATURE_STATUS.md) · [Known Gaps](KNOWN_GAPS.md)

Bảng này là ánh xạ chính: mỗi checklist ID xuất hiện đúng một lần. Trạng thái checklist được giữ nguyên; cột baseline chỉ ghi phát hiện source, không tự cập nhật Google Sheets.

| Checklist ID | Feature | Module | Spec anchor | Source reference | Implementation status | Acceptance status |
| --- | --- | --- | --- | --- | --- | --- |
| CRM-01 | Danh sách, tạo và cập nhật Lead | crm | [LEAD](../features/crm/LEAD.md#feature-crm-01) | FrappeLead.vue | Có; source reference FrappeLead.vue. | Cần kiểm |
| CRM-02 | Lead → Deal cho cá nhân và doanh nghiệp | crm | [LEAD_CONVERSION](../features/crm/LEAD_CONVERSION.md#feature-crm-02) | doublet_lead.py | Có; source reference doublet_lead.py. | Cần kiểm |
| CRM-03 | Quản lý cơ hội và pipeline | crm | [DEAL_PIPELINE](../features/crm/DEAL_PIPELINE.md#feature-crm-03) | DealsView.vue | Có; source reference DealsView.vue. | Cần kiểm |
| CRM-04 | Danh sách, chi tiết Contact và Company | crm | [CUSTOMER](../features/crm/CUSTOMER.md#feature-crm-04) | router.js | Có; source reference router.js. | Cần kiểm |
| CRM-05 | Hồ sơ khách tập trung và timeline đa kênh | crm | [CUSTOMER](../features/crm/CUSTOMER.md#feature-crm-05) | api.py | Có một phần; source reference api.py. | Cần làm |
| CRM-06 | Phát hiện và xử lý hồ sơ trùng | crm | [IDENTITY_DUPLICATES](../features/crm/IDENTITY_DUPLICATES.md#feature-crm-06) | doublet_lead.py | Có một phần; source reference doublet_lead.py. | Cần làm |
| CRM-07 | Role và phạm vi xem/sửa hồ sơ | crm | [PERMISSIONS](../features/crm/PERMISSIONS.md#feature-crm-07) | ContactDetailView.vue | Có một phần; source reference ContactDetailView.vue. | Cần kiểm |
| CRM-08 | Chạy luồng lõi trên app DoubleT độc lập | platform | [STANDALONE](../features/platform/STANDALONE.md#feature-crm-08) | api.py | Có app standalone; clean-install chỉ Frappe chưa xác minh. | Cần làm |
| SALE-01 | Category chính/phụ và Product Standard | sales | [PRODUCT_CATALOG](../features/sales/PRODUCT_CATALOG.md#feature-sale-01) | doublet_product.py | Có; source reference doublet_product.py. | Cần kiểm |
| SALE-02 | Template và Product Variant | sales | [PRODUCT_CATALOG](../features/sales/PRODUCT_CATALOG.md#feature-sale-02) | doublet_product.py | Có; source reference doublet_product.py. | Cần kiểm |
| SALE-08 | Ảnh sản phẩm và chế độ List/Grid | sales | [PRODUCT_CATALOG](../features/sales/PRODUCT_CATALOG.md#feature-sale-08) | ProductsView.vue | Có; source reference ProductsView.vue. | Cần kiểm |
| SALE-09 | Trang chi tiết Product và danh sách Variant | sales | [PRODUCT_CATALOG](../features/sales/PRODUCT_CATALOG.md#feature-sale-09) | ProductDetailView.vue | Có; source reference ProductDetailView.vue. | Cần kiểm |
| SALE-10 | Chọn sản phẩm từ Catalog trong Quotation | sales | [QUOTATION](../features/sales/QUOTATION.md#feature-sale-10) | QuotationForm.vue | Có; source reference QuotationForm.vue. | Cần kiểm |
| SALE-03 | Bảng giá theo khách và giá dự phòng | sales | [PRICING](../features/sales/PRICING.md#feature-sale-03) | pricing.py | Có; source reference pricing.py. | Cần kiểm |
| SALE-04 | Lập Quotation từ Deal và danh sách | sales | [QUOTATION](../features/sales/QUOTATION.md#feature-sale-04) | QuotationForm.vue | Có; source reference QuotationForm.vue. | Cần kiểm |
| SALE-11 | Đơn giản hóa chọn khách, Deal và bảng giá | sales | [QUOTATION](../features/sales/QUOTATION.md#feature-sale-11) | QuotationForm.vue | Có; source reference QuotationForm.vue. | Cần kiểm |
| SALE-05 | Tính chiết khấu %, số tiền và làm tròn | sales | [QUOTATION](../features/sales/QUOTATION.md#feature-sale-05) | doublet_quotation.py | Có; source reference doublet_quotation.py. | Cần kiểm |
| SALE-06 | Snapshot, dữ liệu cũ và trạng thái báo giá | sales | [QUOTATION](../features/sales/QUOTATION.md#feature-sale-06) | doublet_quotation.py | Có; source reference doublet_quotation.py. | Cần kiểm |
| SALE-07 | Xuất và gửi PDF báo giá qua email | sales | [QUOTATION](../features/sales/QUOTATION.md#feature-sale-07) | quotation_pdf.py | Có; source reference quotation_pdf.py. | Cần kiểm |
| ORD-01 | Danh sách, chi tiết và tạo/sửa Order thủ công | sales | [ORDER](../features/sales/ORDER.md#feature-ord-01) | OrderForm.vue | Có; source reference OrderForm.vue. | Cần kiểm |
| ORD-02 | Tạo một Order từ Quotation và giữ dữ liệu giá đã lưu | sales | [ORDER](../features/sales/ORDER.md#feature-ord-02) | doublet_order.py | Có; source reference doublet_order.py. | Cần kiểm |
| ORD-03 | Hoàn tất hoặc hủy Order khi báo giá nguồn thay đổi | sales | [ORDER](../features/sales/ORDER.md#feature-ord-03) | doublet_order.py | Có; source reference doublet_order.py. | Cần kiểm |
| ORD-04 | Lọc Deal theo Customer Type và Contact/Company | sales | [ORDER](../features/sales/ORDER.md#feature-ord-04) | OrderForm.vue | Có; source reference OrderForm.vue. | Cần kiểm |
| ORD-05 | Quy tắc trạng thái Quotation được phép tạo Order | sales | [ORDER](../features/sales/ORDER.md#feature-ord-05) | QuotationForm.vue | Có; source reference QuotationForm.vue. | Cần kiểm |
| ORD-06 | Quyền xem và sửa Order của Sales và quản lý | sales | [ORDER](../features/sales/ORDER.md#feature-ord-06) | doublet_order.json | Có một phần; source reference doublet_order.json. | Cần kiểm |
| ORD-07 | Nghiệm thu Order trên bản main đã gộp | sales | [ORDER](../features/sales/ORDER.md#feature-ord-07) | test_doublet_order.py | Có; source reference test_doublet_order.py. | Cần kiểm |
| ACT-01 | Tasks và phân công | activities | [TASKS](../features/activities/TASKS.md#feature-act-01) | Tasks.vue | Có; source reference Tasks.vue. | Cần kiểm |
| ACT-02 | Notes và Activities | activities | [NOTES_TIMELINE](../features/activities/NOTES_TIMELINE.md#feature-act-02) | SharedNotes.vue | Có; source reference SharedNotes.vue. | Cần kiểm |
| REP-01 | Dashboard tổng quan nhanh Lead, Deal và báo giá (giữ nguyên khi xây Reports) | analytics | [DASHBOARD](../features/analytics/DASHBOARD.md#feature-rep-01) | dashboard.py · Dashboard.vue · smart_insights.py | Có; source reference dashboard.py · Dashboard.vue · smart_insights.py. | Cần kiểm |
| REP-02 | Sales Performance: hiệu suất bán hàng theo nhân viên và kỳ | analytics | [SALES_PERFORMANCE](../features/analytics/SALES_PERFORMANCE.md#feature-rep-02) | reports.py · SalesPerformanceReport.vue · report_tools.py | Có; source reference reports.py · SalesPerformanceReport.vue · report_tools.py. | Cần kiểm |
| UX-01 | Hiển thị bảng tiền và modal ở cửa sổ hẹp | platform | [UX_LOCALIZATION](../features/platform/UX_LOCALIZATION.md#feature-ux-01) | QuotationForm.vue | Cần xác minh; source reference QuotationForm.vue. | Cần kiểm |
| CRM-09 | Điều hướng hai chiều giữa hồ sơ và cơ hội | crm | [DEAL_PIPELINE](../features/crm/DEAL_PIPELINE.md#feature-crm-09) | DoubleTEntityDetail.vue | Có một phần; source reference DoubleTEntityDetail.vue. | Cần làm |
| UX-02 | Việt hóa màn hình ưu tiên | platform | [UX_LOCALIZATION](../features/platform/UX_LOCALIZATION.md#feature-ux-02) | main.js | Có một phần; source reference main.js. | Cần làm |
| R2-01 | Tiếp nhận và lưu tin nhắn OA | contact-center | [INBOX](../features/contact-center/INBOX.md#feature-r2-01) | zalo_oa.py:86 | Có một phần; source reference zalo_oa.py:86. | Chờ phụ thuộc |
| R2-02 | Inbox, lịch sử và phản hồi OA | contact-center | [INBOX](../features/contact-center/INBOX.md#feature-r2-02) | zalo_inbox.py:364 | Có một phần; source reference zalo_inbox.py:364. | Cần kiểm |
| R2-03 | Tạo hoặc cập nhật Lead từ OA | contact-center | [INBOX](../features/contact-center/INBOX.md#feature-r2-03) | zalo_oa.py:86 | Có một phần; source reference zalo_oa.py:86. | Chờ phụ thuộc |
| R2-04 | Lượt 1 · Email báo giá trên Lead, Deal và Quotation | contact-center | [EMAIL](../features/contact-center/EMAIL.md#feature-r2-04) | QuotationEmails.vue:192 | Có; source reference QuotationEmails.vue:192. | Cần kiểm |
| R2-06 | Nguồn dữ liệu, sự kiện lặp và lịch sử đồng bộ | integration | [WEBHOOK_N8N](../features/integration/WEBHOOK_N8N.md#feature-r2-06) | hooks.py | Có một phần; source reference hooks.py. | Cần làm |
| R3-01 | Workflow n8n chạy trên DoubleT | integration | [WEBHOOK_N8N](../features/integration/WEBHOOK_N8N.md#feature-r3-01) | hooks.py | Bản cũ/ngoài repo; source reference hooks.py. | Cần làm |
| REP-03 | Activity & Contact Center Reports theo nhân viên/kỳ | analytics | [ACTIVITY_CONTACT_CENTER](../features/analytics/ACTIVITY_CONTACT_CENTER.md#feature-rep-03) | reports.py · ActivityContactCenterReport.vue · report_tools.py · test_activity_reports.py | Có một phần; source reference reports.py · ActivityContactCenterReport.vue · report_tools.py · test_activity_reports.py. | Cần kiểm |
| R2-05 | Đồng bộ Product/SKU/Variant với WooCommerce | integration | [WOOCOMMERCE](../features/integration/WOOCOMMERCE.md#feature-r2-05) | ProductsView.vue | Chưa thấy; source reference ProductsView.vue. | Cần làm |
| R3-02 | Chấm điểm Lead và tạo Task theo dõi | automation | [LEAD_ASSIGNMENT_SCORING](../features/automation/LEAD_ASSIGNMENT_SCORING.md#feature-r3-02) | doublet_lead.json | Chưa thấy; source reference doublet_lead.json. | Cần làm |
| R3-03 | Thông báo Telegram từ workflow | integration | [EXTERNAL_CHANNELS](../features/integration/EXTERNAL_CHANNELS.md#feature-r3-03) | hooks.py | Chưa thấy; source reference hooks.py. | Cần làm |
| R3-04 | AI hỗ trợ một tình huống tư vấn/chăm sóc | integration | [EXTERNAL_CHANNELS](../features/integration/EXTERNAL_CHANNELS.md#feature-r3-04) | hooks.py | Chưa thấy; source reference hooks.py. | Cần chốt |
| R3-05 | Custom app cấu hình và giám sát Webhook | integration | [WEBHOOK_N8N](../features/integration/WEBHOOK_N8N.md#feature-r3-05) | hooks.py | Cần chốt; source reference hooks.py. | Cần chốt |
| QA-01 | Hồi quy browser và quyền trên build cuối | platform | [QUALITY_ACCEPTANCE](../features/platform/QUALITY_ACCEPTANCE.md#feature-qa-01) | FEATURE_STATUS.md | Cần xác minh; source reference FEATURE_STATUS.md. | Cần kiểm |
| QA-02 | Cài sạch, nâng cấp dữ liệu và đồng bộ asset | platform | [QUALITY_ACCEPTANCE](../features/platform/QUALITY_ACCEPTANCE.md#feature-qa-02) | patches.txt | Cần xác minh; source reference patches.txt. | Cần kiểm |
| QA-03 | Hướng dẫn cài đặt, demo và minh chứng khóa luận | platform | [QUALITY_ACCEPTANCE](../features/platform/QUALITY_ACCEPTANCE.md#feature-qa-03) | ARCHITECTURE.md | Có một phần; source reference ARCHITECTURE.md. | Cần làm |
| QA-04 | Tổng hợp số đo đạt mục tiêu BA | platform | [QUALITY_ACCEPTANCE](../features/platform/QUALITY_ACCEPTANCE.md#feature-qa-04) | FEATURE_STATUS.md | Cần xác minh; source reference FEATURE_STATUS.md. | Cần kiểm |
| NEW-01 | Tạo bản sửa từ báo giá đã gửi | sales | [QUOTATION](../features/sales/QUOTATION.md#feature-new-01) | doublet_quotation.py | Đề xuất; source reference doublet_quotation.py. | Đề xuất |
| NEW-02 | Nhắc follow-up Deal và báo giá sắp hết hạn | automation | [FOLLOW_UP](../features/automation/FOLLOW_UP.md#feature-new-02) | dashboard.py | Đề xuất; source reference dashboard.py. | Đề xuất |
| NEW-03 | Hàng chờ gắn hội thoại chưa rõ khách | contact-center | [INBOX](../features/contact-center/INBOX.md#feature-new-03) | api.py | Đề xuất; source reference api.py. | Đề xuất |
| EXT-01 | Một Contact đại diện nhiều Company | crm | [CUSTOMER](../features/crm/CUSTOMER.md#feature-ext-01) | doublet_contact.json | Có một phần; source reference doublet_contact.json. | Cần làm |
| EXT-02 | Vai trò người liên hệ trong Deal | crm | [CUSTOMER](../features/crm/CUSTOMER.md#feature-ext-02) | doublet_deal.json | Chưa thấy; source reference doublet_deal.json. | Đề xuất |
| EXT-03 | Đánh dấu khách quay lại | crm | [CUSTOMER](../features/crm/CUSTOMER.md#feature-ext-03) | doublet_lead.py | Chưa thấy; source reference doublet_lead.py. | Đề xuất |
| EXT-04 | Gộp hồ sơ trùng có người duyệt | crm | [IDENTITY_DUPLICATES](../features/crm/IDENTITY_DUPLICATES.md#feature-ext-04) | DoubleTContactDataPanel.vue | Chưa thấy; source reference DoubleTContactDataPanel.vue. | Đề xuất |
| EXT-27 | Quyền theo người phụ trách và nhóm | crm | [PERMISSIONS](../features/crm/PERMISSIONS.md#feature-ext-27) | doublet_deal.json | Cần xác minh; source reference doublet_deal.json. | Cần kiểm |
| EXT-16 | Điều kiện bắt buộc khi chuyển stage | crm | [ADVANCED_CRM](../features/crm/ADVANCED_CRM.md#feature-ext-16) | doublet_deal.py | Có một phần; source reference doublet_deal.py. | Đề xuất |
| EXT-05 | Gắn sản phẩm quan tâm ngay trên Deal | sales | [QUOTATION](../features/sales/QUOTATION.md#feature-ext-05) | sales_completion.py · Deal Products | Có; source reference sales_completion.py · Deal Products. | Cần kiểm |
| EXT-06 | Tạo báo giá từ Lead đã Qualified | sales | [QUOTATION](../features/sales/QUOTATION.md#feature-ext-06) | FrappeLead.vue · Create Quotation | Có; source reference FrappeLead.vue · Create Quotation. | Cần kiểm |
| EXT-07 | Hiển thị và lọc báo giá hết hạn | sales | [QUOTATION](../features/sales/QUOTATION.md#feature-ext-07) | doublet_quotation.json | Có; source reference doublet_quotation.json. | Cần kiểm |
| EXT-10 | Bộ lọc Task theo ngày đến hạn | activities | [TASKS](../features/activities/TASKS.md#feature-ext-10) | Tasks.vue | Có; source reference Tasks.vue. | Cần kiểm |
| EXT-11 | Lịch hẹn và cuộc gặp gắn hồ sơ | activities | [APPOINTMENTS_REMINDERS](../features/activities/APPOINTMENTS_REMINDERS.md#feature-ext-11) | doublet_task.json | Appointment/reminder source có; mapping checklist cũ; acceptance pending. | Cần kiểm |
| EXT-34 | Bộ đếm Task quá hạn trên thẻ Deal | activities | [TASKS](../features/activities/TASKS.md#feature-ext-34) | DoubleTDealKanban.vue | Chưa thấy; source reference DoubleTDealKanban.vue. | Đề xuất |
| EXT-13 | Giá trị Deal Won theo kỳ (nguồn cho Sales Reports) | analytics | [SALES_PERFORMANCE](../features/analytics/SALES_PERFORMANCE.md#feature-ext-13) | doublet_crm/reports.py · SalesPerformanceReport.vue · test_reports.py | Có; source reference doublet_crm/reports.py · SalesPerformanceReport.vue · test_reports.py. | Đã xong |
| EXT-32 | Lost Reason Analytics: lý do mất Deal | analytics | [PIPELINE_ANALYTICS](../features/analytics/PIPELINE_ANALYTICS.md#feature-ext-32) | doublet_crm/reports.py · PipelineAnalyticsReport.vue · test_reports.py | Có; source reference doublet_crm/reports.py · PipelineAnalyticsReport.vue · test_reports.py. | Đã xong |
| EXT-24 | Nhận Lead từ form website | integration | [EXTERNAL_CHANNELS](../features/integration/EXTERNAL_CHANNELS.md#feature-ext-24) | hooks.py | Chưa thấy; source reference hooks.py. | Đề xuất |
| EXT-25 | Lưu bộ lọc dùng lại trên Lead và Deal | platform | [VIEWS_IMPORT_CUSTOM_FIELDS](../features/platform/VIEWS_IMPORT_CUSTOM_FIELDS.md#feature-ext-25) | ViewControls.vue | Có một phần; source reference ViewControls.vue. | Đề xuất |
| EXT-26 | Nhập Lead/Contact và xuất danh sách đã lọc | platform | [VIEWS_IMPORT_CUSTOM_FIELDS](../features/platform/VIEWS_IMPORT_CUSTOM_FIELDS.md#feature-ext-26) | ViewControls.vue | Cần xác minh; source reference ViewControls.vue. | Cần kiểm |
| EXT-31 | Lịch sử báo giá trên hồ sơ khách | crm | [CUSTOMER](../features/crm/CUSTOMER.md#feature-ext-31) | DealQuotations.vue | Có một phần; source reference DealQuotations.vue. | Cần làm |
| EXT-19 | Conversation/Message dùng chung và OA adapter | contact-center | [INBOX](../features/contact-center/INBOX.md#feature-ext-19) | zalo_inbox.py:364 | Có một phần; source reference zalo_inbox.py:364. | Cần làm |
| EXT-20 | Phân công và bàn giao hội thoại OA | contact-center | [INBOX](../features/contact-center/INBOX.md#feature-ext-20) | api.py | Source baseline mới hơn checklist; implementation lifecycle/assignment có, acceptance pending. | Đề xuất |
| EXT-21 | Đo thời gian phản hồi đầu tiên của OA | contact-center | [INBOX](../features/contact-center/INBOX.md#feature-ext-21) | dashboard.py | Source baseline mới hơn checklist; customer linking có, acceptance pending. | Đề xuất |
| EXT-22 | Mẫu email bán hàng dùng lại | contact-center | [EMAIL](../features/contact-center/EMAIL.md#feature-ext-22) | QuotationForm.vue | Chưa thấy; source reference QuotationForm.vue. | Đề xuất |
| EXT-14 | Funnel theo nhóm Lead cùng kỳ | analytics | [CUSTOMER_JOURNEY](../features/analytics/CUSTOMER_JOURNEY.md#feature-ext-14) | reports.py · CustomerJourneyReport.vue · test_reports.py | Có; source reference reports.py · CustomerJourneyReport.vue · test_reports.py. | Cần kiểm |
| EXT-15 | Dự báo doanh thu theo ngày dự kiến chốt | analytics | [PIPELINE_ANALYTICS](../features/analytics/PIPELINE_ANALYTICS.md#feature-ext-15) | reports.py · PipelineAnalyticsReport.vue · report_tools.py · test_reports.py | Source baseline có Stage Aging; acceptance pending. | Cần kiểm |
| EXT-33 | Deal đứng lâu ở một stage | analytics | [PIPELINE_ANALYTICS](../features/analytics/PIPELINE_ANALYTICS.md#feature-ext-33) | stage_aging.py · reports.py · smart_insights.py · PipelineAnalyticsReport.vue | Source baseline có Deal Health/analytics; acceptance pending. | Cần kiểm |
| EXT-23 | Tự gán Lead theo nguồn hoặc nhóm | automation | [LEAD_ASSIGNMENT_SCORING](../features/automation/LEAD_ASSIGNMENT_SCORING.md#feature-ext-23) | api.py | Có một phần; source reference api.py. | Đề xuất |
| EXT-29 | Tạo hoạt động khi Deal vào stage | automation | [DEAL_AUTOMATION](../features/automation/DEAL_AUTOMATION.md#feature-ext-29) | hooks.py | Chưa thấy; source reference hooks.py. | Đề xuất |
| EXT-28 | Admin thêm trường nghiệp vụ ngoài core | platform | [VIEWS_IMPORT_CUSTOM_FIELDS](../features/platform/VIEWS_IMPORT_CUSTOM_FIELDS.md#feature-ext-28) | FrappeLead.vue | Cần xác minh; source reference FrappeLead.vue. | Cần kiểm |
| EXT-08 | Mẫu báo giá theo nhóm sản phẩm/dịch vụ | sales | [QUOTATION](../features/sales/QUOTATION.md#feature-ext-08) | quotation_pdf.py | Có; source reference quotation_pdf.py. | Cần kiểm |
| EXT-09 | Duyệt chiết khấu vượt ngưỡng | sales | [QUOTATION](../features/sales/QUOTATION.md#feature-ext-09) | doublet_quotation.py | Có; source reference doublet_quotation.py. | Cần kiểm |
| EXT-12 | Hàng đợi việc cần xử lý cho Sales | activities | [TASKS](../features/activities/TASKS.md#feature-ext-12) | Tasks.vue | Có một phần; source reference Tasks.vue. | Đề xuất |
| EXT-17 | Playbook bán hàng theo từng stage | crm | [ADVANCED_CRM](../features/crm/ADVANCED_CRM.md#feature-ext-17) | DealDetailView.vue | Chưa thấy; source reference DealDetailView.vue. | Đề xuất |
| EXT-18 | Nhiều pipeline theo loại hình bán | crm | [ADVANCED_CRM](../features/crm/ADVANCED_CRM.md#feature-ext-18) | doublet_deal_stage.json | Chưa thấy; source reference doublet_deal_stage.json. | Đề xuất |
| EXT-30 | Tạo Deal định kỳ cho khách gia hạn | crm | [ADVANCED_CRM](../features/crm/ADVANCED_CRM.md#feature-ext-30) | hooks.py | Chưa thấy; source reference hooks.py. | Đề xuất |
| CC-01 | Lượt 2 · Kênh Email trong Inbox của Contact Center | contact-center | [EMAIL](../features/contact-center/EMAIL.md#feature-cc-01) | router.js | Chưa thấy; source reference router.js. | Cần làm |
| CC-02 | Trạng thái xử lý hội thoại | contact-center | [INBOX](../features/contact-center/INBOX.md#feature-cc-02) | api.py | Source baseline mới hơn checklist; state/actions có, acceptance pending. | Cần làm |
| CC-03 | Phân quyền hàng đợi và cấu hình kênh | contact-center | [INBOX](../features/contact-center/INBOX.md#feature-cc-03) | api.py | Source baseline mới hơn checklist; audit/idempotency có, acceptance pending. | Cần làm |
| CC-04 | v | contact-center | [INBOX](../features/contact-center/INBOX.md#feature-cc-04) | api.py | Tên checklist là `v`; diễn giải từ hiện trạng/AC, không sửa Sheet. | Đề xuất |
| CC-05 | Giờ làm việc và trả lời ngoài giờ | contact-center | [INBOX](../features/contact-center/INBOX.md#feature-cc-05) | api.py | Đề xuất; source reference api.py. | Đề xuất |
| CC-06 | Mẫu trả lời nhanh trong Inbox | contact-center | [INBOX](../features/contact-center/INBOX.md#feature-cc-06) | router.js | Đề xuất; source reference router.js. | Đề xuất |
| CC-07 | Cảnh báo hội thoại chờ quá lâu | contact-center | [INBOX](../features/contact-center/INBOX.md#feature-cc-07) | dashboard.py | Đề xuất; source reference dashboard.py. | Đề xuất |
| CC-08 | Đánh giá hỗ trợ sau khi đóng hội thoại | contact-center | [INBOX](../features/contact-center/INBOX.md#feature-cc-08) | dashboard.py | Đề xuất; source reference dashboard.py. | Đề xuất |
| CC-09 | Tích hợp tổng đài thật qua SIP/PBX | contact-center | [CALLS](../features/contact-center/CALLS.md#feature-cc-09) | router.js | Cần chốt; source reference router.js. | Cần chốt |
| CC-10 | Tạo việc gọi lại từ cuộc gọi nhỡ | contact-center | [CALLS](../features/contact-center/CALLS.md#feature-cc-10) | api.py | Có; source reference api.py. | Cần kiểm |
| CRM-10 | Hoàn thiện danh sách và chi tiết Company | crm | [CUSTOMER](../features/crm/CUSTOMER.md#feature-crm-10) | useDoubleTCompanies.js:75 | Có; source reference useDoubleTCompanies.js:75. | Cần kiểm |
| CALL-01 | Call Logs, thống kê và phân trang | contact-center | [CALLS](../features/contact-center/CALLS.md#feature-call-01) | api.py:790, 820 | Có; source reference api.py:790, 820. | Cần kiểm |
| CALL-02 | Xác minh AI Summary cho Call Logs | contact-center | [CALLS](../features/contact-center/CALLS.md#feature-call-02) | CallLogs.vue:366 | Có; source reference CallLogs.vue:366. | Cần kiểm |
| REP-04 | Reports Hub: 6 nhóm báo cáo chuyên sâu, không trùng Dashboard | analytics | [REPORT_PLATFORM](../features/analytics/REPORT_PLATFORM.md#feature-rep-04) | ReportsPage.vue · ReportsLayout.vue · router.js · components/Reports/ | Có; source reference ReportsPage.vue · ReportsLayout.vue · router.js · components/Reports/. | Cần kiểm |
| REP-05 | Bộ lọc thời gian, nhân viên và so sánh kỳ | analytics | [REPORT_PLATFORM](../features/analytics/REPORT_PLATFORM.md#feature-rep-05) | ReportsFilters.vue · ReportActions.vue · reports.py | Có một phần; source reference ReportsFilters.vue · ReportActions.vue · reports.py. | Cần kiểm |
| REP-06 | Customer Journey: Lead → Deal → Quotation → Order | analytics | [CUSTOMER_JOURNEY](../features/analytics/CUSTOMER_JOURNEY.md#feature-rep-06) | reports.py · CustomerJourneyReport.vue · test_reports.py | Có; source reference reports.py · CustomerJourneyReport.vue · test_reports.py. | Cần kiểm |
| REP-07 | Pipeline Analytics: giá trị, giai đoạn, cơ hội rủi ro | analytics | [PIPELINE_ANALYTICS](../features/analytics/PIPELINE_ANALYTICS.md#feature-rep-07) | reports.py · stage_aging.py · PipelineAnalyticsReport.vue | Có; source reference reports.py · stage_aging.py · PipelineAnalyticsReport.vue. | Cần kiểm |
| REP-08 | Quotation & Order Analytics theo kỳ/nhân viên | analytics | [QUOTATION_ORDER](../features/analytics/QUOTATION_ORDER.md#feature-rep-08) | reports.py · QuotationOrderReport.vue · test_reports.py | Có; source reference reports.py · QuotationOrderReport.vue · test_reports.py. | Cần kiểm |
| REP-09 | Smart Insights: cảnh báo có lý do và thao tác | analytics | [SMART_INSIGHTS](../features/analytics/SMART_INSIGHTS.md#feature-rep-09) | smart_insights.py · SmartInsightsReport.vue · test_smart_insights.py | Có; source reference smart_insights.py · SmartInsightsReport.vue · test_smart_insights.py. | Cần kiểm |
| REP-10 | Deal Health Score: điểm rủi ro cơ hội minh bạch | analytics | [SMART_INSIGHTS](../features/analytics/SMART_INSIGHTS.md#feature-rep-10) | smart_insights.py · SmartInsightsReport.vue · test_smart_insights.py | Có; source reference smart_insights.py · SmartInsightsReport.vue · test_smart_insights.py. | Cần kiểm |
| REP-11 | Biểu đồ trực quan, drill-down và tình trạng dữ liệu rỗng | analytics | [REPORT_PLATFORM](../features/analytics/REPORT_PLATFORM.md#feature-rep-11) | frontend/src/components/Reports/ · ReportsPage.vue · frontend/tests/ | Có; source reference frontend/src/components/Reports/ · ReportsPage.vue · frontend/tests/. | Cần kiểm |
| REP-12 | Xuất báo cáo và lưu bộ lọc cá nhân | analytics | [REPORT_PLATFORM](../features/analytics/REPORT_PLATFORM.md#feature-rep-12) | report_tools.py · ReportActions.vue · test_smart_insights.py | Có; source reference report_tools.py · ReportActions.vue · test_smart_insights.py. | Cần kiểm |
| REP-13 | AI diễn giải báo cáo dựa trên số liệu đã kiểm chứng | analytics | [AI_INSIGHTS](../features/analytics/AI_INSIGHTS.md#feature-rep-13) | smart_insights.py · reports.py (nguồn dự kiến) | Không có source baseline; evidence ngoài main không được tính PASS. | Đang làm |
| REP-14 | Nâng cấp Dashboard cũ thành trung tâm điều hành hằng ngày | analytics | [DASHBOARD](../features/analytics/DASHBOARD.md#feature-rep-14) | dashboard.py · Dashboard.vue · smart_insights.py | Có; source reference dashboard.py · Dashboard.vue · smart_insights.py. | Cần kiểm |

## Coverage self-check

| Chỉ số | Kết quả |
| --- | --- |
| Dòng checklist | 110 |
| ID unique | 110 |
| ID đã ánh xạ | 110 |
| ID thiếu | 0 |
| ID trùng | 0 |
| Coverage | 100% |
| Phân bố đánh giá checklist | Có 52; Có một phần 21; Cần xác minh 7; Chưa thấy 20; Đề xuất 7; Cần chốt 2; Bản cũ/ngoài repo 1 |
| Phân bố acceptance checklist | Cần kiểm 61; Cần làm 17; Chờ phụ thuộc 2; Cần chốt 3; Đề xuất 24; Đã xong 2; Đang làm 1 |

## Khác biệt checklist và source baseline

- `EXT-20`, `EXT-21`, `CC-02`, `CC-03`: checklist chưa phản ánh PR #36; source có assignment/transfer, lifecycle, record permission, audit Event và response metrics. Chưa có migration/browser/role evidence baseline.
- `EXT-11`: checklist trỏ Task, nhưng baseline có DocType/controller/page Appointment và reminder scheduler riêng.
- `EXT-15`, `EXT-33`: baseline có probability/stage-entry source sau PR #35; acceptance vẫn pending.
- `REP-13`: “Đang làm” dựa worktree ngoài main; baseline không có AI Business Insights foundation.
- `CRM-08`: còn inherited `crm.*`, `crm.fcrm.*`, WhatsApp/ViewControls/telephony và optional ERPNext paths; clean install chưa chứng minh.
- `CC-04`: tên checklist là `v`; tài liệu giữ ID và diễn giải từ hiện trạng/AC, không sửa Google Sheet.
