import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def setup_custom_fields(args=None):
	comment_fields = [
		dict(
			fieldname="clickup_comment_id",
			fieldtype="Data",
			label="Clickup Comment Id",
			insert_after="reference_name",
			read_only=1,
			print_hide=1,
			translatable=0
		)
	]

	file_fields = [
		dict(
			fieldname="clickup_attachment_id",
			fieldtype="Data",
			label="Clickup Attachment Id",
			insert_after="attached_to_name",
			read_only=1,
			print_hide=1,
			translatable=0
		)
	]

	task_fields = [
		dict(
			fieldname="sb_clickup_information",
			label="Clickup Information",
			fieldtype="Section Break",
			insert_after="template_task",
			collapsible=1,
		),
		dict(
			fieldname="team_id",
			fieldtype="Data",
			label="Team Id",
			insert_after="sb_clickup_information",
			read_only=1,
			print_hide=1,
			translatable=0
		),
		dict(
			fieldname="space_id",
			fieldtype="Data",
			label="Space Id",
			insert_after="team_id",
			read_only=1,
			print_hide=1,
			translatable=0
		),
		dict(
			fieldname="folder_id",
			fieldtype="Data",
			label="Folder Id",
			insert_after="space_id",
			read_only=1,
			print_hide=1,
			translatable=0
		),
		dict(
			fieldname="list_id",
			fieldtype="Data",
			label="List Id",
			insert_after="folder_id",
			read_only=1,
			print_hide=1,
			translatable=0
		),
		dict(
			fieldname="task_id",
			fieldtype="Data",
			label="Task Id",
			insert_after="list_id",
			read_only=1,
			print_hide=1,
			translatable=0
		),
		dict(
			fieldname="cb_clickup_information",
			fieldtype="Column Break",
			insert_after="folder_id",
		),
		dict(
			fieldname="team_name",
			fieldtype="Data",
			label="Team",
			insert_after="cb_clickup_information",
			read_only=1,
			print_hide=1,
			translatable=0
		),
		dict(
			fieldname="space_name",
			fieldtype="Data",
			label="Space",
			insert_after="team_name",
			read_only=1,
			print_hide=1,
			translatable=0
		),
		dict(
			fieldname="folder_name",
			fieldtype="Data",
			label="Folder",
			insert_after="space_name",
			read_only=1,
			print_hide=1,
			translatable=0
		),
		dict(
			fieldname="list_name",
			fieldtype="Data",
			label="List",
			insert_after="folder_name",
			read_only=1,
			print_hide=1,
			translatable=0
		),
	]

	custom_fields = {
		"Task": task_fields,
		"Comment": comment_fields,
		"File": file_fields
	}

	print("Creating custom fields for Clickup Integration")
	create_custom_fields(custom_fields)