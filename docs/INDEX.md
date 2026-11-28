# DoubleT CRM Documentation Index

Tài liệu này là entry point cho đặc tả DoubleT CRM tại baseline `a7534e74090f46498f5cbfcd30e0fcf77d882f2e` (PR #38, ngày 28/11/2026). Với task hẹp, chỉ đọc feature file và dependency/workflow được liên kết; không cần đọc toàn bộ tài liệu.

## Kiến trúc và dữ liệu

- [Tổng quan và phạm vi](architecture/SYSTEM_OVERVIEW.md)
- [Kiến trúc hệ thống và API contracts](architecture/SYSTEM_ARCHITECTURE.md)
- [Ranh giới module](architecture/MODULE_BOUNDARIES.md)
- [Data Model / ERD](architecture/DATA_MODEL.md)
- [Single Source of Truth](architecture/DATA_OWNERSHIP.md)
- [Permission Model](architecture/PERMISSION_MODEL.md)
- [Cross-module Dependency Map](architecture/DEPENDENCY_MAP.md)
- [End-to-End Business Flow Contract](architecture/BUSINESS_FLOW_CONTRACT.md)

## Feature specifications

- [CRM](features/crm/README.md)
- [Sales](features/sales/README.md)
- [Activities](features/activities/README.md)
- [Contact Center](features/contact-center/README.md)
- [Analytics](features/analytics/README.md)
- [Integration](features/integration/README.md)
- [Automation](features/automation/README.md)
- [Platform](features/platform/README.md)

## Luồng, kiểm thử và vận hành

- [11 end-to-end workflows](workflows/README.md)
- [Testing & Acceptance](testing/README.md)
- [Cross-module Acceptance Scenarios](testing/CROSS_MODULE_ACCEPTANCE.md)
- [Deployment & Migration](deployment/README.md)

## Theo dõi

- [Feature Index — 110/110 checklist IDs](tracking/FEATURE_INDEX.md)
- [Feature Status & Evidence](tracking/FEATURE_STATUS.md)
- [Known Gaps](tracking/KNOWN_GAPS.md)
- [Cross-module Workflow Gaps](tracking/WORKFLOW_GAPS.md)
- [Current Task](CURRENT_TASK.md)

## Quy ước trạng thái

- **Source verified:** đã đối chiếu schema/controller/API/UI tại baseline; không đồng nghĩa runtime PASS.
- **Partial:** mới có một phần contract hoặc workflow.
- **Target / Not implemented:** không mô tả như đang vận hành.
- **Acceptance pending:** thiếu test/build/migration/browser/role/live evidence trên exact baseline.
