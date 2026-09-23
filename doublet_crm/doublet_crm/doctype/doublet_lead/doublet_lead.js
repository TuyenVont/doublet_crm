frappe.ui.form.on("DoubleT Lead", {
	refresh(frm) {
		if (frm.is_new() || frm.is_dirty() || frm.doc.status === "CONVERTED" || frm.doc.converted_contact) {
			return;
		}

		frm.add_custom_button(__("Convert Lead"), () => {
			const dialog = new frappe.ui.Dialog({
				title: __("Convert Lead"),
				fields: [
					{
						fieldname: "create_company",
						fieldtype: "Check",
						label: __("Create Company"),
						onchange: () => {
							const enabled = Boolean(dialog.get_value("create_company"));
							dialog.set_df_property("company_name", "hidden", !enabled);
							dialog.set_df_property("company_name", "reqd", enabled);
						},
					},
					{
						fieldname: "company_name",
						fieldtype: "Data",
						label: __("Company Name"),
						default: frm.doc.company_name,
						hidden: 1,
					},
					{
						fieldname: "create_deal",
						fieldtype: "Check",
						label: __("Create Deal"),
						onchange: () => {
							const enabled = Boolean(dialog.get_value("create_deal"));
							for (const fieldname of ["deal_title", "stage", "amount"]) {
								dialog.set_df_property(fieldname, "hidden", !enabled);
							}
							dialog.set_df_property("deal_title", "reqd", enabled);
							dialog.set_df_property("stage", "reqd", enabled);
						},
					},
					{
						fieldname: "deal_title",
						fieldtype: "Data",
						label: __("Deal Title"),
						hidden: 1,
					},
					{
						fieldname: "stage",
						fieldtype: "Link",
						options: "DoubleT Deal Stage",
						label: __("Deal Stage"),
						hidden: 1,
					},
					{
						fieldname: "amount",
						fieldtype: "Currency",
						label: __("Amount"),
						default: 0,
						hidden: 1,
					},
				],
				primary_action_label: __("Convert Lead"),
				primary_action(values) {
					frappe.call({
						method: "doublet_crm.doublet_crm.doctype.doublet_lead.doublet_lead.convert_lead",
						args: {
							lead_name: frm.doc.name,
							...values,
						},
						freeze: true,
						callback(response) {
							if (response.message) {
								dialog.hide();
								frappe.show_alert({ message: __("Lead converted successfully"), indicator: "green" });
								frm.reload_doc();
							}
						},
					});
				},
			});

			dialog.show();
		});
	},
});
