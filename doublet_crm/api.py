import frappe
from frappe import _
from frappe.utils import now


@frappe.whitelist()
def update_deal_stage(deal_name, stage, lost_reason=None):
    if not frappe.db.exists("DoubleT Deal", deal_name):
        frappe.throw(_("Deal does not exist"))

    if not frappe.db.exists("DoubleT Deal Stage", stage):
        frappe.throw(_("Deal Stage does not exist"))

    deal = frappe.get_doc("DoubleT Deal", deal_name)

    # vẫn kiểm tra quyền Write
    deal.check_permission("write")

    target_type = (
        frappe.db.get_value(
            "DoubleT Deal Stage",
            stage,
            "stage_type",
        )
        or ""
    ).upper()

    current_type = ""

    if deal.stage:
        current_type = (
            frappe.db.get_value(
                "DoubleT Deal Stage",
                deal.stage,
                "stage_type",
            )
            or ""
        ).upper()

    values = {
        "stage": stage,
    }

    if target_type == "LOST":
        reason = (lost_reason or "").strip()

        if not reason:
            frappe.throw(
                _("Lost Reason is required")
            )

        values.update({
            "lost_reason": reason,
            "lost_on": now(),
            "won_on": None,
        })

    elif target_type == "WON":
        values.update({
            "won_on": now(),
            "lost_on": None,
            "lost_reason": None,
        })

    else:
        # chỉ clear terminal state nếu thực sự rời WON/LOST
        if current_type == "WON":
            values["won_on"] = None

        if current_type == "LOST":
            values["lost_on"] = None
            values["lost_reason"] = None

    frappe.db.set_value(
        "DoubleT Deal",
        deal_name,
        values,
        update_modified=True,
    )

    return values