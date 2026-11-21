import frappe

from doublet_crm.doublet_crm.doctype.doublet_call_log.doublet_call_log import INCOMING_CALL_TYPES, MISSED_STATUSES


def execute():
	# Every historical row stays in Call Logs. Only missed inbound calls need follow-up.
	log = frappe.qb.DocType("DoubleT Call Log")
	(
		frappe.qb.update(log)
		.set(log.handling_status, "Waiting")
		.set(log.queue_priority, 1)
		.where(log.handling_status.isnull() | (log.handling_status == ""))
		.where(log.call_type.isin(INCOMING_CALL_TYPES) & log.status.isin(MISSED_STATUSES))
	).run()
