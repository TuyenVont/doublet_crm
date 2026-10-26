import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, cstr, now_datetime


class DoubleTLead(Document):
	pass


@frappe.whitelist()
def check_duplicate_lead(email=None, phone=None):
	email = cstr(email).strip()
	phone = cstr(phone).strip()

	matches = {}

	def add_matches(doctype, fieldname, value, fields):
		if not value:
			return

		rows = frappe.get_list(
			doctype,
			filters={
				fieldname: value,
			},
			fields=fields,
			limit_page_length=10,
		)

		for row in rows:
			key = f"{doctype}:{row.name}"

			if key not in matches:
				full_name = " ".join(
					filter(
						None,
						[
							row.get("first_name"),
							row.get("last_name"),
						],
					)
				)

				matches[key] = {
					"doctype": doctype,
					"name": row.name,
					"full_name": full_name,
					"email": row.get("email"),
					"phone": row.get("phone"),
					"status": row.get("status"),
					"company": (
						row.get("company_name")
						or row.get("company")
					),
					"matched_by": [],
				}

			if fieldname not in matches[key]["matched_by"]:
				matches[key]["matched_by"].append(fieldname)

	lead_fields = [
		"name",
		"first_name",
		"last_name",
		"email",
		"phone",
		"company_name",
		"status",
	]

	contact_fields = [
		"name",
		"first_name",
		"last_name",
		"email",
		"phone",
		"company",
	]

	add_matches(
		"DoubleT Lead",
		"email",
		email,
		lead_fields,
	)

	add_matches(
		"DoubleT Lead",
		"phone",
		phone,
		lead_fields,
	)

	add_matches(
		"DoubleT Contact",
		"email",
		email,
		contact_fields,
	)

	add_matches(
		"DoubleT Contact",
		"phone",
		phone,
		contact_fields,
	)

	return {
		"has_duplicates": bool(matches),
		"matches": list(matches.values()),
	}


@frappe.whitelist(methods=["POST"])
def convert_lead(
	lead_name,
	existing_contact=None,
	existing_company=None,
	create_company=0,
	company_name=None,
	create_deal=1,
	deal_title=None,
	stage=None,
	amount=0,
):
	"""Convert DoubleT Lead using existing/new Contact and Company."""

	existing_contact = cstr(existing_contact).strip()
	existing_company = cstr(existing_company).strip()

	create_company = cint(create_company)
	create_deal = cint(create_deal)

	company_name = cstr(company_name).strip()
	deal_title = cstr(deal_title).strip()
	stage = cstr(stage).strip()

	# --------------------------------
	# LOCK LEAD
	# --------------------------------

	frappe.db.get_value(
		"DoubleT Lead",
		lead_name,
		"name",
		for_update=True,
	)

	lead = frappe.get_doc(
		"DoubleT Lead",
		lead_name,
	)

	lead.check_permission("write")

	# --------------------------------
	# TC-03: PREVENT RECONVERSION
	# --------------------------------

	if (
		lead.status == "CONVERTED"
		or lead.converted_contact
	):
		frappe.throw(
			_("This lead has already been converted."),
			frappe.ValidationError,
		)

	# --------------------------------
	# VALIDATION
	# --------------------------------

	if existing_company and create_company:
		frappe.throw(
			_(
				"Choose either an existing company or create a new company."
			),
			frappe.ValidationError,
		)

	if create_company and not company_name:
		frappe.throw(
			_(
				"Company Name is required when creating a company."
			),
			frappe.ValidationError,
		)

	if create_deal and not deal_title:
		frappe.throw(
			_("Deal Title is required."),
			frappe.ValidationError,
		)

	if create_deal and not stage:
		frappe.throw(
			_("Deal Stage is required."),
			frappe.ValidationError,
		)

	# --------------------------------
	# TRANSACTION
	# --------------------------------

	save_point = (
		f"doublet_lead_conversion_"
		f"{frappe.generate_hash(length=12)}"
	)

	frappe.db.savepoint(save_point)

	try:
		contact = None
		company = None
		deal = None

		contact_created = False
		company_created = False

		# --------------------------------
		# COMPANY
		# --------------------------------

		if existing_company:
			company = frappe.get_doc(
				"DoubleT Company",
				existing_company,
			)

			company.check_permission("read")

		elif create_company:
			company = frappe.get_doc({
				"doctype": "DoubleT Company",
				"company_name": company_name,
			}).insert()

			company_created = True

		# --------------------------------
		# CONTACT
		# --------------------------------

		if existing_contact:
			contact = frappe.get_doc(
				"DoubleT Contact",
				existing_contact,
			)

			contact.check_permission("read")

		else:
			contact = frappe.get_doc({
				"doctype": "DoubleT Contact",
				"first_name": lead.first_name,
				"last_name": lead.last_name,
				"email": lead.email,
				"phone": lead.phone,
				"source": lead.source,
				"contact_owner": lead.lead_owner,
				"notes": lead.notes,
				"company": (
					company.name
					if company
					else None
				),
			}).insert()

			contact_created = True
			

		# --------------------------------
		# DEAL
		# --------------------------------

		if create_deal:
			deal = frappe.get_doc({
				"doctype": "DoubleT Deal",

				"deal_title": deal_title,

				"deal_type": (
					"COMPANY"
					if company
					else "PERSONAL"
				),

				"stage": stage,

				"amount": (
					0
					if amount is None
					or amount == ""
					else amount
				),
				"deal_owner": lead.lead_owner,
"source": lead.source,

				"source_lead": lead.name,

				"contact": contact.name,

				"company": (
					company.name
					if company
					else None
				),
			}).insert()

		# --------------------------------
		# UPDATE LEAD
		# --------------------------------

		lead.status = "CONVERTED"

		lead.converted_on = (
			now_datetime()
		)

		lead.converted_contact = (
			contact.name
		)

		lead.converted_company = (
			company.name
			if company
			else None
		)

		lead.converted_deal = (
			deal.name
			if deal
			else None
		)

		lead.save()

		# --------------------------------
		# TIMELINE COMMENT
		# --------------------------------

		linked = [
			_("Contact {0}").format(
				contact.name
			)
		]

		if company:
			linked.append(
				_("Company {0}").format(
					company.name
				)
			)

		if deal:
			linked.append(
				_("Deal {0}").format(
					deal.name
				)
			)

		lead.add_comment(
			"Info",
			_(
				"Lead converted: {0}"
			).format(
				", ".join(linked)
			),
		)

	except Exception:
		frappe.db.rollback(
			save_point=save_point
		)
		raise

	else:
		frappe.db.release_savepoint(
			save_point
		)

	# --------------------------------
	# RESPONSE
	# --------------------------------

	return {
		"contact": contact.name,

		"contact_created":
			contact_created,

		"company": (
			company.name
			if company
			else None
		),

		"company_created":
			company_created,

		"deal": (
			deal.name
			if deal
			else None
		),
	}