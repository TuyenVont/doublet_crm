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

function update_deal_type_fields(frm) {
	const is_personal = frm.doc.deal_type === "PERSONAL";
	const is_company = frm.doc.deal_type === "COMPANY";
	frm.set_df_property("contact", "hidden", 0);
	frm.set_df_property("contact", "reqd", is_personal ? 1 : 0);
	frm.set_df_property("company", "hidden", is_personal ? 1 : 0);
	frm.set_df_property("company", "reqd", is_company ? 1 : 0);
}

frappe.ui.form.on("DoubleT Deal", {
	refresh(frm) {
		update_lost_reason_field(frm);
		update_deal_type_fields(frm);
	},
	async deal_type(frm) {
		if (frm.doc.deal_type === "PERSONAL" && frm.doc.company) {
			await frm.set_value("company", null);
		}
		update_deal_type_fields(frm);
	},
	stage: update_lost_reason_field,
});
