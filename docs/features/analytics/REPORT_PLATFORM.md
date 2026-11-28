# Report Platform, Export & Saved Filters

[← analytics index](README.md) · [Documentation Index](../../INDEX.md) · [Feature Status](../../tracking/FEATURE_STATUS.md)

## Feature IDs

<a id="feature-rep-04"></a>
- `REP-04` — Reports Hub: 6 nhóm báo cáo chuyên sâu, không trùng Dashboard
<a id="feature-rep-05"></a>
- `REP-05` — Bộ lọc thời gian, nhân viên và so sánh kỳ
<a id="feature-rep-11"></a>
- `REP-11` — Biểu đồ trực quan, drill-down và tình trạng dữ liệu rỗng
<a id="feature-rep-12"></a>
- `REP-12` — Xuất báo cáo và lưu bộ lọc cá nhân

## Mục đích nghiệp vụ

Reports Hub: 6 nhóm báo cáo chuyên sâu, không trùng Dashboard; Bộ lọc thời gian, nhân viên và so sánh kỳ; Biểu đồ trực quan, drill-down và tình trạng dữ liệu rỗng; Xuất báo cáo và lưu bộ lọc cá nhân. Mục này được quản lý cùng nhau vì dùng chung entity, lifecycle hoặc integration boundary.

## Chức năng chi tiết

| ID | Tính năng/việc | Hạng mục | Ưu tiên | Căn cứ và hiện trạng | Nguồn yêu cầu |
| --- | --- | --- | --- | --- | --- |
| REP-04 | Reports Hub: 6 nhóm báo cáo chuyên sâu, không trùng Dashboard | R1 · Reports | P0 | 25/11 · PR #33 đã merge main 319ee10 (feature 5980359). Reports Hub có 6 nhóm live: Sales Performance, Pipeline, Customer Journey, Quotation & Order, Activity & Contact Center, Smart Insights. KeepAlive và vùng cuộn ổn định hơn; Dashboard độc lập. | Chốt thiết kế 22/11 · REP-01/REP-14 · Tham khảo Odoo, HubSpot, Salesforce, Bitrix24 |
| REP-05 | Bộ lọc thời gian, nhân viên và so sánh kỳ | R1 · Reports | P0 | 25/11 · PR #33 đã merge main 319ee10 (feature 5980359). Bộ lọc chung kỳ/owner, compare ở báo cáo hỗ trợ, bổ sung lọc kênh/nguồn và saved filters. Team chưa có schema; Activity không compare. | Đề xuất 22/11 · Odoo filter · REP-02 |
| REP-11 | Biểu đồ trực quan, drill-down và tình trạng dữ liệu rỗng | R1 · Reports | P0 | 25/11 · PR #33 đã merge main 319ee10 (feature 5980359). 6 báo cáo có KPI/biểu đồ/bảng và drill-down; Journey mở rộng hồ sơ, forecast và aging có bảng chi tiết. KeepAlive giảm giật khi quay lại tab. | Đề xuất 22/11 · Phản biện ảnh Odoo · UX Reports |
| REP-12 | Xuất báo cáo và lưu bộ lọc cá nhân | R2 · Reports nâng cao | P2 | 25/11 · PR #33 đã merge main 319ee10 (feature 5980359). CSV UTF-8 BOM, chống formula injection, chạy lại theo applied filters; kiểm quyền nguồn/trường/liên kết. Saved filters cá nhân theo report; có forecast/aging export. | Đề xuất 22/11 · Odoo/HubSpot · EXT-26 |

## Data Model

Permission-scoped query trên Deal, Order, Quotation, Activity, Conversation và Call; không tạo nguồn KPI song song.

Xem [Data Model](../../architecture/DATA_MODEL.md) và [Data Ownership](../../architecture/DATA_OWNERSHIP.md).

## Business Rules

**Tài liệu quản lý chính cho nhóm quy tắc này:** file hiện tại.

Booked Sales = Confirmed/Completed Order theo order_date; Won Deal Value = Deal.amount theo won_on; paid revenue chưa có source. Cohort/denominator/link chain phải nêu rõ. Forecast giữ unknown khác 0. Health Score là risk score, không phải probability. Aggregate/export/drill-down dùng cùng authorized set.

## Workflow và State Transitions

Filter/cohort → authorized query → aggregate/chart/table → export/drill-down trên cùng dataset.

Drill-down route và follow-up action tuân theo [BF-09](../../architecture/BUSINESS_FLOW_CONTRACT.md#bf-09--reportsmart-insight--source-or-follow-up-task): route mang exact source ID, backend query quyết định population được phép và restricted/unknown không được thay bằng zero.

Chi tiết end-to-end nằm ở mục Related Workflows; state không được suy ra từ nhãn UI nếu controller/schema quy định khác.

## Permissions

Aggregate, export và drill-down phải cùng record scope; unknown không được ép thành 0.

Contract chung: [Permission Model](../../architecture/PERMISSION_MODEL.md).

## Source Mapping

| ID | Source reference | Bằng chứng mới trong checklist |
| --- | --- | --- |
| REP-04 | ReportsPage.vue · ReportsLayout.vue · router.js · components/Reports/ | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. 6 Reports giữ nguyên sau tích hợp. |
| REP-05 | ReportsFilters.vue · ReportActions.vue · reports.py | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. Giữ giới hạn Team/Activity compare và Email/Zalo attribution. |
| REP-11 | frontend/src/components/Reports/ · ReportsPage.vue · frontend/tests/ | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. Cải tiến UI và pagination; màn hẹp cần kiểm. |
| REP-12 | report_tools.py · ReportActions.vue · test_smart_insights.py | 27/11 · PR #35 → main b7b6a5d; tích hợp 94c5a25, fix controller cbf0dc6. Frontend test/build PASS theo user; migrate PASS theo log; backend 197/197 trước tích hợp (Codex báo), chưa chạy lại sau tích hợp; UI user báo xong, chưa có log từng role. Forecast CSV và saved filters; kiểm thực tế. |

## Upstream Dependencies

- Business source of truth và date/filter contract.
- [Permission Model](../../architecture/PERMISSION_MODEL.md)
- [Dashboard](DASHBOARD.md)

## Downstream Impact

- Dashboard, management decision, Smart Insights và follow-up.
- Thay đổi schema/state/permission phải kiểm các consumer trong [Dependency Map](../../architecture/DEPENDENCY_MAP.md).

## Related Workflows

- [WF 09 SMART INSIGHTS FOLLOW UP](../../workflows/WF_09_SMART_INSIGHTS_FOLLOW_UP.md)
- [Report/Insight acceptance](../../testing/CROSS_MODULE_ACCEPTANCE.md#reports-and-smart-insights)

## Implementation Status

| ID | Checklist assessment | Checklist progress | Baseline/source finding |
| --- | --- | --- | --- |
| REP-04 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| REP-05 | Có một phần | Cần kiểm | Checklist: Có một phần; Cần kiểm. Không suy ra runtime PASS. |
| REP-11 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |
| REP-12 | Có | Cần kiểm | Checklist: Có; Cần kiểm. Không suy ra runtime PASS. |

## Acceptance Criteria

1. Backend permission đúng theo role, record và field; không dựa vào frontend gating.
2. Happy path, validation/negative path và duplicate/retry path liên quan có bằng chứng trên exact baseline.
3. Dữ liệu liên kết/snapshot và downstream projection nhất quán.
4. Bằng chứng ghi rõ commit, site, role và loại kiểm tra.

| ID | Tiêu chí riêng theo checklist |
| --- | --- |
| REP-04 | Kiểm 6 route, filter/cache dữ liệu mới, desktop/narrow và 3 role; chấp nhận nháy nhẹ lần đầu, không chặn demo. |
| REP-05 | Kiểm reset/apply, kỳ rỗng, saved filters theo tài khoản; giữ rõ giới hạn Team và Email/Zalo. |
| REP-11 | Kiểm aggregate khớp drill-down, empty/error/retry, màn hẹp và dữ liệu cập nhật khi quay lại tab. |
| REP-12 | Kiểm CSV bằng các role thực tế, trường hạn chế, đối chiếu số liệu; lưu/mở/xóa filter bằng hai tài khoản. |

## Known Limitations

- **REP-04:** Source có nhưng vẫn phải theo acceptance status.
- **REP-05:** 25/11 · PR #33 đã merge main 319ee10 (feature 5980359). Bộ lọc chung kỳ/owner, compare ở báo cáo hỗ trợ, bổ sung lọc kênh/nguồn và saved filters. Team chưa có schema; Activity không compare.
- **REP-11:** Source có nhưng vẫn phải theo acceptance status.
- **REP-12:** Source có nhưng vẫn phải theo acceptance status.

Không tự nâng trạng thái checklist hoặc acceptance khi chưa có bằng chứng tương ứng.
