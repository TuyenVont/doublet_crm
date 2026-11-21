from doublet_crm.patches.archive_legacy_call_ai_notes import execute as archive_call_notes


def execute():
	# Revisit sites that ran the earlier patch before section boundaries were preserved.
	archive_call_notes()
