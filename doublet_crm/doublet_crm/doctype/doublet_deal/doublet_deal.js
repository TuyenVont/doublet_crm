function update_lost_reason_field(frm) {
	const selected_stage = frm.doc.stage;
	if (!selected_stage) {
		frm.set_df_property("lost_reason", "reqd", 0);
		frm.set_df_property("lost_reason", "hidden", 1);
		return;
	}

	frappe.db.get_value("DoubleT Deal Stage", selected_stage, "stage_type").then((response) => {
		if (frm.doc.stage !== selected_stage) {
			return;
		}
		const is_lost = response.message?.stage_type === "LOST";
		frm.set_df_property("lost_reason", "reqd", is_lost ? 1 : 0);
		frm.set_df_property("lost_reason", "hidden", is_lost ? 0 : 1);
	});
}

frappe.ui.form.on("DoubleT Deal", {
	refresh: update_lost_reason_field,
	stage: update_lost_reason_field,
});
