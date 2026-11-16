import frappe

from doublet_crm.zalo_oa import LEAD_SOURCE


def execute():
    """Seed the source used by Zalo OA Leads."""
    doctype = "DoubleT Lead Source"
    if not frappe.db.exists(doctype, LEAD_SOURCE):
        frappe.get_doc({"doctype": doctype, "source_name": LEAD_SOURCE}).insert()
