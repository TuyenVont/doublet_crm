from decimal import Decimal, InvalidOperation

import frappe
from frappe import _
from frappe.utils import cint, flt


def validate_probability(value, label):
	"""Validate an optional probability without turning blank or invalid input into zero."""
	if value in (None, ""):
		return None
	try:
		probability = Decimal(str(value))
	except (InvalidOperation, TypeError, ValueError):
		frappe.throw(_("{0} must be a number from 0 to 100.").format(label), frappe.ValidationError)
	if not probability.is_finite() or probability < 0 or probability > 100:
		frappe.throw(_("{0} must be from 0 to 100.").format(label), frappe.ValidationError)
	return flt(probability, 2)


def set_probability_configuration(doc, label, fieldname="probability"):
	"""Persist an explicit configured flag because Frappe numeric columns store blank as zero."""
	configured_field = f"{fieldname}_configured"
	previous = doc.get_doc_before_save()
	raw_value = doc.get(fieldname)
	if doc.is_new() or not previous:
		configured = bool(cint(doc.get(configured_field))) or raw_value not in (None, "")
	elif cint(doc.get(configured_field)):
		configured = True
	elif doc.has_value_changed(configured_field):
		configured = False
	elif doc.has_value_changed(fieldname):
		configured = raw_value not in (None, "")
	else:
		configured = bool(cint(previous.get(configured_field)))
	doc.set(configured_field, cint(configured))
	doc.set(fieldname, validate_probability(raw_value, label) if configured else 0)
