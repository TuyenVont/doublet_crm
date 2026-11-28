import frappe
from frappe import _
from frappe.model.document import Document

from doublet_crm.zalo_oa import external_key


class DoubleTConversation(Document):
    def autoname(self):
        self.name = external_key(self.source, self.oa_id, self.external_user_id)

    def validate(self):
        if self.name != external_key(self.source, self.oa_id, self.external_user_id):
            frappe.throw(_("Conversation identity cannot be changed."))
        previous = self.get_doc_before_save()
        fields = ("contact", "lead", "assigned_to", "resolved_at", "handling_status")
        if previous:
            changed = any((self.get(field) or "") != (previous.get(field) or "") for field in fields)
        else:
            changed = any(self.get(field) for field in fields[:-1]) or self.handling_status not in (None, "", "Waiting")
        if changed:
            frappe.throw(_("Use the Zalo Inbox workflow to update this conversation."), frappe.PermissionError)
