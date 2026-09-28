import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, flt, now_datetime


class DoubleTDeal(Document):
	def _set_defaults(self):
		# Frappe otherwise fills a missing Select with its first option before validate.
		deal_type = self.get("deal_type")
		super()._set_defaults()
		self.deal_type = deal_type

	def validate(self):
		if flt(self.amount) < 0:
			frappe.throw(_("Amount cannot be negative."))

		if self.deal_type not in {"PERSONAL", "COMPANY"}:
			frappe.throw(_("Deal Type must be PERSONAL or COMPANY."), frappe.ValidationError)
		if self.deal_type == "PERSONAL":
			if not self.contact:
				frappe.throw(_("Contact is required for a PERSONAL deal."), frappe.ValidationError)
			if self.company:
				frappe.throw(_("Company must be empty for a PERSONAL deal."), frappe.ValidationError)
		elif not self.company:
			frappe.throw(_("Company is required for a COMPANY deal."), frappe.ValidationError)

		if not self.stage:
			frappe.throw(_("Deal Stage is required."), frappe.ValidationError)
		stage_type = frappe.db.get_value("DoubleT Deal Stage", self.stage, "stage_type")
		if stage_type not in {"OPEN", "WON", "LOST"}:
			frappe.throw(_("Select a valid Deal Stage."), frappe.ValidationError)

		previous = self.get_doc_before_save()
		previous_stage_type = (
			frappe.db.get_value("DoubleT Deal Stage", previous.stage, "stage_type")
			if previous and previous.stage
			else None
		)

		if stage_type == "OPEN":
			self.won_on = None
			self.lost_on = None
			self.lost_reason = None
		elif stage_type == "WON":
			self.won_on = (
				previous.won_on if previous_stage_type == "WON" and previous.won_on else now_datetime()
			)
			self.lost_on = None
			self.lost_reason = None
		else:
			self.lost_reason = cstr(self.lost_reason).strip()
			if not self.lost_reason:
				frappe.throw(
					_("Lost Reason is required for a lost deal. Open the Deal and enter a reason first."),
					frappe.ValidationError,
				)
			self.lost_on = (
				previous.lost_on if previous_stage_type == "LOST" and previous.lost_on else now_datetime()
			)
			self.won_on = None
