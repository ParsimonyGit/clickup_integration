// Copyright (c) 2024, Parsimony LLC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Clickup Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Sync Tasks"), function () {
			frappe.call({
				method: "clickup_integration.clickup_integration.doctype.clickup_settings.clickup_settings.sync_tasks",
				callback(r) {
					if (r.message) {
						frappe.msgprint(__("Background Job is created to sync to the Data"));
					}
				},
			});
		});
	},
});
