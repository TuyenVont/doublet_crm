# Data Model & Entity Relationships

[← Documentation Index](../INDEX.md) · [Data Ownership](DATA_OWNERSHIP.md) · [Permission Model](PERMISSION_MODEL.md)

## 6.1 ERD hiện trạng

```mermaid
erDiagram
  DOUBLET_LEAD_SOURCE ||--o{ DOUBLET_LEAD : source
  DOUBLET_LEAD ||--o| DOUBLET_CONTACT : converted_contact
  DOUBLET_LEAD ||--o| DOUBLET_COMPANY : converted_company
  DOUBLET_LEAD ||--o| DOUBLET_DEAL : converted_deal
  DOUBLET_CONTACT }o--o| DOUBLET_COMPANY : company
  DOUBLET_DEAL_STAGE ||--o{ DOUBLET_DEAL : stage
  DOUBLET_LEAD ||--o{ DOUBLET_DEAL : source_lead
  DOUBLET_CONTACT ||--o{ DOUBLET_DEAL : contact
  DOUBLET_COMPANY ||--o{ DOUBLET_DEAL : company
  DOUBLET_DEAL ||--o{ DOUBLET_DEAL_PRODUCT : interested_products
  DOUBLET_PRODUCT ||--o{ DOUBLET_DEAL_PRODUCT : product

  DOUBLET_PRODUCT_CATEGORY ||--o{ DOUBLET_PRODUCT_CATEGORY_ASSIGNMENT : category
  DOUBLET_PRODUCT ||--o{ DOUBLET_PRODUCT_CATEGORY_ASSIGNMENT : categories
  DOUBLET_PRODUCT ||--o{ DOUBLET_PRODUCT : variant_of
  DOUBLET_PRODUCT ||--o{ DOUBLET_PRODUCT_VARIANT_ATTRIBUTE : variant_attributes
  DOUBLET_PRICE_LIST ||--o{ DOUBLET_PRICE_LIST_ITEM : items
  DOUBLET_PRODUCT ||--o{ DOUBLET_PRICE_LIST_ITEM : product
  DOUBLET_PRICE_LIST ||--o{ DOUBLET_CONTACT : price_list
  DOUBLET_PRICE_LIST ||--o{ DOUBLET_COMPANY : price_list

  DOUBLET_DEAL ||--o{ DOUBLET_QUOTATION : deal
  DOUBLET_QUOTATION ||--|{ DOUBLET_QUOTATION_ITEM : items
  DOUBLET_PRODUCT ||--o{ DOUBLET_QUOTATION_ITEM : product
  DOUBLET_QUOTATION_TEMPLATE ||--|{ DOUBLET_QUOTATION_TEMPLATE_ITEM : items
  DOUBLET_PRODUCT ||--o{ DOUBLET_QUOTATION_TEMPLATE_ITEM : product
  DOUBLET_QUOTATION ||--o| DOUBLET_ORDER : quotation_unique
  DOUBLET_ORDER ||--|{ DOUBLET_ORDER_ITEM : items
  DOUBLET_PRODUCT ||--o{ DOUBLET_ORDER_ITEM : product

  DOUBLET_CONVERSATION ||--o{ DOUBLET_MESSAGE : conversation
  DOUBLET_CONVERSATION ||--o{ DOUBLET_CONVERSATION_EVENT : audit
  DOUBLET_LEAD ||--o{ DOUBLET_CONVERSATION : lead
  DOUBLET_CONTACT ||--o{ DOUBLET_CONVERSATION : contact
  DOUBLET_CALL_LOG ||--o{ DOUBLET_CALL_EVENT : audit
  DOUBLET_CALL_LOG ||--o| DOUBLET_CALL_AI_SUMMARY : unique_summary
  DOUBLET_CALL_LOG ||--o| DOUBLET_TASK : unique_callback
  DOUBLET_CALL_LOG ||--o| DOUBLET_NOTE : unique_next_steps
```

## 6.2 Dynamic Link và Frappe records

`DoubleT Task.reference_docname`, `DoubleT Appointment.reference_docname`, `DoubleT Note.reference_name` và `DoubleT Call Log.reference_name` là Dynamic Link; controller giới hạn Task/Appointment/Note vào bốn entity Lead/Deal/Contact/Company. Call Log schema dùng `Link DocType` và phải được API validate. `Communication`, `File`, `Comment`, `Version` và `Notification Log` là Frappe DocType dùng dynamic reference/attachment, không phải child table của business record.

## 6.3 Unique và snapshot

- `Product.sku`, `Product.variant_key`, `Deal Stage.stage_name`, `Lead Source.source_name`, `Price List.price_list_name`, `Quotation Template.template_name` unique.
- `Order.quotation` unique; `Call AI Summary.call_log`, `Task.callback_call_log`, `Note.source_call_log` unique.
- `Call Log.external_call_id` unique; inbound Zalo dùng deterministic external key theo source/OA/user/message.
- Quotation/Order item lưu `product_name`, `sku`, price, quantity, discount và computed total như snapshot; Product/Price List thay đổi không được reprice lịch sử đã lưu.
- Contact hiện chỉ có một `company`; quan hệ nhiều Company là target `EXT-01`, không có trong ERD hiện trạng.
