from frappe.model.document import Document

from doublet_crm.zalo_oa import external_key


class DoubleTConversation(Document):
    def autoname(self):
        self.name = external_key(self.source, self.oa_id, self.external_user_id)
