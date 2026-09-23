import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, cstr, now_datetime


class DoubleTLead(Document):
	pass


@frappe.whitelist(methods=["POST"])
def convert_lead(lead_name, create_company=0, company_name=None, create_deal=0, deal_title=None, stage=None, amount=0):
	"""Create conversion records and update the lead in a single transaction."""
	create_company = cint(create_company)
	create_deal = cint(create_deal)
	company_name = cstr(company_name).strip()
	deal_title = cstr(deal_title).strip()
	stage = cstr(stage).strip()

	# Lock the lead so two requests cannot both pass the conversion check.
	frappe.db.get_value("DoubleT Lead", lead_name, "name", for_update=True)
	lead = frappe.get_doc("DoubleT Lead", lead_name)
	lead.check_permission("write")
	if lead.status == "CONVERTED" or lead.converted_contact:
		frappe.throw(_("This lead has already been converted."), frappe.ValidationError)

	if create_company and not company_name:
		frappe.throw(_("Company Name is required when creating a company."), frappe.ValidationError)
	if create_deal and not deal_title:
		frappe.throw(_("Deal Title is required when creating a deal."), frappe.ValidationError)
	if create_deal and not stage:
		frappe.throw(_("Deal Stage is required when creating a deal."), frappe.ValidationError)

	save_point = f"doublet_lead_conversion_{frappe.generate_hash(length=12)}"
	frappe.db.savepoint(save_point)
	try:
		company = None
		if create_company:
			company = frappe.get_doc({
				"doctype": "DoubleT Company",
				"company_name": company_name,
			}).insert()

		contact = frappe.get_doc({
			"doctype": "DoubleT Contact",
			"first_name": lead.first_name,
			"last_name": lead.last_name,
			"email": lead.email,
			"phone": lead.phone,
			"source": lead.source,
			"contact_owner": lead.lead_owner,
			"notes": lead.notes,
			"company": company.name if company else None,
		}).insert()

		deal = None
		if create_deal:
			deal = frappe.get_doc({
				"doctype": "DoubleT Deal",
				"deal_title": deal_title,
				"stage": stage,
				"amount": 0 if amount is None or amount == "" else amount,
				"source_lead": lead.name,
				"contact": contact.name,
				"company": company.name if company else None,
			}).insert()

		lead.status = "CONVERTED"
		lead.converted_on = now_datetime()
		lead.converted_contact = contact.name
		lead.converted_company = company.name if company else None
		lead.converted_deal = deal.name if deal else None
		lead.save()
		created = [_("Contact {0}").format(contact.name)]
		if company:
			created.append(_("Company {0}").format(company.name))
		if deal:
			created.append(_("Deal {0}").format(deal.name))
		lead.add_comment("Info", _("Lead converted: {0}").format(", ".join(created)))
	except Exception:
		frappe.db.rollback(save_point=save_point)
		raise
	else:
		frappe.db.release_savepoint(save_point)

	return {
		"contact": contact.name,
		"company": company.name if company else None,
		"deal": deal.name if deal else None,
	}
