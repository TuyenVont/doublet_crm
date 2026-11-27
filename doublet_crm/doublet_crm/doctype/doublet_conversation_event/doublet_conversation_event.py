from frappe.model.document import Document

from doublet_crm.zalo_oa import external_key


class DoubleTConversationEvent(Document):
    def autoname(self):
        if self.request_id:
            self.name = external_key(self.conversation, self.request_id)
