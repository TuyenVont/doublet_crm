import json
import frappe


def _save_layout(doctype, layout_type, layout):
    existing = frappe.db.get_value(
        "CRM Fields Layout",
        {"dt": doctype, "type": layout_type},
        "name",
    )

    if existing:
        doc = frappe.get_doc("CRM Fields Layout", existing)
    else:
        doc = frappe.new_doc("CRM Fields Layout")

    doc.dt = doctype
    doc.type = layout_type
    doc.layout = json.dumps(layout)
    doc.save(ignore_permissions=True)

    print(f"Saved: {doctype} / {layout_type}")


def sync_layouts():

    # =====================================================
    # DOUBLET DEAL - DATA TAB
    # =====================================================
    deal_data = [
        {
            "name": "first_tab",
            "sections": [
                {
                    "label": "Deal Information",
                    "name": "deal_information",
                    "opened": True,
                    "columns": [
                        {
                            "name": "deal_column_1",
                            "fields": [
                                "deal_title",
                                "deal_type",
                                "stage",
                                "amount",
                            ],
                        },
                        {
                            "name": "deal_column_2",
                            "fields": [
                                "deal_owner",
                                "expected_close_date",
                                "contact",
                                "company",
                                "source_lead",
                            ],
                        },
                    ],
                },
                {
                    "label": "Outcome",
                    "name": "deal_outcome",
                    "opened": True,
                    "columns": [
                        {
                            "name": "deal_outcome_1",
                            "fields": [
                                "won_on",
                                "lost_on",
                            ],
                        },
                        {
                            "name": "deal_outcome_2",
                            "fields": [
                                "lost_reason",
                            ],
                        },
                    ],
                },
            ],
        }
    ]

    # =====================================================
    # DOUBLET DEAL - RIGHT PANEL
    # =====================================================
    deal_side = [
        {
            "label": "Deal Details",
            "name": "deal_details_section",
            "opened": True,
            "columns": [
                {
                    "name": "deal_details_column",
                    "fields": [
                        "stage",
                        "amount",
                        "expected_close_date",
                        "deal_owner",
                        "deal_type",
                    ],
                }
            ],
        },
        {
            "label": "Related",
            "name": "related_section",
            "opened": True,
            "columns": [
                {
                    "name": "related_column",
                    "fields": [
                        "contact",
                        "company",
                        "source_lead",
                    ],
                }
            ],
        },
    ]

    # =====================================================
    # DOUBLET LEAD - DATA TAB
    # =====================================================
    lead_data = [
        {
            "name": "first_tab",
            "sections": [
                {
                    "label": "Lead Information",
                    "name": "lead_information",
                    "opened": True,
                    "columns": [
                        {
                            "name": "lead_column_1",
                            "fields": [
                                "first_name",
                                "last_name",
                                "company_name",
                                "source",
                                "status",
                            ],
                        },
                        {
                            "name": "lead_column_2",
                            "fields": [
                                "email",
                                "phone",
                                "lead_owner",
                                "notes",
                            ],
                        },
                    ],
                },
                {
                    "label": "Conversion",
                    "name": "lead_conversion",
                    "opened": True,
                    "columns": [
                        {
                            "name": "conversion_column_1",
                            "fields": [
                                "converted_on",
                                "converted_contact",
                            ],
                        },
                        {
                            "name": "conversion_column_2",
                            "fields": [
                                "converted_company",
                                "converted_deal",
                            ],
                        },
                    ],
                },
            ],
        }
    ]

    # =====================================================
    # DOUBLET LEAD - RIGHT PANEL
    # =====================================================
    lead_side = [
        {
            "label": "Lead Details",
            "name": "lead_details_section",
            "opened": True,
            "columns": [
                {
                    "name": "lead_details_column",
                    "fields": [
                        "company_name",
                        "source",
                        "status",
                        "lead_owner",
                    ],
                }
            ],
        },
        {
            "label": "Contact",
            "name": "lead_contact_section",
            "opened": True,
            "columns": [
                {
                    "name": "lead_contact_column",
                    "fields": [
                        "first_name",
                        "last_name",
                        "email",
                        "phone",
                    ],
                }
            ],
        },
    ]

    _save_layout("DoubleT Deal", "Data Fields", deal_data)
    _save_layout("DoubleT Deal", "Side Panel", deal_side)

    _save_layout("DoubleT Lead", "Data Fields", lead_data)
    _save_layout("DoubleT Lead", "Side Panel", lead_side)

    frappe.db.commit()

    print("DoubleT CRM layouts synced successfully")
