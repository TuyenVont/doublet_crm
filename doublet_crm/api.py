import frappe
from frappe import _


@frappe.whitelist()
def get_linked_tasks(doctype: str, docname: str):
    supported_doctypes = {
        "DoubleT Lead",
        "DoubleT Deal",
        "DoubleT Contact",
        "DoubleT Company",
    }
    if doctype not in supported_doctypes:
        frappe.throw(_("Unsupported reference DocType"), frappe.ValidationError)

    if not frappe.db.exists(doctype, docname):
        frappe.throw(_("Document not found"), frappe.DoesNotExistError)
    if not frappe.has_permission(doctype, "read", docname):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    tasks = frappe.get_list(
        "CRM Task",
        filters={"reference_doctype": doctype, "reference_docname": docname},
        fields=[
            "name",
            "title",
            "description",
            "assigned_to",
            "due_date",
            "priority",
            "status",
            "modified",
            "creation",
        ],
    )
    return [[], [], [], tasks, []]


@frappe.whitelist()
def update_deal_stage(deal_name, stage, lost_reason=None):
    if not frappe.db.exists("DoubleT Deal", deal_name):
        frappe.throw(_("Deal does not exist"))

    if not frappe.db.exists("DoubleT Deal Stage", stage):
        frappe.throw(_("Deal Stage does not exist"))

    stage_doc = frappe.get_doc(
        "DoubleT Deal Stage",
        stage,
    )

    if not stage_doc.enabled:
        frappe.throw(
            _("Deal Stage is disabled"),
            frappe.ValidationError,
        )

    deal = frappe.get_doc(
        "DoubleT Deal",
        deal_name,
    )

    deal.check_permission("write")

    target_type = (
        stage_doc.stage_type or ""
    ).upper()

    deal.stage = stage

    if target_type == "LOST":
        reason = (
            lost_reason or ""
        ).strip()

        if not reason:
            frappe.throw(
                _(
                    "Lost Reason is required"
                ),
                frappe.ValidationError,
            )

        deal.lost_reason = reason

    deal.save()

    return {
        "stage": deal.stage,
        "lost_reason": deal.lost_reason,
        "won_on": deal.won_on,
        "lost_on": deal.lost_on,
    }