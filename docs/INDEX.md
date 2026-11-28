# DoubleT CRM Documentation Index

Tài liệu này là entry point cho đặc tả DoubleT CRM tại baseline `c087d806e16d26701f6a1597bd82ae3ab6a55319`. Với task hẹp, chỉ đọc feature file và dependency/workflow được liên kết; không cần đọc toàn bộ tài liệu.

## Kiến trúc và dữ liệu

- [Tổng quan và phạm vi](architecture/SYSTEM_OVERVIEW.md)
- [Kiến trúc hệ thống và API contracts](architecture/SYSTEM_ARCHITECTURE.md)
- [Ranh giới module](architecture/MODULE_BOUNDARIES.md)
- [Data Model / ERD](architecture/DATA_MODEL.md)
- [Single Source of Truth](architecture/DATA_OWNERSHIP.md)
- [Permission Model](architecture/PERMISSION_MODEL.md)
- [Cross-module Dependency Map](architecture/DEPENDENCY_MAP.md)

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

- [10 end-to-end workflows](workflows/README.md)
- [Testing & Acceptance](testing/README.md)
- [Deployment & Migration](deployment/README.md)

## Theo dõi

- [Feature Index — 110/110 checklist IDs](tracking/FEATURE_INDEX.md)
- [Feature Status & Evidence](tracking/FEATURE_STATUS.md)
- [Known Gaps](tracking/KNOWN_GAPS.md)
- [Current Task](CURRENT_TASK.md)

## Quy ước trạng thái

- **Source verified:** đã đối chiếu schema/controller/API/UI tại baseline; không đồng nghĩa runtime PASS.
- **Partial:** mới có một phần contract hoặc workflow.
- **Target / Not implemented:** không mô tả như đang vận hành.
- **Acceptance pending:** thiếu test/build/migration/browser/role/live evidence trên exact baseline.
