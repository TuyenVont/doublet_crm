from frappe.model.document import Document

from doublet_crm.deal_probability import set_probability_configuration


class DoubleTDealStage(Document):
	def validate(self):
		set_probability_configuration(self, "Default Close Probability")

