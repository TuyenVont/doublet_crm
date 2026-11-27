import frappe
from frappe import _
from frappe.model.document import Document

from doublet_crm.zalo_oa import CONVERSATION, external_key


class DoubleTMessage(Document):
    def autoname(self):
        self.name = external_key(self.source, self.oa_id, self.external_message_id)

    def validate(self):
        parent = frappe.db.get_value(CONVERSATION, self.conversation, ["source", "oa_id"], as_dict=True, for_update=True)
        if not parent or parent.source != self.source or parent.oa_id != self.oa_id:
            frappe.throw(_("The message must belong to the same OA and source as its conversation."))
