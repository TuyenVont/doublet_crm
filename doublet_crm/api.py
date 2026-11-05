import frappe
from frappe import _

from doublet_crm.doublet_crm.doctype.doublet_note.doublet_note import ALLOWED_REFERENCES


def _note_reference_label(doctype, docname):
    """Readable reference name for centralized Notes; keep docname as the link ID."""
    record = frappe.get_doc(doctype, docname)
    if doctype in ("DoubleT Lead", "DoubleT Contact"):
        label = record.get("full_name") or " ".join(
            part.strip()
            for part in (record.get("first_name"), record.get("last_name"))
            if isinstance(part, str) and part.strip()
        )
    elif doctype == "DoubleT Deal":
        label = record.get("deal_title")
    elif doctype == "DoubleT Company":
        label = record.get("company_name")
    else:
        label = None
    return str(label or record.get_title() or docname).strip()


@frappe.whitelist()
def get_notes(search: str | None = None, reference_doctype: str | None = None):
    frappe.has_permission("DoubleT Note", "read", throw=True)
    if reference_doctype and reference_doctype not in ALLOWED_REFERENCES:
        frappe.throw(_("Unsupported reference DocType"), frappe.ValidationError)

    filters = {"reference_doctype": reference_doctype} if reference_doctype else {}
    term = (search or "").strip()
    or_filters = None
    if term:
        pattern = f"%{term}%"
        or_filters = {
            "title": ["like", pattern],
            "content": ["like", pattern],
            "reference_name": ["like", pattern],
        }

    notes = frappe.get_list(
        "DoubleT Note",
        filters=filters,
        or_filters=or_filters,
        fields=[
            "name",
            "title",
            "content",
            "reference_doctype",
            "reference_name",
            "owner",
            "modified",
            "creation",
        ],
        order_by="modified desc",
        limit_page_length=500,
    )
    visible_notes = []
    reference_labels = {}
    for note in notes:
        if not (
            frappe.db.exists(note.reference_doctype, note.reference_name)
            and frappe.has_permission(note.reference_doctype, "read", note.reference_name)
        ):
            continue
        reference = (note.reference_doctype, note.reference_name)
        if reference not in reference_labels:
            reference_labels[reference] = _note_reference_label(*reference)
        note["reference_label"] = reference_labels[reference]
        visible_notes.append(note)
    return visible_notes


@frappe.whitelist()
def get_linked_notes(doctype: str, docname: str):
    if doctype not in ALLOWED_REFERENCES:
        frappe.throw(_("Unsupported reference DocType"), frappe.ValidationError)

    if not frappe.db.exists(doctype, docname):
        frappe.throw(_("Document not found"), frappe.DoesNotExistError)
    if not frappe.has_permission(doctype, "read", docname):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    return frappe.get_list(
        "DoubleT Note",
        filters={"reference_doctype": doctype, "reference_name": docname},
        fields=[
            "name",
            "title",
            "content",
            "reference_doctype",
            "reference_name",
            "owner",
            "modified",
            "creation",
        ],
        order_by="modified desc",
    )


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
        "DoubleT Task",
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
